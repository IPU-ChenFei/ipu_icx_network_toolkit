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
from dtaf_core.lib.dtaf_constants import Framework
from src.provider.vm_provider import VMProvider
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.test_content_logger import TestContentLogger
from src.provider.vm_provider import VMs
from src.lib.install_collateral import InstallCollateral
from src.lib.common_content_lib import CommonContentLib
from src.provider.mlc_provider import MlcProvider

class VirtualizationCentOSNestedVirtualizationRunMLCWLd(VirtualizationCommon):
    """
    Phoenix ID: P16014653168-VirtualizationCentOSNestedVirtualizationRunMLCWLd
    The purpose of this test case is making sure the creation of VM in VM guests on KVM using Virt-Manager.
    1. Install virt-install if not present.
    2. Copy CENT OS Image to SUT under ./var/lib/libvirt/images'
    3. Create First level VM and verify if VM is running
    4. Copy RHEL ISO image to SUT under '/var/lib/libvirt/images'.
    5. Create Second level nested VM and verify if VM is running.
    6. Wait for 2 hours
    7. Verify if first level and second level VMs are running, Run MLC Workload.
    8. Cleanup all VM resources
    """
    TEST_CASE_ID = ["P16014653168", "VirtualizationCentOSNestedVirtualizationRunMLCWLd"]
    STEP_DATA_DICT = {
        1: {'step_details': "Create the VM machine names.",
            'expected_results': "VM machine names created and saved in list"},
        2: {'step_details': "Generate Virtual machines on SUT",
            'expected_results': "Virtual machines created successfully"},
        3: {'step_details': "Create the Nested VM machine names.",
            'expected_results': "Nested VM machine names created and saved in list."},
        4: {'step_details': "Generate Nested Virtual machines on SUT.",
            'expected_results': "Nested Virtual machines created successfully."},
        5: {'step_details': "Wait for 2 hours.",
            'expected_results': "Waited for 2 hours successfully."},
        6: {'step_details': "Check the VM and nested VM.",
            'expected_results': "VM and nested chcked successfully and found stable."},
        7: {'step_details': "Destroy the VMs and nested VMs.",
            'expected_results': "VMs and nested VMs destroyed successfully."},
    }
    NUMBER_OF_VMS = 1
    VM = [VMs.CENTOS] * 1
    VM_TYPE = "CENTOS"
    VMN = [VMs.CENTOS] * 1
    VMN_TYPE = "CENTOS"
    TC_ID = ["P16014653168-VirtualizationCentOSNestedVirtualizationRunMLCWLd"]
    TEST_TIME_SLEEP = 7200
    STORAGE_VOLUME = ["/home"]
    MLC_LOG_FILE_HOST = "mlc_log_host.log"
    MLC_LOG_FILE_VM_L1 = "mlc_log_host_l1.log"
    MLC_LOG_FILE_VM_L2 = "mlc_log_host_l2.log"
    BIOS_CONFIG_FILE = "virt_kvm_nested_virt_run_mlcml_biosknobs.cfg"
    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationCentOSNestedVirtualizationRunMLCWLd object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationCentOSNestedVirtualizationRunMLCWLd, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._cfg_opt_tc = cfg_opts
        self._arg_tc = arguments
        self._test_log_tc = test_log

    def execute_mlc_test(self, os_obj, exec_time, common_content_obj=None):
        """
        Run MLC test
        """
        if common_content_obj is None:
            common_content_obj = self._common_content_lib
        mlc_provider = MlcProvider.factory(self._test_log_tc, os_obj=os_obj, cfg_opts=self._cfg_opt_tc)
        common_content_obj.execute_sut_cmd("chmod +x mlc", "Assigning executable privledges ",
                                                 self._command_timeout, self._mlc_provider.mlc_path)
        mlc_provider.execute_mlc_test(" ", self.MLC_LOG_FILE_HOST)

    def prepare(self):
        # self.bios_util.load_bios_defaults()
        # self.bios_util.set_bios_knob(bios_config_file=self.BIOS_CONFIG_FILE)
        # self.bios_util.verify_bios_knob(bios_config_file=self.BIOS_CONFIG_FILE)
        # self._log.info("Bios knobs setting done")
        self._vm_provider.create_bridge_network("virbr0")
        self._log.info("VirBr0 created on SUT")

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

        # mlc_thread_host = threading.Thread(target=self.execute_mlc_test,
        #                                    args=(self.os, self.exec_time, None))
        # mlc_thread_host.start()

        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)

        self._common_content_lib = CommonContentLib(self._log, self.os, self._cfg_opt_tc)
        self.get_yum_repo_config(self.os, self._common_content_lib,os_type="centos")
        self._test_content_logger.start_step_logger(1)
        # for index in range(self.NUMBER_OF_VMS):
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on CentOS.".format(vm_name))
        self._test_content_logger.end_step_logger(1, True)

        vm_sut_obj_list = []
        self._test_content_logger.start_step_logger(2)
        mac_index = 0
        # extra_disk = 10 [iso file] + 7 [vm disk space]+ 7 [other for VM ]
        extra_disk = 56
        # for vm_name in self.LIST_OF_VM_NAMES:
        for vm_name in self.LIST_OF_VM_NAMES:
            # create with default values
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
            self.create_vm_pool_nested(vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True,
                                       pool_id=free_storage_pool, extra_disk_space=extra_disk, nesting_level=None)
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            self._log.info(" Created VM:{} on RHEL.".format(vm_name))
            # create VM os object
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm_obj = CommonContentLib(self._test_log_tc, vm_os_obj, self._cfg_opt_tc)
            install_collateral_vm_obj = InstallCollateral(self._test_log_tc, vm_os_obj, self._cfg_opt_tc)
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, os_type="centos", machine_type="vm")
            install_collateral_vm_obj.screen_package_installation()

        self._test_content_logger.end_step_logger(2, True)
        virtualization_obj_vm_list = []
        vm_nested_vm_obj_list = []
        for index, each_vm_obj, l1_vm_name in zip(range(len(self.LIST_OF_VM_NAMES)), vm_sut_obj_list, self.LIST_OF_VM_NAMES):
            self._test_content_logger.start_step_logger(3)
            # vm_provider = VMProvider.factory(self._test_log_tc, self._cfg_opt_tc, each_vm_obj)
            virtualization_obj_vm = VirtualizationCommon(self._log, self._arg_tc, self._cfg_opt_tc, os_obj = each_vm_obj)
            virtualization_obj_vm_list.append(virtualization_obj_vm)
            for index_nested in range(self.NUMBER_OF_VMS):
                # Creates VM names dynamically according to the OS and its resources
                vm_name_nested = self.VMN[index_nested] + "_" + str(index) + "_" + str(index_nested)
                self.LIST_OF_NESTED_VM_NAMES.append(vm_name_nested)
                self._log.info(" NESTED VM:{} on CENTOS.".format(vm_name_nested))
            self._test_content_logger.end_step_logger(3, True)

            self._test_content_logger.start_step_logger(4)

            for vm_name_nested in self.LIST_OF_NESTED_VM_NAMES:
                # create with default values
                # free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                #                                                                   self.VMN_TYPE)
                # self._log.info("Pool with Storage {}".format(free_storage_pool))
                virtualization_obj_vm._vm_provider.destroy_vm(vm_name_nested)
                virtualization_obj_vm._vm_provider.create_bridge_network("virbr0", vm_name=l1_vm_name)
                self.reboot_linux_vm(l1_vm_name)
                time.sleep(5)
                virtualization_obj_vm.create_vm_pool_nested(vm_name_nested, self.VMN_TYPE, vm_create_async=None,
                                                            mac_addr=True, pool_id=None, extra_disk_space=None,
                                                            nesting_level="l2")

                virtualization_obj_vm.verify_vm_functionality(vm_name_nested, self.VMN_TYPE)
                virtualization_obj_vm._vm_provider.check_if_vm_exist(vm_name_nested)
                vm_nested_os_obj = self.create_vm_host(vm_name_nested, self.VMN_TYPE)
                vm_nested_vm_obj_list.append(vm_nested_os_obj)
                common_content_lib_vm_nested_obj = CommonContentLib(self._test_log_tc, vm_nested_os_obj, self._cfg_opt_tc)
                install_collateral_vm_nested_obj = InstallCollateral(self._test_log_tc, vm_nested_os_obj, self._cfg_opt_tc)
                self._log.info(" Created NESTED VM:{} on RHEL.".format(vm_name_nested))
                mlc_thread_vm_l2 = threading.Thread(target=self.execute_mlc_test,
                                                    args=(vm_nested_os_obj, self.exec_time, common_content_lib_vm_nested_obj))
                mlc_thread_vm_l2.start()

            mlc_thread_vm_l1 = threading.Thread(target=self.execute_mlc_test,
                                               args=(vm_os_obj, self.exec_time, common_content_lib_vm_obj))
            mlc_thread_vm_l1.start()
            self._test_content_logger.end_step_logger(4, True)

            mlc_thread_host = threading.Thread(target=self.execute_mlc_test,
                                                args=(self.os, self.exec_time, None))
            mlc_thread_host.start()
            # wait and check after 2 hours is all VMs are fine
            self._test_content_logger.start_step_logger(5)
            time.sleep(self.TEST_TIME_SLEEP)
            mlc_thread_vm_l2.join()
            mlc_thread_vm_l1.join()
            mlc_thread_host.join()
            self._test_content_logger.end_step_logger(5, True)

            self._test_content_logger.start_step_logger(6)
            for index, vm_name_nest, virtualization_obj_vm in zip(range(len(self.LIST_OF_NESTED_VM_NAMES)),
                                                                  self.LIST_OF_NESTED_VM_NAMES, virtualization_obj_vm_list):
                # virtualization_obj_vm.verify_vm_functionality(vm_name_nested, self.VMN_TYPE)
                virtualization_obj_vm._vm_provider.check_if_vm_exist(vm_name_nest)

            for vm_name in self.LIST_OF_VM_NAMES:
                self.verify_vm_functionality(vm_name, self.VM_TYPE)
            self._test_content_logger.end_step_logger(6, True)

            self._test_content_logger.start_step_logger(7)
            for index, vm_name_nest, virtualization_obj_vm in zip(range(len(self.LIST_OF_NESTED_VM_NAMES)),
                                                                  self.LIST_OF_NESTED_VM_NAMES, virtualization_obj_vm_list):
                virtualization_obj_vm._vm_provider.destroy_vm(vm_name_nest)

            for vm_name in self.LIST_OF_VM_NAMES:
                self._vm_provider.destroy_vm(vm_name)
            self._test_content_logger.end_step_logger(7, True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationCentOSNestedVirtualizationRunMLCWLd, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationCentOSNestedVirtualizationRunMLCWLd.main()
             else Framework.TEST_RESULT_FAIL)
