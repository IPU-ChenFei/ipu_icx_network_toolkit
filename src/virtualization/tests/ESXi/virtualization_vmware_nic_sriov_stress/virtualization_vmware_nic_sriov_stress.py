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
import os
import threading

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib.content_artifactory_utils import ContentArtifactoryUtils

from dtaf_core.providers.internal.ssh_sut_os_provider import SshSutOsProvider
from dtaf_core.providers.provider_factory import ProviderFactory


class  VirtualizationVmwareNicSriovStress(VirtualizationCommon):
    TEST_CASE_ID = {"P16014135729","Virtualization_VMWare_NIC_SRIOV_stress"}
    STEP_DATA_DICT = {
        1: {'step_details': "Enable Vtd in Bios.",
            'expected_results': "Vtd should be enabled in bios"},
        2: {'step_details': "Check if SRIOV capable PCIe network device is present.",
            'expected_results': "ColumbiaVille Network device with SRIOV Function"},
        3: {'step_details': "Create the required Virtual Functions as per network device list",
            'expected_results': "Virtual Functions for network adapter successfully created"},
        4: {'step_details': "Get the VF adapter details",
            'expected_results': "Get the list of VF adapters created"},
        5: {'step_details': "Create virtual switch and assign static ip",
            'expected_results': "Virtual switch created and verfied"},
        6: {'step_details': "Create the VM with VM name and install vmware tools",
            'expected_results': "VM created and verified"},
        7: {'step_details' : "Install iperf on sut",
            'expected_results': "installed iperf on Host"},
        8: {'step_details': "Shutdown the VM,Attach VF PCIe device to VM and start the VM",
            'expected_results': "Virtual function adapter attached to VM"},
        9: {'step_details': "Verify the attached VFs in VMs",
             'expected_results': "Virtual function verified in VM"},
        10: {'step_details': "Get Virtual Adapter name in VM",
            'expected_results': "Virtual adapter ID is correct and verified"},
        11: {'step_details': "Assign static IP:",
             'expected_results': "Static IP assigned"},
        12: {'step_details': "Execute the PING test from SUT to VM",
             'expected_results': "PING test passed"},
        13: {'step_details': "install iperf in VM",
             'expected_results': "installation was successfull"},
        14: {'step_details': "Execute the iPerf test from SUT to 10 VM's for 2 hours",
             'expected_results': "iPerf test passed"},
        15: {'step_details': "Detach the VFs from VMs and disable SRIOV",
             'expected_results': "VFs detached from VMs and disabled sriov successfully"},

    }


    NO_OF_VMS=64
    NO_OF_VMS_FOR_IPERF = 10
    IPERF_EXEC_TIME = 20#7200
    BASE_PORT = 5201


    VM = [VMs.RHEL] * 64
    VM_TYPE = []
    VSWITCH_NAME = "vSwitch4"
    VMNIC_PORT = "vmnic2"
    PORT_GROUP = "NIC_PORT4"

    GET_VIRTUAL_NET_ADAPTER_CMD = "lshw -class network -businfo | grep 'Ethernet Adaptive' | cut -f3 -d' '"


    # vf_index_used = 0

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwareToolsInstallRHelGuest object.

        """
        super(VirtualizationVmwareNicSriovStress, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._log = test_log
        sut_ssh_cfg = cfg_opts.find(SshSutOsProvider.DEFAULT_CONFIG_PATH)
        self.sut_ssh = ProviderFactory.create(sut_ssh_cfg, test_log)
        self.sut_ip = self.sut_ssh._config_model.driver_cfg.ip
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self._artifactory_obj = ContentArtifactoryUtils(self._log, self.os, self._common_content_lib, self._cfg_opts)

    def prepare(self):
        # Need to implement bios configuration for ESXi SUT
        self._test_content_logger.start_step_logger(1)
        if self.os.os_type != OperatingSystems.ESXI:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._log.info("VMWare ESXi SUT detected for the testcase")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def enable_SRIOV( self, dev_id, server_ip, num=1):
        cmd = "$spec=New-Object VMware.Vim.HostSriovConfig;" \
              "$spec.SriovEnabled='$true';" \
              "$spec.NumVirtualFunction={};" \
              "$spec.Id='{}';" \
              "$spec.ApplyNow='$true';" \
              "$esx=Get-VMHost {};" \
              "$ptMgr=Get-View -Id $esx.ExtensionData.ConfigManager.PciPassthruSystem;" \
              "$ptMgr.UpdatePassthruConfig($spec);echo $spec"
        self.virt_execute_host_cmd_esxi(cmd.format(num, dev_id, server_ip))
        return

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
        ##check CVL device and BDF addresses
        self._test_content_logger.start_step_logger(2)
        nw_device_name = self._common_content_configuration.get_columbiaville_nic_device_name()
        self._log.info(nw_device_name)
        nw_device_list = self._vm_provider.get_passthrough_device_details(nw_device_name)
        nw_adapter_pci_value = nw_device_list[0].split(" ")[0]
        self._log.info(nw_adapter_pci_value)
        self._test_content_logger.end_step_logger(2, return_val=True)

        ##enable sriov and reboot SUT
        self._test_content_logger.start_step_logger(3)
        self.enable_SRIOV(nw_adapter_pci_value, self.sut_ip ,num=12)
        cmd_reboot = "reboot"
        self._common_content_lib.execute_sut_cmd(cmd_reboot, "reboot sut" , 60)
        time.sleep(300)
        self._log.info("Rebooted SUT")
        self._test_content_logger.end_step_logger(3, return_val=True)


        ##get vf details
        self._test_content_logger.start_step_logger(4)
        cmand = "lspci -p | grep -i '8086:1889'"
        cvl_vf_device_list = self._common_content_lib.execute_sut_cmd(cmand, "Check CVL VFs", 60)
        self._log.info(cvl_vf_device_list)
        self._test_content_logger.end_step_logger(4, return_val=True)

        ##Create 64 VMs ,install vmware tools and attach 64 VFs to 64 VMs and assign statis IP to each VF

        for index in range(self.NO_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index) +"sriov"
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.VM_TYPE.append(self.VM[index])
            self._log.info(" VM:{} on ESXi.".format(vm_name))

        ##create a virtual switch and VMKernel and assign static ip to physical nic
        self._test_content_logger.start_step_logger(5)
        pf_ip = "192.168.123.11"
        pf_subnet = "255.255.255.0"
        cmd_1="esxcfg-vswitch -l"
        cmd_2=f"esxcfg-vswitch -a {self.VSWITCH_NAME}" #create vswitch
        cmd_3=f'esxcfg-vswitch -A "{self.PORT_GROUP}" {self.VSWITCH_NAME}'
        cmd_4=f"esxcfg-vmknic -a -i {pf_ip} -n {pf_subnet} {self.PORT_GROUP}"
        self._common_content_lib.execute_sut_cmd(cmd_1, "list_vswitch", 60)
        self._common_content_lib.execute_sut_cmd(cmd_2, "create_vswitch",60)
        self._common_content_lib.execute_sut_cmd(cmd_3, "assign a port",60)
        self._common_content_lib.execute_sut_cmd(cmd_4, "assign_static_ip",60)

        # ##command to add uplink to vswitch
        cmd_to_add_vmk = f"esxcli network ip interface ipv4 set --ipv4={pf_ip} --netmask={pf_subnet} --type=static --interface-name=vmk1"
        self._common_content_lib.execute_sut_cmd(cmd_to_add_vmk, "restarting network services", 60)
        cmd_5 = "esxcli network vswitch standard uplink add --uplink-name={} --vswitch-name={}"
        output = self._common_content_lib.execute_sut_cmd(cmd_5.format(self.VMNIC_PORT, self.VSWITCH_NAME),
                                                          "add uplink", 100, "/vmfs/volumes/datastore1")
        self._common_content_lib.execute_sut_cmd(cmd_to_add_vmk, "restarting network services", 60)
        cmd_restart_network_services = "services.sh restart"
        self._common_content_lib.execute_sut_cmd(cmd_restart_network_services, "restarting network services", 60)
        self._test_content_logger.end_step_logger(5, return_val=True)


        vm_sut_obj_list = []
        # vf_index_used = 0
        for vm_index,vm_name in enumerate(self.LIST_OF_VM_NAMES):
            #create vm and install vmware tools
            self._test_content_logger.start_step_logger(6)
            self._vm_provider.destroy_vm(vm_name)
            self.create_vmware_vm_generic(vm_name, self.VM_TYPE[vm_index], vm_parallel="yes", vm_create_async=None,
                                          mac_addr=True, use_powercli="use_powercli")
            self._test_content_logger.end_step_logger(6, return_val=True)
            self._test_content_logger.start_step_logger(7)
            #self._vm_provider.install_vmware_tool_on_vm(vm_name)
            self._test_content_logger.end_step_logger(7,return_val=True)

        self.create_vm_wait()


        ##install iperf on esxi and disable firewall
        self._test_content_logger.start_step_logger(7)
        #self._install_collateral.install_iperf_on_esxi(self._common_content_lib)
        self._install_collateral.disable_firewall_in_esxi(self._common_content_lib)
        ##iperf is installed by default in esxi
        cmad_to_copy_iperf_local="cp /usr/lib/vmware/vsan/bin/iperf3  /vmfs/volumes/datastore1/iperf3"
        self._common_content_lib.execute_sut_cmd(cmad_to_copy_iperf_local, "iperf tool local copy", 60)
        self._test_content_logger.end_step_logger(7, return_val=True)


        vm_list=[]
        server_thread_res=[]
        client_thread_res=[]
        ping_flood_res = []
        vf_index_used = 0

    ####Run IPerf in 10 VMs
        for index in range(self.NO_OF_VMS_FOR_IPERF):
            vm_name = self.VM[index] + "_" + str(index) + "sriov"
            vm_os_obj = self.create_esxi_vm_host(vm_name, self.VM_TYPE[index])
            vm_sut_obj_list.append(vm_os_obj)
            common_content_obj_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self.get_yum_repo_config(vm_os_obj, common_content_obj_vm, machine_type="vm")

            ##attach VFs to VMs
            self._test_content_logger.start_step_logger(8)
            self.shutdown_vm_esxi(vm_name)
            cmd1 = "$devs=Get-PassthroughDevice -VMHost {} | Where-Object Name -like '*Virtual Function*';" \
                   "Add-PassthroughDevice -VM {} -PassthroughDevice $devs[{}];" \
                   "$spec=New-Object VMware.Vim.VirtualMachineConfigSpec;$spec.memoryReservationLockedToMax=$true;"
            self.virt_execute_host_cmd_esxi(cmd1.format(self.sut_ip, vm_name, vf_index_used))
            self._test_content_logger.end_step_logger(8, return_val=True)
            self.start_vm_esxi(vm_name)
            vf_index_used = vf_index_used + 1
            vm_ip = self.get_vm_ip_esxi(vm_name)
            self._log.info(vm_ip)
            self._test_content_logger.end_step_logger(8, return_val=True)

            self._test_content_logger.start_step_logger(9)
            vm_vf = common_content_obj_vm.execute_sut_cmd('lspci | grep -i "Virtual Function"',
                                                            "verifying vf function",
                                                            self._command_timeout)
            self._log.info("{}".format(vm_vf))
            self._test_content_logger.end_step_logger(9, return_val=True)

            ##get vf adapter in vm##
            self._test_content_logger.start_step_logger(10)
            get_vf_name_in_vm = common_content_obj_vm.execute_sut_cmd(self.GET_VIRTUAL_NET_ADAPTER_CMD,
                                                                      "get vm virtual adapter", self._command_timeout)
            print(get_vf_name_in_vm)
            vf_adapter_name = get_vf_name_in_vm.strip().split()[0]
            self._log.info("Successfully get the Network Pass through VF device name: {}".format(vf_adapter_name))
            self._log.info(vf_adapter_name)
            self._test_content_logger.end_step_logger(10, return_val=True)

            ###assign the IP to the VM##
            self._test_content_logger.start_step_logger(11)
            static_ip = "192.168.123.{}".format(index + 2)
            subnet = "255.255.255.0"
            self.assign_ip_to_vf_in_vm(vm_os_obj, static_ip, subnet, vf_adapter_name, vm_name)
            self._test_content_logger.end_step_logger(11, return_val=True)

            # ping  ip from the SUT
            self._test_content_logger.start_step_logger(12)
            self._vm_provider.ping_vm_from_sut(static_ip)
            self._test_content_logger.end_step_logger(12, return_val=True)

            self._test_content_logger.start_step_logger(13)
        #    self._install_collateral.install_iperf_on_linux_rpm_cmd(common_content_obj_vm, vm_os_obj)
            self._test_content_logger.end_step_logger(13, return_val=True)

            self._test_content_logger.start_step_logger(14)
            server_ip = pf_ip
            server_port_id= self.BASE_PORT + index

            # server_thread = threading.Thread(target=self.execute_esxi_sut_as_iperf_server,
            #                                  args=(self.IPERF_EXEC_TIME, server_port_id))
            # client_thread = threading.Thread(target=self.execute_iperf_client_esxi_vm,
            #                                  args=(server_ip, server_port_id, self.IPERF_EXEC_TIME, common_content_obj_vm))
            # vm_list.append(vm_name)
            # server_thread_res.append(server_thread)
            # client_thread_res.append(client_thread)
            self._log.info("Start PING Flood")
            ping_thread = threading.Thread(target=self.execute_ping_flood_test,
                                           args=(common_content_obj_vm, server_ip, self.IPERF_EXEC_TIME))
            ping_flood_res.append(ping_thread)
            self._test_content_logger.end_step_logger(14, return_val=True)


        ###ping flood
        for thread in ping_flood_res:
            thread.start()

        # for thread_sut in server_thread_res:
        #     thread_sut.start()
        #
        # time.sleep(10)
        #
        #
        # for thread_vm in client_thread_res:
        #     thread_vm.start()
        #
        #
        # for thread_sut, thread_vm in zip(server_thread_res, client_thread_res):
        #     thread_sut.join()
        #     thread_vm.join()

        for thread1 in ping_flood_res:
            thread1.join()
        time.sleep(self.IPERF_EXEC_TIME + 60)

        self._test_content_logger.start_step_logger(15)
        for vm_index,vm_name in enumerate(self.LIST_OF_VM_NAMES):
            self.shutdown_vm_esxi(vm_name)
            cmd_to_detach_vfs = "Get-PassthroughDevice -VM {} | Remove-PassthroughDevice -confirm:$false"
            self.virt_execute_host_cmd_esxi(cmd_to_detach_vfs.format(vm_name))
        self.disable_SRIOV(nw_adapter_pci_value, self.sut_ip)
        cmd="reboot"
        self._common_content_lib.execute_sut_cmd(cmd, "rebooted sut", self._command_timeout)
        time.sleep(300)
        self._test_content_logger.end_step_logger(15, True)

        return True

    def cleanup(self, return_status):
        super(VirtualizationVmwareNicSriovStress, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmwareNicSriovStress.main()
             else Framework.TEST_RESULT_FAIL)


