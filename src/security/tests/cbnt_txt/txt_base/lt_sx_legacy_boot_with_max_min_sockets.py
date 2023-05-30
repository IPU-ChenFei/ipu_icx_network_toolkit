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

from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions


class LtSxLegacyBootWithMaxMinSockets(TxtBaseTest):
    """
    Glasgow ID : G58218-LT-SX Legacy boot with max/min sockets
    This Test case is to demonstrate With TXT Disabled by selecting trusted OS
    and ensuring that boots is non-trusted

    pre-requisites:
    1.Ensure that the system is in sync with the latest BKC.
    2.Ensure that you have a Linux OS image or hard drive with tboot installed.
    3.Ensure that the platform has a TPM provisioned with an ANY policy installed and active
    """
    TEST_CASE_ID = ["G58218", "LT-SX_Legacy_boo_with_max/min_sockets"]
    _BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_disable.cfg"
    STEP_DATA_DICT = {1: {'step_details': 'Disable TXT bios knobs 58991 TC',
                          'expected_results': 'Verify TXT bios disabled'},
                      2: {'step_details': 'Check SUT is booted to Untrusted boot',
                          'expected_results': 'Verify SUT is booted to Untrusted boot'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of LtSxLegacyBootWithMaxMinSockets
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(LtSxLegacyBootWithMaxMinSockets, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.tboot_index = None

    def prepare(self):
        # type: () -> None
        """
        Pre-validating whether sut is configured with tboot by getting the tboot index in OS boot order
        Loading BIOS defaults settings.
        Sets the bios knobs according to configuration file and verifies if bios knobs sets successfully.
        :return: None
        """
        self._test_content_logger.start_step_logger(1)
        # get the tboot_index from grub menu entry
        self.tboot_index = self.get_tboot_boot_position()
        # Set tboot as default boot and reboot
        self.set_default_boot_entry(self.tboot_index)
        self.enable_and_verify_bios_knob() # enable and verify bios knobs
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This function is used to check SUT did not boot in Untrusted environment

        :raise: raise content_exceptions TestFail if SUT is booted to Trusted Boot
        :return: True if Test case pass else fail
        """
        self._test_content_logger.start_step_logger(2)
        self.verify_sut_booted_in_tboot_mode(self.tboot_index)
        # To verify the sut boot in Untrusted mode
        if not self.verify_untrusted_boot():
            raise content_exceptions.TestFail("The OS is booted in trusted mode, even when TXT is disabled in BIOS")
        self._log.info("The OS is booted in Non - trusted mode after TXT disabled in BIOS... ")
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LtSxLegacyBootWithMaxMinSockets.main() else Framework.TEST_RESULT_FAIL)
