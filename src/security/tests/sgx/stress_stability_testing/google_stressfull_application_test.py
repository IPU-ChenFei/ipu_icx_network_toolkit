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
import re
import os

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import TimeConstants
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_base_test_case
from src.provider.stressapp_provider import StressAppTestProvider
from src.provider.sgx_provider import SGXProvider
from src.security.tests.sgx.sgx_enumeration_discovery.sgx_enumeration_discovery import SGXEnumerationDiscovery


class GoogleStressfullApplicationTest(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow Id : G63241.2 - Google_Stressfull_Application_Test

    Google Stressful Application Test (or stressapptest, its unix name) is a memory interface test.
    It tries to maximize randomized traffic to memory from processor and I/O, with the intent of creating a realistic
    high load situation in order to test the existing hardware devices in a computer.
    It has been used at Google for some time and now it is available under the apache 2.0 license
    """
    TEST_CASE_ID = ["G63241.2","Google_Stressfull_Application_Test"]
    STRESS_APP_EXECUTE_CMD = "./stressapptest -s {} -M 256 -m 18 -W -l stress.log "
    REGEX_FOR_STRESS_APP_STATUS = r'\sStatus:\sPASS\s+\S+.*'
    CLEAR_STRESS_LOG = "echo ''>{}"
    CMD_TO_GET_APP_STRESS_LOG = r"cat stress.log"
    STEP_DATA_DICT = {
        1: {'step_details': 'Enable SGX',
            'expected_results': 'Verified SGX enabled'},
        2: {'step_details': 'Copy semt app and Starts the workload: ./semt -S2 1024 1024 for 1 hour',
            'expected_results': 'Semt app workload completed successfully'},
        3: {'step_details': 'On SUT, Download & Install StressApptest abd Execute the StressAppTest',
            'expected_results': 'Successfully build the Google stressapptest, and test should return with:'
                                'Status: PASS'}}
    BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of GoogleStressfullApplicationTest

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(GoogleStressfullApplicationTest, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.timeout = TimeConstants.TEN_HOURS_IN_SEC

    def prepare(self):
        """
        preparing the setup:
        Enabling SGX
        """
        self._test_content_logger.start_step_logger(1)
        super(GoogleStressfullApplicationTest, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This method executes the below:
        1.Verifies SGX is enabled
        2.Copy and extract semt app
        3.Start the workload: ./semt -S2 1024 1024
        4.Install Stressapptest
        5.Execute Stressapptest and Verifies the status running in background
        return:
        """
        self._test_content_logger.start_step_logger(2)
        # Copy and extract semt app and starts workload
        self.sgx.is_sgx_enabled()
        self.sgx.run_semt_app(semt_timeout=None)
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._install_collateral.install_stress_test_app()

        self._stress_provider.execute_async_stress_tool((self.STRESS_APP_EXECUTE_CMD.format(self.timeout)), "stressapptest")
        self.sgx.verify_stress_tool_executing(self.timeout)
        self._test_content_logger.start_step_logger(3)
        command_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.CMD_TO_GET_APP_STRESS_LOG,
                                                                  cmd_str="App Stress Log",
                                                                  execute_timeout=self._command_timeout)
        self._log.debug("Stress Log Output: {}".format(command_output))
        stress_app_status = re.findall(self.REGEX_FOR_STRESS_APP_STATUS, command_output)
        if not stress_app_status:
            raise content_exceptions.TestFail('Stress App Test is Failed')
        self._log.info("Successfully Executed StressAppTest: {}".format(stress_app_status))
        self.sgx.kill_semt_app()
        self._test_content_logger.end_step_logger(3, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if GoogleStressfullApplicationTest.main() else Framework.TEST_RESULT_FAIL)
