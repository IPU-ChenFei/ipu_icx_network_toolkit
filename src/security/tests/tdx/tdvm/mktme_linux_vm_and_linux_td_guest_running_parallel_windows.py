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
    :TDX Linux TDVM and MKTME enabled Linux TDVM can work parallel:

    Verify MKTME Linux VM and  Linux TDVM can run parallel in a single host.
"""

import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.tdx_common_windows import WindowsTdxBaseTest


class LinuxMKTMEAndTDVMParallelWindows(WindowsTdxBaseTest):
    """This recipe tests TDVM boot and requires the use of a OS supporting TDVM.

            :Scenario: MKTME Linux VM and Linux TDVM has to work parallel

            :Phoenix IDs: 14015392550

            :Test steps:

                Launch a Linux TDVM and MKTME Linux VM one after another.  Both has to be work parallel.

            :Expected results: Linux TDVM and MKTME Linux VM has to launch and shutdown successfully.

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
        super(LinuxMKTMEAndTDVMParallelWindows, self).__init__(test_log, arguments, cfg_opts)
        self.IDLE_TIME = int(arguments.VM_PARALLEL_EXEC_TIME)

    @classmethod
    def add_arguments(cls, parser):
        """
        :param parser: argument parser
        :return: None
        """
        super(LinuxMKTMEAndTDVMParallelWindows, cls).add_arguments(parser)
        parser.add_argument("-t", "--VM_PARALLEL_EXEC_TIME", action="store", dest="VM_PARALLEL_EXEC_TIME", default="120")

    def execute(self):
        tdx_vm_shutdown_timeout = self.vm_reboot_timeout
        self._log.info("Get all VM lists in the hyper v manager")
        self.get_vm_list()
        self.clean_all_vms()
        self.clean_linux_vm_tdx_apps()

        # launch td guest
        tdvm_key = 0
        self._log.info("Create a Linux TDVM and launch")
        tdvm_key, tdvm_name = self.create_vm_name(tdvm_key, legacy=False, vm_os="LINUX")
        self.launch_ubuntu_td_guest(tdvm_key, tdvm_name)
        self._log.info("Linux TDVM VM-1 is alive after launching.")

        # launch the mktme vm(Windows OS)
        mktme_vm_key = tdvm_key + 1
        mktme_vm_key, mktme_vm_name = self.create_vm_name(mktme_vm_key, legacy=True)
        mktme_vm_name = mktme_vm_name.replace("LEGACY", "MKTME")
        self.launch_mktme_guest(mktme_vm_key, mktme_vm_name)
        self._log.info("MKTME VM is alive after launching.")

        # let both of the vms to run some time.
        self._log.info(f"Waiting {self.IDLE_TIME} seconds to run both VMs")
        time.sleep(self.IDLE_TIME)

        # shutdown TDVM and MKTME VM
        for vm_name in [tdvm_name, mktme_vm_name]:
            self._log.info(f"Shutdown VM {vm_name}.")
            self.teardown_vm(vm_name, timeout=tdx_vm_shutdown_timeout)
            self._log.info(f"Waiting {tdx_vm_shutdown_timeout} seconds")
            time.sleep(tdx_vm_shutdown_timeout)

        return True

    def cleanup(self, return_status):
        """DTAF cleanup"""
        self.clean_linux_vm_tdx_apps()
        super(LinuxMKTMEAndTDVMParallelWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LinuxMKTMEAndTDVMParallelWindows.main() else Framework.TEST_RESULT_FAIL)
