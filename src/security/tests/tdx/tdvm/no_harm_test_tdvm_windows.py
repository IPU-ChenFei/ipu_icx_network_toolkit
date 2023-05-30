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
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.tdx_common_windows import WindowsTdxBaseTest
from src.lib import content_exceptions


class TDLaunchNoHarmWindows(WindowsTdxBaseTest):
    """
            This recipe tests TDVM boot and requires the use of a OS supporting TDVM.

            :Scenario: Launch the TDVM created and verify the VM can boot then disable the TDX support and
            verify whether VM can restart

            :Phoenix IDs: 18014074532

            :Test steps:

                Launch a TDVM and then disable TDX bios support and try to relaunch the VM. VM shouldn't launch
                without TDX support.

            :Expected results: TDVM should boot with TDX enabled and shouldn't launch without TDX support

            :Reported and fixed bugs:

            :Test functions:

        """
    def cleanup(self, return_status):
        # change BIOS knob to non TDX settings.
        self._log.info("Enabling the TDX bios settings and reboot the SUT")
        self.set_knobs(self.tdx_only_bios_enable)
        # Give cooling time to complete OS booting.
        time.sleep(self.WINDOWS_OS_REBOOT_TIME)

        super(TDLaunchNoHarmWindows, self).cleanup(return_status)

    def execute(self):

        tdvm = True
        key = 0

        self._log.info("Get all VM lists in the hyper v manager")
        self.get_vm_list()
        self._log.info("Remove all existing VMs")
        self.clean_all_vms()  # Shutdown and remove from hyperv and delete all related files.

        self._log.info("Starting guest {}.".format(key))
        key, vm_name = self.create_vm_name(key, legacy=False)
        ret_val = self.launch_tdx_vm_with_mtc_settings(key, vm_name,
                                                       tdvm,
                                                       self.is_vm_tdx_enabled,
                                                       self.enable_ethernet,
                                                       self.vm_reboot_timeout)
        if ret_val is False:
            raise content_exceptions.TestFail("Failed to launch TDVM")
        self._log.info("TDVM is alive after launching.")

        # shutdown VM
        self._log.info("Shutdown the VM in progress.")
        self.teardown_vm(vm_name, force=True)
        time.sleep(30)

        # change BIOS knob to non TDX settings.
        self._log.info("Disabling the TDX bios settings and reboot the SUT")
        self.set_knobs(self.tdx_only_bios_disable)
        # Give cooling time to complete OS booting.
        time.sleep(self.WINDOWS_OS_REBOOT_TIME)

        # attempt to restart VM, it shouldn't be launch
        try:
            self._log.info("Restarting the VM, it should fail.")
            self.start_vm(vm_name)
        except RuntimeError as e:
            self._log.info("Unable to launch the VM without TDX set value.")
            search_string = "'{}' failed".format(vm_name)
            if search_string in str(e):
                # test is passed
                return True
        # in case VM is start success, need to wait for boot time and check the status of the VM.
        time.sleep(self.vm_reboot_timeout)

        self._log.debug("If VM state is 'power off', it can be considered as the test pass")
        self._log.info("Verify  VM state. {}".format(vm_name))
        if self.verify_vm_state(vm_name, self._vm_provider.VM_STATE_STR):
            self._log.info("{} is running. TDX VM shouldn't run with TDX disabled".format(vm_name))
            return False

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDLaunchNoHarmWindows.main() else Framework.TEST_RESULT_FAIL)
