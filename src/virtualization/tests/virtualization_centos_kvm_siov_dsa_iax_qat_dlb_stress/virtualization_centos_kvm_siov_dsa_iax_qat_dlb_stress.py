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
import array

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.provider_factory import ProviderFactory

from src.provider.vm_provider import VMs
from src.virtualization.dsa_common_virtualization import DsaBaseTest_virtualization
from src.lib.test_content_logger import TestContentLogger
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions
from src.virtualization.base_qat_util import BaseQATUtil


class VirtualizationCentOsKvmSiovDsaIaxQatDlbStress(BaseQATUtil, DsaBaseTest_virtualization):
    """
    HPALM ID: 16014132153
    HPALM TITLE: Virtualization-CentOS-KVM-SIOV-DSA/IAX/QAT/DLB-stress
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. IOMMU scalable mode need to be enabled in.
    2. Configure Work Queue DSA and IAX.
    3. Enable DSA, IAX, QAT, DLB Device
    4. Enable Workqueue and associate UUID to WQ.
    5. Create mdev and configure guests with mdev for dsa and iax.
    6. Run workload to attached device as MDEV.
    """
    BIOS_CONFIG_FILE = "virtualization_centos_kvm_siov_dsa_iax_qat_dlb_stress.cfg"
    NUMBER_OF_VMS = 4
    NUMBER_OF_DSA_VMS = [VMs.CENTOS]*NUMBER_OF_VMS
    NUMBER_OF_IAX_VMS = [VMs.CENTOS]*NUMBER_OF_VMS
    NUMBER_OF_QAT_VMS = [VMs.CENTOS]*NUMBER_OF_VMS
    NUMBER_OF_DLB_VMS = [VMs.CENTOS]*NUMBER_OF_VMS
    DSA_VM_NAMES = []
    IAX_VM_NAMES = []
    QAT_VM_NAMES = []
    DLB_VM_NAMES = []
    DLB_LOAD_TEST_TIME = 7200
    VM_TYPE = "CENTOS"
    DSA_MDEV = []
    IAX_MDEV = []
    TEST_CASE_ID = ["P16014132153", "Virtualization-CentOS-KVM-SIOV-DSA/IAX/QAT/DLB-stress"]
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
    QAT_DEPENDENCY_PACKAGES = "epel-release zlib-devel libnl3-devel boost-devel systemd-devel yasm lz4-devel " \
                              "elfutils-libelf-devel openssl-devel readline-devel"

    STEP_DATA_DICT = {1: {'step_details': 'Enable Intel VT for Directed I/O (VT-d), Interrupt Remapping, '
                                          'PCIe ENQCMD/ENQCMDS, VMX Bios and reboot,'
                                          'IAX=enabled,DSA=enabled,CPM=Enabled,HQM=Enabled ',
                          'expected_results': 'Verify the enabled BIOS'},
                      2: {'step_details': 'IOMMU scalable mode need to be enabled in.',
                          'expected_results': 'Should be successfull'},
                      3: {'step_details': 'Install the depedencies packages on the host',
                          'expected_results': 'Fail if not found the devices'},
                      4: {'step_details': 'Enable DSA and Workqueues on host',
                          'expected_results': 'Verify DSA devices should be dsa0 to dsa7 devices should be available'},
                      5: {'step_details': 'Verify IAX devices should be iax0 to iax7 devices should be available',
                          'expected_results': 'Verify DSA devices should be dsa0 to dsa7 devices should be available'},
                      6: {'step_details': 'Check and create the qat devices',
                          'expected_results': 'QAT devices created successfullyl'},
                      7: {'step_details': 'Verify the HQM/DLB in kernel',
                          'expected_results': 'HQM/DLB verified and driver removed'},
                      8: {'step_details': 'Create VM and enable DSA work queue',
                          'expected_results': 'Should be successfull'},
                      9: {'step_details': 'Create VM and enable IAX work queue',
                          'expected_results': 'Should be successfull'},
                      10: {'step_details': 'Create VM and attach QAT device as mdev instance',
                           'expected_results': 'Should be successfull'},
                      11: {'step_details': 'Create VM and attach DLB2 device as mdev instance',
                           'expected_results': 'Should be successfull'},
                      12: {'step_details': 'Run Workload DSA,IAX,QAT,DLB to attached mdev device on VMs',
                           'expected_results': 'Should be successfull'},
                      13: {'step_details': 'Detach all the mdev instances (DSA,IAX,QAT,DLB) from VM',
                           'expected_results': 'Should be successfull'},
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of DsaLibInstall
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.virtualization_siov_stress_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                  self.BIOS_CONFIG_FILE)
        super(VirtualizationCentOsKvmSiovDsaIaxQatDlbStress, self).__init__(test_log, arguments, cfg_opts,
                                                                            self.virtualization_siov_stress_bios_knobs)
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._cfg_opt = cfg_opts
        self._test_log = test_log
        self.sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self.os = ProviderFactory.create(self.sut_os_cfg, test_log)  # type: SutOsProvider
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self._arg_tc = arguments

    def prepare(self):
        # type: () -> None
        """
        preparing the setup by enabling VTd, Interrupt remapping, VMX, PCIe ENQCMD /ENQCMDS  and verify all kobs are
        enabled successfully
        """
        self._test_content_logger.start_step_logger(1)
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        super(VirtualizationCentOsKvmSiovDsaIaxQatDlbStress, self).prepare()
        self._vm_provider.create_bridge_network("virbr0")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This function execute
        1. IOMMU scalable mode need to be enabled in.
        2. Enable DSA,IAX,QAT,DLB Device.
        3. Enable Workqueue and associate UUID to WQ.
        4. Create MDev and configure guests with mdev.
        5. Run workload to attached device as MDEV.
        :return: True if test case pass else fail
        """
        # Enabling the Intel iommu in kernel
        self._test_content_logger.start_step_logger(2)
        if not self.enable_intel_iommu_by_kernel():
            raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")
        self._install_collateral.screen_package_installation()
        self._test_content_logger.end_step_logger(2, return_val=True)
        self.get_yum_repo_config(self.os, self._common_content_lib, os_type="centos")
        # Installing the dependency packages
        self._test_content_logger.start_step_logger(3)
        self._log.info("Installing dependency package for CentOS: {}".format(self.INSTALL_DEPENDENCY_PACKAGE))
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
        release_cmd = "uname -a | grep spr"
        output = self.os.execute(release_cmd, self._command_timeout)
        uname_output = output.stdout
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
        # Enable IAX and Workqueues on host
        spr_dir_path = self._install_collateral.get_spr_path()
        self._install_collateral.configure_iax(spr_dir_path)
        self._test_content_logger.end_step_logger(5, return_val=True)
        socket, core_socket, threads_per_core = self.get_cpu_core_info()
        total_cpus = socket * core_socket * threads_per_core
        qat_per_socket = 4
        mdev_per_socket = 4
        total_mdev = socket * mdev_per_socket
        cpus_per_vm = int(total_cpus / total_mdev)
        vqat_per_qat_dev = 4
        # Configure QAT device
        self._test_content_logger.start_step_logger(6)
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
        list_dev_sym_asym_dc = [[] for i in range(len(bdf_sym_asym_dc_dict['bdf']))]
        total_dev_sym_asym_dc = array.array('i',(0 for i in range(len(bdf_sym_asym_dc_dict['bdf']))))
        for index in range(len(bdf_sym_asym_dc_dict['bdf'])):
            bdf.append((bdf_sym_asym_dc_dict['bdf'])[index])

            number_of_dev, dev_uuid_list = self.create_qat_devices(bdf[index], (bdf_sym_asym_dc_dict['sym'])[index],
                                                                   "sym", self._common_content_lib)
            uuid_sym.append(dev_uuid_list)
            list_dev_sym_asym_dc[index].extend(dev_uuid_list)
            total_dev_sym_asym_dc[index] = total_dev_sym_asym_dc[index] + number_of_dev
            # update the total no of vqat device in system
            sym.append(number_of_dev)
            total_dev_sym_and_dc = total_dev_sym_and_dc + number_of_dev
            (bdf_sym_asym_dc_dict['sym'])[index] = number_of_dev

            number_of_dev, dev_uuid_list = self.create_qat_devices(bdf[index], (bdf_sym_asym_dc_dict['asym'])[index],
                                                                   "asym", self._common_content_lib)
            uuid_asym.append(dev_uuid_list)
            list_dev_sym_asym_dc[index].extend(dev_uuid_list)
            total_dev_sym_asym_dc[index] = total_dev_sym_asym_dc[index] + number_of_dev
            # update the total no of vqat device in system
            asym.append(number_of_dev)
            (bdf_sym_asym_dc_dict['asym'])[index] = number_of_dev
            # total_dev_sym_and_dc = total_dev_sym_and_dc + number_of_dev

            number_of_dev, dev_uuid_list = self.create_qat_devices(bdf[index], (bdf_sym_asym_dc_dict['dc'])[index],
                                                                   "dc", self._common_content_lib)
            uuid_dc.append(dev_uuid_list)
            list_dev_sym_asym_dc[index].extend(dev_uuid_list)
            total_dev_sym_asym_dc[index] = total_dev_sym_asym_dc[index] + number_of_dev
            # update the total no of vqat device in system
            dc.append(number_of_dev)
            (bdf_sym_asym_dc_dict['dc'])[index] = number_of_dev
            total_dev_sym_and_dc = total_dev_sym_and_dc + number_of_dev

        vqat_per_vm = 1
        vqat_start_index_socket0 = 0
        vqat_start_index_socket1 = int(total_dev_sym_and_dc / socket)
        self._test_content_logger.end_step_logger(6, return_val=True)
        # Configure DLB device
        self._test_content_logger.start_step_logger(7)
        self.verify_hqm_dlb_kernel()
        self.install_hqm_driver_library()
        self.install_hqm_dpdk_library()
        self._test_content_logger.end_step_logger(7, return_val=True)
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
                self._vm_provider.create_storage_pool(pool_id, mount_dev)
        for index in range(self.NUMBER_OF_VMS):
            dsa_vm = self.NUMBER_OF_DSA_VMS[index] + "_" + str(index) + "_dsa"
            iax_vm = self.NUMBER_OF_IAX_VMS[index] + "_" + str(index) + "_iax"
            qat_vm = self.NUMBER_OF_QAT_VMS[index] + "_" + str(index) + "_qat"
            dlb_vm = self.NUMBER_OF_DLB_VMS[index] + "_" + str(index) + "_dlb"
            self.DSA_VM_NAMES.append(dsa_vm)
            self.IAX_VM_NAMES.append(iax_vm)
            self.QAT_VM_NAMES.append(qat_vm)
            self.DLB_VM_NAMES.append(dlb_vm)
        vm_sut_obj_list = []
        uuid_for_vm_list = []

        vms_per_socket = int(self.NUMBER_OF_VMS/socket)
        list_dev_sym_asym_dc_bu = list_dev_sym_asym_dc
        total_dev_sym_asym_dc_bu = total_dev_sym_asym_dc
        # Creating VMs for DSA workload
        self._test_content_logger.start_step_logger(8)
        for vm_index, vm_name in zip(range(len(self.NUMBER_OF_DSA_VMS)), self.DSA_VM_NAMES):
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL, self.VM_TYPE)
            end_index = (total_cpus - 1) - (vm_index * cpus_per_vm)
            # start_index = end_index - ((vm_index + 1) * cpus_per_vm) + 1
            start_index = end_index - cpus_per_vm + 1
            cpu_list = "{}-{}".format(start_index, end_index)
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True,
                                   pool_id=free_storage_pool, pool_vol_id=None, cpu_core_list=cpu_list, nw_bridge="virbr0")
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm_obj = CommonContentLib(self._test_log, vm_os_obj, self._cfg_opt)
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, os_type="centos",machine_type="vm")
            self.enable_intel_iommu_by_kernel_in_vm(vm_name, grub_param=self.GRUB_PARAM,
                                                    common_content_lib=common_content_lib_vm_obj)
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
            uuid_list = uuid[vm_index]
            self.DSA_MDEV.append(uuid_list)
            self.attach_mdev_instance_to_vm(vm_name, uuid_list)
            self._install_collateral.install_and_verify_accel_config_vm(common_content_lib_vm_obj)
            self._install_collateral.run_workload_on_vm(spr_dir_path, common_content_lib_vm_obj, vm_os_obj)
        self._test_content_logger.end_step_logger(8, return_val=True)
        self._test_content_logger.start_step_logger(9)
        for vm_index, vm_name in zip(range(len(self.NUMBER_OF_IAX_VMS)), self.IAX_VM_NAMES):
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
            end_index = (total_cpus - 1) - (vm_index * cpus_per_vm)
            # start_index = end_index - ((vm_index + 1) * cpus_per_vm) + 1
            start_index = end_index - cpus_per_vm + 1
            cpu_list = "{}-{}".format(start_index, end_index)
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True,
                                   pool_id=free_storage_pool,
                                   pool_vol_id=None, cpu_core_list=cpu_list)
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm_obj = CommonContentLib(self._test_log, vm_os_obj, self._cfg_opt)
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, os_type="centos",machine_type="vm")
            self.enable_intel_iommu_by_kernel_in_vm(vm_name, grub_param=self.GRUB_PARAM,
                                                    common_content_lib=common_content_lib_vm_obj)
            # Installing the dependency packages
            self._log.info("Installing dependency package for CentOS: {}".format(self.INSTALL_DEPENDENCY_PACKAGE))
            for command_line in self.LIST_OF_LINUX_OS_COMMANDS:
                cmd_result = vm_os_obj.execute(command_line, self._command_timeout)
                if cmd_result.cmd_failed():
                    log_error = "Failed to run command '{}' with " \
                                "return value = '{}' and " \
                                "std_error='{}'..".format(command_line, cmd_result.return_code, cmd_result.stderr)
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
                else:
                    self._log.info("The command '{}' executed successfully..".format(command_line))
                self._log.info("IAX dependencies package installation on VM was successfull...")
            uuid = self.get_iax_uuid()
            uuid_list = uuid[vm_index]
            self.IAX_MDEV.append(uuid_list)
            self.attach_mdev_instance_to_vm(vm_name, uuid_list)
            self._install_collateral.install_and_verify_accel_config_vm(common_content_lib_vm_obj)
            self._install_collateral.run_workload_on_vm(spr_dir_path, common_content_lib_vm_obj, vm_os_obj)
        self._test_content_logger.end_step_logger(9, return_val=True)
        # create Vm and enable QAT device
        self._test_content_logger.start_step_logger(10)
        for vm_index, vm_name in zip(range(len(self.NUMBER_OF_QAT_VMS)), self.QAT_VM_NAMES):
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
            end_index = (total_cpus - 1) - (vm_index * cpus_per_vm)
            # start_index = end_index - ((vm_index + 1) * cpus_per_vm) + 1
            start_index = end_index - cpus_per_vm + 1
            cpu_list = "{}-{}".format(start_index, end_index)
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True,
                                   pool_id=free_storage_pool, pool_vol_id=None, cpu_core_list=cpu_list)
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._test_log, vm_os_obj, self._cfg_opt)
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, os_type="centos",machine_type="vm")
            self.enable_intel_iommu_by_kernel_in_vm(vm_name, grub_param=None,
                                                    common_content_lib=common_content_lib_vm_obj)

            #     # when VM index reaches the index from where the socket1 VMs start
            #     # for socket1 VMs, vqat devices to be attached from vqat devices created using qat devices on socket0
            #     # e.g. VM4-VM7<-> vqat from socket0
            #     # when VM index reaches the index from where the socket0 VMs start
            #     # for socket0 VMs, vqat devices to be attached from vqat devices created using qat devices on socket1
            #     # e.g. VM0-VM3 <-> vqat from socket1
            uuid_for_vm = ""
            qat_dev_index = qat_per_socket * (socket - int(vm_index / vms_per_socket) - 1)
            qat_start_index = qat_dev_index
            qat_end_index = qat_dev_index + qat_per_socket
            total_vqat_attached_vm = 0
            for qat_index in range(qat_start_index, qat_end_index):
                vqat_start_index_vm_group = qat_index * int(total_dev_sym_and_dc / socket)   # for a group of VMs on a socket
                vqat_end_index_vm_group = vqat_start_index_vm_group + int(total_dev_sym_and_dc / socket)  # for a group of VMs on a socket
                uuid_for_vm = ""
                for vqat_dev_no in range(0, total_dev_sym_asym_dc_bu[qat_index]):
                    if list_dev_sym_asym_dc_bu[qat_index][vqat_dev_no] != "":
                        uuid_for_vm = list_dev_sym_asym_dc_bu[qat_index][vqat_dev_no]
                        # invalidate so that it can not be taken for next VM
                        list_dev_sym_asym_dc_bu[qat_index][vqat_dev_no] = ""
                    else:
                        continue

                    if uuid_for_vm != "":
                        total_vqat_attached_vm = total_vqat_attached_vm + 1
                        uuid_for_vm_list.append(uuid_for_vm)
                        self.attach_vqat_instance_to_vm(vm_name, uuid_for_vm)
                        self._log.info("QAT device {} attach to VM {} was successfull...".format(uuid_for_vm, vm_name))
                        uuid_for_vm = ""
                    # break "for loop"
                    if total_vqat_attached_vm >= vqat_per_vm:
                        break
                # break external "for loop"
                if total_vqat_attached_vm >= vqat_per_vm:
                    break

            self.install_check_qat_status(vm_name=vm_name, os_obj=vm_os_obj,
                                          qat_type="siov", target_type="guest",
                                          common_content_object=common_content_lib_vm_obj, is_vm="yes")
            self.get_qat_device_status_adfctl(qat_dev_index, common_content_lib_vm_obj)
            self.set_qat_device_up_adfctl(qat_dev_index, common_content_lib_vm_obj)
            self.check_vqat_device_type_attached(common_content_lib_vm_obj)
        self._test_content_logger.end_step_logger(10, return_val=True)
        # Create DLB VM
        self._test_content_logger.start_step_logger(11)
        for vm_index, vm_name in zip(range(len(self.NUMBER_OF_DLB_VMS)), self.DLB_VM_NAMES):
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
            end_index = (total_cpus - 1) - (vm_index * cpus_per_vm)
            # start_index = end_index - ((vm_index + 1) * cpus_per_vm) + 1
            start_index = end_index - cpus_per_vm + 1
            # cpu_list = list(range(start_index, end_index+1))
            cpu_list = "{}-{}".format(start_index, end_index)
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True,
                                   pool_id=free_storage_pool,
                                   pool_vol_id=None, cpu_core_list=cpu_list)
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            self._log.info(" Created VM:{} on CentOS.".format(vm_name))
            uuid, domain, bus, device, function = self._vm_provider.create_mdev_dlb2_instance(vm_index)
            self.attach_pci_device_using_dbdf_to_vm(vm_name, domain, bus, device, function)
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm_obj = CommonContentLib(self._test_log, vm_os_obj, self._cfg_opt)
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, os_type="centos",machine_type="vm")
            self.enable_intel_iommu_by_kernel_in_vm(vm_name, grub_param=None,
                                                    common_content_lib=common_content_lib_vm_obj)
            self.verify_hqm_dlb_kernel(common_content_lib_vm_obj)
            self.install_hqm_driver_library(os_obj=vm_os_obj, common_content_lib=common_content_lib_vm_obj, is_vm="yes")
            self.install_hqm_dpdk_library(os_obj=vm_os_obj, common_content_lib=common_content_lib_vm_obj, is_vm="yes")
        self._test_content_logger.end_step_logger(11, return_val=True)
        self._test_content_logger.start_step_logger(12)
        dsa_thread = []
        for vm_name in self.DLB_VM_NAMES:
            # Creates VM names dynamically according to the OS and its resources
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            work_load = threading.Thread(target=self._install_collateral.run_dma_test,
                                         args=(common_content_lib_vm_obj, vm_os_obj))
            dsa_thread.append(work_load)
        iax_thread = []
        for vm_name in self.IAX_VM_NAMES:
            # Creates VM names dynamically according to the OS and its resources
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            work_load = threading.Thread(target=self._install_collateral.run_dma_test,
                                         args=(common_content_lib_vm_obj, vm_os_obj))
            iax_thread.append(work_load)
        for vm_name in self.QAT_VM_NAMES:
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self.run_qat_workload(common_content_lib_vm_obj)
        for vm_name in self.DLB_VM_NAMES:
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self.run_dlb_work_load_vm(vm_name, common_content_lib=common_content_lib_vm_obj)
        start_time = time.time()
        seconds = self.DLB_LOAD_TEST_TIME
        while True:
            current_time = time.time()
            elapsed_time = current_time - start_time
            if elapsed_time > seconds:
                self._log.info("Finished dlb load test after: " + str(int(elapsed_time)) + " seconds")
                break
        self._test_content_logger.end_step_logger(12, return_val=True)
        self._test_content_logger.start_step_logger(13)
        # # Detaching all the mdev instance assigned to VM
        for vm_index, vm_name in zip(range(len(self.NUMBER_OF_DSA_VMS)), self.DSA_VM_NAMES):
            self.detach_mdev_instance_from_vm(vm_name, self.DSA_MDEV[vm_index])
        for vm_index, vm_name in zip(range(len(self.NUMBER_OF_IAX_VMS)), self.IAX_VM_NAMES):
            self.detach_mdev_instance_from_vm(vm_name, self.IAX_MDEV[vm_index])
        for index, vm_name in zip(range(len(self.NUMBER_OF_QAT_VMS)), self.QAT_VM_NAMES):
            start_vqat_index_in_list = index * vqat_per_vm
            for vqat_num in range(start_vqat_index_in_list, (start_vqat_index_in_list + vqat_per_vm) ):
                vqat_uuid = uuid_for_vm_list[vqat_num]
                self.detach_vqat_instance_from_vm(vm_name, vqat_uuid)
                self.remove_qat_devices(vqat_uuid)
        self._test_content_logger.end_step_logger(13, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationCentOsKvmSiovDsaIaxQatDlbStress, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationCentOsKvmSiovDsaIaxQatDlbStress.main()
             else Framework.TEST_RESULT_FAIL)
