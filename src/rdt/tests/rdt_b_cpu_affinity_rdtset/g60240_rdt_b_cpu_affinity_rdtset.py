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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib.test_content_logger import TestContentLogger
from src.lib import content_base_test_case
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral


class RdtCpuAffinityRdtSet(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow ID : G60240.0 - PI_RDT_B_CPUAffinity_rdtset

    This test case aims to install RDT if it not installed and also installs memtester tool and
    verify Set CPU affinity single/multiple core via command/task and verify the affinity via rdtset tool.
    """
    TEST_CASE_ID = ["G60240.0-PI_RDT_B_CPUAffinity_rdtset"]
    RDTSET_VALUE = 1
    SINGLE_CORE = 4
    GROUP_CORE = "4-5"
    MEM_CPU_CMD = "rdtset -c {} memtester 10M"
    RDTSET_CPU_CMD = "rdtset -c {} -p 1"
    TASKSET_CMD = "taskset -p {}"
    FOR_MASK_10 = "current affinity mask: 10"
    FOR_MASK_30 = "current affinity mask: 30"
    INFO_SINGLE_CPU = "CPU affinity to set to single CPU"
    INFO_GROUP_CPU = "CPU affinity to set to CPU group"

    STEP_DATA_DICT = {
        1: {'step_details': 'Verify if RDT is installed on sut',
            'expected_results': 'Verified installation'},
        2: {'step_details': 'Restore RDT to default monitoring',
            'expected_results': 'Restore RDT to default monitoring is successful'},
        3: {'step_details': 'Set & Verify CPU affinity to single CPU by running command rdtset -c 4 memtester 10M',
            'expected_results': 'CPU affinity to single CPU set successfully'},
        4: {'step_details': 'Set & Verify CPU affinity to CPU group by running command rdtset -c 4-5 memtester 10M',
            'expected_results': 'CPU affinity to CPU group set successfully'},
        5: {'step_details': 'Set & Verify CPU affinity to single CPU by running command rdtset -c 4 -p 1',
            'expected_results': 'CPU affinity to single CPU set successfully'},
        6: {'step_details': 'Set & Verify CPU affinity to CPU group by running command rdtset -c 4-5 -p 1',
            'expected_results': 'CPU affinity to CPU group set successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtCpuAffinityRdtSet

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtCpuAffinityRdtSet, self).__init__(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def prepare(self):
        # type: () -> None
        """Test preparation/setup and install the stress tool to sut"""
        super(RdtCpuAffinityRdtSet, self).prepare()
        self._install_collateral.install_memtester_tool_to_sut()

    def execute(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. Set & Verify CPU affinity to single CPU by running command rdtset -c 4 memtester 10M
        4. Set & Verify CPU affinity to CPU group by running command rdtset -c 4-5 memtester 10M
        5. Set & Verify CPU affinity to single CPU by running command rdtset -c 4 -p 1
        6. Set & Verify CPU affinity to CPU group by running command rdtset -c 4-5 -p 1

        :raise: content_exceptions.TestFail if current affinity mask not observed in taskset output
        :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(1)
        # Verify if RDT is installed, If not it will install
        self._rdt.install_rdt()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        # Restore default monitoring: pqos -R
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self.os.execute_async(self.MEM_CPU_CMD.format(self.SINGLE_CORE))
        memtest_pid = self._rdt.get_pid_value()
        unmatched_value = self._common_content_lib.execute_cmd_and_get_unmatched_result \
            (cmd_to_execute=self.TASKSET_CMD.format(memtest_pid),
             cmd_info=self.INFO_SINGLE_CPU,
             string_pattern_to_search=self.FOR_MASK_10,
             cmd_timeout=self._rdt._command_timeout)
        self._rdt.stop_memtester_tool()
        if unmatched_value:
            raise content_exceptions.TestFail(
                "{} did not find in the {} output".format(self.FOR_MASK_10, unmatched_value))
        self._log.info("CPU affinity has been set to single CPU successfully")
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self.os.execute_async(self.MEM_CPU_CMD.format(self.GROUP_CORE))
        memtest_pid = self._rdt.get_pid_value()
        unmatched_value = self._common_content_lib.execute_cmd_and_get_unmatched_result \
            (cmd_to_execute=self.TASKSET_CMD.format(memtest_pid),
             cmd_info=self.INFO_GROUP_CPU,
             string_pattern_to_search=self.FOR_MASK_30,
             cmd_timeout=self._rdt._command_timeout)
        self._rdt.stop_memtester_tool()
        if unmatched_value:
            raise content_exceptions.TestFail(
                "{} did not find in the {} output".format(self.FOR_MASK_30, unmatched_value))
        self._log.info("CPU affinity has been set to CPU group successfully")
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        self.os.execute_async(self.RDTSET_CPU_CMD.format(self.SINGLE_CORE))
        unmatched_value = self._common_content_lib.execute_cmd_and_get_unmatched_result \
            (cmd_to_execute=self.TASKSET_CMD.format(self.RDTSET_VALUE),
             cmd_info=self.INFO_SINGLE_CPU,
             string_pattern_to_search=self.FOR_MASK_10,
             cmd_timeout=self._rdt._command_timeout)
        if unmatched_value:
            raise content_exceptions.TestFail(
                "{} did not find in the {} output".format(self.FOR_MASK_10, unmatched_value))
        self._log.info("CPU affinity has been set to single CPU successfully")
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        self.os.execute_async(self.RDTSET_CPU_CMD.format(self.GROUP_CORE))
        unmatched_value = self._common_content_lib.execute_cmd_and_get_unmatched_result \
            (cmd_to_execute=self.TASKSET_CMD.format(self.RDTSET_VALUE),
             cmd_info=self.INFO_GROUP_CPU,
             string_pattern_to_search=self.FOR_MASK_30,
             cmd_timeout=self._rdt._command_timeout)
        if unmatched_value:
            raise content_exceptions.TestFail(
                "{} did not find in the {} output".format(self.FOR_MASK_30, unmatched_value))
        self._log.info("CPU affinity has been set to CPU group successfully")
        self._test_content_logger.end_step_logger(6, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtCpuAffinityRdtSet.main() else Framework.TEST_RESULT_FAIL)
