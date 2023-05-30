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

class VirtualizationCentOSDSAPassthruGuestVMWorkload(VirtualizationCommon, DsaBaseTest_virtualization):
    """
    Phoenix ID : 16013977440
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
    NUMBER_OF_VMS = 1
    VM = [VMs.CENTOS] * 1
    VM_TYPE = "CENTOS"
    TEST_CASE_ID = ["P16013977440", "VirtualizationCentOSDSAPassthruGuestVMWorkload"]
    BIOS_CONFIG_FILE = "virt_dsa_passthru_guest_vmwl_biosknobs.cfg"
    STORAGE_VOLUME = ["/home"]
    DSA_LOAD_TEST_TIME = 7200
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
        6: {'step_details': 'Check DSA device details, dbdf and bind vfio driver to guest',
            'expected_results': 'DSA devices detailes fetched and dsa device binded to guest vfio-pci driver'},
        7: {'step_details': 'Create the Storage Pool for VMs',
            'expected_results': 'Storage Pools created successfully'},
        8: {'step_details': 'Create the VM using storage pool',
            'expected_results': 'VM creation successfully done'},
        9: {'step_details': 'Enable IOMMU using kernel command line params in VM',
            'expected_results': 'Kernel command line params updated to enable iommu in VM'},
        10: {'step_details': 'Start creating the VMs as per the names created',
             'expected_results': 'All VMs created with mdev devices nd dlb2 driver and libdlb'},
        11: {'step_details': 'Install and configure the yum repo config file in VM and install DSA dependencies',
             'expected_results': 'Yum repo configured and DSA related package dependencies installed successfully in VM'},
        12: {'step_details': 'Install DSA driver/accel_config in VM, verify it installed or not',
             'expected_results': 'DSA driver/accel_config are installed successfully in VM'},
        13: {'step_details': 'Attach the created DSA device to VM',
             'expected_results': 'Created DSA device attached to VM'},
        14: {'step_details': 'Execute DSA work load for 2 hours',
             'expected_results': 'DSA workload executed successfully for 2 hours'},
        15: {'step_details': 'Detach the created DSA device from VM',
             'expected_results': 'Passthrough DSA device detached from VM'},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of TC Class, TestContentLogger and CommonContentLib

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.virtualization_dsa_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(VirtualizationCentOSDSAPassthruGuestVMWorkload, self).__init__(test_log, arguments, cfg_opts, self.virtualization_dsa_bios_knobs)
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
        super(VirtualizationCentOSDSAPassthruGuestVMWorkload, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This validates the DSA passthrough for guest VM and run workload.
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
        :return: True if test case pass else fail
        """
        self._test_content_logger.start_step_logger(2)
        # Enabling the Intel iommu in kernel
        if not self.enable_intel_iommu_by_kernel():
            raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")
        # unbind the QAT devices by uloading vfio driver, in case system not rebooted
        self.unload_vfio_driver()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)

        self._log.info("Installing dependency package for CentOS: {}".format(self.INSTALL_DEPENDENCY_PACKAGE))

        list_of_linux_os_commands = [r"yum remove -y libuuid-devel;echo y",
                                     r"yum remove -y kmod-devel;echo y",
                                     r"yum remove -y libudev-devel;echo y",
                                     r"yum remove -y xmlto*;echo y",
                                     r"yum remove -y systemd-devel;echo y",
                                     r"yum remove -y kernel-spr-bkc-pc-modules-internal;echo y",
                                     r"yum remove -y json-c-devel"]

        for command_line in list_of_linux_os_commands:
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
        list_of_linux_os_commands = [r"yum install -y libuuid-devel;echo y",
                                     r"yum install -y kmod-devel;echo y",
                                     r"yum install -y libudev-devel;echo y",
                                     r"yum install -y xmlto*;echo y",
                                     r"yum install -y systemd-devel;echo y",
                                     r"yum install -y kernel-spr-bkc-pc-modules-internal;echo y",
                                     r"yum install -y json-c-devel"]

        for command_line in list_of_linux_os_commands:
            cmd_result = self.os.execute(command_line, self._command_timeout)
            if cmd_result.cmd_failed():
                log_error = "Failed to run command '{}' with " \
                            "return value = '{}' and " \
                            "std_error='{}'..".format(command_line, cmd_result.return_code, cmd_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)
            else:
                self._log.info("The command '{}' executed successfully..".format(command_line))

        self._test_content_logger.end_step_logger(3, return_val=True)
        self._test_content_logger.start_step_logger(4)
        release_cmd = "uname -a | grep spr"
        output = self.os.execute(release_cmd, self._command_timeout)
        uname_output = output.stdout
       # Kernel source have to be installed as well but after checking the kernel version in SUT
       # kernel_source_install = "https://emb-pub.ostc.intel.com/overlay/centos/8.4.2105/202109221317/repo/x86_64/kernel-next-server-devel-5.12.0-2021.05.07_39.el8.x86_64.rpm"
       # self._install_collateral.yum_install(package_name=kernel_source_install)

        if 'spr' in uname_output:
            self._log.info("The system is in SPR, hence utilty is part of the BKC")
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
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        spr_dir_path = self._install_collateral.get_spr_path()
        self._install_collateral.configure_dsa_ca(spr_dir_path)
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        dbdf_list = self.get_vf_device_dbdf_by_devid(devid="0b25", common_content_object=self._common_content_lib)
        if len(dbdf_list) <= 0:
            raise content_exceptions.TestFail("Failed: No DSA device found in system")
        self.load_vfio_driver()
        for index in range(self.NUMBER_OF_VMS):
            self.host_vfio_accel_driver_unbind(dbsf_value=dbdf_list[index],
                                               common_content_object=self._common_content_lib)
            self.guest_vfio_pci_accel_driver_bind(dbsf_value=dbdf_list[index], accel_type="dsa",
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
            self.create_vm_pool_nested(vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True,
                                       pool_id=free_storage_pool,
                                       extra_disk_space=extra_disk)
            # create VM os object
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            self.verify_vm_functionality(vm_name, self.VM[index], enable_yum_repo=True)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm = CommonContentLib(self._test_log, vm_os_obj, self._cfg_opt)
            self._test_content_logger.end_step_logger(9, return_val=True)

            self._test_content_logger.start_step_logger(10)
            common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            grub_param = "intel_iommu=on,sm_on iommu=on no5lvl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce"
            self.enable_intel_iommu_by_kernel_in_vm(vm_name, grub_param=grub_param,
                                                    common_content_lib=common_content_lib_vm)
            self.reboot_linux_vm(vm_name)
            time.sleep(300)
            self._test_content_logger.end_step_logger(10, return_val=True)

            self._test_content_logger.start_step_logger(11)
            # Installing the dependency packages
            install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)

            if 'spr' in uname_output:
                self._log.info("The system is in SPR, hence utilty is part of the BKC")
            else:
                install_collateral_vm_obj.install_and_verify_accel_config_vm(common_content_lib_vm)
            self._test_content_logger.end_step_logger(11, return_val=True)

            self._test_content_logger.start_step_logger(12)
            PROXY_COMMANDS = "export http_proxy=http://proxy-iind.intel.com:911;export HTTP_PROXY=http://proxy-iind.intel.com:911;export https_proxy=http://proxy-iind.intel.com:911;export HTTPS_PROXY=http://proxy-iind.intel.com:911;export no_proxy='localhost, 127.0.0.1, intel.com';yum remove -y libuuid-devel;yum remove -y kmod-devel;yum remove -y libudev-devel;yum remove -y xmlto*;yum remove -y systemd-devel;yum remove -y kernel-spr-bkc-pc-modules-internal;yum remove -y json-c-devel;yum install -y libuuid-devel;yum install -y kmod-devel;yum install -y libudev-devel;yum install -y xmlto*;yum install -y systemd-devel;yum install -y kernel-spr-bkc-pc-modules-internal;yum install -y json-c-devel;"
            common_content_lib_vm.execute_sut_cmd(PROXY_COMMANDS, "Enabling Proxy in System", 400)
            time.sleep(150)
            self._log.info("DSA dependencies package installation on VM was successfull...")

            self._test_content_logger.end_step_logger(12, return_val=True)

            self._test_content_logger.start_step_logger(13)
            domain_value, bus_value, device_value, function_value = self.get_split_hex_bdf_values_from_dbdf(
                dbdf_list[index])
            self.attach_vfiopci_device_using_dbdf_to_vm(vm_name, domain_value, bus_value, device_value, function_value)
            self._test_content_logger.end_step_logger(13, return_val=True)

        self._test_content_logger.end_step_logger(8, return_val=True)
        # ==========================================================================

        self._log.info("Run the DSA load test for 7200 seconds in all guest VMs")

        self._test_content_logger.start_step_logger(14)
        start_time = time.time()
        seconds = self.DSA_LOAD_TEST_TIME
        while True:
            current_time = time.time()
            elapsed_time = current_time - start_time

            for index, vm_name, each_vm_obj in zip(range(len(self.LIST_OF_VM_NAMES)), self.LIST_OF_VM_NAMES,
                                                   vm_sut_obj_list):
                spr_dir_path = self._install_collateral.get_spr_path(common_content_lib_vm)
                common_content_lib_vm_obj = CommonContentLib(self._test_log, each_vm_obj, self._cfg_opt)
                self._install_collateral.run_dsa_workload_on_all_wq_in_vm(spr_dir_path, common_content_lib_vm_obj,
                                                                          each_vm_obj)

            if elapsed_time > seconds:
                self._log.info("Finished DSA load test after: " + str(int(elapsed_time)) + " seconds")
                break
        self._test_content_logger.end_step_logger(14, return_val=True)

        self._test_content_logger.start_step_logger(15)
        for index, vm_name, in zip(range(len(self.LIST_OF_VM_NAMES)), self.LIST_OF_VM_NAMES):
            domain_value, bus_value, device_value, function_value = self.get_split_hex_bdf_values_from_dbdf(
                dbdf_list[index])
            self.detach_vfiopci_device_using_dbdf_from_vm(vm_name, domain_value, bus_value, device_value,
                                                          function_value)
        self._test_content_logger.end_step_logger(15, return_val=True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationCentOSDSAPassthruGuestVMWorkload, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationCentOSDSAPassthruGuestVMWorkload.main() else Framework.TEST_RESULT_FAIL)
