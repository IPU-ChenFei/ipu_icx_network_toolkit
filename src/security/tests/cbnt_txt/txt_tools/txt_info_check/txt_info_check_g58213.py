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
# treaty provisions0. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################
import sys

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.bios_util import ItpXmlCli, BootOptions
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot
from src.lib.test_content_logger import TestContentLogger
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

class TxtInfoCheck(TxtBaseTest):
    """
       Glasgow ID : 58213
       Phoenix ID : P18014071058
       This Test case execute the TxtBtgInfo/ServerTXTINFO efi tool and check the results for any errors
       pre-requisites:
       1. It should be TXT enabled and Tboot system.
       2. USB Drive should be attached to SUT
    """
    _BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"
    _TEST_CASE_ID = ["P18014071058", "txt info check"]
    _TOOL_ZIP_FILE = {"Tpm_Tools": "TPM_Tools.zip", "TXT_TOOLS": "txtinfo.zip"}
    step_data_dict = {1: {'step_details': 'Executing lsmem/lscpu/lspci command, enabling TXT BIOS Knobs'
                          'and Booting to tboot', 'expected_results': 'Verifying TXT BIOS Knobs and verifying'
                          'SUT entered to Tboot and comparing the lsmem/lscpu/lspci results'},
                      2: {'step_details': 'Boot to UEFI Shell', 'expected_results': 'Entered into UEFI Shell'},
                      3: {'step_details': ' Executing TxtBtgInfo.efi/ServerTXTINFO.efi tool in CBnT/Non-CBnT platform',
                          'expected_results': 'Check the results if any error'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of txtinfocheck

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self._test_content_logger = TestContentLogger(test_log, self._TEST_CASE_ID, self.step_data_dict)
        self._test_content_logger.start_step_logger(1)
        self._trusted_boot = TrustedBootWithTboot(test_log, arguments, cfg_opts)
        self._trusted_boot.prepare()
        self._trusted_boot.execute()
        self._test_content_logger.end_step_logger(1, return_val=True)
        super(TxtInfoCheck, self).__init__(test_log, arguments, cfg_opts)
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()
        self.previous_boot_oder = None
        self.current_boot_order = None
        self.itp_xml_cli_util = None
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(
            si_dbg_cfg, test_log)  # type: SiliconDebugProvider

    def prepare(self):
        # type: () -> None
        """
        Copying the required file for checking the TXT environment.
        Enter to uefi shell.
        """
        # Copy ServerTXTINFO and TxtBtginfo file to usb
        self._test_content_logger.start_step_logger(2)
        self.copy_file(self._TOOL_ZIP_FILE)
        #self._csp = ProviderFactory.create(self._csp_cfg, self._log)
        self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)
        self.previous_boot_oder = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Previous boot order {}".format(self.previous_boot_oder))
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._log.info("waiting for uefi shell..")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        This Function execute below steps
        1. Runs the ServerTXTINFO or TxtBtgInfo tool to check for errors
        :return: True if test is passed
        """
        try:
            self._test_content_logger.start_step_logger(3)
            usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
            self._log.info("Executing ServerTXTINFO or TxtBtgInfo tool to check for errors")
            self.txt_check_info(usb_drive_list)
            self._test_content_logger.end_step_logger(3, return_val=True)
        finally:
            self._sdp.itp.unlock()
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
            self.perform_graceful_g3()
            self._sdp.itp.unlock()
            self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """Test Cleanup"""
        if str(self.current_boot_order) != str(self.previous_boot_oder):
            self.set_boot_order(self.itp_xml_cli_util, self.previous_boot_oder)
        super(TxtInfoCheck, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TxtInfoCheck.main() else Framework.TEST_RESULT_FAIL)
