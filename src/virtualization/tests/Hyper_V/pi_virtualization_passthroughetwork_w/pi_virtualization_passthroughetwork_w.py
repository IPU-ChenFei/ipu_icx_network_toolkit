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
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon


class VirtualizationPassThroughNetwork(VirtualizationCommon):
    """
    HPALM ID: 79619
    Microsoft Hyper-V, codenamed Viridian, formerly known as Windows Server Virtualization, is a native hypervisor;
    it can create virtual machines on x86-64 systems running Windows.

    The purpose of this test case is making sure the creation of VMs guest on Hyper-V Hypervisor.
    1. Install Hyper-V module if not installed.
    2. Copy Windows ISO image to SUT under 'C:\VM_IMAGES'.
    3. Create VM.
    4. Verify VM if pinging from SUT.
    """
    TC_ID = ["H79619", "PI_Virtualization_PassThroughNetwork_W"]
    BIOS_CONFIG_FILE = "hyperv_passthroughnetwork_bios_knobs.cfg"
    NUMBER_OF_VMS = 1
    VM = [VMs.WINDOWS]
    VM_TYPE = "RS5"
    NETWORK_ASSIGNMENT_TYPE = "DDA"
    VSWITCH_NAME = "ExternalSwitch"
    ADAPTER_NAME = None

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationPassThroughNetwork object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: Test NotImplemented Error
        """
        # calling base class init
        self.bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(VirtualizationPassThroughNetwork, self).__init__(test_log, arguments, cfg_opts, self.bios_config_file)
        if self.os.os_type != OperatingSystems.WINDOWS:
            raise TestNotImplementedError("This Test case is not supported on {} OS".format(self.os.os_type))

    def prepare(self):  # type: () -> None
        """

        1. Enabling Bios knobs (VMX, VT-d)
        2. Install Hyper-v Module on SUT
        """
        super(VirtualizationPassThroughNetwork, self).prepare()
        self._vm_provider.install_vm_tool()

    def execute(self):
        """
        1. Create VM on Hyper-V
        2. Perform Network Passthrough by creating External Switch using Physical adapter
        """

        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            self._log.info("Creating VM on Hyper V")
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_hyperv_vm(vm_name, self.VM_TYPE)  # Create VM function
            self._vm_provider.wait_for_vm(vm_name) # Wait for VM to boot
            # Add Network Adapter to Vm using Direct Assignment
            self._vm_provider.add_vm_network_adapter(self.NETWORK_ASSIGNMENT_TYPE, vm_name, self.ADAPTER_NAME,
                                                     self.VSWITCH_NAME)
            # Performs Hyper-V Network passthrough test by pinging VM from SUT
            self._log.info("Performing Hyper-V VM passthrough Network test")
            self.verify_hyperv_vm(vm_name, self.VM_TYPE)
            self._log.info("Successfully verified Hyper-V Network Pass through on Virtual Machine")

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationPassThroughNetwork, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationPassThroughNetwork.main() else Framework.TEST_RESULT_FAIL)
