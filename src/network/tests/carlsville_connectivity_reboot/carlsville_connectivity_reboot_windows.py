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
from src.provider.driver_provider import NetworkDrivers
from src.lib import content_exceptions


class CarlsvilleConnectivityRebootWindows(NetworkingCommon):
    """
    HPQC ID : H91330-PI_Networking_Carlsville_ConnectivityReboot_W

    This Class is used to check the networking connectivity after Reboot Cycles of SUT.
    """
    TEST_CASE_ID = ["H91330", "PI_Networking_Carlsville_ConnectivityReboot_W"]
    NUMBER_OF_ITERATIONS = 5

    STEP_DATA_DICT = {
        1: {'step_details': "Boot to Windows OS, make sure Network adapter driver has been installed successfully."
                            "ping DHCP server's IP address.",
            'expected_results': "Network's driver has been installed correctly."
                                "Ping DHCP server's IP address is successful."},
        2: {'step_details': "Reboot the SUT, then ping DHCP server's IP address."
                            "Enable network adapter in OS, ping DHCP server's IP address",
            'expected_results': "Network driver will auto loading after reboot the SUT."
                                "Boot to OS, ping DHCP server's IP address is successful."},
        3: {'step_details': "Reboot SUT five times, then check network's connectivity by ping "
                            "DHCP server's IP address.",
            'expected_results': "SUT's network connectivity is stable during reboot cycles."}
        }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of CarlsvilleConnectivityRebootWindows.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(CarlsvilleConnectivityRebootWindows, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.driver_inf_file = self._common_content_configuration.get_driver_inf_file_name(
            NetworkDrivers.CARLSVILLE_DRIVER_NAME)
        self.driver_device_id = self._common_content_configuration.get_driver_device_id(
            NetworkDrivers.CARLSVILLE_DRIVER_NAME)

    def prepare(self):  # type: () -> None
        """
        PreChecks if the Carlsville Driver is installed in System.
        """
        self.driver_provider.install_driver(self.driver_inf_file, self.driver_device_id)

    def execute(self):  # type: () -> bool
        """
        This Method is Used to.
        1) Boot System to Windows OS and Verify its connectivity by Pinging System IP.
        2) Reboot the System and Boot the System back to OS and Verify its connectivity by Pinging
        System IP and repeat same for 5 Iterations.

        :raise: content_exceptions.TestFail
        :return: True if all steps executes and getting the status as expected.
        """
        self._test_content_logger.start_step_logger(1)
        if not self.network_provider.is_sut_pingable():
            raise content_exceptions.TestFail("System is not Pinging as Expected")
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        self.reset_base_test.warm_reset()
        if not self.network_provider.is_sut_pingable():
            raise content_exceptions.TestFail("System is not Pinging after Warm Reset")
        self._test_content_logger.end_step_logger(2, True)

        self._test_content_logger.start_step_logger(3)
        for iteration in range(self.NUMBER_OF_ITERATIONS):
            self._log.info("Rebooting the SUT, Iteration: %d", iteration + 1)
            self.reset_base_test.warm_reset()
            if not self.network_provider.is_sut_pingable():
                raise content_exceptions.TestFail("System is not Ping as Expected after reboot Iteration {}"
                                                  .format(iteration + 1))
            self._log.debug("System is Pinging and Reachable after Warm Reset Iteration {}".format(iteration + 1))
        self._log.debug("System is Pinging and Reachable for all Reboot {} Iterations".
                        format(self.NUMBER_OF_ITERATIONS))
        self._test_content_logger.end_step_logger(3, True)
        return True

    def cleanup(self, return_status):
        """
        This Method is Used to Override Cleanup Method of ContentBaseTestCase to avoid command_timeout_error.
        """
        self.driver_provider.install_driver(self.driver_inf_file, self.driver_device_id)
        super(ContentBaseTestCase, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CarlsvilleConnectivityRebootWindows.main()
             else Framework.TEST_RESULT_FAIL)
