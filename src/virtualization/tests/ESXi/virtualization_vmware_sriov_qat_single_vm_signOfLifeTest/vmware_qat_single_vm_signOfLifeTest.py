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
from src.lib.content_artifactory_utils import ContentArtifactoryUtils

class VirtualizationVmwareQATSRIOVSingleVMSignOfLife(BaseQATUtil):
    """
    Phoenix ID: 16013373284
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
    TEST_CASE_ID = ["P16013373284", "Virtualization_VMware_QAT_SRIOV_Single_VM_SignOfLife"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully"},
        2: {'step_details': "Create Rhel VM on ESXi SUT",
            'expected_results': "VM Created Successfully"},
        3: {'step_details': "Verify VMware Tool installed on VM or not",
            'expected_results': "Successfully verified VMware Tool on VM"},
        4: {'step_details': "Install qat driver in sut",
            'expected_results': "Qat driver installed in sut successfully"},
        5: {'step_details': "Get the qat driver to create virtual functions ",
            'expected_results': "Virtual functions for the qat driver created successfully"},
        6: {'step_details': "Enable SRIOV for qat driver ",
            'expected_results': "Enabled SRIOV successfully"},
        7: {'step_details': "Enabling qat vf for passthrough",
            'expected_results': "The qat vf for passthrough enabled successfully"},
        8: {'step_details': "Adding qat vf to vm",
            'expected_results': "Qat vf added to vm enabled successfully"},
        9: {'step_details': "Installing qat driver in vm",
            'expected_results': "The qat driver installed in vm successfully"},
        10: {'step_details': "Running qat workload in vm",
            'expected_results': "Qat workload ran in vm enabled successfully"},
        11: {'step_details': "Remove qat VFs from VM",
             'expected_results': "Qat Vfs detached successfully from VM"},
        12: {'step_details': "Uninstall qat driver from sut",
             'expected_results': "qat driver removed successfully from SUT"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwarePciePassthroughRHelGuest object.

        """
        super(VirtualizationVmwareQATSRIOVSingleVMSignOfLife, self).__init__(test_log, arguments, cfg_opts)
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
              "$spec.ApplyNow=$true;" \
              "$esx=Get-VMHost {};" \
              "$ptMgr=Get-View -Id $esx.ExtensionData.ConfigManager.PciPassthruSystem;" \
              "$ptMgr.UpdatePassthruConfig($spec);echo $spec;"
        self.virt_execute_host_cmd_esxi(cmd.format(dev_id, server_ip))
        return

    def execute(self):
        """
        1. create VM.
        2. Start the VM.
        3. Verify VMware tool installed or not on VM.
        4. Install QAT in sut
        5. QAT Vf passthrough to vm
        6. Run QAt workload in vm
        """

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
            common_content_obj_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self.get_yum_repo_config(vm_os_obj, common_content_obj_vm, machine_type="vm")

            self._test_content_logger.start_step_logger(4)
            self.qat_driver_install_esxi()
            self._test_content_logger.end_step_logger(4, return_val=True)

            self._test_content_logger.start_step_logger(5)
            qat_bdf_value = self.get_qat_device_bdf_value(0)
            self._test_content_logger.end_step_logger(5, return_val=True)

            self._test_content_logger.start_step_logger(6)
            self.enable_SRIOV(qat_bdf_value, self.sut_ip, num=1)
            self._test_content_logger.end_step_logger(6, return_val=True)
            cmand2 = "reboot"
            self._common_content_lib.execute_sut_cmd(cmand2, "reboot the sut", 60)
            time.sleep(300)

            self._test_content_logger.start_step_logger(7)
            cmand3 = "lspci -p | grep 8086:4941"
            qat_vf_device_list = self._common_content_lib.execute_sut_cmd(cmand3, "check qat in sut", 60)
            self._log.info(qat_vf_device_list)
            qat_vf_bdf_value = (re.sub('\s\s+', '*', qat_vf_device_list)).split('*')[0].split(" ")[0]
            self._log.info(qat_vf_bdf_value)
            try :
                cmand4 = "esxcli hardware pci pcipassthru set -d={} -e=on -a"
                self._common_content_lib.execute_sut_cmd(cmand4.format(qat_vf_bdf_value),
                                                         "enable the qat vf for pci passthrough in the sut", 60)
            except :
                pass
            self._test_content_logger.end_step_logger(7, return_val=True)
            self.shutdown_vm_esxi(vm_name)
            self._test_content_logger.start_step_logger(8)
            cmand5 = " $devs=Get-PassthroughDevice -VMHost {} | Where-Object Name -like '*QAT VF*';" \
                     "Add-PassthroughDevice -VM {} -PassthroughDevice $devs[0];"
            self.virt_execute_host_cmd_esxi(cmand5.format(self.sut_ip,vm_name))
            self._test_content_logger.end_step_logger(8, return_val=True)
            self.start_vm_esxi(vm_name)
            self._test_content_logger.start_step_logger(9)
            self.install_check_qat_status(vm_name=vm_name, os_obj=vm_os_obj,
                                          qat_type="sriov", target_type="guest",
                                          common_content_object=common_content_obj_vm, is_vm="yes")
            self._test_content_logger.end_step_logger(9, return_val=True)
            self._test_content_logger.start_step_logger(10)
            cpa_sample_command = "./cpa_sample_code signOfLife=1"
            self.execute_cpa_sample_code(cpa_sample_command, common_content_object=common_content_obj_vm)
            self._test_content_logger.end_step_logger(10, return_val=True)

            self._test_content_logger.start_step_logger(11)
            self.shutdown_vm_esxi(vm_name)
            time.sleep(60)
            cmd3 = "Get-PassthroughDevice -VM {} | Remove-PassthroughDevice -confirm:$false"
            self.virt_execute_host_cmd_esxi(cmd3.format(vm_name))
            self._test_content_logger.end_step_logger(11, return_val=True)

            self._test_content_logger.start_step_logger(11)
            try:
                cmand4 = "esxcli hardware pci pcipassthru set -d={} -e=off -a"
                self._common_content_lib.execute_sut_cmd(cmand4.format(qat_vf_bdf_value),
                                                         "enable the qat vf for pci passthrough in the sut", 60)
            except:
                pass
            self.disable_SRIOV(qat_bdf_value, self.sut_ip)
            self._test_content_logger.end_step_logger(11, return_val=True)

            self._test_content_logger.start_step_logger(12)
            self.uninstall_driver_esxi('qat')
            self._test_content_logger.end_step_logger(12, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationVmwareQATSRIOVSingleVMSignOfLife, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmwareQATSRIOVSingleVMSignOfLife.main()
             else Framework.TEST_RESULT_FAIL)
