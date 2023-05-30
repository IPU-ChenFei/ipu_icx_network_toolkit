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

from src.lib import content_base_test_case
from src.lib.test_content_logger import TestContentLogger
from src.provider.sgx_provider import SGXProvider
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot
from src.security.tests.sgx.sgx_constant import SGXConstant

class VerifySgxAndTxt(content_base_test_case.ContentBaseTestCase):
    """
    Phoenix ID : P18014073330-Verify on a TXT enabled system that SGX works as expected

    Verify SGX and TXT work together.
    """
    TEST_CASE_ID = ["P18014073330", "Verify on a TXT enabled system that SGX works as expected"]
    STEP_DATA_DICT = {1: {'step_details': 'Enable the Bios knobs for SGX, TXT, and comparing the lsmem/lscpu/lspci'
                                          'pre-tboot and post tboot',
                          'expected_results': 'SGX and TXT knobs are enabled and Pre-tboot and post tboot lsmem/lscpu'
                                              '/lspci result are same'},
                      2: {'step_details': 'Running SGX_APP',
                          'expected_results': 'SGX_APP ran successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of VerifySgxAndTxt

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.bios_config_file = SGXConstant(test_log).sgx_bios_knobs()
        super(VerifySgxAndTxt, self).__init__(test_log, arguments, cfg_opts, self.bios_config_file)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.TrustedBootWithTboot = TrustedBootWithTboot(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        This method executes the following steps:
        1. preparing the setup and setting knobs
        2. Enable and verify Sgx
        3. Enable and verify TXT
        """
        self._test_content_logger.start_step_logger(1)
        super(VerifySgxAndTxt, self).prepare()
        self.sgx.check_sgx_enable()
        self.TrustedBootWithTboot.prepare()
        self.TrustedBootWithTboot.execute()
        self._test_content_logger.end_step_logger(1, return_val=True)


    def execute(self):
        """
        This method is used to run the Sgx_app and verify SGX and TXT work together

        :return: True if Test case pass
        """
        self._test_content_logger.start_step_logger(2)
        self.sgx.load_sgx_properites()
        self.sgx.run_sgx_app_test()
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifySgxAndTxt.main() else
             Framework.TEST_RESULT_FAIL)
