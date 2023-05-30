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
from src.provider.vss_provider import VssProvider
from src.storage.test.storage_common import StorageCommon
from src.storage.lib.nvme_raid_util import NvmeRaidUtil
from src.lib.bios_util import SerialBiosUtil
from src.lib.dtaf_content_constants import RaidConstants
from src.environment.os_installation import OsInstallation
from src.lib import content_exceptions


class U2NvmeStabilityILVSSRaidMode(StorageCommon):
    """
    Phoenix ID : 16013942532 U.2NVME-Stability and Stress- Data integrity - ILVSS in RAID Mode

    """
    TEST_CASE_ID = ["16013942532", "U.2_NVME_Stability_and_Stress_Data_integrity_ILVSS_in_RAID_Mode"]
    VMD_PORT = ["IOU3", "IOU4"]
    PROCESS_NAME = "texec"
    LOG_NAME = "ilvss_log.log"

    step_data_dict = {
        1: {'step_details': 'Enable VMD BIOS Knobs of IOU3 and IOU4',
            'expected_results': 'VMD Knobs to be enabled Successfully'},
        2: {'step_details': 'Check the drive are been detected in BIOS Successfully',
            'expected_results': 'List of devices to be detected successfully'},
        3: {'step_details': 'Create RAID on the system and BOOT to OS',
            'expected_results': 'RAID to be created successfully and system to boot to OS'},
        4: {'step_details': 'run ilvss tool',
            'expected_results': 'Ilvss tool ran successfully'},
        5: {'step_details': 'Delete the Created RAID Volume',
            'expected_results': 'Raid Volume deleted successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new U2NvmeStabilityILVSSRaidMode object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self._log = test_log
        self._cfg_opts = cfg_opts
        self._cc_log_path = arguments.outputpath
        super(U2NvmeStabilityILVSSRaidMode, self).__init__(test_log, arguments, cfg_opts)
        self._serial_bios_util = SerialBiosUtil(self.ac_power, test_log, self._common_content_lib, cfg_opts)
        self._raid_util = NvmeRaidUtil(self._log, self._common_content_lib, self._common_content_configuration,
                                       self.bios_util, self._serial_bios_util, self.ac_power)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self.raid_levels = None
        self.non_raid_disk_name = None
        self._vss_provider_obj = VssProvider.factory(self._log, cfg_opts=cfg_opts, os_obj=self.os)

    def prepare(self):
        # type: () -> None
        """
        1. Enable VMD bios knobs
        2. To check devices in VROC in Bios

        return None
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
        self._common_content_lib.clear_all_os_error_logs()
        self.bios_util.load_bios_defaults()
        for iou in self.VMD_PORT:
            self.enable_vmd_bios_knob_using_port(iou)
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        self.check_disk_detected_intel_vroc()
        self._test_content_logger.end_step_logger(2, True)

    def execute(self):
        """
        1. Create RAID0, RAID1, RAID5, RAID10
        2. Run the ilvss tool
        3. Delete the RAID

        :return: True
        :raise:
        """
        ret_value = []
        self.raid_levels = [RaidConstants.RAID0, RaidConstants.RAID1, RaidConstants.RAID5, RaidConstants.RAID10]

        for raid_level in self.raid_levels:
            self._test_content_logger.start_step_logger(3)
            self._log.info("Creating {} volume ".format(raid_level))
            self._raid_util.create_raid(raid_level)
            self._log.info("Waiting for SUT to boot to OS")
            self.os.wait_for_os(self.reboot_timeout)
            self._test_content_logger.end_step_logger(3, True)

            self._test_content_logger.start_step_logger(4)
            # installing screen package
            self._install_collateral.screen_package_installation()

            # To copy the package
            self._vss_provider_obj.configure_vss_stress_storage()

            self._log.info("Executing the ilvss ...")
            # Execute ilvss configuration for stress
            self._vss_provider_obj.execute_vss_storage_test_package(flow_tree="S2")

            # wait for the VSS to complete
            self._vss_provider_obj.wait_for_vss_to_complete(self.PROCESS_NAME)

            # Parsing ilvss log
            ret_value.append(self._vss_provider_obj.verify_vss_logs(self.LOG_NAME))

            self._test_content_logger.end_step_logger(4, all(ret_value))

            self._test_content_logger.start_step_logger(5)
            self._raid_util.delete_raid(raid_level=raid_level, non_raid_disk=self.non_raid_disk_name)

            self._test_content_logger.end_step_logger(5, True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(U2NvmeStabilityILVSSRaidMode, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if U2NvmeStabilityILVSSRaidMode.main() else Framework.TEST_RESULT_FAIL)
