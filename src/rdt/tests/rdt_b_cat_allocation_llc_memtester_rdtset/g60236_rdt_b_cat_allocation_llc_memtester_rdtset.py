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
import re
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_base_test_case
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions


class RdtCatAllocationLlcMemtesterRdtset(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow ID : G60236.1-PI_RDT_B_CATAllocation_LLC_memtester_rdtset

    This test case aims to install RDT if it not installed and
    verify L3 CAT Set COS definition command/task and verify the cache allocation via rdtset tool when memtester is running
    """
    TEST_CASE_ID = ["G60236.1-PI_RDT_B_CATAllocation_LLC_memtester_rdtset"]
    COS_ARG5 = "5"
    COS_ARG6 = "6"
    EXPECTED_VALUE = "COS14"
    CPU_CORE_VALUE = "5-6"
    RDTSET_L3_CAT_MASK = 'rdtset -t "l3={};cpu={}" -c {} memtester 10M'
    L3CAT_BITMASK_CMD_CHECK = "One or more of requested L3 CBMs .MASK: {}. not supported by system .too long."
    CACHE_ALLOCATION_CMD = "rdtset -I -t 'l3={}' -c {} -p 1"
    L3CAT_BITMASK_FOR_TASK_ID  = "rdtset -I -t 'l3={}' -p 1"
    CACHE_ALLOCATION_SUCCESS_INFO = "L3CA {} => MASK {}"
    MIN_SOCKET = 2
    STEP_DATA_DICT = {
        1: {'step_details': 'Verify RDT is installed in sut',
            'expected_results': 'Installation od RDT is verified successfully'},
        2: {'step_details': 'Restore default monitoring',
            'expected_results': 'Restore to default monitoring is successful'},
        3: {'step_details': 'Install memtester tool if not installed.',
            'expected_results': 'Successfully installed memtester'},
        4: {'step_details': 'Set cache allocation with rdtset for cpu {}, and run stress on this core'.format(
            CPU_CORE_VALUE),
            'expected_results': 'Setting Cache allocation is successful'},
        5: {'step_details': 'Verify cache allocation',
            'expected_results': 'Cache allocation verified Successfully'},
        6: {'step_details': 'Terminate memtester process ',
            'expected_results': 'Memtester process terminated successfully'},
        7: {'step_details': 'Check ability to run command with too long L3 CAT bitmask',
            'expected_results': 'Verified that its Unable to run command with too long L3 CAT bitmask'},
        8: {'step_details': 'Set L3 CAT bitmask for Task Id',
            'expected_results': 'L3 CAT bitmask for Task Id set successfully'},
        9: {'step_details': 'Verify cache allocation',
            'expected_results': 'Cache allocation verified Successfully'},
        10: {'step_details': 'Check that its Unable to set too long L3 CAT bitmask for the task ID',
             'expected_results': 'Verified that its Unable to set too long L3 CAT bitmask for the task ID'},
        11: {'step_details': 'Restore default monitoring',
             'expected_results': 'Restore to default monitoring is successful'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtCatAllocationLlcMemtesterRdtset

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtCatAllocationLlcMemtesterRdtset, self).__init__(test_log, arguments, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def prepare(self):  # type: () -> None
        """Test preparation/setup and install the stress tool to sut"""
        super(RdtCatAllocationLlcMemtesterRdtset, self).prepare()

    def execute(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. Check actual L3CA COS definitions by running command  pqos -s
        4. Run the "rdtset -t 'l3=0xf;cpu=5-6' -c 5-6 memtester 10M" to set cache allocation
        5. Verify cache allocation with "pqos -s" command
        6. Terminate memtester process
        7. Run the "rdtset -t 'l3=0xffffffff;cpu=5-6' -c 5-6 memtester 10M" to set cache allocation and
        Observe "One or more of requested L3 CBMs (MASK: 0xffffffff) not supported by system (too long) in output
        8. Run the "rdtset -I -t 'l3=0xf' -c 5-6 -p 1" to set cache allocation
        9. Verify cache allocation with "pqos -s" command
        10. Run the "Run the rdtset -I -t 'l3=0xffff' -p 1" to set cache allocation and Observe "One or more of
        requested L3 CBMs (MASK: 0xffff) not supported by system (too long) in output
        11. Restore default allocation:  pqos -R

        :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(1)
        self._rdt.install_rdt()
        self._test_content_logger.end_step_logger(1, return_val=True)

        # Restore rdt monitor to default mode
        self._test_content_logger.start_step_logger(2)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Instal memtester tool if not installed.
        self._test_content_logger.start_step_logger(3)
        self._install_collateral.install_memtester_tool_to_sut()
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Run the "rdtset -t 'l3=0xf;cpu=5-6' -c 5-6 memtester 10M" to set cache allocation
        self._test_content_logger.start_step_logger(4)
        self.os.execute_async(self.RDTSET_L3_CAT_MASK.format(self._rdt.COS_ARG1_VALUE, self.CPU_CORE_VALUE, self.CPU_CORE_VALUE))
        self._log.debug("Executed command {}".format(
            self.RDTSET_L3_CAT_MASK.format(self._rdt.COS_ARG1_VALUE, self.CPU_CORE_VALUE, self.CPU_CORE_VALUE)))
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Verify cache allocation with "pqos -s" command
        self._test_content_logger.start_step_logger(5)
        self._rdt.check_l3ca_core_definitions(self._rdt.CHECK_L3CA_CMD, self.COS_ARG5, self.EXPECTED_VALUE)
        self._rdt.check_l3ca_core_definitions(self._rdt.CHECK_L3CA_CMD, self.COS_ARG6, self.EXPECTED_VALUE)
        cache_allocation_result = self._common_content_lib.execute_sut_cmd(
            self._rdt.CHECK_L3CA_CMD + "| grep {}".format(self.EXPECTED_VALUE),
            self._rdt.CHECK_L3CA_CMD, self._command_timeout)
        if self.CACHE_ALLOCATION_SUCCESS_INFO.format(self.EXPECTED_VALUE,
                                                     self._rdt.COS_ARG1_VALUE) not in cache_allocation_result:
            raise content_exceptions.TestFail("{} not found in the output : {}".format(
                self.self.CACHE_ALLOCATION_SUCCESS_INFO.format(self.EXPECTED_VALUE, self._rdt.COS_ARG1_VALUE),
                cache_allocation_result))
        self._log.info("{} Observed in pqos output".format(self.CACHE_ALLOCATION_SUCCESS_INFO.format(self.EXPECTED_VALUE,
                                                     self._rdt.COS_ARG1_VALUE)))
        self._test_content_logger.end_step_logger(5, return_val=True)

        #  Terminate memtester process
        self._test_content_logger.start_step_logger(6)
        self._rdt.stop_memtester_tool()
        self._test_content_logger.end_step_logger(6, return_val=True)

        # Unable to run command with too long L3 CAT bitmask
        self._test_content_logger.start_step_logger(7)
        command_output = self.os.execute(self.RDTSET_L3_CAT_MASK.format(self._rdt.COS_ARG3_VALUE,
                                                    self.CPU_CORE_VALUE, self.CPU_CORE_VALUE), self._command_timeout)
        if not re.search(self.L3CAT_BITMASK_CMD_CHECK.format(self._rdt.COS_ARG3_VALUE), command_output.stderr):
            raise content_exceptions.TestFail("{} not found in the output : {}".
                                              format(self.L3CAT_BITMASK_CMD_CHECK.format(self._rdt.COS_ARG3_VALUE),
                                                     command_output))
        self._log.info("Found the string {} in output".format(self.L3CAT_BITMASK_CMD_CHECK.format(self._rdt.COS_ARG3_VALUE)))
        self._test_content_logger.end_step_logger(7, return_val=True)

        # Set L3 CAT bitmask for Task Id
        self._test_content_logger.start_step_logger(8)
        self.os.execute_async(self.CACHE_ALLOCATION_CMD)
        self._log.debug("Executed command {}".format(self.CACHE_ALLOCATION_CMD))
        self._test_content_logger.end_step_logger(8, return_val=True)

        # Verify cache allocation with "pqos -s" command
        self._test_content_logger.start_step_logger(9)
        cache_allocation_result = self._common_content_lib.execute_sut_cmd(
            self._rdt.CHECK_L3CA_CMD + "| grep {}".format(self.EXPECTED_VALUE),
            self._rdt.CHECK_L3CA_CMD ,self._command_timeout)
        self._log.debug("{} Command output : {}".format(self._rdt.CHECK_L3CA_CMD + "| grep {}".format(
                                    self.EXPECTED_VALUE), cache_allocation_result))
        if self.CACHE_ALLOCATION_SUCCESS_INFO.format(self.EXPECTED_VALUE,
                                                     self._rdt.COS_ARG1_VALUE) not in cache_allocation_result:
            raise content_exceptions.TestFail("{} not found in the output : {}".format(
                self.self.CACHE_ALLOCATION_SUCCESS_INFO.format(self.EXPECTED_VALUE, self._rdt.COS_ARG1_VALUE),
                cache_allocation_result))
        self._log.info("Successfully Set L3 CAT bitmask for Task Id")
        self._test_content_logger.end_step_logger(9, return_val=True)

        # Unable to set too long L3 CAT bitmask for the task ID
        self._test_content_logger.start_step_logger(10)
        command_output = self.os.execute(self.L3CAT_BITMASK_FOR_TASK_ID.format(self._rdt.COS_ARG4_VALUE), self._command_timeout)
        self._log.debug("Command Output : {} and {}".format(command_output.stdout,command_output.stderr))
        if not re.search(self.L3CAT_BITMASK_CMD_CHECK.format(self._rdt.COS_ARG4_VALUE), command_output.stderr):
            raise content_exceptions.TestFail("{} not found in the output : {}".
                                              format(self.L3CAT_BITMASK_CMD_CHECK.format(self._rdt.COS_ARG4_VALUE),
                                                     command_output.stderr))
        self._test_content_logger.end_step_logger(10, return_val=True)

        # Restore rdt monitor to default mode
        self._test_content_logger.start_step_logger(11)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(11, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtCatAllocationLlcMemtesterRdtset.main() else Framework.TEST_RESULT_FAIL)
