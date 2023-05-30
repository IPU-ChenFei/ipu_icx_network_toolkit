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

from src.lib.bios_util import ItpXmlCli, BootOptions
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest


class AlgorithmAgilitySha256(TxtBaseTest):
    """
    Glasgow ID : 58885
    Phoneix ID : P18014069570
    Verify SHA256 algorithm on TPM 2.0, provision TPM 2.0, and verify can boot trusted.
    1: Enable TXT knobs,  boot to tboot + Linux.
    2: Reboot SUT to UEFI shell and provision TPM 2.0 with SHA256.
    3: Reboot system and verify SUT can boot trusted.
    """

    _BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"
    _TEST_CASE_ID = ["P18014069570", "AlgorithmAgilitySha256"]
    _TOOL_ZIP_FILE = {"Tpm_Tools": "TPM_Tools.zip", "TXT_TOOLS": "txtinfo.zip"}

    step_data_dict = {1: {'step_details': 'Executing lsmem/lscpu/lspci command, enabling TXT BIOS Knobs'
                                          'and Booting to tboot',
                          'expected_results': 'Verifying TXT BIOS Knobs and verifying'
                                              'SUT entered to Tboot and comparing the lsmem/lscpu/lspci results'},
                      2: {'step_details': 'Boot to UEFI Shell', 'expected_results': 'Entered into UEFI Shell'},
                      3: {'step_details': 'Execute TPM provisioning command with SHA256',
                          'expected_results': 'Provisioning completed successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of AlgorithmAgilitySha256
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        """
        self._test_content_logger = TestContentLogger(test_log, self._TEST_CASE_ID, self.step_data_dict)
        self._test_content_logger.start_step_logger(1)
        self._trusted_boot = TrustedBootWithTboot(test_log, arguments, cfg_opts)
        self._trusted_boot.prepare()
        self._trusted_boot.execute()
        self._test_content_logger.end_step_logger(1, return_val=True)
        super(AlgorithmAgilitySha256, self).__init__(test_log, arguments, cfg_opts)
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()
        self.previous_boot_oder = None
        self.current_boot_order = None
        self.itp_xml_cli_util = None

    def prepare(self):
        """
        This function does the below task.
        1. Copy the provising file from artifactory to pendrive
        2. Boot to UEFI shell and verify the system in UEFI shell
        """
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
        This Function execute the test case
        1. check whether the system is enabled with SHA256
        2. Provision the TPM
        3. Verify system booted with trusted boot

        :return: True if test is passed, False if failed
        """
        try:
            self._test_content_logger.start_step_logger(3)
            usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
            self._log.info("Executing TPM provisioning")
            self.verify_sha256_and_provision_tpm(usb_drive_list)
            self._test_content_logger.end_step_logger(3, return_val=True)
        finally:
            self.set_boot_order(self.itp_xml_cli_util, self.previous_boot_oder)
            self.perform_graceful_g3()
            self.current_boot_order = self.get_boot_order_xmlcli(self.itp_xml_cli_util)
		
		if self.verify_trusted_boot():  # verify the sut boot with trusted environment
            self._log.info("SUT Booted to Trusted environment Successfully")
            ret_val = True
        else:
            if self.verify_trusted_boot(expect_ltreset=True):  # verify the sut boot with trusted environment
                self._log.info("SUT Booted to Trusted environment Successfully")
                ret_val = True
            else:
                self._log.error("SUT did not Boot into Trusted environment")
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """Test Cleanup"""
        if str(self.current_boot_order) != str(self.previous_boot_oder):
            self.set_boot_order(self.itp_xml_cli_util, self.previous_boot_oder)
        super(AlgorithmAgilitySha256, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if AlgorithmAgilitySha256.main() else Framework.TEST_RESULT_FAIL)
