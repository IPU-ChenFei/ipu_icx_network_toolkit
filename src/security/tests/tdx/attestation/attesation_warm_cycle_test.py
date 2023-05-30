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
    :OS Warm cycle TDX test:

    Boot to OS with TDX VMM enabled and launch TD guest.  Warm reset SUT back to OS and launch TD guest again.  Repeat
    for prescribed number of cycles.
"""

import sys
import logging
import argparse
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.lib.dtaf_content_constants import ResetStatus
from src.security.tests.tdx.cycling.TDX0100_warm_cycle_test import TdxOsWarmCycleTest
from src.security.tests.tdx.attestation.linux_attestation_base_test import TdAttestation


class TdAttestationWarmCycle(TdxOsWarmCycleTest):
    """
           This test case is to test the coexistence of disabled HyperThreading and TDX attestation.

            :Scenario: Disable HyperThreading in BIOS and run TDX attestation verification script.

            :Phoenix IDs: 22013145077

            :Test steps:

                :1: Enable TDX.

                :2: Boot to OS and run TDX attestation script.

                :3: Warm reset the SUT.

                :4: Repeat steps 2 and 3 for given number of cycles.

            :Expected results: Each time after a warm reset, the SUT should boot to the OS.  Each time the TDX
            attestation script is run, there should be no errors in the log file.

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
        super(TdAttestationWarmCycle, self).__init__(test_log, arguments, cfg_opts)
        self.attestation = TdAttestation(test_log, arguments, cfg_opts)
        try:
            self.total_cycles = self.multiple_tdvms.tdx_properties[self.multiple_tdvms.tdx_consts.ATTESTATION_WARM_CYCLES]
        except (IndexError, KeyError):
            try:
                self.total_cycles = self.multiple_tdvms.tdx_properties[self.multiple_tdvms.tdx_consts.WARM_CYCLES]
            except (IndexError, KeyError):
                raise content_exceptions.TestSetupError("Cycles are not defined in "
                                                        "<TDX><LINUX><cycling><attestation_warm_reboot_cycles>. Please "
                                                        "check the content_configuration.xml file for this section "
                                                        "and provide a valid integer value.")
        self.cycle_test_type = "attestation_warm"

    def prepare(self) -> None:
        super(TdAttestationWarmCycle, self).prepare()
        self.attestation.prepare()

    def execute(self) -> bool:
        return super(TdAttestationWarmCycle, self).execute()

    def during_cycle(self, cycle_number: int) -> None:
        """Run attestation check on each reboot.
        :param cycle_number: number of current cycle; provided for use with log files."""
        if not self.attestation.run_attestation_check():
            raise content_exceptions.TestFail(f"Failed attestation on {cycle_number}.")


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdAttestationWarmCycle.main() else Framework.TEST_RESULT_FAIL)
