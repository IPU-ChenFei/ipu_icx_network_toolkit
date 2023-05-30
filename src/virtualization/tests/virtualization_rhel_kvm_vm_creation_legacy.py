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

import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon


class VirtualizationRHELKvmVmCreation(VirtualizationCommon):
    """
    Phoenix ID: 18014072902
    HPALM ID: 80292
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Install virt-install if not present.
    2. Copy RHEL ISO image to SUT under '/var/lib/libvirt/images'.
    4. Create VM.
    5. Verify VM is running.
    """
    VM = [VMs.RHEL]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationRHELKvmVmCreation object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationRHELKvmVmCreation, self).__init__(test_log, arguments, cfg_opts)

    def execute(self):
        """
        1. create VM
        2. check VM is functioning or not
        """
        for index in range(len(self.VM)):
            # create VM names dynamically according to the OS
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_vm(vm_name, self.VM[index],mac_addr=True)
            self.verify_vm_functionality(vm_name, self.VM[index])
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationRHELKvmVmCreation, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationRHELKvmVmCreation.main()
             else Framework.TEST_RESULT_FAIL)
