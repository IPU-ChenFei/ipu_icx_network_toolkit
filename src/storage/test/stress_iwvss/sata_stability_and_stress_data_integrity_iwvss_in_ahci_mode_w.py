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
from src.lib.dtaf_content_constants import VssMode, TimeConstants

from src.lib.test_content_logger import TestContentLogger
from src.provider.stressapp_provider import StressAppTestProvider
from src.provider.vss_provider import VssProvider
from src.lib.install_collateral import InstallCollateral
from src.storage.test.storage_common import StorageCommon


class SataStabilityAndStressDataIntegrityIwvssAhciMode(StorageCommon):
    """
    Phoenix 1509390638: SATA-Stability and Stress- Data integrity - IWVSS in AHCI Mode

    Starting the iwvss stress tool on the SATA SSD in AHCI mode.
    """
    TEST_CASE_ID = ["1509390638", "SATA-Stability and Stress- Data integrity - IWVSS in AHCI Mode"]
    LOG_NAME = "iwvss_log.log"

    step_data_dict = {1: {'step_details': 'Copy and install the iwvss tool.',
                          'expected_results': 'iwvss tool copied and installed successfully'},
                      2: {'step_details': 'Create simple volume for all the connected SATA SSD.',
                          'expected_results': 'Simple volume for all the connected SATA SSD created'},
                      3: {'step_details': 'Trigger the iwvss tool with S2 flow and save the logs for given time',
                          'expected_results': 'No errors should be reported'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance SataStabilityAndStressDataIntegrityIwvssAhciMode

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param  arguments: None
        :return: None
        :raises: None
        """
        # calling base class init
        super(SataStabilityAndStressDataIntegrityIwvssAhciMode, self).__init__(test_log, arguments, cfg_opts)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._vss_provider_obj = VssProvider.factory(self._log, cfg_opts=cfg_opts, os_obj=self.os)
        self._test_content_logger.start_step_logger(1)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        To clear OS logs and load default bios settings.

        :return: None
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        super(SataStabilityAndStressDataIntegrityIwvssAhciMode, self).prepare()
        self.format_drive_win("sata")

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        1.Select package in iwVSS and run workload for given time

        :return: True, if the test case is successful.
        """
        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        self._log.info("Executing the iwvss ...")
        # Execute iwvss configuration for stress
        self._vss_provider_obj.execute_vss_storage_test_package(flow_tree="S2")

        # wait for the VSS to complete
        self._vss_provider_obj.wait_for_vss_to_complete(VssMode.IWVSS_MODE)

        self._vss_provider_obj.terminating_process(VssMode.IWVSS_MODE)

        # Parsing iwvss log
        return_value = self._vss_provider_obj.verify_vss_logs(self.LOG_NAME)

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=return_value)

        return return_value

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(SataStabilityAndStressDataIntegrityIwvssAhciMode, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SataStabilityAndStressDataIntegrityIwvssAhciMode.main()
             else Framework.TEST_RESULT_FAIL)
