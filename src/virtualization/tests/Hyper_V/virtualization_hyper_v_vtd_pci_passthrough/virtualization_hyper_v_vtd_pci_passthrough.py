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
from shutil import copy
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_exceptions import *
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib.dtaf_content_constants import IOmeterToolConstants
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon


class VirtualizationHypervVtdPciPassthrough(VirtualizationCommon):
    """
    HPALM ID: 67422
    The purpose of this test case is making sure the creation of VMs guests on Hyper-V.
    1. Create VM.
    2. Verify VM is running.
    3. Make PCIe Storage Device offline on SUT.
    4. Attach the PCIe Storage Device to VM.
    5. Copy file to attached PCIe Storage Device in VM
    """
    TC_ID = ["H67422", "VirtualizationHypervVtdPciPassthrough"]
    VM = [VMs.WINDOWS]
    VM_TYPE = "RS5"
    VSWITCH_NAME = "ExternalSwitch"
    BUS_TYPE = "NVMe"
    SCSI_CONTROLLER = "SAS"
    DISK_LIST_VALUE = 0
    step_data_dict = {
                        1: {'step_details': 'Enable BIOS settings that Vt-x and VT-d are enabled',
                            'expected_results': 'BIOS settings are set to be enabled'},
                        2: {'step_details': 'Install both Hyper V and Windows Server',
                            'expected_results': 'Installation shoud be successfull'},
                        3: {'step_details': 'Create 2 VMs and disable the PCIE device you want to pass to the VM ',
                            'expected_results': 'Disable should be successfull.'},
                        4: {'step_details': 'Add PCIe device to the VMs and ensure VM that is going to recieve PCIe device is turned off ',
                            'expected_results': 'PCI assigned should be successfull.'},
                        5: {'step_details': 'Use any stress tool(IOMeter) to run stress on the PCIe device ',
                            'expected_results': 'Should be successfull.'}
                        }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationHypervVtdPciPassthrough object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationHypervVtdPciPassthrough, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opt = cfg_opts
        if self.os.os_type != OperatingSystems.WINDOWS:
            raise TestNotImplementedError("This Test case is not supported on {} OS".format(self.os.os_type))
        self._test_content_logger = TestContentLogger(test_log, self.TC_ID, self.step_data_dict)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)

    def execute(self):
        """
        1. Create VM.
        2. Verify VM is running.
        3. Make PCIe Storage Device offline on SUT.
        4. Attach the PCIe Storage Device to VM.
        5. Copy file to attached PCIe Storage NVMe Device in VM
        6. Run Stress using any tool(IOmeter)
        """
        # self._vm_provider.create_bridge_network(self.VSWITCH_NAME)
        for index in range(len(self.VM)):
            self._log.info("Creating VM on Hyper V")
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            if self._vm_provider._get_vm_state(vm_name) is False:
               self._vm_provider.destroy_vm(vm_name)
            self.create_hyperv_vm(vm_name, self.VM_TYPE)  # Create VM function
            self._vm_provider.wait_for_vm(vm_name)  # Wait for VM to boot
            # Add Network Adapter to Vm using Direct Assignment
            vm_network_adapter = self._vm_provider.add_vm_ethernet_adapter(vm_name, self.VSWITCH_NAME)
            self._vm_provider.assign_vm_mac_id(vm_network_adapter, index, vm_name, self.VM_TYPE)
            self._vm_provider.wait_for_vm(vm_name)  # Wait for VM to boot
            self.verify_hyperv_vm(vm_name, self.VM_TYPE)
            self.create_ssh_vm_object(vm_name)
            common_content_lib_sut = CommonContentLib(self._log, self.os, self._cfg_opt)
            device_id = self._vm_provider.enumerate_storage_device(self.BUS_TYPE, index, common_content_lib_sut)
            self._log.info("Device id present in PCEI:+++++++{}".format(device_id))
            self._vm_provider.set_disk_offline(device_id, common_content_lib_sut)
            self._vm_provider.add_storage_device_to_vm(vm_name, device_id, storage_size=None)

            vm_os_obj = self.windows_vm_object(vm_name, self.VM_TYPE)
            install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opt)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opt)
            self._log.info("VM_OBJ:{}, Collateral_obj:{}, Common:{}".format(vm_os_obj,
                                                                            install_collateral_vm_obj,
                                                                            common_content_lib_vm_obj))
            vm_device_list = self._vm_provider.enumerate_storage_device(self.SCSI_CONTROLLER,
                                                                        self.DISK_LIST_VALUE,
                                                                        common_content_lib_vm_obj)
            self._vm_provider.set_disk_online(vm_device_list, common_content_lib_vm_obj)
            self._log.info("Starting Iometer on host machine")
            iometer_tool_path = os.path.join(self._common_content_lib.get_collateral_path(),
                                             IOmeterToolConstants.IOMETER_TOOL_FOLDER)
            bkc_config_file_path = self._common_content_configuration.get_iometer_tool_config_file()
            copy(bkc_config_file_path, iometer_tool_path)
            # Executing import iometer.reg command
            reg_output = self._common_content_lib.execute_cmd_on_host(IOmeterToolConstants.REG_CMD, iometer_tool_path)
            self._log.debug("Successfully run iometer org file: {}".format(reg_output))
            # Executing IOMETER Tool on host
            self._log.info("Executing iometer command:{}".format(IOmeterToolConstants.EXECUTE_IOMETER_CMD))
            io_output = self._common_content_lib.execute_cmd_on_host(IOmeterToolConstants.EXECUTE_IOMETER_CMD,
                                                                     iometer_tool_path)
            self._log.debug("Successfully run iometer tool: \n{}".format(io_output))
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationHypervVtdPciPassthrough, self).cleanup(return_status)


if __name__ == "__main__":

    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationHypervVtdPciPassthrough.main()
             else Framework.TEST_RESULT_FAIL)
