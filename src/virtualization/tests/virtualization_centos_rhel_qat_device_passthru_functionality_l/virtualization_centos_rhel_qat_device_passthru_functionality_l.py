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
from src.virtualization.virtualization_common import VirtualizationCommon
from src.virtualization.base_qat_util import BaseQATUtil
from src.lib.install_collateral import InstallCollateral
from src.lib.common_content_lib import CommonContentLib
from src.provider.vm_provider import VMs

class VirtualizationQatKvmDevicePassthroughFunctionality(BaseQATUtil):
    """
    Phoenix ID : 16012898765
    Purpose of this test case is to validate passthrough functionality of QAT devices.
    """
    NUMBER_OF_VMS = 1
    VM = [VMs.CENTOS] * 1
    VM_TYPE = "CENTOS"
    TEST_CASE_ID = ["P16012898765", "VirtualizationQatKvmDevicePassthroughFunctionality"]
    BIOS_CONFIG_FILE = "virtualization_centos_rhel_qat_device_passthru_functionality_l.cfg"
    STORAGE_VOLUME = ["/home"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Install and verify Bios knobs for QAT',
            'expected_results': 'Bios knobs installed and verified successfully'},
        2: {'step_details': 'Enable IOMMU in Kernel',
            'expected_results': 'IOMMU enabled in Kernel'},
        3: {'step_details': 'Install and configure the yum repo config file',
            'expected_results': 'Yum repo configured successfully'},
        4: {'step_details': 'Install the QAT depemdencies, may be kernel sources as well',
            'expected_results': 'All packages installed successfully'},
        5: {'step_details': 'Check the status of QAT Devices',
            'expected_results': 'Getting the status expected status of QAT Devices'},
        6: {'step_details': 'Checking the status of QAT Devices',
            'expected_results': 'Checked the status of QAT Devices'},
        7: {'step_details': 'Getting the QAT device details',
            'expected_results': 'Got the QAT device details'},
        8: {'step_details': 'Loading the vfio-pci driver',
            'expected_results': 'Loaded the vfio-pci driver'},
        9: {'step_details': 'Unbinding the host driver from the SUT',
            'expected_results': 'Driver unbinded from host successfully'},
        10: {'step_details': 'Binding to vfio-pci driver to the guest',
            'expected_results': 'Binded the vfio-cpi driver to the guest successfully'},
        11: {'step_details': 'Creating the storage pool fro VM',
            'expected_results': 'Successfully created storage pool for VM'},
        12: {'step_details': 'Creating the VM',
            'expected_results': 'Created the VM successfully'},
        13: {'step_details': 'Yum repo configuring successfully for VM',
            'expected_results': 'Yum repo configured successfully for VM'},
        14: {'step_details': 'Enabling IOMMU in VM',
            'expected_results': 'Enabled IOMMU in Kernel'},
        15: {'step_details': 'Attaching PCI device to VM by using DBSF value',
            'expected_results': 'Successfully attached PCI device to VM'},
        16: {'step_details': 'Build and install QAT Driver',
             'expected_results': 'Successfully installed QAT driver!'},
        17: {'step_details': 'Check if attached passed through device present in VM',
             'expected_results': 'Successfully verified the passed thorugh device in VM'},
        18: {'step_details': 'Detaching PCI device from VM',
            'expected_results': 'Successfully detached PCI device from VM'},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of InstallAndVerify HQM,Dpdk & run Dpdk, QAT workload inside host

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.virtualization_qat_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(VirtualizationQatKvmDevicePassthroughFunctionality, self).__init__(test_log, arguments, cfg_opts, self.virtualization_qat_bios_knobs)
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
        super(VirtualizationQatKvmDevicePassthroughFunctionality, self).prepare()
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        self._vm_provider.create_bridge_network("virbr0")
        self._test_content_logger.end_step_logger(1, return_val=True)

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
        # unbind the QAT devices by uloading vfio driver, in case system not rebooted
        self.unload_vfio_driver()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self.get_yum_repo_config(self.os, self._common_content_lib, os_type="centos")
        self._test_content_logger.end_step_logger(3, return_val=True)
        socket, core_socket, threads_per_core = self.get_cpu_core_info()
        total_cpus = socket * core_socket * threads_per_core
        mdev_per_socket = 4
        total_mdev = socket * mdev_per_socket

        vqat_per_qat_dev = 4
        # cpus_per_vm = int(total_cpus/total_mdev)
        cpus_per_vm = int(total_cpus / self.NUMBER_OF_VMS)
        vqat_start_index_socket0 = 0
        vqat_start_index_socket1 = int(total_mdev / socket)
        self._test_content_logger.start_step_logger(4)
        qat_dependency_packages = "zlib-devel libnl3-devel boost-devel systemd-devel yasm lz4-devel elfutils-libelf-devel openssl-devel readline-devel"
        self._install_collateral.yum_install(package_name = qat_dependency_packages)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        self.install_check_qat_status(qat_type="siov", target_type="host", common_content_object=self._common_content_lib)
        for index in range(total_mdev):
            self.update_qat_siov_in_file(vqat_per_qat_dev, "/etc/4xxx_dev{}.conf".format(index),
                                         self._common_content_lib)
        self.stop_qat_service(self._common_content_lib)
        self.start_qat_service(self._common_content_lib)
        self._test_content_logger.end_step_logger(5, return_val=True)
        self._test_content_logger.start_step_logger(6)
        self.qat_device_presence()
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        bdf_sym_asym_dc_dict = self.get_qat_device_details(self._common_content_lib)
        self._test_content_logger.end_step_logger(7, return_val=True)

        self._test_content_logger.start_step_logger(8)
        self.load_vfio_driver()
        self._test_content_logger.end_step_logger(8, return_val=True)

        self._test_content_logger.start_step_logger(9)
        for index in range(self.NUMBER_OF_VMS):
            self.host_vfio_driver_unbind(dbsf_value=bdf_sym_asym_dc_dict['bdf'][index],
                                         common_content_object=self._common_content_lib)
            self._test_content_logger.end_step_logger(9, return_val=True)
            self._test_content_logger.start_step_logger(10)
            self.guest_vfio_pci_driver_bind(dbsf_value=bdf_sym_asym_dc_dict['bdf'][index],
                                            accel_type="qat",
                                            common_content_object=self._common_content_lib)
        self._test_content_logger.end_step_logger(10, return_val=True)
        self._test_content_logger.start_step_logger(11)
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)
            self._test_content_logger.end_step_logger(11, return_val=True)

        self._test_content_logger.start_step_logger(12)
        vm_sut_obj_list = []
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)+"kk"
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on CentOS.".format(vm_name))

        for vm_index, vm_name in zip(range(self.NUMBER_OF_VMS), self.LIST_OF_VM_NAMES):
            # create with default values
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True,
                                   pool_id=free_storage_pool,
                                   pool_vol_id=None, cpu_core_list=None,
                                   nw_bridge="virbr0")
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            self._log.info(" Created VM:{} on CentOS.".format(vm_name))
            self._test_content_logger.end_step_logger(12, return_val=True)

            # create VM os object
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm_obj = CommonContentLib(self._test_log, vm_os_obj, self._cfg_opt)
            install_collateral_vm_obj = InstallCollateral(self._test_log, vm_os_obj, self._cfg_opt)
            self._test_content_logger.start_step_logger(13)
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, os_type="centos", machine_type="vm")
            self._test_content_logger.end_step_logger(13, return_val=True)
            self._test_content_logger.start_step_logger(14)
            self.enable_intel_iommu_by_kernel_in_vm(vm_name, grub_param=None,
                                                    common_content_lib=common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(14, return_val=True)

            domain_value, bus_value, device_value, function_value = self.get_split_hex_bdf_values_from_dbdf(
                bdf_sym_asym_dc_dict['bdf'][vm_index])
            self._test_content_logger.start_step_logger(15)
            try:
                self.detach_pci_device_using_dbdf_from_vm(vm_name, domain_value, bus_value, device_value, function_value)
            except:
                pass
            self.attach_pci_device_using_dbdf_to_vm(vm_name, domain_value, bus_value, device_value, function_value)
            self._test_content_logger.end_step_logger(15, return_val=True)
            self._test_content_logger.start_step_logger(16)
            self.install_check_qat_status(vm_name=vm_name, os_obj=vm_os_obj,
                                          qat_type="siov", target_type="guest",
                                          common_content_object=common_content_lib_vm_obj, is_vm="yes")
            self._test_content_logger.end_step_logger(16, return_val=True)
            self._test_content_logger.start_step_logger(17)
            # check if device present in VM as pass through with ID: 4940
            self.qat_passthrough_device_presencein_vm(common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(17, return_val=True)
            self._test_content_logger.start_step_logger(18)
            try:
                self.detach_pci_device_using_dbdf_from_vm(vm_name, domain_value, bus_value, device_value, function_value)
            except:
                pass
            self._test_content_logger.end_step_logger(18, return_val=True)

        return True

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationQatKvmDevicePassthroughFunctionality.main() else Framework.TEST_RESULT_FAIL)
