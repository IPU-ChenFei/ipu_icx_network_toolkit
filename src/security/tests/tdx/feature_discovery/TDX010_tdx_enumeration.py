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
    :TDX Enumeration:

    Verify TDX is enumerated.
"""
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest


class TdxEnumeration(LinuxTdxBaseTest):
    """
            This recipe verifies TDX is enumerated.

            :Scenario: With TDX enabled, check MTTC Capabilities MSR to verify TDX is enumerated.

            :Prerequisite:  SUT must be configured with the latest BKC applicable for the platform.

            :Phoenix ID: 18014073872

            :Test steps:

                :1: Boot to BIOS menu.

                :2: Verify TDX is enabled.

                :3: Read MTTC Capabilities MSR and verify TDX is enumerated.

            :Expected results: The bit for TDX enumeration should be set.  For EGS, this is bit 15.

            :Reported and fixed bugs:

            :Test functions:

        """

    def execute(self):
        self._log.info("Checking TDX enumeration.")
        results = self.msr_read(self.tdx_consts.RegisterConstants.MTTR_CAPABILITIES)
        if not self.bit_util.is_bit_set(results, self.tdx_consts.MTTRCapabilitiesBits.TDX_ENUMERATION):
            self._log.error("TDX enumeration bit is not set! MSR 0x{:x}: 0x{:x}".format(
                self.tdx_consts.RegisterConstants.MTTR_CAPABILITIES, int(results)))
            return False

        self._log.info("TDX enumeration bit is set! MSR 0x{:x}: 0x{:x}".format(
            self.tdx_consts.RegisterConstants.MTTR_CAPABILITIES, int(results)))
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxEnumeration.main() else Framework.TEST_RESULT_FAIL)
