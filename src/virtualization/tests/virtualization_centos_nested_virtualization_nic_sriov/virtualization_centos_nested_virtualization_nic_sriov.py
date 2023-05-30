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
import os
import threading
import time

from pathlib import Path
from shutil import copy
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.provider.vm_provider import VMProvider
from src.provider.vm_provider import VMs
from src.lib import content_exceptions
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.test_content_logger import TestContentLogger
from src.provider.vm_provider import VMs
from src.lib.install_collateral import InstallCollateral
from src.lib.common_content_lib import CommonContentLib
#from src.security.tests.dsa.dsa_common import DsaBaseTest

class VirtualizationCentOSNestedVirtualizationNicSRIOV(VirtualizationCommon):
    """
    Phoenix ID: P16014135631-VirtualizationCentOSNestedVirtualization
    The purpose of this test case is making sure the creation of VM in VM guests on KVM using Virt-Manager.
    1. Install virt-install if not present.
    2. Copy CENT OS Image to SUT under ./var/lib/libvirt/images'
    3. Create First level VM and verify if VM is running
    4. Copy RHEL ISO image to SUT under '/var/lib/libvirt/images'.
    5. Create Second level nested VM and verify if VM is running.
    6. Wait for 2 hours
    7. Verify if first level and second level VMs are running.
    8. Cleanup all VM resources
    """
    TEST_CASE_ID = ["P16014135670", "VirtualizationCentOSNestedVirtualizationNicSRIOV"]
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
        9: {'step_details': "Create the VM with VM name and attach VF to VM",
            'expected_results': "VM created and VF attached"},
        10: {'step_details': "Create the VM machine names.",
             'expected_results': "VM machine names created and saved in list"},
        11: {'step_details': "Verify VM functionality and assigning ip ",
             'expected_results': "VM functionality verified and ip assigned"},
        12: {'step_details': "Attach VF PCIe device to VM",
             'expected_results': "Virtual function adapter attached to VM"},
        13: {'step_details': "Verify the attached VFs in VMs",
             'expected_results': "Virtual function verified in VM"},
        14: {'step_details': "Get the VF adapter device name in VM",
             'expected_results': "Virtual function adapter name in VM obtained successfully"},
        15: {'step_details': "Assign Static IP to VF in VM",
             'expected_results': "Static IP assigned to VF adapter of VM"},
        16: {'step_details': "Execute the PING test from SUT to VM",
             'expected_results': "PING test passed"},
        17: {'step_details': "Execute the ssh connection from SUT to VM IP",
             'expected_results': "SSH test passed"},
        18: {'step_details': "Execute the iPerf test from SUT to VM's for few hours",
             'expected_results': "iPerf test passed"},
        19: {'step_details': "Create the Nested VM machine names.",
             'expected_results': "Nested VM machine names created and saved in list."},
        20: {'step_details': "Generate Nested Virtual machines on SUT.",
             'expected_results': "Nested Virtual machines created successfully."},
        21: {'step_details': "Wait for 2 hours.",
             'expected_results': "Waited for 2 hours successfully."},
        22: {'step_details': "Check the VM and nested VM.",
             'expected_results': "VM and nested chcked successfully and found stable."},
        23: {'step_details': "Destroy the VMs and nested VMs.",
             'expected_results': "VMs and nested VMs destroyed successfully."},
    }
    NUMBER_OF_VMS = 1
    VM = [VMs.CENTOS] * NUMBER_OF_VMS
    VM_TYPE = "CENTOS"
    VMN = [VMs.CENTOS] * NUMBER_OF_VMS
    VMN_TYPE = "CENTOS"
    TC_ID = ["P16014135631-VirtualizationCentOSNestedVirtualizationNicSRIOV"]
    BIOS_CONFIG_FILE = "virtualization_centos_nested_virtualization_bios_knobs.cfg"
    REPOS_FOLDER_PATH_SUT = "/etc/yum.repos.d"
    C_DRIVE_PATH = "C:\\"
    YUM_REPO_FILE_NAME = r"intel-yum-rhel.repo"
    REPOS_FOLDER_PATH_SUT = "/etc/yum.repos.d"
    ENABLE_YUM_REPO_COMMAND = "yum repolist all"
    TEST_TIME_SLEEP = 200
    STORAGE_VOLUME = ["/home"]
    IPERF_EXEC_TIME = 200
    EXEC_IPERF_INSTANCE = 1
    BASE_PORT = 5000
    IPERF_SERVER_CMD = "iperf3 -s -p {}"
    IPERF_CLIENT_CMD = "iperf3 -c {} -p {} -t {}"
    REGEX_FOR_DATA_LOSS = r".*sec.*0.00.*Bytes.*0.00.*bits.sec$"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationCentOSNestedVirtualization object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationCentOSNestedVirtualizationNicSRIOV, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        #self._grubby = DsaBaseTest(test_log, arguments, cfg_opts)
        self._cfg_opt_tc = cfg_opts
        self._arg_tc = arguments
        self._test_log_tc = test_log
        self._common_content_lib = CommonContentLib(self._log, self.os, self._cfg_opt_tc)
        self._cfg_opt = cfg_opts
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)

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
        if self.os.os_type == OperatingSystems.LINUX:
            self._log.info("We have Linux OS for test case... proceeding further..")
        else:
            raise content_exceptions.TestFail("Target is not booted with Linux")
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        self._vm_provider.create_bridge_network("virbr0")
        super(VirtualizationCentOSNestedVirtualizationNicSRIOV, self).prepare()

    def execute(self):
        """
        1. create VM
        2. create Nested VM
        3. check Nested VM is functioning or not
        4. check VM is functioning or not
        5. Wait for 2 hours and check if VMs are stable and running
        6. Destroy VM and Nested VM
        """
        self._install_collateral.screen_package_installation()
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)
        self.get_yum_repo_config(self.os, self._common_content_lib, os_type=self.VM_TYPE)

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

        self._test_content_logger.start_step_logger(9)
        vm_sut_obj_list = []
        self._test_content_logger.start_step_logger(10)
        mac_index = 0
        # extra_disk = 10 [iso file] + 7 [vm disk space]+ 7 [other for VM ]
        extra_disk = 56
        # for vm_name in self.LIST_OF_VM_NAMES:
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" Creating VM:{} on CENTOS.".format(vm_name))
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
            self.create_vm_pool_nested(vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True,
                                       pool_id=free_storage_pool, extra_disk_space=extra_disk)
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            self._log.info(" Created VM:{} on CENTOS.".format(vm_name))
            # create VM os object
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm_obj = CommonContentLib(self._test_log_tc, vm_os_obj, self._cfg_opt_tc)
            install_collateral_vm_obj = InstallCollateral(self._test_log_tc, vm_os_obj, self._cfg_opt_tc)
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj,os_type=self.VM_TYPE, machine_type="vm")
            install_collateral_vm_obj.screen_package_installation()
        self._test_content_logger.end_step_logger(10, True)
        # for index in range(self.NUMBER_OF_VMS):
        for index, vm_name in zip(range(len(self.LIST_OF_VM_NAMES)), self.LIST_OF_VM_NAMES):
            # create with default values
            # getting the ip & netmask of the VF
            self._test_content_logger.start_step_logger(11)
            ip, subnet = opt_dict[nw_device_list[0]]
            ip = ip[:-2] + str(int(ip[-2:]) + 5 + index)
            self.verify_vm_functionality(vm_name, self.VM[index])
            self._test_content_logger.end_step_logger(11, True)
            # attaching the VF device to the VM
            self._test_content_logger.start_step_logger(12)
            self.attach_pci_nw_device_to_vm(vfs_data_list[index], vm_name)
            self._test_content_logger.end_step_logger(12, True)
            # create VM os object
            vm_os_obj = self.create_vm_host(vm_name, self.VM[index])
            common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            vm_sut_obj_list.append(vm_os_obj)
            # verify VF in VM
            self._test_content_logger.start_step_logger(13)
            self.verify_vf_in_vm(vm_os_obj)
            self._test_content_logger.end_step_logger(13, True)
            # get vf adapter name in VM
            self._test_content_logger.start_step_logger(14)
            vf_adapter_name = self.get_vf_net_adapter_name_in_vm(common_content_lib_vm)
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
            self._vm_provider.ssh_from_sut_to_ip(self._common_content_lib, ip, "root", "password")
            self._test_content_logger.end_step_logger(17, True)
        self._test_content_logger.end_step_logger(9, True)

        self._test_content_logger.start_step_logger(18)
        self._log.info("Executing iperf test on SUT and VM's")
        self.collateral_installer.install_iperf_on_linux()
        server_thread_res = []
        client_thread_res = []
        vm_list = []
        for index in range(self.EXEC_IPERF_INSTANCE):
            vm_name = self.VM[index] + "_" + str(index)
            vm_os_obj = self.create_vm_host(vm_name, self.VM[index])
            common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opt)
            server_port_id = self.BASE_PORT + index
            install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opt)
            install_collateral_vm_obj.install_iperf_on_linux()
            server_ip = self.get_ip(self._common_content_lib)
            server_thread = threading.Thread(target=self.execute_sut_as_iperf_server,
                                             args=(self.IPERF_EXEC_TIME, server_port_id))
            client_thread = threading.Thread(target=self.execute_iperf_client,
                                             args=(self.IPERF_EXEC_TIME, server_port_id, server_ip,
                                                   common_content_lib_vm))
            server_thread.start()
            client_thread.start()
            vm_list.append(vm_name)
            server_thread_res.append(server_thread)
            client_thread_res.append(client_thread)
        time.sleep(self.IPERF_EXEC_TIME)
        for thread_sut, thread_vm in zip(server_thread_res, client_thread_res):
            thread_sut.join()
            thread_vm.join()
        self._test_content_logger.end_step_logger(18, True)
        self._test_content_logger.start_step_logger(17)
        if not self.os.is_alive():
            self._log.error("Linux SUT is not alive")
            return False
        self._test_content_logger.end_step_logger(17, True)

        self._test_content_logger.start_step_logger(19)
        virtualization_obj_vm_list = []
        for index, each_vm_obj in zip(range(len(self.LIST_OF_VM_NAMES)), vm_sut_obj_list):
            # vm_provider = VMProvider.factory(self._test_log_tc, self._cfg_opt_tc, each_vm_obj)
            virtualization_obj_vm = VirtualizationCommon(self._log, self._arg_tc, self._cfg_opt_tc, os_obj=each_vm_obj)
            virtualization_obj_vm._vm_provider.create_bridge_network("virbr0")
            virtualization_obj_vm_list.append(virtualization_obj_vm)
            for index_nested in range(self.NUMBER_OF_VMS):
                # Creates VM names dynamically according to the OS and its resources
                vm_name_nested = self.VMN[index_nested] + "_" + str(index) + "_" + str(index_nested)
                self.LIST_OF_NESTED_VM_NAMES.append(vm_name_nested)
                self._log.info(" NESTED VM:{} on CENTOS.".format(vm_name_nested))
            self._test_content_logger.end_step_logger(19, True)

            self._test_content_logger.start_step_logger(20)
            for vm_name_nested in self.LIST_OF_NESTED_VM_NAMES:
                # create with default values
                # free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                #                                                                   self.VMN_TYPE)
                # self._log.info("Pool with Storage {}".format(free_storage_pool))

                virtualization_obj_vm._vm_provider.destroy_vm(vm_name_nested)
                virtualization_obj_vm.create_vm_pool_nested(vm_name_nested, self.VMN_TYPE, vm_create_async=False,
                                                            mac_addr=True,
                                                            pool_id=None,
                                                            extra_disk_space=None,
                                                            nesting_level="l2")
                virtualization_obj_vm._vm_provider.check_if_vm_exist(vm_name_nested)

                vm_vm_os_obj = virtualization_obj_vm.create_vm_host_nested(vm_name_nested, self.VMN_TYPE, nesting_level="l2")
                common_content_lib_vm_vm_obj = CommonContentLib(self._test_log_tc, vm_vm_os_obj, self._cfg_opt_tc)
                install_collateral_vm_vm_obj = InstallCollateral(self._test_log_tc, vm_vm_os_obj, self._cfg_opt_tc)
                self.get_yum_repo_config(vm_vm_os_obj, common_content_lib_vm_vm_obj, os_type="centos",
                                         machine_type="vm")
                # virtualization_obj_vm.verify_vm_functionality(vm_name_nested, self.VMN_TYPE)
                self._log.info(" Created NESTED VM:{} on CENTOS.".format(vm_name_nested))
            self._test_content_logger.end_step_logger(20, True)

            # wait and check after 2 hours is all VMs are fine
            self._test_content_logger.start_step_logger(21)
            time.sleep(self.TEST_TIME_SLEEP)
            self._test_content_logger.end_step_logger(21, True)

            self._test_content_logger.start_step_logger(22)
            for index, vm_name_nest, virtualization_obj_vm in zip(range(len(self.LIST_OF_NESTED_VM_NAMES)),
                                                                  self.LIST_OF_NESTED_VM_NAMES, virtualization_obj_vm_list):
                # virtualization_obj_vm.verify_vm_functionality(vm_name_nested, self.VMN_TYPE)
                virtualization_obj_vm._vm_provider.check_if_vm_exist(vm_name_nest)

            for vm_name in self.LIST_OF_VM_NAMES:
                self.verify_vm_functionality(vm_name, self.VM_TYPE)
            self._test_content_logger.end_step_logger(22, True)

            self._test_content_logger.start_step_logger(23)
            for index, vm_name_nest, virtualization_obj_vm in zip(range(len(self.LIST_OF_NESTED_VM_NAMES)),
                                                                  self.LIST_OF_NESTED_VM_NAMES, virtualization_obj_vm_list):
                virtualization_obj_vm._vm_provider.destroy_vm(vm_name_nest)

            for vm_name in self.LIST_OF_VM_NAMES:
                self._vm_provider.destroy_vm(vm_name)
            self._test_content_logger.end_step_logger(23, True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationCentOSNestedVirtualizationNicSRIOV, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationCentOSNestedVirtualizationNicSRIOV.main()
             else Framework.TEST_RESULT_FAIL)
