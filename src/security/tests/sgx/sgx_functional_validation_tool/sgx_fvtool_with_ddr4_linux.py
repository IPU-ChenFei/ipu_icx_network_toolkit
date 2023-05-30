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
from src.provider.memory_provider import MemoryProvider


class SGXFunctionalValidationToolDDR4Linux(content_base_test_case.ContentBaseTestCase):
    """
    HPALM ID : H79545-PI_Security_SGX_FunctionalValidationTool_with_DDR4_L

    Verify SGX PSW Installed
    Hardware
    Serer should be configured with 2S configuration

    For Linux:
    After initial configuration setup, cd into the SGXFunctionalValidation directory and run the following command line
    (FVT test):
    ./SGXFunctionalValidation -l -v -skip_power_tests
    """
    BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"
    TEST_CASE_ID = ["H79545-PI_Security_SGX_FunctionalValidationTool_with_DDR4_L"]
    DDR4_MEMORY = "DDR4"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXFunctionalValidationToolDDR4Linux

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), self.BIOS_CONFIG_FILE)

        super(SGXFunctionalValidationToolDDR4Linux, self).__init__(
                test_log, arguments, cfg_opts,
                bios_config_file_path=bios_config_file)
        self._log.debug("Bios config file: %s", bios_config_file)
        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.srp = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os,
                                       self.sdp)
        self._memory_provider = MemoryProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self.os)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        # Set sgx knobs in bios
        super(SGXFunctionalValidationToolDDR4Linux, self).prepare()
        # Verify if systems all slots are populated with DDR4 memory
        self._memory_provider.verify_populated_memory_type(self.DDR4_MEMORY)

    def execute(self):
        """Check for SGX PSW Installation"""
        # Enables sgx
        self._log.info("Checks SGX set successfully")
        self.sgx.check_sgx_enable()
        # Installs psw and verifies if it is installed successfully
        self.sgx.check_psw_installation()
        # Verify sgx working as expected
        self.sgx.execute_functional_validation_tool()

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXFunctionalValidationToolDDR4Linux.main()
             else Framework.TEST_RESULT_FAIL)
