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

    Verify TDVM can be created on top of TDX capable VMM.
"""

import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.tdx_common_windows import WindowsTdxBaseTest


class LinuxTDVMEnterExitWindows(WindowsTdxBaseTest):
    """
            This recipe tests TDVM boot and requires the use of a OS supporting TDVM.

            :Scenario: Pause and resume Linux TDVM.

            :Phoenix IDs: 22015072727, 14015392714

            :Test steps:

                Launch a Linux TDVM and verify the TDVM can be paused and resumed.

            :Expected results: Linux TDVM be paused and resumed.

            :Reported and fixed bugs:

            :Test functions:

        """
    PAUSE_TIME = 60

    def execute(self):
        key = 0
        self._log.info("Get all tdx VM lists in the hyper v manager")
        self.get_vm_list()
        self.clean_all_vms()
        self.clean_linux_vm_tdx_apps()

        key, vm_name = self.create_vm_name(key, legacy=False, vm_os="LINUX")
        self.launch_ubuntu_td_guest(key, vm_name)
        vm_ip_address = self.get_vm_ipaddress_for_linux_guest(vm_name)
        self._log.info("VM is alive after launching.")
        self._log.info(f"Pausing VM {vm_name}.")
        self.pause_vm(vm_name, self.PAUSE_TIME)
        self._log.info(f"Waiting time {self.PAUSE_TIME}")
        time.sleep(self.PAUSE_TIME)

        # test whether VM is active
        try:
            ret_val = self.test_linux_vm_folder_accessible(vm_name, vm_ip_address)
            if ret_val is True:
                raise content_exceptions.TestFail("VM is still be accessible while paused")
        except RuntimeError as err:
            if "not in running state" not in str(err):
                raise content_exceptions.TestFail("VM is still be accessible while paused")

        self._log.info(f"Resuming VM {vm_name}.")
        self.resume_vm(vm_name)
        time.sleep(self.PAUSE_TIME)
        self._log.info(f"Verify  VM is running. {vm_name}")
        ret_val = self.test_linux_vm_folder_accessible(vm_name, vm_ip_address)
        if ret_val is True:
            self._log.info("VM is working after resume")
        else:
            raise content_exceptions.TestFail("VM is not accessible after resuming")
        return True

    def cleanup(self, return_status):
        """DTAF cleanup"""
        self.clean_linux_vm_tdx_apps()
        super(LinuxTDVMEnterExitWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LinuxTDVMEnterExitWindows.main() else Framework.TEST_RESULT_FAIL)
