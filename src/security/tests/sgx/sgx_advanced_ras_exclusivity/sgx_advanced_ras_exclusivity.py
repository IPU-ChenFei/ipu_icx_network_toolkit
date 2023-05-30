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
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.provider_factory import ProviderFactory

from src.provider.sgx_provider import SGXProvider
from src.lib.test_content_logger import TestContentLogger
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions


class SGXAdvancedRASExclusivity(ContentBaseTestCase):
    """
    Glasgow ID : G59241.2-Advanced_RAS_Exclusivity
    Verify inability to enable SGX after enabling an advanced RAS feature in BIOS setup
    """

    BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"
    TEST_CASE_ID = ["G59241.2", "Advanced_RAS_Exclusivity"]
    STEP_DATA_DICT = {
        1: {'step_details': 'EDKII->Socket Configuration->Processor Configuration->'
                            'Total Memory Encryption/SW Guard Extensions (SGX) (TME) = Enable',
            'expected_results': 'TME and SGX should be enabled in the BIOS.'},
        2: {'step_details': 'Verify if SGX is enabled over advanced ras.',
            'expected_results': 'SGX should be enabled over advanced ras.'}
        }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXEnableThroughBios

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        enable_sgx_tme_bios = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  self.BIOS_CONFIG_FILE)
        super(SGXAdvancedRASExclusivity, self).__init__(test_log, arguments,cfg_opts,
                                 bios_config_file_path=enable_sgx_tme_bios)
        self._log.debug("Bios config file: %s", enable_sgx_tme_bios)
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx_provider = SGXProvider.factory(self._log, cfg_opts, self.os, self.sdp)

    def prepare(self):
        # type: () -> None
        """preparing the setup and setting knobs"""
        super(SGXAdvancedRASExclusivity, self).prepare()

    def execute(self):
        """
        This method executes the following steps:
        1. Verifying if sgx is enabled over advanced ras
        2. checking the bit value for msr

        :raise: content exception if TME or SGX knob is not enabled
        :return: True if Test case pass
        """
        self._test_content_logger.start_step_logger(2)
        self._log.info("Verifying if SGX is chosen over advanced ras" )
        if not self.sgx_provider.is_sgx_enabled_over_advanced_ras():
            raise content_exceptions.TestFail("SGX is not enabled over advanced ras.")
        self._log.info("SGX is enabled over advanced ras successfully.")
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXAdvancedRASExclusivity.main() else Framework.TEST_RESULT_FAIL)
