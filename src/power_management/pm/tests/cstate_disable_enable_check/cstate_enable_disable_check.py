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
import os

from dtaf_core.lib.dtaf_constants import Framework

from src.power_management.socwatch_common import SocWatchBaseTest
from src.provider.socwatch_provider import CoreCStates


class CStateEnableDisableCheck(SocWatchBaseTest):
    """
    HPQC ID : H82176-PI_Powermanagement_Power_Cstate_Disable-enable_check_SoCwatch_L
    This Test case install SocWatch Tool in the SUT and Execute the Socwatch command
    Verify the Package C-State and Core C-state residency values
    """
    TEST_CASE_ID = ["H82176", "PI_Powermanagement_Power_Cstate_Disable-enable_check_SoCwatch_L"]
    BIOS_CONFIG_FILE_ENABLE = "power_cstate_enable_bios_knobs.cfg"
    BIOS_CONFIG_FILE_DISABLE = "power_cstate_disable_bios_knobs.cfg"
    SOCWATCH_RUN_TIME = 900  # socwatch tool run time in seconds
    SOCWATCH_RUN_TIME_CSTATE_DISABLE = 600  # socwatch tool run time in seconds
    SYSTEM_IDLE_TIME = 300  # system idle time in seconds
    CC6_CSTATE_ENABLE_THRESHOLD = 90
    CC6_CSTATE_DISABLE_THRESHOLD = 10
    CC0_CC1_CSTATE_DISABLE_THRESHOLD = 90
    BIT_TIMEOUT = 15  # in minutes
    BURNING_CONFIG_FILE = "cmdline_config_100_workload.txt"
    CC0_STRESS_THRESHOLD = 90
    CC0_STRESS_CONDITION = "%s > " + str(CC0_STRESS_THRESHOLD)

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of CStateEnableDisableCheck

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.cstate_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               self.BIOS_CONFIG_FILE_ENABLE)
        super(CStateEnableDisableCheck, self).__init__(test_log, arguments, cfg_opts, self.cstate_bios_enable)
        self.cstate_bios_disable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                self.BIOS_CONFIG_FILE_DISABLE)

    def prepare(self):
        # type: () -> None
        """
        This function will Clear the mce errors and load bios defaults to SUT
        """
        super(CStateEnableDisableCheck, self).prepare()

    def execute(self):
        """
        This function install socwatch and execute socwatch
        Copy CSV file to host, read and verify the C-state values
        Setting the C-state bios to disable and repeat the same steps twice

        :return: True if test completed successfully, False otherwise.
        """
        self.execute_socwatch_tool(socwatch_runtime=self.SOCWATCH_RUN_TIME, system_idle_timeout=self.SYSTEM_IDLE_TIME,
                                   execute_stress=False)
        # Verify the Core/Package C-state residency values
        self._log.info("Verify Core C-State residency percentage for CC6 with threshold : {}".format("%s > %d" % (
            CoreCStates.CORE_C_STATE_CC6, self.CC6_CSTATE_ENABLE_THRESHOLD)))
        self.csv_reader_obj.verify_core_c_state_residency(CoreCStates.CORE_C_STATE_CC6, "%s > %d" % (
            CoreCStates.CORE_C_STATE_CC6, self.CC6_CSTATE_ENABLE_THRESHOLD))

        burnin_config_file = self.collateral_installer.download_tool_to_host(self.BURNING_CONFIG_FILE)
        # Run Burn-In stress and Run socwatch tool for 15 min
        self.execute_socwatch_tool(socwatch_runtime=self.SOCWATCH_RUN_TIME, burnin_config_file=burnin_config_file,
                                   bit_timeout=self.BIT_TIMEOUT, execute_stress=True)
        # To verify CC0 state should be > 90%
        self._log.info("Verify Core C-State residency percentage CC0 with burnin test with threshold : {}...".
                       format(self.CC0_STRESS_CONDITION % CoreCStates.CORE_C_STATE_CC0))

        self.csv_reader_obj.verify_core_c_state_residency(CoreCStates.CORE_C_STATE_CC0,
                                                          self.CC0_STRESS_CONDITION % CoreCStates.CORE_C_STATE_CC0)
        # Step2: Disable the C-state bios
        self.set_verify_bios_knobs(self.cstate_bios_disable)

        self.execute_socwatch_tool(socwatch_runtime=self.SOCWATCH_RUN_TIME_CSTATE_DISABLE,
                                   execute_stress=False)

        # Verify Core C-State residency values
        try:
            self._log.info("Verify Core C-State residency percentage CC0")
            self.csv_reader_obj.verify_core_c_state_residency(CoreCStates.CORE_C_STATE_CC0,
                                                              "%s > %d" % (CoreCStates.CORE_C_STATE_CC0,
                                                                           self.CC0_CC1_CSTATE_DISABLE_THRESHOLD))
        except Exception as e:
            self._log.debug("Verification for CC0 got failed due to exception {}".format(e))
            self._log.info("Verify Core C-State residency percentage CC1")
            self.csv_reader_obj.verify_core_c_state_residency(CoreCStates.CORE_C_STATE_CC1,
                                                              "%s > %d" % (CoreCStates.CORE_C_STATE_CC1,
                                                                           self.CC0_CC1_CSTATE_DISABLE_THRESHOLD))
        self._log.info("Verify Core C-State residency percentage CC6")
        self.csv_reader_obj.verify_core_c_state_residency(CoreCStates.CORE_C_STATE_CC6,
                                                          "%s < %d" % (CoreCStates.CORE_C_STATE_CC6,
                                                                       self.CC6_CSTATE_DISABLE_THRESHOLD))
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(CStateEnableDisableCheck, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CStateEnableDisableCheck.main() else Framework.TEST_RESULT_FAIL)
