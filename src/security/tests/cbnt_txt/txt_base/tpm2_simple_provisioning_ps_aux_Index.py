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
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.physical_control import PhysicalControlProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib import content_exceptions
from src.lib.bios_util import ItpXmlCli
from src.lib.bios_util import BootOptions
from src.lib.cbnt_constants import HashAlgorithms
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.cbnt_txt.txt_constants import TpmIndices
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest


class Tpm2SimpleProvisioningPsAuxIndex(TxtBaseTest):
    """
    HPQC ID : 79534-[Purley & BasinFalls] PI_Security_TXT_TPM2.0_Simple Provisioning [PS AUX Index]_L

    TPM 2.0 simple provisioning PS Aux Index
    1: Boot SUT to UEFI shell and provision TPM 2.0 with PS Aux Index
    """
    TEST_CASE_ID = ["H79534-[Purley & BasinFalls] PI_Security_TXT_TPM2.0_Simple Provisioning [PS AUX Index]_L"]
    WAIT_TIME_OUT = 5
    step_data_dict = {1: {'step_details': 'Boot UEFI Shell and Map usb drive', 'expected_results': 'Verifying '
                                                                                                   'SUT entered to '
                                                                                                   'UEFI Shell'},
                      2: {'step_details': ' Executed TPM2TxtProv.nsh SHA256 EXAMPLE for TPM Provision',
                          'expected_results': 'TPM Provision should complete Successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of Tpm2SimpleProvisioningPsAuxIndex

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        """
        super(Tpm2SimpleProvisioningPsAuxIndex, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._csp = ProviderFactory.create(self._csp_cfg, test_log)
        self.itp_xml_cli_util = ItpXmlCli(test_log, self._cfg)
        self.previous_boot_oder = None
        self.current_boot_order = None
        phy_cfg = cfg_opts.find(PhysicalControlProvider.DEFAULT_CONFIG_PATH)
        self._phy = ProviderFactory.create(phy_cfg, test_log)  # type: PhysicalControlProvider

    def prepare(self):
        """
        Copy TPM Provision files to SUT, Verify TPM and Enter to uefi shell.

        :raise: content_exceptions.TestFail If SUT did not enter to uefi internal shell.
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        # check if usb is connected to SUT or HOST.
        if self._phy.connect_usb_to_host(self.usb_set_time):
            self._log.info("USB Drive Is Connected To HostMachine")
            # Its Mandatory that USB To Be Connected To SUT
            if not self._phy.connect_usb_to_sut(self.usb_set_time):
                time.sleep(self.usb_set_time)
                self._log.error("USB Drive Is Not Connected To Platform(SUT)")
                raise content_exceptions.TestFail("USB Drive Is Not Connected To Platform(SUT)")

        # Copy Tools zip file to usb
        self.copy_file(self._TPM_TOOL_ZIP_FILE)
        # Verify TPM present or not
        self.verify_tpm()

        self.previous_boot_oder = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Previous boot order {}".format(self.previous_boot_oder))
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._log.info("waiting for uefi shell..")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        time.sleep(self.WAIT_TIME_OUT)
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This Function execute TPM2.0 TPM2TxtProv.nsh file to provision the TPM

        :return: True if test is passed,
        :raise: content_exceptions.TestFail if Provisioning is not done successfully
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        reset_platform_cmd = "ResetPlatformAuth.nsh SHA256 example"
        success_reset_platform = "Successfully set PlatformAuth to EMPTY"
        reset_platform_cmd_end_line = "EMPTY"
        try:
            usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
            self._log.info("Set Platform Auth to Empty using ResetPlatformAuth.nsh command")
            if not self._uefi_util_obj.execute_efi_cmd(usb_drive_list, reset_platform_cmd, success_reset_platform,
                                                       reset_platform_cmd_end_line):
                raise content_exceptions.TestFail("Platform Reset Failed!")
            self._log.info("Platform Reset successfully")

            # Provision the TPM2 PS aux index
            if not self.provision_tpm2(usb_drive_list, TpmIndices.PS, HashAlgorithms.SHA256):
                raise content_exceptions.TestFail("Provisioning for PS index has failed!")
            self._log.info("Provisioning is done for PS index Successfully")

        finally:
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
            self.perform_graceful_g3()
            self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        #  Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        if str(self.current_boot_order) != str(self.previous_boot_oder):
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
        super(Tpm2SimpleProvisioningPsAuxIndex, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if Tpm2SimpleProvisioningPsAuxIndex.main() else Framework.TEST_RESULT_FAIL)
