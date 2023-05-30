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

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.lib import content_base_test_case
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib.install_collateral import InstallCollateral


class RdtMbmMonitorMemoryMemtester(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow ID : G60244.0-PI_RDT_B_MBMMonitor_Memory_memtester

    This test case aims to install RDT if it not installed and also installs memtester tool and
    verify that CMT Monitor MBL occupancy for cores/tasks via pqos OS interface when memtester is running
    """
    TEST_CASE_ID = ["G60244.0", "PI_RDT_B_MBMMonitor_Memory_memtester"]
    CORE = 4
    MEMTESTER_CMD = "taskset -c {} memtester 100M".format(CORE)
    MBM_MEMTESTER_CMD = "memtester 100M"
    MBM_MONITOR_CMD = "pqos -m mbl:0-23 -m mbr:0-23 -t 30"
    MBM_TASK_CMD = "pqos -I -p mbl:{} -p mbl:1 -p mbr:{} -p mbr:1 -t 30"
    MBM_CAP_COMMAND = "pqos -d"
    EVENT_LIST = ["MBL[MB/s]"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Verify if RDT is installed on sut',
            'expected_results': 'Verified installation'},
        2: {'step_details': 'Restore RDT to default monitoring',
            'expected_results': 'Restore RDT to default monitoring is successful'},
        3: {'step_details': 'Verify MBM capability is detected on platform',
            'expected_results': 'MBM capability is detected successfully on platform'},
        4: {'step_details': 'Start memtester process by executing command taskset -c 4 memtester 100M',
            'expected_results': 'Memtester process started to load memory and CPU usage'},
        5: {'step_details': 'Turn on RDT monitoring for MBM events on all core: pqos -m mbl:0-23 -m mbr:0-23 -t 30 and '
                            'check if values are high for core 4',
            'expected_results': 'RDT monitoring is turned on and observed event values are high for core 4'},
        6: {'step_details': 'Turn the memtester off',
            'expected_results': 'Memtester is turned off successfully'},
        7: {'step_details': 'Verify MBM values for task id by running memtester in background and '
                            'MBM monitoring and check if values are high for memtester pid value and turn off '
                            'memtester',
            'expected_results': 'Memtester is running successfully, MBM monitoring successful with values higher for '
                                'pid memtester value'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtMbmMonitorMemoryMemtester

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtMbmMonitorMemoryMemtester, self).__init__(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):  # type: () -> None
        """Test preparation/setup and install the stress tool to sut"""
        super(RdtMbmMonitorMemoryMemtester, self).prepare()
        self._install_collateral.install_memtester_tool_to_sut()

    def execute(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -I -R
        3. Verify MBM capability is detected on platform
        4. Start memtester process by executing command taskset -c 4 memtester 100M
        5. Turn on RDT monitoring for MBM events on all core: pqos -m mbl:0-23 -m mbr:0-23 and
            check if values are high for core 4
        6. Turn the Memtester off
        7. Verify MBM values for task id by running memtester in background and MBM monitoring and check if values
            are high for memtester pid value and turn off memtester

        :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(1)
        # Verify if RDT is installed, If not it will install
        self._rdt.install_rdt()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        # Restore default monitoring: pqos -R
        self._rdt.restore_default_monitoring(self)
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        # Verify MBM capability is detected on platform
        self._rdt.verify_mbm_capability(mbm_capability_command=self.MBM_CAP_COMMAND)
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        # Start memtester process: taskset -c 4 memtester 100M
        self.os.execute_async(self.MEMTESTER_CMD)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        # Turn on RDT monitoring for MBM events on all core: pqos -m mbl:0-23 -m mbr:0-23
        self._rdt.check_cmt_event_core(pqos_cmd=self.MBM_MONITOR_CMD, core_value=self.CORE, event=self.EVENT_LIST)
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        # Turn off memtester
        self._rdt.stop_memtester_tool()
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        # Execute memtester command
        self.os.execute_async(cmd=self.MBM_MEMTESTER_CMD)
        # Get process id of memtester command
        pid_value = self._rdt.get_pid_value()
        # Check whether MBL value is much higher than memtester process id value
        self._rdt.check_cmt_event_taskid(cmt_task_cmd=self.MBM_TASK_CMD.format(pid_value, pid_value), task_id=pid_value,
                                         event=self.EVENT_LIST)
        # Turn off memtester
        self._rdt.stop_memtester_tool()
        self._test_content_logger.end_step_logger(7, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtMbmMonitorMemoryMemtester.main() else Framework.TEST_RESULT_FAIL)
    