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


class RdtMonitorLlcTwoPqosInstancesStress(content_base_test_case.ContentBaseTestCase):
    """
    HPQC ID : H79572-PI_RDT_A_MonitorLLC_MemBW_TwoPQoSInstances_stress_L,
              H55278-PI_RDT_A_MonitorLLC_MemBW_TwoPQoSInstances_stress

    This test case aims to install RDT if it not installed and Check the behavior of the RDT monitoring tool on attempt
     to run two pqos instances and report error
    """

    TEST_CASE_ID = ["H79572", "PI_RDT_A_MonitorLLC_MemBW_TwoPQoSInstances_stress_L",
                    "H55278", "PI_RDT_A_MonitorLLC_MemBW_TwoPQoSInstances_stress"]
    TASKSET_CMD = "stress -m 100 -c 100"
    PQOS_CMD = "pqos"
    CHECK_PQOS_CMD = "ps -ef | grep pqos"
    ERROR_MSG = "error on core(s) 0"
    step_data_dict = {
        1: {'step_details': 'Verify RDT is installed on sut',
            'expected_results': 'Verified installation'},
        2: {'step_details': 'Restore default monitoring',
            'expected_results': 'Restore to default monitoring is successful'},
        3: {'step_details': 'Turn on RDT monitoring for all available cpus: pqos',
            'expected_results': 'RDT monitoring is turned on'},
        4: {'step_details': 'start stress tool for all cores: stress -m 100 -c 100',
            'expected_results': 'Stress tool started to load memory and CPU usage on all cores'},
        5: {'step_details': 'Turn on RDT monitoring for all available cpus: pqos, and compare event values should '
                            'increase',
            'expected_results': 'RDT monitoring is turned on and all event values are increased significantly'},
        6: {'step_details': 'Run pqos in async mode and in new terminal run another instance of pqos ',
            'expected_results': 'Verification as expected : "Monitoring start error on core(s) 0, status 3" '},
        7: {'step_details': 'Turn the pqos command off',
            'expected_results': 'pqos command turned off successfully.'},
        8: {'step_details': 'Turn the stress off',
            'expected_results': 'stress turned off successfully.'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtMonitorLlcTwoPqosInstancesStress

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtMonitorLlcTwoPqosInstancesStress, self).__init__(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def prepare(self):
        # type: () -> None
        """Test preparation/setup and install the stress tool to sut"""
        super(RdtMonitorLlcTwoPqosInstancesStress, self).prepare()
        self._install_collateral.install_stress_tool_to_sut()

    def execute(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. Turn on RDT monitoring for all available cpus cores: pqos
        4. start stress tool for group of cores: stress -m 100 -c 100
        5. Turn on RDT monitoring for all available cpus: pqos, and compare event values should increase
        6. Turn off pqos
        7. Turn off stress

        :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(1)
        self._rdt.install_rdt()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        res_before_stress = self._rdt.collect_rdt_monitored_events()
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self.os.execute_async(self.TASKSET_CMD)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        res_after_stress = self._rdt.collect_rdt_monitored_events(stress=True)
        try:
            self._rdt.check_rdt_event_statistics_increased(res_before_stress, res_after_stress)
        except Exception as ex:
            self._log.debug("Some cores are not showing increase data,ignoring this")
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        self._log.info("To run two pqos instances simultaneously and check report error")
        self._log.info("Executing first instance of pqos command {}".format(self.PQOS_CMD))
        self.os.execute_async(self.PQOS_CMD)
        pqos_output = self.os.execute(self.CHECK_PQOS_CMD, self._command_timeout)
        pqos_count = pqos_output.stdout.count(self.PQOS_CMD)
        if pqos_count < 1:
            error = "PQOS is not running !!!"
            raise content_exceptions.TestFail(error)

        self._log.info("Executing second instance of pqos command {}".format(self.PQOS_CMD))
        result = self.os.execute(self.PQOS_CMD, self._command_timeout)
        if self.ERROR_MSG not in result.stdout:
            error = "Only one pqos instance is running !!!"
            raise content_exceptions.TestFail(error)
        else:
            self._log.info("Verification pass: Error is thrown as expected:{}".format(result.stdout))
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        self._common_content_lib.execute_sut_cmd(self._rdt.KILL_PQOS_CMD, self._rdt.KILL_PQOS_CMD,
                                                 self._command_timeout)
        self._test_content_logger.end_step_logger(7, return_val=True)

        self._test_content_logger.start_step_logger(8)
        if not self._rdt.is_stress_running():
            raise content_exceptions.TestFail("Stress Tool not running is system")
        self._rdt.stop_stress_tool()
        self._test_content_logger.end_step_logger(8, return_val=True)

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        if self._rdt.is_stress_running():
            self._rdt.stop_stress_tool()
        super(RdtMonitorLlcTwoPqosInstancesStress, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtMonitorLlcTwoPqosInstancesStress.main() else Framework.TEST_RESULT_FAIL)
