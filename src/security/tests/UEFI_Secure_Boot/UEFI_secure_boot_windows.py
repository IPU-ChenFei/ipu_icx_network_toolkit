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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.content_configuration import ContentConfiguration
from src.lib.common_content_lib import CommonContentLib


class UEFISecureBootWindows(BaseTestCase):
    """
    Glasgow ID : 49492
    Confirm that Secure Boot is enabled by checking the Secure Boot status on the local computer through Windows
    PowerShell.
    Verify the Policy version of the Secure Boot configuration through Windows PowerShell.
    Verify the UEFI variable values related to Secure Boot such as the SetupMode, SecureBoot and PK.
    Ensure coordinated events with BIOS, Secure boot, and OS (embedded) driver.
    This test case assume that cerificates are already installed on the system as per test case.
    Need to configure certificates in BIOS manually to enable secure boot and this test case will check OS only.
    """

    CONFIRM_SECURE_BOOT_CMD = "PowerShell Confirm-SecureBootUEFI"
    SECURE_BOOT_POLICY_CMD = 'PowerShell "Get-SecureBootPolicy | Format-List"'
    SECURE_BOOT_UEFI_CMD = 'PowerShell "Get-SecureBootUefi -Name PK | Format-List"'
    SECURE_BOOT_STATUS = "SECURE BOOT STATUS"
    SECURE_BOOT_POLICY = "GET SECURE BOOT POLICY"
    SECURE_BOOT_UEFI = "GET SECURE BOOT POLICY"

    def __init__(self, test_log, arguments, cfg_opts):
        """

        :param test_log: Used for error, debug and info messages.
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UEFISecureBootWindows, self).__init__(test_log, arguments, cfg_opts)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()

    def prepare(self):
        """
        Pre validate the SUT should be in Windows OS and check SUT is alive or not.
        """
        if not self._os.os_type == OperatingSystems.WINDOWS:
            log_error = "This test case only applicable for Windows system"
            raise RuntimeError(log_error)
        if not self._os.is_alive():
            raise RuntimeError("OS is not alive")

    def security_boot_status_command(self, secure_boot_command, secure_boot_check):
        """
        Get the secure boot enabled on sut using command and change the unicode to string

        :param secure_boot_command: The command execute on the SUT.
        :param secure_boot_check: execute command information.
        :return: the secure_boot_status i.e enabled or disable on the SUT and check secure boot certificates.
        """

        secure_boot_status = self._common_content_lib.execute_sut_cmd(
            secure_boot_command, secure_boot_check, self._command_timeout, None)
        return secure_boot_status.encode('utf-8')

    def execute(self):
        """
        Checking Secure boot status in command, Policy and UEFI in Windows OS.

        :return True if Secure boot is enabled in bios else False.
        """

        ret_value = []
        if "True" in self.security_boot_status_command(self.CONFIRM_SECURE_BOOT_CMD, self.SECURE_BOOT_STATUS):
            ret_value.append(True)
            self._log.info("Secure boot is enabled on SUT")
        else:
            ret_value.append(False)
            self._log.error("Secure boot is not enabled on SUT")

        # Searching secure boot "Publisher" and "Version" from shell.
        result = self.security_boot_status_command(
            self.SECURE_BOOT_POLICY_CMD, self.SECURE_BOOT_POLICY)
        if "Publisher" and "Version" in result:
            ret_value.append(True)
            self._log.info("Secure boot policy is present, command output {}".format(result))
        else:
            ret_value.append(False)
            self._log.error("Secure boot policy is not present")

        # Searching secure boot "Bytes" and "Attributes" from shell.
        data = self.security_boot_status_command(
            self.SECURE_BOOT_UEFI_CMD,
            self.SECURE_BOOT_UEFI)
        if "Bytes" and "Attributes" in data:
            ret_value.append(True)
            self._log.info('"Bytes" and "Attributes" string are present"{}'.format(data))
        else:
            ret_value.append(False)
            self._log.error('"Bytes" and "Attributes" string are not present"')
        return all(ret_value)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UEFISecureBootWindows.main() else Framework.TEST_RESULT_FAIL)
