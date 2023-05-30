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
import re

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.hqm.hqm_common import HqmBaseTest


class HqmDataMovementPf(HqmBaseTest):
    """
    HPQC ID : H79973-PI_SPR_HQM_Data_Movement_via_PF_L
    This Test case HQM Data Movement via PF in the SUT
    """
    TEST_CASE_ID = ["H79973-PI_SPR_HQM_Data_Movement_via_PF_L"]
    BIOS_CONFIG_FILE = "../hqm_driver_enable_bios.cfg"
    LDB_TRAFFIC_FILE_CMD = r"ldb_traffic -n {} -w poll"
    REGEX_TX = r"Sent\s(\d+)\sevents"
    REGEX_RX = r"Received\s(\d+)\sevents"
    STEP_DATA_DICT = {1: {'step_details': 'HQM Driver Installation on SUT',
                          'expected_results': 'Verify HQM driver installation'},
                      2: {'step_details': 'Execute ldb_traffic file "ldb_traffic -n 1024 -w poll"',
                          'expected_results': 'Verify tx/rx should match'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of HqmDataMovementPf

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.hqm_driver_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(HqmDataMovementPf, self).__init__(test_log, arguments, cfg_opts, self.hqm_driver_bios_enable)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._ldb_traffic_data = self._common_content_configuration.get_hqm_ldb_traffic_data()
        self.LDB_TRAFFIC_FILE_CMD = r"ldb_traffic -n {} -w poll".format(self._ldb_traffic_data)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestFail("This test is Supported only on Linux")

    def prepare(self):
        # type: () -> None
        """
        This function verify intel next kernel installed in the sut and enable Vt-d and Interrupt remapping bios knobs.
        """
        super(HqmDataMovementPf, self).prepare()

    def execute(self):
        """
        This function calling hqm installation and verify it is installed successfully and execute ldb_traffic command

        :return: True if test case pass else fail
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self.verify_hqm_dlb_kernel()
        self.install_hqm_driver_libaray()
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)
        # Step logger start for Step  2
        self._test_content_logger.start_step_logger(2)
        self.execute_ldb_traffic()
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if HqmDataMovementPf.main() else Framework.TEST_RESULT_FAIL)
