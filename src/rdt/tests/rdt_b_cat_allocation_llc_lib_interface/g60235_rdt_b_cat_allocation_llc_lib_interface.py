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

from src.lib.test_content_logger import TestContentLogger
from src.lib import content_base_test_case
from src.provider.cpu_info_provider import CpuInfoProvider
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions


class RdtCatAllocationLlcLibInterface(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow ID : G60235.0-PI_RDT_B_CATAllocation_LLC_LibInterface

    This test case aims to install RDT if it not installed and
    verify L3 CAT Set COS definition and Set COS association for core/tasks and Reset via pqos OS interface
    """
    TEST_CASE_ID = ["G60235.0-PI_RDT_B_CATAllocation_LLC_LibInterface"]
    COS_ARG1 = "1"
    COS_ARG2 = "2"
    COS_ARG3 = "3"
    COS7_VALUE = "7"
    OFFLINE_CORES = "1000"
    EXPECTED_VALUE = "COS7"
    UNKNOWN_PID = "9999999999"
    COS_BIT_MASK_CMD = "pqos -I -e 'llc:{}={};llc:{}={}'"
    ERR_COS_BIT_MASK_CMD = "pqos -I -e llc:{}={}"
    CORE_ALLOCATION_CMD = "pqos -I -a llc:{}={},{}".format(COS7_VALUE, COS_ARG1, COS_ARG3)
    ALLOCATION_CMD_for_OFFLINE_CORES = "pqos -I -a llc:{}={}".format(COS7_VALUE, OFFLINE_CORES)
    ALLOCATE_COS_CMD_FOR_GIVEN_PIDS = "pqos -I -a pid:2={}"
    ALLOCATION_FAILURE_STRING = "Core number or class id is out of bounds!"

    MIN_SOCKET = 2
    STEP_DATA_DICT = {
        1: {'step_details': 'Verify RDT is installed in sut',
            'expected_results': 'Installation od RDT is verified successfully'},
        2: {'step_details': 'Restore default monitoring',
            'expected_results': 'Restore to default monitoring is successful'},
        3: {'step_details': 'Check actual L3CA COS definitions',
            'expected_results': 'L3CA COS value is equals to as default COS mask value'},
        4: {'step_details': 'Change bit-mask value of COS definition',
            'expected_results': 'Mask value is changed successfully'},
        5: {'step_details': 'Check actual L3CA COS definitions value is changed',
            'expected_results': 'L3CA COS value is changed accordingly'},
        6: {'step_details': 'Change bit-mask value of COS definition with value more than 28 bits',
            'expected_results': 'Unable to set up allocation COS with a bitmask more than 28 bits'},
        7: {'step_details': 'Allocate COS for the given cores 1 and 3',
            'expected_results': 'Core Allocation Set successfully'},
        8: {'step_details': 'Verify Core Allocation',
            'expected_results': 'Cores 1 and 3 are assigned to COS 7'},
        9: {'step_details': 'Check that its Unable to allocate COS for the unknown/offline cores',
            'expected_results': 'Detected "Core number or class id is out of bounds" String in output'},
        10: {'step_details': 'Allocate COS for the given pids ',
             'expected_results': 'COS Allocation for given pids verfied successfully'},
        11: {'step_details': 'Verify if its Unable to allocate COS for the invalid/unknown pids ',
             'expected_results': 'Verified that ts Unable to allocate COS for the invalid/unknown pids'},
        12: {'step_details': 'Restore default monitoring',
             'expected_results': 'Restore to default monitoring is successful'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtCatAllocationLlcLibInterface

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtCatAllocationLlcLibInterface, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def prepare(self):  # type: () -> None
        """Test preparation/setup and install the stress tool to sut"""
        super(RdtCatAllocationLlcLibInterface, self).prepare()

    def execute(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. Check actual L3CA COS definitions by running command  pqos -s
        4. Change Bit mask value like: "pqos -e 'llc:1=0xf;llc:2=0xf0'"
        5. Check L3CA COS definitions after changes by running command pqos -s
        6. Check if its Unable to set up allocation COS with a bitmask more than
           28 bits by running : "pqos -e llc:2=0xffffffff" and Observe "SOCKET 0
           L3CA COS2 - FAILED!" and "Allocation configuration error!" in output
        7. Allocate COS for the given cores ,Run "pqos -a llc:7=1,3" to set core association.
        8. Verity core association with "pqos -s" and check "Allocation configuration altered."
           in output ,also Cores 1 and 3 are assigned to COS 7.
        9. Check if its Unable to allocate COS for the unknown/offline cores by
           running : "pqos -a llc:7=1000" to set core association and check "Core number or
           class id is out of bounds!" in output.
        10. Restore default allocation:  pqos -R
        11. Check actual L3CA COS definitions by running command pqos -s

        :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(1)
        self._rdt.install_rdt()
        self._test_content_logger.end_step_logger(1, return_val=True)

        # Restore rdt monitor to default mode
        self._test_content_logger.start_step_logger(2)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Check all L3CA default COS value
        self._test_content_logger.start_step_logger(3)
        self._rdt.verify_l3ca_capability(interface=True)
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Change Bit mask values of respective cos definitions
        self._test_content_logger.start_step_logger(4)
        bit_mask_output = self._rdt.change_bit_mask_value(
            self.COS_BIT_MASK_CMD.format(self.COS_ARG1, self._rdt.COS_ARG1_VALUE,
                                         self.COS_ARG2, self._rdt.COS_ARG2_VALUE))
        self._test_content_logger.end_step_logger(4, return_val=True)

        # verify COS bit mask value is changed successfully
        self._test_content_logger.start_step_logger(5)
        self._rdt.verify_bit_mask_value(bit_mask_output, interface=True)
        self._test_content_logger.end_step_logger(5, return_val=True)

        # Change and observe that its Unable to set up allocation COS with a bitmask more than 28 bits
        self._test_content_logger.start_step_logger(6)
        self._rdt.check_allocation_config_error(
            self.ERR_COS_BIT_MASK_CMD.format(self.COS_ARG2, self._rdt.COS_ARG3_VALUE))
        self._test_content_logger.end_step_logger(6, return_val=True)

        # Allocate COS for the given cores
        self._test_content_logger.start_step_logger(7)
        self._log.info("Allocating COS for the given cores {} and {}".format(self.COS_ARG1, self.COS_ARG3))
        command_output = self._common_content_lib.execute_sut_cmd(self.CORE_ALLOCATION_CMD, self.CORE_ALLOCATION_CMD,
                                                                  self._command_timeout)
        self._log.debug("command output {}".format(command_output))
        if not re.search(self._rdt.BIT_MASKING_SUCCESSFUL_INFO, command_output):
            raise content_exceptions.TestFail("{} not found in the output : {}".
                                              format(self._rdt.BIT_MASKING_SUCCESSFUL_INFO, command_output))
        self._test_content_logger.end_step_logger(7, return_val=True)

        # Verity core association with "pqos -s"
        self._test_content_logger.start_step_logger(8)
        self._rdt.check_l3ca_core_definitions(self._rdt.CHECK_L3CA_CMD, self.COS_ARG1, self.EXPECTED_VALUE)
        self._rdt.check_l3ca_core_definitions(self._rdt.CHECK_L3CA_CMD, self.COS_ARG3, self.EXPECTED_VALUE)
        self._test_content_logger.end_step_logger(8, return_val=True)

        # Check that its Unable to allocate COS for the unknown/offline cores
        self._test_content_logger.start_step_logger(9)
        command_output = self.os.execute(self.ALLOCATION_CMD_for_OFFLINE_CORES, self._command_timeout)
        if self.ALLOCATION_FAILURE_STRING not in command_output.stdout:
            raise content_exceptions.TestFail("{} not found in the output : {}".
                                              format(self.ALLOCATION_FAILURE_STRING, command_output))
        self._test_content_logger.end_step_logger(9, return_val=True)

        # Allocate COS for the given pids
        self._test_content_logger.start_step_logger(10)
        self._rdt.change_bit_mask_value(self.ALLOCATE_COS_CMD_FOR_GIVEN_PIDS.format(self.COS_ARG1))
        self._test_content_logger.end_step_logger(10, return_val=True)

        # Verify if its Unable to allocate COS for the invalid/unknown pids
        self._test_content_logger.start_step_logger(11)
        self._rdt.check_allocation_config_error_for_unknown_pid(
            self.ALLOCATE_COS_CMD_FOR_GIVEN_PIDS.format(self.UNKNOWN_PID))
        self._test_content_logger.end_step_logger(11, return_val=True)

        # Restore rdt monitor to default mode
        self._test_content_logger.start_step_logger(12)
        self._rdt.restore_default_rdt_monitor(interface=True)
        self._test_content_logger.end_step_logger(12, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtCatAllocationLlcLibInterface.main() else Framework.TEST_RESULT_FAIL)
