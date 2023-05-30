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
from src.lib import content_exceptions
from src.security.tests.tdx.tdx_common_windows import WindowsTdxBaseTest


class LegacyVMAndTDVMParallelWindows(WindowsTdxBaseTest):
    """
            This recipe tests TDVM boot and requires the use of a OS supporting TDVM.

            :Scenario: Levacy VM and TDVM has to work parallel

            :Phoenix IDs: 22013095866

            :Test steps:

                Launch a TDVM and legacy VM one after another.  Both has to be work paralle.

            :Expected results: TDVM and legacy VM has to launch and shutdown successfully.

            :Reported and fixed bugs:

            :Test functions:

        """
    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        """
        super(LegacyVMAndTDVMParallelWindows, self).__init__(test_log, arguments, cfg_opts)

    def execute(self):
        tdvm = True
        tdvm_key = 0
        legacy_vm_key = 1
        tdx_vm_shutdown_timeout = self.vm_reboot_timeout

        self._log.info("Get VM lists in the hyper v manager")
        self.get_vm_list()
        self._log.info("Remove all existing VMs")
        self.clean_all_vms()

        self._log.info("Create a TDVM and launch")
        tdvm_key, tdvm_name = self.create_vm_name(tdvm_key, legacy=False)
        ret_val = self.launch_tdx_vm_with_mtc_settings(tdvm_key, tdvm_name, tdvm, self.is_vm_tdx_enabled, self.enable_ethernet,
                                                       self.vm_reboot_timeout)
        if ret_val is False:
            raise content_exceptions.TestFail("Failed to launch TDVM")
        self._log.info("TDVM is alive after launching.")

        legacy_vm_key, legacy_vm_name = self.create_vm_name(legacy_vm_key, legacy=True)
        ret_val = self.launch_legacy_vm(legacy_vm_key, legacy_vm_name, False,
                                        self.enable_ethernet, self.vm_reboot_timeout)
        if ret_val is False:
            raise content_exceptions.TestFail("Failed to launch Legacy VM")
        self._log.info("Legacy VM is alive after launching.")

        # shutdown TDVM and Legacy VM
        for vm_name in [tdvm_name, legacy_vm_name]:
            self._log.info("Shutdown VM {}.".format(vm_name))
            self.teardown_vm(vm_name, timeout=tdx_vm_shutdown_timeout)
            self._log.info("waiting {} seconds".format(str(tdx_vm_shutdown_timeout)))
            time.sleep(tdx_vm_shutdown_timeout)

        self._log.info("Verify the VM is active or not")
        for vm_name in [tdvm_name, legacy_vm_name]:
            # test whether VM is active
            test_path = r'Test-Path -Path "c:\\Windows"'
            try:
                ret_val = self.run_powershell_command_in_vm(vm_name, test_path)
                if "True" in ret_val:
                    raise content_exceptions.TestFail("VM is accessible after shutdown")
            except RuntimeError as err:
                if "not in running state" not in str(err):
                    raise content_exceptions.TestFail("VM is accessible after shutdown")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LegacyVMAndTDVMParallelWindows.main() else Framework.TEST_RESULT_FAIL)
