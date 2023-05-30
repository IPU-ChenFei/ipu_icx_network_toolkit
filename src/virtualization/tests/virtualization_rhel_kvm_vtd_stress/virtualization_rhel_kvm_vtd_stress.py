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
import time
import os
import threading

from src.provider.storage_provider import StorageProvider
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.provider.driver_provider import DriverProvider, NetworkDrivers
from src.lib.test_content_logger import TestContentLogger
from src.lib.common_content_lib import CommonContentLib
from src.provider.vm_provider import VMs
from pathlib import Path
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import TimeConstants
from src.provider.stressapp_provider import StressAppTestProvider


class VirtualizationRHELVTdVMStress(VirtualizationCommon):
    """
    Phoenix ID: 16012980172
    The purpose of this test VTD stress – IOTLB stress, VTD BAR stress from the OS level use cases.
    VM boot cycling - 48 hours. 1 VM on every 2 logical core. Boot cycling the VM.
    1. SRIOV NIC iperf for 6VMs,4 VMs are assigned with VFs, 2 VMs are assigned with PFs
    2. Run FIO stress on 4 VMs.
    3.CPU and Memory stress on 8VMs using burnin tool
    4. VM cycling on 12 VMs.
    """
    TEST_CASE_ID = ["p16012980172", "VirtualizationRHELVTdVMStress"]
    STEP_DATA_DICT = {
        1: {'step_details': "SRIOV NIC iperf for 6VMs,4 VMs are assigned with VFs, 2 VMs are assigned with PFs",
            'expected_results': "Should be successfull"},
        2: {'step_details': "Run FIO stress on 4 VMs",
            'expected_results': "Should be successfully"},
        3: {'step_details': "CPU and Memory stress on 8VMs using burnin tool",
            'expected_results': "Should be successfully "},
        4: {'step_details': "VM cycling on 12 VMs",
            'expected_results': "Should be successful"},
    }

    # NUMBER_OF_VMS_TOTAL = 32
    # stressapp_provider_obj_list=[]
    # NUMBER_OF_VMS_CYCLING = 12
    # NUMBER_OF_VMS_PFS = 2
    # NUMBER_OF_VMS_VFS = 4
    # NUMBER_OF_VMS_IPERF = 6

    BASE_PORT = 5000
    NUMBER_OF_VMS = 4  # 1, tested with 1
    VM = [VMs.RHEL] * 4  # 1, tested with 1
    VM_TYPE = "RHEL"
    BURNING_80_WORKLOAD_CONFIG_FILE = "cmdline_config_80_workload.txt"
    BIT_TIMEOUT = 1  # 120 in minutes
    SUT_BIT_LOCATION = None
    WAITING_TIME_IN_SEC = 300
    IPERF_EXEC_TIME = 5
    BURNING_CONFIG_FILE = "cmdline_config_100_workload.txt"


    # NUMBER_OF_VMS_FIO = 6
    STORAGE_VOLUME = ["/home"]
    TEST_TIMEOUT = 5

    NUMBER_OF_VMS_TOTAL = 5

    NUMBER_OF_VMS_PFS = 1
    NUMBER_OF_VMS_VFS = 1

    NUMBER_OF_VMS_CYCLING = 1

    NUMBER_OF_VMS_IPERF = 2
    NUMBER_OF_VMS_FIO = 1
    NUMBER_OF_VMS_BURNIN = 1


    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationRHELVTdVMStress object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationRHELVTdVMStress, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._storage_provider = StorageProvider.factory(self._log, self.os, cfg_opts)  # type: StorageProvider
        self.driver_provider = DriverProvider.factory(self._log, cfg_opts, self.os)  # type: DriverProvider
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self.common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self._cfg_opt = cfg_opts
        if self.os.os_type == OperatingSystems.LINUX:
            self.burnin_config_file = self.collateral_installer.download_tool_to_host(self.BURNING_CONFIG_FILE)
        elif self.os.os_type == OperatingSystems.WINDOWS:
            self.burnin_config_file = Path(os.path.dirname(os.path.abspath(__file__))).parent
            self.burnin_config_file = os.path.join(self.burnin_config_file, self.BURNING_CONFIG_FILE_WINDOWS)
        else:
            raise NotImplementedError("not implemented for this OS %s" % self._os.os_type)

        self.stress_app_provider = StressAppTestProvider.factory(self._log, os_obj=self.os, cfg_opts=cfg_opts)
        self.burnin_config_file = Path(os.path.dirname(os.path.abspath(__file__)))
        self.burnin_config_file = os.path.join(self.burnin_config_file, self.BURNING_80_WORKLOAD_CONFIG_FILE)

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


    #     super(VirtualizationRHELVTdVMStress, self).prepare()


    def execute(self):
        """
        This Method is Used to.
        1 SRIOV NIC iperf for 6VMs,4 VMs are assigned with VFs, 2 VMs are assigned with PFs
        2 Run FIO stress on 4 VMs
        3 CPU and Memory stress on 8VMs using burnin tool
        4 VM cycling on 12 VMs
        :return: True if all steps executes and getting the status as expected.
        """
        self._vm_provider.create_bridge_network("virbr0")
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)

        extra_disk = 24
        stress_thread = []
        vm_sut_obj_list = []
        bit_location_vm = None
        stressapp_provider_obj_list = []
        thread_val = []
        self.bit_location = self.collateral_installer.install_burnintest()
        for index in range(self.NUMBER_OF_VMS_TOTAL):
            vm_name = self.VM_TYPE + "_" + str(index)
            self._vm_provider.destroy_vm(vm_name)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" Creating VM:{} on RHEL.".format(vm_name))
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL, self.VM_TYPE)
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True,
                                   pool_id=free_storage_pool, pool_vol_id=None, cpu_core_list=None)
            time.sleep(120)
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            self._log.info(" Created VM:{} on RHEL.".format(vm_name))

        for index in range(self.NUMBER_OF_VMS_TOTAL):
            self._test_content_logger.start_step_logger(1)
            if index == 0 or index <= self.NUMBER_OF_VMS_IPERF:
                network_device_name = self._common_content_configuration.get_columbiaville_nic_device_name()
                nw_device_list = self.get_sriovf_enabled_nw_adapters(network_device_name)
                opt_dict = self.assign_static_ip_to_nw_adapters(nw_device_list)

                nw_adapter_name = nw_device_list[0]
                # create VF
                self.create_virtual_function(self.NUMBER_OF_VMS, nw_adapter_name)
                # get the VF adapter details
                vfs_data_list = self.get_vf_adapter_details()


                # VF module details
                self.get_and_verify_vf_module_details()
                # get VF mac ids & assign it
                vf_mac_id_details = self.get_vf_mac_details()
                mac_id_list = self.assign_macs_to_vfs(self.NUMBER_OF_VMS, vf_mac_id_details, nw_adapter_name)
                # MAC id details of VM list
                self.verify_vf_mac_details(mac_id_list)
                # VF module details
                self.get_and_verify_vf_module_details()
                vm_sut_obj_list = []
                mac_index = 0
                extra_disk = 24
                LIST_OF_VM_NAMES_NEW = []
                for index in range(self.NUMBER_OF_VMS_VFS):
                    vm_name = self.VM[index] + "_" + str(index)
                    LIST_OF_VM_NAMES_NEW.append(vm_name)

                for index, vm_name in zip(range(len(LIST_OF_VM_NAMES_NEW)), LIST_OF_VM_NAMES_NEW):
                    ip, subnet = opt_dict[nw_device_list[0]]
                    ip = ip[:-2] + str(int(ip[-2:]) + 5 + index)
                    self.verify_vm_functionality(vm_name, self.VM[index])
                    # attaching the VF device to the VM
                    self.attach_pci_nw_device_to_vm(vfs_data_list[index], vm_name)
                    # create VM os object
                    vm_os_obj = self.create_vm_host(vm_name, self.VM[index])
                    common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opt)
                    vm_sut_obj_list.append(vm_os_obj)
                    # verify VF in VM
                    self.verify_vf_in_vm(vm_os_obj)
                    # get vf adapter name in VM
                    vf_adapter_name = self.get_virtual_adapter_name_in_vm(common_content_lib_vm)
                    # assign the IP to the VM
                    self.assign_ip_to_vf_in_vm(vm_os_obj, ip, subnet, vf_adapter_name, vm_name)
                    # ping the ip from the SUT
                    self._vm_provider.ping_vm_from_sut(ip)

                    self._vm_provider.ssh_from_sut_to_ip(self._common_content_lib, ip, "root", "password")

                for index in range(self.NUMBER_OF_VMS_PFS):
                    print("Entered the PFs")

                    vm_name = self.VM_TYPE + "_" + str(index)
                    network_device_name = self._common_content_configuration.get_columbiaville_nic_device_name()
                    device_list = self.get_sriovf_enabled_nw_adapters(network_device_name)
                    nw_device_id = device_list[index]
                    network_device_name = self.get_pci_info(nw_device_id)
                    pcie_device = network_device_name[0]
                    self.attach_pci_nw_device_to_vm(pcie_device, vm_name)
                    index = self.NUMBER_OF_VMS_IPERF
                    print("Completed the PFs")


                client_thread,server_thread = self.execute_iperf_SRIOV()
            self._test_content_logger.end_step_logger(1, True)

            index_range = index + self.NUMBER_OF_VMS_FIO
            new_thread = []
            cycle_thread = []
            self._test_content_logger.start_step_logger(2)
            #if index == 6 or index_range >= self.NUMBER_OF_VMS_FIO:
            if index == 2 or  index_range >= self.NUMBER_OF_VMS_FIO:
                for index in range(self.NUMBER_OF_VMS_FIO):
                     # Creates VM names dynamically according to th
                     #index_new = 6 + index
                     index_new = 2 + index
                     vm_name = self.VM_TYPE + "_" + str(index_new)
                     print("the vm name for FIO case")
                     print(vm_name)

                     vm_obj = self.create_vm_host(vm_name, self.VM_TYPE)
                     common_content_lib_vm_obj = CommonContentLib(self._log, vm_obj, self._cfg_opt)
                     self.get_yum_repo_config(vm_obj, common_content_lib_vm_obj, os_type="centos",machine_type="vm")
                     install_collateral_vm_obj = InstallCollateral(self._log, vm_obj, self._cfg_opt)
                     install_collateral_vm_obj.install_fio(install_fio_package=True)
                     new_thread = threading.Thread(target=self.execute_fio_SRIOV,
                                                   args=(common_content_lib_vm_obj,))
                     new_thread.start()

                     index = self.NUMBER_OF_VMS_IPERF + self.NUMBER_OF_VMS_FIO

            index_range = index + self.NUMBER_OF_VMS_CYCLING
            self._test_content_logger.end_step_logger(2, True)

            self._test_content_logger.start_step_logger(3)

     #   if index == 12 and index_range >= self.NUMBER_OF_VMS_CYCLING:
            if index == 3 and index_range >= self.NUMBER_OF_VMS_CYCLING:
                for index in range(self.NUMBER_OF_VMS_CYCLING):
                #new_index = 12 + index
                    new_index = 3 + index

                    vm_name = self.VM_TYPE + "_" + str(new_index)
                    self.reboot_linux_vm1(vm_name)
                    index = self.NUMBER_OF_VMS_IPERF + self.NUMBER_OF_VMS_FIO + self.NUMBER_OF_VMS_CYCLING

            self._test_content_logger.end_step_logger(3, True)

            self._test_content_logger.start_step_logger(4)
            index_range = index + self.NUMBER_OF_VMS_BURNIN

            if index == 4 and index_range >= self.NUMBER_OF_VMS_BURNIN:
           #if index == 0 and index_range >= self.NUMBER_OF_VMS_BURNIN:
                self.execute_burnin_SRIOV()
            self._test_content_logger.end_step_logger(4, True)


            new_thread.join()

            return True


    def reboot_linux_vm1(self, vm_name):
        REBOOT_VM_COMMAND = "virsh reboot {}"
        cmd_result = self._common_content_lib.execute_sut_cmd(self.REBOOT_VM_COMMAND
                                                          .format(vm_name),
                                                          "create snapshot of VM {}".format(vm_name),
                                                          self._command_timeout)
        self._log.info("Successfully rebooted VM {} : result {}\n"
                      .format(vm_name, cmd_result))

    def execute_iperf_SRIOV(self):
        for index in range(self.NUMBER_OF_VMS_IPERF):
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
            time.sleep(60)
            return (server_thread,client_thread)


    def execute_fio_SRIOV(self, common_content_lib_vm_obj):
        self._install_collateral.install_fio(install_fio_package=True)
        fio_thread = None

        fio_thread1 = None
        fio_thread = threading.Thread(target=self.fio_execute_thread,
                                      args=(self.FIO_CMD, self.FIO_CMD, self.TEST_TIMEOUT, common_content_lib_vm_obj))
        fio_thread.start()
        self._log.info("Successfully tested fio Stress on SUT")


    def execute_burnin_SRIOV(self):
        thread_val = []
        vm_sut_obj_list = []
        stressapp_provider_obj_list = []
        for index in range(self.NUMBER_OF_VMS_BURNIN):

           # new_index = 18 + index
            new_index = 4 + index

            vm_name = self.VM_TYPE + "_" + str(index)
            vm_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_obj)
            install_collateral_vm_obj = InstallCollateral(self._log, vm_obj, self._cfg_opt)
            stress_app_provider_vm = StressAppTestProvider.factory(self._log, os_obj=vm_obj, cfg_opts=self._cfg_opt)
            stressapp_provider_obj_list.append(stress_app_provider_vm)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_obj, self._cfg_opt)
            self.get_yum_repo_config(vm_obj, common_content_lib_vm_obj, os_type="centos",machine_type="vm")
            self.install_burnin_dependencies_linux(vm_obj, common_content_lib_vm_obj)
            # To install BurnIn tool in VM
            bit_location_vm = install_collateral_vm_obj.install_burnin_linux()

        for index, each, app_list in zip(range(self.NUMBER_OF_VMS_BURNIN), vm_sut_obj_list,
                                         stressapp_provider_obj_list):
            new_index = 18 + index
            vm_name = self.VM_TYPE + "_" + str(index)
            vm_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            stress_thread = threading.Thread(target=app_list.execute_burnin_test,
                                             args=(self.log_dir, self.BIT_TIMEOUT, bit_location_vm,
                                               self.BURNING_80_WORKLOAD_CONFIG_FILE, vm_name))
            # Thread has been started
            stress_thread.start()
            thread_val.append(stress_thread)
        # execute burnin test on SUT
        self._log.info("Starting Burnin stress test on SUT")
        burnin_thread = threading.Thread(target=self.stress_app_provider.execute_burnin_test,
                                         args=(self.log_dir, self.BIT_TIMEOUT, self.bit_location,
                                           self.BURNING_80_WORKLOAD_CONFIG_FILE,))
        # Thread has been started
        burnin_thread.start()
        self._log.info("Successfully started Burnin Stress on SUT and VM")

        time.sleep((self.BIT_TIMEOUT) + TimeConstants.FIVE_MIN_IN_SEC)
        self._log.info("Killing all threads for Burnin Stress on SUT and VM")


def cleanup(self, return_status):  # type: (bool) -> None
    super(VirtualizationRHELVTdVMStress, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationRHELVTdVMStress.main()
             else Framework.TEST_RESULT_FAIL)

