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
from src.lib.install_collateral import InstallCollateral
from src.lib.common_content_lib import CommonContentLib
from src.provider.vm_provider import VMs

class VirtualizationSIOVDLBCrossSocketTopology(VirtualizationCommon):
    """
    Phoenix ID : 16014132088
    The purpose of this test case is to validate the Cross Socket topology using SIOV DLB successfully on SUT/VM.
    Then execute DPDK and DLB workload inside host
    """
    NUMBER_OF_VMS = 2
    VM = [VMs.CENTOS] * 2
    VM_TYPE = "CENTOS"
    TEST_CASE_ID = ["P16014132088", "VirtualizationSIOVDLBCrossSocketTopology"]
    BIOS_CONFIG_FILE = "virt_siov_dlb_cross_socket_topo_bios.cfg"
    STORAGE_VOLUME = ["/home"]
    DLB_LOAD_TEST_TIME = 7200
    STEP_DATA_DICT = {
        1: {'step_details': 'Install and verify Bios knobs for DLB',
            'expected_results': 'Bios knobs installed and verified successfully'},
        2: {'step_details': 'Create the Storage Pool for VMs',
            'expected_results': 'Storage Pools created successfully'},
        3: {'step_details': 'Install and configure the yum repo config file',
            'expected_results': 'Yum repo configured successfully'},
        4: {'step_details': 'Verify the HQM/DLB in kernel',
            'expected_results': 'HQM/DLB verified and driver removed'},
        5: {'step_details': 'Install HQM and libdlb, verify it installed or not',
            'expected_results': 'HQM is installed successfully and DPDK folders are present'},
        6: {'step_details': 'Get the CPU socket, core and threads per core info',
            'expected_results': 'CPU core information retrieved'},
        7: {'step_details': 'Create the Names for VMs to be created',
            'expected_results': 'VM names created'},
        8: {'step_details': 'Start creating the VMs as per the names created',
            'expected_results': 'All VMs created with mdev devices nd dlb2 driver and libdlb'},
        9: {'step_details': 'Create the VM',
            'expected_results': 'VM creation successfully done'},
        10: {'step_details': 'Create the mdev device',
            'expected_results': 'MDEV device for dlb2 created successfully'},
        11: {'step_details': 'Attach the created mdev device to VM',
            'expected_results': 'Created mdev device attached to VM'},
        12: {'step_details': 'Create VM object and enable command line params for iommu enable',
             'expected_results': 'VM object created and enabled command line params for iommu in VM'},
        13: {'step_details': 'Verify the HQM/DLB in kernel in VM',
             'expected_results': 'HQM/DLB verified and driver removed in VM'},
        14: {'step_details': 'Install HQM and libdlb, verify it installed or not',
            'expected_results': 'HQM is installed successfully and DPDK folders are present'},
        15: {'step_details': 'Execute libdlb work load for 2 hours',
            'expected_results': 'libdlb workload executed successfully for 2 hours'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of InstallAndVerify HQM,Dpdk & run Dpdk, dlb workload inside host

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.virtualization_dpdk_dlb_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(VirtualizationSIOVDLBCrossSocketTopology, self).__init__(test_log, arguments, cfg_opts, self.virtualization_dpdk_dlb_bios_knobs)
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
        super(VirtualizationSIOVDLBCrossSocketTopology, self).prepare()
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        self._vm_provider.create_bridge_network("virbr0")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This validates the Cross Socket topology using SIOV DLB successfully on SUT/VM.
        Then execute DPDK and DLB workload inside host
        """
        """
            This function calling hqm installation and verify it is installed successfully and execute 
            DPDK and DLB in host 

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
        self.get_yum_repo_config(self.os, self._common_content_lib, os_type="centos")
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self.verify_hqm_dlb_kernel()
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        self.install_hqm_driver_library()
        self.install_hqm_dpdk_library()
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        socket, core_socket, threads_per_core = self.get_cpu_core_info()
        total_cpus = socket * core_socket * threads_per_core
        mdev_per_socket = 4
        total_mdev = socket * mdev_per_socket

        cpus_per_vm = int(total_cpus/total_mdev)
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
            end_index = (total_cpus - 1) - (vm_index * cpus_per_vm)
            # start_index = end_index - ((vm_index + 1) * cpus_per_vm) + 1
            start_index = end_index - cpus_per_vm + 1
            # cpu_list = list(range(start_index, end_index+1))
            cpu_list = "{}-{}".format(start_index, end_index)
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True, pool_id=free_storage_pool,
                                  pool_vol_id=None, cpu_core_list=cpu_list, nw_bridge="virbr0")
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            self._test_content_logger.end_step_logger(9, return_val=True)

            self._log.info(" Created VM:{} on CentOS.".format(vm_name))
            self._test_content_logger.start_step_logger(10)
            # uuid = self._vm_provider.create_mdev_dlb2_instance(vm_index)
            uuid, domain, bus, device, function = self._vm_provider.create_mdev_dlb2_instance(vm_index)
            self._test_content_logger.end_step_logger(10, return_val=True)
            self._test_content_logger.start_step_logger(11)
            # self.attach_mdev_instance_to_vm(vm_name, uuid)
            self.attach_pci_device_using_dbdf_to_vm(vm_name, domain, bus, device, function)
            self._test_content_logger.end_step_logger(11, return_val=True)

            vm_index = vm_index + 1
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
            self.verify_hqm_dlb_kernel(common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(13, return_val=True)

            self._test_content_logger.start_step_logger(14)
            self.install_hqm_driver_library(os_obj=vm_os_obj, common_content_lib = common_content_lib_vm_obj, is_vm="yes")
            self.install_hqm_dpdk_library(os_obj=vm_os_obj, common_content_lib = common_content_lib_vm_obj, is_vm="yes")
            self._test_content_logger.end_step_logger(14, return_val=True)

        self._test_content_logger.end_step_logger(8, True)

        self._log.info("Run the dlb load test for 7200 seconds in all guest VMs")

        self._test_content_logger.start_step_logger(15)
        start_time = time.time()
        seconds = self.DLB_LOAD_TEST_TIME
        while True:
            current_time = time.time()
            elapsed_time = current_time - start_time

            for index, vm_name, each_vm_obj in zip(range(len(self.LIST_OF_VM_NAMES)), self.LIST_OF_VM_NAMES, vm_sut_obj_list):
                common_content_lib_vm_obj = CommonContentLib(self._test_log, each_vm_obj, self._cfg_opt)
                self.run_dlb_work_load_vm(vm_name, common_content_lib = common_content_lib_vm_obj)

            if elapsed_time > seconds:
                self._log.info("Finished dlb load test after: " + str(int(elapsed_time)) + " seconds")
                break
        self._test_content_logger.end_step_logger(15, return_val=True)

        return True

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationSIOVDLBCrossSocketTopology.main() else Framework.TEST_RESULT_FAIL)
