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
    :TDX TDVM and MKTME enabled TDVM can work parallel:

    Verify MKTME and TDVM can run parallel in a single host.
"""

import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.tdx_common_windows import WindowsTdxBaseTest


class MKTMEVMAndTDVMParallelWindows(WindowsTdxBaseTest):
    """This recipe tests TDVM boot and requires the use of a OS supporting TDVM.

            :Scenario: MKTME VM and TDVM has to work parallel

            :Phoenix IDs: 18014073776

            :Test steps:

                Launch a TDVM and MKTME VM one after another.  Both has to be work parallel.

            :Expected results: TDVM and MKTME VM has to launch and shutdown successfully.

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
        super(MKTMEVMAndTDVMParallelWindows, self).__init__(test_log, arguments, cfg_opts)
        self.IDLE_TIME = int(arguments.VM_PARALLEL_EXEC_TIME)

    @classmethod
    def add_arguments(cls, parser):
        """
        :param parser: argument parser
        :return: None
        """
        super(MKTMEVMAndTDVMParallelWindows, cls).add_arguments(parser)
        parser.add_argument("-t", "--VM_PARALLEL_EXEC_TIME", action="store", dest="VM_PARALLEL_EXEC_TIME", default="120")

    def execute(self):
        tdx_vm_shutdown_timeout = self.vm_reboot_timeout
        self._log.info("Get all VM lists in the hyper v manager")
        self.get_vm_list()
        self.clean_all_vms()

        # launch td guest
        td_key = 0
        td_key, tdvm_name = self.create_vm_name(td_key, legacy=False)
        self.launch_td_guest(td_key, tdvm_name)

        # launch mktme guest
        mktme_key = td_key + 1
        mktme_key, mktme_name = self.create_vm_name(mktme_key, legacy=True)
        mktme_name = mktme_name.replace("LEGACY", "MKTME")
        self.launch_mktme_guest(mktme_key, mktme_name)

        # let both of the vms to run some time.
        self._log.info(f"Waiting {self.IDLE_TIME} seconds to run both VMs")
        time.sleep(self.IDLE_TIME)

        # shutdown TDVM and MKTME VM
        for vm_name in [tdvm_name, mktme_name]:
            self._log.info(f"Shutdown VM {vm_name}")
            self.teardown_vm(vm_name, timeout=tdx_vm_shutdown_timeout)
            self._log.info(f"Waiting {tdx_vm_shutdown_timeout} seconds")
            time.sleep(tdx_vm_shutdown_timeout)

        self._log.info("Verify the VM is active or not")
        for vm_name in [tdvm_name, mktme_name]:
            # test whether VM is active
            ret_val = self.test_vm_folder_accessible(vm_name)
            if ret_val is True:
                raise content_exceptions.TestFail("VM could still be accessed while shutdown")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MKTMEVMAndTDVMParallelWindows.main() else Framework.TEST_RESULT_FAIL)
