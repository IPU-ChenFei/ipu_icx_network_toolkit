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

from src.ras.tests.upi_dynamic_link_width_reduction_tests.upi_lane_failover_common import UpiLaneFailoverCommon


class PiProcessorUpiWidth(UpiLaneFailoverCommon):
    """
    Testcase_id : H53994, H79584

    Test and verify if UPI link Width of Tx Link and Rx Link
    """
    TEST_CASE_ID = ["H53994 - PI_Processor_UPI_Width_L","H79584 - PI_Processor_UPI_Width_L"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PiProcessorUpiWidth object

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PiProcessorUpiWidth, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Copy mcelog.conf file to sut and reboot
        2. Clear All Os Logs before Starting the Test Case
        3. Set the bios knobs to its default mode.
        4. Set the bios knobs as per the test case.
        5. Reboot the SUT to apply the new bios settings.
        6. Verify the bios knobs whether they updated properly.

        :return: None
        """
        super(PiProcessorUpiWidth, self).prepare()

    def execute(self):
        """
        This Method is Used to Verify Processor Upi Width by Getting Tx Link Width and Rx Link Width and Comparing Both
         of Them

        :return: True or False based on the Output of inject_and_check_upi_link_width_change_failure
        """
        return self.verify_processor_upi_width()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiProcessorUpiWidth.main() else Framework.TEST_RESULT_FAIL)
