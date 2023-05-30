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
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.mktme.mktme_common_windows import WindowsMktmeBase


class MktmeMulitVMStressWindows(WindowsMktmeBase):
    """
        Phoenix id: 18014070342

        This test is targeting to
        - Launch multiple VMs in MKTME enabled host machine
        - Encrypt the VM memory
        - Run for few minutes
        - Shutdown
    """
    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        """
        super(MktmeMulitVMStressWindows, self).__init__(test_log, arguments, cfg_opts)
        self.BUFFER_TIME = 5

    def prepare(self):
        self.clean_all_vms_from_hyper_v()
        super(MktmeMulitVMStressWindows, self).prepare()

    def execute(self):
        legacy = False
        enable_ethernet = True
        num_of_vms = 3

        # launch multiple VMs
        for key_index in range(num_of_vms):
            key, vm_name = self.create_vm_name(key_index, legacy)
            self.launch_vm(key, vm_name, legacy, enable_ethernet)
            self._log.info("VM is alive after launching.")

            # applying memory encryption to VM
            self._log.info("applying memory encryption settings on VM {}".format(vm_name))
            ret_val = self.apply_memory_encryption_on_vm(vm_name, self.vm_reboot_timeout)
            if not ret_val:
                raise content_exceptions.TestFail("Memory encryption is not applied to the VM")
            self._log.info("Verify  VM is running. {}".format(vm_name))
            ret_val = self.test_vm_folder_accessible(vm_name)
            if ret_val is True:
                self._log.info("VM is accessible")
            else:
                raise content_exceptions.TestFail("VM is not accessible after applying memory encryption")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MktmeMulitVMStressWindows.main() else Framework.TEST_RESULT_FAIL)
