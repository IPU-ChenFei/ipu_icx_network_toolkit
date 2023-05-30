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
from src.power_management.lib.reset_base_test import ResetBaseTest
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot
from src.security.lib.cycling_common import TbootCyclingCommon
from src.lib.test_content_logger import TestContentLogger
from src.provider.rdmsr_and_cpuid_provider import RdmsrAndCpuidProvider


class TrustedBootWarmResetCycling(TxtBaseTest):
    """
    Glasgow ID : G58988.1-Trusted_Boot_Warm_Reset_Cycling

    Cycle testing using the OS's reboot functionality.
    Must be performed with TXT enabled (able to boot trusted) and BtG profile 5 enabled.
    """
    TEST_CASE_ID = ["G58988.1", "Trusted_Boot_Warm_Reset_Cycling"]
    STEP_DATA_DICT = {

        1: {'step_details': 'Boot the platform trusted',
            'expected_results': 'Platform has Booted Trusted Successfully'},
        2: {'step_details': 'Warm reset the platform and verify Btg 5 enabled and platform boot trusted',
            'expected_results': 'Btg 5 verified and Platform has Booted Trusted Successfully'},
        3: {'step_details': 'Warm reset the platform and verify platform boot to trusted',
            'expected_results': 'Platform has Booted Trusted Successfully'}}
    _WARM_REBOOT = "warm_reboot"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of TrustedBootWarmResetCycling

        :param test_log: Used for error, debug and info messages.
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param arguments: None
        """
        super(TrustedBootWarmResetCycling, self).__init__(test_log, arguments, cfg_opts)
        self._reset_obj = ResetBaseTest(test_log, arguments, cfg_opts)
        self._trusted_boot = TrustedBootWithTboot(test_log, arguments, cfg_opts)
        self.cycling_common = TbootCyclingCommon(self._log, self, self._reset_obj, self._common_content_lib)
        self.rdmsr_obj = RdmsrAndCpuidProvider.factory(self._log, self._os, cfg_opts)
        self.total_tboot_warm_reboot_cycle_number, self.warm_reboot_recovery_mode = \
            self._common_content_configuration.get_tboot_num_of_cycles(self._WARM_REBOOT)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """Load Bios default and clears OS logs and perform power cycle """
        self._test_content_logger.start_step_logger(1)
        self._trusted_boot.prepare()  # execute the prepare method of test case 58199
        self._trusted_boot.execute()  # execute the execute method of test case 58199
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This method follows:
        1. Flashing BTG 5 profile image on this SUT.
        2. Enable the knobs and checks platform boot trusted successfully
        3. Perform Warm reset and verifies after each cycle, Btg 5 is enabled and platform boot trusted successfully

        :raise: content exception if Btg 5 verification failed or Trusted boot is not booted
        :return: True, if test case passes
        """
        self._test_content_logger.start_step_logger(3)
        self.rdmsr_obj.install_msr_tools()
        self.cycling_common.trigger_txt_cycles_without_bootguard(self.total_tboot_warm_reboot_cycle_number,
                                                                 "warm_reboot", "Warm reboot",
                                                                 self.warm_reboot_recovery_mode)
        self._test_content_logger.end_step_logger(3, return_val=True)
        if self.cycling_common.number_of_failures > 0:
            return False
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """Test Cleanup"""
        self.cycling_common.cycling_summary_report()
        super(TrustedBootWarmResetCycling, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TrustedBootWarmResetCycling.main() else Framework.TEST_RESULT_FAIL)
