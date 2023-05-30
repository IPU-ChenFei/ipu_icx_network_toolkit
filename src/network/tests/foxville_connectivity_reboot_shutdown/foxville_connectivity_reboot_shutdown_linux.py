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

from dtaf_core.lib.dtaf_constants import Framework
from src.provider.driver_provider import NetworkDrivers

from src.lib.content_base_test_case import ContentBaseTestCase

from src.lib.test_content_logger import TestContentLogger
from src.network.networking_common import NetworkingCommon
from src.lib import content_exceptions


class FoxvilleConnectivityRebootShutdownLinux(NetworkingCommon):
    """
    HPQC ID : H80219-PI_Networking_Foxville_ConnectivityReboot_shutdownL

    This Class is Used to Check the Connectivity of Foxville Network Driver by Rebooting and Shutting Down the System
    and Pinging System Ip.
    """
    TEST_CASE_ID = ["H80219", "PI_Networking_Foxville_ConnectivityReboot_shutdownL"]
    NUMBER_OF_ITERATIONS = 5
    STEP_DATA_DICT = {
        1: {'step_details': "Boot to Linux OS, make sure Network adapter driver has been installed successfully."
                            "Connect SUT with switch, ping DHCP server's IP address.",
            'expected_results': "Network's driver has been installed corrently. "
                                "Ping DHCP server's IP address is successful."},
        2: {'step_details': "Reboot the SUT, then ping DHCP server's IP address.",
            'expected_results': "Network driver will auto loading after reboot the SUT. Boot to OS, "
                                "ping DHCP server's IP address is successful."},
        3: {'step_details': "Reboot SUT five times, then check network's connectivity by ping DHCP server's "
                            "IP address.",
            'expected_results': "SUT's network connectivity is stable during reboot cycles."},
        4: {'step_details': "Shutdown the SUT, manually power on SUT, then ping DHCP server's IP address.",
            'expected_results': "Network driver will auto loading after power on SUT. Boot to OS, "
                                "ping DHCP server's IP address is successful."}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of FoxvilleConnectivityRebootShutdownLinux.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(FoxvilleConnectivityRebootShutdownLinux, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):  # type: () -> None
        """
        PreChecks if the System is Booted to Linux OS and Checks if Foxville Driver is Installed.

        :raise: content_exception.TestNAError if OS is not Linux.
        """
        self.driver_provider.install_driver(NetworkDrivers.FOXVILLE_DRIVER_CODE,
                                            NetworkDrivers.FOXVILLE_DRIVER_NAME)

    def execute(self):  # type: () -> bool
        """
        This Method is Used to.
        1) Boot System to Linux OS and Verify its connectivity by Pinging System IP.
        2) Reboot and Shutdown the System and Boot the System back to OS and Verify its connectivity by Pinging
        System IP and repeat same for 5 Iterations.

        :raise: content_exceptions.TestFail
        :return: True if all steps executes and getting the status as expected.
        """
        self._test_content_logger.start_step_logger(1)
        if not self.network_provider.ping_network_adapter_ip():
            raise content_exceptions.TestFail("Network Driver is not Pinging as Expected")
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        self.reset_base_test.warm_reset()
        if not self.network_provider.ping_network_adapter_ip():
            raise content_exceptions.TestFail("Network Driver is not Pinging after Performing Warm Reset")
        self._test_content_logger.end_step_logger(2, True)

        self._test_content_logger.start_step_logger(3)
        for iteration in range(self.NUMBER_OF_ITERATIONS):
            self._log.info("Rebooting the SUT, Iteration: %d", iteration)
            self.reset_base_test.warm_reset()
            if not self.network_provider.ping_network_adapter_ip():
                raise content_exceptions.TestFail("Network Driver is not Pinging after Warm Reset "
                                                  "Iteration {}".format(iteration + 1))
            self._log.info("Network Driver is Pinging and Reachable after Warm Reset Iteration {}".format(iteration+1))
        self._log.debug("Network Driver is Pinging and Reachable for all Warm Reset {} Iterations"
                        .format(self.NUMBER_OF_ITERATIONS))
        self._test_content_logger.end_step_logger(3, True)

        self._test_content_logger.start_step_logger(4)
        self.perform_graceful_g3()
        if not self.network_provider.ping_network_adapter_ip():
            raise content_exceptions.TestFail("Network Driver is not Pinging after Performing Shutdown")
        self._log.debug("Network Driver is Up and Pinging as Expected after Performing Shutdown")
        self._test_content_logger.end_step_logger(4, True)
        return True

    def cleanup(self, return_status):
        """
        This Method is Used to Override Cleanup Method of ContentBaseTestCase to avoid command_timeout_error.
        """
        self.driver_provider.install_driver(NetworkDrivers.FOXVILLE_DRIVER_CODE,
                                            NetworkDrivers.FOXVILLE_DRIVER_NAME)
        super(ContentBaseTestCase, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if FoxvilleConnectivityRebootShutdownLinux.main()
             else Framework.TEST_RESULT_FAIL)
