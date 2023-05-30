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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions
from src.lib.content_artifactory_utils import ContentArtifactoryUtils
from src.lib.mlc_utils import MlcUtils


class VirtualizationKvmVirtualMachinesMemoryWorkloadsStress(VirtualizationCommon):
    """
    Phoenix ID: 16014085515
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager and run MLC test.
    1. Install virt-install if not present.
    2. Copy RHEL ISO image to SUT under '/var/lib/libvirt/images'.
    4. Create VM.
    5. Verify VM is running.
    6. Run MLC test on all VM and verify VM is running.
    """
    TEST_CASE_ID = "p16014085515"
    TEST_CASE_DETAILS = ["p16014085515", "Virtualization-KVM-Virtual-Machines-Memory-workloads-Stress"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully'"},
        2: {'step_details': "Enable INTEL_IOMMU=on on SUT",
            'expected_results': "Successfully enabled INTEL_IOMMU=on on SUT"},
        3: {'step_details': "Create CentOs VM's",
            'expected_results': "VM's Created Successfully"},
        4: {'step_details': "Enable INTEL_IOMMU=on on VM and install MLC tool from artifactory",
            'expected_results': "Successfully enabled INTEL_IOMMU=on and installed MLC tool on VM"},
        5: {'step_details': "Start MLC tol on all VM",
            'expected_results': "VM tool started successfully on all VM"},
    }

    BIOS_CONFIG_FILE = "virtualization_kvm_vm_stress_memory_bios.cfg"
    NUMBER_OF_VMS = [VMs.CENTOS] * 5
    STORAGE_VOLUME = ["/home"]
    MAC_ID = True
    VM_TYPE = "CENTOS"
    _MLC_RUNTIME = 30

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationCentOsKvmScalableIovGen4NicStress2Vm object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationKvmVirtualMachinesMemoryWorkloadsStress, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        if self.os.os_type != OperatingSystems.LINUX:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(test_log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self._mlc_utils = MlcUtils(self._log)
        self._artifactory_obj = ContentArtifactoryUtils(self._log, self.os, self._common_content_lib, cfg_opts)

    def prepare(self):
        self._test_content_logger.start_step_logger(1)
        self.bios_util.load_bios_defaults()
        self.bios_util.set_bios_knob(bios_config_file=self.BIOS_CONFIG_FILE)
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        self.bios_util.verify_bios_knob(bios_config_file=self.BIOS_CONFIG_FILE)
        self._test_content_logger.end_step_logger(1, True)
        self._vm_provider.create_bridge_network("virbr0")

    def execute(self):
        self._test_content_logger.start_step_logger(2)
        #  To check and enable intel_iommu by using grub menu
        if not self.enable_intel_iommu_by_kernel():
            raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")
        self._test_content_logger.end_step_logger(2, True)
        self._install_collateral.screen_package_installation()
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)
        vm_obj_list = []
        mlc_thread_list = []
        self._test_content_logger.start_step_logger(3)
        for index in range(len(self.NUMBER_OF_VMS)):
            vm_name = self.NUMBER_OF_VMS[index] + "_" + str(index)
            self._log.info(" Creating VM:{} on CentOS".format(vm_name))
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.NUMBER_OF_VMS[index])
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_parallel="yes", vm_create_async=True,
                                   mac_addr=True, pool_id=free_storage_pool, pool_vol_id=None,
                                   cpu_core_list=None, nw_bridge="virbr0")
        self._test_content_logger.end_step_logger(3, True)
        self.create_vm_wait()
        time.sleep(self.VM_WAIT_TIME)
        # Start MLC test in thread
        for index, vm_name in zip(range(len(self.NUMBER_OF_VMS)), self.LIST_OF_VM_NAMES):
            self._log.info("Starting mlc stress test on VM:{}".format(vm_name))
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            time.sleep(self.VM_WAIT_TIME)
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, os_type="centos",machine_type="vm")
            self._test_content_logger.start_step_logger(4)
            mlc_install_result = self.install_mlc_on_linux_vm(vm_os_obj)
            self._test_content_logger.end_step_logger(4, True)
            mlc_thread = threading.Thread(target=self.execute_mlc_test_on_vm,
                                          args=(vm_name, vm_os_obj, mlc_install_result))
            mlc_thread_list.append(mlc_thread)
            mlc_thread.start()
        time.sleep(self._MLC_RUNTIME)
        self._test_content_logger.start_step_logger(5)
        for vm_name, vm_os in zip(self.LIST_OF_VM_NAMES, vm_obj_list):
            self.stop_mlc_stress_vm(vm_name, vm_os)
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            self._log.info("Successfully tested Memory load test on VM:{}".format(vm_name))
        self._test_content_logger.end_step_logger(5, True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationKvmVirtualMachinesMemoryWorkloadsStress, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationKvmVirtualMachinesMemoryWorkloadsStress.main()
             else Framework.TEST_RESULT_FAIL)
