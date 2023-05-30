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
from src.security.tests.sgx.sgx_constant import SGXConstant


class LaunchControlPolicyUnlocked(content_base_test_case.ContentBaseTestCase):
    """
    Phoenix ID : P18014073510-Launch Control Policy - Unlocked
    The Flexible LCP feature give the OEM the ability to change the enclave signing keys, so only enclaves with
    the desired keys will work.
    By default, the LE keys are Intel's keys.

    When the LCP is unlocked, it means that enclave created does not have Intel signature and you can change the keys
    The default mode is unlocked mode - There is a BIOS knob: SGXLEPUBKEYHASHx Write Enable which by default is set to
    enable, thus causing MSR_IA32_FEATURE_CONTROL.LeWr = 1 which makes the SGX_LE_PUBKEYHASH writeable
    """
    BIOS_CONFIG_FILE = "launch_control_policy_unlocked.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of FlexibleLaunchControlPolicyUnlocked

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        self.bios_config_file = SGXConstant(test_log).sgx_bios_knobs(bios_config_file)
        super(LaunchControlPolicyUnlocked, self).__init__(test_log, arguments, cfg_opts,
                                                          bios_config_file_path=self.bios_config_file)
        self._log.debug("Bios config file: {}".format(bios_config_file))
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(LaunchControlPolicyUnlocked, self).prepare()

    def execute(self):
        """verify for lcp unlock mode"""
        self._log.info("SGX set successfully")
        self.sgx.verify_lcp_unlocked_mode()
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LaunchControlPolicyUnlocked.main() else Framework.TEST_RESULT_FAIL)
