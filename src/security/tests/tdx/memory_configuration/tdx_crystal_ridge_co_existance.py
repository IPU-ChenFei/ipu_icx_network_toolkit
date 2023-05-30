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
    :TDX and Crystal Ridge DIMM co-existance:

    Verify that the TDX guest can coexist with Crystal Ridge DIMM + DDR5.
"""
import sys


from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.tdvm.TDX008a_launch_tdvm_windows import TDLaunchWindows


class TdxCrystalRidgeDIMMCoexistanceWindows(TDLaunchWindows):
    """
            This recipe tests memory configuration compatibility and is applicable to TDX compatible OSs.

            :Scenario:  TDX Guest can be load with 1LM volatile memory mode on Crystal Ridge DIMM

            :Prerequisite:  SUT must be configured with the latest BKC applicable for the platform and an ITP probe
            must be attached to the SUT. The Platform should have equal number of Crystal Ridge dimms and DDR5

            :Phoenix ID: 22013314464

            :Test steps:

                :1: Verify TDX is enabled.

                :2: Boot a TD guest.

            :Expected results: SUT should boot to OS with TDX enabled and TD guest should be able to boot.

            :Reported and fixed bugs:

            :Test functions:

    """
    def execute(self):
        self._log.info(f"This test assumes that the Platform should have equal number of Crystal Ridge dimms and DDR5")
        return super(TdxCrystalRidgeDIMMCoexistanceWindows, self).execute()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxCrystalRidgeDIMMCoexistanceWindows.main() else Framework.TEST_RESULT_FAIL)
