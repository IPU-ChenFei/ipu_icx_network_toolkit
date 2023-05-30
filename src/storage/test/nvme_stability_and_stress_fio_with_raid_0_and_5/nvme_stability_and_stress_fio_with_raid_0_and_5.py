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

from src.provider.storage_provider import StorageProvider
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.test_content_logger import TestContentLogger
from src.lib.install_collateral import InstallCollateral
from src.storage.test.storage_common import StorageCommon
from src.storage.lib.nvme_raid_util import NvmeRaidUtil
from src.lib.bios_util import SerialBiosUtil
from src.lib.dtaf_content_constants import RaidConstants
from src.environment.os_installation import OsInstallation
from src.lib import content_exceptions


class NvmeStressFioRaid0And5(StorageCommon):
    """
    Phoenix ID : 16013957609 NVME-Stability and Stress- FIO with RAID 0 and 5
    This test case functionality is to install, execute intelmas tool on SUT and upgrade the SSD FW
    """
    TEST_CASE_ID = ["16013957609", "NVME_Stability_and_Stress_FIO_with_RAID_0_and_5"]
    VMD_PORT = ["IOU3", "IOU4"]
    DISK_RAID_CREATION = ["U2_NVME", "PCIE"]
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
        1: {'step_details': 'Get the non-raid ssd from SUT inventory file',
            'expected_results': 'non-raid ssd to be captured from the SUT inventory file'},
        2: {'step_details': 'Enable the BIOS Knobs based on the disk running and verify ',
            'expected_results': 'BIOS knobs to be enabled successfully'},
        3: {'step_details': 'Create RAID0 and RAID5 on the system and BOOT to OS',
            'expected_results': 'RAID0 and RAID5 to be created successfully and system to boot to OS'},
        4: {'step_details': 'Get RAID devices to run FIO',
            'expected_results': 'Raid devices to be fetched successfully.'},
        5: {'step_details': 'Execute the FIO command',
            'expected_results': 'FIO commands to executed successfully.'},
        6: {'step_details': 'Get and verify the logs',
            'expected_results': 'There should not be any error detected.'},
        7: {'step_details': 'Delete the Created RAID levels for the clean up',
            'expected_results': 'Raid Volumes to be deleted successfully to be successful'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new NvmeStressFioRaid0And5 object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self._log = test_log
        self._cfg_opts = cfg_opts
        self._cc_log_path = arguments.outputpath
        super(NvmeStressFioRaid0And5, self).__init__(test_log, arguments, cfg_opts)
        self._serial_bios_util = SerialBiosUtil(self.ac_power, test_log, self._common_content_lib, cfg_opts)
        self._raid_util = NvmeRaidUtil(self._log, self._common_content_lib, self._common_content_configuration,
                                       self.bios_util, self._serial_bios_util, self.ac_power)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._storage_provider = StorageProvider.factory(self._log, self.os, self._cfg_opts, "os")
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self.raid_levels = None
        self.non_raid_disk_name = None

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        self._install_collateral.install_fio(install_fio_package=False)
        super(NvmeStressFioRaid0And5, self).prepare()
        self._test_content_logger.start_step_logger(1)
        sut_inv_file_path = self._os_installation_lib.get_sut_inventory_file_path()
        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if "non_raid_ssd_name" in line:
                    self.non_raid_disk_name = line
                    break

        if not self.non_raid_disk_name:
            raise content_exceptions.TestError("Unable to find non RAID SSD name, please check the file under "
                                               "{}".format(sut_inv_file_path))

        self.non_raid_disk_name = self.non_raid_disk_name.split("=")[1]
        self._log.info("non RAID SSD Name from config file : {}".format(self.non_raid_disk_name))
        self._test_content_logger.end_step_logger(1, True)

    def execute(self):
        """
        This test case functionality is to install, execute intel mas tool on SUT and upgrade the SSD FW

        :return: True
        :raise: If Upgradation failed raise content_exceptions.TestFail
        """
        for disk in self.DISK_RAID_CREATION:
            self.raid_levels = [RaidConstants.RAID0, RaidConstants.RAID5]
            for raid_level in self.raid_levels:
                self._test_content_logger.start_step_logger(2)
                if disk == "PCIE":
                    self.enable_vmd_bios_knobs()
                else:
                    for iou in self.VMD_PORT:
                        self.enable_vmd_bios_knob_using_port(iou)
                self._test_content_logger.end_step_logger(2, True)
                self._test_content_logger.start_step_logger(3)
                self._log.info("Creating {} volume on {}".format(raid_level, disk))
                self._raid_util.create_raid_disk(raid_level, disk)
                self._log.info("Waiting for SUT to boot to OS after {} Creattion".format(raid_level))
                self.os.wait_for_os(self.reboot_timeout)
                self._test_content_logger.end_step_logger(3, True)
                self._test_content_logger.start_step_logger(4)
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
                            device_list.append("/dev/"+line_split.strip())
                devices = ":".join(device_list)
                self._test_content_logger.end_step_logger(4, True)
                for each_cmd in self.FIO_CMDS:
                    self._test_content_logger.start_step_logger(5)
                    fio_cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=each_cmd.format(devices),
                                                                              cmd_str=each_cmd,
                                                                              execute_timeout=self._command_timeout)
                    self._test_content_logger.end_step_logger(5, True)
                    self._test_content_logger.start_step_logger(6)
                    self._log.info(fio_cmd_output.strip())
                    reg_output = re.findall(self.REGEX_FOR_FIO, fio_cmd_output.strip())
                    if not len(reg_output):
                        raise content_exceptions.TestFail('Un-expected Error Captured in Fio output Log')
                    self._log.info('No Error Captured as Expected')
                    self._stress_provider.check_app_running(app_name=self.FIO_TOOL_NAME,
                                                            stress_test_command="./" + self.FIO_TOOL_NAME)
                    self._log.info("FIO Command execution has completed successfully and been Verified Bandwidth!")
                    self._test_content_logger.end_step_logger(6, True)
                self._test_content_logger.start_step_logger(7)
                self._raid_util.delete_raid(raid_level, self.non_raid_disk_name)
                self.os.wait_for_os(self.reboot_timeout)
                self.bios_util.load_bios_defaults()
                self.os.reboot(self.reboot_timeout)
                self.os.wait_for_os(self.reboot_timeout)
                self._test_content_logger.end_step_logger(7, True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(NvmeStressFioRaid0And5, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if NvmeStressFioRaid0And5.main() else Framework.TEST_RESULT_FAIL)
