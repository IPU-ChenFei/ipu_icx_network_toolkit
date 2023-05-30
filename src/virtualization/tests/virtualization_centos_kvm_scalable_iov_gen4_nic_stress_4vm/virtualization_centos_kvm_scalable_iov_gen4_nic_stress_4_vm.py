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
import threading
import subprocess
import re

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions


class VirtualizationCentOsKvmScalableIovGen4NicStress4Vm(VirtualizationCommon):
    """
    Phoenix ID: 16013376174
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Install virt-install if not present.
    2. Copy RHEL ISO image to SUT under '/var/lib/libvirt/images'.
    4. Create VM.
    5. Verify VM is running.
    """
    TEST_CASE_ID = ["p16013376174", "Virtualization-CentOs-Kvm-ScalableIov-Gen4-Nic-Stress-4vm"]
    STEP_DATA_DICT = {
        1: {'step_details': "Check if SIOV capable PCIe network device is present.",
            'expected_results': "ColumbiaVille Network device with SRIOV Function"},
        2: {'step_details': "Assign static IPs to all network devices in list",
            'expected_results': "Static IPs assigned successfully"},
        3: {'step_details': "Build ice Driver for CVL device",
            'expected_results': "CVL driver build completed"},
        4: {'step_details': "Create 4 CentOS virtual machine based on given name",
            'expected_results': "virtual machine created successfully"},
        5: {'step_details': "Create mdev instance based on uuid generated",
            'expected_results': "mdev instance created successfully"},
        6: {'step_details': "Attach mdev instance to VM",
            'expected_results': "Successfully attached mdev instance to VM"},
        7: {'step_details': "Assign Static IP to QEMU VM network adapter",
            'expected_results': "Assigned Static IP to VM network adapter"},
        8: {'step_details': "Configure iperf tool and start nic stress",
            'expected_results': "iperf siov nic stress completed successfully"},
    }

    BIOS_CONFIG_FILE = "virtualization_centos_kvm_scalable_iov_bios.cfg"
    NUMBER_OF_VMS = [VMs.CENTOS]*4  # 1, tested with 1
    DEVICE_INFO = "vfio-pci,sysfsdev=/sys/bus/mdev/devices/{}/"
    IPERF_EXEC_TIME = 5
    IPERF_SERVER_CMD = "iperf3 -s"
    IPERF_CLIENT_CMD = "iperf3 -c {} -t {}"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationRHELConfigSRIOVVirtualFunctionVM object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationCentOsKvmScalableIovGen4NicStress4Vm, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        if self.os.os_type != OperatingSystems.LINUX:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):

        self.bios_util.load_bios_defaults()
        self.bios_util.set_bios_knob(bios_config_file=self.BIOS_CONFIG_FILE)
        self._vm_provider.create_bridge_network("virbr0")
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
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

        for index in range(len(self.NUMBER_OF_VMS)):
            vm_name = self.NUMBER_OF_VMS[index] + "_" + str(index)
            self._log.info(" Creating VM:{} on CentOS".format(vm_name))
            self._test_content_logger.start_step_logger(4)
            self.create_vm(vm_name, self.NUMBER_OF_VMS[index], mac_addr=True)
            self.verify_vm_functionality(vm_name, self.NUMBER_OF_VMS[index])
            self.LIST_OF_VM_NAMES.append(vm_name)
            vm_os_obj = self.create_vm_host(vm_name, self.NUMBER_OF_VMS[index])
            common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)
            self._test_content_logger.end_step_logger(4, True)
            self._test_content_logger.start_step_logger(5)
            uuid = self._vm_provider.create_mdev_instance(index)
            self._log.info("uuid info:{}".format(uuid))
            self._test_content_logger.end_step_logger(5, True)
            self._test_content_logger.start_step_logger(6)
            self.attach_mdev_instance_to_vm(vm_name, uuid)
            self._test_content_logger.end_step_logger(6, True)
            self._test_content_logger.start_step_logger(7)
            self._vm_provider.iavf_driver_build_on_vm(vm_os_obj, install_collateral_vm_obj)
            self.verify_vf_in_vm(vm_os_obj)
            vf_adapter_name = self.get_virtual_adapter_name_in_vm(common_content_lib_vm)
            ip, subnet = opt_dict[nw_device_list[0]]
            ip = ip[:-2] + str(int(ip[-2:]) + 5 + index)
            self.assign_ip_to_vf_in_vm(vm_os_obj, ip, subnet, vf_adapter_name, vm_name)
            self._log.info("Executing iperf test on SUT and VM's")
            server_thread = threading.Thread(target=self.execute_iperf_server)
            client_thread = threading.Thread(target=self.execute_iperf_client,
                                             args=(common_content_lib_vm, self.IPERF_EXEC_TIME))
            server_thread.start()
            client_thread.start()
            self._test_content_logger.end_step_logger(7, True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationCentOsKvmScalableIovGen4NicStress4Vm, self).cleanup(return_status)

    def execute_iperf_server(self):
        """
        This Method is Used to Set Sut as Iperf Server and verify whether there is any data loss at server side..

        :raise content_exceptions.TestFail: If there is any data loss at Server Side.
        """
        self._log.info("Set Sut as Iperf Server")
        cmd_output = subprocess.call(self.IPERF_SERVER_CMD, timeout=self.IPERF_EXEC_TIME, shell=True)
        self._log.debug("Sut is Successfully Set as Iperf Server and perf Response from Server is : {}".format(
            str(cmd_output)))
        if re.search(self.REGEX_FOR_DATA_LOSS, str(cmd_output)):
            raise content_exceptions.TestFail("Data Loss is Observed at Server Side")
        self._log.info("There is No Data Loss at Server Side")

    def execute_iperf_client(self, common_content_vm_obj, exec_time):
        """
        This Method is Used to Execute VM as a Iperf Client and Verify Whether there is any Data Loss at Client Side.

        :param common_content_vm_obj: common_content_lib object for VM to execute commands
        :param exec_time: Iperf Execution Time.
        :raise content_exceptions.TestFail: If there is any Data Loss at Client Side.
        """
        sut_ip = self.get_ip(self._common_content_lib)
        self._log.info("Set VM as Iperf Client")
        exec_time_min = 5
        if exec_time_min < exec_time:
            exec_time_min = exec_time
        cmd_output = common_content_vm_obj.execute_sut_cmd(self.IPERF_CLIENT_CMD.format(
            sut_ip, exec_time_min),
            self.IPERF_CLIENT_CMD.format(sut_ip, exec_time_min), exec_time_min+self._command_timeout)
        self._log.debug("VM is Successfully Set as Iperf Client and Iperf Response from Client is : {}".format(
            cmd_output))
        if re.search(self.REGEX_FOR_DATA_LOSS, cmd_output):
            raise content_exceptions.TestFail("Data Loss is Observed at Client Side")
        self._log.info("There is No Data Loss at Client Side")


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationCentOsKvmScalableIovGen4NicStress4Vm.main()
             else Framework.TEST_RESULT_FAIL)
