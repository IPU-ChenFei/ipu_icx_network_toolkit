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
import math
import os
import time
import threading

from pathlib import Path
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.provider.stressapp_provider import StressAppTestProvider


class VirtualizationVmwareOverCommitCpuIOWrkLdMultiVM(VirtualizationCommon):
    """
    Phoenix ID: 16013374726
    The purpose of this test case to do Over Commit or Max CPU Allocation and run IO workloads into multiple VM's.
    1. Enable VT-d bios on ESXi sut.
    2. Copy RHEL ISO image to ESXi SUT under 'vmfs/volumes/datastore1'.
    4. Create VM.
    5. Verify VM is running.
    6. Verify VMware tool installed on VM or not.
    """
    VM = [VMs.RHEL]*2
    VM_TYPE = "RHEL"
    TEST_CASE_ID = ["P16013374726", "Virtualization_VMware_OverCommitCPU_IOWorkLd_MultiVM"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully'"},
        2: {'step_details': "Create CentOS VM on ESXi SUT",
            'expected_results': "VM Created Successfully"},
        3: {'step_details': "Verify VMware Tool installed on VM or not",
            'expected_results': "Successfully verified VMware Tool on VM"},
        4: {'step_details': "Shutdown the VM",
            'expected_results': "VM shutdown executed successfully"},
        5: {'step_details': "Set half of the CPUs to 2 VMs",
            'expected_results': "Successfully set CPUs in VMs"},
        6: {'step_details': "Start CPU Stress in both VMs",
            'expected_results': "Successfully Executed CPU Stress test"},
    }
    BURNIN_EXECUTION_TIME = 30  # in minutes
    BURNING_80_WORKLOAD_CONFIG_FILE = "cmdline_config.txt"
    BIOS_CONFIG_FILE = "virtualization_vmware_burn_stress_bios_knob.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwareToolsInstallRHelGuest object.

        """
        super(VirtualizationVmwareOverCommitCpuIOWrkLdMultiVM, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self.stress_app_provider = StressAppTestProvider.factory(test_log, os_obj=self.os, cfg_opts=cfg_opts)
        self.burnin_config_file = Path(os.path.dirname(os.path.abspath(__file__)))
        self.burnin_config_file = os.path.join(self.burnin_config_file, self.BURNING_80_WORKLOAD_CONFIG_FILE)

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

            self._test_content_logger.start_step_logger(4)
            # Shutdown the VM
            # self.shutdown_vm_esxi(vm_name)
            self._test_content_logger.end_step_logger(4, return_val=True)

        cpu_num = self._common_content_lib.execute_sut_cmd("cat /proc/cpuinfo | grep 'process' | sort | uniq | wc -l",
                                                           "get total CPU", self._command_timeout)
        num = math.ceil(int(cpu_num) / 2)

        for index in range(len(self.VM)):
            vm_name = self.VM[index] + "_" + str(index)
            self._log.info('Assign more CPUs to the virtual machines than total available CPUs on SUT')
            self._test_content_logger.start_step_logger(5)
            result = self.virt_execute_host_cmd_esxi(f'Get-VM {vm_name} | Set-VM -NumCpu {num} -Confirm:$false')
            self._test_content_logger.end_step_logger(5, return_val=True)
            self._log.info('Each CLI exec successfully and returns a zero return code', result == '')
            self.start_vm_esxi(vm_name)
            vm_os_obj = self.create_esxi_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self._test_content_logger.start_step_logger(6)
            self._log.info('Run stress tests in VM {} with half of assigned CPU simultaneously'.format(index))

            bit_location = self._install_collateral.install_burnin_linux(common_content_lib_vm_obj, vm_os_obj)
            cpu_thread = threading.Thread(target=self.stress_app_provider.execute_burnin_test, args=(self.log_dir,
                                                                                                     self.BURNIN_EXECUTION_TIME,
                                                                                                     bit_location,
                                                                                                     self.burnin_config_file,
                                                                                                     vm_name, True,
                                                                                                     vm_os_obj,
                                                                                                     common_content_lib_vm_obj))
            self._log.info("Stress Start")
            cpu_thread.start()
            time.sleep(6)

            self._test_content_logger.end_step_logger(6, return_val=True)


        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationVmwareOverCommitCpuIOWrkLdMultiVM, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmwareOverCommitCpuIOWrkLdMultiVM.main()
             else Framework.TEST_RESULT_FAIL)
