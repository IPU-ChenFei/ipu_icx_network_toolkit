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

from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions
from src.lib.bios_util import ItpXmlCli
from src.lib.bios_util import BootOptions


class SecurityTpmCheckOsLevel(TxtBaseTest):
    """
    HPQC ID : H79538-PI_Security_TPM_check_OS_L
    Verify SHA256 algorithm on TPM 2.0, Boot SUT to UEFI shell and provision TPM 2.0 with SHA256.
    Verifies TPM2 is recognized in os level.

    """
    TEST_CASE_ID = ["H79538-PI_Security_TPM_check_OS_L"]
    step_data_dict = {1: {'step_details': 'Provision the TPM2.0 and Verify SHA256 is enabled',
                          'expected_results': 'TPM2.0 Provisioning is done and SHA256 is enabled successfully'},
                      2: {'step_details': 'Check TPM devices available',
                          'expected_results': 'TPM2 is recognized by os'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SecurityTpmCheckOsLevel

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        """
        super(SecurityTpmCheckOsLevel, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._csp = ProviderFactory.create(self._csp_cfg, test_log)
        self.itp_xml_cli_util = ItpXmlCli(test_log, self._cfg)
        self.previous_boot_oder = None
        self.current_boot_order = None

    def prepare(self):
        """
        Check if system is alive and make it alive if it is not. Enter to uefi shell.
        """
        self._test_content_logger.start_step_logger(1)
        super(SecurityTpmCheckOsLevel, self).prepare()
        # Copy Tools zip file to usb
        self.copy_file(self._TPM_TOOL_ZIP_FILE)
        self.previous_boot_oder = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Previous boot order {}".format(self.previous_boot_oder))
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._log.info("Wait till the system enter uefi shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)

    def execute(self):
        """
        This Function execute the test case
        1. check whether the system is enabled with SHA256
        2. Provision the TPM2
        3. Verifies if TPM2 is recognised by os

        :return: True if test is passed, False if failed
        """

        try:
            usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
            self.verify_sha256_and_provision_tpm(usb_drive_list)

        finally:
            # Exiting out from UEFI shell
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
            self.perform_graceful_g3()
        self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        # check TPM2 is recognized by os
        self._log.info("Verifying TPM2 is recognised by os")
        self.verifies_tpm2_active()
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        if str(self.current_boot_order) != str(self.previous_boot_oder):
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
        super(SecurityTpmCheckOsLevel, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SecurityTpmCheckOsLevel.main() else Framework.TEST_RESULT_FAIL)
