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

import os
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.lib.test_content_logger import TestContentLogger
from src.lib.dtaf_content_constants import RootDirectoriesConstants
from src.lib import content_base_test_case
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral


class RdtCatEffectivenessMemtesterStreamCmtLatency(content_base_test_case.ContentBaseTestCase):
    """
    HPQC ID : H57902 PI_RDT_C_CAT_Effectiveness_memtester_STREAM_CMTLatency

    This test case aims run the memtester and stream on differenr cores with different COS scanning
    CAT COS bitmask from one bit to all bits, verify the CATs effectiveness on LLC.
    """

    TEST_CASE_ID = ["H57902", "PI_RDT_C_CAT_Effectiveness_memtester_STREAM_CMTLatency"]
    HT_BIOS_CONFIG_FILE = "../disable_ht_bios.cfg"
    ITERATION_STREAM_CMD = 5
    CLOS1_VALUE = "0"
    CLOS2_VALUE = "1"
    LLC_ALLOCATION_ONE = "0:0"
    LLC_ALLOCATION_TWO = "0:1"
    MEMTESTER_TASKSET_CMD_IN_COS1 = "taskset -c 0 memtester 100M"
    STREAM_TASKSET_CMD_IN_COS2 = "taskset -c {} ./example.sh"
    DELAY_EACH_COS_VALUE = 60
    PQOS_CMD_TO_RECORD_LLC = "pqos -m all:0-5 -u csv -o {}"
    PQOS_CSV_FILE = "pqos_mon_57902.csv"

    STEP_DATA_DICT = {
        1: {'step_details': 'Disable Intel HT Technology through the BIOS.',
            'expected_results': 'Disabled Intel HT Technology through the BIOS Successfully'},
        2: {'step_details': 'Install stream tool & Memtester tool if not installed.',
            'expected_results': 'Successfully installed stream & memtester'},
        3: {'step_details': 'Verify RDT is installed in sut',
            'expected_results': 'Installation of RDT is verified successfully'},
        4: {'step_details': 'Restore default monitoring',
            'expected_results': 'Restore to default monitoring is successful'},
        5: {'step_details': 'Run 5 instances of STREAM in CLOS[2] with the following command:'
                            'taskset -c 1 ./stream (keep running)'
                            'taskset -c 2 ./stream (keep running)'
                            'taskset -c 3 ./stream (keep running)'
                            'taskset -c 4 ./stream (keep running)'
                            'taskset -c 5 ./stream (keep running)',
            'expected_results': 'Runs continuously until all cos values assigned'},
        6: {'step_details': 'Use pqos to monitor local and remote memory bandwidth events, and then save the results '
                            'to a CSV file',
            'expected_results': 'Monitored pqos and saved the results in csv file Successfully'},
        7: {'step_details': 'Run one instance of memtester in CLOS[1] with the following command:'
                            'taskset -c 0 ./memtester 100M > /dev/tmp &',
            'expected_results': 'stress applied to core 0'},
        8: {'step_details': 'Set CLOS[1] with access to a single LLC CBM bit (most significant bit [MSB]) '
                            'using the following command'
                            'pqos -a llc:1=0'
                            'pqos -a llc:2=1,2,3,4,5',
            'expected_results': 'Verifies Allocation reset successful'},
        9: {'step_details': 'Set CLOS[1] and CLOS[2] values to LLC Bit with below command and following values'
                            'pqos -e llc@0:1=0x4000'
                            'pqos -e llc@0:2=0x3fff'
                            '(0x4000, 0x3fff), (0x6000, 0x1fff), (0x7000, 0x0fff),(0x7800, 0x7ff)'
                            '(0x7C00, 0x03ff),(0x7E00, 0x01ff), (0x7F00, 0x00FF),(0x7F80, 0x007F)'
                            '(0x7FC0, 0x003F), (0x7FE0, 0x001F), (0x7FF0, 0x000F),(0x7FF8, 0x0007)'
                            '(0x7FFC, 0x0003),(0x7FFE, 0x0001)',
            'expected_results': 'Verifies Allocation reset Successfully'},
        10: {'step_details': 'kill all the process running',
             'expected_results': 'Successfully Kills all the process which are running'},
        11: {'step_details': 'copies the pqos_mon.csv file from sut to host and read'
                             'the pqos_mon.csv file and fetches the required values from pqos output  and'
                             'returns  core 0, core 1,2,3,4,5, sum of both values',
             'expected_results': 'Successfully reads csv file and copied to host '},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtCatEffectivenessMemtesterStreamCmtLatency

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtCatEffectivenessMemtesterStreamCmtLatency, self).__init__(test_log, arguments, cfg_opts,
                                                                           self.HT_BIOS_CONFIG_FILE)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration,
                             self.os, cfg_opts)
        self.stream_folder_path = None
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def prepare(self):  # type: () -> None
        """
        Test preparation/setup and install the stress tool and Memtester to sut
        """
        self._test_content_logger.start_step_logger(1)
        super(RdtCatEffectivenessMemtesterStreamCmtLatency, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._test_content_logger.start_step_logger(2)
        self._install_collateral.install_memtester_tool_to_sut()
        self.stream_folder_path = self._install_collateral.install_rdt_stream_tool_to_sut()
        self._test_content_logger.end_step_logger(2, return_val=True)

    def run_taskset_stream_cmd(self, stream_file_path):
        """
        This method is used to run the taskset command for 5 instances and to run continuously

        :param stream_file_path:file path where stream tool exists on SUT
        """
        self._log.info("Running 5 instances of stream in cos2:")
        self._rdt.run_taskset_file(stream_file_path)
        for instance in range(1, self.ITERATION_STREAM_CMD + 1):
            self.os.execute_async(self.STREAM_TASKSET_CMD_IN_COS2.format(instance), stream_file_path)
            self._log.info("Executing taskset stream command {} COS2".
                           format(self.STREAM_TASKSET_CMD_IN_COS2.format(instance)))
            self._rdt.check_rdt_monitor_command_running_status(self._rdt.STREAM_STR)

    def execute(self):
        """
        This method executes the below:

        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. run the taskset command for 5 instances and to run continuously
        4. run one instance of memtester in core 1
        5. run pqos monitor command to store the values.
        6. Allocate Cache to core
        7. Allocate cos values to core 1 & core 2 to have access to entire LLC CBM bit.
        8. Kills Pqos and taskset command which are running
        9. copies the pqos_mon.csv file from sut to host and read the pqos_mon.csv file
         and fetches the required values from pqos output and returns  core 0, core 1,2,3,4,5, sum of both values and
         saves plotting graph file

         :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(3)
        self._rdt.install_rdt()
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        self.run_taskset_stream_cmd(self.stream_folder_path)
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        self.os.execute_async(self.MEMTESTER_TASKSET_CMD_IN_COS1, RootDirectoriesConstants.LINUX_ROOT_DIR)
        self._rdt.check_rdt_monitor_command_running_status(self._rdt.MEMTESTER_STR)
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        self.os.execute_async(self.PQOS_CMD_TO_RECORD_LLC.format(self.PQOS_CSV_FILE), RootDirectoriesConstants.LINUX_ROOT_DIR)
        self._rdt.check_rdt_monitor_command_running_status(self._rdt.PQOS_STR)
        self._test_content_logger.end_step_logger(7, return_val=True)

        self._test_content_logger.start_step_logger(8)
        self._rdt.set_cache_to_core(self.CLOS1_VALUE, self.CLOS2_VALUE)
        self._test_content_logger.end_step_logger(8, return_val=True)

        self._test_content_logger.start_step_logger(9)
        for cos_values in self._rdt.COS_VALUE_LIST:
            self._rdt.allocate_core1_core2_with_cos_values(cos_values[0], cos_values[1], self.LLC_ALLOCATION_ONE,
                                                           self.LLC_ALLOCATION_TWO)
            time.sleep(self.DELAY_EACH_COS_VALUE)
        self._test_content_logger.end_step_logger(9, return_val=True)

        self._test_content_logger.start_step_logger(10)
        self.os.execute_async(self._rdt.KILL_PQOS_CMD)
        self.os.execute_async(self._rdt.KILL_TASKSET_CMD)
        self._test_content_logger.end_step_logger(10, return_val=True)

        self._test_content_logger.start_step_logger(11)
        read_pqos_mon_values = self._rdt.copy_and_read_csv_file(self.PQOS_CSV_FILE, os.path.join(
            self.log_dir, self.PQOS_CSV_FILE))
        self._log.debug(
            "Value fetched from {} file : {}".format(self.PQOS_CSV_FILE, read_pqos_mon_values))
        self._test_content_logger.end_step_logger(11, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtCatEffectivenessMemtesterStreamCmtLatency.main() else Framework.TEST_RESULT_FAIL)
