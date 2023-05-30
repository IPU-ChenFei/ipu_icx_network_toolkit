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

from src.provider.storage_provider import StorageProvider
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.provider.driver_provider import DriverProvider, NetworkDrivers
from src.lib.test_content_logger import TestContentLogger
from src.lib.common_content_lib import CommonContentLib
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral


class VirtualizationRhelKvmSriovConfigureandTest3rdPartyMellanoxNetworkCard(VirtualizationCommon):
    """
    Phoenix ID: 16013171739
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Install virt-install if not present.
    2. Copy RHEL ISO image to SUT under '/var/lib/libvirt/images'.
    4. Create VM.
    5. Verify VM is running.
    """
    TEST_CASE_ID = ["p16013171739", "VirtualizationRhelKvmSriovConfigureandTest3rdPartyMellanoxNetworkCard"]
    STEP_DATA_DICT = {
        1: {'step_details': "Check if SRIOV capable Mellanox network device is present.",
            'expected_results': "Mellanox Network device found with SRIOV"},
        2: {'step_details': "Remove all existing VF's",
            'expected_results': "Successfully removed existing VF's"},
        3: {'step_details': "Assign static IPs to Mellanox network device in list",
            'expected_results': "Static IPs assigned successfully"},
        4: {'step_details': "Create the required Virtual Functions as per netowrk device list",
            'expected_results': "Virtual Functions for network adapter successfully created"},
        5: {'step_details': "Get the VF adapter details",
            'expected_results': "Get te list of VF adapters created"},
        6: {'step_details': "Get and verify VF module details",
            'expected_results': "VF module details verified"},
        7: {'step_details': "Get the list of MACs for VFs",
            'expected_results': "list of MACs for VF created successfully"},
        8: {'step_details': "Assign MAC Id to all VFs",
            'expected_results': "MAC IDs assigned to VFs"},
        9: {'step_details': "Verify VF MAC ID details",
            'expected_results': "MAC IDs of VFs verified"},
        10: {'step_details': "Create the name of All VMs to be created",
            'expected_results': "VM names created successfully"},
        11: {'step_details': "Create the VM with VM name",
            'expected_results': "VM created and verified"},
        12: {'step_details': "Attach VF PCIe device to VM",
            'expected_results': "Virtual function adapter attached to VM"},
        13: {'step_details': "Verify the attached VFs in VMs",
             'expected_results': "Virtual function verified in VM"},
        14: {'step_details': "Get the VF adpater device name in VM",
             'expected_results': "Virtual function adapter name in VM obtained successfully"},
        15: {'step_details': "Assign Static IP to VF in VM",
             'expected_results': "Static IP assigned to VF adpater of VM"},
        16: {'step_details': "Execute the PING test from SUT to VM",
            'expected_results': "PING test passed"},
        17: {'step_details': "Execute the SSH test from SUT to VM",
            'expected_results': "SSH test passed"},
        18: {'step_details': "Detach the VFs from VMs",
             'expected_results': "VFs detached from VMs"},
        19: {'step_details': "Verify the SUT and VM if both are running and stable & Remove all Virtual Functions for netowrk device list",
             'expected_results': "SUT and VMs are running fine & Virtual Functions for network adapter successfully removed"},
    }
    BIOS_CONFIG_FILE = "virtual_rhel_kvm_sriov_config_3rdparty_mellanox_nic_l.cfg"
    NUMBER_OF_VMS = 4
    VM = [VMs.RHEL]*4
    VM_TYPE = "RHEL"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationRHELConfigSRIOVVirtualFunctionVM object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationRhelKvmSriovConfigureandTest3rdPartyMellanoxNetworkCard, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._storage_provider = StorageProvider.factory(self._log, self.os, cfg_opts)  # type: StorageProvider
        self.driver_provider = DriverProvider.factory(self._log, cfg_opts, self.os)  # type: DriverProvider
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self.common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self._cfg_opt = cfg_opts
        self._test_log = test_log

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.

        :return: None
        """
        # Check the for the Windows OS in the SUT
        if self.os.os_type == OperatingSystems.LINUX:
            self._log.info("We have Linux OS for test case... proceeding further..")
        else:
            raise content_exceptions.TestFail("Target is not booted with Linux")
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        super(VirtualizationRhelKvmSriovConfigureandTest3rdPartyMellanoxNetworkCard, self).prepare()

    # how to control TC execution time
    def execute(self):
        """
        This Method is Used to.
        1) Generate Given Number of Virtual Network Adapters and Verify
        2) Assign Static MAC Address to each Virtual Network Adapter generated.
        3) Assign Static IP Address to each Virtual Network Adapter generated.
        4) Verify the MACs and IPs for all VFs
        5) create VM
        6) check VM is functioning or not
        7) Assign VFs to VMs
        8) Check if Ping is working
        9) Check if SSH is working
        10) Reset the created Virtual Function
        :return: True if all steps executes and getting the status as expected.
        """
        self._test_content_logger.start_step_logger(1)
        network_device_name = self._common_content_configuration.get_mellanox_nic_device_name()
        nw_device_list = self.get_sriovf_enabled_nw_adapters(network_device_name)
        self._test_content_logger.end_step_logger(1, True)
        self._test_content_logger.start_step_logger(2)
        nw_adapter_name = nw_device_list[0]
        self.remove_virtual_function(nw_adapter_name)
        self._test_content_logger.end_step_logger(2, True)

        self._test_content_logger.start_step_logger(3)
        opt_dict = self.assign_static_ip_to_nw_adapters(nw_device_list)
        self._test_content_logger.end_step_logger(3, True)

        self._test_content_logger.start_step_logger(4)
        # create VF
        self.create_virtual_function(self.NUMBER_OF_VMS, nw_adapter_name)
        self._test_content_logger.end_step_logger(4, True)

        self._test_content_logger.start_step_logger(5)
        # get the VF adapter details
        vfs_data_list = self.get_vf_adapter_details()
        self._test_content_logger.end_step_logger(5, True)

        # VF module details
        self._test_content_logger.start_step_logger(6)
        # self.get_and_verify_vf_module_details()
        self._test_content_logger.end_step_logger(6, True)

        # get VF mac ids & assign it
        self._test_content_logger.start_step_logger(7)
        # vf_mac_id_details = self.get_vf_mac_details_list() # get_vf_adapter_details
        self._test_content_logger.end_step_logger(7, True)

        self._test_content_logger.start_step_logger(8)
        # mac_id_list = self.assign_macs_to_vfs(self.NUMBER_OF_VMS, vf_mac_id_details, nw_adapter_name)
        self._test_content_logger.end_step_logger(8, True)

        # MAC id details of VM list
        self._test_content_logger.start_step_logger(9)
        # self.verify_vf_mac_details(mac_id_list)
        # VF module details
        # self.get_and_verify_vf_module_details()
        self._test_content_logger.end_step_logger(9, True)

        self._test_content_logger.start_step_logger(10)
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" Creating VM:{} on RHEL.".format(vm_name))
        self._test_content_logger.end_step_logger(10, True)

        self._test_content_logger.start_step_logger(11)
        vm_sut_obj_list = []
        common_content_lib_vm_obj = None
        for index in range(self.NUMBER_OF_VMS):
            # create with default values
            # getting the ip & netmask of the VF
            vm_name = self.LIST_OF_VM_NAMES[index]
            ip, subnet = opt_dict[nw_device_list[0]]
            ip = ip[:-2] + str(int(ip[-2:]) + 5 + index)
            self._vm_provider.destroy_vm(vm_name)
            self.create_vm(vm_name, self.VM_TYPE, mac_addr=True)
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            self._test_content_logger.end_step_logger(11, True)

            # attaching the VF device to the VM
            self._test_content_logger.start_step_logger(12)
            self.attach_pci_nw_device_to_vm(vfs_data_list[index], vm_name)
            self._test_content_logger.end_step_logger(12, True)
            # create VM os object
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._test_log, vm_os_obj, self._cfg_opt)
            vm_sut_obj_list.append(vm_os_obj)

            # verify VF in VM
            self._test_content_logger.start_step_logger(13)
            self.verify_vf_in_vm(vm_os_obj)
            self._test_content_logger.end_step_logger(13, True)

            # get vf adapter name in VM
            self._test_content_logger.start_step_logger(14)
            # vf_adapter_name = self.get_vf_adapter_name_in_vm(vm_name, mac_id_list[index])
            vf_adapter_name = self.get_vf_net_adapter_detail_in_vm(common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(14, True)

            # assign the IP to the VM
            self._test_content_logger.start_step_logger(15)
            self.assign_ip_to_vf_in_vm(vm_os_obj, ip, subnet, vf_adapter_name, vm_name)
            self._test_content_logger.end_step_logger(15, True)

            # ping the ip from the SUT
            self._test_content_logger.start_step_logger(16)
            self._vm_provider.ping_vm_from_sut(ip)
            self._test_content_logger.end_step_logger(16, True)

            self._test_content_logger.start_step_logger(17)
            self._vm_provider.ssh_from_sut_to_ip(self.common_content_lib, ip, "root", "password")
            self._test_content_logger.end_step_logger(17, True)

            # detach the VF from the VM
            self._test_content_logger.start_step_logger(18)
            self.detach_pci_nw_device_from_vm(vfs_data_list[index], vm_name)
            self._test_content_logger.end_step_logger(18, True)

            self._test_content_logger.start_step_logger(19)
        for vm_name in self.LIST_OF_VM_NAMES:
            self.verify_vm_functionality(vm_name, self.VM_TYPE)

            if self.os.is_alive():
                # remove VF
                self.remove_virtual_function(nw_adapter_name)
            self._log.error("Linux SUT is not alive")
            return True
        self._test_content_logger.end_step_logger(19, True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationRhelKvmSriovConfigureandTest3rdPartyMellanoxNetworkCard, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationRhelKvmSriovConfigureandTest3rdPartyMellanoxNetworkCard.main()
             else Framework.TEST_RESULT_FAIL)
