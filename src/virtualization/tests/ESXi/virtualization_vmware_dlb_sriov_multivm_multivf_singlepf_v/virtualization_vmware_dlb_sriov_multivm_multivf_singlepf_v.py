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
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.internal.ssh_sut_os_provider import SshSutOsProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.virtualization.base_qat_util import BaseQATUtil

class VirtualizationVmwareDLBSriovMultiVMMultiVFSinglePF(VirtualizationCommon):
    """
    Phoenix ID: 16013527924
    The purpose of this test case is making sure the creation of VMs guests on VMware ESXi.
    1. Enable VT-d bios on ESXi sut.
    2. Copy RHEL ISO image to ESXi SUT under 'vmfs/volumes/datastore1'.
    4. Create VM.
    5. Verify VM is running.
    6. Verify VMware tool installed on VM or not.
    """
    NUMBER_OF_VMS = 8
    VM = [VMs.CENTOS] * 8
    VM_TYPE = "CENTOS"
    test_time = 15*60
    TEST_CASE_ID = ["P16013527973", "VirtualizationVmwareDLBSriovMultiVMMultiVFSinglePF"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully"},
        2: {'step_details': "Create Centos VM on ESXi SUT",
            'expected_results': "VM Created Successfully"},
        3: {'step_details': "Verify VMware Tool installed on VM or not",
            'expected_results': "Successfully verified VMware Tool on VM"},
        4: {'step_details': "Install dlb driver in sut",
            'expected_results': "DLB driver installed in sut successfully"},
        5: {'step_details': "Enable SRIOV for dlb driver ",
            'expected_results': "Enabled SRIOV successfully"},
        6: {'step_details': "Get the dlb driver to create virtual functions ",
            'expected_results': "Virtual functions for the dlb driver created successfully"},
        7: {'step_details': "Enabling dlb vf for passthrough",
            'expected_results': "The dlb vf for passthrough enabled successfully"},
        8: {'step_details': "Adding dlb vf to vm",
            'expected_results': "DLB vf added to vm enabled successfully"},
        9: {'step_details': "Installing dlb driver in vm",
            'expected_results': "The dlb driver installed in vm successfully"},
        10: {'step_details': "Running dlb workload in vm",
            'expected_results': "DLB workload ran in vm enabled successfully"},
        11: {'step_details': "Unloading and removing dlb from sut",
             'expected_results': "DLB driver removed and unloaded from sut successfully"}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwarePciePassthroughCentosGuest object.

        """
        super(VirtualizationVmwareDLBSriovMultiVMMultiVFSinglePF, self).__init__(test_log, arguments, cfg_opts)
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

    def enable_SRIOV( self, dev_id, server_ip, num):
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

    def add_dlb_drivers_to_vm(self,sut_ip, vm_name,index):
        no_of_dlb_devices = 1
        for dlb_index in range(0, no_of_dlb_devices):
            cmand = "$devs=Get-PassthroughDevice -VMHost {} | Where-Object Name -like '*DLB VF*';" \
                     "Add-PassthroughDevice -VM {} -PassthroughDevice $devs[{}];" \
                     "Add-PassthroughDevice -VM {} -PassthroughDevice $devs[{}];"
            self.virt_execute_host_cmd_esxi(cmand.format(sut_ip,vm_name,index, vm_name,1+index))
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
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] +"_"+ str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on ESXi.".format(vm_name))

        self._test_content_logger.start_step_logger(4)
        self.dlb_driver_install_esxi(driver_type="sriov")
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        no_of_vf_per_pf = 2
        no_of_dlb_devices = 8
        dlb_bdf_list = []
        for dlb_index in range(0, no_of_dlb_devices):
            dlb_bdf_value = self.get_dlb_device_bdf_value(dlb_index)
            dlb_bdf_list.append(dlb_bdf_value)
            self.enable_SRIOV(dlb_bdf_value, self.sut_ip, num=no_of_vf_per_pf)
        self._test_content_logger.end_step_logger(5, return_val=True)
        cmand2 = "reboot"
        self._common_content_lib.execute_sut_cmd(cmand2, "reboot the sut", 60)
        time.sleep(300)

        self._test_content_logger.start_step_logger(6)
        cmand3 = "lspci -p | grep 2711"
        dlb_vf_device_list = self._common_content_lib.execute_sut_cmd(cmand3, "check dlb vf in sut", 60)
        self._log.info(dlb_vf_device_list)
        dlb_vf_dev_bdf_list = []
        total_num_of_dlb_vf = 0
        dlb_value = dlb_vf_device_list.split("\n")
        for value in dlb_value:
            dlb_vf_bdf_value = value.split(" ")[0]
            if dlb_vf_bdf_value is not None and dlb_vf_bdf_value is not "":
                dlb_vf_dev_bdf_list.append(dlb_vf_bdf_value)
                total_num_of_dlb_vf = total_num_of_dlb_vf + 1
                self._log.info(dlb_vf_bdf_value)
        self._log.info(total_num_of_dlb_vf)
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        for dlb_vf in dlb_vf_dev_bdf_list:
            try:
                cmand4 = "esxcli hardware pci pcipassthru set -d={} -e=on -a"
                self._common_content_lib.execute_sut_cmd(cmand4.format(dlb_vf),
                                                         "enable the dlb vf for pci passthrough in the sut", 60)
            except:
                pass
        self._test_content_logger.end_step_logger(7, return_val=True)

        vm_sut_obj_list = []
        index = 0
        for vm_name in self.LIST_OF_VM_NAMES:
            self._test_content_logger.start_step_logger(2)
            self._vm_provider.destroy_vm(vm_name)
            self.create_vmware_vm(vm_name, self.VM_TYPE, mac_addr=True, use_powercli="use_powercli")
            self._test_content_logger.end_step_logger(2, return_val=True)
            self._test_content_logger.start_step_logger(3)
            self._vm_provider.install_vmware_tool_on_vm(vm_name)
            self._test_content_logger.end_step_logger(3, return_val=True)
            # create VM os object
            vm_os_obj = self.create_esxi_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_obj_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self.get_yum_repo_config(vm_os_obj, common_content_obj_vm, machine_type="vm")
            self.shutdown_vm_esxi(vm_name)
            self._test_content_logger.start_step_logger(8)
            self.add_dlb_drivers_to_vm(self.sut_ip, vm_name,index)
            self._test_content_logger.end_step_logger(8, return_val=True)
            self.start_vm_esxi(vm_name)
            self._test_content_logger.start_step_logger(9)
            self.verify_hqm_dlb_kernel(common_content_lib=common_content_obj_vm)
            self.install_hqm_driver_library(common_content_lib=common_content_obj_vm)
            self._test_content_logger.end_step_logger(9, return_val=True)
            index = index + 5

        for vm_name in self.LIST_OF_VM_NAMES:
            vm_os_obj = self.create_esxi_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_obj_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self._test_content_logger.start_step_logger(10)
            self.run_dlb_work_load_vmware(vm_name, vm_parallel = "yes", common_content_lib=common_content_obj_vm, runtime=self.test_time)
            self._test_content_logger.end_step_logger(10, return_val=True)

        time.sleep(self.test_time + 60)


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
        for dlb_index in range(0, no_of_dlb_devices):
            dlb_bdf_value = self.get_dlb_device_bdf_value(dlb_index)
            dlb_bdf_list.append(dlb_bdf_value)
            self.disable_SRIOV(dlb_bdf_value, self.sut_ip)

        self._test_content_logger.start_step_logger(11)
        self.uninstall_driver_esxi('dlb')
        self._log.info("Dlb driver unloaded and removed from sut")
        self._test_content_logger.end_step_logger(11, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationVmwareDLBSriovMultiVMMultiVFSinglePF, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmwareDLBSriovMultiVMMultiVFSinglePF.main()
             else Framework.TEST_RESULT_FAIL)
