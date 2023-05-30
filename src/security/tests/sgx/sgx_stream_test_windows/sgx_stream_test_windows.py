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
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.security.tests.sgx.sgx_enumeration_discovery.sgx_enumeration_discovery import SGXEnumerationDiscovery
from src.security.tests.sgx.sgx_platform_setup_windows.sgx_platform_setup_windows import SgxPlatformSetupWindows

from src.lib.dtaf_content_constants import TimeConstants
from src.provider.sgx_provider import SGXProvider
from src.lib import content_base_test_case
from src.lib.test_content_logger import TestContentLogger


class SgxStreamTestWindows(content_base_test_case.ContentBaseTestCase):
    """
    Phoenix Id : P18015174666-SGX Stream Test Windows
    This binary is built for default (from original C source file) array element size =40Million to run in Server A core
    Windows environment. Also, the loop count is set to 3000. Just one thread runs for approximately ~25 mins.
    This is the Windows version of Stream benchmark which runs in SGX environment.
    """

    TEST_CASE_ID = ["P18015174666", "SGX_Stream_Test_Windows"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Set SGX and MKTME Integrity Bios knobs',
            'expected_results': 'SGX and MKTME Integrity Bios knobs are set successfully'},
        2: {'step_details': 'Boot to OS, and install sgx stream app',
            'expected_results': 'Sgx stream app is installed successful'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SgxStreamTestWindows

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        self.sgx_enumeration_discovery = SGXEnumerationDiscovery(test_log, arguments, cfg_opts)
        self.sgx_platform_setup_windows = SgxPlatformSetupWindows(test_log, arguments, cfg_opts)
        super(SgxStreamTestWindows, self).__init__(test_log, arguments, cfg_opts)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        """
        preparing the setup:
        This method calls prepare and execute of sgx_enumeration_discovery and prepare of sgx_platform_setup_windows
        """
        self._test_content_logger.start_step_logger(1)
        self.sgx_enumeration_discovery.prepare()
        self.sgx_enumeration_discovery.execute()
        self.sgx_platform_setup_windows.execute()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Installing the sgx stream app by verifying the array size , total memory, and kernel loop count.

        :return: True if test completed successfully, False otherwise
        """
        self._test_content_logger.start_step_logger(2)
        self.sgx.load_sgx_properites()
        self.sgx.run_sgx_stream_app(int(self.sgx.SGX_STREAM_APP_TEST_TIMEOUT_IN_SECS))
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxStreamTestWindows.main() else Framework.TEST_RESULT_FAIL)
