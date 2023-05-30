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


class PminIdleSocWatch(SocWatchBaseTest):
    """
    HPQC ID : H81611 (Linux) / H87935 (Windows)
    This Test case install SocWatch Tool and Execute Socwatch tool with specific run time.
    verify the CPU Idle P-State residency values
    """
    TEST_CASE_ID = ["H81611", "PI_Powermanagement_Power_Pmin_Idle_SoCwatch_L",
                    "H87935", "PI_PowerManagement_Power_Pstates_Idle_Socwatch_W"]
    PSTATE_BIOS_ENABLE = "pstate_enable_bios_knobs.cfg"
    SOCWATCH_RUN_TIME = 900
    CPU_IDLE_THRESHOLD = 70
    SYSTEM_IDLE_TIME = 300
    CPU_IDLE_CONDITION = "%s > " + str(CPU_IDLE_THRESHOLD)

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of PminIdleSocWatch

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.pstate_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.PSTATE_BIOS_ENABLE)
        super(PminIdleSocWatch, self).__init__(test_log, arguments, cfg_opts, self.pstate_bios_enable)

    def prepare(self):
        # type: () -> None
        """
        This function will Clear the mce errors and load bios defaults to SUT
        """
        super(PminIdleSocWatch, self).prepare()

    def execute(self):
        """
        This function install socwatch, execute socwatch tool
        Copy CSV file to host, read and verify the P-state Cpu Idle values

        :return: True if test completed successfully, False otherwise.
        :raise: content_exceptions.TestFail if not getting expected threshold values
        """
        self.execute_socwatch_tool(socwatch_runtime=self.SOCWATCH_RUN_TIME, execute_stress=False,
                                   system_idle_timeout=self.SYSTEM_IDLE_TIME)

        pstate_table = self.csv_reader_obj.get_package_p_state_residency_time_summary()
        try:
            idle_core_p_state_values = pstate_table[PacakgePState.PACKAGE_P_STATE_CPU_IDLE]
        except KeyError:
            raise content_exceptions.TestFail("Failed to get Cpu Idle")
        self._log.debug("P-State CPU Idle Values {}".format(idle_core_p_state_values))

        # Verify the P-state CPU Idle residency percentage values
        self._log.info("Verify Package P-State residency percentage for CPU Idle > {}".format(self.CPU_IDLE_THRESHOLD))
        invalid_matches = []
        for key, value in idle_core_p_state_values.items():
            if self.csv_reader_obj._RESIDENCY_PERCENT_MATCH in key:
                if not eval(self.CPU_IDLE_CONDITION % (float(idle_core_p_state_values[key]))):
                    invalid_matches.append(key)
        if invalid_matches:
            raise content_exceptions.TestFail("CPU Idle  threshold values are not matching with expected %s " %
                                              invalid_matches)

        self._log.info("Package P-state has been verified successfully")
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PminIdleSocWatch, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PminIdleSocWatch.main() else Framework.TEST_RESULT_FAIL)
