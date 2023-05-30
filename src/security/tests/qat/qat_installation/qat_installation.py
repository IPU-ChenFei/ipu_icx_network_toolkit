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

from src.lib.test_content_logger import TestContentLogger
from src.security.tests.qat.qat_common import QatBaseTest
from src.lib import content_exceptions


class QatInstallation(QatBaseTest):
    """
    HPQC ID : H79558/H79968
    This Test case install QAT TOOL in the SUT
    """
    TEST_CASE_ID = ["H79558-PI_SPR_QAT_Installation_L", "H79968-PI_SPR_QAT_Installation_L"]
    BIOS_CONFIG_FILE_DISABLE = "../vtd_bios_knob_disable.cfg"

    STEP_DATA_DICT = {1: {'step_details': 'Intel  VT for Directed I/O (VT-d) bios knob disable',
                          'expected_results': 'Verify Intel  VT for Directed I/O (VT-d) disabled successfully'},
                      2: {'step_details': 'QAT Installation',
                          'expected_results': 'Installation successful'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of QatInstallation

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.vtd_bios_disable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE_DISABLE)
        super(QatInstallation, self).__init__(test_log, arguments, cfg_opts, self.vtd_bios_disable)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """
        Pre-checks if the test case is applicable for RHEL Linux OS.
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        super(QatInstallation, self).prepare()
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This function calling qat installation and check the status of the QAT

        :return: True if installed successfully and getting the status as expected else false
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        self.install_qat_tool()
        if not self.qat_device_status():
            raise content_exceptions.TestFail("QAT Tool is not supported in this system")
        #  Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if QatInstallation.main() else Framework.TEST_RESULT_FAIL)
