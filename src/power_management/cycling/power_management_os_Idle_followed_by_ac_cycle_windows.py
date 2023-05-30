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
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.power_management.lib.reset_base_test import ResetBaseTest
import src.lib.content_exceptions as content_exceptions
from src.provider.pm_provider import PmProvider
from src.lib.dtaf_content_constants import PowerManagementConstants


class PowerManagementOSIdleFollowedByACCycleWindows(ResetBaseTest):
    """
    HPQC ID : H87940_Power Management - OS Idle followed by AC Cycle - Windows
    The objective of this test case is to validate system stability by performing multiple cycles of idle operation
    followed by AC power cycling.
    """
    _BIOS_CONFIG_FILE = "power_management_os_Idle_followed_by_ac_cycle_windows_bios_knobs.cfg"
    NO_OF_CYCLE = 6
    MINUTE = 60
    TEST_CASE_ID= ["H87940_Power Management - OS Idle followed by AC Cycle - Windows"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PowerManagementOSIdleFollowedByACCycleWindows object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PowerManagementOSIdleFollowedByACCycleWindows, self).__init__(test_log, arguments, cfg_opts,
                                                                            self._BIOS_CONFIG_FILE)
        self._pm_provider = PmProvider.factory(test_log, cfg_opts, self.os)
        if self.os.os_type != OperatingSystems.WINDOWS:
            raise NotImplementedError("This Test Case is Only Supported on Windows")

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.

        :return: None
        """
        super(PowerManagementOSIdleFollowedByACCycleWindows, self).prepare()

    def execute(self):
        """
        This Method is Used to execute verify_machine_check_errors_in_various_ac_cycles and verifying status of MCE in
        every Cycle.

        :return: True or False
        """
        mce_errors = []
        self._pm_provider.set_power_scheme("Balanced")
        self._pm_provider.set_screen_saver_blank(PowerManagementConstants.BLANK_SCREEN_TIMEOUT)
        for cycle_number in range(self.NO_OF_CYCLE):
            self._log.info("Power cycle %d", cycle_number)
            self._log.info("System is set to Idle state for {} minutes".
                           format(PowerManagementConstants.SYSTEM_IDLE_TIME_1_HR // self.MINUTE))
            start_time = time.time()
            current_time = time.time() - start_time
            while current_time <= PowerManagementConstants.SYSTEM_IDLE_TIME_1_HR:
                if not self.os.is_alive():
                    raise RuntimeError("SUT is not responding at %d secs during the idle time", current_time)
                self._log.debug("Waiting for %d seconds", PowerManagementConstants.WAIT_TIME)
                time.sleep(PowerManagementConstants.WAIT_TIME)
                current_time = time.time() - start_time
            self._log.info("Successfully completed system Idle state for {} minutes".
                           format(PowerManagementConstants.SYSTEM_IDLE_TIME_1_HR // self.MINUTE))
            errors = self._common_content_lib.check_if_mce_errors()
            if errors:
                mce_errors.append("MCE Errors during the System Idle Cycle_{} are '{}'".format(cycle_number, errors))
            self._common_content_lib.clear_mce_errors()
            self.perform_graceful_g3()
            errors = self._common_content_lib.check_if_mce_errors()
            if errors:
                mce_errors.append("MCE Errors during the AC Cycle_{} are '{}'".format(cycle_number, errors))

        if mce_errors:
            raise content_exceptions.TestFail("\n".join(mce_errors))

        self._log.info("Sut is booted back to OS in all the '{}' Cycles and there are no Machine Check "
                       "Errors Logged".format(self.NO_OF_CYCLE))
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PowerManagementOSIdleFollowedByACCycleWindows.main() else
             Framework.TEST_RESULT_FAIL)
