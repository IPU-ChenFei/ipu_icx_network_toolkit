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
from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.dtaf_content_constants import RootDirectoriesConstants
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot


class PWPCRNoRandomization(ContentBaseTestCase):
    """
       Glasgow ID : G58222.2 - Debug, PW PCR 17/18 no randomization
       Boot Trusted, capture PCR 17 and 18, reboot Trusted and recapture PCR 17 and 18.
       Verify PCR 17 same from previous boot; verify PCR 18 same from previous boot.

    """
    TEST_CASE_ID = ["G58222.2 - Debug, PW PCR 17/18 no randomization"]
    _DIFF_PCR_17 = "17c17"
    _DIFF_PCR_18 = "18c18"
    _PCR_FILE_AFTER_FIRST_BOOT = "first_boot.txt"
    _PCR_FILE_AFTER_SECOND_BOOT = "second_boot.txt"
    _FILE_EXT = ".txt"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of PWPCRNoRandomization

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(PWPCRNoRandomization, self).__init__(test_log, arguments, cfg_opts)
        self._txt_base = TxtBaseTest(test_log, arguments, cfg_opts)
        self._trusted_boot_obj = TrustedBootWithTboot(test_log, arguments, cfg_opts)

    def prepare(self):
        """
        1. Execute OS commands before the Tboot set.
        2. Pre-validate whether sut is configured with Tboot by get the Tboot index in OS boot order.
        3. Load BIOS defaults settings.
        4. Sets the bios knobs according to configuration file and verifies if bios knobs sets successfully.
        """
        self._trusted_boot_obj.prepare()
        self._trusted_boot_obj.execute()

    def execute(self):
        """
        Boot Trusted, capture PCR 17 and 18, reboot Trusted and recapture PCR 17 and 18.
        Verify PCR 17 same from previous boot; verify PCR 18 same from previous boot.

        :return: True if Test case pass else fail
        """
        tpm_version = self._txt_base.get_tpm_version()
        pcr_file_first_boot = self._txt_base.read_current_pcr_values(self._PCR_FILE_AFTER_FIRST_BOOT, tpm_version)
        self._common_content_lib.copy_log_files_to_host(self.log_dir, RootDirectoriesConstants.LINUX_ROOT_DIR, self._FILE_EXT)
        self._log.info("Reboot back to Linux + Tboot, ensure it still booted trusted")
        self.tboot_index = self._txt_base.get_tboot_boot_position()  # Get the Tboot_index from grub menu entry
        self._txt_base.set_default_boot_entry(self.tboot_index)
        self._txt_base.verify_sut_booted_in_tboot_mode(self.tboot_index)  # verify if the system booted in Trusted mode.
        self.perform_graceful_g3()
        if self._txt_base.verify_trusted_boot():  # verify the sut boot with trusted environment
            self._log.info("SUT Booted to Trusted environment Successfully")
            ret_val = True
        else:
            if self._txt_base.verify_trusted_boot(expect_ltreset=True):  # verify the sut boot with trusted environment
                self._log.info("SUT Booted to Trusted environment Successfully")
                ret_val = True
            else:
                log_error = "SUT did not Boot into Trusted environment"
                self._log.error(log_error)
                raise content_exceptions.TestFail(log_error)

        pcr_file_second_boot = self._txt_base.read_current_pcr_values(self._PCR_FILE_AFTER_SECOND_BOOT, tpm_version)
        self._common_content_lib.copy_log_files_to_host(self.log_dir,RootDirectoriesConstants.LINUX_ROOT_DIR, self._FILE_EXT)
        diff_command = "diff {} {}".format(pcr_file_first_boot.strip(), pcr_file_second_boot.strip())
        self._log.debug("command : {}".format(diff_command))
        diff_output = self.os.execute(diff_command, self._command_timeout)
        self._log.debug("stdout : {}".format(diff_output.stdout))
        self._log.debug("stderr : {}".format(diff_output.stderr))
        if self._DIFF_PCR_17 in diff_output.stdout :
            self._log.error("PCR 17 should not show up in the diff! Should be identical between boots")
            self._log.error(
                "The PCRs which are not identical between Boots are as follows : {} ".format(diff_output.stdout))
            ret_val = False
        elif self._DIFF_PCR_18 in diff_output.stdout:
            self._log.error("PCR 17 should not show up in the diff! Should be identical between boots")
            self._log.error(
                "The PCRs which are not identical between Boots are as follows : {} ".format(diff_output.stdout))
            ret_val = False
        else:
            self._log.info("PCR 17 and PCR 18 Readings are identical between boots")
        return ret_val


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PWPCRNoRandomization.main() else Framework.TEST_RESULT_FAIL)
