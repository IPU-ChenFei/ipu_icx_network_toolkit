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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.power_management.lib.reset_base_test import ResetBaseTest
from src.provider.sgx_provider import SGXProvider
from src.lib import content_base_test_case
from src.security.tests.sgx.sgx_enable_through_bios.sgx_enable_through_bios import SGXEnableThroughBios


class SgxStabilityAfterResetFlow(content_base_test_case.ContentBaseTestCase):
    """
    HPQC ID : H90203-PI_Security_SGX_stability_after_reset_flows_L

    Enable SGX, Perform 50 warm reboot cycles from the OS and Verify SGX enabled through bios
    Perform 50 cold reboot cycles from the OS  and Verify SGX enabled through bios
    Verifies data sealing/unsealing across S5 reboot
    Verifies data sealing/unsealing across S5 shutdown
    Hardware
    Server should be configured with 2S configuration

    Software
    Navigate to EDKII Menu/Socket Configuration/Processor Configuration
    Verify Total Memory Encryption (TME) option is exposed in the BIOS
    EDKII->Socket Configuration->Processor Configuration->Total Memory Encryption (TME) = Enable
    Verify SGX (SW Guard Extensions) option is exposed in the BIOS
    EDKII->Socket Configuration->Processor Configuration->SW Guard Extensions (SGX) = Enable
    Save (F10). Reset at the top of BIOS menu. Wait till BIOS reboot
    """
    TEST_CASE_ID = ["H90203", "PI_Security_SGX_stability_after_reset_flows_L"]
    SOCKET0 = 0
    SOCKET1 = 1

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SgxStabilityAfterResetFlow

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SgxStabilityAfterResetFlow, self).__init__(test_log, arguments, cfg_opts)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self._sgx_provider = SGXProvider.factory(self._log, cfg_opts, self.os, self._sdp)
        self._sgx_enable_obj = SGXEnableThroughBios(test_log, arguments, cfg_opts)
        self._reset_obj = ResetBaseTest(test_log, arguments, cfg_opts)
        self._reboot_iteration = self._common_content_configuration.get_reboot_iteration()

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        # Executing the TC G58854 prepare function
        self._sgx_enable_obj.prepare()

    def execute(self):
        """
        This test case executes following:
        Enable SGX, Perform warm reboot cycles from the OS and Verify SGX enabled through bios
        Perform cold reboot cycles from the OS  and Verify SGX enabled through bios
        Verifies data sealing/unsealing across S5 reboot
        Verifies data sealing/unsealing across S5 shutdown

        :return: True if test case pass
        """
        # Executing the TC G58854 Execute function
        self._sgx_enable_obj.execute()
        self._log.info("Perform warm reset")
        for iteration in range(self._reboot_iteration):
            self._log.debug("Iteration {} to perform warm reset".format(iteration + 1))
            self._reset_obj.warm_reset()
        self._sgx_provider.check_sgx_enable()  # Check SGX is enabled
        self._log.info("SGX capability is supported after warm reset")
        self._log.info("Perform cold reset")
        for iteration in range(self._reboot_iteration):
            self._log.debug("Iteration {} to perform cold reset".format(iteration + 1))
            self._reset_obj.graceful_s5()
        self._sgx_provider.check_sgx_enable()  # Check SGX is enabled
        self._sgx_provider.install_requirements()
        self._log.info("SGX capability is supported after cold reset")
        self._sgx_provider.perform_s5_reboot_test(self.SOCKET0)  # Perform s5 reboot test on socket 0
        self._sgx_provider.perform_s5_reboot_test(self.SOCKET1)  # Perform s5 reboot test on socket 1
        self._sgx_provider.verify_seal_unseal_reboot_test()  # verify S5 reboot sealing/unsealing test is success
        self._sgx_provider.perform_s5_shutdown_test(self.SOCKET0)  # Perform s5 shutdown test on socket 0
        self._sgx_provider.perform_s5_shutdown_test(self.SOCKET1)  # Perform s5 shutdown test on socket 1
        self._sgx_provider.verify_seal_unseal_shutdown_test()  # verify S5 shutdown sealing/unsealing test is success
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(SgxStabilityAfterResetFlow, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxStabilityAfterResetFlow.main()
             else Framework.TEST_RESULT_FAIL)
