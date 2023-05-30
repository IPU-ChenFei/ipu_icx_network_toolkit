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

import re
import sys

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_base_test_case
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions


class RdtMbaAllocationMemoryMemTesterRdtset(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow ID : G60242.0 - PI_RDT_B_MBAAllocation_Memory_memtester_rdtset
    This test case verify MBA Set COS definition command and verify MBA via rdtset tool when memtester is running
    """
    TEST_CASE_ID = ["G60242.0 - PI_RDT_B_MBAAllocation_Memory_memtester_rdtset"]
    RDT_SET_CMD = 'rdtset -t "mba={};cpu=5-6" -c 5-6 memtester 10M'
    MBA_RATE_VALUE = "50"
    MBA_INVALID_RATE_VALUE = "200"
    STEP_DATA_DICT = \
        {
            1: {'step_details': 'Restore default allocation',
                'expected_results': 'Restore RDT to default monitoring is successful'},
            2: {'step_details': 'Run command with provided MBA rate ',
                'expected_results': 'Observe in pqos output MBA COS14 => 50% available '},
            3: {'step_details': 'Unable to run command with invalid MBA rate ',
                'expected_results': 'Observe "Invalid RDT parameters" in output '}
        }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtMbaAllocationMemoryMemTesterRdtset

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtMbaAllocationMemoryMemTesterRdtset, self).__init__(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """
        Test preparation/setup
        """
        super(RdtMbaAllocationMemoryMemTesterRdtset, self).prepare()
        self._install_collateral.install_memtester_tool_to_sut()
        self._rdt.install_rdt()

    def execute(self):
        """
        This method executes the below:
        1. Restore default allocation
        2. Run command with provided MBA rate and Verify Cache allocation
        3. Unable to run command with invalid MBA rate

        :raise:  ContentException if match not found.
        :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(1)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self.os.execute_async(self.RDT_SET_CMD.format(self.MBA_RATE_VALUE))
        command_result = self._common_content_lib.execute_sut_cmd(self._rdt.CHECK_L3CA_CMD,
                                                                  self._rdt.CHECK_L3CA_CMD,
                                                                  self._command_timeout)
        self._log.debug("{} Command output : {}".format(self._rdt.CHECK_L3CA_CMD,command_result))
        if not re.search(self._rdt.PQOS_SUCCESSFULL_INFO.format(self.MBA_RATE_VALUE), command_result):
            raise content_exceptions.TestFail("Failed to Observe Pqos Output")
        self._log.info("Successfully Observed Pqos Output {}".format(self._rdt.PQOS_SUCCESSFULL_INFO.
                                                                     format(self.MBA_RATE_VALUE)))
        self._rdt.stop_memtester_tool()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        command_result = self.os.execute(self.RDT_SET_CMD.format(self.MBA_INVALID_RATE_VALUE), self._command_timeout)
        if not re.search(self._rdt.PQOS_INVALID_SUCCESFUL_INFO, command_result.stderr):
            raise content_exceptions.TestFail("Failed to Observe the Output, Result in {}:".
                                              format(self.RDT_SET_CMD.format(self.MBA_INVALID_RATE_VALUE)))
        self._log.info("Observed Invalid RDT Parameter in the output")
        self._test_content_logger.end_step_logger(3, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtMbaAllocationMemoryMemTesterRdtset.main() else Framework.TEST_RESULT_FAIL)
