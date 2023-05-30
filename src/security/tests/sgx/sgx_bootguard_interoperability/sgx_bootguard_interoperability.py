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
import os
import sys

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.lib import content_base_test_case
from src.lib.dtaf_content_constants import CbntConstants
from src.lib.test_content_logger import TestContentLogger
from src.provider.sgx_provider import SGXProvider
from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_common import BootGuardValidator
from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_profile5 import BootGuardProfile5


class SgxBootGuardInteroperability(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow ID : G59123.4-SGX_BootGuard_Interoperability

    To ensure that Boot Guard Profile 5 and SGX work together.
    """
    BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"
    TEST_CASE_ID = ["G59123.4", "SGX_BootGuard_Interoperability"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Enable SGX and verify in BIOS',
            'expected_results': 'SGX enabled and verified successfully'},
        2: {'step_details': 'Enable Boot Guard Profile 5',
            'expected_results': 'BootGuard Profile5 is enabled'},
        3: {'step_details': 'Again enable SGX after flashing BTG profile 5 and verify in BIOS',
            'expected_results': 'SGX enabled and verified successfully'},
        4: {'step_details': 'Run sgx_app by executing command "./sgx_app -auto" ',
            'expected_results': 'All 7 tests pass'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SgxBootGuardInteroperability

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE)
        super(SgxBootGuardInteroperability, self).__init__(test_log, arguments, cfg_opts,
                                                           bios_config_file_path=self.bios_config_file)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(self._log, cfg_opts, self.os, self.sdp)
        self._boot_guard_profile_5_obj = BootGuardProfile5(test_log, arguments, cfg_opts)
        self._boot_guard_obj = BootGuardValidator(test_log, arguments, cfg_opts)
        self._flash_obj = self._boot_guard_obj._flash_obj

    def prepare(self):
        # type: () -> None
        """preparing the setup by enabling sgx and verifying if sgx is enabled successfully"""
        self._test_content_logger.start_step_logger(1)
        super(SgxBootGuardInteroperability, self).prepare()
        # enable SGX and verify
        self.sgx.check_sgx_enable()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This method executes below:-
        1. Execute the Boot Guard Profile 5
        2. Enable SGX bios knobs after flashing BTG Profile 5
        3. Run sgx_app by executing command " ./sgx_app -auto"

        :return: True if the Test pass else False
        """
        self._test_content_logger.start_step_logger(2)
        # execute G58206 of BTG Profile 5
        self._boot_guard_profile_5_obj.execute()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        # enable SGX and verify
        self.bios_util.set_bios_knob(bios_config_file=self.bios_config_file)
        self.perform_graceful_g3()
        self.bios_util.verify_bios_knob(bios_config_file=self.bios_config_file)
        self.sgx.check_sgx_enable()
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        # run sgx app
        self.sgx.check_sgx_tem_base_test()
        self._test_content_logger.end_step_logger(4, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """Test Cleanup
        Restoring current IFWI"""
        current_ifwi_version = self._flash_obj.get_bios_version()
        if current_ifwi_version != self._boot_guard_obj.before_flash_bios_version:
            # flash current IFWI
            self._boot_guard_obj.flash_binary_image(CbntConstants.CURRENT_VERSION)
        super(SgxBootGuardInteroperability, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxBootGuardInteroperability.main()
             else Framework.TEST_RESULT_FAIL)
