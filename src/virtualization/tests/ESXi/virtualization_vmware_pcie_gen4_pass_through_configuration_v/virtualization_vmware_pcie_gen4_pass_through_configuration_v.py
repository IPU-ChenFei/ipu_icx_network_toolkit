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
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.internal.ssh_sut_os_provider import SshSutOsProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger


class VirtualizationVmwarePcieGen4PassthroughConfiguration(VirtualizationCommon):
    """
    Phoenix ID: 16013375716
    The purpose of this test case is making sure the creation of VMs guests on VMware ESXi.
    1. Enable VT-d bios on ESXi sut.
    2. Copy RHEL ISO image to ESXi SUT under 'vmfs/volumes/datastore1'.
    4. Create VM.
    5. Verify VM is running.
    6. Verify VMware tool installed on VM or not.
    7. Verify pci passthrough in vm or not
    """
    NUMBER_OF_VMS = 1
    VM = [VMs.RHEL]
    VM_TYPE = "RHEL"
    TEST_CASE_ID = ["P16013375716", "Virtualization_VMware_Pcie_Gen4_Passthrough_configuration"]
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
        6: {'step_details': "Adding pci passthrough to vm",
            'expected_results': "The pci passthrough device addded successfully"},
        7: {'step_details': "Creating objects for vm",
            'expected_results': "The vm objects created succesfully"},
        8: {'step_details': "Verifying the pci passthrough in vm",
            'expected_results': "The pci passthrough in vm verified successfully"},
        9: {'step_details': "Removing the pci passthrough in vm and disabling pci device in sut",
            'expected_results': "The pci passthrough in vm removed and pci device disabled in sut successfully"}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwarePciePassthroughRHelGuest object.

        """
        super(VirtualizationVmwarePcieGen4PassthroughConfiguration, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._log = test_log
        sut_ssh_cfg = cfg_opts.find(SshSutOsProvider.DEFAULT_CONFIG_PATH)
        self.sut_ssh = ProviderFactory.create(sut_ssh_cfg, test_log)
        self.sut_ip = self.sut_ssh._config_model.driver_cfg.ip
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
        columbiaville_device_name = self._common_content_configuration.get_columbiaville_nic_device_name()
        self._log.info(columbiaville_device_name)
        nw_device_list = self._vm_provider.get_passthrough_device_details(columbiaville_device_name)
        self._log.info(nw_device_list)
        nw_adapter_pci_value = nw_device_list[0].split(" ")[0]
        self._log.info(nw_adapter_pci_value)
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
            cmand = "reboot"
            self._common_content_lib.execute_sut_cmd(cmand, "reboot the sut", 60)
            time.sleep(300)
            self._log.info("Rebooted sut")
            self.shutdown_vm_esxi(vm_name)
            self._test_content_logger.start_step_logger(6)
            cmd1 = "$devs=Get-PassthroughDevice -VMHost {} | Where-Object Name -like '*{}*';" \
                   "Add-PassthroughDevice -VM {} -PassthroughDevice $devs[0];" \
                   "$spec=New-Object VMware.Vim.VirtualMachineConfigSpec;$spec.memoryReservationLockedToMax=$true;" \
                   "(Get-VM {}).ExtensionData.ReconfigVM_Task($spec)"
            self.virt_execute_host_cmd_esxi(cmd1.format(self.sut_ip, columbiaville_device_name, vm_name, vm_name))
            self._test_content_logger.end_step_logger(6, return_val=True)
            self.start_vm_esxi(vm_name)

            vm_index = vm_index + 1
            # create VM os object
            self._test_content_logger.start_step_logger(7)
            vm_os_obj = self.create_esxi_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, machine_type="vm")
            self._test_content_logger.end_step_logger(7, return_val=True)
            self._test_content_logger.start_step_logger(8)
            self._vm_provider.verify_pci_passthrough_in_vm(vm_name, columbiaville_device_name, common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(8, return_val=True)

            self._test_content_logger.start_step_logger(9)
            cmd2 = "Get-PassthroughDevice -VM {} | Remove-PassthroughDevice -confirm:$false"
            self.virt_execute_host_cmd_esxi(cmd2.format(vm_name))
            self._log.info("Removing pci passthrough device from vm {}".format(vm_name))
            cmd3 = "esxcli hardware pci pcipassthru set -d {} -e False"
            self._common_content_lib.execute_sut_cmd(cmd3.format(nw_adapter_pci_value),"Disable pci device in sut",60)
            self._test_content_logger.end_step_logger(9, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationVmwarePcieGen4PassthroughConfiguration, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmwarePcieGen4PassthroughConfiguration.main()
             else Framework.TEST_RESULT_FAIL)
