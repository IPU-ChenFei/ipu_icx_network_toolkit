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
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.test_content_logger import TestContentLogger
from src.network.networking_common import NetworkingCommon
from src.lib import content_exceptions
from src.provider.driver_provider import NetworkDrivers


class ColumbiavilleConnectivityRebootShutdownLinux(NetworkingCommon):
    """
    HPQC ID : H81651 - PI_Networking_Columbiaville_ConnectivityReboot_Shutdown_L
    This TestCase is to connect the linux system and check the connectivity and reboot
    and shutdown for an occurrence.

    1) install Columbiaville Driver and verifies whether the driver is loaded.
    2) Reboots the SUT and verifies if the DHCP IP is Pingable.
    3) reinstall Columbiaville Driver and verifies whether the driver is loaded.
    4) shutdown the SUT, Manually power on the SUT and verifies the DHCP IP is Pingable.
    5) Shutdown SUT 5 times and check DHCP IP if it is pingable.
    """
    TEST_CASE_ID = ["H81651", "PI_Networking_Columbiaville_ConnectivityReboot_Shutdown_L"]
    NUMBER_OF_ITERATIONS = 5
    STEP_DATA_DICT = {
        1: {'step_details': "Boot to Linux OS, make sure Network adapter driver has been installed successfully."
                            "Connect SUT with switch, ping DHCP server's IP address.",
            'expected_results': "Network's driver has been installed correctly. "
                                "Ping DHCP server's IP address is successful."},
        2: {'step_details': "Reboot the SUT, then ping DHCP server's IP address.",
            'expected_results': "Network driver should be auto loading after reboot the SUT, "
                                "Boot to OS, ping DHCP server's IP address is successful."},
        3: {'step_details': "Shutdown the SUT, manually power on SUT, then ping DHCP server's IP address.",
            'expected_results': "Network driver will auto loading after power on SUT, Boot to OS, "
                                "ping DHCP server's IP address is successful."},
        4: {'step_details': "Shutdown SUT five times, then check network's connectivity by ping DHCP server's "
                            "IP address.",
            'expected_results': "SUT's network connectivity is stable during Shutdown cycles."}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of ColumbiavilleConnectivityRebootShutdownLinux.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(ColumbiavilleConnectivityRebootShutdownLinux, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.network_provider.disable_foxville_port()
        self.interface, self.ip_address = self.assign_static_ip(NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME)

    def prepare(self):  # type: () -> None
        """
        PreChecks if the System is Booted to Linux OS with Columbiaville Network Adapter
        """
        self.driver_provider.install_driver(NetworkDrivers.COLUMBIAVILLE_DRIVER_CODE,
                                            NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME)

    def execute(self):  # type: () -> bool
        """
        This function calls Driver installation provider and performs below step.
        1) Reboots the SUT and verifies if the DHCP IP is Pingable.
        2) shutdown the SUT, Manually power on the SUT and verifies the DHCP IP is Pingable.
        3) reboot SUT 5 times and check DHCP IP if it is pingable.

        :raise: content_exception.TestFail if any of the above requirements fail.
        :return: True if all steps executes and getting the status as expected.
        """
        self._test_content_logger.start_step_logger(1)
        if not self.network_provider.ping_network_adapter_ip(self.ip_address):
            raise content_exceptions.TestFail("Network Adapter is not Pingable")
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self.reset_base_test.warm_reset()
        self.network_provider.get_network_adapter_interfaces(assign_static_ip=True)
        if not self.network_provider.ping_network_adapter_ip(self.ip_address):
            raise content_exceptions.TestFail("Network Adapter is not Pinging as Expected after Performing Warm Reset")
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self.perform_graceful_g3()
        self.network_provider.get_network_adapter_interfaces(assign_static_ip=True)
        if not self.network_provider.ping_network_adapter_ip(self.ip_address):
            raise content_exceptions.TestFail("Network Adapter is not Pinging as Expected after Performing Shutdown"
                                              " and Booting Back to OS")
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        for iteration in range(self.NUMBER_OF_ITERATIONS):
            self._log.info("Shutdown the SUT, Iteration: %d", iteration + 1)
            self.perform_graceful_g3()
            self.network_provider.get_network_adapter_interfaces(assign_static_ip=True)
            if not self.network_provider.ping_network_adapter_ip(self.ip_address):
                raise content_exceptions.TestFail("Network Adapter is not Pinging as Expected after Shutdown"
                                                  " Iteration {}".format(iteration + 1))
            self._log.info("After Shutdown Iteration {} Network Adapter is Pinging".format(iteration + 1))
        self._log.debug("Network Adapter is Pinging and Reachable for all Shutdown {} Iterations"
                        .format(self.NUMBER_OF_ITERATIONS))
        self._test_content_logger.end_step_logger(4, return_val=True)
        return True

    def cleanup(self, return_status):
        """
        This Method is Used to Installing driver and Override Cleanup Method of ContentBaseTestCase to avoid
        command_timeout_error and enables
        """
        self.driver_provider.install_driver(NetworkDrivers.COLUMBIAVILLE_DRIVER_CODE,
                                            NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME)
        self.network_provider.deallocate_static_ip()
        super(ContentBaseTestCase, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ColumbiavilleConnectivityRebootShutdownLinux.main()
             else Framework.TEST_RESULT_FAIL)
