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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.lib.content_base_test_case import ContentBaseTestCase
from src.network.networking_common import NetworkingCommon
from src.provider.driver_provider import NetworkDrivers
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions


class ColumbiavilleDriverInstallUninstall(NetworkingCommon):
    """
    This Class is Used for Installation and Uninstallation of Columbiaville network Driver.

    HPQC ID : H80138-PI_Networking_Columbiaville_DriverInstallUninstall_W,
              H98583-PI_Networking_Columbiaville_DriverInstallUninstall_L
    """
    TEST_CASE_ID = ["H80138", "PI_Networking_Columbiaville_DriverInstallUninstall_W",
                    "H98583", "PI_Networking_Columbiaville_DriverInstallUninstall_L"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Copy drivers packages to sut, Identify Driver Package in Sut and Install the Driver',
            'expected_results': 'Packages are copied successfully and Driver is Successfully Installed'},
        2: {'step_details': 'Uninstall Columbiaville driver in sut',
            'expected_results': 'SUT is not pinging after uninstalling Driver'},
        3: {'step_details': 'ReInstall Columbiaville driver in sut',
            'expected_results': 'SUT is pinging successfully after ReInstalling Driver'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of ColumbiavilleDriverInstallUninstall.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(ColumbiavilleDriverInstallUninstall, self).__init__(test_log, arguments, cfg_opts)
        self.driver_inf_file = self._common_content_configuration.get_driver_inf_file_name(
            NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME)
        self.driver_device_id = self._common_content_configuration.get_driver_device_id(
            NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        if self.os.os_type == OperatingSystems.WINDOWS:
            self.install_collateral.copy_devcon_to_sut()
            try:
                self.driver_provider.install_driver(self.foxville_inf_file, self.foxville_device_id)
            except Exception as ex:
                self._log.error("Exception Occurred during Installation of Driver : '{}'".format(ex))
            try:
                self.driver_provider.uninstall_driver(self.foxville_inf_file, self.foxville_device_id)
            except Exception as ex:
                self._log.error("Exception Occurred during UnInstallation of Driver : '{}'".format(ex))
            self.network_provider.deallocate_static_ip()
        elif self.os.os_type == OperatingSystems.LINUX:
            self.network_provider.disable_foxville_port()
        self.interface, self.ip_address = self.assign_static_ip(NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME)
        self.ethernet_devices = ""

    def prepare(self):  # type: () -> None
        """preparing the setup"""
        self._test_content_logger.start_step_logger(1)
        if self.os.os_type == OperatingSystems.WINDOWS:
            self.driver_provider.install_driver(self.driver_inf_file, self.driver_device_id)
        elif self.os.os_type == OperatingSystems.LINUX:
            self.driver_provider.install_driver(
                NetworkDrivers.COLUMBIAVILLE_DRIVER_CODE, NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME)
            self.ethernet_devices = self.driver_provider.get_ethernet_devices()
            self.driver_provider.identify_device_controller(self.ethernet_devices, NetworkDrivers.COLUMBIAVILLE_DRIVER_CODE)
        else:
            raise content_exceptions.TestUnSupportedError("This Test Case is Not Supported on {}"
                                                          .format(self.os.os_type))
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):  # type: () -> bool
        """
        This function calls Driver installation provider and performs below steps
        1) Uninstall Columbiaville Driver and verifies the sut is not pinging.
        2) Install Columbiaville Driver and verifies the sut is pinging.

        :raise: Content exception if system is pinging after driver uninstall or vice versa
        :return: True if all steps executes and getting the status as expected.
        """
        self._test_content_logger.start_step_logger(2)
        if self.os.os_type == OperatingSystems.WINDOWS:
            self.driver_provider.uninstall_driver(self.driver_inf_file, self.driver_device_id)
        elif self.os.os_type == OperatingSystems.LINUX:
            self.driver_provider.uninstall_driver(
                NetworkDrivers.COLUMBIAVILLE_DRIVER_CODE, NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME)
        else:
            raise content_exceptions.TestUnSupportedError("This Test Case is Not Supported on {}"
                                                          .format(self.os.os_type))
        if self.network_provider.ping_network_adapter_ip(self.ip_address):
            raise content_exceptions.TestFail("Network Adapter is still Pinging after driver uninstallation")
        self._log.info("As expected Network Adapter is not pinging after uninstalling driver")
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        if self.os.os_type == OperatingSystems.WINDOWS:
            self.driver_provider.install_driver(self.driver_inf_file, self.driver_device_id)
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)  # Reboot for changes
        elif self.os.os_type == OperatingSystems.LINUX:
            self.driver_provider.install_driver(
                NetworkDrivers.COLUMBIAVILLE_DRIVER_CODE, NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME)
        else:
            raise content_exceptions.TestUnSupportedError("This Test Case is Not Supported on {}"
                                                          .format(self.os.os_type))
        self.network_provider.get_network_adapter_interfaces(assign_static_ip=True)
        time.sleep(self.WAITING_TIME_IN_SEC)
        if not self.network_provider.ping_network_adapter_ip(self.ip_address):
            raise content_exceptions.TestFail("Network Adapter is not Pinging after driver is installed")
        self._log.info("Network Adapter is pinging after driver is installed")
        self._test_content_logger.end_step_logger(3, return_val=True)

        return True

    def cleanup(self, return_status):
        """
        This Method is Used to Override Cleanup Method of ContentBaseTestCase to avoid command_timeout_error.
        """
        if self.os.os_type == OperatingSystems.WINDOWS:
            self.driver_provider.install_driver(self.driver_inf_file, self.driver_device_id)
            self.network_provider.deallocate_static_ip()
            self.driver_provider.install_driver(self.foxville_inf_file, self.foxville_device_id)
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        elif self.os.os_type == OperatingSystems.LINUX:
            self.driver_provider.install_driver(
                NetworkDrivers.COLUMBIAVILLE_DRIVER_CODE, NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME)
            self.network_provider.deallocate_static_ip()
        super(ContentBaseTestCase, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ColumbiavilleDriverInstallUninstall.main()
             else Framework.TEST_RESULT_FAIL)
