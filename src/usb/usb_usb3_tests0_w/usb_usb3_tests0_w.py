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
from src.power_management.lib.reset_base_test import ResetBaseTest


class Usb3Tests0W(ContentBaseTestCase):
    """
    HPQC ID : H81082-PI_USB_USB3_TestS0_W, H51656-PI_USB_USB3ACPISleepTestS5_W
    
    Ensures that HDD, Usb hub, keyboard, mouse, pen drive are enumerated, connected to usb port 3.0 and writable
    """
    TEST_CASE_ID = ["H81082", "PI_USB_USB3_TestS0_W", "H51656", "PI_USB_USB3ACPISleepTestS5_W"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Copy UsbTreeView zip file from host to sut, unzip and generate UsbTreeView log file by '
                            'running UsbTreeView command and parse the log file to get device details',
            'expected_results': 'Copy, extract,log file generated and parse successfully'},
        2: {'step_details': 'Check the devices are disk drive and are writable or not ',
            'expected_results': 'Disk drives should be writable'},
        3: {'step_details': 'Use OS option to shut down system and Press power button to bring system back to S0 for '
                            'given number of iterations',
            'expected_results': 'System is back to S0 successfully and No yellow bang on USB devices in device manager'
                                ',USB mouse, keyboard function well and Both USB3 HDDs are enumerated and writable in'
                                ' all given iterations'}}

    SHUTDOWN_ITERATIONS = 5

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of Usb3TestS0L

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(Usb3Tests0W, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.usb_utils = USBProvider.factory(test_log, cfg_opts, self.os)
        self.reset_base_test = ResetBaseTest(test_log, arguments, cfg_opts)

    def prepare(self):  # type: () -> None
        """
        This Method is Used to Prepare the System for the Execution of Test Case.
        """
        super(Usb3Tests0W, self).prepare()

    def execute(self):
        """
        This method executes the below:
        1. Copy UsbTreeView zip file from host to sut, unzip and generate UsbTreeView log file by
                            running UsbTreeView command.
        2. Parse the generated usb tree view log file and verify device are enumerated, writable and usb port is 3.0
           as expected
        3. Shutdowns the system for given number of times and verify whether USB Devices are Writable.

        :return: True if test case pass or raise exception if fails
        """
        self._test_content_logger.start_step_logger(1)
        self.usb_utils.get_device_details()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self.usb_utils.check_devices_writable()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        for iteration in range(self.SHUTDOWN_ITERATIONS):
            self._log.info("Performing Shutdown Iteration{}".format(iteration+1))
            self.reset_base_test.graceful_s5()
            self.usb_utils.check_devices_writable()
            self._log.debug("After Shutdown Iteration{} USB Devices are Writable as Expected".format(iteration+1))
        self._log.info("After all {} Shutdown Iterations USB Devices are Writable".format(self.SHUTDOWN_ITERATIONS))
        self._test_content_logger.end_step_logger(3, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if Usb3Tests0W.main() else Framework.TEST_RESULT_FAIL)
