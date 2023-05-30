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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.os_lib import WindowsCommonLib

from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import VmStressAttribute

from src.provider.stressapp_provider import StressAppTestProvider
from src.hsio.upi.hsio_upi_common import HsioUpiCommon
from src.provider.vm_provider import VMs
from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon
from src.lib import content_exceptions


class VmStressOsWithLargeCapacityVms(IoVirtualizationCommon):
    """
    Test Virtualization OS with several large capacity VMs. The goal of this test case is to get the SUT to
    simutaniously run a few virtual machines that are configured with very large VM configuration.
    Ideally with many virtual CPUs, Memory, Network, and Disk capacity.
    """

    VM_SUB_TYPE = [VMs.RS5, VMs.RS5, VMs.RHEL]
    IPERF_SUT_LOG = "iperf_client_sut.txt"
    IPERF_VM_LOG = "iperf_client_Linux.txt"
    IPERF_LINUX_VM_PATH = "/root/iperf_client_Linux.txt"
    VM_OS = [VmStressAttribute.WINDOWS_16, VmStressAttribute.WINDOWS_19, VmStressAttribute.LINUX]
    TEMPLATE_DICT = {VmStressAttribute.WINDOWS_19: False, VmStressAttribute.WINDOWS_16: True,
                     VmStressAttribute.LINUX: False}
    VM_OS_TYPE_DICT = {VmStressAttribute.WINDOWS_19: OperatingSystems.WINDOWS,
                       VmStressAttribute.WINDOWS_16: OperatingSystems.WINDOWS,
                       VmStressAttribute.LINUX: OperatingSystems.LINUX
                       }
    WAIT_TIME_IN_SEC = 100
    POLLING_TIME_IN_SEC = 300

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts
    ):
        """
        Create an instance of VmmPfaTestAndVmsUnderLoadLinux
        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(
            VmStressOsWithLargeCapacityVms,
            self).__init__(
            test_log,
            arguments,
            cfg_opts)
        self._args = arguments
        self.num_vms = 3
        self._windows_common_lib = WindowsCommonLib(self._log, self.os)
        self.install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.install_collateral.install_burnin_tool_on_windows()
        self.iperf_path_on_sut = self.install_collateral.install_iperf_on_windows()
        vm_adapter = self._common_content_configuration.get_ethernet_adapter_for_vm()
        self.vm_physical_adapter = self._windows_common_lib.get_network_adapter_name(vm_adapter)
        loop_back_adapter = self._common_content_configuration.get_loop_back_adapter()
        self.loop_back_physical_adpater = self._windows_common_lib.get_network_adapter_name(loop_back_adapter)
        self.SUT_STATIC_IP = self._common_content_configuration.get_sut_static_ip()
        self.VM_STATIC_IP = self._common_content_configuration.get_vm_static_ip()
        self.SUBNET_MASK = self._common_content_configuration.get_subnet_mask()
        self.GATEWAY_IP = self._common_content_configuration.get_gateway_ip()
        self._vm_stress_tool_execution_time = self._common_content_configuration.get_stress_execution_time_for_vm()
        self.static_ip = {VmStressAttribute.WINDOWS_19: self._common_content_configuration.get_vm_2019_static_ip(),
                          VmStressAttribute.WINDOWS_16: self._common_content_configuration.get_vm_2016_static_ip(),
                          VmStressAttribute.LINUX: self._common_content_configuration.get_vm_static_ip()}

    def execute(self):  # type: () -> bool
        """
        This method is to
        1. Create VM (Linux, Windows 2019, Windows 2016).
        2. Install Iperf and Burnin on VM.
        3. Run iperf and Burnin stress on VM.
        """
        vm_os_obj = []
        vm_details_dict = {}

        # Assign static ip on SUT network adapter
        self._log.info(
            "Set static ip {} to adapter {} on SUT".format(self.SUT_STATIC_IP, self.loop_back_physical_adpater))
        self._windows_common_lib.configure_static_ip(self.loop_back_physical_adpater, self.SUT_STATIC_IP,
                                                     self.SUBNET_MASK, self.GATEWAY_IP)

        # Create Virtual Switch for Static IP
        self._vm_provider_obj.create_bridge_network(switch_name=VmStressAttribute.VSWITCH_FOR_STATIC,
                                                    adapter_name=self.vm_physical_adapter)

        for index in range(self.num_vms):
            vm_dict = {}

            #  Create VM names dynamically according to the OS
            vm_name = self.VM_OS[index]
            vm_type = self.VM_SUB_TYPE[index]

            self._log.info("Creating VM - {}".format(vm_name))
            vm_os = self.create_vm_on_windows_sut(vm_name=vm_name, vm_type=vm_type,
                                                  template=self.TEMPLATE_DICT[vm_name], vm_os_type=
                                                  self.VM_OS_TYPE_DICT[vm_name])
            self._log.info("VM - {} got created".format(vm_name))

            vm_install_collateral = InstallCollateral(self._log, vm_os, self.cfg_opts)
            vm_os_obj.append(vm_os)

            SILENT_CONTINUE = "$progressPreference = 'silentlyContinue'"
            GET_NET_ADAPTER_CMD_STATUS = 'powershell.exe {}; ("Get-NetAdapter -Name * -Physical | ? Status -eq ' \
                                         'Up).Name'.format(SILENT_CONTINUE)

            # Get the adapter name used for VM(Dynamic IP)
            dhcp_adapter_name = vm_os.execute(GET_NET_ADAPTER_CMD_STATUS,
                                              self._command_timeout).stdout.strip()

            #  Add VM Ethernet Adapter in VM.
            self._vm_provider_obj.add_vm_ethernet_adapter(vm_name, VmStressAttribute.VSWITCH_FOR_STATIC)

            self._vm_provider_obj.start_vm(vm_name)

            time.sleep(self.WAIT_TIME_IN_SEC)

            if vm_type != VMs.RHEL:
                adapter_name_list = vm_os.execute(GET_NET_ADAPTER_CMD_STATUS,
                                                  self._command_timeout).stdout.strip().split('\n')
                static_adapter_name = None
                for each_name in adapter_name_list:
                    if each_name != dhcp_adapter_name:
                        static_adapter_name = each_name
                        break
                if static_adapter_name is None:
                    raise content_exceptions.TestFail("Adapter is not found in VM for Assigning static IP")
            else:
                static_adapter_name = VmStressAttribute.LINUX_ETHERNET_INTERFACE_NAME

            self.assign_static_ip_to_vm(vm_os, static_adapter_name, self.static_ip[vm_name],
                                        self.SUBNET_MASK, self.GATEWAY_IP)

            if vm_type == VMs.RHEL:
                vm_install_collateral.screen_package_installation()

            vm_dict[VmStressAttribute.IP] = vm_os._ip
            vm_dict[VmStressAttribute.IPERF_SUT_PATH] = vm_install_collateral.install_iperf_on_vm()
            vm_dict[VmStressAttribute.VM_OS_OBJ] = vm_os

            vm_details_dict[vm_name] = vm_dict
        server_ip = []

        end_time = time.time() + self._vm_stress_tool_execution_time

        for index in range(self.num_vms):
            vm_name = self.VM_OS[index]
            vm_type = self.VM_SUB_TYPE[index]
            vm_dict = vm_details_dict[vm_name]
            vm_os = vm_dict[VmStressAttribute.VM_OS_OBJ]
            vm_iperf_path = vm_dict[VmStressAttribute.IPERF_SUT_PATH]

            if index == 0 or index == 1:
                #  As index=0- Windows_19, 1-Windows_16 used as Server in iperf test.

                #  Appending the VM ip.
                server_ip.append(vm_os._ip)

                #  Run iperf on VM as server
                self.run_iperf_as_server(vm_os, os_type=vm_type, sut_iperf_path=vm_iperf_path,
                                         tool_execution_time_seconds=self._vm_stress_tool_execution_time, vm_name=vm_name)
            else:
                #  Run iperf between Windows_19(Server) and Linux VM(Client)

                self._log.info("Running iperf stress between Windows_19(Server) and Linux VM(Client)")
                self.run_iperf_as_client(vm_os, vm_type, sut_iperf_path=vm_iperf_path, ip=self.static_ip[
                    VmStressAttribute.WINDOWS_19], vm_name=vm_name, tool_execution_time_seconds=
                self._vm_stress_tool_execution_time)

                #  running iperf between Windows_16(Server) and SUT (Client)

                self._log.info("Running iperf stress between Windows_16(Server) and SUT (Client)")
                self.run_iperf_as_client(self.os, VMs.RS5, sut_iperf_path=self.iperf_path_on_sut,
                                         ip=self.static_ip[VmStressAttribute.WINDOWS_16],
                                         tool_execution_time_seconds=self._vm_stress_tool_execution_time)

            tool_path = self.install_burnin_tool_on_vm(vm_os, vm_type)
            #  Run Burnin tool on VM
            self._log.info("Running Burnin tools VM- {}".format(vm_name))
            self.start_burnin_stress_on_vm(vm_os_obj=vm_os, vm_os_type=vm_type,
                                           duration_time=self._vm_stress_tool_execution_time,
                                           sut_tool_path=tool_path)
        try:
            self._log.info("Checking tools is Alive or not.....")
            while time.time() < end_time:
                self._log.info("checking if iperf3 client is not running on SUT")
                time.sleep(self.POLLING_TIME_IN_SEC)
                sut_stress_app = StressAppTestProvider.factory(self._log, self.cfg_opts, self.os)
                if sut_stress_app.check_app_running(app_name="iperf3", stress_test_command=VmStressAttribute.WINDOWS_IPERF_TEST_CMD):

                    raise content_exceptions.TestFail("iperf3 (Client) is not running on SUT")
                self._log.info("Iperf3 (Client) is running on SUT as expected")

                for index in range(self.num_vms):
                    vm_name = self.VM_OS[index]
                    vm_type = self.VM_SUB_TYPE[index]
                    vm_dict = vm_details_dict[vm_name]
                    vm_os = vm_dict[VmStressAttribute.VM_OS_OBJ]
                    vm_iperf_path = vm_dict[VmStressAttribute.IPERF_SUT_PATH]
                    stress_app = StressAppTestProvider.factory(self._log, self.cfg_opts, vm_os)

                    if vm_type == VMs.RHEL:
                        if not stress_app.check_app_running(app_name="iperf3", stress_test_command="iperf3 -c"):
                            raise content_exceptions.TestFail("iperf3 (Client) is not running on Linux VM")

                        self._log.info("Iperf3 is running on -{} VM as expected".format(vm_name))

                        if not stress_app.check_app_running(app_name="bit_cmd_line_x64",
                                                            stress_test_command="./bit_cmd_line_x64"):
                            raise content_exceptions.TestFail("Burnin test is not running on Linux VM")
                        self._log.info("Burnin test is running on -{} VM as expected".format(vm_name))
        except:
            raise content_exceptions.TestFail("Failed during tool polling")
        finally:
            sut_iperf_path = os.path.join(self.log_dir, self.IPERF_SUT_LOG)

            self.os.copy_file_from_sut_to_local(os.path.join(self.iperf_path_on_sut, self.IPERF_SUT_LOG), sut_iperf_path)
            vm_iperf_path = os.path.join(self.log_dir, self.IPERF_VM_LOG)
            for index in range(self.num_vms):
                vm_name = self.VM_OS[index]
                vm_type = self.VM_SUB_TYPE[index]
                vm_dict = vm_details_dict[vm_name]
                vm_os = vm_dict[VmStressAttribute.VM_OS_OBJ]
                if vm_type.upper() == VMs.RHEL:
                    vm_os.copy_file_from_sut_to_local(self.IPERF_LINUX_VM_PATH, vm_iperf_path)

        return True

    def cleanup(self, return_status):
        for index in range(self.num_vms):
            vm_name = self.VM_OS[index]
            try:
                self._vm_provider_obj.destroy_vm(vm_name)
            except:
                self._log.error("Unable to Delete the VM - {}".format(vm_name))
        super(VmStressOsWithLargeCapacityVms, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VmStressOsWithLargeCapacityVms.main()
             else Framework.TEST_RESULT_FAIL)
