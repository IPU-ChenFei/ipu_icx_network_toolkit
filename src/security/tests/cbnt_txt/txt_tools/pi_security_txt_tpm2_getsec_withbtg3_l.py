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
import sys

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from src.lib import content_exceptions
from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_common import BootGuardValidator

from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.lib.test_content_logger import TestContentLogger
from src.lib.bios_util import ItpXmlCli
from src.lib.bios_util import BootOptions


class SystemBootSecretFlagWithBTG3(TxtBaseTest):
    """
    HPQC ID : H101224-PI_Security_TXT_TPM2.0_Getsec_withBTG3_L
    PHOENIX Id : 18016910180-PI_Security_TXT_TPM2.0_Getsec_withBTG3_L

    This test case is to verify if system boot with secrets flag set with below procedure:
    1.Enable Bios knobs, Verify SHA256 algorithm on TPM 2.0, provision TPM 2.0
    2.Execute SENTER with the getsec EFI tool to confirm that the platform and
      ACM can enter a trusted environment.
    3.Execute the Server Secrets64.efi -s to assert secret flag
    4.Reset the platform and enter to TXT environment and execute Server Secrets64.efi -n to de-assert secret flag
    5.Verify Boot Guard Profile 3
    """

    _BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"
    _TEST_CASE_ID = ["H101224","PI_Security_TXT_TPM2.0_Getsec_withBTG3_L", "18016910180"]
    _EXIT_TXT_ENV_FLAG = False
    step_data_dict = {1: {'step_details': 'Enable the Bios knobs for TXT',
                          'expected_results': 'All TXT knobs are enabled properly'},
                      2: {'step_details': 'Provision the TPM2.0 and Verify SHA256 is enabled',
                          'expected_results': 'TPM2.0 Provisioning is done and SHA256 is enabled successfully'},
                      3: {'step_details': 'Execute SENTER with the getsec EFI tool',
                          'expected_results': 'System entered the TXT environment successfully'},
                      4: {'step_details': 'Execute the Server getsec64-t1.efi -s to assert secret flag',
                          'expected_results': 'Secret flag asserted successfully'},
                      5: {'step_details': 'Perform a power cycle',
                          'expected_results': 'Power cycle is done successfully'},
                      6: {'step_details': 'Execute SENTER with the getsec EFI tool',
                          'expected_results': 'System entered the TXT environment successfully'},
                      7: {'step_details': 'Execute the Server getsec64-t1.efi -n to de-assert secret flag',
                          'expected_results': 'Secret flag de-asserted successfully'},
                      8: {'step_details': 'Verification of MSR_BOOT_GUARD_SACM_INFO should match the excepted value '
                        'TPM1.2: 0x70000006B/0xF0000006B ,TPM2.0: 0x70000006D/0xF0000006D, PTT on HCI: '
                                          '0x70000006F/0xF0000006F', 'expected_results': 'matched the excepted'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SystemBootSecretFlagWithBTG3

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        """
        super(SystemBootSecretFlagWithBTG3, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        self._test_content_logger = TestContentLogger(test_log, self._TEST_CASE_ID, self.step_data_dict)
        self._bootguard_common_obj = BootGuardValidator(test_log, arguments, cfg_opts)
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.previous_boot_oder = None
        self.current_boot_order = None
        self.itp_xml_cli_util = None

    def prepare(self):
        """
        Loading BIOS defaults settings.
        Sets the bios knobs according to configuration file and verifies if bios knobs sets successfully.
        Enter to uefi shell.
        """
        self._test_content_logger.start_step_logger(1)
        super(SystemBootSecretFlagWithBTG3, self).prepare()

        # Copy Tools zip file to usb
        self.copy_file(self._TPM_TOOL_ZIP_FILE)
        self.enable_and_verify_bios_knob()  # Enable and verify Bios knobs
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self._csp = ProviderFactory.create(self._csp_cfg, self._log)
        self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)
        self.previous_boot_oder = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Previous boot order {}".format(self.previous_boot_oder))
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)

    def execute(self):
        """
        This Function execute the test case
        1. check whether the system is enabled with SHA256
        2. Provision the TPM2.0
        3. Runs the getsec EFI tool to enter in TXT environment
        3. Execute the Server getsec64-t1.efi -s to assert secret flag
        4. Reset the platform and getsec EFI tool to enter in TXT environment
        5. execute Server getsec64-t1.efi -n to de-assert secret flag
        6. Verify Profile 3 MSR value

        :return: True if test is passed
        """

        try:
            self._log.info("executing the get usb drive list command")
            usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
            self._log.info("Checking SHA256 is enabled and provisioning the TPM")
            self.verify_sha256_and_provision_tpm(usb_drive_list)
            self._test_content_logger.end_step_logger(2, return_val=True)

            self._test_content_logger.start_step_logger(3)
            self._log.info("Executing getsec64 tool to check the TXT environment")
            self.execute_getsec_uefi_tool(usb_drive_list, self._EXIT_TXT_ENV_FLAG)
            self._test_content_logger.end_step_logger(3, return_val=True)

            self._test_content_logger.start_step_logger(4)
            self._log.info("Executing ServerSecrets tool to check secret bit is asserted")
            self.verify_secret_flag_assert(usb_drive_list)
            self._test_content_logger.end_step_logger(4, return_val=True)

            self._test_content_logger.start_step_logger(5)
            self._log.info("Performing reset of platform")
            self._uefi_obj.warm_reset()
            self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
            self._test_content_logger.end_step_logger(5, return_val=True)

            self._test_content_logger.start_step_logger(6)
            self._log.info("Executing getsec64 tool to check the TXT environment")
            self.execute_getsec_uefi_tool(usb_drive_list, self._EXIT_TXT_ENV_FLAG)
            self._test_content_logger.end_step_logger(6, return_val=True)

            self._test_content_logger.start_step_logger(7)
            self._log.info("Executing ServerSecrets tool to check secret bit is De-asserted")
            self.verify_secret_flag_de_assert(usb_drive_list)

        finally:
            # Exiting out from UEFI shell
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
            self.perform_graceful_g3()
            self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
            self._test_content_logger.end_step_logger(7, return_val=True)

        self._test_content_logger.start_step_logger(8)
        if not self._bootguard_common_obj.verify_profile_3():
            raise content_exceptions.TestFail("Bootguard profile 3 verification failed")
        self._test_content_logger.end_step_logger(8, return_val=True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        if str(self.current_boot_order) != str(self.previous_boot_oder):
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
        super(SystemBootSecretFlagWithBTG3, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SystemBootSecretFlagWithBTG3.main() else Framework.TEST_RESULT_FAIL)
