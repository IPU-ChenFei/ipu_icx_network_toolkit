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
import re
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.dc_power import DcPowerControlProvider
from src.lib.mirror_mode_common import MirrorCommon


class MemoryMirroring(TxtBaseTest):
    """
    Glasgow ID : 59139
    This test is to Configure memory mirror, boot trusted, then do a surprise reset and verify recovery of SUT
    """
    _BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable_with_mirror.cfg"
    _GLASGOW_ID = "59139"
    _FILE_NAME = "59139_cscript_log.txt"
    _MIRROR_MODE = 0x1
    _ERROR_EXP = r"([0-9]*)\s*Errors|\s*detected\s*.*"
    _COUNTER = 2

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of MemoryMirroring

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(MemoryMirroring, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        self.tboot_index = None
        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider
        dc_cfg = cfg_opts.find(DcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._dc = ProviderFactory.create(dc_cfg, test_log)  # type: DcPowerControlProvider
        self._klaxon = self._cscripts.get_cscripts_utils().get_klaxon_obj()
        self._mirror_common = MirrorCommon(self._log, self._cscripts, self._sdp)
        self._log_file_path = self._common_content_lib.get_log_file_path(self._GLASGOW_ID, self._FILE_NAME)

    def prepare(self):
        # type: () -> None
        """
        Pre-validating whether sut is configured with tboot by getting the tboot index in OS boot order
        Loading BIOS defaults settings.
        Sets the bios knobs according to configuration file and verifies if bios knobs sets successfully.

        :return: None
        """
        self.tboot_index = self.get_tboot_boot_position()  # Get the tboot_index from grub menu entry
        self.set_default_boot_entry(self.tboot_index)  # Set tboot as default boot and reboot
        self._bios_util.load_bios_defaults()  # To set Bios knobs to default.
        self._bios_util.set_bios_knob()  # To set the bios knob setting
        self._os.reboot(self._reboot_timeout)  # To apply Bios changes
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set

    def parse_error(self):
        """
        This function is to Parse cscript logs and checks whether there is any unexplained error exist

        :raise : OSError, IOError Exception is raised if any error has occurred during reading the cscript log file
        :return: True is any unexplained error has occurred else False
        """
        error_flag = False
        try:
            with open(self._log_file_path, "r") as log_file:  # Open the cscript lof file for checking any error
                log_details = log_file.read()
                expected_error = re.findall(self._ERROR_EXP, log_details)
                actual_experienced_error = [string for string in expected_error if string != ""]  # filter empty strings
                if actual_experienced_error:
                    for line in actual_experienced_error:
                        if int(line) > 0:
                            # Capture the error log information in test case log file
                            self._log.info("Start of m2mem errors details")
                            self._log.info("Output of failed log is: '{}'".format(log_details))
                            self._log.info("End of m2mem errors details")
                            error_flag = True
                            break

        except (OSError, IOError) as e:
            self._log.error("Error in reading file due to exception '{}'".format(e))
            raise e
        if error_flag:
            log_error = "System has experienced some unexplained errors"
            self._log.error(log_error)
        else:
            self._log.info("No unexplained errors detected ")
        return error_flag

    def check_system_error(self):
        """
        This function is to run commands to check any unexplained errors exist.

        :return: True is any unexplained error has occurred else False
        """
        error_flag = False
        self._log.info("Checking the system errors")
        self._sdp.start_log(self._log_file_path, "w")  # Opening the Cscripts Log File to log the output
        self._klaxon.m2mem_errors()
        self._sdp.stop_log()  # CLosing the Cscripts Log File
        if self.parse_error():  # parsing error for checking if any error detected or not
            error_flag = True
        self._sdp.start_log(self._log_file_path, "w")  # Opening the Cscripts Log File to log the output
        self._klaxon.imc_errors()
        self._sdp.stop_log()  # CLosing the Cscripts Log File
        if self.parse_error():  # parsing error for checking if error detected or not
            error_flag = True

        return error_flag

    def verify_mirror_mode_enabled(self):
        """
        This function checks whether mirror mode is enabled.

        :return : True if mirror mode is enable else false

        """
        mirror_enable = False
        self._log.info("Verify if Mirror Mode is Successfully Enabled")
        mirror_mode = self._mirror_common.get_mirror_status_registers()
        if mirror_mode == self._MIRROR_MODE:
            self._log.info("Mirror mode has been successfully enabled")
            mirror_enable = True
        else:
            self._log.error("Mirror Mode is Not Enabled")
        return mirror_enable

    def execute(self):
        """
        This function is used to check SUT boot to trusted environment.
        DO surprise reset and Then again verifies recovery by checking whether the SUT boot trusted.

        :return: True if Test case pass else fail
        """
        ret_val = False
        self.verify_sut_booted_in_tboot_mode(self.tboot_index)  # Check if tboot is set as default boot
        if self.check_system_error() or not self.verify_mirror_mode_enabled():
            return False
        self._os.reboot(self._reboot_timeout)  # Reboot for a graceful restart of system
        if self.verify_trusted_boot():  # verify the sut boot with trusted environment
            self._log.info("SUT Booted to Trusted environment Successfully")
        else:
            self._log.error("SUT did not Boot into Trusted environment")
            return False

        self._log.info("making SUT surprise reset to SUT")
        if self._dc.dc_power_reset():
            self._log.info("Surprise reset is done to system")
        else:
            self._log.error("Surprise reset is not done to system")
            raise RuntimeError("Surprise reset is not done to system")
        time.sleep(self._reboot_timeout)
        if self.verify_trusted_boot():  # verify the sut boot with trusted environment
            self._log.info("SUT Booted to Trusted environment Successfully")
            ret_val = True
        else:
            if self.verify_trusted_boot(expect_ltreset=True):  # verify the sut boot with trusted environment
                self._log.info("SUT Booted to Trusted environment Successfully")
                ret_val = True
            else:
                self._log.error("SUT did not Boot into Trusted environment")
        return ret_val


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MemoryMirroring.main() else Framework.TEST_RESULT_FAIL)
