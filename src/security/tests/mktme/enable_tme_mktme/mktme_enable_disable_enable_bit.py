#!/usr/bin/env python
##########################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and
# proprietary and confidential information of Intel Corporation and its
# suppliers and licensors, and is protected by worldwide copyright and trade
# secret laws and treaty provisions. No part of the Material may be used,copied,
# reproduced, modified, published, uploaded, posted, transmitted, distributed,
# or disclosed in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################


import os
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions
from src.security.tests.mktme.mktme_common import MktmeBaseTest


class MktmeEnableDisableBit(MktmeBaseTest):
    """
    Glasgow ID : G59526 MKTME_Enable_in-band_Disable_with_enabling_bit
    Phoenix ID : P18014070238 MKTME cannot be disabled by changing 'enabling bit' after it is enabled
    
    This Test case is enabling TME and MKTME BIOS Knobs and verify read and write msr values
    """
    BIOS_CONFIG_FILE = "../security_tme_mktme_bios_enable.cfg"
    TEST_CASE_ID = ["G59526.2 - MKTME_Enable_in-band_Disable_with_enabling_bit",
                    "P18014070238 - MKTME cannot be disabled by changing 'enabling bit' after it is enabled"]

    STEP_DATA_DICT = {1: {'step_details': 'Enable TME and MKTME Bios Knobs',
                          'expected_results': 'Verify TME and MKTME Bios Knobs set'},
                      2: {'step_details': 'Get intial reading for MSR 0x982 e.g itp.msr(0x982)',
                          'expected_results': 'Verify initial reading of msr value is 0x100060000000B'},
                      3: {'step_details': 'Write to MSR 0x982 e.g itp.msr(0x982, 0)',
                          'expected_results': 'Verify the output is IPC_Error: MSR_Access_Faulted messages'},
                      4: {'step_details': 'Get second reading for MSR 0x982 e.g itp.msr(0x982)',
                          'expected_results': 'Verify second reading of msr value is 0x100060000000B'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of MktmeEnableDisableBit

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.tme_mktme_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(MktmeEnableDisableBit, self).__init__(test_log, arguments, cfg_opts,self.tme_mktme_bios_enable)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """
        This function verify platform supporting the MKTME and
        Enabling TME and MK-TME Bios knobs.

        :raise: raise content_exceptions.TestNAError if there is any error while check CPU SKU support of MK-TME
        """
        self._test_content_logger.start_step_logger(1)
        # Verify platform will support MKTME or not
        if not self.verify_mktme():
            raise content_exceptions.TestNAError("This CPU SKU does not support for MK-TME")
        self._log.info("SUT supports MK-TME Bios Knob")
        # Enabling TME and MKTME BIOS Knobs
        super(MktmeEnableDisableBit, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        check the TME and MKTME MSR Values for read & write and verify read values

        :return True if values are read as expected after writing else false if not same
        """

        self._test_content_logger.start_step_logger(2)
        # Read the value from msr register and verify the value returned
        self.msr_read_and_verify(self.MSR_TME_ADDRESS, self.ENABLE_TME_MSR_VALUE)
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._test_content_logger.start_step_logger(3)
        # Write the value provided to the msr register
        self.msr_write_values(self.MSR_TME_ADDRESS, self.MSR_WRITE_VAL)
        self._test_content_logger.end_step_logger(3, return_val=True)
        self._test_content_logger.start_step_logger(4)
        # Read the value from msr register and verify the value returned
        self.msr_read_and_verify(self.MSR_TME_ADDRESS, self.ENABLE_TME_MSR_VALUE)
        self._test_content_logger.end_step_logger(4, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MktmeEnableDisableBit.main()
             else Framework.TEST_RESULT_FAIL)
