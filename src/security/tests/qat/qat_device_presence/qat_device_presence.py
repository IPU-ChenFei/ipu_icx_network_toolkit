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

from src.lib.test_content_logger import TestContentLogger
from src.security.tests.qat.qat_common import QatBaseTest


class QatDevicePresence(QatBaseTest):
    """
    HPQC ID : H79557
    This Test case execute lspci command to check QAT device presence
    """
    TEST_CASE_ID = ["H79557"]

    step_data_dict = {1: {'step_details': 'Check QAT tool installation status',
                          'expected_results': "Install QAT Tool if not installed"},
                      2: {'step_details': 'Check QAT device presence',
                          'expected_results': 'SUT should show QAT Acceleration devices'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of QatDevicePresence

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(QatDevicePresence, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        Pre-checks if the sut is alive or not.
        """
        super(QatDevicePresence, self).prepare()

    def execute(self):
        """
        This function check QAT device presence on SUT

        :return: True if get the QAT device presence test case pass else fail
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        if not self.qat_device_status():
            self.install_qat_tool()
        self._test_content_logger.end_step_logger(1, return_val=True)
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        self.qat_device_presence()
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if QatDevicePresence.main() else Framework.TEST_RESULT_FAIL)
