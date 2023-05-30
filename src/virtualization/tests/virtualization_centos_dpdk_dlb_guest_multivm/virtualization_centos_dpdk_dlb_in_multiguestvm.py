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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.virtualization.virtualization_common import VirtualizationCommon
from src.provider.vm_provider import VMs


class VirtualizationDpdkDlbMultiVM(VirtualizationCommon):
    """
    Phoenix ID : 16014126519
    The purpose of this test case is to install and verify HQM driver,DPDK has been downloaded and installed & verified
    successfully on SUT.
    Then execute DPDK and DLB workload inside multiple guest
    """
    NUMBER_OF_VMS = 2
    VM = [VMs.CENTOS] * 2
    VM_TYPE = "CENTOS"
    TEST_CASE_ID = ["p16014126519", "Virtualization_Dpdk_Dlb_multipleguestVM"]
    BIOS_CONFIG_FILE = "virtualization_dpdk_dlb_bios_knobs.cfg"
    STORAGE_VOLUME = ["/home"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Install and verify Bios knobs for QAT',
            'expected_results': 'Bios knobs installed and verified successfully'},
        2: {'step_details': 'Create the Storage Pool for VMs',
            'expected_results': 'Storage Pools created successfully'},
        3: {'step_details': 'Configuring core socket for total cpus',
            'expected_results': 'total cpus configured successfully'},
        4: {'step_details': 'Install and configure the yum repo config file',
            'expected_results': 'Yum repo configured successfully'},
        5: {'step_details': 'Verify the HQM in kernel',
            'expected_results': 'HQM verified successfully'},
        6: {'step_details': 'Install HQM and dpdk, verify it installed or not',
            'expected_results': 'HQM is installed successfully and DPDK folders are present'},
        7: {'step_details': 'Create the Names for VMs to be created',
            'expected_results': 'VM names created'},
        8: {'step_details': 'Start creating the VMs as per the names created',
            'expected_results': 'All VMs created with mdev devices nd dlb2 driver and libdlb'},
        9: {'step_details': 'Create the VM',
            'expected_results': 'VM creation successfully done'},
        10: {'step_details': 'Enabling iommu on VM',
             'expected_results': 'iommu was enabled successfully on VM'},
        11: {'step_details': 'Create the mdev device',
             'expected_results': 'MDEV device for dlb2 created successfully'},
        12: {'step_details': 'Attach the created mdev device to VM',
             'expected_results': 'Created mdev device attached to VM'},
        13: {'step_details': 'Verify the HQM/dpdk in kernel in VM',
             'expected_results': 'HQM/dpdk verified successfully'},
        14: {'step_details': 'Install HQM and libdlb, verify it installed or not',
             'expected_results': 'HQM is installed successfully and DPDK folders are present'},
        15: {'step_details': 'Execute dpdk and dlb work load in VM',
             'expected_results': 'dpdk and dlb workload executed successfully in VM'}
    }


    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of InstallAndVerify HQM,Dpdk & run Dpdk, dlb workload inside host

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.virtualization_dpdk_dlb_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(VirtualizationDpdkDlbMultiVM, self).__init__(test_log, arguments, cfg_opts, self.virtualization_dpdk_dlb_bios_knobs)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self._cfg_opt = cfg_opts
        self._test_log = test_log

    def prepare(self):

        # type: () -> None
        """Test preparation/setup """

        if self.os.os_type == OperatingSystems.LINUX:
            self._log.info("We have Linux OS for test case... proceeding further..")
        else:
            raise content_exceptions.TestFail("Target is not booted with Linux")

        self._test_content_logger.start_step_logger(1)
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        self._vm_provider.create_bridge_network("virbr0")
        super(VirtualizationDpdkDlbMultiVM, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This method installs the HQM, DPDK on sut and verify if it is installed properly.
        Then execute DPDK and DLB workload inside guest
        """
        """
            This function calling hqm installation and verify it is installed successfully and execute 
            DPDK and DLB in guest 

            :return: True if test case pass else fail
        """
        self._test_content_logger.start_step_logger(2)
        self.enable_intel_iommu_by_kernel()
        self._install_collateral.screen_package_installation()
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        socket, core_socket, threads_per_core = self.get_cpu_core_info()
        total_cpus = socket * core_socket * threads_per_core
        mdev_per_socket = 4
        total_mdev = socket * mdev_per_socket
        cpus_per_vm = int(total_cpus/total_mdev)
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self.get_yum_repo_config(self.os, self._common_content_lib,os_type=self.VM_TYPE.lower())
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        self.verify_hqm_dlb_kernel()
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        self.install_hqm_driver_library(common_content_lib = self.common_content_lib)
        self.install_hqm_dpdk_library(common_content_lib = self.common_content_lib)
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on CentOS.".format(vm_name))
        self._test_content_logger.end_step_logger(7, True)

        vm_sut_obj_list = []
        self._test_content_logger.start_step_logger(8)
        vm_index = 0
        for vm_name in self.LIST_OF_VM_NAMES:
            # create with default values
            self._test_content_logger.start_step_logger(9)
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
            # self.create_vm_pool(vm_name, self.VM_TYPE, mac_addr=True, pool_id=free_storage_pool)
            end_index = (total_cpus - 1) - (vm_index * cpus_per_vm)
            # start_index = end_index - ((vm_index+1) * cpus_per_vm) + 1
            start_index = end_index - cpus_per_vm + 1
            # cpu_list = list(range(start_index, end_index+1))
            cpu_list = "{}-{}".format(start_index, end_index)
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True, pool_id=free_storage_pool,
                                   pool_vol_id=None, cpu_core_list=cpu_list, nw_bridge="virbr0")
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            self._test_content_logger.end_step_logger(9, return_val=True)

            # create VM os object
            self._test_content_logger.start_step_logger(10)
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm_obj = CommonContentLib(self._test_log, vm_os_obj, self._cfg_opt)
            install_collateral_vm_obj = InstallCollateral(self._test_log, vm_os_obj, self._cfg_opt)
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, os_type=self.VM_TYPE.lower(),machine_type="vm")
            self.enable_intel_iommu_by_kernel_in_vm(vm_name, grub_param=None, common_content_lib=common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(10, return_val=True)

            self._log.info(" Created VM:{} on CentOS.".format(vm_name))
            self._test_content_logger.start_step_logger(11)
            uuid, domain, bus, device, function = self._vm_provider.create_mdev_dlb2_instance(vm_index)
            self._test_content_logger.end_step_logger(11, return_val=True)

            self._test_content_logger.start_step_logger(12)
            self.attach_pci_device_using_dbdf_to_vm(vm_name, domain, bus, device, function)
            self._test_content_logger.end_step_logger(12, return_val=True)

            vm_index = vm_index + 1

            self._test_content_logger.start_step_logger(13)
            self.verify_hqm_dlb_kernel(common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(13, return_val=True)

            self._test_content_logger.start_step_logger(14)
            self.install_hqm_driver_library(os_obj=vm_os_obj, common_content_lib = common_content_lib_vm_obj, is_vm="yes")
            self.install_hqm_dpdk_library(os_obj=vm_os_obj, common_content_lib = common_content_lib_vm_obj, is_vm="yes")
            self._test_content_logger.end_step_logger(14, return_val=True)

            self._test_content_logger.start_step_logger(15)
            self.run_dpdk_work_load_vm(vm_name, common_content_lib = common_content_lib_vm_obj)
            self.run_dlb_work_load_vm(vm_name, common_content_lib = common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(15, return_val=True)
            self.detach_pci_device_using_dbdf_from_vm(vm_name, domain, bus, device, function)

        self._test_content_logger.end_step_logger(8, return_val=True)

        return True

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationDpdkDlbMultiVM.main() else Framework.TEST_RESULT_FAIL)
