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


class RdtDefineCosBitMaskSocket(content_base_test_case.ContentBaseTestCase):
    """
    HPQC ID : H79576-PI_RDT_A_CATDefineCOSBitmask_Sockets_L

    This test case aims to install RDT if it not installed and
    Checks possibility of defining the allocation classes with bitmask for
    CPU cache resources in multiple sockets via pqos -e
    """

    TEST_CASE_ID = ["H79576-PI_RDT_A_CATDefineCOSBitmask_Sockets_L"]
    COS_ARG1 = "1"
    COS_ARG2 = "2"
    COS_ARG3 = "3"
    COS_ARG1_VALUE = "0xf"
    COS_ARG2_VALUE = "0xff0"
    COS_ARG3_VALUE = "0x3c"
    CHANGE_BIT_MASK_CMD = "pqos -e 'llc:{}={};llc@0,1:{}={};llc@1:{}={}'".format(COS_ARG1, COS_ARG1_VALUE,
                                                                                 COS_ARG2, COS_ARG2_VALUE,
                                                                                 COS_ARG3, COS_ARG3_VALUE)
    MIN_SOCKET = 2
    step_data_dict = {
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
        6: {'step_details': 'Restore default monitoring',
            'expected_results': 'Restore to default monitoring is successful'},
        7: {'step_details': 'Check actual L3CA COS definitions',
            'expected_results': 'L3CA COS value is equals to as default COS mask value'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtDefineCosBitMaskSocket

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtDefineCosBitMaskSocket, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))
        self._num_sockets = int(self._common_content_lib.execute_sut_cmd("grep 'physical id' /proc/cpuinfo | "
                                                                         "sort -u | wc -l", "Get socket cmd",
                                                                         self._command_timeout))
        if self._num_sockets < self.MIN_SOCKET:
            raise content_exceptions.TestFail("Execution of this test should be on sut with 2 or more sockets")

    def execute(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. Check actual L3CA COS definitions by running command  pqos -s
        4. Change Bit mask value like: pqos -e 'llc:1=0x000f;llc@0,1:2=0x0ff0;llc@1:3=0x3c'
        5. Check L3CA COS definitions after changes by running command pqos -s
        6. Restore default allocation:  pqos -R
        7. Check actual L3CA COS definitions by running command pqos -s

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
        self._rdt.run_l3ca_cmd_and_verify_default_cos_val()
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Change Bit mask values of respective cos definitions
        self._test_content_logger.start_step_logger(4)
        bit_mask_output = self._rdt.change_bit_mask_value(self.CHANGE_BIT_MASK_CMD)
        self._test_content_logger.end_step_logger(4, return_val=True)

        # verify COS bit mask value is changed successfully
        self._test_content_logger.start_step_logger(5)
        self._rdt.verify_bit_mask_value(bit_mask_output)
        self._test_content_logger.end_step_logger(5, return_val=True)

        # Restore rdt monitor to default mode
        self._test_content_logger.start_step_logger(6)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(6, return_val=True)

        # Check all L3CA default COS value
        self._test_content_logger.start_step_logger(7)
        self._rdt.run_l3ca_cmd_and_verify_default_cos_val()
        self._test_content_logger.end_step_logger(7, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtDefineCosBitMaskSocket.main() else Framework.TEST_RESULT_FAIL)
