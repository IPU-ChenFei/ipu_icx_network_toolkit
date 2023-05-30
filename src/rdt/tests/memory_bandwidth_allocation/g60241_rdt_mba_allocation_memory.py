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
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions


class RdtMbaAllocationMemory(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow ID : G60241.0 - PI_RDT_B_MBAAllocation_Memory
    This test case verifies MBA Set COS definition and Set COS association cores/tasks via pqos command.
    """
    TEST_CASE_ID = ["G60241.0 - PI_RDT_B_MBAAllocation_Memory"]
    COS_ARG1 = "2"
    COS_ARG1_VALUE = "50"
    COS_ARG2_VALUE = "20"
    COS_ARG3_VALUE = "80"
    COS_ARG4_VALUE = "200"
    SET_CORE_ASSOCIATION_CMD = "pqos -a llc:{}={},{}"
    NUM_OF_SOCKETS_CMD = "grep 'physical id' /proc/cpuinfo | ""sort -u | wc -l"
    SET_UNKNOWN_CORE_ASSOCIATION_CMD = "pqos -a llc:{}={}"
    CORE_ARG1 = "6"
    CORE_ARG1_VALUE = "1"
    CORE_ARG2_VALUE = "3"
    CORE_ARG3_VALUE = "1000"
    ERR_CORE_INFO = "Core number or class id is out of bounds!"
    SET_PID_ASSOCIATION_CMD = "pqos -I -a pid:{}={}"
    PID_VALUE = "2"
    PID_ARG1_VALUE = "1"
    PID_ARG2_VALUE = "9999999999"
    PID_ASSOCIATION_CMD_INFO = "Task ID number or class id is out of bounds!"
    CORE = "Core {}"
    EXP_COS_VALUE = "COS6"
    STEP_DATA_DICT = \
        {
            1: {'step_details': 'Restore default allocation',
                'expected_results': 'Restore RDT to default monitoring is successful'},
            2: {'step_details': 'Verify MBA capability is detected on platform ',
                'expected_results': 'Observe "MBA capability detected" in output'},
            3: {'step_details': 'Verify setting MBA COS definition to 50% ',
                'expected_results': 'Observe the following Output "SOCKET 0 MBA COS2 => 50% requested, 50% applied"'},
            4: {'step_details': 'Verify setting MBA COS definition to 20%',
                'expected_results': 'Observe the following in output "SOCKET 0 MBA COS2 => 20% requested, 20% applied" '},
            5: {'step_details': 'Verify setting MBA COS definition to 80% ',
                'expected_results': 'Observe the following in output "SOCKET 0 MBA COS2 => 80% requested, 80% applied '},
            6: {'step_details': 'Unable to set MBA COS definition to invalid value',
                'expected_results': 'Observe "MBA COS2 rate out of range (from 1-100)" in output'},
            7: {'step_details': 'Allocate COS for the given cores',
                'expected_results': 'Observe "Allocation configuration altered." in output'},
            8: {'step_details': 'Unable to allocate COS for the unknown/offline cores',
                'expected_results': 'Observe "Core number or class id is out of bounds!" in output'},
            9: {'step_details': 'Allocate COS for the given pids',
                'expected_results': 'Observe "Allocation configuration altered." in output'},
            10: {'step_details': 'Unable to allocate COS for the invalid/unknown pids',
                 'expected_results': 'Observe "Task ID number or class id is out of bounds!" in output'}
        }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtMbaAllocationMemory

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtMbaAllocationMemory, self).__init__(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._num_sockets = int(self._common_content_lib.execute_sut_cmd(self.NUM_OF_SOCKETS_CMD, self.NUM_OF_SOCKETS_CMD,
                                                                         self._command_timeout))

    def prepare(self):
        # type:
        # () -> None
        """
        Test preparation/setup
        """
        super(RdtMbaAllocationMemory, self).prepare()

    def execute(self):
        """
        This method executes the below:
        1. Restore default allocation
        2. Verify MBA capability is detected on platform
        3. Verify setting MBA COS definition to 50%
        4. Verify setting MBA COS definition to 20%
        5. Verify setting MBA COS definition to 80%
        6. Unable to set MBA COS definition to invalid value
        7. Allocate COS for the given cores
        8. Unable to allocate COS for the unknown/offline cores
        9. Allocate COS for the given pids
        10. Unable to allocate COS for the invalid/unknown pids

        :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(1)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self._rdt.verify_mba_capability()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self._rdt.set_mba_rate(self.COS_ARG1, self.COS_ARG1_VALUE, self._num_sockets)
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self._rdt.set_mba_rate(self.COS_ARG1, self.COS_ARG2_VALUE, self._num_sockets)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        self._rdt.set_mba_rate(self.COS_ARG1, self.COS_ARG3_VALUE, self._num_sockets)
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        self._rdt.set_mba_rate(self.COS_ARG1, self.COS_ARG4_VALUE, self._num_sockets)
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        core_association = self._rdt.change_bit_mask_value(self.SET_CORE_ASSOCIATION_CMD.format
                                                          (self.CORE_ARG1, self.CORE_ARG1_VALUE, self.CORE_ARG2_VALUE))

        if self._rdt.BIT_MASKING_SUCCESSFUL_INFO not in core_association:
            raise content_exceptions.TestFail("Unable to set Core Association, '{}'".format(
                self._rdt.BIT_MASKING_SUCCESSFUL_INFO))

        self._rdt.check_l3ca_core_definitions(self._rdt.CHECK_L3CA_CMD, self.CORE.format(self.CORE_ARG1_VALUE), self.EXP_COS_VALUE)
        self._rdt.check_l3ca_core_definitions(self._rdt.CHECK_L3CA_CMD, self.CORE.format(self.CORE_ARG2_VALUE), self.EXP_COS_VALUE)
        self._log.info("Successfully Set Core Association")
        self._test_content_logger.end_step_logger(7, return_val=True)

        self._test_content_logger.start_step_logger(8)
        core_assigned_to_invalid = self.os.execute(self.SET_UNKNOWN_CORE_ASSOCIATION_CMD.
                                             format(self.CORE_ARG1, self.CORE_ARG3_VALUE), self._command_timeout)
        self._log.debug("{} command output is:{},{}".format(self.SET_UNKNOWN_CORE_ASSOCIATION_CMD.
                                             format(self.CORE_ARG1, self.CORE_ARG3_VALUE),
                                             core_assigned_to_invalid.stdout,core_assigned_to_invalid.stderr))
        if self.ERR_CORE_INFO not in core_assigned_to_invalid.stdout:
            raise content_exceptions.TestFail("Unable to allocate COS for the unknown/offline cores, '{}'".
                                              format(self.ERR_CORE_INFO))
        self._log.info("COS assigned to unknown/offline Cores")
        self._test_content_logger.end_step_logger(8, return_val=True)

        self._test_content_logger.start_step_logger(9)
        pid_association = self._rdt.change_bit_mask_value(self.SET_PID_ASSOCIATION_CMD.
                                                            format(self.PID_VALUE, self.PID_ARG1_VALUE))
        if self._rdt.BIT_MASKING_SUCCESSFUL_INFO not in pid_association:
            raise content_exceptions.TestFail("Unable to set Process ID Association, '{}'".
                                              format(self._rdt.BIT_MASKING_SUCCESSFUL_INFO))
        self._log.info("Succesfully set process association")
        self._test_content_logger.end_step_logger(9, return_val=True)

        self._test_content_logger.start_step_logger(10)
        pid_associate_to_invalid = self.os.execute(self.SET_PID_ASSOCIATION_CMD.format
                                                     (self.PID_VALUE, self.PID_ARG2_VALUE), self._command_timeout)
        self._log.debug("{} command output is {},{}".format(self.SET_PID_ASSOCIATION_CMD.format
                                                     (self.PID_VALUE, self.PID_ARG2_VALUE),
                                                     pid_associate_to_invalid.stdout, pid_associate_to_invalid.stderr))
        if self.PID_ASSOCIATION_CMD_INFO not in pid_associate_to_invalid.stdout:
            raise content_exceptions.TestFail("Unable to set Core Association, '{}'".
                                              format(self.PID_VALUE, self.PID_ARG2_VALUE))
        self._log.info("SuccesfullY set Process association to Invalid Core")
        self._test_content_logger.end_step_logger(10, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtMbaAllocationMemory.main() else Framework.TEST_RESULT_FAIL)
