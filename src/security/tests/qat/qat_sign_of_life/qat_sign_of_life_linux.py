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
import os
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.qat.qat_common import QatBaseTest


class SprQatSignOfLife(QatBaseTest):
    """
    HPQC ID : H79560-PI_SPR_QAT_signOfLifeTests_UserSpace_L
    This Test case execute the cpa_sample_code to get QAT Sign Of Life
    """
    CPA_SAMPLE_CODE_SIGN_OF_LIFE = r"./cpa_sample_code signOfLife=1"
    CONFIGURE_SPR_SIGN_OF_LIFE_CMD = r"./configure  --enable-icp-sriov=host && make uninstall"
    TEST_CASE_ID = ["H79560-PI_SPR_QAT_signOfLifeTests_UserSpace_L"]
    BIOS_CONFIG_FILE_DISABLE = "../vtd_bios_knob_disable.cfg"

    STEP_DATA_DICT = {1: {'step_details': 'Disable VT-d, Install QAT Tool and Check device installation status',
                          'expected_results': 'Verify VT-d bios disabled and QAT device status QAT Acceleration device'},
                      2: {'step_details': 'Execute ./cpa_sample_code signOfLife=1 on build folder to get '
                                          'QAT Sign Of Life',
                          'expected_results': 'Verify it is executed successfully the cpa_sample_code'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of SprQatSignOfLife

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.vtd_bios_disable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE_DISABLE)
        super(SprQatSignOfLife, self).__init__(test_log, arguments, cfg_opts, self.vtd_bios_disable)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """
        Pre-checks if the sut is alive or not.
        """
        super(SprQatSignOfLife, self).prepare()

    def execute(self):
        """
        This function check QAT Sign of Life on SUT

        :return: True if get the QAT data movement results successfully test case pass else fail
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self.install_qat_tool(configure_spr_cmd=self.CONFIGURE_SPR_SIGN_OF_LIFE_CMD)
        if not self.qat_device_status():
            raise content_exceptions.TestFail("QAT Tool does not supported in this system")
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        self.execute_cpa_sample_code(self.CPA_SAMPLE_CODE_SIGN_OF_LIFE)
        #  Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SprQatSignOfLife.main() else Framework.TEST_RESULT_FAIL)
