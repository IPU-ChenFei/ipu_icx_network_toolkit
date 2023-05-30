#!/usr/bin/env python
##########################################################################
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
##########################################################################
import sys
import os
import time
import six

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.lib.dtaf_constants import OperatingSystems, Framework
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.dtaf_content_constants import ErrorTypeAttribute
from src.lib.os_lib import WindowsCommonLib
from src.provider.vm_provider import VMs
from src.ras.tests.io_virtualization.cscripts_pcie_error_injection_base_test import VmmCscriptsPcieErrorInjectionBaseTest
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib import content_exceptions


class VirtualizationHyperVSriovStressCorrectableErrorInjection(VmmCscriptsPcieErrorInjectionBaseTest):
    """
    Create and stress SR-IOV ports created in Hyper-V  and stress agianst other VMs or external clients to ensure stability of the SR-IOV ports.
    While the system is running inject errors throughout the duration (12 hrs) of the test to ensure system remains stable
    Glossgow: G69456
    """

    BIOS_CONFIG_FILE = "sriov_stress_bios_knobs.cfg"
    C_DRIVE_PATH = "C:\\"

    VM = VMs.WINDOWS
    VM_TYPE = "RS5"
    NETWORK_ASSIGNMENT_TYPE = "SRIOV"
    VSWITCH_NAME = "ExternalSwitch"
    STRESS_DURATION_IN_SEC = 43200
    STRESS_TOOL_BUFFER_TIMER_IN_SEC = 600
    NETWORK_SWITCH_WAIT_TIMER_IN_SEC = 20
    STRESS_TOOL = "iperf3.exe"
    ERR_TYPE = ErrorTypeAttribute.CORRECTABLE
    SEVERITY = None
    CORRECTABLE_ERROR_SIG = ["corrected hardware error", "PCI Express Root Port"]

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts
    ):
        """
        Create an instance of VirtualizationHyperVSriovStressCorrectableErrorInjection

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(VirtualizationHyperVSriovStressCorrectableErrorInjection, self).__init__(test_log, arguments, cfg_opts, bios_config_file=bios_config_file)
        self._windows_common_lib = WindowsCommonLib(self._log, self.os)
        self._stress_provider_obj = StressAppTestProvider.factory(self._log, cfg_opts, self.os)
        self.num_vms = 1
        self.VM_OS = [VMs.WINDOWS]
        vm_adapter = self._common_content_configuration.get_sriov_adapter()
        self.vm_physical_adapter = self._windows_common_lib.get_network_adapter_name(vm_adapter)
        loop_back_adapter = self._common_content_configuration.get_loop_back_adapter()
        self.loop_back_physical_adpater = self._windows_common_lib.get_network_adapter_name(loop_back_adapter)
        self.SUT_STATIC_IP = self._common_content_configuration.get_sut_static_ip()
        self.VM_STATIC_IP = self._common_content_configuration.get_vm_static_ip()
        self.SUBNET_MASK = self._common_content_configuration.get_subnet_mask()
        self.GATEWAY_IP = self._common_content_configuration.get_gateway_ip()
        self.cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        self.sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)

    def prepare(self):  # type: () -> None
        """
        This method is to execute prepare.
        """
        super(VirtualizationHyperVSriovStressCorrectableErrorInjection, self).prepare()
        self._vm_provider_obj.install_vm_tool()
        self._vm_provider_obj.remove_network_adapter(self.VSWITCH_NAME)
        # Copy iperf on SUT
        self.sut_iperf_path = self._install_collateral.install_iperf_on_windows()

    def execute(self, ERR_TYPE=ErrorTypeAttribute.CORRECTABLE, SEVERITY=None):  # type: () -> bool
        """
        This method is to
        1. Create VM
        2. Verify VM
        3. add SRIOV supported network adapter to VM
        4. Configure static ip on VM and SUT
        3. Run iperf traffic across SUT and VM
        4. inject correctable error
        5. Verify VM

        """
        destination_path_on_vm = os.path.join("c:\\", self._install_collateral.IPERF_TOOL_WINDOWS)
        #  Create VM names dynamically according to the OS
        self._log.info("Creating VM on Hyper V")
        vm_name = self.VM + "_0"
        self.virtualization_obj.create_hyperv_vm(vm_name, self.VM_TYPE)
        self._vm_provider_obj.wait_for_vm(vm_name)

        # Assign Network Adapter to VM using SRIOV
        self._vm_provider_obj.add_vm_network_adapter(self.NETWORK_ASSIGNMENT_TYPE, vm_name, self.vm_physical_adapter,
                                                     self.VSWITCH_NAME)
        time.sleep(self.NETWORK_SWITCH_WAIT_TIMER_IN_SEC)

        # Assign static ip on SUT network adapter
        self._log.info("Set static ip {} to adapter {} on SUT".format(self.SUT_STATIC_IP, self.loop_back_physical_adpater))
        self._windows_common_lib.configure_static_ip(self.loop_back_physical_adpater, self.SUT_STATIC_IP, self.SUBNET_MASK, self.GATEWAY_IP)

        # Assign static ip on VM
        self._log.info("Set static ip {} to VM {}".format(self.VM_STATIC_IP, vm_name))
        self._vm_provider_obj.assign_static_ip_to_vm(vm_name, self.WINDOWS_VM_USERNAME, self.WINDOWS_VM_PASSWORD,
                                                     static_ip=self.VM_STATIC_IP, gateway_ip=self.GATEWAY_IP, subnet_mask=self.SUBNET_MASK)
        if not self._vm_provider_obj.ping_vm_from_sut(self.VM_STATIC_IP, vm_name, self.WINDOWS_VM_USERNAME, self.WINDOWS_VM_PASSWORD):
            raise content_exceptions.TestFail("Fail to ping the VM ip {} from SUT".format(self.SUT_STATIC_IP))

        # Copy iperf on VM
        self.vm_iperf_path = self._vm_provider_obj.copy_package_to_VM(vm_name, self.WINDOWS_VM_USERNAME,
                                                                      self.WINDOWS_VM_PASSWORD, self._install_collateral.IPERF_TOOL_WINDOWS,
                                                                      destination_path_on_vm)

        #Start iperf on SUT and VM
        iperf_server_cmd = "{} -s -p 5201 > iperf_server.txt".format(self.STRESS_TOOL)
        iperf_client_cmd = "{" + '{} -c {} -u -t {} -i 1 -p 5201'.format(self.STRESS_TOOL, self.SUT_STATIC_IP, self.STRESS_DURATION_IN_SEC + self.STRESS_TOOL_BUFFER_TIMER_IN_SEC) + "}"
        self._stress_provider_obj.execute_async_stress_tool(iperf_server_cmd, "iperf3.exe", self.sut_iperf_path)
        self._log.info("Started iperf server on SUT")
        self._vm_provider_obj.start_iperf_on_vm(vm_name, self.WINDOWS_VM_USERNAME, self.WINDOWS_VM_PASSWORD, iperf_client_cmd, self.vm_iperf_path)

        # Get socket and port from config
        socket = self._common_content_configuration.get_cscripts_ei_pcie_device_socket()
        port = self._common_content_configuration.get_cscripts_ei_pcie_device_pxp_port()

        if ERR_TYPE == ErrorTypeAttribute.CORRECTABLE:
            error_type = "ce"
            error_signautre_list = self.CORRECTABLE_ERROR_SIG
        elif ERR_TYPE == ErrorTypeAttribute.UNC_NON_FATAL:
            error_type = "uce"
            error_signautre_list = self.ERR_SIG[OperatingSystems.WINDOWS][ErrorTypeAttribute.UNC_NON_FATAL_EDPC_DISABLED]

        # Inject CE error and monitor the iperf status on SUT and VM
        self._log.info("Inject {} error and monitor the iperf status on SUT and VM".format(error_type.upper()))
        start_time = time.time()
        end_time = start_time + self.STRESS_DURATION_IN_SEC
        counter = 1
        while end_time > time.time():
            if not self._vm_provider_obj.check_application_status(vm_name, self.WINDOWS_VM_USERNAME, self.WINDOWS_VM_PASSWORD, self.STRESS_TOOL):
                raise content_exceptions.TestFail("{} fails to run on VM after {} iteration".format(self.STRESS_TOOL, counter))
            if self._stress_provider_obj.check_app_running(self.STRESS_TOOL):
                raise content_exceptions.TestFail("{} fails to run on SUT after {} iteration".format(self.STRESS_TOOL, counter))
            self._log.info("iperf is running on the SUT")

            self._common_content_lib._clear_all_windows_os_error_logs(set_date=False)
            self.smm_break_and_inject_pcie_error_via_cscripts(self.cscripts_obj, self.sdp_obj, socket, port, error_type, SEVERITY)
            time.sleep(60)
            counter += 1
            self._log.info("Verify error in OS log")
            #  Verify error in OS
            vmm_indicated_err_in_event_log = self._os_log_obj.verify_os_log_error_messages(
                __file__, self._os_log_obj.DUT_WINDOWS_WHEA_LOG, error_signautre_list)
            if not vmm_indicated_err_in_event_log:
                raise content_exceptions.TestFail("Error Signature was not Captured in OS Log")
            self._log.info("Error Signature was found as Expected in OS Log")
        self._log.info("Error injection and stress test is successful for {}sec".format(self.STRESS_DURATION_IN_SEC))
        return True

    def cleanup(self, return_status):
        try:
            self._common_content_lib.execute_sut_cmd("taskkill /F /IM {} /T".format(self.STRESS_TOOL), "Kill iperf",
                                                     10)
        except Exception as err:
            self._log.info("iperf is not running on SUT - {}".format(err))
        super(VirtualizationHyperVSriovStressCorrectableErrorInjection, self).cleanup(return_status)

if __name__== "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationHyperVSriovStressCorrectableErrorInjection.main()
             else Framework.TEST_RESULT_FAIL)
