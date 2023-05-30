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


class SealingAndUnsealingDataAcrossS5RebootBoundary(content_base_test_case.ContentBaseTestCase):
    """
    Phoenix ID : P18014072854 - Platform Power State Compatibility - Sealing  and Unsealing data across S5
                                reboot boundary
    Glasgow ID : G59083.3-Sealing  and Unsealing data across S5 reboot boundary
    Verifies data sealing/unsealing acroos S5 reboot
    """
    BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"
    TEST_CASE_ID = ["G59083.3", "Sealing and Unsealing data across S5 reboot boundary"]
    SOCKET0 = 0
    SOCKET1 = 1
    STEP_DATA_DICT = {
        1: {'step_details': 'Enable SGX and verify in BIOS',
            'expected_results': 'SGX enabled and verified successfully'},
        2: {'step_details': 'Set correct permission by running command sudo usermod -a -Groot aesmd',
            'expected_results': 'Permission command executed successfully'},
        3: {'step_details': 'Perform Reboot test for socket 0',
            'expected_results': 'Reboot test was successfully performed'},
        4: {'step_details': 'Set correct permission by running command sudo usermod -a -Groot aesmd',
            'expected_results': 'Permission command executed successfully'},
        5: {'step_details': 'Perform Reboot test for socket 1',
            'expected_results': 'Reboot test was successfully performed'},
        6: {'step_details': 'Set correct permission by running command sudo usermod -a -Groot aesmd',
            'expected_results': 'Permission command executed successfully'},
        7: {'step_details': 'Verify S5 reboot sealing/unsealing',
            'expected_results': 'S5 reboot sealing/unsealing verified successfully'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SealingAndUnsealingDataAcrossS5RebootBoundary

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(SealingAndUnsealingDataAcrossS5RebootBoundary, self).__init__(test_log, arguments, cfg_opts,
                                                                            bios_config_file_path=bios_config_file)
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
        super(SealingAndUnsealingDataAcrossS5RebootBoundary, self).prepare()
        self._log.info("SGX set successfully")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """Run Sealing And Unsealing Data Across S5 Reboot Boundary"""
        self._test_content_logger.start_step_logger(2)
        self.sgx.check_psw_installation()
        self._common_content_lib.execute_sut_cmd(self.sgx.AESM_RESTART_CMD, self.sgx.AESM_RESTART_CMD,
                                                 self.sgx.EXECUTION_TIMEOUT)
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._test_content_logger.start_step_logger(3)
        self.sgx.perform_s5_reboot_boundary(self.SOCKET0)
        self._test_content_logger.end_step_logger(3, return_val=True)
        self._test_content_logger.start_step_logger(4)
        self._common_content_lib.execute_sut_cmd(self.sgx.AESM_RESTART_CMD, self.sgx.AESM_RESTART_CMD,
                                                 self.sgx.EXECUTION_TIMEOUT)
        self._test_content_logger.end_step_logger(4, return_val=True)
        self._test_content_logger.start_step_logger(5)
        self.sgx.perform_s5_reboot_boundary(self.SOCKET1)
        self._test_content_logger.end_step_logger(5, return_val=True)
        self._test_content_logger.start_step_logger(6)
        self._common_content_lib.execute_sut_cmd(self.sgx.AESM_RESTART_CMD, self.sgx.AESM_RESTART_CMD,
                                                 self.sgx.EXECUTION_TIMEOUT)
        self._test_content_logger.end_step_logger(6, return_val=True)
        self._test_content_logger.start_step_logger(7)
        self.sgx.verify_seal_unseal_reboot_boundary()
        self._test_content_logger.end_step_logger(7, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SealingAndUnsealingDataAcrossS5RebootBoundary.main() else
             Framework.TEST_RESULT_FAIL)
