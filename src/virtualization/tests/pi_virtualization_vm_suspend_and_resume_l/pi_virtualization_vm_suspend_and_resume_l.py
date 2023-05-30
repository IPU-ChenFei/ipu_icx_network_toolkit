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
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon


class PiVirtualizationVMSuspendAndResumeL(VirtualizationCommon):
    """
    HPALM ID: H79626-PI_Virtualization_VM_Suspend_and_Resume_L
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Install virt-install if not present.
    2. Copy RHEL ISO image to SUT under '/var/lib/libvirt/images'.
    4. Create VM.
    5. Verify VM is running.
    6. Suspend the VM.
    7. Resume the VM.
    """
    TC_ID = ["H79626-PI_Virtualization_VM_Suspend_and_Resume_L"]
    VM = [VMs.RHEL]
    BIOS_CONFIG_FILE = "pi_virtualization_vm_suspend_and_resume_l_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiVirtualizationVMSuspendAndResumeL object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiVirtualizationVMSuspendAndResumeL, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))

    def prepare(self):  # type: () -> None
        self.bios_util.set_bios_knob(self.BIOS_CONFIG_FILE)
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        self.bios_util.verify_bios_knob(self.BIOS_CONFIG_FILE)

    def execute(self):
        """
        1. create VM
        2. check VM is functioning or not
        """
        for index in range(len(self.VM)):
            # create VM names dynamically according to the OS
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_vm(vm_name, self.VM[index], mac_addr=True)
            self.verify_vm_functionality(vm_name, self.VM[index])
            vm_ip = self._vm_provider.get_vm_ip(vm_name)
            self._vm_provider.suspend_vm(vm_name)
            ping_status = self.ping_vm_from_host(vm_ip)
            if ping_status:
                raise TestFail("{} VM is not suspended".format(vm_name))
            self._vm_provider.resume_vm(vm_name)
            ping_status = self.ping_vm_from_host(vm_ip)
            if not ping_status:
                raise TestFail("{} VM is not resumed".format(vm_name))
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(PiVirtualizationVMSuspendAndResumeL, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiVirtualizationVMSuspendAndResumeL.main()
             else Framework.TEST_RESULT_FAIL)
