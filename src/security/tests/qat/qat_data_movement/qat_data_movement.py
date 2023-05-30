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
import os

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.qat.qat_common import QatBaseTest


class SprQatDataMovement(QatBaseTest):
    """
    HPQC ID : H79969-PI_SPR_QAT_Data_Movement_L
    This Test case execute the cpa_sample_code to get QAT data movement
    """
    CPA_SAMPLE_CODE_CONFIGURE = r"./cpa_sample_code"
    TEST_CASE_ID = ["H79969", "PI_SPR_QAT_Data_Movement_L"]
    BIOS_CONFIG_FILE_DISABLE = "../vtd_bios_knob_disable.cfg"

    step_data_dict = {1: {'step_details': 'Install QAT Tool and Check device installation status',
                          'expected_results': 'Verify QAT device status QAT Acceleration device'},
                      2: {'step_details': 'Execute ./cpa_sample_code on build folder to get QAT data movement',
                          'expected_results': 'Verify it is executed successfully the cpa_sample_code'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of SprQatDataMovement

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.vtd_bios_disable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE_DISABLE)
        super(SprQatDataMovement, self).__init__(test_log, arguments, cfg_opts, self.vtd_bios_disable)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        Pre-checks if the sut is alive or not.
        """
        super(SprQatDataMovement, self).prepare()

    def execute(self):
        """
        This function check QAT data movement on SUT

        :return: True if get the QAT data movement results successfully test case pass else fail
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self.install_qat_tool()
        if not self.qat_device_status():
            raise content_exceptions.TestFail("QAT Tool does not supported in this system")
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        self.execute_cpa_sample_code(self.CPA_SAMPLE_CODE_CONFIGURE)
        #  Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SprQatDataMovement.main() else Framework.TEST_RESULT_FAIL)
