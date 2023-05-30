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
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.lib.test_content_logger import TestContentLogger


class EnableTxt(TxtBaseTest):
    """
    Glasgow ID : G58991.7-Enable TXT

    This Test case is to enable TXT knobs in BIOS and verify all knobs are set properly
    """
    TEST_CASE_ID = ["G58991.7", "Enable_TXT"]
    BIOS_CONFIG_FILE = "security_txt_bios_knobs_enable.cfg"
    STEP_DATA_DICT = {
        1: {'step_details': 'Enable TXT supported BIOS knobs',
            'expected_results': 'TXT Knobs are set successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of EnableTxt

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.enable_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(EnableTxt, self).__init__(test_log, arguments, cfg_opts, self.enable_bios_config_file)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """Test preparation/setup """
        super(EnableTxt, self).prepare()

    def execute(self):
        """
        This function is to verify the BIOS knobs are set properly and pass test case if everything works fine.
        """
        self._test_content_logger.start_step_logger(1)
        self.enable_and_verify_bios_knob()  # Enable and verify TXT bios knobs
        self._test_content_logger.end_step_logger(1, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if EnableTxt.main() else Framework.TEST_RESULT_FAIL)
