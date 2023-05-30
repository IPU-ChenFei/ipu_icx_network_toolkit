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
import six
import os
import time

from abc import ABCMeta
from threading import Event
from typing import List

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.security.tests.common.common_windows import WindowsBase
from src.security.tests.tdx.tdx_common import TdxBaseTest
from src.lib import content_exceptions


@six.add_metaclass(ABCMeta)
class WindowsTdxBaseTest(WindowsBase, TdxBaseTest):
    """Base class extension for TDX which holds common arguments, functions."""

    # TODO: has to be a better way to do this....
    _BIOS_CONFIG_FILE_TDX_ENABLE = "collateral/tdx_en_windows_reference_knobs.cfg"
    _LINUX_TD_BUILD_SCRIPT = "collateral/vm_setup.sh"

    def __init__(self, test_log, arguments, cfg_opts):
        """Create an instance of TdxBaseTest

        :param cfg_opts: Configuration Object of provider
        :type cfg_opts: str
        :param test_log: Log object
        :type arguments: Namespace
        :param arguments: None
        :type cfg_opts: Namespace
        :return: None
        """
        super(WindowsTdxBaseTest, self).__init__(test_log, arguments, cfg_opts)

        if self.sut_os != OperatingSystems.WINDOWS:
            raise content_exceptions.TestSetupError("Cannot run Windows test on {} OS.".format(self.sut_os))

        self.tdx_bios_disable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             self.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_TDX_DISABLE)
        self.tdx_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            self._BIOS_CONFIG_FILE_TDX_ENABLE)
        self.TDVM_OSes = self.tdx_consts.TDVMOS
        self._os_booted_event = Event()
        self.command_timeout = self._vm_provider._command_timeout
        self.linux_vm_comport_map = dict()

        # fill the values from content_configuration.xml\security\TDX\WINDOWS section
        self.vm_user_name = self.tdx_properties[self.tdx_consts.TD_GUEST_USER]
        self.vm_user_pwd = self.tdx_properties[self.tdx_consts.TD_GUEST_USER_PWD]
        self.vm_reboot_timeout = int(self.tdx_properties[self.tdx_consts.VM_BOOT_TIMEOUT])
        self.is_vm_tdx_enabled = self.tdx_properties[self.tdx_consts.TD_GUEST_IMAGE_MTC_SETUP_ENABLED]
        self.enable_ethernet = self.tdx_properties[self.tdx_consts.TD_GUEST_IMAGE_ENABLE_ETHERNET_ADAPTER]

        self.vm_os = self.tdx_properties[self.tdx_consts.VM_OS]
        self.vm_tools_base_loc = self.tdx_properties[self.tdx_consts.VM_TOOLS_BASE_LOC]
        self.vm_guest_image_path_to_import = self.tdx_properties[self.tdx_consts.TD_GUEST_IMAGE_PATH + "_" + self.vm_os.upper()]
        self.legacy_vm_image_path_to_import = self.tdx_properties[self.tdx_consts.LEGACY_VM_IMAGE_PATH_SUT + "_" + self.vm_os.upper()]
        self.ubuntu_vm_guest_image_path_to_import = self.tdx_properties[self.tdx_consts.TD_GUEST_IMAGE_PATH_SUT_UBUNTU]
        self.ubuntu_legacy_vm_guest_image_path_to_import = self.tdx_properties[self.tdx_consts.LEGACY_GUEST_IMAGE_PATH_SUT_UBUNTU]
        self.vm_import_image_base_loc = self.tdx_properties[self.tdx_consts.TD_GUEST_IMAGE_DIR]
        self.ac_reset = self.tdx_properties[self.tdx_consts.AC_RESET]

    def prepare(self):
        if not self.tdx_properties[self.tdx_consts.CMCI_MORPHING_ENABLE]:
            cmci_morphing_dis_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  self.tdx_consts.KNOBS[self.tdx_consts.CMCI_MORPHING_ENABLE
                                                                        + "_False"])
            self.check_knobs(knob_file=cmci_morphing_dis_file, set_on_fail=True)

        # call prepare() of both parent classes.
        WindowsBase.prepare(self)
        TdxBaseTest.prepare(self)

        self._log.info("Checking out OS set up.")
        if self.ac_reset:
            self._log.warning("Using AC cycle to reboot SUT instead of graceful reboot from OS.")
        dest_folders_sut = [self.vm_import_image_base_loc, self.PUTTY_LOG_LOC]
        for dest_folder in dest_folders_sut:
            if not self.os.check_if_path_exists(dest_folder, directory=True):
                self.execute_os_cmd("mkdir {}".format(dest_folder))
                if not self.os.check_if_path_exists(dest_folder, directory=True):
                    raise content_exceptions.TestSetupError(f"Failed to create the destination folder {dest_folder} at SUT")

    def move_mtc_files_to_vm(self, vm_name):
        """Moving mtc specific vm file to a VM
        :param vm_name: VM name which is active in hyperv
        :type: str
        :return: True if the files are copying successfully to the VM otherwise false
        """

        sut_exec_path = self.WINDOWS_MTC_HV_LOCAL_PATH
        move_file_loc = r"{0} -vmname {1}".format(self.WINDOWS_MTC_HV_TO_VM_MOVE_FILE_SCRIPT, vm_name)
        mtc_file_move_cmd = "powershell.exe  -File {}".format(move_file_loc)
        mov_result = self._common_content_lib.execute_sut_cmd(mtc_file_move_cmd, "MTC file move command",
                                                              self.command_timeout, sut_exec_path)
        self._log.info("Output of mtc file upload command:\n{}".format(mov_result))
        # Verify the files are copied properly.
        test_path = r'Test-Path -Path "c:\\tmp\\td\\update-td.bat"'
        ret_val = self.run_powershell_command_in_vm(vm_name, test_path)
        return True if "True" in ret_val else False

    def run_mtc_files_in_vm(self, vm_name: str) -> bool:
        """Run the mtc specific batch file in the VM
        :param vm_name: VM name
        :return: True if mtc file ran in the VM otherwise False
        """

        self._log.info("Running the batch file in VM - c:\\tmp\\td\\update-td.bat")
        user_name = self.vm_user_name
        password = self.vm_user_pwd
        update_diskpart = r"{$arg= '/C c:\tmp\td\diskpart-vm.bat';Start-Process 'cmd.exe' -WorkingDirectory 'c:\tmp\td' -ArgumentList $arg -Verb runAs -Wait; return 'Success'}"
        update_td = r"{$arg= '/C c:\tmp\td\update-td.bat';Start-Process 'cmd.exe' -WorkingDirectory 'c:\tmp\td' -ArgumentList $arg -Verb runAs -Wait; return 'Success'}"

        try:
            # run disk partition to create B: partition
            update_diskpart_cmd = self._vm_provider.ESTABLISH_PS_SESSION.format(user_name, password, vm_name, update_diskpart)
            update_diskpart_output = self._common_content_lib.execute_sut_cmd("powershell {}".format(update_diskpart_cmd),
                                                                        "VM disk part", self._command_timeout)
            self._log.debug(update_diskpart_output)

            # run the batch file to update the binaries.
            update_td_cmd = self._vm_provider.ESTABLISH_PS_SESSION.format(user_name, password, vm_name, update_td)
            update_td_output = self._common_content_lib.execute_sut_cmd("powershell {}".format(update_td_cmd),
                                                                        "Update TD", self._command_timeout)
            self._log.debug(update_td_output)
        except Exception as e:
            self._log.debug("Exception while running the VM TDs")
            self._log.exception(e)
            return False
        return True

    def apply_mtc_security_settings_in_vmcx_file(self,
                                                 vm_name: str,
                                                 hvsedit_verify_string: List[str],
                                                 hvsedit_command_list: List[str]) -> bool:
        """Apply mtc specific configuration setting on  TD VM's vmcx file.

        :param vm_name: virtual machine name
        :param hvsedit_verify_string: list of strings to be verified
        :param hvsedit_command_list: list of commands to be run on vmcx file
        :return: True if mtc settings applied in vmcx file otherwise False.
        """
        self._log.info("Update the vmcx with MTC config settings")
        cmd_path = self.WINDOWS_MTC_HV_LOCAL_PATH
        vmcx_filepath = self._get_vmcx_path_from_vm(vm_name)
        if len(vmcx_filepath) == 0:
            raise "Failed to find the vmcx file"
        self._log.info("Update the vmcx file with config settings")
        for command in hvsedit_command_list:
            try:
                command = command.format(vmcx_filepath)
                self._log.info(command)
                sut_cmd_result = self._common_content_lib.execute_sut_cmd_no_exception(command, "hvsedit command", self._command_timeout, cmd_path, "Yes")
                self._log.debug(sut_cmd_result)
            except Exception as e:
                self._log.debug("Exception while running the vmcx commands TDs")
                self._log.exception(e)
                raise

        # verify the command is applied successfully
        command = 'hvsedit  "{0}"'.format(vmcx_filepath)
        sut_cmd_result = self._common_content_lib.execute_sut_cmd_no_exception(command, "hvsedit command", self._command_timeout, cmd_path, "Yes")
        self._log.debug(sut_cmd_result)
        ret_val = True
        for line in hvsedit_verify_string:
            if line in sut_cmd_result:
                self._log.info("The value {} found in vmcx file".format(line))
                continue
            else:
                self._log.info("The value {}  not found in vmcx file".format(line))
                ret_val = False
        return ret_val

    def apply_mtc_security_settings_for_windows_vm(self, vm_name: str) -> bool:
        """apply mtc special setting for Windows VM:
        :param vm_name: VM name"""
        hvs_edit_verify_string = ['tdx/enabled',
                                  'settings/vbs_opt_out']
        hvs_edit_command_list = ['hvsedit  "{0}" -s bool /configuration/settings/tdx/enabled true',
                                 'hvsedit  "{0}" -s bool /configuration/security/settings/vbs_opt_out true']

        return self.apply_mtc_security_settings_in_vmcx_file(vm_name, hvs_edit_verify_string, hvs_edit_command_list)

    def apply_mtc_security_settings_for_linux_vm(self, vm_name: str) -> bool:
        """apply mtc special setting for Windows VM:
        :param vm_name: VM name"""
        hvs_edit_verify_string = ['tdx/enabled',
                                  'settings/vbs_opt_out',
                                  'tdx/linuxguest']
        hvs_edit_command_list = ['hvsedit  "{0}" -s bool /configuration/settings/tdx/enabled true',
                                 'hvsedit  "{0}" -s bool /configuration/security/settings/vbs_opt_out true',
                                 'hvsedit  "{0}" -s bool /configuration/settings/tdx/linuxguest true']

        return self.apply_mtc_security_settings_in_vmcx_file(vm_name, hvs_edit_verify_string, hvs_edit_command_list)

    def apply_virtual_processors_to_vm_image(self, vm_name: str, virtual_proc_count: int = 0) -> bool:
        """Apply virtual processor count to vms
        :param vm_name: virtual machine name
        :param virtual_proc_count: number of virtual processor to be applied
        :return: True if success else False"""
        hvs_edit_verify_string = ['processors/count']
        hvs_edit_command_list = ['hvsedit  "{0}" -s int /configuration/settings/processors/count ' +
                                 str(virtual_proc_count)]
        return self.apply_mtc_security_settings_in_vmcx_file(vm_name, hvs_edit_verify_string, hvs_edit_command_list)

    def prepare_vm_with_mtc_setup(self, vm_name: str, vm_reboot_timeout: int = 300) -> None:
        """Prepare the VM with mtc files and restart the vm.
        :param vm_name: the index to be used to select the TDX VM.
        :param vm_reboot_timeout: timeout for VM rebooting.
        """
        # Copy MTC files from SUT to VM
        self.move_mtc_files_to_vm(vm_name)

        # set secure boot is disable/enable
        vhdx_generation = self.tdx_properties[self.tdx_consts.TD_GUEST_VHD_GENERATION]
        if vhdx_generation == "2":
            self.set_secure_boot(vm_name, "False")

        # run the MTC update batch file
        self.run_mtc_files_in_vm(vm_name)

        # shutdown VM and update the vmcx file with additional parameters.
        self.teardown_vm(vm_name)

        # Give 5 seconds to shutdown the machine.
        time.sleep(5)

        # Enable TDX settings
        self.apply_mtc_security_settings_for_windows_vm(vm_name)

        # Start-VM
        self.start_vm(vm_name)

        # wait for some time to boot the vm.
        self._log.info("waiting {} seconds". format(str(vm_reboot_timeout)))
        time.sleep(vm_reboot_timeout)

    def launch_tdx_vm_with_mtc_settings(self, key: int, vm_name: str, tdvm: bool, is_vm_tdx_enabled: bool,
                                        enable_ethernet: bool, tdx_vm_reboot_timeout: int) -> bool:
        """ launch tdx vm and apply mtc settings for tdvms. MTC settings never apply on legacy VMs.

        :param key: index to the vm name identifier.
        :param vm_name: vm name
        :param tdvm: is trusted vm or not
        :param is_vm_tdx_enabled: True if VM prepared with MTC settings otherwise False
        :param enable_ethernet: True if ethernet need to be enable in the VM otherwise False
        :param tdx_vm_reboot_timeout: Timeout required for TDX enabled VM.
        :return: True if VM start successfully.
        """

        if vm_name not in self.vm_names_list:
            if not tdvm:
                src_path = self.legacy_vm_image_path_to_import
            else:
                src_path = self.vm_guest_image_path_to_import

            dest_path = os.path.join(self.vm_import_image_base_loc, vm_name)
            self.import_vm(key, vm_name, src_path, dest_path)

        self.start_vm(vm_name=vm_name)
        # tdx vm need additional time for booting.
        if is_vm_tdx_enabled is True:
            self._log.info("waiting {} seconds".format(str(tdx_vm_reboot_timeout)))
            time.sleep(tdx_vm_reboot_timeout)
        if enable_ethernet is True:
            self._log.info("setting the network connectivity to the VM")
            self.attach_ethernet_adapter_to_vm(vm_name)
            self._log.info("Restarting the VM with NW connectivity")
            self.start_vm(vm_name=vm_name)
            self._log.info("waiting {} seconds".format(str(tdx_vm_reboot_timeout)))
            time.sleep(tdx_vm_reboot_timeout)
        self._log.info("Verify VM is running. {}".format(vm_name))
        if self.verify_vm_state(vm_name, self._vm_provider.VM_STATE_STR):
            self._log.info("{} is running".format(vm_name))
        else:
            self._log.info("{} is not running".format(vm_name))
            return False

        # If VM is not prepared with MTC binaries, need to be execute now.
        if is_vm_tdx_enabled is False and tdvm is True:
            self._log.info("Prepare VM - {} with MTC files".format(vm_name))
            self.prepare_vm_with_mtc_setup(vm_name, tdx_vm_reboot_timeout)

        # Ping from SUT to the guest machine.
        if enable_ethernet is True:
            self._log.info("Pinging guest {}.".format(vm_name))
            if not self.vm_is_alive(vm_name=vm_name):
                raise content_exceptions.TestFail("VM {} could not be reached after booting.".format(vm_name))
            self._log.info("Ping was successful; VM is up.")
        return True

    def launch_legacy_vm(self, key: int, vm_name: str, tdvm: bool, enable_ethernet: bool = False,
                         vm_reboot_time: int = 30) -> bool:
        """launch legacy VM and verify the connectivity
        :param key: key to identify the VM
        :param vm_name: vm name
        :param tdvm: True if trusted VM otherwise False legacy VM
        :param enable_ethernet: True to setup the NW connectivity
        :param vm_reboot_time: reboot time for VM
        :return: True if VM is running successfully otherwise False
        """

        if vm_name not in self.vm_names_list:
            if not tdvm:
                src_path = self.legacy_vm_image_path_to_import
            else:
                src_path = self.vm_guest_image_path_to_import

            dest_path = os.path.join(self.vm_import_image_base_loc, vm_name)
            self.import_vm(key, vm_name, src_path, dest_path)

            # start the VM
        self.start_vm(vm_name=vm_name)

        # activate the network connectivity
        if enable_ethernet is True:
            self._log.info("setting the network connectivity to the VM")
            self.attach_ethernet_adapter_to_vm(vm_name)
            self._log.info("Restarting the VM with NW connectivity")
            self.start_vm(vm_name=vm_name)
            self._log.info("waiting {} seconds".format(str(vm_reboot_time)))
            time.sleep(vm_reboot_time)

        self._log.info("Verify VM is running. {}".format(vm_name))
        if self.verify_vm_state(vm_name, self._vm_provider.VM_STATE_STR):
            self._log.info("{} is running".format(vm_name))
        else:
            self._log.info("{} is not running".format(vm_name))
            return False

        # Ping from SUT to the guest machine.
        if enable_ethernet is True:
            self._log.info("Pinging guest {}.".format(vm_name))
            if not self.vm_is_alive(vm_name=vm_name):
                raise content_exceptions.TestFail("VM {} could not be reached after booting.".format(vm_name))
            self._log.info("Ping was successful; VM is up.")
        return True

    def launch_td_guest(self, key: int, vm_name: str) -> None:
        """Launch TD guest
        :param key: key index to identify the vm name
        :param vm_name: VM name
        :raise: content_exceptions.TestFail if td guest creation fails"""
        tdvm = True
        ret_val = self.launch_tdx_vm_with_mtc_settings(key, vm_name, tdvm, self.is_vm_tdx_enabled,
                                                       self.enable_ethernet, self.vm_reboot_timeout)
        if ret_val is False:
            raise content_exceptions.TestFail("Failed to launch TDVM")

    def launch_legacy_guest(self, key: int, vm_name: str) -> None:
        """Launch legacy guest
        :param key: key index to identify the vm name
        :param vm_name: VM name
        :raise: content_exceptions.TestFail if legacy guest creation fails"""
        tdvm = False
        ret_val = self.launch_legacy_vm(key, vm_name, tdvm, self.enable_ethernet, self.vm_reboot_timeout)
        if ret_val is False:
            raise content_exceptions.TestFail("Failed to launch legacy VM guest")

    def launch_mktme_guest(self, key: int, vm_name: str) -> None:
        """Launch TD guest with mktme settings
        :param key: key index to identify the vm name
        :param vm_name: VM name
        :raise: content_exceptions.TestFail if mk-tme guest creation fails"""
        tdvm = False
        ret_val = self.launch_legacy_vm(key, vm_name, tdvm, self.enable_ethernet, self.vm_reboot_timeout)
        if ret_val is False:
            raise content_exceptions.TestFail("Failed to launch legacy VM")

        # shutdown tdvm and apply MKTME settings.
        self.apply_mktme_settings_on_vm(vm_name)

    def launch_ubuntu_td_guest(self, key: int, vm_name: str) -> None:
        """Launch Ubuntu TD guest
        :param key: key index to identify the vm name
        :param vm_name: VM name
        :raise: content_exceptions.TestFail if td guest creation fails"""
        ret_val = self.launch_ubuntu_tdx_vm_with_mtc_settings(key, vm_name, self.vm_reboot_timeout)
        if ret_val is False:
            raise content_exceptions.TestFail("Failed to launch  Ubuntu TDVM")

    def launch_legacy_ubuntu_guest(self, key: int, vm_name: str) -> None:
        """Launch legacy Ubuntu guest
        :param key: key index to identify the vm name
        :param vm_name: VM name
        :raise: content_exceptions.TestFail if ubuntu guest creation fails"""

        ret_val = self.launch_legacy_ubuntu_vm(key, vm_name, self.vm_reboot_timeout)
        if ret_val is False:
            raise content_exceptions.TestFail("Failed to launch  Ubuntu VM")

    def verify_tdx_enumeration(self) -> bool:
        """Verify TDX is enumerated
        :return True if TDX capabilities are enumerated else return False"""
        self._log.info("Checking TDX enumeration.")
        results = self.msr_read(self.tdx_consts.RegisterConstants.MTTR_CAPABILITIES)
        if not self.bit_util.is_bit_set(results, self.tdx_consts.MTTRCapabilitiesBits.TDX_ENUMERATION):
            self._log.error("TDX enumeration bit is not set! MSR 0x{:x}: 0x{:x}".format(
                self.tdx_consts.RegisterConstants.MTTR_CAPABILITIES, int(results)))
            return False

        self._log.info("TDX enumeration bit is set! MSR 0x{:x}: 0x{:x}".format(
            self.tdx_consts.RegisterConstants.MTTR_CAPABILITIES, int(results)))
        return True

    def install_pkgs_for_ubuntu_vm(self, vm_ip_address: str):
        """install all relevant packages for ubuntu VM
        :param vm_ip_address: VM ipaddress"""
        pkg_net_tools = f" echo {self.vm_user_pwd} | sudo -S apt-get install net-tools"
        self.run_command_in_linux_vm_using_ssh(vm_ip_address, pkg_net_tools)

    def prepare_ubuntu_vm_with_mtc_setup(self, vm_name: str, vm_ip_address: str, tdx_vm_reboot_timeout: int) -> None:
        """prepare ubuntu tdx vm with MTC setups.
        :param vm_name: VM name
        :parma vm_ip_address: vm's ip address
        :param tdx_vm_reboot_timeout: vm reboot timeout."""
        # basic paths/commands.
        del_image_file_cmd = r"cd /home/administrator; rm linux-image-*.deb; rm linux-headers-*.deb"
        linux_tools_src_path = r"C:\tmp\linux-tools\*"
        linux_tools_dest_path = r"/home/administrator//"
        linux_tdx_vm_setup_script = f"/home/administrator/vm_setup.sh"
        linux_td_build_script = r"C:\tmp\linux-tools\vm_setup.sh"

        if self.verify_vm_state(vm_name, self._vm_provider.VM_STATE_STR):
            self._log.info("{} is running".format(vm_name))
        else:
            self._log.info("{} is not running".format(vm_name))
            self.start_vm(vm_name=vm_name)
            self._log.info("waiting {} seconds".format(str(tdx_vm_reboot_timeout)))
            time.sleep(tdx_vm_reboot_timeout)
            vm_ip_address = self.get_vm_ipaddress_for_linux_guest(vm_name)

        # copy ssh keys to vm
        self.create_ssh_keys_sut(self.sut_login_name)
        self.copy_ssh_key_from_sut_to_linux_vm(self.sut_login_name, vm_ip_address)

        if self.is_vm_tdx_enabled:
            self._log.info("VM already prepared with MTC settings.")
            return
        # copy the script to sut
        if not self.test_path_sut(linux_td_build_script):
            src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._LINUX_TD_BUILD_SCRIPT)
            self.copy_file_from_host_to_sut(src_path, linux_tools_src_path.replace("*", ""))
        # install all necessary software packages
        # TODO: If VM is connected to exteral virtual switch packages can install without any issues, otherwise
        # the package has to be copied to VM and install. Need to revisit this function later and and complete it.
        # self.install_pkgs_for_ubuntu_vm(vm_ip_address)
        # remove the old images.
        self.run_command_in_linux_vm_using_ssh(vm_ip_address, del_image_file_cmd)

        # copy mtc files to ubuntu vm
        self.copy_files_between_sut_and_linux_vm(linux_tools_src_path, linux_tools_dest_path, True, vm_ip_address)
        command = f"echo {self.vm_user_pwd} | sudo -S chmod +x {linux_tdx_vm_setup_script}"
        self.run_command_in_linux_vm_using_ssh(vm_ip_address, command)

        # run shell script in vm
        self._log.info("Running command: " + linux_tdx_vm_setup_script)
        self.run_command_in_linux_vm_using_ssh(vm_ip_address, f"{linux_tdx_vm_setup_script} {self.vm_user_pwd}")

        # shutdown VM
        self.teardown_vm(vm_name)

        # apply mtc settings on vmcx file.
        self.apply_mtc_security_settings_for_linux_vm(vm_name)

        # launch PipeServer with putty connectivity name
        # comport and putty connectivity are using similar naming conventions like vmname+com2+(p for putty)
        #  eg: vm0linuxcom2 vm0linuxcom2p
        comport_2 = str(vm_name.replace("-", "") + "com2").lower()
        putty_conn_name = str(comport_2 + "p").lower()
        self.launch_pipe_server_for_linux_vm(comport_2, putty_conn_name)

        # launch the putty
        output_log = os.path.join(self.PUTTY_LOG_LOC, f"{putty_conn_name}.log")
        if self.test_path_sut(output_log):
            self.delete_folder_at_sut(output_log)
        self.launch_putty_for_pipe_server(putty_conn_name, 115200, output_log)

        # launch VM
        self.start_vm(vm_name)
        time.sleep(tdx_vm_reboot_timeout)

    def apply_vm_com_port_to_vm(self, vm_name: str) -> None:
        """Applying the VM port to the vm
        :param vm_name: virtual machine name"""
        # apply vm com ports.
        comport_1 = str(vm_name.replace("-", "") + "com1").lower()
        self.set_vm_com_port(vm_name, 1, comport_1)

        comport_2 = str(vm_name.replace("-", "") + "com2").lower()
        self.set_vm_com_port(vm_name, 2, comport_2)

    def setup_ubuntu_vm_image(self, key: int, vm_name: str, tdvm: bool, vm_reboot_timeout: int) -> bool:
        """Using to import vm and setup the network for ubuntu vm image.
        :param key: virtual machine identification key
        :param vm_name: VM name
        :param tdvm: tdvm or legacy vm.
        :param vm_reboot_timeout: reboot timeout
        :return: True if it success else false
        """

        if vm_name not in self.vm_names_list:
            if tdvm:
                src_path = self.ubuntu_vm_guest_image_path_to_import
            else:
                src_path = self.ubuntu_legacy_vm_guest_image_path_to_import
            dest_path = os.path.join(self.vm_import_image_base_loc, vm_name)
            self.import_vm(key, vm_name, src_path, dest_path)
            self.apply_vm_com_port_to_vm(vm_name)

        self.start_vm(vm_name=vm_name)
        # tdx vm need additional time for booting.
        self._log.info(f"Waiting {vm_reboot_timeout} seconds")
        time.sleep(vm_reboot_timeout)
        self._log.info("Setting the network connectivity to the VM")
        self.attach_ethernet_adapter_to_vm(vm_name)
        self._log.info("Restarting the VM with NW connectivity")
        self.start_vm(vm_name=vm_name)
        self._log.info(f"Waiting {vm_reboot_timeout} seconds")
        time.sleep(vm_reboot_timeout)
        self._log.info(f"Verify VM, {vm_name} is running")
        if self.verify_vm_state(vm_name, self._vm_provider.VM_STATE_STR):
            self._log.info("{} is running".format(vm_name))
        else:
            self._log.info("{} is not running".format(vm_name))
            return False
        return True

    def launch_ubuntu_tdx_vm_with_mtc_settings(self, key: int, vm_name: str,
                                               tdx_vm_reboot_timeout: int) -> bool:
        """Launch ubuntu VM and apply mtc settings.

        :param key: index to the vm name identifier.
        :param vm_name: vm name
        :param tdx_vm_reboot_timeout: Timeout required for TDX enabled VM.
        :return: True if VM start successfully.
        """
        tdvm = True
        ret_val = self.setup_ubuntu_vm_image(key, vm_name, tdvm, tdx_vm_reboot_timeout)
        if not ret_val:
            raise content_exceptions.TestFail(f"VM {vm_name} not running")

        # If VM is not prepared with MTC binaries, need to be execute now.
        self._log.info(f"Prepare VM - {vm_name} with MTC files")
        vm_ip_address = self.get_vm_ipaddress_for_linux_guest(vm_name)
        self.prepare_ubuntu_vm_with_mtc_setup(vm_name, vm_ip_address, tdx_vm_reboot_timeout)

        # Ping from SUT to Linux guest machine.
        self._log.info(f"Pinging to the guest {vm_name}")
        if not self.vm_is_alive(vm_name=vm_name, vm_ip=vm_ip_address):
            raise content_exceptions.TestFail(f"VM '{vm_name}' could not be reached after booting.")
        self._log.info("Ping was successful; VM is up.")
        return True

    def launch_legacy_ubuntu_vm(self, key: int, vm_name: str, vm_reboot_timeout: int) -> bool:
        """Launch ubuntu VM and apply mtc settings.

        :param key: index to the vm name identifier.
        :param vm_name: vm name
        :param vm_reboot_timeout: Timeout required for TDX enabled VM.
        :return: True if VM start successfully.
        """
        tdvm = False
        ret_val = self.setup_ubuntu_vm_image(key, vm_name, tdvm, vm_reboot_timeout)
        if not ret_val:
            raise content_exceptions.TestFail(f"VM {vm_name} not running")

        vm_ip_address = self.get_vm_ipaddress_for_linux_guest(vm_name)
        # copy ssh keys to vm
        self.create_ssh_keys_sut(self.sut_login_name)
        self.copy_ssh_key_from_sut_to_linux_vm(self.sut_login_name, vm_ip_address)

        # Ping from SUT to Linux guest machine.
        self._log.info(f"Pinging guest {vm_name}")
        if not self.vm_is_alive(vm_name=vm_name, vm_ip=vm_ip_address):
            raise content_exceptions.TestFail(f"VM {vm_name} could not be reached after booting.")
        self._log.info("Ping was successful; VM is up.")
        return True
