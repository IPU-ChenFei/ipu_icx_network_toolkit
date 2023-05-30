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


class USBBigDataCopyReliabilityL(ContentBaseTestCase):
    """
    PHOENIX ID : 1509810653-PI_USB_BigDataCopyReliability_L
    Ensure that file copy between USB3 devices is successful and within expected time.

    eg. 50GB data within 6.5 minutes (1024*50/(150*(1-10%)))
    """
    TEST_CASE_ID = ["1509810653", "PI_USB_BigDataCopyReliability_L"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Check device connected to hub are accessible by running lsusb command and'
                            'verify bcdUSB value of each device connected to hub, and check if hdd is enumerated and '
                            'writable',
            'expected_results': 'Device connected are accessible and bcdUSB is as expected and hdd is enumerated and '
                                'writable'},
        2: {'step_details': 'Copy 50GB file to HDD and check the total time consumed',
            'expected_results': '50GB file copied successfully within 7 minutes.'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of USBBigDataCopyReliabilityL

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(USBBigDataCopyReliabilityL, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.usb_utils = USBProvider.factory(test_log, cfg_opts, self.os)
        self.usb_copy = UsbRemovableDriveProvider.factory(test_log, cfg_opts, self.os)

    def prepare(self):
        # type: () -> None
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """
        super(USBBigDataCopyReliabilityL, self).prepare()

    def execute(self):
        """
        This method executes the below:
        1. Check device connected to hub are accessible by running lsusb command and
           verify bcdUSB value of hdd and writable
        2: Copy 50GB file to HDD and check the total time consumed

        :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(1)
        self.usb_utils.verify_hdd_bcd_value()
        self.usb_utils.check_devices_writable()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self.usb_utils.copy_bulk_file_to_hdd()
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if USBBigDataCopyReliabilityL.main() else Framework.TEST_RESULT_FAIL)
