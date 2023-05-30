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


class VirtualizationRhelKvmVmScalableIovAndAllDsa(VirtualizationCommon, DsaBaseTest_virtualization):
    """
    HPALM ID: 16013838059
    HPALM TITLE: Pi_Virtualization_Rhel_Kvm_vm_scalableiov_configure_dsa_vdev
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager and test below:
    1. Enable Intel VT for Directed I/O (VT-d), Interrupt Remapping, PCIe ENQCMD  VMX on BIOS.
    2. IOMMU scalable mode need to be enabled in.
    3. Install the depedencies packages on the host
    4. Enable DSA and Workqueues on host
    5. Enable Intel IOMMU paramters on VM
    6. Enable Workqueue and associate UUID to WQ.
    7. Install the depedencies packages on the VM.
    8. Configure DSA on guest.
    9. Run workload to attached device as MDEV.
    """
    BIOS_CONFIG_FILE = "../vtd_bios_config.cfg"
    NUMBER_OF_VMS = 8
    NUMBER_OF_DSA = 8
    VM_TYPE = "CENTOS"
    VM = [VMs.CENTOS]*NUMBER_OF_VMS
    VM_NAME = None
    DSA_MDEV = []
    UUID_LIST = []
    TEST_CASE_ID = ["H16013838059", "DSA_TEST"]
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
    STEP_DATA_DICT = {1: {'step_details': 'Enable Intel VT for Directed I/O (VT-d), Interrupt Remapping, PCIe ENQCMD '
                                          '/ENQCMDS, VMX Bios and reboot',
                          'expected_results': 'Verify the enabled BIOS'},
                      2: {'step_details': 'IOMMU scalable mode need to be enabled in.', 'expected_results': 'Should be '
                                                                                                 'successfull'},
                      3: {'step_details': 'Install the depedencies packages on the host', 'expected_results': 'Fail if not found the '
                                                                                             'devices'},
                      4: {'step_details': 'Enable DSA and Workqueues on host', 'expected_results': 'Verify DSA devices '
                                                                                               'should be dsa0 to dsa7 devices should be available'},
                      5: {'step_details': 'Enable Intel IOMMU paramters on VM', 'expected_results': 'Should be successfull'},
                      6: {'step_details': 'Enable Workqueue and associate UUID to WQ', 'expected_results': 'Should be successfull'},
                      7: {'step_details': ' Configure DSA on guest', 'expected_results': 'Should be successfull'},
                      8: {'step_details': 'Install the depedencies packages on the VM',
                          'expected_results': 'Should be successfull'},
                      9: {'step_details': 'Run workload (ex dmatest) inside multiple VMs',
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
        super(VirtualizationRhelKvmVmScalableIovAndAllDsa, self).__init__(test_log, arguments, cfg_opts,
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
        super(VirtualizationRhelKvmVmScalableIovAndAllDsa, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This function execute
        1. Enable Intel VT for Directed I/O (VT-d), Interrupt Remapping, PCIe ENQCMD  VMX on BIOS.
        2. IOMMU scalable mode need to be enabled in.
        3. Install the depedencies packages on the host
        4. Enable DSA and Workqueues on host
        5. Enable Intel IOMMU paramters on VM
        6. Enable Workqueue and associate UUID to WQ.
        7. Configure DSA on guest.
        8. Install the depedencies packages on the VM.
        9. Run workload (ex dmatest) inside multiple VMs.
        :return: True if test case pass else fail
        """

        # Enabling the Intel iommu in kernel
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
        # Installing the dependency packages
        self._log.info("Installing dependency package for CentOS: {}".format(self.INSTALL_DEPENDENCY_PACKAGE))
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

        spr_dir_path = self._install_collateral.get_spr_path()
        self._install_collateral.configure_dsa(spr_dir_path)
        extra_disk = 24
        vm_sut_obj_list = []
        for index in range(self.NUMBER_OF_VMS):
            uuid = self._install_collateral.get_mdev_id(index)
            self.UUID_LIST.append(uuid)
        self._test_content_logger.end_step_logger(4, return_val=True)
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on CentOS.".format(vm_name))

        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)

        for vm_name, uuid in zip(self.LIST_OF_VM_NAMES, self.UUID_LIST):
            self._log.info(" Creating VM:{} on CentOS".format(vm_name))
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
            self.create_vm_pool(vm_name, self.VM_TYPE, mac_addr=True, pool_id=free_storage_pool)

            self.verify_vm_functionality(vm_name, self.VM_TYPE, enable_yum_repo=True)
            self.LIST_OF_VM_NAMES.append(vm_name)
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)
            install_collateral_vm_obj.install_kernel_rpm_on_linux(is_vm="yes")
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, os_type="centos",machine_type="vm")

            self._test_content_logger.start_step_logger(5)
            grub_param = "intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode='modern',device-iotlb=on,aw-bits=48 intel_iommu=on,sm_on ats_with_iommu_swizzle iommu=pt no5lvl"
            self.enable_intel_iommu_by_kernel_vm(vm_os_obj, common_content_lib_vm, grub_param)
            self.reboot_linux_vm(vm_name)
            time.sleep(60)
            self._test_content_logger.end_step_logger(5, True)
            self._test_content_logger.start_step_logger(6)
            # Installing the dependency packages
            self.reboot_linux_vm(vm_name)
            time.sleep(200)
            install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)
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

            self._test_content_logger.end_step_logger(6, return_val=True)
            self._test_content_logger.start_step_logger(7)
            self.attach_mdev_instance_to_vm(vm_name, uuid)
            self.DSA_MDEV.append(uuid)
            self._install_collateral.install_and_verify_accel_config_vm(common_content_lib_vm)
            spr_dir_path = self._install_collateral.get_spr_path(common_content_lib_vm)
            self._test_content_logger.end_step_logger(7, return_val=True)
            self._test_content_logger.start_step_logger(8)
            cmd_dma = "./Guest_Mdev_Randomize_DSA_Conf.sh -ck"
            cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=cmd_dma, cmd_str=cmd_dma,
                                                               execute_timeout=self._command_timeout,
                                                               cmd_path=spr_dir_path)
            self._log.info("DSA configuration output on VM {}".format(cmd_output))
            self._test_content_logger.end_step_logger(8, return_val=True)
            self._test_content_logger.start_step_logger(9)
            self._install_collateral.run_dma_test(common_content_lib_vm, vm_os_obj)
            self._test_content_logger.end_step_logger(9, return_val=True)

            # Detaching all the mdev instance assigned to VM
            for index in range(len(self.LIST_OF_VM_NAMES)):
                self.detach_mdev_instance_from_vm(self.LIST_OF_VM_NAMES[index], self.DSA_MDEV[index])

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationRhelKvmVmScalableIovAndAllDsa, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if VirtualizationRhelKvmVmScalableIovAndAllDsa.main() else Framework.TEST_RESULT_FAIL)


