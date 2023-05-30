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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
# from src.virtualization.virtualization_common import VirtualizationCommon
from src.virtualization.base_qat_util import BaseQATUtil
from src.lib.install_collateral import InstallCollateral
from src.lib.common_content_lib import CommonContentLib
from src.provider.vm_provider import VMs


class VirtualizationSRIOVQATCpmVFVMWorkload(BaseQATUtil):
    """
    Phoenix ID : 16012899028
    The purpose of this test case is to validate the SR-IOV functionality using QAT device.
    Then execute QAT workload inside host/guest
    """
    NUMBER_OF_VMS = 1
    VM = [VMs.CENTOS] * NUMBER_OF_VMS
    VM_TYPE = "CENTOS"
    TEST_CASE_ID = ["P16012899028", "VirtualizationSRIOVQATCpmVFVMWorkload"]
    BIOS_CONFIG_FILE = "virt_sriov_qatcpm_vf_vmwl_biosknobs.cfg"
    STORAGE_VOLUME = ["/home"]
    QAT_VM_LOAD_TEST_TIME = 7200
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
        7: {'step_details': 'Check and create the qat VF devices, Bind with VFIO driver',
            'expected_results': 'QAT VF devices created and binded with VFIO driver successfully'},
        8: {'step_details': 'Create the Storage Pool for VMs',
            'expected_results': 'Storage Pools created successfully'},
        9: {'step_details': 'Create the Names for VMs to be created',
            'expected_results': 'VM names created'},
        10: {'step_details': 'Start creating the VMs as per the names created',
             'expected_results': 'All VMs created with QAT VF device and QAT drivers'},
        11: {'step_details': 'Create the VM',
             'expected_results': 'VM creation successfully done'},
        12: {'step_details': 'Verify the QAT in kernel in VM',
             'expected_results': 'QAT verified and driver removed in VM'},
        13: {'step_details': 'Attach the created VF device to VM',
             'expected_results': 'Created VF device attached to VM'},
        14: {'step_details': 'Install QAT driver/utils, verify it installed or not',
             'expected_results': 'QAT driver/utils are installed successfully'},
        15: {'step_details': 'Check the attached device in VM and make it up',
             'expected_results': 'VQAT device checked and made "up" successfully'},
        16: {'step_details': 'Execute QAT work load for 2 hours',
             'expected_results': 'QAT workload executed successfully for 2 hours'},
        17: {'step_details': 'Detach the created VF device from VM',
             'expected_results': 'Created VF device detached from VM'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of TC Class, TestContentLogger and CommonContentLib

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.virtualization_qatcpm_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                             self.BIOS_CONFIG_FILE)
        super(VirtualizationSRIOVQATCpmVFVMWorkload, self).__init__(test_log, arguments, cfg_opts,
                                                                    self.virtualization_qatcpm_bios_knobs)
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
        super(VirtualizationSRIOVQATCpmVFVMWorkload, self).prepare()
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        self._vm_provider.create_bridge_network("virbr0")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This validates the SR-IOV QAT functionality using QATCPM Virtual Function devices in host.
        Then execute QATCPM workload inside guest VM

        :return: True if test case pass else fail
        """
        self._test_content_logger.start_step_logger(2)
        self.enable_intel_iommu_by_kernel()
        # unbind the QAT devices by uloading vfio driver, in case system not rebooted
        self.unload_vfio_driver()
        socket, core_socket, threads_per_core = self.get_cpu_core_info()
        total_cpus = socket * core_socket * threads_per_core
        mdev_per_socket = 4
        total_mdev = socket * mdev_per_socket

        cpus_per_vm = int(total_cpus / total_mdev)
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self.get_yum_repo_config(self.os, self._common_content_lib, os_type="centos")
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)

        qat_dependency_packages = "epel-release zlib-devel libnl3-devel boost-devel systemd-devel yasm lz4-devel elfutils-libelf-devel openssl-devel readline-devel"

        self._install_collateral.yum_install(package_name=qat_dependency_packages)
        # Kernel source have to be installed as well but after checking the kernel version in SUT
        # kernel_source_install = "https://emb-pub.ostc.intel.com/overlay/centos/8.4.2105/202109221317/repo/x86_64/kernel-next-server-devel-5.12.0-2021.05.07_39.el8.x86_64.rpm"
        # self._install_collateral.yum_install(package_name=kernel_source_install)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        self.install_check_qat_status(qat_type="sriov", target_type="host",
                                      common_content_object=self._common_content_lib)
        socket, core_socket, threads_per_core = self.get_cpu_core_info()
        total_cpus = socket * core_socket * threads_per_core
        mdev_per_socket = 4
        total_mdev = socket * mdev_per_socket

        vqat_per_qat_dev = 4
        # cpus_per_vm = int(total_cpus/total_mdev)
        cpus_per_vm = int(total_cpus / self.NUMBER_OF_VMS)
        vqat_start_index_socket0 = 0
        vqat_start_index_socket1 = int(total_mdev / socket)
        # for index in range(total_mdev):
        #     self.update_qat_siov_in_file(vqat_per_qat_dev, "/etc/4xxx_dev{}.conf".format(index),
        #                                  self._common_content_lib)
        self.stop_qat_service(self._common_content_lib)
        self.start_qat_service(self._common_content_lib)

        # bdf_sym_asym_dc_dict = self.get_qat_device_details(self._common_content_lib)

        bdf_sym_asym_dc_dict = self.get_all_qat_device_bdf_value(self._common_content_lib)

        for index in range(len(bdf_sym_asym_dc_dict['bdf'])):
            self.create_accel_virtual_function(16, (bdf_sym_asym_dc_dict['bdf'])[index])

        self.qat_vf_device_presence()

        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        self.get_qat_device_status_adfctl(0, self._common_content_lib)
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)

        bdf_sym_asym_dc_dict_vf = self.get_qat_vf_device_details(self._common_content_lib)

        self.load_vfio_driver()
        for index in range(self.NUMBER_OF_VMS):
            self.host_vfio_driver_unbind(dbsf_value=bdf_sym_asym_dc_dict_vf['bdf'][index],
                                         common_content_object=self._common_content_lib)
            self.guest_vfio_pci_driver_bind(dbsf_value=bdf_sym_asym_dc_dict_vf['bdf'][index], accel_type="qat",
                                            common_content_object=self._common_content_lib)
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
            vm_name = self.VM[index] + "_" + str(index) + "kk"
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on CentOS.".format(vm_name))
        self._test_content_logger.end_step_logger(9, True)

        vm_sut_obj_list = []
        self._test_content_logger.start_step_logger(10)
        for vm_index, vm_name in zip(range(self.NUMBER_OF_VMS), self.LIST_OF_VM_NAMES):
            # create with default values
            self._test_content_logger.start_step_logger(11)
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
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
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, os_type="centos",machine_type="vm")
            self.enable_intel_iommu_by_kernel_in_vm(vm_name, grub_param=None,
                                                    common_content_lib=common_content_lib_vm_obj)
            # install_collateral_vm_obj.screen_package_installation()
            # Also Stop and disbale firewalld in VM
            # yum -y install boost-devel* cc* gcc* clang*
            self._test_content_logger.end_step_logger(12, return_val=True)

            self._test_content_logger.start_step_logger(13)
            domain_value, bus_value, device_value, function_value = self.get_split_hex_bdf_values_from_dbdf(
                bdf_sym_asym_dc_dict_vf['bdf'][vm_index])
            self._log.info("attaching device to {}: {} {} {} {} ".format(vm_name, domain_value, bus_value,
                                                                           device_value, function_value))
            try:
                self.detach_pci_device_using_dbdf_from_vm(vm_name, domain_value, bus_value, device_value, function_value)
            except:
                pass
            self.attach_pci_device_using_dbdf_to_vm(vm_name, domain_value, bus_value, device_value, function_value)
            self.install_check_qat_status(vm_name=vm_name, os_obj=vm_os_obj,
                                          qat_type="sriov", target_type="guest",
                                          common_content_object=common_content_lib_vm_obj, is_vm="yes")
            # not sure about the below if it is required
            # Note : If VM is launched with scalable vIommu mode then need to update the VM config file
            # for the QAT device like below :
            # vim /etc/4xxxvf_dev0.conf
            # Add below line in the config file
            # SVMEnabled=0
            for index in range(total_mdev):
                self.check_and_disbale_if_svm_enabled("/etc/4xxx_dev{}.conf".format(index),
                                                      common_content_object=common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(13, return_val=True)

            self._test_content_logger.start_step_logger(14)
            self.check_vqat_device_type_attached(common_content_object=common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(14, return_val=True)

            self._test_content_logger.start_step_logger(15)

            self.restart_qat_service(common_content_object=common_content_lib_vm_obj)
            self.get_qat_device_status_adfctl(vm_index, common_content_lib_vm_obj)
            self.set_qat_device_up_adfctl(vm_index, common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(15, return_val=True)

        self._test_content_logger.end_step_logger(10, True)

        self._log.info("Run the QAT load test for 7200 seconds in all guest VMs")

        self._test_content_logger.start_step_logger(16)
        start_time = time.time()
        seconds = self.QAT_VM_LOAD_TEST_TIME
        while True:
            current_time = time.time()
            elapsed_time = current_time - start_time

            for index, vm_name, each_vm_obj in zip(range(len(self.LIST_OF_VM_NAMES)), self.LIST_OF_VM_NAMES,
                                                   vm_sut_obj_list):
                common_content_lib_vm_obj = CommonContentLib(self._test_log, each_vm_obj, self._cfg_opt)
                self.run_qat_signoflife_workload(common_content_lib_vm_obj)

            if elapsed_time > seconds:
                self._log.info("Finished QAT load test after: " + str(int(elapsed_time)) + " seconds")
                break
        self._test_content_logger.end_step_logger(16, return_val=True)

        self._test_content_logger.start_step_logger(17)
        for index, vm_name, in zip(range(len(self.LIST_OF_VM_NAMES)), self.LIST_OF_VM_NAMES):
            domain_value, bus_value, device_value, function_value = self.get_split_hex_bdf_values_from_dbdf(
                bdf_sym_asym_dc_dict_vf['bdf'][index])
            self._log.info("detaching device from {}: {} {} {} {} ".format(vm_name, domain_value, bus_value,
                                                                    device_value, function_value))
            try:
                self.detach_pci_device_using_dbdf_from_vm(vm_name, domain_value, bus_value, device_value, function_value)
            except:
                pass
        for index in range(len(bdf_sym_asym_dc_dict_vf['bdf'])):
            try:
                self.delete_accel_virtual_function((bdf_sym_asym_dc_dict['bdf'])[index])
            except:
                pass

        for index in range(self.NUMBER_OF_VMS):
            self.guest_vfio_pci_driver_unbind(dbsf_value=bdf_sym_asym_dc_dict_vf['bdf'][index], accel_type="qat",
                                            common_content_object=self._common_content_lib)
            self.host_vfio_driver_bind(dbsf_value=bdf_sym_asym_dc_dict_vf['bdf'][index],
                                         common_content_object=self._common_content_lib)
        self.unload_vfio_driver()
        self._test_content_logger.end_step_logger(17, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        pass


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationSRIOVQATCpmVFVMWorkload.main() else Framework.TEST_RESULT_FAIL)
