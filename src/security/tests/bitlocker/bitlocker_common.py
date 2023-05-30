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
import time
from dtaf_content.src.lib.content_base_test_case import ContentBaseTestCase
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib import content_exceptions
from dtaf_core.lib.exceptions import DriverIOError


class BitLockerBaseTest(ContentBaseTestCase):
    """Base class extension for bitlocker test cases which holds common arguments, functions."""
    _INTEROP_KNOBS = "collateral/interop_knobs.cfg"
    _UEFI_CONFIG_PATH = 'suts/sut/providers/uefi_shell'
    _ENCRYPTED_DRIVE = "C:"
    _ENCRYPTION_UPDATE_FREQUENCY = 5
    _REBOOT_TIMEOUT = 120
    _RESTART_DELAY = 10

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of BitLockerStartupPasswordTest
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super().__init__(test_log, arguments, cfg_opts, self._INTEROP_KNOBS)

    def prepare(self):
        """
        Pre-validating basic test requirements
        :return: None
        """
        super(BitLockerBaseTest, self).prepare()

        if self.os.os_type != OperatingSystems.WINDOWS:
            raise content_exceptions.TestUnSupportedError("This test requires Windows OS")

        if not self.encrypted_drive_exists():
            raise content_exceptions.TestUnSupportedError("This test requires C: drive")

        try:
            self.cng_log.serial.write("")
        except DriverIOError as _ex:
            raise content_exceptions.TestSetupError("Unable to write to serial. Is PuTTY open?")

        self.perform_graceful_g3()

        if not self.bitlocker_is_enabled():
            self._log.info("BitLocker encryption is disabled - This test case requires BitLocker to be enabled")
            self.enable_bitlocker()
        else:
            self._log.info("Disabling and re-enabling BitLocker to reset protectors")
            self.disable_bitlocker()
            self.enable_bitlocker()

    def cleanup(self, return_status):
        """
        Test Cleanup
        :return: None
        """
        if self.bitlocker_is_enabled():
            self.disable_bitlocker()
        super(BitLockerBaseTest, self).cleanup(return_status)

    def enable_bitlocker(self):
        """
        Enable BitLocker on the SUT
        :return: None
        :raise RuntimeError: If BitLocker Fails to enable
        """
        self._log.info("Enabling BitLocker drive encryption")
        self.run_cmd_sut(f"manage-bde -on -used {self._ENCRYPTED_DRIVE}")
        self._log.info("Performing restart to test hardware")
        self.restart_windows()
        while not self.bitlocker_encryption_complete():
            self._log.info(f"Encrypting {self._ENCRYPTED_DRIVE} Drive: {self.bitlocker_encryption_percentage()}%")
            time.sleep(self._ENCRYPTION_UPDATE_FREQUENCY)
        if not self.bitlocker_is_enabled():
            raise RuntimeError("Failed to enable BitLocker drive encryption")
        self._log.info(f"BitLocker is now enabled for drive {self._ENCRYPTED_DRIVE}")
        self.remove_bitlocker_key()

    def disable_bitlocker(self):
        """
        Disable BitLocker on the SUT
        :return: None
        :raise RuntimeError: if BitLocker Fails to disable
        """
        self._log.info("Disabling BitLocker drive encryption")
        self.run_cmd_sut(f"manage-bde -off {self._ENCRYPTED_DRIVE}")
        while not self.bitlocker_decryption_complete():
            self._log.info(f"Decrypting {self._ENCRYPTED_DRIVE} Drive: {self.bitlocker_encryption_percentage()}%")
            time.sleep(self._ENCRYPTION_UPDATE_FREQUENCY)
        self._log.info("Performing restart to ensure bitlocker disable")
        self.restart_windows()
        if self.bitlocker_is_enabled():
            raise RuntimeError("Failed to enable BitLocker drive encryption")
        self._log.info(f"BitLocker is now disabled for drive {self._ENCRYPTED_DRIVE}")

    def encrypted_drive_exists(self) -> bool:
        """
        Return whether the drive which the test will be encrypting exists
        :return: bool: if the encrypted drive exists
        """
        return 'True' == self.run_powershell_cmd_sut(f"Test-Path {self._ENCRYPTED_DRIVE}")

    def bitlocker_is_enabled(self) -> bool:
        """
        Return whether bitlocker is enabled
        :return: bool: if bitlocker is enabled
        """
        return 'FullyEncrypted' == self.run_powershell_cmd_sut(f"(Get-BitLockerVolume {self._ENCRYPTED_DRIVE})"
                                                               f".VolumeStatus")

    def bitlocker_encryption_complete(self) -> bool:
        """
        Return whether bitlocker encryption is complete
        :return: bool: if bitlocker encryption is complete
        """
        return "100" == self.bitlocker_encryption_percentage()

    def bitlocker_decryption_complete(self) -> bool:
        """
        Return whether bitlocker decryption is complete
        :return: bool: if bitlocker decryption is complete
        """
        return "0" == self.bitlocker_encryption_percentage()

    def bitlocker_encryption_percentage(self) -> str:
        """
        Return bitlocker encryption percentage
        :return: str: bitlocker encryption percentage
        """
        return self.run_powershell_cmd_sut(f"(Get-BitLockerVolume {self._ENCRYPTED_DRIVE}).EncryptionPercentage")

    def bitlocker_key_protector_type(self) -> str:
        """
        Return bitlocker key protector type
        :return: str: bitlocker key protector type
        """
        return self.run_powershell_cmd_sut(f"(Get-BitLockerVolume {self._ENCRYPTED_DRIVE}"
                                           f").KeyProtector.KeyProtectorType")

    def remove_bitlocker_key(self):
        """
        Remove the bitlocker key protector for the encrypted drive
        :return: None
        :raise: RuntimeError if key protector fails to remove
        """
        self._log.info("Removing BitLocker Key")
        self.run_powershell_cmd_sut(f"Remove-BitLockerKeyProtector -MountPoint {self._ENCRYPTED_DRIVE} -KeyProtectorId "
                                    f"(Get-BitLockerVolume {self._ENCRYPTED_DRIVE}).KeyProtector.KeyProtectorId")
        if self.bitlocker_key_protector_type() != "":
            raise RuntimeError("Failed to remove BitLocker key protector")

    def run_powershell_cmd_sut(self, command) -> str:
        """
        Runs a powershell command on the SUT
        :return: str: the command output
        :param command: command to run
        :type command: str
        """
        return self.run_cmd_sut(f'''powershell "{command}"''')

    def run_cmd_sut(self, command) -> str:
        """
        Runs a command on the SUT
        :return: str: the command output
        :param command: command to run
        :type command: str
         """
        return self._common_content_lib.execute_sut_cmd(command, command, self._command_timeout).strip('\n')

    def has_tpm(self) -> bool:
        """
        Returns whether the SUT has a tpm installed
        :return: bool: whether the SUT has a tpm installed
        """
        return "True" == self.run_powershell_cmd_sut("(Get-TPM).TpmPresent")

    def restart_windows(self) -> bool:
        """
        Restarts windows of the SUT
        :return: bool: whether the sut successfully booted into the os after reboot
        """
        try:
            self.run_cmd_sut("shutdown /r /f /t 00")
            time.sleep(self._RESTART_DELAY)
            self._common_content_lib.wait_for_os(self._REBOOT_TIMEOUT)
        except content_exceptions.TestFail:
            return False
        return True

    def write_to_serial(self, serial_input: str):
        """
        Writes characters to the serial com provider, with a short delay between each write.
        Enter is sent to serial after completion
        :return: None
        :param: serial_input: the characters to write to serial
        :type: serial_input: str
        """
        for char in serial_input:
            self.cng_log.serial.write(char)
            time.sleep(0.05)
        self.cng_log.serial.write("\r\n")
