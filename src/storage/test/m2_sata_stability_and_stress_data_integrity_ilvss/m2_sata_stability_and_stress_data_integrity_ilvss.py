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

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.stressapp_provider import StressAppTestProvider
from src.provider.vss_provider import VssProvider
from src.provider.memory_provider import MemoryProvider
from src.lib.install_collateral import InstallCollateral
from src.storage.test.storage_common import StorageCommon


class M2SataStabilityAndStressILVSS(StorageCommon):
    """
    Phoenix 16014320767, M.2 SATA-Stability and Stress- Data integrity - ILVSS, Pheonix ID : 18014075131

    Mount M.2 SATA and Run ilvss tool
    """

    TEST_CASE_ID = ["16014320767", "M.2 SATA-Stability and Stress- Data integrity - ILVSS"]
    PROCESS_NAME = "texec"
    LOG_NAME = "ilvss_log.log"

    step_data_dict = {1: {'step_details': 'To clear OS logs and load default bios settings ...',
                          'expected_results': 'Cleared OS logs and default bios settings done ...'},
                      2: {'step_details': 'Select package in ilVSS and run workload ',
                          'expected_results': 'No errors should be reported'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance M2SataStabilityAndStressILVSS

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        :raises: None
        """

        # calling base class init
        super(M2SataStabilityAndStressILVSS, self).__init__(test_log, arguments, cfg_opts)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._vss_provider_obj = VssProvider.factory(self._log, cfg_opts=cfg_opts, os_obj=self.os)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._command_timeout = self._common_content_configuration.get_command_timeout()

    def prepare(self):
        # type: () -> None
        """
        To clear OS logs and load default bios settings.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        super(M2SataStabilityAndStressILVSS, self).prepare()

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. Format the M.2 device
        2. Select package in ilVSS and run workload.

        :return: True, if the test case is successful.
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        m_2_device = self.get_m_2_device()
        self._log.info("m.2 device :{}".format(m_2_device))
        # To Format the device
        wipe_cmd = "wipefs {}".format(m_2_device)
        self.os.execute(wipe_cmd, self._command_timeout,self.ROOT_DIR)
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        mkfs_commad = "mkfs.ext4 -F {}".format(m_2_device)
        mount_point = "/mnt/QM-0"
        self._common_content_lib.execute_sut_cmd(mkfs_commad, "To make file system", self._command_timeout, self.ROOT_DIR)

        self._storage_provider.mount_the_drive(m_2_device, mount_point)

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

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=return_value)

        return return_value

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(M2SataStabilityAndStressILVSS, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if M2SataStabilityAndStressILVSS.main() else Framework.TEST_RESULT_FAIL)
