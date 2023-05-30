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

from src.lib.bios_util import ItpXmlCli
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest


class UefiGetsecCheck(TxtBaseTest):
    """
    Glasgow ID : 58214
    Phoneix ID : P18014070682
    Execute SENTER and SEXIT with the getsec EFI tool to confirm that the platform and
    ACM can enter a trusted environment.

    """
    _BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"
    _TEST_CASE_ID = ["P18014070682", "getsec check"]
    _TOOL_ZIP_FILE = {"Tpm_Tools": "TPM_Tools.zip", "TXT_TOOLS": "txtinfo.zip"}
    _EXIT_TXT_ENV_FLAG = True
    step_data_dict = {1: {'step_details': 'Enable the Bios knobs for TXT',
                          'expected_results': 'All TXT knobs are enabled properly'},
                      2: {'step_details': 'Boot to UEFI Shell', 'expected_results': 'Entered into UEFI Shell'},
                      3: {'step_details': 'Execute SENTER and SEXIT with the getsec EFI tool',
                          'expected_results': 'System entered the TXT environment successfully and '
                                              'System has exited TXT Environment message should be displayed'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of UefiGetsecCheck

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        """
        super(UefiGetsecCheck, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        self._test_content_logger = TestContentLogger(test_log, self._TEST_CASE_ID, self.step_data_dict)
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()
        self.previous_boot_oder = None
        self.current_boot_order = None
        self.itp_xml_cli_util = None

    def prepare(self):
        """
        Copying the required file for checking the TXT environment.
        Pre-validating whether sut is configured with tboot by getting the tboot index in OS boot order.
        Loading BIOS defaults settings.
        Sets the bios knobs according to configuration file and verifies if bios knobs sets successfully.
        Enter to uefi shell.
        """
        self._test_content_logger.start_step_logger(1)
        super(UefiGetsecCheck, self).prepare()

        self.copy_file(self._TOOL_ZIP_FILE)
        self.enable_and_verify_bios_knob()  # Enable and verify Bios knobs
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._test_content_logger.start_step_logger(2)
        self._csp = ProviderFactory.create(self._csp_cfg, self._log)
        self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)
        self.previous_boot_oder = self.get_boot_order_xmlcli(self.itp_xml_cli_util)
        self.set_uefi_shell_bootorder(self.itp_xml_cli_util)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._log.info("waiting for uefi shell..")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        This Function execute below steps
        1. Runs the getsec EFI tool
        2. Verifies whether the system entered TXT Environment
        3. Verifies whether the system exited TXT Environment
        :return: True if test is passed
        """
        try:
            self._test_content_logger.start_step_logger(3)
            usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
            self._log.info("Executing getsec64 tool to check the system entered to TXT environment")
            self.execute_getsec_uefi_tool(usb_drive_list, self._EXIT_TXT_ENV_FLAG)
            self._test_content_logger.end_step_logger(3, return_val=True)
        finally:
            self.set_boot_order(self.itp_xml_cli_util, self.previous_boot_oder)
            self.perform_graceful_g3()
            self.current_boot_order = self.get_boot_order_xmlcli(self.itp_xml_cli_util)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """Test Cleanup"""
        if str(self.current_boot_order) != str(self.previous_boot_oder):
            self.set_boot_order(self.itp_xml_cli_util, self.previous_boot_oder)
        super(UefiGetsecCheck, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UefiGetsecCheck.main() else Framework.TEST_RESULT_FAIL)
