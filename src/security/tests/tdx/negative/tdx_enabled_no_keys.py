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
    :TDX Enabled with No Keys:

    Enable TDX and assign all keys to TME-MT.  SUT should boot with TDX OS and MSRs should indicate SEAM is not valid.
"""
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest
from src.lib import content_exceptions


class TdxEnNoKeys(LinuxTdxBaseTest):
    """
            This recipe tests no harm of enabling TDX and assigning all available keys to TME-MT (no keys are allocated
            to TDX).

            :Scenario: With TDX enabled, reserve all available keys for TME-MT.

            :Prerequisite:  SUT must be configured with the latest BKC applicable for the platform.

            :Phoenix ID: https://hsdes.intel.com/appstore/article/#/22012469121

            :Test steps:

                :1: Boot to BIOS menu.

                :2: Verify TDX is enabled.

                :3: Set keys available to TDX to 0.

                :4: Reboot SUT to OS and verify that TDX cannot be enabled with no keys assigned.

            :Expected results: SUT should boot to OS with TDX enabled and TDX keys should not be set to zero.

            :Reported and fixed bugs:

            :Test functions:

        """

    def execute(self):
        self._log.info("TDX is enabled, setting key split to 0 for TDX.")

        try:
            self.split_keys(0)
        except (content_exceptions.TestSetupError, RuntimeError):
            self._log.info("Could not set keys to zero while TDX was enabled.")

        # verify TDX keys are not 0
        keys_after_split = self.get_keys("tdx")
        if keys_after_split == 0x0:
            raise RuntimeError("TDX keys could be assigned to 0 despite TDX being enabled! TDX keys: {}".format(
                keys_after_split))
        self._log.info("TDX keys could not be set to 0 with TDX enabled.")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxEnNoKeys.main() else Framework.TEST_RESULT_FAIL)
