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
from src.lib.content_artifactory_utils import ContentArtifactoryUtils

class VirtualizationVmwareQATSriovSingleVMMultiVFDataMov(BaseQATUtil):
    """
    Phoenix ID: 16013373485
    The purpose of this test case is to execute the scenario -
    Virtualization - Vmware Esxi - QAT_SRIOV_Single_VM_Multi_VF_Data_Movement_L.
    1. Enable VT-d bios on ESXi sut.
    2. Install the QAT driver
    3. Enable SRIOV and Create 6 VFs for any of the single QAT PF
    4. Get and save the list of all BDFs for each of the created VFs
    5. Copy RHEL/CentOS ISO image to ESXi SUT under 'vmfs/volumes/datastore1'.
    6. Create VM and install OS.
    7. Verify VMware tool installed on VM or not and Verify VM is running.
    8. Create/Enable the Passthrough for each of the 6 VFs created from a single PF
    9. Attach the 6 VFs created from same PF to single VM
    10. Run the CPA Sample Code test on the VM
    11. Remove the Passthrough from VM
    """
    NUM_VM = 1
    VM = [VMs.RHEL]*NUM_VM #, VMs.WINDOWS]
    VM_TYPE = ["RHEL"]*NUM_VM #, "WINDOWS"]
    cpa_sample_command = "./cpa_sample_code signOfLife=1"
    TEST_CASE_ID = ["P16013373485", "VirtualizationVmwareQATSriovSingleVMMultiVFDataMov"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully"},
        2: {'step_details': "Create Rhel/CentOS VM Names for ESXi SUT",
            'expected_results': "VM Names Created Successfully"},
        3: {'step_details': "Install qat driver in sut",
            'expected_results': "Qat driver installed in sut successfully"},
        4: {'step_details': "Read the no of sockets, cores and threads of the host",
            'expected_results': "Got the sockets, cores and thread from SUT successfully"},
        5: {'step_details': "Enable SRIOV for QAT and create virtual functions ",
            'expected_results': "Virtual functions for the qat driver created successfully"},
        6: {'step_details': "Get the BDF list of all VFs created",
            'expected_results': "BDF list created for all VFs"},
        7: {'step_details': "Create Rhel/CentOS VM on ESXi SUT",
            'expected_results': "VM Created Successfully"},
        8: {'step_details': "Verify VMware Tool installed on VM or not",
            'expected_results': "Successfully verified VMware Tool on VM"},
        9: {'step_details': "Enabling qat vf for passthrough",
            'expected_results': "The qat vf for passthrough enabled successfully"},
        10: {'step_details': "Shut down the VM",
             'expected_results': "Shutdown VM done successfully"},
        11: {'step_details': "Adding qat vf to vm",
             'expected_results': "Qat vf added to vm enabled successfully"},
        12: {'step_details': "Start the VM",
             'expected_results': "Started VM successfully"},
        13: {'step_details': "Installing qat driver in vm",
             'expected_results': "The qat driver installed in vm successfully"},
        14: {'step_details': "Running qat workload in vm",
             'expected_results': "Qat workload ran in vm enabled successfully"},
        15: {'step_details': "Remove the Passthrough QAT VF devices",
             'expected_results': "Passthrough QAT VF devices removed successfully"},
        16: {'step_details': "Disable SRIOV for QAT  ",
             'expected_results': "Disabled qat sriov successfully"},
        17: {'step_details': "Uninstall qat driver from sut",
             'expected_results': "qat driver removed successfully from SUT"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwareToolsInstallRHelGuest object.

        """
        super(VirtualizationVmwareQATSriovSingleVMMultiVFDataMov, self).__init__(test_log, arguments, cfg_opts)
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

    def enable_SRIOV(self, dev_id, server_ip, num=1):
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
        host_cpu = (re.findall(r"Host_CPU:(\d{1,5})", str(command_to_get_host_cores_threads)))[0]
        corepersocket = (re.findall(r"Host_CPU_Core:(\d{1,5})", str(command_to_get_host_cores_threads)))[0]
        threadspersocket = (re.findall(r"Host_CPU_Thread:(\d{1,5})", str(command_to_get_host_cores_threads)))[0]
        self._log.info(
            "Per Socket Configuration: host Cpu: {}, core per socket: {}, threads per socket:{}".format(
                host_cpu, corepersocket,
                threadspersocket))
        return int(host_cpu), int(corepersocket), int(threadspersocket)

    def execute(self):
        """
        1. create VM.
        2. Start the VM.
        3. Verify VMware tool installed or not on VM.
        4. Install QAT in sut
        5. QAT Vf passthrough to vm
        6. Run QAt workload in vm
        """

        self._test_content_logger.start_step_logger(2)
        for index in range(self.NUM_VM):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on ESXi.".format(vm_name))
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self.qat_driver_install_esxi()
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        host_cpu, corepersocket, threadspersocket = self.get_no_sockets_core_threads_esxi()

        no_of_qat_devices = host_cpu * self.QAT_DEVICE_NUM
        self._test_content_logger.end_step_logger(4, return_val=True)

        no_of_vf_per_pf = 6
        qat_bdf_list = []
        self._test_content_logger.start_step_logger(5)
        for qat_index in range(0, 1):   #no_of_qat_devices):
            qat_bdf_value = self.get_qat_device_bdf_value(qat_index)
            qat_bdf_list.append(qat_bdf_value)
            self.enable_SRIOV(qat_bdf_value, self.sut_ip, num=no_of_vf_per_pf)
        cmand2 = "reboot"
        self._common_content_lib.execute_sut_cmd(cmand2, "reboot the sut", 60)
        time.sleep(300)
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        cmand3 = "lspci -p | grep 8086:4941"
        qat_vf_device_list = self._common_content_lib.execute_sut_cmd(cmand3, "check qat in sut", 60).split("\n")
        self._log.info(qat_vf_device_list)
        qat_vf_dev_bdf_list = []
        total_num_of_qat_vf = 0
        for qat_vf_dev in qat_vf_device_list:
            qat_vf_bdf_value = qat_vf_dev.split(" ")[0]
            if qat_vf_bdf_value is not None and qat_vf_bdf_value is not "":
                qat_vf_dev_bdf_list.append(qat_vf_bdf_value)
                total_num_of_qat_vf = total_num_of_qat_vf + 1
                self._log.info(qat_vf_bdf_value)
                self._log.info(total_num_of_qat_vf)
        self._test_content_logger.end_step_logger(6, return_val=True)

        vm_sut_obj_list = []
        qat_vf_index_used = 0
        for vm_index, vm_name in enumerate(self.LIST_OF_VM_NAMES):
            self._test_content_logger.start_step_logger(7)
            self._vm_provider.destroy_vm(vm_name)
            self.create_vmware_vm(vm_name, self.VM_TYPE[vm_index], mac_addr=True)
            self._test_content_logger.end_step_logger(7, return_val=True)

            self._test_content_logger.start_step_logger(8)
            self._vm_provider.install_vmware_tool_on_vm(vm_name)
            self._test_content_logger.end_step_logger(8, return_val=True)
            # create VM os object
            vm_os_obj = self.create_esxi_vm_host(vm_name, self.VM_TYPE[vm_index])
            vm_sut_obj_list.append(vm_os_obj)
            common_content_obj_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self.get_yum_repo_config(vm_os_obj, common_content_obj_vm, machine_type="vm")

            self._test_content_logger.start_step_logger(9)
            # for qat_vf_index in range(qat_vf_index_used, qat_vf_index_used+(total_num_of_qat_vf/self.NUM_VM)):
            for qat_vf_index in range(qat_vf_index_used, qat_vf_index_used + no_of_vf_per_pf):
                try:
                    cmand4 = "esxcli hardware pci pcipassthru set -d={} -e=on -a"
                    self._common_content_lib.execute_sut_cmd(cmand4.format(qat_vf_dev_bdf_list[qat_vf_index]),
                                                             "enable the qat vf for pci passthrough in the sut", 60)
                except:
                    pass
            # qat_vf_index_used = qat_vf_index_used + (total_num_of_qat_vf/self.NUM_VM)
            qat_vf_index_used = qat_vf_index_used + no_of_vf_per_pf
            self._test_content_logger.end_step_logger(9, return_val=True)

            self._test_content_logger.start_step_logger(10)
            self.shutdown_vm_esxi(vm_name)
            self._test_content_logger.end_step_logger(10, return_val=True)

            self._test_content_logger.start_step_logger(11)
            cmand5 = "$devs=Get-PassthroughDevice -VMHost {} | Where-Object Name -like '*QAT VF*';" \
                     "foreach($dev_qat in $devs) {{ Add-PassthroughDevice -VM {} -PassthroughDevice $dev_qat; }};"
            self.virt_execute_host_cmd_esxi(cmand5.format(self.sut_ip,vm_name))
            self._test_content_logger.end_step_logger(11, return_val=True)

            self._test_content_logger.start_step_logger(12)
            self.start_vm_esxi(vm_name)
            self._test_content_logger.end_step_logger(12, return_val=True)

            self._test_content_logger.start_step_logger(13)
            self.install_check_qat_status(vm_name=vm_name, os_obj=vm_os_obj,
                                          qat_type="sriov", target_type="guest",
                                          common_content_object=common_content_obj_vm, is_vm="yes")
            self._test_content_logger.end_step_logger(13, return_val=True)

        self._test_content_logger.start_step_logger(14)
        for vm_name, vm_os_obj in zip(self.LIST_OF_VM_NAMES, vm_sut_obj_list):
            common_content_obj_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            cpa_sample_command = "./cpa_sample_code" #data_movement
            self.execute_cpa_sample_code(cpa_sample_command, common_content_object=common_content_obj_vm)
        self._test_content_logger.end_step_logger(14, return_val=True)

        self._test_content_logger.start_step_logger(15)
        for vm_name in self.LIST_OF_VM_NAMES:
            self.shutdown_vm_esxi(vm_name)
            time.sleep(60)
            cmd3 = "Get-PassthroughDevice -VM {} | Remove-PassthroughDevice -confirm:$false"
            self.virt_execute_host_cmd_esxi(cmd3.format(vm_name))
        self._test_content_logger.end_step_logger(15, return_val=True)

        self._test_content_logger.start_step_logger(16)
        for qat_vf_index in range(qat_vf_index_used, qat_vf_index_used + no_of_vf_per_pf):
            try:
                cmand4 = "esxcli hardware pci pcipassthru set -d={} -e=off -a"
                self._common_content_lib.execute_sut_cmd(cmand4.format(qat_vf_dev_bdf_list[qat_vf_index]),
                                                         "disable the qat vf for pci passthrough in the sut", 60)
            except:
                pass
        for qat_index in range(0, 1):
            qat_bdf_value = self.get_qat_device_bdf_value(qat_index)
            qat_bdf_list.append(qat_bdf_value)
            self.disable_SRIOV(qat_bdf_value, self.sut_ip)
        self._test_content_logger.end_step_logger(16, return_val=True)

        self._test_content_logger.start_step_logger(17)
        self.uninstall_driver_esxi('qat')
        self._test_content_logger.end_step_logger(17, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationVmwareQATSriovSingleVMMultiVFDataMov, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmwareQATSriovSingleVMMultiVFDataMov.main()
             else Framework.TEST_RESULT_FAIL)
