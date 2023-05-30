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

from src.lib.test_content_logger import TestContentLogger
from src.lib import content_base_test_case


class PiMemoryDdrSingleNumaConfiguration(content_base_test_case.ContentBaseTestCase):
    """
    HP QC ID: 80037

    This case is used to validate single NUMA configuration.
    """

    TEST_CASE_ID = ["H80037 - PI_Memory_DDR5_Single_NUMA_Configuration_L"]
    WAIT_TIME_FOR_30_MIN = 1800
    COMMAND_TO_GET_FREE_MEMORY = "cat /proc/meminfo |grep MemFree"
    LINUX_USR_ROOT_PATH = "/root"

    step_data_dict = {1: {'step_details': 'Clear OS logs and load default bios knobs',
                          'expected_results': 'Clear ALL the system Os logs and default bios knob setting done.'},
                      2: {'step_details': 'Run the command cat /proc/meminfo to get the free memory',
                          'expected_results': 'MemFree information got from cat /proc/meminfo'},
                      3: {'step_details': 'Run the command dd if=/dev/zero of=/temp',
                          'expected_results': 'The command dd if=/dev/zero of=/temp executed successfully'},
                      4: {'step_details': 'Run the command cat /proc/meminfo to get the free memory',
                          'expected_results': 'MemFree in /proc/meminfo is changed to a small number'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiMemoryDdrSingleNumaConfiguration object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiMemoryDdrSingleNumaConfiguration, self).__init__(test_log, arguments, cfg_opts)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. To clear os log

        :return: None
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        super(PiMemoryDdrSingleNumaConfiguration, self).prepare()

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. To set zone reclaim mode to 0
        2. Get free memory before executing dd if=/dev/zero of=/temp
        3. Get free memory after executing dd if=/dev/zero of=/temp
        4. Compare the free memory.The free memory should less value after executing dd if=/dev/zero of=/temp

        :return: True, if the test case is successful.
        """
        final_result = True

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        self._common_content_lib.execute_sut_cmd("sysctl vm.zone_reclaim_mode=0", "To run sysctl command",
                                                 self._command_timeout, self.LINUX_USR_ROOT_PATH)

        pre_free_memory = self._common_content_lib.execute_sut_cmd(
            self.COMMAND_TO_GET_FREE_MEMORY, "Get free memory information",
            self._command_timeout, self.LINUX_USR_ROOT_PATH).split(":")[1].split()[0]

        self._log.info("The available free memory : {} in kB ".format(pre_free_memory))

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=pre_free_memory)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        ret_val = self.os.execute("timeout {} dd if=/dev/zero of=/temp".format(self.WAIT_TIME_FOR_30_MIN),
                                  self.WAIT_TIME_FOR_30_MIN, self.LINUX_USR_ROOT_PATH)
        if ret_val.cmd_failed():
            self._log.info("The output of dd if=/dev/zero of=/temp command is {}:".format(ret_val.stderr))

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        post_free_memory = self._common_content_lib.execute_sut_cmd(
            self.COMMAND_TO_GET_FREE_MEMORY, "Get free memory information",
            self._command_timeout, self.LINUX_USR_ROOT_PATH).split(":")[1].split()[0]

        self._log.info("The available free memory : {} in kB ".format(post_free_memory))

        if pre_free_memory <= post_free_memory:
            self._log.error("After executing dd if=/dev/zero of=/temp command, MemFree in /proc/meminfo "
                            "not changed to a small number")
            final_result = False

        self._log.info("After executing dd if=/dev/zero of=/temp command, MemFree in /proc/meminfo "
                       "changed to a small number")

        self._common_content_lib.execute_sut_cmd("rm -rf /temp", "To delete created file in root",
                                                 self._command_timeout, self.LINUX_USR_ROOT_PATH)
        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=final_result)

        return final_result

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiMemoryDdrSingleNumaConfiguration, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiMemoryDdrSingleNumaConfiguration.main() else Framework.TEST_RESULT_FAIL)
