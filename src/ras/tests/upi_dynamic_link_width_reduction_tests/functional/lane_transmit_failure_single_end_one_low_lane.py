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


class UpiLaneTransmitFailureSingleEndOneLowLane(UpiLaneFailoverCommon):
    """
    Glasgow_id : 58358
    H81566-PI_RAS_UPI_lane_transmit_failure_single_end_one_low_lane

    Intel UPI links are capable of detecting various types of correctable and uncorrected errors. Once an error is
    detected, it is reported (logged and signaled) using Intel UPI link MCA banks and platform specific log registers.

    This test causes a UPI port 1 transmit failure on a single link endpoint on all low lanes [7:0] and verifies the
    error is corrected and signaled to the OS as such.
    """
    _BIOS_CONFIG_FILE = "upi_lane_failure_bios_knobs.cfg"
    TEST_CASE_ID = ["H81566-G58358", "PI_RAS_UPI_lane_transmit_failure_single_end_one_low_lane"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UpiLaneTransmitFailureSingleEndOneLowLane object

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UpiLaneTransmitFailureSingleEndOneLowLane, self).__init__(test_log, arguments, cfg_opts,
                                                                        self._BIOS_CONFIG_FILE)

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
        super(UpiLaneTransmitFailureSingleEndOneLowLane, self).prepare()

    def execute(self):
        """
        This method is used to execute check_upi_lane_failover_enabled to verify if Upi self healing is enabled and
        causes a UPI port 1 transmit failure on a single link endpoint on all low lanes [7:0] and verifies the error is
         corrected and signaled to the OS as such.

        :return: True or False based on the Output of inject_and_check_upi_link_width_change_failure
        """
        self.check_upi_lane_failover_enabled()
        return self.inject_and_check_upi_link_width_change_failure(self.TRANSMIT,
                                                                   self.UPI_LANE_MASK_DISABLE_FIRST_LOW_LANE)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UpiLaneTransmitFailureSingleEndOneLowLane.main() else
             Framework.TEST_RESULT_FAIL)
