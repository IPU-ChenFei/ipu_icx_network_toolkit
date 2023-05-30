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


class DpdkDts(DpdkCommon):
    """
    HPALM ID : 80097-PI_DPDK_DTS_L

    This test case is to validate those key DPDK test sutie cases (L2fwd/L3fwd/RX TX callbacks)
    RXTX_callbacks: The RX/TX Callbacks sample application is a packet forwarding application that demonstrates the
    use of user defined callbacks on received and transmitted packets.
    The application performs a simple latency check, using callbacks, to determine the time packets spend
    within the application.
    L2 forward: The L2 Forwarding sample application is a simple example of packet processing using the Data Plane
     Development Kit (DPDK). It is intended as a demonstration of the basic components of a DPDK forwarding application.
    The L3 Forwarding application is a simple example of packet processing using the DPDK.
    The application performs L3 forwarding.
    """
    TEST_CASE_ID = ["H80097", "PI_DPDK_DTS_L"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Install DPDK in sut and Create Hugepages and port bind',
            'expected_results': 'DPDK is installed, Hugepages created successfully and port are bind successfully'},
        2: {'step_details': 'Compiling the Application and run L2fwd test',
            'expected_results': 'The L2fwd test can be launched without error/failure'},
        3: {'step_details': 'Compiling the Application and run L3fwd test',
            'expected_results': 'The L3fwd test can be launched without error/failure'},
        4: {'step_details': 'Compiling the Application and run rxtx_callbacks test for 30 min',
            'expected_results': 'The rxtx_callbacks test can be launched without error/failure and cpu usage is '
                                'close to 100%'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of DpdkDts

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(DpdkDts, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._dpdk_install = InstallAndVerifyDpdk(test_log, arguments, cfg_opts)
        self.dpdk_path = None

    def prepare(self):
        # type: () -> None
        """This method installs the DPDK on sut and verify if it is installed properly."""
        self._test_content_logger.start_step_logger(1)
        self._dpdk_install.prepare()  # Prepare of DPDK Installation
        self._dpdk_install.execute()  # Execute of DPDK installation
        self.dpdk_path = self._dpdk_install.DPDK_INSTALLATION_PATH
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This method runs l2fwd, l3fwd and rxtx callbacks test

        :return: True is Test case pass
        """
        # Run l2fwd test
        self._test_content_logger.start_step_logger(2)
        self.build_and_run_l2fwd_test(self.dpdk_path)
        self._test_content_logger.end_step_logger(2, return_val=True)
        # Run l3fwd test
        self._test_content_logger.start_step_logger(3)
        self.build_and_run_l3fwd_test(self.dpdk_path)
        self._test_content_logger.end_step_logger(3, return_val=True)
        # Run RXTX callback test
        self._test_content_logger.start_step_logger(4)
        self.build_and_run_rxtx_test(self.dpdk_path)
        self._test_content_logger.end_step_logger(4, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if DpdkDts.main() else Framework.TEST_RESULT_FAIL)
