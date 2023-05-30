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


class FortvilleDriverInstallUninstallLinux(NetworkingCommon):
    """
    HPQC ID : H98584-PI_Networking_Fortville_DriverInstallUninstall_L

    1) Identify the device using Ethernet
    2) Identify the driver used in the SUT
    3) Uninstall Fortville Driver and verify ping is not successful
    4) Install Fortville Driver and verifies ping is successful
    """
    TEST_CASE_ID = ["H98584", "PI_Networking_Fortville_DriverInstallUninstall_L"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Identify the device using Ethernet command',
            'expected_results': 'Get information about the Ethernet devices'},
        2: {'step_details': 'Identify the driver used in the sut',
            'expected_results': 'Verify the network driver used in sut'},
        3: {'step_details': 'Uninstall Fortville driver in sut',
            'expected_results': 'Verify the driver got uninstalled'},
        4: {'step_details': 'Install Fortville driver in sut',
            'expected_results': 'Verify the Fortville driver got installed'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of FortvilleDriverInstallUninstallLinux.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(FortvilleDriverInstallUninstallLinux, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.network_provider.disable_foxville_port()
        self.interface, self.ip_address = self.assign_static_ip(NetworkDrivers.FORTVILLE_DRIVER_NAME)

    def prepare(self):  # type: () -> None
        """
        Pre-checks if the Fortville Driver is Installed and Install the driver if it is not installed.
        """
        self.driver_provider.install_driver(
            NetworkDrivers.FORTVILLE_DRIVER_CODE, NetworkDrivers.FORTVILLE_DRIVER_NAME)

    def execute(self):  # type: () -> bool
        """
        This function calls Driver installation provider and performs below step.
        1) Identify the device using Ethernet
        2) Identify  the driver used in the sut
        3) Verify Un-installation of Fortville Driver is successful
        4) Verify Fortville Driver installed successfully

        :raise: content_exception.TestFail if ping not successful.
        :return: True if all steps executes and getting the status as expected.
        """
        self._test_content_logger.start_step_logger(1)
        ethernet_devices = self.driver_provider.get_ethernet_devices()
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._test_content_logger.start_step_logger(2)
        self.driver_provider.identify_device_controller(ethernet_devices, NetworkDrivers.FORTVILLE_DRIVER_CODE)
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._test_content_logger.start_step_logger(3)
        self.driver_provider.uninstall_driver(
            NetworkDrivers.FORTVILLE_DRIVER_CODE, NetworkDrivers.FORTVILLE_DRIVER_NAME)
        if self.network_provider.ping_network_adapter_ip(self.ip_address):
            raise content_exceptions.TestFail("Network Adapter is still Pinging after driver uninstallation")
        self._log.info("As expected Network Adapter is not pinging after uninstalling driver")
        self._test_content_logger.end_step_logger(3, return_val=True)
        self._test_content_logger.start_step_logger(4)
        self.driver_provider.install_driver(
            NetworkDrivers.FORTVILLE_DRIVER_CODE, NetworkDrivers.FORTVILLE_DRIVER_NAME)
        self.network_provider.get_network_adapter_interfaces(assign_static_ip=True)
        time.sleep(self.WAITING_TIME_IN_SEC)
        if not self.network_provider.ping_network_adapter_ip(self.ip_address):
            raise content_exceptions.TestFail("Network Adapter is not Pinging after driver is installed")
        self._log.info("Network Adapter is pinging after driver is installed")
        self._test_content_logger.end_step_logger(4, True)
        return True

    def cleanup(self, return_status):
        """
        This Method is Used to Override Cleanup Method of ContentBaseTestCase to avoid command_timeout_error.
        """
        self.driver_provider.install_driver(
            NetworkDrivers.FORTVILLE_DRIVER_CODE, NetworkDrivers.FORTVILLE_DRIVER_NAME)
        self.network_provider.deallocate_static_ip()
        super(ContentBaseTestCase, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if FortvilleDriverInstallUninstallLinux.main()
             else Framework.TEST_RESULT_FAIL)
