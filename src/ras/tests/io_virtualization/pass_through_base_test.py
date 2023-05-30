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
import re
import time

from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.dtaf_content_constants import PassThroughAttribute
from src.lib.install_collateral import InstallCollateral
from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.provider.vm_provider import VMProvider
from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon

from src.virtualization.virtualization_common import VirtualizationCommon

from src.lib import content_exceptions
from src.ras.lib.os_log_verification import OsLogVerifyCommon


class PciPassThroughBaseTest(IoVirtualizationCommon):
    """
    This Class is Used as Common Class For PassThroughBaseTest
    """

    VM_OS = []
    VM_NAME = None
    FUNCTIONALITY_TEST_CYCLE = 1
    LIST_OF_VM_NAMES = []
    VM_TYPE = "RS5"
    NETWORK_ASSIGNMENT_TYPE = "DDA"
    VSWITCH_NAME = "ExternalSwitch"
    ADAPTER_NAME = None
    NUMBER_OF_VMS = 1
    DELAY_IN_SEC = 60

    NETWORK_PASS_THROUGH_CMD = r"powershell.exe $pnpdevs =Get-PnpDevice ^| Where-Object {$_.Present -eq $True} ^| " \
                               r"Where-Object {$_.Class -eq 'Net'}; echo 'Before Disavle pnpdevs\n'; $pnpdevs; " \
                               r"Disable-PnpDevice -InstanceId $pnpdevs[%s].InstanceId -Confirm:$false; $pnpdevs= Get-PnpDevice ^| " \
                               r"Where-Object {$_.Present -eq $True} ^| Where-Object {$_.Class -eq 'Net'}; " \
                               r"echo 'After Disable pnpdevs'; $pnpdevs; $locationpath1 = " \
                               r"($pnpdevs[%s] ^| Get-PnpDeviceProperty DEVPKEY_Device_LocationPaths).data[0]; " \
                               r"echo 'location path\n'; $locationpath1; " \
                               r"Dismount-VMHostAssignableDevice -locationpath $locationpath1 -force; " \
                               r"Get-PnpDevice ^| Where-Object {$_.Friendlyname -like '*dismount*'};" \
                               r"Add-VMAssignableDevice -LocationPath $locationpath1 -VMname %s"
    STORAGE_PASS_THROUGH_CMD = r"powershell.exe $pnpdevs = Get-PnpDevice ^| Where-Object {$_.Present -eq $True} ^| " \
                               r"Where-Object {$_.Friendlyname -like '*NVM*'}; echo 'Before Disavle pnpdevs\n'; " \
                               r"$pnpdevs; " \
                               r"Disable-PnpDevice -InstanceId $pnpdevs[%s].InstanceId -Confirm:$false; " \
                               r"$pnpdevs = Get-PnpDevice ^| Where-Object {$_.Present -eq $True} ^| Where-Object " \
                               r"{$_.Friendlyname -like '*NVM*'}; echo 'After Disable pnpdevs'; " \
                               r"$pnpdevs; $locationpath1 = ($pnpdevs[%s] ^| " \
                               r"Get-PnpDeviceProperty DEVPKEY_Device_LocationPaths).data[0]; " \
                               r"echo 'location path\n'; $locationpath1; " \
                               r"Dismount-VMHostAssignableDevice -locationpath $locationpath1 -force; " \
                               r"Get-PnpDevice ^| Where-Object {$_.Friendlyname -like '*dismount*'};" \
                               r"Add-VMAssignableDevice -LocationPath $locationpath1 -VMname %s"
    CMD_TO_GET_PNP_NETWORK_DEVICE = "powershell.exe Get-PnpDevice ^| Where-Object {$_.Present -eq $True} ^| " \
                                    "Where-Object {$_.Class -eq 'Net'}"

    CMD_TO_GET_PNP_NVM_DEVICE = "powershell.exe Get-PnpDevice ^| Where-Object {$_.Present -eq $True} ^| " \
                                "Where-Object {$_.FriendlyName -like '*NVM*'}"

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts,
            bios_config_file=None
    ):
        """
        Create an instance of PassThroughBaseTest

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(
            PciPassThroughBaseTest,
            self).__init__(
            test_log,
            arguments,
            cfg_opts, bios_config_file=bios_config_file)
        self.cfg_opts = cfg_opts
        self.virtualization_obj = VirtualizationCommon(self._log, arguments, cfg_opts)
        self._vm_provider_obj = VMProvider.factory(test_log, cfg_opts, self.os)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._os_log_obj = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.num_vms = self._common_content_configuration.get_num_vms_to_create()

    def prepare(self):  # type: () -> None
        super(PciPassThroughBaseTest, self).prepare()

    def get_index_for_pnp_device(self, device_name, card_type=PassThroughAttribute.Network.value):
        """
        This method is to get the index of required device from Pnpdevice Command.

        :param device_name Device Name which needs to pass through VM.
        :param card_type Card type- ex for storage- "NVMe, for Network- "Net
        :return index of Required Network Card from PNP device.
        """
        #  Get the Command which needs to execute for PNP device index.

        pnp_cmd = {
            PassThroughAttribute.Network.value: self.CMD_TO_GET_PNP_NETWORK_DEVICE,
            PassThroughAttribute.NVMe.value: self.CMD_TO_GET_PNP_NVM_DEVICE
        }

        pnpdev_output = self._common_content_lib.execute_sut_cmd(sut_cmd=pnp_cmd[card_type],
                                                                 cmd_str=pnp_cmd[card_type],
                                                                 execute_timeout=20).strip().split('\n')

        self._log.info("Pnp device output- {}".format(pnpdev_output))

        index = -1
        #  Logic to get the device_name index
        for each_line in pnpdev_output:
            if "------" in each_line:
                continue
            elif device_name in each_line:
                return index
            else:
                index = index + 1

        if index == -1:
            raise content_exceptions.TestFail("{} Card is not detected in PnpDevice command".format(card_type))

    def pass_through_pci_device(self, vm_name, type):
        """
        This method is to Pass Storage Card to VM.

        :param vm_name
        :param type
        """
        #  check if type need to pass, if not return from method.
        if type not in self._common_content_configuration.get_pass_through_device_type():
            return

        pass_through_cmd_dict = {
            PassThroughAttribute.Network.value: self.NETWORK_PASS_THROUGH_CMD,
            PassThroughAttribute.NVMe.value: self.STORAGE_PASS_THROUGH_CMD
        }

        devices_list = self._common_content_configuration.get_pass_through_device_name_list(type)
        for each_device in devices_list:
            self._log.info(each_device)
            index = self.get_index_for_pnp_device(each_device, type)

            pass_thruogh_cmd = pass_through_cmd_dict[type] % (index, index, vm_name)
            pass_through_output = self._common_content_lib.execute_sut_cmd(sut_cmd=pass_thruogh_cmd,
                                                                           cmd_str=pass_thruogh_cmd,
                                                                           execute_timeout=self._command_timeout)

            self._log.info("Storage Pass through execution output- {}".format(pass_through_output))

    def device_pass_through_to_windows_vm(self, vm_name):
        """
        This method has functionality.

        1. TurnOFF VM.
        2. Set Automatic Stop Action before pass through.
        3. Passthrough Network card
        4. Passthrough NVMe Card
        5. Start VM

        :param vm_name
        """
        self._vm_provider_obj.turn_off_vm(vm_name=vm_name)
        self._vm_provider_obj.set_automatic_stop_action(vm_name, "TurnOff")
        self.pass_through_pci_device(vm_name, PassThroughAttribute.Network.value)
        self.pass_through_pci_device(vm_name, PassThroughAttribute.NVMe.value)
        self._vm_provider_obj.start_vm(vm_name)
        return True

    def install_pcie_driver_in_vm(self, vm_os_obj, type):
        """
        This Method is to verify the Network Pass through from Vm side.

        :param vm_os_obj
        :param type
        """
        if PassThroughAttribute.NVMe.value == type or \
                (type not in self._common_content_configuration.get_pass_through_device_type()):
            return

        #  Get the driver name list which needs to be installed.
        driver_list = self._common_content_configuration.get_driver_inf_file_name_in_list()

        #  Get the device id of Network to install the driver.
        device_id_list = self._common_content_configuration.get_device_id_name_in_list(type=type)

        #  Create Install collateral object.
        install_collateral_for_vm = InstallCollateral(self._log, vm_os_obj, self.cfg_opts)

        #  Install Driver on Windows VM
        install_collateral_for_vm.install_driver_on_windows(inf_file_list=driver_list, device_id_list=device_id_list)

    def verify_pcie_pass_through_from_vm_side(self, vm_os_obj, vm_name, type):
        """
        This method is to Verify PCIe Pass through from VM Side.

        :param vm_os_obj
        :param vm_name
        :param type
        """
        #  Run command on VM to check the Card in VM
        if type not in self._common_content_configuration.get_pass_through_device_type():
            return

        pcie_details_cmd_dict = {
            PassThroughAttribute.Network.value: self.CMD_TO_GET_PNP_NETWORK_DEVICE,
            PassThroughAttribute.NVMe.value: self.CMD_TO_GET_PNP_NVM_DEVICE
        }

        cmd_to_get_pcie_details = pcie_details_cmd_dict[type]

        device_list = self._common_content_configuration.get_pass_through_device_name_list(type=type)

        vm_common_content_lib_obj = CommonContentLib(self._log, vm_os_obj, self.cfg_opts)
        pnp_output_in_vm = vm_common_content_lib_obj.execute_sut_cmd(sut_cmd=cmd_to_get_pcie_details,
                                                                     cmd_str=cmd_to_get_pcie_details,
                                                                     execute_timeout=self._command_timeout)

        for each_device in device_list:
            REGEX_TO_CHECK_STATUS_IN_VM = "OK.*{}".format(each_device[:-2])
            REGEX_TO_CHECK_STATUS_IN_VM = REGEX_TO_CHECK_STATUS_IN_VM.replace("(R)", "\(R\)")
            self._log.info("regex: {}".format(REGEX_TO_CHECK_STATUS_IN_VM))
            if not re.findall(REGEX_TO_CHECK_STATUS_IN_VM, pnp_output_in_vm):
                raise content_exceptions.TestFail("TestFailed: Unable to detect the Storage card-{} in VM- {}".format(
                    each_device, vm_name
                ))
            self._log.info("{} Card-{} got detected in VM- {}".format(type, each_device, vm_name))
        self._log.info("All {} Card got detected in VM- {}".format(type, vm_name))

    def install_driver_and_verify_passthrough_from_vm_side(self, vm_name, vm_type):
        """
        This method is to install driver and verify passthrough from VM side.

        :param vm_name
        :param vm_type
        return True if pass
        """
        try:
            #  Create VM os object.
            vm_os_obj = self.virtualization_obj.windows_vm_object(vm_name=vm_name, vm_type=vm_type)

            self.install_pcie_driver_in_vm(vm_os_obj, PassThroughAttribute.Network.value)

            #  Verify Network Pass through from VM side.
            self.verify_pcie_pass_through_from_vm_side(vm_os_obj, vm_name, PassThroughAttribute.Network.value)

            #  Verify Storage Pass through from VM side.
            self.verify_pcie_pass_through_from_vm_side(vm_os_obj, vm_name, PassThroughAttribute.NVMe.value)

        except Exception as ex:
            raise content_exceptions.TestFail("Failed during Pass through Verification from VM side- {}".format(ex))

    def degrade_nvme_gen_speed(self, csp, sdp, socket=0, port="pxp4.flexbus.port0", gen=4):
        """
        This method is to degrade the Gen Speed

        :param csp - cscript object
        :param sdp - silicon debug provider
        :param socket - socket
        :param port - port
        :param gen - generation
        """
        tls_reg = {ProductFamilies.SPR: "pi5.{}.cfg.linkctl2.tls".format(port)}
        csp.get_by_path(csp.UNCORE, reg_path=tls_reg[self._common_content_lib.get_platform_family()],
                        socket_index=socket).write(gen)

        rl_reg = {ProductFamilies.SPR: "pi5.{}.cfg.linkctl.rl".format(port)}
        csp.get_by_path(csp.UNCORE, reg_path=rl_reg[self._common_content_lib.get_platform_family()],
                        socket_index=socket).write(1)

        pcie_obj = csp.get_cscripts_utils().get_pcie_obj()
        sdp.start_log("pcie_sls.log")
        pcie_obj.sls()
        sdp.stop_log()

        fp = open("pcie_sls.log", "r")
        self._log.info("Pcie sls out put- {}".format(fp.readlines()))

    def install_disk_spd_tool_on_vm(self, vm_os_obj):
        """
        This method is to install disk sdp tool on VM.

        :param vm_os_obj
        :return path
        """
        install_collateral_vm = InstallCollateral(self._log, vm_os_obj, self.cfg_opts)
        sut_path = install_collateral_vm.download_and_copy_zip_to_sut("disk_spd_auto", "disk_spd_auto.zip") +\
                   r"\disk_spd_auto"

        return sut_path

    def get_read_write_speed(self, vm_os_obj, cmd_path):
        """
        This method is to get read- write gen speed.

        :param vm_os_obj - os object for VM
        :param cmd_path - tool directory path
        :return read_speed, write_speed
        """
        out_put = vm_os_obj.execute(r"powershell.exe .\BenchmarkDrive -drive ('e:\')", self._command_timeout, cmd_path)
        self._log.info(out_put.stdout)

        read_regex = r"Sequential Read 1MB.*:\s(\S+)"
        write_regex = r"Sequential Write 1MB.*:\s(\S+)"
        import re
        read_speed = re.findall(read_regex, out_put.stdout)
        write_speed = re.findall(write_regex, out_put.stdout)
        if not (len(read_speed) or len(write_speed)):
            raise content_exceptions.TestFail("Failed:- Please check disk spd tool execution output")

        return float(read_speed[0]), float(write_speed[0])

    def execute(self):  # type: () -> bool
        """
        This method is to
        1. Create VM
        2. Verify VM
        3. Pass Network card to VM
        4. Verify Passthrough from VM side

        :return True if Test pass
        """
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
            self._vm_provider_obj.add_vm_network_adapter(self.NETWORK_ASSIGNMENT_TYPE, vm_name, self.ADAPTER_NAME,
                                                         self.VSWITCH_NAME, vm_type="RS5", mac_addr=mac_id_flag)

            #  Verify Hyper-V VM
            self.virtualization_obj.verify_hyperv_vm(vm_name, vm_type="RS5")

            #  Start VM
            self._vm_provider_obj.start_vm(vm_name)

            #  Create SSH to VM
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

        for index in range(0, self.NUMBER_OF_VMS):
            vm_name = self.VM_OS[0] + "_" + str(index)
            self.device_pass_through_to_windows_vm(vm_name)
            time.sleep(self.DELAY_IN_SEC)

        for index in range(0, self.NUMBER_OF_VMS):
            vm_name = self.VM_OS[0] + "_" + str(index)
            self.install_driver_and_verify_passthrough_from_vm_side(vm_name, vm_type=self.VM_TYPE)

        return True

    def restore_device_to_host(self, vm_name):
        """
        This method is to remove the device from VM and assigned back to Host.

        :param vm_name
        """
        #  Command to remove the Device from VM.
        remove_device_from_vm_cmd = "powershell.exe Remove-VMAssignableDevice -VMName {} -Verbose".format(vm_name)

        #  Command to Mount the device.
        mount_device = "powershell.exe Get-VMHostAssignableDevice ^| Mount-VmHostAssignableDevice -Verbose"
        command_execution_list = [remove_device_from_vm_cmd, mount_device]

        #  Executing each Command to remove and Mount the device.
        for each_command in command_execution_list:
            remove_device_output = self._common_content_lib.execute_sut_cmd(sut_cmd=each_command,
                                                                            cmd_str=each_command,
                                                                            execute_timeout=self._command_timeout)
            self._log.info("Command {} output is- {}".format(each_command, remove_device_output))

        device_id_list = []
        if PassThroughAttribute.Network.value in self._common_content_configuration.get_pass_through_device_type():
            device_id_list = self._common_content_configuration.get_device_id_name_in_list(
                type=PassThroughAttribute.Network.value)

        if PassThroughAttribute.NVMe.value in self._common_content_configuration.get_pass_through_device_type():
            device_id_list.extend(self._common_content_configuration.get_device_id_name_in_list(
                type=PassThroughAttribute.NVMe.value))

        #  Execute the command Enable the device for Host.
        for each_device_id in device_id_list:
            #  Command to get the HwID's
            cmd_to_get_hw_ids = "powershell.exe Get-CimInstance -ClassName Win32_PNPEntity ^| " \
                                "Select-Object -Property DeviceID ^| findstr '{}'".format(each_device_id)
            hw_ids = self._common_content_lib.execute_sut_cmd(sut_cmd=cmd_to_get_hw_ids, cmd_str=cmd_to_get_hw_ids,
                                                              execute_timeout=self._command_timeout).strip()
            regex_to_find_hw_id = "VEN.*{}".format(each_device_id)
            hw_id_list = re.findall(regex_to_find_hw_id, hw_ids)
            self._log.info(hw_id_list)

            #  Command to Enable the Device for Host.
            enable_device = """powershell.exe "(Get-PnpDevice -PresentOnly).Where{ $_.InstanceId -match '%s' } " \
                            "| Enable-PnpDevice -Confirm:$false -Verbose" """ % (hw_id_list[0])

            #  Execute the command to enable the Device for Host.
            enable_device_output = self._common_content_lib.execute_sut_cmd(sut_cmd=enable_device,
                                                                            cmd_str=enable_device,
                                                                            execute_timeout=self._command_timeout)
            self._log.info(enable_device_output)

    def cleanup(self, return_status):
        try:
            for index in range(self.NUMBER_OF_VMS):
                vm_name = self.VM_OS[0] + "_" + str(index)
                try:
                    self.restore_device_to_host(vm_name)
                except Exception as ex:
                    raise content_exceptions.TestError("Unable to restore the devices")
                finally:
                    self._vm_provider_obj.destroy_vm(vm_name)
        except Exception as ex:
            raise RuntimeError("Unable to Destroy the VM")
        super(PciPassThroughBaseTest, self).cleanup(return_status)
