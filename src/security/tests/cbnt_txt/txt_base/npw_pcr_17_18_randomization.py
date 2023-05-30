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
import os
from datetime import datetime, timedelta

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.lib.test_content_logger import TestContentLogger
from src.lib.dtaf_content_constants import RootDirectoriesConstants
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot


class NPWPCRRandomization(ContentBaseTestCase):
    """
       Glasgow ID : G58221.3 - NPW PCR17/18 randomization
       Boot Trusted, capture PCR 17 and 18, reboot Trusted and recapture PCR 17 and 18.
       Verify PCR 17 randomized from previous boot; verify PCR 18 randomized from previous boot.

    """
    TEST_CASE_ID = ["G58221.3", "NPW PCR17/18 randomization"]
    _DIFF_PCR_17 = "17c17"
    _DIFF_PCR_18 = "18c18 :"
    _PCR_FILE_AFTER_FIRST_BOOT = "first_boot.txt"
    _PCR_FILE_AFTER_SECOND_BOOT = "second_boot.txt"
    CMD_SET_DATE = "date --set=" + '"' + str({}) + '"'
    CMD_HW_SYNC_SYS_TO_HC = "hwclock --systohc"
    CMD_STR2 = "Hardware clock sync with system date"
    CMD_STR1 = "Increment date by 1 day"
    STEP_DATA_DICT = {
        1: {'step_details': 'Enable TXT and boot trusted',
            'expected_results': 'Enabled TXT and Verified Trusted boot'},
        2: {'step_details': 'Read out the contents of PCR17 and PCR18 and save them to the SUT',
            'expected_results': 'File named "first_boot.txt" generated with the current values of the PCRs.'},
        3: {'step_details': 'Ensure SUT booted back to Linux + Tboot after reboot',
            'expected_results': 'Successfully booted to Trusted Environment'},
        4: {'step_details': 'Read out the contents of PCR17 and PCR18 and save them to the SUT',
            'expected_results': 'File named "second_boot.txt" generated with the current values of the PCRs.'},
        5: {'step_details': 'Run the command "diff first_boot.txt second_boot.txt',
            'expected_results': 'PCR 17 and PCR 18 are different between boots).'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of NPWPCRRandomization

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(NPWPCRRandomization, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("This test is not applicable for " + self.os.os_type)
        self._txt_base = TxtBaseTest(test_log, arguments, cfg_opts)
        self._trusted_boot_obj = TrustedBootWithTboot(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        """
        1. Execute OS commands before the Tboot set.
        2. Pre-validate whether sut is configured with Tboot by get the Tboot index in OS boot order.
        3. Load BIOS defaults settings.
        4. Sets the bios knobs according to configuration file and verifies if bios knobs sets successfully.
        """
        self._test_content_logger.start_step_logger(1)
        self._trusted_boot_obj.prepare()
        self._trusted_boot_obj.execute()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Boot Trusted, capture PCR 17 and 18, reboot Trusted and recapture PCR 17 and 18.
        Verify PCR 17 different from previous boot; verify PCR 18 different from previous boot.

        :return: True if Test case pass else fail
        """
        tpm_version = self._txt_base.get_tpm_version()
        self._test_content_logger.start_step_logger(2)
        pcr_file_first_boot = self._txt_base.read_current_pcr_values(self._PCR_FILE_AFTER_FIRST_BOOT, tpm_version)
        self.os.copy_file_from_sut_to_local(RootDirectoriesConstants.LINUX_ROOT_DIR + self._PCR_FILE_AFTER_FIRST_BOOT,
                                            os.path.join(self.log_dir,
                                                         self._PCR_FILE_AFTER_FIRST_BOOT))
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self._log.info("Reboot back to Linux + Tboot, ensure it still booted trusted")
        # Setting the Date and Time in SUT
        self._common_content_lib.set_datetime_on_sut()
        self._log.info("SUT time is successfully set to : {}".format(datetime.now()))
        # Adding 1 day to the current date
        current_date_plus_1 = datetime.now() + timedelta(days=1)
        self._common_content_lib.execute_sut_cmd(self.CMD_SET_DATE.format(current_date_plus_1), self.CMD_STR1,
                                                 self._command_timeout)
        self._log.info("Run hwclock --systohc command to sync hardware clock with the system clock")
        self._common_content_lib.execute_sut_cmd(self.CMD_HW_SYNC_SYS_TO_HC, self.CMD_STR2, self._command_timeout)
        self._log.info("SUT Date is successfully incremented by 1 day")
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)

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

        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        pcr_file_second_boot = self._txt_base.read_current_pcr_values(self._PCR_FILE_AFTER_SECOND_BOOT, tpm_version)
        self.os.copy_file_from_sut_to_local(RootDirectoriesConstants.LINUX_ROOT_DIR + self._PCR_FILE_AFTER_SECOND_BOOT,
                                            os.path.join(self.log_dir,
                                                         self._PCR_FILE_AFTER_SECOND_BOOT))
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        diff_command = "diff {} {}".format(pcr_file_first_boot.strip(), pcr_file_second_boot.strip())
        self._log.debug("command : {}".format(diff_command))
        diff_output = self.os.execute(diff_command, self._command_timeout)
        self._log.debug("stdout : {}".format(diff_output.stdout))
        self._log.debug("stderr : {}".format(diff_output.stderr))

        if self._DIFF_PCR_18 not in diff_output.stdout and self._DIFF_PCR_17 not in diff_output.stdout:
            raise content_exceptions.TestFail("Either PCR 17 or PCR18 did not show up after the tboot")
        self._log.info("PCR 17 and PCR 18 Readings are not identical between boots as expected!")
        self._test_content_logger.end_step_logger(5, return_val=True)

        if not ret_val:
            log_error = "PCR 17 and PCR 18 Readings are identical between boots"
            self._log.error(log_error)
            raise content_exceptions.TestFail(log_error)

    def cleanup(self, return_status):  # type: (bool) -> None
        current_date = datetime.now()
        self._common_content_lib.execute_sut_cmd(self.CMD_SET_DATE.format(current_date), self.CMD_STR1,
                                                 self._command_timeout)
        self._common_content_lib.execute_sut_cmd(self.CMD_HW_SYNC_SYS_TO_HC, self.CMD_STR2, self._command_timeout)
        self._log.info("SUT Date is set to today's date successfully ")
        super(NPWPCRRandomization, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if NPWPCRRandomization.main() else Framework.TEST_RESULT_FAIL)
