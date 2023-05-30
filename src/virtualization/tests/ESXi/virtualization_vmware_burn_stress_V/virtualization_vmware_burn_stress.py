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
import os
import sys
import time
import threading
from pathlib import Path

from src.lib.content_artifactory_utils import ContentArtifactoryUtils

from src.provider.stressapp_provider import StressAppTestProvider

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.internal.ssh_sut_os_provider import SshSutOsProvider

class VirtualizationVmwareBurnStress(VirtualizationCommon):
    """
    Phoenix ID: 18014075592
    Install Virtual OS on Vmware ,Make sure your config should have 64G memory at least.

    1. Enable vtd in Bios
    2. Copy Centos ISO images to ESXi SUT under 'vmfs/volumes/datastore1'.
    3. Create VM.
    5. Verify VM is running.
    6. Verify VMware tool installed on VM or not.
    7. Start burnin app on virtual OS for 2 hours.
    """

    NUM_VM=2
    NO_OF_RHEL_VMS = [VMs.RHEL] * NUM_VM
    NO_OF_WIN_VMS = [VMs.WINDOWS] * NUM_VM
    NUM_TOTAL_VM = 4

    VM_TYPE = []

    TEST_CASE_ID = ["P18014075592", "Virtualization_VMWare_Burn_Stress"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully'" },
        2: {'step_details': "Create 2 Windows and 2 Rhel VMs on ESXi SUT and Make unit configuration has memory size more than 64GB.",
            'expected_results': "VM2 Created Successfully" },
        3: {'step_details': "Verify VMware Tool installed on VM or not",
            'expected_results': "Successfully verified VMware Tool on VM" },
        4: {'step_details': "Boot to each virutal OS, start burnin app with default setting for 2hrs ",
            'expected_results': "Virtual OS is booting without error, burnin app is installed and VMs are running normally, No Os Crash " },
                    }
    BURNIN_EXECUTION_TIME = 10 # in minutes
    BURNING_80_WORKLOAD_CONFIG_FILE = "cmdline_config.txt"
    BIOS_CONFIG_FILE = "virtualization_vmware_burn_stress_bios_knob.cfg"
    BURNING_80_WORKLOAD_CONFIG_FILE_WINDOWS = "cmd_100_newbit.bitcfg"


    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwareBurnStress Object
        """
        super(VirtualizationVmwareBurnStress, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts= cfg_opts
        self._log= test_log
        self._virtualization_common = VirtualizationCommon
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self.stress_app_provider = StressAppTestProvider.factory(test_log, os_obj=self.os, cfg_opts=cfg_opts)
        self.burnin_config_file = Path(os.path.dirname(os.path.abspath(__file__)))
        self.burnin_config_file_win= Path(os.path.dirname(os.path.abspath(__file__)))
        self.burnin_config_file = os.path.join(self.burnin_config_file, self.BURNING_80_WORKLOAD_CONFIG_FILE)
        self.burnin_config_file_win = os.path.join(self.burnin_config_file_win, self.BURNING_80_WORKLOAD_CONFIG_FILE_WINDOWS)
        sut_ssh_cfg = cfg_opts.find(SshSutOsProvider.DEFAULT_CONFIG_PATH)
        self.sut_ssh = ProviderFactory.create(sut_ssh_cfg, test_log)
        self.sut_ip = self.sut_ssh._config_model.driver_cfg.ip
        self._artifactory_obj = ContentArtifactoryUtils(self._log, self.os, self._common_content_lib, self._cfg_opts)

    def prepare(self):
        # Need to implement bios configuration for ESXi SUT

        self._test_content_logger.start_step_logger(1)
        super(VirtualizationVmwareBurnStress, self).prepare()
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        self._test_content_logger.end_step_logger(1, return_val=True)


    def execute(self):
        """
        1. Create VMs
        2. Start VMS and install VMWare tools
        3. Start Burnin app on VMs for 2hrs with default option
        """
        burn_thread_list = []
        burn_thread_win_list = []
        vm_sut_obj_list = []

        self.NO_OF_VMS = self.NO_OF_RHEL_VMS + self.NO_OF_WIN_VMS

        for index in range(len(self.NO_OF_VMS)):
            self._test_content_logger.start_step_logger(2)
            vm_name = self.NO_OF_VMS[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.VM_TYPE.append(self.NO_OF_VMS[index])
            self._vm_provider.destroy_vm(vm_name)
            self.create_vmware_vm(vm_name, self.NO_OF_VMS[index], mac_addr=True, use_powercli="yes")
            self._test_content_logger.end_step_logger(2, return_val=True)
            self._test_content_logger.start_step_logger(3)
            self._vm_provider.install_vmware_tool_on_vm(vm_name)
            self._test_content_logger.end_step_logger(3, return_val=True)

            vm_os_obj = self.create_esxi_vm_host(vm_name, self.VM_TYPE[index])
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)

           # time.sleep(60)


            #if self.VM_TYPE == "RHEL":
            self._test_content_logger.start_step_logger(4)

            if "RHEL" in vm_name:
                self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, machine_type="vm")
                bit_location = self._install_collateral.install_burnin_linux(common_content_lib_vm_obj,vm_os_obj)
                time.sleep(10)
                burn_thread = threading.Thread(target=self.stress_app_provider.execute_burnin_test, args=(self.log_dir, self.BURNIN_EXECUTION_TIME,bit_location,
                                                                                                          self.burnin_config_file, vm_name,True,
                                                                                                          vm_os_obj, common_content_lib_vm_obj))
                self._log.info("Stress Start")
                burn_thread_list.append(burn_thread)
                time.sleep(6)


            elif "WINDOWS" in vm_name:

                vm_id = self.get_vm_id_esxi(vm_name)
                self.create_ssh_vm_object(vm_id = vm_id,vm_name=vm_name, copy_open_ssh=True, common_content_lib_vm_obj=common_content_lib_vm_obj)
                bit_location = self._install_collateral.install_burnin_windows(common_content_lib_vm_obj,vm_os_obj)
                time.sleep(10)

                burn_thread_win = threading.Thread(target=self.stress_app_provider.execute_burnin_test,
                                                   args=(self.log_dir,
                                                         self.BURNIN_EXECUTION_TIME,
                                                         bit_location,
                                                         self.burnin_config_file_win,
                                                         vm_name,True,vm_os_obj,
                                                         common_content_lib_vm_obj))
                self._log.info("Stress Start")
                burn_thread_win_list.append(burn_thread_win)
                time.sleep(6)
            self._test_content_logger.end_step_logger(4, return_val=True)

        for thread1 in burn_thread_list:
            thread1.start()

        for thread2 in burn_thread_win_list:
            thread2.start()

        for threads in (burn_thread_list+burn_thread_win_list):
            threads.join()

        return True

    def cleanup(self, return_status):
        super(VirtualizationVmwareBurnStress, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmwareBurnStress.main()
                else Framework.TEST_RESULT_FAIL)
