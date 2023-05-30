#!/usr/bin/env python
#################################################################################
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
#################################################################################
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.lib.test_content_logger import TestContentLogger
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions
from src.lib.bios_util import ItpXmlCli
from src.provider.storage_provider import StorageProvider


class UsbDetection(ContentBaseTestCase):
    """
    HPQC ID : H80085-PI_USB_DetectionAndHotPlugUSB3_L ,H51651-PI_USB_DetectionAndHotPlugUSB3_L
    This test case aims to detect hot plug USB device connected and to check the bcd value.
    """
    TEST_CASE_ID = ["H80085", "PI_USB_DetectionAndHotPlugUSB3_L", "H51651", "PI_USB_DetectionAndHotPlugUSB3_L"]
    USB_TYPE = "type"
    USB_BCD = "bcd"

    step_data_dict = {
        1: {'step_details': 'Clear the CMOS and Configure the BIOS to default settings',
            'expected_results': 'CMOS cleared and BIOS configured to default settings'},
        2: {'step_details': 'Boot to OS and Clear the system logs',
            'expected_results': 'System booted and logs cleared'},
        3: {'step_details': 'Disconnect and then connect the USB and wait till USB gets ready',
            'expected_results': 'USB gets disconnected and connected and is ready to use'},
        4: {'step_details': 'Run the command lsusb -v',
            'expected_results': 'The Mouse or pen drive bcdUSB value should be greater than 2'},
        5: {'step_details': 'Disconnect and then connect the USB and wait till USB gets ready',
            'expected_results': 'USB gets disconnected and connected and is ready to use'},
        6: {'step_details': 'Run the command lsusb -v',
            'expected_results': 'The Mouse and pen drive bcdUSB value should be greater than 2'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of UsbDetection

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(UsbDetection, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self.install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.itp_xml_cli_util = None
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = None
        self._storage_provider = StorageProvider.factory(self._log, self.os, cfg_opts)  # type: StorageProvider
        self.usb_set_time = self._common_content_configuration.get_usb_set_time_delay()
        self.usb_connected = self._common_content_configuration.get_usb_device()

    def prepare(self):
        # type: () -> None
        """
        This method prepares the system as below:-
        1. Clear the cmos and Loads BIOS defaults settings.
        2. Boot the OS and clear the logs
        """
        self._test_content_logger.start_step_logger(1)
        self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)
        self._sdp = ProviderFactory.create(self.si_dbg_cfg, self._log)
        self.itp_xml_cli_util.perform_clear_cmos(self._sdp, self.os, self.reboot_timeout)
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._test_content_logger.start_step_logger(2)
        super(UsbDetection, self).prepare()
        self._test_content_logger.end_step_logger(2, return_val=True)

    def get_lsub_difference(self, before_hotplug, after_hotplug):
        """
        Retrieves the lsusb device after hot-plug and return the difference device information which before and lsusb
        after disconnection

        :param before_hotplug: device connected before hotplug
        :param after_hotplug: device connected after hotplug
        :return :returns the difference of device connected before and after hot plug.
        :raise :content_exceptions.TestFail when no device detected before and after hot plug.
        """
        before_set = set(before_hotplug.strip().split("\n"))
        after_set = set(after_hotplug.strip().split("\n"))
        diff = ", ".join(after_set.difference(before_set))
        if not diff:
            raise content_exceptions.TestFail("No device is connected after hotplug")
        return diff

    def verify_hotplug_device_status(self, hotplug_device_info, config_device_info):
        """
        Compares the device type and bcd value retrieved from content configuration with hot plugged device type and
        bcd value

        :param hotplug_device_info: device type and bcd value of hot plugged device
        :param config_device_info: device type and bcd value from configuration file
        :raise :content_exceptions.TestFail if device type and bcd value of hot plugged device and configuration
        does not match.
        """
        self._log.info("checking for hot plug device status")
        for key, value in hotplug_device_info.items():
            if key == self.USB_TYPE:
                res = [i for i in value if config_device_info.get(key).lower() in i.lower()]
                self._log.debug("Device type connected after hot plug %s" % res)
                if not res:
                    raise content_exceptions.TestFail("No device type {} is detected after hot plug". format(
                        config_device_info.get(key)))
            elif key == self.USB_BCD:
                if not config_device_info.get(key) == value:
                    raise content_exceptions.TestFail("{} value of the device type {} does not match after hot plug".
                                                      format(key, config_device_info.get(key)))
        self._log.info("Device type {} and bcd value {} detected after hot plug".format(config_device_info.get(
            self.USB_TYPE), config_device_info.get(self.USB_BCD)))

    def execute(self):
        """
        This method executes the below:
        1. Disconnects and connect the USB to SUT and wait till it gets ready for use.
        2. Runs the command lsusb -v and verifies the BCD version
        3. The process is repeated twice

        :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(3)
        self._log.info("USB disconnecting")
        self.phy.disconnect_usb(self.usb_set_time)
        usb_detail_before = self._storage_provider.get_usb_details()
        self._log.debug("Output before usb connect {}".format(usb_detail_before))
        self._log.info("USB connecting")
        self.phy.connect_usb_to_sut(self.usb_set_time)
        time.sleep(self.usb_set_time)
        self._test_content_logger.end_step_logger(3, return_val=True)
        self._test_content_logger.start_step_logger(4)
        usb_detail_after = self._storage_provider.get_usb_details()
        self._log.debug("Output after usb connect {}".format(usb_detail_after))
        difference = self.get_lsub_difference(usb_detail_before, usb_detail_after)
        device_connected = self._storage_provider.get_bus_device_type_info(difference)
        self.verify_hotplug_device_status(device_connected, self.usb_connected)
        self._test_content_logger.end_step_logger(4, return_val=True)
        self._test_content_logger.start_step_logger(5)
        self._log.info("USB disconnecting")
        self.phy.disconnect_usb(self.usb_set_time)
        usb_detail_before = self._storage_provider.get_usb_details()
        self._log.info("USB connecting")
        self.phy.connect_usb_to_sut(self.usb_set_time)
        time.sleep(self.usb_set_time)
        self._test_content_logger.end_step_logger(5, return_val=True)
        self._test_content_logger.start_step_logger(6)
        usb_detail_after = self._storage_provider.get_usb_details()
        self._log.debug("Output after usb connect {}".format(usb_detail_after))
        difference = self.get_lsub_difference(usb_detail_before, usb_detail_after)
        device_connected = self._storage_provider.get_bus_device_type_info(difference)
        self.verify_hotplug_device_status(device_connected, self.usb_connected)
        self._test_content_logger.end_step_logger(6, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UsbDetection.main() else Framework.TEST_RESULT_FAIL)
