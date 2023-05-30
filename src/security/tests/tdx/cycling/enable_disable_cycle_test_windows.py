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
    :Enable-Disable Cycle TDX Test:

    Boot to OS with TDX VMM enabled and launch TD guest.  Disable TDX, reboot SUT, attempt to boot TDX guest. Repeat
    for prescribed number of cycles.
"""

import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.tdx_common_windows import WindowsTdxBaseTest


class TdxEnableDisableCycleTestWindows(WindowsTdxBaseTest):
    """
            This recipe tests TD guest boot and requires the use of a OS supporting TD guests.

            :Scenario: Boot to an OS with a TDX enabled VMM and launch a TD guest VM.  Disable TDX, reboot SUT, attempt
            to boot TDX guest. Repeat for given number of cycles.

            :Phoenix ID:  22014296905

            :Test steps:

                :1: Boot to an OS with a TDX enabled VMM.

                :2: Launch a TD guest VM.

                :3: Disable TDX and warm reset the SUT.

                :4: Attempt to boot a TD guest (this should fail).

                :5: Enable TDX.

                :6: Repeat steps 1-5 for given number of cycles.

            :Expected results: Each time after a warm reset, the SUT should boot to the OS.  Each time a TD guest is
            attempted to be launched with TDX enabled should be successful.  Each time a TD guest is attempted to be
            launched with TDX disabled should fail.

            :Reported and fixed bugs:

            :Test functions:

        """

    def execute(self):
        cycles = self.tdx_properties[self.tdx_consts.TDX_DISABLE_ENABLE_CYCLES]
        key = 0
        tdvm = True

        self._log.info("Get all VM lists in the hyper v manager")
        self.get_vm_list()
        self.clean_all_vms()
        key, vm_name = self.create_vm_name(key, legacy=False)

        for cycle_number in range(1, (cycles+1)):
            self._log.info("Iteration {} of {}.".format(cycle_number, cycles))
            self._log.info(f"Starting TD guest {vm_name}.")
            if cycle_number == 1:
                ret_val = self.launch_tdx_vm_with_mtc_settings(key, vm_name, tdvm, self.is_vm_tdx_enabled,
                                                               self.enable_ethernet, self.vm_reboot_timeout)
                if ret_val is False:
                    raise content_exceptions.TestFail("Failed to launch TDVM")
            else:
                self.start_vm(vm_name=vm_name)
                time.sleep(self.vm_reboot_timeout)

            # shutdown VM
            self._log.info("Shutdown/TurnOff the VM in progress.")
            self.teardown_vm(vm_name, force=True)

            # change BIOS knob to non TDX settings.
            self._log.info("Disabling TDX - {} of {}".format(cycle_number, cycles))
            self.set_knobs(self.tdx_only_bios_disable)

            # set_knobs cause rebooting the system. So make sure that all VMs are down.
            self.shutdown_all_vms()

            # attempt to restart VM, it shouldn't be launch
            try:
                self._log.info("Restarting the VM, it should fail.")
                self.start_vm(vm_name)
                time.sleep(5)  # buffer time
                if self.test_vm_folder_accessible(vm_name) is True:
                    raise content_exceptions.TestFail("TD guest could be launched with TDX disabled. Iteration "
                                                      "{} of {}.".format(cycle_number, cycles))
            except RuntimeError as e:
                self._log.info("Unable to launch the VM without TDX set value.")
                search_string = "'{}' failed to start".format(vm_name)
                if search_string in str(e):
                    self._log.info("Tdvm couldn't start without tdx settings")
                else:
                    raise content_exceptions.TestFail("TD guest could be launched with TDX disabled. Iteration "
                                                      "{} of {}.".format(cycle_number, cycles))

            self._log.info("Enabling TDX - {} of {}".format(cycle_number, cycles))
            self.set_knobs(self.tdx_bios_enable)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxEnableDisableCycleTestWindows.main() else Framework.TEST_RESULT_FAIL)
