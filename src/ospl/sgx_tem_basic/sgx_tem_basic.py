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

from src.provider.sgx_provider import SGXProvider
from src.lib import content_base_test_case


class SGXTEMBasic(content_base_test_case.ContentBaseTestCase):
    """
    HPALM ID : H80112-PI_SGX_TEM_BasicTest_L
    Glasgow ID : G59448.9 - SGX Platform Setup - RHEL8.0_Intel-Next/DCAP Driver
    Enable SGX and check sgx_app test results and all tests should be passed
    LD_LIBRARY_PATH=./ ./sgx_app -auto  (test result would be saved in a file named 'TestResult.csv')
    """
    BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"
    TEST_CASE_ID = ["H80112", "PI_SGX_TEM_BasicTest_L", "G59448.9", "SGX_Platform_Setup_RHEL8.0_Intel_Next_DCAP_Driver"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXTEMBasic

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE)

        super(SGXTEMBasic, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path=bios_config_file)
        self._log.debug("Bios config file: %s", bios_config_file)
        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.srp = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os,
                                       self.sdp)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(SGXTEMBasic, self).prepare()
        self._common_content_lib.update_micro_code()

    def execute(self):
        """Check for SGX app results"""
        self._log.info("SGX set successfully")
        self.sgx.check_sgx_enable()
        self.sgx.check_sgx_tem_base_test()
        self.sgx.execute_functional_validation_tool()
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(SGXTEMBasic, self).cleanup(return_status)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXTEMBasic.main() else
             Framework.TEST_RESULT_FAIL)
