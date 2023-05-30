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

import os
import re
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from src.provider.usb_provider import USBProvider
from src.lib.test_content_logger import TestContentLogger
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions
from src.lib.bios_util import ItpXmlCli


class UsbDetectionAndHotPlugWindows(ContentBaseTestCase):
    """
    HPQC ID : H51657-PI_USB_DetectionAndHotPlugUSB3_W

    This test case aims to detect hot plug USB device connected and to check the bcd value of mouse.
    """
    TEST_CASE_ID = ["H51657", "PI_USB_DetectionAndHotPlugUSB3_W"]
    REGEX_FOR_MOUSE_CLASS = r".*Class.*Mouse"
    REGEX_FOR_BCD_USB_VALUE_OF_MOUSE = r"bcdUSB.*0x200"

    STEP_DATA_DICT = {
        1: {'step_details': 'Clear the CMOS and Configure the BIOS to default settings',
            'expected_results': 'CMOS cleared and BIOS configured to default settings'},
        2: {'step_details': 'Boot to OS and Clear the system logs',
            'expected_results': 'System booted and logs cleared'},
        3: {'step_details': 'Run USBView. Check the bcdUSB register value of the mouse device',
            'expected_results': 'BcdUSB value of mouse is 0x0200'},
        4: {'step_details': 'Safely remove all the mice and USB keys. And check system logs',
            'expected_results': 'No Errors are logged in Event Logs after disconnecting USB Keys'},
        5: {'step_details': 'Plug back the USB devices. Wait until OS showed new device is ready for using',
            'expected_results': 'All devices get recognized by system and functions well'},
        6: {'step_details': 'Run USBView. Check the bcdUSB register value of the mouse device',
            'expected_results': 'BcdUSB value of mouse is 0x0200'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of UsbDetectionAndHotPlugWindows

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(UsbDetectionAndHotPlugWindows, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.itp_xml_cli_util = None
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = None
        self.usb_set_time = self._common_content_configuration.get_usb_set_time_delay()
        self.usb_connected = self._common_content_configuration.get_usb_device()
        self.usb_utils = USBProvider.factory(test_log, cfg_opts, self.os)
        self.log_dir = self._common_content_lib.get_log_file_dir()

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
        super(UsbDetectionAndHotPlugWindows, self).prepare()
        try:
            self._common_content_lib.clear_all_os_error_logs()
        except RuntimeError as e:
            self._log.error("failed to clear the logs, error is %s", str(e))
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        This method executes the below:
        1. Run USB Tree View and verify whether BCD Value of Mouse is 0x0200
        2. Disconnects the USB Keys from SUT and Verify whether there are any errors logged in Event Logs.
        3. Reconnects the Usb Keys and verify whether all Usb Keys are Recognized by System.
        4. Run USB Tree View and verify whether BCD Value of Mouse is 0x0200

        :return: True if all steps are executed successfully.
        :raise: content_exceptions.TestError if BCD Value of Mouse is Not as Expected.
        """
        self._test_content_logger.start_step_logger(3)
        self._log.info("Get USB Device Details Connected to SUT.")
        log_file = self.usb_utils.get_usb_device_details()
        with open(os.path.join(self.log_dir, os.path.split(log_file)[-1]), encoding="utf-16") as log_file:
            log_file_list = log_file.readlines()
            self._log.debug("Details of USB Keys are : {}".format("\n".join(log_file_list)))
            bcd_mouse_log_file = "".join(log_file_list).split(self.REGEX_FOR_BCD_USB_VALUE_OF_MOUSE)[0]
            if not re.search(self.REGEX_FOR_MOUSE_CLASS, bcd_mouse_log_file):
                raise content_exceptions.TestError("BCD Value of Mouse is not as Expected")
            self._log.info("BCD Value of Mouse is as Expected as 0x0200")
        self._test_content_logger.end_step_logger(3, True)

        self._test_content_logger.start_step_logger(4)
        self._log.info("Disconnecting USB Keys")
        self.phy.disconnect_usb(self.usb_set_time)
        self._log.debug("Verify whether there are any system errors are in Event Logs")
        system_errors = self._common_content_lib.check_if_mce_errors()
        self._log.info("System Logs are :{}".format(system_errors))
        if system_errors:
            raise content_exceptions.TestFail("System Errors are Captured in Log.")
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        self._log.info("Reconnecting USB Keys Back to SUT")
        self.phy.connect_usb_to_sut(self.usb_set_time)
        time.sleep(self.usb_set_time)
        self._log.debug("Verifying whether all devices get recognised by System and Functions as Expected")
        self.usb_utils.check_devices_writable()
        self._test_content_logger.end_step_logger(5, True)

        self._test_content_logger.start_step_logger(6)
        self._log.info("Get USB Device Details after Connecting USB Keys Back to SUT.")
        log_file = self.usb_utils.get_usb_device_details()
        with open(os.path.join(self.log_dir, os.path.split(log_file)[-1]), encoding="utf-16") as log_file:
            log_file_list = log_file.readlines()
            self._log.debug("Details of USB Keys are : {}".format("\n".join(log_file_list)))
            bcd_mouse_log_file = "".join(log_file_list).split(self.REGEX_FOR_BCD_USB_VALUE_OF_MOUSE)[0]
            if not re.search(self.REGEX_FOR_MOUSE_CLASS, bcd_mouse_log_file):
                raise content_exceptions.TestError("BCD Value of Mouse is not as Expected")
            self._log.info("BCD Value of Mouse is as Expected as 0x0200")
        self._test_content_logger.end_step_logger(6, True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UsbDetectionAndHotPlugWindows.main() else Framework.TEST_RESULT_FAIL)
