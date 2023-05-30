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


class WriteReadMbaMsrRegister(content_base_test_case.ContentBaseTestCase):
    """
    HPQC ID : H79579-PI_RDT_C_MBA_Register_Written_Read_Coherence_L

    This test case aims to install MSR Tools if it is not installed and check the write & read mba msr register
    to verify the value result coherence.
    """

    TEST_CASE_ID = ["H79579", "PI_RDT_C_MBA_Register_Written_Read_Coherence_L"]
    step_data_dict = {
        1: {'step_details': 'Verify if MSR Tool is installed sut',
            'expected_results': 'Verified installation successfully'},
        2: {'step_details': 'Test all values greater than or equal to 10 (decimal) and less than 39 (decimal) by '
                            'writing and reading into msr for all register 0xd50 to 0xd57',
            'expected_results': 'Values greater than or equal to 10 (decimal) and less than 39 (decimal) written to '
                                'the MBA delay value (Bits [15:0]) might be read back as 10 percent.'}}

    def __init__(self, test_log, arguments, cfg_opts):

        """
        Create an instance of WriteReadMbaMsrRegister

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(WriteReadMbaMsrRegister, self).__init__(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("MSR installation is not implemented for the os: {}".format(
                self.os.os_type))

    def prepare(self):  # type: () -> None
        """Test preparation/setup and install the rdt tool to sut"""
        super(WriteReadMbaMsrRegister, self).prepare()
        self._rdt.install_rdt()

    def execute(self):
        """
        This method executes the below:
        1. Verify if MSR is installed, If not, it will install
        2. Store values greater than 10 and less than 39 in msr - wrmsr -p 0 0xd51 10
        3. Read value that is stored in msr - 'rdmsr -p 0 0xd51'
        4. Test all values greater than or equal to 10 (decimal) and less than 39 (decimal) by writing and reading
        into msr for all register 0xd50 to 0xd57
        :return: True if test case pass
        """

        self._test_content_logger.start_step_logger(1)
        self._rdt.verify_msr_tools()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self._rdt.MSR_OUTPUT_VALUES = self._rdt.write_read_msr(self._rdt.READ_MSR_VALUES)
        for value in self._rdt.MSR_OUTPUT_VALUES:
            self._rdt.compare_write_read_msr(value)
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if WriteReadMbaMsrRegister.main() else Framework.TEST_RESULT_FAIL)
