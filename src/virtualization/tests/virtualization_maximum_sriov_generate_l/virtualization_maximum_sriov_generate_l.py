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
import threading
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.lib.common_content_lib import CommonContentLib
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger


class VirtualizationMaximumSriovGenerateL(VirtualizationCommon):
    """
    Phoenix ID: 18014074390
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Install virt-install if not present.
    2. Copy CentOS ISO image to SUT under '/var/lib/libvirt/images'.
    4. Create VM.
    5. Verify VM is running.
    6. Configure SRIOV and attach VFs to Vm and verify ping test
    """
    TEST_CASE_ID = ["P18014074390", "PI_Virtualization_MaximumSR-IOVGenerate_L"]
    STEP_DATA_DICT = {
        1: {'step_details': "Check if SRIOV capable PCIe network device is present.",
            'expected_results': "ColumbiaVille Network device with SRIOV Function"},
        2: {'step_details': "Assign static IPs to all network devices in list",
            'expected_results': "Static IPs assigned successfully"},
        3: {'step_details': "Create the required Virtual Functions as per network device list",
            'expected_results': "Virtual Functions for network adapter successfully created"},
        4: {'step_details': "Get the VF adapter details",
            'expected_results': "Get the list of VF adapters created"},
        5: {'step_details': "Get and verify VF module details",
            'expected_results': "VF module details verified"},
        6: {'step_details': "Get the list of MACs for VFs",
            'expected_results': "list of MACs for VF created successfully"},
        7: {'step_details': "Assign MAC Id to all VFs",
            'expected_results': "MAC IDs assigned to VFs"},
        8: {'step_details': "Verify VF MAC ID details",
            'expected_results': "MAC IDs of VFs verified"},
        9: {'step_details': "Create the VM with VM name",
            'expected_results': "VM created and verified"},
        10: {'step_details': "Attach VF PCIe device to VM",
             'expected_results': "Virtual function adapter attached to VM"},
        11: {'step_details': "Verify the attached VFs in VMs",
             'expected_results': "Virtual function verified in VM"},
        12: {'step_details': "Get the VF adapter device name in VM",
             'expected_results': "Virtual function adapter name in VM obtained successfully"},
        13: {'step_details': "Assign Static IP to VF in VM",
             'expected_results': "Static IP assigned to VF adapter of VM"},
        14: {'step_details': "Execute the PING test from SUT to VM",
             'expected_results': "PING test passed"},
        15: {'step_details': "Execute the ssh connection from SUT to VM IP",
             'expected_results': "SSH test passed"},
        16: {'step_details': "Verify the SUT and VM if both are running and stable",
             'expected_results': "SUT and VMs are running fine"},
        17: {'step_details': "Detach the VFs from VMs",
             'expected_results': "VFs detached from VMs"},
        18: {'step_details': "Remove all Virtual Functions for network device list",
             'expected_results': "Virtual Functions for network adapter successfully removed"},
    }
    BIOS_CONFIG_FILE = "virtualization_maximum_sriov_generate_l.cfg"
    NUMBER_OF_VMS = 10
    VM = [VMs.CENTOS]*10
    STORAGE_VOLUME = ["/home"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationRHELConfigSRIOVVirtualFunctionVM object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationMaximumSriovGenerateL, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self.common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self._cfg_opt = cfg_opts
        self.test_log = test_log

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
        # Check the for the Linux OS in the SUT
        if self.os.os_type == OperatingSystems.LINUX:
            self._log.info("We have Linux OS for test case... proceeding further..")
        else:
            raise content_exceptions.TestFail("Target is not booted with Linux")

        super(VirtualizationMaximumSriovGenerateL, self).prepare()
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        self._vm_provider.create_bridge_network("virbr0")

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
        if not self.enable_intel_iommu_by_kernel():
            raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)
        self._test_content_logger.start_step_logger(1)
        network_device_name = self._common_content_configuration.get_columbiaville_nic_device_name()
        nw_device_list = self.get_sriovf_enabled_nw_adapters(network_device_name)
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        opt_dict = self.assign_static_ip_to_nw_adapters(nw_device_list)
        self._test_content_logger.end_step_logger(2, True)

        nw_adapter_name = nw_device_list[0]
        self._test_content_logger.start_step_logger(3)
        # create VF
        self.create_virtual_function(self.NUMBER_OF_VMS, nw_adapter_name)
        self._test_content_logger.end_step_logger(3, True)

        self._test_content_logger.start_step_logger(4)
        # get the VF adapter details
        vfs_data_list = self.get_vf_adapter_details()
        self._test_content_logger.end_step_logger(4, True)

        # VF module details
        self._test_content_logger.start_step_logger(5)
        self.get_and_verify_vf_module_details()
        self._test_content_logger.end_step_logger(5, True)

        # get VF mac ids & assign it
        self._test_content_logger.start_step_logger(6)
        vf_mac_id_details = self.get_vf_mac_details()
        self._test_content_logger.end_step_logger(6, True)

        self._test_content_logger.start_step_logger(7)
        mac_id_list = self.assign_macs_to_vfs(self.NUMBER_OF_VMS, vf_mac_id_details, nw_adapter_name)
        self._test_content_logger.end_step_logger(7, True)
        # MAC id details of VM list
        self._test_content_logger.start_step_logger(8)
        self.verify_vf_mac_details(mac_id_list)
        # VF module details
        self.get_and_verify_vf_module_details()
        self._test_content_logger.end_step_logger(8, True)
        vm_sut_obj_list = []
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" Creating VM:{} on RHEL.".format(vm_name))
            # create with default values
            # getting the ip & netmask of the VF
            self._test_content_logger.start_step_logger(9)
            ip, subnet = opt_dict[nw_device_list[0]]
            ip = ip[:-2] + str(int(ip[-2:]) + 5 + index)
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL, self.VM[index])
            self.create_vm_pool(vm_name, self.VM[index], mac_addr=True, pool_id=free_storage_pool)
            # self.create_vm_generic(vm_name, self.VM[index], vm_create_async=None, mac_addr=True,
            #                        pool_id=free_storage_pool, pool_vol_id=None,
            #						 cpu_core_list=None, nw_bridge="virbr0")
            self.create_vm_wait()
            self.verify_vm_functionality(vm_name, self.VM[index])
            self._test_content_logger.end_step_logger(9, True)
            # attaching the VF device to the VM
            self._test_content_logger.start_step_logger(10)
            self.attach_pci_nw_device_to_vm(vfs_data_list[index], vm_name)
            self._test_content_logger.end_step_logger(10, True)
            # create VM os object
            vm_os_obj = self.create_vm_host(vm_name, self.VM[index])
            vm_sut_obj_list.append(vm_os_obj)
            # verify VF in VM
            self._test_content_logger.start_step_logger(11)
            self.verify_vf_in_vm(vm_os_obj)
            self._test_content_logger.end_step_logger(11, True)
            # get vf adapter name in VM
            self._test_content_logger.start_step_logger(12)
            common_content_lib_vm_obj = CommonContentLib(self.test_log, vm_os_obj, self._cfg_opts)
            vf_adapter_name = self.get_vf_net_adapter_name_in_vm(common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(12, True)
            # assign the IP to the VM
            self._test_content_logger.start_step_logger(13)
            self.assign_ip_to_vf_in_vm(vm_os_obj, ip, subnet, vf_adapter_name, vm_name)
            self._test_content_logger.end_step_logger(13, True)

            # ping the ip from the SUT
            self._test_content_logger.start_step_logger(14)
            self._vm_provider.ping_vm_from_sut(ip)
            self._test_content_logger.end_step_logger(14, True)

            self._test_content_logger.start_step_logger(15)
            self._vm_provider.ssh_from_sut_to_ip(self.common_content_lib, ip, "root", "password")
            self._test_content_logger.end_step_logger(15, True)

        self._test_content_logger.start_step_logger(16)
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.verify_vm_functionality(vm_name, self.VM[index])
        self._test_content_logger.end_step_logger(16, True)
        self._test_content_logger.start_step_logger(17)
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            # detach the VF from the VM
            self.detach_pci_nw_device_from_vm(vfs_data_list[index], vm_name)
        self._test_content_logger.end_step_logger(17, True)
        # remove VF
        self._test_content_logger.start_step_logger(18)
        self.remove_virtual_function(nw_adapter_name)
        self._test_content_logger.end_step_logger(18, True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationMaximumSriovGenerateL, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationMaximumSriovGenerateL.main()
             else Framework.TEST_RESULT_FAIL)
