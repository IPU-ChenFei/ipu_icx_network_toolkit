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

    Verify TDVM can be created on top of TDX capable VMM with multi virtual processors

"""

import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.tdx_common_windows import WindowsTdxBaseTest


class TDVMMultiVirtualProcessorsWindows(WindowsTdxBaseTest):
    """
            This recipe tests TDVM boot and requires the use of a OS supporting TDVM.

            :Scenario: Launch TDVM with 2 and 4 virtual processors

            :Phoenix IDs: 22015400245

            :Test steps:

                Launch a TDVM and verify the TDVM can be launch and shutdown with 2 & 4 virtual processors.

            :Expected results: TDVM be launch and shutdown.

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
        super(TDVMMultiVirtualProcessorsWindows, self).__init__(test_log, arguments, cfg_opts)
        vir_proc_counts = arguments.VIRT_PROC_COUNT.strip()
        self.VIRT_PROC_COUNTS = vir_proc_counts.split(",")

    @classmethod
    def add_arguments(cls, parser):
        """
        :param parser: argument parser
        :return: None
        """
        super(TDVMMultiVirtualProcessorsWindows, cls).add_arguments(parser)
        # Run the script with argument -vp <diff virtual processor counts separated by ',' > eg: -vp 4,8
        parser.add_argument("-vp", "--VIRT_PROC_COUNT", type=str, action="store", dest="VIRT_PROC_COUNT", default="2,4")

    def execute(self):
        """
            1. Launch TDX VM guest
            2. Change the virtual processor count to different
            3. Relaunch TDX VM
            4. Repeat this process for all input virtual process counts
        """
        tdx_vm_shutdown_timeout = self.vm_reboot_timeout
        tdvm = True
        key = 0

        self._log.info("Get VM lists in the hyper v manager")
        self.get_vm_list()
        self.clean_all_vms()

        # launch the tdvm VM
        self._log.info("Create a TDVM and launch")
        key, vm_name = self.create_vm_name(key, legacy=False)
        ret_val = self.launch_tdx_vm_with_mtc_settings(key,
                                                       vm_name,
                                                       tdvm,
                                                       self.is_vm_tdx_enabled,
                                                       self.enable_ethernet,
                                                       self.vm_reboot_timeout)
        if ret_val is False:
            raise content_exceptions.TestFail("Failed to launch TDVM")
        self._log.info("TDVM is alive after launching.")

        for virtual_proc_count in self.VIRT_PROC_COUNTS:
            # shutdown VM.
            self._log.info("Shutdown VM: {}.".format(vm_name))
            self.teardown_vm(vm_name, timeout=tdx_vm_shutdown_timeout)
            self._log.info("waiting {} seconds".format(str(tdx_vm_shutdown_timeout)))
            time.sleep(tdx_vm_shutdown_timeout)
            # apply new virtual processor count on vm image
            self.apply_virtual_processors_to_vm_image(vm_name, virtual_proc_count)

            # Start-VM
            self.start_vm(vm_name)

            # wait for some time to boot the vm.
            self._log.info("waiting {} seconds".format(str(self.vm_reboot_timeout)))
            time.sleep(self.vm_reboot_timeout)

            self._log.info("Verify the VM is active or not")
            ret_val = self.test_vm_folder_accessible(vm_name)
            if ret_val is False:
                raise content_exceptions.TestFail(f"VM is not accessible with virtual processor count {virtual_proc_count}")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDVMMultiVirtualProcessorsWindows.main() else Framework.TEST_RESULT_FAIL)
