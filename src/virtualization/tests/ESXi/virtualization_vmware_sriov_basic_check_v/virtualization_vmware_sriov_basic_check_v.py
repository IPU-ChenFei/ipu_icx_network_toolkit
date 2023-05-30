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


class VirtualizationVmwareSriovBasicCheck(VirtualizationCommon):
    """
    Phoenix ID: 18014075586
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
    VSWITCH_NAME = "vSwitch4"
    VMNIC_PORT = "vmnic4"
    PORT_GROUP = "NIC_PORT4"

    GET_VIRTUAL_NET_ADAPTER_CMD = "lshw -class network -businfo | grep 'Ethernet Adaptive' | cut -f3 -d' '"

    TEST_CASE_ID = ["P18014075586", "Virtualization_VMware_SRIOV_Basic_Check"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully"},
        2: {'step_details': "create switch and add uplink to vswitch",
            'expected_results': "created vswitch successfully"},
        3: {'step_details': "Create Rhel VM on ESXi SUT",
            'expected_results': "VM Created Successfully"},
        4: {'step_details': "Verify VMware Tool installed on VM or not",
            'expected_results': "Successfully verified VMware Tool on VM"},
        5: {'step_details': "Check the columbiaville card in sut present or not ",
            'expected_results': "the columbiaville card is present in sut"},
        6: {'step_details': "Enable sriov in sut",
            'expected_results': "Enabled sriovin sut successfully"},
        7: {'step_details': "Verify vf for vm ",
            'expected_results': "The vf in vm got succesfully"},
        8: {'step_details': "Assign dhcp  in vm",
            'expected_results': "The dhcp assigned successfully"},
        9: {'step_details': "remove sriov adapter from VM and disable sriov",
            'expected_results': "removed sriov adapter successfully and disabled sriov"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwarePciePassthroughRHelGuest object.

        """
        super(VirtualizationVmwareSriovBasicCheck, self).__init__(test_log, arguments, cfg_opts)
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

    def enable_SRIOV( self, dev_id, server_ip, num=1):
        cmd = "'$spec=New-Object VMware.Vim.HostSriovConfig;'" \
              "'$spec.SriovEnabled='$true';' " \
              "f'$spec.NumVirtualFunction='{}';' " \
              "f'$spec.Id='{}';' " \
              "f'$spec.ApplyNow='$true';' " \
              "f'$esx=Get-VMHost {};' " \
              "f'$ptMgr=Get-View -Id $esx.ExtensionData.ConfigManager.PciPassthruSystem;' " \
              "f'$ptMgr.UpdatePassthruConfig($spec);echo $spec'"
        self.virt_execute_host_cmd_esxi(cmd.format(num, dev_id, server_ip))
        return True

    def disable_SRIOV(self, dev_id, server_ip):
        cmd = "$spec=New-Object VMware.Vim.HostSriovConfig;" \
              "$spec.SriovEnabled=$false;" \
              "$spec.Id='{}';" \
              "$spec.ApplyNow='$true';" \
              "$esx=Get-VMHost {};" \
              "$ptMgr=Get-View -Id $esx.ExtensionData.ConfigManager.PciPassthruSystem;" \
              "$ptMgr.UpdatePassthruConfig($spec);echo $spec"
        self.virt_execute_host_cmd_esxi(cmd.format(dev_id, server_ip))
        return

    def execute(self):
        """
        1. create VM.
        2. Start the VM.
        3. Verify VMware tool installed or not on VM.
        4. Updating vmx file for enabling passthrough in sut for vm
        5. Verify passthrough is done or not in vm
        """

        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on ESXi.".format(vm_name))

            ##create a virtual switch and VMKernel and assign static ip to physical nic
            self._test_content_logger.start_step_logger(2)
            pf_ip = "192.168.10.40"
            pf_subnet = "255.255.255.0"
            cmd_1 = "esxcfg-vswitch -l"
            cmd_2 = f"esxcfg-vswitch -a {self.VSWITCH_NAME}"  # create vswitch
            cmd_3 = f'esxcfg-vswitch -A "{self.PORT_GROUP}" {self.VSWITCH_NAME}'
            cmd_4 = f'esxcfg-vmknic -a -i {pf_ip} -n {pf_subnet} {self.PORT_GROUP}'
            self._common_content_lib.execute_sut_cmd(cmd_1, "list_vswitch", 60)
            self._common_content_lib.execute_sut_cmd(cmd_2, "create_vswitch", 60)
            self._common_content_lib.execute_sut_cmd(cmd_3, "assign a port", 60)
            self._common_content_lib.execute_sut_cmd(cmd_4, "assign_static_ip", 60)

            #command to add uplink to vswitch
            cmd_to_add_vmk = f"esxcli network ip interface ipv4 set --ipv4={pf_ip} --netmask={pf_subnet} --type=static --interface-name=vmk1"
            self._common_content_lib.execute_sut_cmd(cmd_to_add_vmk, "restarting network services", 60)
            cmd_5 = "esxcli network vswitch standard uplink add --uplink-name={} --vswitch-name={}"
            output = self._common_content_lib.execute_sut_cmd(cmd_5.format(self.VMNIC_PORT,self.VSWITCH_NAME), "add uplink", 100,"/vmfs/volumes/datastore1")
            self._common_content_lib.execute_sut_cmd(cmd_to_add_vmk, "restarting network services", 60)
            cmd_restart_network_services = "services.sh restart"
            self._common_content_lib.execute_sut_cmd(cmd_restart_network_services, "restarting network services", 60)
            self._test_content_logger.end_step_logger(2, return_val=True)

        vm_sut_obj_list = []
        for vm_name in self.LIST_OF_VM_NAMES:
            self._test_content_logger.start_step_logger(3)
            self._vm_provider.destroy_vm(vm_name)
            self.create_vmware_vm(vm_name, self.VM_TYPE, mac_addr=True, use_powercli="use_powercli")
            self._test_content_logger.end_step_logger(3, return_val=True)
            self._test_content_logger.start_step_logger(4)
            self._vm_provider.install_vmware_tool_on_vm(vm_name)
            self._test_content_logger.end_step_logger(4, return_val=True)
            # create VM os object
            vm_os_obj = self.create_esxi_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)

            self._test_content_logger.start_step_logger(5)
            columbiaville_device_name = self._common_content_configuration.get_columbiaville_nic_device_name()
            self._log.info(columbiaville_device_name)
            nw_device_list = self._vm_provider.get_passthrough_device_details(columbiaville_device_name)
            nw_adapter_pci_value = nw_device_list[0].split(" ")[0]
            self._test_content_logger.end_step_logger(5, return_val=True)

            self._test_content_logger.start_step_logger(6)
            self.enable_SRIOV(nw_adapter_pci_value, self.sut_ip, num=1)
            cmd_reboot = "reboot"
            self._common_content_lib.execute_sut_cmd(cmd_reboot, "reboot sut", 60)
            time.sleep(300)
            self._log.info("Rebooted SUT")
            self._test_content_logger.end_step_logger(6, return_val=True)

            self._log.info("Use the following command to obtain the SR-IOV device bus number：")
            cmand = "lspci -p | grep -i '8086:1889'"
            cvl_vf_device_list = self._common_content_lib.execute_sut_cmd(cmand, "Check CVL VFs", 60)
            self._log.info(cvl_vf_device_list)
            self._log.info("The devicename and nw_adapter_pci_value in the output result should be the device of virtual"
                           "functions.")

            self._log.info("Add a new SR-IOV network adapter:")
            cmd2 =  "New-NetworkAdapter -VM {} -type SriovEthernetCard -NetworkName 'VM Network' -PhysicalFunction {}"
            self.virt_execute_host_cmd_esxi(cmd2.format(vm_name, nw_adapter_pci_value))
            self._log.info("Add SR-IOV network adapter success")

            #self.start_vm_esxi(vm_name)
            vm_ip = self.get_vm_ip_esxi(vm_name)
            self._log.info("Get {} pass".format(vm_ip))

            self._test_content_logger.start_step_logger(7)
            out = common_content_lib_vm_obj.execute_sut_cmd('lspci | grep -i "Virtual Function"', "verifying vf function",
                                                            self._command_timeout)
            self._log.info("{}".format(out))

            ##get vf name in VM
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            get_vf_name_in_vm = common_content_lib_vm_obj.execute_sut_cmd(self.GET_VIRTUAL_NET_ADAPTER_CMD,
                                                                      "get vm virtual adapter", self._command_timeout)
            print(get_vf_name_in_vm)
            vf_adapter_name = get_vf_name_in_vm.strip()
            self._log.info("Successfully get the Network Pass through VF device name: {}".format(vf_adapter_name))
            self._log.info(vf_adapter_name)
            self._test_content_logger.end_step_logger(7, return_val=True)

            self._test_content_logger.start_step_logger(8)
            static_ip = "192.168.10.10"
            subnet = "255.255.255.0"
            self.assign_ip_to_vf_in_vm(vm_os_obj, static_ip, subnet, vf_adapter_name, vm_name)
            self._vm_provider.ping_vm_from_sut(static_ip)
            self._test_content_logger.end_step_logger(8, return_val=True)

            self._test_content_logger.start_step_logger(9)
            self.shutdown_vm_esxi(vm_name)
            cmd_to_detach_vfs ='$nic=Get-NetworkAdapter -VM {} | Where-Object Name -like "SR-IOV*";' \
                               'Remove-NetworkAdapter -NetworkAdapter $nic -Confirm:$false'
            self.virt_execute_host_cmd_esxi(cmd_to_detach_vfs.format(vm_name))


            self.disable_SRIOV(nw_adapter_pci_value, self.sut_ip)
            cmd = "reboot"
            self._common_content_lib.execute_sut_cmd(cmd, "rebooted sut", self._command_timeout)
            time.sleep(300)
            self._test_content_logger.end_step_logger(9, True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationVmwareSriovBasicCheck, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmwareSriovBasicCheck.main()
             else Framework.TEST_RESULT_FAIL)
