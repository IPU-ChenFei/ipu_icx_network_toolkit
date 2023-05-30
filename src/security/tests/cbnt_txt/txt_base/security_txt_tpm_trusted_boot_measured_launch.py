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

from dtaf_core.lib.dtaf_constants import Framework

from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.lib import content_exceptions
from src.lib.bios_util import ItpXmlCli, PlatformConfigReader


class SecurityTxtTpm2TbootMearsuredLaunch(TxtBaseTest):
    """
    HPQC ID : H2026
    Check TPM 2.0 module, Reboot SUT to UEFI shell and provision TPM 2.0 with SHA256.
    Enable TXT knobs in BIOS and verify all knobs are set properly
    verify the system booted in Trusted mode or not
    """
    BIOS_CONFIG_FILE = "security_txt_bios_knobs_enable.cfg"
    TEST_CASE_ID = ["H2026"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SecurityTxtTpm2TbootMearsuredLaunch
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None

        """
        self.txt_bios_enable_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            self.BIOS_CONFIG_FILE)
        super(SecurityTxtTpm2TbootMearsuredLaunch, self).__init__(test_log, arguments,
                                                                      cfg_opts, self.txt_bios_enable_path)
        self.platform_xmlci_config = ItpXmlCli(test_log, self._cfg)
        self.platform_config_read = PlatformConfigReader(self.platform_xmlci_config.get_platform_config_file_path(),
                                                         test_log=test_log)

    def prepare(self):
        # type: () -> None
        """
        This function verify the tpm module, copy tools zip file to usb and check sut entered into uefi shell or not

        :raise: content_exceptions If SUT did not enter to UEFI internal shell.
        """

        # Verify The "Current TPM Device is TPM 2.0"
        self._log.info("verify the TPM 2.0 module")
        tpm_device = self.platform_config_read.get_current_tpm_device()
        if tpm_device != self._TPM_DEVICE:
            raise content_exceptions.TestFail("Failed to verify TPM Device, Expected={}, Actual={}".format(
                self._TPM_DEVICE, tpm_device))

        # Copy Tools zip file to usb
        self._log.info("Copy Tools zip file to usb")
        self.copy_file(self._TPM_TOOL_ZIP_FILE)

        if not self._uefi_util_obj.enter_uefi_shell():
            raise content_exceptions.TestFail("SUT did not enter to UEFI Internal Shell")

    def execute(self):
        """
        This Function execute the test case
        1. Provision the TPM
        2. set the bios knobs and verify the bios is set properly
        3. Verify the system booted in trusted boot mode

        :return: True if test is passed, False if failed
        """
        try:
            usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
            self._log.info("Checking SHA256 is enabled and provision the TPM2")
            self.verify_sha256_and_provision_tpm(usb_drive_list)

        finally:
            # Exiting out from UEFI shell
            self.perform_graceful_g3()
        self._bios_util.load_bios_defaults()  # To set Bios knobs to default.
        self._bios_util.set_bios_knob()  # To set the bios knob
        self._uefi_util_obj.graceful_sut_ac_power_on()
        self._os.wait_for_os(self._reboot_timeout)
        self._log.info("Verify the Bios knob value set")
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set

        t_boot_index = self.get_tboot_boot_position()  # Get the t_boot_index from grub menu entry
        self.set_default_boot_entry(t_boot_index)  # Set trusted boot as default boot
        self._os.reboot(self._reboot_timeout)
        self.verify_sut_booted_in_tboot_mode(t_boot_index)  # verify if the system booted in Trusted mode.
        # verify the sut boot with trusted env
        self._log.info("Verify the system booted in trusted boot mode")
        if not self.verify_trusted_boot():
            if not self.verify_trusted_boot(expect_ltreset=True):
                raise content_exceptions.TestFail("SUT not booted to trusted environment")
        self._log.info("SUT booted to trusted environment successfully")

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        # super(SecurityTxtTpm2TbootMearsuredLaunch, self).cleanup(return_status)
        self.set_default_boot_entry(self._DEFAULT_ENTRY)  # Set system to default normal os boot
        self._os.reboot(self._reboot_timeout)
        super(SecurityTxtTpm2TbootMearsuredLaunch, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS
             if SecurityTxtTpm2TbootMearsuredLaunch.main() else Framework.TEST_RESULT_FAIL)
