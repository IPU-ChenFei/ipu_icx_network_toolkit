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
from src.lib.test_content_logger import TestContentLogger


class InstallAndVerifyDpdk(DpdkCommon):
    """
    HPALM ID : H80087-PI_DPDK_Installation_L
    The purpose of this test case is to verify if the DPDK file has been downloaded and installed successfully on SUT.
    """
    TEST_CASE_ID = ["H80087", "PI_DPDK_Installation_L"]
    step_data_dict = {
        1: {'step_details': 'Install DPDK in sut using make and Verify if the DPDK folders are present',
            'expected_results': 'DPDK is installed successfully and all DPDK folders are present'},
        2: {'step_details': 'Create Hugepages and port bind',
            'expected_results': 'Hugepages created successfully and port are bind successfully'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of InstallAndVerifyDpdk

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(InstallAndVerifyDpdk, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """Test preparation/setup """
        pass
        #super(InstallAndVerifyDpdk, self).prepare()

    def execute(self):
        """
        This method installs the DPDK on sut and verify if it is installed properly.
        """
        self._test_content_logger.start_step_logger(1)
        self.install_and_verify_dpdk()
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._test_content_logger.start_step_logger(2)
        self.hugepages_setup_and_port_bind()
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if InstallAndVerifyDpdk.main() else Framework.TEST_RESULT_FAIL)
