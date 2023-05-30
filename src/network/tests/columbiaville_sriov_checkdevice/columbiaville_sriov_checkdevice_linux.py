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


class ColumbiavilleSriovCheckDeviceLinux(NetworkingCommon):
    """
    HPQC ID : H80127-PI_Networking_Columbiaville_SRIOVCheckDevice_L

    This Class is Used to Generate Columbiaville Virtual Network Adapters and assign Static IP and IPv6 Address to each
    Virtual Network Adapter Generated and Ping them. Reset Count of Virtual Network Adapters to there Default Value.
    """
    TEST_CASE_ID = ["H80127", "PI_Networking_Columbiaville_SRIOVCheckDevice_L"]
    STEP_DATA_DICT = {
        1: {'step_details': "Make sure Columbiaville Network driver has been installed.",
            'expected_results': "Columbiaville Network Driver is Installed"},
        2: {'step_details': "Generate Virtual Columbiaville Network Adapters and Verify",
            'expected_results': "Virtual Columbiaville Network Adapters are Generated"},
        3: {'step_details': "Manually assign IPv4 for each Columbiaville virtual adapters, "
                            "then ping assigned IP address on SUT",
            'expected_results': "Ping of Columbiaville Virtual Network Adapter IPv4 address is successful"},
        4: {'step_details': "Manually assign IPv6 for each Columbiaville virtual adapters, "
                            "then ping assigned IP address on SUT",
            'expected_results': "Ping of Columbiaville Virtual Network Adapter IPv6 address is successful"},
        5: {'step_details': "Reset Columbiaville Virtual Adapters to Default",
            'expected_results': "Columbiaville Virtual Network Adapters are Reset to Default Value"},
        }

    NUMBER_OF_VIRTUAL_ADAPTERS = 4

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of ColumbiavilleSriovCheckDeviceLinux

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(ColumbiavilleSriovCheckDeviceLinux, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):  # type: () -> None
        """
        PreChecks if the System is installed with Columbiaville Network Adapter.
        """
        self._test_content_logger.start_step_logger(1)
        self.driver_provider.install_driver(
            NetworkDrivers.COLUMBIAVILLE_DRIVER_CODE, NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME)
        self._test_content_logger.end_step_logger(1, True)
        self.network_provider.disable_foxville_port()

    def execute(self):  # type: () -> bool
        """
        This Method is Used to.
        1) Generate Given Number of Virtual Network Adapters and Verify
        2) Assign Static Ip Address to each Virtual Network Adapter generated and Ping them.
        3) Assign Static IPv6 Address to each Virtual Network Adapter generated and Ping them.
        4) Reset Virtual Network Adapter Count to Its Default Value

        :return: True if all steps executes and getting the status as expected.
        """
        self._test_content_logger.start_step_logger(2)
        self.network_provider.generate_virtual_functions(num_of_adapters=self.NUMBER_OF_VIRTUAL_ADAPTERS)
        self._test_content_logger.end_step_logger(2, True)

        self._test_content_logger.start_step_logger(3)
        self.network_provider.assign_static_ip_address_to_virtual_interfaces_and_ping()
        self._test_content_logger.end_step_logger(3, True)

        self._test_content_logger.start_step_logger(4)
        self.network_provider.assign_static_ipv6_address_to_virtual_interfaces_and_ping()
        self._test_content_logger.end_step_logger(4, True)

        self._test_content_logger.start_step_logger(5)
        self.network_provider.reset_virtual_network_adapters()
        self._test_content_logger.end_step_logger(5, True)

        return True

    def cleanup(self, return_status):
        """
        This Method is Used to Install Columbiaville driver and Reset Virtual Network Adapters to their Default Value.
        """
        self.driver_provider. \
            install_driver(NetworkDrivers.COLUMBIAVILLE_DRIVER_CODE, NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME)
        self.network_provider.reset_virtual_network_adapters()
        super(ContentBaseTestCase, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ColumbiavilleSriovCheckDeviceLinux.main()
             else Framework.TEST_RESULT_FAIL)
