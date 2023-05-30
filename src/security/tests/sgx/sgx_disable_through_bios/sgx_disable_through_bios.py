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


class SGXDisableThroughBios(content_base_test_case.ContentBaseTestCase):
    """
    HPQC ID : H80101-PI_Security_SGX_Disable_SGX_L/H81529-PI_Security_SGX_Disable_SGX_W
    GLASGOW ID : G59455.2-Disable SGX
    Verify SGX Knob disable using ITP/cpuid tool
    """
    SGX_ENABLE_BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"
    SGX_DISABLE_BIOS_CONFIG_FILE = "../sgx_disable_through_bios.cfg"
    TEST_CASE_ID = ["H80101", "PI_Security_SGX_Disable_SGX_L", "G59455.2", "Disable SGX", "81529",
                    "PI_Security_SGX_Disable_SGX_W"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXDisableThroughBios

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.enable_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    self.SGX_ENABLE_BIOS_CONFIG_FILE)
        self.disable_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                     self.SGX_DISABLE_BIOS_CONFIG_FILE)
        super(SGXDisableThroughBios, self).__init__(test_log, arguments, cfg_opts,
                                                    bios_config_file_path=self.enable_bios_config_file)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx_provider = SGXProvider.factory(self._log, cfg_opts, self.os, self.sdp)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(SGXDisableThroughBios, self).prepare()
        if not self.sgx_provider.is_sgx_enabled():
            raise content_exceptions.TestFail("SGX is not enabled")
        self._log.info("SGX set successfully")

    def disable_sgx(self):
        """
        This function disable the sgx bios knob
        """
        self._log.info("Setting required bios settings")
        self.bios_util.set_bios_knob(bios_config_file=self.disable_bios_config_file)
        self.perform_graceful_g3()
        self._log.info("Verifying bios settings")
        self.bios_util.verify_bios_knob(bios_config_file=self.disable_bios_config_file)

    def execute(self):
        """
        This function call disable sgx and verify it is disable in ITP and cpuid tool.

        :return True if sgx disabled successfully  else false
        """
        # Disable sgx bios knob
        self._log.info("Disable SGX Bios Knob")
        self.disable_sgx()
        if not self.sgx_provider.is_sgx_disabled():
            raise content_exceptions.TestFail("SGX is not disabled")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXDisableThroughBios.main() else Framework.TEST_RESULT_FAIL)
