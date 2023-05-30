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
# treaty provisions. No part of the Material may be used, copied, reproduced,
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
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.lib.bios_util import ItpXmlCli
from src.lib.bios_util import BootOptions
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest


class ExecuteServerPCRDump(TxtBaseTest):
    """
    HPQC ID : H79539-PI_Security_TPM2.0_PCR_value_check_General_UEFI

    This test case is to verify the TPM PCR 0 value after executing
    the ServerPCRDumpTPM2.efi is same.
    1. Verify the TPM2.0 device is active.
    2. Navigate to UEFI shell.
    3. Executes command  ServerPCRDumpTPM2.efi on UEFI shell.
    4. Compare TPM PCR0 value from output result before and after reset.
    5. Navigates to Os.
    """
    TEST_CASE_ID = ["H79539-PI_Security_TPM2.0_PCR_value_check_General_UEFI"]
    STEP_DATA_DICT = {1: {'step_details': 'Verify TPM2.0 Device is active and copy the ServerPCRDumpTPM2.efi from '
                                          'host to usb ',
                          'expected_results': 'ServerPCRDumpTPM2.efi is moved to usb'},
                      2: {'step_details': ' Navigate to UEFI shell and Executed ServerPCRDumpTPM2.efi '
                                          ' do reset and repeat for another reset and collect results',
                          'expected_results': 'Verify TPM PCR0 values for both the output result should be same'}}

    TPM_SERVERPCRDUMP_ZIP_FILE = "ServerPCRDumpTPM2.zip"
    TPM_SERVER_DIR = "TPM_SERVER_DUMP"
    PCR_NUM = "TPM PCR 0"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of ExecuteServerPCRDump.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(ExecuteServerPCRDump, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.previous_boot_oder = None
        self.current_boot_order = None
        self.itp_xml_cli_util = None

    def prepare(self):  # type: () -> None
        self._test_content_logger.start_step_logger(1)
        super(ExecuteServerPCRDump, self).prepare()
        # check TPM2 is recognized by os
        self._log.info("Verifying TPM2 is recognised by os")
        self.verifies_tpm2_active()
        # Copy zip file to usb
        zip_file_path = self._common_content_lib.copy_zip_file_to_linux_sut(self.TPM_SERVER_DIR, self.TPM_SERVERPCRDUMP_ZIP_FILE)
        self._copy_usb.copy_file_from_sut_to_usb(self._common_content_lib,
                                                               self._common_content_configuration,
                                                               zip_file_path, self.TPM_SERVER_DIR)
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This function navigates to UEFI shell and  executes the ServerPCRDumpTPM2.efi, collect the output.
        compare TPM PCR 0: value in before and after reset.

        :raise: content exception id PCR 0 value is not same
        :return: True if test case pass
        """

        self._test_content_logger.start_step_logger(2)
        self._csp = ProviderFactory.create(self._csp_cfg, self._log)
        self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)
        self.previous_boot_oder = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Previous boot order {}".format(self.previous_boot_oder))
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)

        before_reset_result = self.get_pcrdump_from_uefi(self._EXECUTE_SERVERPCRDUMP_TPM2, self.TPM_SERVER_DIR)
        self._uefi_util_obj.perform_uefi_warm_reset()
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        after_reset_result = self.get_pcrdump_from_uefi(self._EXECUTE_SERVERPCRDUMP_TPM2, self.TPM_SERVER_DIR)

        # Exiting out from UEFI shell
        self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
        self.perform_graceful_g3()
        self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()

        # Verify PCR 0 is equal
        if not self.verify_pcr_values_equal(before_reset_result, after_reset_result, self.PCR_NUM):
            raise content_exceptions.TestFail("PCR {} values are not same as expected".format(self.PCR_NUM))
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        if str(self.current_boot_order) != str(self.previous_boot_oder):
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
        super(ExecuteServerPCRDump, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ExecuteServerPCRDump.main()
             else Framework.TEST_RESULT_FAIL)
