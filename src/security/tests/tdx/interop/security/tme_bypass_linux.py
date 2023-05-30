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
    :TME Bypass No Harm Test - Linux:

    Enable TME Bypass knob and verify TD guest can coexist with legacy VM.
"""

import sys
import os

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.tdvm.TDX015_launch_tdvm_legacy_vm_linux import TdGuestLegacyVMLaunchLinux


class TmeBypassLinux(TdGuestLegacyVMLaunchLinux):
    """
            This recipe tests TD guest boot and requires the use of a OS supporting TD guests.

            :Scenario: Enable TME Bypass knob with TDX knobs, then boot to TDX OS and boot a TD guest and a legacy VM.
            Both the TD guest and the legacy VM should boot successfully.

            The number of TD guests launched is configured by the <TDX><NUMBER_OF_VMS> value defined in
            content_configuration.xml.

            :Phoenix IDs: 22013223683

            :Test steps:

                :1:  Enable TME Bypass knob in BIOS menu.

                :2: Boot to TDX enabled Linux stack.

                :3: Launch a TD guest.

                :4: Launch a legacy VM guest.

                :5: Confirm both VMs booted successfully.

            :Expected results: TD guests and legacy VMs should all boot.

            :Reported and fixed bugs:

            :Test functions:

        """

    def prepare(self):
        super(TmeBypassLinux, self).prepare()
        self._log.info("Checking TME Bypass is enabled.")
        knob_file = self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_TME_BYPASS
        knob_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../../{knob_file}")
        self.check_knobs(knob_file, set_on_fail=True)
        if not self.tme_bypass_check():
            raise content_exceptions.TestSetupError("TME Bypass failed to be enable after setting BIOS knobs! Please "
                                                    "check your configuration and verify the parts used support bypass.")

    def execute(self):
        return super(TmeBypassLinux, self).execute()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TmeBypassLinux.main() else Framework.TEST_RESULT_FAIL)
