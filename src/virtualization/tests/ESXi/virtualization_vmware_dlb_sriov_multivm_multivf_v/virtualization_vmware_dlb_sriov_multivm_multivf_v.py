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
import re

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.virtualization.base_qat_util import BaseQATUtil
from dtaf_core.providers.internal.ssh_sut_os_provider import SshSutOsProvider
from dtaf_core.providers.provider_factory import ProviderFactory

class VirtualizationVmwareDLBSriovMultiVMMultiVF(VirtualizationCommon):
    """
    Phoenix ID: 16013527973
    The purpose of this test case is to execute the scenario -
    Virtualization - Vmware Esxi - DLB_SRIOV_Multi_VM_Multi_VF.
    1. Enable VT-d bios on ESXi sut.
    2. Install the DLB driver
    3. Enable SRIOV and Create 6 VFs for each DLB PFs
    4. Get and save the list of all BDFs for each of the created VFs
    5. Copy RHEL/CentOS ISO image to ESXi SUT under 'vmfs/volumes/datastore1'.
    6. Create VM and install OS.
    7. Verify VMware tool installed on VM or not and Verify VM is running.
    8. Create/Enable the Passthrough for each of the 6 VFs created from a single PF
    9. Attach the 6 VFs created from same PF to single VM
    10. Continue the same steps for total 2 VMs
    11. Run the CPA Sample Code test on each of the VM
    12. Remove the Passthrough from VMs
    """
    NUM_VM = 8
    VM = [VMs.CENTOS]*NUM_VM #, VMs.WINDOWS]
    VM_TYPE = ["CENTOS"]*NUM_VM #, "WINDOWS"]

    test_time = 15 * 60
    no_of_dlb_devices = 0

    TEST_CASE_ID = ["P16013527973", "VirtualizationVmwareDLBSriovMultiVMMultiVF"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully"},
        2: {'step_details': "Create Rhel/CentOS VM Names for ESXi SUT",
            'expected_results': "VM Names Created Successfully"},
        3: {'step_details': "Install DLB driver in sut",
            'expected_results': "DLB driver installed in sut successfully"},
        4: {'step_details': "Read the no of sockets, cores and threads of the host",
            'expected_results': "Got the sockets, cores and thread from SUT successfully"},
        5: {'step_details': "Enable SRIOV for DLB and create virtual functions ",
            'expected_results': "Virtual functions for the DLB driver created successfully"},
        6: {'step_details': "Get the BDF list of all VFs created",
            'expected_results': "BDF list created for all VFs"},
        7: {'step_details': "Enabling DLB vf for passthrough",
            'expected_results': "The DLB vf for passthrough enabled successfully"},
        8: {'step_details': "Create Rhel/CentOS VM on ESXi SUT",
            'expected_results': "VM Created Successfully"},
        9: {'step_details': "Verify VMware Tool installed on VM or not",
            'expected_results': "Successfully verified VMware Tool on VM"},
        10: {'step_details': "Shut down the VM",
             'expected_results': "Shutdown VM done successfully"},
        11: {'step_details': "Adding DLB vf to vm",
             'expected_results': "DLB vf added to vm enabled successfully"},
        12: {'step_details': "Start the VM",
             'expected_results': "Started VM successfully"},
        13: {'step_details': "Installing DLB driver in vm",
             'expected_results': "The DLB driver installed in vm successfully"},
        14: {'step_details': "Running DLB workload in vm",
             'expected_results': "DLB workload ran in vm enabled successfully"},
        15: {'step_details': "Remove the Passthrough DLB VF devices",
             'expected_results': "Passthrough DLB VF devices removed successfully"},
        16: {'step_details': "Uninstall dlb driver",
             'expected_results': "DLB driver uninstalled successfully"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwareToolsInstallRHelGuest object.

        """
        super(VirtualizationVmwareDLBSriovMultiVMMultiVF, self).__init__(test_log, arguments, cfg_opts)
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

    def get_dlb_device_bdf_value(self, index):
        """
          Purpose: To install DLB driver
          Args:
              No
          Returns:
              dlb bdf value
          Example:
              Simplest usage: get DLB bdf value
                  get_dlb_device_bdf_value
        """
        dlb_bdf_value = ""
        cmand_dlb_list = "lspci -p | grep 8086:2710"
        dlb_device_list_data = self._common_content_lib.execute_sut_cmd(cmand_dlb_list, "check qat in sut", 60)
        self._log.info(dlb_device_list_data)
        if dlb_device_list_data is not None:
            dlb_device_list = re.findall(r'\b([0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}.\d{1}\s*)',
                                         dlb_device_list_data)
            dlb_bdf_value = dlb_device_list[index].strip()
            self._log.info(dlb_bdf_value)
        return dlb_bdf_value

    def enable_SRIOV(self, dev_id, server_ip, num):
        cmd = "$spec=New-Object VMware.Vim.HostSriovConfig;" \
              "$spec.SriovEnabled='$true';" \
              "$spec.NumVirtualFunction={};" \
              "$spec.Id='{}';" \
              "$spec.ApplyNow='$true';" \
              "$esx=Get-VMHost {};" \
              "$ptMgr=Get-View -Id $esx.ExtensionData.ConfigManager.PciPassthruSystem;" \
              "$ptMgr.UpdatePassthruConfig($spec);echo $spec;"
        self.virt_execute_host_cmd_esxi(cmd.format(num, dev_id, server_ip))
        return

    def disable_SRIOV(self, dev_id, server_ip):
        cmd = "$spec=New-Object VMware.Vim.HostSriovConfig;" \
              "$spec.SriovEnabled=$false;" \
              "$spec.Id='{}';" \
              "$spec.ApplyNow=$true;" \
              "$esx=Get-VMHost {};" \
              "$ptMgr=Get-View -Id $esx.ExtensionData.ConfigManager.PciPassthruSystem;" \
              "$ptMgr.UpdatePassthruConfig($spec);echo $spec;"
        self.virt_execute_host_cmd_esxi(cmd.format(dev_id, server_ip))
        return

    def get_no_sockets_core_threads_esxi(self):
        # cmd = "$result = @();" \
        #         "$vmhost = get-vmhost;" \
        #         "foreach ($esxi in $vmhost) {" \
        #         "    $HostCPU = $esxi.ExtensionData.Summary.Hardware.NumCpuPkgs;" \
        #         "    $HostCPUcore = $esxi.ExtensionData.Summary.Hardware.NumCpuCores/$HostCPU;" \
        #         "    $obj = new-object psobject;" \
        #         "    $obj | Add-Member -MemberType NoteProperty -Name name -Value $esxi.Name;" \
        #         "    $obj | Add-Member -MemberType NoteProperty -Name CPUSocket -Value $HostCPU;" \
        #         "    $obj | Add-Member -MemberType NoteProperty -Name Corepersocket -Value $HostCPUcore;" \
        #         "    $result += $obj;" \
        #         "};" \
        #         "echo $result;"
        cmd = '$vmhost = get-vmhost;' \
              'foreach($esxi in $vmhost) {' \
              '$HostCPU = $esxi.ExtensionData.Summary.Hardware.NumCpuPkgs;' \
              '$HostCPUcore = $esxi.ExtensionData.Summary.Hardware.NumCpuCores/$HostCPU;' \
              '$HostCPUThreads = $esxi.ExtensionData.Summary.Hardware.NumCpuThreads/$HostCPU;' \
              '};' \
              'echo "Host_CPU:$HostCPU Host_CPU_Core:$HostCPUcore Host_CPU_Thread:$HostCPUThreads";'
        command_to_get_host_cores_threads = self.virt_execute_host_cmd_esxi(cmd)
        hostsocket = (re.findall(r"Host_CPU:(\d{1,5})", str(command_to_get_host_cores_threads)))[0]
        corepersocket = (re.findall(r"Host_CPU_Core:(\d{1,5})", str(command_to_get_host_cores_threads)))[0]
        threadspersocket = (re.findall(r"Host_CPU_Thread:(\d{1,5})", str(command_to_get_host_cores_threads)))[0]
        # self._log.info(host_cpu, corepersocket, threadspersocket)
        self._log.info(
            "Per Socket Configuration: host Cpu: {}, core per socket: {}, threads per socket:{}".format(hostsocket,
                                                                                                        corepersocket,
                                                                                                        threadspersocket))
        return int(hostsocket), int(corepersocket), int(threadspersocket)

    def add_dlb_devices_to_vm_with_allvf_enabled(self, sut_ip, vm_name, start_index, no_of_dev):
        index = 0
        # cmand5 = "$devs=Get-PassthroughDevice -VMHost {} | Where-Object Name -like '*QAT VF*';" \
        #               for($i=0; $i -lt {}; $i++){$devices_qat[$i]=$devs[{}+$i]}.format(no_of_dev, start_index)
        #          "foreach($dev_qat in $devices_qat) {{ Add-PassthroughDevice -VM {} -PassthroughDevice $dev_qat; }};"
        # no_of_pf = 8, cur_tot_no_vfs_per_pf = no of devices in a group of devices for a PF
        # total_vf_created =  $devs.length, no_of_vf_per_pf_tba = no_of_dev/no_of_pf
        # cur_tot_no_vfs_per_pf = total_vf_created/no_of_pf
        # for (pf_index = 1 to no_of_pf) { end_index = pf_index * cur_tot_no_vfs_per_pf,
        # start_index = end_index -  no_of_vf_per_pf_tba}
        #
        cmand = "$devs=Get-PassthroughDevice -VMHost {} | Where-Object Name -like '*DLB VF*';" \
                "$index_start_for_attach={};$no_of_pf={}; $no_of_vf_per_pf_tba={}/$no_of_pf;" \
                "$total_vf_created=$devs.length; $cur_tot_no_vfs_per_pf=$total_vf_created/$no_of_pf;" \
                "for($j=0; $j -lt $no_of_pf; $j++) " \
                "{{ $devices_qat=@();" \
                "   $start_index=($j*$cur_tot_no_vfs_per_pf + ($index_start_for_attach * $no_of_vf_per_pf_tba));" \
                "   $end_index=($start_index + $no_of_vf_per_pf_tba);" \
                "   for($i=$start_index; $i -lt $end_index; $i++) {{$devices_qat += $devs[$i];}};" \
                "   foreach($dev_qat in $devices_qat) " \
                "   {{ " \
                "       Add-PassthroughDevice -VM {} -PassthroughDevice $dev_qat; " \
                "       echo $dev_qat.Bus.tostring('X') $dev_qat.DeviceId.tostring('X'); " \
                "       echo $dev_qat.ClassId.tostring('X') $dev_qat.Function.tostring('X'); " \
                "   }}; " \
                "}};".format(sut_ip, start_index, self.no_of_dlb_devices, no_of_dev, vm_name)
        self.virt_execute_host_cmd_esxi(cmand)
        time.sleep(60)
        return

    def execute(self):
        """
        1. create VM.
        2. Start the VM.
        3. Verify VMware tool installed or not on VM.
        4. Install DLB in sut
        5. DLB Vf passthrough to vm
        6. Run DLB workload in vm
        """

        self._test_content_logger.start_step_logger(2)
        for index in range(self.NUM_VM):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on ESXi.".format(vm_name))
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self.dlb_driver_install_esxi(driver_type="sriov")
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        hostsocket, corepersocket, threadspersocket = self.get_no_sockets_core_threads_esxi()

        self.no_of_dlb_devices = hostsocket * self.DLB_DEVICE_NUM
        self._test_content_logger.end_step_logger(4, return_val=True)

        #no_of_vf_per_pf = self.NUM_VM * 2 * self.no_of_dlb_devices
        no_of_vf_per_pf = 16

        dlb_vf_per_pf_per_vm = int(no_of_vf_per_pf / self.NUM_VM)
        dlb_bdf_list = []
        self._test_content_logger.start_step_logger(5)
        for dlb_index in range(0, self.no_of_dlb_devices):
            dlb_bdf_value = self.get_dlb_device_bdf_value(dlb_index)
            dlb_bdf_list.append(dlb_bdf_value)
            self.enable_SRIOV(dlb_bdf_value, self.sut_ip, num=no_of_vf_per_pf)
        cmand2 = "reboot"
        self._common_content_lib.execute_sut_cmd(cmand2, "reboot the sut", 60)
        time.sleep(300)
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        cmand3 = "lspci -p | grep 2711"
        dlb_vf_device_list = self._common_content_lib.execute_sut_cmd(cmand3, "check dlb vf in sut", 60).split("\n")
        self._log.info(dlb_vf_device_list)
        dlb_vf_dev_bdf_list = []
        total_num_of_dlb_vf = 0
        for dlb_vf_dev in dlb_vf_device_list:
            dlb_vf_bdf_value = dlb_vf_dev.split(" ")[0]
            if dlb_vf_bdf_value is not None and dlb_vf_bdf_value is not "":
                dlb_vf_dev_bdf_list.append(dlb_vf_bdf_value)
                total_num_of_dlb_vf = total_num_of_dlb_vf + 1
                self._log.info(dlb_vf_bdf_value)
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        for vm_index, vm_name in enumerate(self.LIST_OF_VM_NAMES):
            for dlb_pf_index in range(self.no_of_dlb_devices):
                # assign 2 VFs from each PF to each VM
                start_dlb_vf_index = (vm_index * 2) + (no_of_vf_per_pf * dlb_pf_index)
                for dlb_vf_index in range(start_dlb_vf_index, start_dlb_vf_index + 2):
                    try:
                        cmand4 = "esxcli hardware pci pcipassthru set -d={} -e=on -a"
                        self._common_content_lib.execute_sut_cmd(cmand4.format(dlb_vf_dev_bdf_list[dlb_vf_index]),
                                                                 "enable the qat vf for pci passthrough in the sut", 60)
                    except:
                        pass
        self._test_content_logger.end_step_logger(7, return_val=True)


        vm_sut_obj_list = []
        dlb_vf_index_used = 0

        for vm_index, vm_name in enumerate(self.LIST_OF_VM_NAMES):
            self._test_content_logger.start_step_logger(8)
            self._vm_provider.destroy_vm(vm_name)
            self.create_vmware_vm(vm_name, self.VM_TYPE[vm_index], mac_addr=True,use_powercli="use_powercli")
            self._test_content_logger.end_step_logger(8, return_val=True)

            self._test_content_logger.start_step_logger(9)
            self._vm_provider.install_vmware_tool_on_vm(vm_name)
            self._test_content_logger.end_step_logger(9, return_val=True)
            # create VM os object
            vm_os_obj = self.create_esxi_vm_host(vm_name, self.VM_TYPE[vm_index])
            vm_sut_obj_list.append(vm_os_obj)
            common_content_obj_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self.get_yum_repo_config(vm_os_obj, common_content_obj_vm, machine_type="vm")


            self._test_content_logger.start_step_logger(10)
            self.shutdown_vm_esxi(vm_name)
            self._test_content_logger.end_step_logger(10, return_val=True)

            self._test_content_logger.start_step_logger(11)
            # cmand5 = "$devs=Get-PassthroughDevice -VMHost {} | Where-Object Name -like '*DLB VF*';" \
            #          "foreach($dev_dlb in $devs) { Add-PassthroughDevice -VM {} -PassthroughDevice $dev_dlb; };"
            # self.virt_execute_host_cmd_esxi(cmand5.format(self.sut_ip, vm_name))
            self.add_dlb_devices_to_vm_with_allvf_enabled(self.sut_ip, vm_name, vm_index, no_of_vf_per_pf)

            dlb_vf_index_used = dlb_vf_index_used + ((vm_index + 1) * dlb_vf_per_pf_per_vm)
            self._test_content_logger.end_step_logger(11, return_val=True)

            self._test_content_logger.start_step_logger(12)
            self.start_vm_esxi(vm_name)
            self._test_content_logger.end_step_logger(12, return_val=True)

            self._test_content_logger.start_step_logger(13)
            self.verify_hqm_dlb_kernel(common_content_lib=common_content_obj_vm)

            self.install_hqm_driver_library(os_obj=vm_os_obj, common_content_lib = common_content_obj_vm, is_vm="yes")

            self._test_content_logger.end_step_logger(13, return_val=True)

        self._test_content_logger.start_step_logger(14)
        for vm_name, vm_os_obj in zip(self.LIST_OF_VM_NAMES, vm_sut_obj_list):
            common_content_obj_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self.run_dlb_work_load_vmware(vm_name, vm_parallel = "yes", common_content_lib=common_content_obj_vm, runtime=self.test_time)
        self._test_content_logger.end_step_logger(14, return_val=True)

        time.sleep(self.test_time + 60)

        self._test_content_logger.start_step_logger(15)
        for vm_name in self.LIST_OF_VM_NAMES:
            self.shutdown_vm_esxi(vm_name)
            cmd3 = "Get-PassthroughDevice -VM {} | Remove-PassthroughDevice -confirm:$false"
            self.virt_execute_host_cmd_esxi(cmd3.format(vm_name))

        for dlb_vf in dlb_vf_dev_bdf_list:
            try:
                cmand5 = "esxcli hardware pci pcipassthru set -d={} -e=off -a"
                self._common_content_lib.execute_sut_cmd(cmand5.format(dlb_vf),
                                                         "disable the dlb vf for pci passthrough in the sut", 60)
            except:
                pass
        for dlb_index in range(0, self.no_of_dlb_devices):
            dlb_bdf_value = self.get_dlb_device_bdf_value(dlb_index)
            dlb_bdf_list.append(dlb_bdf_value)
            self.disable_SRIOV(dlb_bdf_value, self.sut_ip)
        self._test_content_logger.end_step_logger(15, return_val=True)

        ###uninstall dlb driver
        self._test_content_logger.end_step_logger(16, return_val=True)
        self.uninstall_driver_esxi('dlb')
        self._log.info("Dlb driver unloaded and removed from sut")
        self._test_content_logger.end_step_logger(16, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationVmwareDLBSriovMultiVMMultiVF, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmwareDLBSriovMultiVMMultiVF.main()
             else Framework.TEST_RESULT_FAIL)
