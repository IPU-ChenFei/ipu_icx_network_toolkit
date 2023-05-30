# !/usr/bin/env python
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
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_common import BootGuardValidator
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot
from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_profile5 import BootGuardProfile5
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.security.lib.cycling_common import TbootCyclingCommon
from src.power_management.lib.reset_base_test import ResetBaseTest


class TrustedBootAcCycle(TxtBaseTest):
    """
    Glasgow ID : 59069.3-Trusted Boot AC Cycle

    Cold boot cycle testing (S0->G3->S0).
    Must be performed with TXT enabled (able to boot trusted) and BtG profile 5 enabled.
    """
    TEST_CASE_ID = ["G59069.3", "Trusted_Boot_AC_Cycle"]
    CURRENT_VERSION = "IFWI Current Version"
    _AC_CYCLE = "ac_cycle"
    STEP_DATA_DICT = {
        1: {'step_details': 'Enable BtG Profile 5',
            'expected_results': 'Btg Profile 5 verified successfully'},
        2: {'step_details': 'Boot the platform trusted',
            'expected_results': 'Platform has Booted Trusted Successfully'},
        3: {'step_details': 'Perform graceful G3 cycle to the platform and verify Btg 5 enabled and platform boot '
                            'trusted',
            'expected_results': 'Btg 5 verified and Platform has Booted Trusted Successfully'},
        4: {'step_details': 'G3 cycle and verify platform boot to trusted',
            'expected_results': 'Platform has Booted Trusted Successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of TrustedBootAcCycle

        :param test_log: Used for error, debug and info messages.
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param arguments: None
        """
        self.bootguard = arguments.BOOTGUARD
        super(TrustedBootAcCycle, self).__init__(test_log, arguments, cfg_opts)
        self._reset_obj = ResetBaseTest(test_log, arguments, cfg_opts)
        self._trusted_boot = TrustedBootWithTboot(test_log, arguments, cfg_opts)
        self.cycling_common = TbootCyclingCommon(self._log, self, self._reset_obj, self._common_content_lib)
        self.bootguard = False if self.bootguard == "False" else True
        if self.bootguard:
            self._btg_p5 = BootGuardProfile5(test_log, arguments, cfg_opts)
            self._boot_guard_obj = BootGuardValidator(test_log, arguments, cfg_opts)
            self._flash_obj = self._boot_guard_obj._flash_obj
        self.total_tboot_ac_cycle_number, self.ac_cycle_recovery_mode = \
            self._common_content_configuration.get_tboot_num_of_cycles(self._AC_CYCLE)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    @classmethod
    def add_arguments(cls, parser):
        """
        :param parser: argument parser
        :return: None
        """
        super(TrustedBootAcCycle, cls).add_arguments(parser)
        parser.add_argument("-bg", "--BOOTGUARD", action="store", dest="BOOTGUARD", default=True)

    def prepare(self):
        # type: () -> None
        """Load default Bios and clears os logs """
        if self.bootguard:
            self._test_content_logger.start_step_logger(1)
            self._btg_p5.prepare()  # execute the prepare method of test case 58206
            self._btg_p5.execute()  # execute the execute method of test case 58206
            self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This method follows:
        1. Flashing BTG 5 profile image on this SUT.
        2. Enable the knobs and checks platform boot trusted successfully
        3. Perform Graceful G3 cycle and verifies after each cycle, Btg 5 is enabled and platform boot trusted
        successfully

        :raise: content exception if Btg 5 verification failed or Trusted boot is not booted
        :return: True if TC pass
        """
        self._test_content_logger.start_step_logger(2)
        self._trusted_boot.prepare()  # execute the prepare method of test case 58199
        self._trusted_boot.execute()  # execute the execute method of test case 58199
        self._test_content_logger.end_step_logger(2, return_val=True)
        if self.bootguard:
            self._test_content_logger.start_step_logger(3)
            self.cycling_common.trigger_txt_cycles_with_bootguard(self.total_tboot_ac_cycle_number,
                                                                  self._AC_CYCLE, "AC Cycle",
                                                                  self.ac_cycle_recovery_mode)
            self._test_content_logger.end_step_logger(3, return_val=True)
        else:
            self._test_content_logger.start_step_logger(4)
            self.cycling_common.trigger_txt_cycles_without_bootguard(self.total_tboot_ac_cycle_number,
                                                                     self._AC_CYCLE, "AC Cycle",
                                                                     self.ac_cycle_recovery_mode)
            self._test_content_logger.end_step_logger(4, return_val=True)
        if self.cycling_common.number_of_failures > 0:
            return False
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """Test Cleanup"""
        if self.bootguard:
            self.set_default_boot_entry(self._DEFAULT_ENTRY)  # Set system to default normal os boot
            # reverting to current IFWI
            self._boot_guard_obj.flash_binary_image(self.CURRENT_VERSION)
            current_ifwi_version = self._flash_obj.get_bios_version()
            if current_ifwi_version != self._boot_guard_obj.before_flash_bios_version:
                raise content_exceptions.TestFail("Original IWFI is not restored to continue the execution")
            self._log.info("IFWI original version is reverted successfully")
            super(TrustedBootAcCycle, self).cleanup(return_status)
        self.cycling_common.cycling_summary_report()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TrustedBootAcCycle.main() else Framework.TEST_RESULT_FAIL)
