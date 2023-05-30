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


class VirtualizationVmwareCheckCoresPerSocket(VirtualizationCommon):
    """
    Phoenix ID: 18014072501
    VMware multicore virtual CPU support lets you control the number of cores per virtual CPU in a virtual machine.
    This capability lets operating systems with socket restrictions use more of the host CPU's cores.

    1. Enable VT-d bios on ESXi sut.
    2. Copy Centos ISO image to ESXi SUT under 'vmfs/volumes/datastore1'.
    4. Create VM.
    5. Verify VM is running.
    6. Verify VMware tool installed on VM or not.
    """
    VM = [VMs.RHEL]
    VM_TYPE = "RHEL"
    TEST_CASE_ID = ["P18014072501", "Virtualization_Check_Cores_Per_Socket"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully'"},
        2: {'step_details': "Create CentOS VM on ESXi SUT",
            'expected_results': "VM Created Successfully"},
        3: {'step_details': "Verify VMware Tool installed on VM or not",
            'expected_results': "Successfully verified VMware Tool on VM"},
        4: {'step_details': "Shutdown the VM",
            'expected_results': "VM shutdown executed successfully"},
        5: {'step_details': "Set no of CPUs anc Cores to VM",
            'expected_results': "Successfully set CPUs and Cores"},
        6: {'step_details': "Get VM IP and read the CPUs and Cores in VM",
            'expected_results': "Successfully verified IP, VM CPUs & Cores"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwareCheckCoresPerSocket object.

        """
        super(VirtualizationVmwareCheckCoresPerSocket, self).__init__(test_log, arguments, cfg_opts)
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
        """
        vm_sut_obj_list = []
        for index in range(len(self.VM)):
            self._test_content_logger.start_step_logger(2)
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._vm_provider.destroy_vm(vm_name)
            self.create_vmware_vm(vm_name, self.VM_TYPE, mac_addr=True)
            self._test_content_logger.end_step_logger(2, return_val=True)
            self._test_content_logger.start_step_logger(3)
            self._vm_provider.install_vmware_tool_on_vm(vm_name)
            self._test_content_logger.end_step_logger(3, return_val=True)
            vm_os_obj = self.create_esxi_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self._test_content_logger.start_step_logger(4)
            # Shutdown the VM
            self.shutdown_vm_esxi(vm_name)
            self._test_content_logger.end_step_logger(4, return_val=True)
            self._test_content_logger.start_step_logger(5)
            out, err = self.virt_execute_host_cmd_esxi(f"Set-VM -VM {vm_name} -NumCpu 4 -CoresPerSocket 4 -confirm:$false")
            if err is not "":
                self._log.error("Set-VM numcpu and core failed")

            self._log.info("Check the results of the settings")
            self.virt_execute_host_cmd_esxi('\"$result = @();'
                                       '$vms = Get-view -ViewType VirtualMachine;'
                                       'foreach ($vm in $vms) {'
                                       '$obj = new-object psobject;'
                                       '\"$obj | Add-Member -MemberType NoteProperty -Name name -Value $vm.Name;'
                                       '$obj | Add-Member -MemberType NoteProperty -Name CPUSocket -Value $vm.config.hardware.NumCPU;'
                                       '$obj | Add-Member -MemberType NoteProperty -Name Corepersocket -Value $vm.config.hardware.NumCoresPerSocket;\"'
                                       '$result += $obj;'
                                       '};'
                                       '$result;\"')

            # start the VM
            self.start_vm_esxi(vm_name)
            self._test_content_logger.end_step_logger(5, return_val=True)
            self._test_content_logger.start_step_logger(6)
            vm_ip = self.get_vm_ip_esxi(vm_name)
            self._log.info(f"Get {vm_ip} pass", vm_ip)

            self._log.info("Use command line to check whether the information of Core(s) per socket and CPU")
            out = common_content_lib_vm_obj.execute_sut_cmd("lscpu", "lscpu", self._command_timeout)
            self._log.info("{}".format(out))
            self._test_content_logger.end_step_logger(6, return_val=True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationVmwareCheckCoresPerSocket, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmwareCheckCoresPerSocket.main()
             else Framework.TEST_RESULT_FAIL)
