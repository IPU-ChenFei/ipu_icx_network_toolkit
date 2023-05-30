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

class UsbHUB3Windows(ContentBaseTestCase):
    """
    HPQC ID : H81081-PI_USB_USBHub3_W
    Check USB2.0 hub and USB3.0 hub functionality
    """

    TEST_CASE_ID = ["H81081", "PI_USB_USBHub3_W"]

    STEP_DATA_DICT = {
        1: {'step_details': 'All attached devices on hub function as expected and are accessible from system',
            'expected_results': 'Devices should function and be accessible.'}
        }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of UsbDetection

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(UsbHUB3Windows, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.usb_utils = USBProvider.factory(test_log, cfg_opts, self.os)

    def execute(self):
        """
        This method executes the below:
        1. copies the USB tree zip file to sut.
        2. verifies the devices are accessible as expected.
        :return: True if test case pass
        """
        self._log.info("Verifying the connected USB devices are Recognized")
        self._test_content_logger.start_step_logger(1)
        self.usb_utils.get_device_details(self)
        self._test_content_logger.end_step_logger(1, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UsbHUB3Windows.main() else Framework.TEST_RESULT_FAIL)
