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
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions


class VirtualizationCentOsKvmCrossSocketTopologySiovStress(VirtualizationCommon):
    """
    Phoenix ID: 16014126249
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Install virtualization_centos_kvm_scalable_iov_gen4_nic_stress_16vm-install if not present.
    2. Copy RHEL ISO image to SUT under '/var/lib/libvirt/images'.
    4. Create VM.
    5. Verify VM is running.
    6. Attach SIOV mdev instance to VM
    7. Stress test mdev instance using iperf
    """
    TEST_CASE_ID = ["p16014126249", "Virtualization-CentOS-KVM-Cross-Socket-Topology-SIOV-Stress"]
    STEP_DATA_DICT = {
        1: {'step_details': "Check if SIOV capable PCIe network device is present.",
            'expected_results': "ColumbiaVille Network device with SRIOV Function"},
        2: {'step_details': "Assign static IPs to all network devices in list connected to each socket",
            'expected_results': "Static IPs assigned successfully"},
        3: {'step_details': "Build ice Driver for CVL device",
            'expected_results': "CVL driver build completed"},
        4: {'step_details': "Create mdev instance based on uuid generated to all NICs connected to each socket",
            'expected_results': "mdev instance created successfully"},
        5: {'step_details': "Create 2 CentOS virtual machine based on given name",
            'expected_results': "virtual machine created successfully"},
        6: {'step_details': "Attach mdev instance to VM",
            'expected_results': "Successfully attached mdev instance to VM"},
        7: {'step_details': "Assign Static IP to CentOS VM network adapter",
            'expected_results': "Assigned Static IP to VM network adapter"},
        8: {'step_details': "Configure iperf tool and start nic stress across VM's",
            'expected_results': "iperf siov nic stress completed successfully"},
        }
    BIOS_CONFIG_FILE = "virtualization_centos_siov_cross_socket_topology.cfg"
    VM = [VMs.CENTOS] * 2
    NUMBER_OF_VMS = 2
    DEVICE_INFO = "vfio-pci,sysfsdev=/sys/bus/mdev/devices/{}/"
    IPERF_PORT = 5201
    STORAGE_VOLUME = ["/home"]
    VM_TYPE = "CENTOS"
    UUID_LIST = []
    IP_LIST = []
    IPERF_EXEC_TIME = 10
    GRUB_PARAMETER = "intel_iommu=on,sm_on no5lvl"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationRHELConfigSRIOVVirtualFunctionVM object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationCentOsKvmCrossSocketTopologySiovStress, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        if self.os.os_type != OperatingSystems.LINUX:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):

        self.bios_util.load_bios_defaults()
        self.bios_util.set_bios_knob(bios_config_file=self.BIOS_CONFIG_FILE)
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        self._vm_provider.create_bridge_network("virbr0")
        self.bios_util.verify_bios_knob(bios_config_file=self.BIOS_CONFIG_FILE)

    def execute(self):
        #  To check and enable intel_iommu by using grub menu
        if not self.enable_intel_iommu_by_kernel():
            raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")
        self._test_content_logger.start_step_logger(1)
        network_device_name = self._common_content_configuration.get_columbiaville_nic_device_name()
        nw_device_list = self.get_sriovf_enabled_nw_adapters(network_device_name)
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        opt_dict = self.assign_static_ip_to_nw_adapters(nw_device_list)
        self._test_content_logger.end_step_logger(2, True)
        self._test_content_logger.start_step_logger(3)
        self._vm_provider.cvl_driver_build()
        self._test_content_logger.end_step_logger(3, True)
        self._test_content_logger.start_step_logger(4)
        for index in range(self.NUMBER_OF_VMS):
            uuid = self._vm_provider.create_mdev_instance(index)
            self.UUID_LIST.append(uuid)
        self._test_content_logger.end_step_logger(4, True)
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on CentOS.".format(vm_name))
        self._test_content_logger.start_step_logger(5)
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
            self._test_content_logger.end_step_logger(5, True)
            self.verify_vm_functionality(vm_name, self.VM_TYPE, enable_yum_repo=True)
            self.LIST_OF_VM_NAMES.append(vm_name)
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)
            self.enable_intel_iommu_by_kernel_vm(vm_os_obj, common_content_lib_vm, self.GRUB_PARAMETER)
            self.reboot_linux_vm(vm_name)
            time.sleep(120)

            self._test_content_logger.start_step_logger(6)
            self.attach_mdev_instance_to_vm(vm_name, uuid)
            self._vm_provider.iavf_driver_build_on_vm(vm_os_obj, install_collateral_vm_obj)
            self.verify_vf_in_vm(vm_os_obj)
            self._test_content_logger.end_step_logger(6, True)
            for index in range(self.NUMBER_OF_VMS):
                vm_name = self.VM[index] + "_" + str(index)
                vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
                common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
                self._test_content_logger.start_step_logger(7)
                vf_adapter_name = self.get_virtual_adapter_name_in_vm(common_content_lib_vm)
                ip, subnet = opt_dict[nw_device_list[0]]
                ip = ip[:-2] + str(int(ip[-2:]) + 5 + index)
                port_id = self.IPERF_PORT + index
                sut_ip = self.get_ip(self._common_content_lib)
                self.assign_ip_to_vf_in_vm(vm_os_obj, ip, subnet, vf_adapter_name, vm_name)
                self._test_content_logger.end_step_logger(7, True)
                self._test_content_logger.start_step_logger(8)
                self._log.info("Executing iperf test on SUT and VM's")
                self.execute_sut_as_iperf_server(self.IPERF_EXEC_TIME, port=port_id)
                self.execute_iperf_client(self.IPERF_EXEC_TIME, port_id, sut_ip, common_content=common_content_lib_vm)
                self._test_content_logger.end_step_logger(8, True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationCentOsKvmCrossSocketTopologySiovStress, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationCentOsKvmCrossSocketTopologySiovStress.main()
             else Framework.TEST_RESULT_FAIL)
