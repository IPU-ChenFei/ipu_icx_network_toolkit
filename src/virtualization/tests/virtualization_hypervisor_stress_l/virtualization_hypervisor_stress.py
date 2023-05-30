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
# treaty provisions. No part of the Mat erial may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret o  r other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#################################################################################

import sys
import os
import re
import threading
import time


from src.provider.storage_provider import StorageProvider
from pathlib import Path

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.lib.test_content_logger import TestContentLogger
from src.lib.common_content_lib import CommonContentLib
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import TimeConstants
from src.provider.stressapp_provider import StressAppTestProvider


class VirtualizationRHELHypervisorStress(VirtualizationCommon):
    """
    Pheonix ID: 18014072832
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Install virt-install if not present.
    2. Copy RHEL ISO image to SUT under '/var/lib/libvirt/images'.
    4. Create VM and install Burin tool on SUT and VM.
    5. Start Stress load testing using Burnin Tool
    5. Verify SUT and VM is running.
    """
    TEST_CASE_ID = ["P18014072832", "VirtualizationRHELHypervisorStress"]
    STEP_DATA_DICT = {
        1: {'step_details': "Create the VM machine names.",
            'expected_results': "VM machine names created successfully"},
        2: {'step_details': "Install Burnin Tool on SUT.",
            'expected_results': "Burnin Tool Installed on SUT successfully"},
        3: {'step_details': "Create the VM machine.",
            'expected_results': "VM machine created successfully"},
        4: {'step_details': "Install Burnin Tool on SUT.",
            'expected_results': "Burnin Tool Installed on SUT successfully."},
        5: {'step_details': "Create thread for Burnin Test on VM",
            'expected_results': "Burnin Test on VM started successfully"},
        6: {'step_details': "Create thread for Burnin Test on SUT",
            'expected_results': "Burnin Test on SUT started successfully"},
        7: {'step_details': "Check if VM is alive",
            'expected_results': "VM OS is working fine and stable"},
        8: {'step_details': "Check if SUT is alive",
            'expected_results': "SUT OS is working fine and stable"},
    }
    BIOS_CONFIG_FILE = "virtualization_hypervisor_stress_bios_knobs.cfg"
    NUMBER_OF_VMS = 1
    VM = [VMs.RHEL]*1
    VM_TYPE = "RHEL"
    BURNING_80_WORKLOAD_CONFIG_FILE = "cmdline_config_80_workload.txt"
    BIT_TIMEOUT = 1   # 120 in minutes
    SUT_BIT_LOCATION = None

    VM_NAME = None
    bit_location = None
    REPOS_FOLDER_PATH_SUT = "/etc/yum.repos.d"
    C_DRIVE_PATH = "C:\\"
    YUM_REPO_FILE_NAME = r"intel-yum-rhel.repo"
    REPOS_FOLDER_PATH_SUT = "/etc/yum.repos.d"
    ENABLE_YUM_REPO_COMMAND = "yum repolist all"
    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationRHELKvmVmCreation object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationRHELHypervisorStress, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._storage_provider = StorageProvider.factory(self._log, self.os, cfg_opts)  # type: StorageProvider
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self.stress_app_provider = StressAppTestProvider.factory(self._log, os_obj=self.os, cfg_opts=cfg_opts)
        self.burnin_config_file = Path(os.path.dirname(os.path.abspath(__file__)))
        self.burnin_config_file = os.path.join(self.burnin_config_file, self.BURNING_80_WORKLOAD_CONFIG_FILE)
        self._cfg_opt = cfg_opts

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.

        :return: None
        """
        # Check the for the Windows OS in the SUT
        if self.os.os_type == OperatingSystems.LINUX:
            self._log.info("We have Linux OS for test case... proceeding further..")
        else:
            raise content_exceptions.TestFail("Target is not booted with Linux")

        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)

        super(VirtualizationRHELHypervisorStress, self).prepare()


    # how to control TC execution time
    def execute(self):
        """
        1. create VM
        2. Install Burin Tool on SUT and VM
        3. Run stress load test using VM
        4. Wait for test to complete
        5. Check if SUT and VM is functioning or not
        """
        self._test_content_logger.start_step_logger(1)
        burnin_thread = None
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" Creating VM:{} on RHEL.".format(vm_name))
        self._test_content_logger.end_step_logger(1, True)

        stress_thread = []
        vm_sut_obj_list = []
        bit_location_vm = None
        stressapp_provider_obj_list = []
        thread_val = []
        self._test_content_logger.start_step_logger(2)
        self.bit_location = self.collateral_installer.install_burnintest()  # install burnin tool
        self._test_content_logger.end_step_logger(2, True)

        common_content_lib_vm_obj = None

        for vm_name in self.LIST_OF_VM_NAMES:
            # create with default values
            # reconfig with max capacity of disk and ram
            self._test_content_logger.start_step_logger(3)
            self.create_vm(vm_name, self.VM_TYPE, mac_addr=True)
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            vm_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_obj)
            self._test_content_logger.end_step_logger(3, True)

            self._test_content_logger.start_step_logger(4)
            install_collateral_vm_obj = InstallCollateral(self._log, vm_obj, self._cfg_opt)
            stress_app_provider_vm = StressAppTestProvider.factory(self._log, os_obj=vm_obj, cfg_opts=self._cfg_opt)
            stressapp_provider_obj_list.append(stress_app_provider_vm)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_obj, self._cfg_opt)
            self.get_yum_repo_config(vm_obj, common_content_lib_vm_obj, os_type="centos",machine_type="vm")
            self.install_burnin_dependencies_linux(vm_obj, common_content_lib_vm_obj)
            # To install BurnIn tool in VM
            bit_location_vm = install_collateral_vm_obj.install_burnin_linux()
            self._test_content_logger.end_step_logger(4, True)


        for index, each, app_list in zip(range(len(self.LIST_OF_VM_NAMES)), vm_sut_obj_list,
                                         stressapp_provider_obj_list):
            vm_name = self.LIST_OF_VM_NAMES[index]
            # execute burnin test on VM
            self._test_content_logger.start_step_logger(5)
            self._log.info("Starting Burnin stress test on VM")
            stress_thread = threading.Thread(target=app_list.execute_burnin_test,
                                             args=(self.log_dir, self.BIT_TIMEOUT, bit_location_vm,
                                                   self.BURNING_80_WORKLOAD_CONFIG_FILE, vm_name))
            # Thread has been started
            stress_thread.start()
            thread_val.append(stress_thread)
            self._test_content_logger.end_step_logger(5, True)

        # execute burnin test on SUT
        self._log.info("Starting Burnin stress test on SUT")
        self._test_content_logger.start_step_logger(6)
        burnin_thread = threading.Thread(target=self.stress_app_provider.execute_burnin_test,
                                         args=(self.log_dir, self.BIT_TIMEOUT, self.bit_location,
                                               self.BURNING_80_WORKLOAD_CONFIG_FILE,))
        # Thread has been started
        burnin_thread.start()
        self._log.info("Successfully started Burnin Stress on SUT and VM")
        self._test_content_logger.end_step_logger(6, True)

        time.sleep((self.BIT_TIMEOUT) + TimeConstants.FIVE_MIN_IN_SEC)

        self._log.info("Killing all threads for Burnin Stress on SUT and VM")

        for thread in thread_val:
            thread.join()

        burnin_thread.join()

        self._test_content_logger.start_step_logger(7)
        for vm_name in self.LIST_OF_VM_NAMES:
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
        self._test_content_logger.end_step_logger(7, True)

        self._test_content_logger.start_step_logger(8)
        if not self.os.is_alive():
            self._log.error("Linux SUT is not alive")
            return False
        self._test_content_logger.end_step_logger(8, True)

        self._log.info("Successfully tested Burnin Stress on VM")
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationRHELHypervisorStress, self).cleanup(return_status)



if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationRHELHypervisorStress.main()
             else Framework.TEST_RESULT_FAIL)
