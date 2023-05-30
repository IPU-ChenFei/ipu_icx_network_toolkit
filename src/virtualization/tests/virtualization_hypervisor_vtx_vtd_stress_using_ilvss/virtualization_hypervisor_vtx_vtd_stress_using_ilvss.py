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


class VirtualizationVtxVtdStressilvss(ilvssutil, VirtualizationCommon):
    """
    Phoenix ID: 18014073596
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Install virt-install if not present.
    2. Copy RHEL ISO image to SUT under '/var/lib/libvirt/images'.
    4. Create VM.
    5. Verify VM is running.
    6.Stress VM using ilvss tool
    """
    TEST_CASE_ID = ["P18014073596", "Virtualization_HyperVisor_VT-x-VT-d_Stress_using_VSS"]
    NUMBER_OF_VMS = [VMs.CENTOS]*1
    VM_TYPE = "CENTOS"
    STORAGE_VOLUME = ["/home"]
    BIOS_CONFIG_FILE = "virtualization_hypervisor_vtx_vtd_stress_using_ilvss.cfg"
    TOOL_RUN_TIME = 15   # in minutes
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully'"},
        2: {'step_details': "Enable INTEL_IOMMU=on on SUT",
            'expected_results': "Successfully enabled INTEL_IOMMU=on on SUT"},
        3: {'step_details': "Create RHEL VM's",
            'expected_results': "VM's Created Successfully"},
        4: {'step_details': "Install ILVSS from artifactory on all VMs",
            'expected_results': "Successfully installed ILVSS tool on VM"},
        5: {'step_details': "Start  tool on all VM",
            'expected_results': "VM tool started successfully on all VM"},
        6: {'step_details': "Verify VM is working or not",
            'expected_results': "VM Verified successfully"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationStressOSMinimumCapacityVms object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationVtxVtdStressilvss, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(test_log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):  # type: () -> None
        self._test_content_logger.start_step_logger(1)
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        super(VirtualizationVtxVtdStressilvss, self).prepare()
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
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, os_type="centos",machine_type="vm")
            install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)
            install_collateral_vm_obj.screen_package_installation()
            self.install_ilvss(common_content_lib_vm_obj, vm_os_obj)
        self._test_content_logger.end_step_logger(4, True)
        self._test_content_logger.start_step_logger(5)
        for vm_name in self.LIST_OF_VM_NAMES:
            #ilvss runtime should be in minutes
            ilvss_runtime = self.TOOL_RUN_TIME
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self.execute_vss_memory_test_package(vm_os_obj, common_content_lib_vm_obj, ilvss_runtime)
        time.sleep(self.TOOL_RUN_TIME * 60)
        self._test_content_logger.end_step_logger(5, True)
        self._test_content_logger.start_step_logger(6)
        for vm_name in self.LIST_OF_VM_NAMES:
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self.wait_for_vss_to_complete(self.ILVSS_MODE, vm_os_obj, run_time=self.TOOL_RUN_TIME)
            # self.verify_vss_logs(self.LOG_NAME, vm_os_obj, common_content_lib_vm_obj)
            self.verify_vss_logs_vm(self.LOG_NAME, vm_os_obj, common_content_lib_vm_obj)
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
        self._test_content_logger.end_step_logger(6, True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationVtxVtdStressilvss, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVtxVtdStressilvss.main()
             else Framework.TEST_RESULT_FAIL)
