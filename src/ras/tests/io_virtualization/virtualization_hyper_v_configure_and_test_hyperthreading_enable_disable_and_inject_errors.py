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

from collections import Counter

from dtaf_core.lib.dtaf_constants import Framework


from src.lib.os_lib import WindowsCommonLib
from src.provider.vm_provider import VMProvider, VMs
from src.ras.tests.io_virtualization.cscripts_pcie_error_injection_base_test import VmmCscriptsPcieErrorInjectionBaseTest
from src.lib.install_collateral import InstallCollateral
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import ErrorTypeAttribute
from dtaf_core.providers.provider_factory import ProviderFactory
from src.ras.lib.ras_common_utils import RasCommonUtil
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.ras.tests.io_virtualization.interleave_base_test import InterleaveBaseTest


class VirtualizationHyperthreadingEnableDisableAndInjectErrors(VmmCscriptsPcieErrorInjectionBaseTest):
    """
    GLASGOW ID: G69285

    This case tests the enable and disable of Hyperthreading and how it may affect virtual machines.
    On top of testing Hyperthreading enable/disable, Injections of PCIe and Memory will be tested to
    ensure system functions w/o any issues.
    """
    BIOS_CONFIG_FILE = ["virtualization_hyperv_hyperthreading_enable.cfg",
                        "virtualization_hyperv_hyperthreading_disable.cfg"]
    C_DRIVE_PATH = "C:\\"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationHyperthreadingEnableDisableAndInjectErrors object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        self._cfg_opts = cfg_opts
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE[0])
        super(VirtualizationHyperthreadingEnableDisableAndInjectErrors, self).__init__(test_log, arguments, cfg_opts,
                                                                                 bios_config_file=bios_config_file)
        self._windows_common_lib = WindowsCommonLib(self._log, self.os)
        self._interleave_base_test = InterleaveBaseTest(test_log, arguments, cfg_opts)

    def prepare(self):  # type: () -> None
        """
        To Setup prepare
        """
        super(VirtualizationHyperthreadingEnableDisableAndInjectErrors, self).prepare()
        self._vm_provider_obj.install_vm_tool()

    def execute(self):
        """
        1. Enable Hyperthreading and Create Gen2 VM
        2. Enter number of processors and start prime95
        3. Inject PCIE and Memory errors
        4. Disable Hyperthreading and repeat

        :return : True on Success
        """
        # Creating Gen2 VM
        self.VM_OS = ["Windows"]
        for index in range(0, self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            self._log.info("Creating VM on Hyper V")
            vm_name = self.VM_OS[0] + "_" + str(index)

            #  Create VM from Template
            self._vm_provider_obj.create_vm_from_template(vm_name, gen=2)  # Create VM function
            self._vm_provider_obj.start_vm(vm_name)
            self._vm_provider_obj.wait_for_vm(vm_name)

            #  Get Mac id flag from config to Assign the Mac id to Network
            mac_id_flag = self._common_content_configuration.enable_with_mac_id()

            #  Add VM Network Adapter to VM
            time.sleep(self.WAIT_TIME)
            self._vm_provider_obj.add_vm_network_adapter(self.NETWORK_ASSIGNMENT_TYPE, vm_name, self.ADAPTER_NAME,
                                                         self.VSWITCH_NAME, vm_type="RS5", mac_addr=mac_id_flag)

            #  Verify Hyper-V VM
            time.sleep(self.WAIT_TIME)
            self.virtualization_obj.verify_hyperv_vm(vm_name, vm_type="RS5")

            #  Start VM
            time.sleep(self.WAIT_TIME)
            self._vm_provider_obj.start_vm(vm_name)

            #  Create SSH to VM
            time.sleep(self.WAIT_TIME)
            self.virtualization_obj.create_ssh_vm_object(vm_name, copy_open_ssh=True)

            vm_os_obj = self.virtualization_obj.windows_vm_object(vm_name=vm_name, vm_type="RS5")
            try:
                ipconfig_output = vm_os_obj.execute("ipconfig", self._command_timeout)
                self._log.info("IPCONFIG- {}".format(ipconfig_output.stdout))
            except:
                self._log.error("SSH is not established properly....trying again to enable the ssh")
                self.virtualization_obj.create_ssh_vm_object(vm_name, copy_open_ssh=False)
                ipconfig_output = vm_os_obj.execute("ipconfig", self._command_timeout)
                self._log.info("IPCONFIG- {}".format(ipconfig_output.stdout))

            # Creating new objects for VM
            self.install_collateral = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)
            self.stress_provider = StressAppTestProvider.factory(self._log, self._cfg_opts, vm_os_obj)
            self.windows_common_lib = WindowsCommonLib(self._log, vm_os_obj)
            self.common_content_lib = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)

        # Running with Hyperthreading enabled
        self._log.info("RUNNING WITH HYPERTHREADING ENABLED.........................")
        self.hyperthreading_functionality(vm_os_obj, vm_name)
        try:
            self._interleave_base_test.enable_interleave_bios_knobs(self.BIOS_CONFIG_FILE[1])
        except:
            raise content_exceptions.TestFail("Second bios setting did not happen i.e."
                                              "Hyperthreading disable bios did not happen")

        # Running with Hyperthreading disabled
        self._log.info("RUNNING WITH HYPERTHREADING DISABLED.........................")
        self.hyperthreading_functionality(vm_os_obj, vm_name)

        # checking if VM is running
        self._log.info("Final check to see VM is running")
        vm_status = self._vm_provider_obj._get_vm_state(vm_name)
        if not 'Running' == vm_status:
            raise content_exceptions.TestFail("Vm is not running after all injections....")
        self._log.info("VM is running.....")
        return True

    def hyperthreading_functionality(self, vm_os_obj, vm_name):
        """
        Method to perform hyperthreading and inject PCIe and Memory Errors.

        :param: vm_os_obj: VM object
        :param: vm_name: name of VM
        :return: True/False
        """
        vm_status = self._vm_provider_obj._get_vm_state(vm_name)
        try:
            if not 'Running' == vm_status:
                self._vm_provider_obj.turn_off_vm(vm_name)
                time.sleep(self.WAIT_TIME)
        except:
            self._log.info("Couldn't turn off the VM")
        try:
            self._vm_provider_obj.start_vm(vm_name)
            time.sleep(self.WAIT_TIME)
        except:
            self._log.info("Couldn't Turn On the VM")
        vm_status = self._vm_provider_obj._get_vm_state(vm_name)
        if not 'Running' == vm_status:
            self._log.info("Hyperthreading disabled confirmed as VM not booting....")

        # set VM Processors and memory
        self._log.info("Changing number of CPUs and Memory...")
        if 'Running' == vm_status:
            self._vm_provider_obj.turn_off_vm(vm_name)
        time.sleep(self.WAIT_TIME)
        available_mem = self._common_content_lib.get_os_available_memory()
        no_of_cpus = self._common_content_lib.get_number_of_cpu_win()
        self._log.info("Available memory in the system = {}\nNumber of CPUs = {}".format(available_mem, no_of_cpus))
        if available_mem > self.MEM_10_GB:
            self._common_content_lib.execute_sut_cmd(self.SET_VM_MEMORY_CMD.format(vm_name, self.MEM_10_GB),
                                                     "setting VM memory", 60)
        else:
            self._common_content_lib.execute_sut_cmd(self.SET_VM_MEMORY_CMD.format(vm_name, available_mem),
                                                     "setting VM memory", 60)
        self._common_content_lib.execute_sut_cmd(self.SET_VM_PROCESSOR_CMD.format(vm_name, int(no_of_cpus / 2 + 1)),
                                                 "setting VM processors", 60)
        self._vm_provider_obj.start_vm(vm_name)
        time.sleep(self.WAIT_TIME)

        try:
            ipconfig_output = vm_os_obj.execute("ipconfig", self._command_timeout)
            self._log.info("IPCONFIG- {}".format(ipconfig_output.stdout))
        except:
            self._log.error("SSH is not established properly....trying again to enable the ssh")
            self.virtualization_obj.create_ssh_vm_object(vm_name, copy_open_ssh=False)
            ipconfig_output = vm_os_obj.execute("ipconfig", self._command_timeout)
            self._log.info("IPCONFIG- {}".format(ipconfig_output.stdout))

        # Copy and run prime95 on VM
        self._stress_app_path, self._stress_tool_name = self.install_collateral.install_prime95(app_details=True)
        system_memory_info = self.windows_common_lib.get_system_memory()
        total_memory_data_win = [int(system_memory_info[0].split(":")[1].strip("MB").strip().replace(",", ""))]
        preference_prime_params = ["V24OptionsConverted=1\n", "StressTester=1\n", "UsePrimenet=0\n",
                                   "TortureMem={}\n".format(total_memory_data_win),
                                   "TortureTime=6\n", "TortureWeak=0\n", "[PrimeNet]\n", "Debug=0"]
        self.common_content_lib.create_prime95_preference_txt_file(self._stress_app_path, preference_prime_params)

        self.stress_provider.execute_async_stress_tool(self.STRESS_COMMAND_DICT[self._stress_tool_name],
                                                       self._stress_tool_name,
                                                       self._stress_app_path)

        # Verify prime tool is running
        time.sleep(self.WAIT_TIME)
        if self.stress_provider.check_app_running(self._stress_tool_name) != 0:
            raise content_exceptions.TestFail("Prime95 tool not running on VM")

        # injecting PCIe errors and verifying
        # self.cscripts_pcie_error_injection_vmm_windows_vm()
        error_type = ErrorTypeAttribute.CE
        err_type = ErrorTypeAttribute.CORRECTABLE
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        socket = self._common_content_configuration.get_cscripts_ei_pcie_device_socket()
        port = self._common_content_configuration.get_cscripts_ei_pcie_device_pxp_port()
        error_signature_list = self.ERR_SIG[OperatingSystems.WINDOWS][err_type]
        self._log.info("Injecting PCIe Correctable error 30 times....")
        for num in range(self.NUM_OF_INJECTIONS):
            self._common_content_lib.clear_windows_mce_logs()
            self._log.info("PCIe error injection - {}".format(num + 1))
            self.smm_break_and_inject_pcie_error_via_cscripts(csp=cscripts_obj, sdp=sdp_obj, socket=socket, port=port,
                                                              err_type=error_type)
            if err_type in self.UNC_LIST:
                ras_common_util = RasCommonUtil(self._log, vm_os_obj, self.cfg_opts, self._common_content_configuration)
                ras_common_util.ac_cycle_if_os_not_alive(self.ac_power, auto_reboot_expected=True)

            time.sleep(self.ERROR_INJECT_WAIT_TIME_SEC)

           #  Verify error in OS
            vmm_indicated_err_in_event_log = self._os_log_obj.verify_os_log_error_messages(
                __file__, self._os_log_obj.DUT_WINDOWS_WHEA_LOG, error_signature_list)
            if not vmm_indicated_err_in_event_log:
                raise content_exceptions.TestFail("Error Signature was not Captured in OS Log")
        self._log.info("Error Signature was found as Expected in OS Log")

        # injecting memory errors and verifying
        self._log.info("Injecting memory error 30 times....")
        for num in range(self.NUM_OF_INJECTIONS):
            self._common_content_lib.clear_windows_mce_logs()
            self._log.info("Memory error injection - {}".format(num + 1))
            self.inject_and_verify_mem_error(ErrorTypeAttribute.CORRECTABLE)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        1. Destroy Created VM.
        """
        super(VirtualizationHyperthreadingEnableDisableAndInjectErrors, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationHyperthreadingEnableDisableAndInjectErrors.main()
             else Framework.TEST_RESULT_FAIL)
