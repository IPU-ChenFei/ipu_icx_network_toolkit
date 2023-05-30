#!/usr/bin/env python
###############################################################################
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
###############################################################################
import sys
import os

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.power_management.socwatch_common import SocWatchBaseTest
from src.provider.socwatch_provider import PacakgePState
from src.lib import content_exceptions


class PowerManagementHWPOOBLinux(SocWatchBaseTest):
    """
    HPALM ID : H81628-PI_Powermanagement_HWP_OOB_L
    This class will install Socwatch tool, execute burnin test and verify Pstate values
    """
    TEST_CASE_ID = ["H81628, PI_Powermanagement_HWP_OOB_L"]
    BIOS_CONFIG_FILE = "pm_hwp_band_mode.cfg"
    BURNING_CONFIG_FILE = "commandline_config_50_workload.txt"
    SOCWATCH_RUN_TIME = 300
    BIT_TIMEOUT = 5  # in minutes
    PSTATES_CONDITION = "%s > 80"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of PowerManagementHWPOOBLinux

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        self.band_mode_enable_bios = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  self.BIOS_CONFIG_FILE)
        self.burnin_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               self.BURNING_CONFIG_FILE)
        super(PowerManagementHWPOOBLinux, self).__init__(test_log, arguments, cfg_opts, self.band_mode_enable_bios)
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("Not implemented for {} OS".format(self.os.os_type))

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(PowerManagementHWPOOBLinux, self).prepare()
        self._common_content_lib.update_micro_code()

    def execute(self):
        """
        Test main logic is copy socwatch to sut. Install Socwatch tool and execute
         burin test with specified workload and verify Pstate values
        """
        self.execute_socwatch_tool(socwatch_runtime=self.SOCWATCH_RUN_TIME, burnin_config_file=self.burnin_config_file,
                                   bit_timeout=self.BIT_TIMEOUT, execute_stress=True)

        pstate_table = self.csv_reader_obj.get_package_p_state_residency_time_summary()
        self._log.info("Verify Package P-State residency percentage for P0/P1")
        p0_p1_matches = []
        for key, value in pstate_table.items():
            if key.startswith(PacakgePState.PACKAGE_P_STATE_P0) or key.startswith(PacakgePState.PACKAGE_P_STATE_P1):
                p_matches = self.csv_reader_obj.verify_package_p_state_residency(key, pstate_table,
                                                                                 self.PSTATES_CONDITION % key)
                if p_matches:
                    p0_p1_matches.append(p_matches)

        if not p0_p1_matches:
            raise content_exceptions.TestFail("P0/P1 values are not matching with expected")
        self._log.info("Package P-state has been verified successfully")
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PowerManagementHWPOOBLinux, self).cleanup(return_status)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PowerManagementHWPOOBLinux.main() else Framework.TEST_RESULT_FAIL)
