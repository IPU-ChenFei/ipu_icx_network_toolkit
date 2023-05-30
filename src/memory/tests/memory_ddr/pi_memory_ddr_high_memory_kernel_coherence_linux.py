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
from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase


class PIMemoryDdrHighMemoryKernelCoherenceLinux(ContentBaseTestCase):
    """
    HP QC ID: 80036

    DDR5 Memory Linux kernel coherence test.
    """

    _bios_config_file = "pi_memory_high_bios_knbos.cfg"
    TEST_CASE_ID = "H80036-PI_Memory_DDR5_High_Memory_Kernel_Coherence_Linux"
    LINUX_USR_ROOT_PATH = "/root"
    MEM_PAGE_ALLOC_FILTER_CMD = "echo 'pfn > 4220000' > /sys/kernel/debug/tracing/events/kmem/mm_page_alloc/filter"
    MEM_PAGE_ALLOC_ENABLE_CMD = "echo 1 > /sys/kernel/debug/tracing/events/kmem/mm_page_alloc/enable"
    SYSTEM_TRACE_COMMAND = "cat /sys/kernel/debug/tracing/trace"
    MM_PAGE_ALLOCATE = "mm_page_alloc"

    step_data_dict = {1: {'step_details': 'Clear OS logs and Set the bios knobs,Restart the system, '
                                          'Boot to OS properly and verify the bios knobs.',
                          'expected_results': 'Clear ALL the system OS logs and BIOS setting done, '
                                              'Successfully boot to OS & Verified the bios knobs.'},
                      2: {'step_details': 'Execute the command echo "pfn > 4220000" > '
                                          '/sys/kernel/debug/tracing/events/kmem/mm_page_alloc/filter',
                          'expected_results': 'echo "pfn > 4220000" > /sys/kernel/debug/tracing/events/kmem/'
                                              'mm_page_alloc/filter command executed without errors..'},
                      3: {'step_details': 'Execute the command '
                                          'echo 1 > /sys/kernel/debug/tracing/events/kmem/mm_page_alloc/enable',
                          'expected_results': 'echo 1 > /sys/kernel/debug/tracing/events/kmem/mm_page_alloc/enable '
                                              'command executed with out errors'},
                      4: {'step_details': 'execute the command cat /sys/kernel/debug/tracing/trace',
                          'expected_results': 'command cat /sys/kernel/debug/tracing/trace executed with out errors '
                                              'and dump memory page allocate'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PIMemoryDdrHighMemoryKernelCoherenceLinux object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PIMemoryDdrHighMemoryKernelCoherenceLinux, self).__init__(test_log, arguments, cfg_opts,
                                                                        self._bios_config_file)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.

        :return: None
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        super(PIMemoryDdrHighMemoryKernelCoherenceLinux, self).prepare()

        self._test_content_logger.end_step_logger(1, return_val=True)
        # Step Logger end for Step 1

    def execute(self):
        """
        Function is responsible for the below tasks,

        1) execute the command echo 'pfn > 4220000' > /sys/kernel/debug/tracing/events/kmem/mm_page_alloc/filter.
        2) execute the command echo 1 > /sys/kernel/debug/tracing/events/kmem/mm_page_alloc/enable.
        3) execute the command cat /sys/kernel/debug/tracing/trace.

        :return: True, if the test case is successful.
        :raise: TestFail
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        cmd_result = self._common_content_lib.execute_sut_cmd(
            self.MEM_PAGE_ALLOC_FILTER_CMD, self.MEM_PAGE_ALLOC_FILTER_CMD,
            self._command_timeout, self.LINUX_USR_ROOT_PATH)
        self._log.debug("stdout : {}".format(cmd_result))

        # Step Logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        cmd_result = self._common_content_lib.execute_sut_cmd(
            self.MEM_PAGE_ALLOC_ENABLE_CMD, self.MEM_PAGE_ALLOC_ENABLE_CMD,
            self._command_timeout, self.LINUX_USR_ROOT_PATH)
        self._log.debug("stdout : {}".format(cmd_result))

        # Step Logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        cmd_result = self._common_content_lib.execute_sut_cmd(
            self.SYSTEM_TRACE_COMMAND, self.SYSTEM_TRACE_COMMAND,
            self._command_timeout, self.LINUX_USR_ROOT_PATH)
        self._log.debug("{} std out result : \n {}".format(self.SYSTEM_TRACE_COMMAND, cmd_result))
        self._log.error("{} std error result : \n {}".format(self.SYSTEM_TRACE_COMMAND, cmd_result))

        if self.MM_PAGE_ALLOCATE not in cmd_result:
            raise content_exceptions.TestFail("DDR5 Memory Linux kernel coherence test failed")
        self._log.info("command {} result is {}".format(self.SYSTEM_TRACE_COMMAND, cmd_result))

        # Step Logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PIMemoryDdrHighMemoryKernelCoherenceLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if PIMemoryDdrHighMemoryKernelCoherenceLinux.main() else Framework.TEST_RESULT_FAIL)
