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
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon

from src.lib.content_exceptions import TestNotImplementedError
from src.lib.test_content_logger import TestContentLogger

class VirtualizationPCIePassThroughNetwork(VirtualizationCommon):
    """
    Pheonix ID: 16013375657
    Microsoft Hyper-V, codenamed Viridian, formerly known as Windows Server Virtualization, is a native hypervisor;
    it can create virtual machines on x86-64 systems running Windows.

    The purpose of this test case is making sure the creation of VMs guest on Hyper-V Hypervisor.
    1. Install Hyper-V module if not installed.
    2. Copy Windows ISO image to SUT under 'C:\VM_IMAGES'.
    3. Create VM.
    4. Verify VM if pinging from SUT.
    """
    TC_ID = ["16013375657", "Virtualization_PCIe_Gen_5.0_PassThroughNetwork_W"]
    STEP_DATA_DICT = {
        1: {'step_details': "Enabling Bios knobs (VMX, VT-d)",
            'expected_results': "BIOS knobs set as per knobs file and verified."},
        2: {'step_details': "Install Hyper-v Module on SUT",
            'expected_results': "Hyper-V module created successfully on SUT"},
        3: {'step_details': "Creates VM names dynamically according to the OS and its resources",
            'expected_results': "VM names on Hyper-V created successfully"},
        4: {'step_details': "Add Network Adapter to Vm using Direct Assignment",
            'expected_results': "Network adapter has been added"},
        5: {'step_details': "Perform Network Passthrough for Gen5.0 by creating External Switch using Physical adapter"
                            "by pinging VM",
            'expected_results': "Passthrough for Gen5.0 has been verified successfully"},
    }
    BIOS_CONFIG_FILE = "hyperv_gen5.0_passthroughnetwork_bios_knobs.cfg"
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
        super(VirtualizationPCIePassThroughNetwork, self).__init__(test_log, arguments, cfg_opts, self.bios_config_file)
        self._test_content_logger = TestContentLogger(self._log, self.TC_ID, self.STEP_DATA_DICT)
        if self.os.os_type != OperatingSystems.WINDOWS:
            raise TestNotImplementedError("This Test case is not supported on {} OS".format(self.os.os_type))

    def prepare(self):  # type: () -> None
        """
        1. Enabling Bios knobs (VMX, VT-d)
        2. Install Hyper-v Module on SUT
        """
        self._test_content_logger.start_step_logger(1)
        super(VirtualizationPCIePassThroughNetwork, self).prepare() #enable the bios knobs
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        self._vm_provider.install_vm_tool()
        self._test_content_logger.end_step_logger(2, True)

    def execute(self):
        """
        3. Create VM on Hyper-V
        4. Perform Network Passthrough for Gen5.0 by creating External Switch using Physical adapter by pinging VM
        """
        self.ADAPTER_NAME = self._vm_provider._get_vm_network_adapter_pci_card()
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            self._test_content_logger.start_step_logger(3)
            self._log.info("Creating VM on Hyper V")
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_hyperv_vm(vm_name, self.VM_TYPE)  # Create VM function
            self._vm_provider.wait_for_vm(vm_name) # Wait for VM to boot
            time.sleep(20)
            self._test_content_logger.end_step_logger(3, True)

            # Add Network Adapter to Vm using Direct Assignment
            self._test_content_logger.start_step_logger(4)
            self._vm_provider.add_vm_network_adapter(self.NETWORK_ASSIGNMENT_TYPE, vm_name, self.ADAPTER_NAME,
                                                     self.VSWITCH_NAME)
            self._test_content_logger.end_step_logger(4, True)

            # Performs Hyper-V Network passthrough for Gen5.0 card test by pinging VM from SUT
            self._test_content_logger.start_step_logger(5)
            self._log.info("Performing Hyper-V VM passthrough Network test")
            self.verify_hyperv_vm(vm_name, self.VM_TYPE)
            self._log.info("Successfully verified Hyper-V Network Pass through on Virtual Machine")
            self._test_content_logger.end_step_logger(5, True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationPCIePassThroughNetwork, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationPCIePassThroughNetwork.main() else Framework.TEST_RESULT_FAIL)
