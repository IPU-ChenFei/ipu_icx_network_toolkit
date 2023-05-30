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
    :TDX NUMA ON / SNC OFF Memory Configuration:

    Verify the TDX memory range compatibility with NUMA ON and SNC OFF.
"""
import sys
import os

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.tdvm.TDX008a_launch_tdvm_linux import TDVMLaunchLinux


class TdxNumaOnSncOff(TDVMLaunchLinux):
    """
            This recipe tests memory configuration compatibility and is applicable to TDX compatible OSs.

            :Scenario: Verify the TDX memory range compatibility with NUMA ON and SNC OFF. Verifying system set-up of
            PRMRR regions with TDX enabled in memory configuration mode NUMA ON and SNC OFF.

            :Prerequisite:  SUT must be configured with the latest BKC applicable for the platform and an ITP probe
            must be attached to the SUT.

            :Phoenix ID: 18014073992

            :Test steps:

                :1: Verify TDX is enabled.

                :2: Boot to BIOS menu.

                :3: Verify the status of the following BIOS knobs:  Numa is enabled, UMA-based clustering is disabled.

                :4: Set Sub NUMA BIOS knob to Disable.

                :5: Reboot SUT to apply BIOs knobs and boot to OS.

                :6: Verify TD guest can boot.

            :Expected results: SUT should boot to OS with TDX enabled.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        """
        super(TdxNumaOnSncOff, self).__init__(test_log, arguments, cfg_opts)
        self._NUMA_SNC_KNOB = "../collateral/snc_dis_reference_knob.cfg"

    def execute(self):
        bios_knob_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._NUMA_SNC_KNOB)
        self._log.info("Checking BIOS knobs that Numa is enabled and Sub NUMA is disabled.")
        self._log.info("If knobs need to be modified, the knobs will be set and the SUT will undergo a warm reset.")
        self.check_knobs(bios_knob_file, set_on_fail=True)

        self._log.info("Verifying that TDX is still enabled.")
        if not self.validate_tdx_setup():
            raise RuntimeError("TDX is no longer enabled with SNC disabled.")

        return super(TdxNumaOnSncOff, self).execute()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxNumaOnSncOff.main() else Framework.TEST_RESULT_FAIL)
