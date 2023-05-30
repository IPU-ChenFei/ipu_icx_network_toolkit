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


from src.provider.vss_provider import VssProvider
from src.storage.test.storage_common import StorageCommon
from src.lib.dtaf_content_constants import VssMode
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.provider.stressapp_provider import StressAppTestProvider
from src.storage.lib.storage_common import StorageCommon
from src.lib.test_content_logger import TestContentLogger



class SsdSataStabilityAndStressIWVSS(ContentBaseTestCase):
    """
    Phoenix 16013596706, SATA-3 GBPS Stress- IWVSS-use mix of all Models SATASSD(windows)

    Running iwvss tool for stress.
    """

    TEST_CASE_ID = ["16013596706", "SATASSD-Stability and Stress- Data integrity - IWVSS(windows)"]
    LOG_NAME = "iwvss_log.log"

    step_data_dict = {1: {'step_details': 'Check Sata device ...',
                          'expected_results': 'Sata device detected in SUT ...'},
                      2: {'step_details': 'Format and assign drive letter to  SATA SSD ...',
                          'expected_results': "Formatted and assigned drive letter to  SATA SSD ..."},
                      3: {'step_details': 'Create S2 package for iwvss ...',
                          'expected_results': 'S2 package created successfully...'},
                      4: {'step_details': 'Select package in iwVSS and run workload',
                          'expected_results': 'No errors should be reported'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance M2SataStabilityAndStressIWVSS

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        :raises: None
        """

        # calling base class init
        super(SsdSataStabilityAndStressIWVSS, self).__init__(test_log, arguments, cfg_opts)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._cfg_opts = cfg_opts
        self._vss_provider_obj = None
        self.storage_common_lib = StorageCommon(self._log, cfg_opts)
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

        # check SATA SSD
        disk_info = self._common_content_lib.execute_sut_cmd("wmic diskdrive list brief", "list disk drive",
                                                             self._command_timeout)
        self._log.info("Physical  Sata SSD show information...{}".format(disk_info))

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. Install windows OS.
        2. Format and assign drive letter to  SATA SSD.
        3. Select package in iWVSS and run workload for storage.

        :return: True, if the test case is successful.
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # formatting the sata drive without OS installed
        self.storage_common_lib.format_drive_win(device_type="SATA", booted_format_drive=False)

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        self._vss_provider_obj = VssProvider.factory(self._log, cfg_opts=self._cfg_opts, os_obj=self.os)
        self._log.info("Executing the iwvss ...")

        # Execute iwvss configuration for stress
        self._vss_provider_obj.execute_vss_storage_test_package(flow_tree="S2")

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        # wait for the VSS to complete
        self._vss_provider_obj.wait_for_vss_to_complete(VssMode.IWVSS_MODE)

        self._vss_provider_obj.terminating_process(VssMode.IWVSS_MODE)

        # Parsing iwvss log
        return_value = self._vss_provider_obj.verify_vss_logs(self.LOG_NAME)

        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=return_value)

        return return_value

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(SsdSataStabilityAndStressIWVSS, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SsdSataStabilityAndStressIWVSS.main() else Framework.TEST_RESULT_FAIL)
