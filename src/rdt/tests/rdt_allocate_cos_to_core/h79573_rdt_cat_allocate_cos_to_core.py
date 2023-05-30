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


class RdtAllocationCosToCore(content_base_test_case.ContentBaseTestCase):
    """
    HPQC ID : H79573-PI_RDT_A_CATAllocateCOStoCore_L, H55279-PI_RDT_A_CATAllocateCOStoCore

    This test case aims to install RDT if it not installed and
    Check possibility of associating classes to cores via pqos -a.
    """

    TEST_CASE_ID = ["H79573", "PI_RDT_A_CATAllocateCOStoCore_L", "H55279", "PI_RDT_A_CATAllocateCOStoCore"]
    CHECK_L3CA_CMD = "pqos -s"
    VAL_OF_CORE = "3"
    CORE = "Core {}".format(VAL_OF_CORE)
    EXP_VAL_BEFORE = "COS0"
    EXP_VAL_AFTER = "COS1"
    ALLOCATE_L3CACHE_TO_CORE_CMD = "pqos -a 'llc:1={}'".format(VAL_OF_CORE)
    step_data_dict = {
        1: {'step_details': 'Verify if RDT is installed sut',
            'expected_results': 'Verified installation'},
        2: {'step_details': 'Restore default monitoring',
            'expected_results': 'Restore to default monitoring is successful'},
        3: {'step_details': 'Check actual L3CA COS definitions',
            'expected_results': 'Actual {} COS value is 0'.format(CORE)},
        4: {'step_details': 'Allocate L3 cache memory for {} to COS1'.format(CORE),
            'expected_results': 'Allocation successful and MBR value should not exceed 1'},
        5: {'step_details': 'Check actual L3CA COS definitions',
            'expected_results': '{} COS value is 1'.format(CORE)},
        6: {'step_details': 'Restore default monitoring',
            'expected_results': 'Restore to default monitoring is successful'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtAllocationCosToCore

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtAllocationCosToCore, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def execute(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. Check actual L3CA COS definitions and core information: pqos -s
        4. Allocate L3 cache memory for core 3 to COS1: pqos -a 'llc:1=3'
        5. Check L3CA COS definitions after changes: pqos -s
        6. Restore default allocation:  pqos -R

        :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(1)
        self._rdt.install_rdt()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self._rdt.check_l3ca_core_definitions(self.CHECK_L3CA_CMD, self.CORE, self.EXP_VAL_BEFORE)
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self._log.info("Allocating L3 cache memory for '{}' to '{}'".format(self.CORE, self.EXP_VAL_AFTER))
        unmatched_value = self._common_content_lib.execute_cmd_and_get_unmatched_result(
            self.ALLOCATE_L3CACHE_TO_CORE_CMD, self._rdt.ALLOCATE_L3CACHE_INFO, self._rdt.ALLOCATION_SUCCESSFUL_INFO,
            self._command_timeout)
        if unmatched_value:
            raise content_exceptions.TestFail("{} did not find in the {} output".
                                              format(unmatched_value, self.ALLOCATE_L3CACHE_TO_CORE_CMD))
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        self._rdt.check_l3ca_core_definitions(self.CHECK_L3CA_CMD, self.CORE, self.EXP_VAL_AFTER)
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(6, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtAllocationCosToCore.main() else Framework.TEST_RESULT_FAIL)
