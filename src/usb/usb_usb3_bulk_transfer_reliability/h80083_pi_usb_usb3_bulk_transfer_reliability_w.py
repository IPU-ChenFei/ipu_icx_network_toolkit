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

from src.lib.dtaf_content_constants import TimeConstants
from src.lib.test_content_logger import TestContentLogger
from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.usb_provider import USBProvider


class Usb3BulkTransferReliabilityW(ContentBaseTestCase):
    """
    HPQC ID : H80083-PI_USB_USB3BulkTransferReliability_W
    Glasgow ID : G44094.3-DV-USB3-Bulk Transfer Reliability

    Ensure that USB3.0 storage devices transfers files in bulk transfer mode without generating errors.
    """
    TEST_CASE_ID = ["H80083", "PI_USB_USB3BulkTransferReliability_W", "G44094.3", "DV-USB3-Bulk_Transfer_Reliability"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Clear System logs and boot to OS.',
            'expected_results': 'System Log cleared and booted to OS.'},
        2: {'step_details': 'Install the driver for the Passmark loopback plug.',
            'expected_results': 'Driver for the Passmark loopback plug has been installed successfully.'},
        3: {'step_details': 'Install the USB3COnsole to execute the Passmark loopback plug and '
                            'Set Test Mode to Loopback, Duration to 15 minutes, Endpoint Type to Bulk',
            'expected_results': 'USB3COnsole has been installed successfully and '
                                'Loopback testing has been executed successfully for 15mins.'},
        4: {'step_details': 'Check for any errors in windows event log.',
            'expected_results': 'No errors found in windows event log.'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of Usb3BulkTransferReliabilityW

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(Usb3BulkTransferReliabilityW, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.usb_utils = USBProvider.factory(test_log, cfg_opts, self.os)

    def prepare(self):
        # type: () -> None
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """
        self._test_content_logger.start_step_logger(1)
        super(Usb3BulkTransferReliabilityW, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This method executes the below:
        1. Install the driver for the Passmark loopback plug.
        2. Install the USB3COnsole to execute the Passmark loopback plug and
            Set Test Mode to Loopback, Duration to 15 minutes, Endpoint Type to Bulk execute Loopback testing
        3. Check for any errors in windows event logs

        :raise: content_exceptions.TestFail if any errors found in windows event log
        :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(2)
        # install loopback driver
        self.usb_utils.install_loopback_driver()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        # run loopback test for 15mins
        self.usb_utils.execute_passmark_loopback(self.usb_utils.MODE[0], self.usb_utils.END_POINT[0],
                                                 TimeConstants.FIFTEEN_IN_SEC)
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self.usb_utils.check_for_windows_error_log()
        self._test_content_logger.end_step_logger(4, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if Usb3BulkTransferReliabilityW.main() else Framework.TEST_RESULT_FAIL)
