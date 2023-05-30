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

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.memory_hbm.memory_hbm_common import MemoryHbmCommon
from src.lib.memory_constants import MemoryTopology, MemoryClusterConstants
from src.lib.memory_constants import PlatformMode
from src.lib.platform_config import PlatformConfiguration


class PiMemoryHBMModeG3CycleLinux(MemoryHbmCommon):
    """
    Pheonix ID:16014742513 -PI_Memory_HBM_Mode_G3_Cycle_L
    """

    TEST_CASE_ID = ["16014742513", "PI_Memory_HBM_Mode_G3_Cycle_L"]
    BIOS_CONFIG_FILE = "one_lm_bios_knob.cfg"
    G3_CYCLES = 10

    step_data_dict = {1: {'step_details': 'To verify SUT has No DDR memory configuration ...',
                          'expected_results': 'SUT has no DDR memory configuration ...'},
                      2: {'step_details': 'Clear OS logs and Set the bios knobs, Restart the system, Boot to OS',
                          'expected_results': 'Cleared os logs and bios settings is done.Successfully boot to os'
                                              'and verified the bios knobs'},
                      3: {'step_details': 'Check Mce errors, Power cycle the system and verify for Number of nodes '
                                          'and node memory',
                          'expected_results': 'Verified Number of Nodes and node memory'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiMemoryHBMModeG3CycleLinux object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        bios_config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)

        # calling base class init
        super(PiMemoryHBMModeG3CycleLinux, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._memory_provider.verify_only_hbm_memory_configuration()

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def prepare(self):
        # type: () -> None
        """
        1. To clear os log.
        2. Set the bios knobs to its default mode and 1LM bios knob
        3. Power cycle the SUT to apply the new bios settings.

        :return: None
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        super(PiMemoryHBMModeG3CycleLinux, self).prepare()

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. To check mce errors
        2. Ac cycle and check the number of nodes and node memory.

        :return: True, if the test case is successful.
        """
        cluster_mode = self.get_default_cluster_mode()

        expected_reg_value = self.QUAD_EXPECTED_VALUE
        if cluster_mode == MemoryClusterConstants.SNC4_STRING:
            expected_reg_value = self.SNC4_EXPECTED_VALUE

        mce_errors = []
        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        for cycle_number in range(1, self.G3_CYCLES + 1):
            self._log.info("Power cycle %d", cycle_number)
            self._common_content_lib.clear_mce_errors()
            self.perform_graceful_g3()
            errors = self._common_content_lib.check_if_mce_errors()
            if errors:
                mce_errors.append("MCE Errors during the Cycle_{} are '{}'".format(cycle_number, errors))

            if mce_errors:
                raise content_exceptions.TestFail("\n".join(mce_errors))

            self.snc_check_with_pythonsv_value(expected_reg_value)

            # To verify node memory
            self._memory_provider.verify_hbm_mode_memory(cluster_mode=cluster_mode, platform_mode=PlatformMode.HBM_MODE)

            # To verify number of nodes
            self.verify_number_of_nodes(memory_mode=PlatformMode.HBM_MODE, cluster_mode=cluster_mode)

        self._log.info("Sut is booted back to OS in all the '{}' AC Cycles and there are no Machine Check "
                       "Errors Logged".format(self.G3_CYCLES))

        # To verify HBM memory
        self.verify_installed_hbm_memory()

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiMemoryHBMModeG3CycleLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiMemoryHBMModeG3CycleLinux.main() else Framework.TEST_RESULT_FAIL)
