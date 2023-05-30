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
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.provider_factory import ProviderFactory

from src.provider.vm_provider import VMs
from src.virtualization.dsa_common_virtualization import DsaBaseTest_virtualization
from src.lib.test_content_logger import TestContentLogger
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions
from src.virtualization.base_qat_util import BaseQATUtil
from src.virtualization.tests.dsa.dsa_common import DsaBaseTest
from src.virtualization.virtualization_common import VirtualizationCommon


class IAXSiovSingleVM(VirtualizationCommon, DsaBaseTest_virtualization):
    """
    PHOENIX ID: 16014810166
    PHOENIX TITLE: . PI_IAX_SIOV_SingleVM
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. IOMMU scalable mode need to be enabled in.
    2. Configure Work Queue DSA and IAX.
    3. Enable IAX Device
    4. Enable Workqueue and associate UUID to WQ.
    5. Create mdev and configure guests with mdev for iax.
    6. Run workload to attached device as MDEV.
    """
    BIOS_CONFIG_FILE = "../vtd_bios_config.cfg"
    NUMBER_OF_IAX_VMS = [VMs.CENTOS]
    IAX_VM_NAMES = []
    VM_TYPE = "CENTOS"
    DSA_MDEV = []
    IAX_MDEV = []
    TEST_CASE_ID = ["16014810166", "PI_IAX_SIOV_SingleVM"]
    STORAGE_VOLUME = ["/home"]
    GRUB_PARAM = "intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode='modern',device-iotlb=on,aw-bits=48 " \
                 "intel_iommu=on,sm_on ats_with_iommu_swizzle iommu=pt no5lvl idle=poll"
    LIST_OF_LINUX_OS_COMMANDS = [r"yum install -y libuuid-devel;echo y",
                                 r"yum install -y kmod-devel;echo y",
                                 r"yum install -y libudev-devel;echo y",
                                 r"yum install -y xmlto*;echo y",
                                 r"yum install -y systemd-devel;echo y",
                                 r"yum install -y json-c-devel"]

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
                      6: {'step_details': 'Create VM and enable IAX work queue',
                          'expected_results': 'Should be successfull'},
                      7: {'step_details': 'Run Workload IAX to attached mdev device on VMs',
                          'expected_results': 'Should be successfull'},
                      8: {'step_details': 'Detach all the mdev instances (IAX) from VM',
                          'expected_results': 'Should be successfull'},
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of IAXSiovSingleVM
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.virtualization_siov_stress_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                  self.BIOS_CONFIG_FILE)
        super(IAXSiovSingleVM, self).__init__(test_log, arguments, cfg_opts,
                                              self.virtualization_siov_stress_bios_knobs)
        self._cfg_opts = cfg_opts
        self._log = test_log
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
        super(IAXSiovSingleVM, self).prepare()
        self._vm_provider.create_bridge_network("virbr0")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This function execute
        1. IOMMU scalable mode need to be enabled in.
        2. Enable IAX Device.
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
        for package in self.INSTALL_DEPENDENCY_PACKAGE:
            self._install_collateral.yum_install(package)
        self._test_content_logger.end_step_logger(3, return_val=True)
        self._test_content_logger.start_step_logger(4)
        # Configure DSA and IAX device
        self.check_idxd_device()
        # Determine the dsa device state
        self.determine_device_state(iax=True)
        # DSA device basic check
        self.driver_basic_check()
        # Check DSA devices
        self.verify_iax_driver_directory()
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        # Enable IAX and Workqueues on host
        self._install_collateral.install_verify_accel_config()
        spr_dir_path = self._install_collateral.get_spr_path()
        self._install_collateral.configure_iax(spr_dir_path)
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)

        iax_vm_name = self.NUMBER_OF_IAX_VMS[0] + "_iax"
        self.IAX_VM_NAMES.append(iax_vm_name)

        # Creating VMs for IAX workload
        # for vm_index, vm_name in zip(range(len(self.NUMBER_OF_DSA_VMS)), self.DSA_VM_NAMES):
        self._vm_provider.destroy_vm(iax_vm_name)
        free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL, self.VM_TYPE)
        self.create_vm_generic(iax_vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True,
                               pool_id=free_storage_pool, pool_vol_id=None, cpu_core_list=None, nw_bridge="virbr0")

        self.create_vm_wait()
        time.sleep(self.VM_WAIT_TIME)

        self.verify_vm_functionality(iax_vm_name, self.VM_TYPE)
        vm_os_obj = self.create_vm_host(iax_vm_name, self.VM_TYPE)
        self.create_vm_wait()
        time.sleep(self.VM_WAIT_TIME)

        common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
        self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, os_type="centos")
        self.enable_intel_iommu_by_kernel_in_vm(iax_vm_name, grub_param=self.GRUB_PARAM,
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
            self._log.info("DSA dependencies package installation on VM was successfull...")

        # Install accel config tool
        self._install_collateral.install_verify_accel_config()
        spr_dir_path = self._install_collateral.get_spr_path()
        self._install_collateral.configure_iax(spr_dir_path)
        uuid = self.get_iax_uuid()
        uuid_list = uuid[0]
        self.IAX_MDEV.append(uuid_list)
        self.attach_mdev_instance_to_vm(iax_vm_name, uuid_list)
        spr_dir_path = self._install_collateral.get_spr_path(common_content_lib_vm_obj)
        self._install_collateral.install_and_verify_accel_config_vm(common_content_lib_vm_obj)
        self._install_collateral.run_iax_workload_on_vm(spr_dir_path, common_content_lib_vm_obj, vm_os_obj, ivalue=100,
                                                        jvalue=2)
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        iax_thread = []
        for vm_name in self.IAX_VM_NAMES:
            # Creates VM names dynamically according to the OS and its resources
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            work_load = threading.Thread(target=self._install_collateral.run_iax_dma_test,
                                         args=(common_content_lib_vm_obj, vm_os_obj))
            iax_thread.append(work_load)

        self._test_content_logger.end_step_logger(7, return_val=True)

        self._test_content_logger.start_step_logger(8)
        # # Detaching all the mdev instance assigned to VM
        for vm_index, vm_name in zip(range(len(self.NUMBER_OF_IAX_VMS)), self.IAX_VM_NAMES):
            self.detach_mdev_instance_from_vm(vm_name, self.IAX_MDEV[vm_index])
        self._test_content_logger.end_step_logger(8, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(IAXSiovSingleVM, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if IAXSiovSingleVM.main()
             else Framework.TEST_RESULT_FAIL)
