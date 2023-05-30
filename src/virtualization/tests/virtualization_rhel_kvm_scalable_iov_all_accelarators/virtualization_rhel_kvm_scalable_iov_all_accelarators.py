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
import time
import threading
from dtaf_core.lib.dtaf_constants import Framework

from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.virtualization.dsa_common_virtualization import DsaBaseTest_virtualization
from src.lib.test_content_logger import TestContentLogger
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.virtualization.base_qat_util import BaseQATUtil
from src.lib import content_exceptions


class VirtualizationCentOsKvmSiovAllAccelarators(BaseQATUtil,VirtualizationCommon, DsaBaseTest_virtualization):
    """
    HPALM ID:16013375201
    HPALM TITLE:  CentOS-KVM-SIOV-Configure all accelerators DSA IAX QAT DLB
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Configure DSA SIOV on host and attach the mdev interface to Guest VM1 and run the workload inside Guest VM1.
    2. Configure HQM SIOV on host and attach the mdev interface to Guest VM2 and run the workload inside Guest VM2.
    3. Configure QAT SIOV on host and attach the mdev interface to Guest VM3 and run the workload inside Guest VM3
    4. Configure IAX SIOV on host and attach the mdev interface to Guest VM4 and run the workload inside Guest VM4
    """
    BIOS_CONFIG_FILE = "virtualization_centos_kvm_siov_dsa_iax_cross_socket_topology_bios.cfg"

    NUMBER_OF_VMS = 1
    VM = [VMs.CENTOS]*1
    VM_TYPE = "CENTOS"
    DSA_MDEV = []
    IAX_MDEV = []
    TEST_CASE_ID = ["P16013375201", "CentOS-KVM-SIOV-Configure all accelerators DSA IAX QAT DLB"]
    STORAGE_VOLUME = ["/home"]
    list_of_linux_os_rm_commands = [r"yum remove -y libuuid-devel;echo y",
                                    r"yum remove -y kmod-devel;echo y",
                                    r"yum remove -y libudev-devel;echo y",
                                    r"yum remove -y xmlto*;echo y",
                                    r"yum remove -y systemd-devel;echo y",
                                    r"yum remove -y json-c-devel"]

    list_of_linux_os_commands = [r"yum install -y libuuid-devel;echo y",
                                 r"yum install -y kmod-devel;echo y",
                                 r"yum install -y libudev-devel;echo y",
                                 r"yum install -y xmlto*;echo y",
                                 r"yum install -y systemd-devel;echo y",
                                 r"yum install -y json-c-devel --allowerasing"]

    STEP_DATA_DICT = {1: {'step_details': 'Configure DSA SIOV on host and attach the mdev interface to Guest '
                                          'VM1 and run the workload inside Guest VM1. ',
                          'expected_results': 'Should be successfull'},
                     2:  {'step_details': 'Configure IAX SIOV on host and attach the mdev interface to Guest'
                                          'VM4 and run the workload inside Guest VM4',
                          'expected_results': 'Should be successfull'},
                     3:  {'step_details': 'Configure QAT SIOV on host and attach the mdev interface to Guest'
                                          'VM3 and run the workload inside Guest VM3',
                          'expected_results': 'Should be successfull'},
                     4:  {'step_details': 'Configure HQM SIOV on host and attach the mdev interface to Guest'
                                           'VM2 and run the workload inside Guest VM2',
                           'expected_results': 'Should be successfull'},
                    }


    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of DsaLibInstall
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.dsa_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(VirtualizationCentOsKvmSiovAllAccelarators, self).__init__(test_log, arguments, cfg_opts,
                                                                                   self.dsa_bios_enable)
        self._cfg_opts = cfg_opts
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)


    def prepare(self):
        # type: () -> None
        """
        preparing the setup by enabling VTd, Interrupt remapping, VMX, PCIe ENQCMD /ENQCMDS  and verify all kobs are
        enabled successfully
        """
        super(VirtualizationCentOsKvmSiovAllAccelarators, self).prepare()
        self._vm_provider.create_bridge_network("virbr0")

    def execute(self):
        """
        This function execute
        :return: True if test case pass else fail
        """

        release_cmd = "uname -a | grep spr"
        output = self.os.execute(release_cmd, self._command_timeout)
        uname_output = output.stdout

        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)

        # Enabling the Intel iommu in kernel
        self._test_content_logger.start_step_logger(2)
        # Enabling the Intel iommu in kernel
        self._test_content_logger.start_step_logger(2)
        if not self.enable_intel_iommu_by_kernel():
            raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")
        self._test_content_logger.end_step_logger(2, return_val=True)
        self.get_yum_repo_config(self.os, self._common_content_lib, os_type="centos")
        # Installing the dependency packages
        self._log.info("Installing dependency package for CentOS: {}".format(self.INSTALL_DEPENDENCY_PACKAGE))
        for command_line in self.list_of_linux_os_rm_commands:
            cmd_result = self.os.execute(command_line, self._command_timeout)
            if cmd_result.cmd_failed():
                log_error = "Failed to run command '{}' with " \
                            "return value = '{}' and " \
                            "std_error='{}'..".format(command_line, cmd_result.return_code, cmd_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)
            else:
                self._log.info("The command '{}' executed successfully..".format(command_line))

        self._log.info("Installing dependency package for CentOS: {}".format(self.INSTALL_DEPENDENCY_PACKAGE))

        for command_line in self.list_of_linux_os_commands:
            cmd_result = self.os.execute(command_line, self._command_timeout)
            if cmd_result.cmd_failed():
                log_error = "Failed to run command '{}' with " \
                            "return value = '{}' and " \
                            "std_error='{}'..".format(command_line, cmd_result.return_code, cmd_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)
            else:
                self._log.info("The command '{}' executed successfully..".format(command_line))

        self._log.info("Installing dependency package for CentOS: {}".format(self.INSTALL_DEPENDENCY_PACKAGE))

        if 'spr' in uname_output:
            self._log.info("The system is in SPR, hence utilty is part of the BKC")
            self._install_collateral.install_kernel_dsa_rpm_on_linux()
        else:
            self._install_collateral.install_verify_accel_config()
            # lsmod grep command for idxd device
            self.check_idxd_device()
            # Determine the dsa device state
            self.determine_device_state()
            # DSA device basic check
            self.driver_basic_check()
            # Check DSA devices
            self.verify_dsa_driver_directory()
            self._test_content_logger.start_step_logger(3)


        spr_dir_path = self._install_collateral.get_spr_path()
        self._install_collateral.configure_dsa(spr_dir_path)
        self._install_collateral.configure_iax(spr_dir_path)

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
        mdev_per_socket = 4
        # Configure QAT device
        total_mdev = socket * mdev_per_socket
        cpus_per_vm = int(total_cpus / total_mdev)
        vqat_per_qat_dev = 4
        # Configure QAT device
        self.install_check_qat_status(qat_type="siov", target_type="host",
                                      common_content_object=self._common_content_lib)
        for index in range(total_mdev):
            self.update_qat_siov_in_file(vqat_per_qat_dev, "/etc/4xxx_dev{}.conf".format(index),
                                         self._common_content_lib)
        self.stop_qat_service(self._common_content_lib)
        self.start_qat_service(self._common_content_lib)
        bdf = []
        sym = []
        asym = []
        dc = []
        uuid_sym = []
        uuid_asym = []
        uuid_dc = []
        total_dev_sym_and_dc = 0
        bdf_sym_asym_dc_dict = self.get_qat_device_details(self._common_content_lib)
        for index in range(len(bdf_sym_asym_dc_dict['bdf'])):
            bdf.append((bdf_sym_asym_dc_dict['bdf'])[index])

            number_of_dev, dev_uuid_list = self.create_qat_devices(bdf[index], (bdf_sym_asym_dc_dict['sym'])[index],
                                                                   "sym", self._common_content_lib)
            uuid_sym.append(dev_uuid_list)
            # update the total no of vqat device in system
            sym.append(number_of_dev)
            total_dev_sym_and_dc = total_dev_sym_and_dc + number_of_dev
            (bdf_sym_asym_dc_dict['sym'])[index] = number_of_dev

            number_of_dev, dev_uuid_list = self.create_qat_devices(bdf[index], (bdf_sym_asym_dc_dict['asym'])[index],
                                                                   "asym", self._common_content_lib)
            uuid_asym.append(dev_uuid_list)
            # update the total no of vqat device in system
            asym.append(number_of_dev)
            (bdf_sym_asym_dc_dict['asym'])[index] = number_of_dev
            # total_dev_sym_and_dc = total_dev_sym_and_dc + number_of_dev

            number_of_dev, dev_uuid_list = self.create_qat_devices(bdf[index], (bdf_sym_asym_dc_dict['dc'])[index],
                                                                   "dc", self._common_content_lib)
            uuid_dc.append(dev_uuid_list)
            # update the total no of vqat device in system
            dc.append(number_of_dev)
            (bdf_sym_asym_dc_dict['dc'])[index] = number_of_dev
            total_dev_sym_and_dc = total_dev_sym_and_dc + number_of_dev

        vqat_start_index_socket0 = 0
        vqat_start_index_socket1 = int(total_dev_sym_and_dc / socket)
        # Configure DLB device
        self.verify_hqm_dlb_kernel()
        self.install_hqm_driver_library()
        self.install_hqm_dpdk_library()

        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index) + "p"
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on CentOS.".format(vm_name))


        for index, vm_name in enumerate(self.LIST_OF_VM_NAMES):
            # create with default values
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_parallel="yes", vm_create_async=True, mac_addr=True, pool_id=free_storage_pool,
                                   pool_vol_id=None, cpu_core_list=None)
            self._log.info(" Create VM:{} on CentOS Called.".format(vm_name))

        self.create_vm_wait()
        time.sleep(900)
        uuid_for_vm_list = []
        used_vqat_num_vm = 0
        uuid_sym_temp = uuid_sym
        uuid_dc_temp = uuid_dc
        time.sleep(600)

        vm_index = 0
        for index, vm_name in zip(range(self.NUMBER_OF_VMS), self.LIST_OF_VM_NAMES):
            if index == 0:
                self._test_content_logger.start_step_logger(1)
                vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
                common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
                install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)
                grub_param = "intel_iommu=on,sm_on iommu=on no5lvl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce"
                self.enable_intel_iommu_by_kernel_in_vm(vm_name, grub_param=grub_param,
                                                        common_content_lib=common_content_lib_vm)
                self.reboot_linux_vm(vm_name)
                time.sleep(200)

                self.enable_proxy_vm(common_content_lib_vm)

                for command_line in self.list_of_linux_os_rm_commands:
                    cmd_result = vm_os_obj.execute(command_line, self._command_timeout)
                    if cmd_result.cmd_failed():
                        log_error = "Failed to run command '{}' with " \
                                    "return value = '{}' and " \
                                    "std_error='{}'..".format(command_line, cmd_result.return_code, cmd_result.stderr)
                        self._log.error(log_error)
                        raise RuntimeError(log_error)
                    else:
                        self._log.info("The command '{}' executed successfully..".format(command_line))

                for command_line in self.list_of_linux_os_commands:
                    cmd_result = vm_os_obj.execute(command_line, self._command_timeout)
                    if cmd_result.cmd_failed():
                        log_error = "Failed to run command '{}' with " \
                                    "return value = '{}' and " \
                                    "std_error='{}'..".format(command_line, cmd_result.return_code, cmd_result.stderr)
                        self._log.error(log_error)
                        raise RuntimeError(log_error)
                    else:
                        self._log.info("The command '{}' executed successfully..".format(command_line))
                    self._log.info("DSA dependencies package installation on VM was successfull...")

                if 'spr' in uname_output:
                    self._log.info("The system is in SPR, hence utilty is part of the BKC")
                    self._install_collateral.install_kernel_dsa_rpm_on_linux(is_vm="yes")
                else:
                    install_collateral_vm_obj.install_and_verify_accel_config_vm(common_content_lib_vm)

                uuid = self.get_dsa_uuid()
                uuid_list = uuid[index]
                self.DSA_MDEV.append(uuid_list)
                self.attach_mdev_instance_to_vm(vm_name, uuid_list)
                spr_file_path = self._install_collateral.get_spr_path(common_content_lib_vm)
                time.sleep(45)
                dsa_thread = threading.Thread(target=self._install_collateral.run_workload_on_vm,
                                              args=(spr_file_path,common_content_lib_vm,
                                              vm_os_obj))
                dsa_thread.start()
                self._test_content_logger.end_step_logger(1, True)

            if index == 1:
                self._test_content_logger.start_step_logger(2)
                self._log.info("Run workload for IAX")
                vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
                common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
                install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)
                grub_param = "intel_iommu=on,sm_on iommu=on no5lvl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce"
                self.enable_intel_iommu_by_kernel_in_vm(vm_name, grub_param=grub_param,
                                                        common_content_lib=common_content_lib_vm)
                self.reboot_linux_vm(vm_name)
                time.sleep(200)
                self.enable_proxy_vm(common_content_lib_vm)

                for command_line in self.list_of_linux_os_rm_commands:
                    cmd_result = vm_os_obj.execute(command_line, self._command_timeout)
                    if cmd_result.cmd_failed():
                        log_error = "Failed to run command '{}' with " \
                                    "return value = '{}' and " \
                                    "std_error='{}'..".format(command_line, cmd_result.return_code, cmd_result.stderr)
                        self._log.error(log_error)
                        raise RuntimeError(log_error)
                    else:
                        self._log.info("The command '{}' executed successfully..".format(command_line))

                for command_line in self.list_of_linux_os_commands:
                    cmd_result = vm_os_obj.execute(command_line, self._command_timeout)
                    if cmd_result.cmd_failed():
                        log_error = "Failed to run command '{}' with " \
                                    "return value = '{}' and " \
                                    "std_error='{}'..".format(command_line, cmd_result.return_code, cmd_result.stderr)
                        self._log.error(log_error)
                        raise RuntimeError(log_error)
                    else:
                        self._log.info("The command '{}' executed successfully..".format(command_line))
                    self._log.info("DSA dependencies package installation on VM was successfull...")

                if 'spr' in uname_output:
                    self._log.info("The system is in SPR, hence utilty is part of the BKC")
                    self._install_collateral.install_kernel_dsa_rpm_on_linux(is_vm="yes")
                else:
                    install_collateral_vm_obj.install_and_verify_accel_config_vm(common_content_lib_vm)

                self._log.info("IAX dependencies package installation on VM was successfull...")
                uuid = self.get_iax_uuid()
                uuid_list = uuid[vm_index]
                self.IAX_MDEV.append(uuid_list)
                self.attach_mdev_instance_to_vm(vm_name, uuid_list)
                spr_dir_path = self._install_collateral.get_spr_path(common_content_lib_vm)
                time.sleep(45)
                self._install_collateral.run_iax_workload_on_vm(spr_dir_path, common_content_lib_vm, vm_os_obj)
                iax_thread = threading.Thread(target=self._install_collateral.run_dma_test,
                                             args=(common_content_lib_vm, vm_os_obj))
                iax_thread.start()
                self._test_content_logger.end_step_logger(2, True)

            if index == 2:
                self._test_content_logger.start_step_logger(3)
                self._log.info("Run workload for HQM")
                vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
                common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
                self.get_yum_repo_config(vm_os_obj, common_content_lib_vm)
                grub_param = "intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode='modern',device-iotlb=on,aw-bits=48 intel_iommu=on,sm_on ats_with_iommu_swizzle iommu=pt no5lvl"
                self.enable_intel_iommu_by_kernel_vm(vm_os_obj, common_content_lib_vm, grub_param)
                self.reboot_linux_vm(vm_name)
                time.sleep(45)
                self.verify_hqm_dlb_kernel(common_content_lib_vm)
                self.install_hqm_driver_library(os_obj=vm_os_obj, common_content_lib=common_content_lib_vm, is_vm="yes")
                self.install_hqm_dpdk_library(os_obj=vm_os_obj, common_content_lib=common_content_lib_vm, is_vm="yes")
                uuid, domain, bus, device, function = self._vm_provider.create_mdev_dlb2_instance(vm_index)
                self.attach_pci_device_using_dbdf_to_vm(vm_name, domain, bus, device, function)

                hqm_thread = threading.Thread(target=self.run_dlb_work_load_vm,
                                           args=(vm_name, common_content_lib_vm))
                hqm_thread.start()
                time.sleep(45)
                self.detach_pci_device_using_dbdf_from_vm(vm_name, domain, bus, device, function)

                self._test_content_logger.end_step_logger(3, True)

            if index == 3:
                self._test_content_logger.start_step_logger(4)

                vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
                common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
                self.get_yum_repo_config(vm_os_obj, common_content_lib_vm)
                grub_param = "intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode='modern',device-iotlb=on,aw-bits=48 intel_iommu=on,sm_on ats_with_iommu_swizzle iommu=pt no5lvl"
                self.enable_intel_iommu_by_kernel_vm(vm_os_obj, common_content_lib_vm, grub_param)
                self.reboot_linux_vm(vm_name)
                time.sleep(45)
                uuid_for_vm = ""
                qat_dev_index = 0
                vqat_start_index = vqat_start_index_socket0
                vqat_end_index = vqat_start_index_socket1

                sym_dev_used = 0
                dc_dev_used = 0

                for vqat_dev_no in range(vqat_start_index, vqat_end_index):
                    if sym_dev_used > (bdf_sym_asym_dc_dict['sym'])[qat_dev_index]:
                        if dc_dev_used > (bdf_sym_asym_dc_dict['dc'])[qat_dev_index]:
                            qat_dev_index = qat_dev_index + 1
                            sym_dev_used = 0
                            dc_dev_used = 0
                            uuid_for_vm = uuid_sym_temp[qat_dev_index][sym_dev_used]
                            uuid_sym_temp[qat_dev_index][sym_dev_used] = ""
                            sym_dev_used = sym_dev_used + 1
                            if uuid_for_vm != "":
                                used_vqat_num_vm = used_vqat_num_vm + 1
                                break
                        else:
                            uuid_for_vm = uuid_dc_temp[qat_dev_index][dc_dev_used]
                            uuid_dc_temp[qat_dev_index][dc_dev_used] = ""
                            dc_dev_used = dc_dev_used + 1
                            if uuid_for_vm != "":
                                used_vqat_num_vm = used_vqat_num_vm + 1
                                break
                    else:
                        uuid_for_vm = uuid_sym_temp[qat_dev_index][sym_dev_used]
                        uuid_sym_temp[qat_dev_index][sym_dev_used] = ""
                        sym_dev_used = sym_dev_used + 1
                        if uuid_for_vm != "":
                            used_vqat_num_vm = used_vqat_num_vm + 1
                            break
                uuid_for_vm_list.append(uuid_for_vm)
                self.attach_vqat_instance_to_vm(vm_name, uuid_for_vm)
                self.install_check_qat_status(vm_name=vm_name, os_obj=vm_os_obj,
                                              qat_type="siov", target_type="guest",
                                              common_content_object=common_content_lib_vm, is_vm="yes")
                self.get_qat_device_status_adfctl(qat_dev_index, common_content_lib_vm)
                self.set_qat_device_up_adfctl(qat_dev_index, common_content_lib_vm)
                self.check_vqat_device_type_attached(common_content_lib_vm)
                time.sleep(45)
                qat_thread = threading.Thread(target=self.run_qat_workload,
                                              args=(common_content_lib_vm))
                qat_thread.start()
                self._test_content_logger.end_step_logger(4, True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationCentOsKvmSiovAllAccelarators, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationCentOsKvmSiovAllAccelarators.main()
             else Framework.TEST_RESULT_FAIL)
