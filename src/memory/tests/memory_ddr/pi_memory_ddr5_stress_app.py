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

from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_ddr.ddr_common import DDRCommon


class PiMemoryDdr5StressApp(DDRCommon):
    """
    HPALM ID: 102745 - PI_Memory_DDR5_Stress_APP

    """
    TEST_CASE_ID = ["H102745", "PI_Memory_DDR5_Stress_APP"]
    BIOS_CONFIG_FILE_NAME = "pi_memory_ddr5_stress_app.cfg"
    LOG_FILE_NAME = "stress.log"
    step_data_dict = {1: {'step_details': 'To verify Maximum Memory population with 2DPC, Clear System and Application '
                                          'Event logs and to load default bios knobs and set the frequency to 4400MHz '
                                          'for 2 DPC',
                          'expected_results': 'Verified Maximum memory, Cleared ALL the System and Application '
                                              'Event logs and bios knob setting done'},
                      2: {'step_details': 'Verify the memory displayed at POST and amount of memory reported by the '
                                          'EDKII Menu -> System Information with amount of physical memory installed '
                                          'in the system.',
                          'expected_results': 'Verified POST memory and System Information matched with amount of '
                                              'physical memory installed in system'},
                      3: {'step_details': 'Verify the amount of memory reported by the operating system matches the '
                                          'amount of memory installed in the system.',
                          'expected_results': 'Verified the OS displayed memory with the memory installed in system.'},
                      4: {'step_details': 'Install latest version of stress app test and run stress for given time',
                          'expected_results': 'Post running stress app test, no error has been reported.'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiMemoryDdr5StressApp object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = os.path.join(cur_path, self.BIOS_CONFIG_FILE_NAME)
        # calling base class init
        super(PiMemoryDdr5StressApp, self).__init__(test_log, arguments, cfg_opts,
                                                    bios_config_file=bios_config_file_path)

        # Object of TestContentLogger class
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

        # Checking for maximum memory
        self.verify_for_maximum_memory_population()

        super(PiMemoryDdr5StressApp, self).prepare()

        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Check memory information.
        2. Install stressapptest and run the stressapptest.

        :return: True, if the test case is successful.
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

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        self._install_collateral.install_stress_test_app()

        self._stress_app_provider.execute_installer_stressapp_test(
            "./stressapptest -s {} -M -m -W -l {}".format(self._stress_app_execute_time, self.LOG_FILE_NAME))

        log_path_in_host = self._common_content_lib.get_log_file_dir()
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            log_path_in_host, sut_log_files_path=self.LINUX_USR_ROOT_PATH, extension=self.LOG_FILE_NAME)

        return_value = self._memory_common_lib.parse_log_for_error_patterns(log_path=os.path.join(log_path_to_parse,
                                                                                                  self.LOG_FILE_NAME))

        # Step Logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=return_value)
        return return_value

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiMemoryDdr5StressApp, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiMemoryDdr5StressApp.main() else Framework.TEST_RESULT_FAIL)
