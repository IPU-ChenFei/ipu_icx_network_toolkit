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
import re

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.content_exceptions import *
from src.lib.dtaf_content_constants import PcieSlotAttribute
from src.lib import content_exceptions
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon


class VirtualizationRhelKvmPcieGen4PassThroughConfiguration(VirtualizationCommon):
    """
    PHOENIX ID: 18014074524 - ["Virtualization_RHEL_KVM_PCIe_Gen_4.0_Pass_Through_Configuration"]
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Enable VT-d in BIOS Setup
    2. IOMMU enable successfully in Kernel
    4. Create VM.
    5. Verify VM is running.
    6. get the ethernet network port name
    7. get the BDF value of the Adapter
    8. attach port-0 of network adapter to VM
    9. check whether IP is assigned successfully or not
    10.detach the attached network adapter to VM
    """
    VM = [VMs.RHEL]
    BIOS_CONFIG_FILE = "virtualization_rhel_kvm_pcie_gen4_pass_through_configuration"
    REGEX_CMD_FOR_VERIFYING_VIRTUAL_ADAPTER = r".*Ethernet\scontroller.*810.*"
    STATIC_IP_FOR_VIRTUAL_ADAPTER = "20.20.20.2{}"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationRhelKvmPcieGen4PassThroughConfiguration object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raise: None
        """
        # calling base class init
        super(VirtualizationRhelKvmPcieGen4PassThroughConfiguration, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opt = cfg_opts
        if self.os.os_type != OperatingSystems.LINUX:
            raise TestNotImplementedError("This Test case is not supported on {} OS".format(self.os.os_type))

    def prepare(self):  # type: () -> None
        # Set & Verify BIOS knob
        # self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        if not self.enable_intel_iommu_by_kernel():
            raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")

    def execute(self):
        """
        1.get the columbiaville device name
        2.get the netowrk device list
        3.get the NW Adapter Details
        4.get the BDF value of network device
        5. create VM
        6. check VM is functioning or not
        7. attach the pcie device to VM
        8. create VM os object
        9. get the network adapter list
        10. assign static ip to attached adapters
        11. get the IP list for the all adapters
        12. check statically assigned ip whether that is available in read list
        13. detach the pcie device to VM
        """
        columbiaville_device_name = self._common_content_configuration.get_columbiaville_nic_device_name()
        self._log.info(columbiaville_device_name)

        nw_device_list = self.get_nw_adapter_details(columbiaville_device_name)

        nw_adapter_name = nw_device_list[0]

        bdf_value = self.get_bdf_values_of_nw_device(nw_adapter_name)
        self._log.info(bdf_value)

        for index in range(len(self.VM)):
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_vm(vm_name, self.VM[index], mac_addr=True)
            self.verify_vm_functionality(vm_name, self.VM[index])
            self._log.info("Copying the {} Test file to SUT".format(self.TEST_VM_FILE_NAME))
            self.attach_pci_nw_device_to_vm(nw_adapter_name, vm_name)
            self._log.info("Successfully attached the PCIe adapter to the VM".format(vm_name))
            vm_os_obj = self.create_vm_host(vm_name, self.VM[index])
            nw_adapter_name_list = self.get_nw_adapters_in_vm(vm_os_obj, columbiaville_device_name)
            network_interface_dict = self.assign_static_ip_to_nw_adapters_in_vm(vm_os_obj, nw_adapter_name_list)
            ip = network_interface_dict[nw_adapter_name_list[0]]
            ip_list = self.get_network_interface_ip_list_in_vm(vm_os_obj)
            if ip[0] not in ip_list:
                raise RuntimeError("IP Assign was failed for Network Adapter {}".format(nw_adapter_name_list[0]))
            self._log.info("Successfully read the assigned IP {} to Network Adapter {}".format(ip[0], nw_adapter_name_list[0]))
            self.detach_pci_nw_device_from_vm(nw_adapter_name, vm_name)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationRhelKvmPcieGen4PassThroughConfiguration, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationRhelKvmPcieGen4PassThroughConfiguration.main()
             else Framework.TEST_RESULT_FAIL)
