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

from src.lib.bios_util import BootOptions
from src.lib.bios_util import ItpXmlCli
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest


class SecurityTpmCheckBiosUEFI(TxtBaseTest):
    """
    HPQC ID : H79537-PI_Security_TPM_check_Bios_UEFI
    Verify SHA256 algorithm on TPM 2.0,
    Reboot SUT to UEFI shell and provision TPM 2.0 with SHA256.
    """
    TEST_CASE_ID = ["H79537", "PI_Security_TPM_check_Bios_UEFI"]
    step_data_dict = {1: {'step_details': 'Check TPM 2.0 is shown as a device',
                          'expected_results': 'Current TPM Device is TPM 2.0'},
                      2: {'step_details': 'Provision the TPM2.0 and Verify SHA256 is enabled',
                          'expected_results': 'TPM2.0 Provisioning is done and SHA256 is enabled successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SecurityTpmCheckBiosUEFI
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        """
        super(SecurityTpmCheckBiosUEFI, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self.previous_boot_oder = None
        self.current_boot_order = None
        self.itp_xml_cli_util = None

    def prepare(self):
        # type: () -> None
        """
        Check the weather system is alive or not make it alive and Enter to uefi shell.

        :raise: RuntimeError If SUT did not enter to UEFI internal shell.
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        # Copy Tools zip file to usb
        self.copy_file(self._TPM_TOOL_ZIP_FILE)
        # Verify TPM present or not
        self.verify_tpm()

        self._csp = ProviderFactory.create(self._csp_cfg, self._log)
        self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)
        self.previous_boot_oder = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Previous boot order {}".format(self.previous_boot_oder))
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This Function execute the test case
        1. check whether the system is enabled with SHA256
        2. Provision the TPM

        :return: True if test is passed, False if failed
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        try:
            usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
            self.verify_sha256_and_provision_tpm(usb_drive_list)

        finally:
            # Exiting out from UEFI shell
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
            self.perform_graceful_g3()
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        if str(self.current_boot_order) != str(self.previous_boot_oder):
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
        super(SecurityTpmCheckBiosUEFI, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SecurityTpmCheckBiosUEFI.main() else Framework.TEST_RESULT_FAIL)
