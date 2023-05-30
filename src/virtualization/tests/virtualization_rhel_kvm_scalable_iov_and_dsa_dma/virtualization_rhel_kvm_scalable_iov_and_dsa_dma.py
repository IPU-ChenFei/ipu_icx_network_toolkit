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


class VirtualizationRhelKvmVmScalableIovRunDSADMA(VirtualizationCommon, DsaBaseTest_virtualization):
    """
    HPALM ID: 16012980184
    HPALM TITLE: Pi_Virtualization_Rhel_Kvm_vm_scalableiov_configure_dsa_vdev
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. IOMMU scalable mode need to be enabled in.
    2. Configure Work Queue and DSA.
    3. Enable DSA Device.
    4. Enable Workqueue and associate UUID to WQ.
    5. Create MDev and configure guests with mdev.
    6. Configure DSA on guest.
    7. Run DMA workload on the VM
    """
    BIOS_CONFIG_FILE = "../vtd_bios_config.cfg"
    NUMBER_OF_VMS = [VMs.CENTOS]
    VM_TYPE = "CENTOS"
    VM = [VMs.CENTOS]
    VM_NAME = None
    SNAPSHOT_NAME = None
    TEST_FILE_CONTENT = "This is a Test File"
    TEST_FILE_NAME = "test.txt"
    TEST_CASE_ID = ["H16012980184", "DSA_TEST"]
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
                      2: {'step_details': 'IOMMU scalable mode need to be enabled in',
                          'expected_results': 'Should be successfull'},
                      3: {'step_details': 'Configure Work Queue and DSA',
                          'expected_results': 'Fail if not found the devices'},
                      4: {'step_details': 'Enable DSA Device',
                          'expected_results': 'Verify DSA devices should be dsa0 to dsa7 devices should be available'},
                      5: {'step_details': 'Enable Workqueue and associate UUID to WQ',
                          'expected_results': 'Should be successfull'},
                      6: {'step_details': 'Configure DSA on guest', 'expected_results': 'Should be successfull'},
                      7: {'step_details': 'Run DMA workload on the VM', 'expected_results': 'Should be successfull'},
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of DsaLibInstall

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.dsa_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(VirtualizationRhelKvmVmScalableIovRunDSADMA, self).__init__(test_log, arguments, cfg_opts,
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
        super(VirtualizationRhelKvmVmScalableIovRunDSADMA, self).prepare()
        self._vm_provider.create_bridge_network("virbr0")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This function execute
        1. IOMMU scalable mode need to be enabled in.
        2. Configure Work Queue and DSA.
        3. Enable DSA Device.
        4. Enable Workqueue and associate UUID to WQ.
        5. Create MDev and configure guests with mdev.
        6. Configure DSA on guest.
        7. Run DMA workload on the VM

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

        spr_dir_path = self._install_collateral.get_spr_path()
        self._install_collateral.configure_dsa(spr_dir_path)

        self._test_content_logger.end_step_logger(5, return_val=True)
        extra_disk = 24
        vm_sut_obj_list = []
        for index in range(len(self.NUMBER_OF_VMS)):
            vm_name = self.NUMBER_OF_VMS[index] + "_" + str(index) + "S"
            self._log.info(" Creating VM:{} on CentOS".format(vm_name))
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
            self.create_vm_pool_nested(vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True,
                                       pool_id=free_storage_pool,
                                       extra_disk_space=extra_disk)
            # create VM os object
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)

            common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
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

            time.sleep(150)
            uuid_list = self.get_dsa_uuid()
            self._log.info("uuid info:{}".format(uuid_list))
            uuid = uuid_list[0]

            self.attach_mdev_instance_to_vm(vm_name, uuid)
            self._log.info("uuid info:{}".format(uuid))

            install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)
            spr_file_path = install_collateral_vm_obj.get_spr_path(common_content_lib_vm)
            self._log.info("Running SetupRandomise script")
            cmd_dma = " ./Guest_Mdev_Randomize_DSA_Conf.sh -ck"
            cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=cmd_dma, cmd_str=cmd_dma,
                                                               execute_timeout=self._command_timeout,
                                                               cmd_path=spr_file_path)
            print(cmd_output)
            cmd_dma = "./Guest_Mdev_Randomize_DSA_Conf.sh -i 1000 -j 10"
            cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=cmd_dma, cmd_str=cmd_dma,
                                                               execute_timeout=self._command_timeout,
                                                               cmd_path=spr_file_path)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationRhelKvmVmScalableIovRunDSADMA, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if VirtualizationRhelKvmVmScalableIovRunDSADMA.main() else Framework.TEST_RESULT_FAIL)
