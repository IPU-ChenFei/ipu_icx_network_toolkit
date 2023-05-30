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
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.test_content_logger import TestContentLogger
from src.provider.sgx_provider import SGXProvider
from src.lib import content_base_test_case
from src.security.tests.sgx.sgx_constant import SGXConstant


class FlexibleLaunchControlPolicyLocked(content_base_test_case.ContentBaseTestCase):
    """
    Phoenix ID : P18014072829-Launch Control Policy - Locked
    Glasgow ID : G58717.8-Flexible Launch Control Policy - Locked
    IA32_FEATURE_CONTROL MSR there is a bit called SGX Launch Control Enable that allows to change the
    IA32_SGXLEPUBKEYHASHn values. By default the hash is the SHA-256 hash of Intel public key.
    By default, the LE keys are Intel's keys:
    IA32_SGXLEPUBKEYHASH0 (0x8C)  0xA6053E051270B7AC
    IA32_SGXLEPUBKEYHASH1 (0x8D)  0x6CFBE8BA8B3B413D
    IA32_SGXLEPUBKEYHASH2 (0x8E)  0xC4916D99F2B3735D
    IA32_SGXLEPUBKEYHASH3 (0x8F)  0xD4F8C05909F9BB3B
    The default mode is unlocked mode.  To enable locked mode, there is a BIOS knob: SGXLEPUBKEYHASHx Write Enable
    which needs to be set to disable, thus causing MSR_IA32_FEATURE_CONTROL.LeWr = 0 which makes the SGX_LE_PUBKEYHASH
    read-only
    When the LCP is locked i.e. using Intel signature and LE_WR is off (by setting the lock bit
    IA32_FEATURE_CONTROL.LOCK - 0x3A bit 0 and) and LE_WR is 0  in IA32_FEATURE_CONTROL.LE_WR (0x3A bit 17)) you cannot
    change the keys (#GP on WRMSR)
    """
    BIOS_CONFIG_FILE = "flexible_launch_control_policy_locked.cfg"
    TEST_CASE_ID = ["G58717.8", "Flexible_Launch_Control_Policy_Locked"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Enable SGX and verify in BIOS',
            'expected_results': 'SGX enabled and verified successfully'},
        2: {'step_details': 'Run the command SGXFunctionalValidation -l -v -skip_power_tests -lcp_legacy_locked and'
                            'verify the output for LCP Legacy Lock mode',
            'expected_results': 'LCP Locked output is verified successfully'}
        }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of FlexibleLaunchControlPolicyLocked

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        self.bios_config_file = SGXConstant(test_log).sgx_bios_knobs(bios_config_file)
        super(FlexibleLaunchControlPolicyLocked, self).__init__(test_log, arguments, cfg_opts,
                                                                bios_config_file_path=self.bios_config_file)
        self._log.debug("Bios config file: {}".format(bios_config_file))
        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.srp = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        self._test_content_logger.start_step_logger(1)
        super(FlexibleLaunchControlPolicyLocked, self).prepare()
        self._log.info("SGX set successfully")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Verify LCP locked mode

        :return: True if Test case pass else False
        """
        self._test_content_logger.start_step_logger(2)
        self.sgx.verify_lcp_locked_mode()
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if FlexibleLaunchControlPolicyLocked.main() else Framework.TEST_RESULT_FAIL)
