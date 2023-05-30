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
import time
import threading

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.provider.stressapp_provider import StressAppTestProvider
from src.memory_hbm.memory_hbm_common import MemoryHbmCommon
from src.memory.lib.memory_common_lib import MemoryCommonLib


class PiCacheSncCheckPrime95Windows(MemoryHbmCommon):
    """
    pheonix id : 16014744236 - PI_Memory_Cache_Mode_SNC_Mode_Prime95_W

    """

    TEST_CASE_ID = ["16014744236", "PI_Memory_Cache_Mode_SNC_Mode_Prime95_W"]
    SNC4_BIOS_CONFIG_FILE = "two_lm_snc4_bios_knob.cfg"
    _prime95_executer_path = None
    LIST_PROCESSES = ["prime95.exe"]
    return_value = []
    SNC4_EXPECTED_VALUE = "0xf"
    step_data_dict = {1: {'step_details': 'To verify SUT has 1DPC or 2DPC memory configuration and '
                                          'Load default bios, Set & verify SNC (Sub NUMA) bios knob to SNC4, '
                                          'Check ktilk_snc_config expected value is 0xf',
                          'expected_results': 'SUT has 1DPC or 2DPC memory configuration and Default bios knob setting,'
                                              ' SNC (Sub NUMA) bios knob to SNC4 set and '
                                              'verified and ktilk_snc_config expected value 0xf verified.'},
                      2: {'step_details': 'To Install Prime95 tool and Run Prime95 Tool for 2 hours',
                          'expected_results': 'Prime95 ran with out errors ...'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiCacheSncCheckPrime95Windows object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """

        self.snc4_bios_config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                       self.SNC4_BIOS_CONFIG_FILE)
        super(PiCacheSncCheckPrime95Windows, self).__init__(test_log, arguments, cfg_opts)
        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._install_collateral = InstallCollateral(test_log, self.os, cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._silicon_family = self._common_content_lib.get_platform_family()
        self._num_of_cycles = self._common_content_configuration.memory_number_of_cycle()
        self._memory_common_lib = MemoryCommonLib(self._log, cfg_opts, self.os, self._num_of_cycles)

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Reboot the SUT to apply the new bios settings.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._memory_provider.verify_1dpc_or_2dpc_memory_configuration()
        # need to put snc_check_with_pythonsv_values in common location src/memory/tests/memory_ddr/pi_memory_snc_check_stressapp_l.py
        self.snc_check_with_pythonsv_values(self.snc4_bios_config_file_path, self.SNC4_EXPECTED_VALUE)

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Set and verify SNC4 and verify PythonSv register value ktilk_snc_config
        2. run the Prime95 tool for 2 Hours.

        :return: True, if the test case is successful.
        :raise: TestFail
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # Execute the prime95 / update the prime.txt file with the configuration.
        prime95_thread = threading.Thread(target=self.execute_prime95_windows,
                                          args=("prime95.exe -t", self._prime95_executer_path,))
        # Thread has been started
        prime95_thread.start()

        # For safety purpose - Just to wait for 10 more sec, so that the process will start in the background.
        time.sleep(TimeConstants.ONE_HOUR_IN_SEC)

        # Verify the background process is running
        self._memory_common_lib.verify_background_process_running(self.LIST_PROCESSES)

        self._log.info("Running the prime95 test Waiting while the prime95 test to run for some time frame .....")

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""

        super(PiCacheSncCheckPrime95Windows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiCacheSncCheckPrime95Windows.main() else Framework.TEST_RESULT_FAIL)
