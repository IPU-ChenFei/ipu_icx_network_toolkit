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

from dtaf_core.lib.dtaf_constants import Framework
from src.provider.copy_usb_provider import UsbRemovableDriveProvider

from src.lib.test_content_logger import TestContentLogger
from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.usb_provider import USBProvider


class Usb3TestS0L(ContentBaseTestCase):
    """
    HPQC ID : H81079-PI_USB_USB3_TestS0_L, H51649-PI_USB_USB3ACPISleepTestS5_L
    Ensure that USB3.0 storage device (USB3.0 HDD in AP list or Master AP list) functonality with power off/on cycles,
    at least 5 times per port.
    """
    TEST_CASE_ID = ["H81079", "PI_USB_USB3_TestS0_L", "H51649", "PI_USB_USB3ACPISleepTestS5_L"]
    NO_OF_REBOOT = 5
    STEP_DATA_DICT = {
        1: {'step_details': 'Check device connected to hub are accessible by running lsusb command and'
                            'verify bcdUSB value of each device connected to hub, and check if hdd is enumerated and '
                            'writable',
            'expected_results': 'Device connected are accessible and bcdUSB is as expected and hdd is enumerated and '
                                'writable'},
        2: {'step_details': 'Shutdowns the system and reboot',
            'expected_results': 'System shutdowns and boots back'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of Usb3TestS0L

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(Usb3TestS0L, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.usb_utils = USBProvider.factory(test_log, cfg_opts, self.os)
        self.usb_copy = UsbRemovableDriveProvider.factory(test_log, cfg_opts, self.os)

    def prepare(self):
        # type: () -> None
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """
        super(Usb3TestS0L, self).prepare()

    def execute(self):
        """
        This method executes the below:
        1. Check device keyboard, mouse, hdd connected to hub are accessible by running lsusb command and
        verifies bcdUSB value of each device connected and hub as well and check if hdd is enumerated and
        writable.
        2. Shutdowns the system and again checks the device connected to SUT.

        :return: True if test case pass
        """
        self._log.info("Total reboots {} for the TC".format(self.NO_OF_REBOOT))
        for reboot in range(1, self.NO_OF_REBOOT+1):
            self._log.info("Current cycle is {}".format(reboot))
            self._test_content_logger.start_step_logger(1)
            self.usb_utils.verify_device_bcd_value(self.usb_utils.MOUSE, self.usb_utils.MOUSE_BCD)
            self.usb_utils.verify_device_bcd_value(self.usb_utils.KEYBOARD, self.usb_utils.KEYBOARD_BCD)
            self.usb_utils.verify_hdd_bcd_value()
            self.usb_utils.check_devices_writable()
            self.usb_utils.verify_hub_bcd_value()
            self._test_content_logger.end_step_logger(1, return_val=True)

            self._test_content_logger.start_step_logger(2)
            self.perform_graceful_g3()
            self._test_content_logger.end_step_logger(2, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if Usb3TestS0L.main() else Framework.TEST_RESULT_FAIL)
