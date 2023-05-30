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

from src.storage.test.storage_common import StorageCommon
from src.lib.test_content_logger import TestContentLogger
from src.multisocket.lib.multisocket_common import MultiSocketCommon


class PCHIoModeW(StorageCommon):
    """
    Phoenix 16014226371, PI_IO_PCHIO_mode_W

    This test cases to Check for IO devices in PCH-IO mode for Windows..
    """

    TEST_CASE_ID = ["16014226371", "PI_IO_PCHIO_mode_W"]
    step_data_dict = {1: {'step_details': 'boot to OS',
                          'expected_results': 'successfully Booted to OS'},
                      2: {'step_details': 'check all IO devices',
                          'expected_results': 'successfully checked all IO devices..'},
                      3: {'step_details': 'verify the basic checks for IO',
                          'expected_results': 'successfully verified the baisc check for IO ...'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance PCHIoModeW

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        :raises: None
        """

        # calling base class init
        super(PCHIoModeW, self).__init__(test_log, arguments, cfg_opts)
        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._multisock_obj = MultiSocketCommon(test_log, arguments, cfg_opts)
        self._silicon_family = self._common_content_lib.get_platform_family()

    def prepare(self):
        # type: () -> None
        """

        :return: None
        """
        self._test_content_logger.start_step_logger(1)
        mode = self._multisock_obj.get_mode_info(self.serial_log_dir, self._SERIAL_LOG_FILE)
        self._log.info("System is in {}".format(mode))
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. check for IO  devices
        2. verify basic checks

        :return: True, if the test case is successful.
        """
        self._test_content_logger.start_step_logger(2)
        get_ioe_device_dict = self._multisock_obj.get_ioe_device_dict()
        self._log.debug("IO devices {}".format(get_ioe_device_dict))
        self._test_content_logger.end_step_logger(2, return_val=True)
        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        self.copy_text_file_to_all_drives()
        sut_ip = self._common_content_lib.get_sut_ip()
        self._log.info("SUT IP is  {}".format(sut_ip))
        output = self._common_content_lib.execute_sut_cmd("ipconfig", "Getting IP", 10.0)
        ip_values = output
        for each in str(output).split("\n"):
            if "IPv4 Address" in each:
                ip_values = each.split(":")[1].strip()
        sut_ip_part = sut_ip.rsplit('.', 1)[0]
        for ip in ip_values:
            if sut_ip_part in ip:
                self._common_content_lib.ping_ip(ip)
        self._test_content_logger.end_step_logger(3, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PCHIoModeW.main() else Framework.TEST_RESULT_FAIL)
