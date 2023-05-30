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
from src.lib.content_base_test_case import ContentBaseTestCase
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions


class PiRdtSetupAndInitialization(ContentBaseTestCase):
    """
    Glasgow ID : G60216.2-PI_RDT_0_Setup_&_Initialization

    This test case aims to install RDT on sut and verify the initialization commands.
    """
    TEST_CASE_ID = ["G60216.2-PI_RDT_0_Setup_&_Initialization"]
    CHECK_L3CA_CMD = "pqos -s"
    VAL_OF_CORE = "3"
    CORE = "Core {}".format(VAL_OF_CORE)
    DEFAULT_COS_VAL = "COS0"
    RESTORE_DEFAULT_CMD = "pqos -R"
    RESTORE_SUCCESSFUL_INFO = ["Allocation reset successful"]
    RESTORE_CMD_INFO = "Restore default monitor cmd"
    ALLOCATE_L3CACHE_TO_CORE_CMD = "pqos -a 'llc:1={}'".format(VAL_OF_CORE)
    EXP_VAL_BEFORE = "COS0"
    EXP_VAL_AFTER = "COS1"
    STEP_DATA_DICT = {
        1: {'step_details': 'Install RDT to sut',
            'expected_results': 'Installation successful'},
        2: {'step_details': 'Turn on RDT monitoring',
            'expected_results': 'Successfully fetched core status for cores 0-3'},
        3: {'step_details': 'Restore default monitoring',
            'expected_results': 'Restore to default monitoring is successful'},
        4: {'step_details': 'Check actual L3CA COS definitions',
            'expected_results': 'Actual {} COS value is 0'.format(CORE)},
        5: {'step_details': 'Allocate L3 cache memory for {} to COS1'.format(CORE),
            'expected_results': 'Allocation successful'},
        6: {'step_details': 'Check actual L3CA COS definitions',
            'expected_results': '{} COS value is 1'.format(CORE)},
        7: {'step_details': 'Restore default monitoring',
            'expected_results': 'Restore to default monitoring is successful'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of PiRdtSetupAndInitialization

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(PiRdtSetupAndInitialization, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def prepare(self):  # type: () -> None
        """
        Prepares the Sut for the Execution of TC
        """
        super(PiRdtSetupAndInitialization, self).prepare()

    def execute(self):
        """
        This method executes the below:
        1. Install RDT on Sut
        2. Turn on RDT monitoring to view the core status: 'pqos -m 'all:0,1,2,3' -t 10'
        3. Restore default monitoring: pqos -R
        4. Check actual L3CA COS definitions and core information: pqos -s
        5. Allocate L3 cache memory for core 3 to COS1: pqos -a 'llc:1=3'
        6. Check L3CA COS definitions after changes: pqos -s
        7. Restore default allocation:  pqos -R

        :return: True if test case pass
        :raise: content_exceptions.TestFail
        """
        self._test_content_logger.start_step_logger(1)
        self._rdt.install_rdt()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self._rdt.turn_on_rdt_monitoring()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self._log.info("Restoring default monitor")
        unmatched_value = self._common_content_lib.execute_cmd_and_get_unmatched_result(self.RESTORE_DEFAULT_CMD,
                                                                                        self.RESTORE_CMD_INFO,
                                                                                        self.RESTORE_SUCCESSFUL_INFO,
                                                                                        self._command_timeout)
        if unmatched_value:
            raise content_exceptions.TestFail("{} did not find in the {} output".format(unmatched_value,
                                                                                        self.RESTORE_DEFAULT_CMD))
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self._rdt.check_l3ca_core_definitions(self.CHECK_L3CA_CMD, self.CORE, self.EXP_VAL_BEFORE)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        self._log.info("Allocating L3 cache memory for '{}' to '{}'".format(self.CORE, self.EXP_VAL_AFTER))
        unmatched_value = self._common_content_lib.execute_cmd_and_get_unmatched_result(
            self.ALLOCATE_L3CACHE_TO_CORE_CMD, self._rdt.ALLOCATE_L3CACHE_INFO, self._rdt.ALLOCATION_SUCCESSFUL_INFO,
            self._command_timeout)
        if unmatched_value:
            raise content_exceptions.TestFail("{} did not find in the {} output".format(
                unmatched_value,
                self.ALLOCATE_L3CACHE_TO_CORE_CMD))
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        self._rdt.check_l3ca_core_definitions(self.CHECK_L3CA_CMD, self.CORE, self.EXP_VAL_AFTER)
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        self._log.info("Restoring default monitor")
        unmatched_value = self._common_content_lib.execute_cmd_and_get_unmatched_result(self.RESTORE_DEFAULT_CMD,
                                                                                        self.RESTORE_CMD_INFO,
                                                                                        self.RESTORE_SUCCESSFUL_INFO,
                                                                                        self._command_timeout)
        if unmatched_value:
            raise content_exceptions.TestFail("{} did not find in the {} output".format(unmatched_value,
                                                                                        self.RESTORE_DEFAULT_CMD))
        self._test_content_logger.end_step_logger(7, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiRdtSetupAndInitialization.main() else Framework.TEST_RESULT_FAIL)
