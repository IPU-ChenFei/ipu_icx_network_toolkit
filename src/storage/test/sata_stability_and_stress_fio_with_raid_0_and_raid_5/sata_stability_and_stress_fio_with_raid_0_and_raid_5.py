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
import re
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.provider.stressapp_provider import StressAppTestProvider

from src.lib.install_collateral import InstallCollateral

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.bios_util import SerialBiosUtil
from src.lib.test_content_logger import TestContentLogger
from src.storage.lib.sata_raid_util import SataRaidUtil
from src.environment.os_installation import OsInstallation
from src.provider.storage_provider import StorageProvider
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import SutInventoryConstants, RaidConstants


class SataStabilityStressFioWithRaid0Raid5(ContentBaseTestCase):
    """
    PHOENIX ID : 1308856622 SATA Stability and Stress FIO with RAID 0 and RAID 5
    this class used to create RAID0 and RAID5 using 8 SATA drives
    """

    TEST_CASE_ID = ["1308856622", "SATA_Stability_and_Stress_FIO_with_RAID_0_and_RAID_5"]
    REGEX_FOR_FIO = r'\serr=\s0'
    FIO_TOOL_NAME = r"fio"
    FIO_CMDS = ["fio --name=read --rw=read --numjobs=2 --bs=8k --filename=/dev/sda"
                " --size=4G --ioengine=posixaio --runtime=20 --time_based --iodepth=2 --group_reporting",
                "fio --name=read --rw=randwrite --numjobs=500 --bs=64k --filename=/dev/md126 --size=8G "
                "--ioengine=posixaio --runtime=20 --time_based --iodepth=1 --group_reporting",
                "fio --name=read --rw=write --numjobs=2 --bs=8k --filename=/dev/md126 --size=4G"
                " --ioengine=posixaio --runtime=20 --time_based --iodepth=2 --group_reporting",
                "fio --name=read --rw=randread --numjobs=100 --bs=8k --filename=/dev/md126 "
                "--size=16G --ioengine=posixaio --runtime=20 --time_based --iodepth=1 --group_reporting"]

    step_data_dict = {
        1: {'step_details': 'create the RAID0 and RAID5 using SATA Drives',
            'expected_results': 'RAID0 and RAID5 Creation successful'},
        2: {'step_details': 'Install FIO tool',
            'expected_results': 'Successfully Installed FIO tool'},
        3: {'step_details': 'Run the fio command for sequential write, read, random read and random write',
            'expected_results': 'Command executed successfully and met the bandwidth requirement as per '
                                'spec and no errors seen in the log'},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
         Creates a new SataStabilityStressFioWithRaid0Raid5 object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self._log = test_log
        self._cfg_opts = cfg_opts

        self._cc_log_path = arguments.outputpath

        super(SataStabilityStressFioWithRaid0Raid5, self).__init__(test_log, arguments, cfg_opts)
        self._serial_bios_util = SerialBiosUtil(self.ac_power, test_log, self._common_content_lib, cfg_opts)
        self._raid_util = SataRaidUtil(self._log, self._common_content_lib, self._common_content_configuration,
                                       self.bios_util, self._serial_bios_util, self.ac_power)
        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._storage_provider = StorageProvider.factory(self._log, self.os, self._cfg_opts, "os")
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self.raid_levels = list()
        self.raid_levels_test = list()
        self._ac = self.ac_power
        self.non_raid_disk_name = None

    def prepare(self):
        # type: () -> None
        """
        This method is to get the non raid disk name from sut inventory
        :return None
        """
        sut_inv_file_path = self._os_installation_lib.get_sut_inventory_file_path()
        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if SutInventoryConstants.NON_RAID_SSD_NAME in line:
                    self.non_raid_disk_name = line

        if not self.non_raid_disk_name:
            raise content_exceptions.TestError("Unable to find non RAID SSD name, please check the file under "
                                               "{}".format(sut_inv_file_path))
        self.non_raid_disk_name = self.non_raid_disk_name.split("=")[1]
        self._log.info("non RAID SSD Name from config file : {}".format(self.non_raid_disk_name))
        self._common_content_lib.update_sut_inventory_file(SutInventoryConstants.SATA_RAID, SutInventoryConstants.RHEL)

    def execute(self):
        """
        This Function to create RAID0 and RAID5 , and run stress tool fio.
        :return: True if RAID creation and Stress Run Successful else False
        """
        ret_val = []
        self.raid_levels = [RaidConstants.RAID0, RaidConstants.RAID5]
        self._log.info("Getting raid levels info from BIOS page")
        raid_levels_supported = self._raid_util.get_supported_raid_levels()
        self._log.debug("Supported RAID Levels for current Device Setup are {}".format(raid_levels_supported))
        for raid_level in self.raid_levels:
            if raid_level in raid_levels_supported:
                self.raid_levels_test.append(raid_level)

        self._common_content_lib.perform_graceful_ac_off_on(self._ac)
        self._log.info("Waiting for SUT to boot to OS..")
        self.os.wait_for_os(self.reboot_timeout)

        for raid_level in self.raid_levels_test:
            # Step logger start for Step 1
            self._test_content_logger.start_step_logger(1)
            bios_info = self._raid_util.create_raid(raid_level)
            self.os.wait_for_os(self.reboot_timeout)
            self._log.info("Closing the Serial Port")
            self.cng_log.__exit__(None, None, None)
            self._log.info("Reopening the Serial Port")
            try:
                self._serial_bios_util = SerialBiosUtil(self.ac_power, self._log, self._common_content_lib,
                                                        self._cfg_opts)
                self._raid_util = SataRaidUtil(self._log, self._common_content_lib, self._common_content_configuration,
                                               self.bios_util, self._serial_bios_util, self.ac_power)

            except Exception as ex:
                self._log.debug("Exception occurred while creating serial_bios_util but we can ignore it:{}".format(ex))
            # Step logger end for Step 1
            self._test_content_logger.end_step_logger(1, return_val=True)

            # Step logger start for Step 2
            self._test_content_logger.start_step_logger(2)
            self._install_collateral.screen_package_installation()
            self._install_collateral.install_fio(install_fio_package=True)
            # Step logger end for Step 2
            self._test_content_logger.end_step_logger(2, return_val=True)

            # Step logger start for Step 3
            self._test_content_logger.start_step_logger(3)
            self._log.info('Execute the fio command...')
            for each_cmd in self.FIO_CMDS:
                fio_cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=each_cmd, cmd_str=each_cmd,
                                                                          execute_timeout=self._command_timeout)
                self._log.info(fio_cmd_output.strip())
                reg_output = re.findall(self.REGEX_FOR_FIO, fio_cmd_output.strip())
                if not len(reg_output):
                    raise content_exceptions.TestFail('Un-expected Error Captured in Fio output Log')
                self._log.info('No Error Captured as Expected')
                self._stress_provider.check_app_running(app_name=self.FIO_TOOL_NAME,
                                                        stress_test_command="./" + self.FIO_TOOL_NAME)

            self._raid_util.delete_raid(raid_level, self.non_raid_disk_name)
            self.os.wait_for_os(self.reboot_timeout)

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)
        return all(ret_val)

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        # setting back the default bios knobs
        self.bios_util.load_bios_defaults()
        self.perform_graceful_g3()
        super(SataStabilityStressFioWithRaid0Raid5, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SataStabilityStressFioWithRaid0Raid5.main() else Framework.TEST_RESULT_FAIL)
