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
import threading
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_exceptions
from src.lib.os_lib import WindowsCommonLib
from src.lib.install_collateral import InstallCollateral
from src.provider.stressapp_provider import StressAppTestProvider

from src.lib.dtaf_content_constants import VmStressAttribute
from src.provider.vm_provider import VMs
from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon


class StressPcieErrorCheckingRasDuringStress(IoVirtualizationCommon):
    """
    GLASGOW ID: G10712
    Phoenix: 18014075828

    The purpose of this test is to ensure that no PCIe correctable errors occur during execution of stress
    on one or more PCIe devices in the SUT.
    This test is intended to be run in parallel with a stress test case.
    """

    TEST_CASE_ID = ["18014075828", "Stress_PCIe_Correctable_error_checking_RAS_during_stress"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new StressPcieErrorCheckingRasDuringStress object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        super(StressPcieErrorCheckingRasDuringStress, self).__init__(test_log, arguments, cfg_opts)
        self.iperf_path_on_sut = self._install_collateral.install_iperf_on_windows()
        self._windows_common_lib = WindowsCommonLib(self._log, self.os)
        vm_adapter = self._common_content_configuration.get_ethernet_adapter_for_vm()
        self.vm_physical_adapter = self._windows_common_lib.get_network_adapter_name(vm_adapter)
        loop_back_adapter = self._common_content_configuration.get_loop_back_adapter()
        self.loop_back_physical_adpater = self._windows_common_lib.get_network_adapter_name(loop_back_adapter)
        self.SUT_STATIC_IP = self._common_content_configuration.get_sut_static_ip()
        self.VM_STATIC_IP = self._common_content_configuration.get_vm_static_ip()
        self.SUBNET_MASK = self._common_content_configuration.get_subnet_mask()
        self.GATEWAY_IP = self._common_content_configuration.get_gateway_ip()
        self._stres_provider_obj = StressAppTestProvider.factory(self._log, cfg_opts, self.os)
        self._stres_provider_obj.kill_stress_tool(stress_tool_name="PCIERRpoll_debug")
        self._pcierrpoll_path = self._install_collateral.install_pcierrpoll()

    def execute(self):
        """
        This method is to
        1. Assign Static IP to SUT (Ethernet Port).
        2. Create VM
        3. Assign Static IP to VM
        4. Run Iperf between SUT and VM.
        5. Run PCIERR Poll Tool to check error.

        :raise : content_exceptions.TestFail
        :return : True on Success
        """
        vm_name = VMs.WINDOWS
        vm_type = VMs.RS5
        # Assign static ip on SUT network adapter
        self._log.info(
            "Set static ip {} to adapter {} on SUT".format(self.SUT_STATIC_IP, self.loop_back_physical_adpater))
        self._windows_common_lib.configure_static_ip(self.loop_back_physical_adpater, self.SUT_STATIC_IP,
                                                     self.SUBNET_MASK, self.GATEWAY_IP)

        # Create Virtual Switch for Static IP
        self._vm_provider_obj.create_bridge_network(switch_name=VmStressAttribute.VSWITCH_FOR_STATIC,
                                                    adapter_name=self.vm_physical_adapter)

        self._log.info("Creating VM - {}".format(vm_name))
        vm_os = self.create_vm_on_windows_sut(vm_name=vm_name, vm_type=vm_type,
                                              template=False, vm_os_type=
                                              OperatingSystems.WINDOWS, vhdx_path=None)
        self._log.info("VM - {} got created".format(vm_name))

        vm_install_collateral = InstallCollateral(self._log, vm_os, self.cfg_opts)

        vm_iperf_path = vm_install_collateral.install_iperf_on_windows()

        # Get the adapter name used for VM(Dynamic IP)
        dhcp_adapter_name = vm_os.execute(self._vm_provider_obj.GET_NET_ADAPTER_CMD,
                                          self._command_timeout).stdout.strip()

        #  Add VM Ethernet Adapter in VM.
        self._vm_provider_obj.add_vm_ethernet_adapter(vm_name, VmStressAttribute.VSWITCH_FOR_STATIC)

        self._vm_provider_obj.start_vm(vm_name)

        time.sleep(self.TWO_MIN_IN_SEC)

        adapter_name_list = vm_os.execute(self._vm_provider_obj.GET_NET_ADAPTER_CMD,
                                          self._command_timeout).stdout.strip().split('\n')
        static_adapter_name = self.get_non_dhcp_network_adapter(adapter_name_list, dhcp_adapter_name)

        self.assign_static_ip_to_vm(vm_os, static_adapter_name, self.VM_STATIC_IP,
                                    self.SUBNET_MASK, self.GATEWAY_IP)

        start_time = time.time()
        try:
            #  Run iperf on VM as server
            self.run_iperf_as_server(vm_os, os_type=vm_type, sut_iperf_path=vm_iperf_path,
                                     tool_execution_time_seconds=self.ONE_HRS_IN_SEC, vm_name=vm_name)

            self.run_iperf_as_client(self.os, VMs.RS5, sut_iperf_path=self.iperf_path_on_sut,
                                 ip=self.VM_STATIC_IP, tool_execution_time_seconds=self.ONE_HRS_IN_SEC)

            pcie_err_thread = threading.Thread(target=self.run_pcierrpoll_win,
                                           args=(self.ONE_HRS_IN_SEC, self._pcierrpoll_path,))
            pcie_err_thread.start()

            while time.time() - start_time > self.ONE_HRS_IN_SEC - 300:
                self._log.info("Checking if iperf is running")
                if self._stres_provider_obj.check_app_running(app_name="iperf3",
                                                              stress_test_command=
                                                              VmStressAttribute.WINDOWS_IPERF_TEST_CMD):
                    raise content_exceptions.TestFail("iperf3 is not running on SUT")
                self._log.info("iperf3 is running on SUT")
                time.sleep(self.FIVE_MIN_IN_SEC)

            self._stres_provider_obj.kill_stress_tool(stress_tool_name="PCIERRpoll_debug")
            pcie_err_thread.join()
        except:
            raise content_exceptions.TestFail("Test Failed during stress tool execution")
        finally:
            # Copying Iperf log to Host
            self._log.info("Copying Iperf Log to Host")
            host_iperf_path = os.path.join(self.log_dir, self.IPERF_HOST_FILE_NAME)
            self.os.copy_file_from_sut_to_local(os.path.join(self.iperf_path_on_sut,
                                                             self.IPERF_HOST_FILE_NAME), host_iperf_path)

            # Copying PCIERRPOLL Log to Host
            host_poll_err_log = os.path.join(self.log_dir, self.PCIERRPOLL_HOST_FILE_NAME)
            self.os.copy_file_from_sut_to_local(os.path.join(self._pcierrpoll_path, self.PCIERRPOLL_HOST_FILE_NAME),
                                                host_poll_err_log)

        with open(host_poll_err_log, "r") as pcie_handler:
            out_put = pcie_handler.read()

        if self.ERR_SIGNATURE in out_put:
            raise content_exceptions.TestFail("Error Found in PCIEError Poll Log")

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        1. Destroy Created VM.
        """
        try:
            self.virtualization_obj.vm_provider.destroy_vm(VMs.WINDOWS)
        except Exception as ex:
            raise content_exceptions.TestFail("Unable to Destroy the VM")
        super(StressPcieErrorCheckingRasDuringStress, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StressPcieErrorCheckingRasDuringStress.main()
             else Framework.TEST_RESULT_FAIL)
