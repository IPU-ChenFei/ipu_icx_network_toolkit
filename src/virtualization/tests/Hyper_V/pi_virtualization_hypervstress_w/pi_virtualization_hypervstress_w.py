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
import os
import time
import threading

from dtaf_core.lib.dtaf_constants import Framework

from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.install_collateral import InstallCollateral
from src.provider.stressapp_provider import StressAppTestProvider
from src.provider.vm_provider import VMs
from src.lib.dtaf_content_constants import TimeConstants, BurnInConstants
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.lib.content_artifactory_utils import ContentArtifactoryUtils


class PiVirtualizationHyperVStressWindows(VirtualizationCommon):
    """
    HPALM ID: H79617 - pi_virtualization_hypervstress_w

    This class is used to create 4 different VM's and run the Burnin parallely on each VM for 2 hours
    """
    TEST_CASE_ID = ["H79617", "pi_virtualization_hypervstress_w"]
    BURNING_100_WORKLOAD_CONFIG_FILE = "cmdline_config_100_workload_windows.bitcfg"
    BIOS_CONFIG_FILE = 'hyperv_stress_bios_knobs.cfg'
    VM_TYPE = "RS5"
    VM = [VMs.WINDOWS] * 4

    STEP_DATA_DICT = {
        1: {'step_details': "Install 4 VM's on the windows HOST",
            'expected_results': "VM's to be installed successfully"},
        2: {'step_details': "Boot to each VM and run Burnin app for 2 hours",
            'expected_results': "Execution of Burin app to be successful in each VM"}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new test object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        self.bios_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(PiVirtualizationHyperVStressWindows, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._artifactory_obj = ContentArtifactoryUtils(self._log, self.os, self._common_content_lib, cfg_opts)
        self.stress_app_provider_sut = StressAppTestProvider.factory(self._log, os_obj=self.os, cfg_opts=cfg_opts)
        self.burnin_config_file_host_path = None

    def prepare(self):  # type: () -> None
        """
        1. sets the BIOS
        2. Installs 4 VM's on the hyperv
        :return: none
        """
        try:
            self.bios_util.load_bios_defaults()
            self.bios_util.set_bios_knob(bios_config_file=self.bios_file_path)
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
            self.bios_util.verify_bios_knob(bios_config_file=self.bios_file_path)
        except Exception as ex:
            self.os.wait_for_os(self.reboot_timeout)

        self._test_content_logger.start_step_logger(1)
        self._vm_provider.install_vm_tool()
        for index in range(len(self.VM)):
            self._log.info("Creating VM on Hyper V")
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_hyperv_vm(vm_name, self.VM_TYPE)  # Create VM function
            self._vm_provider.wait_for_vm(vm_name)  # Wait for VM to boot
            self._vm_provider.add_vm_network_adapter(self.NETWORK_ASSIGNMENT_TYPE, vm_name, self.ADAPTER_NAME,
                                                     self.VSWITCH_NAME)
            self.verify_hyperv_vm(vm_name, self.VM_TYPE)
        self._test_content_logger.end_step_logger(1, True)

    def execute(self):
        """
        1. To create the windows VM.
        2. To enable SSH in Windows VM
        3. Execute the burnin test on the VM's and SUT.

        :return: True if Burin all the VM's boot and run Burnin parallelly else False
        """
        stressapp_provider_obj_list = []
        vm_sut_obj_list = []
        bit_location = None
        self._test_content_logger.start_step_logger(2)
        for vm_name in self.LIST_OF_VM_NAMES:
            self.create_ssh_vm_object(vm_name)
            vm_obj = self.windows_vm_object(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_obj)
            install_collateral_vm_obj = InstallCollateral(log=self._log, os_obj=vm_obj, cfg_opts=self._cfg)
            stress_app_provider_vm = StressAppTestProvider.factory(self._log, os_obj=vm_obj, cfg_opts=self._cfg)
            stressapp_provider_obj_list.append(stress_app_provider_vm)
            bit_location = install_collateral_vm_obj.install_burnin_windows()
        stressapp_provider_obj_list.append(self.stress_app_provider_sut)
        for each in vm_sut_obj_list:
            self.burnin_config_file_host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
                self.BURNING_100_WORKLOAD_CONFIG_FILE)
            self._log.info("Starting Burning on VM WINDOWS_{}".format(vm_sut_obj_list.index(each)))
            stress_thread = threading.Thread(target=self.burn, args=(bit_location, self.burnin_config_file_host_path,
                                                                     TimeConstants.TWO_HOUR_IN_SEC/
                                                                     TimeConstants.ONE_MIN_IN_SEC, each))
            stress_thread.start()
        time.sleep(TimeConstants.TWO_HOUR_IN_SEC)
        for stress_obj in stressapp_provider_obj_list:
            self._log.info("Killing Stress on VM WINDOWS_{}".format(stressapp_provider_obj_list.index(stress_obj)))
            stress_obj.kill_stress_tool(BurnInConstants.BIT_EXE_FILE_NAME_WINDOWS.split('.')[0])
        for each in vm_sut_obj_list:
            bit_log_path = os.path.join(bit_location, BurnInConstants.BURNIN_BIT_LOG)
            each.copy_file_from_sut_to_local(bit_log_path.strip(), os.path.join(self.log_dir,
                                                                                BurnInConstants.BURNIN_BIT_LOG))
            with open(os.path.join(self.log_dir, BurnInConstants.BURNIN_BIT_LOG)) as f:
                data = f.read()
                if BurnInConstants.BURNIN_TEST_FAIL_CMD in data:
                    raise content_exceptions.TestFail("BurnIn Test ended with failures")
        self._log.info("Burnin stress executed successfully")
        for vm_name in self.LIST_OF_VM_NAMES:
            self._log.info("Verifing VM Functionality for {}".format(vm_name))
            self.verify_vm_functionality(vm_name, self.VM_TYPE, enable_yum_repo=False)
        self._test_content_logger.end_step_logger(2, True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """DTAF cleanup"""
        super(PiVirtualizationHyperVStressWindows, self).cleanup(return_status)

    def burn(self, bit_location, config_file, timeout, object_to_test):
        """
        This Method is used to run the burnin app
        :bit_location: to copy burnin app to the destination folder
        :config_file: config_file to run the stress on
        :object_to_test: which object to be tested
        :return: None
        """
        stress_app_provider = StressAppTestProvider.factory(self._log, os_obj=object_to_test, cfg_opts=self._cfg)
        # Copy the config file to the folder
        self._log.info("Copy the config file to the burnin tool folder")
        object_to_test.copy_local_file_to_sut(source_path=config_file, destination_path=bit_location)

        self._log.info("Execute burnin test tool command {}".format(
            BurnInConstants.BURNIN_TEST_CMD_WINDOWS.format(os.path.basename(config_file), timeout)))

        stress_app_provider.execute_async_stress_tool(
            stress_tool_cmd=BurnInConstants.BURNIN_TEST_CMD_WINDOWS.format(os.path.basename(config_file), timeout),
            stress_tool_name=BurnInConstants.BIT_EXE_FILE_NAME_WINDOWS, executor_path=bit_location,
            timeout=timeout * 60)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiVirtualizationHyperVStressWindows.main() else Framework.TEST_RESULT_FAIL)

