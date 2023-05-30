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
from src.memory.tests.memory_ddr.ddr_common import DDRCommon
from src.lib.memory_constants import PlatformMode


class PiMemoryHBMModeOSBootLinux(MemoryHbmCommon):
    """
    Phoenix ID:16014742737 - PI_Memory_HBM_Mode_OS_Boot_L
    """

    TEST_CASE_ID = ["16014742737", "PI_Memory_HBM_Mode_OS_Boot_L"]
    BIOS_CONFIG_FILE = "one_lm_bios_knob.cfg"

    step_data_dict = {1: {'step_details': 'Clear OS logs and Set the bios knobs, Restart the system, Boot to OS',
                          'expected_results': 'Cleared os logs and bios settings is done.Successfully boot to os'
                                              'and verified the bios knobs'},
                      2: {'step_details': 'Verify memory displayed at POST and amount of memory reported by the '
                                          'EDKII Menu -> System Information with amount of memory installed in the '
                                          'system',
                          'expected_results': 'Verified POST memory and System Information matched with amount of '
                                              'memory installed in system'},
                      3: {'step_details': 'Check Mce errors, verify for Number of nodes and node memory',
                          'expected_results': 'Verified Number of Nodes and node memory'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiMemoryHBMModeOSBootLinux object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        bios_config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)

        super(PiMemoryHBMModeOSBootLinux, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path)

        self._ddr_common = DDRCommon(test_log, arguments, cfg_opts)
        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._memory_provider.verify_only_hbm_memory_configuration()

    def prepare(self):
        # type: () -> None
        """
        1. To clear os log.
        2. Set the bios knobs to its default mode and 1LM bios setting.
        3. Power cycle the SUT to apply the new bios settings.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._common_content_lib.clear_mce_errors()
        super(PiMemoryHBMModeOSBootLinux, self).prepare()

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. To check system memory in EDKII Menu --> System Information
        2. To check mce errors
        3. To check the number of nodes and node memory.

        :return: True, if the test case is successful.
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        # to check manually for both 1LM and 2lM in HBM system so function need modification
        self._memory_provider.verify_only_hbm_memory_configuration()

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        cluster_mode = self.get_default_cluster_mode()

        mce_errors = []
        errors = self._common_content_lib.check_if_mce_errors()
        if errors:
            mce_errors.append("MCE Errors are '{}'".format(errors))

        if mce_errors:
            raise content_exceptions.TestFail("\n".join(mce_errors))

        # To verify node memory
        self._memory_provider.verify_hbm_mode_memory(cluster_mode=cluster_mode, platform_mode=PlatformMode.HBM_MODE)

        # To verify number of nodes
        self.verify_number_of_nodes(memory_mode=PlatformMode.HBM_MODE, cluster_mode=cluster_mode)

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiMemoryHBMModeOSBootLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiMemoryHBMModeOSBootLinux.main() else Framework.TEST_RESULT_FAIL)
