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
from src.lib import content_base_test_case
from src.lib.test_content_logger import TestContentLogger


class SgxiCpuidCheck(content_base_test_case.ContentBaseTestCase):
    """
    Phoenix Id : P22012457880-SGXi-CPUID Check
    CPUID.SGX_LEAF subleaf n > 1. EDX:ECX bits 3:0 will enumerate TMEi-protected SGX memory as 0x3 -
    Confidentiality and Integrity Protected".
    """
    BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"
    TEST_CASE_ID = ["P22012457880", "SGX-CPUID Check"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Set SGX Bios knobs',
            'expected_results': 'SGX Bios knobs are set successfully'},
        2: {'step_details': 'Boot to OS, and verify SGXi enumeration',
            'expected_results': 'SGXi enumeration verification is successful'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SgxiCpuidCheck

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(SgxiCpuidCheck, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
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
        super(SgxiCpuidCheck, self).prepare()
        self._log.info("SGX BIOS knobs are set successfully")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Checks SGXi enumeration by verifying the values of cpuid - eax, ebx, ecx and edx

        :return: True if test completed successfully, False otherwise
        """
        self._test_content_logger.start_step_logger(2)
        self.sgx.check_sgxi_enumeration()
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxiCpuidCheck.main() else Framework.TEST_RESULT_FAIL)
