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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_base_test_case
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral


class RdtCmtStatisticsLlcStress(content_base_test_case.ContentBaseTestCase):
    """
    HPQC ID : H79562-PI_RDT_A_CMTStatistics_LLC_stress_L

    This test case aims to install RDT if it not installed and Verify CMT statistics - LLC occupancy can be
    collected by pqos correctly when stress is running
    """

    TEST_CASE_ID = ["H79562-PI_RDT_A_CMTStatistics_LLC_stress_L"]
    CORE = "0"
    PQOS_CMD = "pqos --mon-core='llc:{}' --mon-file=llc.txt -t 60".format(CORE)
    PQOS_END_DURATION = 60.0
    DISPLAY_PQOS_DATA = "tail -n 30 llc.txt"
    TASKSET_CMD = "taskset -c {}  stress -m 100".format(CORE)
    EVENT_NAME = "LLC[KB]"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtCmtStatisticsLlcStress

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtCmtStatisticsLlcStress, self).__init__(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def prepare(self):  # type: () -> None
        """Test preparation/setup and install the stress tool to sut"""
        super(RdtCmtStatisticsLlcStress, self).prepare()
        self._install_collateral.install_stress_tool_to_sut()

    def collect_llc_statistics(self, stop_stress_process=False):
        """
        This method executes the pqos command to collect llc statistics. This runs It redirect the output to a file
        and gets the value of last 10 monitoring result.

        :param stop_stress_process: True if stress is running and it has to be stopped, False else
        :return: llc statistic result
        """
        self._log.info("Collecting llc statistic by running command".format(self.PQOS_CMD))
        self._common_content_lib.execute_sut_cmd(self.PQOS_CMD, self.PQOS_CMD, self._command_timeout)
        time.sleep(self.PQOS_END_DURATION)
        if stop_stress_process:
            if not self._rdt.is_stress_running():
                raise content_exceptions.TestFail("Stress Tool not running is system")
            self._rdt.stop_stress_tool()
        llc_result = self._common_content_lib.execute_sut_cmd(self.DISPLAY_PQOS_DATA, self.DISPLAY_PQOS_DATA,
                                                              self._command_timeout)
        self._log.debug("Command {} result is {}".format(self.PQOS_CMD, llc_result))

        return llc_result

    def execute_rdt_cmt_statistic_llc_stress(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. Start collecting LLC statistics for selected physical core with pqos before running stress:
            pqos --mon-core="llc:0" --mon-file=llc.txt
        4. Start memory load tool with simultaneous redirection of the process to the CPU core:
          'taskset -c 0  stress -m 100 '
        5. Start collecting LLC statistics for selected physical core with pqos after running stress:
            'pqos --mon-core="llc:0" --mon-file=llc.txt'
        6. Comparing the llc result before running stress and after running stress
        """
        self._rdt.install_rdt()
        self._rdt.restore_default_rdt_monitor()
        llc_res_before_stress = self.collect_llc_statistics()
        self._log.info("Start memory load tool with simultaneous redirection of the process to the CPU core")
        self.os.execute_async(self.TASKSET_CMD)
        self._log.info("Memory load tool started")
        llc_res_after_res = self.collect_llc_statistics(stop_stress_process=True)
        self._rdt.compare_event_statistic_data(llc_res_before_stress, llc_res_after_res, self.EVENT_NAME)

    def execute(self):
        """
        This method executes the test case with given number of iterations

        :return: True if test case pass
        """
        test_case_status = False
        for index in range(self._rdt.ITERATION):
            try:
                self._log.info("Iteration {}".format(index))
                self.execute_rdt_cmt_statistic_llc_stress()
                test_case_status = True
                break
            except Exception as e:
                self._log.error("Attempt number {} failed due to {}".format(index, e))
            finally:
                if self._rdt.is_stress_running():
                    self._rdt.stop_stress_tool()

        return test_case_status

    def cleanup(self, return_status):
        """Test Cleanup"""
        if self._rdt.is_stress_running():
            self._rdt.stop_stress_tool()
        super(RdtCmtStatisticsLlcStress, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtCmtStatisticsLlcStress.main() else Framework.TEST_RESULT_FAIL)
