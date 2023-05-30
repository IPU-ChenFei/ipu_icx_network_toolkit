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
from src.lib import content_exceptions

from src.lib.test_content_logger import TestContentLogger
from src.provider.stressapp_provider import StressAppTestProvider
from src.provider.vss_provider import VssProvider
from src.lib.install_collateral import InstallCollateral
from src.storage.test.storage_common import StorageCommon


class U2NvmeStabilityAndStressILVSS(StorageCommon):
    """
    Phoenix 16013945391, U.2NVME-Stability and Stress- Data integrity - ILVSS in VMD Disabled mode

    Mount U.2 NVMe and Run ilvss tool
    """

    TEST_CASE_ID = ["16013945391", "U2_NVME_Stability_and_Stress_Data_integrity_ILVSS_in_VMD_Disabled_mode"]
    PROCESS_NAME = "texec"
    LOG_NAME = "ilvss_log.log"
    MKFS_COMMAD = "mkfs.ext4 -F {}"
    MOUNT_POINT = "/mnt/QM-0"
    WIPE_CMD = "wipefs {}"
    CMD_TO_GET_NVM_DISK = r"nvme list | egrep /dev/nvme"

    step_data_dict = {1: {'step_details': 'To clear OS logs and load default bios settings ...',
                          'expected_results': 'Cleared OS logs and default bios settings done ...'},
                      2: {'step_details': 'Format and mount u.2 devices',
                          'expected_results': 'Formatted and mounted U.2 devices ...'},
                      3: {'step_details': 'Select package in ilVSS and run workload ',
                          'expected_results': 'No errors should be reported ...'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance U2NvmeStabilityAndStressILVSS

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        :raises: None
        """

        # calling base class init
        super(U2NvmeStabilityAndStressILVSS, self).__init__(test_log, arguments, cfg_opts)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._vss_provider_obj = VssProvider.factory(self._log, cfg_opts=cfg_opts, os_obj=self.os)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        To clear OS logs and load default bios settings.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        super(U2NvmeStabilityAndStressILVSS, self).prepare()

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. Format the U.2 device and Mount the U.2 devices
        2. Select package in ilVSS and run workload.

        :return: True, if the test case is successful.
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        cmd_res = self._common_content_lib.execute_sut_cmd(self.CMD_TO_GET_NVM_DISK, "cmd", self._command_timeout)
        nvme_list = []
        for each in cmd_res.split("\n"):
            nvme_list.append(re.findall(r"/dev/nvme\dn\d", each))

        nvme_devices = self._common_content_lib.list_flattening(nvme_list)
        self._log.info("NVME devices list : {}".format(nvme_devices))
        if not nvme_devices:
            raise content_exceptions.TestFail("Please check NVMe connected or not in SUT  ...")

        # To Format the device
        for each_nvme in nvme_devices:
            wipe_device = self.WIPE_CMD.format(each_nvme)
            self.os.execute(wipe_device, self._command_timeout, self.ROOT_DIR)
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)

        # To make a File system
        for index in range(0, len(nvme_devices)):
            mkfs_commad = self.MKFS_COMMAD.format(nvme_devices[index])
            mount_point = "/mnt/QM-{}".format(index)
            self.os.execute("umount {}".format(nvme_devices[index]), self._command_timeout)
            self._common_content_lib.execute_sut_cmd(mkfs_commad, "To make file system", self._command_timeout,
                                                     self.ROOT_DIR)

            self._storage_provider.mount_the_drive(nvme_devices[index], mount_point)

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

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
        return_value = self._vss_provider_obj.verify_vss_logs(self.LOG_NAME)

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=return_value)

        return return_value

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(U2NvmeStabilityAndStressILVSS, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if U2NvmeStabilityAndStressILVSS.main() else Framework.TEST_RESULT_FAIL)
