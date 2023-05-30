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

import re
import os
import time
import threading
import subprocess
from importlib import import_module
from abc import ABCMeta, abstractmethod
from six import add_metaclass
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import OperatingSystems, Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.lib.os_lib import LinuxDistributions
from dtaf_core.providers.internal.ssh_sut_os_provider import SshSutOsProvider
from src.lib.content_artifactory_utils import ContentArtifactoryUtils

from src.provider.base_provider import BaseProvider
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions

VM_CONFIGURATION_FILE = """<?xml version="1.0" encoding="UTF-8"?>
<sut_os name="{}" subtype="{}" version="{}" kernel="{}">
    <shutdown_delay>5.0</shutdown_delay>
    <driver>
        <ssh>
            <credentials user="{}" password="{}"/>
            <ipv4>{}</ipv4>
        </ssh>
    </driver>
</sut_os>
"""


class VMs(object):
    RHEL = "RHEL"
    FEDORA = "Fedora"
    WINDOWS = "WINDOWS"
    LINUX = "LINUX"
    CENTOS = "CENTOS"
    RS5 = "RS5"

@add_metaclass(ABCMeta)
class VMProvider(BaseProvider):
    """
    Create a new VMProvider object.

    :param log: Logger object to use for output messages
    :param os_obj: OS object
    """

    def __init__(self, log, cfg_opts, os_obj):
        super(VMProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self.os = os_obj
        self._sut_os = self.os.os_type

        #  common_content_obj and config object
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._linux_raw_image_host_location = self._common_content_configuration.get_rhel_img_image_host_location()
        self._centos_raw_image_host_location = self._common_content_configuration.get_centos_img_image_host_location()
        self._linux_image_host_location = self._common_content_configuration.get_rhel_iso_image_host_location()
        self._centos_image_host_location = self._common_content_configuration.get_centos_iso_image_host_location()
        self._windows_image_host_location = self._common_content_configuration.get_windows_iso_image_host_location()
        self._linux_vm_template_host_location = self._common_content_configuration.get_rhel_vm_template_host_location()
        self._windows_vm_template_host_location = self._common_content_configuration.get_windows_vm_template_host_location()
        self.accel_file_path = self._common_content_configuration.get_idx_file()
        self._stress_provider_obj = StressAppTestProvider.factory(self._log, cfg_opts, self.os)
        sut_ssh_cfg = cfg_opts.find(SshSutOsProvider.DEFAULT_CONFIG_PATH)
        self.sut_ssh = ProviderFactory.create(sut_ssh_cfg, log)  # type: SutOsProvider
        self.sut_user = self.sut_ssh._config_model.driver_cfg.user
        self.sut_pass = self.sut_ssh._config_model.driver_cfg.password
        self.sut_ip = self.sut_ssh._config_model.driver_cfg.ip
        self.sut_ostype = self._common_content_lib.sut_os
        self._artifactory_obj = ContentArtifactoryUtils(self._log, self.os, self._common_content_lib, cfg_opts)

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        """
        package = r"src.provider.vm_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "WindowsVmProvider"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "LinuxVmProvider"
        elif OperatingSystems.ESXI == os_obj.os_type:
            mod_name = "ESXiVmProvider"
        else:
            raise NotImplementedError("Test is not implemented for %s" % os_obj.os_type)
        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(log=log, cfg_opts=cfg_opts, os_obj=os_obj)

    @abstractmethod
    def create_vm(self, vm_name, os_variant, no_of_cpu=None, disk_size=None, memory_size=None,
                  vm_creation_timeout=None, vm_create_async=None, mac_addr=None, pool_id=None, pool_vol_id=None,
                  cpu_core_list=None, nw_bridge=None, vm_os_subtype=None, nesting_level=None, vhdx_dir_path=None,
                  devlist=[], qemu=None):
        """
        Execute the the command to create a VM from scratch using iso image.

        :param vm_name: Name of the new VM
        :param vm_create_async: if VM is has to be created in async mode such as required for nested VM
        :param no_of_cpu: No of CPUs in VM
        :param disk_size: Size of the VM disk drive
        :param memory_size: Size of the VM memory
        :param os_variant: linux Os version
        :param vm_creation_timeout: timeout for vm creation
        :param mac_addr: Assign MacAddress to Network.
        :param pool_id: Storage pool id from storage
        :param vhdx_dir_path: path to create .vhdx
        :param vm_os_subtype: VM os sub type - RHEL, CENTOS, RS5.
        :param pool_vol_id: Storage pool Volume id from storage volume created in the given pool
        :param cpu_core_list: CPU core list to be assigned to VM with --cpuset
        :param nw_bridge : Some Non-None value is bridge type default n/w required in VM
        :param nesting_level: nesting_level in case of nested VM
        :return vm_name: Name of the new VM

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def create_vm_from_template(self, vm_name, memory_size, vm_creation_timeout, gen):
        """
        Execute the the command to create a VM from an existing template base image in vhdx format.

        :param vm_name: Name of the new VM
        :param memory_size: Size of the VM memory
        :param vm_creation_timeout: timeout for vm creation in ms.
        :param gen: VM generation

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def create_bridge_network(self):
        """
        Method to create the network bridge on SUT.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def start_vm(self, vm_name):
        """
        Method to start VM.

        :param vm_name: Name of the VM to start
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def destroy_vm(self, vm_name):
        """
        Method to destroy the VM & it's resources

        :param vm_name: Name of the VM to destroy
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_vm_ip(self, vm_name):
        """
        Method to get the IPV4 address of the given VM

        :param vm_name: Name of the VM to get the IP
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def remove_bridge_network(self):
        """
        Method to remove the existed network bridge on SUT.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def create_vm_host(self, os_subtype, os_version, kernel_vr, vm_username, vm_password, vm_ip):
        """
        Method to create os executable object for given VM.

        :param vm_ip: ip of the VM OS
        :param vm_username: username of the VM OS
        :param os_version: os version
        :param os_subtype: os subtype
        :param kernel_vr: kernel version
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def ping_vm_from_sut(self, vm_ip, vm_name=None, vm_account=None, vm_password=None):
        """
        This method is to ping the VM from SUT system

        :param vm_name: name of given VM
        :param vm_ip: IP of the VM
        :param vm_account: user account for the VM
        :param vm_password: password for the VM account
        :return: None
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_vm_info(self, vm_name):
        """
        This method is to get the dominfo about the given VM

        :param vm_name: name of the VM
        :return: None
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def copy_file_from_sut_to_vm(self, vm_name, vm_username, source_path, destination_path):
        """
        This method is to copy file from SUT to VM

        """
        raise NotImplementedError

    @abstractmethod
    def add_storage_device_to_vm(self, vm_name, vm_disk_name, storage_size):
        """
        This method is add additional storage device to VM

        :param vm_name: name of the VM
        :param vm_disk_name: disk name going to attach to the VM
        :param storage_size: size of the storage device to add in GB
        :return: None
        """
        raise NotImplementedError

    @abstractmethod
    def remove_storage_device_from_vm(self, vm_name):
        """
        This method is add additional storage device to VM

        :param vm_name: name of the VM
        :return: None
        """
        raise NotImplementedError

    @abstractmethod
    def suspend_vm(self, vm_name):
        """
        This method is to suspend the existing VM

        :param vm_name: Name of the VM
        """
        raise NotImplementedError

    @abstractmethod
    def resume_vm(self, vm_name):
        """
        This method is to resume the suspended VM

        :param vm_name: Name of the VM
        """
        raise NotImplementedError

    @abstractmethod
    def save_vm_configuration(self, vm_name):
        """
        This method will save the VM configuration into a XML file

        :param vm_name: Name of the VM
        :return: complete_vm_config_file
        """
        raise NotImplementedError

    @abstractmethod
    def restore_vm_configuration(self, vm_name, vm_config_file):
        """
        This method will restore the VM from configuration file

        :param vm_name: Name of the VM
        :param vm_config_file: Previously saved VM configuration file with path
        """
        raise NotImplementedError

    @abstractmethod
    def attach_usb_device_to_vm(self, usb_data_dict, vm_name):
        """
        This method is to attach the usb device to the vm

        :param usb_data_dict: dictionary data should contain vendor id and product id
        :param vm_name: name of the VM
        :return :None
        """
        raise NotImplementedError

    @abstractmethod
    def detach_usb_device_from_vm(self, vm_name):
        """
        This method is to detach the usb device from VM.

        :param vm_name: name of the VM
        :return: None
        """
        raise NotImplementedError

    @abstractmethod
    def install_vm_tool(self):
        """
        This method is to install all the dependency tools for VM creation

        :return :None
        """
        raise NotImplementedError

    @abstractmethod
    def install_kvm_vm_tool(self):
        """
        This method is to install all the dependency tools for VM creation

        :return :None
        """
        raise NotImplementedError

    @abstractmethod
    def add_vm_network_adapter(self, methods, vm_name, physical_adapter_name, switch_name, vm_type=None, mac_addr=None):
        """
        Method to add network adapter for given VM.

        :param methods: The methods to add network adapter to VM. The value is expected to be "DDA" or "SRIOV".
        :param vm_name: Name of the VM.
        :param physical_adapter_name: Name of the physical network adapter on SUT.
                             Note: the adapter is expected to be extra test NIC instead of builtin NIC.
        :param switch_name: Name of the switch you create
        :param vm_type: VM type for eg:- "RS5"
        :param mac_addr: Assign Mac Addr to Network Adapter.
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def import_vm(self, source_path=None, destination_path=None):
        """Method to import VM.
        :param source_path: path on the SUT to the VM template image.
        :type: str
        :param destination_path: path on the SUT to where the new VM image will be.
        :type: str
        """
        raise NotImplementedError

    @abstractmethod
    def rename_vm(self, current_vm_name=None, new_vm_name=None):
        """Method to rename VM.
        :param current_vm_name: Current VM name.
        :type: str
        :param new_vm_name: New VM name.
        :type: str"""
        raise NotImplementedError

    @abstractmethod
    def apply_checkpoint(self, vm_name=None, checkpoint_name=None):
        """Method to apply a stored checkpoint for a named VM.
        :param vm_name: Name of the VM to which the checkpoint will be applied.
        :type: str
        :param checkpoint_name: name of the checkpoint to apply to the VM.
        :type: str"""
        raise NotImplementedError

    @abstractmethod
    def delete_checkpoint(self, vm_name=None, checkpoint_name=None):
        """Method to delete a stored checkpoint for a named VM.
        :param vm_name: Name of the VM to which the checkpoint will be deleted.
        :type: str
        :param checkpoint_name: name of the checkpoint to apply to the VM.
        :type: str"""
        raise NotImplementedError

    @abstractmethod
    def get_network_bridge_list(self):
        """Retrieves list of VM switches registered into Hyper-V.
        :return: List of VM switches
        :rtype: str"""
        raise NotImplementedError

    @abstractmethod
    def set_boot_order(self, vm_name=None, boot_device_type=None):
        """Set boot order of a VM.
        :param vm_name: Name of the VM to change the boot order.
        :type: str
        :param boot_device_type: Type of device to use as boot device.  Expected values are: VMBootSource,
        VMNetworkAdapter,HardDiskDrive,DVDDrive.
        :type: str"""
        raise NotImplementedError

    @abstractmethod
    def set_automatic_stop_action(self, vm_name, stop_action_type="TurnOff"):
        """
        This method is to set the Automatic stop Action.

        :param vm_name
        :param stop_action_type - TurnOff, Save, and ShutDown
        """
        raise NotImplementedError

    @abstractmethod
    def turn_off_vm(self, vm_name):
        """
        This method is to Turn OFF VM.

        :param vm_name
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def copy_package_to_VM(self, vm_name, vm_account, vm_password, package_name, destination_path):
        """
        This method is to copy file from SUT to VM
        :param vm_name : name of the VM. ex: WINDOWS_1
        :param vm_account : VM admin account "Administrator"
        :param vm_password : VM password
        :param destination_path: Destination path in VM
        :param package_name : Name of the package to be copied to VM
        :return : pakage path on VM

        :raise: RuntimeError
        """
        raise NotImplementedError


class WindowsVmProvider(VMProvider):
    """
    Class to provide VM methods for Windows platform

    """
    SILENT_CONTINUE = "$progressPreference = 'silentlyContinue'"
    GET_HYPER_V_INSTALLED_CMD = "powershell.exe Get-Command *-VM"
    VM_START_TIME_OUT = 3000  # Command timeout constant to wait for VM
    VSWITCH_TIME = 200   # Command timeout constant to create vSwitch
    WAIT_VM = 200
    VM_TIME_OUT = 1200
    COMMON_TIMEOUT = 30
    ENABLE_HYPER_V_CMD = "powershell.exe {}; Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V" \
                         " -All -NoRestart".format(SILENT_CONTINUE)
    INSTALL_HYPER_V_MODULES = "powershell.exe {}; Install-WindowsFeature -Name RSAT-Hyper-V-Tools". \
        format(SILENT_CONTINUE)
    NEW_VM_STR = "New-VM"
    SCSI_TYPE_STR = "SCSI"
    CREATE_VM_FROM_TEMPLATE_CMD = "powershell.exe $progressPreference = 'silentlyContinue'; New-VM -Name {} -MemoryStartupBytes {}MB -Generation {} -VHDPath {}"
    SUT_ISO_IMAGE_LOCATION = "C:\\Automation\\"
    CREATE_VM_FROM_ISO_CMD = "powershell.exe $progressPreference = 'silentlyContinue'; \"New-VM -Name {} -MemoryStartupBytes {}MB " \
                             "-NewVHDPath {} " \
                             "-NewVHDSizeBytes {}GB | Add-VMDvdDrive -Path {} \""
    GET_VM_CMD = "powershell.exe $progressPreference = 'silentlyContinue'; Get-VM -Name {}"
    VM_STATE_STR = "Running"
    GET_VM_LIST_CMD = "powershell.exe $progressPreference = 'silentlyContinue'; Get-VM"
    VERIFY_VM_STATE = "powershell.exe {}; Get-VM -Name {}"
    START_VM_CMD = "powershell.exe $progressPreference = 'silentlyContinue'; Start-VM -Name {}"
    WAIT_VM_CMD = "powershell.exe {}; Wait-VM -Name {}"
    REMOVE_VM_CMD = "powershell.exe $progressPreference = 'silentlyContinue'; Remove-VM -Name {} -Force"
    GET_VM_VHDPATH_CMD = "powershell.exe $progressPreference = 'silentlyContinue'; Get-VMHardDiskDrive -VMName {} ^| Select Path"
    SET_SRIOV_VM_NETWORK_ADAPTER_CMD = "powershell.exe $progressPreference = 'silentlyContinue'; Set-VMNetworkAdapter -VMName {} -IovWeight 100"
    DELETE_VHD_CMD = "powershell.exe $progressPreference = 'silentlyContinue'; Del {}"
    COPY_COMMAND_TO_VM = "powershell.exe {}; Copy-VMFile '{}' -SourcePath '{}' -DestinationPath '{}'" \
                         " -CreateFullPath -FileSource Host"
    SHUTDOWN_VM_CMD = "powershell.exe $progressPreference = 'silentlyContinue'; Stop-VM -Name {} -Force"
    RESTART_VM_CMD = "powershell {}; Restart-VM -Name {} -Force"
    GET_VM_Memory_CMD = "powershell.exe $progressPreference = 'silentlyContinue'; Get-VMMemory -VMName {}"
    MODIFY_VM_MEMORY_COMMAND = "powershell.exe {}; Set-VMMemory -VMName {} -StartupBytes {}GB"
    GET_CPU_NUM_CMD = "powershell.exe $progressPreference = 'silentlyContinue'; Get-VMProcessor {}"
    MODIFY_VM_CPU_COMMAND = "powershell.exe {}; Set-VMProcessor -VMName {} -Count {}"
    GET_NETWORK_INTERFACE_NAME_CMD = "powershell.exe {};  Get-NetIPAddress  ^| Select InterfaceAlias, " \
                                     "IPAddress, PrefixOrigin, SuffixOrigin"
    GET_NET_ADAPTER_CMD_STATUS = 'powershell.exe {}; ("Get-NetAdapter -Name * -Physical | ? Status -eq ' \
                                 'Up).Name'.format(SILENT_CONTINUE)
    GET_NET_ADAPTER_CMD = "powershell.exe {};  Get-NetIPAddress  ^| Select InterfaceAlias, " \
                          "IPAddress, PrefixOrigin, SuffixOrigin".format(SILENT_CONTINUE)
    GET_NET_ADAPTER_NAME = 'Get-NetAdapter -InterfaceDescription "{}" ^| Format-List -Property "Name"'
    GET_NET_ADAPTER_NAME_GEN4 = "powershell.exe  $progressPreference = 'silentlyContinue'; Get-NetAdapter -InterfaceDescription '*E810*'"
    GET_VM_NETWORK_ADAPTER_CMD = "powershell.exe {}; Get-VMNetworkAdapter -VMName '{}' ^| Select-Object IPAddresses, " \
                                 "MacAddress, Name"
    NEW_VM_SWITCH_CMD = "powershell.exe {}; New-VMSwitch -Name {} -NetAdapterName '{}'" \
                        " -AllowManagementOS $true"
    NEW_VM_SWITCH_WITH_SRIOV_CMD = "powershell.exe $progressPreference = 'silentlyContinue'; New-VMSwitch {} -NetAdapterName '{}' -EnableIov 1"
    ADD_VM_NETWORK_ADAPTER_CMD = "powershell.exe {}; Add-VMNetworkAdapter -VMName {} -Name '{}'" \
                                 " -SwitchName {}"
    ASSIGN_IP_ADDRESS = "powershell.exe {}; New-NetIPAddress -IPAddress {} -InterfaceIndex {} " \
                        "-PrefixLength 24 -DefaultGateway {}"
    RENAME_NET_ADAPTER_CMD = "powershell.exe {}; Rename-NetAdapter -Name '{}' -NewName '{}'"
    GET_VM_NIC_NAME_CMD = "powershell.exe {}; Get-NetAdapterAdvancedProperty -DisplayName " \
                          "'Hyper-V Network Adapter Name'"
    GET_NET_ADAPTER_INTERFACE_INDEX_CMD = "powershell.exe {}; Get-NetAdapter -Name '{}' ^| Select " \
                                          "InterfaceIndex -Expandproperty InterfaceIndex"
    VSWITCH_NAME = "powershell.exe $progressPreference = 'silentlyContinue'; Get-NetAdapterSriov ^| Where-Object " \
                   "ElementName -eq '{}' ^| Select Name -ExpandProperty Name"
    ENABLE_SRIOV = "powershell.exe $progressPreference = 'silentlyContinue'; Enable-NetAdapterSriov -Name '{}'"
    REGEDIT_CMD = 'powershell.exe "$progressPreference = \'silentlyContinue\'; reg add ' \
                  'HKLM\Software\Microsoft\WindowsNT /v IOVEnableOverride /t REG_DWORD /d \'1\' /F"'
    NET_VMMS_CMD = "net {} vmms"
    VM_INTEGRATION_SERVICE = "powershell.exe $progressPreference = 'silentlyContinue'; " \
                             "Enable-VMIntegrationService -VMName {} -Name 'Guest Service Interface'"
    NEW_VM_SWITCH_WITH_SRIOV = "powershell.exe {}; New-VMSwitch -Name {} -AllowManagementOS $false -NetAdapterName '{}' -EnableIov {}"
    GET_NET_ADAPTER_SRIOV = "powershell.exe {}; $progressPreference = 'silentlyContinue'; Get-NetAdapterSriov -Name '{}'"
    SET_SRIOV_VM_NETWORK_ADAPTER = "powershell.exe {}; Set-VMNetworkAdapter -VMName {} -Name {} -IovWeight 100"
    ASSIGN_MAC_ID = "powershell.exe {}; Set-VMNetworkAdapter -VMName {} -Name {} -StaticMacAddress {}"
    REMOVE_VM_NETWORK_ADAPTER_CMD = "powershell.exe {}; Remove-VMNetworkAdapter -VMName {} -VMNetworkAdapterName {}"
    GET_VSWITCH = "powershell.exe {}; Get-VMNetworkAdapter -VMName '{}' ^| fl"
    GET_SUT_VSWITCH = "powershell.exe {}; Get-VMSwitch ^| Select-Object Name -ExpandProperty Name"
    REMOVE_VM_SWITCH_COMMAND = "powershell.exe {}; Remove-VMSwitch -Name '{}' -Force"
    ESTABLISH_PS_SESSION = "$account = '{}';$password = '{}';$secpwd = convertTo-secureString " \
                           "$password -asplaintext -force ;$cred = new-object " \
                           "System.Management.Automation.PSCredential -argumentlist $account," \
                           "$secpwd ;Invoke-Command  -VMName '{}' -Credential $cred -ScriptBlock {} "
    ASSIGN_MAC_ID_VM = "powershell.exe Set-VMNetworkAdapter -VMName {} -Name {} -StaticMacAddress '{}'"
    SSH_FILE_NAME = "\OpenSSH-Win64.zip"
    TEST_VM_FILE_NAME = "vm_test_file.txt"
    SSH_PATH = Framework.CFG_BASE[OperatingSystems.WINDOWS]  # "C:\\Automation\\"
    SSH_STR = "OpenSSH-Win64.zip"
    VM_ROOT_PATH = CommonContentLib.C_DRIVE_PATH
    VM_SSH_FOLDER = VM_ROOT_PATH + SSH_STR
    ROOT_PATH = "/root"
    SSH_FILE = "{C:\\OpenSSH-Win64\\install-sshd.ps1}"
    START_SERVICE_SSHD_CMD = "{Start-Service sshd}"
    SET_SERVICE_CMD = "{Set-Service -Name sshd -StartupType 'Automatic'}"
    GET_SSH_NAME_CMD = "{Get-NetFirewallRule -Name *ssh*}"
    DISPLAY_SSH_CMD = "{New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' " \
                      "-Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22}"
    ENABLE_VM_INTEGRATION_SERVICE_CMD = "powershell.exe {}; Enable-VMIntegrationService -VMName '{}' -Name '{}'"
    GUEST_SERVICE_STR = "Guest Service Interface"
    EXTRACT_FILE_STR = "Expand-Archive -Path '{}' -DestinationPath '{}'"
    COPY_ITEM_CMD = "powershell {}; Copy-Item -Path {} -Destination {}"
    STORAGE_DEVICE_LIST_CMD = "powershell {}; Get-Disk ^| Where-Object IsSystem -eq $False ^| " \
                              "Where-Object BusType -EQ '{}' ^| Where-Object OperationalStatus -EQ '{}' ^|" \
                              "Select-Object *"
    SET_DISK_OFFLINE_CMD = "powershell {}; Set-Disk -Number '{}' -IsOffline $True"
    SET_DISK_ONLINE_CMD = "powershell {}; Set-Disk -Number '{}' -IsOffline $False"
    GET_DISK_STATUS = "powershell {}; Get-Disk -Number '{}' ^| Select-Object Model, " \
                      "DiskNumber, BusType, OperationalStatus"
    DISK_STATUS = "Online"
    MAC_ID_INDEX = 0
    ATTACH_STORAGE_DEVICE_TO_VM = "powershell {}; Get-VM {} ^| Add-VMHardDiskDrive -ControllerType {} -DiskNumber '{}'"
    DETACH_STORAGE_DEVICE_TO_VM = "powershell {}; Remove-VMHardDiskDrive -VMName {} -Passthru -ControllerType {} " \
                                  "-ControllerNumber 0 -ControllerLocation 0"
    OPERATIONAL_STATUS = "ONLINE"
    SET_DISK_WRITABLE = "powershell {}; Set-Disk -Number '{}' -IsReadOnly $False"
    TURNOFF_VM_CMD = "powershell.exe Stop-VM -Name {} -TurnOff"
    SET_HYPER_V_VM_AUTOMATIC_STOP_ACTION_CMD = "powershell.exe Set-VM -Name {} -AutomaticStopAction {}"
    GET_DEVICE_PARTITION = "powershell {}; Get-Partition -DiskNumber '{}' ^| Select-Object AccessPaths, DiskNumber, " \
                           "DiskPath, DriveLetter, OperationalStatus, Size"
    IMPORT_VM_FROM_COPY = "powershell.exe Import-VM -Path '{0}' -Copy -GenerateNewId " \
                          "-SmartPagingFilePath '{1}' -SnapshotFilePath " \
                          "'{1}' -VhdDestinationPath '{1}\\VHD' " \
                          "-VirtualMachinePath '{1}'"
    RENAME_VM = "powershell.exe Rename-VM -Name {} -NewName {}"
    GET_VM_SWITCH = "powershell.exe Get-VMSwitch ^| Select-Object -Property Name ^|ft -HideTableHeaders"
    GET_CHECKPOINTS = "powershell.exe Get-VMCheckpoint -VMName {0} ^| Where-Object {{$_.VMName -eq '{0}'}} ^| " \
                      "Select-Object -Property Name ^| ft -HideTableHeaders"
    REMOVE_CHECKPOINT = "powershell.exe Remove-VMCheckPoint -Name '{}' -VMName {}"
    APPLY_CHECKPOINT = "powershell.exe Restore-VMCheckPoint -Name '{}' -VMName {} -Confirm:$false"
    SET_BOOT_ORDER_CMD = "powershell.exe Set-VMFirmware '{}' -BootOrder {}"
    TEMPLATE_MAC_ID = "00-15-5D-10-20-00"
    GET_VM_SRIOV_ADAPTER = "powershell.exe {}; Get-NetAdapter"

    def create_vm(self, vm_name, os_variant, no_of_cpu=2, disk_size=6, memory_size=4, vm_creation_timeout=1600,
                  vm_create_async=None, mac_addr=None, pool_id=None, pool_vol_id=None, cpu_core_list=None,
                  nw_bridge=None, vm_os_subtype=None, nesting_level=None, vhdx_dir_path=None, devlist=[], qemu=None):
        """
        Execute the the command to create a VM from scratch using iso image.
        Please note that ISO image which supports unattended installation needs to be prepare first in order to
        install OS for VM automatically.
        Follow the instruction src/configuration/vm_provider_BKM.md to create an ISO image which supports unattended installation.

        :param vm_name: Name of the new VM
        :param vm_create_async: if VM is has to be created in async mode such as required for nested VM
        :param no_of_cpu: No of CPUs in VM
        :param disk_size: Size of the VM disk drive. Expected to be an int value. The measurement here is GB.
        :param memory_size: Size of the VM memory. Expected to be an int value. The measurement here is GB.
        :param os_variant: linux Os version
        :param vm_creation_timeout: timeout for vm creation, default is 1600 seconds
        :param mac_addr: Assign MacAddress to Network.
        :param pool_id: Storage pool id from storage
        :param pool_vol_id: Storage pool Volume id from storage volume created in the given pool
        :param cpu_core_list: CPU core list to be assigned to VM with --cpuset
        :param nw_bridge : Some Non-None value is bridge type default n/w required in VM
        :param nesting_level: nesting_level in case of nested VM
        :return vm_name: Name of the new VM

        :raise: RunTimeError
        """
        if vm_name is None or vm_name is "":
            raise RuntimeError("Invalid VM name! VM name can't be none.\n")

        if " " in vm_name:
            raise RuntimeError("Invalid VM name! Space is not allowed in vm name.\n")

        check_vm_existance = self.get_vm_info(vm_name)
        if check_vm_existance is not None:
            self._log.info("VM named {} already existed. Cancelling creation...\n".format(vm_name))
            raise RuntimeError("vm_name {} is taken. Please create VM with another name.\n".format(vm_name))

        self._log.info("VM type- {}".format(vm_os_subtype))
        if VMs.CENTOS.lower() in vm_name.lower() or VMs.RHEL.lower() in vm_name.lower() or VMs.WINDOWS.lower() in vm_name.lower():
            verify_iso_image = self._verify_iso_existance(vm_name, vm_os_subtype)
            if not verify_iso_image:
                image_path = self._copy_iso_image_to_windows_sut(vm_name)
            else:
                self._log.info("ISO image already present on SUT. Continue VM : {}Creation".format(vm_name))
                image_path = self._verify_iso_existance(vm_name, vm_os_subtype)
        else:
            raise NotImplementedError("Only linux and windows VM type is supported and the VM name should contain "
                                      "windows/linux. {} VM type is not implemented".format(vm_name))

        self._log.info("Creating VM named {} from ISO image".format(vm_name))
        if vhdx_dir_path:
            vhd_path = vhdx_dir_path + vm_name + ".vhdx"
        else:
            vhd_path = self.SUT_ISO_IMAGE_LOCATION + vm_name + ".vhdx"
        vhd_size = disk_size
        create_vm_result = self._common_content_lib.execute_sut_cmd(self.CREATE_VM_FROM_ISO_CMD.format(vm_name,
                                                                                                       memory_size,
                                                                                                       vhd_path,
                                                                                                       vhd_size,
                                                                                                       image_path),
                                                                    "VM creation", vm_creation_timeout)
        get_vm_result = self.get_vm_info(vm_name)
        self._log.debug("'Hyper-V' command response \n{}".format(get_vm_result))
        if get_vm_result is None:
            self._log.error("Failed create the {} VM".format(vm_name))
            raise RuntimeError("Failed to create the {} VM".format(vm_name))
        self._log.info("Successfully created the {} VM".format(vm_name))

    def _verify_iso_existance(self, vm_name, vm_os_subtype=None):
        """
         Method to verify if ISO image already present on the windows SUT

        :param vm_name: Name of the new VM. Either "linux" or "windows" should be included in the name
        :param vm_os_subtype: sub OS type
        :return : Complete location of ISO image
        """
        self._log.info("Check if ISO image already present on SUT for given VM")
        cmd_result = []

        self._log.info("Check if {} folder exist".format(self.SUT_ISO_IMAGE_LOCATION))
        if not self.os.check_if_path_exists(self.SUT_ISO_IMAGE_LOCATION):
            self._log.info("Folder not available, creating now..")
            self.os.execute("mkdir {}".format(self.SUT_ISO_IMAGE_LOCATION), self._command_timeout)

        if vm_os_subtype in [VMs.RHEL, VMs.CENTOS]:
            if vm_os_subtype:
                image_host_location = self._common_content_configuration.get_os_iso_location_on_host(
                    self.os.os_type.lower(), vm_os_subtype)
            else:
                image_host_location = self._linux_image_host_location

            iso_filename = self.SUT_ISO_IMAGE_LOCATION + os.path.basename(image_host_location)
            path_exist_status = self.os.check_if_path_exists(iso_filename)
            self._log.info("Existing ISO image: {}".format(iso_filename))
            if not path_exist_status:
                self.os.copy_local_file_to_sut(image_host_location, iso_filename)
                return iso_filename
            else:
                return iso_filename
        elif "windows" in vm_name.lower():
            self._log.info("Check if {} folder exist".format(self.SUT_ISO_IMAGE_LOCATION))
            if not self.os.check_if_path_exists(self.SUT_ISO_IMAGE_LOCATION):
                self._log.info("Folder not available, creating now..")
                self.os.execute("mkdir {}".format(self.SUT_ISO_IMAGE_LOCATION), self._command_timeout)
            iso_filename = self.SUT_ISO_IMAGE_LOCATION + os.path.basename(self._windows_image_host_location)
            path_exist_status = self.os.check_if_path_exists(iso_filename)
            self._log.info("Existing ISO image: {}".format(iso_filename))
            if not path_exist_status:
                self.os.copy_local_file_to_sut(self._windows_image_host_location, iso_filename)
                return iso_filename
            else:
                return iso_filename

    def _copy_iso_image_to_windows_sut(self, vm_name):
        """
        Private method to copy the ISO image to the windows SUT
        :param vm_name: Name of the new VM. Either "linux" or "windows" should be included in the name
        :return : complete location of the copied Image file
        """
        self._log.info("Copying ISO image to windows SUT")
        iso_filename = None
        iso_location = None
        if VMs.CENTOS.lower() in vm_name.lower() or VMs.RHEL.lower() in vm_name.lower():
            iso_filename = os.path.basename(self._linux_image_host_location)
            iso_location = self._linux_image_host_location
        elif VMs.WINDOWS.lower() in vm_name.lower():
            iso_filename = os.path.basename(self._windows_image_host_location)
            iso_location = self._windows_image_host_location
        else:
            raise NotImplementedError("{} VM type is not implemented".format(vm_name))

        if not os.path.exists(iso_location):
            raise RuntimeError("ISO image is not present.Note that this ISO image is expected to support "
                               "unattended installation. Please keep the file under {} "
                               .format(iso_location))
        cmd_result = self._common_content_lib.execute_sut_cmd("powershell.exe ls", "getting the folder content",
                                                              self._command_timeout,
                                                              cmd_path=self.SUT_ISO_IMAGE_LOCATION)
        self._log.debug("{} Folder contains :\n{}".format(self.SUT_ISO_IMAGE_LOCATION, cmd_result))
        if not self.os.check_if_path_exists(iso_location):
            self.os.copy_local_file_to_sut(iso_location, self.SUT_ISO_IMAGE_LOCATION + iso_filename)
            self._log.info("Successfully copied the iso image file to {}".format(self.SUT_ISO_IMAGE_LOCATION))
        else:
            raise RuntimeError("Target path for ISO image: {} doesn't exist on SUT".format(iso_location))
        return self.SUT_ISO_IMAGE_LOCATION + iso_filename

    def create_vm_from_template(self, vm_name, memory_size=4, vm_creation_timeout=1600, gen=1, vhdx_path=None):
        """
        Execute the the command to create a VM from an existing template base image in vhdx format.

        :param vm_name: Name of the new VM. Either "linux" or "windows" should be included in the name
        :param memory_size: Size of the VM memory
        :param vm_creation_timeout: timeout for vm creation in ms.
        :param gen: VM generation.

        :raise: RunTimeError
        """
        if vm_name is None or vm_name is "":
            raise RuntimeError("Invalid VM name! VM name can't be none.\n")

        if " " in vm_name:
            raise RuntimeError("Invalid VM name! Space is not allowed in vm name.\n")

        check_vm_existance = self.get_vm_info(vm_name)
        if check_vm_existance is not None:
            self._log.error("VM named {} already existed. Cancelling creation...\n".format(vm_name))
            raise RuntimeError("vm_name {} is taken. Please create VM with another name.\n".format(vm_name))

        if "linux" in vm_name.lower() or "windows" in vm_name.lower():
            image_path = self._copy_vm_template_to_sut_windows_sut(vm_name, vhdx_path)
        else:
            raise NotImplementedError("Only linux and windows VM type is supported and the VM name should contain "
                                      "windows/linux. {} VM type is not implemented".format(vm_name))
        self.install_vm_tool()
        self.install_kvm_vm_tool()
        self._log.info("Creating VM named {} from existing template".format(vm_name))
        create_vm_result = self._common_content_lib.execute_sut_cmd(self.CREATE_VM_FROM_TEMPLATE_CMD.
                                                                    format(vm_name, memory_size, gen, image_path),
                                                                    "VM creation",
                                                                    vm_creation_timeout)
        self._log.debug("'Hyper-V' command response \n{}".format(create_vm_result))
        if vm_name and "Operating normally" not in create_vm_result:
            raise RuntimeError("Failed to create the {} VM".format(vm_name))
        # TODO: Need to get storge size and number of cpu info and print it
        self._log.info("Successfully create the {}  VM".format(vm_name))

    def _copy_vm_template_to_sut_windows_sut(self, vm_name, vhdx_path=None):
        """
        Private method to copy the vm template file to the windows SUT
        :param vm_name: Name of the new VM. Either "linux" or "windows" should be included in the name
        :return : complete location of the copied Image file
        """
        self._log.info("Copying VM template file to windows SUT")
        template_filename = None
        template_location = None
        if "linux" in vm_name.lower():
            template_filename = os.path.basename(self._linux_vm_template_host_location)
            template_location = self._linux_vm_template_host_location
        elif "windows" in vm_name.lower():
            template_filename = os.path.basename(self._windows_vm_template_host_location)
            template_location = self._windows_vm_template_host_location
        else:
            raise NotImplementedError("{} VM type is not implemented".format(vm_name))

        if not os.path.exists(template_location):
            raise RuntimeError("VM template file is not present. Please keep the file under {}"
                               .format(template_location))
        if vhdx_path:
            expected_template_dir_location = vhdx_path
        else:
            expected_template_dir_location = self.SUT_ISO_IMAGE_LOCATION
        cmd_result = self._common_content_lib.execute_sut_cmd("powershell.exe ls", "getting the folder content",
                                                              self._command_timeout,
                                                              cmd_path=expected_template_dir_location)
        self._log.debug("{} Folder contains :\n{}".format(self.SUT_ISO_IMAGE_LOCATION, cmd_result))
        sut_vhd_path = expected_template_dir_location + vm_name + ".vhdx"
        if not self.os.check_if_path_exists(sut_vhd_path):
            self.os.copy_local_file_to_sut(template_location, sut_vhd_path)
            self._log.info("Successfully copied the VM template file to {}".format(expected_template_dir_location))
        return sut_vhd_path

    def create_bridge_network(self, switch_name, adapter_name=None):
        """
        Method to create the network bridge on SUT.

        :param switch_name - Switch Name
        :param adapter_name - Ethernet Adapter Name eg:- Ethernet 1, Ethernet 2
        :raise: NotImplementedError
        """
        try:
            self.remove_bridge_network()
            regex_for_nic_name = r".+\s*10\..+\s*Dhcp.+\s*Dhcp"
            self._log.info("Creating vSwitch : {} for VM".format(switch_name))
            if adapter_name is None:
                adapter_info = self._common_content_lib.execute_sut_cmd(
                    self.GET_NETWORK_INTERFACE_NAME_CMD.format(self.SILENT_CONTINUE), "Get net adapters",
                    self._command_timeout)
                adapter_list = re.findall(regex_for_nic_name, adapter_info)
                display_name = (re.sub('\s\s+', '*', adapter_list[0])).split('*')
                adapter_name = display_name[0]
            self._log.info("Get the network adapter info:{}\n".format(adapter_name))
            new_switch = self._common_content_lib.execute_sut_cmd(
                self.NEW_VM_SWITCH_CMD.format(self.SILENT_CONTINUE, switch_name, adapter_name), "New vm switch",
                self.VSWITCH_TIME)
            self._log.debug("New vSwitch stdout:\n{}".format(new_switch))
            self._log.info("Successfully created new vSwitch")
        except Exception as ex:
            self._log.error("SUT will lose its network connectivity while creating vSwitch. Ignoring this "
                            "exception '{}'...".format(ex))

    def add_vm_network_adapter(self, methods, vm_name, physical_adapter_name, switch_name, vm_type=None, mac_addr=None):
        """
        Method to add network adapter for given VM.

        :param methods: The methods to add network adapter to VM. The value is expected to be "DDA" or "SRIOV".
        :param vm_name: Name of the VM.
        :param physical_adapter_name: Name of the physical network adapter on SUT.
                             Note: the adapter is expected to be extra test NIC instead of builtin NIC.
        :param switch_name: Name of the switch you create
        :param vm_type: VM type for eg: "RS5"
        :param physical_adapter_name: Physical Adapter Name
        :param mac_addr: Assign Mac Address to Network Adapter
        :raise: RunTimeError
        :return: None
        """
        try:
            if methods.lower() == "dda":
                self._add_vm_network_adapter_via_dda(vm_name, switch_name, vm_type, mac_addr,
                                                     adapter_name=physical_adapter_name)
            elif methods.lower() == "sriov":
                self._add_vm_network_adapter_via_sriov(vm_name, physical_adapter_name, switch_name)
            else:
                raise RuntimeError("Invalid params for methods!The methods is expected to be DDA or SRIOV. "
                                   "{} is not supported.\n".format(methods))

            self._log.info("Successfully added network adapter to {}.\n".format(vm_name))
            adapter_info = self._common_content_lib.execute_sut_cmd(self.GET_NET_ADAPTER_CMD,
                                                                    "Get net adapters", 60)
            self._log.info("Get the network adapter info:{}\n".format(adapter_info))

        except Exception as ex:
            raise ("Unable to add network adapter to VM due to : {}".format(ex))

    def _get_vm_network_adapter(self, vm_name):
        """
        Method to add network adapter for given VM.

        :param vm_name: Name of the VM.
        :raise: RunTimeError. It will the error caught when executing the GET_VM_NETWORK_ADAPTER_CMD.
        :return: None
        """
        try:
            self._log.info("Get {} network adapter...\n".format(vm_name))
            adapter_info = self._common_content_lib.execute_sut_cmd(self.GET_VM_NETWORK_ADAPTER_CMD.format(vm_name),
                                                                    "GET_VM_NETWORK_ADAPTER_CMD", 60)
            self._log.info(adapter_info)
            return adapter_info
        except RuntimeError:
            self._log.error("Fail to get {} network adapter!\n".format(vm_name))
            raise

    def _get_vm_network_adapter_pci_card(self):
        """
        Method to add network adapter for given VM.

        :param vm_name: Name of the VM.
        :raise: RunTimeError. It will the error caught when executing the GET_VM_NETWORK_ADAPTER_CMD.
        :return: None
        """
        try:
            regex_for_nic_name = ".*Intel\(R\)\sEthernet\sNetwork\sAdapter\sE8.*"
            self._log.info("Get pci card network adapter...\n")
            adapter_info = self._common_content_lib.execute_sut_cmd(self.GET_NET_ADAPTER_NAME_GEN4,
                                                                    "GET_VM_NETWORK_ADAPTER_CMD", 60)
            self._log.info(adapter_info)
            adapter_info = re.findall(regex_for_nic_name, adapter_info)
            display_name = (re.sub('\s\s+', '*', adapter_info[0])).split('*')
            adapter_name = display_name[0]
            return adapter_name
        except RuntimeError:
            self._log.error("Fail to get pci card Gen 4 network adapter!\n")
            raise

    def add_vm_ethernet_adapter(self, vm_name, switch_name, vm_type=None, mac_addr=None):
        """
        Method to add network adapter for given VM.

        :param vm_name: Name of the VM.
        :raise: RunTimeError. It will the error caught when executing the GET_VM_NETWORK_ADAPTER_CMD.
        :return: None
        """
        try:
            vm_state = self._get_vm_state(vm_name)
            if self.VM_STATE_STR == vm_state:
                self._log.info("{} is in Running state. Powering Off VM...\n".format(vm_name))
                self._shutdown_vm(vm_name)
                # wait for vm to shutdown
                time.sleep(self.COMMON_TIMEOUT)
            # add vm network adapter
            vm_adapter_name = "adapter_for_{}".format(vm_name)
            add_vm_network_adapter = self._common_content_lib.execute_sut_cmd(
                self.ADD_VM_NETWORK_ADAPTER_CMD.format(self.SILENT_CONTINUE, vm_name, vm_adapter_name, switch_name),
                "Add vm network adapter", self.VSWITCH_TIME)
            self._log.debug("Network Adapter stdout:\n{}".format(add_vm_network_adapter))
            if mac_addr:
                net_adapter_with_register_mac_dict = {}
                if vm_adapter_name not in net_adapter_with_register_mac_dict.keys():
                    mac_id_list = self._common_content_configuration.get_mac_address_for_vm(self.os.os_type.lower(),
                                                                                            vm_type)
                    net_adapter_with_register_mac_dict[vm_adapter_name] = mac_id_list[WindowsVmProvider.MAC_ID_INDEX]
                    WindowsVmProvider.MAC_ID_INDEX += 1
                assign_mac_id = self._common_content_lib.execute_sut_cmd(
                    self.ASSIGN_MAC_ID.format(self.SILENT_CONTINUE, vm_name, vm_adapter_name,
                                              net_adapter_with_register_mac_dict[vm_adapter_name]),
                    "Assigning Mac ID to"
                    " Adapter",
                    self._command_timeout)
            self._log.info("Successfully added network adapter to VM")

        except Exception as ex:
            raise ("Fail to get network adapter!\n {}".format(ex))

    def _add_vm_network_adapter_via_sriov(self, vm_name, physical_adapter_name, switch_name):
        """
        Method to add network adapter via SRIOV. The given network adapter will be assigen to VM as a virtual function.

        :param vm_name: Name of the VM.
        :param physical_adapter_name: Name of the physical network adapter on SUT.
                             Note: the adapter is expected to support SRIOV feature.
        :param switch_name: Name of the switch you create
        :raise: RunTimeError. It will be whatever caught inside the try block. It can be the exception when calling the
        execute_sut_cmd() or when calling other private function in WindowsVMProvider.
        :return: None
        """
        self._log.info("Add vm network adapter via SRIOV...\n")
        try:
            adapter_info = self._common_content_lib.execute_sut_cmd(self.GET_NET_ADAPTER_CMD,
                                                                    "Get net adapters", 60)
            self._log.info("Get the network adapter info:{}\n".format(adapter_info))
            if physical_adapter_name not in adapter_info:
                self._log.info("Invalid adapter name!")
                raise RuntimeError("Invalid adapter name!")
            # new VM switch
            new_switch = self._common_content_lib.execute_sut_cmd(self.NEW_VM_SWITCH_WITH_SRIOV_CMD.format(switch_name, physical_adapter_name),
                                                                  "NEW_VM_SWITCH_WITH_SRIOV_CMD", 60)

            # add vm network adapter
            vm_adapter_name = "adapter_for_{}".format(vm_name)
            self.turn_off_vm(vm_name)
            add_vm_network_adapter = self._common_content_lib.execute_sut_cmd(self.ADD_VM_NETWORK_ADAPTER_CMD.format
                                                                              (self.SILENT_CONTINUE, vm_name,
                                                                               vm_adapter_name, switch_name),
                                                                              "Add vm network adapter", 60)
            set_sriov_vm_network_adapter = self._common_content_lib.execute_sut_cmd(self.SET_SRIOV_VM_NETWORK_ADAPTER_CMD.format
                                                                              (vm_name), "Set SRIOV on vm network adapter", 60)
            self.start_vm(vm_name)
            # wait for vm to boot into os
            wait_for_vm_result = self._common_content_lib.execute_sut_cmd(
                self.WAIT_VM_CMD.format(self.SILENT_CONTINUE, vm_name), "Wait for VM to boot",
                self.VM_START_TIME_OUT)
            time.sleep(self.WAIT_VM)
        except RuntimeError:
            raise

    def _add_vm_network_adapter_via_dda(self, vm_name, switch_name, vm_type=None, mac_addr=None, adapter_name=None):

        """
        Method to add network adapter via DDA(Direct Device Assignment),which means pass through physical network
        adapter on SUT to VM.

        :param vm_name: Name of the VM.
        :param switch_name: Name of the switch you create
        :param mac_addr: Assign Mac Address to Network Adapter
        :param adapter_name: Physical Adapter Name for creating Virtual Switch - Ethernet 11, Ethernet 1
        :raise: RunTimeError. It will be whatever caught inside the try block. It can be the exception when calling the
        execute_sut_cmd() or when calling other private function in WindowsVMProvider.
        :return: None
        """
        self._log.info("Add vm network adapter via DDA...\n")
        self._log.info("Creating {} for VM : {}".format(switch_name, vm_name))
        vm_state = self._get_vm_state(vm_name)
        if self.VM_STATE_STR == vm_state:
            self._log.info("{} is in Running state. Powering Off VM...\n".format(vm_name))
        self._shutdown_vm(vm_name)
        # wait for vm to shutdown
        time.sleep(30)
        regex_for_nic_name = r".+\s*10\..+\s*Dhcp.+\s*Dhcp"
        if adapter_name is None:
            adapter_info = self._common_content_lib.execute_sut_cmd(
                self.GET_NETWORK_INTERFACE_NAME_CMD.format(self.SILENT_CONTINUE), "Get net adapters",
                self._command_timeout)
            adapter_list = re.findall(regex_for_nic_name, adapter_info)
            display_name = (re.sub('\s\s+', '*', adapter_list[0])).split('*')
            adapter_name = display_name[0]
            self._log.info("Get the network adapter info:{}\n".format(adapter_name))
        try:
            # new VM switch
            new_switch = self._common_content_lib.execute_sut_cmd(
                self.NEW_VM_SWITCH_CMD.format(self.SILENT_CONTINUE, switch_name, adapter_name), "New vm switch",
                self.VSWITCH_TIME)

        except Exception as ex:
            self._log.error("SUT will lose its network connectivity while creating vSwitch. Ignoring this "
                            "exception '{}'...".format(ex))

        self._os.execute(
            "powershell.exe Get-VMNetworkAdapter -VMName {} -Name 'Network Adapter' ^| Remove-VMNetworkAdapter".format(
                vm_name), self.VSWITCH_TIME)

        # add vm network adapter
        vm_adapter_name = "adapter_for_{}".format(vm_name)
        add_vm_network_adapter = self._common_content_lib.execute_sut_cmd(
            self.ADD_VM_NETWORK_ADAPTER_CMD.format(self.SILENT_CONTINUE, vm_name, vm_adapter_name, switch_name),
            "Add vm network adapter", self.VSWITCH_TIME)
        if mac_addr:
            net_adapter_with_register_mac_dict = {}
            if vm_adapter_name not in net_adapter_with_register_mac_dict.keys():
                mac_id_list = self._common_content_configuration.get_mac_address_for_vm(self.os.os_type.lower(),
                                                                                        vm_type)
                net_adapter_with_register_mac_dict[vm_adapter_name] = mac_id_list[WindowsVmProvider.MAC_ID_INDEX]
                WindowsVmProvider.MAC_ID_INDEX += 1
            assign_mac_id = self._common_content_lib.execute_sut_cmd(
                self.ASSIGN_MAC_ID.format(self.SILENT_CONTINUE, vm_name, vm_adapter_name,
                                          net_adapter_with_register_mac_dict[vm_adapter_name]), "Assigning Mac ID to"
                                                                                                " Adapter",
                self._command_timeout)
            self._log.info("Successfully added network adapter to VM {}".format(assign_mac_id))
        time.sleep(30)

    def start_vm(self, vm_name):
        """
        Method to start VM.

        :param vm_name: Name of the VM to start
        :raise: RuntimeError. It will raise error when failed in executing the START_VM_CMD.
        """

        try:
            vm_state = self._get_vm_state(vm_name)
            if self.VM_STATE_STR not in vm_state:
                self._log.info("{} is powered off. Powering on VM\n".format(vm_name))
                start_vm_result = self._common_content_lib.execute_sut_cmd(
                    self.START_VM_CMD.format(vm_name), "Start VM: {}".format(vm_name), 60)
                self._log.info("Successfully started VM {}".format(vm_name))
            elif self.VM_STATE_STR in vm_state:
                self._log.info("WARNING: VM {} is already in running state.".format(vm_name))
        except RuntimeError:
            self._log.error("Unable to start the VM : {}".format(vm_name))
            raise

    def _shutdown_vm(self, vm_name, timeout=60):
        """
        Method to shutdown the VM.

        :param vm_name: Name of the VM to shutdown
        :param timeout: timeout for shutdown
        :raise: RunTimeError
        """
        try:
            shutdown_vm_result = self._common_content_lib.execute_sut_cmd(self.SHUTDOWN_VM_CMD.
                                                                          format(vm_name),
                                                                          "Shutdown VM: {}".format(vm_name), timeout)
            if "" is shutdown_vm_result:
                self._log.info("Successfully shutdown VM {}".format(vm_name))
        except RuntimeError:
            raise

    def reboot_vm(self, vm_name):
        """
        This method is to reboot the VM & verify if it is running or not

        :param vm_name: name of the VM
        """
        self._log.info("Rebooting the {} VM".format(vm_name))
        reboot_result = self._common_content_lib.execute_sut_cmd(
            self.RESTART_VM_CMD.format(self.SILENT_CONTINUE, vm_name), "restarting VM", self._command_timeout)
        self._common_content_lib.execute_sut_cmd(
            self.WAIT_VM_CMD.format(self.SILENT_CONTINUE, vm_name), "Wait for VM to boot", self._command_timeout)
        self._log.debug("Wait VM stdout:\n{}".format(reboot_result))
        self._log.info("Successfully Rebooted {} VM".format(vm_name))

    def wait_for_vm(self, vm_name):
        """
        This method is to wait for VM to boot properly after starting the VM
        """
        self._log.info("Waiting for VM: {} to boot".format(vm_name))
        wait_for_vm_result = self._common_content_lib.execute_sut_cmd(
            self.WAIT_VM_CMD.format(self.SILENT_CONTINUE, vm_name), "Wait for VM to boot", self.VM_TIME_OUT)
        time.sleep(self.WAIT_VM)

    def destroy_vm(self, vm_name):
        """
        Method to destroy the VM & it's resources

        :param vm_name: Name of the VM to destroy
        :raise: RunTimeError
        """

        try:
            # check current status of the VM and need to shut down VM if it's in running state
            vm_info = self._get_vm_state(vm_name)
            if self.VM_STATE_STR in vm_info:
                self._log.info("{} is in running state. Running CMD to stop it...".format(vm_name))
                self._shutdown_vm(vm_name)
                self.get_vm_info(vm_name)
            vhd_path = self._get_vm_vhd_path(vm_name)
            self._log.info("VHD Path of VM: {}".format(vhd_path))
            self.destroy_network_adapter(vm_name)
            remove_vm = self._common_content_lib.execute_sut_cmd(self.REMOVE_VM_CMD.
                                                                 format(vm_name),
                                                                 "Destroy VM: {}".format(vm_name), 60)
            if "" is remove_vm:
                self._log.info("Successfully removed VM {}".format(vm_name))

            self._log.debug(self.DELETE_VHD_CMD.format(vhd_path))
            remove_vhd = self._common_content_lib.execute_sut_cmd(self.DELETE_VHD_CMD.
                                                                  format(vhd_path),
                                                                  "Remove the vhd of VM: {}".format(vm_name), 60)

            if "" is remove_vhd:
                self._log.info("Successfully removed the VHD of VM {}".format(vm_name))
        except RuntimeError:
            raise

    def _get_vm_state(self, vm_name):
        """
        Method to get state of the given VM

        :param vm_name: the name of the given VM
        :raise: RunTimeError
        :return: the state of cpus. Running/Off/Paused
        """
        try:
            vm_info = self._common_content_lib.execute_sut_cmd(self.GET_VM_CMD.format(vm_name),
                                                               "Get state of: {}".format(vm_name), 60)
            self._log.info("Get state info:\n{}".format(vm_info))
            str_list = vm_info.split('\n')
            state = None
            index = 0
            for str in str_list:
                if str is not '' and '---' not in str:
                    res = re.finditer(r"\S+", str)
                    tmp_index = 0
                    for match in res:
                        if index is 0:
                            index = index + 1
                            break
                        if tmp_index is 0:
                            tmp_index = tmp_index + 1
                        else:
                            state = match.group()
                            break
            if state is None:
                return RuntimeError("Fail to get state info of the VM.")
            else:
                self._log.info("Get the state of {}:{}\n".format(vm_name, state))
                return state
        except RuntimeError:
            raise

    def _get_vm_num_of_cpus(self, vm_name):
        """
        Method to get the number of cpus of the given VM

        :param vm_name: the name of the given VM
        :raise: RunTimeError
        :return: the number of cpus
        """
        try:
            cpu_info = self._common_content_lib.execute_sut_cmd(self.GET_CPU_NUM_CMD.format(vm_name),
                                                                "Get cpu numbers of: {}".format(vm_name), 60)
            self._log.info("Get cpu info:{}".format(cpu_info))
            str_list = cpu_info.split('\n')
            num = None
            index = 0
            for str in str_list:
                if str is not '' and '---' not in str:
                    res = re.finditer(r"\S+", str)
                    tmp_index = 0
                    for match in res:
                        if index is 0:
                            index = index + 1
                            break
                        if tmp_index is 0:
                            tmp_index = tmp_index + 1
                        else:
                            num = match.group()
                            break
            if num is None:
                return RuntimeError("Fail to get number of cpus of the VM.")
            else:
                self._log.info("Get the number of cpus of {}:{}\n".format(vm_name, num))
                return num
        except RuntimeError:
            raise

    def update_vm_num_of_cpus(self, vm_name, cpu_config):
        """
        Method to Update number of cpus of the given VM

        :param vm_name: the name of the given VM
        :param cpu_config: updated CPU config value
        :raise: RunTimeError
        :return: the number of cpus
        """
        try:
            self._log.info("Increase CPU core to {} on VM:{}".format(cpu_config, vm_name))
            cpu_info = self._common_content_lib.execute_sut_cmd(
                self.MODIFY_VM_CPU_COMMAND.format(self.SILENT_CONTINUE, vm_name, cpu_config),
                "Update CPU configuration", self._command_timeout)
            self._log.debug("{} command stdout\n{}".format(self.MODIFY_VM_CPU_COMMAND, cpu_info))
            self._log.info("Successfully updated CPU configuration on VM:{}".format(vm_name))
            self._get_vm_num_of_cpus(vm_name)
        except Exception as ex:
            self._log.error("Error while updating cpu configuration.{}".format(ex))
            raise ex

    def _get_vm_vhd_path(self, vm_name):
        """
        Method to get the VHD Path of the given VM

        :param vm_name: the name of the given VM
        :raise: RunTimeError
        :return: Path of the vhd of the given VM
        """
        try:
            get_vm_vhd = self._common_content_lib.execute_sut_cmd(self.GET_VM_VHDPATH_CMD.
                                                                  format(vm_name),
                                                                  "Get VHD Path of: {}".format(vm_name), 60)
            self._log.info("Get VHD Path:{}".format(get_vm_vhd))
            str_list = get_vm_vhd.split('\n')
            vhd_path = None
            for str in str_list:
                if str is not '' and '---' not in str:
                    res = re.finditer(r"\S+", str)
                    tmp_list = []
                    for match in res:
                        if ".vhdx" in match.group():
                            vhd_path = match.group()
                            break
            if vhd_path is None:
                return RuntimeError("Fail to get VHD Path.")
            else:
                return vhd_path
        except RuntimeError:
            raise

    def get_vm_ip(self, vm_name):
        """
        Method to get the IPV4 address of the given VM

        :param vm_name: Name of the VM to get the IP
        :raise: RunTimeError
        :return: ip address in string type
        """

        try:
            vm_state = self._get_vm_state(vm_name)
            if self.VM_STATE_STR != vm_state:
                self._log.info("{} is not in Running state. Start VM...\n".format(vm_name))
                self.start_vm(vm_name)
                time.sleep(20)
                # wait for vm to boot into os
                wait_for_vm_result = self._common_content_lib.execute_sut_cmd(
                    self.WAIT_VM_CMD.format(self.SILENT_CONTINUE, vm_name), "Wait for VM to boot",
                    self.VM_START_TIME_OUT)
            time.sleep(30)
            ip_info = self._common_content_lib.execute_sut_cmd(
                self.GET_VM_NETWORK_ADAPTER_CMD.format(self.SILENT_CONTINUE, vm_name),
                "GET_VM_NETWORK_ADAPTER_CMD of: {}".format(self.SILENT_CONTINUE, vm_name), 60)
            self._log.info("ip info: \n{}".format(ip_info))
            str_list = ip_info.split('\n')
            ip = None
            vm_adapter_name = "adapter_for_{}".format(vm_name)
            for str in str_list:
                if vm_adapter_name in str:
                    res = re.search(r'\d+\.\d+\.\d+\.\d+', str, re.M | re.I)
                    if res:
                        ip = res.group()
            if ip is not None:
                self._log.info("Get {} ip: {}\n".format(vm_name, ip))
                return ip
            else:
                raise RuntimeError("Fail to get ip for vm {}!\n".format(vm_name))
        except RuntimeError:
            raise

    def destroy_network_adapter(self, vm_name):
        try:
            self._log.info("Destroying virtual network adapter")
            vswitch_res = self._common_content_lib.execute_sut_cmd(self.GET_VSWITCH.format(
                self.SILENT_CONTINUE, vm_name), "Get VM vSwitch", self._command_timeout)
            self._log.debug("{} command stdout\n{}".format(self.GET_VSWITCH, vswitch_res))
            vswitch = re.findall("SwitchName.*", vswitch_res)[0]
            switchname = vswitch.split(": ")[1]
            if len(switchname.strip()) == 0:
                self._log.info("vSwitch destroyed already")
            else:
                self._common_content_lib.execute_sut_cmd(
                    self.REMOVE_VM_SWITCH_COMMAND(self.SILENT_CONTINUE, switchname), "Remove vswitch",
                    self._command_timeout)
                self._log.info("Successfully destroyed vSwitch:{}".format(switchname))
        except Exception as ex:
            self._log.error("SUT will lose its network connectivity while creating or destroying vSwitch. Ignoring this"
                            "exception '{}'...".format(ex))

    def remove_bridge_network(self):
        """
        Method to remove the existed network bridge on SUT.

        :raise: NotImplementedError
        """
        try:
            self._log.info("Destroying Virtual Switch on SUT")
            vswitch_res = self._common_content_lib.execute_sut_cmd(self.GET_SUT_VSWITCH.format(
                self.SILENT_CONTINUE), "Get VM vSwitch", self._command_timeout)
            vswitch_list = vswitch_res.split("\n")
            self._log.info("Detected vswitch on sut : {}".format(vswitch_list))
            for name in vswitch_list:
                if name != '':
                    try:
                        self._log.info("Removing vswitch on sut : {}".format(name))
                        self._common_content_lib.execute_sut_cmd(self.REMOVE_VM_SWITCH_COMMAND.format(
                            self.SILENT_CONTINUE, name), "Deleting VSwitch", self._command_timeout)
                        self._log.info("Waiting for {} seconds to remove vswitch from sut".format(self.VSWITCH_TIME))
                        time.sleep(self.VSWITCH_TIME)
                    except Exception as ex:
                        self._log.error(
                            "SUT will lose its network connectivity while creating or destroying vSwitch. Ignoring this"
                            "exception '{}'...".format(ex))
                else:
                    self._log.info("Completed removing vswitch on SUT")
        except Exception as ex:
            self._log.error("SUT will lose its network connectivity while creating or destroying vSwitch. Ignoring this"
                            "exception '{}'...".format(ex))

    def create_vm_host(self, os_subtype, os_version, kernel_vr, vm_username, vm_password, vm_ip):
        """
        Method to create os executable object for given VM.

        :param vm_ip: ip of the VM OS
        :param vm_username: username of the VM
        :param os_version: os version
        :param os_subtype: os subtype
        :param kernel_vr: kernel version
        :param vm_password: Password of the VM
        :return : None
        """
        self._log.info("Creating OS executable object for given VM")
        if os_subtype in [VMs.RHEL, VMs.CENTOS]:
            os_name = OperatingSystems.LINUX
        else:
            os_name = self.os.os_type
        vm_cfg_opts = ElementTree.fromstring(VM_CONFIGURATION_FILE.format(os_name, os_subtype, os_version, kernel_vr,
                                                                          vm_username, vm_password, vm_ip))
        vm_os_obj = ProviderFactory.create(vm_cfg_opts, self._log)
        return vm_os_obj

    def ping_vm_from_sut(self, vm_ip, vm_name=None, vm_account=None, vm_password=None):
        """
        This method is to ping the VM from SUT system

        :param vm_name: name of given VM
        :param vm_ip: IP of the VM
        :param vm_account: user account for the VM
        :param vm_password: password for the VM account
        :return: ping result of the VM
        :raise: RunTimeError
        """
        try:
            if "windows" in vm_name.lower():
                # disable firewall is guest OS is windows
                self._disable_firewall_on_windows_vm(vm_name, vm_account, vm_password)

            self._log.info("pinging {} from SUT".format(vm_ip))
            ping_result = self._common_content_lib.execute_sut_cmd("ping {}".format(vm_ip), "ping {}".format(
                vm_ip), self._command_timeout)
            self._log.info("Ping result data :\n{}".format(ping_result))
            self._log.info("Successfully pinged the VM from SUT")
            return ping_result
        except RuntimeError:
            self._log.error("Fail to ping the VM from SUT")
            raise

    def _disable_firewall_on_windows_vm(self, vm_name, vm_account, vm_password):
        """
        Method to disable firewall on windows VM

        :param vm_name: the name of given VM
        :params vm_account: account for os
        :params vm_password: password for the account
        :raise: RunTimeError
        :return: None
        """

        self._log.info("Try to disable firewall in VM...")
        try:
            establish_ps_session = "$account = '{}';$password = '{}';$secpwd = convertTo-secureString " \
                                   "$password -asplaintext -force ;$cred = new-object " \
                                   "System.Management.Automation.PSCredential -argumentlist $account," \
                                   "$secpwd ;Invoke-Command  -VMName '{}' -Credential $cred -ScriptBlock {{netsh advfirewall set allprofiles state off}} "
            disable_firewall_cmd = establish_ps_session.format(vm_account, vm_password, vm_name)

            self._common_content_lib.execute_sut_cmd("powershell {}".format(disable_firewall_cmd),
                                                     "DISABLE_FIREWALL_CMD", 60)
        except RuntimeError:
            self._log.error("Fail to disable firewall in VM!")
            raise
        self._log.info("Successfully disabled firewall in VM.")

    def _get_vm_memory_info(self, vm_name):
        """
        Method to get the startup memory size of the given VM

        :param vm_name: the name of given VM
        :raise: RunTimeError
        :return: memory info of the given VM in dict type.
                 Example: {'VMName': 'linux_VM1', 'DynamicMemoryEnabled': 'False', 'Minimum(M)': '512', 'Startup(M)': '2048', 'Maximum(M)': '1048576'}
        """
        try:
            get_vm_memory = self._common_content_lib.execute_sut_cmd(self.GET_VM_Memory_CMD.
                                                                     format(vm_name),
                                                                     "Get VM memory of: {}".format(vm_name), 60)
            self._log.info("Get VM memory:{}".format(get_vm_memory))
            str_list = get_vm_memory.split('\n')
            value_list = []
            for str in str_list:
                if str is not '' and '---' not in str:
                    res = re.finditer(r"\S+", str)
                    for match in res:
                        value_list.append(match.group())
            if len(value_list) is 0:
                raise RuntimeError("Invalid data\n")

            memory_dict = dict(zip(value_list[:int(len(value_list) / 2)], value_list[int(len(value_list) / 2):]))
            self._log.info("Get VM memory info:\n{}".format(memory_dict))
            return memory_dict
        except RuntimeError:
            raise

    def update_vm_memory_info(self, vm_name, memory_config):
        """
        Method to Update the VM memory configuration

        :param vm_name: the name of the given VM
        :param memory_config: updated VM memory value
        :raise: RunTimeError
        :return: None
        """
        try:
            self._log.info("Increase memory to {}GB on VM:{}".format(memory_config, vm_name))
            memory_info = self._common_content_lib.execute_sut_cmd(
                self.MODIFY_VM_MEMORY_COMMAND.format(self.SILENT_CONTINUE, vm_name, memory_config),
                "Update memory configuration", self._command_timeout)
            self._log.debug("{} command stdout\n{}".format(self.MODIFY_VM_MEMORY_COMMAND, memory_info))
            self._log.info("Successfully updated Memory configuration on VM:{}".format(vm_name))
            self._get_vm_memory_info(vm_name)
        except Exception as ex:
            self._log.error("Error while updating Memory configuration.{}".format(ex))
            raise ex

    def get_vm_list(self):
        """
        This method is to get the list of current VMs

        :return: a list which contains the names of current VMs
        :raise: RunTimeError
        """
        vm_list = []
        try:
            get_vm_result = self._common_content_lib.execute_sut_cmd(self.GET_VM_LIST_CMD,
                                                                     "Get VM list", 60)
            self._log.info("All available vm data  is:\n{}".format(get_vm_result))
            str_list = get_vm_result.split('\n')
            index = 0
            for str in str_list:
                if str is not '' and '---' not in str:
                    res = re.finditer(r"\S+", str)
                    for match in res:
                        if index is 0:
                            index = index + 1
                            break
                        vm_list.append(match.group())
                        break
        except RuntimeError:
            raise
        return vm_list

    def get_vm_info(self, vm_name):
        """
        This method is to get the vm info about the given VM

        :param vm_name: name of the VM
        :return: vm data with dict type which contains info about name, os_type, state, memory_info
        :raise: RunTimeError
        """
        try:
            vm_info_dict = {}
            # add vm_name into vm_info_dict
            vm_info_dict["name"] = vm_name
            # add os_type into vm_info_dict
            if "linux" in vm_name.lower():
                vm_info_dict["os_type"] = "linux"
            else:
                vm_info_dict["os_type"] = "windows"
            # add state into vm_info_dict
            vm_info_dict["state"] = self._get_vm_state(vm_name)
            # add number of cpus into vm_info_dict
            vm_info_dict["number_of_cpus"] = self._get_vm_num_of_cpus(vm_name)
            # add memory info into vm_info_dict
            vm_info_dict["memory_info"] = self._get_vm_memory_info(vm_name)
            self._log.info("Get vm info as below:\n{}\n".format(vm_info_dict))
            return vm_info_dict
        except RuntimeError:
            self._log.error("Fail to get VM data.\n")
            return None

    def copy_file_from_sut_to_vm(self, vm_name, vm_username, source_path, destination_path):
        """
        This method is to copy file from SUT to VM

        :raise: NotImplementedError
        """
        raise NotImplementedError

    def copy_file_to_vm_storage_device(self, disk_id, vm_os_obj, command_exec_obj):
        """
        This method is to copy the test file to VM USB from HOST

        :param disk_id: DiskNumber to get Drive volume details. ex: C:\ or E:\
        :param vm_os_obj: os object for VM
        :param command_exec_obj: OS object to execute command.
        """
        try:
            self._log.info("Copying the Test file to VM Storage Device")
            vm_test_file_host_path = self._install_collateral.download_tool_to_host("vm_test_file.txt")
            vm_os_obj.copy_local_file_to_sut(vm_test_file_host_path, self.VM_ROOT_PATH)
            vm_file_path = self.VM_ROOT_PATH + "\\" + self.TEST_VM_FILE_NAME
            command_exec_obj.execute_sut_cmd(
                self.SET_DISK_WRITABLE.format(self.SILENT_CONTINUE, disk_id),
                "Set disk ReadOnly False", self._command_timeout)
            get_device_partition = command_exec_obj.execute_sut_cmd(self.GET_DEVICE_PARTITION.format(
                self.SILENT_CONTINUE, disk_id), "Get Drive partition", self._command_timeout).strip()
            self._log.debug("{} command stdout\n{}".format(self.GET_DEVICE_PARTITION, get_device_partition))
            drives = re.findall("(DriveLetter.*)", get_device_partition)
            for drive in drives:
                letter_split = drive.split(": ")[1].strip()
                if letter_split.isalpha():
                    self._log.info("The drive letter is: ", letter_split)
                    storage_device_path = letter_split + ":" + "\\" + self.TEST_VM_FILE_NAME
                    copy_file_result = command_exec_obj.execute_sut_cmd(self.COPY_ITEM_CMD.format(
                        self.SILENT_CONTINUE, vm_file_path, storage_device_path),"Copy file to storage device",
                        self._command_timeout)
                    self._log.debug("{} command stdout\n{}".format(self.COPY_ITEM_CMD, copy_file_result))
                    return storage_device_path
        except Exception as ex:
            raise ("Could not copy file to VM storage device {}".format(ex))

    def copy_ssh_file_to_vm(self, vm_name, vm_account, vm_password, source_path, destination_path):
        """
        This method is to copy file from SUT to VM
        :param vm_name : name of the VM. ex: WINDOWS_1
        :param vm_account : VM admin account "Administrator"
        :param vm_password : VM password
        :param source_path : SSH file path in SUT
        :param destination_path: Destination path in VM
        :return : None

        :raise: NotImplementedError
        """
        try:
            self._log.info("Copying {} from SUT to VM".format(self.SSH_FILE_NAME))
            enable_vm_service = self._common_content_lib.execute_sut_cmd(
                self.ENABLE_VM_INTEGRATION_SERVICE_CMD.format(self.SILENT_CONTINUE, vm_name, self.GUEST_SERVICE_STR),
                "Enable Integration Service", self._command_timeout)
            copy_cmd = self._common_content_lib.execute_sut_cmd(
                self.COPY_COMMAND_TO_VM.format(self.SILENT_CONTINUE, vm_name, source_path, destination_path),
                "Copy File to VM", self._command_timeout)
            script_block = "{" + self.EXTRACT_FILE_STR.format(self.VM_SSH_FOLDER, self.VM_ROOT_PATH) + "}"
            extract_file = self.ESTABLISH_PS_SESSION.format(vm_account, vm_password, vm_name, script_block)
            command_result = self._common_content_lib.execute_sut_cmd(
                "powershell $progressPreference = 'silentlyContinue'; {}".format(extract_file), "Extracting File", self._command_timeout)
            self._log.debug(command_result)
            self._log.info("Successfully copied OpenSSH file & Extracted in VM.")
        except Exception as ex:
            raise ("Failed to Copy OpenSSH to VM! {}".format(ex))

    def install_opennssh_sut_win(self):
        """
        Install openssh using scheduler
        """
        cmd = '$dateTime = (Get-Date).AddSeconds(5).ToString(\\"h:mm:ss tt\\");' \
              '$taskAction = New-ScheduledTaskAction -Execute \\"powershell.exe\\" -Argument \\"Add-WindowsCapability ' \
              '-Online -Name OpenSSH.Server~~~~0.0.1.0\\";$taskTrigger = New-ScheduledTaskTrigger -Once -At $dateTime;' \
              '$taskName = \\"OpenSSHInstall\\";$description = \\"Install OpenSSH Server\\";' \
              'Unregister-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue -Confirm:$false;' \
              'Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger $taskTrigger ' \
              '-Description $description;'
        try:
            command_result = self._common_content_lib.execute_sut_cmd(
                'powershell.exe {}; {}'.format(self.SILENT_CONTINUE, cmd),
                "executing {}".format(cmd), self._command_timeout)
            self._log.debug(command_result)
            self._log.info(command_result)
        except:
            self._log.error(command_result)
            self._log.info(command_result)
            pass
        time.sleep(5)
        cmd1 = 'Start-Service sshd;' \
               'Set-Service -Name sshd -StartupType \\"Automatic\\";' \
               'New-NetFirewallRule -Name \\"OpenSSH-Server-In-TCP\\" -DisplayName \\"OpenSSH Server (sshd)\\" -Enabled True ' \
               '-Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 -ErrorAction SilentlyContinue;'
        try:
            command_result = self._common_content_lib.execute_sut_cmd(
                'powershell.exe {}; {}'.format(self.SILENT_CONTINUE, cmd1),
                "executing {}".format(cmd1), self._command_timeout)
            self._log.debug(command_result)
            self._log.info(command_result)
        except:
            self._log.error(command_result)
            self._log.info(command_result)
            pass
        time.sleep(5)

    def copy_ssh_package_to_windows_sut(self):
        """
        This method used to copy openSSH zip file to the windows SUT.

        :return:ssh_file_path_host : SSH folder path in Windows SUT
        """
        self._log.info("copying open-ssh zip file from Host to SUT...")
        ssh_file_path = self._install_collateral.download_tool_to_host("OpenSSH-Win64.zip")
        self.os.copy_local_file_to_sut(ssh_file_path, self.SSH_PATH)
        self._log.info("Successfully copied the open-ssh  file to SUT")
        host_file_path = self.SSH_PATH+self.SSH_STR
        return host_file_path

    def _enable_ssh_in_vm(self, vm_name, vm_account, vm_password, copy_open_ssh=True):
        """
        This method is used to enable SSH in VM.

        :param vm_name : name of the VM. ex: WINDOWS_1
        :param vm_account : VM admin account "Administrator"
        :param vm_password : VM password
        :param copy_open_ssh : To copy open SSh tool to VM
        :return : None
        """
        try:
            vm_ip = self.get_vm_ip(vm_name)
            self._log.info("Enabling SSH in VM : {}...".format(vm_name))
            if copy_open_ssh:
                host_path = self.copy_ssh_package_to_windows_sut()
                # # Copy SSH Zip file from SUT to VM
                self.copy_ssh_file_to_vm(vm_name, vm_account, vm_password, host_path, self.VM_SSH_FOLDER)
            run_ssh_cmd = self.ESTABLISH_PS_SESSION.format(vm_account, vm_password, vm_name, self.SSH_FILE)
            start_ssh = self.ESTABLISH_PS_SESSION.format(vm_account, vm_password, vm_name, self.START_SERVICE_SSHD_CMD)
            set_ssh_service = self.ESTABLISH_PS_SESSION.format(vm_account, vm_password, vm_name, self.SET_SERVICE_CMD)
            get_ssh_name = self.ESTABLISH_PS_SESSION.format(vm_account, vm_password, vm_name, self.GET_SSH_NAME_CMD)
            enable_ssh_cmd = self.ESTABLISH_PS_SESSION.format(vm_account, vm_password, vm_name, self.DISPLAY_SSH_CMD)
            ssh_commands_list = [run_ssh_cmd, start_ssh, set_ssh_service, get_ssh_name, enable_ssh_cmd]
            for each_command in ssh_commands_list:
                try:
                    command_result = self._common_content_lib.execute_sut_cmd(
                        "powershell.exe {}; {}".format(self.SILENT_CONTINUE, each_command),
                        "executing {}".format(each_command), self._command_timeout)
                    self._log.debug(command_result)
                except:
                    pass
                time.sleep(self.COMMON_TIMEOUT)
                self._log.info("Successfully Enabled SSH in VM : {}...".format(vm_name))

        except Exception as ex:
            raise ("Error while enabling SSH in VM : {}...".format(ex))

    def _install_ini_in_vm(self, vm_name, vm_account, vm_password):
        """
        This method is used to install driver in VM.

        :param vm_name : name of the VM. ex: WINDOWS_1
        :param vm_account : VM admin account "Administrator"
        :param vm_password : VM password
        :return : None
        """
        try:
            self._log.info("Installing driver in VM : {}...".format(vm_name))
            ssh_folder_path = self._common_content_configuration.get_driver_folder_path()

            self.DRIVER_FILE = "{" + ssh_folder_path + "\\pnputil /add-driver i40e /install" "}"
            install_driver_cmd = self.ESTABLISH_PS_SESSION.format(vm_account, vm_password, vm_name,
                                                                  self.DRIVER_FILE)

            driver_commands_list = [install_driver_cmd, install_driver_cmd]
            for each_command in driver_commands_list:
                try:
                    command_result = self._os.execute("powershell {}".format(each_command), self._command_timeout)
                    self._log.debug(command_result.stdout)
                except:
                    pass

                time.sleep(self.COMMON_TIMEOUT)

        except Exception as ex:
            raise ("Error while installing driver in VM : {}...".format(ex))

    def enumerate_storage_device(self, bus_type, index_value, command_exec_obj):
        """
        This method is to list all available storage device on SUT.

        :param bus_type: Storage Device type. ex: NVMe, USB
        :param index_value: Index value for Disk
        :param command_exec_obj: Command executable OS object. ex: SUT or VM object.
        :return: device_list
        """
        self._log.info("{} Device list info".format(bus_type))
        device_list = command_exec_obj.execute_sut_cmd(
            self.STORAGE_DEVICE_LIST_CMD.format(self.SILENT_CONTINUE, bus_type, "Online"), "Get Disk",
            self._command_timeout)
        self._log.debug("{} command stdout\n{}".format(self.STORAGE_DEVICE_LIST_CMD, device_list))
        disk_number = re.findall("DiskNumber.*", device_list)[0]
        self._log.info(disk_number)
        disk_id = disk_number.split(": ")[1]
        self._log.info("Selected Disk ID : {}".format(disk_id))
        return disk_id

    def set_disk_offline(self, disk_id, command_exec_obj):
        """
        This method is to set disk offline for Storage passthrough.

        :param disk_id: Storage Device id.
        :param command_exec_obj: Object to execute commands. Ex : Sut object or Vm object
        :return: None
        """
        try:
            self._log.info("Set Disk: {} to offline state to enable device sharing".format(disk_id))
            command_exec_obj.execute_sut_cmd(
                self.SET_DISK_OFFLINE_CMD.format(self.SILENT_CONTINUE, disk_id), "Set Disk Offline",
                self._command_timeout)
            get_device_status = command_exec_obj.execute_sut_cmd(
                self.GET_DISK_STATUS.format(self.SILENT_CONTINUE, disk_id), "Get Disk Status",
                self._command_timeout)
            self._log.debug("{} command stdout\n{}".format(self.GET_DISK_STATUS, get_device_status))
            if self.DISK_STATUS in get_device_status:
                return RuntimeError("Failed to set Disk:{} Offline.".format(disk_id))
            self._log.info("Set Disk offline successful on DiskNumber:{}".format(disk_id))

        except Exception as ex:
            self._log.error("Error while setting Disk:{} to offline State".format(ex))
            raise ex

    def set_disk_online(self, disk_id, command_exec_obj):
        """
        This method is to set disk offline for Storage passthrough.

        :param disk_id: Storage Device id.
        :param command_exec_obj: Object to execute commands. Ex : Sut object or Vm object
        :return: None
        """
        self._log.info("Set Disk: {} online to access from file explorer".format(disk_id))
        try:
            command_exec_obj.execute_sut_cmd(
                self.SET_DISK_ONLINE_CMD.format(self.SILENT_CONTINUE, disk_id), "Set Disk Online",
                self._command_timeout)
            get_device_status = command_exec_obj.execute_sut_cmd(
                self.GET_DISK_STATUS.format(self.SILENT_CONTINUE, disk_id), "Get Disk Status",
                self._command_timeout)
            self._log.debug("{} command stdout\n{}".format(self.GET_DISK_STATUS, get_device_status))
            if self.DISK_STATUS not in get_device_status:
                return RuntimeError("Failed to set Disk:{} Online.".format(disk_id))
            self._log.info("Set Disk Online successful on DiskNumber:{}".format(disk_id))
        except Exception as ex:
            self._log.error("Error while setting Disk to Online State".format(ex))
            raise ex

    def add_storage_device_to_vm(self, vm_name, vm_disk_name, storage_size):
        """
        This method is add additional storage device to VM

        :param vm_name: name of the VM
        :param vm_disk_name: disk name going to attach to the VM
        :param storage_size: size of the storage device to add in GB
        :return: None
        """
        vm_state = self._get_vm_state(vm_name)
        if self.VM_STATE_STR == vm_state:
            self._log.info("{} is in Running state. Powering Off VM...\n".format(vm_name))
            self._shutdown_vm(vm_name)
            # wait for vm to shutdown
            time.sleep(self.COMMON_TIMEOUT)
        try:
            attach_storage_device = self._common_content_lib.execute_sut_cmd(
                self.ATTACH_STORAGE_DEVICE_TO_VM.format(self.SILENT_CONTINUE, vm_name,
                                                        self.SCSI_TYPE_STR, vm_disk_name),
                "Attach Storage Device", self._command_timeout)
        except Exception as ex:
            raise ("Unable to add storage device to VM {}".format(ex))

    def remove_storage_device_from_vm(self, vm_name):
        """
        This method is add additional storage device to VM

        :param vm_name: name of the VM
        :return: None
        """
        vm_state = self._get_vm_state(vm_name)
        if self.VM_STATE_STR == vm_state:
            self._log.info("{} is in Running state. Powering Off VM...\n".format(vm_name))
            self._shutdown_vm(vm_name)
            # wait for vm to shutdown
            time.sleep(self.COMMON_TIMEOUT)
        try:
            self._common_content_lib.execute_sut_cmd(self.DETACH_STORAGE_DEVICE_TO_VM.format
                                                     (self.SILENT_CONTINUE, vm_name, self.SCSI_TYPE_STR),
                "Detach Storage Device", self._command_timeout)
        except Exception as ex:
            raise ("Unable to Detach storage device to VM {}".format(ex))

    def suspend_vm(self, vm_name):
        """
        This method is to suspend the existing VM

        :param vm_name: Name of the VM
        """
        raise NotImplementedError

    def resume_vm(self, vm_name):
        """
        This method is to resume the suspended VM

        :param vm_name: Name of the VM
        """
        raise NotImplementedError

    def save_vm_configuration(self, vm_name):
        """
        This method will save the VM configuration into a XML file

        :param vm_name: Name of the VM
        :return: complete_vm_config_file
        """
        raise NotImplementedError

    def restore_vm_configuration(self, vm_name, vm_config_file):
        """
        This method will restore the VM from configuration file

        :param vm_name: Name of the VM
        :param vm_config_file: Previously saved VM configuration file with path
        """
        raise NotImplementedError

    def attach_usb_device_to_vm(self, usb_data_dict, vm_name):
        """
        This method is to attach the usb device to the vm

        :param usb_data_dict: dictionary data should contain vendor id and product id
        :param vm_name: name of the VM
        :return :None
        """
        raise NotImplementedError

    def detach_usb_device_from_vm(self, vm_name):
        """
        This method is to detach the usb device from VM.

        :param vm_name: name of the VM
        :return: None
        """
        raise NotImplementedError

    def install_vm_tool(self):
        """
        This method is to install all the dependency tools for VM creation

        :return: None
        """
        self._log.info("Enabling Hyper-V role")
        enable_cmd_result = self._common_content_lib.execute_sut_cmd(self.ENABLE_HYPER_V_CMD, "install hyper-v "
                                                                                              "command",
                                                                     self._command_timeout)
        self._log.debug("Enable Hyper-V command stdout\n{}".format(enable_cmd_result))
        self._log.info("Hyper-V role is enabled successfully")
        if not self._is_hyper_v_installed():
            self._log.info("Hyper-V module is not installed, installing it")
            install_cmd_result = self._common_content_lib.execute_sut_cmd(self.INSTALL_HYPER_V_MODULES,
                                                                          "install hyper-v command",
                                                                          self._command_timeout)
            self._log.debug("install Hyper-V command stdout\n{}".format(install_cmd_result))
            if "True" not in install_cmd_result:
                raise RuntimeError("Failed to install Hyper-V module")
        # rebooting the SUT as after enable and installation of Hyper-V module SUT required a must reboot
        self._common_content_lib.perform_os_reboot(self._reboot_timeout)
        if not self._is_hyper_v_installed():
            raise RuntimeError("Hyper-V module is not installed")
        self._log.info("Hyper-V module is installed successfully ")
        return True

    def install_kvm_vm_tool(self):
        """
        This method is to install all the dependency tools for VM creation

        :return: None
        """
        self._log.info("Enabling RHEL-KVM role")
        enable_cmd_result = self._common_content_lib.execute_sut_cmd(self.ENABLE_HYPER_V_CMD, "install RHEL KVM"
                                                                                              "command",
                                                                     self._command_timeout)
        self._log.debug("Enable Rhel KVM command stdout\n{}".format(enable_cmd_result))
        self._log.info("Rhel KVM role is enabled successfully")
        if not self._is_hyper_v_installed():
            self._log.info("RHEL KVM module is not installed, installing it")
            install_cmd_result = self._common_content_lib.execute_sut_cmd(self.INSTALL_HYPER_V_MODULES,
                                                                          "install RHEL KVM command",
                                                                          self._command_timeout)
            self._log.debug("install RHEL KVM command stdout\n{}".format(install_cmd_result))
            if "True" not in install_cmd_result:
                raise RuntimeError("Failed to install RHEL KVMmodule")
        # rebooting the SUT as after enable and installation of RHEL_KVM module SUT required a must reboot
        self._common_content_lib.perform_os_reboot(self._reboot_timeout)
        if not self._is_hyper_v_installed():
            raise RuntimeError("RHEL KVM module is not installed")
        self._log.info("RHEL KVM module is installed successfully ")
        return True

    def _is_hyper_v_installed(self):
        """
        This method is to verify Hyper-V module is installed or not

        :return : True if Hyper-V module is installed else False
        """
        self._log.info("Verifying Hyper-V is installed or not")
        install_module_data = self._common_content_lib.execute_sut_cmd(self.GET_HYPER_V_INSTALLED_CMD,
                                                                       "is hyper-v install"
                                                                       "command", self._command_timeout)
        self._log.debug("{} command stdout\n{}".format(self.GET_HYPER_V_INSTALLED_CMD, install_module_data))
        if self.NEW_VM_STR not in install_module_data:
            self._log.error("Hyper-V module is not installed")
            return False
        self._log.info("Hyper-V module is installed")
        return True

    def set_automatic_stop_action(self, vm_name, stop_action_type="TurnOff"):
        """
        This method is to set the Automatic stop Action.

        :param vm_name
        :param stop_action_type - TurnOff (pulling plug- Removing cable), Save, and ShutDown ( Software-OS shut down)
        """
        vm_state = self._get_vm_state(vm_name=vm_name)
        if self.VM_STATE_STR in vm_state:
            self._log.info("VM -{} state is - {}".format(vm_name, vm_state))
            self.turn_off_vm(vm_name)
        time.sleep(15)
        automatic_stop_action_output = self._common_content_lib.execute_sut_cmd(
            self.SET_HYPER_V_VM_AUTOMATIC_STOP_ACTION_CMD.format(vm_name, stop_action_type),
            self.SET_HYPER_V_VM_AUTOMATIC_STOP_ACTION_CMD.format(vm_name, stop_action_type), self._command_timeout
        )
        if "" is not automatic_stop_action_output:
            raise content_exceptions.TestFail("Unable to set Automatic Stop Action for VM - {} with type- {}".format(
                vm_name, stop_action_type))
        self._log.info("Automatic Stop Action Set for VM- {} with type- {}".format(vm_name, stop_action_type))
        self.start_vm(vm_name)

    def turn_off_vm(self, vm_name):
        """
        This method is to Turn OFF VM (turn off is non graceful shutdown (similar to removing power plug).

        :param vm_name
        """
        self._log.info("TurnOff VM- {}".format(vm_name))
        turn_off_vm_result = self._common_content_lib.execute_sut_cmd(self.TURNOFF_VM_CMD.format(vm_name),
                                                                      self.TURNOFF_VM_CMD.format(vm_name),
                                                                      self._command_timeout)
        print(turn_off_vm_result)
        if "" is not turn_off_vm_result:
            raise content_exceptions.TestFail("Unable to TurnOff the VM - {}".format(vm_name))
        self._log.info("Successfully TurnOff the VM {}".format(vm_name))


    def import_vm(self, source_path=None, destination_path=None):
        """Method to import VM.
        :param source_path: path on the SUT to the VM template image.
        :type: str
        :param destination_path: path on the SUT to where the new VM image will be.
        :type: str
        """
        if source_path is None or destination_path is None:
            content_exceptions.TestSetupError("VM import source or destination path was not provided.  Source: {}, "
                                              "Destination: {}".format(source_path, destination_path))
        import_cmd = self.IMPORT_VM_FROM_COPY.format(source_path, destination_path)
        import_vm_result = self._common_content_lib.execute_sut_cmd(import_cmd,
                                                                    "import-vm powershell command",
                                                                    self._command_timeout)
        self._log.debug("Import-VM command: {}".format(import_vm_result))
        if "Operating normally" not in import_vm_result:
            raise content_exceptions.TestError("Import-VM failed for source path {}.".format(source_path))

    def rename_vm(self, current_vm_name=None, new_vm_name=None):
        """Method to rename VM.
        :param current_vm_name: Current VM name.
        :type: str
        :param new_vm_name: New VM name.
        :type: str"""
        self._common_content_lib.execute_sut_cmd(self.RENAME_VM.format(current_vm_name, new_vm_name),
                                                 "rename-vm command", self._command_timeout)

    def apply_checkpoint(self, vm_name=None, checkpoint_name=None):
        """Method to apply a stored checkpoint for a named VM.
        :param vm_name: Name of the VM to which the checkpoint will be applied.
        :type: str
        :param checkpoint_name: name of the checkpoint to apply to the VM.
        :type: str"""
        if vm_name is None:
            raise RuntimeError("No VM name specified to apply checkpoint!")
        if checkpoint_name is None:
            self._log.warning("No checkpoint name was specified; if there is only 1 checkpoint for the VM, it will be "
                              "applied.")
            checkpoint_name = self._common_content_lib.execute_sut_cmd(self.GET_CHECKPOINTS.format(vm_name),
                                                                       "Get VM checkpoints PS command",
                                                                       self._command_timeout).strip()
        self._common_content_lib.execute_sut_cmd(self.APPLY_CHECKPOINT.format(checkpoint_name, vm_name),
                                                 "Restore VM checkpoint", self._command_timeout)

    def delete_checkpoint(self, vm_name=None, checkpoint_name=None):
        """Method to delete a stored checkpoint for a named VM.
        :param vm_name: Name of the VM to which the checkpoint will be deleted.
        :type: str
        :param checkpoint_name: name of the checkpoint to apply to the VM.
        :type: str"""
        if vm_name is None:
            raise RuntimeError("No VM name specified to apply checkpoint!")
        if checkpoint_name is None:
            self._log.warning("No checkpoint name was specified; if there is only 1 checkpoint for the VM, it will be "
                              "deleted.")
            checkpoint_name = self._common_content_lib.execute_sut_cmd(self.GET_CHECKPOINTS.format(vm_name),
                                                                       "Get VM checkpoints PS command",
                                                                       self._command_timeout).strip()
        if len(checkpoint_name) != 0:
            self._common_content_lib.execute_sut_cmd(self.REMOVE_CHECKPOINT.format(checkpoint_name, vm_name),
                                                 "Delete VM checkpoint", self._command_timeout)

    def get_network_bridge_list(self):
        """Retrieves list of VM switches registered into Hyper-V.
        :return: List of VM switches
        :rtype: str"""
        return self._common_content_lib.execute_sut_cmd(self.GET_VM_SWITCH, "Get VM switch PS command",
                                                        self._command_timeout).strip()

    def set_boot_order(self, vm_name=None, boot_device_type=None):
        """Set boot order of a VM.
        :param vm_name: Name of the VM to change the boot order.
        :type: str
        :param boot_device_type: Type of device to use as boot device.  Expected values are: VMBootSource,
        VMNetworkAdapter,HardDiskDrive,DVDDrive.
        :type: str"""
        device_cmd = ""
        if boot_device_type.lower() == "harddiskdrive":
            """Setting the boot order requires a specific objet type from PowerShell.  Returning this with an 
            independent command from SutOsProvider ruins the context of this object, so the command must be embedded 
             within the "Set-VMFirmware" command.  These two strings are parsing the existing Get-VHDHardDiskDrive 
             implementation and embedding it into a PowerShell command to set the FW order."""
            get_disk_drive_cmd = self.GET_VM_VHDPATH_CMD.split(" ", 1)[1].format(vm_name)
            device_cmd = "$({})".format(get_disk_drive_cmd)
        else:
            raise NotImplementedError("Support for boot device type {} is not yet "
                                      "implemented.".format(boot_device_type))
        if device_cmd == "":
            raise RuntimeError("Valid device type was not provided to set boot order.")
        self._common_content_lib.execute_sut_cmd(self.SET_BOOT_ORDER_CMD.format(vm_name, device_cmd),
                                                 "Setting Boot Order", self._command_timeout)
    def assign_static_ip_to_vm(self, vm_name, user_name, password, static_ip=None, gateway_ip=None, subnet_mask=None):
        """
        This method is used to assign static ip to the VM
        :param vm_name: name of given VM
        :param user_name: user account for the VM
        :param password: password for the VM account
        :param static_ip: ip address of VM
        :param gateway_ip: gateway ip address
        :param subnet_mask: subnet mask

        :return None
        :raise RunTimeError
        """
        get_adapter = "{netsh interface show interface}"
        assign_static_ip_cmd = 'netsh interface ipv4 set address name=\'{}\' static {} {} {}'
        get_adapter_ip = "{ipconfig}"
        wait_for_ip_assignment_in_sec = 10
        get_adapter_cmd = self.ESTABLISH_PS_SESSION.format(user_name, password, vm_name, get_adapter)
        get_adapter_output = self._common_content_lib.execute_sut_cmd("powershell {}".format(get_adapter_cmd),
                                                                     "get VM adapter", self._command_timeout)
        self._log.info(get_adapter_output)
        network_interface_value = re.findall(r".*Connected.*", get_adapter_output, re.MULTILINE)
        if network_interface_value:
            network_interface_list = [interface.split("  ")[-1] for interface in network_interface_value]
        else:
            raise RuntimeError("Network interface in VM were not in connected state")
        if static_ip:
            self._log.info("Assigning Static IP {} to Network Adapter Interfaces {} in {}".format(static_ip, network_interface_list[0], vm_name))
            assign_ip = assign_static_ip_cmd.format(network_interface_list[0], static_ip, subnet_mask, gateway_ip)
            assign_vm_static_ip_cmd = self.ESTABLISH_PS_SESSION.format(user_name, password, vm_name, "{" + assign_ip + "}")
            self._common_content_lib.execute_sut_cmd("powershell {}".format(assign_vm_static_ip_cmd), "Assigning Static IP", self._command_timeout)
            time.sleep(wait_for_ip_assignment_in_sec)
            self._log.info("Check the VM ip address")
            get_ip =  self.ESTABLISH_PS_SESSION.format(user_name, password, vm_name, get_adapter_ip)
            check_ip = self._common_content_lib.execute_sut_cmd("powershell {}".format(get_ip), "get adapter IP", self._command_timeout)
            self._log.info("VM adapters ip are \n{}".format(check_ip))
            ip_value = re.findall(r"IPv4\sAddress.*:.*", check_ip, re.MULTILINE | re.IGNORECASE)
            ip_list = [ip_address.split(":")[-1].strip() for ip_address in ip_value]
            if static_ip in ip_list:
                self._log.info("{} is configured succesfully with ip {}".format(vm_name, static_ip))
            else:
                raise RuntimeError("{} expected ip {} but assigned ip {}".format(vm_name, static_ip, ip_list))

    def copy_package_to_VM(self, vm_name, vm_account, vm_password, package_name, destination_path):
        """
        This method is to copy file from SUT to VM
        :param vm_name : name of the VM. ex: WINDOWS_1
        :param vm_account : VM admin account "Administrator"
        :param vm_password : VM password
        :param destination_path: Destination path in VM
        :param package_name : Name of the package to be copied to VM
        :return : pakage path on VM

        :raise: RuntimeError
        """
        try:
            self._log.info("Copying {} to SUT".format(package_name))
            host_file_path = self._install_collateral.download_tool_to_host(package_name)
            self.os.copy_local_file_to_sut(host_file_path, Framework.CFG_BASE[OperatingSystems.WINDOWS])
            self._log.info("Successfully copied the {}  file to SUT".format(package_name))
            source_path = Framework.CFG_BASE[OperatingSystems.WINDOWS] + package_name

            self._log.info("Copying {} from SUT to VM".format(package_name))
            enable_vm_service = self._common_content_lib.execute_sut_cmd(
                self.ENABLE_VM_INTEGRATION_SERVICE_CMD.format(self.SILENT_CONTINUE, vm_name, self.GUEST_SERVICE_STR),
                "Enable Integration Service", self._command_timeout)
            copy_cmd = self._common_content_lib.execute_sut_cmd(
                self.COPY_COMMAND_TO_VM.format(self.SILENT_CONTINUE, vm_name, source_path, destination_path),
                "Copy File to VM", self._command_timeout)
            script_block = "{" + self.EXTRACT_FILE_STR.format(self.VM_ROOT_PATH + package_name, self.VM_ROOT_PATH) + "}"
            extract_file = self.ESTABLISH_PS_SESSION.format(vm_account, vm_password, vm_name, script_block)
            command_result = self._common_content_lib.execute_sut_cmd(
                "powershell {}".format(extract_file), "Extracting File", self._command_timeout)
            self._log.debug(command_result)
            package_path = self.VM_ROOT_PATH + package_name.replace(".zip", "")
            self._log.info("Successfully copied {} & Extracted in VM under {}".format(package_name, package_path))
            return package_path
        except Exception as ex:
            raise RuntimeError("Failed to Copy {} to VM! {}".format(package_name, ex))

    def start_iperf_on_vm(self, vm_name, vm_account, vm_password, iperf_cmd, iperf_path):
        """
        This method is used to start iperf on vm

        :param vm_name: name of given VM
        :param vm_account: user account for the VM
        :param vm_password: password for the VM account
        :param iperf_cmd: iperf command to execute on VM
        :param iperf_path: path where command to run

        :return None
        :raise RuntimeError
        """
        # set iperf to the Environment variable
        set_environment_variable = "{" + 'setx Path "{}"'.format(iperf_path) + "}"
        set_iperf_env_variable = self.ESTABLISH_PS_SESSION.format(vm_account, vm_password, vm_name, set_environment_variable)
        command_result = self._common_content_lib.execute_sut_cmd(
            "powershell {}".format(set_iperf_env_variable), "Setting environment variable", self._command_timeout)
        self._log.debug(command_result)

        # Start the iperf session
        iperf_cmd_vm = self.ESTABLISH_PS_SESSION.format(vm_account, vm_password, vm_name, iperf_cmd)
        self._stress_provider_obj.execute_async_stress_tool("powershell {}".format(iperf_cmd_vm), "iperf3.exe")

        # Check does iperf is triggered on VM
        if not self.check_application_status(vm_name, vm_account, vm_password, "iperf3.exe"):
            raise RuntimeError("iperf fail to start on VM {}".format(vm_name))

    def check_application_status(self, vm_name, vm_account, vm_password, app_name):
        """
        This method is used to check the status of an application on VM

        :param vm_name: name of given VM
        :param vm_account: user account for the VM
        :param vm_password: password for the VM account
        :param app_name: application to be checked

        :return: Boolean
        """
        current_running_process_cmd = self.ESTABLISH_PS_SESSION.format(vm_account, vm_password, vm_name, "{TASKLIST}")
        current_running_process_result = self._common_content_lib.execute_sut_cmd(
            "powershell {}".format(current_running_process_cmd), "{} status".format(app_name), self._command_timeout)
        self._log.debug(current_running_process_result)
        if not app_name in current_running_process_result:
            return False
        self._log.info("{} application is ruuning on VM {}".format(app_name, vm_name))
        return True

    def remove_network_adapter(self, switchname):
        """
        This method is used to remove the network adapter from SUT

        :param switchname : network adapter interface to be removed
        :return None
        """
        try:
            self._common_content_lib.execute_sut_cmd(
                self.REMOVE_VM_SWITCH_COMMAND.format(self.SILENT_CONTINUE, switchname), "Remove vswitch",
                self._command_timeout)
            self._log.info("Successfully destroyed vSwitch:{}".format(switchname))
        except Exception as ex:
            self._log.error("SUT will lose its network connectivity while creating or destroying vSwitch. Ignoring this"
                            "exception '{}'...".format(ex))

    def assign_static_ip_to_sriov_vf_vm(self, common_content_lib_vm, nic_name, static_ip=None, gateway_ip=None):
        """
        This method is used to assign static ip to the ethernet
        :param ip_address: name of given ethernet
        :param interface_index: interface_index for the ethernet
        :param addr_type: type of address - IPv4 or Ipv6

        :return None
        :raise RunTimeError
        """
        try:
            interface_id = common_content_lib_vm.execute_sut_cmd(
                self.GET_NET_ADAPTER_INTERFACE_INDEX_CMD.format(self.SILENT_CONTINUE, nic_name),
                "Getting interface id for Ethernet", self._command_timeout)
            common_content_lib_vm.execute_sut_cmd(
                self.ASSIGN_IP_ADDRESS.format(self.SILENT_CONTINUE, static_ip, interface_id, gateway_ip),
                self.ASSIGN_IP_ADDRESS.format(self.SILENT_CONTINUE, static_ip, interface_id, gateway_ip),
                self._command_timeout)
            self._log.info("Successfully assigned ip: {} to the ethernet".format(static_ip))
        except Exception as ex:
            raise Exception("Error occurred while assigning ip address to the ethernet. Exception '{}'...".format(ex))

    def enable_sriov(self, network_device_name):
        """
        This method is used to enable sriov
        :param network_device: network device name

        :return None
        :raise RunTimeError
        """
        try:
            vswitch_out = self._common_content_lib.execute_sut_cmd(self.VSWITCH_NAME.format(network_device_name),
                                                                   "Executing regedit command", self._command_timeout)
            vswitch_out = vswitch_out.split("-")[0].strip()
            self._common_content_lib.execute_sut_cmd(self.ENABLE_SRIOV.format(vswitch_out), "Enable SRIOV",
                                                     self._command_timeout)
        except Exception as ex:
            raise Exception("Error Occurred while enabling SRIOV: {}".format(ex))

    def get_sriov_network_adapter_in_vm(self, common_content_lib_vm, mac_id):
        """
        This method is used to get the sriov network adapter name in VM.

        :param common_content_lib_vm: common content lib VM object
        :param mac_id: Mac id of the NIC
        :return:
        """
        try:
            self._log.info("Fetching sriov internet adapter on VM using mac id : {}".format(mac_id))
            vm_sriov_adapter = common_content_lib_vm.execute_sut_cmd(self.GET_VM_SRIOV_ADAPTER.format(
                self.SILENT_CONTINUE), "Get VM SRIOV Nic name", self._command_timeout)
            regex_pattern = ".+\s*{}".format(mac_id)
            sriov_adapter = re.findall(regex_pattern, vm_sriov_adapter)
            display_name = (re.sub('\s\s+', '*', sriov_adapter[0])).split('*')
            return display_name[0]
        except Exception as ex:
            raise Exception("Error Occurred while fetching SRIOV nic name in VM: {}".format(ex))

    def execute_reg_edit(self):
        """
        This method is used to execute the reg edit command.

        :return: None
        """
        try:
            self._common_content_lib.execute_sut_cmd(self.REGEDIT_CMD, "Executing regedit command",
                                                     self._command_timeout)
        except Exception as ex:
            raise Exception("Error Occurred while executing regedit command: {}".format(ex))

    def start_net_vmms(self):
        """
        This method is used to start the vmms service.

        :return: None
        """
        try:
            self._common_content_lib.execute_sut_cmd(self.NET_VMMS_CMD.format("start"), "start vm",
                                                     self._command_timeout)
        except Exception as ex:
            raise Exception("Error Occurred while starting VMMS: {}".format(ex))

    def stop_net_vmms(self):
        """
        This method is used to stop the vmms service.

        :return: None
        """
        try:
            self._common_content_lib.execute_sut_cmd(self.NET_VMMS_CMD.format("stop"), "stop vm", self._command_timeout)
        except Exception as ex:
            raise Exception("Error Occurred while stopping VMMS: {}".format(ex))

    def enable_vm_integration_service(self, vm_name):
        """
        This method is used to enable the vm integration service

        :param vm_name:
        :return:
        """
        try:
            self._common_content_lib.execute_sut_cmd(self.VM_INTEGRATION_SERVICE.format(vm_name),
                                                     "Enabling VM Integration service", self._command_timeout)
        except Exception as ex:
            raise Exception("Error Occurred while Enabling VM Integration service: {}".format(ex))

    def get_adapter_name_and_create_vswitch_for_sriov(self, switch_name, vm_physical_adapter, no_of_iov):
        """
        This method is used to fetch the adapter name for SRIOV.

        :param switch_name:
        :param vm_physical_adapter:
        :return: None
        """
        try:
            self._common_content_lib.execute_sut_cmd(self.GET_NET_ADAPTER_SRIOV.format(self.SILENT_CONTINUE, vm_physical_adapter),
                                                     "fetching the adapter name for SRIOV", self._command_timeout)
            self._common_content_lib.execute_sut_cmd(self.NEW_VM_SWITCH_WITH_SRIOV.format(self.SILENT_CONTINUE,
                switch_name, vm_physical_adapter, no_of_iov), "fetching the adapter name for SRIOV", self._command_timeout)
        except Exception as ex:
            raise Exception("Error Occurred while fetching the adapter name for SRIOV: {}".format(ex))

    def add_sriov_ethernet_adapter_to_vm(self, vm_name, sriov_switch, mac_addr=None):
        """
        Method to add network adapter for given VM.

        :param vm_name: Name of the VM.
        :raise: RunTimeError. It will the error caught when executing the GET_VM_NETWORK_ADAPTER_CMD.
        :return: None
        """
        try:
            vm_state = self._get_vm_state(vm_name)
            if self.VM_STATE_STR == vm_state:
                self._log.info("{} is in Running state. Powering Off VM...\n".format(vm_name))
                self._shutdown_vm(vm_name)
                # wait for vm to shutdown
                time.sleep(self.COMMON_TIMEOUT)
            # add vm network adapter
            sriov_adapter_name = "adapter_for_{}".format(sriov_switch)
            add_vm_network_adapter = self._common_content_lib.execute_sut_cmd(
                self.ADD_VM_NETWORK_ADAPTER_CMD.format(self.SILENT_CONTINUE, vm_name, sriov_adapter_name, sriov_switch),
                "Add vm network adapter", self.VSWITCH_TIME)
            self._log.debug("Network Adapter stdout:\n{}".format(add_vm_network_adapter))
            self._log.info("Successfully added SRIOV network adapter to VM")
            self._common_content_lib.execute_sut_cmd(
                self.SET_SRIOV_VM_NETWORK_ADAPTER.format(self.SILENT_CONTINUE, vm_name, sriov_adapter_name),
                "Set SRIOV vm network adapter", self.VSWITCH_TIME)
            if mac_addr:
                self._log.info("Assigning mac {} to network adapter {}".format(mac_addr, sriov_adapter_name))
                assign_mac_id = self._common_content_lib.execute_sut_cmd(
                    self.ASSIGN_MAC_ID.format(self.SILENT_CONTINUE, vm_name, sriov_adapter_name, mac_addr),
                    "Assigning Mac ID to Adapter", self._command_timeout)
            self._log.info("Successfully Set SRIOV network adapter to VM")
            vm_state = self._get_vm_state(vm_name)
            if vm_state.lower() != "running":
                self._log.info("{} is not in Running state. Powering On VM...\n".format(vm_name))
                self.start_vm(vm_name)
                # wait for vm to shutdown
                time.sleep(self.COMMON_TIMEOUT)
        except Exception as ex:
            raise ("Fail to set network adapter SRIOV!\n {}".format(ex))

    def configure_mac_id_for_sriov_vf(self):
        """
        This method is used to set the MAC id for the SRIOV VF
        :return: Mac id List
        """
        mac_counter = 0
        mac_id = self.TEMPLATE_MAC_ID
        mac_id_list = []
        if mac_counter != 0:
            increment = str(int(mac_id[-2:]) + 1)
            mac_id = mac_id[:-2] + increment.zfill(2)
        self._log.info("mac id info:\n{}".format(mac_id))
        mac_counter = mac_counter + 1
        mac_id_list.append(mac_id)
        return mac_id_list

    def set_nic_device_naming_on_vm(self, vm_name, common_content_lib_vm):
        """
        This method is used to set the device naming on VM for SRIOV NIC Device
        :param vm_name:
        :param common_content_lib_vm:
        :return:
        """
        nic_name = common_content_lib_vm.execute_sut_cmd(self.GET_VM_NIC_NAME_CMD.format(self.SILENT_CONTINUE),
                                                         "Fetching Nic device naming on Hyper-v", self.VSWITCH_TIME)
        # self._log.info("Fetched Nic Name on Hyper-V: ",nic_name)
        REGEX_FOR_NIC_NAME = r"Hyper\-V\sNetwork\sAdapter\sName"
        output_list = re.findall(REGEX_FOR_NIC_NAME, nic_name)
        display_name = (re.sub('\s\s+', '*', output_list[0])).split('*')
        final_list = (list(filter(lambda a: a != 'Hyper-V Network Adapter Name', display_name)))
        if final_list == []:
            final_list = common_content_lib_vm.execute_sut_cmd(self.GET_NET_ADAPTER_CMD_STATUS,
                                                               "Fetching Nic device naming on Hyper-v",
                                                               self.VSWITCH_TIME)
            final_list = final_list.split()
        else:
            for i in range(len(final_list) - 1):
                if i % 2 == 0:
                    altered_name = common_content_lib_vm.execute_sut_cmd(self.RENAME_NET_ADAPTER_CMD.format(
                        self.SILENT_CONTINUE, final_list[i], final_list[i + 1]), "Renaming Nic device on Hyper-v",
                        self.VSWITCH_TIME)
                # self._log.info("Name Set for Nic device SRIOV on VM:  ", altered_name)

class LinuxVmProvider(VMProvider):
    """
    Class to provide VM methods for Linux platform

    """
    qemu_vm_list = {}
    VM_CREATION_TIME_OUT = 2000  # command timeout constant to create a VM
    ROOT_PATH = r"/root"
    BRIDGE_NAME = "br0"
    NETWORK_SCRIPTS = "/network-scripts"
    KSTART_FILE_NAME = "/linux_vm_kstart.cfg"
    KSTART_CENTOS_FILE_NAME = "/linux_vm_centos_kstart.cfg"
    QEMU_CMD_TO_CREATE_LINUX_VM_WITH_MAC_BRIDGE = '{} -name {} -machine q35 ' \
                                                  '-enable-kvm -global kvm-apic.vapic=false -m {} -cpu host ' \
                                                  '-drive format=raw,file={} -bios {} ' \
                                                  '-device intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode=modern,' \
                                                  'device-iotlb=on,aw-bits=48 -smp {} -serial mon:stdio ' \
                                                  '-nic user,hostfwd=tcp::{}-:22 ' \
                                                  '-net nic,model=virtio,macaddr={} -net bridge,br={} ' \
                                                  '-nographic '
    # --cpu=host-model-only
    VIRT_INSTALL_CMD_TO_CREATE_LINUX_VM_WITH_MAC_ADDRESS = 'virt-install --name={} --memory={} --cpu=host-passthrough --vcpu={} ' \
                                                           '--cpuset={} --location={} --network type=direct,source={},source_mode=bridge,model=virtio ' \
                                                           '--os-type=linux --os-variant={} --mac="{}" --memtune hard_limit=4294967296,soft_limit=4294967296 ' \
                                                           '--disk size={} --initrd-inject=/root{} --extra-args ' \
                                                           '"ks=file:{} console=tty0 console=ttyS0,115200"'
    VIRT_INSTALL_CMD_TO_CREATE_LINUX_VM_WITH_MAC_BRIDGE = 'virt-install --name={} --memory={} --cpu=host-passthrough --vcpu={} ' \
                                                           '--cpuset={} --location={} --network bridge,source={},model=virtio ' \
                                                           '--os-type=linux --os-variant={} --mac="{}" --memtune hard_limit=4294967296,soft_limit=4294967296 ' \
                                                           '--disk size={} --initrd-inject=/root{} --extra-args ' \
                                                           '"ks=file:{} console=tty0 console=ttyS0,115200"'
    VIRT_INSTALL_CMD_TO_CREATE_LINUX_VM = 'virt-install --name={} --memory={} --cpu=host-passthrough --vcpu={} ' \
                                          '--cpuset={} --location={} --network type=direct,source={},source_mode=bridge,model=virtio ' \
                                          '--os-type=linux --os-variant={} --memtune hard_limit=4294967296,soft_limit=4294967296 ' \
                                          '--disk size={} --initrd-inject=/root{} --extra-args ' \
                                          '"ks=file:{} console=tty0 console=ttyS0,115200"'
    VIRT_INSTALL_CMD_TO_CREATE_LINUX_VM_MAC = 'virt-install --name={} --memory={} --cpu=host-passthrough --vcpu={} ' \
                                          '--cpuset={} --location={} --network type=direct,source={},source_mode=bridge,model=virtio ' \
                                          '--os-type=linux --os-variant={} --mac={} --memtune hard_limit=4294967296,soft_limit=4294967296 ' \
                                          '--disk size={} --initrd-inject=/root{} --extra-args ' \
                                          '"ks=file:{} console=tty0 console=ttyS0,115200"'
    VIRT_INSTALL_CMD_TO_CREATE_LINUX_VM_MAC_POOL_BRIDGE = 'virt-install --name={} --memory={} --cpu=host-passthrough --vcpu={} ' \
                                               '--location={} --network bridge,source={},model=virtio ' \
                                               '--os-type=linux --os-variant={} --mac={} --memtune hard_limit=4294967296,soft_limit=4294967296 ' \
                                               '--disk {}={},size={} --initrd-inject=/root{} --extra-args ' \
                                               '"ks=file:{} console=tty0 console=ttyS0,115200"'
    VIRT_INSTALL_CMD_TO_CREATE_LINUX_VM_MAC_POOL = 'virt-install --name={} --memory={} --cpu=host-passthrough --vcpu={} ' \
                                                   '--cpuset={} --location={} --network type=direct,source={},source_mode=bridge,model=virtio ' \
                                                   '--os-type=linux --os-variant={} --mac={} --memtune hard_limit=4294967296,soft_limit=4294967296 ' \
                                                   '--disk {}={},size={} --initrd-inject=/root{} --extra-args ' \
                                                   '"ks=file:{} console=tty0 console=ttyS0,115200"'
    VIRT_INSTALL_CMD_TO_CREATE_LINUX_VM_POOL = 'virt-install --name={} --memory={} --cpu=host-passthrough --vcpu={} ' \
                                               '--cpuset={} --location={} --network type=direct,source={},source_mode=bridge,model=virtio ' \
                                               '--os-type=linux --os-variant={} --memtune hard_limit=4294967296,soft_limit=4294967296 ' \
                                               '--disk {}={},size={} --initrd-inject=/root{} --extra-args ' \
                                               '"ks=file:{} console=tty0 console=ttyS0,115200"'

    VIRT_INSTALL_CMD_TO_CREATE_WINDOWS_VM_WITH_MAC_ADDRESS = 'virt-install --name={} --memory={} --cpu=host-passthrough --vcpu={} ' \
                                                             '--cdrom={} --network bridge={},model=virtio ' \
                                                             '--os-type=windows --os-variant={} --mac={} ' \
                                                             '--disk size={} --disk {},device=cdrom ' \
                                                             '--disk {},device=cdrom --disk {},device=cdrom'

    VIRT_INSTALL_CMD_TO_CREATE_WINDOWS_VM = 'virt-install --name={} --memory={} --cpu=host-passthrough --vcpu={} ' \
                                            '--cdrom={} --network bridge={},model=virtio ' \
                                            '--os-type=windows --os-variant={} ' \
                                            '--disk size={} --disk {},device=cdrom ' \
                                            '--disk {},device=cdrom --disk {},device=cdrom'

    VIRT_INSTALL_CMD_TO_CREATE_WINDOWS_VM_MAC_POOL = 'virt-install --name={} --memory={} --cpu=host-passthrough --vcpu={} ' \
                                                     '--cdrom={} --network bridge={},model=virtio ' \
                                                     '--os-type=windows --os-variant={} --mac={} ' \
                                                     '--disk pool={},size={} --disk {},device=cdrom ' \
                                                     '--disk {},device=cdrom --disk {},device=cdrom'

    VIRT_INSTALL_CMD_TO_CREATE_WINDOWS_VM_POOL = 'virt-install --name={} --memory={} --cpu=host-passthrough --vcpu={} ' \
                                                 '--cdrom={} --network bridge={},model=virtio ' \
                                                 '--os-type=windows --os-variant={} ' \
                                                 '--disk pool={},size={} --disk {},device=cdrom ' \
                                                 '--disk {},device=cdrom --disk {},device=cdrom'
    START_LIBVIRTD_CMD = "systemctl start libvirtd"
    ENABLE_LIBVIRTD_CMD = "systemctl enable libvirtd"
    INSTALL_RHEL_KVM_MODULES = "yum -y install qemu-kvm virt-install virt-manager"
    LOAD_KVM_MODULE = "lsmod | grep kvm"
    SUT_WIN_VMKICKSTART_ISO_IMAGE_LOCATION = "/var/lib/libvirt/images/"
    SUT_RAW_IMG_BASE_IMAGE_LOCATION = "/home/rawimg/"
    SUT_RAW_IMG_IMAGE_LOCATION = "/home/{}_img/"
    SUT_ISO_IMAGE_LOCATION = "/var/lib/libvirt/images/"
    GET_NETWORK_INTERFACE_NAME_CMD = r"ip addr show | awk '/inet.*brd/{print $NF; exit}'"
    GET_NETWORK_INTERFACE_NAME_CMD1 = r"ip addr show | awk '/inet.*{}.*brd/{}'"
    GET_NETWORK_INTERFACE_NAME_DYNAMIC_CMD = r"ip addr show | awk '/inet.*brd.*dynamic/{print $NF; exit}'"
    GET_NETWORK_INTERFACE_NAME_IP_CMD = r"ip addr show | awk '/inet.*brd/{print $2; exit}'"
    GET_NETWORK_INTERFACE_NAME_DYNAMIC_IP_CMD = r"ip addr show | awk '/inet.*brd.*dynamic/{print $2; exit}'"
    GET_NETWORK_BRIDGE_INTERFACE_NAME_CMD = r"ip addr show | awk '/inet.*brd.*dynamic.*br/{print $NF; exit}'"
    GET_NETWORK_BRIDGE_INTERFACE_IP_CMD = r"ip addr show | awk '/inet.*brd.*dynamic.*br/{print $2; exit}'"
    GET_NETWORK_BRIDGE_INTERFACE_NAME_WO_DYNAMIC_CMD = r"ip addr show | awk '/inet.*brd.*br/{print $NF; exit}'"
    # DISABLE_NETWORK_MANAGER_CMDS = ["chkconfig NetworkManager off", "chkconfig network on",
    #                                 "service NetworkManager stop", "service network start"]
    DISABLE_NETWORK_MANAGER_CMDS = ["chkconfig NetworkManager off", "chkconfig network on",
                                    "systemctl stop NetworkManager", "systemctl start NetworkManager"]
    SYSCONFIG_SCRIPTS_PATH = r"/etc/sysconfig"
    ADD_BRIDGE_NAME_TO_CONFIGURATION_FILE = r"sed -i.bak '$ a\BRIDGE=br0' {}/ifcfg-{}"
    CMD_TO_CHECK_NW_CONFIG_FILE = "cat {}/ifcfg-{}"
    CMD_TO_CHECK_DATA_IN_FILE = "cat {}/{}"
    ADD_ADDR_NAME_TO_CONFIGURATION_FILE = r"sed -i.bak '$ a\{}' {}/ifcfg-{}"
    ADD_ADDR_NAME_TO_CONFIGURATION_FILENAME = r"sed -i.bak '$ a\{}' {}/{}"
    GET_MAC_ADDRESS_CMD = "ip -o link | awk '$2 != \"lo:\" {{print $2, $(NF-2)}}' | grep {}"
    BRIDGE_CONFIG_FILE_CONTENTS = ["DEVICE=br0", "TYPE=Bridge", "BOOTPROTO=dhcp", "ONBOOT=yes", "DELAY=0"]
    ADD_VIRBRIDGE_NAME_TO_CONFIGURATION_FILE = r"sed -i.bak '$ a\BRIDGE={}' {}/ifcfg-{}"
    VIRBRIDGE_CONFIG_FILE_CONTENTS = ["DEVICE={}", "TYPE=Bridge", "PROXY_METHOD=none", "BOOTPROTO=dhcp", "DEFROUTE=yes",
                                      "IPV4_FAILURE_FATAL=no", "IPV6INIT=yes", "IPV6_AUTOCONF=yes", "IPV6_DEFROUTE=yes",
                                      "IPV6_FAILURE_FATAL=no", "ONBOOT=yes", "DELAY=0"]
    ATTACH_DISK_CMD = "virsh attach-disk {} {}{} {} --cache none"
    CREATE_DISK_CMD = "qemu-img create -f raw {} {}G"
    SCP_COPY_TO_VM_CMD = "./go_scp -remote {} -user {} -password {} -source {} -destination {}"
    SUSPEND_VM_CMD_LINUX = "virsh suspend {}"
    RESUME_VM_CMD_LINUX = "virsh resume {}"
    VM_NETWORK_INTERFACE_NAME = "eth0"
    ENABLE_NETWORK_MANAGER_CMDS = ["chkconfig NetworkManager on", "service NetworkManager start"]
    SAVE_VM_CONFIG_CMD = "virsh save {} --bypass-cache {}"
    RESTORE_VM_CONFIG_CMD = "virsh restore --bypass-cache {}"
    USB_DEVICE_XML_FILE_NAME = "usb_device.xml"
    USB_DEVICE_XML_FILE_DATA = """<hostdev mode='subsystem' type='usb' managed='yes'>
    <source>
        <vendor id='{}'/>
        <product id='{}'/>
    </source>
    </hostdev>"""
    ATTACH_USB_DEVICE_COMMAND = " virsh attach-device {} --file {} --current"
    DETACH_USB_DEVICE_COMMAND = " virsh detach-device {} --file {} --current"

    # __MAC_INDEX = 0
    # CREATE_STORAGE_POOL = "virsh pool-define-as --name {} --type dir --target {}"
    CREATE_STORAGE_POOL = "virsh pool-define-as --name {} dir - - - - {}"
    BUILD_STORAGE_POOL_VOL = "virsh pool-build {}"
    DESTROY_STORAGE_POOL = "virsh pool-destroy {}"
    DELETE_STORAGE_POOL = "virsh pool-delete {}"
    UNDEFINE_STORAGE_POOL = "virsh pool-undefine {}"
    START_STORAGE_POOL = "virsh pool-start {}"
    AUTOSTART_STORAGE_POOL = "virsh pool-autostart {}"
    # STORAGE_POOL_INFO = "virsh pool-info {} | awk '/Available:*/ {print $2}'"
    STORAGE_POOL_INFO = "virsh pool-info {} --bytes"
    STORAGE_POOL_ALL = "virsh pool-list --all"
    STORAGE_POOL_STATUS = "virsh pool-info {}" #| awk '/State:*/ {print $2}'"
    CREATE_STORAGE_POOL_VOL = "virsh vol-create-as --pool {} --name {} --capacity {}GB"
    DELETE_STORAGE_POOL_VOL = "virsh vol-delete --pool {} --vol {}"
    LIST_STORAGE_POOL_VOL = "virsh vol-list {}"
    STORAGE_POOL_VOL_INFO = "virsh vol-info --pool {} {} --bytes"
    LIST_VOL_INFO_REGEX = ".*\/{}"
    CHECK_VM_STATUS = "virsh list --all | grep {}"
    __MAC_ADDR_INDEX = 0

    CVL_ICE_DRIVER_FILE_NAME = "ice-1.5.0_rc35_24_g9904f5da_dirty.tar.gz"
    CVL_ICE_DRIVER_STR = "ice-1.5.0_rc35_24_g9904f5da_dirty"
    CVL_IAVF_DRIVER_FILE_NAME = "iavf-4.2.7.tar.gz"
    CVL_IAVF_DRIVER_STR = "iavf-4.2.7"
    UNTAR_FILE_CMD = r"tar -xvf {}"
    MDEV_PATH = "/sys/class/mdev_bus/"
    MDEV_CREATION_TIMEOUT = 30
    CREATE_MDEV_CMD = "echo {} > /sys/class/mdev_bus/{}/mdev_supported_types/{}/create"
    CHECK_UUID_CMD = "ls /sys/class/mdev_bus/{}/mdev_supported_types/{}"
    CREATE_DLB2_MDEV_CMD = "echo {} > {}/device/mdev_supported_types/dlb2-dlb/create"
    MDEV_DLB2_PATH = "/sys/bus/mdev/devices/{}/dlb2_mdev/"

    MEM_INFO = "cat /proc/meminfo"
    TOTAL_MEM_INFO = "MemTotal:\s+([0-9]+)"

    CONFIGURE_MAX_MEM = "virsh setmaxmem {} {} --config"
    SET_VM_MEM = "virsh setmem {} {} --config"

    CONFIGURE_MAX_CPU = "virsh setvcpus {} {} --config --maximum"
    SET_VM_CPU = "virsh setvcpus {} {} --config"

    FIND_VM_LOCATION = "virsh domblklist {}"
    DISK_RESIZE_CMD = "virsh blockresize {} {} {}GB"

    def create_vm(self, vm_name, os_variant, no_of_cpu=2, disk_size=6, memory_size=4098, vm_creation_timeout=1600,
                  vm_create_async=None, mac_addr=None, pool_id=None, pool_vol_id=None, cpu_core_list=None,
                  nw_bridge=None, vm_os_subtype=None, nesting_level=None, vhdx_dir_path=None, devlist=[], qemu=None):
        """
        Execute the the command to create a linux VM.

        :param vm_name: Name of the new VM
        :param vm_create_async: if VM is nested VM
        :param no_of_cpu: No of CPUs in VM
        :param disk_size: Size of the VM disk drive
        :param memory_size: Size of the VM memory
        :param os_variant: linux Os version
        :param vm_creation_timeout: timeout for vm creation
        :param mac_addr: Mac address for VM
        :return vm_name: Name of the new VM
        :param pool_vol_id: Storage pool Volume id from storage volume created in the given pool
        :param cpu_core_list: CPU core list to be assigned to VM with --cpuset
        :param nesting_level: nesting_level in case of nested VM
        :raise: RuntimeError
        """
        linux_distribution_list = [LinuxDistributions.RHEL.lower(), LinuxDistributions.Fedora.lower(),
                                   LinuxDistributions.Ubuntu.lower(), LinuxDistributions.CentOS.lower()]
        vm_name_lower = vm_name.lower()
        vm_list = vm_name_lower.split("_")
        if any(elm in linux_distribution_list for elm in vm_list):
            if qemu=="qemu":
                return self._create_linux_vm_qemu(vm_name, os_variant, no_of_cpu, disk_size, memory_size,
                                             vm_creation_timeout,
                                             vm_create_async=vm_create_async, mac_addr=mac_addr, pool_id=pool_id,
                                             pool_vol_id=pool_vol_id, cpu_core_list=cpu_core_list, nw_bridge=nw_bridge,
                                             nesting_level=nesting_level, devlist=devlist)
            else:
                return self._create_linux_vm(vm_name, os_variant, no_of_cpu, disk_size, memory_size, vm_creation_timeout,
                                         vm_create_async=vm_create_async, mac_addr=mac_addr, pool_id=pool_id,
                                         pool_vol_id=pool_vol_id, cpu_core_list=cpu_core_list, nw_bridge=nw_bridge,
                                         nesting_level=nesting_level, devlist=devlist)
        elif "windows" in vm_name.lower():
            return self._create_windows_vm(vm_name, os_variant, no_of_cpu, disk_size, memory_size, vm_creation_timeout,
                                           vm_create_async=vm_create_async, mac_addr=mac_addr, pool_id=pool_id,
                                           pool_vol_id=pool_vol_id, cpu_core_list=cpu_core_list, nw_bridge=nw_bridge,
                                           nesting_level=nesting_level, devlist=devlist)
        else:
            raise NotImplementedError("{} VM type is not implemented".format(vm_name))

    def get_attach_device_cmd_qemu(self, devlist):
        """
        device_type: "pt", "dsa", "qat", "mdev", "dlb"
        devlist = [<device_type>=<Value>]
        e.g. devlist=[mdev=/sys/bus/mdev/devices/ae4ee338-2cba-46a2-82c9-9b4beaba527f,
                        mdev=/sys/bus/mdev/devices/ae4ee338-2cba-46a2-82c9-9b4beaba527f,
                        pt=0000:6d:00.01]
        "-device vfio-pci,sysfsdev=/sys/bus/mdev/devices/ae4ee338-2cba-46a2-82c9-9b4beaba527f"
        "-device vfio-pci,host=0000:6d:00.01"
        """

        if not devlist:
            return ''
        if len(devlist) == 0:
            return ''
        # device_type = "mdev"
        cmd = ''
        for dev_val in devlist:
            device_type = dev_val.split("==")[0].strip()
            dev_val = dev_val.split("==")[1].strip()
            if device_type == "pt":
                cmd += f'-device vfio-pci,host={dev_val} '
            elif device_type == "mdev":
                cmd += f'-device vfio-pci,sysfsdev={dev_val} '
            elif device_type == "qemuparam":
                cmd += f'{dev_val} '
            else:
                self._log.info("vm not creating")
        return cmd.strip()

    def qet_free_port_qemu(self):
        port_start = 2222
        port_end = 3333

        for port in range(port_start, port_end + 2):
            out = self._common_content_lib.execute_sut_cmd_no_exception(f'lsof -i:{port}',
                                                                        f'lsof -i:{port}',
                                                                        self._command_timeout,
                                                                        cmd_path="/root",
                                                                        ignore_result="ignore")
            if out.strip() == '':
                return port

        err_msg = 'error: cannot find free port between 2222 and 3333'
        self._log.info("execute lsof -i cmd output: {}".format(err_msg))
        raise Exception(err_msg)

    def os_kernel_version(self):
        out = self._common_content_lib.execute_sut_cmd_no_exception("uname -r",
                                                                    "uname -r",
                                                                    self._command_timeout,
                                                                    cmd_path="/root",
                                                                    ignore_result="ignore")
        self._log.debug("execute systemctl stop firewalld cmd : {}".format(out))
        line_list = out.strip().split('-')
        if line_list[0] <= '5.12.0':
            qemu_cmd = 'qemu-system-x86_64'
        else:
            qemu_cmd = '/usr/libexec/qemu-kvm'
        return qemu_cmd

    def get_ssh_port_qemu_vm_linux(self, vm_name):
        """
        Returns the ssh port used by VM created by qemu
        """
        if vm_name in self.qemu_vm_list:
            return self.qemu_vm_list[vm_name]["ssh_port"]
        else:
            port=""
            qemu_bin = os.path.basename(self.os_kernel_version())
            cmd = "ps -ef| grep {} | grep -v libvirt | grep {} | grep -v grep".format(qemu_bin, vm_name)
            out_result = self._common_content_lib.execute_sut_cmd(cmd,
                                                                  cmd_str="execute command:{}".format(cmd),
                                                                  execute_timeout=self._command_timeout,
                                                                  cmd_path="/")
            cmdnew = out_result.replace("tcp::", "PortNumber:")
            cmdnew_split = cmdnew.split("PortNumber")
            port = cmdnew_split[1].strip().split(":")[1].strip("-")
            if port != None or port !="":
                return int(port)
            return None

    def execute_async_command_on_qemu_vm(self, vm_name, cmd, cmd_str="", cmd_path="/", execute_timeout=None):
        """
        This function is to rum commands on VM created with Qemu Command on Linux
        :param vm_name:
        :param cmd:
        :param cmd_str:
        :param cmd_path:
        :param execute_timeout:
        :return:
        """
        out_result = ""
        self._log.info("Execute async command on qemu VM {} :{}".format(cmd, cmd_str))
        self._log.debug("Execute async command on qemu VM {} :{}".format(cmd, cmd_str))
        if execute_timeout == None:
            execute_timeout = self._command_timeout
        if self.is_qemu_vm_running(vm_name) == True:
            port_no = self.get_ssh_port_qemu_vm_linux(vm_name)
            cmd = "sshpass -p password ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {} root@localhost {}".format(port_no, cmd)
            out_result = self._common_content_lib.execute_sut_cmd_async(cmd,
                                                            cmd_str="execute command:{}".format(cmd),
                                                            execute_timeout=execute_timeout,
                                                            cmd_path=cmd_path)
            self._log.debug("Async Command {} on qemu VM {} successfully done :{}".format(cmd, vm_name, cmd_str))
        else:
            self._log.error("Execute async command {} failed on qemu VM {}, no qmu vm running".format(cmd, vm_name))

        return out_result

    def execute_command_on_qemu_vm(self, vm_name, cmd, cmd_str="", cmd_path="/", execute_timeout=None):
        """
        This function is to rum commands on VM created with Qemu Command on Linux
        :param vm_name:
        :param cmd:
        :param cmd_str:
        :param cmd_path:
        :param execute_timeout:
        :return:
        """
        out_result = ""
        self._log.info("Execute command on qemu VM {} :{}".format(cmd, cmd_str))
        self._log.debug("Execute command on qemu VM {} :{}".format(cmd, cmd_str))
        if execute_timeout == None:
            execute_timeout = self._command_timeout
        if self.is_qemu_vm_running(vm_name) == True:
            port_no = self.get_ssh_port_qemu_vm_linux(vm_name)
            cmd = "sshpass -p password ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {} root@localhost {}".format(port_no, cmd)
            out_result = self._common_content_lib.execute_sut_cmd(cmd,
                                                            cmd_str="execute command:{}".format(cmd),
                                                            execute_timeout=execute_timeout,
                                                            cmd_path=cmd_path)
            self._log.debug("Command {} on qemu VM {} successfully done :{}".format(cmd, vm_name, cmd_str))
        else:
            self._log.error("Execute command {} failed on qemu VM {}, no qmu vm running".format(cmd, vm_name))

        return out_result

    def _create_linux_vm_qemu(self, vm_name, os_variant, no_of_cpu, disk_size, memory_size, vm_creation_timeout=1600,
                              vm_create_async=None, mac_addr=None, pool_id=None, pool_vol_id=None, cpu_core_list=None,
                              nw_bridge=None, nesting_level=None, devlist=[]):
        """
        Execute the the command to create a linux VM.

        :param vm_name: Name of the new VM
        :param vm_create_async: if VM is has to be created in async mode such as required for nested VM
        :param no_of_cpu: No of CPUs in VM
        :param disk_size: Size of the VM disk drive
        :param memory_size: Size of the VM memory
        :param os_variant: linux Os version
        :param vm_creation_timeout: timeout for vm creation
        :param mac_addr: Assign MacAddress to Network.
        :param pool_id: Storage pool id from storage
        :param pool_vol_id: Storage pool Volume id from storage volume created in the given pool
        :param cpu_core_list: CPU core list to be assigned to VM with --cpuset
        :param nw_bridge : Some Non-None value is bridge type default n/w required in VM
        :param nesting_level: nesting_level in case of nested VM
        :return vm_name: Name of the new VM
        :raise: RuntimeError
        """
        self.qemu_vm_list[vm_name] = {}
        ssh_port = self.qet_free_port_qemu()
        self.qemu_vm_list[vm_name]["ssh_port"] = ssh_port

        qemu_cmd = self.os_kernel_version()
        bios = '/usr/share/qemu/OVMF.fd'  # take this file from artifactory

        disk_size_mb = disk_size * 1024
        ram_size_mb = memory_size

        self._log.info("MAC ADDR INDEX {}".format(self.__MAC_ADDR_INDEX))
        vm_name_lower_list = vm_name.lower().split("_")
        centos_list = ["centos"]
        self.install_vm_tool()
        self.install_kvm_vm_tool()
        self.install_qemu_vm_tool()
        supported_vm_list = ["linux", "windows", "centos", "rhel", "ubuntu", "fedora"]
        if any(elm in vm_name_lower_list for elm in supported_vm_list):
            verify_img_image = self._verify_imageforvm_img_existance(vm_name)
            if not verify_img_image:
                image_path = self._copy_raw_imageforvm_to_sut_linux_sut(vm_name)
            else:
                self._log.info("ISO image already present on SUT. Continue VM : {}Creation".format(vm_name))
                image_path = self._verify_imageforvm_img_existance(vm_name)
        else:
            raise NotImplementedError("Only linux and windows VM type is supported and the VM name should contain "
                                      "windows/linux. {} VM type is not implemented".format(vm_name))

        self._common_content_lib.execute_sut_cmd_no_exception(
            "mkdir -p {}; rm -f {}/{}_launch.exp;".format(self.SUT_RAW_IMG_IMAGE_LOCATION.format(vm_name),
                                                          self.SUT_RAW_IMG_IMAGE_LOCATION.format(vm_name),
                                                          vm_name),
            "To delete the vm launch file", self._command_timeout, self.ROOT_PATH, ignore_result="ignore")

        self._common_content_lib.execute_sut_cmd_no_exception(
            "mkdir -p {}; touch {}/{}_launch.exp;".format(self.SUT_RAW_IMG_IMAGE_LOCATION.format(vm_name),
                                                          self.SUT_RAW_IMG_IMAGE_LOCATION.format(vm_name),
                                                          vm_name),
            "To Create a vm launch file", self._command_timeout, self.ROOT_PATH, ignore_result="ignore")

        vm_launch_filepath = "{}/{}_launch.exp".format(self.SUT_RAW_IMG_IMAGE_LOCATION.format(vm_name), vm_name)
        self.qemu_vm_list[vm_name]["disk_path"] = image_path
        self._log.info("Creating Linux VM named {}".format(vm_name))
        os_variant = vm_name.split("_")[0].lower() + os_variant
        if nw_bridge is not None:
            current_network_interface_name = "virbr0"  # self._get_current_network_bridge_interface_linux()
        else:
            current_network_interface_name = self._get_current_network_interface_linux()

        if cpu_core_list is None:
            cpu_core_list = "auto"

        mac_id = self.get_free_mac_from_available_list(self.os.os_type.lower(),
                                                       vm_name.split("_")[0].upper(),
                                                       nesting_level)
        if mac_id == "" or mac_id is None:
            raise RuntimeError("Failed to create the {} VM, No free MAC address available!".format(vm_name))

        self.qemu_vm_list[vm_name]["mac_id"] = mac_id

        if nw_bridge is None:
            raise RuntimeError("Failed to create the {} VM, Virtual bridge is required for VM!".format(vm_name))
        else:
            qemu_vm_create_cmd = self.QEMU_CMD_TO_CREATE_LINUX_VM_WITH_MAC_BRIDGE.format(qemu_cmd, vm_name, ram_size_mb,
                                                                                         image_path, bios,
                                                                                         no_of_cpu, ssh_port, mac_id,
                                                                                         current_network_interface_name)
            qemu_vm_create_cmd += self.get_attach_device_cmd_qemu(devlist)

        vmlaunch_content = "echo '#!/usr/bin/expect -f' >> {};" \
                           "echo 'set timeout -1'  >> {};" \
                           "echo 'spawn {}' >> {};" \
                           "echo 'expect \"login: \"' >> {};" \
                           "echo 'send \"root\\n\"' >> {};" \
                           "echo 'expect {}' >> {};" \
                           "echo '\"Password:*\" {} send \"password\\n\" {}' >> {};" \
                           "echo '\"# \" {} send \"\\n\" {}' >> {};" \
                           "echo '{}' >> {};" \
                           "echo 'expect \"# \"' >> {};" \
                           "echo 'send \"passwd root\\n\"' >> {};" \
                           "echo 'expect \"*password:\"' >> {};" \
                           "echo 'send \"password\\n\"' >> {};" \
                           "echo 'expect \"*password:\"' >> {};" \
                           "echo 'send \"password\\n\"' >> {};".format(vm_launch_filepath, vm_launch_filepath, qemu_vm_create_cmd,
                                                             vm_launch_filepath, vm_launch_filepath, vm_launch_filepath,
                                                             "{",
                                                             vm_launch_filepath, "{", "}", vm_launch_filepath,
                                                             "{", "}", vm_launch_filepath, "}", vm_launch_filepath,
                                                             vm_launch_filepath, vm_launch_filepath, vm_launch_filepath,
                                                             vm_launch_filepath, vm_launch_filepath, vm_launch_filepath,
                                                             vm_launch_filepath)

        self._common_content_lib.execute_sut_cmd(vmlaunch_content, "LINUX VM launch script creation-1",
                                                 self._command_timeout,
                                                 cmd_path=self.ROOT_PATH)

        # Add sleep in case no screen utility and want t o sleep forever after executing all expect commands
        # vmlaunch_content = "echo 'sleep {}' >> {};" \
        #                    "echo 'interact' >> {};".format(vm_creation_timeout, vm_launch_filepath,
        #                     vm_launch_filepath)

        # self._common_content_lib.execute_sut_cmd(vmlaunch_content, "LINUX VM launch script creation-2",
        #                                          self._command_timeout,
        #                                          cmd_path=self.ROOT_PATH)

        # create_vm_result = self._common_content_lib.execute_sut_cmd_async("bash -c '{} &'".format(vm_launch_filepath),
        #                                                                   "LINUX VM creation",
        #                                                                   vm_creation_timeout, cmd_path="/")


        vmlaunch_content =  "echo 'interact' >> {};".format(vm_launch_filepath)

        self._common_content_lib.execute_sut_cmd(vmlaunch_content, "LINUX VM launch script creation-2",
                                                                          self._command_timeout,
                                                                          cmd_path=self.ROOT_PATH )

        # change the permissions to executable
        create_vm_result = self._common_content_lib.execute_sut_cmd("chmod 777 {}".format(vm_launch_filepath),
                                                                    "chmod 777 {}".format(vm_launch_filepath),
                                                                    self._command_timeout, cmd_path="/")

        vm_creation_timeout = 14*24*3600

        create_vm_result = self._common_content_lib.execute_sut_cmd("screen -dmS {}_scr bash -c '{}'".format(vm_name,
                                                                                                vm_launch_filepath),
                                                                    "LINUX VM creation",
                                                                    vm_creation_timeout, cmd_path="/")

        self._log.info("Successfully executed qemu_vm_create_cmd to create the {} linux VM".format(vm_name))
        time.sleep(120)
        self._log.debug("'qemu-kvm' vm create command response {}".format(create_vm_result))
        # clear the ssh key at SUT in case it was there already otherwise ignore it
        try:
            self._common_content_lib.execute_sut_cmd("ssh-keygen -R [localhost]:{}".format(ssh_port),
                                                     "ssh-keygen -R [localhost]:{}".format(ssh_port),
                                                     self._command_timeout,
                                                     self.ROOT_PATH)
        except:
            pass
        time.sleep(10)
        self._log.info("Successfully created the {} linux Qemu VM".format(vm_name))

    def _create_linux_vm(self, vm_name, os_variant, no_of_cpu, disk_size, memory_size, vm_creation_timeout=1600,
                         vm_create_async=None, mac_addr=None, pool_id=None, pool_vol_id=None, cpu_core_list=None,
                         nw_bridge=None, nesting_level=None, devlist=[]):
        """
        Execute the the command to create a linux VM.

        :param vm_name: Name of the new VM
        :param vm_create_async: if VM is has to be created in async mode such as required for nested VM
        :param no_of_cpu: No of CPUs in VM
        :param disk_size: Size of the VM disk drive
        :param memory_size: Size of the VM memory
        :param os_variant: linux Os version
        :param vm_creation_timeout: timeout for vm creation
        :param mac_addr: Assign MacAddress to Network.
        :param pool_id: Storage pool id from storage
        :param pool_vol_id: Storage pool Volume id from storage volume created in the given pool
        :param cpu_core_list: CPU core list to be assigned to VM with --cpuset
        :param nw_bridge : Some Non-None value is bridge type default n/w required in VM
        :param nesting_level: nesting_level in case of nested VM
        :return vm_name: Name of the new VM
        :raise: RuntimeError
        """
        self._log.info("MAC ADDR INDEX {}".format(self.__MAC_ADDR_INDEX))
        vm_name_lower_list = vm_name.lower().split("_")
        centos_list = ["centos"]
        self.install_vm_tool()
        self.install_kvm_vm_tool()
        kick_start_file_name = self.KSTART_FILE_NAME
        if any(elm in vm_name_lower_list for elm in centos_list):
            kick_start_file_name = "/{}".format(
                self._common_content_configuration.get_kickstart_file_name_centos())  # self.KSTART_CENTOS_FILE_NAME
        self._copy_kstart_to_sut(kick_start_file_name)
        supported_vm_list = ["linux", "windows", "centos", "rhel", "ubuntu", "fedora"]
        if any(elm in vm_name_lower_list for elm in supported_vm_list):
            verify_iso_image = self._verify_iso_existance(vm_name)
            if not verify_iso_image:
                image_path = self._copy_iso_image_to_sut_linux_sut(vm_name)
            else:
                self._log.info("ISO image already present on SUT. Continue VM : {}Creation".format(vm_name))
                image_path = self._verify_iso_existance(vm_name)
        else:
            raise NotImplementedError("Only linux and windows VM type is supported and the VM name should contain "
                                      "windows/linux. {} VM type is not implemented".format(vm_name))

        # image_path = self._copy_iso_image_to_sut_linux_sut()
        self._log.info("Creating Linux VM named {}".format(vm_name))
        os_variant = vm_name.split("_")[0].lower() + os_variant
        if nw_bridge is not None:
            current_network_interface_name = "virbr0"  # self._get_current_network_bridge_interface_linux()
        else:
            current_network_interface_name = self._get_current_network_interface_linux()
        if pool_vol_id is not None:
            pool_tag = "vol"
            final_pool_vol_id = "{}/{}".format(pool_id, pool_vol_id)
        elif pool_id is not None:
            pool_tag = "pool"
            final_pool_vol_id = pool_id
        else:
            self._log.info("No Pool for VM {} creation, using default storage.".format(vm_name))

        if cpu_core_list is None:
            cpu_core_list = "auto"

        if nesting_level=="l2":
            if mac_addr:
                mac_id = self.get_free_mac_from_available_list(self.os.os_type.lower(),
                                                               vm_name.split("_")[0].upper(),
                                                               nesting_level)
                if mac_id == "" or mac_id is None:
                    raise RuntimeError("Failed to create the {} VM, No free MAC address available!".format(vm_name))

                virt_install_cmd = self.VIRT_INSTALL_CMD_TO_CREATE_LINUX_VM_MAC.format(vm_name, memory_size, no_of_cpu,
                                                                                   cpu_core_list, image_path,
                                                                                   current_network_interface_name,
                                                                                   os_variant, mac_id, disk_size,
                                                                                   kick_start_file_name,
                                                                                   kick_start_file_name)
            else:
                virt_install_cmd = self.VIRT_INSTALL_CMD_TO_CREATE_LINUX_VM.format(vm_name, memory_size, no_of_cpu,
                                                                               cpu_core_list, image_path,
                                                                               current_network_interface_name,
                                                                               os_variant, disk_size,
                                                                               kick_start_file_name,
                                                                               kick_start_file_name)
        else:
            if mac_addr and (pool_id is not None):
                mac_id = self.get_free_mac_from_available_list(self.os.os_type.lower(),
                                                               vm_name.split("_")[0].upper(),
                                                               nesting_level)
                if mac_id == "" or mac_id is None:
                    raise RuntimeError("Failed to create the {} VM, No free MAC address available!".format(vm_name))
                # mac_id = mac_id_list[self.__MAC_ADDR_INDEX]
                if nw_bridge is None:
                    virt_install_cmd_params = self.VIRT_INSTALL_CMD_TO_CREATE_LINUX_VM_MAC_POOL
                    virt_install_cmd = virt_install_cmd_params.format(vm_name, memory_size, no_of_cpu,
                                                                      cpu_core_list, image_path,
                                                                      current_network_interface_name,
                                                                      os_variant,
                                                                      mac_id,
                                                                      pool_tag, final_pool_vol_id,
                                                                      disk_size,
                                                                      kick_start_file_name,
                                                                      kick_start_file_name)
                else:
                    virt_install_cmd_params = self.VIRT_INSTALL_CMD_TO_CREATE_LINUX_VM_MAC_POOL_BRIDGE
                    virt_install_cmd = virt_install_cmd_params.format(vm_name, memory_size, no_of_cpu,
                                                                      image_path,
                                                                      current_network_interface_name,
                                                                      os_variant,
                                                                      mac_id,
                                                                      pool_tag, final_pool_vol_id,
                                                                      disk_size,
                                                                      kick_start_file_name,
                                                                      kick_start_file_name)
                # self.__MAC_ADDR_INDEX += 1
            elif pool_id is not None:
                virt_install_cmd = self.VIRT_INSTALL_CMD_TO_CREATE_LINUX_VM_POOL.format(vm_name, memory_size, no_of_cpu,
                                                                                        cpu_core_list, image_path,
                                                                                        current_network_interface_name,
                                                                                        os_variant,
                                                                                        pool_tag, final_pool_vol_id,
                                                                                        disk_size,
                                                                                        kick_start_file_name,
                                                                                        kick_start_file_name)

            elif mac_addr:
                mac_id = self.get_free_mac_from_available_list(self.os.os_type.lower(),
                                                               vm_name.split("_")[0].upper(),
                                                               nesting_level)
                if mac_id == "" or mac_id is None:
                    raise RuntimeError("Failed to create the {} VM, No free MAC address available!".format(vm_name))

                if nw_bridge is not None:
                    virt_install_cmd_params = self.VIRT_INSTALL_CMD_TO_CREATE_LINUX_VM_WITH_MAC_BRIDGE
                else:
                    virt_install_cmd_params = self.VIRT_INSTALL_CMD_TO_CREATE_LINUX_VM_WITH_MAC_ADDRESS

                virt_install_cmd = virt_install_cmd_params.format(vm_name, memory_size,
                                                                  no_of_cpu,
                                                                  cpu_core_list,
                                                                  image_path,
                                                                  current_network_interface_name,
                                                                  os_variant, mac_id,
                                                                  disk_size,
                                                                  kick_start_file_name,
                                                                  kick_start_file_name)
                # self.__MAC_ADDR_INDEX += 1
            else:
                virt_install_cmd = self.VIRT_INSTALL_CMD_TO_CREATE_LINUX_VM.format(vm_name, memory_size, no_of_cpu,
                                                                                   cpu_core_list, image_path,
                                                                                   current_network_interface_name,
                                                                                   os_variant, disk_size,
                                                                                   kick_start_file_name,
                                                                                   kick_start_file_name)

        if vm_create_async:
            create_vm_result = self._common_content_lib.execute_sut_cmd_async(virt_install_cmd, "LINUX VM creation",
                                                                              vm_creation_timeout, ps_name=vm_name)
            self._log.info("Successfully executed virt-install to create the {} linux VM".format(vm_name))
        else:
            create_vm_result = self._common_content_lib.execute_sut_cmd(virt_install_cmd, "LINUX VM creation",
                                                                        vm_creation_timeout)

            self._log.debug("'virt-install' command response \n{}".format(create_vm_result))
            if vm_name and "Domain creation completed." and "Restarting guest." not in create_vm_result:
                raise RuntimeError("Failed to create the {} VM".format(vm_name))
            self._log.info("Successfully create the {} linux VM".format(vm_name))

    def _create_windows_vm(self, vm_name, os_variant, no_of_cpu, disk_size, memory_size, vm_creation_timeout=1600,
                            vm_create_async=None, mac_addr=None, pool_id=None, pool_vol_id=None, cpu_core_list=None,
                            nw_bridge=None, nesting_level=None, devlist=[]):
        """
        Execute the the command to create a windows VM.

        :param vm_name: Name of the new VM
        :param vm_create_async: if VM is has to be created in async mode such as required for nested VM
        :param no_of_cpu: No of CPUs in VM
        :param disk_size: Size of the VM disk drive
        :param memory_size: Size of the VM memory
        :param os_variant: linux Os version
        :param vm_creation_timeout: timeout for vm creation
        :param mac_addr: Assign MacAddress to Network.
        :param pool_id: Storage pool id from storage
        :param pool_vol_id: Storage pool Volume id from storage volume created in the given pool
        :param cpu_core_list: CPU core list to be assigned to VM with --cpuset
        :param nw_bridge : Some Non-None value is bridge type default n/w required in VM
        :param nesting_level: nesting_level in case of nested VM
        :return vm_name: Name of the new VM

        :raise: RuntimeError
        """
        virtio_win_iso_file_path = ""
        win_kickstart_iso_file_path = ""
        self.install_vm_tool()
        self.install_kvm_vm_tool()
        self.install_kvm_virtio_win_tool()
        self._install_collateral.copy_win_kickstart_iso()
        # self._copy_kstart_to_sut(self.KSTART_FILE_NAME)
        vm_name_lower = vm_name.lower()

        virtio_win_iso_path_find = "find / -type f -name virtio-win*.iso"
        win_kickstart_iso_path_find = "find / -type f -name win_kickstart_iso.iso"

        virtio_win_iso_file_path_output = self._common_content_lib.execute_sut_cmd_no_exception(virtio_win_iso_path_find,
                                                                           "run find command:{}".format(
                                                                               virtio_win_iso_path_find),
                                                                           self._command_timeout,
                                                                           self.ROOT_PATH,
                                                                           ignore_result="ignore")

        virtio_win_iso_file_path_list = virtio_win_iso_file_path_output.split('\n')
        if len(virtio_win_iso_file_path_list) > 1:
            virtio_win_iso_file_path = virtio_win_iso_file_path_list[0].strip()
        else:
            virtio_win_iso_file_path = virtio_win_iso_file_path_output.strip()


        win_kickstart_iso_file_path_output = self._common_content_lib.execute_sut_cmd_no_exception(win_kickstart_iso_path_find,
                                                                                         "run find command:{}".format(
                                                                                             win_kickstart_iso_path_find),
                                                                                         self._command_timeout,
                                                                                         self.ROOT_PATH,
                                                                                         ignore_result="ignore")
        win_kickstart_iso_file_path_list = win_kickstart_iso_file_path_output.split('\n')
        if len(win_kickstart_iso_file_path_list) > 1:
            for elem in win_kickstart_iso_file_path_list:
                if "images" in elem:
                    win_kickstart_iso_file_path = elem.strip()
                    break
        else:
            win_kickstart_iso_file_path = win_kickstart_iso_file_path_output.strip()

        supported_vm_list = ["windows"]
        if any(elm in vm_name_lower for elm in supported_vm_list):
            verify_iso_image = self._verify_iso_existance(vm_name)
            if not verify_iso_image:
                image_path = self._copy_iso_image_to_sut_linux_sut(vm_name)
            else:
                self._log.info("ISO image already present on SUT. Continue VM : {}Creation".format(vm_name))
                image_path = self._verify_iso_existance(vm_name)
        else:
            raise NotImplementedError("Only linux and windows VM type is supported and the VM name should contain "
                                      "windows/linux. {} VM type is not implemented".format(vm_name))

        # image_path = self._copy_iso_image_to_sut_linux_sut()
        self._log.info("Creating WINDOWS VM named {}".format(vm_name))
        os_variant = vm_name.split("_")[0][0:3].lower() + os_variant
        current_network_interface_name = self._get_current_network_bridge_interface_linux()

        sut_ip_iso = self.create_runtime_iso_sut(vm_name)
        if sut_ip_iso is None:
            raise RuntimeError("Failed to create the {} VM, sut_ip_iso creation failed".format(vm_name))

        if mac_addr and (pool_id is not None):
            mac_id = self.get_free_mac_from_available_list(self.os.os_type.lower(),
                                                                                    vm_name.split("_")[0].upper(),
                                                                                    nesting_level)

            if mac_id == "" or mac_id is None:
                raise RuntimeError("Failed to create the {} VM, No free MAC address available!".format(vm_name))
            # mac_id = mac_id_list[self.__MAC_ADDR_INDEX]
            virt_install_cmd = self.VIRT_INSTALL_CMD_TO_CREATE_WINDOWS_VM_MAC_POOL.format(vm_name, memory_size,
                                                                                        no_of_cpu,
                                                                                        image_path,
                                                                                        current_network_interface_name,
                                                                                        os_variant, mac_id,
                                                                                        pool_id,
                                                                                        disk_size,
                                                                                        virtio_win_iso_file_path,
                                                                                        win_kickstart_iso_file_path,
                                                                                        sut_ip_iso)
            # self.__MAC_ADDR_INDEX += 1
        elif pool_id is not None:
            virt_install_cmd = self.VIRT_INSTALL_CMD_TO_CREATE_WINDOWS_VM_POOL.format(vm_name, memory_size, no_of_cpu,
                                                                                    image_path,
                                                                                    current_network_interface_name,
                                                                                    os_variant,
                                                                                    pool_id,
                                                                                    disk_size,
                                                                                    virtio_win_iso_file_path,
                                                                                    win_kickstart_iso_file_path,
                                                                                    sut_ip_iso)

        elif mac_addr:
            mac_id = self.get_free_mac_from_available_list(self.os.os_type.lower(),
                                                                                    vm_name.split("_")[0].upper(),
                                                                                    nesting_level)
            if mac_id == "" or mac_id is None:
                raise RuntimeError("Failed to create the {} VM, No free MAC address available!".format(vm_name))
            # mac_id = mac_id_list[self.__MAC_ADDR_INDEX]
            virt_install_cmd = self.VIRT_INSTALL_CMD_TO_CREATE_WINDOWS_VM_WITH_MAC_ADDRESS.format(vm_name, memory_size,
                                                                                                no_of_cpu,
                                                                                                image_path,
                                                                                                current_network_interface_name,
                                                                                                os_variant, mac_id,
                                                                                                disk_size,
                                                                                                virtio_win_iso_file_path,
                                                                                                win_kickstart_iso_file_path,
                                                                                                sut_ip_iso)
            # self.__MAC_ADDR_INDEX += 1
        else:
            virt_install_cmd = self.VIRT_INSTALL_CMD_TO_CREATE_WINDOWS_VM.format(vm_name, memory_size, no_of_cpu,
                                                                               image_path,
                                                                               current_network_interface_name,
                                                                               os_variant, disk_size,
                                                                               virtio_win_iso_file_path,
                                                                               win_kickstart_iso_file_path,
                                                                               sut_ip_iso)
        if vm_create_async:
            create_vm_result = self._common_content_lib.execute_sut_cmd_async(virt_install_cmd, "WINDOWS VM creation",
                                                                              vm_creation_timeout, ps_name=vm_name)
            self._log.info("Successfully executed virt-install to create the {} WINDOWS VM".format(vm_name))
        else:
            create_vm_result = self._common_content_lib.execute_sut_cmd(virt_install_cmd, "WINDOWS VM creation",
                                                                        vm_creation_timeout)
            self._log.debug("'virt-install' command response \n{}".format(create_vm_result))
            if vm_name and "Domain creation completed." and "Restarting guest." not in create_vm_result:
                raise RuntimeError("Failed to create the {} VM".format(vm_name))
            self._log.info("Successfully create the {} WINDOWS VM".format(vm_name))

    def get_free_mac_from_available_list(self, os_type_lower, vm_name_upper, nesting_level):
        """
        Get the free MAC ID from the list of available MAC address list
        param os_type_lower: OS Type of VM in lower case
        param vm_name_upper: VM Name in upper case
        param nesting_level: VM Nesting Level

        return mac_id: free mac address
        """
        mac_id = ""
        mac_id_list = self._common_content_configuration.get_mac_address_for_vm(os_type_lower,
                                                                                vm_name_upper,
                                                                                nesting_level)

        vm_mac_list_used = self.get_mac_ids_used_in_sut()
        for mac_index in range(self.__MAC_ADDR_INDEX, len(mac_id_list)):
            mac_id = mac_id_list[mac_index]
            if mac_id.lower() in vm_mac_list_used:
                continue
            else:
                self.__MAC_ADDR_INDEX = mac_index + 1
                break
        return mac_id

    def get_mac_ids_used_in_sut(self):
        """
        Get the free MAC ID from the list of available MAC address list

        return mac_id: free mac address
        """
        vm_list_in_sut = []
        mac_used_list_in_sut = []
        vm_list_in_sut_out = self._common_content_lib.execute_sut_cmd("virsh list --all",
                                                                          "virsh list --all",
                                                                          self._command_timeout)
        vm_list_in_sut_out_res = re.findall("^\s+\d+\s+.*\s+", vm_list_in_sut_out, re.MULTILINE | re.IGNORECASE)
        vm_list_in_sut_out_res1 = re.findall("^\s+-\s+.*\s+", vm_list_in_sut_out, re.MULTILINE | re.IGNORECASE)
        vm_list_in_sut_out_res.extend(vm_list_in_sut_out_res1)
        if vm_list_in_sut_out_res is not "":
            for vm_element in vm_list_in_sut_out_res:
                vm_elem_split = vm_element.split()
                vm_list_in_sut.append(vm_elem_split[1])

        for vm_in_vmlist in vm_list_in_sut:
            vm_mac_list_in_sut_out = self._common_content_lib.execute_sut_cmd("virsh domiflist {}".format(vm_in_vmlist),
                                                                              "virsh domiflist {}".format(vm_in_vmlist),
                                                                              self._command_timeout)
            mac = re.search(r'([0-9A-F]{2}[:-]){5}([0-9A-F]{2})', vm_mac_list_in_sut_out, re.I).group()
            mac_used_list_in_sut.append(mac.lower())
        return mac_used_list_in_sut

    def create_runtime_iso_sut(self, vm_name):
        """
        Create the ISO file for SUT with files to be passed to VM dynamically
        param vm_name: VM Name

        return iso_name: name of iso file
        """
        iso_name = "{}_iso.iso".format(vm_name)
        iso_folder_name = "{}_iso".format(vm_name)
        create_iso_folder_cmd = "mkdir -p /home/{}".format(iso_folder_name)
        self._install_collateral.yum_install(package_name="genisoimage")
        create_iso_cmd = "mkisofs -J -o {} /home/{}".format(iso_name, iso_folder_name)

        sut_ip = self.get_sut_ip()
        self._log.info("IP address of the SUT {}".format(sut_ip))

        create_sup_ip_file_cmd = "echo {} > /home/{}/sutip".format(sut_ip, iso_folder_name)

        create_iso_folder_result = self._common_content_lib.execute_sut_cmd_no_exception(create_iso_folder_cmd,
                                                            "Creating ISO folder : {}".format(create_iso_folder_cmd),
                                                            self._command_timeout,
                                                            ignore_result="ignore")
        self._log.info("Create ISO folder result: {}".format(create_iso_folder_result))

        create_sup_ip_file_res = self._common_content_lib.execute_sut_cmd_no_exception(create_sup_ip_file_cmd,
                                                                                  "Creating file with IP  : {}".format(
                                                                                      create_sup_ip_file_cmd),
                                                                                  self._command_timeout,
                                                                                  ignore_result="ignore")
        self._log.info("Create file with sut ip result: {}".format(create_sup_ip_file_res))

        create_iso_result = self._common_content_lib.execute_sut_cmd_no_exception(create_iso_cmd,
                                                                                         "Creating ISO  : {}".format(
                                                                                             create_iso_cmd),
                                                                                         self._command_timeout,
                                                                                         ignore_result="ignore")
        self._log.info("Create ISO result: {}".format(create_iso_result))
        return iso_name

    def create_vm_from_template(self, vm_name, memory_size, vm_creation_timeout, gen=1):
        """
        Execute the the command to create a VM from an existing template base image in vhdx format.

        :param vm_name: Name of the new VM
        :param memory_size: Size of the VM memory
        :param vm_creation_timeout: timeout for vm creation
        :param gen: generation
        :raise: NotImplementedError
        """
        raise NotImplementedError

    def kill_running_tool_in_vm(self, tool_name, common_content_lib=None):
        """
        Terminate stress tool process.
        :param tool_name: Name of the stress app tool.
        :param common_content_lib: object to execute the command
        :return : None
        :raise: Raise RuntimeError Exception if failed to kill the stress tool process.
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        self._log.info("killing {} tool".format(tool_name))
        check_running_cmd = "ps -A | grep -i {}"
        check_tool = re.search("{}".format(tool_name), check_running_cmd, flags=re.IGNORECASE | re.M)
        if check_tool is None:
            self._log.warning("Warn: killing {} tool not needed as process does not exists!".format(tool_name))
            return

        common_content_lib.execute("pkill {}".format(tool_name), self._command_timeout)
        not_killed = True
        while not_killed:
            time.sleep(60)  # give some time for app to terminate itself
            command_result = common_content_lib.execute(check_running_cmd.format(tool_name), self._command_timeout)
            self._log.debug(command_result.stdout)
            if tool_name not in command_result.stdout:
                self._log.info("{} tool is still running... killing again..".format(tool_name))
                common_content_lib.execute("killall {}".format(tool_name), self._command_timeout)
                continue
            else:
                not_killed = False
            check_running_cmd = "ps -A | grep -i {}"
            check_tool = re.search("{}".format(tool_name), check_running_cmd, flags=re.IGNORECASE | re.M)
            if check_tool is None:
                self._log.warning(" process {} already killed!".format(tool_name))
                break
        command_result = common_content_lib.execute(check_running_cmd.format(tool_name), self._command_timeout)
        self._log.debug(command_result.stdout)
        if tool_name not in command_result.stdout:
            raise RuntimeError('{} tool not killed'.format(tool_name))

    def _vp_reboot_linux_vm(self, vm_name, use_shutdown_resume=None):
        """
        This method is to Reboot the VM

        :param vm_name: Name of the VM, which is going to be rebooted
        :return: None
        """
        self._log.info("Rebooting up the VM {}".format(vm_name))
        cmd = "virsh destroy {} --graceful"
        cmd_result = self._common_content_lib.execute_sut_cmd(cmd.format(vm_name),
                                                              "force off VM {}".format(vm_name),
                                                              self._command_timeout)
        cmd_start = "virsh start {}"
        cmd_result = self._common_content_lib.execute_sut_cmd(cmd_start.format(vm_name),
                                                              "start VM {}".format(vm_name),
                                                              self._command_timeout)
        #        if use_shutdown_resume is not None:

    #           self.shutdown_linux_vm(vm_name)
    #           self.resume_linux_vm(vm_name)
    #       else:
    #           cmd_result = self._common_content_lib.execute_sut_cmd(self.REBOOT_VM_COMMAND
    #                                                                .format(vm_name),
    #                                                                "create snapshot of VM {}".format(vm_name),
    #                                                                self._command_timeout)
    #      self._log.info("Successfully rebooted VM {} : result {}\n"
    #                     .format(vm_name, cmd_result))

    def create_bridge_network(self, bridge_name="br0", vm_name=None):
        """
        Method to create the network bridge on SUT.

        :raise: NotImplementedError
        """
        try:
            network_interface_name = self._is_available_network_bridge_interface_linux()
            if network_interface_name == bridge_name:
                ip_addr_show1 = self.os.execute("ip addr show | grep {}".format(bridge_name),
                                                self._command_timeout,
                                                cwd=self.ROOT_PATH)
                check_virbr0_active = re.search("{}:\s+.*NO-CARRIER.*DOWN.*".format(bridge_name), ip_addr_show1.stdout,
                                                re.I | re.M)

                if check_virbr0_active != None and check_virbr0_active != "":
                    self._log.info("Virtual bridge {} is not active, recreate it".format(bridge_name))
                    self.os.execute("nmcli conn down {}; nmcli conn del {};".format(bridge_name, bridge_name),
                                    self._command_timeout,
                                    cwd=self.ROOT_PATH)
                else:
                    self._log.info("Virtual bridge {} is already active".format(bridge_name))
                    return
            self._log.info("Deleting the existing network-scripts folder from {}".format(self.ROOT_PATH))
            delete_result = self.os.execute("rm -r {}".format(self.NETWORK_SCRIPTS.strip("/")), self._command_timeout,
                                            cwd=self.ROOT_PATH)
            self._log.debug("{} folder deleted successfully \n {}".format(self.NETWORK_SCRIPTS, delete_result.stdout))
            self._log.error("{} folder is not existed \n {}".format(self.NETWORK_SCRIPTS, delete_result.stderr))

            self._log.info("copy {} folder under {}".format(self.SYSCONFIG_SCRIPTS_PATH + self.NETWORK_SCRIPTS,
                                                            self.ROOT_PATH))
            self._common_content_lib.execute_sut_cmd("cp -rf {} {}".format(self.SYSCONFIG_SCRIPTS_PATH +
                                                                           self.NETWORK_SCRIPTS,
                                                                           self.ROOT_PATH),
                                                     "backup 'network-scripts' folder",
                                                     self._command_timeout)
            self._log.info("Successfully taken the backup of {} folder".format(self.NETWORK_SCRIPTS))

            network_interface_name = self._get_current_network_interface_linux()
            for command in self.DISABLE_NETWORK_MANAGER_CMDS:
                cmd_result = self.os.execute(command, self._command_timeout)
                self._log.debug(cmd_result.stdout)
                self._log.error(cmd_result.stderr)
            self._log.info("Successfully ran all the commands to disable NetworkManager")
            # self._add_bridge_in_network_scripts(network_interface_name)
            # self._create_bridge_network_file()
            self._add_vir_bridge_in_network_scripts(bridge_name, network_interface_name)
            self._create_vir_bridge_network_file(bridge_name)

        except Exception as ex:
            self.remove_bridge_network()
            raise ("Not able to create Bridge Network on SUT due to {}".format(ex))
        finally:
            for command in self.ENABLE_NETWORK_MANAGER_CMDS:
                cmd_result = self.os.execute(command, self._command_timeout)
                self._log.debug(cmd_result.stdout)
                self._log.error(cmd_result.stderr)
            cmd_result = self.os.execute("systemctl restart NetworkManager", self._command_timeout)
            self._log.debug(cmd_result.stdout)
            self._log.error(cmd_result.stderr)
            if vm_name is None:
                try:
                    self._common_content_lib.perform_os_reboot(self._reboot_timeout)
                except:
                    pass
            else:
                self._vp_reboot_linux_vm(vm_name)



    def get_sut_ip(self):
        """
        Method to get the ip address of the sut
        """
        sut_br_ip_address = self.get_sut_bridge_ip_linux()
        sut_ip_address = self.get_sut_ip_linux()
        if sut_br_ip_address is None and sut_ip_address is None:
                raise RuntimeError("Unable to get the current network interface ip")

        if sut_br_ip_address is not None:
            return sut_br_ip_address
        elif sut_ip_address is not None:
            return sut_ip_address

    def get_sut_bridge_ip_linux(self):
        """
        Method to get the ip address of the bridge
        """
        network_interface_ip = self._common_content_lib.execute_sut_cmd(self.GET_NETWORK_BRIDGE_INTERFACE_IP_CMD,
                                                                        "get current bridge n/w interface name",
                                                                        self._command_timeout)
        if not network_interface_ip:
            self._log.error("Unable to get the current network interface ip")
            return None
        ip_address = network_interface_ip.split('/')[0]
        self._log.debug("Current Network Interface ip is: {}".format(ip_address))
        return ip_address

    def get_sut_ip_linux(self):
        """
        Private method to get the current network interface IP of linux SUT

        :return network_interface_ip: IP of the current active network interface
        :raise: RuntimeError
        """
        self._log.info("Getting Current Network Interface IP")
        network_interface_ip = self._common_content_lib.execute_sut_cmd(self.GET_NETWORK_INTERFACE_NAME_IP_CMD,
                                                                          "get current network interface name",
                                                                          self._command_timeout)
        if not network_interface_ip:
            self._log.error("Unable to get the current network interface ip")
            return None
        ip_address = network_interface_ip.split('/')[0]
        self._log.debug("Current Network Interface ip is: {}".format(ip_address))
        return ip_address

    def try_to_connect_to_qemu_vm(self, vm_name):
        # ssh_port = self.qemu_vm_list[vm_name]["ssh_port"]
        ssh_port = self.get_ssh_port_qemu_vm_linux(vm_name)
        cmd = "sshpass -p password ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {} root@localhost".format(ssh_port)

        rcode = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._command_timeout)
        return rcode == 0

    def get_all_qemu_vm_running(self):
        """
        get all the qemu VMs running in system
        :return:
        """
        qemu_bin = os.path.basename(self.os_kernel_version())
        cmd = "lsof | grep -v -i screen | grep -v libvirt | grep {}| grep -v grep".format(qemu_bin)
        # cmd = "lsof | grep -v SCREEN| grep {}| grep -v grep".format(qemu_bin)
        std_out = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._command_timeout)
        qemu_list = std_out.split("\n")
        vm_list = []
        for vm_cmd in qemu_list:
            vm_n = re.search(".*-name\s.*\s-machine.*", vm_cmd, re.M | re.I)
            if vm_n is not None and vm_n != "" and vm_n not in vm_list:
                vm_list.append(vm_n.group(0).split(" ")[2].strip())
        return vm_list

    def is_qemu_vm_running(self, vm_name):
        """
        function get_running_vm
        :param vm_name:
        :return:
        """
        self._log.info("cheking if qemu vm running ...{}".format(vm_name))
        qemu_bin = os.path.basename(self.os_kernel_version())

        cmd = "ps -ef | grep -v -i screen | grep -v libvirt | grep {} | grep {} | wc -l".format(qemu_bin, vm_name)
        # cmd = "lsof | grep -v SCREEN | grep -v libvirt | grep {} | grep {} | wc -l".format(qemu_bin, vm_name)
        std_out = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._command_timeout)
        if int(std_out.strip()) != 0:
            return True
        return False

    def shutdown_qemu_vm(self, vm_name):
        """
        shutdown VM
        """
        cmd = "poweroff"
        self.execute_command_on_qemu_vm(vm_name=vm_name, cmd=cmd, cmd_str=cmd,
                                                     cmd_path="/", execute_timeout=self._command_timeout)
        # self._common_content_lib.execute_sut_cmd(cmd, cmd, self._command_timeout)
        time.sleep(30)

    def check_if_vm_is_qemu_vm(self, vm_name):
        """
        This checks if VM was created using qemu command and is running,
        Please Note it must be used for VMs which are created in CURRENT execution of script
        """
        if False == self.is_qemu_vm_running(vm_name):
            return False
        if vm_name not in self.qemu_vm_list:
            return False
        return True

    def destroy_qemu_vm(self, vm_name, vm_resource_keep_safe=None):
        """
        Method to destroy the VM & it's resources

        :param vm_name: Name of the VM to destroy
        :param vm_resource_keep_safe: If this is not None, VM resource will be cleaned
        :raise: NotImplementedError
        """
        qemu_bin = os.path.basename(self.os_kernel_version())

        cmd = "ps -ef | grep -v -i screen | grep -v libvirt | grep {} | grep {} | wc -l".format(qemu_bin, vm_name)
        # cmd = "lsof | grep -v SCREEN | grep -v libvirt | grep {} | grep {} | wc -l".format(qemu_bin, vm_name)
        std_out = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._command_timeout)
        if int(std_out.strip()) == 0:
            return
        qemu_bin = os.path.basename(self.os_kernel_version())
        self._log.info("trying to kill {}".format(vm_name))
        cmd = "ps -ef | grep -v -i screen | grep -v libvirt | grep {} | grep {}".format(qemu_bin, vm_name)
        # cmd = "ps -ef | grep -v SCREEN | grep -v libvirt | grep {} | grep {}".format(qemu_bin, vm_name)
        std_out = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._command_timeout)
        pid_proc = re.findall("\d+", std_out, re.I|re.M)
        pid0 = pid_proc[0]
        # pid1 = pid_proc[1]
        cmd = "kill {}".format(pid0)
        self.os.execute(cmd, self._command_timeout)
        # wipe all screen sessions which are invalid
        cmd = "screen -wipe"
        try:
            self.os.execute(cmd, self._command_timeout)
        except Exception as ex:
            pass
        # remove from valid qemu VM list
        if vm_name in self.qemu_vm_list:
           self.qemu_vm_list.pop(vm_name)
        return True

    def destroy_vm(self, vm_name, vm_resource_keep_safe=None):
        """
        Method to destroy the VM & it's resources

        :param vm_name: Name of the VM to destroy
        :param vm_resource_keep_safe: If this is not None, VM resource will be cleaned
        :raise: NotImplementedError
        """
        # retry 3 times to make sure cleanup properly done
        # check if it is vm created with qemu command
        if True == self.is_qemu_vm_running(vm_name):
            self.destroy_qemu_vm(vm_name, vm_resource_keep_safe)
            self._log.debug("Destroyed Qemu VM resources {}".format(vm_name))
            self._log.info("Destroyed Qemu VM resources {}".format(vm_name))
            return

        for retry_cnt in range(0,3):
            vm_list = self.os.execute("virsh list --all", self._command_timeout)
            if vm_name in vm_list.stdout:
                shutdown_result = self.os.execute("virsh shutdown {}".format(vm_name), self._command_timeout)
                self._log.debug("Shutdown VM \n{}".format(shutdown_result.stdout))
                self._log.error("Shutdown VM \n{}".format(shutdown_result.stderr))
                destroy_result = self.os.execute("virsh destroy {}".format(vm_name), self._command_timeout)
                self._log.debug("Destroy VM \n{}".format(destroy_result.stdout))
                self._log.error("Destroy VM \n{}".format(destroy_result.stderr))
                if vm_resource_keep_safe is None:
                    destroy_vm_resources = self.os.execute("virsh undefine --domain {} --remove-all-storage".format(vm_name),
                                                           self._command_timeout)
                    self._log.debug("Destroy VM resources \n{}".format(destroy_vm_resources.stdout))
                    self._log.error("Destroy VM resources \n{}".format(destroy_vm_resources.stderr))
            else:
                break
        if vm_resource_keep_safe is None:
            self._log.info("Successfully destroyed the VM {} & it's resources".format(vm_name))
        else:
            self._log.info("Successfully destroyed the VM {}.".format(vm_name))

    def find_vm_state(self, vm_name):
        """
        This method is to check the status of the VM.
        """
        state = "invalid_vm"
        virsh_list_result = self._common_content_lib.execute_sut_cmd(self.CHECK_VM_STATUS.format(vm_name),
                                                                       "Run virsh list --all", self._command_timeout)
        data = re.search(r".*\d+\s+{}\s+.*".format(vm_name), virsh_list_result, flags=re.IGNORECASE | re.M)
        if data is not None:
            data = data.group()
            state = str(data).split(" ")[-1:]
            self._log.info("VM {} found with State {} \n".format(vm_name, state))
            return state
        return state


    def check_if_vm_exist(self, vm_name):
        """
        This method is to check the status of the VM.
        """
        state = "invalid_vm"
        virsh_list_result = self._common_content_lib.execute_sut_cmd(self.CHECK_VM_STATUS.format(vm_name),
                                                                       "Run virsh list --all", self._command_timeout)
        data = re.search(r".*\d+\s+{}\s+.*".format(vm_name), virsh_list_result, flags=re.IGNORECASE | re.M)
        if data is not None:
            data = data.group()
            state = str(data).split(" ")[-1:]
            testlist = ["running", "paused", "shut off", "idle"]
            if any(elm in state for elm in testlist):
                self._log.info("VM {} found with State {} \n".format(vm_name, state))
                return True
            else:
                self._log.debug("Could not get valid VM {} \n".format(vm_name))
                self._log.error("Could not get valid VM {} \n".format(vm_name))
                raise RuntimeError("Could not get valid VM {}\n".format(vm_name))

    def get_qemu_vm_ip(self, vm_name):
        """
        Method to get the IPV4 address of the given VM

        :param vm_name: Name of the VM to get the IP
        :return vm_ip: IPV4 address of the given VM
        :raise: None
        """
        ssh_port = self.get_ssh_port_qemu_vm_linux(vm_name)
        cmd = "sshpass -p password ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {} root@127.0.0.1 {}".format(ssh_port, self.GET_NETWORK_INTERFACE_NAME_DYNAMIC_IP_CMD)

        network_interface_ip = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._command_timeout)

        if not network_interface_ip:
            self._log.error("Unable to get the current network interface ip")
            return None
        ip_address = network_interface_ip.split('/')[0]
        self._log.debug("Current Network Interface ip is: {}".format(ip_address))
        return ip_address

    def get_vm_ip(self, vm_name):
        """
        Method to get the IPV4 address of the given VM

        :param vm_name: Name of the VM to get the IP
        :return vm_ip: IPV4 address of the given VM
        :raise: None
        """
        if True == self.is_qemu_vm_running(vm_name):
            return self.get_qemu_vm_ip(vm_name)

        current_active_network = self._get_current_network_interface_linux()
        ip_data_result = self._common_content_lib.execute_sut_cmd("ifconfig {}".format(current_active_network),
                                                                  "get sut ip", self._command_timeout)
        sut_ip = re.search(r'((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9])', ip_data_result, re.I) \
            .group()
        subnet_ip = ".".join(sut_ip.split(".")[:1]) + "."
        self._log.info("Getting the VM IP")
        cmd_data = self._common_content_lib.execute_sut_cmd("virsh -q domifaddr {} --source agent | grep {}".format(
            vm_name, subnet_ip), "get {} vm network info".format(vm_name), self._command_timeout)
        self._log.debug("{} VM network information : \n{}".format(vm_name, cmd_data))
        vm_ip = re.search(r'((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9])', cmd_data, re.I).group()
        self._log.info("IPV4 address of {} is: {}".format(vm_name, vm_ip))
        return vm_ip

    def get_nested_vm_ip(self, vm_name, nesting_level=None):
        """
        Method to get the IPV4 address of the given VM

        :param vm_name: Name of the VM to get the IP
        :return vm_ip: IPV4 address of the given VM
        :raise: None
        """
        if True == self.is_qemu_vm_running(vm_name):
            return self.get_qemu_vm_ip(vm_name)

        current_active_network = self._get_current_network_interface_linux(nesting_level)
        ip_data_result = self._common_content_lib.execute_sut_cmd("ifconfig {}".format(current_active_network),
                                                                  "get sut ip", self._command_timeout)
        sut_ip = re.search(r'((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9])', ip_data_result, re.I) \
            .group()
        subnet_ip = ".".join(sut_ip.split(".")[:1]) + "."
        self._log.info("Getting the VM IP")
        cmd_data = self._common_content_lib.execute_sut_cmd("virsh -q domifaddr {} --source agent | grep {}".format(
            vm_name, subnet_ip), "get {} vm network info".format(vm_name), self._command_timeout)
        self._log.debug("{} VM network information : \n{}".format(vm_name, cmd_data))
        vm_ip = re.search(r'((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9])', cmd_data, re.I).group()
        self._log.info("IPV4 address of {} is: {}".format(vm_name, vm_ip))
        return vm_ip

    def remove_bridge_network(self):
        """
        Method to remove the existed network bridge on SUT.

        :return:None
        :raise: None
        """
        try:
            self._log.info("removing current bridge")
            self._common_content_lib.execute_sut_cmd("echo y | cp -rf {} {}".format(self.ROOT_PATH +
                                                                                    self.NETWORK_SCRIPTS,
                                                                                    self.SYSCONFIG_SCRIPTS_PATH),
                                                     "copying back the network scripts folder under sysconfig",
                                                     self._command_timeout)
            self._log.info("Successfully copied back the network-scripts folder")
            br0_file_path = self.SYSCONFIG_SCRIPTS_PATH + self.NETWORK_SCRIPTS + "/ifcfg-br0"
            cmd_result = self.os.execute("rm -f {}".format(br0_file_path), self._command_timeout)
            self._log.debug("delete command stdout:\n {}".format(cmd_result.stdout))
            self._log.error("delete command stderr:\n {}".format(cmd_result.stderr))
        except Exception as ex:
            raise ("Unable to remove the network bridge due to : {}".format(ex))
        finally:
            for command in self.ENABLE_NETWORK_MANAGER_CMDS:
                cmd_result = self.os.execute(command, self._command_timeout)
                self._log.debug(cmd_result.stdout)
                self._log.error(cmd_result.stderr)
            self._common_content_lib.perform_os_reboot(self._reboot_timeout)

    def create_vm_host(self, os_subtype, os_version, kernel_vr, vm_username, vm_password, vm_ip):
        """
        Method to create os executable object for given VM.

        :param vm_ip: ip of the VM OS
        :param vm_username: username of the VM OS
        :param os_version: os version
        :param os_subtype: os subtype
        :param kernel_vr: kernel version
        :raise: None
        :return vm_os_obj: callable os object for VM
        """
        if os_subtype in [VMs.WINDOWS]:
            os_name = OperatingSystems.WINDOWS
        else:
            vm_password = self.__get_linux_vm_password()
            os_name = self.os.os_type
        vm_cfg_opts = ElementTree.fromstring(VM_CONFIGURATION_FILE.format(os_name, os_subtype, os_version, kernel_vr,
                                                                          vm_username, vm_password, vm_ip))
        vm_os_obj = ProviderFactory.create(vm_cfg_opts, self._log)
        return vm_os_obj

    def _copy_kstart_to_sut(self, kick_start_file=None):
        """
        Private method to copy the kick-starter file to the linux SUT

        :return : None
        """
        if kick_start_file is None:
            kick_start_file = self.KSTART_FILE_NAME
        self._log.info("Copying Kick-starter file from HOST to SUT")
        kstart_file_path = self._install_collateral.download_tool_to_host(kick_start_file)
        self.os.copy_local_file_to_sut(kstart_file_path, self.ROOT_PATH)
        self._log.info("Successfully copied the Kick-starter file to SUT")

    def _verify_iso_existance(self, vm_name):
        """
         Method to verify if ISO image already present on the windows SUT

        :param vm_name: Name of the new VM. Either "linux" or "windows" should be included in the name
        :return : Complete location of ISO image
        """
        self._log.info("Check if ISO image already present on SUT for given VM")
        cmd_result = []

        if "rhel" in vm_name.lower():
            iso_filename = self.SUT_ISO_IMAGE_LOCATION + os.path.basename(self._linux_image_host_location)
            cmd_result = self.os.check_if_path_exists(iso_filename)
            self._log.info("Existing ISO image: {}".format(iso_filename))

        elif "centos" in vm_name.lower():
            iso_filename = self.SUT_ISO_IMAGE_LOCATION + os.path.basename(self._centos_image_host_location)
            cmd_result = self.os.check_if_path_exists(iso_filename)
            self._log.info("Existing ISO image: {}".format(iso_filename))

        elif "windows" in vm_name.lower():
            iso_filename = self.SUT_ISO_IMAGE_LOCATION + os.path.basename(self._windows_image_host_location)
            cmd_result = self.os.check_if_path_exists(iso_filename)
            self._log.info("Existing ISO image: {}".format(iso_filename))

        if cmd_result:
            return iso_filename
        return False

    def _verify_img_base_existance(self, vm_name):
        """
         Method to verify if IMG raw image already present on the windows SUT

        :param vm_name: Name of the new VM. Either "linux" or "windows" should be included in the name
        :return : Complete location of ISO image
        """
        self._log.info("Check if RAW .img image already present on SUT for given VM")
        cmd_result = []

        # create a dir in /home folder with vm_name_img and then copy .img file there to be used with VM

        if "rhel" in vm_name.lower():
            img_filename = self.SUT_RAW_IMG_BASE_IMAGE_LOCATION + os.path.basename(self._linux_raw_image_host_location)
            cmd_result = self.os.check_if_path_exists(img_filename)
            self._log.info("Existing ISO image: {}".format(img_filename))

        elif "centos" in vm_name.lower():
            img_filename = self.SUT_RAW_IMG_BASE_IMAGE_LOCATION + os.path.basename(self._centos_raw_image_host_location)
            cmd_result = self.os.check_if_path_exists(img_filename)
            self._log.info("Existing ISO image: {}".format(img_filename))

        elif "windows" in vm_name.lower():
            self._log.info("Windows not supported...")
            return False

        if cmd_result:
            return img_filename
        return False

    def _copy_raw_image_base_to_linux_sut(self, vm_name=None):
        """
        Private method to copy the OS image file to the linux SUT

        :return : complete location of the copied OS Image file
        """
        self._log.info("Copying OS image to linux SUT")
        self._common_content_lib.execute_sut_cmd_no_exception("rm -rf {}".format(self.SUT_RAW_IMG_BASE_IMAGE_LOCATION), "To delete a folder",
                                                    self._command_timeout, self.ROOT_PATH, ignore_result="ignore")

        self._common_content_lib.execute_sut_cmd_no_exception("mkdir -p {}".format(self.SUT_RAW_IMG_BASE_IMAGE_LOCATION), "To Create a folder",
                                                    self._command_timeout, self.ROOT_PATH, ignore_result="ignore")
        img_filename = None
        img_location = None
        if vm_name is None:
            img_filename = os.path.basename(self._linux_raw_image_host_location)
            img_location = self._linux_raw_image_host_location
        else:
            vm_name_lower = vm_name.lower()
            vm_name_alpha = re.findall(r"^.*[a-zA-Z]", vm_name_lower)
            if "rhel" in vm_name.lower():
                img_filename = os.path.basename(self._linux_raw_image_host_location)
                img_location = self._linux_raw_image_host_location
            elif "centos" in vm_name.lower():
                img_filename = os.path.basename(self._centos_raw_image_host_location)
                img_location = self._centos_raw_image_host_location
            elif "windows" in vm_name.lower():
                raise NotImplementedError("{} Win VM type is not implemented".format(vm_name))
            else:
                raise NotImplementedError("{} VM type is not implemented".format(vm_name))

        if not os.path.exists(img_location):
            raise RuntimeError("Raw image file is not present. Please keep the ISO image file under {}"
                               .format(img_location))
        # cmd_result = self._common_content_lib.execute_sut_cmd("ls", "getting the folder content", self._command_timeout,
        #                                                       cmd_path=self.SUT_RAW_IMG_BASE_IMAGE_LOCATION)
        # self._log.debug("{} Folder contains :\n{}".format(self.SUT_RAW_IMG_BASE_IMAGE_LOCATION, cmd_result))
        img_path_on_sut = self.SUT_RAW_IMG_BASE_IMAGE_LOCATION
        if not self.os.check_if_path_exists(img_path_on_sut):
            self.os.copy_local_file_to_sut(img_location, self.SUT_RAW_IMG_BASE_IMAGE_LOCATION + img_filename)
            self._log.info("Successfully copied the .iso image file to {}".format(self.SUT_RAW_IMG_BASE_IMAGE_LOCATION))
        else:
            raise RuntimeError("Target path for ISO image: {} doesn't exist on SUT".format(img_location))
        return self.SUT_RAW_IMG_BASE_IMAGE_LOCATION + img_filename

    def _verify_imageforvm_img_existance(self, vm_name):
        """
         Method to verify if IMG raw image already present on the windows SUT

        :param vm_name: Name of the new VM. Either "linux" or "windows" should be included in the name
        :return : Complete location of ISO image
        """
        self._log.info("Check if RAW .img image already present on SUT for given VM")
        cmd_result = []

        # create a dir in /home folder with vm_name_img and then copy .img file there to be used with VM

        if "rhel" in vm_name.lower():
            img_filename = self.SUT_RAW_IMG_IMAGE_LOCATION.format(vm_name) + os.path.basename(self._linux_raw_image_host_location)
            cmd_result = self.os.check_if_path_exists(img_filename)
            self._log.info("Existing ISO image: {}".format(img_filename))

        elif "centos" in vm_name.lower():
            img_filename = self.SUT_RAW_IMG_IMAGE_LOCATION.format(vm_name) + os.path.basename(self._centos_raw_image_host_location)
            cmd_result = self.os.check_if_path_exists(img_filename)
            self._log.info("Existing ISO image: {}".format(img_filename))

        elif "windows" in vm_name.lower():
            self._log.info("Windows not supported...")
            return False

        if cmd_result:
            return img_filename
        return False

    def _copy_raw_imageforvm_to_sut_linux_sut(self, vm_name=None):
        """
        Private method to copy the OS image file to the linux SUT

        :return : complete location of the copied OS Image file
        """
        self._log.info("Copying OS image to linux SUT")
        self._common_content_lib.execute_sut_cmd_no_exception("rm -rf {}".format(self.SUT_RAW_IMG_IMAGE_LOCATION.format(vm_name)),
                             "To delete a folder",
                             self._command_timeout, self.ROOT_PATH, ignore_result="ignore")

        self._common_content_lib.execute_sut_cmd_no_exception("mkdir -p {}".format(self.SUT_RAW_IMG_IMAGE_LOCATION.format(vm_name)),
                                                 "To Create a folder",
                                                 self._command_timeout, self.ROOT_PATH, ignore_result="ignore")
        img_filename = None
        img_location = None
        if vm_name is None:
            img_filename = os.path.basename(self._linux_raw_image_host_location)
            img_location = self._linux_raw_image_host_location
        else:
            vm_name_lower = vm_name.lower()
            vm_name_alpha = re.findall(r"^.*[a-zA-Z]", vm_name_lower)
            if "rhel" in vm_name.lower():
                img_filename = os.path.basename(self._linux_raw_image_host_location)
                img_location = self._linux_raw_image_host_location
            elif "centos" in vm_name.lower():
                img_filename = os.path.basename(self._centos_raw_image_host_location)
                img_location = self._centos_raw_image_host_location
            elif "windows" in vm_name.lower():
                raise NotImplementedError("{} Win VM type is not implemented".format(vm_name))
            else:
                raise NotImplementedError("{} VM type is not implemented".format(vm_name))

        if not os.path.exists(img_location):
            raise RuntimeError("Raw image file is not present. Please keep the IMG image file under {}"
                               .format(img_location))
        # cmd_result = self._common_content_lib.execute_sut_cmd("ls", "getting the folder content", self._command_timeout,
        #                                                       cmd_path=self.SUT_RAW_IMG_BASE_IMAGE_LOCATION)
        # self._log.debug("{} Folder contains :\n{}".format(self.SUT_RAW_IMG_BASE_IMAGE_LOCATION, cmd_result))
        img_path_sut = self.SUT_RAW_IMG_IMAGE_LOCATION.format(vm_name)
        if not self.os.check_if_path_exists(img_path_sut):
            vm_name_lower_list = vm_name.lower().split("_")
            supported_vm_list = ["linux", "windows", "centos", "rhel", "ubuntu", "fedora"]
            if any(elm in vm_name_lower_list for elm in supported_vm_list):
                verify_img_image = self._verify_img_base_existance(vm_name)
                if not verify_img_image:
                    image_path = self._copy_raw_image_base_to_linux_sut(vm_name)
                else:
                    self._log.info("RAW Base image already present on SUT. Continue VM : {}Creation".format(vm_name))
            else:
                raise NotImplementedError("Only linux and windows VM type is supported and the VM name should contain "
                                          "windows/linux. {} VM type is not implemented".format(vm_name))

            self._common_content_lib.execute_sut_cmd("cp {} {}".format(
                                                                self.SUT_RAW_IMG_BASE_IMAGE_LOCATION + img_filename,
                                                                self.SUT_RAW_IMG_IMAGE_LOCATION.format(vm_name) + img_filename),
                                                     "getting the folder content", self._command_timeout,
                                                     cmd_path=self.ROOT_PATH)
            self._log.info("Successfully copied the .iso image file to {}".format(self.SUT_RAW_IMG_IMAGE_LOCATION.format(vm_name)))
        else:
            raise RuntimeError("Target path for ISO image: {} doesn't exist on SUT".format(img_location))
        return self.SUT_RAW_IMG_IMAGE_LOCATION.format(vm_name) + img_filename

    def _copy_iso_image_to_sut_linux_sut(self, vm_name=None):
        """
        Private method to copy the OS image file to the linux SUT

        :return : complete location of the copied OS Image file
        """
        self._log.info("Copying OS image to linux SUT")
        iso_filename = None
        iso_location = None
        if vm_name is None:
            iso_filename = os.path.basename(self._linux_image_host_location)
            iso_location = self._linux_image_host_location
        else:
            vm_name_lower = vm_name.lower()
            vm_name_alpha = re.findall(r"^.*[a-zA-Z]", vm_name_lower)
            if "rhel" in vm_name.lower():
                iso_filename = os.path.basename(self._linux_image_host_location)
                iso_location = self._linux_image_host_location
            elif "centos" in vm_name.lower():
                iso_filename = os.path.basename(self._centos_image_host_location)
                iso_location = self._centos_image_host_location
            elif "windows" in vm_name.lower():
                iso_filename = os.path.basename(self._windows_image_host_location)
                iso_location = self._windows_image_host_location

            else:
                raise NotImplementedError("{} VM type is not implemented".format(vm_name))

        if not os.path.exists(iso_location):
            raise RuntimeError("ISO image file is not present. Please keep the ISO image file under {}"
                               .format(iso_location))
        cmd_result = self._common_content_lib.execute_sut_cmd("ls", "getting the folder content", self._command_timeout,
                                                              cmd_path=self.SUT_ISO_IMAGE_LOCATION)
        self._log.debug("{} Folder contains :\n{}".format(self.SUT_ISO_IMAGE_LOCATION, cmd_result))
        if not self.os.check_if_path_exists(iso_location):
            self.os.copy_local_file_to_sut(iso_location, self.SUT_ISO_IMAGE_LOCATION + iso_filename)
            self._log.info("Successfully copied the .iso image file to {}".format(self.SUT_ISO_IMAGE_LOCATION))
        else:
            raise RuntimeError("Target path for ISO image: {} doesn't exist on SUT".format(iso_location))
        return self.SUT_ISO_IMAGE_LOCATION + iso_filename

    # def _copy_iso_image_to_sut_linux_sut(self):
    #     """
    #     Private method to copy the OS image file to the linux SUT
    #
    #     :return : complete location of the copied OS Image file
    #     """
    #     self._log.info("Copying OS image to linux SUT")
    #     file_name = os.path.basename(self._linux_image_host_location)
    #     if not os.path.exists(self._linux_image_host_location):
    #         raise RuntimeError("RHEL .iso image file is not present. Please keep the RHEL .iso image file under {}"
    #                            .format(self._linux_image_host_location))
    #     cmd_result = self._common_content_lib.execute_sut_cmd("ls", "getting the folder content", self._command_timeout,
    #                                                           cmd_path=self.SUT_ISO_IMAGE_LOCATION)
    #     self._log.debug("{} Folder contains :\n{}".format(self.SUT_ISO_IMAGE_LOCATION, cmd_result))
    #     if not self.os.check_if_path_exists(self.SUT_ISO_IMAGE_LOCATION + file_name):
    #         self.os.copy_local_file_to_sut(self._linux_image_host_location, self.SUT_ISO_IMAGE_LOCATION + file_name)
    #     self._log.info("Successfully copied the .iso image file to {}".format(self.SUT_ISO_IMAGE_LOCATION))
    #     return self.SUT_ISO_IMAGE_LOCATION + file_name

    def _get_nw_interface_name(self):
        """
        Support function for _get_current_network_interface_linux
        Private method to get the current network interface name of linux SUT

        :return network_interface_name: Name of the current active network interface
        :raise: RuntimeError
        """
        self._log.info("Getting Current Network Interface name")
        self._common_content_lib.execute_sut_cmd("systemctl restart NetworkManager; sync; sleep 30;",
                                                 "restart network manager to get update from network scripts",
                                                 self._command_timeout)
        network_interface_name = self._common_content_lib.execute_sut_cmd(self.GET_NETWORK_INTERFACE_NAME_DYNAMIC_CMD,
                                                                          "get current network interface name",
                                                                          self._command_timeout)
        self._log.info("Current Network Interface name is: {}".format(network_interface_name))
        self._log.debug("Current Network Interface name is: {}".format(network_interface_name))
        if not network_interface_name.strip():
            network_interface_name = self._common_content_lib.execute_sut_cmd(
                self.GET_NETWORK_INTERFACE_NAME_CMD1.format(self.sut_ip, "{print $NF; exit}"),
                "get current network interface name",
                self._command_timeout)
            self._log.info("Current Network Interface name is: {}".format(network_interface_name))

        return network_interface_name.strip()

    def _get_nw_interface_name_generic(self):
        """
        Support function for _get_current_network_interface_linux
        Private method to get the current network interface name of linux SUT

        :return network_interface_name: Name of the current active network interface
        :raise: RuntimeError
        """
        self._log.info("Getting Current Network Interface name")
        self._common_content_lib.execute_sut_cmd("systemctl restart NetworkManager; sync; sleep 30;",
                                                 "restart network manager to get update from network scripts",
                                                 self._command_timeout)
        network_interface_name = self._common_content_lib.execute_sut_cmd(self.GET_NETWORK_INTERFACE_NAME_DYNAMIC_CMD,
                                                                          "get current network interface name",
                                                                          self._command_timeout)
        self._log.info("Current Network Interface name is: {}".format(network_interface_name))
        self._log.debug("Current Network Interface name is: {}".format(network_interface_name))
        if not network_interface_name.strip():
            network_interface_name = self._common_content_lib.execute_sut_cmd(
                self.GET_NETWORK_INTERFACE_NAME_CMD,
                "get current network interface name",
                self._command_timeout)
            self._log.info("Current Network Interface name is: {}".format(network_interface_name))

        return network_interface_name.strip()

    def _check_if_nw_device_active(self, network_interface_name):
        """
        Support function for _get_current_network_interface_linux
        Private method to check if the current network interface is active

        :return True/False
        :raise: RuntimeError
        """
        nw_dev = network_interface_name.strip()
        ip_addr_show1 = self.os.execute("ip addr show | grep {}".format(nw_dev),
                                        self._command_timeout,
                                        cwd=self.ROOT_PATH)
        check_nwdev_active = re.search("{}:\s+.*NO-CARRIER.*DOWN.*".format(nw_dev), ip_addr_show1.stdout,
                                        re.I | re.M)

        if check_nwdev_active != None and check_nwdev_active != "":
            self._log.info("NW dev {} is not active, recreate it".format(nw_dev))
            self.os.execute("nmcli conn down {}; nmcli conn del {};".format(nw_dev, nw_dev),
                            self._command_timeout,
                            cwd=self.ROOT_PATH)
            return False
        else:
            self._log.info("NW dev {} is active".format(nw_dev))
            return True

    def _get_current_network_interface_linux(self, nesting_level=None):
        """
        Private method to get the current network interface name of linux SUT

        :return network_interface_name: Name of the current active network interface
        :raise: RuntimeError
        """
        self._log.info("Getting Current Network Interface name")
        self._common_content_lib.execute_sut_cmd("systemctl restart NetworkManager; sync; sleep 5;",
                                                 "restart network manager to get update from network scripts",
                                                 self._command_timeout)
        network_interface_name = self._common_content_lib.execute_sut_cmd(self.GET_NETWORK_INTERFACE_NAME_DYNAMIC_CMD,
                                                                          "get current network interface name",
                                                                          self._command_timeout)
        self._log.info("Current Network Interface name is: {}".format(network_interface_name))
        if not network_interface_name.strip():
            if nesting_level != None:
                get_net_if_cmd = self.GET_NETWORK_INTERFACE_NAME_CMD
            else:
                get_net_if_cmd = self.GET_NETWORK_INTERFACE_NAME_CMD1.format(self.sut_ip, "{print $NF; exit}")
            network_interface_name = self._common_content_lib.execute_sut_cmd(
                get_net_if_cmd,
                "get current network interface name",
                self._command_timeout)
            self._log.info("Current Network Interface name is: {}".format(network_interface_name))
            if not network_interface_name.strip():
                raise RuntimeError("Unable to get the current network interface name")
            else:
                if False == self._check_if_nw_device_active(network_interface_name):
                    # again try for correct active device
                    network_interface_name = self._get_nw_interface_name()
                    self._log.info("Current Network Interface name is: {}".format(network_interface_name))
                    if not network_interface_name.strip():
                        raise RuntimeError("Unable to get the current network interface name")
                else:
                    self._log.info("NW dev {} is active".format(network_interface_name))
        self._log.debug("Current Network Interface name is: {}".format(network_interface_name.strip()))
        return network_interface_name.strip()

    def copy_file_using_scp_cmd(self, host_ip, destination_path, host_file_path, common_content_lib):
        scp_cmd = "scp root@{}:{} {}".format(host_ip,host_file_path,destination_path)
        common_content_lib.execute_sut_cmd(scp_cmd,
                                           "SCP command to copy the file",
                                           self._command_timeout)

    def _get_current_network_interface(self, common_content_lib=None):
        """
        Private method to get the current network interface name of linux SUT

        :return network_interface_name: Name of the current active network interface
        :raise: RuntimeError
        """
        if common_content_lib is not None:
            self._common_content_lib = common_content_lib
        self._log.info("Getting Current Network Interface name")
        self._common_content_lib.execute_sut_cmd("systemctl restart NetworkManager",
                                                 "restart network manager to get update from network scripts",
                                                 self._command_timeout)
        network_interface_name = self._common_content_lib.execute_sut_cmd(self.GET_NETWORK_INTERFACE_NAME_DYNAMIC_CMD,
                                                                          "get current network interface name",
                                                                          self._command_timeout)
        self._log.info("Current Network Interface name is: {}".format(network_interface_name))
        if not network_interface_name.strip():
            network_interface_name = self._common_content_lib.execute_sut_cmd(
                self.GET_NETWORK_INTERFACE_NAME_CMD,
                "get current network interface name",
                self._command_timeout)
            self._log.info("Current Network Bridge Interface name is: {}".format(network_interface_name))
            if not network_interface_name.strip():
                raise RuntimeError("Unable to get the current network interface name")
            else:
                if False == self._check_if_nw_device_active(network_interface_name):
                    # again try for correct active device
                    network_interface_name = self._get_nw_interface_name_generic()
                    self._log.info("Current Network Interface name is: {}".format(network_interface_name))
                    if not network_interface_name.strip():
                        raise RuntimeError("Unable to get the current network interface name")
                else:
                    self._log.info("NW dev {} is active".format(network_interface_name))
        self._log.debug("Current Network Interface name is: {}".format(network_interface_name.strip()))
        return network_interface_name.strip()

    def _get_nw_bridge_interface_name(self):
        """
        Support function for _get_current_network_interface_linux
        Private method to get the current network interface name of linux SUT

        :return network_interface_name: Name of the current active network interface
        :raise: RuntimeError
        """
        self._log.info("Getting Current Network Interface name")
        self._common_content_lib.execute_sut_cmd("systemctl restart NetworkManager; sync; sleep 5;",
                                                 "restart network manager to get update from network scripts",
                                                 self._command_timeout)
        network_interface_name = self._common_content_lib.execute_sut_cmd(self.GET_NETWORK_BRIDGE_INTERFACE_NAME_CMD,
                                                                          "get current network interface name",
                                                                          self._command_timeout)
        self._log.info("Current Network Interface name is: {}".format(network_interface_name))
        self._log.debug("Current Network Interface name is: {}".format(network_interface_name))
        if not network_interface_name.strip():
            network_interface_name = self._common_content_lib.execute_sut_cmd(
                self.GET_NETWORK_BRIDGE_INTERFACE_NAME_WO_DYNAMIC_CMD.format(self.sut_ip, "{print $NF; exit}"),
                "get current network interface name",
                self._command_timeout)
            self._log.info("Current Network Interface name is: {}".format(network_interface_name))

        return network_interface_name.strip()

    def _get_current_network_bridge_interface_linux(self):
        """
        Private method to get the current network bridge interface name of linux SUT

        :return network_br_interface_name: Name of the current active network bridge interface
        :raise: RuntimeError
        """
        self._log.info("Getting Current Network Interface name")
        self._common_content_lib.execute_sut_cmd("systemctl restart NetworkManager",
                                                 "restart network manager to get update from network scripts",
                                                 self._command_timeout)
        network_br_interface_name = self._common_content_lib.execute_sut_cmd(self.GET_NETWORK_BRIDGE_INTERFACE_NAME_CMD,
                                                                          "get current network interface name",
                                                                          self._command_timeout)
        self._log.info("Current Network Bridge Interface name is: {}".format(network_br_interface_name))
        if not network_br_interface_name.strip():
            network_br_interface_name = self._common_content_lib.execute_sut_cmd(
                self.GET_NETWORK_BRIDGE_INTERFACE_NAME_WO_DYNAMIC_CMD,
                "get current network interface name",
                self._command_timeout)
            self._log.info("Current Network Bridge Interface name is: {}".format(network_br_interface_name))
            if not network_br_interface_name.strip():
                self._log.error("No Network Bridge Interface in system")
                raise RuntimeError("Unable to get the current network bridge interface name")
            else:
                if False == self._check_if_nw_device_active(network_br_interface_name):
                    # again try for correct active device
                    network_br_interface_name = self._get_nw_bridge_interface_name()
                    self._log.info("Current Network Bridge Interface name is: {}".format(network_br_interface_name))
                    if not network_br_interface_name.strip():
                        raise RuntimeError("Unable to get the current network Bridge interface name")
                else:
                    self._log.info("NW Bridge dev {} is active".format(network_br_interface_name))
        self._log.debug("Current Network Bridge Interface name is: {}".format(network_br_interface_name.strip()))
        return network_br_interface_name.strip()

    def _is_available_network_bridge_interface_linux(self):
        """
        Private method to get the current network bridge interface name of linux SUT

        :return network_br_interface_name: Name of the current active network bridge interface
        :raise: RuntimeError
        """
        self._log.info("Getting Current Network Interface name")
        self._common_content_lib.execute_sut_cmd("systemctl restart NetworkManager",
                                                 "restart network manager to get update from network scripts",
                                                 self._command_timeout)
        network_br_interface_name = self._common_content_lib.execute_sut_cmd(self.GET_NETWORK_BRIDGE_INTERFACE_NAME_CMD,
                                                                          "get current network interface name",
                                                                          self._command_timeout)
        self._log.info("Current Network Bridge Interface name is: {}".format(network_br_interface_name))
        if not network_br_interface_name.strip():
            # self._log.error("No Network Bridge Interface in system")
            network_br_interface_name = self._common_content_lib.execute_sut_cmd(
                self.GET_NETWORK_BRIDGE_INTERFACE_NAME_WO_DYNAMIC_CMD,
                "get current network interface name",
                self._command_timeout)
            self._log.info("Current Network Bridge Interface name is: {}".format(network_br_interface_name))
            if not network_br_interface_name.strip():
                self._log.error("No Network Bridge Interface in system")
                return None
        else:
            if False == self._check_if_nw_device_active(network_br_interface_name):
                self._log.error("No Active Bridge Interface in system")
                return None
            else:
                self._log.info("NW Bridge dev {} is active".format(network_br_interface_name))
        self._log.debug("Current Network Bridge Interface name is: {}".format(network_br_interface_name.strip()))
        return network_br_interface_name.strip()


    def _add_bridge_in_network_scripts(self, network_interface_name):
        """
        Private method to add the bridge param to the current network config file on linux SUT

        :param network_interface_name: current network interface name (ex:eth0)
        :raise: RuntimeError
        :return: None
        """
        self._log.info("Getting the MAC address of the SUT")
        # get the mac of the sut
        get_mac_result = self._common_content_lib.execute_sut_cmd(self.GET_MAC_ADDRESS_CMD.format(
            network_interface_name),
            "get MAC address of the current network interface",
            self._command_timeout)
        self._log.debug("Get MAC command result \n{}".format(get_mac_result))
        mac = re.search(r'([0-9A-F]{2}[:-]){5}([0-9A-F]{2})', get_mac_result, re.I).group()
        self._log.info("Current MAC address of the SUT is : {}".format(mac))
        hwaddr_str = "HWADDR={}".format(mac)
        macaddr_str = "MACADDR={}".format(mac)
        self._log.info("Checking the current network interface configuration file")
        # check the content of the current network interface configuration file
        nw_cfg_data = self._common_content_lib.execute_sut_cmd(self.CMD_TO_CHECK_NW_CONFIG_FILE.format(
            self.SYSCONFIG_SCRIPTS_PATH + self.NETWORK_SCRIPTS,
            network_interface_name),
            "get ifcfg data of '{}' interface".format(
                network_interface_name), self._command_timeout)
        self._log.debug("ifcfg data of {} network interface\n{}".format(network_interface_name, nw_cfg_data))

        # check if the HWADDR data is already present in the nw-config file or not
        self._log.debug("Adding HWADDR to ifcfg-{} file".format(network_interface_name))
        if hwaddr_str not in nw_cfg_data:
            self._common_content_lib.execute_sut_cmd(self.ADD_ADDR_NAME_TO_CONFIGURATION_FILE.format(hwaddr_str,
                                                                                                     self.SYSCONFIG_SCRIPTS_PATH + self.NETWORK_SCRIPTS,
                                                                                                     network_interface_name),
                                                     "adding HWADDR in Active Network interface",
                                                     self._command_timeout)

        self._log.info("Successfully added the HWADDR value in the network configuration file")

        # check if the MACADDR data is already present in the nw-config file or not
        self._log.debug("Adding MACADDR to ifcfg-{} file".format(network_interface_name))
        if macaddr_str not in nw_cfg_data:
            self._common_content_lib.execute_sut_cmd(self.ADD_ADDR_NAME_TO_CONFIGURATION_FILE.format(macaddr_str,
                                                                                                     self.SYSCONFIG_SCRIPTS_PATH + self.NETWORK_SCRIPTS,
                                                                                                     network_interface_name),
                                                     "adding MACADDR in Active Network interface",
                                                     self._command_timeout)

        self._log.info("Successfully added the MACADDR value in the network configuration file")

        self._common_content_lib.execute_sut_cmd(self.ADD_BRIDGE_NAME_TO_CONFIGURATION_FILE.format(
            self.SYSCONFIG_SCRIPTS_PATH + self.NETWORK_SCRIPTS,
            network_interface_name),
            "adding br0 in Active Network interface",
            self._command_timeout)

        self._log.info("Successfully added the network bridge param")

    def _create_bridge_network_file(self):
        """
        Private method to create the bridge network config file on linux SUT

        :raise: RuntimeError
        """
        self._log.info("Creating the ifcfg-br0 file")
        file_path = self.SYSCONFIG_SCRIPTS_PATH + self.NETWORK_SCRIPTS + "/ifcfg-br0"
        self._common_content_lib.execute_sut_cmd("touch {}".format(file_path), "create file", self._command_timeout)
        self._log.debug("ifcfg-br0 file is created")
        for index in range(0, len(self.BRIDGE_CONFIG_FILE_CONTENTS)):
            self._log.info("setting the param {}".format(self.BRIDGE_CONFIG_FILE_CONTENTS[index]))
            if index == 0:
                self._common_content_lib.execute_sut_cmd("echo {} | tee {}".format(self.BRIDGE_CONFIG_FILE_CONTENTS[
                                                                                       index], file_path),
                                                         "adding 1st line", self._command_timeout)
                self._log.debug("Added the content in the bridge configuration file")
            else:
                self._common_content_lib.execute_sut_cmd(r"sed -i '$ a\{}' {}".format(self.BRIDGE_CONFIG_FILE_CONTENTS[
                                                                                          index], file_path),
                                                         "adding next lines", self._command_timeout)
        interface_name = self._get_current_network_interface_linux()
        current_network_info = self._common_content_lib.execute_sut_cmd("ifconfig {} | grep inet".
                                                                        format(interface_name),
                                                                        "getting network info", self._command_timeout)
        network_info = current_network_info.split("\n")[0].strip().split()
        sut_ip, net_mask = network_info[1], network_info[3]
        self._common_content_lib.execute_sut_cmd(r"sed -i '$ a\IPADDR={}' {}".format(sut_ip, file_path),
                                                 "Adding IPADDR", self._command_timeout)
        self._common_content_lib.execute_sut_cmd(r"sed -i '$ a\NETMASK={}' {}".format(net_mask, file_path),
                                                 "Adding NETMASK", self._command_timeout)
        bridge_network_file_data = self._common_content_lib.execute_sut_cmd("cat {}".format(file_path),
                                                                            "print output of bridge network config "
                                                                            "file", self._command_timeout)
        self._log.debug("Current content of Bridge Network configuration file: \n{}".format(bridge_network_file_data))
        self._log.info("Added all the contents in the bridge configuration file")

    def check_if_file_exist(self, dir_name, file_name):
        """
        This will check for the file_name in dir_name

        :return file name / None
        """
        self._log.info("Getting the file name")
        list_of_files_op = self._common_content_lib.execute_sut_cmd("ls -1 {}".format(dir_name),
                                                                    "list of all files",
                                                                    self._command_timeout)
        list_of_files = list_of_files_op.splitlines()

        for file in list_of_files:
            if file == file_name:
                return file_name

        return None

    def get_ifcfg_file_for_nw_device(self, mac_addr, network_interface_name):
        """
        This will search for the file in /etc/sysconfig/network-scripts/ifcfg-*

        :return file name with given mac_addr
        :raise: Exception
        """
        try:
            self._log.info("Getting the ifconfig file")
            list_of_ifcfg_op = self._common_content_lib.execute_sut_cmd("ls -1 /etc/sysconfig/network-scripts",
                                                     "list all ifcfg-* files",
                                                     self._command_timeout)
            list_of_ifcfg = list_of_ifcfg_op.splitlines()
            self._log.info("Successfully taken list of file in folder {}".format(self.NETWORK_SCRIPTS))

            for file in list_of_ifcfg:
                if file.startswith("ifcfg") and file != "{}.bak".format(os.path.splitext(file)[0]):
                    file_data = self._common_content_lib.execute_sut_cmd("cat /etc/sysconfig/network-scripts/{}".format(file),
                                                     "read data from file",
                                                     self._command_timeout)
                    if re.search("HWADDR=", file_data):
                        mac_addr_read = re.findall("HWADDR=.*", file_data)[0].split("=")[1].strip()
                        if mac_addr_read.lower() == mac_addr.lower():
                            self._log.info("Successfully retrieve the file name {} with MAC {}".format(file, mac_addr))
                            return file
                    elif re.search("DEVICE=", file_data):
                        nw_if_name = re.findall("DEVICE=.*", file_data)[0].split("=")[1].strip()
                        if nw_if_name.lower() == network_interface_name.lower():
                            self._log.info("Successfully retrieve the file name {} with nw_interface_name {}".format(file, network_interface_name))
                            return file
        except Exception as ex:
            raise ("Could not retrieve the valid ifcfg-* file name with MAC {}".format(mac_addr))

    def _add_vir_bridge_in_network_scripts(self, bridge_name, network_interface_name):
        """
        Private method to add the bridge param to the current network config file on linux SUT

        :param network_interface_name: current network interface name (ex:eth0)
        :raise: RuntimeError
        :return: None
        """
        self._log.info("Getting the MAC address of the SUT")
        # get the mac of the sut
        get_mac_result = self._common_content_lib.execute_sut_cmd(self.GET_MAC_ADDRESS_CMD.format(
            network_interface_name),
            "get MAC address of the current network interface",
            self._command_timeout)
        self._log.debug("Get MAC command result \n{}".format(get_mac_result))
        mac = re.search(r'([0-9A-F]{2}[:-]){5}([0-9A-F]{2})', get_mac_result, re.I).group()
        self._log.info("Current MAC address of the SUT is : {}".format(mac))
        hwaddr_str = "HWADDR={}".format(mac)
        macaddr_str = "MACADDR={}".format(mac)
        nw_devie_name_str = "DEVICE={}".format(network_interface_name)
        self._log.info("Checking the current network interface configuration file")
        # check the content of the current network interface configuration file
        script_file_path = self.SYSCONFIG_SCRIPTS_PATH + self.NETWORK_SCRIPTS
        check_file_op = self.check_if_file_exist(script_file_path,
                                                 "ifcfg-{}".format(network_interface_name))
        if check_file_op is None:
            file_name_with_same_mac = self.get_ifcfg_file_for_nw_device("{}".format(mac), network_interface_name)
            nw_cfg_data = self._common_content_lib.execute_sut_cmd(self.CMD_TO_CHECK_DATA_IN_FILE.format(
                self.SYSCONFIG_SCRIPTS_PATH + self.NETWORK_SCRIPTS,
                file_name_with_same_mac),
                "get ifcfg data of '{}' interface".format(
                    file_name_with_same_mac), self._command_timeout)
            self._log.debug("ifcfg data of {} network interface\n{}".format(file_name_with_same_mac, nw_cfg_data))
            # check if the DEVICE NAME data is already present in the nw-config file or not
            self._log.debug("Adding DeviceName to {} ".format(file_name_with_same_mac))
            if nw_devie_name_str not in nw_cfg_data:
                self._common_content_lib.execute_sut_cmd(self.ADD_ADDR_NAME_TO_CONFIGURATION_FILENAME.format(
                    nw_devie_name_str,
                    self.SYSCONFIG_SCRIPTS_PATH + self.NETWORK_SCRIPTS,
                    file_name_with_same_mac),
                    "adding DEVICE in Active Network interface",
                    self._command_timeout)
            self._log.info("Successfully added the DEVICE value in the network configuration file")

            nw_cfg_file_create_result = self._common_content_lib.execute_sut_cmd_no_exception(
                "cp {}/{} {}/ifcfg-{}".
                    format(script_file_path, file_name_with_same_mac, script_file_path, network_interface_name),
                "create file with name ifcfg-{} interface".format(
                    network_interface_name), self._command_timeout, ignore_result="ignore")
            self._log.debug("create result for ifcfg data of {} network interface\n{}".format(network_interface_name,
                                                                                              nw_cfg_file_create_result))

        nw_cfg_data = self._common_content_lib.execute_sut_cmd(self.CMD_TO_CHECK_NW_CONFIG_FILE.format(
            self.SYSCONFIG_SCRIPTS_PATH + self.NETWORK_SCRIPTS,
            network_interface_name),
            "get ifcfg data of '{}' interface".format(
                network_interface_name), self._command_timeout)
        self._log.debug("ifcfg data of {} network interface\n{}".format(network_interface_name, nw_cfg_data))

        # check if the DEVICE NAME data is already present in the nw-config file or not
        self._log.debug("Adding DeviceName to ifcfg-{}".format(network_interface_name))
        if nw_devie_name_str not in nw_cfg_data:
            self._common_content_lib.execute_sut_cmd(self.ADD_ADDR_NAME_TO_CONFIGURATION_FILE.format(nw_devie_name_str,
                                                                                                     self.SYSCONFIG_SCRIPTS_PATH + self.NETWORK_SCRIPTS,
                                                                                                     network_interface_name),
                                                     "adding DEVICE in Active Network interface",
                                                     self._command_timeout)
        self._log.info("Successfully added the DEVICE value in the network configuration file")

        # check if the HWADDR data is already present in the nw-config file or not
        self._log.debug("Adding HWADDR to ifcfg-{} file".format(network_interface_name))
        if hwaddr_str not in nw_cfg_data:
            self._common_content_lib.execute_sut_cmd(self.ADD_ADDR_NAME_TO_CONFIGURATION_FILE.format(hwaddr_str,
                                                                                                     self.SYSCONFIG_SCRIPTS_PATH + self.NETWORK_SCRIPTS,
                                                                                                     network_interface_name),
                                                     "adding HWADDR in Active Network interface",
                                                     self._command_timeout)

        self._log.info("Successfully added the HWADDR value in the network configuration file")

        # check if the MACADDR data is already present in the nw-config file or not
        self._log.debug("Adding MACADDR to ifcfg-{} file".format(network_interface_name))
        if macaddr_str not in nw_cfg_data:
            self._common_content_lib.execute_sut_cmd(self.ADD_ADDR_NAME_TO_CONFIGURATION_FILE.format(macaddr_str,
                                                                                                     self.SYSCONFIG_SCRIPTS_PATH + self.NETWORK_SCRIPTS,
                                                                                                     network_interface_name),
                                                     "adding MACADDR in Active Network interface",
                                                     self._command_timeout)

        self._log.info("Successfully added the MACADDR value in the network configuration file")

        self._common_content_lib.execute_sut_cmd(self.ADD_VIRBRIDGE_NAME_TO_CONFIGURATION_FILE.format(
            bridge_name, self.SYSCONFIG_SCRIPTS_PATH + self.NETWORK_SCRIPTS,
            network_interface_name),
            "adding br0 in Active Network interface",
            self._command_timeout)

        self._log.info("Successfully added the network bridge param")

    def _create_vir_bridge_network_file(self, bridge_name):
        """
        Private method to create the bridge network config file on linux SUT

        :raise: RuntimeError
        """
        self._log.info("Creating the ifcfg-{} file".format(bridge_name))
        file_path = self.SYSCONFIG_SCRIPTS_PATH + self.NETWORK_SCRIPTS + "/ifcfg-{}".format(bridge_name)
        self._common_content_lib.execute_sut_cmd("touch {}".format(file_path), "create file", self._command_timeout)
        self._log.debug("ifcfg-{} file is created".format(bridge_name))
        for index in range(0, len(self.VIRBRIDGE_CONFIG_FILE_CONTENTS)):
            if index == 0:
                self._log.info(
                    "setting the param {}".format(self.VIRBRIDGE_CONFIG_FILE_CONTENTS[index].format(bridge_name)))
                self._common_content_lib.execute_sut_cmd("echo {} | tee {}".format(self.VIRBRIDGE_CONFIG_FILE_CONTENTS[
                                                                                       index].format(bridge_name), file_path),
                                                         "adding 1st line", self._command_timeout)
                self._common_content_lib.execute_sut_cmd("sync", "sync the data", self._command_timeout)
                self._log.debug("Added the content in the bridge configuration file")
            else:
                self._log.info(
                    "setting the param {}".format(self.VIRBRIDGE_CONFIG_FILE_CONTENTS[index]))
                self._common_content_lib.execute_sut_cmd(r"sed -i '$ a\{}' {}".format(self.VIRBRIDGE_CONFIG_FILE_CONTENTS[
                                                                                          index], file_path),
                                                         "adding next lines", self._command_timeout)
                self._common_content_lib.execute_sut_cmd("sync", "sync the data", self._command_timeout)

        interface_name = self._get_current_network_interface_linux()
        current_network_info = self._common_content_lib.execute_sut_cmd("ifconfig {} | grep inet".
                                                                        format(interface_name),
                                                                        "getting network info", self._command_timeout)
        network_info = current_network_info.split("\n")[0].strip().split()
        sut_ip, net_mask = network_info[1], network_info[3]
        self._common_content_lib.execute_sut_cmd(r"sed -i '$ a\IPADDR={}' {}".format(sut_ip, file_path),
                                                 "Adding IPADDR", self._command_timeout)
        self._common_content_lib.execute_sut_cmd(r"sed -i '$ a\NETMASK={}' {}".format(net_mask, file_path),
                                                 "Adding NETMASK", self._command_timeout)
        bridge_network_file_data = self._common_content_lib.execute_sut_cmd("cat {}".format(file_path),
                                                                            "print output of bridge network config "
                                                                            "file", self._command_timeout)
        self._log.debug("Current content of Bridge Network configuration file: \n{}".format(bridge_network_file_data))
        self._log.info("Added all the contents in the bridge configuration file")

    def __get_linux_vm_password(self):
        """
        This private method will get the OS password of the VM and return it

        :return password: OS password of the VM
        :raise: Exception
        """
        try:
            self._log.info("Getting the VM password from the Kick-start file")
            kstart_file_name = "{}".format(
                self._common_content_configuration.get_kickstart_file_name_centos())
            if kstart_file_name is None or kstart_file_name == "":
                kstart_file_name = "linux_vm_kstart.cfg"
            kstart_file_path = self._install_collateral.download_tool_to_host("{}".format(kstart_file_name))
            with open(kstart_file_path, "r+") as fp:
                kstart_file_data = fp.read()
                if re.search("rootpw", kstart_file_data):
                    pass_line_list = re.findall("rootpw.*", kstart_file_data)[0].split()
                    if len(pass_line_list) > 2:
                        password = re.findall("rootpw.*", kstart_file_data)[0].split()[2].strip()
                    else:
                        password = re.findall("rootpw.*", kstart_file_data)[0].split()[1].strip()
                    self._log.info("Successfully retrieve the password of linux VM: {}".format(password))
                    return password
        except Exception as ex:
            raise ("Could not retrieve the password of linux VM due to {}".format(ex))

    def ping_vm_from_sut(self, vm_ip, vm_name=None, vm_account=None, vm_password=None):
        """
        This method is to ping the VM from SUT system

        :param vm_name: name of given VM
        :param vm_ip: IP of the VM
        :param vm_account: user account for the VM
        :param vm_password: password for the VM account
        :return: None
        :raise: RunTimeError
        """
        try:
            self._log.info("pinging {} from SUT".format(vm_ip))
            ping_result = self._common_content_lib.execute_sut_cmd("ping -c 4 {}".format(vm_ip), "pinging {}".format(
                vm_ip), self._command_timeout)
            self._log.debug("Ping result data :\n{}".format(ping_result))

            match = re.compile(
                r'(\d+) packets transmitted, (\d+) (?:packets )?received, (\d+\.?\d*)% packet loss').search(ping_result)

            if not match:
                raise content_exceptions.TestFail('Invalid PING output:\n' + ping_result)

            sent, received, packet_loss = match.groups()
            # check for ping output and loss

            if (int(sent) != int(received)) and (float(packet_loss) > 5):
                raise content_exceptions.TestFail("Data Loss is Observed at test {}%".format(packet_loss))
                return False

            self._log.info("Successfully pinged the VM from SUT")
            return True
        except Exception as ex:
            self._log.error("Fail to ping the VM from SUT")
            return False

    def ssh_from_sut_to_ip(self, src_content, dest_ip, account=None, password=None):
        """
        This method is to ssh the VM from SUT system

        :param dest_ip: IP of the VM
        :param account: user account for the VM
        :param password: password for the VM account
        :return: None
        :raise: RunTimeError
        """
        self._log.info("trying to establish ssh connection with {}".format(dest_ip))
        # ssh_result = src_content.execute_sut_cmd("ssh {}@{} -v".format(account, dest_ip),
        #                                           "doing ssh to {}".format(dest_ip), self._command_timeout)
        ssh_result = self._os.execute("ssh {}@{} -v".format(account, dest_ip), self._command_timeout,)
        self._log.debug("ssh result data :\n {} {}".format(ssh_result.stdout,ssh_result.stderr))
        REGEX_SSH_OUPUT1 = r".*\sConnection\sestablished"
        op_connection = re.findall(REGEX_SSH_OUPUT1, ssh_result.stderr)
        if len(op_connection) != 0:
            self._log.info("Successfully established ssh connection with IP {}".format(dest_ip))
            return True

        self._log.error("Fail to ssh the IP {}".format(dest_ip))
        return False

    def add_storage_device_to_vm(self, vm_name, vm_disk_name, storage_size):
        """
        This method is add additional storage device to VM

        :param vm_name: name of the VM
        :param vm_disk_name: disk name going to attach to the VM
        :param storage_size: size of the storage device to add in GB
        :return: None
        """
        self._log.info("Creating additional disk for {} VM".format(vm_name))
        disk_name = "{}_vm_disk_{}G".format(vm_name, storage_size)
        create_image_result = self._common_content_lib.execute_sut_cmd(self.CREATE_DISK_CMD.format(disk_name,
                                                                                                   storage_size),
                                                                       "create vm-disk", self._command_timeout,
                                                                       cmd_path=self.SUT_ISO_IMAGE_LOCATION)
        self._log.debug(create_image_result)
        self._log.info("Successfully created the additional disk for {} VM".format(vm_name))
        self._log.info("Attaching the {} disk to the {} VM".format(vm_disk_name, vm_name))
        add_disk_result = self._common_content_lib.execute_sut_cmd(self.ATTACH_DISK_CMD.format(vm_name,
                                                                                               self.SUT_ISO_IMAGE_LOCATION,
                                                                                               disk_name,
                                                                                               vm_disk_name),
                                                                   "adding disk to {} VM".format(vm_name),
                                                                   self._command_timeout)
        self._log.debug(add_disk_result)
        self._log.info("Successfully attached the {} disk to the {} VM".format(vm_disk_name, vm_name))

    def create_storage_pool(self, pool_id, dev_mapper):
        """
        This method is to create Storage pool for QEMU VM's.
        """
        self._log.info("Creating storage pool for libvirt named {}".format(pool_id))
        storage_pool_result = self._common_content_lib.execute_sut_cmd(self.CREATE_STORAGE_POOL.format(
            pool_id, dev_mapper), "Storage pool creation", self._command_timeout)
        self._log.debug(storage_pool_result)
        self._log.info("Creating storage pool Vol for libvirt named {}".format(dev_mapper))

        storage_vol_result = self._common_content_lib.execute_sut_cmd(self.BUILD_STORAGE_POOL_VOL.format(
            pool_id), "Storage pool Volume creation", self._command_timeout)
        self._log.debug(storage_vol_result)

        start_storage_pool = self._common_content_lib.execute_sut_cmd(self.START_STORAGE_POOL.format(
            pool_id), "Start Storage pool", self._command_timeout)
        self._log.debug(start_storage_pool)
        autostart_storage_pool = self._common_content_lib.execute_sut_cmd(self.AUTOSTART_STORAGE_POOL.format(
            pool_id), "Autostart Storage pool", self._command_timeout)
        self._log.debug(autostart_storage_pool)
        self._log.info("Successfully created and started Storage pool {}".format(pool_id))

    def delete_storage_pool(self, pool_id):
        """
        This method is to delete Storage pool for QEMU VM's.
        """
        if(self.find_if_storage_pool_active(pool_id)):
            self._log.info("Deleting storage pool for libvirt named {}".format(pool_id))
            destroy_pool_result = self._common_content_lib.execute_sut_cmd(self.DESTROY_STORAGE_POOL.format(
                pool_id), "Storage pool destroying", self._command_timeout)
            self._log.debug(destroy_pool_result)

        undefine_storage_result = self._common_content_lib.execute_sut_cmd(self.UNDEFINE_STORAGE_POOL.format(
            pool_id), "Undefining Storage pool", self._command_timeout)
        self._log.debug(undefine_storage_result)
        # delete_storage_result = self._common_content_lib.execute_sut_cmd(self.DELETE_STORAGE_POOL.format(
        #     pool_id), "Deleting Storage pool", self._command_timeout)
        # self._log.debug(delete_storage_result)
        self._log.info("Successfully Deleted and Cleaned Storage pool {}".format(pool_id))

    def find_available_storage_pool(self, pool_id, vm_type):
        """
        This method is to get the available storage from pool.
        """
        self._log.info("Find available space from storage device {}".format(pool_id))
        storage_data_dict = []
        sut_os_type = self._sut_os.lower()
        memory_size = self._common_content_configuration.get_vm_disk_size(sut_os_type, vm_type)
        for pool in pool_id:
            pool_details = self._common_content_lib.execute_sut_cmd(self.STORAGE_POOL_INFO.format(
                pool), "Storage pool info", self._command_timeout)
            stateline = re.findall(r"Available:.*[0-9]", pool_details)
            maximum_storage_size = int(stateline[0].split(":")[1].strip(), 10)
            self._log.info("Available Storage space on {} : {}".format(pool, maximum_storage_size))
            if maximum_storage_size >= memory_size:
                return pool
                break
            else:
                self._log.info("Available storage size on {} is not enough of VM size : {}".format(pool, memory_size))

    def find_storage_pool_available_size(self, pool_id):
        """
        This method is to create Storage pool for QEMU VM's.
        """
        self._log.info("Find total available space for storage pool {}".format(pool_id))
        pool_details = self._common_content_lib.execute_sut_cmd(self.STORAGE_POOL_INFO.format(
            pool_id), "Storage pool info", self._command_timeout)
        stateline = re.search(r"Available:.*[0-9]", pool_details)
        maximum_storage_size = int(stateline[0].split(":")[1].strip(), 10)
        self._log.info("Available Storage space on {} : {}".format(pool_id, maximum_storage_size))
        return maximum_storage_size

    def find_storage_pool_capacity_size(self, pool_id):
        """
        This method is to get the total capacity of storage pool.
        """
        self._log.info("Find total Capacity space for storage pool {}".format(pool_id))
        pool_details = self._common_content_lib.execute_sut_cmd(self.STORAGE_POOL_INFO.format(
            pool_id), "Storage pool info", self._command_timeout)
        stateline = re.search(r"Capacity:.*[0-9]", pool_details)
        maximum_storage_size = int(stateline[0].split(":")[1].strip(), 10)
        self._log.info("Capacity of Storage space on {} : {}".format(pool_id, maximum_storage_size))
        return maximum_storage_size

    def find_storage_pool_allocated_size(self, pool_id):
        """
        This method is to get the allocated storage from pool.
        """
        self._log.info("Find total allocated space for storage pool {}".format(pool_id))
        pool_details = self._common_content_lib.execute_sut_cmd(self.STORAGE_POOL_INFO.format(
            pool_id), "Storage pool info", self._command_timeout)
        stateline = re.search(r"Allocation:.*[0-9]", pool_details)
        maximum_storage_size = int(stateline[0].split(":")[1].strip(), 10)
        self._log.info("Allocated Storage space on {} : {}".format(pool_id, maximum_storage_size))
        return maximum_storage_size

    def find_if_storage_pool_exist(self, pool_id):
        """
        This method is to create Storage pool for QEMU VM's.
        """
        self._log.info("Find State of Storage pool {}".format(pool_id))
        list_of_all_pools = self._common_content_lib.execute_sut_cmd_no_exception(self.STORAGE_POOL_ALL,
                                                                                  "List all Storage pools",
                                                                                  self._command_timeout,
                                                                                  ignore_result="ignore")
        if pool_id in list_of_all_pools:
            pool_state = self._common_content_lib.execute_sut_cmd_no_exception(self.STORAGE_POOL_STATUS.format(
                    pool_id), "Storage pool info", self._command_timeout, ignore_result="ignore")
            stateline = re.findall(r"State:.*[a-zA-Z]", pool_state)
            state = [line.split(":")[1].strip() for line in stateline]
            self._log.info("Status of Storage pool {} : {}".format(pool_id, state))
            testlist = ["running", "inactive", "active"]
            if any(elm in state for elm in testlist):
                return True
        return False

    def find_if_storage_pool_active(self, pool_id):
        """
        This method is to create Storage pool for QEMU VM's.
        """
        self._log.info("Find State of Storage pool {}".format(pool_id))
        list_of_all_pools = self._common_content_lib.execute_sut_cmd(self.STORAGE_POOL_ALL, "List all Storage pools", self._command_timeout)
        if pool_id in list_of_all_pools:
            pool_state = self._common_content_lib.execute_sut_cmd(self.STORAGE_POOL_STATUS.format(
                    pool_id), "Storage pool info", self._command_timeout)
            stateline = re.findall(r"State:.*[a-zA-Z]", pool_state)
            state = [line.split(":")[1].strip() for line in stateline]
            self._log.info("Status of Storage pool {} : {}".format(pool_id, state))
            testlist = ["running", "active"]
            if any(elm in state for elm in testlist):
                return True
        return False

    def get_storage_pool_using_vol(self, vol_id):
        for pool_id, pool_vol_list in self.LIST_OF_POOL_VOL.items():
            for elem in pool_vol_list:
                if elem == vol_id:
                    return pool_id
        self._log.info("Failed findind the Storage pool for Vol ID {}".format(vol_id))
        return None

    def create_storage_pool_vol(self, pool_id, vol_id, size_in_gb):
        """
        This method is to create Storage pool for QEMU VM's.
        """
        self._log.info("Creating storage pool vol for libvirt named {}".format(pool_id))
        storage_pool_result = self._common_content_lib.execute_sut_cmd(self.CREATE_STORAGE_POOL_VOL.format(
            pool_id, vol_id, size_in_gb), "Storage pool vol creation", self._command_timeout)
        self._log.debug(storage_pool_result)
        self._log.info("Creating storage pool Vol for libvirt named {}/{}".format(pool_id, vol_id))

        storage_vol_result = self._common_content_lib.execute_sut_cmd(self.LIST_STORAGE_POOL_VOL.format(
            pool_id), "Storage pool Volume list", self._command_timeout)
        self._log.debug(storage_vol_result)

        search_vol = re.search(self.LIST_VOL_INFO_REGEX.format(vol_id), storage_vol_result)
        if not (search_vol):
            raise content_exceptions.TestFail("Failed to create the Vol")

        self._log.info("Successfully created Storage pool vol : {}".format(search_vol))

    def delete_storage_pool_vol(self, pool_id, vol_id):
        """
        This method is to delete Storage pool for QEMU VM's.
        """
        if (self.find_if_storage_pool_vol_exist(pool_id, vol_id)):
            self._log.info("Deleting storage pool vol {}/{}".format(pool_id, vol_id))
            delete_pool_vol_result = self._common_content_lib.execute_sut_cmd(self.DELETE_STORAGE_POOL_VOL.format(
                pool_id, vol_id), "Storage pool deleting", self._command_timeout)
            self._log.debug(delete_pool_vol_result)

        storage_vol_result = self._common_content_lib.execute_sut_cmd(self.LIST_STORAGE_POOL_VOL.format(
            pool_id), "Storage pool Volume list", self._command_timeout)
        self._log.debug(storage_vol_result)

        search_vol = re.search(self.LIST_VOL_INFO_REGEX.format(vol_id), storage_vol_result)
        if search_vol:
            raise content_exceptions.TestFail("Failed to delete the Vol {}".format(vol_id))

        self._log.info("Successfully Deleted and Cleaned Storage pool vol {}/{}".format(pool_id, vol_id))

    def find_available_storage_pool_vol(self, pool_id, vol_id):
        """
        This method is to find storage pool vol information.
        virsh vol-info --pool Storage_0 vol2
        Name:           vol2
        Type:           file
        Capacity:       22.35 GiB
        Allocation:     22.35 GiB
        """
        self._log.info("Find total space in storage vol device {}/{}".format(pool_id, vol_id))
        cap_size = 0
        alloc_size = 0
        if self.find_if_storage_pool_vol_exist(pool_id, vol_id):
            pool_vol_details = self._common_content_lib.execute_sut_cmd(self.STORAGE_POOL_VOL_INFO.format(
                pool_id, vol_id), "Storage pool vol info", self._command_timeout)
            regex_name = "Name:.*{}".format(vol_id)
            state_line = re.search(regex_name, pool_vol_details)

            if vol_id in state_line:
                regex_capacity = "Capacity:.*[0-9]\sbytes"
                cap_line = re.search(regex_capacity, pool_vol_details)
                cap_size = int(cap_line[0].split(":")[1].strip().split(" ")[0], 10)
                regex_allocation = "Allocation:.*[0-9]\sbytes"
                alloc_line = re.search(regex_allocation, pool_vol_details)
                alloc_size = int(alloc_line[0].split(":")[1].strip().split(" ")[0], 10)
                self._log.info(
                    "Available space on {}/{}-capacity {}:allocated {}".format(pool_id, vol_id, cap_size, alloc_size))
        else:
            self._log.info(
                "Failed: Available space on {}/{}-capacity {}:allocated {}".format(pool_id, vol_id, cap_size, alloc_size))

        return cap_size, alloc_size

    def find_if_storage_pool_vol_exist(self, pool_id, vol_id):
        """
        This method is to find if pool volume exists.
        """
        storage_vol_result = self._common_content_lib.execute_sut_cmd(self.LIST_STORAGE_POOL_VOL.format(
            pool_id), "Storage pool Volume list", self._command_timeout)
        self._log.debug(storage_vol_result)

        search_vol = re.search(self.LIST_VOL_INFO_REGEX.format(vol_id), storage_vol_result)
        if not (search_vol):
            return False
        self._log.info("Successfully found Storage pool vol : {}".format(search_vol))
        return True

    def get_vm_info(self, vm_name):
        """
        This method is to get the dominfo of the given VM

        :param vm_name: name of the VM
        :return: dominfo_data_dict
        :raise: RuntimeError
        """
        dominfo_data_dict = {}
        dominfo_result = self._common_content_lib.execute_sut_cmd("virsh dominfo {}".format(vm_name), "get domninfo ",
                                                                  self._command_timeout)
        self._log.debug("dominfo data of {} VM is:\n{}".format(vm_name, dominfo_result))
        if dominfo_result.strip() == "":
            raise RuntimeError("Failed to get the dominfo data")
        for line in dominfo_result.splitlines():
            if line.strip() != "":
                dominfo_data_dict[line.strip().split(':')[0].strip()] = "".join(line.strip().split(':')[1::]).strip()
        self._log.debug("dominfo data_dict of {} VM: \n{}".format(vm_name, dominfo_data_dict))
        return dominfo_data_dict

    def copy_file_from_sut_to_vm(self, vm_name, vm_username, source_path, destination_path):
        """
        This method is to copy file from SUT to VM

        :param vm_name: name of the VM
        :param vm_username: user name of the VM
        :param source_path: complete file source path
        :param destination_path: destination VM path
        :return : None
        """
        # get scp_go file location
        scp_go_file_location, scp_go_file_name = self._install_collateral.copy_scp_go_to_sut()
        self._log.info("Giving permission to the {} file".format(scp_go_file_name))
        self._common_content_lib.execute_sut_cmd("chmod 777 {}".format(scp_go_file_name),
                                                 "give permission to {}".format(scp_go_file_name),
                                                 self._command_timeout,
                                                 cmd_path=scp_go_file_location)
        vm_ip = self.get_vm_ip(vm_name)
        vm_password = self.__get_linux_vm_password()
        self._log.info("Copying {} file to VM from SUT".format(source_path))
        self._common_content_lib.execute_sut_cmd(self.SCP_COPY_TO_VM_CMD.format(vm_ip, vm_username, vm_password,
                                                                                source_path, destination_path),
                                                 "copy file by using go_scp", self._command_timeout,
                                                 cmd_path=scp_go_file_location)
        self._log.info("Successfully copied {} file to VM from SUT".format(source_path))

    def remove_storage_device_from_vm(self, vm_name):
        """
        This method is add additional storage device to VM

        :param vm_name: name of the VM
        :return: None
        """
        raise NotImplementedError

    def suspend_vm(self, vm_name):
        """
        This method is to suspend the existing VM

        :param vm_name: Name of the VM
        """
        self._log.info("Suspending the {} VM".format(vm_name))
        suspend_result = self._common_content_lib.execute_sut_cmd(self.SUSPEND_VM_CMD_LINUX.format(vm_name),
                                                                  "suspending {} VM".format(vm_name),
                                                                  self._command_timeout)
        self._log.debug(suspend_result)
        if "Domain {} suspended".format(vm_name) not in suspend_result:
            raise RuntimeError("Fail to suspend {} VM".format(vm_name))
        self._log.info("Successfully suspended {} VM".format(vm_name))

    def resume_vm(self, vm_name):
        """
        This method is to resume the suspended VM

        :param vm_name: Name of the VM
        """
        self._log.info("Resuming the {} VM".format(vm_name))
        resume_result = self._common_content_lib.execute_sut_cmd(self.RESUME_VM_CMD_LINUX.format(vm_name),
                                                                 "Resuming {} VM".format(vm_name),
                                                                 self._command_timeout)
        self._log.debug(resume_result)
        if "Domain {} resumed".format(vm_name) not in resume_result:
            raise RuntimeError("Fail to resume {} VM".format(vm_name))
        self._log.info("Successfully resumed {} VM".format(vm_name))

    def save_vm_configuration(self, vm_name):
        """
        This method will save the VM configuration into a XML file

        :param vm_name: Name of the VM
        :return: complete_vm_config_file
        """
        self._log.info("Saving the {} VM configuration".format(vm_name))
        vm_config_file = vm_name + "_config.save"
        save_result = self._common_content_lib.execute_sut_cmd(self.SAVE_VM_CONFIG_CMD.format(vm_name, vm_config_file),
                                                               "save {} VM config", self._command_timeout,
                                                               cmd_path=self.ROOT_PATH)
        self._log.debug("Save VM command stdout:\n{}".format(save_result))
        complete_vm_config_file = self.ROOT_PATH + "/" + vm_config_file
        self._log.info("Successfully saved the {} VM in {} file".format(vm_name, complete_vm_config_file))
        return complete_vm_config_file

    def restore_vm_configuration(self, vm_name, vm_config_file):
        """
        This method will restore the VM from configuration file

        :param vm_name: Name of the VM
        :param vm_config_file: Previously saved VM configuration file with path
        """
        self._log.info("Restoring the {} VM from {} file".format(vm_name, vm_config_file))
        restore_result = self._common_content_lib.execute_sut_cmd(self.RESTORE_VM_CONFIG_CMD.format(vm_config_file),
                                                                  "restore {} VM", self._command_timeout)
        self._log.debug("Restore VM command stdout:\n{}".format(restore_result))
        self._log.info("Successfully restored the {} VM from {} file".format(vm_name, vm_config_file))

    def attach_usb_device_to_vm(self, usb_data_dict, vm_name):
        """
        This method is to attach the usb device to the vm

        :param usb_data_dict: dictionary data should contain vendor id and product id
        :param vm_name: name of the VM
        :return: None
        :raise: RuntimeError
        """
        self._log.info("Making the {} file".format(self.USB_DEVICE_XML_FILE_NAME))
        with open(self.USB_DEVICE_XML_FILE_NAME, "w+") as fp:
            fp.writelines(self.USB_DEVICE_XML_FILE_DATA.format(usb_data_dict["idVendor"], usb_data_dict["idProduct"]))
        self._log.info("Coping the {} file to SUT".format(self.USB_DEVICE_XML_FILE_NAME))
        self.os.copy_local_file_to_sut(self.USB_DEVICE_XML_FILE_NAME, self.ROOT_PATH)
        self._log.info("Successfully copied the {} file to SUT".format(self.USB_DEVICE_XML_FILE_NAME))
        self._log.info("Attaching the USB device to VM {}".format(vm_name))
        cmd_opt = self._common_content_lib.execute_sut_cmd(self.ATTACH_USB_DEVICE_COMMAND.
                                                           format(vm_name, self.USB_DEVICE_XML_FILE_NAME),
                                                           "Attaching USB device to VM", self._command_timeout,
                                                           cmd_path=self.ROOT_PATH)
        if "Device attached successfully" not in cmd_opt:
            raise RuntimeError("Fail to attach the USB device to VM {}".format(vm_name))
        self._log.info("Successfully attached the USB device to VM {}".format(vm_name))

    def detach_usb_device_from_vm(self, vm_name):
        """
        This method is to detach the usb device from VM.

        :param vm_name: name of the VM
        :return: None
        :raise: RuntimeError
        """
        self._log.info("Detaching USB device from VM {}".format(vm_name))
        cmd_opt = self._common_content_lib.execute_sut_cmd(self.DETACH_USB_DEVICE_COMMAND.
                                                           format(vm_name, self.USB_DEVICE_XML_FILE_NAME),
                                                           "Detaching USB device to VM", self._command_timeout,
                                                           cmd_path=self.ROOT_PATH)
        if "Device detached successfully" not in cmd_opt:
            raise RuntimeError("Fail to detach the USB device to VM {}".format(vm_name))
        self._log.info("Successfully detached the USB device to VM {}".format(vm_name))

    def install_kvm_virtio_win_tool(self):
        """
        This method is to install all the dependency tools for VM creation

        :return: None
        """
        self._install_collateral.yum_remove(package_name="virtio-win")
        self._install_collateral.yum_install(package_name="virtio-win*")
        self._log.info("Successfully installed all the dependency Packages")

    def install_vm_tool(self):
        """
        This method is to install all the dependency tools for VM creation

        :return: None
        """
        self._install_collateral.yum_install(package_name="libvirt")
        self._install_collateral.yum_install(package_name="virt-install")
        self._install_collateral.yum_remove(package_name="virt-viewer")
        self._log.info("Successfully installed all the dependency Packages")

    def install_kvm_vm_tool(self):
        """
        This method is to install all the dependency tools for VM creation

        :return: None
        """
        self._install_collateral.yum_install(package_name="qemu-kvm virt-install virt-manager")
        # self._install_collateral.yum_install(package_name="@virt")
        self._common_content_lib.execute_sut_cmd("systemctl start libvirtd", "systemctl start libvirtd",
                                                 self._command_timeout)
        self._common_content_lib.execute_sut_cmd("systemctl enable libvirtd", "ssystemctl enable libvirtd",
                                                 self._command_timeout)
        self._log.info("Successfully installed all the dependency Packages")

    def install_qemu_vm_tool(self):
        """
        This method is to install all the dependency tools for qemu VM creation

        :return: None
        """
        self._install_collateral.yum_install(package_name="screen")
        self._install_collateral.yum_install(package_name="expect")
        self._install_collateral.yum_install(package_name="sshpass")
        self._log.info("Successfully installed all the qemu VM dependency Packages")

    def start_vm(self, vm_name):
        """
        Method to start VM.

        :param vm_name: Name of the VM to start
        :raise: NotImplementedError
        """
        raise NotImplementedError

    def add_vm_network_adapter(self, methods, vm_name, physical_adapter_name, switch_name, vm_type=None, mac_addr=None):
        """
        Method to add network adapter for given VM.

        :param methods: The methods to add network adapter to VM. The value is expected to be "DDA" or "SRIOV".
        :param vm_name: Name of the VM.
        :param physical_adapter_name: Name of the physical network adapter on SUT.
                             Note: the adapter is expected to be extra test NIC instead of builtin NIC.
        :param switch_name: Name of the switch you create
        :param vm_type: VM type for eg:- "RS5"
        :param mac_addr: Assign MacAddress to Network Adapter.
        :raise: RunTimeError
        :return: None
        """
        raise NotImplementedError

    def set_automatic_stop_action(self, vm_name, stop_action_type="TurnOff"):
        """
        This method is to set the Automatic stop Action.

        :param vm_name
        :param stop_action_type - TurnOff, Save, and ShutDown
        """
        raise NotImplementedError

    def turn_off_vm(self, vm_name):
        """
        This method is to TurnOFF VM.

        :param vm_name
        :raise NotImplementedError
        """
        raise NotImplementedError

    def enumerate_storage_device(self, bus_type, index_value, command_exec_obj):
        """
        Execute the the command to create a VM from an existing template base image in vhdx format.

        :param vm_name: Name of the new VM
        :param memory_size: Size of the VM memory
        :param vm_creation_timeout: timeout for vm creation
        :raise: NotImplementedError
        """
        raise NotImplementedError

    def cvl_driver_build(self):
        """
        This method is to build Columbiaville device driver on SUT to create mdev

        """
        self._log.info("Copying CVL driver to SUT")
        driver_file_path = self._install_collateral.download_tool_to_host(self.CVL_ICE_DRIVER_FILE_NAME)
        cvl_driver_path = self.CVL_ICE_DRIVER_STR + "/src/"
        self.os.copy_local_file_to_sut(driver_file_path, self.ROOT_PATH)
        self.os.execute(self.UNTAR_FILE_CMD.format(self.CVL_ICE_DRIVER_FILE_NAME), self._command_timeout)
        self._log.info("CVL driver successfully copeied and unzipped on SUT")
        driver_build_cmd = ['make -C {}'.format(cvl_driver_path), 'modprobe vfio-mdev', 'rmmod ice',
                            'insmod {}ice.ko'.format(cvl_driver_path)]
        self.os.execute(self.UNTAR_FILE_CMD.format(self.CVL_ICE_DRIVER_FILE_NAME), self._command_timeout)
        for command in driver_build_cmd:
            cmd_opt =  self.os.execute(command, self._command_timeout)
            self._log.debug("{} stdout:\n{}".format(command, cmd_opt.stdout))
            self._log.error("{} stderr:\n{}".format(command, cmd_opt.stderr))
        self._log.info("Successfully executed columbiaville driver build command")

    def iavf_driver_build_on_vm(self, vm_os_obj, install_collateral_vm_obj):
        """
        This method is to build iavf device driver on QEMU VM.

        """
        self._log.info("Copying iavf driver to SUT")
        driver_file_path = install_collateral_vm_obj.download_tool_to_host(self.CVL_IAVF_DRIVER_FILE_NAME)
        vm_os_obj.copy_local_file_to_sut(driver_file_path, self.ROOT_PATH)
        iavf_driver_path = self.CVL_IAVF_DRIVER_STR + "/src/"
        vm_os_obj.execute(self.UNTAR_FILE_CMD.format(self.CVL_IAVF_DRIVER_FILE_NAME), self._command_timeout)
        driver_build_cmd = ['make -C {}'.format(iavf_driver_path), 'rmmod iavf',
                            'insmod {}iavf.ko'.format(iavf_driver_path)]
        for command in driver_build_cmd:
            cmd_opt = vm_os_obj.execute(command, self._command_timeout)
            self._log.debug("{} stdout:\n{}".format(command, cmd_opt.stdout))
            self._log.error("{} stderr:\n{}".format(command, cmd_opt.stderr))
        self._log.info("Successfully executed columbiaville iavf driver build command")

    def create_mdev_instance(self, mdev_index=0, mdev_bus_id=0):
        """
        This method is to create mdev instance using columbiaville device on SUT

        :param mdev_index: index number from mdev bus id list
        :param mdev_bus_id: mdev bdf
        :return uuid: UUID value
        """
        device_path = self.MDEV_PATH + "{}" + "/mdev_supported_types/"
        self._log.info("Create mdev instance using network device")
        uuidgen_res = self._common_content_lib.execute_sut_cmd("uuidgen", "uuidgen cmd", self._command_timeout)
        self._log.info("Generated UUID : {}".format(uuidgen_res))
        uuid = uuidgen_res.split("\n")[0]
        if not mdev_bus_id:
            output_list = self._common_content_lib.execute_sut_cmd("ls {}".format(self.MDEV_PATH),"mdev bus id",
                                                                   self._command_timeout)
            mdev_bus_id = output_list.split("\n")[mdev_index]
        self._log.info("mdev id : {}".format(mdev_bus_id))
        device_list = self._common_content_lib.execute_sut_cmd("ls {}".format(device_path.format(mdev_bus_id)),
                                                               "List device info for mdev", self._command_timeout)
        device_id = device_list.split("\n")[0]
        self._log.info("mdev device id : {}".format(device_id))
        username = self._common_content_lib.execute_sut_cmd("whoami",
                                                               "username ...whoami", self._command_timeout)
        self._log.info("username : {}".format(username))
        uuid = self.check_on_uuid(uuid, mdev_bus_id, device_id)

        exec_mdev_cmd = self._common_content_lib.execute_sut_cmd(self.CREATE_MDEV_CMD.format(uuid, mdev_bus_id, device_id), "Create mdev",
                                                 self._command_timeout)
        self._log.debug("{} stdout:\n{}".format(exec_mdev_cmd, exec_mdev_cmd))
        self._log.info("Successfully created mdev instance with uuid: {}".format(uuidgen_res))
        time.sleep(self.MDEV_CREATION_TIMEOUT)
        return uuid

    def check_on_uuid(self, uuid, mdev_bus_id, device_id):
        """
        This method checks whether the existing uuid is not already in use, if yes, creates a new one and returns.

        :param uuid: uuid existing
        :param mdev_bus_id: bdf of mdev interface name
        :param device_id: siov driver device id
        :return uuid: validated uuid
        """
        self._log.info("Check if UUID generated is not in already use.....")
        while True:
            if uuid in self.os.execute(self.CHECK_UUID_CMD.format(mdev_bus_id, device_id),
                                       self._command_timeout).stdout.split():
                self._log.info("UUID - {}, Already in use".format(uuid))
                uuidgen_res = self._common_content_lib.execute_sut_cmd("uuidgen", "uuidgen cmd", self._command_timeout)
                self._log.info("Newly Generated UUID : {}".format(uuidgen_res))
                uuid = uuidgen_res.split("\n")[0]
            else:
                self._log.info("{} validated and available".format(uuid))
                return uuid

    def create_mdev_dlb2_instance(self, mdev_index):
        """
        This method is to create mdev instance using columbiaville device on SUT
        export UUID='83b8f4f2-509f-382f-3c1e-e6bfe0fa1001'
        export SYSFS_PATH=/sys/class/dlb2/dlb0
        export MDEV_PATH=/sys/bus/mdev/devices/$UUID/dlb2_mdev/

        echo $UUID > $SYSFS_PATH/device/mdev_supported_types/dlb2-dlb/create

        echo 2048 > $MDEV_PATH/num_atomic_inflights
        echo 2048 > $MDEV_PATH/num_dir_credits
        echo 64 > $MDEV_PATH/num_dir_ports
        echo 2048 > $MDEV_PATH/num_hist_list_entries
        echo 8192 > $MDEV_PATH/num_ldb_credits
        echo 64 > $MDEV_PATH/num_ldb_ports
        echo 32 > $MDEV_PATH/num_ldb_queues
        echo 32 > $MDEV_PATH/num_sched_domains

        :return : uuid, domain, bud, device, function
        """
        cmd1 = "cd /root/HQM/libdlb;modprobe vfio"
        cmd1_res = self._common_content_lib.execute_sut_cmd(cmd1, "modprobe vfio cmd", self._command_timeout)
        cmd2 = "cd /root/HQM/libdlb;modprobe vfio-pci"
        cmd2_res = self._common_content_lib.execute_sut_cmd(cmd2, ";modprobe vfio-pci cmd", self._command_timeout)
        cmd3 = "cd /root/HQM/libdlb;modprobe mdev"
        cmd3_res = self._common_content_lib.execute_sut_cmd(cmd3, "modprobe mdev cmd", self._command_timeout)
        self._log.info("Create mdev instance using network device")
        uuidgen_res = self._common_content_lib.execute_sut_cmd("uuidgen", "uuidgen cmd", self._command_timeout)
        self._log.info("Generated UUID : {}".format(uuidgen_res))
        uuid = uuidgen_res.split("\n")[0]
        sysfs_path = "/sys/class/dlb2/dlb{}".format(mdev_index)
        mdev_path = "/sys/bus/mdev/devices/{}/dlb2_mdev/".format(uuid)

        bdf_get_cmd = "ls -la /sys/class/dlb2"
        exec_ls_dbdf = self._common_content_lib.execute_sut_cmd_no_exception(bdf_get_cmd,
                                                                 "run {}".format(bdf_get_cmd),
                                                                 self._command_timeout,
                                                                 ignore_result="ignore")
        self._log.debug("{} output:\n{}".format(bdf_get_cmd, exec_ls_dbdf))

        val = re.findall(".*\sdlb{}\s.*".format(mdev_index), exec_ls_dbdf, re.M)

        if val is not None:
            dbdf = val[0].split("/")[4]

        function = dbdf.split(".")[1].strip()
        dbd = dbdf.split(".")[0].strip()
        domain = dbd.split(":")[0].strip()
        bus = dbd.split(":")[1].strip()
        device = dbd.split(":")[2].strip()

        exec_mdev_cmd = self._common_content_lib.execute_sut_cmd(self.CREATE_DLB2_MDEV_CMD.format(uuid, sysfs_path),
                                                                "Create mdev",
                                                                self._command_timeout)
        self._log.debug("{} stdout:\n{}".format(exec_mdev_cmd, exec_mdev_cmd))
        self._log.info("Successfully created mdev instance with uuid: {}".format(uuidgen_res))
        time.sleep(self.MDEV_CREATION_TIMEOUT)

        cmd_mdev_device_params = """
                                echo 2048 > {}/num_atomic_inflights;
                                echo 2048 > {}/num_dir_credits;
                                echo 64 > {}/num_dir_ports;
                                echo 2048 > {}/num_hist_list_entries;
                                echo 8192 > {}/num_ldb_credits;
                                echo 64 > {}/num_ldb_ports;
                                echo 32 > {}/num_ldb_queues;
                                echo 32 > {}/num_sched_domains;
                                echo 16 > {}/num_sn0_slots;
                                echo 16 > {}/num_sn1_slots;
                                """.format(mdev_path, mdev_path, mdev_path, mdev_path,
                                           mdev_path, mdev_path, mdev_path, mdev_path, mdev_path, mdev_path)

        mdev_setting_result = self._common_content_lib.execute_sut_cmd(cmd_mdev_device_params,
                                                                       "execute cmd to set mdev device params",
                                                                       self._command_timeout, cmd_path=self.ROOT_PATH)
        self._log.debug("MDEV device params setting result {}".format(mdev_setting_result))

        return uuid, domain, bus, device, function

    def import_vm(self, source_path=None, destination_path=None):
        """Method to import VM.
        :param source_path: path on the SUT to the VM template image.
        :type: str
        :param destination_path: path on the SUT to where the new VM image will be.
        :type: str
        """
        raise NotImplementedError

    def apply_checkpoint(self, vm_name=None, checkpoint_name=None):
        """Method to apply a stored checkpoint for a named VM.
        :param vm_name: Name of the VM to which the checkpoint will be applied.
        :type: str
        :param checkpoint_name: name of the checkpoint to apply to the VM.
        :type: str"""
        raise NotImplementedError

    def rename_vm(self, current_vm_name=None, new_vm_name=None):
        """Method to rename VM.
        :param current_vm_name: Current VM name.
        :type: str
        :param new_vm_name: New VM name.
        :type: str"""
        raise NotImplementedError

    def delete_checkpoint(self, vm_name=None, checkpoint_name=None):
        """Method to delete a stored checkpoint for a named VM.
        :param vm_name: Name of the VM to which the checkpoint will be deleted.
        :type: str
        :param checkpoint_name: name of the checkpoint to apply to the VM.
        :type: str"""
        raise NotImplementedError

    def get_network_bridge_list(self):
        """Retrieves list of VM switches registered into Hyper-V.
        :return: List of VM switches
        :rtype: str"""
        raise NotImplementedError

    def set_boot_order(self, vm_name=None, boot_device_type=None):
        """Set boot order of a VM.
        :param vm_name: Name of the VM to change the boot order.
        :type: str
        :param boot_device_type: Type of device to use as boot device.  Expected values are: VMBootSource,
        VMNetworkAdapter,HardDiskDrive,DVDDrive.
        :type: str"""
        raise NotImplementedError

    def create_sriov_dlb2_instance(self, mdev_index):
        """
        This method is to create mdev instance using columbiaville device on SUT
        echo 0000:eb:00.1 > /sys/bus/pci/drivers/dlb2/unbind
        (OR echo 0000:eb:00.1 > /sys/bus/pci/devices/0000:eb:00.1/driver/unbind)
        echo 8086 2711 > /sys/bus/pci/drivers/vfio-pci/new_id

        echo 2048 > /sys/bus/pci/devices/0000:eb:00.0/vf0_resources/num_atomic_inflights
        echo 2048 > /sys/bus/pci/devices/0000:eb:00.0/vf0_resources/num_dir_credits
        echo 64 > /sys/bus/pci/devices/0000:eb:00.0/vf0_resources/num_dir_ports
        echo 2048 > /sys/bus/pci/devices/0000:eb:00.0/vf0_resources/num_hist_list_entries
        echo 8192 > /sys/bus/pci/devices/0000:eb:00.0/vf0_resources/num_ldb_credits
        echo 64 > /sys/bus/pci/devices/0000:eb:00.0/vf0_resources/num_ldb_ports
        echo 32 > /sys/bus/pci/devices/0000:eb:00.0/vf0_resources/num_ldb_queues
        echo 32 > /sys/bus/pci/devices/0000:eb:00.0/vf0_resources/num_sched_domains

        """
        self._log.info("Create bdf instance using network device")

        self._common_content_lib.execute_sut_cmd("modprobe vfio", "unbinding ", self._command_timeout)
        self._common_content_lib.execute_sut_cmd("modprobe vfio-pci", "checking vfio-pci", self._command_timeout)

        cmand = "lspci -Dd :2711"
        dlb_vf_device_list = self._common_content_lib.execute_sut_cmd(cmand, "check dlb vf in sut", 60)
        self._log.info(dlb_vf_device_list)
        dlb_vf_dev_bdf_list = []
        dlb_value = dlb_vf_device_list.split("\n")
        for value in dlb_value:
            dlb_vf_bdf_value = value.split(" ")[0]
            if dlb_vf_bdf_value is not None and dlb_vf_bdf_value is not "":
                dlb_vf_dev_bdf_list.append(dlb_vf_bdf_value)
                self._log.info(dlb_vf_bdf_value)

        bdf_get_cmd = "ls -la /sys/class/dlb2"
        exec_ls_dbdf = self._common_content_lib.execute_sut_cmd_no_exception(bdf_get_cmd,
                                                                             "run {}".format(bdf_get_cmd),
                                                                             self._command_timeout,
                                                                             ignore_result="ignore")
        self._log.debug("{} output:\n{}".format(bdf_get_cmd, exec_ls_dbdf))

        val = re.findall(".*\sdlb{}\s.*".format(mdev_index), exec_ls_dbdf, re.M)

        if val is not None:
            dbdf = val[0].split("/")[4]

        domain = dbdf.split(":")[0]
        bus = dbdf.split(":")[1]
        device = dbdf.split(":")[2].split(".")[0]
        function = dbdf.split(":")[2].split(".")[1]
        try:
            command = "echo {} > /sys/bus/pci/drivers/dlb2/unbind".format(dlb_vf_dev_bdf_list[0])
            output = self._common_content_lib.execute_sut_cmd(command, "run command:{}".format(command),
                                                              self._command_timeout, self.ROOT_PATH)
            output = output.strip()
            self._log.info("Result of the run {} command: {}".format(command, output))
        except:
            pass

        dbdf_vf = "{:04x}\:{:02x}\:{:02x}.{:01x}".format(int(domain,16), int(bus,16), int(device,16), int(function,16))
        cmd_mdev_device_params = """
                                echo 8086 2711 > /sys/bus/pci/drivers/vfio-pci/new_id
                                echo 2048 > /sys/bus/pci/devices/{}/vf0_resources/num_atomic_inflights
                                echo 2048 > /sys/bus/pci/devices/{}/vf0_resources/num_dir_credits
                                echo 64 > /sys/bus/pci/devices/{}/vf0_resources/num_dir_ports
                                echo 2048 > /sys/bus/pci/devices/{}/vf0_resources/num_hist_list_entries
                                echo 8192 > /sys/bus/pci/devices/{}/vf0_resources/num_ldb_credits
                                echo 64 > /sys/bus/pci/devices/{}/vf0_resources/num_ldb_ports
                                echo 32 > /sys/bus/pci/devices/{}/vf0_resources/num_ldb_queues
                                echo 32 > /sys/bus/pci/devices/{}/vf0_resources/num_sched_domains
                                echo 16 > /sys/bus/pci/devices/{}/vf0_resources/num_sn0_slots
                                echo 16 > /sys/bus/pci/devices/{}/vf0_resources/num_sn1_slots
                                """.format(dbdf_vf, dbdf_vf, dbdf_vf, dbdf_vf,
                                           dbdf_vf, dbdf_vf, dbdf_vf, dbdf_vf, dbdf_vf, dbdf_vf)

        mdev_setting_result = self._common_content_lib.execute_sut_cmd(cmd_mdev_device_params,
                                                                       "execute cmd to set mdev device params",
                                                                       self._command_timeout, cmd_path=self.ROOT_PATH)
        self._log.debug("MDEV device params setting result {}".format(mdev_setting_result))

        return domain, bus, device, function

    def copy_package_to_VM(self, vm_name, vm_account, vm_password, package_name, destination_path):
        """
        This method is to copy file from SUT to VM
        :param vm_name : name of the VM. ex: WINDOWS_1
        :param vm_account : VM admin account "Administrator"
        :param vm_password : VM password
        :param destination_path: Destination path in VM
        :param package_name : Name of the package to be copied to VM
        :return : pakage path on VM

        :raise: NotImplementedError
        """
        raise NotImplementedError

    def get_sut_mem_info(self):
        """
        This function is to get the Memory  information
        Returns : Available Memory on SUT
        """
        try:
            mem_info_result = self._common_content_lib.execute_sut_cmd(self.MEM_INFO, self.MEM_INFO,
                                                                       self._command_timeout)
            self._log.debug("{} command result:{}".format(self.MEM_INFO, mem_info_result))

            if not re.search(self.TOTAL_MEM_INFO, mem_info_result):
                raise content_exceptions.TestFail("Failed to get socket info from Solar tool")

            memory_size = int(re.search(self.TOTAL_MEM_INFO, mem_info_result).group(1))
            mem_size_in_mb = int(memory_size / 1024)

            self._log.info("Total Memory Size:{} MB".format(mem_size_in_mb))

            return mem_size_in_mb

        except Exception as ex:
            self._log.error("Exception occurred while fetching SUT memory details")
            raise ex


    def reconfigure_memory_on_vm(self, vm_name, maximum_memory, vm_memory):
        """
        This function is to reconfigure memory on VM

        :Param : vm_name
        :param: maximum_memory: Maximum memory allocated for VM
        :param: vm_memory: Assigned memory for VM
        """
        try:
            # Set max memory on VM
            self._common_content_lib.execute_sut_cmd(self.CONFIGURE_MAX_MEM.format(vm_name, maximum_memory),
                                                     self.CONFIGURE_MAX_MEM, self._command_timeout)
            self._log.info("VM maximum memory set to {}MB".format(maximum_memory))
            # Assign memory on vm
            self._common_content_lib.execute_sut_cmd(self.SET_VM_MEM.format(vm_name, vm_memory),
                                                     self.SET_VM_MEM.format(vm_name, vm_memory), self._command_timeout)
            self._log.info("VM memory set to {}MB".format(vm_memory))
        except Exception as ex:
            self._log.error("Exception occurred while reconfiguring VM memory")
            raise ex

    def reconfigure_cpu_on_vm(self, vm_name, maximum_cpu, vm_cpu):
        """
        This function is to reconfigure CPU on VM

        :Param : vm_name
        :param: maximum_cpu: Maximum vcpu allocated for VM
        :param: vm_cpu: Assigned vcpu for VM
        """
        try:
            # Set max CPU on VM
            self._common_content_lib.execute_sut_cmd(self.CONFIGURE_MAX_CPU.format(vm_name, maximum_cpu),
                                                     self.CONFIGURE_MAX_CPU.format(vm_name, maximum_cpu),
                                                     self._command_timeout)
            self._log.info("VM maximum CPU set to {}vcpu".format(maximum_cpu))
            # Assign CPU on vm
            self._common_content_lib.execute_sut_cmd(self.SET_VM_CPU.format(vm_name, vm_cpu),
                                                     self.SET_VM_CPU.format(vm_name, vm_cpu), self._command_timeout)
            self._log.info("VM cpu set to {}vcpu".format(vm_cpu))
        except Exception as ex:
            self._log.error("Exception occurred while reconfiguring VM CPU")
            raise ex

    def find_vm_storage_location(self, vm_name):
        """

        :param: vm_name: Name of the VM
        :return: VM location details
        """
        try:
            vm_location = self._common_content_lib.execute_sut_cmd(self.FIND_VM_LOCATION.format(vm_name),
                                                                   "vm storage info", self._command_timeout)
            stateline = re.findall(r"vda\s*.+", vm_location)[0].split()[1]
            self._log.info("VM location details: {}".format(stateline))
            return stateline
        except Exception as ex:
            self._log.error("Exception occurred while fetching VM location details")
            raise ex

    def reconfigure_disksize_on_vm(self, vm_name, disk_location, disk_size):
        """

        :param: vm_name: Name of the VM
        :param: disk_location: Location of the VM disk
        :param: disk_size: Reconfigurable disk size
        """
        try:
            self._common_content_lib.execute_sut_cmd(self.DISK_RESIZE_CMD.format(vm_name, disk_location, disk_size),
                                                     "vm disk reconfigure",
                                                     self._command_timeout)
            self._log.info("Reconfigured VM disk size to {}GB".format(disk_size))
        except Exception as ex:
            self._log.error("Exception occurred while reconfiguring VM disk size")
            raise ex


class ESXiVmProvider(VMProvider):
    """
    Class to provide VM methods for ESXI platform

    """
    WAIT_VM_RESUME = 200
    VM_WAIT_TIME = 900
    VM_START_TIME = 200
    WIN_USERNAME = "Administrator"
    WIN_PASSWORD = "Intel@123"
    LINUX_USERNAME = "root"
    LINUX_PASSWORD = "password"
    VM_CREATE_THREAD_LIST = []
    SUT_FILE_LOCATION = "vmfs/volumes/datastore1/"
    SUT_ISO_IMAGE_LOCATION = "vmfs/volumes/datastore1/"
    VM_CONFIG_FILE_NAME = "vmware_esxi_vm_config.vmx"
    VMX_DIR_FOR_VM = "{}/{}.vmx"
    ECHO_CMD_TO_FILE = "echo '{}' >> {}"
    CPU_CMD = 'numvcpus = "{}"'
    MEM_CMD = 'memSize = "{}"'
    MEM_MIN = 'sched.mem.min = "{}"'
    MEM_MIN_SIZE = 'sched.mem.minSize = "{}"'
    MEM_MIN_SHARE = 'sched.mem.shares = "normal"'
    DISK_CMD = 'scsi0:0.fileName = "{}.vmdk"'
    ISO_CMD = 'sata0:0.fileName = "/{}"'
    SVGA_VMOTION_CMD = "vmotion.checkpointFBSize"
    SVGA_VMOTION_SIZE = 'vmotion.checkpointFBSize = "4194304"'
    VMNAME_CMD = 'displayName = "{}"'
    OS_VARIANT_CMD = 'guestOS = "{}"'
    NVRAM_CMD = 'nvram = "{}.nvram"'
    EXT_CONFIG_FILE = 'extendedConfigFile = "{}.vmxf"'
    ETHERNET_MAC_TYPE = 'ethernet0.addressType = "{}"'
    MAC_ID = 'ethernet0.address = "{}"'
    CMD_TO_CREATE_VM_HARD_DISK = "vmkfstools -c {}G -d thin /{}{}/{}.vmdk"
    CMD_TO_DESTROY_VM_HARD_DISK = "vmkfstools -U /{}{}/{}.vmdk"
    CMD_TO_REGISTER_ESXI_VM = "vim-cmd solo/registervm /{}{}/{}.vmx"
    CMD_TO_GET_VM_INFO = "vim-cmd /vmsvc/getallvms"
    GET_VM_POWER_STATE = "vim-cmd /vmsvc/get.summary {} | grep powerState"
    VM_POWER_OFF_STR = "poweredOff"
    VM_POWER_ON_STR = "poweredOn"
    VM_POWER_SUSPENDED_STR = "suspended"
    START_VM_CMD = "vim-cmd /vmsvc/power.on {}"
    START_LOCK = threading.Lock()
    GET_VMWARE_TOOL_STATUS_IN_VM = "vim-cmd /vmsvc/get.summary {} | grep toolsStatus"
    VMWARE_TOOLS_STATUS = "toolsOk"
    VMWARE_TOOL_INSTAL_ON_VM = "vim-cmd /vmsvc/tools.install {}"
    __MAC_ADDR_COUNT = 0
    TURNOFF_VM_CMD = "vim-cmd /vmsvc/power.off {}"
    DESTROY_VM_CMD = "vim-cmd /vmsvc/destroy {}"
    RELOAD_VM_CMD = "vim-cmd /vmsvc/reload {}"
    UNREGISTER_VM_CMD = "vim-cmd /vmsvc/unregister {}"
    GET_DEVICES_VM_CMD_ESXI = "vim-cmd /vmsvc/device.getdevices {}"
    SUSPEND_VM_CMD_ESXI = "vim-cmd /vmsvc/power.suspend {}"
    SUSPEND_RESUME_VM_CMD_ESXI = "vim-cmd /vmsvc/power.suspendResume {}"
    RESET_VM_CMD_ESXI = "vim-cmd /vmsvc/power.reset {}"
    SHUTDOWN_VM_CMD_ESXI = "vim-cmd /vmsvc/power.shutdown {}"
    TURNON_VM_CMD_ESXI = "vim-cmd /vmsvc.power.on {}"
    GET_NW_VM_CMD_ESXI = "vim-cmd /vmsvc/get.networks {}"
    REBOOT_VM_CMD_ESXI = "vim-cmd /vmsvc/power.reboot {}"
    DISK_ADD_VM_CMD_ESXI = "vim-cmd /vmsvc/device.diskadd vmid size controller_numer unit_number datastore [ctlr_type]"
    DISK_EXTEND_VM_CMD_ESXI = "vim-cmd /vmsvc/device.diskextend vmid new_size controller_numer unit_number [ctlr_type]"
    DISK_REMOVE_VM_CMD_ESXI = "vim-cmd /vmsvc/device.diskremove vmid controller_number unit_number delete_file [controller_type]"

    RM_DIR_NO_ERROR = "rm -rf {}"
    ENABLE_PCI_PASSTHROUGH_DEVICE = "esxcli hardware pci pcipassthru set -d {} -e True"
    GET_UUID_SUT_INFO = "esxcli system uuid get"
    GET_PCI_VALUES_INFO = "esxcli hardware pci list | grep -E -A 38 {}"
    _REGEX_TO_FETCH_PCIE_DBSF_VALUES = r'\b([0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}.\d{1}\S*)'
    PASSTHROUGH_ID_CMD = 'pciPassthru{}.id = "{}"'
    PASSTHROUGH_DEVICEID_CMD = 'pciPassthru{}.deviceId = "{}"'
    PASSTHROUGH_VENDORID_CMD = 'pciPassthru{}.vendorId = "{}"'
    PASSTHROUGH_SYSTEMID_CMD = 'pciPassthru{}.systemId = "{}"'
    PASSTHROUGH_PRESENT_CMD  = 'pciPassthru{}.present = "TRUE"'
    GET_VMWARE_VM_IP = "vim-cmd /vmsvc/get.summary {} | grep ipAddress"
    SED_CMD_TO_EDIT_VMX_FILE = "sed -i 's/{}.*/{}/g' /{}/{}/{}.vmx"
    GET_USB_INFO_CMD = "lsusb -v | grep -i {}"
    ENABLE_USB_PASSTHROUGH_CMD = "esxcli hardware usb passthrough device enable -d {}"
    DISABLE_USB_PASSTHROUGH_CMD = "esxcli hardware usb passthrough device disable -d {}"
    USB_PASS_THROUGH_CMD = "vim-cmd vmsvc/device.connusbdev {} {}"

    SSH_FILE_NAME = "\OpenSSH-Win64.zip"
    SSH_STR = "OpenSSH-Win64.zip"
    SSH_PATH = Framework.CFG_BASE[OperatingSystems.ESXI]
    VM_ROOT_PATH = CommonContentLib.C_DRIVE_PATH
    VM_SSH_FOLDER = VM_ROOT_PATH + SSH_STR

    ROOT_PATH = "/root"

    SSH_FILE = "'C:\\OpenSSH-Win64\\install-sshd.ps1'"
    START_SERVICE_SSHD_CMD = "'Start-Service sshd'"
    SET_SERVICE_CMD = "'Set-Service -Name sshd -StartupType Automatic'"
    GET_SSH_NAME_CMD = "'Get-NetFirewallRule -Name *ssh*'"

    ENABLE_VM_INTEGRATION_SERVICE_CMD = "scp vmfs/volumes/datastore1/Open*  root@10.190.176.151:C\\Administrator"
    GUEST_SERVICE_STR = "Guest Service Interface"
    SILENT_CONTINUE = "$progressPreference = 'silentlyContinue'"

    COPY_COMMAND_TO_VM = "Connect-VIServer {} -User {} -Password {};Copy-VMGuestFile -Source {} -Destination {} -LocalToGuest -VM {} -GuestUser {} -GuestPassword {}"

    EXTRACT_FILE_STR = "'Expand-Archive -Path {} -DestinationPath {}'"
    ESTABLISH_PS_SESSION = "Connect-VIServer {} -User {}" \
                           " -Password {};$vm = Get-vm -name {};$Output=Invoke-VMScript -vm $vm " \
                           "-ScriptText {} -GuestUser {} -GuestPassword {}"

    def create_vm(self, vm_name, os_variant, no_of_cpu=2, disk_size=6, memory_size=4, vm_creation_timeout=1600,
                  vm_parallel=None, vm_create_async=None, mac_addr=None, pool_id=None, pool_vol_id=None,cpu_core_list=None,
                  nw_bridge=None, vm_os_subtype=None, nesting_level=None, vhdx_dir_path=None, os_version=0,
                  use_powercli=None, devlist=[], qemu=None):
        self._log.info("Create vm function on ESXi")
        linux_distribution_list = [LinuxDistributions.RHEL.lower(), LinuxDistributions.Fedora.lower(),
                                   LinuxDistributions.Ubuntu.lower(), LinuxDistributions.CentOS.lower()]
        vm_name_lower = vm_name.lower()
        vm_list = vm_name_lower.split("_")
        if any(elm in linux_distribution_list for elm in vm_list):
            if mac_addr is not None:
                return self._create_linux_vm(vm_name, os_variant, no_of_cpu, disk_size, memory_size,
                                             vm_creation_timeout,
                                             vm_parallel=vm_parallel, vm_create_async=vm_create_async,
                                             mac_addr=mac_addr, pool_id=pool_id,
                                             pool_vol_id=pool_vol_id, cpu_core_list=cpu_core_list, nw_bridge=nw_bridge,
                                             os_version=os_version, use_powercli=use_powercli)
            else:
                return self._create_linux_vm(vm_name, os_variant, no_of_cpu, disk_size, memory_size,
                                             vm_creation_timeout, vm_parallel=vm_parallel,
                                             vm_create_async=vm_create_async, mac_addr=None, pool_id=pool_id,
                                             os_version=os_version, use_powercli=use_powercli)
        elif "windows" in vm_name.lower():
            if mac_addr is not None:
                return self._create_windows_vm(vm_name, os_variant, no_of_cpu, disk_size, memory_size,
                                               vm_creation_timeout,
                                               vm_parallel=vm_parallel, vm_create_async=vm_create_async, mac_addr=mac_addr,
                                               pool_id=pool_id,
                                               pool_vol_id=pool_vol_id, cpu_core_list=cpu_core_list,
                                               nw_bridge=nw_bridge,
                                               os_version=os_version, use_powercli=use_powercli)
            else:
                return self._create_windows_vm(vm_name, os_variant, no_of_cpu, disk_size, memory_size,
                                               vm_creation_timeout,
                                               vm_parallel=vm_parallel, vm_create_async=vm_create_async,
                                               mac_addr=None,
                                               pool_id=pool_id,
                                               pool_vol_id=pool_vol_id, cpu_core_list=cpu_core_list,
                                               nw_bridge=nw_bridge,
                                               os_version=os_version, use_powercli=use_powercli)

        else:
            raise NotImplementedError("{} VM type is not implemented".format(vm_name))

    def _create_linux_vm(self, vm_name, os_variant, no_of_cpu, disk_size, memory_size, vm_creation_timeout=1600,
                         vm_parallel=None, vm_create_async=None, mac_addr=None, pool_id=None, pool_vol_id=None,
                         cpu_core_list=None,
                         nw_bridge=None, os_version=0, use_powercli=None):
        """
        Execute the the command to create a linux VM.

        :param vm_name: Name of the new VM
        :param vm_create_async: if VM is has to be created in async mode such as required for nested VM
        :param no_of_cpu: No of CPUs in VM
        :param disk_size: Size of the VM disk drive
        :param memory_size: Size of the VM memory
        :param os_variant: linux Os version
        :param vm_creation_timeout: timeout for vm creation
        :param mac_addr: Assign MacAddress to Network.
        :param pool_id: Storage pool id from storage
        :param pool_vol_id: Storage pool Volume id from storage volume created in the given pool
        :param cpu_core_list: CPU core list to be assigned to VM with --cpuset
        :param nw_bridge : Some Non-None value is bridge type default n/w required in VM
        :return vm_name: Name of the new VM
        :raise: RuntimeError
        """
        vm_name_lower_list = vm_name.lower().split("_")
        supported_vm_list = ["linux", "windows", "centos", "rhel", "ubuntu", "fedora"]
        if any(elm in vm_name_lower_list for elm in supported_vm_list):
            verify_iso_image = self._verify_iso_existance(vm_name)
            if not verify_iso_image:
                image_path = self._copy_iso_image_to_esxi_sut(vm_name)
            else:
                self._log.info("ISO image already present on SUT. Continue VM : {}Creation".format(vm_name))
                image_path = self._verify_iso_existance(vm_name)
        else:
            raise NotImplementedError("Only linux and windows VM type is supported and the VM name should contain "
                                      "windows/linux. {} VM type is not implemented".format(vm_name))
        self._log.info("Creating Linux VM named {}".format(vm_name))
        if use_powercli is None:
            self._log.info("Creating Directory for VM named {} under path /{}".format(vm_name, self.SUT_FILE_LOCATION))
            vm_config_path = self.copy_vm_config_file_to_esxi_sut()
            cmd_to_create_vm_config_file = ["mkdir -p /{}{}".format(self.SUT_ISO_IMAGE_LOCATION, vm_name),
                                            "touch /{}{}/{}.vmx".format(self.SUT_ISO_IMAGE_LOCATION, vm_name, vm_name),
                                            "cat {} >> /{}{}".format(vm_config_path, self.SUT_ISO_IMAGE_LOCATION,
                                                                     self.VMX_DIR_FOR_VM.format(vm_name, vm_name))]
            for command in cmd_to_create_vm_config_file:
                self._log.info("Executing command {}".format(command))
                self._common_content_lib.execute_sut_cmd(command, command, self._command_timeout, cmd_path="/")
            self._log.info("Creating VM:{} from config file".format(vm_name))
            self._common_content_lib.execute_sut_cmd(
                self.ECHO_CMD_TO_FILE.format(" ", self.VMX_DIR_FOR_VM.format(vm_name, vm_name)),
                "Creating VM", self._command_timeout, cmd_path="/{}".format(self.SUT_FILE_LOCATION))

            if mac_addr is not None:
                mac_id_list = self._common_content_configuration.get_mac_address_for_vm(self.os.os_type.lower(),
                                                                                        vm_name.split("_")[0].upper())
                mac_id = mac_id_list[self.__MAC_ADDR_COUNT]
                mac_type = "static"
                cmd_to_create_vm_vmx_file = [self.CPU_CMD.format(no_of_cpu), self.MEM_CMD.format(memory_size),
                                             self.MEM_MIN.format(memory_size), self.MEM_MIN_SIZE.format(memory_size),
                                             self.MEM_MIN_SHARE, self.DISK_CMD.format(vm_name),
                                             self.ISO_CMD.format(image_path),
                                             self.VMNAME_CMD.format(vm_name), self.OS_VARIANT_CMD.format(os_variant),
                                             self.NVRAM_CMD.format(vm_name), self.EXT_CONFIG_FILE.format(vm_name),
                                             self.ETHERNET_MAC_TYPE.format(mac_type),
                                             self.MAC_ID.format(mac_id)]
                self.__MAC_ADDR_COUNT += 1
            else:
                mac_type = "generated"
                cmd_to_create_vm_vmx_file = [self.CPU_CMD.format(no_of_cpu), self.MEM_CMD.format(memory_size),
                                             self.MEM_MIN.format(memory_size), self.MEM_MIN_SIZE.format(memory_size),
                                             self.MEM_MIN_SHARE, self.DISK_CMD.format(vm_name),
                                             self.ISO_CMD.format(image_path),
                                             self.VMNAME_CMD.format(vm_name), self.OS_VARIANT_CMD.format(os_variant),
                                             self.NVRAM_CMD.format(vm_name), self.EXT_CONFIG_FILE.format(vm_name),
                                             self.ETHERNET_MAC_TYPE.format(mac_type)]

            for command in cmd_to_create_vm_vmx_file:
                self._log.info(self.ECHO_CMD_TO_FILE.format(command, self.VMX_DIR_FOR_VM.format(vm_name, vm_name)))
                self._common_content_lib.execute_sut_cmd(
                    self.ECHO_CMD_TO_FILE.format(command, self.VMX_DIR_FOR_VM.format(vm_name, vm_name)), command,
                    self._command_timeout, cmd_path="/{}".format(self.SUT_FILE_LOCATION))
            self._log.info("Registering VM from {}.vmx file".format(vm_name))
            self._common_content_lib.execute_sut_cmd_no_exception(self.CMD_TO_CREATE_VM_HARD_DISK.format(
                disk_size, self.SUT_FILE_LOCATION, vm_name, vm_name), "command to create vm hard disk",
                self._command_timeout, ignore_result="ignore")
            self._common_content_lib.execute_sut_cmd(self.CMD_TO_REGISTER_ESXI_VM.format(
                self.SUT_FILE_LOCATION, vm_name, vm_name), "command to register VM", self._command_timeout)
        else:
            new_vm_param = "'Name' = '{}';" \
                           "'Datastore' = 'datastore1';" \
                           "'DiskGB' = {};" \
                           "'NumCpu' = {};" \
                           "'DiskStorageFormat' = 'Thin';" \
                           "'MemoryMB' = {};" \
                           "'GuestId' = '{}';" \
                           "'HardwareVersion' = 'vmx-19';".format(vm_name, disk_size, no_of_cpu, memory_size,
                                                                  os_variant)

            image_host_location = self._common_content_configuration.get_os_iso_location_on_host(
                self.os.os_type.lower(), vm_name.upper().split("_")[0])
            iso_filename = os.path.basename(image_host_location)
            cdrom = "'VM' = '{}'; 'IsoPath' = '[datastore1] {}'; 'StartConnected' = $true;".format(vm_name,
                                                                                                   iso_filename)
            attrib = ""
            cmd = ""
            if mac_addr is not None:
                mac_id_list = self._common_content_configuration.get_mac_address_for_vm(self.os.os_type.lower(),
                                                                                        vm_name.split("_")[0].upper())
                mac_id = mac_id_list[self.__MAC_ADDR_COUNT]
                self.__MAC_ADDR_COUNT += 1
                cmd = r"$NewVMParams = @{} {} {};" \
                      "$vm = New-VM @NewVMParams -RunAsync;" \
                      "sleep -Seconds 10;" \
                      "$NewCDDriveParams = @{} {} {};" \
                      "New-CDDrive @NewCDDriveParams;" \
                      "sleep -Seconds 10;$vm = Get-VM '{}';" \
                      "$spec = New-Object VMware.Vim.VirtualMachineConfigSpec;" \
                      "$spec.Firmware = [VMware.Vim.GuestOsDescriptorFirmwareType]::BIOS;" \
                      "$boot = New-Object VMware.Vim.VirtualMachineBootOptions;" \
                      "$boot.EfiSecureBootEnabled = $false;" \
                      "$spec.BootOptions = $boot;" \
                      "$vm.ExtensionData.ReconfigVM($spec);sleep -Seconds 10;" \
                      "Get-VM '{}' | Get-NetworkAdapter | Set-NetworkAdapter -MacAddress '{}' -Confirm:$false;" \
                      "$vm = Get-VM -Name '{}'; $vm | Get-VMResourceConfiguration | Set-VMResourceConfiguration" \
                      " -MemReservationMB $vm.MemoryMB;".format("{", new_vm_param,
                                                                "}",
                                                                "{", cdrom, "}",
                                                                vm_name, vm_name, mac_id, vm_name)
            else:
                cmd = "$NewVMParams = @{} {} {};" \
                      "$vm = New-VM @NewVMParams -RunAsync;" \
                      "sleep -Seconds 10;" \
                      "$NewCDDriveParams = @{} {} {};" \
                      "New-CDDrive @NewCDDriveParams;" \
                      "sleep -Seconds 10;$vm = Get-VM '{}';" \
                      "$spec = New-Object VMware.Vim.VirtualMachineConfigSpec;" \
                      "$spec.Firmware = [VMware.Vim.GuestOsDescriptorFirmwareType]::bios;" \
                      "$boot = New-Object VMware.Vim.VirtualMachineBootOptions;" \
                      "$boot.EfiSecureBootEnabled = $false;" \
                      "$spec.BootOptions = $boot;sleep -Seconds 10;" \
                      "$vm.ExtensionData.ReconfigVM($spec);" \
                      "$vm = Get-VM -Name '{}'; $vm | Get-VMResourceConfiguration | Set-VMResourceConfiguration" \
                      " -MemReservationMB $vm.MemoryMB;".format("{", new_vm_param, "}", "{", cdrom, "}", vm_name,
                                                                vm_name)

            self.vmp_execute_host_cmd_esxi(cmd=cmd, cwd=".", timeout=60)
            # cmd = "sleep -Seconds  40";
            # self.vmp_execute_host_cmd_esxi(cmd=cmd, cwd=".", timeout=60)
            self._log.info("Created the VM with pwrcli:{}".format(vm_name))

        self._log.info("Starting the VM:{}".format(vm_name))
        if vm_create_async is not None and use_powercli is None:
            start_vm_thread = threading.Thread(target=self.__start_vm_thread,
                                               args=(vm_name,))
            start_vm_thread.start()
            self._log.info(" Started VM creation thread for VM:{}.".format(vm_name))
            self.VM_CREATE_THREAD_LIST.append(start_vm_thread)
        else:
            if use_powercli is None:
                self.start_vm(vm_name)
            else:
                if vm_create_async is not None:
                    self.start_vm_install_parallel(vm_name, vm_parallel=vm_parallel)
                else:
                    self.start_vm_install(vm_name, vm_parallel=vm_parallel)
                    time.sleep(self.VM_START_TIME)

    def _create_windows_vm(self, vm_name, os_variant, no_of_cpu, disk_size, memory_size, vm_creation_timeout=1600,
                           vm_parallel=None, vm_create_async=None, mac_addr=None, pool_id=None, pool_vol_id=None,
                           cpu_core_list=None,
                           nw_bridge=None, os_version=0, use_powercli=None):
        """
        Execute the the command to create a Windows VM.

        :param vm_name: Name of the new VM
        :param vm_create_async: if VM is has to be created in async mode such as required for nested VM
        :param no_of_cpu: No of CPUs in VM
        :param disk_size: Size of the VM disk drive
        :param memory_size: Size of the VM memory
        :param os_variant: linux Os version
        :param vm_creation_timeout: timeout for vm creation
        :param mac_addr: Assign MacAddress to Network.
        :param pool_id: Storage pool id from storage
        :param pool_vol_id: Storage pool Volume id from storage volume created in the given pool
        :param cpu_core_list: CPU core list to be assigned to VM with --cpuset
        :param nw_bridge : Some Non-None value is bridge type default n/w required in VM
        :return vm_name: Name of the new VM
        :raise: RuntimeError
        """
        vm_name_lower_list = vm_name.lower().split("_")
        supported_vm_list = ["linux", "windows", "centos", "rhel", "ubuntu", "fedora"]
        if any(elm in vm_name_lower_list for elm in supported_vm_list):
            verify_iso_image = self._verify_iso_existance(vm_name)
            if not verify_iso_image:
                image_path = self._copy_iso_image_to_esxi_sut(vm_name)
            else:
                self._log.info("ISO image already present on SUT. Continue VM : {}Creation".format(vm_name))
                image_path = self._verify_iso_existance(vm_name)
        else:
            raise NotImplementedError("Only linux and windows VM type is supported and the VM name should contain "
                                      "windows/linux. {} VM type is not implemented".format(vm_name))
        self._log.info("Creating Windows VM named {}".format(vm_name))
        if use_powercli is None:
            self._log.info("Creating Directory for VM named {} under path /{}".format(vm_name, self.SUT_FILE_LOCATION))
            vm_config_path = self.copy_vm_config_file_to_esxi_sut()
            cmd_to_create_vm_config_file = ["mkdir -p /{}{}".format(self.SUT_ISO_IMAGE_LOCATION, vm_name),
                                            "touch /{}{}/{}.vmx".format(self.SUT_ISO_IMAGE_LOCATION, vm_name, vm_name),
                                            "cat {} >> /{}{}".format(vm_config_path, self.SUT_ISO_IMAGE_LOCATION,
                                                                     self.VMX_DIR_FOR_VM.format(vm_name, vm_name))]
            for command in cmd_to_create_vm_config_file:
                self._log.info("Executing command {}".format(command))
                self._common_content_lib.execute_sut_cmd(command, command, self._command_timeout, cmd_path="/")
            self._log.info("Creating VM:{} from config file".format(vm_name))
            self._common_content_lib.execute_sut_cmd(
                self.ECHO_CMD_TO_FILE.format(" ", self.VMX_DIR_FOR_VM.format(vm_name, vm_name)),
                "Creating VM", self._command_timeout, cmd_path="/{}".format(self.SUT_FILE_LOCATION))
            if mac_addr is not None:
                mac_id_list = self._common_content_configuration.get_mac_address_for_vm(self.os.os_type.lower(),
                                                                                        vm_name.split("_")[0].upper())
                mac_id = mac_id_list[self.__MAC_ADDR_COUNT]
                mac_type = "static"
                cmd_to_create_vm_vmx_file = [self.CPU_CMD.format(no_of_cpu), self.MEM_CMD.format(memory_size),
                                             self.DISK_CMD.format(vm_name), self.ISO_CMD.format(image_path),
                                             self.VMNAME_CMD.format(vm_name), self.OS_VARIANT_CMD.format(os_variant),
                                             self.NVRAM_CMD.format(vm_name), self.EXT_CONFIG_FILE.format(vm_name),
                                             self.ETHERNET_MAC_TYPE.format(mac_type),
                                             self.MAC_ID.format(mac_id)]
                self.__MAC_ADDR_COUNT += 1
            else:
                mac_type = "generated"
                cmd_to_create_vm_vmx_file = [self.CPU_CMD.format(no_of_cpu), self.MEM_CMD.format(memory_size),
                                             self.DISK_CMD.format(vm_name), self.ISO_CMD.format(image_path),
                                             self.VMNAME_CMD.format(vm_name), self.OS_VARIANT_CMD.format(os_variant),
                                             self.NVRAM_CMD.format(vm_name), self.EXT_CONFIG_FILE.format(vm_name),
                                             self.ETHERNET_MAC_TYPE.format(mac_type)]
            for command in cmd_to_create_vm_vmx_file:
                self._log.info(self.ECHO_CMD_TO_FILE.format(command, self.VMX_DIR_FOR_VM.format(vm_name, vm_name)))
                self._common_content_lib.execute_sut_cmd(
                    self.ECHO_CMD_TO_FILE.format(command, self.VMX_DIR_FOR_VM.format(vm_name, vm_name)), command,
                    self._command_timeout, cmd_path="/{}".format(self.SUT_FILE_LOCATION))
            self._log.info("Registering VM from {}.vmx file".format(vm_name))
            self._common_content_lib.execute_sut_cmd_no_exception(self.CMD_TO_CREATE_VM_HARD_DISK.format(
                disk_size, self.SUT_FILE_LOCATION, vm_name, vm_name), "command to create vm hard disk",
                self._command_timeout,
                ignore_result="ignore")
            self._common_content_lib.execute_sut_cmd(self.CMD_TO_REGISTER_ESXI_VM.format(
                self.SUT_FILE_LOCATION, vm_name, vm_name), "command to register VM", self._command_timeout)
        else:
            new_vm_param = "'Name' = '{}';" \
                           "'Datastore' = 'datastore1';" \
                           "'DiskGB' = {};" \
                           "'NumCpu' = {};" \
                           "'DiskStorageFormat' = 'Thin';" \
                           "'MemoryMB' = {};" \
                           "'GuestId' = '{}';" \
                           "'HardwareVersion' = 'vmx-19';".format(vm_name, disk_size, no_of_cpu, memory_size,
                                                                  os_variant)

            image_host_location = self._common_content_configuration.get_os_iso_location_on_host(
                self.os.os_type.lower(), vm_name.upper().split("_")[0])
            iso_filename = os.path.basename(image_host_location)
            cdrom = "'VM' = '{}'; 'IsoPath' = '[datastore1] {}'; 'StartConnected' = $true;".format(vm_name,
                                                                                                   iso_filename)
            attrib = ""
            cmd = ""
            if mac_addr is not None:
                mac_id_list = self._common_content_configuration.get_mac_address_for_vm(self.os.os_type.lower(),
                                                                                        vm_name.split("_")[0].upper())
                mac_id = mac_id_list[self.__MAC_ADDR_COUNT]
                self.__MAC_ADDR_COUNT += 1
                cmd = r"$NewVMParams = @{} {} {};" \
                      "$vm = New-VM @NewVMParams -RunAsync;" \
                      "sleep -Seconds 10;" \
                      "$NewCDDriveParams = @{} {} {};" \
                      "New-CDDrive @NewCDDriveParams;" \
                      "sleep -Seconds 10;$vm = Get-VM '{}';" \
                      "$spec = New-Object VMware.Vim.VirtualMachineConfigSpec;" \
                      "$spec.Firmware = [VMware.Vim.GuestOsDescriptorFirmwareType]::BIOS;" \
                      "$boot = New-Object VMware.Vim.VirtualMachineBootOptions;" \
                      "$boot.EfiSecureBootEnabled = $false;" \
                      "$spec.BootOptions = $boot;" \
                      "$vm.ExtensionData.ReconfigVM($spec);sleep -Seconds 10;" \
                      "Get-VM '{}' | Get-NetworkAdapter | Set-NetworkAdapter -MacAddress '{}' -Confirm:$false;" \
                      "$vm = Get-VM -Name '{}'; $vm | Get-VMResourceConfiguration | Set-VMResourceConfiguration" \
                      " -MemReservationMB $vm.MemoryMB;".format("{", new_vm_param,
                                                                "}",
                                                                "{", cdrom, "}",
                                                                vm_name, vm_name, mac_id, vm_name)
            else:
                cmd = "$NewVMParams = @{} {} {};" \
                      "$vm = New-VM @NewVMParams -RunAsync;" \
                      "sleep -Seconds 10;" \
                      "$NewCDDriveParams = @{} {} {};" \
                      "New-CDDrive @NewCDDriveParams;" \
                      "sleep -Seconds 10;$vm = Get-VM '{}';" \
                      "$spec = New-Object VMware.Vim.VirtualMachineConfigSpec;" \
                      "$spec.Firmware = [VMware.Vim.GuestOsDescriptorFirmwareType]::bios;" \
                      "$boot = New-Object VMware.Vim.VirtualMachineBootOptions;" \
                      "$boot.EfiSecureBootEnabled = $false;" \
                      "$spec.BootOptions = $boot;sleep -Seconds 10;" \
                      "$vm.ExtensionData.ReconfigVM($spec);" \
                      "$vm = Get-VM -Name '{}'; $vm | Get-VMResourceConfiguration | Set-VMResourceConfiguration" \
                      " -MemReservationMB $vm.MemoryMB;".format("{", new_vm_param, "}", "{", cdrom, "}", vm_name,
                                                                vm_name)

            self.vmp_execute_host_cmd_esxi(cmd=cmd, cwd=".", timeout=60)
            # cmd = "sleep -Seconds  40";
            # self.vmp_execute_host_cmd_esxi(cmd=cmd, cwd=".", timeout=60)
            self._log.info("Created the VM with pwrcli:{}".format(vm_name))

        self._log.info("Starting the VM:{}".format(vm_name))
        if vm_create_async is not None and use_powercli is None:
            start_vm_thread = threading.Thread(target=self.__start_vm_thread,
                                               args=(vm_name,))
            start_vm_thread.start()
            self._log.info(" Started VM creation thread for VM:{}.".format(vm_name))
            self.VM_CREATE_THREAD_LIST.append(start_vm_thread)
        else:
            if use_powercli is None:
                self.start_vm(vm_name)
            else:
                if vm_create_async is not None:
                    self.start_vm_install_parallel(vm_name, vm_parallel=vm_parallel)
                else:
                    self.start_vm_install(vm_name, vm_parallel=vm_parallel)
                    time.sleep(self.VM_START_TIME)

    def copy_vm_config_file_to_esxi_sut(self):
        """
        Private method to copy the ISO image to the windows SUT
        :param vm_name: Name of the new VM. Either "linux" or "windows" or "esxi" should be included in the name
        :return : complete location of the copied Image file
        """
        self._log.info("Copying VM .vmx config file to ESXi SUT")
        if not self.os.check_if_path_exists(self.SUT_FILE_LOCATION + self.VM_CONFIG_FILE_NAME):
            tool_host_path = self._install_collateral.download_tool_to_host(tool_name=self.VM_CONFIG_FILE_NAME)
            self.os.copy_local_file_to_sut(tool_host_path, self.SUT_FILE_LOCATION + self.VM_CONFIG_FILE_NAME )
            self._log.info("Successfully copied VM .vmx config file to {}".format(self.SUT_FILE_LOCATION))
        else:
            self._log.info("VM .vmx config file already present on SUT location {}".format(self.SUT_FILE_LOCATION))
        return self.SUT_FILE_LOCATION + self.VM_CONFIG_FILE_NAME

    def get_esxi_vm_id_data(self, vm_name):
        """"""
        self._log.info("Getting VM id information for : {}".format(vm_name))
        re_string = re.compile(r"\d*\s*{}.*".format(vm_name))
        cmd_result = self._common_content_lib.execute_sut_cmd_no_exception(self.CMD_TO_GET_VM_INFO,
                                                                           "Command to get VM id",
                                                                           self._command_timeout,
                                                                           ignore_result="ignore")
        research_data = re.findall(re_string, cmd_result)
        vm_id = 0xDEAD
        for elem in research_data:
            if vm_name in elem:
                data_str = ' '.join([str(elm) for elm in research_data])
                vm_id_list = data_str.split()
                vm_id = vm_id_list[0]

        self._log.info("VM id for {}: {}".format(vm_name, vm_id))
        return vm_id

    def _verify_iso_existance(self, vm_name, vm_os_subtype=None):
        """
         Method to verify if ISO image already present on the windows SUT

        :param vm_name: Name of the new VM. Either "linux" or "windows" or "esxi" should be included in the name
        :param vm_os_subtype: sub OS type
        :return : Complete location of ISO image
        """
        self._log.info("Check if ISO image already present on SUT for given VM")
        vm_name = vm_name.split("_")[0]
        self._log.info("Given os Base variant is {} and subtype is {}".format(vm_name, vm_os_subtype))
        self._log.info("Check if {} folder exist".format(self.SUT_ISO_IMAGE_LOCATION))
        if not self.os.check_if_path_exists(self.SUT_ISO_IMAGE_LOCATION, directory=self.SUT_ISO_IMAGE_LOCATION):
            raise RuntimeError("DataStore path for ISO image: {} doesn't exist on SUT".format(self.SUT_ISO_IMAGE_LOCATION))
        if "rhel" in vm_name.lower() or "centos" in vm_name.lower():
            self._log.info("Check if {} folder exist for given VM {}".format(self.SUT_ISO_IMAGE_LOCATION, vm_name))
            image_host_location = self._common_content_configuration.get_os_iso_location_on_host(self.os.os_type.lower(), vm_name)
            iso_filename = self.SUT_ISO_IMAGE_LOCATION + os.path.basename(image_host_location)
            cmd_result = self.os.check_if_path_exists(iso_filename)
            if cmd_result:
                return iso_filename
            return False
        elif "windows" in vm_name.lower():
            self._log.info("Check if {} folder exist for given VM {}".format(self.SUT_ISO_IMAGE_LOCATION, vm_name))
            image_host_location = self._common_content_configuration.get_os_iso_location_on_host(self.os.os_type.lower(), vm_name)
            iso_filename = self.SUT_ISO_IMAGE_LOCATION + os.path.basename(image_host_location)
            cmd_result = self.os.check_if_path_exists(iso_filename)
            if cmd_result:
                return iso_filename
            return False
        else:
            raise RuntimeError("Not implemented for VM name :{}".format(vm_name))

    def _copy_iso_image_to_esxi_sut(self, vm_name):
        """
        Private method to copy the ISO image to the windows SUT
        :param vm_name: Name of the new VM. Either "linux" or "windows" should be included in the name
        :return : complete location of the copied Image file
        """
        self._log.info("Copying ISO image to ESXi SUT")
        vm_name = vm_name.split("_")[0]
        image_host_location = self._common_content_configuration.get_os_iso_location_on_host(self.os.os_type.lower(),
                                                                                             vm_name)
        file_name = os.path.basename(image_host_location)
        if not os.path.exists(image_host_location):
            raise RuntimeError("ISO image is not present.Note that this ISO image is expected to support "
                               "unattended installation. Please keep the file under {} "
                               .format(image_host_location))
        cmd_result = self._common_content_lib.execute_sut_cmd("ls", "getting the folder content",
                                                              self._command_timeout,
                                                              cmd_path=self.SUT_ISO_IMAGE_LOCATION)
        self._log.debug("{} Folder contains :\n{}".format(self.SUT_ISO_IMAGE_LOCATION, cmd_result))
        if not self.os.check_if_path_exists(self.SUT_ISO_IMAGE_LOCATION + file_name):
            self.os.copy_local_file_to_sut(image_host_location, self.SUT_ISO_IMAGE_LOCATION + file_name)
            self._log.info("Successfully copied the .iso image file to {}".format(self.SUT_ISO_IMAGE_LOCATION))
        return file_name

    def create_vm_from_template(self, vm_name, memory_size=4, vm_creation_timeout=1600, gen=1):
        """
        Execute the the command to create a VM from an existing template base image in vhdx format.

        :param vm_name: Name of the new VM. Either "linux" or "windows" should be included in the name
        :param memory_size: Size of the VM memory
        :param vm_creation_timeout: timeout for vm creation in ms.
        :param gen: VM generation.

        :raise: RunTimeError
        """
        raise NotImplementedError

    def _copy_vm_template_to_sut_windows_sut(self, vm_name):
        """
        Private method to copy the vm template file to the windows SUT
        :param vm_name: Name of the new VM. Either "linux" or "windows" should be included in the name
        :return : complete location of the copied Image file
        """
        raise NotImplementedError

    def create_bridge_network(self, switch_name):
        """
        Method to create the network bridge on SUT.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    def add_vm_network_adapter(self, methods, vm_name, physical_adapter_name, switch_name, vm_type=None, mac_addr=None):
        """
        Method to add network adapter for given VM.

        :param methods: The methods to add network adapter to VM. The value is expected to be "DDA" or "SRIOV".
        :param vm_name: Name of the VM.
        :param physical_adapter_name: Name of the physical network adapter on SUT.
                             Note: the adapter is expected to be extra test NIC instead of builtin NIC.
        :param switch_name: Name of the switch you create
        :param vm_type: VM type for eg: "RS5"
        :param mac_addr: Assign Mac Address to Network Adapter
        :raise: RunTimeError
        :return: None
        """
        raise NotImplementedError

    def _get_vm_network_adapter(self, vm_name):
        """
        Method to add network adapter for given VM.

        :param vm_name: Name of the VM.
        :raise: RunTimeError. It will the error caught when executing the GET_VM_NETWORK_ADAPTER_CMD.
        :return: None
        """
        raise NotImplementedError

    def add_vm_ethernet_adapter(self, vm_name, switch_name):
        """
        Method to add network adapter for given VM.

        :param vm_name: Name of the VM.
        :raise: RunTimeError. It will the error caught when executing the GET_VM_NETWORK_ADAPTER_CMD.
        :return: None
        """
        raise NotImplementedError

    def _add_vm_network_adapter_via_sriov(self, vm_name, physical_adapter_name, switch_name):
        """
        Method to add network adapter via SRIOV. The given network adapter will be assigen to VM as a virtual function.

        :param vm_name: Name of the VM.
        :param physical_adapter_name: Name of the physical network adapter on SUT.
                             Note: the adapter is expected to support SRIOV feature.
        :param switch_name: Name of the switch you create
        :raise: RunTimeError. It will be whatever caught inside the try block. It can be the exception when calling the
        execute_sut_cmd() or when calling other private function in ESXiVMProvider.
        :return: None
        """
        raise NotImplementedError

    def _add_vm_network_adapter_via_dda(self, vm_name, switch_name, vm_type=None, mac_addr=None):

        """
        Method to add network adapter via DDA(Direct Device Assignment),which means pass through physical network
        adapter on SUT to VM.

        :param vm_name: Name of the VM.
        :param switch_name: Name of the switch you create
        :param mac_addr: Assign Mac Address to Network Adaptor
        :raise: RunTimeError. It will be whatever caught inside the try block. It can be the exception when calling the
        execute_sut_cmd() or when calling other private function in ESXiVMProvider.
        :return: None
        """
        raise NotImplementedError

    def start_vm(self, vm_name):
        """
        Method to start VM.

        :param vm_name: Name of the VM to start
        :raise: RuntimeError. It will raise error when failed in executing the START_VM_CMD.
        """
        try:
            vm_id = self.get_esxi_vm_id_data(vm_name)
            vm_state = self._get_vm_state(vm_name, vm_id)
            if self.VM_POWER_ON_STR not in vm_state or self.VM_POWER_SUSPENDED_STR in vm_state:
                self._log.info("{} is powered off. Powering on VM\n".format(vm_name))
                start_vm_result = self._common_content_lib.execute_sut_cmd(
                    self.START_VM_CMD.format(vm_id), "Start VM: {}".format(vm_name), 60)
                self._log.info("Successfully started VM {}".format(vm_name))
                # time.sleep(self.VM_START_TIME)
                self.wait_check_for_vm_to_bootup_esxi(vm_name, self.VM_START_TIME)
            elif self.VM_POWER_ON_STR in vm_state:
                self._log.info("WARNING: VM {} is already in running state.".format(vm_name))
        except RuntimeError:
            self._log.error("Unable to start the VM : {}".format(vm_name))
            raise

    def wait_check_for_vm_to_bootup_esxi(self, vm_name, max_wait=VM_WAIT_TIME):
        """
        $vm = get-vm vm_name
        Start-Sleep -Seconds 20;
        $vm  | Get-VMQuestion | Set-VMQuestion -DefaultOption -confirm:$false;
        do
        {
            Start-Sleep -Seconds 5;
            $toolsStatus = $vm.extensionData.Guest.ToolsStatus;
        }while($toolsStatus -ne "toolsOK");
        """

        cmd = "$vm = get-vm {}; Start-Sleep -Seconds 30;$tm=0;" \
              "$vm | Get-VMQuestion | Set-VMQuestion -DefaultOption -confirm:$false;" \
              "do {{ Start-Sleep -Seconds 5; $tm = $tm + 5;" \
              "$vm = get-vm {}; $vm | Get-VMQuestion | Set-VMQuestion -DefaultOption -confirm:$false;" \
              "$toolsStatus = $vm.extensionData.Guest.ToolsStatus;}}" \
              " while($toolsStatus -ne 'toolsOK' -And $tm -le {});".format(vm_name, vm_name, max_wait)
        self.vmp_execute_host_cmd_esxi(cmd=cmd, cwd=".", timeout=max_wait)
        cmd = "Start-Sleep -Seconds 30;"
        self.vmp_execute_host_cmd_esxi(cmd=cmd, cwd=".", timeout=60)

    def start_vm_install(self, vm_name, vm_parallel=None):
        """
        Method to start VM.

        :param vm_name: Name of the VM to start
        :raise: RuntimeError. It will raise error when failed in executing the START_VM_CMD.
        """
        try:
            vm_id = self.get_esxi_vm_id_data(vm_name)
            vm_state = self._get_vm_state(vm_name, vm_id)
            if self.VM_POWER_ON_STR not in vm_state or self.VM_POWER_SUSPENDED_STR in vm_state:
                self._log.info("{} is powered off. Powering on VM\n".format(vm_name))
                start_vm_result = self._common_content_lib.execute_sut_cmd(
                    self.START_VM_CMD.format(vm_id), "Start VM: {}".format(vm_name), 60)
                self._log.info("Successfully started VM {}".format(vm_name))
                # time.sleep(self.VM_WAIT_TIME)
                if vm_parallel == None:
                    self.wait_check_for_vm_to_bootup_esxi(vm_name, self.VM_WAIT_TIME)
            elif self.VM_POWER_ON_STR in vm_state:
                self._log.info("WARNING: VM {} is already in running state.".format(vm_name))
        except RuntimeError:
            self._log.error("Unable to start the VM : {}".format(vm_name))
            raise

    def start_vm_install_parallel(self, vm_name, vm_parallel=None):
        """
        Method to start VM.

        :param vm_name: Name of the VM to start
        :raise: RuntimeError. It will raise error when failed in executing the START_VM_CMD.
        """
        try:
            vm_id = self.get_esxi_vm_id_data(vm_name)
            vm_state = self._get_vm_state(vm_name, vm_id)
            if self.VM_POWER_ON_STR not in vm_state or self.VM_POWER_SUSPENDED_STR in vm_state:
                self._log.info("{} is powered off. Powering on VM\n".format(vm_name))
                start_vm_result = self._common_content_lib.execute_sut_cmd(
                    self.START_VM_CMD.format(vm_id), "Start VM: {}".format(vm_name), 60)
                self._log.info("Successfully started VM {}".format(vm_name))
                # time.sleep(self.VM_WAIT_TIME)
                # self.wait_check_for_vm_to_bootup_esxi(vm_name, self.VM_WAIT_TIME)
            elif self.VM_POWER_ON_STR in vm_state:
                self._log.info("WARNING: VM {} is already in running state.".format(vm_name))
        except RuntimeError:
            self._log.error("Unable to start the VM : {}".format(vm_name))

    def __start_vm_thread(self, vm_name):
        """
        Method to start VM in Thread.

        :param vm_name: Name of the VM to start
        :raise: RuntimeError. It will raise error when failed in executing the START_VM_CMD.
        """
        try:
            vm_id = self.get_esxi_vm_id_data(vm_name)
            vm_state = self._get_vm_state(vm_name, vm_id)
            self.START_LOCK.acquire()
            if self.VM_POWER_ON_STR not in vm_state:
                self._log.info("{} is powered off. Powering on VM\n".format(vm_name))
                start_vm_result = self._common_content_lib.execute_sut_cmd(
                    self.START_VM_CMD.format(vm_id), "Start VM: {}".format(vm_name), 60)
                self._log.info("Successfully started VM {}".format(vm_name))
            elif self.VM_POWER_ON_STR in vm_state:
                self._log.info("WARNING: VM {} is already in running state.".format(vm_name))
            time.sleep(self.VM_WAIT_TIME)
            self.START_LOCK.release()
        except RuntimeError:
            self._log.error("Unable to start the VM : {}".format(vm_name))
            raise

    def _shutdown_vm(self, vm_name):
        """
        Method to shutdown the VM.

        :param vm_name: Name of the VM to shutdown
        :raise: RunTimeError
        """
        try:
            vm_id = self.get_esxi_vm_id_data(vm_name)
            if vm_id == 0xDEAD:
                self._log.error("No VM found: {}".format(vm_name))
                return
            vm_state = self._get_vm_state(vm_name, vm_id)
            if self.VM_POWER_ON_STR in vm_state:
                self._common_content_lib.execute_sut_cmd(self.SHUTDOWN_VM_CMD_ESXI.
                                                                              format(vm_name),
                                                                              "Shutdown VM: {}".format(vm_name), 60)
            self._log.info("Successfully shutdown VM {}".format(vm_name))
        except RuntimeError:
            raise

    def reboot_vm(self, vm_name):
        """
        This method is to reboot the VM & verify if it is running or not

        :param vm_name: name of the VM
        """
        self._log.info("Rebooting the {} VM".format(vm_name))
        vm_id = self.get_esxi_vm_id_data(vm_name)
        if vm_id == 0xDEAD:
            self._log.error("No VM found: {}".format(vm_name))
            return
        vm_state = self._get_vm_state(vm_name, vm_id)
        if self.VM_POWER_ON_STR in vm_state:
            reboot_result = self._common_content_lib.execute_sut_cmd(
                                self.REBOOT_VM_CMD_ESXI.format(self.SILENT_CONTINUE, vm_name),
                                "restarting VM", self._command_timeout)
            self.wait_for_vm(vm_name)
        self._log.debug("Wait VM stdout:\n{}".format(reboot_result))
        self._log.info("Successfully Rebooted {} VM".format(vm_name))

    def wait_for_vm(self, vm_name):
        """
        This method is to wait for VM to boot properly after starting the VM
        """
        time.sleep(self.WAIT_VM_RESUME)

    def unregister_vm(self, vm_name):
        """
        Method to unregister the VM

        :param vm_name: Name of the VM to unregister
        :raise: RunTimeError
        """
        try:
            vm_id = self.get_esxi_vm_id_data(vm_name)
            if vm_id == 0xDEAD:
                self._log.error("No VM found: {}".format(vm_name))
                return
            vm_state = self._get_vm_state(vm_name, vm_id)
            if self.VM_POWER_ON_STR in vm_state:
                self.turn_off_vm(vm_name)
                self._log.info("{} is powered off now\n".format(vm_name))
            self._common_content_lib.execute_sut_cmd_no_exception(
                self.UNREGISTER_VM_CMD.format(vm_id), "Unregister VM: {}".format(vm_name), 60,
                ignore_result="ignore")
            self._log.info("Successfully unregistered VM {}".format(vm_name))

        except RuntimeError:
            self._log.error("Unable to unregister the VM : {}".format(vm_name))
            raise

    def register_vm(self, vm_name):
        """
        Method to register the VM

        :param vm_name: Name of the VM to register
        :raise: RunTimeError
        """
        try:
            vm_id = self.get_esxi_vm_id_data(vm_name)
            if vm_id == 0xDEAD:
                self._log.error("No VM found: {}".format(vm_name))
                return
            self._common_content_lib.execute_sut_cmd(self.CMD_TO_REGISTER_ESXI_VM.format(
                self.SUT_FILE_LOCATION, vm_name, vm_name), "command to register VM", self._command_timeout)
            self._log.info("Successfully registered VM {}".format(vm_name))
            self.start_vm(vm_name)
            self._log.info("Starting the VM:{}".format(vm_name))
            time.sleep(self.VM_WAIT_TIME)
        except RuntimeError:
            self._log.error("Unable to register the VM : {}".format(vm_name))
            raise

    def destroy_vm(self, vm_name):
        """
        Method to destroy the VM & it's resources

        :param vm_name: Name of the VM to destroy
        :raise: RunTimeError
        """
        try:
            vm_id = self.get_esxi_vm_id_data(vm_name)
            if vm_id == 0xDEAD:
                self._log.error("No VM found: {}".format(vm_name))
                return
            vm_state = self._get_vm_state(vm_name, vm_id)
            if self.VM_POWER_ON_STR not in vm_state:
                self._log.info("{} is powered off. Destroying the VM\n".format(vm_name))
                self._common_content_lib.execute_sut_cmd_no_exception(
                    self.UNREGISTER_VM_CMD.format(vm_id), "Unregister VM: {}".format(vm_name), 60,
                    ignore_result="ignore")
                self._log.info("Successfully unregistered VM {}".format(vm_name))
                self._common_content_lib.execute_sut_cmd_no_exception(
                    self.DESTROY_VM_CMD.format(vm_id), "Destroy VM: {}".format(vm_name), 60,
                    ignore_result="ignore")
                self._log.info("Successfully Destroyed VM {}".format(vm_name))
            elif self.VM_POWER_ON_STR in vm_state:
                self.turn_off_vm(vm_name)
                self._common_content_lib.execute_sut_cmd_no_exception(
                    self.UNREGISTER_VM_CMD.format(vm_id), "Unregister VM: {}".format(vm_name), 60,
                    ignore_result="ignore")
                self._log.info("Successfully unregistered VM {}".format(vm_name))
                self._common_content_lib.execute_sut_cmd_no_exception(
                    self.DESTROY_VM_CMD.format(vm_id), "Destroy VM: {}".format(vm_name), 60,
                    ignore_result="ignore")
                self._log.info("Successfully Destroyed VM {}".format(vm_name))
            self._log.info("Deleting the harddisk for VM from {}.vmx file".format(vm_name))
            self._common_content_lib.execute_sut_cmd_no_exception(self.CMD_TO_DESTROY_VM_HARD_DISK.format(
                self.SUT_FILE_LOCATION, vm_name, vm_name), "command to destroy vm hard disk",
                self._command_timeout, ignore_result="ignore")
            self._log.info("Deleted the harddisk for the VM:{}".format(vm_name))
            if vm_name is not None and vm_name != "":
                self._common_content_lib.execute_sut_cmd_no_exception(self.RM_DIR_NO_ERROR.format(vm_name),
                                                            "command to destroy VM directory",
                                                             self._command_timeout,
                                                            cmd_path="/{}".format(self.SUT_ISO_IMAGE_LOCATION),
                                                            ignore_result="ignore")
                self._log.info("Deleted the VM file folder for the VM:{}".format(vm_name))
        except RuntimeError:
            self._log.error("Unable to Destroy the VM : {}".format(vm_name))
            raise

    def _get_vm_state(self, vm_name, vm_id):
        """
        Method to get state of the given VM

        :param vm_name: the name of the given VM
        :raise: RunTimeError
        :return: the state of cpus. Running/Off/Paused
        """
        try:
            vm_info = self._common_content_lib.execute_sut_cmd_no_exception(self.GET_VM_POWER_STATE.format(vm_id),
                                                               "Get state of VM: {}".format(vm_name), 60,
                                                                ignore_result="ignore")
            self._log.info("Get state info:\n{}".format(vm_info))
            str_list = vm_info.split('"')
            state = str_list[1]
            self._log.info(str_list)
            if state is None:
                return RuntimeError("Fail to get state info of the VM.")
            else:
                self._log.info("State of VM{}:{}\n".format(vm_name, state))
                return state
        except RuntimeError:
            raise

    def _get_vm_num_of_cpus(self, vm_name):
        """
        Method to get the number of cpus of the given VM

        :param vm_name: the name of the given VM
        :raise: RunTimeError
        :return: the number of cpus
        """
        raise NotImplementedError

    def update_vm_num_of_cpus(self, vm_name, cpu_config):
        """
        Method to Update number of cpus of the given VM

        :param vm_name: the name of the given VM
        :param cpu_config: updated CPU config value
        :raise: RunTimeError
        :return: the number of cpus
        """
        raise NotImplementedError

    def _get_vm_vhd_path(self, vm_name):
        """
        Method to get the VHD Path of the given VM

        :param vm_name: the name of the given VM
        :raise: RunTimeError
        :return: Path of the vhd of the given VM
        """
        raise NotImplementedError

    def get_vm_ip(self, vm_id, vm_name):
        """
        Method to get the IPV4 address of the given VM

        :param vm_name: Name of the VM to get the IP
        :raise: RunTimeError
        :return: ip address in string type
        """
        try:
            vm_ip_info = self._common_content_lib.execute_sut_cmd(self.GET_VMWARE_VM_IP.format(vm_id),
                                                                 "Get vm ip of VM : {}".format(vm_name), 60)
            self._log.info("Get vm ip info:\n{}".format(vm_ip_info))
            str_list = vm_ip_info.split('"')
            vm_ip_status = str_list[1]
            self._log.info(str_list)
            if vm_ip_status is None:
                return RuntimeError("Fail to get vm ip info of the VM {}".format(vm_name))
            else:
                self._log.info("vm ip of VM{}:{}\n".format(vm_name, vm_ip_status))
                return vm_ip_status
        except RuntimeError:
            raise

    def __get_linux_vm_password(self):
        """
        This private method will get the OS password of the VM and return it

        :return password: OS password of the VM
        :raise: Exception
        """
        try:
            self._log.info("Getting the VM password from the Kick-start file")
            kstart_file_path = self._install_collateral.download_tool_to_host("linux_vm_kstart.cfg")
            with open(kstart_file_path, "r+") as fp:
                kstart_file_data = fp.read()
                if re.search("rootpw", kstart_file_data):
                    password = re.findall("rootpw.*", kstart_file_data)[0].split()[1].strip()
                    self._log.info("Successfully retrieve the password of linux VM: {}".format(password))
                    return password
        except Exception as ex:
            raise ("Could not retrieve the password of linux VM due to {}".format(ex))

    def destroy_network_adapter(self, vm_name):
        raise NotImplementedError

    def remove_bridge_network(self):
        """
        Method to remove the existed network bridge on SUT.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    def create_vm_host(self, os_subtype, os_version, kernel_vr, vm_ip):
        """
        Method to create os executable object for given VM.

        :param vm_ip: ip of the VM OS
        :param vm_username: username of the VM
        :param os_version: os version
        :param os_subtype: os subtype
        :param kernel_vr: kernel version
        :param vm_password: Password of the VM
        :return : None
        """
        if os_subtype in [VMs.WINDOWS]:
            os_name = OperatingSystems.WINDOWS
            vm_username = self.WIN_USERNAME
            vm_password = self.WIN_PASSWORD
        elif os_subtype in [VMs.RHEL] or os_subtype in [VMs.CENTOS]:
            os_name = OperatingSystems.LINUX
            vm_username = self.LINUX_USERNAME
            vm_password = self.LINUX_PASSWORD
        vm_cfg_opts = ElementTree.fromstring(VM_CONFIGURATION_FILE.format(os_name, os_subtype, os_version, kernel_vr,
                                                                          vm_username, vm_password, vm_ip))
        vm_os_obj = ProviderFactory.create(vm_cfg_opts, self._log)
        return vm_os_obj


    def ping_vm_from_sut(self, vm_ip, vm_name=None, vm_account=None, vm_password=None):
        """
        This method is to ping the VM from SUT system

        :param vm_name: name of given VM
        :param vm_ip: IP of the VM
        :param vm_account: user account for the VM
        :param vm_password: password for the VM account
        :return: ping result of the VM
        :raise: RunTimeError
        """

        try:
            self._log.info("pinging {} from SUT".format(vm_ip))
            ping_result = self._common_content_lib.execute_sut_cmd("ping -c 4 {}".format(vm_ip),
                                                                   "pinging {}".format(
                                                                       vm_ip), self._command_timeout)
            self._log.debug("Ping result data :\n{}".format(ping_result))

            match = re.compile(
                r'(\d+) packets transmitted, (\d+) (?:packets )?received, (\d+\.?\d*)% packet loss').search(
                ping_result)

            if not match:
                raise content_exceptions.TestFail('Invalid PING output:\n' + ping_result)

            sent, received, packet_loss = match.groups()
            # check for ping output and loss

            if (int(sent) != int(received)) and (float(packet_loss) > 5):
                raise content_exceptions.TestFail("Data Loss is Observed at test {}%".format(packet_loss))
                return False

            self._log.info("Successfully pinged the VM from SUT")
            return True
        except Exception as ex:
            self._log.error("Fail to ping the VM from SUT")
            return False

    def _disable_firewall_on_windows_vm(self, vm_name, vm_account, vm_password):
        """
        Method to disable firewall on windows VM

        :param vm_name: the name of given VM
        :params vm_account: account for os
        :params vm_password: password for the account
        :raise: RunTimeError
        :return: None
        """
        raise NotImplementedError

    def _get_vm_memory_info(self, vm_name):
        """
        Method to get the startup memory size of the given VM

        :param vm_name: the name of given VM
        :raise: RunTimeError
        :return: memory info of the given VM in dict type.
                 Example: {'VMName': 'esxi_VM1', 'DynamicMemoryEnabled': 'False', 'Minimum(M)': '512', 'Startup(M)': '2048', 'Maximum(M)': '1048576'}
        """
        raise NotImplementedError

    def update_vm_memory_info(self, vm_name, memory_config):
        """
        Method to Update the VM memory configuration

        :param vm_name: the name of the given VM
        :param memory_config: updated VM memory value
        :raise: RunTimeError
        :return: None
        """
        raise NotImplementedError

    def _get_vm_list(self):
        """
        This method is to get the list of current VMs

        :return: a list which contains the names of current VMs
        :raise: RunTimeError
        """
        vm_list = []
        try:
            get_vm_result = self._common_content_lib.execute_sut_cmd(self.GET_VM_LIST_CMD,
                                                                     "Get VM list", 60)
            self._log.info("All available vm data  is:\n{}".format(get_vm_result))
            str_list = get_vm_result.split('\n')
            index = 0
            for str in str_list:
                if str is not '' and '---' not in str:
                    res = re.finditer(r"\S+", str)
                    for match in res:
                        if index is 0:
                            index = index + 1
                            break
                        vm_list.append(match.group())
                        break
        except RuntimeError:
            raise
        return vm_list

    def get_vm_info(self, vm_name):
        """
        This method is to get the vm info about the given VM

        :param vm_name: name of the VM
        :return: vm data with dict type which contains info about name, os_type, state, memory_info
        :raise: RunTimeError
        """
        raise NotImplementedError

    def copy_file_from_sut_to_vm(self, vm_name, vm_username, source_path, destination_path):
        """
        This method is to copy file from SUT to VM

        :raise: NotImplementedError
        """
        raise NotImplementedError

    def copy_file_to_vm_storage_device(self, disk_id, vm_os_obj, command_exec_obj):
        """
        This method is to copy the test file to VM USB from HOST

        :param disk_id: DiskNumber to get Drive volume details. ex: C:\ or E:\
        :param vm_os_obj: os object for VM
        :param command_exec_obj: OS object to execute command.
        """
        raise NotImplementedError


    def copy_ssh_file_to_vm(self, vm_name, vm_account, vm_password, source_path, destination_path, common_content_lib_vm_obj=None):
        """
        This method is to copy file from SUT to VM
        :param vm_name : name of the VM. ex: ESXI_1
        :param vm_account : VM admin account "root"
        :param vm_password : VM password
        :param source_path : SSH file path in SUT
        :param destination_path: Destination path in VM
        :return : None

        :raise: NotImplementedError
        """
        try:
            self._log.info("Copying {} from SUT to VM".format(self.SSH_FILE_NAME))

            #===========================================================
            copy_ssh_file = self.COPY_COMMAND_TO_VM.format(self.sut_ip, self.sut_user, self.sut_pass,source_path,destination_path, vm_name,vm_account, vm_password)

            self._log.info(copy_ssh_file)
            command_result = os.system(
                "powershell $progressPreference = 'silentlyContinue'; {}".format(copy_ssh_file))

            #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



            script_block = self.EXTRACT_FILE_STR.format(self.VM_SSH_FOLDER, self.VM_ROOT_PATH)


            extract_file = self.ESTABLISH_PS_SESSION.format(self.sut_ip, self.sut_user,self.sut_pass,
                                                            vm_name, script_block, vm_account, vm_password)
            self._log.info(extract_file)
            command_result = os.system(
                "powershell $progressPreference = 'silentlyContinue'; {}".format(extract_file))
            # self._log.debug(command_result)
            self._log.info("Successfully copied OpenSSH file & Extracted in VM.")
        except Exception as ex:
            raise ("Failed to Copy OpenSSH to VM! {}".format(ex))
        #raise NotImplementedError

    def copy_ssh_package_to_esxi_sut(self):
        """
        This method used to copy openSSH zip file to the windows SUT.

        :return:ssh_file_path_host : SSH folder path in Windows SUT
        """

        self._log.info("copying open-ssh zip file from Host to SUT...")
        ssh_file_path = self._install_collateral.download_tool_to_host("OpenSSH-Win64.zip")
        # self._log.info("Path to copy in SUT",ssh_file_path,self.SSH_PATH)
        self.os.copy_local_file_to_sut(ssh_file_path, self.SSH_PATH)
        self._log.info("Successfully copied the open-ssh  file to SUT")
        host_file_path = self.SSH_PATH + self.SSH_STR
        return host_file_path

    def _enable_ssh_in_vm(self, vm_id, vm_name, vm_account, vm_password, copy_open_ssh=True,
                          common_content_lib_vm_obj=None):
        """
        This method is used to enable SSH in VM.

        :param vm_name : name of the VM. ex: ESXI_1
        :param vm_account : VM admin account "root"
        :param vm_password : VM password
        :param copy_open_ssh : To copy open SSh tool to VM
        :return : None
        """
        if "WINDOWS" in vm_name:
            try:
                vm_ip = self.get_vm_ip(vm_id, vm_name)
                self._log.info("Enabling SSH in VM : {}...".format(vm_name))
                if copy_open_ssh:
                    host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.SSH_STR)
                    self.copy_ssh_file_to_vm(vm_name, vm_account, vm_password, host_path, self.VM_SSH_FOLDER,
                                             common_content_lib_vm_obj=common_content_lib_vm_obj)

                run_ssh_cmd = self.ESTABLISH_PS_SESSION.format(self.sut_ip, self.sut_user, self.sut_pass,
                                                               vm_name, self.SSH_FILE, vm_account, vm_password)

                start_ssh = self.ESTABLISH_PS_SESSION.format(self.sut_ip, self.sut_user, self.sut_pass,
                                                             vm_name, self.START_SERVICE_SSHD_CMD, vm_account,
                                                             vm_password)

                set_ssh_service = self.ESTABLISH_PS_SESSION.format(self.sut_ip, self.sut_user, self.sut_pass,
                                                                   vm_name, self.SET_SERVICE_CMD, vm_account,
                                                                   vm_password)

                get_ssh_name = self.ESTABLISH_PS_SESSION.format(self.sut_ip, self.sut_user, self.sut_pass,
                                                                vm_name, self.GET_SSH_NAME_CMD, vm_account, vm_password)

                ssh_commands_list = [run_ssh_cmd, start_ssh, set_ssh_service, get_ssh_name]
                for each_command in ssh_commands_list:
                    try:
                        command_result = os.system(
                            "powershell $progressPreference = 'silentlyContinue'; {}".format(each_command))
                        self._log.debug(command_result)
                    except:
                        pass
                    time.sleep(20)
                    self._log.info("Successfully Enabled SSH in VM : {}...".format(vm_name))

            except Exception as ex:
                raise ("Error while enabling SSH in VM : {}...".format(ex))
        elif "RHEL" or "CENTOS" in vm_name:
            pass

    def enumerate_storage_device(self, bus_type, index_value, command_exec_obj):
        """
        This method is to list all available storage device on SUT.

        :param bus_type: Storage Device type. ex: NVMe, USB
        :param index_value: Index value for Disk
        :param command_exec_obj: Command executable OS object. ex: SUT or VM object.
        :return: device_list
        """
        raise NotImplementedError

    def set_disk_offline(self, disk_id, command_exec_obj):
        """
        This method is to set disk offline for Storage passthrough.

        :param disk_id: Storage Device id.
        :param command_exec_obj: Object to execute commands. Ex : Sut object or Vm object
        :return: None
        """
        raise NotImplementedError

    def set_disk_online(self, disk_id, command_exec_obj):
        """
        This method is to set disk offline for Storage passthrough.

        :param disk_id: Storage Device id.
        :param command_exec_obj: Object to execute commands. Ex : Sut object or Vm object
        :return: None
        """
        raise NotImplementedError

    def add_storage_device_to_vm(self, vm_name, vm_disk_name, storage_size):
        """
        This method is add additional storage device to VM

        :param vm_name: name of the VM
        :param vm_disk_name: disk name going to attach to the VM
        :param storage_size: size of the storage device to add in GB
        :return: None
        """
        raise NotImplementedError

    def remove_storage_device_from_vm(self, vm_name):
        """
        This method is add additional storage device to VM

        :param vm_name: name of the VM
        :return: None
        """
        raise NotImplementedError

    def suspend_resume_vm(self, vm_name):
        """
        This method is to suspend and resume the existing VM

        :param vm_name: Name of the VM
        """
        try:
            vm_id = self.get_esxi_vm_id_data(vm_name)
            if vm_id == 0xDEAD:
                self._log.error("No VM found: {}".format(vm_name))
                return
            vm_state = self._get_vm_state(vm_name, vm_id)
            if self.VM_POWER_ON_STR not in vm_state or self.VM_POWER_SUSPENDED_STR in vm_state:
                self._log.info("{} is powered off. Can not suspend the VM\n".format(vm_name))
            elif self.VM_POWER_ON_STR in vm_state:
                self._common_content_lib.execute_sut_cmd_no_exception(
                    self.SUSPEND_RESUME_VM_CMD_ESXI.format(vm_id), "Suspend VM: {}".format(vm_name), 60,
                    ignore_result="ignore")
                self._log.info("Successfully Suspended and Resumed VM {}".format(vm_name))
        except RuntimeError:
            self._log.error("Unable to Suspend the VM : {}".format(vm_name))
            raise

    def suspend_vm(self, vm_name):
        """
        This method is to suspend the existing VM

        :param vm_name: Name of the VM
        """
        try:
            vm_id = self.get_esxi_vm_id_data(vm_name)
            if vm_id == 0xDEAD:
                self._log.error("No VM found: {}".format(vm_name))
                return
            vm_state = self._get_vm_state(vm_name, vm_id)
            if self.VM_POWER_ON_STR not in vm_state or self.VM_POWER_SUSPENDED_STR in vm_state:
                self._log.info("{} is powered off. Can not suspend the VM\n".format(vm_name))
            elif self.VM_POWER_ON_STR in vm_state:
                self._common_content_lib.execute_sut_cmd_no_exception(
                    self.SUSPEND_VM_CMD_ESXI.format(vm_id), "Suspend VM: {}".format(vm_name), 60,
                    ignore_result="ignore")
                self._log.info("Successfully Suspended VM {}".format(vm_name))
        except RuntimeError:
            self._log.error("Unable to Suspend the VM : {}".format(vm_name))
            raise

    def resume_vm(self, vm_name):
        """
        This method is to resume the suspended VM

        :param vm_name: Name of the VM
        """
        try:
            vm_id = self.get_esxi_vm_id_data(vm_name)
            if vm_id == 0xDEAD:
                self._log.error("No VM found: {}".format(vm_name))
                return
            vm_state = self._get_vm_state(vm_name, vm_id)
            if self.VM_POWER_ON_STR not in vm_state or self.VM_POWER_SUSPENDED_STR in vm_state:
                self._log.info("{} is powered off. resuming on the VM\n".format(vm_name))
                self._common_content_lib.execute_sut_cmd_no_exception(
                    self.TURNON_VM_CMD_ESXI.format(vm_id), "resuming VM: {}".format(vm_name), 60,
                    ignore_result="ignore")
                self._log.info("Successfully resumed VM {}".format(vm_name))

            elif self.VM_POWER_ON_STR in vm_state:
                self._log.info("Already in Power ON State, VM {}".format(vm_name))

        except RuntimeError:
            self._log.error("Unable to Resume the VM : {}".format(vm_name))
            raise

    def save_vm_configuration(self, vm_name):
        """
        This method will save the VM configuration into a XML file

        :param vm_name: Name of the VM
        :return: complete_vm_config_file
        """
        raise NotImplementedError

    def restore_vm_configuration(self, vm_name, vm_config_file):
        """
        This method will restore the VM from configuration file

        :param vm_name: Name of the VM
        :param vm_config_file: Previously saved VM configuration file with path
        """
        raise NotImplementedError

    def attach_usb_device_to_vm(self, usb_data_dict, vm_name):
        """
        This method is to attach the usb device to the vm

        :param usb_data_dict: dictionary data should contain vendor id and product id
        :param vm_name: name of the VM
        :return :None
        """
        raise NotImplementedError

    def detach_usb_device_from_vm(self, vm_name):
        """
        This method is to detach the usb device from VM.

        :param vm_name: name of the VM
        :return: None
        """
        raise NotImplementedError

    def install_vm_tool(self):
        """
        This method is to install all the dependency tools for VM creation

        :return: None
        """

        raise NotImplementedError

    def install_vmware_tool_on_vm(self, vm_name):
        """
        This method is to install all the dependency tools on VM.

        :return: None
        """
        try:
            if "rhel" or "centos" in vm_name.lower():
                self._log.info("Checking VMware Tools status on {}, if not need to be installed ".format(vm_name))
                vm_id = self.get_esxi_vm_id_data(vm_name)
                tools_status = self._get_tools_status(vm_name, vm_id)
                if self.VMWARE_TOOLS_STATUS not in tools_status:
                    self._log.info("{} vmware tools to be installed".format(vm_name))
                    self._common_content_lib.execute_sut_cmd(self.VMWARE_TOOL_INSTAL_ON_VM.format(vm_id),
                                                             "Start tools installing in VM: {}".format(vm_name),
                                                             self._command_timeout)
                    self._log.info("Successfully installed VMware tools in VM {}".format(vm_name))
                elif self.VMWARE_TOOLS_STATUS in tools_status:
                    self._log.info("VMware tools in VM {} is already installed".format(vm_name))
            elif "windows" in vm_name.lower():
                self._log.info("Checking VMware Tools status on {}, if not need to be installed ".format(vm_name))
                vm_id = self.get_esxi_vm_id_data(vm_name)
                tools_status = self._get_tools_status(vm_name, vm_id)
                if self.VMWARE_TOOLS_STATUS not in tools_status:
                    self._log.info("{} vmware tools to be installed".format(vm_name))
                    self._common_content_lib.execute_sut_cmd(self.VMWARE_TOOL_INSTAL_ON_VM.format(vm_id),
                                                             "Start tools installing in VM: {}".format(vm_name),
                                                             self._command_timeout)
                    self._log.info("Successfully installed VMware tools in VM {}".format(vm_name))
                elif self.VMWARE_TOOLS_STATUS in tools_status:
                    self._log.info("VMware tools in VM {} is already installed".format(vm_name))
            else:
                self._log.error("Not supported for {} VM".format(vm_name))
        except RuntimeError:
            self._log.error("Unable to start the VM : {}".format(vm_name))
            raise

    def _get_tools_status(self, vm_name, vm_id):
        """
        Method to get tools status of the given VM

        :param vm_name: the name of the given VM
        :param vm_id: VM id for the created VM
        :raise: RunTimeError
        :return: the state of tools. toolsOk/None
        """
        try:
            tool_info = self._common_content_lib.execute_sut_cmd(self.GET_VMWARE_TOOL_STATUS_IN_VM.format(vm_id),
                                                                 "Get tools status of VM : {}".format(vm_name), 60)
            self._log.info("Get tools status info:\n{}".format(tool_info))
            str_list = tool_info.split('"')
            tools_status = str_list[1]
            self._log.info(str_list)
            if tools_status is None:
                return RuntimeError("Fail to get tools status info of the VM.")
            else:
                self._log.info("Tools status of VM{}:{}\n".format(vm_name, tools_status))
                return tools_status
        except RuntimeError:
            raise

    def install_kvm_vm_tool(self):
        """
        This method is to install all the dependency tools for VM creation

        :return: None
        """
        raise NotImplementedError

    def _is_hyper_v_installed(self):
        """
        This method is to verify Hyper-V module is installed or not

        :return : True if Hyper-V module is installed else False
        """
        raise NotImplementedError

    def set_automatic_stop_action(self, vm_name, stop_action_type="TurnOff"):
        """
        This method is to set the Automatic stop Action.

        :param vm_name
        :param stop_action_type - TurnOff (pulling plug- Removing cable), Save, and ShutDown ( Software-OS shut down)
        """
        raise NotImplementedError

    def get_bdf_values_of_nw_device(self, pcie_device):
        """
        This method is to get the BDF values of PCIe device

        :param pcie_device: details of the PCIe device. ex: 0000:6b:02.0 Ethernet controller: Intel Corporation Ethernet
                           Virtual Function 700 Series (rev 02)
        :return: domain-bus-slot-function value
        """
        dbsf_value = re.findall(self._REGEX_TO_FETCH_PCIE_DBSF_VALUES, pcie_device.split("\n")[0])
        domain_value = int(dbsf_value[0].split(":")[0], 16)
        bus_value = int(dbsf_value[0].split(":")[1], 16)
        slot_value = int(dbsf_value[0].split(":")[2].split(".")[0], 16)
        function_value = int(dbsf_value[0].split(":")[2].split(".")[1], 16)
        return domain_value, bus_value, slot_value, function_value

    def enable_pci_passthrough_in_sut(self, pci_device_id):
        """
        This method is to set the Gen4 Nic card passthrough in vm.

        :return: None
        """
        self._log.info("Enabling the PCIe card bdf value in the SUT")
        # enable Gen4 nic card in sut
        enable_passthrough_info = self._common_content_lib.execute_sut_cmd_no_exception(
                                                            self.ENABLE_PCI_PASSTHROUGH_DEVICE.format(pci_device_id),
                                                            "Set passthrough device in sut as True", 60,
                                                            ignore_result="ignore")
        self._log.info("Enable pci passthrouh in sut status info:\n{}".format(enable_passthrough_info))

    def get_uuid_of_sut(self, vm_name):
        """
        This method is to get the uuid of sut.

        :return: uuid of s
        """
        self._log.info("Getting the UUID of the SUT for {} to passthrough".format(vm_name))
        # get uuid of sut
        get_uuid_info = self._common_content_lib.execute_sut_cmd(self.GET_UUID_SUT_INFO,
                                                                 "getting the uuid of the sut", 60)
        self._log.info("Get uuid of sut info:\n{}".format(get_uuid_info))
        uuid_list = get_uuid_info.split(" ")
        uuid = uuid_list[0].strip()
        return uuid

    def get_passthrough_device_details(self, device_id):
        """
        This method is to get the PCIe device details

        :param nw_device_id: id of the network device
        :return: True on Success else False
        """
        # get the  adapter details
        device_details = self._common_content_lib.execute_sut_cmd("lspci -vv | grep -E '{}'".format(device_id),
                                                              "getting passthrough info", self._command_timeout)
        self._log.info("Network adapter details details:\n{}".format(device_details))
        return device_details.split("\n")

    def get_hardware_pci_list_in_sut(self,vm_name, uuid, nw_adapter_pci_value):
        """
        This method is to set the Gen4 Nic card passthrough in vm.

        :return: None
        """
        self._log.info("Getting the vendor ID and device ID of the SUT to passthrough in vm:\n{}".format(vm_name))
        self._log.info("The uuid {} of the SUT for the vm {}".format(uuid, vm_name))
        self._log.info("Getting the vendor ID and device ID of the SUT")
        # getting the vendor ID and device ID of the SUT
        get_pcivalues_info = self._common_content_lib.execute_sut_cmd(self.GET_PCI_VALUES_INFO.format(nw_adapter_pci_value),
                                                                      "getting the vendor ID and device ID of the sut", 60)
        self._log.info("Get pci details of sut info:\n{}".format(get_pcivalues_info))
        pci_value_output = re.findall(r"Vendor\sID\:\s\d.+\n\s*Device\sID\:\s\d.+", get_pcivalues_info)
        pci_value = (re.sub('\n', ':', pci_value_output[0])).split(':')
        vendor_id = pci_value[1].strip()
        device_id = pci_value[3].strip()
        domain_value, bus_value, slot_value, function_value = self.get_bdf_values_of_nw_device(nw_adapter_pci_value)
        if len(str(domain_value)) < 4:
            domain_value = '0' * (4 - len(str(domain_value))) + str(domain_value)
        if len(str(slot_value)) < 2:
            slot_value = '0' * (2 - len(str(slot_value))) + str(slot_value)

        bdf_dec_value = str(domain_value) + ":" + str(bus_value) + ":" + str(slot_value) + "." + str(function_value)
        return vendor_id, device_id, bdf_dec_value

    def get_passthrough_pci_device_in_vm(self,index, vm_name, bdf_dec_value, vendor, device, uuid):
        """
        This method is to set the Gen4 Nic card passthrough in vm.

        :return: None
        """
        self._log.info("Getting the passthrough of pci device in vm {} ".format(vm_name))
        # get pci passthrough in vm
        vm_id = self.get_esxi_vm_id_data(vm_name)
        cmd_to_create_passthrough_vmx_file = [self.PASSTHROUGH_ID_CMD.format(index, bdf_dec_value),
                                              self.PASSTHROUGH_DEVICEID_CMD.format(index, device),
                                              self.PASSTHROUGH_VENDORID_CMD.format(index, vendor),
                                              self.PASSTHROUGH_SYSTEMID_CMD.format(index, uuid),
                                              self.PASSTHROUGH_PRESENT_CMD.format(index)]

        self.turn_off_vm(vm_name)
        # self.unregister_vm(vm_name)
        for command in cmd_to_create_passthrough_vmx_file:
            self._log.info(self.ECHO_CMD_TO_FILE.format(command, self.VMX_DIR_FOR_VM.format(vm_name, vm_name)))
            self._common_content_lib.execute_sut_cmd(
                self.ECHO_CMD_TO_FILE.format(command, self.VMX_DIR_FOR_VM.format(vm_name, vm_name)), command,
                self._command_timeout, cmd_path=self.SUT_FILE_LOCATION)
        self._log.info("pci passthrough from sut to VM {}.vmx file".format(vm_name))
        reload_vm_result = self._common_content_lib.execute_sut_cmd(self.RELOAD_VM_CMD.format(vm_id),
                                                                    self.RELOAD_VM_CMD.format(vm_id),
                                                                    self._command_timeout)
        self._log.info(reload_vm_result)
        # self.register_vm(vm_name)
        self.start_vm(vm_name)

    def verify_pci_passthrough_in_vm(self,vm_name, device_name, common_content_lib=None):
        """
        This method is to set the verify Gen4 Nic card passthrough in vm.

        :param: vm_name: name of the VM
        :param: device_name: Passthrough device name
        :common_content_lib: VM common content lib object
        :return: None
        """
        try :
            lspci_cmd_pci_passthrough = "lspci -D | grep '{}'".format(device_name)
            if common_content_lib is None:
                common_content_lib = self._common_content_lib
            self._log.info("Verify the pci passthrough in vm {} or not".format(vm_name))
            cmd_output = common_content_lib.execute_sut_cmd(lspci_cmd_pci_passthrough, "To verify pci passthrough has done "
                                                                                       "in vm or not", 60)
            self._log.debug("lspci command output results in vm {}".format(cmd_output))
            REGEX_FOR_NIC_NAME = r"\s*Ethernet.+"
            output_list = re.findall(REGEX_FOR_NIC_NAME, cmd_output)
            device_data = output_list[0].split(":")
            pci_passthrough_status = device_data[1]
            if pci_passthrough_status in device_name:
                self._log.info("pci passthrough status of VM{}:{}".format(vm_name, pci_passthrough_status))
                return pci_passthrough_status
            else:
                return RuntimeError("Fail to get pci passthrough status info of the VM {}".format(vm_name))
        except RuntimeError:
            raise

    def dhcp_ip_assgin(self, vm_name, common_content_lib=None):
        """
        This method is to assign dhcp ip to Gen4 Nic card for sriov in vm.

        :param: vm_name: name of the VM
        :common_content_lib: VM common content lib object
        :return: None
        """
        try:
            lspci_cmd_pci_device = "lspci |grep -i 'Virtual Function'"
            if common_content_lib is None:
                common_content_lib = self._common_content_lib
            cmd_output = common_content_lib.execute_sut_cmd(lspci_cmd_pci_device, "To verify vf in pci ", 60)
            nics = str(cmd_output)[:-1].split('\n')
            target_nic = nics[0].strip().split(' ')
            bdf = target_nic[0].strip()
            cmd1 = "f'dhclient -r && dhclient'"
            common_content_lib.execute_sut_cmd(cmd1, "print dhclinet", 60)
            cmd2 = "ls /sys/bus/pci/devices/0000:{}/net"
            ether_name = common_content_lib.execute_sut_cmd(cmd2.format(bdf), "list bdf values", 60)
            cmd3 = "ifconfig {}"
            cmd_output_for_ether = common_content_lib.execute_sut_cmd(cmd3.format(ether_name), "list ether name", 60)
            REGEX_FOR_inet = r"\s*inet.+"
            output_list = re.findall(REGEX_FOR_inet, cmd_output_for_ether)
            if output_list is not None:
                return True
        except RuntimeError:
            raise

    def reconfig_vmx_file(self, vm_name, string_to_find, string_to_change):
        """
        This method is to reconfigure VM VMX file (turn off the VM).

        :param vm_name: name of the VM
        :string_to_find: String to find in vmx file.
        :string_to_change: String to change in vmx file.
        """
        try:
            self._log.info("Reconfig vmx file in VM:{}".format(vm_name))
            self.turn_off_vm(vm_name)
            vm_id = self.get_esxi_vm_id_data(vm_name)
            cmd_to_reconfig_vmx = self._common_content_lib.execute_sut_cmd(
                self.SED_CMD_TO_EDIT_VMX_FILE.format(
                    string_to_find, string_to_change, self.SUT_FILE_LOCATION, vm_name, vm_name), self.SED_CMD_TO_EDIT_VMX_FILE.format(
                    string_to_find, string_to_change, self.SUT_FILE_LOCATION, vm_name, vm_name), 60)
            self._log.debug("vmx reconfig output results in vm {}".format(cmd_to_reconfig_vmx))
            reload_vm_result = self._common_content_lib.execute_sut_cmd(self.RELOAD_VM_CMD.format(vm_id),
                                                                        self.RELOAD_VM_CMD.format(vm_id),
                                                                        self._command_timeout)
            self._log.info(reload_vm_result)
            time.sleep(30)
            self.start_vm(vm_name)
        except RuntimeError:
            raise

    def relaod_vm(self, vm_name):
        """
        This method is to Turn OFF VM (turn off is non graceful shutdown (similar to removing power plug).

        :param vm_name
        """
        self._log.info("Reload VM:{}".format(vm_name))
        vm_id = self.get_esxi_vm_id_data(vm_name)
        reload_vm_result = self._common_content_lib.execute_sut_cmd(self.RELOAD_VM_CMD.format(vm_id),
                                                                    self.RELOAD_VM_CMD.format(vm_id),
                                                                    self._command_timeout)
        self._log.info(reload_vm_result)
        time.sleep(30)

    def turn_off_vm(self, vm_name):
        """
        This method is to Turn OFF VM (turn off is non graceful shutdown (similar to removing power plug).

        :param vm_name
        """
        self._log.info("TurnOff VM- {}".format(vm_name))
        vm_id = self.get_esxi_vm_id_data(vm_name)
        vm_state = self._get_vm_state(vm_name, vm_id)
        if self.VM_POWER_ON_STR in vm_state or self.VM_POWER_SUSPENDED_STR in vm_state:
            turn_off_vm_result = self._common_content_lib.execute_sut_cmd(self.SHUTDOWN_VM_CMD_ESXI.format(vm_id),
                                                                              self.SHUTDOWN_VM_CMD_ESXI.format(vm_id),
                                                                              self._command_timeout)

            # turn_off_vm_result = self._common_content_lib.execute_sut_cmd(self.TURNOFF_VM_CMD.format(vm_id),
            #                                                               self.TURNOFF_VM_CMD.format(vm_id),
            #                                                               self._command_timeout)
            self._log.info(turn_off_vm_result)
            time.sleep(20)
        self._log.info("Successfully TurnOff the VM {}".format(vm_name))

    def import_vm(self, source_path=None, destination_path=None):
        """Method to import VM.
        :param source_path: path on the SUT to the VM template image.
        :type: str
        :param destination_path: path on the SUT to where the new VM image will be.
        :type: str
        """
        raise NotImplementedError

    def rename_vm(self, current_vm_name=None, new_vm_name=None):
        """Method to rename VM.
        :param current_vm_name: Current VM name.
        :type: str
        :param new_vm_name: New VM name.
        :type: str"""
        raise NotImplementedError

    def apply_checkpoint(self, vm_name=None, checkpoint_name=None):
        """Method to apply a stored checkpoint for a named VM.
        :param vm_name: Name of the VM to which the checkpoint will be applied.
        :type: str
        :param checkpoint_name: name of the checkpoint to apply to the VM.
        :type: str"""
        raise NotImplementedError

    def delete_checkpoint(self, vm_name=None, checkpoint_name=None):
        """Method to delete a stored checkpoint for a named VM.
        :param vm_name: Name of the VM to which the checkpoint will be deleted.
        :type: str
        :param checkpoint_name: name of the checkpoint to apply to the VM.
        :type: str"""
        raise NotImplementedError

    def get_network_bridge_list(self):
        """Retrieves list of VM switches registered into Hyper-V.
        :return: List of VM switches
        :rtype: str"""
        raise NotImplementedError

    def set_boot_order(self, vm_name=None, boot_device_type=None):
        """Set boot order of a VM.
        :param vm_name: Name of the VM to change the boot order.
        :type: str
        :param boot_device_type: Type of device to use as boot device.  Expected values are: VMBootSource,
        VMNetworkAdapter,HardDiskDrive,DVDDrive.
        :type: str"""
        device_cmd = ""
        raise NotImplementedError

    def assign_static_ip_to_vm(self, vm_name, user_name, password, static_ip=None, gateway_ip=None, subnet_mask=None):
        """
        This method is used to assign static ip to the VM
        :param vm_name: name of given VM
        :param user_name: user account for the VM
        :param password: password for the VM account
        :param static_ip: ip address of VM
        :param gateway_ip: gateway ip address
        :param subnet_mask: subnet mask

        :return None
        :raise RunTimeError
        """
        raise NotImplementedError

    def copy_package_to_VM(self, vm_name, vm_account, vm_password, package_name, destination_path):
        """
        This method is to copy file from SUT to VM
        :param vm_name : name of the VM. ex: WINDOWS_1
        :param vm_account : VM admin account "Administrator"
        :param vm_password : VM password
        :param destination_path: Destination path in VM
        :param package_name : Name of the package to be copied to VM
        :return : pakage path on VM

        :raise: RuntimeError
        """
        raise NotImplementedError

    def start_iperf_on_vm(self, vm_name, vm_account, vm_password, iperf_cmd, iperf_path):
        """
        This method is used to start iperf on vm

        :param vm_name: name of given VM
        :param vm_account: user account for the VM
        :param vm_password: password for the VM account
        :param iperf_cmd: iperf command to execute on VM
        :param iperf_path: path where command to run

        :return None
        :raise RuntimeError
        """
        raise NotImplementedError

    def check_application_status(self, vm_name, vm_account, vm_password, app_name):
        """
        This method is used to check the status of an application on VM

        :param vm_name: name of given VM
        :param vm_account: user account for the VM
        :param vm_password: password for the VM account
        :param app_name: application to be checked

        :return: Boolean
        """
        raise NotImplementedError

    def remove_network_adapter(self, switchname):
        """
        This method is used to remove the network adapter from SUT

        :param switchname : network adapter interface to be removed
        :return None
        """
        raise NotImplementedError

    def enumerate_usb_from_esxi(self):
        device_name = self._common_content_configuration.get_usb_device_name()
        get_vm_result = self._common_content_lib.execute_sut_cmd(
            self.GET_USB_INFO_CMD.format(device_name), "Get USB info", 60)
        self._log.info("All available vm data  is:\n{}".format(get_vm_result))
        regex_usb_info = r"Bus\s\d+\sDevice\s\d+\:\sID\s\w+\:\w+\s{}.+".format(device_name)
        result = re.findall(regex_usb_info, get_vm_result)
        device_info = result[0].split()
        return device_info

    def enable_disable_usb_passthrough(self, device_info, enable=False):
        if enable:
            self._common_content_lib.execute_sut_cmd(
                self.ENABLE_USB_PASSTHROUGH_CMD.format(device_info),
                "Enabling USB passthrough", 60)
            self._log.info("Successfully enabled the USB Pass through in ESXI")
        else:
            self._common_content_lib.execute_sut_cmd(
                self.DISABLE_USB_PASSTHROUGH_CMD.format(device_info),
                "Disabling USB passthrough", 60)
            self._log.info("Successfully disabled the USB Pass through in ESXI")

    def storage_device_vm_passthrough(self, vm_id, device_data):
        self._common_content_lib.execute_sut_cmd(
            self.USB_PASS_THROUGH_CMD.format(vm_id, device_data),
            "USB Pass through to VM from ESXI", 60)
        self._log.info("Successfully executed the USB Pass through in ESXI")

    def verify_usb_passthrough_in_vm(self, vm_name, common_content_lib=None):
        """
        This method is to set the verify USB passthrough in vm.

        :param: vm_name: name of the VM
        :param: device_name: Passthrough device name
        :common_content_lib: VM common content lib object
        :return: None
        """
        try:
            if common_content_lib is None:
                common_content_lib = self._common_content_lib
            device_name = self._common_content_configuration.get_usb_device_name()
            self._log.info("Verify the pci passthrough in vm {} or not".format(vm_name))
            time.sleep(60)
            cmd_output = common_content_lib.execute_sut_cmd(
                "lsusb | grep -i {}".format(device_name),
                "Verification of USB pass through in VM", 60)
            self._log.info("lsusb command output results in vm {}".format(cmd_output))
            regex_usb_name = r".+{}".format(device_name)
            output_list = re.findall(regex_usb_name, cmd_output)
            device_data = output_list[0].split()
            if device_name in device_data:
                self._log.info("usb passthrough status of VM{}:{}".format(vm_name, True))
                return True
            else:
                return RuntimeError("Fail to get usb passthrough status info of the VM {}".format(vm_name))
        except RuntimeError:
            raise

    def __vmp_execute_host_cmd(self, cmd, timeout=30, cwd=None, powershell=False):
        """
        default windows shell is cmd.
        returncode: execute successfully:0(zero), execute failed: not zero
        """
        if powershell:
            cmd = 'C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe "& {' + cmd + ' }"'
        child = subprocess.Popen(cmd,
                                 shell=True,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=cwd)

        outlines, errlines = child.communicate(timeout=timeout)
        self._log.info('return stdout: {}'.format(outlines.decode()))
        self._log.debug('return stderr: {}'.format(errlines.decode()))
        return outlines, errlines
        # os.system(cmd)

    def vmp_execute_host_cmd(self, cmd, timeout=30, cwd=None, powershell=False):
        # type: (str, int, str, bool) -> (int, str, str)
        """
        Execute command synchronously on local host OS shell

        Args:
            cmd: shell command line
            timeout: optional, command return timeout
            cwd: optional, current working directory on remote os
            powershell: optional, for windows power shell command
        Raises:
            exceptions if error happened
        Returns:
            (return_code, stdout, stderr) if executed
        """
        timeout = int(timeout * 5)
        self._log.debug('execute_host_cmd [{}]'.format(cmd))
        out, err = self.__vmp_execute_host_cmd(cmd, timeout, cwd, powershell)
        return out.decode(), err.decode()

    def vmp_execute_host_cmd_esxi(self, cmd, cwd=".", timeout=30):
        """
         Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false -WarningAction 0 2>$null|out-null;
         Connect-VIServer -Server 10.89.91.247 -Protocol https -User root -Password intel@123 -Force -WarningAction 0 2>$null|out-null;
        """
        CMD_SUPRESS_CERT_WARN = f'Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false ' \
                                f'-WarningAction 0 2>$null|out-null'
        VMP_CMD_CONNECT_TO_ESXI = f'$Conn = Connect-VIServer -Server {self.sut_ip} ' + \
                                  f'-Protocol https -User {self.sut_user} ' + \
                                  f'-Password {self.sut_pass} ' + \
                                  f'-Force -WarningAction 0 2>$null|out-null'
        self._log.debug(f"<{self.sut_ip}> execute host command {cmd} in PowerCLI")
        host_cmd = f"{CMD_SUPRESS_CERT_WARN}; {VMP_CMD_CONNECT_TO_ESXI}; {cmd}"
        self.vmp_execute_host_cmd(cmd=host_cmd, cwd=cwd, timeout=timeout, powershell=True)
