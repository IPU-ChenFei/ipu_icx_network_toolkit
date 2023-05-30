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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib.test_content_logger import TestContentLogger
from src.lib import content_base_test_case
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral


class RdtMonitorLlcSingleCpuCoreStress(content_base_test_case.ContentBaseTestCase):
    """
    HPQC ID : H86526-PI_RDT_A_MonitorLLC_MemBW_SingleCPUCores_stress , H55275-PI_RDT_A_MonitorLLC_MemBW_SingleCPUCores _stress

    This test case aims to install RDT if it not installed and Check the RDT monitoring functions for a single core
    with pqos command when stress is running on this single cores.
    """

    TEST_CASE_ID = ["H86526","H55275","PI_RDT_A_MonitorLLC_MemBW_SingleCPUCores_stress"]
    CORE = "10"
    RDT_MONITOR_CMD = "pqos -m 'all:{}' -t 10".format(CORE)
    TASKSET_CMD = "taskset -c {} stress -m 30 -c 30 -t 60 ".format(CORE)
    step_data_dict = {
        1: {'step_details': 'Verify if RDT is installed on sut',
            'expected_results': 'Verified installation'},
        2: {'step_details': 'Restore RDT to default monitoring',
            'expected_results': 'Restore RDT to default monitoring is successful'},
        3: {'step_details': 'Turn on RDT monitoring for CPU core {}'.format(CORE),
            'expected_results': 'RDT monitoring is turned on successfully and data is collected'},
        4: {'step_details': 'Start memory and cpu load process',
            'expected_results': 'Stress tool started to load memory and CPU usage'},
        5: {'step_details': 'Turn on RDT monitoring for CPU core {} and compare results'.format(CORE),
            'expected_results': 'RDT monitoring is turned on and observed event values are increased after running '
                                'stress'},
        6: {'step_details': 'Turn the stress off',
            'expected_results': 'Stress is turned off successfully'},
        7: {'step_details': 'Turn on RDT monitoring for CPU core {} and compare results'.format(CORE),
            'expected_results': 'RDT monitoring is turned on and all event values are decreased significantly'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtMonitorLlcSingleCpuCoreStress

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtMonitorLlcSingleCpuCoreStress, self).__init__(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def prepare(self):  # type: () -> None
        """Test preparation/setup and install the stress tool to sut"""
        super(RdtMonitorLlcSingleCpuCoreStress, self).prepare()
        self._install_collateral.install_stress_tool_to_sut()

    def execute_rdt_monitor_single_cpu_core_stress(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. Turn on RDT monitoring for all events on selected group of cores: pqos -m 'all:10 '
        4. Start memory and cpu load process: taskset -c 10 stress -m 30 -c 30 -t 60
        5. Turn on RDT monitoring for all events on selected group of cores: pqos -m 'all:10 '
            and compare the event values are increased
        6. Turn the stress off
        7. Turn on RDT monitoring for all events on selected group of cores: pqos -m 'all:10 '
            and compare the event values are decreased

        """
        self._test_content_logger.start_step_logger(1)
        # Verify if RDT is installed, If not it will install
        self._rdt.install_rdt()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        # Restore default monitoring: pqos -R
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        # Turn on RDT monitoring for all events on selected single core: pqos -m 'all:10 '
        before_stress_event_values = self._rdt.collect_rdt_monitored_events(pqos_cmd=self.RDT_MONITOR_CMD)
        self._log.debug("RDT event values before running stress is '{}'".format(before_stress_event_values))
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        # Start memory and cpu load process: taskset -c 10 stress -m 30 -c 30 -t 60
        self.os.execute_async(self.TASKSET_CMD)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        # Turn on RDT monitoring for all events on selected single core and compare the event values are increased
        after_stress_event_values = self._rdt.collect_rdt_monitored_events(pqos_cmd=self.RDT_MONITOR_CMD, stress=True)
        self._rdt.check_rdt_event_statistics_increased(before_stress_event_values, after_stress_event_values)
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        # Turn the stress off
        if not self._rdt.is_stress_running():
            raise content_exceptions.TestFail("Stress Tool not running is system")
        self._rdt.stop_stress_tool()
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        # Turn on RDT monitoring for all events on selected single core and compare the event values are decreased
        res_without_stress = self._rdt.collect_rdt_monitored_events(pqos_cmd=self.RDT_MONITOR_CMD)
        self._rdt.check_rdt_event_statistics_decreased(after_stress_event_values, res_without_stress)
        self._test_content_logger.end_step_logger(7, return_val=True)

    def execute(self):
        """
        This method executes the test case with given number of iterations

        :return: True if test case pass
        """
        test_case_status = False
        for index in range(self._rdt.ITERATION):
            try:
                self._log.info("Iteration {}".format(index))
                self.execute_rdt_monitor_single_cpu_core_stress()
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
        super(RdtMonitorLlcSingleCpuCoreStress, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtMonitorLlcSingleCpuCoreStress.main() else Framework.TEST_RESULT_FAIL)
