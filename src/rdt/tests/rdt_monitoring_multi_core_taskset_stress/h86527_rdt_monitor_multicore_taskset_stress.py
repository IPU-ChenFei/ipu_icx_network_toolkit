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


class RdtMonitoringMultiCoreStress(content_base_test_case.ContentBaseTestCase):
    """
    HPQC ID : H86527-PI_RDT_A_MonitorLLC_MemBW_MultipleCPUCores_stress_L,
              H55276-PI_RDT_A_MonitorLLC_MemBW_MultipleCPUCores_stress,
              H79570-PI_RDT_A_MonitorLLC_MemBW_MultipleCPUCores_stress
    This test case aims to install RDT if it not installed and Check the RDT event values before and after running
    stress via taskset command when stress tool is running.
    """
    TEST_CASE_ID = ["H86527", "PI_RDT_A_MonitorLLC_MemBW_MultipleCPUCores_stress_L",
                    "H55276", "PI_RDT_A_MonitorLLC_MemBW_MultipleCPUCores_stress",
                    "H79570", "PI_RDT_A_MonitorLLC_MemBW_MultipleCPUCores_stress"]
    CORES = "0,1,3,21,22,23"
    RDT_MONITOR_CMD = "pqos -m 'all: {}' -t 10".format(CORES)
    TASKSET_CMD = 'taskset -c {}  stress -m 30 -c 30 -t 60'.format(CORES)
    step_data_dict = {
        1: {'step_details': 'Verify if RDT is installed sut',
            'expected_results': 'Verified installation'},
        2: {'step_details': 'Restore RDT to default monitoring',
            'expected_results': 'Restore RDT to default monitoring is successful'},
        3: {'step_details': 'Turn on RDT monitoring for CPU cores {}'.format(CORES),
            'expected_results': 'RDT monitoring is turned on successfully'},
        4: {'step_details': 'Start memory load on selected cores: {}'.format(CORES),
            'expected_results': 'Stress tool starts to load memory and CPU usage.'},
        5: {'step_details': 'Turn on RDT monitoring for CPU core {} and compare results'.format(CORES),
            'expected_results': 'RDT monitoring is turned on and observed event values are increased after running '
                                'stress'},
        6: {'step_details': 'Turn off memory load stress tool',
            'expected_results': 'No process of taskset should be running for selected cores : {}'.format(CORES)},
        7: {'step_details': 'Turn on RDT monitoring for CPU core {} and compare results'.format(CORES),
            'expected_results': 'RDT monitoring is turned on and observed event values should be equal to 1 or 0'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtMonitoringMultiCoreStress
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtMonitoringMultiCoreStress, self).__init__(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def execute_rdt_monitor_multicore_taskset_stress(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. Turn on RDT monitoring for selected CPU cores: "pqos -m 'all: 0,1,3,21,22,23' -t 0"
        4. Run stress on the selected cores: 'taskset -c 0,1,3,21,22,23 stress -m 30 -c 30 -t 60'
        5. Turn on RDT monitoring for selected cores: "pqos -m 'all: 0,1,3,21,22,23' -t 0"
        6. Compare RDT event values before and after running stress
        7. Stops the Stress and checks the RDT events set to default values

        """
        self._test_content_logger.start_step_logger(1)
        self._rdt.install_rdt()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        res_before_stress = self._rdt.collect_rdt_monitored_events(pqos_cmd=self.RDT_MONITOR_CMD)
        self._test_content_logger.end_step_logger(3, return_val=True)
        self._log.info("Start RDT events on selected cores before stress {}, ".format(res_before_stress))

        self._test_content_logger.start_step_logger(4)
        self._log.info("Start memory load on selected cores {}, ".format(self.CORES))
        self.os.execute_async(self.TASKSET_CMD)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        res_after_stress = self._rdt.collect_rdt_monitored_events(pqos_cmd=self.RDT_MONITOR_CMD, stress=True)
        self._log.info("Start RDT events on selected cores after stress {}, ".format(res_after_stress))
        self._rdt.check_rdt_event_statistics_increased(res_before_stress, res_after_stress)
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        if not self._rdt.is_stress_running():
            raise content_exceptions.TestFail("Stress Tool not running is system")
        self._rdt.stop_stress_tool()
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        res_stop_stress = self._rdt.collect_rdt_monitored_events(pqos_cmd=self.RDT_MONITOR_CMD)
        self._rdt.check_rdt_event_statistics_decreased(res_after_stress, res_stop_stress)
        self._log.info("RDT event values after stopping stress is '{}'".format(res_stop_stress))
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
                self.execute_rdt_monitor_multicore_taskset_stress()
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
        super(RdtMonitoringMultiCoreStress, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtMonitoringMultiCoreStress.main() else Framework.TEST_RESULT_FAIL)
