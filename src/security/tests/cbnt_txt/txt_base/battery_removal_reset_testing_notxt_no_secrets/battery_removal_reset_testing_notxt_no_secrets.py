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
from dtaf_core.providers.physical_control import PhysicalControlProvider

from src.lib import content_exceptions
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.lib.test_content_logger import TestContentLogger


class BatterRemovalResetTestingNoTXTNoSecret(TxtBaseTest):
    """
    Glasgow ID : 58223-Battery removal reset testing (TXT not set as default, no secrets)
    Phoneix ID : P18014069672-Battery removal reset testing (TXT not set as default, no secrets)
    Boot trusted, clear secrets flag, verifies secrets are cleared from memory, and does a surprise AC off.
    CMOS clear and Remove battery for at least 1 minute and Wait till system comes up,
    sets TXT enabled, and then verifies that the SUT boots trusted.
    pre-requisites:
    1.Ensure that the system is in sync with the BKC.
    2.Ensure that you have a Linux OS image or hard drive with tboot installed.
    3.Ensure that the platform has a TPM provisioned with an ANY policy installed
        and active
    """
    BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"
    TEST_CASE_ID = ["G58223-Battery removal reset testing (TXT not set as default, no secrets)",
                    "18014069672-Battery removal reset testing (TXT not set as default, no secrets)"]
    step_data_dict = {1: {'step_details': 'Executing lsmem/lscpu/lspci command, enabling TXT BIOS Knobs'
                                          'and Booting to Tboot',
                          'expected_results': 'Verifying TXT BIOS Knobs and verifying'
                                              'SUT entered to Tboot and comparing the lsmem/lscpu/lspci results'},
                      2: {'step_details': 'verify that the MLE is launched and the secrets bit has been set',
                          'expected_results': 'MLE launch successfully and the secrets bit has been set'},
                      3: {'step_details': 'Clear secret flag',
                          'expected_results': 'Secret flag is cleared successfully'},
                      4: {'step_details': 'AC power off, Physically remove battery/clear CMOS  and AC power on',
                          'expected_results': 'AC power off successfully, Physically battery removed and '
                                              'CMOS clear done and AC power on successfully'},
                      5: {'step_details': 'Executing lsmem/lscpu/lspci command, enabling TXT BIOS Knobs'
                                          'and Booting to Tboot',
                          'expected_results': 'Verifying TXT BIOS Knobs and verifying'
                                              'SUT entered to Tboot and comparing the lsmem/lscpu/lspci results'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(BatterRemovalResetTestingNoTXTNoSecret, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        phy_cfg = cfg_opts.find(PhysicalControlProvider.DEFAULT_CONFIG_PATH)
        self._phy = ProviderFactory.create(phy_cfg, test_log)  # type: PhysicalControlProvider
        self._trusted_boot = TrustedBootWithTboot(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        Pre-validating whether sut is configured with tboot by getting the Tboot index in OS boot order.
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        # get pre Tboot lsmem, lscpu and lspci data
        self._trusted_boot.prepare()  # execute the prepare method of test case 58199
        self._trusted_boot.execute()  # execute the execute method of test case 58199
        self._test_content_logger.end_step_logger(1, return_val=True)

    def ungraceful_g3(self):
        """
        This function performs the ungraceful reset and also performs the clear CMOS Operation

        :raise: content_exceptions: If Fail to perform AC power off/On
        :raise: content_exceptions: If Fail to perform clear CMOS
        :return: None
        """

        if not self._ac_obj.ac_power_off(self._AC_TIMEOUT):
            raise content_exceptions.TestFail("Unable to ac power off the system")
        self._log.info("AC power is turned OFF")

        if not self._phy.set_clear_cmos(self._AC_TIMEOUT):  # Clears CMOS value
            raise content_exceptions.TestFail("Clear CMOS is not done successfully")
        self._log.info("CMOS Cleared Successfully")

        if not self._ac_obj.ac_power_on(self._AC_TIMEOUT):
            raise content_exceptions.TestFail("Unable to ac power On the system")
        self._log.info("AC power is turned ON")
        self._os.wait_for_os(self._reboot_timeout)

    def execute(self):
        """
        This function performs below operation.
        1. checks mle launch and secret bit is set or not
        2. clear secret flag
        3. performs ungraceful shutdown and clear cmos.
        4. verify if the sut booted to Tboot.
        :return: True if Test case pass else fail
        """
        self._test_content_logger.start_step_logger(2)
        self.mle_launch_and_secret_bit_is_set()
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._test_content_logger.start_step_logger(3)
        # Clear secrets flag
        self.clear_secret_flag()
        self._test_content_logger.end_step_logger(3, return_val=True)
        self._test_content_logger.start_step_logger(4)
        self.ungraceful_g3()
        self._test_content_logger.end_step_logger(4, return_val=True)
        self._test_content_logger.start_step_logger(5)
        self._os.wait_for_os(self._reboot_timeout)  # Waits until the system comes up
        self._trusted_boot.prepare()
        self._trusted_boot.execute()
        self._test_content_logger.end_step_logger(5, return_val=True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """Clean-up method called when a script ends"""
        # stopping serial driver
        self._uefi_obj.serial._release()
        super(BatterRemovalResetTestingNoTXTNoSecret, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if BatterRemovalResetTestingNoTXTNoSecret.main() else Framework.TEST_RESULT_FAIL)
