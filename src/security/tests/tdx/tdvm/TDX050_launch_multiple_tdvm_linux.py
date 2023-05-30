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
    :Multiple TDX TDVMs can be created on top of TDX capable VMM:

    Verify multiple TDVMs can be created on top of TDX capable VMM.
"""

import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest
from src.lib import content_exceptions


class MultipleTDVMLaunch(LinuxTdxBaseTest):
    """
            This recipe tests TDVM boot and requires the use of a OS supporting TDVM.

            :Scenario: Launch the TDVM created and verify the VM can boot.

            :Phoenix IDs: 14013591018

            :Test steps:

                With a TDVM created (from TDX007_TDVM_Build), launch TDVM.

            :Expected results: TDVMs should all boot.

            :Reported and fixed bugs:

            :Test functions:

        """

    def execute(self) -> bool:
        num_vms = self.tdx_properties[self.tdx_consts.NUMBER_OF_VMS]
        self._log.info(f"Creating and launching {num_vms} VMs.")
        for key in range(0, num_vms):
            self._log.info(f"Starting TD guest {key}.")
            self.launch_vm(key=key, tdvm=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MultipleTDVMLaunch.main() else Framework.TEST_RESULT_FAIL)
