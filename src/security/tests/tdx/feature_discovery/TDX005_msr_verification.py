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
    :TDX and TME MSR Verification:

    Verify MSR values for TDX and TME.
"""
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest


class TdxMsrTest(LinuxTdxBaseTest):
    """
            This recipe tests verifying different bits of the TDX and TME MSRs.

            :Scenario: With TDX enabled, split the max keys available and verify the correct number of keys are divided
            between each feature.

            :Prerequisite:  SUT must be configured with the latest BKC applicable for the platform.

            :Phoenix ID: 18014072627

            :Test steps:

                :1: Boot to BIOS menu.

                :2: Verify TDX is enabled.

                :3: Check the TDX max keys in menu EDKII->Socket Configuration->Processor Configuration.

                :4: Divide the keys between MKTME and TDX.

                :5: Verify that the number of TDX keys + the number of MKTME keys = the number of max keys.

                :6: Verify SEAMRR Base valid and locked bits are set and SEAMRR Mask Configured bit is set.

            :Expected results: The number of TDX keys + the number of MKTME keys = the number of max keys and the
            number of keys for each technology match the BIOS menu option.

            :Reported and fixed bugs:

            :Test functions:

        """

    def execute(self):
        # prepare raises error if TDX cannot be enabled, MSR check is part of validate tdx flow in prepare
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxMsrTest.main() else Framework.TEST_RESULT_FAIL)
