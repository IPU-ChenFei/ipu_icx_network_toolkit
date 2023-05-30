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
from dtaf_core.lib.dtaf_constants import Framework

from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.virtualization.dsa_common_virtualization import DsaBaseTest_virtualization
from src.lib.test_content_logger import TestContentLogger
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions


class VirtualizationCentOsKvmSiovIAXDMA(VirtualizationCommon, DsaBaseTest_virtualization):
    """
    HPALM ID: 16014657706
    HPALM TITLE: Virtualization-CentOS-KVM-SIOV-IAX and run DMA workload
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Enable Intel VT for Directed I/O (VT-d), Interrupt Remapping, PCIe ENQCMD ENQCMDS.
    2. IOMMU scalable mode need to be enabled in.
    3. INstall dependency packages
    4. Configure IAX.
    5. Enable IAX Device
    6. Enable Workqueue and associate UUID to WQ.
    7. Create mdev and configure guests with mdev for iax.
    8. Run workload to attached device as MDEV.
    """
    BIOS_CONFIG_FILE = "virtualization_centos_kvm_siov_dsa_iax_cross_socket_topology_bios.cfg"
    NUMBER_OF_VMS = [VMs.CENTOS]
    VM_TYPE = "CENTOS"
    VM = [VMs.CENTOS]
    LIST_OF_IAX_VM_NAMES = []
    DSA_MDEV = []
    IAX_MDEV = []
    TEST_FILE_CONTENT = "This is a Test File"
    TEST_FILE_NAME = "test.txt"
    TEST_CASE_ID = ["P16014657706", "Virtualization-CentOS-KVM-SIOV-IAX and run DMA workload"]
    STORAGE_VOLUME = ["/home"]
    GRUB_PARAM = "intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode='modern',device-iotlb=on,aw-bits=48 " \
                 "intel_iommu=on,sm_on ats_with_iommu_swizzle iommu=pt no5lvl idle=poll"
    LIST_OF_LINUX_OS_COMMANDS = [r"yum install -y libuuid-devel;echo y",
                                 r"yum install -y kmod-devel;echo y",
                                 r"yum install -y libudev-devel;echo y",
                                 r"yum install -y xmlto*;echo y",
                                 r"yum install -y systemd-devel;echo y",
                                 r"yum install -y json-c-devel"]
    STEP_DATA_DICT = {1: {'step_details': 'Enable Intel VT for Directed I/O (VT-d), Interrupt Remapping, PCIe ENQCMD '
                                          '/ENQCMDS, VMX Bios and reboot, IAX = enabled, DSA = enabled ',
                          'expected_results': 'Verify the enabled BIOS'},
                      2: {'step_details': 'IOMMU scalable mode need to be enabled in.',
                          'expected_results': 'Should be successfull'},
                      3: {'step_details': 'Install the depedencies packages on the host',
                          'expected_results': 'Fail if not found the devices'},
                      4: {'step_details': 'Configure IAX',
                          'expected_results': 'IAX configuration should be successfull.'},
                      5: {'step_details': 'Enable IAX on host and VM',
                          'expected_results': 'Should be successfull'},
                      6: {'step_details': 'Install the depedencies packages on the VM',
                          'expected_results': 'Should be successfull'},
                      7: {'step_details': 'Enable Workqueue and associate UUID to WQ',
                          'expected_results': 'Should be successfull'},
                      8: {'step_details': 'Create mdev and configure guests with mdev for iax',
                          'expected_results': 'Should be successfull'},
                      9: {'step_details': 'Run workload DMA to attached device as MDEV',
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
        super(VirtualizationCentOsKvmSiovIAXDMA, self).__init__(test_log, arguments, cfg_opts,
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
        super(VirtualizationCentOsKvmSiovIAXDMA, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This function execute
        1. IOMMU scalable mode need to be enabled in.
        2. Install all the dependencies
        3. Configure IAX.
        4. Enable IOMMU paramters.
        5. Create MDev and configure guests with mdev.
        6. Run workload using DMA test.
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

        # Installing the dependency packages
        self._test_content_logger.start_step_logger(3)
        self._log.info("Installing dependency package for CentOS: {}".format(self.INSTALL_DEPENDENCY_PACKAGE))
        for package in self.INSTALL_DEPENDENCY_PACKAGE:
            self._install_collateral.yum_install(package)
        self._test_content_logger.end_step_logger(3, return_val=True)
        self._test_content_logger.start_step_logger(4)
        # lsmod grep command for idxd device
        self.check_idxd_device()
        # Determine the dsa device state
        self.determine_device_state()
        # Check DSA devices
        self.verify_dsa_driver_directory()

        spr_dir_path = self._install_collateral.get_spr_path()
        command_r_modprobe = "modprobe -r idxd"
        self._common_content_lib.execute_sut_cmd_no_exception(command_r_modprobe, " modprobe remove command",
                                                              self._command_timeout, self.ROOT_PATH,
                                                              ignore_result="ignore")
        command_modprobe = "modprobe idxd"
        self._common_content_lib.execute_sut_cmd_no_exception(command_modprobe, " modprobe command",
                                                              self._command_timeout, self.ROOT_PATH,
                                                              ignore_result="ignore")

        self._install_collateral.configure_iax(spr_dir_path)
        self._test_content_logger.end_step_logger(4, return_val=True)


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
            self._log.info(" Creating VM:{} on CentOS".format(vm_name))
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,self.VM_TYPE)
            self.create_vm_pool(vm_name, self.VM_TYPE, mac_addr=True, pool_id=free_storage_pool)
            self.verify_vm_functionality(vm_name, self.VM_TYPE, enable_yum_repo=True)
            self.LIST_OF_VM_NAMES.append(vm_name)
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self.enable_intel_iommu_by_kernel_vm(vm_os_obj, common_content_lib_vm, self.GRUB_PARAM)
            self.reboot_linux_vm(vm_name)
            time.sleep(60)
            self.verify_vm_functionality(vm_name, self.VM[index], enable_yum_repo=True)
            install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)
            install_collateral_vm_obj.install_kernel_rpm_on_linux(is_vm="yes")
            self._enable_yum_repo_in_cent_vm(vm_os_obj)

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
            self._test_content_logger.start_step_logger(5)
            uuid = self.get_iax_uuid()
            uuid_list = uuid[index]
            self._log.info("uuid info:{}".format(uuid_list))
            self.IAX_MDEV.append(uuid_list)
            self.attach_mdev_instance_to_vm(vm_name, uuid_list)
            self._test_content_logger.end_step_logger(5, return_val=True)
            self._test_content_logger.start_step_logger(6)
            install_collateral_vm_obj.install_and_verify_accel_config_vm(common_content_lib_vm)
            spr_dir_path = install_collateral_vm_obj.get_spr_path(common_content_lib_vm)
            self._test_content_logger.end_step_logger(6, return_val=True)
            self._test_content_logger.start_step_logger(7)
            self.IAX_MDEV.append(uuid)
            self._test_content_logger.end_step_logger(7, return_val=True)
            self._test_content_logger.start_step_logger(8)
            install_collateral_vm_obj.run_iax_workload_on_vm(spr_dir_path, common_content_lib_vm, vm_os_obj)
            self._test_content_logger.end_step_logger(8, return_val=True)

        for index in range(len(self.NUMBER_OF_VMS)):
            vm_name = self.NUMBER_OF_VMS[index] + "_" + str(index)
            self.detach_mdev_instance_from_vm(vm_name, self.IAX_MDEV[index])

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationCentOsKvmSiovIAXDMA, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationCentOsKvmSiovIAXDMA.main()
             else Framework.TEST_RESULT_FAIL)

