#!/usr/bin/env python
#################################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and proprietary
# and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#################################################################################
import sys
import re

from dtaf_core.lib.dtaf_constants import Framework

from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.bios_util import SerialBiosUtil
from src.lib.test_content_logger import TestContentLogger
from src.storage.lib.sata_raid_util import SataRaidUtil
from src.environment.os_installation import OsInstallation
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import SutInventoryConstants
from src.lib.install_collateral import InstallCollateral


class StorageStressSataRaid0Raid10(ContentBaseTestCase):
    """
    Pheonix : 16013819124-SATA_Stability_and_Stress_FIO_with_RAID_1_and_RAID_10
    This class used for create RAID and execute FIO
    """

    TEST_CASE_ID = ["16013819124", "SATA_Stability_and_Stress_FIO_with_RAID_1_and_RAID_10"]
    REGEX_FOR_FIO = r'\serr=\s0'
    FIO_TOOL_NAME = r"fio"
    FIO_CMDS = ["fio --name=read --rw=read --numjobs=2 --bs=8k --filename={}"
                " --size=4G --ioengine=posixaio --runtime=20 --time_based --iodepth=2 --group_reporting",
                "fio --name=read --rw=randwrite --numjobs=500 --bs=64k --filename={} --size=8G "
                "--ioengine=posixaio --runtime=20 --time_based --iodepth=1 --group_reporting",
                "fio --name=read --rw=write --numjobs=2 --bs=8k --filename={} --size=4G"
                " --ioengine=posixaio --runtime=20 --time_based --iodepth=2 --group_reporting",
                "fio --name=read --rw=randread --numjobs=100 --bs=8k --filename={} "
                "--size=16G --ioengine=posixaio --runtime=20 --time_based --iodepth=1 --group_reporting"]


    step_data_dict = {
                      1: {'step_details': 'Create the RAID1 and RAID10',
                          'expected_results': 'RAID1 and RAID10 Creation successful'},
                      2: {'step_details': 'Execute FIO on the created RAID',
                          'expected_results': 'FIO execution to be successful.'},
                      3: {'step_details': 'Verify FIO log no error to be detected',
                          'expected_results': 'Verified FIO log is successful'},
                      4: {'step_details': 'Delete RAID Volume',
                          'expected_results': 'Successfully deleted RAID Volume'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
         Creates a new StorageBootingToSataRaid0Raid1 object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self._log = test_log
        self._cfg_opts = cfg_opts
        self._cc_log_path = arguments.outputpath

        super(StorageStressSataRaid0Raid10, self).__init__(test_log, arguments, cfg_opts)
        self._serial_bios_util = SerialBiosUtil(self.ac_power, test_log, self._common_content_lib, cfg_opts)
        self._raid_util = SataRaidUtil(self._log, self._common_content_lib, self._common_content_configuration,
                                       self.bios_util, self._serial_bios_util, self.ac_power)
        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self.raid_levels = list()
        self.non_raid_disk_name = None

    def prepare(self):
        # type: () -> None
        """
        This method is to get the non raid disk name from sut inventory
        :return None
        """
        self._install_collateral.install_fio(install_fio_package=False)
        super(StorageStressSataRaid0Raid10, self).prepare()
        sut_inv_file_path = self._os_installation_lib.get_sut_inventory_file_path()
        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if SutInventoryConstants.NON_RAID_SSD_NAME in line:
                    self.non_raid_disk_name = line
                    break

        if not self.non_raid_disk_name:
            raise content_exceptions.TestError("Unable to find non RAID SSD name, please check the file under "
                                               "{}".format(sut_inv_file_path))

        self.non_raid_disk_name = self.non_raid_disk_name.split("=")[1]
        self._log.info("non RAID SSD Name from config file : {}".format(self.non_raid_disk_name))

    def execute(self):
        """
        This Method is used for:
        1. Create Raid1 and Raid10 on SATA
        2. Execute FIO on the RAID
        """
        self.raid_levels = ["RAID1(Mirror)", "RAID10(RAID1+0)"]
        for raid_level in self.raid_levels:
            # Step logger start for Step 1
            self._test_content_logger.start_step_logger(1)
            self._raid_util.create_raid(raid_level)
            self.os.wait_for_os(self.reboot_timeout)
            # Step logger end for Step 1
            self._test_content_logger.end_step_logger(1, return_val=True)
            self._log.info("Getting the RAID devices from OS")
            fio_execution_device = self._common_content_lib.execute_sut_cmd("cat /proc/mdstat",
                                                                            cmd_str="cat /proc/mdstat",
                                                                            execute_timeout=
                                                                            self._command_timeout)
            fio_execution_device = fio_execution_device.split("\n")
            device_list = list()
            for line in fio_execution_device:
                line_split = line.split(":")[0]
                if "md" in line_split:
                    active_devices = line.split(":")[1].split(" ")
                    if "active" in active_devices:
                        device_list.append("/dev/" + line_split.strip())
            if len(device_list) > 1:
                devices = ":".join(device_list)
            else:
                devices = device_list[0]
            for each_cmd in self.FIO_CMDS:
                self._test_content_logger.start_step_logger(2)
                fio_cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=each_cmd.format(devices),
                                                                          cmd_str=each_cmd,
                                                                          execute_timeout=self._command_timeout)
                self._test_content_logger.end_step_logger(2, True)
                self._test_content_logger.start_step_logger(3)
                self._log.info(fio_cmd_output.strip())
                reg_output = re.findall(self.REGEX_FOR_FIO, fio_cmd_output.strip())
                if not len(reg_output):
                    raise content_exceptions.TestFail('Un-expected Error Captured in Fio output Log')
                self._log.info('No Error Captured as Expected')
                self._stress_provider.check_app_running(app_name=self.FIO_TOOL_NAME,
                                                        stress_test_command="./" + self.FIO_TOOL_NAME)
                self._log.info("FIO Command execution has completed successfully and been Verified Bandwidth!")
                self._test_content_logger.end_step_logger(3, True)
            self._test_content_logger.start_step_logger(4)
            self._raid_util.delete_raid(raid_level, self.non_raid_disk_name)
            self.os.wait_for_os(self.reboot_timeout)
            self.bios_util.load_bios_defaults()
            self.os.reboot(self.reboot_timeout)
            self.os.wait_for_os(self.reboot_timeout)
            self._test_content_logger.end_step_logger(4, True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageStressSataRaid0Raid10.main() else Framework.TEST_RESULT_FAIL)
