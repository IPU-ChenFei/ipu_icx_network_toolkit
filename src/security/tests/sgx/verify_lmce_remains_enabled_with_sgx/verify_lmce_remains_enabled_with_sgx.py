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
import os

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from src.provider.sgx_provider import SGXProvider
from src.lib import content_base_test_case, content_exceptions
from src.lib.test_content_logger import TestContentLogger


class VerifyLmceRemainsEnabledWithSgx(content_base_test_case.ContentBaseTestCase):
    """
    Phoenix Id : P18015104695-Verify LMCE remains enabled with SGX

    Read MSR (0xA3) and verify SGX_RAS_OPTIN is set With SGX enabled,
    read MSR (0x3A) and verify bit 20 is set to ensure LMCE is supported
    """
    BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"
    TEST_CASE_ID = ["P18015104695","Verify LMCE remains enabled with SGX"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Set SGX Bios knobs',
            'expected_results': 'SGX Bios knobs are set successfully'},
        2: {'step_details': 'Boot to OS with SGX enabled',
            'expected_results': 'SGX is enabled'},
        3: {'step_details': 'Read MSR (0xA3) and verify SGX_RAS_OPTIN is set',
            'expected_results': 'SGX_RAS_OPTIN is bit 0 is set'},
        4: {'step_details': 'Verify bit 20 is set to ensure LMCE is supported',
            'expected_results': 'LMCE is supported and bit 20 is set'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of VerifyLmceRemainsEnabledWithSgx

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)

        super(VerifyLmceRemainsEnabledWithSgx, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        """
        preparing the setup:
        Set SGX Bios knobs
        """
        self._test_content_logger.start_step_logger(1)
        super(VerifyLmceRemainsEnabledWithSgx, self).prepare()
        self._log.info("SGX BIOS knobs are set successfully")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This method executes the below:
        1.verifies SGX is enabled
        2.verifies SGX_RAS bit 0 is set
        3.verifies LMCE bit 20 is set

        :raise: TestFail if SGX is not enabled or SGX_RAS bit is not enabled or LMCE bit is not enabled
        :return: True if test completed successfully, False otherwise.
        """
        self.sgx.check_sgx_enable()
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._test_content_logger.start_step_logger(3)
        if not self.sgx.is_sgx_enabled_over_advanced_ras():
            raise content_exceptions.TestFail("SGX-RAS is not enabled")
        self._log.info("SGX-RAS is enabled")
        self._test_content_logger.end_step_logger(3, return_val=True)
        self._test_content_logger.start_step_logger(4)
        if not self.sgx.is_lmce_sgx_bit_set():
            raise content_exceptions.TestFail("LMCE is not enabled with SGX")
        self._log.info("LMCE is enabled with SGX")
        self._test_content_logger.end_step_logger(4, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyLmceRemainsEnabledWithSgx.main() else Framework.TEST_RESULT_FAIL)
