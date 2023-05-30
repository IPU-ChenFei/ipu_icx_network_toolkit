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
from src.lib.dtaf_content_constants import TimeConstants
from src.security.tests.sgx.sgx_constant import SGXConstant
from src.security.tests.sgx.sgx_prmrr_size.sgx_prmrr_size_2g.sgx_prm_size_2g import SgxPrmSize2G


class SgxiInitializeSgxMemory(content_base_test_case.ContentBaseTestCase):
    """
    Phoenix Id : P22012373646-SGXi-initialize_Sgx_memory
    Ucode would have initialized integrity metadata with MOVDIR64B instruction. Outside the enclave we cant read EPC memory. We can run a
    sample SGX app with huge heap covering the entire EPC memory and launch it.  Within the application allocate as much heap as possible
    and attempt to partial read then partial write, look for any errors.   If the integrity bits have not been initialized by the uCode,
    then we will get a machine check exception.".
    """
    BIOS_CONFIG_FILE = "../sgx_prmrr_size/sgx_prmrr_size_2g/sgx_prm_size_2g.cfg"
    TEST_CASE_ID = ["P22012373646", "SGXi-initialize_Sgx_memory"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Set 2G and SGX Bios knobs',
            'expected_results': '2G and SGX Bios knobs are set successfully'},
        2: {'step_details': 'Boot to OS, and verify SGXi enumeration',
            'expected_results': 'SGXi enumeration verification is successful'},
        3: {'step_details': 'Modify the Enclave.config.xml file and run the Semt App command & verify the allocated'
            'memory',
            'expected_results': 'Enclave.config.xml file modified and SEMT App ran succssfully & allocated memory '
                                'verified'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SgxiInitializeSgxMemory

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        bios_2g_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        self.bios_config_file = SGXConstant(test_log).sgx_bios_knobs(bios_2g_config_file)
        super(SgxiInitializeSgxMemory, self).__init__(test_log, arguments, cfg_opts, self.bios_config_file)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        """
        preparing the setup:
        Set 2G and SGX Bios knobs
        Checks SGXi enumeration by verifying the values of cpuid - eax, ebx, ecx and edx
        """

        self._test_content_logger.start_step_logger(1)
        super(SgxiInitializeSgxMemory,self).prepare()
        self._log.info("2G and SGX BIOS knobs are set successfully")
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self.sgx.check_sgxi_enumeration()
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        Verifying the allocated memory by modifying the Enclave.config.xml & running the SEMT App cmd

        :return: True if test completed successfully, False otherwise
        """
        self._test_content_logger.start_step_logger(3)
        self.sgx.run_semt_app_sgxi(semt_timeout=TimeConstants.TEN_HOURS_IN_SEC)
        self.sgx.check_sgxi_sgx_enabled()
        self._test_content_logger.end_step_logger(3, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxiInitializeSgxMemory.main() else Framework.TEST_RESULT_FAIL)
