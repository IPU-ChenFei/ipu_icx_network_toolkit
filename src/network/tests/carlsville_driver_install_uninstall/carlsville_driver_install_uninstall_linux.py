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
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.test_content_logger import TestContentLogger
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions
from src.provider.driver_provider import NetworkDrivers
from src.network.networking_common import NetworkingCommon


class CarlsvilleDriverInstallUninstallLinux(NetworkingCommon):
    """
    HPQC ID : H91326-PI_Networking_Carlsville_DriverInstallUninstall_L
    1) Identify the device using Ethernet
    2) Identify the driver used in the SUT
    3) Uninstall Carlsville Driver and verify ping is not successful
    4) Install Carlsville Driver and verifies ping is successful
    """
    TEST_CASE_ID = ["H91326", "PI_Networking_Carlsville_DriverInstallUninstall_L"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Identify the device using Ethernet command',
            'expected_results': 'Get information about the Ethernet devices'},
        2: {'step_details': 'Identify the driver used in the sut',
            'expected_results': 'Verify the network driver used in sut'},
        3: {'step_details': 'Uninstall Carlsville driver in sut',
            'expected_results': 'Verify the driver got uninstalled'},
        4: {'step_details': 'Install Carlsville driver in sut',
            'expected_results': 'Verify the Carlsville driver got installed'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of CarlsvilleDriverInstallUninstallLinux.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(CarlsvilleDriverInstallUninstallLinux, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):  # type: () -> None
        """
        Pre-checks whether carlsville network driver is installed in system.
        """
        self.driver_provider.install_driver(NetworkDrivers.CARLSVILLE_DRIVER_CODE,
                                            NetworkDrivers.CARLSVILLE_DRIVER_NAME)
        self.network_provider.disable_foxville_port()

    def execute(self):  # type: () -> bool
        """
        This function calls Driver installation provider and performs below step.
        1) Identify the device using Ethernet
        2) Identify  the driver used in the sut
        3) Verify Un-installation of Carlsville Driver is successful
        4) Verify Carlsville Driver installed successfully

        :raise: content_exception.TestFail if ping not successful.
        :return: True if all steps executes and getting the status as expected.
        """
        self._test_content_logger.start_step_logger(1)
        ethernet_devices = self.driver_provider.get_ethernet_devices()
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._test_content_logger.start_step_logger(2)
        self.driver_provider.identify_device_controller(ethernet_devices, NetworkDrivers.CARLSVILLE_DRIVER_CODE)
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._test_content_logger.start_step_logger(3)
        self.driver_provider.uninstall_driver(
            NetworkDrivers.CARLSVILLE_DRIVER_CODE, NetworkDrivers.CARLSVILLE_DRIVER_NAME)
        if self.network_provider.ping_network_adapter_ip():
            raise content_exceptions.TestFail("Network Adapter is still Pinging after driver uninstallation")
        self._log.info("As expected Network Adapter is not pinging after uninstalling driver")
        self._test_content_logger.end_step_logger(3, return_val=True)
        self._test_content_logger.start_step_logger(4)
        self.driver_provider.install_driver(
            NetworkDrivers.CARLSVILLE_DRIVER_CODE, NetworkDrivers.CARLSVILLE_DRIVER_NAME)
        time.sleep(self.WAITING_TIME_IN_SEC)
        if not self.network_provider.ping_network_adapter_ip():
            raise content_exceptions.TestFail("Network Adapter is not Pinging after driver is installed")
        self._log.info("Network Adapter is pinging after driver is installed")
        self._test_content_logger.end_step_logger(4, return_val=True)
        return True

    def cleanup(self, return_status):
        """
        This Method is Used to Override Cleanup Method of ContentBaseTestCase to avoid command_timeout_error.
        """
        self.driver_provider.install_driver(NetworkDrivers.CARLSVILLE_DRIVER_CODE,
                                            NetworkDrivers.CARLSVILLE_DRIVER_NAME)
        super(ContentBaseTestCase, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CarlsvilleDriverInstallUninstallLinux.main()
             else Framework.TEST_RESULT_FAIL)
