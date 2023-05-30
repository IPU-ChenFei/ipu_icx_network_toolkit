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
import six

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.power_management.socwatch_common import SocWatchBaseTest
from src.provider.socwatch_provider import PacakgePState
from src.lib import content_exceptions


class PStatesAllSocWatch(SocWatchBaseTest):
    """
    HPQC ID : H81608 (Linux) / H87944 (Windows)
    This Test case install SocWatch Tool/Burnintest and Execute Socwatch/Burnintest to load the sut
    verify the P-State residency values
    """
    TEST_CASE_ID = ["H81608", "PI_Powermanagement_Power_Pstates_All_SoCwatch_L",
                    "H87944", "PI_Powermanagement_Power_Pstate_All_SoCwatch_W"]
    BIOS_CONFIG_FILE_NAME = "pstates_all_socwatch.cfg"
    BURNING_CONFIG_FILE = "cmdline_config_100_workload.txt"
    BURNING_CONFIG_FILE_WINDOWS = "cmdline_config_50_workload_windows.bitcfg"
    SOCWATCH_RUN_TIME = 900  # Soc watch run time in seconds
    BIT_TIMEOUT = 15  # BurnIn test time in minutes
    PSTATES_CONDITION = "%s > 70"
    PSTATES_THRESHOLD = 70

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of PStatesAllSocWatch

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.pstates_all = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE_NAME)
        super(PStatesAllSocWatch, self).__init__(test_log, arguments, cfg_opts, self.pstates_all)
        if self.os.os_type == OperatingSystems.LINUX:
            self.burnin_config_file = self.collateral_installer.download_tool_to_host(self.BURNING_CONFIG_FILE)
        elif self.os.os_type == OperatingSystems.WINDOWS:
            self.burnin_config_file = Path(os.path.dirname(os.path.abspath(__file__))).parent
            self.burnin_config_file = os.path.join(self.burnin_config_file, self.BURNING_CONFIG_FILE_WINDOWS)
        else:
            raise NotImplementedError("not implemented for this OS %s" % self._os.os_type)

    def prepare(self):
        # type: () -> None
        """
        This function will Clear the mce errors and load bios defaults to SUT
        """
        super(PStatesAllSocWatch, self).prepare()

    def execute(self):
        """
        This function install socwatch and burnin, execute socwatch and burnin tool
        Copy CSV file to host, read and verify the P-state values

        :return: True if test completed successfully, False otherwise.
        """
        self.execute_socwatch_tool(self.SOCWATCH_RUN_TIME, self.burnin_config_file, self.BIT_TIMEOUT,
                                   execute_stress=True)
        # Verify the Core/Package P-state residency values
        pstate_table = self.csv_reader_obj.get_package_p_state_residency_time_summary()
        if not len(pstate_table):
            raise content_exceptions.TestError("Could not find the package P state residency table in SocWatchOutput")
        p0_matches_values = []
        p0_matches = []
        p0_sum = []
        p1_matches = []
        # Adding P0 values
        for key, value in pstate_table.items():
            if key.startswith(PacakgePState.PACKAGE_P_STATE_P0):
                p0_sum = self.add_p0_values(key, pstate_table)
        self._log.info("After adding all P0 values : {}".format(p0_sum))
        # Checking for P0
        for key, value in p0_sum.items():
            if value > self.PSTATES_THRESHOLD:
                p0_matches_values.append(value)
                p0_matches.append(True)
            else:
                p0_matches.append(False)
        self._log.info("P0 Matches values : {}".format(p0_matches_values))

        # If P0 will not match then checking for P1
        if not all(p0_matches):
            for key, value in pstate_table.items():
                if key.startswith(PacakgePState.PACKAGE_P_STATE_P1):
                    p_matches = self.csv_reader_obj.verify_package_p_state_residency(key, pstate_table,
                                                                                     self.PSTATES_CONDITION % key)
                    if p_matches:
                        p1_matches.append(p_matches)
            if not p1_matches:
                raise content_exceptions.TestFail("P1 values are not matching with expected")

        self._log.info("Package P-state has been verified successfully")
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PStatesAllSocWatch, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PStatesAllSocWatch.main() else Framework.TEST_RESULT_FAIL)
