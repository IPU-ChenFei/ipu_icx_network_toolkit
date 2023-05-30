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

from dtaf_core.lib.dtaf_constants import Framework

from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.virtualization.dsa_common_virtualization import DsaBaseTest_virtualization
from src.lib.test_content_logger import TestContentLogger
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions


class VirtualizationCentOsKvmSiovDsaIaxCrossSocketTopology(VirtualizationCommon, DsaBaseTest_virtualization):
    """
    HPALM ID: 16014131676
    HPALM TITLE: Virtualization-CentOS-KVM-SIOV-DSA/IAX-Cross-socket-topology
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. IOMMU scalable mode need to be enabled in.
    2. Configure Work Queue DSA and IAX.
    3. Enable DSA and IAX Device
    4. Enable Workqueue and associate UUID to WQ.
    5. Create mdev and configure guests with mdev for dsa and iax.
    6. Run workload to attached device as MDEV.
    """
    BIOS_CONFIG_FILE = "virtualization_centos_kvm_siov_dsa_iax_cross_socket_topology_bios.cfg"
    NUMBER_OF_DSA_VMS = [VMs.CENTOS] * 8
    VM_TYPE = "CENTOS"
    VM = [VMs.CENTOS]

    NUMBER_OF_IAX_VM = [VMs.CENTOS]
    VM_TYPE = "CENTOS"
    VM = [VMs.CENTOS]
    VM_LOAD_TEST_TIME = 100

    LIST_OF_IAX_VM_NAMES = []
    DSA_MDEV = []
    IAX_MDEV = []
    TEST_FILE_CONTENT = "This is a Test File"
    TEST_FILE_NAME = "test.txt"
    TEST_CASE_ID = ["P16014131676", "Virtualization-CentOS-KVM-SIOV-DSA/IAX-Cross-socket-topology"]
    STORAGE_VOLUME = ["/home"]
    GRUB_PARAM = "intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode='modern',device-iotlb=on,aw-bits=48 " \
                 "intel_iommu=on,sm_on ats_with_iommu_swizzle iommu=pt no5lvl idle=poll"
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
    STEP_DATA_DICT = {1: {'step_details': 'Enable Intel VT for Directed I/O (VT-d), Interrupt Remapping, PCIe ENQCMD '
                                          '/ENQCMDS, VMX Bios and reboot, IAX = enabled, DSA = enabled ',
                          'expected_results': 'Verify the enabled BIOS'},
                      2: {'step_details': 'IOMMU scalable mode need to be enabled in.',
                          'expected_results': 'Should be successfull'},
                      3: {'step_details': 'Install the depedencies packages on the host',
                          'expected_results': 'Fail if not found the devices'},
                      4: {'step_details': 'Enable DSA and Workqueues on host',
                          'expected_results': 'Verify DSA devices should be dsa0 to dsa7 devices should be available'},
                      5: {'step_details': 'Enable Intel IOMMU paramters on VM',
                          'expected_results': 'Should be successfull'},
                      6: {'step_details': 'Install the depedencies packages on the VM',
                          'expected_results': 'Should be successfull'},
                      7: {'step_details': 'Enable Workqueue and associate UUID to WQ',
                          'expected_results': 'Should be successfull'},
                      8: {'step_details': 'Run workload to attached device as MDEV',
                          'expected_results': 'Should be successfull'},
                      9: {'step_details': 'Enable IAX and Workqueues on host',
                          'expected_results': 'Verify IAX devices should be iax0 to iax7 devices should be available'},
                      10: {'step_details': 'Enable Intel IOMMU paramters on IAX VM',
                           'expected_results': 'Should be successfull'},
                      11: {'step_details': 'Install the depedencies packages on the IAX VM',
                           'expected_results': 'Should be successfull'},
                      12: {'step_details': 'Enable Workqueue and associate UUID to WQ',
                           'expected_results': 'Should be successfull'},
                      13: {'step_details': 'Run workload to attached device as MDEV on IAX VM',
                           'expected_results': 'Should be successfull'},
                      14: {'step_details': 'Run DMA workload on all VM',
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
        super(VirtualizationCentOsKvmSiovDsaIaxCrossSocketTopology, self).__init__(test_log, arguments, cfg_opts,
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
        self._test_content_logger.start_step_logger(1)
        super(VirtualizationCentOsKvmSiovDsaIaxCrossSocketTopology, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def run_iax_workload_on_vm_2hours(self, spr_file_path, common_content_lib_vm, vm_obj, i_value=1000, j_value=10):
        """
        This function runs IAX workload on VM.

        :param : vm_os_obj : VM OS object

        :return: None
        """
        start_time = time.time()
        seconds = self.VM_LOAD_TEST_TIME
        while True:
            current_time = time.time()
            elapsed_time = current_time - start_time

            if elapsed_time > seconds:
                self._log.info("Finished stress test after: " + str(int(elapsed_time)) + " seconds")
                break
            else:
                self._log.info("Running DMA test")
                configure_wq = "./Guest_Mdev_Randomize_IAX_Conf.sh -ck"
                cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=configure_wq, cmd_str=configure_wq,
                                                                   execute_timeout=self._command_timeout,
                                                                   cmd_path=spr_file_path)
                self._log.info("Configuring workqueues {}".format(cmd_output))
                cmd_dma = "./Guest_Mdev_Randomize_IAX_Conf.sh -i {} -j {}".format(i_value, j_value)
                cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=cmd_dma, cmd_str=cmd_dma,
                                                                   execute_timeout=self._command_timeout,
                                                                   cmd_path=spr_file_path)
                self._log.info("Running IAX workload on vm and output is {}".format(cmd_output))

                cmd_check_error = "journalctl --dmesg | grep error"
                cmd_opt = vm_obj.execute(cmd_check_error, self._command_timeout)
                if len(cmd_opt.stdout) == 0:
                    self._log.info("No errors found")
                else:
                    raise RuntimeError("Errors found after running workload")


    def run_workload_on_vm_thread(self, spr_file_path,common_content_lib_vm,vm_obj):
        """
        This function runs workload on VM

        :param : vm_os_obj : VM OS object

        :return: None
        """
        start_time = time.time()
        seconds = self.VM_LOAD_TEST_TIME
        while True:
            current_time = time.time()
            elapsed_time = current_time - start_time

            if elapsed_time > seconds:
                self._log.info("Finished stress test after: " + str(int(elapsed_time)) + " seconds")
                break
            else:
                self._log.info("Running DMA test")
                configure_wq = "./Guest_Mdev_Randomize_DSA_Conf.sh -ck"
                cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=configure_wq,cmd_str=configure_wq,
                                                                   execute_timeout=self._command_timeout,
                                                                   cmd_path=spr_file_path)
                self._log.info("Configuring workqueues {}".format(cmd_output))
                cmd_dma = "./Guest_Mdev_Randomize_DSA_Conf.sh -i 1000 -j 10"
                cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=cmd_dma,cmd_str=cmd_dma,
                                                                   execute_timeout=self._command_timeout,
                                                                   cmd_path=spr_file_path)
                self._log.info("Running DSA workload on vm and output is {}".format(cmd_output))

                cmd_check_error = "journalctl --dmesg | grep error"
                cmd_opt = vm_obj.execute(cmd_check_error, self._command_timeout)
                if len(cmd_opt.stdout) == 0:
                    self._log.info("No errors found")
                else:
                    raise RuntimeError("Errors found after running workload")

    def execute(self):
        """
        This function execute
        1. IOMMU scalable mode need to be enabled in.
        2. Configure Work Queue and DSA.
        3. Enable DSA and IAX Device.
        4. Enable Workqueue and associate UUID to WQ.
        5. Create MDev and configure guests with mdev.
        6. Configure DSA on 1-8th and IAX on 9th guest.
        7. Run workload to attached device as MDEV.
        :return: True if test case pass else fail
        """
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
        if not self.enable_intel_iommu_by_kernel():
            raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")
        self._test_content_logger.end_step_logger(2, return_val=True)

        socket, core_socket, threads_per_core = self.get_cpu_core_info()
        total_cpus = socket * core_socket * threads_per_core
        mdev_per_socket = 4
        total_mdev = socket * mdev_per_socket
        cpus_per_vm = int(total_cpus / total_mdev)
        self.get_yum_repo_config(self.os, self._common_content_lib, os_type="centos")

        release_cmd = "uname -a | grep spr"
        output = self.os.execute(release_cmd, self._command_timeout)
        uname_output = output.stdout

        self._test_content_logger.start_step_logger(2)
        if not self.enable_intel_iommu_by_kernel():
            raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")
        self._test_content_logger.end_step_logger(2, return_val=True)
        # Installing the dependency packages
        self.get_yum_repo_config(self.os, self._common_content_lib, os_type="centos")
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
            command_r_modprobe = "modprobe -r idxd"
            self._common_content_lib.execute_sut_cmd_no_exception(command_r_modprobe, " modprobe remove command",
                                                                  self._command_timeout, self.ROOT_PATH,
                                                                  ignore_result="ignore")
            command_modprobe = "modprobe idxd"
            self._common_content_lib.execute_sut_cmd_no_exception(command_modprobe, " modprobe command",
                                                                  self._command_timeout, self.ROOT_PATH,
                                                                  ignore_result="ignore")

        self._test_content_logger.end_step_logger(3, return_val=True)
        self._test_content_logger.start_step_logger(4)
        spr_dir_path = self._install_collateral.get_spr_path()
        self._test_content_logger.end_step_logger(4, return_val=True)
        self._test_content_logger.start_step_logger(5)

        self._install_collateral.configure_dsa(spr_dir_path)
        extra_disk = 2
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)


        for vm_index in range(len(self.NUMBER_OF_DSA_VMS)):
            vm_name = self.NUMBER_OF_DSA_VMS[index] + "_" + str(index)
            self._vm_provider.destroy_vm(vm_name)
            self.LIST_OF_VM_NAMES.append(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
            end_index = (total_cpus - 1) - (vm_index * cpus_per_vm)
            # start_index = end_index - ((vm_index + 1) * cpus_per_vm) + 1
            start_index = end_index - cpus_per_vm + 1
            cpu_list = list(range(start_index, end_index+1))
            cpu_list = "{}-{}".format(start_index, end_index)
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_parallel=None, vm_create_async=None, mac_addr=True,
                                  pool_id=free_storage_pool, pool_vol_id=None, cpu_core_list=cpu_list)
            self.verify_vm_functionality(vm_name, self.VM_TYPE)

            self._log.info(" Created VM:{} on CentOS.".format(vm_name))

            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)

            common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            grub_param = "intel_iommu=on,sm_on iommu=on no5lvl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce"
            self.enable_intel_iommu_by_kernel_in_vm(vm_name, grub_param=grub_param,
                                                    common_content_lib=common_content_lib_vm)
            self.reboot_linux_vm(vm_name)
            time.sleep(200)

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


            self._log.info("DSA dependencies package installation on VM was successfull...")
            self._test_content_logger.end_step_logger(6, return_val=True)
            self._test_content_logger.start_step_logger(7)
            uuid = self.get_dsa_uuid()
            uuid_list = uuid[index]
            self.attach_mdev_instance_to_vm(vm_name, uuid_list)
            self.DSA_MDEV.append(uuid_list)
            if 'spr' in uname_output:
                self._log.info("The system is in SPR, hence utilty is part of the BKC")
            else:
                install_collateral_vm_obj.install_and_verify_accel_config_vm(common_content_lib_vm)

            spr_dir_path = self._install_collateral.get_spr_path(common_content_lib_vm)
            self._test_content_logger.end_step_logger(7, return_val=True)
            self._test_content_logger.start_step_logger(8)

        # Enable IAX and Workqueues on host
        self._test_content_logger.start_step_logger(9)
        spr_dir_path = self._install_collateral.get_spr_path()
        self._install_collateral.configure_iax(spr_dir_path)
        self._test_content_logger.end_step_logger(9, return_val=True)

        for index in range(len(self.NUMBER_OF_IAX_VM)):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.NUMBER_OF_IAX_VM[index] + "_" + "iax" + "_" + str(index) + "p"
            self._log.info(" VM:{} on CentOS.".format(vm_name))
            self._vm_provider.destroy_vm(vm_name)
            self.LIST_OF_VM_NAMES.append(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
            self.create_vm_pool(vm_name, self.NUMBER_OF_IAX_VM[index], mac_addr=True, pool_id=free_storage_pool)
            self.verify_vm_functionality(vm_name, self.NUMBER_OF_IAX_VM[index])
            vm_os_obj = self.create_vm_host(vm_name, self.NUMBER_OF_IAX_VM[index])
            common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self._test_content_logger.start_step_logger(10)
            self.verify_vm_functionality(vm_name, self.VM[index], enable_yum_repo=True)
            time.sleep(120)
            grub_param = "intel_iommu=on,sm_on iommu=on no5lvl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce"
            self.enable_intel_iommu_by_kernel_in_vm(vm_name, grub_param=grub_param,
                                                    common_content_lib=common_content_lib_vm)
            self.reboot_linux_vm(vm_name)
            time.sleep(200)
            self._test_content_logger.end_step_logger(10, return_val=True)
            self._test_content_logger.start_step_logger(11)
            install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)
            PROXY_COMMANDS = "export http_proxy=http://proxy-iind.intel.com:911;export HTTP_PROXY=http://proxy-iind.intel.com:911;export https_proxy=http://proxy-iind.intel.com:911;export HTTPS_PROXY=http://proxy-iind.intel.com:911;export no_proxy='localhost, 127.0.0.1, intel.com';yum remove -y libuuid-devel;yum remove -y kmod-devel;yum remove -y libudev-devel;yum remove -y xmlto*;yum remove -y systemd-devel;yum remove -y kernel-spr-bkc-pc-modules-internal;yum remove -y json-c-devel;yum install -y libuuid-devel;yum install -y kmod-devel;yum install -y libudev-devel;yum install -y xmlto*;yum install -y systemd-devel;yum install -y kernel-spr-bkc-pc-modules-internal;yum install -y json-c-devel;"
            common_content_lib_vm.execute_sut_cmd(PROXY_COMMANDS, "Enabling Proxy in System", 400)
            time.sleep(150)
            self._log.info("IAX dependencies package installation on VM was successfull...")
            self._test_content_logger.end_step_logger(11, return_val=True)
            self._test_content_logger.start_step_logger(12)
            uuid = self.get_iax_uuid()
            uuid_list = uuid[index]
            self._log.info("uuid info:{}".format(uuid_list))
            self.IAX_MDEV.append(uuid_list)
            self.attach_mdev_instance_to_vm(vm_name, uuid_list)

            if 'spr' in uname_output:
                self._log.info("The system is in SPR, hence utilty is part of the BKC")
            else:
                install_collateral_vm_obj.install_and_verify_accel_config_vm(common_content_lib_vm)

            spr_dir_path = self._install_collateral.get_spr_path(common_content_lib_vm)
            self._test_content_logger.end_step_logger(12, return_val=True)
            self._test_content_logger.start_step_logger(13)

        threadlist_all =[]

        for vm_name in self.LIST_OF_VM_NAMES:
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            if 'iax' in vm_name:
                thread_iax = threading.Thread(target=self.run_iax_workload_on_vm_2hours,
                                              args=(spr_dir_path, common_content_lib_vm, vm_os_obj))
                threadlist_all.append(thread_iax)
                thread_iax.start()
                time.sleep(60)
            else:
                thread_dsa = threading.Thread(target=self.run_workload_on_vm_thread,
                                             args=(spr_dir_path, common_content_lib_vm, vm_os_obj))
                threadlist_all.append(thread_dsa)
                thread_dsa.start()
                time.sleep(60)
        self._test_content_logger.end_step_logger(13, return_val=True)

        self._test_content_logger.start_step_logger(14)
        for thread_accel in  threadlist_all:
            thread_accel.join(timeout=2)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationCentOsKvmSiovDsaIaxCrossSocketTopology, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationCentOsKvmSiovDsaIaxCrossSocketTopology.main()
             else Framework.TEST_RESULT_FAIL)
