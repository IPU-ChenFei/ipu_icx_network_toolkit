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
    :TDX TDVM can be created on top of TDX capable VMM:

    Verify TDVM can be created on top of TDX capable VMM.
"""

import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.tdx_common_windows import WindowsTdxBaseTest
from src.lib import content_exceptions


class TDLaunchWindows(WindowsTdxBaseTest):
    """
            This recipe tests TDVM boot and requires the use of a OS supporting TDVM.

            :Scenario: Launch the TDVM created and verify the VM can boot.

            :Phoenix IDs: 18014072405, 18014548761, 18014072273

            :Test steps:

                With a TDVM created (from TDX007_TDVM_Build), launch TDVM.

            :Expected results: TDVM should boot.

            :Reported and fixed bugs:

            :Test functions:

        """

    def execute(self):
        tdvm = True
        key = 0

        self._log.info("Get all tdx VM lists in the hyper v manager")
        self.get_vm_list()
        self.clean_all_vms()
        key, vm_name = self.create_vm_name(key, legacy=False)

        ret_val = self.launch_tdx_vm_with_mtc_settings(key,
                                                       vm_name,
                                                       tdvm,
                                                       self.is_vm_tdx_enabled,
                                                       self.enable_ethernet,
                                                       self.vm_reboot_timeout)
        if ret_val is False:
            raise content_exceptions.TestFail("Failed to launch TDVM")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDLaunchWindows.main() else Framework.TEST_RESULT_FAIL)
