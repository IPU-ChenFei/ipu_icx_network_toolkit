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
    :Redfish warm cycle TDX test:

    Boot to OS with TDX VMM enabled and launch TD guest.  Warm reset SUT from BMC with Redfish, boot to the OS, and
    launch TD guest again.  Repeat for prescribed number of cycles.
"""

import sys
import logging
import argparse
from xml.etree import ElementTree

from dtaf_core.lib.exceptions import OsCommandTimeoutException
from dtaf_core.lib.dtaf_constants import Framework

from src.lib.dtaf_content_constants import ResetStatus
from src.security.tests.tdx.cycling.tdx_cycle_common import TdxCycleTest
from src.manageability.lib.redfish_test_common import RedFishTestCommon
from src.lib import content_exceptions


class TdxRedfishWarmCycleTest(TdxCycleTest):
    """
            This recipe tests TD guest boot and requires the use of a OS supporting TD guests.

            :Scenario: Boot to an OS with a TDX enabled VMM and launch a TD guest VM.  Warm reset the SUT and relaunch
            the TD guest.  Repeat for given number of cycles.

            :Phoenix ID: 22012522968

            :Test steps:

                :1: Boot to an OS with a TDX enabled VMM.

                :2: Launch a TD guest VM.

                :3: Warm reset the SUT from the BMC using Redfish.

                :4: Repeat steps 1-3 for given number of cycles.

            :Expected results: Each time after a warm reset, the SUT should boot to the OS.  Each time a TD guest is
            attempted to be launched should be successful.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log: logging.Logger, arguments: argparse.Namespace, cfg_opts: ElementTree) -> None:
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(TdxRedfishWarmCycleTest, self).__init__(test_log, arguments, cfg_opts)
        try:
            self.total_cycles = self.tdx_properties[self.multiple_tdvms.tdx_consts.REDFISH_CYCLES]
        except (IndexError, KeyError):
            raise content_exceptions.TestSetupError("Cycles are not defined in "
                                                    "<TDX><LINUX><cycling><redfish_reboot_cycles>. Please check the "
                                                    "content_configuration.xml file for this section and provide a "
                                                    "valid integer value.")
        self.cycle_test_type = "Redfish"
        self.redfish_obj = RedFishTestCommon(test_log, arguments, cfg_opts)

    def execute(self) -> bool:
        return super(TdxRedfishWarmCycleTest, self).execute()

    def power_cycle(self) -> ResetStatus:
        """Power cycle SUT with Redfish."""
        try:
            self.redfish_obj.redfish_graceful_restart()  # Perform graceful reset to platform from Redfish
        except RuntimeError:
            return ResetStatus.STATE_CHANGE_FAILURE
        except OsCommandTimeoutException:
            return ResetStatus.OS_NOT_ALIVE
        return ResetStatus.SUCCESS


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxRedfishWarmCycleTest.main() else Framework.TEST_RESULT_FAIL)
