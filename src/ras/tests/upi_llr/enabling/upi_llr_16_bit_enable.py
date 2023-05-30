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

from src.ras.tests.upi_llr.upi_llr_common import UpiLlrCrcCommon


class Verify16BitRollingUpiLlrCrcIsEnabled(UpiLlrCrcCommon):
    """
    Glasgow_id : 59151.2

    Intel UPI links are capable of detecting various types of correctable and uncorrected errors. Once an error is
    detected, it is reported (logged and signaled) using Intel UPI link MCA banks and platform specific log registers.
    """
    _BIOS_CONFIG_FILE = "../upi_llr_16_bit_bios_knobs.cfg"
    TEST_CASE_ID = ["G59151.2 - UPI LLR- 16-bit CRC Enabling"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new Verify16BitRollingUpiLlrCrcIsEnabled object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(Verify16BitRollingUpiLlrCrcIsEnabled, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        super(Verify16BitRollingUpiLlrCrcIsEnabled, self).prepare()

    def execute(self):
        """
        This method is used to execute check_upi_llr_crc_enabled method to verify if Upi Llr rolling crc is enabled
        through Bios Knobs.

        :return: True or False based on the Output of check_upi_llr_crc_enabled method.
        """
        return self.check_upi_llr_crc_enabled(expected_crc_mode=self.CRC_16_BIT_MODE)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if Verify16BitRollingUpiLlrCrcIsEnabled.main() else Framework.TEST_RESULT_FAIL)
