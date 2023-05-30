#!/usr/bin/env python
#################################################################################
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
#################################################################################

import os
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon


class PIVirtualizationPassThroughNetworkL(VirtualizationCommon):
    """
    HPALM ID: 84452
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Install virt-install if not present.
    2. Copy RHEL ISO image to SUT under '/var/lib/libvirt/images'.
    4. Create VM.
    5. Verify VM is running.
    6. Do a ping operation from SUT.
    7. Do a network file copy from SUT to VM.
    """
    VM = [VMs.RHEL]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PIVirtualizationPassThroughNetworkL object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PIVirtualizationPassThroughNetworkL, self).__init__(test_log, arguments, cfg_opts)

    def execute(self):
        """
        1. create VM
        2. check VM is functioning or not
        """
        self._vm_provider.create_bridge_network("virbr0")
        for index in range(len(self.VM)):
            # create VM names dynamically according to the OS
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_vm(vm_name, self.VM[index], mac_addr=True)
            self.verify_vm_functionality(vm_name, self.VM[index])
            self._log.info("Copying the {} Test file to SUT".format(self.TEST_VM_FILE_NAME))
            complete_host_file_path = self._install_collateral.download_tool_to_host(self.TEST_VM_FILE_NAME)
            self.os.copy_local_file_to_sut(complete_host_file_path, self.ROOT_PATH)
            self._log.info("Successfully copied the {} Test File to SUT".format(self.TEST_VM_FILE_NAME))
            self.copy_file_from_sut_to_vm(vm_name, self.VM[index], self.ROOT_PATH + "/" + self.TEST_VM_FILE_NAME,
                                          self.ROOT_PATH + "/" + self.TEST_VM_FILE_NAME)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(PIVirtualizationPassThroughNetworkL, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PIVirtualizationPassThroughNetworkL.main()
             else Framework.TEST_RESULT_FAIL)
