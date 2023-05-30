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

from src.provider.stressapp_provider import StressAppTestProvider
from src.provider.pm_provider import PmProvider
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import PowerManagementConstants


class VerifySutTransitionFromIdleToNormal(ContentBaseTestCase):
    """
     HPQC ID : G56577-Power Management - Idle -  SUT Transition From Idle to Normal Operating State
     
    This class is implemented to set system into power savings ,sleep states and allow the system
    to idle with BIOS C-states enabled
    """
    TEST_CASE_ID = ["G56577", "Power Management-Idle-SUT Transition From Idle to Normal Operating State"]
    _BIOS_CONFIG_FILE = "enable_c_state_bios_knobs.cfg"
    STRESS_TIME = 20
    MINUTE = 60
    STRESS_COMMAND_DICT = {"prime95": "prime95.exe -t", "mprime": "./mprime -t"}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifySutTransitionFromIdleToNormal, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

        self._pm_provider = PmProvider.factory(test_log, cfg_opts, self.os)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._install_collateral = InstallCollateral(test_log, self.os, cfg_opts)

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
        super(VerifySutTransitionFromIdleToNormal, self).prepare()
        self._log.info("Step 2 scope is justified by verifying the CPU C State enable")

    def execute(self):
        """"
        This Method keep's system in idle state for 12 hrs and execute any stress application and check state of OS.
        :return: True or False
        :raise: RunTimeError
        """
        self._pm_provider.set_power_scheme("Balanced")
        self._pm_provider.set_sleep_timeout(PowerManagementConstants.SLEEP_TIMEOUT_NEVER)
        self._pm_provider.set_screen_saver_blank(PowerManagementConstants.BLANK_SCREEN_TIMEOUT)
        self._log.info("System is set to Idle state for {} minutes".
                       format(PowerManagementConstants.SYSTEM_IDLE_TIME_12_HRS//self.MINUTE))
        start_time = time.time()
        current_time = time.time() - start_time
        while current_time <= PowerManagementConstants.SYSTEM_IDLE_TIME_12_HRS:
            if not self.os.is_alive():
                raise RuntimeError("SUT is not responding at %d secs during the idle time", current_time)
            self._log.debug("Waiting for %d seconds", PowerManagementConstants.WAIT_TIME)
            time.sleep(PowerManagementConstants.WAIT_TIME)
            current_time = time.time() - start_time
        self._log.info("Successfully completed system Idle state for {} minutes".
                       format(PowerManagementConstants.SYSTEM_IDLE_TIME_12_HRS // self.MINUTE))
        self._log.info("Installing the stress test")
        stress_app_path, stress_tool_name = self._install_collateral.install_prime95(app_details=True)
        self._log.info("installed stress application")
        self._stress_provider.execute_async_stress_tool(self.STRESS_COMMAND_DICT[stress_tool_name], stress_tool_name,
                                                        stress_app_path)
        self._log.info("Waiting for stress test to be completed in (%d seconds)", self.STRESS_TIME)
        time.sleep(self.STRESS_TIME)
        self._stress_provider.kill_stress_tool(stress_tool_name, self.STRESS_COMMAND_DICT[stress_tool_name])

        if not self.os.is_alive():
            raise RuntimeError("SUT is not responding after executing stress and idle time")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifySutTransitionFromIdleToNormal.main() else Framework.TEST_RESULT_FAIL)
