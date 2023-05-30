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
    :TDX Linux TDVM can be created on top of TDX capable Hyper-v VMM:

    Verify Linux TDVM can be created on top of TDX capable Hyper-v VMM.
"""

import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.tdx_common_windows import WindowsTdxBaseTest


class LinuxTDVMStressWindows(WindowsTdxBaseTest):
    """
            This recipe tests TDVM boot and requires the use of a OS supporting TDVM.

            :Scenario: Launch multiple Linux TDVMs created and verify the VM can boot

            :Phoenix IDs: 14015392689

            :Test steps:

                Create 5 or more tdvm guest images and run parallel

            :Expected results: all Linux TDVM should boot
        """
    MINIMUM_VMS = 5

    def execute(self):
        number_of_vms = int(self.tdx_properties[self.tdx_consts.NUMBER_OF_VMS])
        if number_of_vms < self.MINIMUM_VMS:
            number_of_vms = self.MINIMUM_VMS

        self._log.info("Get all tdx VM lists in the hyper v manager")
        self.get_vm_list()
        self.clean_all_vms()
        self.clean_linux_vm_tdx_apps()

        for vm_number in range(0, number_of_vms):
            key, vm_name = self.create_vm_name(vm_number, legacy=False, vm_os="LINUX")
            self.launch_ubuntu_td_guest(key, vm_name)
            self._log.info(f"TDVM {vm_name} is alive after launching.")

        return True

    def cleanup(self, return_status):
        """DTAF cleanup"""
        self.clean_linux_vm_tdx_apps()
        super(LinuxTDVMStressWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LinuxTDVMStressWindows.main() else Framework.TEST_RESULT_FAIL)
