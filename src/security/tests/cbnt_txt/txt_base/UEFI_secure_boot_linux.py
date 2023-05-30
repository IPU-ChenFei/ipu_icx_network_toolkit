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
import os
from datetime import datetime

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.content_configuration import ContentConfiguration
from src.lib.common_content_lib import CommonContentLib


class UEFISecureBootLinux(BaseTestCase):
    """
    Glasgow ID : 49491
    Test Secure boot on Linux with Secure certificate.
    Ensure coordinated events with BIOS, Secure boot, and OS (embedded) driver.
	This test case assume that cerificates are already installed on the system as per test case.
	Need to configure certificates in BIOS manually to enable secure boot and this test case will check OS only.
	"""

    CMD_GET_SECURE_BOOT_STATUS = "mokutil --sb-state"
    CMD_SECURE_BOOT_DELETE_LOG = "rm -f /var/log/messages"
    CMD_SECURE_BOOT_ENABLED_LOG = "grep 'Secure boot enabled' /var/log/messages"
    CMD_SECURE_BOOT_KEYS_CERTIFICATES = "mokutil --list-enrolled"
    WAIT_TIME_300_SEC = 300

    def __init__(self, test_log, arguments, cfg_opts):
        """

        :param test_log: Used for error, debug and info messages.
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UEFISecureBootLinux, self).__init__(test_log, arguments, cfg_opts)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()

    def prepare(self):
        """
        Pre validate the SUT should be in Linux OS and check SUT is alive or not.
        """
        if not self._os.os_type == OperatingSystems.LINUX:
            log_error = "This test case only applicable for Linux system"
            self._log.error(log_error)
            raise RuntimeError(log_error)
        if not self._os.is_alive():
            self._log.error("System is not alive")
            raise RuntimeError("OS is not alive")
        self._log.info("Delete the old OS messages log ")
        self._common_content_lib.execute_sut_cmd(
            self.CMD_SECURE_BOOT_DELETE_LOG, "SECURE BOOT LOGS DELETE", self._command_timeout, None)
        self._os.reboot(self._reboot_timeout)

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
        Checking Secure boot status in command, logs and certificates in linux OS.

        :return True if Secure boot is enabled in bios else False.
        """

        # Fetching data from shell command "mokutil --sb-state".

        start = datetime.now()
        while (datetime.now() - start).seconds < self.WAIT_TIME_300_SEC:
            if os.path.exists(self.CMD_SECURE_BOOT_ENABLED_LOG):
                break
            else:
                continue

        secure_boot_status = "SECURE BOOT STATUS"
        secure_boot_enabled_log = "SECURE BOOT ENABLED LOG"
        secure_boot_keys_certificates = "SECURE BOOT KEYS CERTIFICATES"

        ret_value = []
        if "enabled" in self.security_boot_status_command(self.CMD_GET_SECURE_BOOT_STATUS, secure_boot_status):
            ret_value.append(True)
            self._log.info("Secure boot is enabled on SUT")
        else:
            ret_value.append(False)
            self._log.error("Secure boot is not enabled on SUT")

        while True:
            time.sleep(self.WAIT_TIME_300_SEC)
            break

        # Fetching secure boot string from shell command in messages.
        if "Secure boot enabled" in self.security_boot_status_command(
                self.CMD_SECURE_BOOT_ENABLED_LOG, secure_boot_enabled_log):
            ret_value.append(True)
            self._log.info("Secure boot is enabled in log messages")
        else:
            ret_value.append(False)
            self._log.error("Secure boot is not enabled in log messages")

        # Searching secure boot "certificates" and "signature algorithm" from shell.
        data = self.security_boot_status_command(
            self.CMD_SECURE_BOOT_KEYS_CERTIFICATES,
            secure_boot_keys_certificates)
        if "Certificate" in data and "Signature Algorithm" in data:
            ret_value.append(True)
            self._log.info('"Certificate" and "Signature Algorithm" string are present"')

        else:
            ret_value.append(False)
            self._log.error('"Certificate" and "Signature Algorithm" string are not present"')
        return all(ret_value)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UEFISecureBootLinux.main() else Framework.TEST_RESULT_FAIL)
