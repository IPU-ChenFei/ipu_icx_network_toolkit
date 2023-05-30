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


class TDVMEnterExitWindows(WindowsTdxBaseTest):
    """
            This recipe tests TDVM boot and requires the use of a OS supporting TDVM.

            :Scenario: Pause and resume TDVM.

            :Phoenix IDs: 22012243236

            :Test steps:

                Launch a TDVM and verify the TDVM can be paused and resumed.

            :Expected results: TDVM be paused and resumed.

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
        super(TDVMEnterExitWindows, self).__init__(test_log, arguments, cfg_opts)
        self.BUFFER_TIME = 5

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

        self._log.info("VM is alive after launching.")
        self._log.info("Pausing VM {}.".format(vm_name))
        self.pause_vm(vm_name, self.BUFFER_TIME)
        time.sleep(self.BUFFER_TIME)

        # test whether VM is active
        try:
            ret_val = self.test_vm_folder_accessible(vm_name)
            if ret_val is True:
                raise content_exceptions.TestFail("VM could still be accessed while paused")
        except RuntimeError as err:
            if "not in running state" not in str(err):
                raise content_exceptions.TestFail("VM could still be accessed while paused")

        self._log.info("Resuming VM {}.".format(vm_name))
        self.resume_vm(vm_name)
        time.sleep(self.BUFFER_TIME)
        self._log.info("Verify  VM is running. {}".format(vm_name))
        ret_val = self.test_vm_folder_accessible(vm_name)
        if ret_val is True:
            self._log.info("VM is working after resume")
        else:
            raise content_exceptions.TestFail("VM is not accessible after resuming")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDVMEnterExitWindows.main() else Framework.TEST_RESULT_FAIL)
