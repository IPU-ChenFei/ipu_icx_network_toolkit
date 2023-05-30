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


class ColumbiavilleInternetProtocolV6Windows(NetworkingCommon):
    """
    HPQC ID : H80149-PI_Networking_Columbiaville_InternetProtocolv6_W

    This Class is used to Assign IPv6 Address to Sut1 and Sut2 Network Interface and Verify whether SUt2 IPv6 Address
    is pinging from Sut1 and Vice versa.
    """
    TEST_CASE_ID = ["H80149", "PI_Networking_Columbiaville_InternetProtocolv6_W"]
    STEP_DATA_DICT = {
        1: {'step_details': "Set IPv6 Address for Network Interfaces of Both Suts",
            'expected_results': "IPv6 address is set for SUT1 and SUT2 Successfully"},
        2: {'step_details': "Ping Sut2 IPv6 Address from Sut1 and Sut1 IPv6 Address from Sut2",
            'expected_results': "Pinging of Sut2 IPv6 Address from Sut1 and Sut1 IPv6 Address from Sut2 is Successful"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of ColumbiavilleInternetProtocolV6Windows

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(ColumbiavilleInternetProtocolV6Windows, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.driver_inf_file = self._common_content_configuration.get_driver_inf_file_name(
            NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME)
        self.driver_device_id = self._common_content_configuration.get_driver_device_id(
            NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME)

    def prepare(self):  # type: () -> None
        """
        Prepares the System for the Execution of Test Case.
        """
        self.driver_provider.install_driver(self.driver_inf_file, self.driver_device_id)

    def execute(self):  # type: () -> bool
        """
        This Method is Used to.
        1) Set Static IPv6 Address for Network Interfaces of both Sut1 and Sut2
        2) Ping Sut2 Ipv6 Address from Sut1 and Vice versa.

        :return: True if all steps executes and getting the status as expected.
        """

        self._test_content_logger.start_step_logger(1)
        self.network_provider.assign_static_ipv6_to_sut1_interface()
        self.network_provider.assign_static_ipv6_to_sut2_interface()
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        self.network_provider.ping_sut2_ipv6_from_sut1()
        self.network_provider.ping_sut1_ipv6_from_sut2()
        self._test_content_logger.end_step_logger(2, True)

        return True

    def cleanup(self, return_status):
        """
        This Method is Used for De Allocating the Static Ip Address assigned to Sut1 and Sut2
        """
        self.network_provider.de_allocate_static_ipv6_from_sut1()
        self.network_provider.de_allocate_static_ipv6_from_sut2()
        super(ContentBaseTestCase, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ColumbiavilleInternetProtocolV6Windows.main()
             else Framework.TEST_RESULT_FAIL)
