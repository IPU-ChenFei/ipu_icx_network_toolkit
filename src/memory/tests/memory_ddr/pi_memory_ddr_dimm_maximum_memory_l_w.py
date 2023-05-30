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
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_ddr.ddr_common import DDRCommon


class PiMemoryDdrDimmMaximumMemory(DDRCommon):
    """
    HP QC ID: H102740-PI_Memory_DDR5_DIMMMaximumMemory_W and
    H80035, pheonix id: 18014075328-PI_Memory_DDR5_DIMMMaximumMemory_L and

    To ensure the server board can operate within the maximum supported range of memory capacity configuration.
    """

    TEST_CASE_ID = ["H102740", "PI_Memory_DDR5_DIMMMaximumMemory_W", "H80035", "PI_Memory_DDR5_DIMMMaximumMemory_L"]

    step_data_dict = {1: {'step_details': 'To verify Maximum Memory population with 2DPC, Clear OS logs and to load '
                                          'default bios knobs',
                          'expected_results': 'Verified Maximum memory,Cleared OS logs,Default bios knob setting done'},
                      2: {'step_details': 'Verify the memory displayed at POST and amount of memory reported by the '
                                          'EDKII Menu -> System Information with amount of memory installed in the '
                                          'system and memory speed,memory mode for windows.'
                                          'If linux amount of memory installed in the system',
                          'expected_results': 'Verified POST memory and System Information matched with amount of '
                                              'memory installed in system and memory speed, memory mode matched.'},
                      3: {'step_details': 'Verify the amount of memory reported by the operating system matches the '
                                          'amount of physical memory installed in the system.',
                          'expected_results': 'Verified the OS displayed memory with the memory installed in system'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiMemoryDdrDimmMaximumMemory object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiMemoryDdrDimmMaximumMemory, self).__init__(test_log, arguments, cfg_opts)

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        1. To verify maximum DIMM capacity installed in the SUT.
        2. To Clear OS logs.
        3. To load default BIOS settings
        4. Verify for Maximum memory population.

        :return: None
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self.verify_for_maximum_memory_population()  # To check maximum DIMM population
        super(PiMemoryDdrDimmMaximumMemory, self).prepare()

        self._test_content_logger.end_step_logger(1, return_val=True)
        # Step Logger end for Step 1

    def execute(self):
        """
        Function is responsible for the below tasks,

        1. Check memory information at POST.
        2. Verify the amount of memory and speed reported by the operating system.

        :return: True, if the test case is successful.
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        if self.os.os_type.lower() == OperatingSystems.WINDOWS.lower():
            self.verify_physical_memory_in_system_information_in_bios(speed_mode=True)
        elif self.os.os_type.lower() == OperatingSystems.LINUX.lower():
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
        super(PiMemoryDdrDimmMaximumMemory, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiMemoryDdrDimmMaximumMemory.main() else Framework.TEST_RESULT_FAIL)
