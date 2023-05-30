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
import time

from src.lib.content_base_test_case import ContentBaseTestCase
from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.ras.lib.ras_einj_common import RasEinjCommon
from src.lib.test_content_logger import TestContentLogger


class UCMultiBitErrorLoggingAfterCEThresholdExceeded(ContentBaseTestCase):
    """
    Glasgow_id : G59743
    This test case verifies when the Correctable ECC error threshold event has occured on a DIMM prior to
    MBE error detection.

    """

    BIOS_CONFIG_FILE = "Uncorrectable_Multi_bit_Error_logging_after_CE_threshold_exceeded.cfg"
    TEST_CASE_ID = ["G59743", "Uncorrectable_Multi_bit_Error_logging_after_CE_threshold_exceeded"]
    TIME_DELAY = 10
    step_data_dict = {1: {'step_details': 'Set the bios knob and boot the system',
                          'expected_results': 'system should boot ..'},
                      2: {'step_details': 'Install Runner Tool',
                          'expected_results': 'Copying the Runner tool to SUT and installing it..'},
                      3: {'step_details': 'Preparing SUT for error Injection, Injects Failed Dimm CE OOB and'
                                          ' Verifies the Logs for Error Capturing',
                          'expected_results': 'Successfully injected CE and Captured error strings in Logs'},
                      4: {'step_details': 'Preparing SUT for error Injection, Injects Failed Dimm UCE OOB and'
                                          ' Verifies the Logs for Error Capturing',
                          'expected_results': 'Successfully injected UCE and Captured error strings in Logs'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UCMultiBitErrorLoggingAfterCEThresholdExceeded object

        :param test_log: Used for debug and info messages
        :param arguments: Arguments used in Baseclass
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UCMultiBitErrorLoggingAfterCEThresholdExceeded, self).__init__(test_log, arguments, cfg_opts,
                                                                     self.BIOS_CONFIG_FILE)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._einj_error = RasEinjCommon(self._log, self.os, self._common_content_lib,
                                         self._common_content_configuration,
                                         self.ac_power)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Setting the bios knobs to its default mode.
        3. Setting the bios knobs as per the test case.
        4. Rebooting the SUT to apply the new bios settings.
        5. Verifying the bios knobs that are set.
        6. Installs ras runner tool

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        super(UCMultiBitErrorLoggingAfterCEThresholdExceeded, self).prepare()
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        self._install_collateral.install_runner_tool()
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        This Method injects and verifies if Failed Dimm Isolation correctable memory OOB error is
        captured or not exceeding CE Threshold and then injects Failed Dimm Isolation uncorrectable memory OOB error.

        :return: Boolean(True/False)
        """
        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        # injects and verifies if os log captured Failed Dimm Isolation Einj correctable memory error.
        try:
            success = self._einj_error.einj_prepare_injection()
            if success:
                ce_error_injection_results = self._common_content_lib.execute_sut_cmd(
                    self._einj_error.RUNNER_EINJ_CE_ERROR_INJECT_CMD.format
                    (self._common_content_configuration.einj_runner_ce_addr()), "Injecting Runner Correctable error",
                    self._command_timeout, self._einj_error.RUNNER_EINJ_PATH)
                self._log.debug("Injected Ras runner CE error {}".format(ce_error_injection_results))
                if self._einj_error.CHECK_RUNNER_EXECUTION_STATUS not in ce_error_injection_results:
                    raise content_exceptions.TestFail("Failed to inject runner Correctable Error")
                else:
                    self._log.info("Successfully Injected Runner Correctable Error")
            else:
                raise content_exceptions.TestFail("There is some issue while enabling the Einj Module")
        except Exception as ex:
            log_error = "An Exception occured: {}".format(str(ex))
            self._log.error(log_error)
        time.sleep(self.TIME_DELAY)
        #  Verify the logs in OS
        os_error_log_found = self._einj_error._os_log_verify.verify_os_log_error_messages(
            __file__, self._einj_error._os_log_verify.DUT_MESSAGES_FILE_NAME, self._einj_error.
                error_injection_list("correctable_oob"))

        if not os_error_log_found:
            raise content_exceptions.TestFail("Expected signature was not captured in OS Log")
        self._log.info("Expected Error Signature was captured in OS")
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)
        # injects and verifies if os log captured Failed Dimm Isolation Einj uncorrectable memory error.
        try:
            success = self._einj_error.einj_prepare_injection()
            if success:
                uce_error_injection_results = self._common_content_lib.execute_sut_cmd(
                    self._einj_error.RUNNER_EINJ_UCE_ERROR_INJECT_CMD.format
                    (self._common_content_configuration.einj_runner_uce_addr()), "Injecting Runner UnCorrectable error",
                    self._command_timeout, self._einj_error.RUNNER_EINJ_PATH)
                self._log.debug("Injected Ras runner UCE error {}".format(uce_error_injection_results))
                if self._einj_error.CHECK_RUNNER_EXECUTION_STATUS not in uce_error_injection_results:
                    raise content_exceptions.TestFail("Failed to inject runner UnCorrectable Error")
                else:
                    self._log.info("Successfully Injected Runner UnCorrectable Error")
            else:
                raise content_exceptions.TestFail("There is some issue while enabling the Einj Module")
        except Exception as ex:
            log_error = "An Exception occured: {}".format(str(ex))
            self._log.error(log_error)
        time.sleep(self.TIME_DELAY)
        #  Verify the logs in OS
        os_error_log_found = self._einj_error._os_log_verify.verify_os_log_error_messages(
            __file__, self._einj_error._os_log_verify.DUT_MESSAGES_FILE_NAME, self._einj_error.
                error_injection_list("uncorrectable_oob"))

        if not os_error_log_found:
            raise content_exceptions.TestFail("Expected signature was not captured in OS Log")
        self._log.info("Expected Error Signature was captured in OS")
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(4, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if UCMultiBitErrorLoggingAfterCEThresholdExceeded.main() else Framework.TEST_RESULT_FAIL)
