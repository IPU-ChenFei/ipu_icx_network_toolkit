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


class JacksonvilleConnectivityEnableDisableWindows(NetworkingCommon):
    """
    HPQC ID : H80074-PI_Networking_JacksonVille_ConnectivityEnableDisable_W

    This Class is Used to Check the Connectivity of Jacksonville Network Driver by Enabling and Disabling Network Adapter
    and Pinging System Ip.
    """
    TEST_CASE_ID = ["H80074", "PI_Networking_JacksonVille_ConnectivityEnableDisable_W"]
    STEP_DATA_DICT = {
        1: {'step_details': "Boot OS, connect SUT with switch via network cable, ping DHCP server's IP address.",
            'expected_results': "The connection between SUT and switch can be setup up, SUT can get IP address from"
                                " DHCP server,Ping is successful."},
        2: {'step_details': "Disable network adapter in OS, ping DHCP server's IP address. "
                            "Enable network adapter in OS, ping DHCP server's IP address",
            'expected_results': "Ping server's IP address is unsuccessful when disable network adapter,"
                                "enable network adapter, ping server's IP address will pass."}}
    NUMBER_OF_ITERATIONS = 3

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of JacksonvilleConnectivityEnableDisableWindows

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(JacksonvilleConnectivityEnableDisableWindows, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.driver_inf_file = self._common_content_configuration.get_driver_inf_file_name(
            NetworkDrivers.JACKSONVILLE_DRIVER_NAME)
        self.driver_device_id = self._common_content_configuration.get_driver_device_id(
            NetworkDrivers.JACKSONVILLE_DRIVER_NAME)

    def prepare(self):  # type: () -> None
        """
        PreChecks if the System is installed with Jacksonville Network Adapter
        """
        self.driver_provider.install_driver(self.driver_inf_file, self.driver_device_id)

    def execute(self):  # type: () -> bool
        """
        This Method is Used to.
        1) Boot System to OS and Verify its connectivity by Pinging System IP.
        2) Disable/Enable the Network Adapter and Verify its connectivity by Pinging System IP and repeat same
        for 3 Iterations.

        :return: True if all steps executes and getting the status as expected.
        :raise: content_exceptions.TestFail
        """
        self._test_content_logger.start_step_logger(1)
        if not self.network_provider.is_sut_pingable():
            raise content_exceptions.TestFail("System is not Pinging as Expected")
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        self._log.debug("Verify the Connectivity of the System by Disabling and "
                        "Enabling Jacksonville Network Adapter "
                        "for {} times".format(self.NUMBER_OF_ITERATIONS))
        for iteration in range(self.NUMBER_OF_ITERATIONS):
            self._log.info("Start of Iteration {}".format(iteration + 1))
            self._log.info("Disable Network Adapter and ping during the Iteration {}".format(iteration + 1))
            self.network_provider.disable_network_adapter_and_ping()
            self._log.info("Enable Network Adapter and ping during the Iteration {}".format(iteration + 1))
            self.network_provider.enable_network_adapter_and_ping()
            self._log.debug("Jacksonville Network Adapter is Working as Expected during "
                            "the Iteration {}".
                            format(iteration + 1))
        self._log.info("Jacksonville Network Adapter is Pinging and Reachable after all "
                       "{} Iterations"
                       .format(self.NUMBER_OF_ITERATIONS))
        self._test_content_logger.end_step_logger(2, True)
        return True

    def cleanup(self, return_status):
        """
        This Method is Used to Override Cleanup Method of ContentBaseTestCase and to Enable Network Adapter.
        """
        self.driver_provider.install_driver(self.driver_inf_file, self.driver_device_id)
        self.network_provider.enable_network_adapter_and_ping()
        super(ContentBaseTestCase, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if JacksonvilleConnectivityEnableDisableWindows.main()
             else Framework.TEST_RESULT_FAIL)
