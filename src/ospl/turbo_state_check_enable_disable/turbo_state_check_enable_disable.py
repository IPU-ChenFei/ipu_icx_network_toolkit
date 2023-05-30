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
from src.provider.socwatch_provider import PacakgePState
from src.lib import content_exceptions


class TurboStateCheckEnableDisable(SocWatchBaseTest):
    """
    HPQC ID : H82175-PI_Powermanagement_Turbo_State_check-Disable_enable_SoCwatch_L
    This Test case Enable/Disable turbo mode bios knob, install SocWatch Tool/Burintest in the SUT and Execute the
    Socwatch command and burnintest. Verify the Package P-State residency percentage
    """
    TEST_CASE_ID = ["H82175", "PI_Powermanagement_Turbo_State_check-Disable_enable_SoCwatch_L"]
    BIOS_CONFIG_FILE_DISABLE = "power_turbo_disable_bios_knobs.cfg"
    BURNING_CONFIG_FILE = "cmdline_config_100_workload.txt"
    SOCWATCH_RUN_TIME = 300
    BIT_TIMEOUT = 5  # in minutes
    PSTATE_P0_P1_THRESHOLD = 0
    P0_CONDITION = "%s > " + str(PSTATE_P0_P1_THRESHOLD)
    P0_TURBO_DISABLE_CONDITION = "%s != " + str(PSTATE_P0_P1_THRESHOLD)
    P1_TURBO_DISABLE_CONDITION = "%s > " + str(PSTATE_P0_P1_THRESHOLD)

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of TurboStateCheckEnableDisable

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.turbo_mode_bios_disable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    self.BIOS_CONFIG_FILE_DISABLE)
        super(TurboStateCheckEnableDisable, self).__init__(test_log, arguments, cfg_opts)
        collateral_path = self._common_content_lib.get_collateral_path()
        self.burnin_config_file = os.path.join(collateral_path, self.BURNING_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        This function will load bios defaults to SUT and Check the mce errors
        """
        super(TurboStateCheckEnableDisable, self).prepare()
        self._common_content_lib.update_micro_code()

    def execute(self):
        """
        This function install socwatch and burnin, execute socwath and burnin tool
        Copy CSV file to host, read and verify the C-state values
        Setting the C-state bios to disable and repeat the steps as above

        :return: True if test completed successfully, False otherwise.
        """
        self.execute_socwatch_tool(self.SOCWATCH_RUN_TIME, self.burnin_config_file, self.BIT_TIMEOUT,
                                   execute_stress=True)
        # Verify the Core P-state residency values
        self._log.info("Verify P-State residency percentage for P0")
        pstate_table = self.csv_reader_obj.get_package_p_state_residency_time_summary()
        if not len(pstate_table):
            raise content_exceptions.TestError("Could not find the package p state residency table in SocWatchOutput")
        pstates_enter = []
        for p_state, value in pstate_table.items():
            if p_state.startswith(PacakgePState.PACKAGE_P_STATE_P0):
                matches = self.csv_reader_obj.verify_package_p_state_residency(p_state, pstate_table,
                                                                              self.P0_CONDITION % p_state)
                if matches:
                    pstates_enter.append(p_state)
        self._log.info("%s P-State entered ", pstates_enter)
        if not pstates_enter:
            raise content_exceptions.TestFail("SUT did not enter into %s pstates" % pstates_enter)
        self._log.info("Package P-state has been verified successfully")

        # Step2: Disable the Turbomode bios
        self.set_verify_bios_knobs(self.turbo_mode_bios_disable)
        # Verify the Core/Package C-state residency values
        self.execute_socwatch_tool(self.SOCWATCH_RUN_TIME, self.burnin_config_file, self.BIT_TIMEOUT,
                                   execute_stress=True)
        # Verify the Core P-state residency values
        self._log.info("Verify Package C-State residency percentage for P0")
        pstate_table = self.csv_reader_obj.get_package_p_state_residency_time_summary()
        if not len(pstate_table):
            raise content_exceptions.TestError("Could not find the package p state residency table in SocWatchOutput")
        pstates_enter = []
        for p_state, value in pstate_table.items():
            if p_state.startswith(PacakgePState.PACKAGE_P_STATE_P0):
                matches = self.csv_reader_obj.verify_package_p_state_residency(p_state, pstate_table,
                                                                              self.P0_TURBO_DISABLE_CONDITION % p_state)
                if matches:
                    pstates_enter.append(p_state)
        self._log.info("%s P-State entered ", pstates_enter)
        if pstates_enter:
            raise content_exceptions.TestFail("SUT entered into %s pstates but it is not expected" % pstates_enter)
        self._log.info("Package P-state has been verified successfully")
        # Verify the Core P-state residency values
        self._log.info("Verify Package C-State residency percentage for P1")
        pstate_table = self.csv_reader_obj.get_package_p_state_residency_time_summary()
        if not len(pstate_table):
            raise content_exceptions.TestError("Could not find the package p state residency table in SocWatchOutput")
        matches = self.csv_reader_obj.verify_package_p_state_residency(PacakgePState.PACKAGE_P_STATE_P1, pstate_table,
                                                                       self.P1_TURBO_DISABLE_CONDITION %
                                                                           PacakgePState.PACKAGE_P_STATE_P1)
        if not matches:
            raise content_exceptions.TestFail("SUT did not enter into %s pstates" % PacakgePState.PACKAGE_P_STATE_P1)
        self._log.info("Package P-state has been verified successfully")
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(TurboStateCheckEnableDisable, self).cleanup(return_status)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TurboStateCheckEnableDisable.main() else Framework.TEST_RESULT_FAIL)
