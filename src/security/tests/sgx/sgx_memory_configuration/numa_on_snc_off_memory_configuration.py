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
from src.lib.dtaf_content_constants import TimeConstants
from src.provider.sgx_provider import SGXProvider
from src.lib import content_base_test_case
from src.lib.test_content_logger import TestContentLogger


class SgxNumaOnSncOffMemoryConfiguration(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow Id : G59132.1-NUMA ON / SNC OFF Memory Configuration

    Verify the SGX memory range compatibility with NUMA ON and SNC OFF.
    Verifying system set-up of PRMRR regions with SGX enabled in memory configuration mode NUMA ON and SNC OFF
    """
    BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"
    SNC_CONFIG_FILE = "../sgx_numa_on_snc_off/sgx_numa_on_snc_off.cfg"
    TEST_CASE_ID = ["G59132.1", "NUMA ON / SNC OFF Memory Configuration"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Enable TME, SGX, NUMA and disable UMA-Based Clustering',
            'expected_results': 'Verified TME, SGX, NUMA enabled and UMA-Based Clustering disabled'},
        2: {'step_details': 'Verifies SNC is disabled and SGX is enabled',
            'expected_results': 'Verified SNC is disabled and SGX is enabled'},
        3: {'step_details': 'Copy semt app and Starts the workload: ./semt -S2 1024 1024 for 1 hour',
            'expected_results': 'Semt app workload completed successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SgxNumaOnSncOffMemoryConfiguration

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        self.bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        self.snc_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.SNC_CONFIG_FILE)
        super(SgxNumaOnSncOffMemoryConfiguration, self).__init__(test_log, arguments, cfg_opts, self.bios_config_file)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        """preparing the setup:
        enabling SGX and Numa and disabling UMA-Based Clustering option
        """
        self._test_content_logger.start_step_logger(1)
        super(SgxNumaOnSncOffMemoryConfiguration, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """This method executes the below:
        1.verifies SNC is disabled
        2.verifies SGX is enabled
        3.copies semt app and Starts the workload: ./semt -S2 1024 1024 for 1 hour

        :return: True if test completed successfully, False otherwise.
        """
        self._log.info("SGX bios knobs are set successfully")
        self._test_content_logger.start_step_logger(2)
        # Verifies SGX is enabled
        self.sgx.check_sgx_enable()
        # check SNC (Sub NUMA) is disabled
        self.bios_util.set_bios_knob(bios_config_file=self.snc_bios_config_file)
        self.perform_graceful_g3()
        self.bios_util.verify_bios_knob(bios_config_file=self.snc_bios_config_file)
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._test_content_logger.start_step_logger(3)
        # copy and extract semt app and starts workload
        self.sgx.run_semt_app(semt_timeout=TimeConstants.ONE_HOUR_IN_SEC)
        self._test_content_logger.end_step_logger(3, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxNumaOnSncOffMemoryConfiguration.main() else Framework.TEST_RESULT_FAIL)
