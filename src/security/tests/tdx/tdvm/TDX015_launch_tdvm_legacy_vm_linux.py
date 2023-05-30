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
    :TDX TDVM and legacy VM can run in parallel on top of TDX capable VMM:

    Verify TDVM and legacy VM can be created on top of TDX capable VMM.
"""

import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest


class TdGuestLegacyVMLaunchLinux(LinuxTdxBaseTest):
    """
            This recipe tests TD guest and legacy VM parallel  boot and requires the use of a OS supporting TDVM.
            
            Number of TD guests and legacy VMs can be customized with <TDX>><number_of_vms> tag in
            content_configuration.xml.  Current ratio is 1:1  for this test case (i.e. if number_of_vms is 2, then 2
            TD guests and 2 legacy VMs will be created).

            :Scenario: Launch the TD guest and legacy VM created and verify both VMs can boot.

            :Phoenix IDs: 18014072534

            :Test steps:

                :1: Launch a TD guest.

                :2: Launch a legacy VM guest.

                :3: Confirm both VMs booted successfully.

            :Expected results: Both the TD guest and the legacy VM should boot.

            :Reported and fixed bugs:

            :Test functions:

        """

    def execute(self):
        num_vms = self.tdx_properties[self.tdx_consts.NUMBER_OF_VMS] * 2
        for idx in range(0, num_vms, 2):
            self._log.info(f"Starting TD guest {idx}.")
            self.launch_vm(key=idx, tdvm=True)
            self._log.info(f"Successfully launched TD guest {idx}.")
    
            idx = idx + 1
            self._log.info(f"Launching legacy VM {idx}.")
            self.launch_vm(key=idx, tdvm=False)
            self._log.info(f"Successfully launched legacy VM {idx}.")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdGuestLegacyVMLaunchLinux.main() else Framework.TEST_RESULT_FAIL)
