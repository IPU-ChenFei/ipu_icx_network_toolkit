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
    :MKTME-D Big TD Guest Test:

    With MKKME-D enabled, launch 1 large TD guest that has more cores than exist on 1 physical socket.
"""

import time
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.workloads.TDX049_launch_tdvm_mprime import TDGuestMprime


class MktmeDBigTdGuest(TDGuestMprime):
    """
            This recipe tests TD guest boot and requires the use of a OS supporting TD guests.  The zip file containing
            the new SEAM module must be saved locally on the lab host and the content_configuration.xml value <TDX>
            <LINUX><SEAM_MODULE_PATH_HOST> must be updated to the path the new SEAM module zip is located.  The new
            SEAM module must be a different version than what is currently installed in the OS or the test may return
            a false negative result.

            :Scenario: Enable Directory Mode and launch 1 large TD guests with more cores assigned than exist on a
            physical socket.  Run workload on TD guest and verify there are no MCEs.

            :Phoenix ID: https://hsdes.intel.com/appstore/article/#/22012591793

            :Test steps:

                :1:  Enable Directory Mode.

                :2:  Get number of cores available on each physical socket.

                :3:  Create and launch a TD guest which has more cores assigned than exist on either single
                physical socket.

                :4:  Run mprime on TD guest.

            :Expected results: TD guest should boot and should not yield MCEs.

            :Reported and fixed bugs:

            :Test functions:

        """

    def prepare(self):
        if self.get_sockets() < 2:
            raise content_exceptions.TestSetupError("System does not have enough sockets for the test.  This test "
                                                    "requires at least two sockets on the system.")

        self.tdx_properties[self.tdx_consts.DIRECTORY_MODE] = True  # directory mode must be enabled
        super(MktmeDBigTdGuest, self).prepare()
        self._log.info("Checking taskset is installed on SUT.")
        self.install_collateral.yum_install("util-linux")

    def execute(self):
        key = 0

        # get number of cores on socket
        cores = self.get_cores()
        num_sockets = self.get_sockets()
        cores = int(cores / num_sockets) + 10
        # creating large VM, overriding config vm core count
        self.tdx_properties[self.tdx_consts.TD_GUEST_CORES] = str(cores)
        self.launch_vm(key=key, tdvm=True)
        if not self.vm_is_alive(key=key):
            raise content_exceptions.TestFail("VM {}failed to boot.".format(key))
        # launch mprime on vms
        self._log.info("Setting up mprime.")
        self.set_up_tool(idx=key)
        self._log.info("Launching {} suite on VM {}.".format(self._tool_name, key))
        log_file_name = "{}/tdvm-{}-{}.txt".format(self._tool_sut_folder_path, self._tool_name, key)
        cmd = self._tool_sut_folder_path + "/" + self._tool_run_cmd.format(
            self._tool_run_time) + log_file_name
        self.ssh_to_vm(key=key, cmd=cmd, async_cmd=True)
        self.check_process_running(key=key, process_name=self._tool_name)
        self._log.info(f"Mprime is running on the big TD guest for {self._tool_run_time} seconds.")
        time.sleep(self._tool_run_time)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MktmeDBigTdGuest.main() else Framework.TEST_RESULT_FAIL)
