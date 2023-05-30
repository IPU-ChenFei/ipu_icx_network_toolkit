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
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger


class SGXSvnMsr(content_base_test_case.ContentBaseTestCase):
    """
    Phoenix ID : P18015174692
    SGX SVN of the uCode applied at CPU Reset
    Verify BIOS_SE_CPUSVN MSR (0x302) reports SGX SVN of the uCode applied at CPU reset- Patch-at-reset SVN is byte 0
    """
    SGX_ENABLE_BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"
    TEST_CASE_ID = ["P18015174692", "SGX SVN of the uCode applied at CPU Reset"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Enable SGX and verify in BIOS ',
            'expected_results': 'SGX has been  enabled successfully'},
        2: {'step_details': 'Check msr(0X302) value in SGX ',
            'expected_results': 'msr(0X302) value checked'}
            }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXSvnMsr

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.enable_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    self.SGX_ENABLE_BIOS_CONFIG_FILE)
        super(SGXSvnMsr, self).__init__(test_log, arguments, cfg_opts,
                                                    bios_config_file_path=self.enable_bios_config_file)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx_provider = SGXProvider.factory(self._log, cfg_opts, self.os, self.sdp)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        self._test_content_logger.start_step_logger(1)
        super(SGXSvnMsr, self).prepare()
        self._log.info("NUMA, TME, SGX, UMA has been set in bios")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This function call check_msr_svn_enabled and check msr(0x302) reports SGX SVN of the uCode applied
        at CPU reset- Patch-at-reset SVN.
        1. Verify the MSR value for SVN

        :return: True if MSR SVN enabled successfully  else false
        :raise: content_exceptions.TestFail - if failed.
        """
        self._test_content_logger.start_step_logger(2)
        self.sgx_provider.check_sgx_enable()
        self._log.info("SGX set successfully")
        if not self.sgx_provider.check_msr_svn_enabled():
            raise content_exceptions.TestFail("SVN Patch-at-Reset for the msr (302) is not set")
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXSvnMsr.main() else Framework.TEST_RESULT_FAIL)
