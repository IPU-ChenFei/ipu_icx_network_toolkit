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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.provider.vm_provider import VMs
from src.lib.content_exceptions import *
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib


class PiVirtualizationPassThroughUsbStorageW(VirtualizationCommon):
    """
    HPALM ID: 79618 - PI_Virtualization_PassThroughUSB_W
    The purpose of this test case is making sure the creation of VMs guests on Hyper-V.
    1. Create VM.
    2. Verify VM is running.
    3. Make USB Storage Device offline on SUT.
    4. Attach the USB Storage Device to VM.
    5. Copy file to attached USB Storage Device in VM
    """
    TC_ID = ["H79620", "PI_Virtualization_PassThroughUSB_W"]
    BIOS_CONFIG_FILE = r"virtualization_hyper_v_basic_bios_knobs.cfg"
    VM = [VMs.WINDOWS] * 2
    VM_TYPE = "RS5"
    VSWITCH_NAME = "ExternalSwitch"
    ADAPTER_NAME = None
    BUS_TYPE = "USB"
    SCSI_CONTROLLER = "SAS"
    DISK_LIST_VALUE = 0

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiVirtualizationPassThroughUsbStorageW object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiVirtualizationPassThroughUsbStorageW, self).__init__(test_log, arguments, cfg_opts)
        self.bios_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        self._cfg_opt = cfg_opts
        if self.os.os_type != OperatingSystems.WINDOWS:
            raise TestNotImplementedError("This Test case is not supported on {} OS".format(self.os.os_type))

    def prepare(self):  # type: () -> None
        """
        1. Enabling BIOS knobs VMX and VT-d
        2. Install Hyper-V module on SUT
        3. Create vSwitch from existing NIC
        """
        self.set_and_verify_bios_knobs(bios_file_path=self.bios_file_path)
        self._vm_provider.install_vm_tool()
        self._vm_provider.create_bridge_network(self.VSWITCH_NAME)

    def execute(self):
        """
        1. Create VM.
        2. Verify VM is running.
        3. Make USB Storage Device offline on SUT.
        4. Attach the USB Storage Device to VM.
        5. Copy file to attached USB Storage Device in VM
        """
        for index in range(len(self.VM)):
            # Creates VM names dynamically according to the OS and its resources
            self._log.info("Creating VM on Hyper V")
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_hyperv_vm(vm_name, self.VM_TYPE)  # Create VM function
            self._vm_provider.wait_for_vm(vm_name)  # Wait for VM to boot
            # Assign Network Adapter to VM using Direct Assignment method
            self._vm_provider.add_vm_network_adapter(self.NETWORK_ASSIGNMENT_TYPE, vm_name, self.ADAPTER_NAME,
                                                     self.VSWITCH_NAME)
            self.verify_hyperv_vm(vm_name, self.VM_TYPE)
            self.create_ssh_vm_object(vm_name, copy_open_ssh=True)
            common_content_lib_sut = CommonContentLib(self._log, self.os, self._cfg_opt)
            device_id = self._vm_provider.enumerate_storage_device(self.BUS_TYPE, index, common_content_lib_sut)
            self._vm_provider.set_disk_offline(device_id, common_content_lib_sut)
            self._vm_provider.add_storage_device_to_vm(vm_name, device_id, storage_size=None)
            vm_os_obj = self.windows_vm_object(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, None)
            vm_device_list = self._vm_provider.enumerate_storage_device(self.SCSI_CONTROLLER, self.DISK_LIST_VALUE,
                                                                        common_content_lib_vm_obj)
            self._vm_provider.set_disk_online(vm_device_list, common_content_lib_vm_obj)
            pci_file_path = self._vm_provider.copy_file_to_vm_storage_device(
                vm_device_list, vm_os_obj, common_content_lib_vm_obj)
            if not vm_os_obj.check_if_path_exists(pci_file_path):
                raise TestError("Fail to verify {} file presence in VM:{}".format(pci_file_path, vm_name))
            self._log.info("Successfully verified {} file presence in VM:{}".format(pci_file_path, vm_name))
            self._log.info("Successfully copied the Test file to VM USB storage device")
            self._vm_provider.destroy_vm(vm_name)
            self.LIST_OF_VM_NAMES.remove(vm_name)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(PiVirtualizationPassThroughUsbStorageW, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiVirtualizationPassThroughUsbStorageW.main()
             else Framework.TEST_RESULT_FAIL)
