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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger


class VirtualizationVmwarePcieGen5PassthroughConfiguration(VirtualizationCommon):
    """
    Phoenix ID: 16013375764
    The purpose of this test case is making sure the creation of VMs guests on VMware ESXi.
    1. Enable VT-d bios on ESXi sut.
    2. Copy RHEL ISO image to ESXi SUT under 'vmfs/volumes/datastore1'.
    4. Create VM.
    5. Verify VM is running.
    6. Verify VMware tool installed on VM or not.
    """
    NUMBER_OF_VMS = 1
    VM = [VMs.RHEL] * 1
    VM_TYPE = "RHEL"
    TEST_CASE_ID = ["P16013375764", "Virtualization_VMware_Pcie_Gen5_Passthrough_configuration"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully"},
        2: {'step_details': "Check the columbiaville card in sut present or not ",
            'expected_results': "the columbiaville card is present in sut"},
        3: {'step_details': "Create Rhel VM on ESXi SUT",
            'expected_results': "VM Created Successfully"},
        4: {'step_details': "Verify VMware Tool installed on VM or not",
            'expected_results': "Successfully verified VMware Tool on VM"},
        5: {'step_details': "Enable pci passthrough in sut",
            'expected_results': "Enabled pci passthrough in sut successfully"},
        6: {'step_details': "Getting uuid of sut for passthrough",
            'expected_results': "The uuid of the sut is fetched successfully"},
        7: {'step_details': "The pci values for passthrough were given to vm",
            'expected_results': "The pci passthrough in vm got succesfully"},
        8: {'step_details': "Verifying the pci passthrough in vm",
            'expected_results': "The pci passthrough in vm verified successfully"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwarePciePassthroughRHelGuest object.

        """
        super(VirtualizationVmwarePcieGen5PassthroughConfiguration, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        # Need to implement bios configuration for ESXi SUT
        self._test_content_logger.start_step_logger(1)
        if self.os.os_type != OperatingSystems.ESXI:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._log.info("VMWare ESXi SUT detected for the testcase")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. create VM.
        2. Start the VM.
        3. Verify VMware tool installed or not on VM.
        4. Updating vmx file for enabling passthrough in sut for vm
        5. Verify passthrough is done or not in vm
        """
        self._test_content_logger.start_step_logger(2)
        gen5_device_name = self._common_content_configuration.get_gen5_nic_device_name()
        self._log.info(gen5_device_name)

        nw_device_list = self._vm_provider.get_passthrough_device_details(gen5_device_name)

        nw_adapter_pci_value = nw_device_list[0].split(" ")[0]
        bdf_value = self._vm_provider.get_bdf_values_of_nw_device(nw_adapter_pci_value)
        self._log.info(bdf_value)
        self._test_content_logger.end_step_logger(2, return_val=True)

        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on ESXi.".format(vm_name))

        vm_sut_obj_list = []
        vm_index = 0
        for vm_name in self.LIST_OF_VM_NAMES:
            self._test_content_logger.start_step_logger(3)
            self._vm_provider.destroy_vm(vm_name)
            self.create_vmware_vm(vm_name, self.VM_TYPE, mac_addr=True)
            self._test_content_logger.end_step_logger(3, return_val=True)
            self._test_content_logger.start_step_logger(4)
            self._vm_provider.install_vmware_tool_on_vm(vm_name)
            self._test_content_logger.end_step_logger(4, return_val=True)
            self._test_content_logger.start_step_logger(5)
            self._vm_provider.enable_pci_passthrough_in_sut(nw_adapter_pci_value)
            self._test_content_logger.end_step_logger(5, return_val=True)
            self._test_content_logger.start_step_logger(6)
            uuid = self._vm_provider.get_uuid_of_sut(vm_name)
            self._test_content_logger.end_step_logger(6, return_val=True)
            self._test_content_logger.start_step_logger(7)
            vendor, device, bdf_dec_value = self._vm_provider.get_hardware_pci_list_in_sut(vm_name, uuid, nw_adapter_pci_value)
            self._vm_provider.get_passthrough_pci_device_in_vm(vm_index, vm_name, bdf_dec_value, vendor, device, uuid)
            self._test_content_logger.end_step_logger(7, return_val=True)
            vm_index = vm_index + 1
            # create VM os object
            self._test_content_logger.start_step_logger(8)
            vm_os_obj = self.create_esxi_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self._vm_provider.verify_pci_passthrough_in_vm(vm_name, gen5_device_name, common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(8, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationVmwarePcieGen5PassthroughConfiguration, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmwarePcieGen5PassthroughConfiguration.main()
             else Framework.TEST_RESULT_FAIL)
