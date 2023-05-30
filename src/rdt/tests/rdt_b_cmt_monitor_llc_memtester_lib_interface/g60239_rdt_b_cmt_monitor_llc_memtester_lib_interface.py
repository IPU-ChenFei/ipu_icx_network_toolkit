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


class RdtCmtMonitorLlcMemtesterLibInterface(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow ID : G60239.1 - PI_RDT_B_CMTMonitor_LLC_memtester_LibInterface

    This test case aims to install RDT if it not installed and also installs memtester tool and
    verify that CMT Monitor LLC occupancy for cores/tasks via pqos OS interface when memtester is running
    """
    TEST_CASE_ID = ["G60239.1-PI_RDT_B_CMTMonitor_LLC_memtester_LibInterface"]
    CORE = 4
    MEMTESTER_CMD = "taskset -c {} memtester 100M".format(CORE)
    CMT_MEMTESTER_CMD = "memtester 100M"
    CMT_MONITOR_CMD = "pqos -I -m llc:0-23 -t 30"
    CMT_TASK_CMD = "pqos -I -p llc:{} -p llc:1 -t 30"
    CMT_CAP_COMMAND = "pqos -I -d"
    CMT_EVENTS_INFO = "Cache Monitoring Technology .CMT. events:\s+LLC Occupancy .LLC."
    EVENT_LIST = ["LLC[KB]"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Verify if RDT is installed on sut',
            'expected_results': 'Verified installation'},
        2: {'step_details': 'Restore RDT to default monitoring',
            'expected_results': 'Restore RDT to default monitoring is successful'},
        3: {'step_details': 'Verify CMT capability is detected on platform',
            'expected_results': 'CMT capability is detected successfully on platform'},
        4: {'step_details': 'Start memtester process by executing command taskset -c 4 memtester 100M',
            'expected_results': 'Memtester process started to load memory and CPU usage'},
        5: {'step_details': 'Turn on RDT monitoring for CMT events on all core: pqos -m llc:0-23 -t 30 and '
                            'check if values are high for core 4',
            'expected_results': 'RDT monitoring is turned on and observed event values are high for core 4'},
        6: {'step_details': 'Turn the memtester off',
            'expected_results': 'Memtester is turned off successfully'},
        7: {'step_details': 'Verify CMT values for task id by running memtester in background and '
                            'CMT monitoring and check if values are high for memtester pid value and turn off '
                            'memtester',
            'expected_results': 'Memtester is running successfully, CMT monitoring successful with values higher for '
                                'pid memtester value'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtCmtMonitorLlcMemtesterLibInterface

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtCmtMonitorLlcMemtesterLibInterface, self).__init__(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def prepare(self):  # type: () -> None
        """Test preparation/setup and install the stress tool to sut"""
        super(RdtCmtMonitorLlcMemtesterLibInterface, self).prepare()
        self._install_collateral.install_memtester_tool_to_sut()

    def execute(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -I -r
        3. Verify CMT capability is detected on platform
        4. Start memtester process by executing command taskset -c 4 memtester 100M
        5. Turn on RDT monitoring for CMT events on all core: pqos -I -m llc:0-23 -t 30 and
            check if values are high for core 4
        6. Turn the Memtester off
        7. Verify CMT values for task id by running memtester in background and CMT monitoring and check if values
            are high for memtester pid value and turn off memtester

        :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(1)
        # Verify if RDT is installed, If not it will install
        self._rdt.install_rdt()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        # Restore default monitoring: pqos -r
        self._rdt.restore_default_monitoring(interface=True)
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        # Verify CMT capability is detected on platform
        self._rdt.verify_cmt_capability(command=self.CMT_CAP_COMMAND)
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        # Start memtester process: taskset -c 4 memtester 100M
        self.os.execute_async(self.MEMTESTER_CMD)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        # Turn on RDT monitoring for CMT events on all core: pqos -m llc:0-23 -t 30
        self._rdt.check_cmt_event_core(pqos_cmd=self.CMT_MONITOR_CMD, core_value=self.CORE, event=self.EVENT_LIST)
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        # Turn off memtester
        self._rdt.stop_memtester_tool()
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        self.os.execute_async(cmd=self.CMT_MEMTESTER_CMD)
        pid_value = self._rdt.get_pid_value()
        self._rdt.check_cmt_event_taskid(cmt_task_cmd=self.CMT_TASK_CMD.format(pid_value), task_id=pid_value,
                                         event=self.EVENT_LIST)
        self._rdt.stop_memtester_tool()
        self._test_content_logger.end_step_logger(7, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtCmtMonitorLlcMemtesterLibInterface.main() else Framework.TEST_RESULT_FAIL)
