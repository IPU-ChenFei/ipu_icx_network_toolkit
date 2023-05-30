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

from src.lib.test_content_logger import TestContentLogger
from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.usb_provider import USBProvider


class UsbHub3L(ContentBaseTestCase):
    """
    HPQC ID : H81080-PI_USB_USBHub3_L, H51652-PI_USB_USBHub3_L
    Check USB2.0 hub and USB3.0 hub functionality
    """
    TEST_CASE_ID = ["H81080", "PI_USB_USBHub3_L", "H51652", "PI_USB_USBHub3_L"]

    STEP_DATA_DICT = {
        1: {'step_details': 'Check device usb-key, keyboard, mouse connected to hub are accessible'
                            'and verify bcdUSB value',
            'expected_results': 'Device are accessible connected to hub and bcdUSB value matches the'
                                'configuration file value'},
        2: {'step_details': 'Verify Hub connected to SUT port has bcdUSB value as expected',
            'expected_results': 'Hub connected to SUT port has bcdUSB value as expected'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of UsbHub3L

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(UsbHub3L, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.usb_utils = USBProvider.factory(test_log, cfg_opts, self.os)

    def prepare(self):
        # type: () -> None
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """
        super(UsbHub3L, self).prepare()

    def execute(self):
        """
        This method executes the below:
        1. Check device usb-key, keyboard, mouse connected to hub are accessible by running lsusb command and
        verifies bcdUSB value.
        2. Verifies Hub connected to SUT port has bcdUSB value as expected

        :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(1)
        self.usb_utils.verify_usb_key_bcd_value()
        self.usb_utils.verify_device_bcd_value(self.usb_utils.KEYBOARD, self.usb_utils.KEYBOARD_BCD)
        self.usb_utils.verify_device_bcd_value(self.usb_utils.MOUSE, self.usb_utils.MOUSE_BCD)
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self.usb_utils.verify_hub_bcd_value()
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UsbHub3L.main() else Framework.TEST_RESULT_FAIL)
