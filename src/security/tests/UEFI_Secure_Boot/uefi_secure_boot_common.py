# !/usr/bin/env python
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
import time
from collections import OrderedDict
from threading import Event
from abc import abstractmethod

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.private.cl_utils.adapter import data_types

from src.lib.reaction_lib import ReactionLib
from src.lib.os_lib import LinuxCommonLib
from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.security.tests.UEFI_Secure_Boot.uefi_secure_boot_constants import SecureBoot
from src.provider.copy_usb_provider import UsbRemovableDriveProvider
from src.lib.bios_util import SerialBiosUtil


class UEFISecureBootCommon(ContentBaseTestCase):
    """
    Base test class for UEFI Secure Boot.

    UEFI Secure Boot tests require use of a USB drive loaded with the certificates listed in the
    content_configuration.xml file in the <secure_boot> tag area as certificates are installed in the BIOS menu where
    there is no network connectivity.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Initialize instance of UEFISecureBootCommon class to install needed collateral, Secure Boot details from
        content_configuration.xml, and variables needed to launch and navigate shim menu.

        :param test_log: Used for error, debug and info messages.
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UEFISecureBootCommon, self).__init__(test_log, arguments, cfg_opts)
        self.install_collateral = InstallCollateral(test_log, self.os, cfg_opts)
        self.command_timeout = self._common_content_configuration.get_command_timeout()
        self.password = "password"
        self.product = self._common_content_lib.get_platform_family()
        self.secure_boot_consts = SecureBoot.get_subtype_cls("SecureBoot" + self.product, False)
        self.copy_usb = UsbRemovableDriveProvider.factory(test_log, cfg_opts, self.os)
        self.uuid = None
        self.secure_boot_properties = self._common_content_configuration.get_security_secure_boot_params()
        self.shim_menu_entered = Event()
        self.serial_bios_util = SerialBiosUtil(self.ac_power, test_log, self._common_content_lib, cfg_opts)
        self.path_to_certs = None
        self.certs_list = []
        for certs in self.secure_boot_properties.keys():
            cert_type = certs
            cert_list = self.secure_boot_properties[cert_type].split(";")
            for cert in cert_list:
                try:
                    file_name, signature = cert.split(",")
                except ValueError:  # raised if no signature
                    file_name = cert
                    signature = None
                cert_obj = SecureBoot.Cert(file_name, cert_type, signature)
                self.certs_list.append(cert_obj)

    def install_certs_bios_menu(self) -> None:
        """Boot to BIOS menu and install certificates, save and exit out of BIOS menu."""
        self.serial_bios_util.navigate_bios_menu()
        self.install_certs()

    def prepare(self) -> None:
        """Prepare for UEFI Secure Boot tests.  Gets data from USB drive where certificates are stored."""
        super(UEFISecureBootCommon, self).prepare()
        self.path_to_certs = self.set_up_certs()  # stage certs in UEFI reachable location
        self.uuid = self.get_uuid(self.path_to_certs)  # get uuid identifier for disk to be selected in BIOS menu

    def install_certs(self) -> None:
        """Navigates the BIOS menu to the Secure Boot menu and iterates over certificates from config file to
        install. """
        self._log.info("Going to Secure Boot menu,")
        self.serial_bios_util.select_enter_knob(self.secure_boot_consts.SECURE_BOOT_PATH)
        self._log.info("Set Secure Boot Configuration to Custom Mode.")
        self.serial_bios_util.set_bios_knob(self.secure_boot_consts.SECURE_BOOT_MODE_LABEL, data_types.BIOS_UI_OPT_TYPE,
                                            self.secure_boot_consts.CUSTOM_MODE_OPTION)

        self._log.info("Going to Custom Secure Boot Options menu.")
        start_knob = self.serial_bios_util.read_item()

        if self.secure_boot_consts.CUSTOM_SECURE_BOOT_OPTIONS_DIR not in start_knob:
            self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_DOWN)

        time.sleep(5)
        while self.secure_boot_consts.CUSTOM_SECURE_BOOT_OPTIONS_DIR not in self.serial_bios_util.read_item() and \
                self.serial_bios_util.read_item() != start_knob:
            self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_DOWN)
            time.sleep(5)
        self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_ENTER)

        # starting certs
        for cert in self.certs_list:
            if cert.type in self.secure_boot_consts.CertTypes.__members__ and not cert.installed:
                self._log.debug(f"Installing {cert.type} cert {cert.file}")
                self.install_cert(cert)
                cert.installed = True
            elif cert.installed:
                self._log.debug(f"{cert.type} cert {cert.file} is already installed in BIOS menu.")
            else:
                self._log.warning(f"{cert.type} is not a valid Secure Boot certificate type.  Ignoring.")

    def install_cert(self, cert: SecureBoot.Cert) -> None:
        """Install cert from cert file location on USB drive.
        :param cert: Cert object containing certificate type, file, and/or signature if applicable.  BIOS supports PK,
        KEK, DB, DBX, DBT."""
        self._log.debug(f"Selecting certificate type {cert.type}")
        self.navigate_cert_window(cert)
        self._log.debug(f"Selecting boot device with uuid {self.uuid} storing certificate")
        self.select_drive_with_certificate()
        self._log.debug(f"Selecting certificate file {cert.file}")
        self.add_certificate_file(cert)

        # skip signature GUID entry for PK
        if cert.signature is not None:
            self._log.debug(f"Adding signature {cert.signature} for {cert.type} certificate {cert.file}.")
            self.enter_signature_guid(cert.signature)

        # Save and commit
        self._log.debug(f"Saving and committing certificate {cert.file} to BIOS.")
        self.serial_bios_util.select_enter_knob(self.secure_boot_consts.SAVE_CERT_OPTIONS)

    def add_certificate_file(self, cert: SecureBoot.Cert) -> None:
        """Select and add certificate file to Secure Boot with BIOS File Explorer from BIOS menu.
        :param cert: Cert object containing file name to be added."""
        # do this for every cert
        screen_data = self.serial_bios_util.get_current_screen_info()

        results = []
        for line in screen_data[0]:
            if not line.startswith(("\\", "/", r"\^")) and line != "File Explorer" and line != "":
                results.append(line)

        for file in results:
            if cert.file not in file:
                self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_DOWN)
                time.sleep(5.0)
            else:
                self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_ENTER)
                time.sleep(5.0)
                break

    def select_drive_with_certificate(self) -> None:
        """Select drive from device list with Secure Boot certificates from BIOS menu."""
        # do this for every cer file
        screen_data = self.serial_bios_util.get_current_screen_info()

        results = []
        entry = ""
        for line in screen_data[0]:
            if line.startswith(">"):
                entry = line  # initialize drive selection
            elif line.endswith("]"):
                results.append(entry)  # ] is the end of the entry, so line must be a completed drive entry
            elif not line.startswith(("\\", "/", "^")):  # if not a header or footer line, must be drive data
                entry = entry + line

        found_disk = False
        for disk in results:
            if self.uuid.upper() not in disk:
                self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_DOWN)
            else:
                found_disk = True
                self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_ENTER)
                break
        if not found_disk:
            raise content_exceptions.TestFail("Could not find drive containing certs in list of devices for "
                                              "Secure Boot.")

    def enter_signature_guid(self, signature_guid: str) -> None:
        """Enter Signature GUID for certificate.
        :param signature_guid: GUID to be entered for Secure Boot certificate."""
        self.serial_bios_util.write_input_text(self.secure_boot_consts.SIGNATURE_GUID_LABEL, data_types.BIOS_UI_OPT_TYPE,
                                               signature_guid)

    def navigate_cert_window(self, cert: SecureBoot.Cert) -> None:
        """Move through cert Options -> Enroll cert -> Enroll cert Using File options in Secure Boot BIOS menu.
        :param cert: cert type (PK, KEK, DB, DBX, DBT types supported)"""
        if cert.type == self.secure_boot_consts.CertTypes.KEK.name:
            enroll_file_label = "Enroll {} using File"  # KEK menu uses lowercase u instead...
        else:
            enroll_file_label = self.secure_boot_consts.ENROLL_FILE_LABEL
        self.serial_bios_util.select_enter_knob(OrderedDict([(self.secure_boot_consts.OPTIONS_DIR.format(cert.type),
                                                             data_types.BIOS_UI_DIR_TYPE)]))
        if self.secure_boot_consts.CertTypes.DB.name in cert.type:
            file_label = "Signature"
        else:
            file_label = cert.type
        self.serial_bios_util.select_enter_knob(OrderedDict([(self.secure_boot_consts.ENROLL_LABEL.format(file_label),
                                                             data_types.BIOS_UI_DIR_TYPE)]))
        self.serial_bios_util.select_enter_knob(OrderedDict([(enroll_file_label.format(file_label),
                                                            data_types.BIOS_UI_DIR_TYPE)]))

    def install_shim(self) -> None:
        """Install OS key into shim."""
        self.os.execute_async("reboot")
        self.shim_menu_entered.clear()
        with ReactionLib(self._log, self.cng_log, console_log_skip_to_end=True, daemon=False) as reaction_engine:
            reaction_engine.register_reaction(r"PROGRESS CODE: V03058001 I0", self.enroll_mok_in_shim)
            self.shim_menu_entered.wait(self.reboot_timeout)
            reaction_engine.remove_reaction(r"PROGRESS CODE: V03058001 I0")
            if not self.shim_menu_entered.is_set():
                raise content_exceptions.TestFail("Timed out waiting to enter shim management window.")
        self.os.wait_for_os(self.reboot_timeout)

    def clear_mok_keys(self) -> None:
        """Remove OS keys from shim."""
        self.os.execute_async("reboot")
        self.shim_menu_entered.clear()
        with ReactionLib(self._log, self.cng_log, console_log_skip_to_end=True, daemon=False) as reaction_engine:
            reaction_engine.register_reaction(r"PROGRESS CODE: V03058001 I0", self.remove_mok_in_shim)
            self.shim_menu_entered.wait(timeout=self.reboot_timeout)
            reaction_engine.remove_reaction(r"PROGRESS CODE: V03058001 I0")
            if not self.shim_menu_entered.is_set():
                self._log.error("Timed out waiting to enter shim management window.")
                raise content_exceptions.TestFail("Timed out waiting to enter shim management window.")
        self.os.wait_for_os(self.reboot_timeout)

    # noinspection PyUnusedLocal
    def enroll_mok_in_shim(self, match) -> None:
        """Enter shim menu and enroll MOK."""
        self._log.debug("Entering shim window.")
        time.sleep(5.0)
        self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_SPACE)
        self.navigate_shim_window("Enroll MOK")
        self.navigate_shim_window("Continue")
        self.navigate_shim_window("Yes")
        self.enter_shim_menu_text(self.password)
        self.navigate_shim_window("Reboot")
        self._log.debug("Exiting shim window.")
        self.shim_menu_entered.set()

    # noinspection PyUnusedLocal
    def remove_mok_in_shim(self, match) -> None:
        """Enter shim menu and remove all MOK."""
        self._log.debug("Entering shim window.")
        time.sleep(5.0)
        self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_SPACE)
        self.navigate_shim_window("Reset MOK")
        self.navigate_shim_window("Yes")
        self.enter_shim_menu_text(self.password)
        self.navigate_shim_window("Reboot")
        self._log.debug("Exiting shim window.")
        self.shim_menu_entered.set()

    def navigate_shim_window(self, select_str: str) -> None:
        """Select option in shim window.
        :param select_str: menu option to select in shim management window
        :raise content_exceptions.TestFail: if option cannot be found in shim menu."""
        if self.shim_menu_entered.is_set():
            return
        time.sleep(5.0)
        screen = self.serial_bios_util.get_current_screen_info()
        menu_text = []
        for line in screen[0]:  # reconstruct menu
            if line[0] == "|":
                menu_text.append(line)

        for menu_entry in menu_text:
            if select_str not in menu_entry:
                self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_DOWN)
            else:
                self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_ENTER)
                return

        raise content_exceptions.TestFail(f"Could not find {select_str} in shim menu.")

    def enter_shim_menu_text(self, data: str) -> None:
        """Enter text into shim menu selection.
        :param data: data to be entered into shim window."""
        for letter in data:
            self.serial_bios_util.press_key(letter)
        self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_ENTER)

    @abstractmethod
    def check_secure_boot(self) -> bool:
        """Check at the OS level that UEFI Secure Boot is enabled.
        :return: True if Secure Boot is enabled in the OS and False if Secure Boot is disabled."""
        raise NotImplementedError("Must be implemented as OS level class.")

    def toggle_secure_boot(self):
        """Disable/enable Secure Boot without modifying certificates."""
        self.serial_bios_util.select_enter_knob(self.secure_boot_consts.SECURE_BOOT_DISABLE_OPTION)
        time.sleep(20)  # add delay to press enter for confirmation window
        self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_ENTER)  # save confirmation window

    def cleanup(self, return_status) -> None:
        """Remove Secure Boot certs from BIOS menu."""
        self.serial_bios_util.navigate_bios_menu()
        self._log.info("Going to Secure Boot menu to clear certificates from BIOS.")
        self.serial_bios_util.select_enter_knob(self.secure_boot_consts.SECURE_BOOT_PATH)
        self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_UP)
        self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_ENTER)
        time.sleep(20)  # add delay to press enter for confirmation window
        self.serial_bios_util.press_key(data_types.BIOS_CMD_KEY_ENTER)
        self._log.info("Removed certificates from BIOS, rebooting to OS to finish clean up.")
        self.perform_graceful_g3()
        super(UEFISecureBootCommon, self).cleanup(return_status)


class LinuxUEFISecureBoot(UEFISecureBootCommon):
    def __init__(self, test_log, arguments, cfg_opts):
        """

        :param test_log: Used for error, debug and info messages.
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(LinuxUEFISecureBoot, self).__init__(test_log, arguments, cfg_opts)
        self.linux_lib = LinuxCommonLib(test_log, self.os)
        self.current_kernel = "/boot/vmlinuz-$(uname -r)"
        self.backup_kernel = "/boot/bak_vmlinuz-$(uname -r)"

    def prepare(self) -> None:
        super(LinuxUEFISecureBoot, self).prepare()
        """Install kernel-core package and import kernel keys."""
        self._log.debug("Installing kernel-core yum package.")
        self.install_collateral.yum_install("openssl-devel openssl")
        self.install_kernel_signing_tools()
        self._log.info("Rebooting to BIOS menu to install Secure Boot MSFT certs.")
        self.install_certs_bios_menu()
        self.serial_bios_util.go_back_a_screen()
        self._log.info("Disabling Secure Boot to sign kernel.")
        self.toggle_secure_boot()
        self._log.info("Booting to OS to sign kernel.")
        self.perform_graceful_g3()
        self._log.info("Signing kernel.")
        self.sign_kernel()
        self._log.info("Booting to BIOS menu to install kernel signed certificate.")
        self.install_certs_bios_menu()
        self._log.info("Re-enabling Secure Boot.")
        self.serial_bios_util.go_back_a_screen()
        self.toggle_secure_boot()
        self._log.info("Booting to OS to verify Secure Boot is enabled.")
        try:
            self.perform_graceful_g3()
        except content_exceptions.TestFail:  # attempt to disable and re-enable secure boot
            self._log.warning("Failed to boot on first attempt to OS with signed kernel after enabling Secure Boot.")
            self.serial_bios_util.navigate_bios_menu()
            self.serial_bios_util.select_enter_knob(self.secure_boot_consts.SECURE_BOOT_PATH)
            self.toggle_secure_boot()
            self.perform_graceful_g3()
            self.serial_bios_util.navigate_bios_menu()
            self.serial_bios_util.select_enter_knob(self.secure_boot_consts.SECURE_BOOT_PATH)
            self.toggle_secure_boot()
            self.perform_graceful_g3()

    def install_kernel_signing_tools(self):
        """Install kernel signing rpm sbsigntools."""
        self._log.debug("Pulling sbsigntools from Artifactory.")
        kernel_signing_tools_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            self.secure_boot_consts.ARTIFACTORY_LINUX_KERNEL_SIGNING_TOOLS)
        sut_path = f"/tmp/{self.secure_boot_consts.ARTIFACTORY_LINUX_KERNEL_SIGNING_TOOLS}"
        self._log.debug(f"Copying sbsigntools to the SUT {sut_path}")
        self.os.copy_local_file_to_sut(kernel_signing_tools_path, sut_path)
        self._log.debug("Installing sbsigntools.")
        results = self.os.execute(f"rpm -ifvh {sut_path}", self.command_timeout)
        self._log.debug(f"{results.stdout}\n{results.stderr}")

    def import_key(self) -> None:
        """Import key and sign current kernel for Secure Boot and shim preparation."""
        self._log.debug("Importing signing certificate.")
        self.os.execute(f"mokutil --generate-hash={self.password} > {self.password_hash_file_name}",
                        self.command_timeout)
        hash_value = self.os.execute(f"kr=$(uname -r); mokutil --import /boot/vmlinuz-${{kr%}}"
                                     f"--hash-file {self.password_hash_file_name}", self.command_timeout).stdout
        hash_value = hash_value.split(" ")[-1]
        self.os.execute(f"mokutil --import-hash {hash_value}", self.command_timeout)
        self.os.execute(f"kr=$(uname -r); mokutil --import /usr/share/doc/kernel-keys/${{kr%}}/kernel-signing-ca.cer "
                        f"--hash-file {self.password_hash_file_name}", self.command_timeout)

    def check_secure_boot(self) -> bool:
        """Check at the OS level that UEFI Secure Boot is enabled.
        :return: True if Secure Boot is enabled in the OS and False if Secure Boot is disabled."""
        results = self.os.execute("mokutil --sb-state", self.command_timeout)
        self._log.debug(f"Output from mokutil --sb-state command: \n\tstdout{results.stdout}\n\t{results.stderr}")
        if "SecureBoot enabled" not in results.stdout:
            self._log.info("Secure Boot is not enabled in the OS.")
            return False
        else:
            self._log.info("Secure Boot is enabled in the OS.")
            return True

    def set_up_certs(self) -> str:
        """Stage certs in EFI accessible area and return path.
        :return: path where certifications are stored"""
        path_to_certs = "/boot/efi/"
        local_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            self.secure_boot_consts.ARTIFACTORY_SECURE_BOOT_CERTS)
        self.os.copy_local_file_to_sut(local_path, "/tmp/")
        self.os.execute(f"unzip -o /tmp/{self.secure_boot_consts.ARTIFACTORY_SECURE_BOOT_CERTS} -d {path_to_certs}",
                        self.command_timeout)
        return path_to_certs

    def sign_kernel(self):
        """Generate certificate and sign kernel, add to list of cerificates to be installed."""
        temp_crt_file = f"{self.path_to_certs}DB.crt"
        temp_cer_file = "DB.cer"
        temp_db_key = f"{self.path_to_certs}DB.key"
        commands = [
            f"mv -f {self.current_kernel} {self.backup_kernel}",  # make backup copy of kernel
            f"sbsign --key {temp_db_key} --cert {temp_crt_file} --output {self.current_kernel} {self.backup_kernel}"  # sign kernel
        ]
        for command in commands:
            results = self.os.execute(command, self.command_timeout)
            self._log.debug(f"stdout: {results.stdout}\nstderr:{results.stderr}")

        if not self.os.check_if_path_exists(self.current_kernel):
            self._log.debug("Failed to sign kernel.  Reverting back to old kernel")
            self._log.debug(self.os.execute(f"mv {self.backup_kernel} {self.current_kernel}",
                                            self.command_timeout).stdout)
            raise content_exceptions.TestFail("Failed to sign kernel with generated certificate.")
        self._log.debug("Kernel signing appears to be successful.")
        cert = SecureBoot.Cert(temp_cer_file, self.secure_boot_consts.CertTypes.DB.name, None)
        self._log.debug(f"Adding {cert.file} to be registered in BIOS.")
        self.certs_list.append(cert)

    def get_uuid(self, path: str) -> str:
        """Get UUID for disk device where certs are being stored
        :param path: path to where the certs are stored on a disk
        :return: UUID of device"""
        return self.linux_lib.get_uuid(path)

    def cleanup(self, return_status) -> None:
        """Remove MOK from shim and OS."""
        super(LinuxUEFISecureBoot, self).cleanup(return_status)
        self._log.debug("Bringing system up to OS for clean up.")
        if not self.os.is_alive():
            self.perform_graceful_g3()
        self._log.debug(f"Removing certs from {self.path_to_certs}.")
        for cert in self.certs_list:
            self.os.execute(f"rm -f {self.path_to_certs}/{cert.file}", self.command_timeout)
        self._log.debug("Cleaning up test certificate files.")
        self.os.execute(f"rm -rf /tmp/{self.secure_boot_consts.ARTIFACTORY_SECURE_BOOT_CERTS}", self.command_timeout)
        self._log.debug(f"Restoring original OS kernel {self.current_kernel} from back up file.")
        self.os.execute(f"mv -f {self.backup_kernel} {self.current_kernel}", self.command_timeout)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UEFISecureBootCommon.main() else Framework.TEST_RESULT_FAIL)
