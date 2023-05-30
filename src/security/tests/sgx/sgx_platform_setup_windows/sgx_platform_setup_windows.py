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
from src.security.tests.sgx.sgx_constant import SGXConstant


class SgxPlatformSetupWindows(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow Id : G62238.1-Sgx_Platform_Setup_Windows
    Platform Setup Requirements to enable SGX testing on ICX LCC Windows Server Core.
    """
    TEST_CASE_ID = ["G62238.1", "Sgx_Platform_Setup_Windows"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Enable SGX bios knobs',
            'expected_results': 'SGX Bios knobs are enabled successfully'},
        2: {'step_details': 'Copy the SGX PSW and SGX registration agent package and install it',
            'expected_results': 'SGX Base, SGX PSW and SGX registration agent software are installed successfully'}
                     }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SgxPlatformSetupWindows

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        self.bios_config_file = SGXConstant(test_log).sgx_bios_knobs()
        super(SgxPlatformSetupWindows, self).__init__(test_log, arguments, cfg_opts, self.bios_config_file)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        """
        preparing the setup:
        Enable SGX Bios knobs
        """
        self._test_content_logger.start_step_logger(1)
        super(SgxPlatformSetupWindows,self).prepare()
        self._log.info("SGX BIOS knobs are set successfully")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Verifying the SGX knobs and installing the SGX Base SGX PSW and SGX Registration Agent.
        :return: True if test installed successfully, False otherwise
        """
        self._test_content_logger.start_step_logger(2)
        self._log.info("SGX set successfully")
        self.sgx.check_sgx_enable()
        self.sgx.check_sgx_base_installation()
        self.sgx.check_psw_installation()
        self.sgx.check_mp_registration_installation()
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxPlatformSetupWindows.main() else Framework.TEST_RESULT_FAIL)
