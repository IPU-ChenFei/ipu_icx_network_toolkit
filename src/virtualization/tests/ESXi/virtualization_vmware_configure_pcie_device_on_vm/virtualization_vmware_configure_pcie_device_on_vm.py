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
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.internal.ssh_sut_os_provider import SshSutOsProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger


class VirtualizationVmwareConfigurePciDeviceOnVM(VirtualizationCommon):
    """
    Phoenix ID: 18014074746
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
    PCI_TYPE = "NVM"
    TEST_CASE_ID = ["P18014074746", "Virtualization_VMware_Configure_Pcie_Device_on_VM"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully"},
        2: {'step_details': "Create Rhel VM on ESXi SUT",
            'expected_results': "VM Created Successfully"},
        3: {'step_details': "Verify VMware Tool installed on VM or not",
            'expected_results': "Successfully verified VMware Tool on VM"},
        4: {'step_details': "Check the NVMe in sut present or not ",
            'expected_results': "the NVMe is present in sut"},
        5: {'step_details': "Enable pci passthrough in sut",
            'expected_results': "Enabled pci passthrough in sut successfully"},
        6: {'step_details': "Setting the setup and for passthrough",
            'expected_results': "passthrough done successfully"},
        7: {'step_details': "Verifying the pci passthrough in vm",
            'expected_results': "The pci passthrough in vm verified successfully"},
        8: {'step_details': "Remove the pci device passthrough in vm",
            'expected_results': "The pci passthrough in vm removed successfully"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwarePciePassthroughRHelGuest object.

        """
        super(VirtualizationVmwareConfigurePciDeviceOnVM, self).__init__(test_log, arguments, cfg_opts)
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
        PCI_TYPE = "NVM"
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on ESXi.".format(vm_name))

        vm_sut_obj_list = []
        for vm_name in self.LIST_OF_VM_NAMES:
            self._test_content_logger.start_step_logger(2)
            self._vm_provider.destroy_vm(vm_name)
            self.create_vmware_vm(vm_name, self.VM_TYPE, mac_addr=True)
            self._test_content_logger.end_step_logger(2, return_val=True)
            self._test_content_logger.start_step_logger(3)
            self._vm_provider.install_vmware_tool_on_vm(vm_name)
            self._test_content_logger.end_step_logger(3, return_val=True)
            # create VM os object
            vm_os_obj = self.create_esxi_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)

            self._test_content_logger.start_step_logger(4)
            cmd1 = "lspci | grep -i {}"
            nw_device_list = self._common_content_lib.execute_sut_cmd(cmd1.format(PCI_TYPE),"list nvme devices",60)
            nw_adapter_pci_value = nw_device_list.split(" ")[0]
            self._test_content_logger.end_step_logger(4, return_val=True)

            self._test_content_logger.start_step_logger(5)
            cmd2 = "esxcli hardware pci pcipassthru set -d={} -e=on  -a"
            self._common_content_lib.execute_sut_cmd(cmd2.format(nw_adapter_pci_value),"enable nvme devices",60)
            self._log.info("The device is configured to passthrough")
            self._test_content_logger.end_step_logger(5, return_val=True)

            self._test_content_logger.start_step_logger(6)
            cmd3 = "Get-VM {}"
            self.virt_execute_host_cmd_esxi(cmd3.format(vm_name))
            self._log.info("get vm status successful")

            self.shutdown_vm_esxi(vm_name)
            self._log.info("Get the Passthrough available device list from the host:")
            cmd4 = "f'Get-PassthroughDevice -VMHost {} | '" \
                   "f'Where-Object {{$_.Name -match {}}} "
            self.virt_execute_host_cmd_esxi(cmd4.format(self.sut_ip, PCI_TYPE))
            self._log.info("Get the Passthrough devices successful!")

            cmd5 = "f'Get-PassthroughDevice -VM {} | Remove-PassthroughDevice -confirm:$false'"
            self.virt_execute_host_cmd_esxi(cmd5.format(vm_name))
            self._log.info("Get the Passthrough devices successful!")

            cmd6 = "f'$scsiDeviceList=Get-PassthroughDevice -VMHost {} '" \
                   "f'-Type Pci | Where-Object{{$_.Name -match {}}}" \
                   "f'Add-PassthroughDevice -VM {} -PassthroughDevice $scsiDeviceList[0];'" \
                   "f'echo $scsiDeviceList[0]'"
            self.virt_execute_host_cmd_esxi(cmd6.format(self.sut_ip, PCI_TYPE, vm_name))

            self._log.info("'Centos OS SSD Passthrough requires Reserve all guest memory (All Locked), use the command "
                           "below to select:)'")
            cmd7 = "($spec=New-Object VMware.Vim.VirtualMachineConfigSpec;" \
                   "$spec.memoryReservationLockedToMax = $true;" \
                    "(Get-VM {}).ExtensionData.ReconfigVM_Task($spec))"
            self.virt_execute_host_cmd_esxi(cmd7.format(vm_name))
            self._log.info("setting Reserve all guest memory successful!")
            self._test_content_logger.end_step_logger(6, return_val=True)

            # start the VM
            self._test_content_logger.start_step_logger(7)
            self.start_vm_esxi(vm_name)
            vm_ip = self.get_vm_ip_esxi(vm_name)
            self._log.info(f"Get {vm_ip} pass", vm_ip)

            out = common_content_lib_vm_obj.execute_sut_cmd("lspci | grep -i ssd", "verifying pci device",
                                                            self._command_timeout)
            self._log.info("{}".format(out))
            self._test_content_logger.end_step_logger(7, return_val=True)

            self._test_content_logger.start_step_logger(8)
            cmd8 = "f'Get-PassthroughDevice -VM {} | Remove-PassthroughDevice -confirm:$false'"
            self.virt_execute_host_cmd_esxi(cmd8.format(vm_name))
            self._test_content_logger.end_step_logger(8, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationVmwareConfigurePciDeviceOnVM, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmwareConfigurePciDeviceOnVM.main()
             else Framework.TEST_RESULT_FAIL)
