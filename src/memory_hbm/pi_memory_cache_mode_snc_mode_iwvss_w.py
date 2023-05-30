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

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.provider.stressapp_provider import StressAppTestProvider
from src.memory_hbm.memory_hbm_common import MemoryHbmCommon
from src.provider.vss_provider import VssProvider

class PiCacheSncCheckIwvssWindows(MemoryHbmCommon):
    """
    pheonix id : 1601474422 - PI_Memory_Cache_Mode_SNC_Mode_Iwvss_W

    """

    TEST_CASE_ID = ["1601474422", "PI_Memory_Cache_Mode_SNC_Mode_Iwvss_W"]
    SNC4_BIOS_CONFIG_FILE = "two_lm_snc4_bios_knob.cfg"
    PROCESS_NAME = "mem64.exe"
    LOG_NAME = "iwvss_log.log"
    SNC4_EXPECTED_VALUE = "0xf"
    step_data_dict = {1: {'step_details': 'To verify SUT has 1DPC or 2DPC memory configuration and '
                                          'Load default bios, Set & verify SNC (Sub NUMA) bios knob to SNC4, '
                                          'Check ktilk_snc_config expected value is 0xf',
                          'expected_results': 'SUT has 1DPC or 2DPC memory configuration and Default bios knob setting,'
                                              ' SNC (Sub NUMA) bios knob to SNC4 set and '
                                              'verified and ktilk_snc_config expected value 0xf verified.'},
                      2: {'step_details': 'To Install Iwvss tool and Run Iwvss Tool for 2 hours',
                          'expected_results': 'Iwvss ran with out errors ...'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiCacheSncCheckIwvssWindows object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """

        self.snc4_bios_config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                       self.SNC4_BIOS_CONFIG_FILE)
        super(PiCacheSncCheckIwvssWindows, self).__init__(test_log, arguments, cfg_opts)
        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._install_collateral = InstallCollateral(test_log, self.os, cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._silicon_family = self._common_content_lib.get_platform_family()
        self._vss_provider_obj = VssProvider.factory(self._log, cfg_opts=cfg_opts, os_obj=self.os)

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
        self._install_collateral.install_vc_redist()

        self._log.info("Executing the iwvss ...")

        self._log.info("Executing the iwvss ...")
        # To copy the package and Execute iwvss configuration for stress
        self._vss_provider_obj.execute_vss_memory_test_package(flow_tree="Mem")

        # wait for the iwvss to complete
        self._vss_provider_obj.wait_for_vss_to_complete(self.PROCESS_NAME)

        # Parsing iwvss log
        return_value = self._vss_provider_obj.verify_vss_logs(self.LOG_NAME)

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=return_value)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""

        super(PiCacheSncCheckIwvssWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiCacheSncCheckIwvssWindows.main() else Framework.TEST_RESULT_FAIL)
