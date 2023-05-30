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

from src.dpdk.dpdk_common import DpdkCommon
from src.dpdk.tests.dpdk_installation import InstallAndVerifyDpdk
from src.lib.test_content_logger import TestContentLogger


class DpdkPollingModeTestStress(DpdkCommon):
    """
    HPALM ID : H80089 - PI_DPDK_PollingModeDriverTest_Stress_L

    This test case is to run packet forwarding test with DPDK mode for 15 hours.
    """
    TEST_CASE_ID = ["H80089", "PI_DPDK_PollingModeDriverTest_Stress_L"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Install DPDK in sut and Create Hugepages and port bind',
            'expected_results': 'DPDK is installed, Hugepages created successfully and port are bind successfully'},
        2: {'step_details': 'Run poll-mode driver test for 15 hours',
            'expected_results': 'The Forward statistics for port 0 and port 1 are fine'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of DpdkPollingModeTestStress

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(DpdkPollingModeTestStress, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._dpdk_install = InstallAndVerifyDpdk(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        This method installs the DPDK on sut and verify if it is installed properly.
        Create the hugepages and Binds the NIC ports
        """

        self._test_content_logger.start_step_logger(1)
        self._dpdk_install.prepare()  # Prepare of DPDK Installation
        self._dpdk_install.execute()  # Execute of DPDK installation
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This method runs testpmd test

        :return: True if test pass else False
        """
        # run testpmd test
        self._test_content_logger.start_step_logger(2)
        self.run_testpmd_stress(self._dpdk_install.DPDK_INSTALLATION_PATH)
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if DpdkPollingModeTestStress.main() else Framework.TEST_RESULT_FAIL)
