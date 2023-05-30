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
from src.memory_hbm.memory_hbm_common import MemoryHbmCommon
from src.lib.memory_constants import MemoryTopology, MemoryClusterConstants
from src.provider.vss_provider import VssProvider


class PiFlatQuadIwvssWindows(MemoryHbmCommon):
    """
    pheonix id : 16014744275 - PI_Memory_Flat_Mode_Quad_Mode_Iwvss_W

    """

    TEST_CASE_ID = ["16014744275", "PI_Memory_Flat_Mode_Quad_Mode_Iwvss_W"]

    BIOS_CONFIG_FILE = "one_lm_quad_mode_bios_knob.cfg"
    QUAD_EXPECTED_VALUE = "0xe"
    PROCESS_NAME = "mem64.exe"
    LOG_NAME = "iwvss_log.log"
    step_data_dict = {1: {'step_details': 'To verify SUT has 1DPC or 2DPC memory configuration and '
                                          'To Load default bios settings and quad mode bios knobs',
                          'expected_results': 'SUT has 1DPC or 2DPC memory configuration and '
                                              'Default Bios and Quad mode bios setting done.'},
                      2: {'step_details': 'To Check Quad mode enabled or not by Python sv commands',
                          'expected_results': 'Quad mode enabled.'},
                      3: {'step_details': 'Install Iwvss tool and Run Iwvss Tool for 1 hour',
                          'expected_results': 'SUT did not hang after running Iwvss tool for 1 hour'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiMemoryFlatQuadMlcLinux object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        # calling base class init
        super(PiFlatQuadIwvssWindows, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._install_collateral = InstallCollateral(test_log, self.os, cfg_opts)
        self._silicon_family = self._common_content_lib.get_platform_family()
        self._vss_provider_obj = VssProvider.factory(self._log, cfg_opts=cfg_opts, os_obj=self.os)

    def prepare(self):
        # type: () -> None
        """
        1. Verify 1DPC or 2DPC memory configuration, Load default bios and Set the bios knobs.
        2. Reboot the SUT to apply the new bios settings.

        :return: None
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._memory_provider.verify_1dpc_or_2dpc_memory_configuration()
        super(PiFlatQuadIwvssWindows, self).prepare()

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Check Quad mode information.
        2. Install Iwvss and run the Iwvss tool for 1 Hour.

        :return: True, if the test case is successful.
        :raise: TestFail
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        cluster_mode = self.get_default_cluster_mode()
        expected_reg_value = self.QUAD_EXPECTED_VALUE
        if cluster_mode == MemoryClusterConstants.SNC4_STRING:
            expected_reg_value = self.SNC4_EXPECTED_VALUE
        self.snc_check_with_pythonsv_value(expected_reg_value)
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        self._install_collateral.install_vc_redist()

        self._log.info("Executing the iwvss ...")
        # To copy the package and Execute iwvss configuration for stress
        self._vss_provider_obj.execute_vss_memory_test_package(flow_tree="Mem")

        # wait for the iwvss to complete
        self._vss_provider_obj.wait_for_vss_to_complete(self.PROCESS_NAME)

        # Parsing iwvss log
        return_value = self._vss_provider_obj.verify_vss_logs(self.LOG_NAME)

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=return_value)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""

        super(PiFlatQuadIwvssWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiFlatQuadIwvssWindows.main() else Framework.TEST_RESULT_FAIL)
