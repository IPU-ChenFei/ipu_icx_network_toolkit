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
from src.security.tests.sgx.sgxi_cpuid_check.sgxi_cpuid_check import SgxiCpuidCheck

from src.provider.sgx_provider import SGXProvider
from src.lib import content_base_test_case
from src.lib.test_content_logger import TestContentLogger


class SgxiIntegrityEnumeration(content_base_test_case.ContentBaseTestCase):
    """
    Phoenix Id : P22012373367-SGXi-Integrity Enumeration
    Verify integrity has been enumerated correctly.
    """

    TEST_CASE_ID = ["P22012373367", "SGXi-Integrity Enumeration"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Set SGX and MKTME Integrity Bios knobs',
            'expected_results': 'SGX and MKTME Integrity Bios knobs are set successfully'},
        2: {'step_details': 'Boot to OS, and verify SGXi enumeration',
            'expected_results': 'SGXi enumeration verification is successful'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SgxiIntegrityEnumeration

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(SgxiIntegrityEnumeration, self).__init__(test_log, arguments, cfg_opts)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.sgx_cpuid_check = SgxiCpuidCheck(test_log, arguments, cfg_opts)

    def prepare(self):
        """
        preparing the setup:
        This method calls prepare and execute of Sgxi_Cpuid_Check
        """
        self._test_content_logger.start_step_logger(1)
        self.sgx_cpuid_check.prepare()
        self.sgx_cpuid_check.execute()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Checks SGXi enumeration by verifying the values of msr981 and msr982

        :return: True if test completed successfully, False otherwise
        """
        self._test_content_logger.start_step_logger(2)
        self.sgx.check_sgxi_sgx_enabled()
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxiIntegrityEnumeration.main() else Framework.TEST_RESULT_FAIL)
