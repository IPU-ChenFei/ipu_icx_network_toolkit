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
import array
import threading

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
# from src.virtualization.virtualization_common import VirtualizationCommon
from src.virtualization.base_qat_util import BaseQATUtil
from src.lib.install_collateral import InstallCollateral
from src.lib.common_content_lib import CommonContentLib
from src.provider.vm_provider import VMs

class VirtualizationSIOVQATCrossSocketTopology(BaseQATUtil):
    """
    Phoenix ID : 16014132014
    The purpose of this test case is to validate the Cross Socket topology using SIOV QAT successfully on SUT/VM.
    Then execute DPDK and QAT workload inside host
    """
    NUMBER_OF_VMS = 2
    VM = [VMs.CENTOS] * NUMBER_OF_VMS
    VM_TYPE = "CENTOS"
    TEST_CASE_ID = ["P16014132014", "VirtualizationSIOVQATCrossSocketTopology"]
    BIOS_CONFIG_FILE = "virt_siov_qat_cross_socket_topo_bios.cfg"
    STORAGE_VOLUME = ["/home"]
    QAT_LOAD_TEST_TIME = 7200
    STEP_DATA_DICT = {
        1: {'step_details': 'Install and verify Bios knobs for QAT',
            'expected_results': 'Bios knobs installed and verified successfully'},
        2: {'step_details': 'Get the CPU socket, core and threads per core info',
            'expected_results': 'CPU core information retrieved'},
        3: {'step_details': 'Install and configure the yum repo config file',
            'expected_results': 'Yum repo configured successfully'},
        4: {'step_details': 'Install the QAT depemdencies, may be kernel sources as well',
            'expected_results': 'All packages installed successfully'},
        5: {'step_details': 'Check and Install the QAT driver and get qat device details',
            'expected_results': 'QAT driver built and installed'},
        6: {'step_details': 'Restart by Stopping and Starting the QAT Services',
            'expected_results': 'QAT Services restarted successfully'},
        7: {'step_details': 'Check and create the qat devices',
            'expected_results': 'QAT devices created successfully'},
        8: {'step_details': 'Create the Storage Pool for VMs',
            'expected_results': 'Storage Pools created successfully'},
        9: {'step_details': 'Create the Names for VMs to be created',
            'expected_results': 'VM names created'},
        10: {'step_details': 'Start creating the VMs as per the names created',
            'expected_results': 'All VMs created with mdev devices nd dlb2 driver and libdlb'},
        11: {'step_details': 'Create the VM',
            'expected_results': 'VM creation successfully done'},
        12: {'step_details': 'Verify the HQM/QAT in kernel in VM',
             'expected_results': 'HQM/QAT verified and driver removed in VM'},
        13: {'step_details': 'Attach the created mdev device to VM',
            'expected_results': 'Created mdev device attached to VM'},
        14: {'step_details': 'Install QAT driver/utils, verify it installed or not',
            'expected_results': 'QAT driver/utils are installed successfully'},
        15: {'step_details': 'Check the attached device in VM and make it up',
             'expected_results': 'VQAT device checked and made "up" successfully'},
        16: {'step_details': 'Execute QAT work load for 2 hours',
            'expected_results': 'QAT workload executed successfully for 2 hours'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of InstallAndVerify HQM,Dpdk & run Dpdk, QAT workload inside host

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.virtualization_qat_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(VirtualizationSIOVQATCrossSocketTopology, self).__init__(test_log, arguments, cfg_opts, self.virtualization_qat_bios_knobs)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(test_log, self.os, cfg_opts)
        self._cfg_opt = cfg_opts
        self._arg_tc = arguments
        self._test_log = test_log

    def prepare(self):
        # type: () -> None
        """Test preparation/setup """

        if self.os.os_type == OperatingSystems.LINUX:
            self._log.info("We have Linux OS for test case... proceeding further..")
        else:
            raise content_exceptions.TestFail("Target is not booted with Linux")

        self._test_content_logger.start_step_logger(1)
        super(VirtualizationSIOVQATCrossSocketTopology, self).prepare()
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        self._vm_provider.create_bridge_network("virbr0")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute_workload_test_on_vm(self, vm_name, vm_os_obj, common_content_obj, time_of_test_sec):
        """
        Executing the workload tool and generate the output file.

        :param: vm_name VM Name
        :param: common_content_obj object of common_content class for VM
        :param: time_of_test_sec test execution time in seconds
        :return: True on success
        """
        start_time = time.time()
        while True:
            current_time = time.time()
            elapsed_time = current_time - start_time
            self.run_qat_workload(common_content_obj)
            if elapsed_time > time_of_test_sec:
                self._log.info("Finished QAT load test after: " + str(int(elapsed_time)) + " seconds")
                break
        self._log.info("Successfully ran wrkload Tool on VM:{}".format(vm_name))

    def execute(self):
        """
        This validates the Cross Socket topology using SIOV QAT successfully on SUT/VM.
        Then execute DPDK and QAT workload inside host
        """
        """
            This function calling hqm installation and verify it is installed successfully and execute 
            DPDK and QAT in host 

            :return: True if test case pass else fail
        """
        self._test_content_logger.start_step_logger(2)
        self.enable_intel_iommu_by_kernel()
        socket, core_socket, threads_per_core = self.get_cpu_core_info()
        total_cpus = socket * core_socket * threads_per_core
        qat_per_socket = 4
        mdev_per_socket = 4
        total_mdev = socket * mdev_per_socket

        vqat_per_qat_dev = 4
        # cpus_per_vm = int(total_cpus/total_mdev)
        cpus_per_vm = int(total_cpus/self.NUMBER_OF_VMS)
        vqat_start_index_socket0 = 0
        vqat_start_index_socket1 = int(total_mdev/socket)
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self.get_yum_repo_config(self.os, self._common_content_lib, os_type="centos")
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        qat_dependency_packages = "epel-release zlib-devel libnl3-devel boost-devel systemd-devel yasm lz4-devel elfutils-libelf-devel openssl-devel readline-devel"
        self._install_collateral.yum_install(package_name = qat_dependency_packages)
        # Kernel source have to be installed as well but after checking the kernel version in SUT
        # kernel_source_install = "https://emb-pub.ostc.intel.com/overlay/centos/8.4.2105/202109221317/repo/x86_64/kernel-next-server-devel-5.12.0-2021.05.07_39.el8.x86_64.rpm"
        # self._install_collateral.yum_install(package_name=kernel_source_install)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        self.install_check_qat_status(qat_type="siov", target_type="host", common_content_object=self._common_content_lib)
        for index in range(total_mdev):
            self.update_qat_siov_in_file(vqat_per_qat_dev, "/etc/4xxx_dev{}.conf".format(index), self._common_content_lib)

        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        self.stop_qat_service(self._common_content_lib)
        self.start_qat_service(self._common_content_lib)
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        bdf = []
        sym = []
        asym = []
        dc = []
        uuid_sym = []
        uuid_asym = []
        uuid_dc = []
        total_dev_sym_and_dc = 0
        bdf_sym_asym_dc_dict = self.get_qat_device_details(self._common_content_lib)
        list_dev_sym_asym_dc = [[] for i in range(len(bdf_sym_asym_dc_dict['bdf']))]
        total_dev_sym_asym_dc = array.array('i', (0 for i in range(len(bdf_sym_asym_dc_dict['bdf']))))
        for index in range(len(bdf_sym_asym_dc_dict['bdf'])):
            bdf.append((bdf_sym_asym_dc_dict['bdf'])[index])

            number_of_dev, dev_uuid_list = self.create_qat_devices(bdf[index], (bdf_sym_asym_dc_dict['sym'])[index],
                                                                   "sym", self._common_content_lib)
            uuid_sym.append(dev_uuid_list)
            list_dev_sym_asym_dc[index].extend(dev_uuid_list)
            total_dev_sym_asym_dc[index] = total_dev_sym_asym_dc[index] + number_of_dev
            # update the total no of vqat device in system
            sym.append(number_of_dev)
            total_dev_sym_and_dc = total_dev_sym_and_dc + number_of_dev
            (bdf_sym_asym_dc_dict['sym'])[index] = number_of_dev

            number_of_dev, dev_uuid_list = self.create_qat_devices(bdf[index], (bdf_sym_asym_dc_dict['asym'])[index],
                                                                   "asym", self._common_content_lib)
            uuid_asym.append(dev_uuid_list)
            list_dev_sym_asym_dc[index].extend(dev_uuid_list)
            total_dev_sym_asym_dc[index] = total_dev_sym_asym_dc[index] + number_of_dev
            # update the total no of vqat device in system
            asym.append(number_of_dev)
            (bdf_sym_asym_dc_dict['asym'])[index] = number_of_dev
            # total_dev_sym_and_dc = total_dev_sym_and_dc + number_of_dev

            number_of_dev, dev_uuid_list = self.create_qat_devices(bdf[index], (bdf_sym_asym_dc_dict['dc'])[index],
                                                                   "dc", self._common_content_lib)
            uuid_dc.append(dev_uuid_list)
            list_dev_sym_asym_dc[index].extend(dev_uuid_list)
            total_dev_sym_asym_dc[index] = total_dev_sym_asym_dc[index] + number_of_dev
            # update the total no of vqat device in system
            dc.append(number_of_dev)
            (bdf_sym_asym_dc_dict['dc'])[index] = number_of_dev
            total_dev_sym_and_dc = total_dev_sym_and_dc + number_of_dev

        vqat_per_vm = 1
        vqat_start_index_socket0 = 0
        vqat_start_index_socket1 = int(total_dev_sym_and_dc / socket)

        self._test_content_logger.end_step_logger(7, return_val=True)

        self._test_content_logger.start_step_logger(8)
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)
        self._test_content_logger.end_step_logger(8, return_val=True)

        self._test_content_logger.start_step_logger(9)
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on CentOS.".format(vm_name))
        self._test_content_logger.end_step_logger(9, True)

        vm_sut_obj_list = []
        uuid_for_vm_list = []
        self._test_content_logger.start_step_logger(10)

        used_vqat_num_vm = 0
        if self.NUMBER_OF_VMS < socket:
            vms_per_socket = self.NUMBER_OF_VMS  # int(self.NUMBER_OF_VMS / socket)
        else:
            vms_per_socket = int(self.NUMBER_OF_VMS / socket)
        list_dev_sym_asym_dc_bu = list_dev_sym_asym_dc
        total_dev_sym_asym_dc_bu = total_dev_sym_asym_dc
        vm_index_start_sock1 = int(self.NUMBER_OF_VMS/socket)
        for vm_index, vm_name in zip(range(self.NUMBER_OF_VMS), self.LIST_OF_VM_NAMES):
            # create with default values
            self._test_content_logger.start_step_logger(11)
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
            # No Of Sockets = 2
            # Total cores = 240
            # Sock0: 0-119, Sock1: 120-239
            # cpus_per_vm = 120
            # VM0 ==> 120-239 ,  VM1 ==> 0-119
            # cpus_per_vm = 60
            # VM0 ==> 180-239, VM1 ==> 120-179, VM2 ==> 60-119, VM3 ==> 0-59
            end_index = (total_cpus - 1) - (vm_index * cpus_per_vm)
            # start_index = end_index - ((vm_index + 1) * cpus_per_vm) + 1
            start_index = end_index - cpus_per_vm + 1
            # cpu_list = list(range(start_index, end_index+1))
            cpu_list = "{}-{}".format(start_index, end_index)
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True, pool_id=free_storage_pool,
                                  pool_vol_id=None, cpu_core_list=cpu_list, nw_bridge="virbr0")
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            self._test_content_logger.end_step_logger(11, return_val=True)

            self._log.info(" Created VM:{} on CentOS.".format(vm_name))

            # create VM os object
            self._test_content_logger.start_step_logger(12)
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm_obj = CommonContentLib(self._test_log, vm_os_obj, self._cfg_opt)
            install_collateral_vm_obj = InstallCollateral(self._test_log, vm_os_obj, self._cfg_opt)
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, os_type="centos", machine_type="vm")
            self.enable_intel_iommu_by_kernel_in_vm(vm_name, grub_param=None, common_content_lib=common_content_lib_vm_obj)
            # install_collateral_vm_obj.screen_package_installation()
            # Also Stop and disbale firewalld in VM
            # yum -y install boost-devel* cc* gcc* clang*
            self._test_content_logger.end_step_logger(12, return_val=True)

            self._test_content_logger.start_step_logger(13)
            # qat_dev_index = vm_index #total_mdev - vm_index -1
            #     # when VM index reaches the index from where the socket1 VMs start
            #     # for socket1 VMs, vqat devices to be attached from vqat devices created using qat devices on socket0
            #     # e.g. VM4-VM7<-> vqat from socket0
            #     # when VM index reaches the index from where the socket0 VMs start
            #     # for socket0 VMs, vqat devices to be attached from vqat devices created using qat devices on socket1
            #     # e.g. VM0-VM3 <-> vqat from socket1
            uuid_for_vm = ""
            qat_dev_index = qat_per_socket * (socket - int(vm_index / vms_per_socket) - 1)
            qat_start_index = qat_dev_index
            qat_end_index = qat_dev_index + qat_per_socket
            total_vqat_attached_vm = 0
            for qat_index in range(qat_start_index, qat_end_index):
                vqat_start_index_vm_group = qat_index * int(
                    total_dev_sym_and_dc / socket)  # for a group of VMs on a socket
                vqat_end_index_vm_group = vqat_start_index_vm_group + int(
                    total_dev_sym_and_dc / socket)  # for a group of VMs on a socket
                uuid_for_vm = ""
                for vqat_dev_no in range(0, total_dev_sym_asym_dc_bu[qat_index]):
                    if list_dev_sym_asym_dc_bu[qat_index][vqat_dev_no] != "":
                        uuid_for_vm = list_dev_sym_asym_dc_bu[qat_index][vqat_dev_no]
                        # invalidate so that it can not be taken for next VM
                        list_dev_sym_asym_dc_bu[qat_index][vqat_dev_no] = ""
                    else:
                        continue

                    if uuid_for_vm != "":
                        total_vqat_attached_vm = total_vqat_attached_vm + 1
                        uuid_for_vm_list.append(uuid_for_vm)
                        self.attach_vqat_instance_to_vm(vm_name, uuid_for_vm)
                        self._log.info("QAT device {} attach to VM {} was successfull...".format(uuid_for_vm, vm_name))
                        uuid_for_vm = ""
                    # break "for loop"
                    if total_vqat_attached_vm >= vqat_per_vm:
                        break
                # break external "for loop"
                if total_vqat_attached_vm >= vqat_per_vm:
                    break

            self._test_content_logger.end_step_logger(13, return_val=True)

            self._test_content_logger.start_step_logger(14)
            self.install_check_qat_status(vm_name=vm_name, os_obj=vm_os_obj,
                                          qat_type="siov", target_type="guest",
                                          common_content_object=common_content_lib_vm_obj, is_vm="yes")
            self._test_content_logger.end_step_logger(14, return_val=True)

            self._test_content_logger.start_step_logger(15)
            self.get_qat_device_status_adfctl(qat_dev_index, common_content_lib_vm_obj)
            self.set_qat_device_up_adfctl(qat_dev_index, common_content_lib_vm_obj)
            self.check_vqat_device_type_attached(common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(15, return_val=True)

        self._test_content_logger.end_step_logger(10, True)

        self._log.info("Run the QAT load test for 7200 seconds in all guest VMs")

        self._test_content_logger.start_step_logger(16)
        wrkld_thread_list_l1 = []

        seconds = self.QAT_LOAD_TEST_TIME

        for index, vm_name, each_vm_obj in zip(range(len(self.LIST_OF_VM_NAMES)), self.LIST_OF_VM_NAMES,
                                               vm_sut_obj_list):
            common_content_lib_vm_obj = CommonContentLib(self._test_log, each_vm_obj, self._cfg_opt)
            vm_wrkld_thread = threading.Thread(target=self.execute_workload_test_on_vm,
                                               args=(vm_name, each_vm_obj, common_content_lib_vm_obj, seconds,))
            wrkld_thread_list_l1.append(vm_wrkld_thread)

        for thread_id in wrkld_thread_list_l1:
            thread_id.start()

        # wait for Workloads to complete the execution
        time.sleep(seconds + 30)

        for thread_id in wrkld_thread_list_l1:
            thread_id.join()
        self._test_content_logger.end_step_logger(16, return_val=True)

        for index, vm_name in zip(range(len(self.LIST_OF_VM_NAMES)), self.LIST_OF_VM_NAMES):
            start_vqat_index_in_list = index * vqat_per_vm
            for vqat_num in range(start_vqat_index_in_list, (start_vqat_index_in_list + vqat_per_vm) ):
                vqat_uuid = uuid_for_vm_list[vqat_num]
                try:
                    self.detach_vqat_instance_from_vm(vm_name, vqat_uuid)
                    self.remove_qat_devices(vqat_uuid)
                except:
                    pass

        return True

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationSIOVQATCrossSocketTopology.main() else Framework.TEST_RESULT_FAIL)
