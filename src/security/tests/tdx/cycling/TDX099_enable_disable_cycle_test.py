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
    :Enable-Disable Cycle TDX Test:

    Boot to OS with TDX VMM enabled and launch TD guest.  Disable TDX, reboot SUT, attempt to boot TDX guest. Repeat
    for prescribed number of cycles.
"""

import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest
from src.lib import content_exceptions


class TdxEnableDisableCycleTest(LinuxTdxBaseTest):
    """
            This recipe tests TD guest boot and requires the use of a OS supporting TD guests.

            :Scenario: Boot to an OS with a TDX enabled VMM and launch a TD guest VM.  Disable TDX, reboot SUT, attempt
            to boot TDX guest. Repeat for given number of cycles.

            :Phoenix ID:  18014072809

            :Test steps:

                :1: Boot to an OS with a TDX enabled VMM.

                :2: Launch a TD guest VM.

                :3: Disable TDX and warm reset the SUT.

                :4: Attempt to boot a TD guest (this should fail).

                :5: Enable TDX.

                :6: Repeat steps 1-5 for given number of cycles.

            :Expected results: Each time after a warm reset, the SUT should boot to the OS.  Each time a TD guest is
            attempted to be launched with TDX enabled should be successful.  Each time a TD guest is attempted to be
            launched with TDX disabled should fail.

            :Reported and fixed bugs:

            :Test functions:

        """

    def execute(self) -> bool:
        key = 0
        cycles = self.tdx_properties[self.tdx_consts.TDX_DISABLE_ENABLE_CYCLES]
        for cycle_number in range(0, cycles):
            self._log.info(f"Iteration {cycle_number} of {cycles}.")
            self._log.info(f"Starting TD guest {key}.")
            self.launch_vm(key=key, tdvm=True)
            self._log.debug(f"Attempting to execute SSH command to VM key {key}.")
            if self.vm_is_alive(key=key):
                self._log.debug("SSH was successful; VM is up.")
            else:
                raise content_exceptions.TestFail(f"VM {key} failed to boot! Iteration {cycle_number} of {cycles}.")
            self._log.info("Disabling TDX.")
            self.set_knobs(self.tdx_only_bios_disable)
            self.start_vm(key=key, tdvm=True)
            self._log.debug("Checking TD guest is not up.")
            self._log.debug(f"Attempting to execute SSH command to VM key {key}.")
            if not self.vm_is_alive(key=key):
                self._log.debug("VM is not accessible; TD guest could not be launched with TDX disabled.")
            else:
                raise content_exceptions.TestFail("TD guest could be launched with TDX disabled. Iteration "
                                                  f"{cycle_number} of {cycles}.")

            self.set_knobs(self.tdx_only_bios_enable, reboot_on_knob_set=False)
            self.perform_graceful_g3()
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxEnableDisableCycleTest.main() else Framework.TEST_RESULT_FAIL)
