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

from src.provider.vm_provider import VMs
from src.lib import content_exceptions
from src.virtualization.virtualization_common import VirtualizationCommon


class PIVirtualizationPassThroughNetworkL(VirtualizationCommon):
    """
    HPALM ID: 79622 - PI_Virtualization_PassThroughNetwork_L

    The purpose of this test case is making sure the Pass Through Network is working on VM.
    1. Enable VT-d in BIOS.
    2. enable intel_iommu.
    3. create VM
    4. check VM is functioning or not
    5. Add the PCI Ethernet Controller to the VM.
    6. Check if the VM is accessible with the pass-through Network.
    """
    VM = [VMs.RHEL]
    BIOS_CONFIG_FILE = "pi_virtualization_passthroughnetwork_bios_knobs.cfg"
    TESTCASE_ID = ["H79622", "PI_Virtualization_Passthroughnetwork_L"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PIVirtualizationPassThroughNetworkL object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: content_exceptions.TestNotImplementedError
        """
        # calling base class init
        super(PIVirtualizationPassThroughNetworkL, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))

    def prepare(self):  # type: () -> None
        """
        This prepare method is going to set and verify BIOS knob and check for the iommu by kernel if it enabled or not
        :return: None
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        self.set_and_verify_bios_knobs(bios_config_file)
        # enable intel_iommu by kernel if not enabled
        if not self.enable_intel_iommu_by_kernel():
            raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")

    def execute(self):
        """
        1. create VM
        2. check VM is functioning or not
        3. Add the PCI Ethernet Controller to the VM.
        4. Check if the VM is accessible with the pass-through Network.
        """
        for index in range(len(self.VM)):
            # create VM names dynamically according to the OS
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_vm(vm_name, self.VM[index], mac_addr=True)
            self.verify_vm_functionality(vm_name, self.VM[index])
            network_device_name = self._common_content_lib.execute_sut_cmd("lshw | grep Ethernet", "Ethernet",
                                                                           self._command_timeout).strip().split("\n") \
                                                                            [1].split(":")[1].strip()
            nw_device_list = self.get_nw_adapter_details(network_device_name)
            nw_adapter_name = nw_device_list[0]
            self.attach_pci_nw_device_to_vm(nw_adapter_name, vm_name)
            self._log.info("Successfully attached the PCIe adapter to the VM".format(vm_name))
            vm_os_obj = self.create_vm_host(vm_name, self.VM[index])
            nw_adapter_name_list = self.get_nw_adapters_in_vm(vm_os_obj, network_device_name)
            network_interface_dict = self.assign_static_ip_to_nw_adapters_in_vm(vm_os_obj, nw_adapter_name_list)
            ip = network_interface_dict[nw_adapter_name_list[0]]
            ip_list = self.get_network_interface_ip_list_in_vm(vm_os_obj)
            if ip[0] not in ip_list:
                raise RuntimeError("IP Assign was failed for Network Adapter {}".format(nw_adapter_name_list[0]))
            self._log.info("Successfully read the assigned IP {} to Network Adapter {}".format(ip[0],
                                                                                               nw_adapter_name_list[0]))
            self.detach_pci_nw_device_from_vm(nw_adapter_name, vm_name)
            bdf_value = self.get_bdf_values_of_nw_device(nw_adapter_name)
            self._log.info(bdf_value)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        This method is used to clean and destroy the VM
        :return: None
        """
        super(PIVirtualizationPassThroughNetworkL, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PIVirtualizationPassThroughNetworkL.main() else Framework.TEST_RESULT_FAIL)

