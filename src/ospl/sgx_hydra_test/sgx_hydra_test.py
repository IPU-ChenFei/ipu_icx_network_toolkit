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

from src.provider.sgx_provider import SGXProvider
from src.lib import content_base_test_case
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.sgx.sgx_enable_through_bios.sgx_enable_through_bios import SGXEnableThroughBios
from src.lib.dtaf_content_constants import TimeConstants


class SgxHydraTest(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow ID : G63262.1-SGXHydra_Test
    HPALM ID : H90201-PI_Security_SGX_stress_SGXhydra_L

    SGXHydra is an application that can be run on Linux to stress test SGX.
    The application allows the tester to create a number of OS threads which then simultaneously call into an enclave where
    enclave memory is updated and the results passed back out to the untrusted hosting application.
    Enclaves of various sizes can be created in order to attempt to consume all or most of the EPC available on the platform.
    """
    TEST_CASE_ID = ["G63262.1", "SGXHydra_Test", "H90201", "PI_Security_SGX_stress_SGXhydra_L"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Enable SGX and verify in BIOS',
            'expected_results': 'SGX enabled and verified successfully'},
        2: {'step_details': 'Install PSW, SDK and Hydra tool and run hydra tool for specific duration',
            'expected_results': 'Installation of PSW, SDK and Hydra tool is executed successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SgxHydraTest

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SgxHydraTest, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(self._log, cfg_opts, self.os, self.sdp)
        self._sgx_enable_obj = SGXEnableThroughBios(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """preparing the setup by enabling sgx and verifying if sgx is enabled successfully"""
        self._test_content_logger.start_step_logger(1)
        # Executing the TC 58854 prepare function
        self._sgx_enable_obj.prepare()
        self._common_content_lib.update_micro_code()
        # Executing the TC 58854 Execute function
        self._sgx_enable_obj.execute()
        self.sgx.check_sgx_enable()
        self._log.info("SGX set successfully")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This method installs PSW, sgx SDK and Hydra tool. Runs Hydra tool for specific duration.

        :return: True if the Test pass else False
        """
        self._test_content_logger.start_step_logger(2)
        self.sgx.run_hydra_test(TimeConstants.ONE_HOUR_IN_SEC)
        self._test_content_logger.end_step_logger(2, return_val=True)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxHydraTest.main()
             else Framework.TEST_RESULT_FAIL)
