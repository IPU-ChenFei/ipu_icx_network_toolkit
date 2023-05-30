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
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.virtualization.virtualization_common import VirtualizationCommon
from src.virtualization.dsa_common_virtualization import DsaBaseTest_virtualization
from src.virtualization.base_qat_util import BaseQATUtil
from src.lib.install_collateral import InstallCollateral
from src.lib.common_content_lib import CommonContentLib
from src.provider.vm_provider import VMs


class SprIaxGuestVMPassThrough(VirtualizationCommon, DsaBaseTest_virtualization):
    """
    Phoenix ID : 16014810061
    The purpose of this test case is to validate the IAX passthrough for guest VM and run workload.
    Then execute IAXTEST on all available work-queues in guest
    1. Enable Intel VT for Directed I/O (VT-d), Interrupt Remapping, PCIe ENQCMD  VMX on BIOS.
    2. IOMMU scalable mode need to be enabled in.
    3. Install the depedencies packages on the host
    4. Enable IAX and Workqueues on host
    5. Enable Intel IOMMU paramters on VM
    6. Enable Workqueue and associate UUID to WQ.
    7. Install the depedencies packages on the VM
    8. Configure IAX on guest.
    9. Run workload to attached device as MDEV.
    """
    NUMBER_OF_VMS = 1
    VM = [VMs.CENTOS] * 1
    VM_TYPE = "CENTOS"
    TEST_CASE_ID = ["16014810061", "PI_SPR_IAX_GuestVM_Passthrough"]
    BIOS_CONFIG_FILE = "../vtd_bios_config.cfg"
    STORAGE_VOLUME = ["/home"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Install and verify Bios knobs for IAX',
            'expected_results': 'Bios knobs installed and verified successfully'},
        2: {'step_details': 'Enable IOMMU using kernel command line params in SUT',
            'expected_results': 'Kernel command line params updated to enable iommu in SUT'},
        3: {'step_details': 'Install and configure the yum repo config file',
            'expected_results': 'Yum repo configured successfully'},
        4: {'step_details': 'Install the IAX depemdencies, may be kernel sources as well',
            'expected_results': 'All packages installed successfully'},
        5: {'step_details': 'Check and Install the IAX driver and accel_config package',
            'expected_results': 'IAX driver and accel_config built and installed'},
        6: {'step_details': 'Check IAX device details, dbdf and bind vfio driver to guest',
            'expected_results': 'IAX devices detailes fetched and IAX device binded to guest vfio-pci driver'},
        7: {'step_details': 'Create the Storage Pool for VMs',
            'expected_results': 'Storage Pools created successfully'},
        8: {'step_details': 'Create the VM using storage pool',
            'expected_results': 'VM creation successfully done'},
        9: {'step_details': 'Enable IOMMU using kernel command line params in VM',
            'expected_results': 'Kernel command line params updated to enable iommu in VM'},
        10: {'step_details': 'Start creating the VMs as per the names created',
             'expected_results': 'All VMs created with mdev devices nd dlb2 driver and libdlb'},
        11: {'step_details': 'Install and configure the yum repo config file in VM and install IAX dependencies',
             'expected_results': 'Yum repo configured and IAX related package dependencies installed successfully in VM'},
        12: {'step_details': 'Install IAX driver/accel_config in VM, verify it installed or not',
             'expected_results': 'IAX driver/accel_config are installed successfully in VM'},
        13: {'step_details': 'Attach the created IAX device to VM',
             'expected_results': 'Created IAX device attached to VM'},
        14: {'step_details': 'Execute opcode and DMA test',
             'expected_results': 'IAX workload and opcode executed successfully'},
        15: {'step_details': 'Detach the created IAX device from VM',
             'expected_results': 'Passthrough IAX device detached from VM'},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of TC Class, TestContentLogger and CommonContentLib

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.virtualization_IAX_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(SprIaxGuestVMPassThrough, self).__init__(test_log, arguments, cfg_opts, self.virtualization_IAX_bios_knobs)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(test_log, self.os, cfg_opts)
        self._cfg_opt = cfg_opts
        self._arg_tc = arguments
        self._test_log = test_log

    def prepare(self):
        # type: () -> None
        """Test preparation/setup """

        if self.os.os_type == OperatingSystems.LINUX:
            self._log.info("We have Linux OS for test case... proceeding further..")
        else:
            raise content_exceptions.TestFail("Target is not booted with Linux")
        self._test_content_logger.start_step_logger(1)
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        self._vm_provider.create_bridge_network("virbr0")
        super(SprIaxGuestVMPassThrough, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This validates the I passthrough for guest VM and run workload.
        Then execute IAX TEST on all available work-queues in guest

        1. Enable Intel VT for Directed I/O (VT-d), Interrupt Remapping, PCIe ENQCMD  VMX on BIOS.
        2. IOMMU scalable mode need to be enabled in.
        3. Install the depedencies packages on the host
        4. Enable IAX and Workqueues on host
        5. Enable Intel IOMMU paramters on VM
        6. Enable Workqueue and associate vfio to WQ.
        7. Install the depedencies packages on the VM
        8. Configure IAX on guest.
        9. Run workload to attached device as MDEV.
        :return: True if test case pass else fail
        """
        self._test_content_logger.start_step_logger(2)
        # Enabling the Intel iommu in kernel
        if not self.enable_intel_iommu_by_kernel():
            raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self.get_yum_repo_config(self.os, self._common_content_lib, os_type="centos")
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        dependency_packages = "json-c-devel kmod-devel libuuid-devel libudev-devel systemd-devel xmlto*"
        self.yum_virt_install(package_group = dependency_packages, common_content_lib=self._common_content_lib, flags="--nobest --skip-broken")

        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        # lsmod grep command for idxd device
        self.check_idxd_device()
        # Determine the IAX device state
        self.determine_device_state()
        # IAX device basic check
        # Check IAX devices
        self.verify_dsa_driver_directory()
        # Install accel config tool
        self._install_collateral.install_verify_accel_config()
        spr_dir_path = self._install_collateral.get_spr_path()
        self._install_collateral.configure_iax(spr_dir_path)
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        dbdf_list = self.get_vf_device_dbdf_by_devid(devid="0b25", common_content_object=self._common_content_lib)
        if len(dbdf_list) <= 0:
            raise content_exceptions.TestFail("Failed: No IAX device found in system")
        self.load_vfio_driver()
        for index in range(self.NUMBER_OF_VMS):
            self.host_vfio_accel_driver_unbind(dbsf_value=dbdf_list[index],
                                         common_content_object=self._common_content_lib)
            self.guest_vfio_pci_accel_driver_bind(dbsf_value=dbdf_list[index], accel_type = "iax",
                                            common_content_object=self._common_content_lib)
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)
        self._test_content_logger.end_step_logger(7, return_val=True)

        extra_disk = 2
        vm_sut_obj_list = []
        self._test_content_logger.start_step_logger(8)
        for index in range(0, self.NUMBER_OF_VMS):
            vm_name = self.VM[index] + "_" + str(index)
            self._log.info(" Creating VM:{} on CentOS".format(vm_name))
            self._vm_provider.destroy_vm(vm_name)
            self._test_content_logger.start_step_logger(9)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
            self.create_vm_pool_nested(vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True, pool_id=free_storage_pool,
                                       extra_disk_space=extra_disk)
            # create VM os object
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            self.verify_vm_functionality(vm_name, self.VM[index], enable_yum_repo=True)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm = CommonContentLib(self._test_log, vm_os_obj, self._cfg_opt)
            self._test_content_logger.end_step_logger(9, return_val=True)

            self._test_content_logger.start_step_logger(10)
            grub_param = "intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode='modern',device-iotlb=on,aw-bits=48 intel_iommu=on,sm_on ats_with_iommu_swizzle iommu=pt no5lvl"
            self.enable_intel_iommu_by_kernel_in_vm(vm_name, grub_param=grub_param, common_content_lib=common_content_lib_vm)
            self.reboot_linux_vm(vm_name)
            time.sleep(45)
            self._test_content_logger.end_step_logger(10, return_val=True)

            self._test_content_logger.start_step_logger(11)
            # Installing the dependency packages
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm, os_type="centos")
            self._log.info("Installing dependency package for CentOS VM.")
            dependency_packages = "json-c-devel kmod-devel libuuid-devel libudev-devel systemd-devel xmlto*"

            self.yum_virt_install(package_group=dependency_packages,
                                  common_content_lib=common_content_lib_vm, flags="--nobest --skip-broken")
            self._log.info("IAX dependencies package installation on VM was successfull...")
            self._test_content_logger.end_step_logger(11, return_val=True)

            self._test_content_logger.start_step_logger(12)
            self._install_collateral.install_and_verify_accel_config_vm(common_content_lib_vm)

            self._test_content_logger.end_step_logger(12, return_val=True)

            self._test_content_logger.start_step_logger(13)
            domain_value, bus_value, device_value, function_value = self.get_split_hex_bdf_values_from_dbdf(
                dbdf_list[index])
            self.attach_vfiopci_device_using_dbdf_to_vm(vm_name, domain_value, bus_value, device_value, function_value)
            self._test_content_logger.end_step_logger(13, return_val=True)

        self._test_content_logger.end_step_logger(8, return_val=True)
        #==========================================================================
        self._test_content_logger.start_step_logger(14)
        for index, vm_name, each_vm_obj in zip(range(len(self.LIST_OF_VM_NAMES)), self.LIST_OF_VM_NAMES,
                                               vm_sut_obj_list):

            spr_dir_path = self._install_collateral.get_spr_path(common_content_lib_vm)
            common_content_lib_vm_obj = CommonContentLib(self._test_log, each_vm_obj, self._cfg_opt)
            self.execute_opcode_test(spr_file_path=spr_dir_path,common_content_lib_vm=common_content_lib_vm_obj, vm_obj=each_vm_obj, device='iax')
            self.execute_dma_test(spr_file_path=spr_dir_path, common_content_lib_vm=common_content_lib_vm_obj, vm_obj=each_vm_obj, device='iax')

        self._test_content_logger.end_step_logger(14, return_val=True)

        self._test_content_logger.start_step_logger(15)
        for index, vm_name, in zip(range(len(self.LIST_OF_VM_NAMES)), self.LIST_OF_VM_NAMES):
            domain_value, bus_value, device_value, function_value = self.get_split_hex_bdf_values_from_dbdf(
                dbdf_list[index])
            self.detach_vfiopci_device_using_dbdf_from_vm(vm_name, domain_value, bus_value, device_value, function_value)
        self._test_content_logger.end_step_logger(15, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(SprIaxGuestVMPassThrough, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SprIaxGuestVMPassThrough.main() else Framework.TEST_RESULT_FAIL)
