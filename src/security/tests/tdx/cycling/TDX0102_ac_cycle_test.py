#!/usr/bin/env python
##########################################################################
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
##########################################################################
"""
    :OS AC cycle TDX test:

    Boot to OS with TDX VMM enabled and launch TD guest.  Shut down the SUT from the OS, remove AC power temporarily,
    restore AC power, boot to the OS, and launch TD guest again.  Repeat for prescribed number of cycles.
"""

import sys
import logging
import argparse
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.lib.dtaf_content_constants import ResetStatus
from src.security.tests.tdx.cycling.tdx_cycle_common import TdxCycleTest


class TdxOsAcCycleTest(TdxCycleTest):
    """
            This recipe tests TD guest boot and requires the use of a OS supporting TD guests.

            :Scenario: Boot to an OS with a TDX enabled VMM and launch a TD guest VM.  Shut down the SUT and remove AC
            power.  Restore AC power, boot SUT to OS,  relaunch the TD guest.  Repeat for given number of cycles.

            :Phoenix ID: 22012522960

            :Test steps:

                :1: Boot to an OS with a TDX enabled VMM.

                :2: Launch a TD guest VM.

                :3: Shut down the SUT from the OS.

                :4: Remove AC power from the SUT.

                :5: Restore AC power to the SUT.

                :6: Repeat steps 1-5 for given number of cycles.

            :Expected results: Each time after an AC reset, the SUT should boot to the OS.  Each time a TD guest is
            attempted to be launched should be successful.

            :Reported and fixed bugs:  Removed usage of power management reset class as it has undocumented
            dependencies.

            :Test functions:

        """

    def __init__(self, test_log: logging.Logger, arguments: argparse.Namespace, cfg_opts: ElementTree) -> None:
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(TdxOsAcCycleTest, self).__init__(test_log, arguments, cfg_opts)
        try:
            self.total_cycles = self.multiple_tdvms.tdx_properties[self.multiple_tdvms.tdx_consts.AC_CYCLES]
        except (IndexError, KeyError):
            raise content_exceptions.TestSetupError("Cycles are not defined in "
                                                    "<TDX><LINUX><cycling><ac_reboot_cycles>. Please check the "
                                                    "content_configuration.xml file for this section and provide a "
                                                    "valid integer value.")
        self.cycle_test_type = "G3"

    def execute(self) -> bool:
        return super(TdxOsAcCycleTest, self).execute()

    def power_cycle(self) -> ResetStatus:
        """AC cycles the system."""
        return self.graceful_g3()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxOsAcCycleTest.main() else Framework.TEST_RESULT_FAIL)
