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


class RdtMonitorLlcAllCpuCoreStress(content_base_test_case.ContentBaseTestCase):
    """
    HPQC ID : H79568-PI_RDT_A_MonitorLLC_MemBW_AllCPUCores_stress_L

    This test case aims to install RDT if it not installed and Check the RDT monitoring functions for all cores with
    pqos command when stress is running on all cores.
    """

    TEST_CASE_ID = ["H79568", "PI_RDT_A_MonitorLLC_MemBW_AllCPUCores_stress_L"]
    START_CORE_RANGE_VAL = 0
    END_CORE_RANGE_VAL = 44
    TASKSET_CMD = "taskset -c {}-{} stress -m 100 -c 100 -t 60".format(START_CORE_RANGE_VAL, END_CORE_RANGE_VAL)
    step_data_dict = {
        1: {'step_details': 'Verify RDT is installed in sut',
            'expected_results': 'Installation of RDT is verified successfully'},
        2: {'step_details': 'Restore default monitoring',
            'expected_results': 'Restore to default monitoring is successful'},
        3: {'step_details': 'Turn on RDT monitoring for all available cpus: pqos',
            'expected_results': 'RDT monitoring is turned on'},
        4: {'step_details': 'start stress tool for group of cores: taskset -c 0-11 stress -m 30 -c 30 -t 60',
            'expected_results': 'Stress tool started to load memory and CPU usage on selected cores'},
        5: {'step_details': 'Turn on RDT monitoring for all available cpus: pqos, and compare event values should '
                            'increase',
            'expected_results': 'RDT monitoring is turned on and all event values are increased significantly'},
        6: {'step_details': 'Turn the stress off',
            'expected_results': 'Turn the stress off successfully.'},
        7: {'step_details': 'Turn on RDT monitoring for all available cpus: pqos, and compare event values should '
                            'decreased',
            'expected_results': 'RDT monitoring is turned on and all event values are decreased significantly'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtMonitorLlcAllCpuCoreStress

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtMonitorLlcAllCpuCoreStress, self).__init__(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def prepare(self):  # type: () -> None
        """Test preparation/setup and install the stress tool to sut"""
        super(RdtMonitorLlcAllCpuCoreStress, self).prepare()
        self._install_collateral.install_stress_tool_to_sut()

    def execute_rdt_monitor_llc_all_cpu_core_stress(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -r
        3. Turn on RDT monitoring for all available cpus: pqos
        4. start stress tool for group of cores: taskset -c 0-44 stress -m 100 -c 100 -t 60
        5. Turn on RDT monitoring for all available cpus: pqos, and compare event values should increase
        6. Turn the stress off
        7. Turn on RDT monitoring for all available cpus: pqos, and compare event values should decrease

        """
        self._test_content_logger.start_step_logger(1)
        self._rdt.install_rdt()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self._rdt.restore_default_monitoring()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        res_before_stress = self._rdt.collect_rdt_monitored_events(start_core_val=self.START_CORE_RANGE_VAL,
                                                                   end_core_val=self.END_CORE_RANGE_VAL)
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self.os.execute_async(self.TASKSET_CMD)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        res_after_stress_starts = self._rdt.collect_rdt_monitored_events(start_core_val=self.START_CORE_RANGE_VAL,
                                                                         end_core_val=self.END_CORE_RANGE_VAL,
                                                                         stress=True)
        self._rdt.check_rdt_event_statistics_increased(res_before_stress, res_after_stress_starts)
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        if not self._rdt.is_stress_running():
            raise content_exceptions.TestFail("Stress Tool not running is system")
        self._rdt.stop_stress_tool()
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        res_after_stress_ends = self._rdt.collect_rdt_monitored_events(start_core_val=self.START_CORE_RANGE_VAL,
                                                                       end_core_val=self.END_CORE_RANGE_VAL)
        self._rdt.check_rdt_event_statistics_decreased(res_after_stress_starts, res_after_stress_ends)
        self._test_content_logger.end_step_logger(7, return_val=True)

    def execute(self):
        """
        This method executes the test case with given number of iterations

        :return: True if test case pass
        """
        test_case_status = False
        for index in range(self._rdt.ITERATION):
            try:
                self._log.info("Iteration {}".format(index+1))
                self.execute_rdt_monitor_llc_all_cpu_core_stress()
                test_case_status = True
                break
            except Exception as e:
                self._log.error("Attempt number {} failed due to {}".format(index+1, e))
            finally:
                if self._rdt.is_stress_running():
                    self._rdt.stop_stress_tool()

        if not test_case_status:
            raise content_exceptions.TestFail("RDT Monitoring functions doesnt show increase in values even after {} "
                                              "iterations".format(self._rdt.ITERATION))

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        if self._rdt.is_stress_running():
            self._rdt.stop_stress_tool()
        super(RdtMonitorLlcAllCpuCoreStress, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtMonitorLlcAllCpuCoreStress.main() else Framework.TEST_RESULT_FAIL)
