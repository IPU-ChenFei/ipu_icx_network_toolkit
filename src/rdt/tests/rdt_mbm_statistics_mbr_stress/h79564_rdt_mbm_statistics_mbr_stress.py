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
import re

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_base_test_case
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral


class RdtStatisticsMbrStress(content_base_test_case.ContentBaseTestCase):
    """
    HPQC ID : H79564-PI_RDT_A_MBMStatistics_MBR_stress_L, H55270-PI_RDT_A_MBMStatistics_MBR_stress

    This test case aims to install RDT if it not installed and Verify MBM statistics - memory bandwidth local (MBR) can
     be collected by pqos correctly when stress is running
    """
    TEST_CASE_ID = ["H79564", "PI_RDT_A_MBMStatistics_MBR_stress_L", "H55270", "PI_RDT_A_MBMStatistics_MBR_stress"]
    CORE_LIST = ['', '']
    PQOS_CMD = "pqos --mon-core='mbr:{}' --mon-file=mbr.txt -t 60"
    PQOS_END_DURATION = 45.0
    DISPLAY_PQOS_DATA = "tail -n 30 mbr.txt"
    TASKSET_CMD = "taskset -c {} numactl --membind={} stress -m 100"
    EVENT_NAME = "MBR[MB/s]"
    PQOS_CMD_LIST = [["pqos -s", "Displays current allocation and monitoring configuration"]]
    NUM_OF_SOCKETS_CMD = "grep 'physical id' /proc/cpuinfo | ""sort -u | wc -l"
    REGEX_CORE = "Core\s+information\s+for\s+socket\s+{}.*\s+Core\s+(\d+),"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtStatisticsMbrStress

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtStatisticsMbrStress, self).__init__(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))
        self._num_sockets = int(
            self._common_content_lib.execute_sut_cmd(self.NUM_OF_SOCKETS_CMD, self.NUM_OF_SOCKETS_CMD,
                                                     self._command_timeout))

    def prepare(self):  # type: () -> None
        """Test preparation/setup and install the stress tool to sut"""
        super(RdtStatisticsMbrStress, self).prepare()
        self._install_collateral.install_stress_tool_to_sut()

    def collect_mbr_statistics(self, stop_stress_process=False, soc_val=None):
        """
        This method executes the pqos command to collect mbr statistics. This runs It redirect the output to a file
        and gets the value of last 10 monitoring result.

        :param stop_stress_process: True if stress is running and it has to be stopped, False else
        :param soc_val: Socket where the Stress is running
        :return: mbr statistic result
        """
        self._log.info("Collecting mbr statistic by running command {}".format(self.PQOS_CMD.format(self.CORE_LIST[
                                                                                                     soc_val])))
        self._common_content_lib.execute_sut_cmd(self.PQOS_CMD.format(self.CORE_LIST[soc_val]),
                                                 self.PQOS_CMD.format(self.CORE_LIST[soc_val]), self._command_timeout)
        time.sleep(self.PQOS_END_DURATION)
        if stop_stress_process:
            if not self._rdt.is_stress_running():
                raise content_exceptions.TestFail("Stress Tool not running is system")
            self._rdt.stop_stress_tool()
        mbr_result = self._common_content_lib.execute_sut_cmd(self.DISPLAY_PQOS_DATA, self.DISPLAY_PQOS_DATA,
                                                              self._command_timeout)
        self._log.debug("Command {} result is {}".format(self.PQOS_CMD.format(self.CORE_LIST[soc_val]), mbr_result))

        return mbr_result

    def execute_rdt_mbr_stress(self, socket=None):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. Executes pqos -s and numactl --hardware
        4. Start collecting MBR statistics for selected physical core with pqos before running stress:
            pqos --mon-core="mbr:0" --mon-file=mbr.txt
        5. Start memory load tool with simultaneous redirection of the process to one selected CPU (Socket 0),
            additionally with numactl tool force the use of memory allocated to the second socket (Socket1):
            taskset -c 0 numactl --membind=1 stress -m 100
        6. Start collecting MBR statistics for selected physical core with pqos after running stress:
            pqos --mon-core="mbr:0" --mon-file=mbr.txt
        7. Comparing the mbr result before running stress and after running stress

        :param socket: Socket where the Stress is running
        """
        # Restore default monitoring: pqos -R
        self._rdt.restore_default_rdt_monitor()
        # Executes pqos -s and numactl --hardware
        self._log.info("Executing {} commands".format(self.PQOS_CMD_LIST[0]))
        self._rdt.execute_pqos_cmd(self.PQOS_CMD_LIST)
        self._rdt.verify_node0()

        # Start collecting MBR statistics for selected physical core
        mbr_res_before_stress = self.collect_mbr_statistics(soc_val=socket)

        # Start memory load tool with simultaneous redirection
        self._log.info("Start memory load tool with simultaneous redirection of the process to the CPU core")
        self.os.execute_async(self.TASKSET_CMD.format(self.CORE_LIST[socket], socket))
        self._log.info("Memory load tool started")

        # Start collecting MBR statistics for selected physical core
        mbr_res_after_stress = self.collect_mbr_statistics(stop_stress_process=True, soc_val=socket)
        self._rdt.compare_event_statistic_data(mbr_res_before_stress, mbr_res_after_stress, self.EVENT_NAME)

    def execute(self):
        """
        This method executes the test case with given number of iterations

        :return: True if test case pass
        """
        test_case_status = False
        core_list_cnt = self._num_sockets
        # Verify if RDT is installed, If not it will install
        self._rdt.install_rdt()
        l3ca_out = self._common_content_lib.execute_sut_cmd(self._rdt.CHECK_L3CA_CMD, self._rdt.CHECK_L3CA_CMD,
                                                            self._command_timeout)
        for each_socket in range(self._num_sockets):
            self.CORE_LIST[core_list_cnt - 1] = re.search(self.REGEX_CORE.format(each_socket), l3ca_out).group(1)
            core_list_cnt -= 1
        for each_socket in range(self._num_sockets-1, -1, -1):
            for index in range(self._rdt.ITERATION):
                try:
                    self._log.info("Iteration #{}".format(index+1))
                    self.execute_rdt_mbr_stress(socket=each_socket)
                    test_case_status = True
                    break
                except Exception as e:
                    self._log.error("Attempt number #{} failed due to {}".format(index+1, str(e)))
                finally:
                    if self._rdt.is_stress_running():
                        self._rdt.stop_stress_tool()
            if test_case_status:
                break

        return test_case_status

    def cleanup(self, return_status):
        """Test Cleanup"""
        if self._rdt.is_stress_running():
            self._rdt.stop_stress_tool()
        super(RdtStatisticsMbrStress, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtStatisticsMbrStress.main() else Framework.TEST_RESULT_FAIL)
