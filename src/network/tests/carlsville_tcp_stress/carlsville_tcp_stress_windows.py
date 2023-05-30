#!/usr/bin/env python
##########################################################################
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
##########################################################################

import sys
import threading
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.test_content_logger import TestContentLogger
from src.network.networking_common import NetworkingCommon
from src.provider.driver_provider import NetworkDrivers


class CarlsvilleTcpStressWindows(NetworkingCommon):
    """
    HPQC ID : H91202-PI_Networking_Carlsville_TCPStress_W

    This Class is used to check the TCP through IPerf, by setting One Sut as iperf Server and other one as Iperf Client.
    """
    TEST_CASE_ID = ["H91202", "PI_Networking_Carlsville_TCPStress_W"]
    STEP_DATA_DICT = {
        1: {'step_details': "Copy Iperf folder on two SUTs and Install Iperf3 rpm package.",
            'expected_results': "Iperf3 app is installed on OS successfully."},
        2: {'step_details': "Set One Sut as server role by command: Iperf3 -s.",
            'expected_results': "Setting of One Sut as Iperf Server is Successful and Ready for Iperf Testing"},
        3: {'step_details': "Set another Sut as client role by command: Iperf3 -c <Server's ip address> -t 14400",
            'expected_results': "Setting of another Sut as Iperf Client is Successful and Ready for Iperf Testing."},
        }

    IPERF_EXEC_TIME = 14400

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of CarlsvilleTcpStressWindows

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(CarlsvilleTcpStressWindows, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.driver_inf_file = self._common_content_configuration.get_driver_inf_file_name(
            NetworkDrivers.CARLSVILLE_DRIVER_NAME)
        self.driver_device_id = self._common_content_configuration.get_driver_device_id(
            NetworkDrivers.CARLSVILLE_DRIVER_NAME)

    def prepare(self):  # type: () -> None
        """
        Prepares the System for the Execution of Test Case.
        """
        self.driver_provider.install_driver(self.driver_inf_file, self.driver_device_id)

    def execute(self):  # type: () -> bool
        """
        This Method is Used to.
        1) Copy Iperf Tool to Sut1 and Sut2.
        2) Set Sut2 as Iperf Server.
        3) Set Sut1 as Iperf Client and execute for given period of time.

        :return: True if all steps executes and getting the status as expected.
        """
        self._test_content_logger.start_step_logger(1)
        self.network_provider.copy_iperf_to_sut1()
        self.network_provider.copy_iperf_to_sut2()
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        server_thread = threading.Thread(target=self.network_provider.execute_sut2_as_iperf_server,
                                         args=(self.IPERF_EXEC_TIME,))
        server_thread.start()
        time.sleep(self.WAITING_TIME_IN_SEC)
        self._test_content_logger.end_step_logger(2, True)

        self._test_content_logger.start_step_logger(3)
        self.network_provider.execute_sut1_as_iperf_client(self.IPERF_EXEC_TIME)
        self._test_content_logger.end_step_logger(3, True)

        self._log.info("Killing Server Thread")
        server_thread.join()

        return True

    def cleanup(self, return_status):
        """
        This Method is Used for Cleanup
        """
        super(ContentBaseTestCase, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CarlsvilleTcpStressWindows.main()
             else Framework.TEST_RESULT_FAIL)
