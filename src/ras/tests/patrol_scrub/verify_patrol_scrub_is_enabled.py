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

from src.ras.tests.patrol_scrub.patrol_scrub_common import PatrolScrubCommon


class VerifyPatrolScrubIsEnabled(PatrolScrubCommon):
    """
        Glasgow_id : 58556
        Patrol scrubbing pro-actively searches the system memory repairing correctable errors. Prevents accumulation of
        single-bit errors and turning it into an uncorrected error. Patrol Scrubbing is programmed at rank address
        granularity and therefore called as Rank Address Based Patrol Scrubbing Mode or Legacy Patrol Scrubbing Mode.
        Skylake has added a new capability called System Address Based Patrol Scrubbing Mode. In this mode, Patrol
        scrubber can be programmed to scrub a selected system physical address range.
        This test performs a basic Patrol Scrub BIOS knob enable and verifies all active memory controllers correctly
        set the appropriate register bit.

        Test case flow:

        -Check if socekts are populated.
        -Verify if Patrol Scrub is enabled properly
        -Clean up after the test runs

    """
    _BIOS_CONFIG_FILE = "verifying_patrol_scrub_is_enabled_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VerifyPatrolScrubIsEnabled object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyPatrolScrubIsEnabled, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

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
        super(VerifyPatrolScrubIsEnabled, self).prepare()

    def execute(self):
        """
        This Method is used to execute is_patrol_scrub_enabled method to verify if patrol scrub is successfully enabled
        or not.

        :return: True or False based on is_patrol_scrub_enabled method
        """
        return self.is_patrol_scrub_feature_enabled()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyPatrolScrubIsEnabled.main() else Framework.TEST_RESULT_FAIL)
