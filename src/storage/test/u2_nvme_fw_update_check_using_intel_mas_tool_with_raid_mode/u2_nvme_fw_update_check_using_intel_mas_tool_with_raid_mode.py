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

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.lib.install_collateral import InstallCollateral
from src.storage.test.storage_common import StorageCommon
from src.storage.lib.nvme_raid_util import NvmeRaidUtil
from src.lib.bios_util import SerialBiosUtil
from src.lib.dtaf_content_constants import RaidConstants
from src.environment.os_installation import OsInstallation
from src.lib import content_exceptions


class U2NvmeFWUpgradeRaidMode(StorageCommon):
    """
    Phoenix ID : 16013819520 U.2 NVME-FW update check using Intel MAS tool With RAID Mode
    This test case functionality is to install, execute intelmas tool on SUT and upgrade the SSD FW
    """
    TEST_CASE_ID = ["16013819520", "U2_nvme_fw_update_check_using_intel_mas_tool_with_raid_mode"]
    VMD_PORT = ["IOU3", "IOU4"]

    step_data_dict = {
        1: {'step_details': 'Enable VMD BIOS Knobs of IOU3 and IOU4',
            'expected_results': 'VMD Knobs to be enabled Successfully'},
        2: {'step_details': 'Check the drive are been detected in BIOS Successfully',
            'expected_results': 'List of devices to be detected successfully'},
        3: {'step_details': 'Create RAID5 on the system and BOOT to OS',
            'expected_results': 'RAID5 to be created successfully and system to boot to OS'},
        4: {'step_details': 'Install IntelMas tool',
            'expected_results': 'Tntel Mas tool to be installed successfully'},
        5: {'step_details': 'Get the SSD ID and Install FirmWare update',
            'expected_results': 'Firmware update to be successful'},
        6: {'step_details': 'Delete the Created RAID5 Volume for the clean up',
            'expected_results': 'Raid5 Volume to be deleted successfully to be successful'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new SATASSDFWUpgradeCheckAHCIMode object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self._log = test_log
        self._cfg_opts = cfg_opts
        self._cc_log_path = arguments.outputpath
        super(U2NvmeFWUpgradeRaidMode, self).__init__(test_log, arguments, cfg_opts)
        self._serial_bios_util = SerialBiosUtil(self.ac_power, test_log, self._common_content_lib, cfg_opts)
        self._raid_util = NvmeRaidUtil(self._log, self._common_content_lib, self._common_content_configuration,
                                       self.bios_util, self._serial_bios_util, self.ac_power)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self.raid_levels = None
        self.non_raid_disk_name = None

    def prepare(self):
        # type: () -> None
        """
        :return None
        """

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

        self._test_content_logger.start_step_logger(1)
        super(U2NvmeFWUpgradeRaidMode, self).prepare()
        for iou in self.VMD_PORT:
            self.enable_vmd_bios_knob_using_port(iou)
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        self.check_disk_detected_intel_vroc()
        self._test_content_logger.end_step_logger(2, True)

    def execute(self):
        """
        This test case functionality is to install, execute intel mas tool on SUT and upgrade the SSD FW

        :return: True
        :raise: If Upgradation failed raise content_exceptions.TestFail
        """
        self.raid_levels = [RaidConstants.RAID5]
        self._test_content_logger.start_step_logger(3)
        for raid_level in self.raid_levels:
            self._log.info("Creating {} volume ".format(raid_level))
            self._raid_util.create_raid(raid_level)
            self._log.info("Waiting for SUT to boot to OS")
            self.os.wait_for_os(self.reboot_timeout)
        self._test_content_logger.end_step_logger(3, True)

        self._test_content_logger.start_step_logger(4)
        # Installing intelmas Tool
        self._install_collateral.install_intel_mas_tool_linux()
        self._test_content_logger.end_step_logger(4, True)

        self._test_content_logger.start_step_logger(5)
        intel_ssd_id_list = self.get_intelssd()
        self._log.info("Upgrade FW using intel mas load command on each Intel SSD present in the System")
        for each_id in intel_ssd_id_list:
            self.upgrade_ssd_fw_and_verify(each_id)
        self._log.info("Successfully Upgraded all Intel SSDs present in the System")
        self._test_content_logger.end_step_logger(5, True)

        self._test_content_logger.start_step_logger(6)
        self._raid_util.delete_raid(raid_level=self.raid_levels[0], non_raid_disk=self.non_raid_disk_name)

        self._test_content_logger.end_step_logger(6, True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(U2NvmeFWUpgradeRaidMode, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if U2NvmeFWUpgradeRaidMode.main() else Framework.TEST_RESULT_FAIL)
