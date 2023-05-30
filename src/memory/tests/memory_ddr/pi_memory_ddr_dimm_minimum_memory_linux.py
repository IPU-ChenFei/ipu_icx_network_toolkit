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
from src.lib import content_exceptions

from src.lib.dtaf_content_constants import TimeConstants
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_ddr.ddr_common import DDRCommon


class PiMemoryDdrDimmMinimumMemory(DDRCommon):
    """
    HP QC ID: 80034-PI_Memory_DDR5_DIMMMinimumMemory_L
    To sure the memory total approximates the total amount of RAM present in the system.
    """

    TEST_CASE_ID = ["H80034", "PI_Memory_DDR5_DIMMMinimumMemory_L"]

    step_data_dict = {1: {'step_details': 'Minimum memory check, clear OS logs and load default bios knobs',
                          'expected_results': '1DPC for minimum memory config, We are concern for slot not to '
                                              'get damage while removing and Connecting DIMMs again and '
                                              'Again in the machine only for this test.'
                                              ' Clear ALL the system OS logs and default'},
                      2: {'step_details': 'Verify the memory displayed at POST is the amount of memory installed in '
                                          'the system.',
                          'expected_results': 'POST displays the amount of physical memory installed in system.'},
                      3: {'step_details': 'Verify the memory displayed at POST and amount of memory reported by the '
                                          'EDKII Menu -> System Information with amount of memory installed in the '
                                          'system.',
                          'expected_results': 'Verified POST memory and System Information matched with amount of '
                                              'memory installed in system'},
                      4: {'step_details': 'Verify the amount of memory reported by the operating system matches the '
                                          'amount of memory installed in the system.',
                          'expected_results': 'OS displays the amount of memory installed in system.'},

                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiMemoryDdrDimmMinimumMemory object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiMemoryDdrDimmMinimumMemory, self).__init__(test_log, arguments, cfg_opts)

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Reboot the SUT to apply the new bios settings.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        # Checking for minimum memory
        # Configuration from dtaf content constants
        dict_config_channel_population = self._memory_provider.get_1_dpc_channel_configuration()

        # Verification between platform configuration and golden configuration info.
        dict_config_match = self._memory_provider.verify_channel_population(dict_config_channel_population)

        if not dict_config_match:
            raise content_exceptions.TestFail("Configuration not set correctly on this platform to support this test "
                                              "case.. please check the configuration and try again..")

        super(PiMemoryDdrDimmMinimumMemory, self).prepare()

        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Check memory information.

        :return: True, if the test case is successful.
        :raise: TestFail
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        self.verify_physical_memory_in_system_information_in_bios()

        # Step Logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        self.verify_installed_memory_in_os_level()

        # Step Logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiMemoryDdrDimmMinimumMemory, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiMemoryDdrDimmMinimumMemory.main() else Framework.TEST_RESULT_FAIL)
