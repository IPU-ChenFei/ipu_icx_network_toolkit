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
import argparse
import logging
import os
import time
import re
import six
import ipccli

from abc import ABCMeta
from threading import Event
from xml.etree import ElementTree
from typing import List, Optional, Union
from datetime import timedelta
from enum import Enum

from dtaf_core.lib.os_lib import Windows
from dtaf_core.lib.private.cl_utils.adapter import data_types
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.lib.exceptions import OsStateTransitionException, OsCommandTimeoutException

from src.lib import content_exceptions
from src.lib.reaction_lib import ReactionLib
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.bios_util import ItpXmlCli, SerialBiosUtil
from src.lib.install_collateral import InstallCollateral
from src.lib.bit_utils import GetBits
from src.provider.vm_provider import VMProvider
from src.provider.sgx_provider import SGXProvider
from src.lib.dtaf_content_constants import SgxHydraToolConstants
from src.lib.os_lib import WindowsCommonLib


class VmOS(Enum):
    WINDOWS = 1
    LINUX = 2

@six.add_metaclass(ABCMeta)
class WindowsBase(ContentBaseTestCase):
    class VMPowerStates(object):
        VM_STATE_RUNNING = "Running"
        VM_STATE_OFF = "Off"

    # Namings
    VM_GUEST_NAME = "VM{}-{}"  # VM name == VM + key - OS#, ex. TD1 - windows, TD3 - centos
    LEGACY_GUEST_NAME = "LEGACY{}-{}"  # VM name == LEGACY + key #, ex. VM1 - windows, VM3 - centos
    VM_OS_DEFAULT = "WINDOWS"
    WINDOWS_VM_SWITCH = "VM_EXTERNAL_SWITCH"
    MEMORY_ENCRYPTION_ENABLED = "MemoryEncryptionEnabled"
    EMPTY_A_DIRECTORY = r"powershell.exe Get-ChildItem '{}\*' -Recurse ^| Remove-Item"
    WINDOWS_MTC_HV_LOCAL_PATH = r"C:\\tmp\\hv"
    WINDOWS_MTC_HV_TO_VM_MOVE_FILE_SCRIPT = r"c:\tmp\hv\move_files_into_td.ps1"
    WINDOWS_OS_REBOOT_TIME = 90

    # Windows VM powershell commands
    WINDOWS_VM_SUSPEND_CMD = "powershell.exe Suspend-VM -Name {}"
    WINDOWS_VM_RESUME_CMD = "powershell.exe Resume-VM -Name {}"
    WINDOWS_VM_SAVE_CMD = "powershell.exe Save-VM -Name {}"
    HYPERV_START_SERVICE_CMD = r'powershell.exe start-service -name vmms'
    HYPERV_STOP_SERVICE_CMD = r'powershell.exe stop-service -name vmms'
    ENABLE_MEMORY_ENCRYPTION_VM = r'powershell.exe Set-VMMemory -VMName {0} -MemoryEncryptionPolicy EnabledIfSupported'
    VM_PROPERTY_VALUE = r"powershell.exe Get-VM -Name {0} ^| Select {1} ^| fl *"
    VM_MEMORY_VALUE = r"powershell.exe Get-VMMemory -VMName {0} ^| Select {1} ^| fl *"
    VM_HOST_VALUE = r"powershell.exe Get-VMHost ^| fl *"

    VM_SECURE_BOOT = r"powershell.exe Set-VMFirmware '{0}' -EnableSecureBoot {1}"
    VM_START_PROCESS_CMD_LINE = r"{{$arg= '/C {0}';Start-Process 'cmd.exe' -WorkingDirectory '{1}' -ArgumentList $arg -Verb RunAs; return 'Success'}}"
    FILE_SEARCH_COMMAND = r"powershell.exe Get-ChildItem -Path '{0}' -Include {1}  -Recurse ^| Select FullName ^| fl"
    GET_VM_NAME_FROM_LOC = "powershell.exe Get-VM ^| Where-Object {{$_.Path -eq '{0}'}} ^| Select Name"

    # Windows Powershell commands
    CREATE_FOLDER = r'New-Item -ItemType "directory" -Path "{0}" -Force'
    STOP_PROCESS = r'Stop-Process -Name "{}" -Force'
    GET_PROCESS = r'Get-Process -Name "{}" '
    START_PROCESS = r'Start-Process -FilePath "{0}" -WorkingDirectory "{1}" -ArgumentList "{2}" -Verb RunAs'
    GET_FILE_CONTENT = r'Get-Content -Path "{0}"'
    COPY_VM_HOST_PS_SESSION = "powershell.exe {}; " \
                              "$account = '{}';$password = '{}';$secpwd = convertTo-secureString " \
                              "$password -asplaintext -force ;$cred = new-object " \
                              "System.Management.Automation.PSCredential -argumentlist $account," \
                              "$secpwd ; $session = New-PSSession  -VMName '{}' -Credential $cred;" \
                              "Copy-Item -{} $Session -Recurse -Path '{}' -Destination '{}' "
    SET_VM_COM_PORT = r'powershell.exe Set-VMComPort {0} {1} \\.\pipe\{2}'

    # common
    PSCP_PATH = r"C:\Program Files\PuTTY\pscp.exe"
    PIPE_SERVER_CMD = r'C:\tmp\linux-tools\PipeServer.exe {0} {1}'
    PUTTY_TOOL_PATH = r'C:\tmp\linux-tools'
    PUTTY_LOG_LOC = r"C:\tmp\putty_log"
    COMPRESSED_TDVM_FILES = "tdvm-logs.zip"

    def __init__(self, test_log: logging.Logger, arguments: argparse.Namespace, cfg_opts: ElementTree) -> None:
        """Create an instance of WindowsBase

        :param test_log: Logger object
        :param arguments: arguments as Namespace
        :param cfg_opts: Configuration object.
        :return: None
        """

        super(WindowsBase, self).__init__(test_log, arguments, cfg_opts)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, self._log)  # type SiliconDebugProvider
        self._vm_provider = VMProvider.factory(test_log, cfg_opts, self.os)
        self.sgx_provider = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)
        self._cfg_opts = cfg_opts
        self._install_collateral = InstallCollateral(test_log, self.os, cfg_opts)
        self.itp_xml_cli_util = ItpXmlCli(self._log, cfg_opts)
        self.serial_bios_util = SerialBiosUtil(self.ac_power, test_log, self._common_content_lib, cfg_opts)
        self.itp = ipccli.baseaccess()
        self.bit_util = GetBits()
        self.sut_os = self.os.os_type
        self._os_booted_event = Event()
        self.sut_reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self.command_timeout = self._common_content_configuration.get_command_timeout()
        self.vm_names_list = dict()  # dict of VM names and values.
        self.sut_login_name, self.sut_login_pwd = self._common_content_lib.get_sut_crediantials(cfg_opts)
        self.windows_lib_obj = WindowsCommonLib(self._log, self.os)

        # overriding parameters, these parameters has to be filled by the derived objects. It can be mktme or tdx etc.
        self.vm_user_name = ""
        self.vm_user_pwd = ""
        self.vm_tools_base_loc = ""
        self.vm_guest_image_path_to_import = ""
        self.legacy_vm_image_path_to_import = ""
        self.vm_reboot_timeout = 0
        self.vm_os = ""
        self.vm_import_image_base_loc = ""
        self.ac_reset = False
        self.is_advanced_options_enabled_in_sut = False
        self.sut_log_path = r"C:\Automation\Logs"

    def prepare(self):
        self._log.info("prepare")
        if self.os.os_type != OperatingSystems.WINDOWS:
            raise content_exceptions.TestNAError("This test case only applicable for Windows system")
        # get the value of 'advanced option' for mtc builds.
        self.refresh_advanced_options_enabled_windows_sut()
        self.sgx_provider.load_sgx_properites()

        # create a log folder at sut
        sut_dest_log_folder_cmd = self.CREATE_FOLDER.format(self.sut_log_path)
        if self.test_path_sut(self.sut_log_path):
            self.delete_folder_at_sut(self.sut_log_path)
        self._common_content_lib.execute_sut_cmd("powershell {}".format(sut_dest_log_folder_cmd),
                                                 sut_dest_log_folder_cmd, self._command_timeout)
        # copy psexec to SUT's system32 folder.
        self.download_from_artifactory_and_copy_to_sut("PsExec.exe", "C:\\Windows\\System32")

    def run_powershell_command_in_vm(self, vm_name: str, powershell_script: str) -> str:
        """run a powershell command in VM and returns the stdout

        :param vm_name: VM name to be execute the command
        :param powershell_script: it can be script block or powershell command etc.
        :return: stdout of the powershell command """

        self._log.info(f"Running '{powershell_script}' in {vm_name}")
        command_format = f"{{{powershell_script}}}"
        run_command = self._vm_provider.ESTABLISH_PS_SESSION.format(self.vm_user_name,
                                                                    self.vm_user_pwd,
                                                                    vm_name,
                                                                    command_format)
        command = "powershell {}".format(run_command)
        run_command_output = self._common_content_lib.execute_sut_cmd(command, command, self._command_timeout)
        return run_command_output

    def create_vm_name(self, key: int = 0, legacy: bool = False, vm_os: str = None) -> (int, str):
        """ It creates a name for new VM by using legacy mode, key and OS names.

        :param key: To indicate an index of the VMs with similar names.
        :param legacy: to indicate legacy or special VMs like MKTME/TDX enabled VMs.
        :param vm_os: to indicate WINDOWS/Linux etc.
        :return:  new name with the index name"""

        if vm_os is None:
            vm_os = self.VM_OS_DEFAULT

        index_values = self.vm_names_list.values()
        existing_vm_names = self.vm_names_list.keys()

        while True:
            if legacy is False:
                vm_name = self.VM_GUEST_NAME.format(key, vm_os.upper())
            else:
                vm_name = self.LEGACY_GUEST_NAME.format(key, vm_os.upper())

            if vm_name in existing_vm_names or key in index_values:
                key = key + 1
            else:
                self._log.info("New VM name created: {}".format(vm_name))
                return key, vm_name

    def vm_is_alive(self, vm_name: str, vm_ip: str = None) -> bool:
        """Attempt to ping to VM to detect if VM is alive.

        :param vm_name: VM name to check the heartbeat
        :param vm_ip: vm_ip address.
        :return: True if VM is alive, False if VM is not alive"""

        # function is clipped from vm_provider implementation
        if vm_ip is None:
            vm_ip = self._vm_provider.get_vm_ip(vm_name)
        ping_result = self._vm_provider.ping_vm_from_sut(vm_ip, vm_name, self.vm_user_name, self.vm_user_pwd)
        if "Received = 4" not in ping_result:
            return False
        return True

    def get_vm_ipaddress(self, vm_name: str) -> str:
        """Get VM's ipaddress.
        :param vm_name: VM name to get ip address
        :return: ipaddress"""

        # function is clipped from vm_provider implementation
        vm_ip = self._vm_provider.get_vm_ip(vm_name)
        return vm_ip

    def import_vm(self, key: int, vm_name: str, source_path: str, dest_path: str) -> None:
        """ Importing VM from an pre exported location

        :param key: a index used to be added in the vm names.
        :param vm_name: a name for the newly imported VM
        :param source_path: exported path of VM for importing
        :param dest_path: destination path for newly imported VM's files"""

        self._log.debug("Importing VM from backup location")

        # get the vmcx file from a parent folder.
        filenames = self.get_filenames_by_using_filter(source_path, "*.vmcx")

        # assuming the first file is the correct vmcx file.
        if len(filenames) == 0:
            raise RuntimeError("Failed to findout the import vmcx file")

        source_image = os.path.join(source_path, filenames[0])

        self._log.info("Importing VM from the backup location {}".format(source_image))
        self.delete_folder_at_sut(dest_path)  # make sure the destination path is clean
        self._vm_provider.import_vm(source_image, dest_path)
        template_vm_name = self.get_vm_name_from_location(dest_path)
        self._vm_provider.rename_vm(template_vm_name, vm_name)
        self.vm_names_list[vm_name] = key  # add a new entry to VM dict

    def start_vm(self, vm_name: str) -> None:
        """Start or power on VM instance.

        :param vm_name: VM name to be started"""

        if vm_name is None or vm_name == "":
            raise ValueError("Vm name is empty to start VM - {}".format(vm_name))

        self._vm_provider.start_vm(vm_name)

    def _check_vm_image(self, key: int = None, vm_os: str =None):
        """Check if VM image already exists in prescribed path on SUT.

        :param key: VM identifier in vm name list.
        :param vm_os: string of OS or distribution."""

        raise NotImplementedError("Not yet implemented for Windows VMs.")

    def teardown_vm(self, vm_name: str, force=False, timeout=60) -> None:
        """Teardown VM.

        :param vm_name: VM name to be shutdown
        :param force: True for power off, False for normal shutdown
        :param timeout: timeout for shutdown"""

        if force is True:
            self._vm_provider.turn_off_vm(vm_name)
        else:
            self._vm_provider._shutdown_vm(vm_name, timeout)

    def pause_vm(self, vm_name: str, timeout: int = 60) -> None:
        """Pause VM, halting all processes.

        :param vm_name: vm name to be pause
        :param timeout: timeout of the suspension"""

        pause_vm_result = self._common_content_lib.execute_sut_cmd(self.WINDOWS_VM_SUSPEND_CMD.format(vm_name),
                                                                   "Suspend VM: {}".format(vm_name), timeout)
        if "" == pause_vm_result:
            self._log.info("Successfully pause/suspend VM {}".format(vm_name))

    def resume_vm(self, vm_name: str, timeout: int = 60) -> None:
        """Resume paused VM, resuming all processes.  Only works on paused VMs.

        :param vm_name: VM name to be resume
        :param timeout: timeout to resume the vm"""

        resume_vm_result = self._common_content_lib.execute_sut_cmd(self.WINDOWS_VM_RESUME_CMD.format(vm_name),
                                                                    "Resume VM: {}".format(vm_name), timeout)
        if "" == resume_vm_result:
            self._log.info("Successfully resumed VM {}".format(vm_name))

    def save_vm(self, vm_name=None, timeout: int = 60):
        """Save VM

        :param vm_name: VM name to be saved
        :param timeout: timeout to save the vm"""

        save_vm_result = self._common_content_lib.execute_sut_cmd(self.WINDOWS_VM_SAVE_CMD.format(vm_name),
                                                                  "Save VM: {}".format(vm_name), timeout)
        if "" == save_vm_result:
            self._log.info("Successfully saved VM {}".format(vm_name))

    def restore_vm(self, vm_name: str = None, config_file: str = None):
        """Restore VM

        :param vm_name: VM name to be restore
        :param config_file: timeout to restore the vm """

        raise NotImplementedError("Not yet supported for TD guests.")

    def reboot_sut(self, is_graceful_g3: bool = False) -> None:
        """Tries to reboot SUT from OS, then reverts to AC cycle if OS reset fails.
        :param is_graceful_g3: to power off and on"""

        self._log.info("Rebooting the SUT")

        # overriding base class method because we do not want to wait for the OS to boot up
        if not self.ac_reset and not is_graceful_g3:
            self.os.execute_async(Windows.Commands.RESTART)
        else:
            try:
                if self.os.is_alive():
                    self._log.info("OS is alive, shutting down the SUT..")
                    self.os.shutdown(self._sut_shutdown_delay)  # To apply the new bios setting.
            except OsStateTransitionException as ex:
                self._log.error("Paramiko throws error sometime if OS is not alive. Ignoring this "
                                "exception '{}'...".format(ex))
            self.ac_power.ac_power_off()
            time.sleep(60.0)
            self.ac_power.ac_power_on()

        if self.is_advanced_options_enabled_in_sut is True:
            self._log.info("Registering reaction")

            self._os_booted_event.clear()
            with ReactionLib(self._log, self.cng_log, console_log_skip_to_end=True, daemon=False) as reaction_engine:
                reaction_engine.register_reaction(r".*PDB = bootmgfw.pdb", self._windows_boot_trigger)
                self._os_booted_event.wait(timeout=self.reboot_timeout)
                reaction_engine.remove_reaction(r".*PDB = bootmgfw.pdb")
                if not self._os_booted_event.is_set():
                    self._log.error("Timed out waiting for Advanced Boot Options prompt.")
                    return

        self.os.wait_for_os(self.reboot_timeout)

    # noinspection PyUnusedLocal
    def _windows_boot_trigger(self, match):
        """Event trigger when Windows boots to Advanced Boot Options."""

        self._log.debug("Reached Windows Advanced Boot Options menu!")
        self._log.debug("Sleeping for 20 seconds before selecting boot option.")
        time.sleep(20.0)
        # sending key presses to select "Disable Driver Signature Enforcement" from Advanced Boot Options
        self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_UP)
        self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_UP)
        self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_UP)
        self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_ENTER)
        self._os_booted_event.set()

    def refresh_advanced_options_enabled_windows_sut(self) -> None:
        """Checking  whether 'advanced options' enabled bcdedit. If 'advanced option' enabled in
        bcdedit, the user has to select a boot option. This entry is import for MTC windows test
        builds."""

        command = "bcdedit.exe"
        advanced_options = "advancedoptions"
        expected_values = "Yes"
        try:
            command_result = self._common_content_lib.execute_sut_cmd(command,command,self.command_timeout)
            str_list = command_result.split('\n')
            for line in str_list:
                if advanced_options in line:
                    if expected_values in line:
                        self.is_advanced_options_enabled_in_sut = True
                        break
        except RuntimeError as e:
            self._log.info("Os is not responding.")

    def enable_vm_integration(self, vm_name: str) -> None:
        """ Enable VM integration service that allow the virtual machine to communicate with the Hyper-V host

        :param vm_name: virtual machine name"""

        enable_vm_service = self._vm_provider.ENABLE_VM_INTEGRATION_SERVICE_CMD.format(self._vm_provider.SILENT_CONTINUE,
                                                                                       vm_name,
                                                                                       self._vm_provider.GUEST_SERVICE_STR)
        enable_vm_service_output = self._common_content_lib.execute_sut_cmd(enable_vm_service,
                                                                            "Enable Integration Service",
                                                                            self.command_timeout)
        self._log.debug("Enable VM Integration service output : {}".format(enable_vm_service_output))

    def extract_pkg_at_vm(self, vm_name: str,
                          vm_account: str,
                          vm_password: str,
                          package_name: str,
                          vm_destination_path: str,
                          pkg_format: str = "zip", ) -> str:
        """Extract a package in the VM machine, now it supports zip format only

        :param vm_name: virtual machine name
        :param vm_account: vm account name
        :param vm_password: vm's login password
        :param package_name: package name to be extract at vm
        :param vm_destination_path: package path in vm
        :param pkg_format: package format.
        :return: location of the extracted package."""

        try:
            # extract the package
            package_path = os.path.join(vm_destination_path, package_name.replace(".zip", ""))
            if pkg_format.lower() == "zip":
                script_block = "{" + self._vm_provider.EXTRACT_FILE_STR.format(
                    os.path.join(vm_destination_path, package_name),
                    package_path) + "}"
                extract_file = self._vm_provider.ESTABLISH_PS_SESSION.format(vm_account,
                                                                             vm_password,
                                                                             vm_name,
                                                                             script_block)
                command_result = self._common_content_lib.execute_sut_cmd(
                    "powershell {}".format(extract_file), "Extracting File", self.command_timeout)
                self._log.debug(command_result)
                self._log.info("Successfully copied {} & Extracted in VM under {}".format(package_name, package_path))
            return package_path
        except Exception as ex:
            raise RuntimeError("Failed to Extract {} to VM! {}".format(package_name, ex))

    def shutdown_all_vms(self):
        """Shutdown or turn off all vms"""

        for vm_name in self.vm_names_list.keys():
            vm_info_data = self._vm_provider.get_vm_info(vm_name)
            if str(vm_info_data["state"]) != str(self.VMPowerStates.VM_STATE_OFF):
                self.teardown_vm(vm_name, force=True)
                time.sleep(10)  # buffer time to settle down.

    def test_path_sut(self, file_folder: str) -> bool:
        """Check the path exist in the SUT

        :param file_folder: it can be full file name or full folder name
        :return: True/False """

        test_path = r"powershell.exe Test-Path -Path '{0}'".format(file_folder)
        ret_val = self._common_content_lib.execute_sut_cmd(test_path, test_path,
                                                           self.command_timeout)
        if "True" in ret_val:
            return True
        else:
            return False

    def start_hyperv_service(self, timeout: int = 30) -> None:
        """Start the Hyper-V service

        :param timeout: timeout to start the service """

        start_hyperv_service_output = self._common_content_lib.execute_sut_cmd(self.HYPERV_START_SERVICE_CMD,
                                                                               self.HYPERV_START_SERVICE_CMD,
                                                                               self.command_timeout)
        self._log.debug("Hyper-V Stop service Output: {}".format(start_hyperv_service_output))
        time.sleep(timeout)

    def stop_hyperv_service(self, timeout: int = 30) -> None:
        """Stop the Hyper-V service

        :param timeout: timeout to stop the service"""

        stop_hyperv_service_output = self._common_content_lib.execute_sut_cmd(self.HYPERV_STOP_SERVICE_CMD,
                                                                              "stop-service -name vmms",
                                                                              self.command_timeout)
        self._log.debug("Hyper-V Stop service Output: {}".format(stop_hyperv_service_output))
        time.sleep(timeout)

    def clean_vm(self, vm_name: str) -> None:
        """shutdown and remove a VM

        :param vm_name: VM name to be shutdown and remove from Hyper-V"""

        self._log.debug("Removing VM {} from HyperV.".format(vm_name))
        try:
            self._log.debug("Removing checkpoint for VM {}.".format(vm_name))
            self._vm_provider.delete_checkpoint(vm_name)
            self._log.debug("Turning off VM {}.".format(vm_name))
            if not self.verify_vm_state(vm_name, self.VMPowerStates.VM_STATE_OFF):
                self._vm_provider.turn_off_vm(vm_name)
            time.sleep(10)
            self._log.debug("Destroying VM {}.".format(vm_name))
            self._vm_provider.destroy_vm(vm_name)
        except Exception as e:
            self._log.exception(e)

        vm_dir_loc = str(self.vm_import_image_base_loc + vm_name)
        # stop the hyper-v service - helps to avoid the access violation.
        self.stop_hyperv_service()
        # delete the VM folders.
        self.delete_folder_at_sut(vm_dir_loc)
        # start the hyper-v service
        self.start_hyperv_service()

    def clean_all_vms(self) -> None:
        """clean all vms"""

        # teardown running VMs
        for vm_name in self.vm_names_list.keys():
            self.clean_vm(vm_name)
        # empty the vm names list
        self.vm_names_list.clear()

        # clear the virtual Machine cache
        self.clear_virtual_machine_cache(is_hyper_disabled=False)

    def cleanup(self, return_status) -> None:

        try:
            self.clean_all_vms()
            super(ContentBaseTestCase, self).cleanup(return_status)
            self._log.debug("Exiting ContentBaseTestCase cleanup")
        except Exception as ex:
            self._log.error("Exception in cleanup")

        # make sure SUT is in working condition.
        if not self.os.is_alive():
            if self.is_advanced_options_enabled_in_sut is True:
                self.hard_reset_if_os_is_dead()
            else:
                self.reboot_sut()

    def clean_all_vms_from_hyper_v(self) -> None:
        """Clean all vms """

        self._log.info("Get all VM lists in the hyper v manager")
        self.get_vm_list()
        # unload all vms.
        self.clean_all_vms()
        # There could be some potential chance that VMs may not be unload completely.
        self.get_vm_list()

    def get_vm_list(self) -> None:
        """Collect all Windows VMs and add to the global list"""

        current_vm_names = self._vm_provider.get_vm_list()
        key = 0
        for vm_name in current_vm_names:
            self.vm_names_list[vm_name] = key
            key = key + 1

    # methods specific to be run inside a  VM
    def vm_stop_running_process(self, vm_name: str, process_name: str) -> bool:
        """ Stop a process running in VM

        :param vm_name: virtual machine name
        :param process_name: process name to be stop in VM
        :return: True if process is stopped otherwise return False """

        stop_process_cmd = self.STOP_PROCESS.format(process_name)
        try:
            ret_val = self.run_powershell_command_in_vm(vm_name, stop_process_cmd)
            if "" in ret_val:
                return True
            else:
                return False
        except RuntimeError as err:
            self._log.debug(str(err))
            return False

    def vm_start_process(self, vm_name: str, process_name: str, file_loc: str, arg: str) -> bool:
        """Starts a process in VM

        :param vm_name: virtual machine name
        :param process_name: process name to be start in VM
        :param file_loc: file location in VM
        :param arg: arguments to the executable
        :return: True/False"""

        start_process_cmd = self.START_PROCESS.format(process_name, file_loc, arg)
        try:
            ret_val = self.run_powershell_command_in_vm(vm_name, start_process_cmd)
            if "" in ret_val:
                return True
            else:
                return False
        except RuntimeError as err:
            self._log.debug(str(err))
            return False

    def get_filenames_by_using_filter(self, base_path: str, filter: str) -> List[str]:
        """Get file names by using filter, it lists all file names matching with the filter and
        it searches all sub folders too.

        :param base_path: valid folder
        :param filter: filter can be full name or with wild characters.
        :return: Empty list or all filenames which are matching with filter.
        """

        filename = []
        file_search_command = self.FILE_SEARCH_COMMAND.format(base_path, filter)
        try:
            file_search_output = self._common_content_lib.execute_sut_cmd(file_search_command,
                                                                          file_search_command,
                                                                          self.command_timeout)
            str_list = file_search_output.split('\n')
            for line in str_list:
                line = line.strip()
                if "FullName" in line:
                    words = line.split(':', 1)
                    if len(words) == 2:
                        filename.append(words[1].strip())
        except Exception as e:
            self._log.exception(e)
        return filename

    def test_vm_folder_accessible(self, vm_name: str, folder_loc: str = None) -> bool:
        """Using to test whether a VM is accessible

        :param vm_name: Virtual machine name
        :param folder_loc: folder location
        :return: True if the folder is accessible otherwise False."""

        self._log.info("Verify  VM state. {}".format(vm_name))
        vm_info_data = self._vm_provider.get_vm_info(vm_name)
        if str(vm_info_data["state"]) != str(self.VMPowerStates.VM_STATE_RUNNING):
            self._log.info("VM is not in running state")
            return False

        if folder_loc is None:
            test_path = r'Test-Path -Path "c:\\Windows"'
        else:
            test_path = r'Test-Path -Path "{0}"'.format(folder_loc)

        try:
            ret_val = self.run_powershell_command_in_vm(vm_name, test_path)
            if "True" in ret_val:
                return True
            else:
                return False
        except RuntimeError as err:
            self._log.debug(str(err))
            return False

    def delete_folder_at_sut(self, dest_folder: str) -> bool:
        """Deleting a folder and it's subdirectories

        :param dest_folder: destination folder
        :return: True if there is no exception otherwise False
        """

        if self.test_path_sut(dest_folder) is False:
            return True  # path doesn't exist. So no need to continue it.
        remove_folder = "powershell.exe  Remove-Item '{0}' -Recurse -Force"
        try:
            command = remove_folder.format(dest_folder)
            get_vm_name_result = self._common_content_lib.execute_sut_cmd(command, command, self.command_timeout)
            self._log.debug("Output of Remove-Item command:\n{}".format(get_vm_name_result))
        except RuntimeError:
            self._log.debug("Exception in Remove-Item command")
            return False
        return True

    def get_vm_name_from_location(self, physical_path: str) -> str:
        """Using to find the VM name running from a specific physical path

        :param physical_path: relative or absolute physical path of vhdx
        :return: VM name """

        vm_list = []
        try:
            command = self.GET_VM_NAME_FROM_LOC.format(physical_path)
            get_vm_name_result = self._common_content_lib.execute_sut_cmd(command, "Get VM Name", self.command_timeout)
            self._log.info("All available vm data  is:\n{}".format(get_vm_name_result))
            str_list = get_vm_name_result.split('\n')
            index = 0
            for str in str_list:
                if str != '' and '---' not in str:
                    res = re.finditer(r"\S+", str)
                    for match in res:
                        if index == 0:
                            index = index + 1
                            break
                        vm_list.append(match.group())
                        break
        except RuntimeError:
            raise
        return "" if len(vm_list) == 0 else vm_list[0]

    def verify_vm_state(self, vm_name: str, state: str) -> bool:
        """Verifying the current state of the VM vs compare value

        :param vm_name:  VM name
        :param state: expected state of the VMs attached to hyperV manager
        :return: True if VM state is matching with the criteria
        """
        vm_info_data = self._vm_provider.get_vm_info(vm_name)
        return True if vm_info_data["state"] == state else False

    def attach_ethernet_adapter_to_vm(self, vm_name: str) -> None:
        """Attach virtual switch to the VM and configure the ethernet adapter in the VM

        :param vm_name: virtual machine name"""

        self._log.info("Setting up switch.")
        switch = self._vm_provider.get_network_bridge_list()
        if switch == "":
            self._log.debug("No switch found matching name {}.  Attempting to create a new switch.".format(
                self.WINDOWS_VM_SWITCH))
            self._vm_provider.create_bridge_network(self.WINDOWS_VM_SWITCH)
            switch = self.WINDOWS_VM_SWITCH
        self._vm_provider.add_vm_ethernet_adapter(vm_name, switch)

    def get_vm_property_value(self, vm_name: str, property_name: str, vm_memory_property: bool = False) -> Optional[str]:
        """ Return the property value of the VM

        :param vm_name: virtual machine name
        :param property_name: property name to get the values.
        :param vm_memory_property: Is the property name belong to VMMemory.
        :return: value of the property or None
        """
        if vm_memory_property:
            self._log.info("Getting the Memory value of VM {0} --> {1}".format(vm_name, property_name))
            get_vm_property_value_cmd = self.VM_MEMORY_VALUE.format(vm_name, property_name)
        else:
            self._log.info("Getting the property value of VM {0} --> {1}".format(vm_name, property_name))
            get_vm_property_value_cmd = self.VM_PROPERTY_VALUE.format(vm_name, property_name)

        try:
            command_output = self._common_content_lib.execute_sut_cmd(get_vm_property_value_cmd,
                                                                      get_vm_property_value_cmd,
                                                                      self.command_timeout)
            self._log.debug(command_output)
            str_list = command_output.split('\n')
            for line in str_list:
                line = line.strip()
                if property_name in line:
                    words = line.split(':', 1)
                    if len(words) == 2:
                        return words[1].strip()
                    break
        except Exception as e:
            self._log.exception(e)
        return None

    def enable_memory_encryption_vm(self, vm_name: str, timeout: int = 60) -> None:
        """Enable Memory encryption for VM.

        :param vm_name: vm name to apply memory encryption
        :param timeout: timeout for the command """

        memory_encryption_vm_result = self._common_content_lib.execute_sut_cmd(self.ENABLE_MEMORY_ENCRYPTION_VM.format(vm_name),
                                                                               "Enable MemoryEncryption on VM: {}".format(vm_name),
                                                                               timeout)
        if "" == memory_encryption_vm_result:
            self._log.info("Successfully Enabled Memory Encryption on VM {}".format(vm_name))

    def apply_memory_encryption_on_vm(self, vm_name: str, timeout: int = 60) -> bool:
        """ Apply the memory encryption on VM. It shutdown the VM, apply encryption then start the vm

        :param vm_name: vm name
        :param timeout: timeout to execute the commands
        :return: True if memory encryption is enabled else return False"""

        self._log.info(f"Shutdown the {vm_name}")
        self.teardown_vm(vm_name, force=False, timeout=timeout)
        self._log.info(f"Waiting {timeout} seconds to shutdown the {vm_name}")
        time.sleep(timeout)
        # apply memory encryption on VM
        self.enable_memory_encryption_vm(vm_name, timeout=timeout)
        self._log.info(f"Starting the VM - {vm_name}")
        self.start_vm(vm_name)
        self._log.info(f"Waiting {timeout} seconds to boot the {vm_name}")
        time.sleep(timeout)
        ret_val = self.get_vm_property_value(vm_name, self.MEMORY_ENCRYPTION_ENABLED, vm_memory_property=True)
        if ret_val is None or ret_val == "" or str(ret_val).upper() == "FALSE":
            return False
        elif str(ret_val).upper() == "TRUE":
            return True
        return False

    def extract_compressed_file_sut(self, sut_src_folder: str, zip_file: str, sut_dest_folder: str) -> None:
        """Extract the zip file in sut. If the destination folder exist, at first it delete the folder
        then create a destination folder and extract the zip file.

        :param sut_src_folder: zip file folder location
        :param zip_file: zip file name
        :param sut_dest_folder: where to extract.
        :return: None
        :RunTimeError: If it failed to create director or extract the zip file"""

        # if the destination path exist, just remove it.
        if self.test_path_sut(sut_dest_folder):
            self.delete_folder_at_sut(sut_dest_folder)
        # creating new destination folder(s)
        command_result = self.os.execute(f"mkdir {sut_dest_folder}",
                                         timeout=self._command_timeout,
                                         cwd=self._common_content_lib.C_DRIVE_PATH)
        if command_result.cmd_failed():
            log_error = f"failed to run the command 'mkdir' with return value = '{command_result.return_code}' and " \
                        f"std error = '{command_result.stderr}' .."
            self._log.error(log_error)
            raise RuntimeError(log_error)

        # creating the folder and extract the zip file
        command_result = self.os.execute(f"tar xf {zip_file} -C {sut_dest_folder}",
                                         timeout=self._command_timeout, cwd=sut_src_folder)
        if command_result.cmd_failed():
            log_error = f"failed to run the command 'tar' with return value = '{command_result.return_code}' and " \
                        f"std error = '{command_result.stderr}' .."
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("Successfully extracted on SUT!")

    @staticmethod
    def set_ipc_unlock_credentials(self, username: str, password: str) -> None:
        """Warning ..  It is not recommended to use this method to set the credentials for unlocking the device.
         Instead of using this method pushUtil-Cache credential (goto/unlocker) will save the credentials to unlock
         the device

        :param username: pythonsv checkout username
        :param password: pythonsv checkout password
        """
        import py2ipc
        authorize_service = py2ipc.IPC_GetService("Authorization")
        authorize_service.SetCredentials(username, password)

    def hard_reset_if_os_is_dead(self) -> None:
        """If OS is dead or non responsive like Blue screen, this method will try to hard reset the platform.
        This method assume that the Windows Advanced Options enabled and boot screen will waiting for'Disable
        Driver Signature Enforcement' option
        """

        self._log.info("Hard reboot the SUT")

        self.ac_power.ac_power_off()
        time.sleep(30.0)
        self.ac_power.ac_power_on()

        self._log.info("Registering reaction")
        self._os_booted_event.clear()
        with ReactionLib(self._log, self.cng_log, console_log_skip_to_end=True, daemon=False) as reaction_engine:
            reaction_engine.register_reaction(r".*PDB = bootmgfw.pdb", self._windows_boot_trigger)
            self._os_booted_event.wait(timeout=self.reboot_timeout)
            reaction_engine.remove_reaction(r".*PDB = bootmgfw.pdb")
            if not self._os_booted_event.is_set():
                self._log.error("Timed out waiting for Advanced Boot Options prompt.")
                return
        self.os.wait_for_os(self.reboot_timeout)

    def get_property_value_of_sut(self, powershell_cmd: str, property_name: str,
                                  cmd_path: str = None) -> List[str]:
        """ It returns the location of the virtual machine
        :param powershell_cmd: powershell command
        :param property_name: property value to be search
        :param cmd_path: command path
        :return: property values list or empty list."""

        command_output = self._common_content_lib.execute_sut_cmd(powershell_cmd, powershell_cmd,
                                                                  self.command_timeout, cmd_path)
        self._log.debug(command_output)
        str_list = command_output.split('\n')
        ret_val = list()
        for line in str_list:
            line = line.strip()
            if property_name in line:
                words = line.split(':', 1)
                if len(words) == 2:
                    ret_val.append(words[1].strip())
        return ret_val

    def clear_virtual_machine_cache(self, is_hyper_disabled: bool = False) -> None:
        """This method will clear the virtual machine cache folder. Occasionally this folder items won't delete during
        VM removal.
        :param is_hyper_disabled: is hyper-v service already disabled or not
        :return: None.
        """
        property_name = "VirtualMachinePath"
        get_virtual_machine_loc_list = self.get_property_value_of_sut(self.VM_HOST_VALUE, property_name)
        if len(get_virtual_machine_loc_list) == 0:
            return  # Nothing to do.
        get_virtual_machine_loc = get_virtual_machine_loc_list[0]
        get_virtual_machine_cache_loc = os.path.join(get_virtual_machine_loc, "Virtual Machines Cache")
        if not is_hyper_disabled:
            self.stop_hyperv_service()

        if self.test_path_sut(get_virtual_machine_loc):
            command = self.EMPTY_A_DIRECTORY.format(get_virtual_machine_cache_loc)
            command_output = self._common_content_lib.execute_sut_cmd(command, command, self.command_timeout)
            self._log.debug(command_output)

        if not is_hyper_disabled:
            self.start_hyperv_service()

    def read_bios_menu(self):
        """Read BIOS menu over serial connection."""
        return self.serial_bios_util.get_page_information()

    def stop_process_running_in_vm(self, vm_name: str, process_name: str) -> bool:
        """ Stop a process running in VM

        :param vm_name: virtual machine name
        :param process_name: process name to be stop in VM
        :return: True/False """

        stop_process_cmd = self.STOP_PROCESS.format(process_name)
        try:
            ret_val = self.run_powershell_command_in_vm(vm_name, stop_process_cmd)
            if "" in ret_val:
                return True
            else:
                return False
        except RuntimeError as err:
            self._log.debug(str(err))
            return False

    def start_process_in_vm(self, vm_name: str, process_name: str, file_loc: str, arg: str) -> bool:
        """ starts a process in VM

        :param vm_name: virtual machine name
        :param process_name: process name to be start in VM
        :param file_loc: file location in VM
        :param arg: arguments to the executable
        :return: True/False"""

        start_process_cmd = self.START_PROCESS.format(process_name, file_loc, arg)
        try:
            ret_val = self.run_powershell_command_in_vm(vm_name, start_process_cmd)
            if "" in ret_val:
                return True
            else:
                return False
        except RuntimeError as err:
            self._log.debug(str(err))
            return False

    def start_process_in_vm_cmd_line(self, vm_name: str, process_name: str, file_loc: str, arg: str) -> bool:
        """ starts a process in VM as command line argument

        :param vm_name: virtual machine name
        :param process_name: process name to be start in VM
        :param file_loc: file location in VM
        :param arg: arguments to the executable
        :return: True/False"""

        exe_cmd = os.path.join(file_loc, process_name)
        exe_cmd = exe_cmd + " " + arg
        run_cmd = r"{{$arg= '/C {0}'; Start-Process 'cmd.exe' -WorkingDirectory '{1}' -ArgumentList $arg -Verb RunAs; return 'Success'}}"
        run_cmd = run_cmd.format(exe_cmd, file_loc)
        self._log.info(run_cmd)

        try:
            command = self._vm_provider.ESTABLISH_PS_SESSION.format(self.vm_user_name, self.vm_user_pwd, vm_name, run_cmd)
            command_output = self._common_content_lib.execute_sut_cmd("powershell {}".format(command),
                                                                      command,
                                                                      self._command_timeout)
            self._log.debug(command_output)
        except Exception as e:
            self._log.debug("Exception while running the command")
            return False

        return True

    def check_process_running(self, vm_name: str, process_name: str = None) -> bool:
        """Check if process with provided string is running on VM.

        :param vm_name: VM identifier.
        :param process_name: name of process to be checked.
        :return: True is process running else False."""

        get_process_cmd = self.GET_PROCESS.format(process_name)
        try:
            ret_val = self.run_powershell_command_in_vm(vm_name, get_process_cmd)
            if process_name in ret_val:
                return True
            else:
                return False
        except RuntimeError as err:
            return False

    def check_process_running_sut(self, process_name: str = None) -> bool:
        """Check if process is running on SUT.
        :param process_name: name of process to be check.
        :return: True if process is running else False."""

        get_process_cmd = "powershell.exe " + self.GET_PROCESS.format(process_name)
        try:
            ret_val = self._common_content_lib.execute_sut_cmd(get_process_cmd,
                                                               get_process_cmd,
                                                               self.command_timeout)
            if process_name in ret_val:
                return True
            else:
                return False
        except RuntimeError as err:
            return False

    def _get_vmcx_path_from_vm(self, vm_name: str) -> Union[str, None]:
        """Find the vmcx full path from VM

        :param vm_name: virtual machine name
        :return: VM's absolute path of vmcx file.
        """

        vm_config_path = self.get_vm_property_value(vm_name, "ConfigurationLocation")
        vmid = self.get_vm_property_value(vm_name, "VMId") + ".vmcx"
        vmcx_path = os.path.join(vm_config_path, "Virtual Machines", vmid)
        self._log.info("vmcx path is {0}".format(vmcx_path))
        # Verify the files are copied properly.
        self._log.info("Testing the vmcx path, {0}  is valid".format(vmcx_path))
        test_path = r"powershell.exe Test-Path -Path '{0}'".format(vmcx_path)
        ret_val = self._common_content_lib.execute_sut_cmd(test_path, test_path,
                                                           self.command_timeout)
        if "True" in ret_val:
            return vmcx_path
        else:
            return None

    def set_secure_boot(self, vm_name: str, enable_secureboot: bool = True) -> None:
        """Enable or disable secure boot for Gen2 type vhds

        :param vm_name: virtual machine name
        :param enable_secureboot: True/False secureboot
        :return: None"""

        if enable_secureboot is True:
            secure_enable = "On"
        else:
            secure_enable = "Off"

        secure_boot_cmd = self.VM_SECURE_BOOT.format(vm_name, secure_enable)
        secure_boot_result = self._common_content_lib.execute_sut_cmd(secure_boot_cmd,
                                                                      secure_boot_cmd,
                                                                      self.command_timeout)
        if "" == secure_boot_result:
            self._log.info("Successfully enabled/disabled secure boot in {}".format(vm_name))

    def get_console_log_line_count(self) -> int:
        """ Returns total number of lines in the console log

        :return: the number of lines in the console log
        """

        total_line = 0
        try:
            with open(self.cng_log.log_file, 'r') as fp:
                total_line = len(fp.readlines())
                self._log.info('Total lines: {}'.format(total_line))
        except (OSError, IOError) as e:
            self._log.error("Error in reading file due to exception '{}'".format(e))
            raise e
        return total_line

    def verify_console_log_for_known_error(self, reference_line_number: int, known_errors: List[str]) -> bool:
        """verify any errors reported in the console log

        :param reference_line_number: jump to this line in the console log then start the verification
        :param known_errors: list of the errors need to be check
        :return: True/False
        :raise RuntimeError, OSError, IOError if file not found or exception to open the file"""

        if len(known_errors) == 0:
            return True

        if os.path.exists(self.cng_log.log_file) is False:
            self._log.error("BIOS console log file doesn't exist at {}".format(self.cng_log.log_file))
            raise RuntimeError("Console log file doesn't exist to get BIOS logs")

        is_passed = True
        try:
            with open(self.cng_log.log_file, 'r') as fp:
                line_count = 0
                for line in fp.readlines():
                    line_count = line_count + 1
                    if line_count > reference_line_number:
                        for known_error in known_errors:
                            if known_error in line:
                                self._log.debug("Console log failure {}".format(known_error))
                                is_passed = False
        except (OSError, IOError) as e:
            self._log.error("Error in reading file due to exception '{}'".format(e))
            raise e
        return is_passed

    def wait_for_application_execution(self, vm_name: str,
                                       process_name: str,
                                       app_run_time: int) -> None:
        """Wait till application execution complete, then kill the process in VM
        :param vm_name: virtual machine name
        :param process_name: process name to be check in the VM task manager.
        :param app_run_time: application execution time
        :raise RuntimeError: if application is not running till the wait time
        :raise TestFail: if application is not exiting after the wait time or failed to kill the process"""

        self._log.info(f"Waiting {app_run_time} seconds to complete the application {process_name}")

        execute_time = time.time() + app_run_time
        while time.time() < execute_time:
            ret_val = self.check_process_running(vm_name, process_name)
            if ret_val is True:
                self._log.info(f"{process_name} still running")
            else:
                self._log.info(f"{process_name} is not running")
                return
            self._log.info("Total waiting time {}".format(str(timedelta(seconds=round(execute_time - time.time())))))
            time.sleep(60)  # wait 60 seconds before next check

        # stop the application
        self._log.info(f"Stop the execution of {process_name} in VM")
        self.stop_process_running_in_vm(vm_name, process_name)
        process_exit = False
        for retry in range(0, 10):
            time.sleep(5)  # buffer time to stop the process
            ret_val = self.check_process_running(vm_name, process_name)
            if ret_val is True:
                self._log.info(f"{process_name} still running")
            else:
                self._log.info(f"{process_name} exited")
                process_exit = True
                break
        if process_exit is False:
            raise content_exceptions.TestFail("{0} doesn't exiting from VM, still running".format(process_name))

    def verify_errors_in_app_log_at_vm(self, vm_name: str,
                                       app_name: str,
                                       result_log_path: str,
                                       known_errors: List[str]) -> None:
        """Verify the application's output file in VM and check the known errors.

        :param vm_name: virtual machine name
        :param app_name: application name
        :param result_log_path: the location of the output file in the VM
        :param known_errors: known error to be check in the output file
        :return: None
        :raise TestFail: if file is missing or known error in the file
        :raise RuntimeError: if the output file doesn't exist in VM
        """

        ret_val = self.test_vm_folder_accessible(vm_name, result_log_path)
        if ret_val is True:
            get_file_content = self.GET_FILE_CONTENT.format(result_log_path)
            results_file_content = self.run_powershell_command_in_vm(vm_name, get_file_content)
            for known_error in known_errors:
                if known_error in results_file_content:
                    raise content_exceptions.TestFail("{0} run failed by {1}".format(app_name, known_error))
        else:
            raise RuntimeError("{0} output file doesn't exist at {1}".format(app_name, result_log_path))

    def enable_mktme_settings_in_vm(self, vm_name: str) -> bool:
        """Apply mktme specific configuration setting on  TD VM's vmcx file.

        :param vm_name: virtual machine name
        :return: True if mktme settings applied in vmcx file otherwise False.
        :return: different exceptions
        """

        self._log.info("Update the vmcx with mktme config settings")
        cmd_path = self.WINDOWS_MTC_HV_LOCAL_PATH
        mktme_verify_string = r"mktme/enabled"
        hvsedit_command = 'hvsedit  "{0}" -s bool /configuration/settings/memory/mktme/enabled true'

        vmcx_filepath = self._get_vmcx_path_from_vm(vm_name)
        if len(vmcx_filepath) == 0:
            raise "Failed to find the vmcx file"
        self._log.info("Update the vmcx file with config settings")
        try:
            command = hvsedit_command.format(vmcx_filepath)
            self._log.info(command)
            sut_cmd_result = self._common_content_lib.execute_sut_cmd_no_exception(command, "hvsedit command",
                                                                                   self._command_timeout,
                                                                                   cmd_path, "Yes")
            self._log.debug(sut_cmd_result)
        except Exception as e:
            self._log.debug("Exception while running the vmcx commands TDs")
            self._log.exception(e)
            raise

        # verify the command is applied successfully
        command = 'hvsedit  "{0}"'.format(vmcx_filepath)
        sut_cmd_result = self._common_content_lib.execute_sut_cmd_no_exception(command, "hvsedit command",
                                                                               self._command_timeout, cmd_path,
                                                                               "Yes")
        self._log.debug(sut_cmd_result)

        if mktme_verify_string in sut_cmd_result:
            self._log.info("The value {} found in vmcx file".format(mktme_verify_string))
            return True
        else:
            self._log.info("The value {}  not found in vmcx file".format(mktme_verify_string))
            return False

    def apply_mktme_settings_on_vm(self, vm_name: str) -> None:
        """apply mktme settings to a vm
        :param vm_name: virtual machine name
        :raise content_exceptions.TestFail : if memory encryption failed.
        """
        self._log.info("Applying memory encryption settings on VM {}".format(vm_name))
        ret_val = self.apply_memory_encryption_on_vm(vm_name, self.vm_reboot_timeout)
        if not ret_val:
            raise content_exceptions.TestFail("Memory encryption is not applied to the VM")

    def sgx_install_psw(self) -> None:
        """ Install PSW on Windows """

        str_psw = "SGX_PSW"
        sgx_psw_setup_loc = self.sgx_provider.get_sgx_executable_dir(self.sgx_provider.PSW_INSTALL_BINARY_MATCH)
        self._log.info(f"SGX_PSW execution path is {sgx_psw_setup_loc}")
        sut_cmd_result = self.os.execute(self.sgx_provider.PSW_INSTALL_BINARY_MATCH,
                                         self.sgx_provider.execution_timeout,
                                         sgx_psw_setup_loc)
        if sut_cmd_result.cmd_failed():
            log_error = f"Failed to run '{self.sgx_provider.PSW_INSTALL_BINARY_MATCH}' command with return" \
                        f" value = '{sut_cmd_result.return_code}' and std_error='{sut_cmd_result.stderr}'.."
            self._log.error(log_error)
            raise RuntimeError(log_error)
        else:
            self._log.debug(sut_cmd_result.stdout)
        self.sgx_provider.install_driver(self.sgx_provider.SGX_PATH, self.sgx_provider.SGX_PSW_INF, str_psw)
        self.reboot_sut()

    def sgx_check_psw_installation(self) -> None:
        """Checks SGX PSW installation
        :raise: raise content_exceptions.TestFail if SGX PSW is not installed
        """
        self._log.info("Check SGX PSW installation")
        if self.sgx_provider.is_psw_installed():
            self._log.info("SGX PSW is installed and verified successfully!")
            return
        self._log.info("SGX PSW is not installed, installing it")
        self.sgx_install_psw()
        if not self.sgx_provider.is_psw_installed():
            raise content_exceptions.TestFail("SGX PSW verification failed, "
                                              "looks like SGX PSW not installed")
        self._log.info("SGX PSW is installed and verified successfully")

    def setup_sgx_packages(self):
        """Copy sgx_sdk_build and hydra test from artifactory then setup in SUT"""

        # copy sgx psw zip package to SUT
        decompress_path = os.path.join(self.sgx_provider.SGX_PATH, "sgx_sdk_build")
        self.download_from_artifactory_and_copy_to_sut(self.sgx_provider.PSW_SGX_APP_INSTALLER,
                                                       self.sgx_provider.SGX_PATH,
                                                       decompress=True,
                                                       decompress_path=decompress_path)
        if self.test_path_sut(decompress_path):
            self._log.info(f"SGX PSW application available at {decompress_path}")
        else:
            self._log.info(f"SGX PSW application not available at {decompress_path}")
        # install SGX SDK installation.
        self._install_collateral.install_vc_redist()
        # copy hydra test to SUT
        hydra_test_path = os.path.join(self._common_content_lib.C_DRIVE_PATH, SgxHydraToolConstants.HYDRA_TEST_DIR, "bin")
        if not self.test_path_sut(hydra_test_path):
            hydra_test_path = self._install_collateral.copy_sgx_hydra_windows()
            hydra_test_path = os.path.join(hydra_test_path, "bin")
            self._log.debug("SGX Hydra tool installed at location {}".format(hydra_test_path))
        else:
            self._log.debug("SGX Hydra tool already installed at location {}".format(hydra_test_path))
        self.sgx_check_psw_installation()
        self.reboot_sut()

    def start_all_vms(self):
        """start all VMs"""
        for vm_name in self.vm_names_list:
            self.start_vm(vm_name)
            self._log.info(f"waiting {self.vm_reboot_timeout} seconds")
            time.sleep(self.vm_reboot_timeout)

    def create_ssh_keys_sut(self, sut_username: str) -> bool:
        """Creates ssh keys in the Windows SUT
         :param sut_username: SUT username
         :return: True if keys are present or created a new one else False"""
        ssh_key_private = r"C:\Users\{}\.ssh\id_rsa".format(sut_username)
        ssh_key_public = r"C:\Users\{}\.ssh\id_rsa.pub".format(sut_username)
        # verify the files are already present.
        ret_val1 = self.test_path_sut(ssh_key_private)
        ret_val2 = self.test_path_sut(ssh_key_public)
        if ret_val1 and ret_val2:
            self._log.info("ssh keys already available")
            return True
        # one of the file is missing. Delete the other pair
        if ret_val1:
            self.delete_folder_at_sut(ssh_key_private)
        if ret_val2:
            self.delete_folder_at_sut(ssh_key_public)

        # create a new key
        command = r'ssh-keygen  -t rsa -N "" -f %userprofile%/.ssh/id_rsa'
        ssh_key_gen_output = self._common_content_lib.execute_sut_cmd(command, command, self.command_timeout)
        self._log.info(ssh_key_gen_output)
        return True

    def run_command_as_async_in_sut(self, exec_command: str) -> str:
        """Run a command asynchronously in SUT using psexec. The SUT should have
        sysinternal's psexec at c:\\windows\\system32 folder
        :param exec_command: the command to be execute as async
        :return None:"""
        try:
            run_command = "psexec.exe -accepteula -d -i -h " + exec_command
            self.os.execute(run_command, self.command_timeout)
        except RuntimeError as err:
            self._log.debug("Error codes returned by PsExec are specific to the applications you execute, not PsExec."
                            "So please check the process is running")
            return ""

    def run_command_in_linux_vm_using_ssh(self, vm_ip_address: str,
                                          command: str,
                                          command_timeout: int = 0,
                                          async_cmd: bool = False) -> str:
        """Run a command in Linux VM by using ssh in SUT
        :param vm_ip_address: ipaddress of the VM
        :param command: single or multiple command separated by ;
        :param command_timeout: command timeout
        :param async_cmd: to run the command as asynchronously
        :return: output string"""

        ssh_path = r"ssh -o StrictHostKeyChecking=no "
        exec_command = f'{ssh_path} {self.vm_user_name}@{vm_ip_address} "{command}"'
        self._log.info(exec_command)
        copy_result = ""
        if command_timeout <= 0:
            command_timeout = self.command_timeout
        if not async_cmd:
            copy_result = self._common_content_lib.execute_sut_cmd(exec_command, exec_command, command_timeout)
        else:
            self.run_command_as_async_in_sut(exec_command)

        return copy_result

    def set_vm_com_port(self, vm_name: str, port_number: int, pipe_name: str) -> None:
        """Set VM comport for Linux VMs
        :param vm_name: VM name
        :param port_number: port number
        :param pipe_name: pipe name"""

        command = self.SET_VM_COM_PORT.format(vm_name, port_number, pipe_name)
        self._log.info(f"Set VMCom Port command : {command}")
        set_vm_com_port_result = self._common_content_lib.execute_sut_cmd(command, command, self._command_timeout)
        if "" == set_vm_com_port_result:
            self._log.info("Successfully set Set-VMComport VM {}".format(vm_name))

    def launch_pipe_server_for_linux_vm(self, pipe_name: str, putty_conn_name: str,
                                        kill_previous_instance: bool = True) -> None:
        """Launch pipe server for linux VM
        :param pipe_name: pipe name to be connect to the pipe server
        :param putty_conn_name: a symbolic pipe name which will be use later for connection
        :param kill_previous_instance: terminate previous instance of the same applicaton
        """
        if kill_previous_instance:
            while True:
                if self.check_process_running_sut("PipeServer"):
                    self.windows_lib_obj.kill_process("PipeServer.exe")
                else:
                    break
        command = self.PIPE_SERVER_CMD.format(pipe_name, putty_conn_name)
        self._log.info(f"Launch Pipe Server command: {command}")
        pipe_server_result = self._common_content_lib.execute_sut_cmd_async(command, command, self._command_timeout)
        self._log.info(pipe_server_result)
        if self.check_process_running_sut("PipeServer"):
            self._log.info("Successfully running PipeServer")
        else:
            raise content_exceptions.TestFail("PipeServer is not running in the SUT")

    def launch_putty_for_pipe_server(self, putty_conn_name: str, baud_rate: int = 115200, output_log: str = None) -> None:
        """Launch the putty for pipe server to verify the data.
        :param putty_conn_name: putty conn_name to pipeserver
        :param baud_rate: baud rate of the serial connection
        :param output_log: full path of log file"""

        putty_launch_cmd = f"putty.exe -serial \\\\.\\pipe\\{putty_conn_name} -sercfg {baud_rate},8,n,1,N"
        if output_log != "":
            putty_launch_cmd = putty_launch_cmd + f" -sessionlog {output_log}"
        self._log.info(f"Putty launch command: {putty_launch_cmd}")

        sut_cmd_result = self._common_content_lib.execute_sut_cmd_no_exception(putty_launch_cmd, putty_launch_cmd,
                                                                               30, self.PUTTY_TOOL_PATH, "Yes")
        self._log.debug(sut_cmd_result)

        if self.check_process_running_sut("putty"):
            self._log.info("Successfully running Putty")
        else:
            raise content_exceptions.TestFail("putty is not running in the SUT")

    def replace_line_in_file_linux_vm(self, search_str: str, replace_str: str,
                                      path_in_vm: str, vm_ip_address: str) -> None:
        """replace a string with another one in a file
        :param search_str: string to be identify in file
        :param replace_str: string to replace.
        :param path_in_vm: path in the linux VM
        :param vm_ip_address: VM ipaddress"""
        command = r"echo {0} | sudo -S sed -i '/{1}c\{2}' {3}".format(self.vm_user_pwd, search_str, replace_str, path_in_vm)
        self._log.info(f"Replace line command {command}")
        self.run_command_in_linux_vm_using_ssh(vm_ip_address, command)

    def test_linux_vm_folder_accessible(self, vm_name: str, vm_ip_address: str, folder_loc: str = None) -> bool:
        """Using to test whether a Linux VM is accessible by checking a folder is accessible
        :param vm_name: Virtual machine name
        :param folder_loc: folder location
        :param vm_ip_address: vm's ip address for communication
        :return: True if the folder is accessible otherwise False."""

        self._log.info("Verify  VM state. {}".format(vm_name))
        vm_info_data = self._vm_provider.get_vm_info(vm_name)
        if str(vm_info_data["state"]) != str(self.VMPowerStates.VM_STATE_RUNNING):
            self._log.info("VM is not in running state")
            return False

        if folder_loc is None:
            exec_cmd = r'ls /home'
        else:
            exec_cmd = f"ls {folder_loc}"

        try:
            ret_val = self.run_command_in_linux_vm_using_ssh(vm_ip_address, exec_cmd)
            if "cannot access" in ret_val or "cannot open" in ret_val:
                return False
            else:
                return True
        except RuntimeError as err:
            self._log.debug(str(err))
            return False

    def get_file_content_sut(self, file_path: str) -> str:
        """Get the content of the file
        :param file_path: file location
        :return: the content of the file"""
        command = "powershell.exe " + self.GET_FILE_CONTENT.format(file_path)
        file_read_result = self._common_content_lib.execute_sut_cmd(command, command, self._command_timeout)
        return file_read_result

    def get_vm_ipaddress_for_linux_guest(self, vm_name) -> str:
        """If vm's ipaddress is published to hyper-v, it reads the value and return
        if ipaddress is empty. It is asking the user to enter manually.  It is a temporary
        adjustment till the issue get solved.
        :param vm_name: vm name
        :return: VM's ipaddress."""
        try:
            return self._vm_provider.get_vm_ip(vm_name)
        except RuntimeError as ex:
            self._log.debug("Linux guest is not publishing the ip_address to hyper-v service")

        # This is a temporary workaround till ipaddress issue get fixed.
        vm_ip_address = input(f"Enter {vm_name}'s ipaddress: ")
        self._log.info(vm_ip_address)
        return vm_ip_address

    def clean_linux_vm_tdx_apps(self) -> None:
        """Exiting all Linux TD guest specific applications and connectivity's"""
        # kill all Pipe Server instances
        while True:
            if self.check_process_running_sut("PipeServer"):
                self.windows_lib_obj.kill_process("PipeServer.exe")
            else:
                break
        # kill all putty connections.
        while True:
            if self.check_process_running_sut("putty"):
                self.windows_lib_obj.kill_process("putty.exe")
            else:
                break

    def clean_arp_table_sut(self) -> None:
        """cleaning the arp table in SUT"""
        command = "cmd.exe /C arp -d"
        arp_clean_cmd_output = self._common_content_lib.execute_sut_cmd(command, command, self._command_timeout)
        self._log.info(arp_clean_cmd_output)

    def get_numa_host_numa_node_values_windows(self) -> int:
        """Get the NUMA Node count in the SUT machine
        :return: numa node count"""
        command = r"powershell.exe Get-VMHostNumaNode ^| Select NodeId ^| fl *"
        numa_node_list_output = self._common_content_lib.execute_sut_cmd(command, command, self.command_timeout)
        numa_node_id_count = 0
        numa_node_list_output = numa_node_list_output.strip()
        str_list = numa_node_list_output.split('\n')
        for line in str_list:
            if "NodeId" in line.strip():
                numa_node_id_count = numa_node_id_count + 1

        return numa_node_id_count

    def check_process_running_in_linux_vm(self, vm_ip_address: str, process_name: str) -> bool:
        """Using to check a process running in linux vm
        :param vm_ip_address: vm ipaddress
        :param process_name: process name
        :return: True if the process is running else False
        """
        pgrep_command = f"pgrep {process_name}"
        try:
            ret_val = self.run_command_in_linux_vm_using_ssh(vm_ip_address, pgrep_command)
        except RuntimeError:
            self._log.info(f"{pgrep_command} throws error means the process is not running.")
            return False
        if ret_val != "":
            self._log.debug(f"Process {process_name} is running on VM {vm_ip_address}.  Output: {ret_val}")
            return True
        return False

    def stop_process_running_in_linux_vm(self, vm_ip_address: str, process_name: str, ctrl_c: bool = False) -> None:
        """using to stop/kill the process running in linux vm
        :param vm_ip_address: vm's ipaddress
        :param process_name: process name
        :param ctrl_c: to send CTRL+C to the process
        :return: None
        """
        kill_command = f"kill -9 $(pgrep {process_name})"
        try:
            self.run_command_in_linux_vm_using_ssh(vm_ip_address, kill_command)
        except RuntimeError:
            self._log.error(f"Looks to be {process_name} does't running")

    def wait_for_application_execution_in_linux_vm(self, vm_ip_address: str,
                                                   process_name: str,
                                                   app_run_time: int) -> None:
        """Wait till application execution complete, then kill the process in VM
        :param vm_ip_address: virtual machine ip address
        :param process_name: process name to be check in the VM task manager.
        :param app_run_time: application execution time
        :raise RuntimeError: if application is not running till the wait time
        :raise TestFail: if application is not exiting after the wait time or failed to kill the process"""

        self._log.info(f"Waiting {app_run_time} seconds to complete the application {process_name}")
        execute_time = time.time() + app_run_time
        while time.time() < execute_time:
            ret_val = self.check_process_running_in_linux_vm(vm_ip_address, process_name)
            if ret_val is True:
                self._log.info(f"{process_name} still running")
            else:
                self._log.info(f"{process_name} exited")
                return
            self._log.info(f"Total waiting time {str(timedelta(seconds=round(execute_time - time.time())))}")
            time.sleep(60)  # wait 60 seconds before next check

        # stop the application
        self._log.info(f"Stop the execution of {process_name} in VM")
        self.stop_process_running_in_linux_vm(vm_ip_address, process_name, ctrl_c=True)
        process_exit = False
        for retry in range(0, 10):
            time.sleep(5)  # buffer time to stop the process
            ret_val = self.check_process_running_in_linux_vm(vm_ip_address, process_name)
            if ret_val is True:
                self._log.info(f"{process_name} still running")
            else:
                self._log.info(f"{process_name} exited")
                process_exit = True
                break
        if process_exit is False:
            raise content_exceptions.TestFail(f"{process_name} doesn't exiting from VM, still running")

    def compress_folder_at_sut(self, source_path: str, destination_name: str) -> bool:
        """compress a folder or file at sut
        :param source_path: source file or directory
        :param destination_name: archive name with location path
        :return: True or False
        """
        command = f"powershell.exe Compress-Archive -Path {source_path} -DestinationPath {destination_name}"
        self._log.info(command)
        self._common_content_lib.execute_sut_cmd(command, command, self.command_timeout)

    def get_virtual_switch_ipaddress(self, switch_name: str) -> str:
        """get the ipaddress of the virtual switch in SUT
        :param switch_name: virtual switch name as interface alias
        :return: ipaddress"""
        command = f"powershell.exe Get-NetIPAddress  -AddressFamily IPv4 ^| where InterfaceAlias -like *{switch_name}*"
        self._log.debug(f"Command to list the ipaddress of virtual switch {switch_name}: {command}")
        property_list = self.get_property_value_of_sut(command, "IPAddress")
        return property_list[0]

    def download_from_artifactory_and_copy_to_sut(self, art_pkg_name: str, sut_dest_folder: str,
                                                  decompress: bool = False,
                                                  decompress_path: str = None) -> None:
        """Download and copy a file/package from artifactory to SUT. It can decompress
        the zip file in SUT at target path
        :param art_pkg_name: package name in artifactory
        :param sut_dest_folder: destination location at SUT
        :param decompress: to unzip the file downloaded
        :param decompress_path: a valid path to decompress the file.
        :raise: RuntimeError if unzip fails.
        """
        host_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(art_pkg_name)
        # copy the file to sut
        self.copy_file_from_host_to_sut(host_tool_path, sut_dest_folder)
        if decompress:
            # extract the zip file.
            self.extract_compressed_file_sut(sut_dest_folder, art_pkg_name, decompress_path)

    def copy_files_between_sut_and_linux_vm(self, src_path: str, dest_path: str,
                                            is_src_dir: bool, vm_ip_address: str, to_vm: bool = True) -> None:
        """copy a file or folder between SUT and Linux VM
        :param src_path: source path
        :param dest_path: destination path
        :param is_src_dir: whether the source is folder or file
        :param vm_ip_address: ipaddress of the VM
        :param to_vm: copy the files to vm otherwise copy to SUT.
        """
        command = f'echo y | "{self.PSCP_PATH}" -scp -pw {self.vm_user_pwd} '
        if is_src_dir:
            command = command + " -r "
        if to_vm is True:
            command = command + src_path + f" {self.vm_user_name}@{vm_ip_address}:{dest_path}"
            self._log.info(f"Copying the files from SUT to VM : {command}")
        else:
            command = command + f" {self.vm_user_name}@{vm_ip_address}:{src_path} " + dest_path
            self._log.info(f"Copying the files from VM to SUT : {command}")

        self._common_content_lib.execute_sut_cmd(command, command, self.command_timeout)

    def copy_ssh_key_from_sut_to_linux_vm(self, sut_username: str, vm_ip_address: str) -> None:
        """Copy ssh keys from SUT to Linux VM
        :param sut_username: sut login name
        :param vm_ip_address: VM's ipaddress"""
        src_path = r"C:\users\{}\.ssh\id_rsa.pub".format(sut_username)
        dest_path = r"~/.ssh/authorized_keys"
        self.copy_files_between_sut_and_linux_vm(src_path, dest_path, False, vm_ip_address)

    def copy_file_from_host_to_sut(self, host_src_file_name: str, sut_dest_path: str) -> None:
        """ copying a file from host machine to SUT. It destination file exist, at first it deletes.
        If destination folder doesn't exist, it creates and then copy the file.

        :param host_src_file_name: The absolute path of source zip file.
        :param sut_dest_path: The destination path of SUT
        :return: None
        :RuntimeError: if it failed to create a directory.
        """

        self._log.info("Copying a file to SUT from host")
        # if the destination path exist, just remove it.
        dest_file_name = os.path.join(sut_dest_path, host_src_file_name.split("\\")[-1])
        if self.test_path_sut(dest_file_name):
            self.delete_folder_at_sut(dest_file_name)
        # creating the new destination folder(s)
        if not self.test_path_sut(sut_dest_path):
            command_result = self.os.execute(f"mkdir {sut_dest_path}",
                                             timeout=self._command_timeout,
                                             cwd=self._common_content_lib.C_DRIVE_PATH)
            if command_result.cmd_failed():
                log_error = f"failed to run the command 'mkdir' with return value = '{command_result.return_code}' and " \
                            f"std error = '{command_result.stderr}' .."
                self._log.error(log_error)
                raise RuntimeError(log_error)

        # copying file to windows SUT from host
        self.os.copy_local_file_to_sut(host_src_file_name, sut_dest_path)

    def copy_file_between_sut_and_vm(self, vm_name: str, source_file_path: str = None,
                                     destination_file_path: str = None, to_vm: bool = True) -> None:
        """Copy file between SUT to VM on SUT.
        :param vm_name: vm name.
        :param source_file_path: path of file to copy.
        :param destination_file_path: path of where file should go on VM.
        :param to_vm: True if copying to VM, False if copying from VM.
        :return: None
        """

        if to_vm is True:
            copy_direction = "ToSession"
            self._log.info("Copying {} from SUT to VM".format(source_file_path))
        else:
            copy_direction = "FromSession"
            self._log.info("Copying {} from VM to SUT".format(source_file_path))

        # copy files from sut to vm or vice versa
        copy_cmd = self.COPY_VM_HOST_PS_SESSION.format(self._vm_provider.SILENT_CONTINUE,
                                                       self.vm_user_name,
                                                       self.vm_user_pwd,
                                                       vm_name,
                                                       copy_direction,
                                                       source_file_path,
                                                       destination_file_path)

        copy_cmd_output = self._common_content_lib.execute_sut_cmd(copy_cmd, "Copy File to VM/SUT",
                                                                   self.command_timeout)
        self._log.debug("copy to vm/sut output : {}".format(copy_cmd_output))

    def copy_file_from_host_to_sut_to_vm(self, vm_name: str,
                                         vm_ipaddress: str,
                                         pkg_name: str,
                                         process_name: str,
                                         tools_absolute_path_in_host: str,
                                         dest_folder_in_sut: str,
                                         dest_path_in_vm: str,
                                         vm_os: VmOS = VmOS.WINDOWS) -> str:
        """Copy tool(zip, tar or binary) host to sut, then copy to VM(Windows or Linux) and extract it.
        :param vm_name: VM name
        :param vm_ipaddress: virtual machine ip address
        :param pkg_name: package name in artifactory or host location.
        :param process_name: using to create sub folder at destination to avoid congestion
        :param tools_absolute_path_in_host: absolute path in host
        :param dest_folder_in_sut: destination folder in SUT
        :param dest_path_in_vm: destination folder in VM(Windows or Linux)
        :param vm_os: VmOS (Windows or Linux)
        :return: package path/extracted path at VM machine """

        extension = pkg_name.split(".")[-1].lower()

        self._log.info(f"Copying {pkg_name} to SUT")
        # copy at SUT's default directory C:\<package_file>
        self.copy_file_from_host_to_sut(tools_absolute_path_in_host, dest_folder_in_sut)
        self._log.info(f"Successfully copied the {pkg_name} file to SUT")

        # copy package from sut to vm
        source_pkg_file = os.path.join(dest_folder_in_sut, pkg_name)
        self._log.info(f"Copying {pkg_name} from SUT to VM")

        # copy package from sut to VM (VM can be Linux VM or Windows VM)
        if vm_os == VmOS.LINUX:
            create_folder = f"mkdir -p -v {dest_path_in_vm}"
            self.run_command_in_linux_vm_using_ssh(vm_ipaddress, create_folder)
            self.copy_files_between_sut_and_linux_vm(source_pkg_file, dest_path_in_vm, False,
                                                     vm_ipaddress)
            # extract the file
            unzip_cmd = ""
            extract_command = f"cd {dest_path_in_vm}; mkdir {process_name}; "
            if "zip" in extension:
                unzip_cmd = f" unzip {pkg_name} -d {process_name}"
            if "gz" in extension:
                unzip_cmd = f" tar -xvf {pkg_name} -C {process_name}"
            extract_command = extract_command + " " + unzip_cmd
            self.run_command_in_linux_vm_using_ssh(vm_ipaddress, extract_command)
            package_path_in_vm = dest_path_in_vm + f"/{process_name}"
        else:
            # Create a tools destination folder at vm like C:\Automation\Tools
            dest_folder_in_vm = self.CREATE_FOLDER.format(dest_path_in_vm)
            self.run_powershell_command_in_vm(vm_name, dest_folder_in_vm)
            self.copy_file_between_sut_and_vm(vm_name, source_pkg_file, dest_path_in_vm)
            if "zip" in extension:
                # extract the zip package in vm machine
                package_path_in_vm = self.extract_pkg_at_vm(vm_name, self.vm_user_name, self.vm_user_pwd,
                                                            pkg_name, dest_path_in_vm, "zip")
            else:
                # in case of non zip folder, the default location is the package path.
                package_path_in_vm = dest_path_in_vm
        return package_path_in_vm

    def get_os_disk_number_of_drive_letter_in_sut(self, os_drive_letter: str = "C") -> str:
        """Using to get the disk number by where the windows OS is running
        :param os_drive_letter: driver letter where OS is installed.
        :return the disk number as string"""

        command = f"powershell.exe Get-Partition -DriveLetter {os_drive_letter} ^| fl DiskNumber"
        self._log.debug(command)
        property_list = self.get_property_value_of_sut(command, "DiskNumber")
        return property_list[0]

    def get_all_nvme_disk_numbers_in_sut(self) -> List[str]:
        """Using to get all storage disk numbers those are connected to NVMe bus in SUT
        :return disk numbers as string."""

        command = f'powershell.exe Get-Disk ^| where BusType -eq NVMe ^| fl DiskNumber'
        self._log.debug(f" Get all storage disks connected to NVMe bus {command}")
        property_list = self.get_property_value_of_sut(command, "DiskNumber")
        return property_list

    def get_disk_property_in_sut(self, disk_number: int, property_name: str) -> str:
        """Using to get a property of hard drive
        :param disk_number: disk number
        :param property_name: name of the property to get the value.
        :return property value"""

        command = f"powershell.exe Get-Disk ^| where DiskNumber -eq {disk_number} ^| fl {property_name}"
        self._log.debug(command)
        return self.get_property_value_of_sut(command, property_name)[0]

    def set_disk_property_in_sut(self, disk_number: int, property_name: str, val: str):
        """Using to change the property value of the disk
         :param disk_number: disk number to change the value
         :param property_name: property name
         :param val: new value to be apply to the property"""

        powershell_cmd = f"powershell.exe Set-Disk -Number {disk_number} -{property_name} {val}"
        self._log.debug(powershell_cmd)
        return self._common_content_lib.execute_sut_cmd(powershell_cmd, powershell_cmd,
                                                        self.command_timeout)

    def set_disk_to_rw_mode_sut(self, disk_number: int) -> bool:
        """Changing the disk to RW mode.
        :param disk_number: disk number in SUT
        :return True if changed to RW mode else False"""

        readonly_mode_of_disk = self.get_disk_property_in_sut(disk_number, "IsReadOnly")
        if readonly_mode_of_disk == "True":
            self.set_disk_property_in_sut(disk_number, "IsReadOnly", "$False")
            readonly_mode_of_disk = self.get_disk_property_in_sut(disk_number, "IsReadOnly")
            if readonly_mode_of_disk == "True":
                self._log.error(f"Cann't change the Readonly status of disk {disk_number} to write mode")
                return False
        return True

    def set_disk_to_offline_mode_sut(self, disk_number: int) -> bool:
        """Set disk to offline mode at SUT
        :param disk_number: disk number
        :return: True if Disk changed to offline mode else False"""

        offline_mode_of_disk = self.get_disk_property_in_sut(disk_number, "IsOffline")
        if offline_mode_of_disk == "False":
            self.set_disk_property_in_sut(disk_number, "IsOffline", "$True")
            offline_mode_of_disk = self.get_disk_property_in_sut(disk_number, "IsOffline")
            if offline_mode_of_disk == "False":
                self._log.error(f"Can not change the status of disk, {disk_number} to offline")
                return False
        return True

    def add_hard_disk_to_vm(self, vm_name: str, disk_number: int):
        """Adding a physical hard drive to a HyperV VM.
        :param vm_name: vm name
        :param disk_number: only offline disk can be add to the VM
        :return: the output of the OS execute command, 'Any' value"""

        powershell_cmd = f"powershell.exe Get-Disk {disk_number} ^| Add-VMHardDiskDrive -VMName {vm_name}"
        self._log.debug(f"Add hard disk to VM {powershell_cmd}")
        return self._common_content_lib.execute_sut_cmd(powershell_cmd, powershell_cmd,
                                                        self.command_timeout)

    def get_disk_number_in_win_vm(self, vm_name: str, guid: str) -> Union[int, None]:
        """ Get disk number in Windows VM matching with a GUID
        :param vm_name: vm name
        :param guid:  GUID of the actualy physical drive
        :return: if guid matching with drive, return disk number else None"""

        for disk_number in range(0, 5):
            powershell_cmd = f"Get-Disk -Number {disk_number} ^| fl Guid"
            command_output = self.run_powershell_command_in_vm(vm_name, powershell_cmd)
            self._log.debug(f"Get Guid of disk  {command_output}")
            str_list = command_output.split('\n')
            for line in str_list:
                line = line.strip()
                if guid in line:
                    return disk_number
        return None

    def activate_disk_in_win_vm(self, vm_name: str, vm_disk_no: int) -> None:
        """Using to activate the disk by RW mode and change to online mode
        :param vm_name: vm name
        :param vm_disk_no: disk number which need to be change to online mode"""

        powershell_cmd = f'Set-Disk -Number {vm_disk_no} -IsReadOnly $False'
        command_output = self.run_powershell_command_in_vm(vm_name, powershell_cmd)
        self._log.debug(command_output)
        powershell_cmd = f'Set-Disk -Number {vm_disk_no} -IsOffline $False'
        command_output = self.run_powershell_command_in_vm(vm_name, powershell_cmd)
        self._log.debug(command_output)

    def format_drive_in_win_vm(self, vm_name: str, drive_letter:str) -> None:
        """Format a drive letter in VM
        :param vm_name: vm name
        :param drive_letter: driver letter which need to be format"""

        powershell_cmd = f"Format-Volume -DriveLetter {drive_letter} -NewFileSystemLabel 'New Volume'"
        command_output = self.run_powershell_command_in_vm(vm_name, powershell_cmd)
        self._log.debug(command_output)

    def change_drive_letter_in_win_vm(self, vm_name: str, drive_letter: str, new_drive_letter: str) -> None:
        """Using to change a driver letter to a new available driver letter
        :param vm_name: vm name
        :param drive_letter: existing drive letter
        :param new_drive_letter: new driver letter"""

        powershell_cmd = f"Set-Partition -DriveLetter {drive_letter} -NewDriveLetter {new_drive_letter}"
        command_output = self.run_powershell_command_in_vm(vm_name, powershell_cmd)
        self._log.debug(command_output)

    def get_all_drive_letters_of_disk_win_vm(self, vm_name: str, vm_disk_no: int) -> List[str]:
        """Using to get all driver letters belong to a disk number
        :param vm_name: vm name
        :param vm_disk_no: disk number in VM
        :return: list of drive letters belong to disk number"""

        powershell_cmd = f"Get-Partition -DiskNumber {vm_disk_no} ^| fl DriveLetter"
        command_output = self.run_powershell_command_in_vm(vm_name, powershell_cmd)
        self._log.debug(f"Get all drive letters belong to disk number: {command_output}")
        str_list = command_output.split('\n')
        drive_letter = list()
        for line in str_list:
            line = line.strip()
            if "DriveLetter" in line:
                words = line.split(':', 1)
                if len(words) == 2:
                    drive_letter_identified = words[1].strip()
                    drive_letter.append(drive_letter_identified)
        return drive_letter
		
