#!/usr/bin/env python
##########################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and
# proprietary and confidential information of Intel Corporation and its
# suppliers and licensors, and is protected by worldwide copyright and trade
# secret laws and treaty provisions. No part of the Material may be used,copied,
# reproduced, modified, published, uploaded, posted, transmitted, distributed,
# or disclosed in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################
import os
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.cbnt_txt.txt_base.security_tpm_check_bios_uefi import SecurityTpmCheckBiosUEFI
from src.lib import content_exceptions
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest


class TxtTpm2TrustedBootMeasuredLaunchL(TxtBaseTest):
    """
    Phoenix ID : P18014074849-PI_Security_TXT_TPM2.0_TrustedBoot_measured launch_L
    To verify that platform is booted with RHEL OS with trustedboot kernel
    """
    BIOS_CONFIG_FILE = "security_txt_bios_knobs_enable.cfg"
    TXT_BIOS_CONFIG = "txt_tpm2_trustedboot_measured_launch.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of TxtTpm2TrustedBootMeasuredLaunchL.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.enable_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        self.txt_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.TXT_BIOS_CONFIG)
        super(TxtTpm2TrustedBootMeasuredLaunchL, self).__init__(test_log, arguments, cfg_opts,
                                                                self.txt_bios_config_file)
        self.bios_config_file = self._common_content_lib.get_combine_config([self.txt_bios_config_file,
                                                                             self.enable_bios_config_file])
        self.enable_tpm = SecurityTpmCheckBiosUEFI(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        Provision TPM2
        """
        self.enable_tpm.prepare()
        self.enable_tpm.execute()

    def execute(self):
        """
        This Function execute the test case
        1. Enables TXT knobs
        2. Installs Tboot
        3. Verifies Trusted boot

        :return: True if test is passed, False if failed
        """
        self.enable_and_verify_bios_knob_without_bios_default(self.bios_config_file)
        self.tboot_installation()
        self.tboot_index = self.get_tboot_boot_position()  # Get the Tboot_index from grub menu entry
        self.set_default_boot_entry(self.tboot_index)  # Set Tboot as default boot
        self.perform_graceful_g3()
        self.verify_sut_booted_in_tboot_mode(self.tboot_index)  # verify if the system booted in Trusted mode.
        if not self.verify_trusted_boot():  # verify the sut boot with trusted env
            raise content_exceptions.TestFail("SUT did not boot to Trusted environment")
        self._log.info("SUT Booted to Trusted environment Successfully")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TxtTpm2TrustedBootMeasuredLaunchL.main() else Framework.TEST_RESULT_FAIL)
