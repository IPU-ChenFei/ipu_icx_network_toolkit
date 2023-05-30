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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib.test_content_logger import TestContentLogger
from src.security.tests.hqm.hqm_common import HqmBaseTest
from src.lib import content_exceptions


class HqmDriverLibraryInstallation(HqmBaseTest):
    """
    HPQC ID : H79972-PI_SPR_HQM_Driver_Library_Installation_L
    This Test case HQM Driver Library Installation in the SUT
    """
    BIOS_CONFIG_FILE = "../hqm_driver_enable_bios.cfg"
    TEST_CASE_ID = ["H79972-PI_SPR_HQM_Driver_Library_Installation_L"]

    step_data_dict = {1: {'step_details': 'Enable Intel Vt-d and  Interrupt remapping, Compile dlb and libdlb, '
                                          'generate dlb2.ko kernel file ',
                          'expected_results': 'Verify Vt-d Interrupt remapping, Verify HQM driver installation'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of HqmDriverLibraryInstallation

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.hqm_driver_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(HqmDriverLibraryInstallation, self).__init__(test_log, arguments, cfg_opts, self.hqm_driver_bios_enable)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestFail("This test is Supported only on Linux")

    def prepare(self):
        # type: () -> None
        """
        This function enable Vt-d and Interrupt remapping bios knobs.
        """
        super(HqmDriverLibraryInstallation, self).prepare()

    def execute(self):
        """
        This function calling hqm installation and verify it is installed successfully

        :return: True if installed successfully else false
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self.install_hqm_driver_libaray()
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if HqmDriverLibraryInstallation.main() else Framework.TEST_RESULT_FAIL)
