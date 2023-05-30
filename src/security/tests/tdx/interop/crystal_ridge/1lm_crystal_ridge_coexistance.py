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
    :TDX + Crystal Ridge Coexistence - 1LM:

    Verify TD guest can launch with Crystal Ridge in 1LM.
"""

import sys
import os

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.tdvm.TDX008a_launch_tdvm_linux import TDVMLaunchLinux


class TdxCrystalRidgeOneLM(TDVMLaunchLinux):
    """
            This recipe tests TDVM boot and requires the use of an OS supporting TDVM.  The SUT must be equipped with
            Crystal Ridge dimms.  Please consult the memory POR documentation for the product to verify supported
            configurations.

            :Scenario: Launch the TDVM created and verify the VM can boot.

            :Phoenix IDs: 22013314512

            :Test steps:

                :1:  Verify Crystal Ridge dimms exist on the SUT.

                :2:  Set memory topology to support 1LM.

                :3:  Enable TDX.

                :4:  Boot to the OS and launch a TD guest.

            :Expected results: TDVM should boot.

            :Reported and fixed bugs:

            :Test functions:

        """

    def prepare(self):
        if not self.check_for_crystal_ridge():
            raise content_exceptions.TestSetupError("SUT does not appear to have Crystal Ridge dimms installed!")
        self.tdx_properties[self.tdx_consts.LM_MODE] = "1LM"  # setting dimms to 1LM
        super(TdxCrystalRidgeOneLM, self).prepare()

    def execute(self):
        key = 0
        self.launch_vm(key=key, tdvm=True)
        return True  # no exceptions are raised


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxCrystalRidgeOneLM.main() else Framework.TEST_RESULT_FAIL)
