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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.lib.os_lib import WindowsCommonLib
from src.lib.test_content_logger import TestContentLogger
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib


class VirtualizationHyperVConfigureTestSriov(VirtualizationCommon):
    """
    Phoenix ID: 18014074405-Virtualization - Hyper-V - Configure and test SR-IOV
    """
    TEST_CASE_ID = ["P18014074405",
                    "Virtualization - Hyper-V - Configure and test SR-IOV"]
    STEP_DATA_DICT = {
        1: {'step_details': "Create VSWITCH and Enable SRIOV .",
            'expected_results': "Successfully created VSWITCH and enabled SRIOV"},
        2: {'step_details': "Create the VM with VM name",
            'expected_results': "VM created and verified"},
        3: {'step_details': "Add VM ethernet adapter",
            'expected_results': "Successfully added VM ethernet adapter"},
        4: {'step_details': "Assign Static IP to the Gen 4 card ethernet adapter",
            'expected_results': "Successfully Assigned Static IP to the Gen4 card "
                                "ethernet adapter"},
        5: {'step_details': "Execute the PING test from SUT to Gen4 card",
            'expected_results': "PING test passed"},
    }
    NUMBER_OF_VMS = 1
    VM = [VMs.WINDOWS]
    VM_TYPE = "RS5"
    BIOS_CONFIG_FILE = "virtualization_hyper_v_configure_and_test_sriov.cfg"
    NETWORK_ASSIGNMENT_TYPE = "SRIOV"
    VSWITCH_NAME_ECARD = "NEW_VSWITCH"
    VSWITCH_NAME = "ExternalSwitch"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationHyperVConfigureTestSriov object.

        :param test_log: Used for. debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: Test NotImplemented Error
        """
        # calling base class init
        self.bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(VirtualizationHyperVConfigureTestSriov, self).__init__(test_log, arguments, cfg_opts,
                                                                     self.bios_config_file)
        self._windows_common_lib = WindowsCommonLib(self._log, self.os)
        self.VM_STATIC_IP = self._common_content_configuration.get_vm_static_ip()
        self.SUBNET_MASK = self._common_content_configuration.get_subnet_mask()
        self.GATEWAY_IP = self._common_content_configuration.get_gateway_ip()
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        if self.os.os_type != OperatingSystems.WINDOWS:
            raise TestNotImplementedError("This Test case is not supported on {} OS".format(self.os.os_type))

    def prepare(self):  # type: () -> None
        """
        1. Enabling BIOS knobs
        2. Add the regedit values
        3. Install Hyper-V module on SUT
        """
        try:
            self.bios_util.load_bios_defaults()
            self.bios_util.set_bios_knob(bios_config_file=self.bios_config_file)
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
            self.bios_util.verify_bios_knob(bios_config_file=self.bios_config_file)
        except Exception as ex:
            self._log.info("Exception Occurred: {}".format(ex))
            self.os.wait_for_os(self.reboot_timeout)
        self._vm_provider.create_bridge_network(self.VSWITCH_NAME)
        self._vm_provider.execute_reg_edit()
        self._vm_provider.stop_net_vmms()
        self._vm_provider.start_net_vmms()
        self._vm_provider.install_vm_tool()

    def execute(self):
        """
        1. Create Virtual Funcation on Hyper-V
        2. Enabled SRIOV in Hyper-V
        3. Create VM on Hyper-V Module
        4. Assign the SRIOV to the Gen4 card network adapter of the hyper-v module
        5. Do Ping test from the SUT for the above network card

        :return: True
        """
        network_device_name = self._common_content_configuration.get_columbiaville_nic_device_name()
        vm_physical_adapter = self._windows_common_lib.get_network_adapter_name(network_device_name)
        self._test_content_logger.start_step_logger(1)
        self._vm_provider.enable_sriov(network_device_name)
        self._test_content_logger.end_step_logger(1, True)
        for index in range(self.NUMBER_OF_VMS):
            self._test_content_logger.start_step_logger(2)
            self._log.info("Creating VM on Hyper V")
            vm_name = self.VM[index] + "_" + str(index)+"K"
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_hyperv_vm(vm_name, self.VM_TYPE)  # Create VM function
            self._vm_provider.wait_for_vm(vm_name)  # Wait for VM to boot
            self._test_content_logger.end_step_logger(2, True)
            self._test_content_logger.start_step_logger(3)
            #Attaching On-board Nic from Vswitch to VM
            self._vm_provider.add_vm_ethernet_adapter(vm_name, self.VSWITCH_NAME, self.VM_TYPE, mac_addr=True)
            self.verify_hyperv_vm(vm_name, self.VM_TYPE)
            self._vm_provider.enable_vm_integration_service(vm_name)
            self._vm_provider.get_adapter_name_and_create_vswitch_for_sriov(
                self.VSWITCH_NAME_ECARD, vm_physical_adapter, index+1)
            mac_id = self._vm_provider.configure_mac_id_for_sriov_vf()
            self._vm_provider.add_sriov_ethernet_adapter_to_vm(vm_name, self.VSWITCH_NAME, mac_id[index])
            vm_obj = self.windows_vm_object(vm_name, self.VM_TYPE)
            common_content_lib_vm = CommonContentLib(self._log, vm_obj, None)
            vm_sriov_adapter = self._vm_provider.get_sriov_network_adapter_in_vm(common_content_lib_vm, mac_id[index])
            self._vm_provider.set_nic_device_naming_on_vm(vm_name, common_content_lib_vm)
            self._test_content_logger.end_step_logger(3, True)
            self._test_content_logger.start_step_logger(4)
            self._log.info("Assigning static ip to Gen4 card:")
            time.sleep(self._vm_provider.COMMON_TIMEOUT)
            self._vm_provider.assign_static_ip_to_sriov_vf_vm(common_content_lib_vm, vm_sriov_adapter,
                                                              static_ip=self.VM_STATIC_IP, gateway_ip=self.GATEWAY_IP)
            self._vm_provider.get_vm_ip(vm_name)
            self._test_content_logger.end_step_logger(4, True)
            self._vm_provider.start_vm(vm_name)
            self._vm_provider.wait_for_vm(vm_name)
            self._test_content_logger.start_step_logger(5)
            ping_output = common_content_lib_vm.execute_sut_cmd(sut_cmd="ping {}".format(self.VM_STATIC_IP),cmd_str="ping {}".format(self.VM_STATIC_IP),
                                                                execute_timeout=20)
            self._log.info("Ping Output: {}".format(ping_output))
            self._log.info("Successfully pinged {} from VM".format(self.VM_STATIC_IP))
            self._test_content_logger.end_step_logger(5, True)
        return True

    def cleanup(self, return_status):
        """
        This method destroys all the VM's created.
        """
        super(VirtualizationHyperVConfigureTestSriov, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationHyperVConfigureTestSriov.main()
             else Framework.TEST_RESULT_FAIL)
