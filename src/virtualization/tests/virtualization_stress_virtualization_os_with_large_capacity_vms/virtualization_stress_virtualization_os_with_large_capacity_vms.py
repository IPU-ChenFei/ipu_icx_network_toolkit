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
import threading

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.dtaf_content_constants import Mprime95ToolConstant
from src.virtualization.tests.ilvss_util import ilvssutil


class VirtualizationStressOsLargeCapacityVms(ilvssutil, VirtualizationCommon):
    """
    Phoenix ID: 18014074835
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Install virt-install if not present.
    2. Copy RHEL ISO image to SUT under '/var/lib/libvirt/images'.
    4. Create VM.
    5. Verify VM is running.
    """
    NUMBER_OF_VMS = [VMs.RHEL]*2
    VM_TYPE = "RHEL"
    STORAGE_VOLUME = ["/home"]
    BIOS_CONFIG_FILE = "virtualization_stress_virtualization_os_with_large_capacity_vms.cfg"
    TOOL_RUN_TIME = 7200
    ARGUMENT_IN_DICT = {"Join Gimps?": "N", "Your choice": "15", "Number of torture test threads to run": "0",
                        "Type of torture test to run ": "2", "Customize settings": "N", "Run a weaker torture test":
                            "N", "Accept the answers above?": "Y"}
    UNEXPECTED_EXPECT = ["Your choice", "Join Gimps?", "Customize settings", "Run a weaker torture test"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully'"},
        2: {'step_details': "Enable INTEL_IOMMU=on on SUT",
            'expected_results': "Successfully enabled INTEL_IOMMU=on on SUT"},
        3: {'step_details': "Create RHEL VM's",
            'expected_results': "VM's Created Successfully"},
        4: {'step_details': "Install ILVSS and PTU tool from artifactory on all VMs",
            'expected_results': "Successfully installed ILVSS and PTU tool on VM"},
        5: {'step_details': "Start  tool on all VM",
            'expected_results': "VM tool started successfully on all VM"},
        6: {'step_details': "Verify VM is working or not",
            'expected_results': "VM Verified successfully"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationStressOsLargeCapacityVms object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationStressOsLargeCapacityVms, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(test_log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):  # type: () -> None
        self._test_content_logger.start_step_logger(1)
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        super(VirtualizationStressOsLargeCapacityVms, self).prepare()
        self._vm_provider.create_bridge_network("virbr0")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. create VM
        2. check VM is functioning or not
        3. Install stress tool and start stress
        4. Verify VM is functioning or not after stress completed
        """
        self._test_content_logger.start_step_logger(2)
        if not self.enable_intel_iommu_by_kernel():
            raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")
        self._install_collateral.screen_package_installation()
        self._test_content_logger.end_step_logger(2, True)
        self._test_content_logger.start_step_logger(3)
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)
        socket, core_socket, threads_per_core = self.get_cpu_core_info()
        total_cpus = socket * core_socket * threads_per_core
        maximum_cpu_per_vm = int(total_cpus/3)
        total_cpu_per_vm = int(maximum_cpu_per_vm-5)
        self._log.info("Total CPU assigned to each VM {}".format(total_cpu_per_vm))
        total_mem = self._vm_provider.get_sut_mem_info()
        maximum_mem_per_vm = int(total_mem/3)
        total_mem_per_vm = int(maximum_mem_per_vm-1000)
        self._log.info("1/3rd of VM memory count {}MB".format(total_mem_per_vm))
        available_disk_size = self._vm_provider.find_storage_pool_capacity_size(self.LIST_OF_POOL[0])
        max_vm_storage = int((available_disk_size/1024)/1024)
        total_vm_storage = int((max_vm_storage/1024)/3)
        self._log.info("size {}GB".format(total_vm_storage))
        for index in range(len(self.NUMBER_OF_VMS)):
            vm_name = self.NUMBER_OF_VMS[index] + "_" + str(index)
            self._log.info(" Creating VM:{} on CentOS".format(vm_name))
            self._vm_provider.destroy_vm(vm_name)
            self.LIST_OF_VM_NAMES.append(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL, self.VM_TYPE)
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_parallel="yes", vm_create_async=True,
                                   mac_addr=True, pool_id=free_storage_pool, pool_vol_id=None,
                                   cpu_core_list=None, nw_bridge="virbr0")
        self.create_vm_wait()
        time.sleep(self.VM_WAIT_TIME)
        self._test_content_logger.end_step_logger(3, True)
        self._test_content_logger.start_step_logger(4)
        for vm_name in self.LIST_OF_VM_NAMES:
            vm_location = self.find_vm_storage_location(vm_name)
            self._log.info("vm location {}".format(vm_location))
            self._vm_provider.reconfigure_memory_on_vm(vm_name, maximum_mem_per_vm, total_mem_per_vm)
            self._vm_provider.reconfigure_cpu_on_vm(vm_name, maximum_cpu_per_vm, total_cpu_per_vm)
            self._vm_provider.reconfigure_disksize_on_vm(vm_name, vm_location, total_vm_storage)
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, os_type="centos",machine_type="vm")
            install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)
            install_collateral_vm_obj.screen_package_installation()
            self.install_ilvss(common_content_lib_vm_obj, vm_os_obj)
            self.install_prime95(self.VM_TYPE, vm_os_obj, common_content_lib_vm_obj)
            install_collateral_vm_obj.copy_collateral_script(Mprime95ToolConstant.MPRIME95_LINUX_SCRIPT_FILE,
                                                             self.ROOT_PATH)
        self._test_content_logger.end_step_logger(4, True)
        ilvss_thread = []
        prime_thread = []
        self._test_content_logger.start_step_logger(5)
        for vm_name in self.LIST_OF_VM_NAMES:
            ilvss_runtime = self.TOOL_RUN_TIME/60
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            ilvss_stress = threading.Thread(target=self.execute_vss_memory_test_package,
                                            args=(vm_os_obj, common_content_lib_vm_obj, ilvss_runtime))
            ilvss_thread.append(ilvss_stress)
            prime_stress = threading.Thread(target=self.configure_and_execute_mprime_tool, args=(vm_os_obj,))
            prime_thread.append(prime_stress)
        for ilvss_workload, prime_workload in zip(ilvss_thread, prime_thread):
            ilvss_workload.start()
            prime_workload.start()
        time.sleep(self.TOOL_RUN_TIME)
        self._test_content_logger.end_step_logger(5, True)
        self._test_content_logger.start_step_logger(6)
        for vm_name in self.LIST_OF_VM_NAMES:
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self.wait_for_vss_to_complete(self.ILVSS_MODE, vm_os_obj)
            self.verify_vss_logs(self.LOG_NAME, vm_os_obj, common_content_lib_vm_obj)
            self.kill_stress_tool(vm_os_obj, stress_tool_name=Mprime95ToolConstant.MPRIME_TOOL_NAME,
                                  stress_test_command="./" + Mprime95ToolConstant.MPRIME_TOOL_NAME)
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
        self._test_content_logger.end_step_logger(6, True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationStressOsLargeCapacityVms, self).cleanup(return_status)

    def configure_and_execute_mprime_tool(self, vm_os_obj):
        """

        This method install and validate prime stress linux

        :param: vm_os_obj: VM executable os object
        :raise: if non zero errors raise content_exceptions.TestFail
        """
        common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
        core_count = common_content_lib_vm_obj.get_core_count_from_os()[0]
        self._log.debug('Number of cores %d', core_count)
        if self.ARGUMENT_IN_DICT.get("Number of torture test threads to run", None):
            self.ARGUMENT_IN_DICT["Number of torture test threads to run"] = \
                str(core_count)
        (unexpected_expect, successfull_test) = \
            self.execute_mprime(vm_os_obj, arguments=self.ARGUMENT_IN_DICT, execution_time=self.TOOL_RUN_TIME,
                                cmd_dir=self.ROOT_PATH)
        self._log.debug(unexpected_expect)
        self._log.debug(successfull_test)
        if len(successfull_test) != core_count:
            raise content_exceptions.TestFail('Torture Test is not started on {} threads'.format(core_count))
        invalid_expect = []
        for expect in unexpected_expect:
            if expect not in self.UNEXPECTED_EXPECT:
                invalid_expect.append(expect)
        self._log.debug(invalid_expect)
        if invalid_expect:
            raise content_exceptions.TestFail('%s are Mandatory options for torture Test' % invalid_expect)
        self.check_app_running(vm_os_obj, app_name=Mprime95ToolConstant.MPRIME_TOOL_NAME,
                               stress_test_command="./" + Mprime95ToolConstant.MPRIME_TOOL_NAME)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationStressOsLargeCapacityVms.main()
             else Framework.TEST_RESULT_FAIL)
