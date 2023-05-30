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

import os
import sys
import threading

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.virtualization.virtualization_common import VirtualizationCommon
from src.virtualization.dsa_common_virtualization import DsaBaseTest_virtualization
from src.lib.common_content_lib import CommonContentLib
from src.lib.grub_util import GrubUtil
from src.provider.vm_provider import VMs
from src.accelerators.dsa_common import DsaBaseTest


class PiSprDsaHiConfiguraitonGuestVMMdevL(VirtualizationCommon, DsaBaseTest_virtualization, DsaBaseTest):
    """
    Phoenix ID : 16014893467 - PI_SPR_DSA_HI_Configuraiton_GuestVM_Mdev_L
    The purpose of this test case is to validate the DSA passthrough for guest VM and run workload.
    Then execute DSATEST on all available work-queues in guest
    1. Enable Intel VT for Directed I/O (VT-d), Interrupt Remapping, PCIe ENQCMD  VMX on BIOS.
    2. IOMMU scalable mode need to be enabled in.
    3. Install the depedencies packages on the host
    4. Enable DSA and Workqueues on host
    5. Enable Intel IOMMU paramters on VM
    6. Enable Workqueue and associate UUID to WQ.
    7. Install the depedencies packages on the VM
    8. Configure DSA on guest.
    9. Run workload to attached device as MDEV.
    """
    TEST_CASE_ID = ["16014893467", "PI_SPR_DSA_HI_Configuraiton_GuestVM_Mdev_L"]
    NUMBER_OF_VMS = 1
    VM = [VMs.CENTOS] * 1
    VM_TYPE = "CENTOS"
    BIOS_CONFIG_FILE = "mdev_spr_configuration_bios.cfg"
    STORAGE_VOLUME = ["/home"]
    DSA_MDEV = []
    DSA_USER_MODE_SCRIPT = "./setup_dsai_user_mode.sh"
    TEST_CASE_CONTENT_PATH = r"/root/pv-dsa-iax-bkc-tests/spr-accelerators-random-config-and-test"
    REGEX_VERIFY_ENABLE = r"enabled.*device.*"
    LIST_OF_LINUX_OS_COMMANDS = [r"yum install -y libuuid-devel;echo y",
                                 r"yum install -y kmod-devel;echo y",
                                 r"yum install -y libudev-devel;echo y",
                                 r"yum install -y xmlto*;echo y",
                                 r"yum install -y systemd-devel;echo y",
                                 r"yum install -y json-c-devel"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Install and verify Bios knobs for DSA',
            'expected_results': 'Bios knobs installed and verified successfully'},
        2: {'step_details': 'Enable IOMMU using kernel command line params in SUT',
            'expected_results': 'Kernel command line params updated to enable iommu in SUT'},
        3: {'step_details': 'Install and configure the yum repo config file',
            'expected_results': 'Yum repo configured successfully'},
        4: {'step_details': 'Install the DSA depemdencies, may be kernel sources as well',
            'expected_results': 'All packages installed successfully'},
        5: {'step_details': 'Check and Install the DSA driver and accel_config package',
            'expected_results': 'DSA driver and accel_config built and installed'},
        6: {'step_details': 'Check DSA device details',
            'expected_results': 'DSA devices detailes fetched '},
        7: {'step_details': 'Create the Storage Pool for VMs',
            'expected_results': 'Storage Pools created successfully'},
        8: {'step_details': 'Create the VM using storage pool',
            'expected_results': 'VM creation successfully done'},
        9: {'step_details': 'Start creating the VMs as per the names created',
             'expected_results': 'All VMs created with mdev devices nd dlb2 driver and libdlb'},
        10: {'step_details': 'Install and configure the yum repo config file in VM and install DSA dependencies',
             'expected_results': 'Yum repo configured and DSA related package dependencies installed successfully in VM'},
        11: {'step_details': 'Install DSA driver/accel_config in VM, verify it installed or not',
             'expected_results': 'DSA driver/accel_config are installed successfully in VM'},
        12: {'step_details': 'Attach the created DSA device to VM',
             'expected_results': 'Created DSA device attached to VM'},
        13: {'step_details': 'Execute opcode and DMA test',
             'expected_results': 'DSA workload and opcode executed successfully'},
        14: {'step_details': 'Detach the created DSA device from VM',
             'expected_results': 'Passthrough DSA device detached from VM'},
        15: {'step_details': 'Detach the created DSA device from SUT',
             'expected_results': 'Passthrough DSA device detached from SUT'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of PiSprDsaHiConfiguraitonGuestVMMdevL Class

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.virtualization_dsa_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(PiSprDsaHiConfiguraitonGuestVMMdevL, self).__init__(test_log, arguments, cfg_opts, self.virtualization_dsa_bios_knobs)
        self._common_content_lib = CommonContentLib(test_log, self.os, cfg_opts)
        self._grub_obj = GrubUtil(test_log, self._common_content_configuration, self._common_content_lib)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._cfg_opt = cfg_opts
        self._arg_tc = arguments
        self._test_log = test_log

    def prepare(self):
        # type: () -> None
        """
        This Method checks for
        1. Linux OS
        2. Makes the grub changes to server side of OS
        3. update the git proxy in the system
        4. sets the BIOS knobs
        5. create VM bridge Network
        """
        if self.os.os_type == OperatingSystems.LINUX:
            self._log.info("We have Linux OS for test case... proceeding further..")
            # To change the kernel to +server in CentOS
            self._grub_obj.set_default_boot_cent_os_server_kernel()
            self.update_git_proxy()
        else:
            raise content_exceptions.TestFail("Target is not booted with Linux")
        self._test_content_logger.start_step_logger(1)
        self.set_and_verify_bios_knobs(bios_file_path=self.virtualization_dsa_bios_knobs)
        self._test_content_logger.end_step_logger(1, True)
        self._vm_provider.create_bridge_network("virbr0")

    def update_git_proxy_vm(self, vm_os_obj):
        """
        This method is to update the proxy commands for VM

        :return : True on Success else raise exception
        """
        self._log.info("updating git proxy commands")
        for proxy in self.PROXY_COMMANDS:
            cmd_output = vm_os_obj.execute(proxy, self._command_timeout)
            if cmd_output.cmd_failed():
                raise content_exceptions.TestFail("updating proxy failed. Please verify proxy or git")
            self._log.info("proxy {} updated successfully".format(proxy))
        return True

    def clone_git_repo_vm(self, vm_os_obj):
        """
        This method is to clone the repo from github for VM

        :return : True on Success else raise exception
        """
        try:
            dsa_path = self.ROOT_FOLDER + "/" + self.DSA_IAX_BKC_FOLDER
            repo_name = self._common_content_configuration.get_git_repo_name()
            token = self._common_content_configuration.get_access_token()
            if "https" in repo_name and token != 'None':
                oauth_token_str = "https://{}:x-oauth-basic@".format(token)
                oauth_git_repo_name = repo_name.replace("https://", oauth_token_str)
                clone_repo_str = "git clone {}".format(oauth_git_repo_name)
                vm_os_obj.execute("rm -rf {}".format(dsa_path), self._command_timeout)
                cmd_output = vm_os_obj.execute(clone_repo_str, self._command_timeout)
                if cmd_output.cmd_failed():
                    raise content_exceptions.TestFail("cloning repo failed. Please check authentication")
            else:
                raise content_exceptions.TestFail("Implementation supports only https and please check the access "
                                                  "token")
        except Exception as ex:
            raise content_exceptions.TestFail("Failed due to {}".format(ex))
        return True

    def execute(self):
        """
        This validates the DSA for guest VM and run workload.
        Then execute DSATEST on all available work-queues in guest

        1	IOMMU scalable mode need to be enabled in.
        2	Enable DSA and Workqueues on host
        3	Enable Intel IOMMU paramters on VM
        4	Enable Workqueue and associate vfio to WQ.
        5	Install the depedencies packages on the VM
        6	Configure DSA on guest.
        7	Run workload to attached device as MDEV.
        8	Run workload on VM
        9	Detach devices from VM

        :return: True if test case pass else fail
        """
        dsa_thread = []
        # Enabling the Intel iommu in kernel
        self._test_content_logger.start_step_logger(2)
        if not self.enable_intel_iommu_by_kernel():
            raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")
        self._test_content_logger.end_step_logger(2, True)
        self._test_content_logger.start_step_logger(3)
        self.get_yum_repo_config(self.os, self._common_content_lib, os_type="centos")
        self._test_content_logger.end_step_logger(3, True)
        self._test_content_logger.start_step_logger(4)
        dependency_packages = "json-c-devel kmod-devel libuuid-devel libudev-devel systemd-devel xmlto*"
        self.yum_virt_install(package_group = dependency_packages, common_content_lib=self._common_content_lib, flags="--nobest --skip-broken")
        self._test_content_logger.end_step_logger(4, True)
        self.clone_git_repo()
        self._common_content_lib.wait_for_os(self.reboot_timeout)
        self._test_content_logger.start_step_logger(5)
        # lsmod grep command for idxd device
        self.check_idxd_device()
        # Determine the dsa device state
        self.determine_device_state()
        self._test_content_logger.end_step_logger(5, True)
        self._test_content_logger.start_step_logger(6)
        # Check DSA devices
        self.verify_dsa_driver_directory()
        self._test_content_logger.end_step_logger(6, True)
        self._test_content_logger.start_step_logger(7)
        # Install accel config tool
        self._install_collateral.install_verify_accel_config_no_idxd_reload()
        self._install_collateral.configure_dsa_devices(self.TEST_CASE_CONTENT_PATH)
        uuid = self.get_dsa_uuid()
        uuid_list = uuid[0]
        self.DSA_MDEV.append(uuid_list)
        self._test_content_logger.end_step_logger(7, True)
        self._test_content_logger.start_step_logger(8)
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)
        self._test_content_logger.end_step_logger(8, True)
        self._test_content_logger.start_step_logger(9)
        for index in range(self.NUMBER_OF_VMS):
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL, self.VM_TYPE)
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True,
                                   pool_id=free_storage_pool, pool_vol_id=None, cpu_core_list=None, nw_bridge="virbr0")
        self._test_content_logger.end_step_logger(9, True)
        for vm_name in self.LIST_OF_VM_NAMES:
            self._test_content_logger.start_step_logger(10)
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._test_log, vm_os_obj, self._cfg_opt)
            self.update_git_proxy_vm(vm_os_obj)
            self.clone_git_repo_vm(vm_os_obj)
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
                self._log.info("DSA dependencies package installation on VM was successful...")
            self._test_content_logger.end_step_logger(10, True)
            self._test_content_logger.start_step_logger(11)
            self.attach_mdev_instance_to_vm(vm_name, uuid_list)
            self._install_collateral.install_and_verify_accel_config_vm(common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(11, True)
            self._test_content_logger.start_step_logger(12)
            self.execute_opcode_test_for_dsa(spr_file_path=self.TEST_CASE_CONTENT_PATH, vm_obj=vm_os_obj)
            self.execute_dma_test_vm(spr_file_path=self.TEST_CASE_CONTENT_PATH, vm_obj=vm_os_obj)
            self._test_content_logger.end_step_logger(12, True)
            self._test_content_logger.start_step_logger(13)
            self._install_collateral.run_dsa_workload_on_vm(self.TEST_CASE_CONTENT_PATH, common_content_lib_vm_obj, vm_os_obj)
            # Creates VM names dynamically according to the OS and its resources
            work_load = threading.Thread(target=self._install_collateral.run_iax_dma_test,
                                         args=(common_content_lib_vm_obj, vm_os_obj))
            dsa_thread.append(work_load)
            self._test_content_logger.end_step_logger(13, True)
        self._test_content_logger.start_step_logger(14)
        for vm_index, vm_name in zip(range(self.NUMBER_OF_VMS), self.LIST_OF_VM_NAMES):
            self.detach_mdev_instance_from_vm(vm_name, self.DSA_MDEV[vm_index])
            self.shutdown_linux_vm(vm_name)
        self._test_content_logger.end_step_logger(14, True)
        self._common_content_lib.perform_os_reboot (self.reboot_timeout)
        self._test_content_logger.start_step_logger(15)
        self._common_content_lib.execute_sut_cmd("./Setup_Randomize_DSA_Conf.sh -d", "./Setup_Randomize_DSA_Conf.sh -d",
                                                 self.reboot_timeout, self.TEST_CASE_CONTENT_PATH)
        self._test_content_logger.end_step_logger(15, True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        This method is used to remove the VM and delete the file created while executing the TC
        """
        super(PiSprDsaHiConfiguraitonGuestVMMdevL, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiSprDsaHiConfiguraitonGuestVMMdevL.main() else Framework.TEST_RESULT_FAIL)
