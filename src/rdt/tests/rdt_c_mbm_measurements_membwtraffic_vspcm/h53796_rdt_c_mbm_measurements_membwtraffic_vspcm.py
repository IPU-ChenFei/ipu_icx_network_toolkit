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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.lib.content_base_test_case import ContentBaseTestCase

from src.lib.test_content_logger import TestContentLogger
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral


class RdtCMbmMeasurementsMemBWTrafficvsPCM(ContentBaseTestCase):
    """
    HPQC ID : H53796-PI_RDT_C_MBM_Measurements_memBWTraffic_vsPCM

    This test case aims to install RDT if it not installed and Run MBM Measurements with
    Write/ NT Write Traffic for local and remote memory  from memBW application,
    to verify the MBM and PCM result coherence.
    """

    TEST_CASE_ID = ["H53796", "PI_RDT_C_MBM_Measurements_memBWTraffic_vsPCM"]
    NUMACTL_MEMBW_NT_WRITE_CMD = "numactl --membind=1 ./membw -c 1 -b 20000 --nt-write"
    NUMACTL_MEMBW_WRITE_CMD = "numactl --membind=1 ./membw -c 1 -b 20000 --write"
    PQOS_CMD = "pqos -m all:1 -u csv -o {} -t 30"
    PCM_CMD = "./pcm-memory.x -csv > {}"
    PQOS_LOCAL = "/root/pqos_local_mon.csv"
    PCM_LOCAL = "test_local.csv"
    PQOS_REMOTE_NT_WRITE = "/root/pqos_remote_nt_write.csv"
    PCM_REMOTE_NT_WRITE = "test_remote_nt_write.csv"
    PQOS_REMOTE_WRITE = "/root/pqos_remote_write.csv"
    PCM_REMOTE_WRITE = "pcm_remote_write.csv"

    step_data_dict = {
        1: {'step_details': 'Verify RDT is installed in sut',
            'expected_results': 'Installation od RDT is verified successfully'},
        2: {'step_details': 'Restore default monitoring',
            'expected_results': 'Restore to default monitoring is successful'},
        3: {'step_details': 'Run membw pinned to a core generating specified memory bandwidth',
            'expected_results': 'membw is successfully running in the background'},
        4: {'step_details': 'Use pqos to monitor local and remote memory bandwidth '
                            'events: pqos -m all:1 -u csv -o pqos_mon.csv -t 30',
            'expected_results': 'pqos executed to monitor local and remote memory bandwidth events'},
        5: {'step_details': 'Use Intel PCM to monitor local and remote socket memory bandwidth :'
                            './pcm-memory.x -csv > test.csv',
            'expected_results': 'Intel PCM executed to monitor local and remote socket memory bandwidth'},
        6: {'step_details': 'Check the average of MBL[MB/s] in pqos_mon.csv and average of Memory (MB/s) '
                            'in test.csv and stop membw ',
            'expected_results': 'Verified that the average of MBL[MB/s] and average of Memory (MB/s) are almost the same.'},
        7: {'step_details': 'Run membw operation pinned to a core generating specified memory bandwidth '
                            'with the following command: numactl --membind=1 ./membw -c 1 -b 20000 --nt-write',
            'expected_results': 'membw is successfully running in the background'},
        8: {'step_details': 'Use pqos to monitor local and remote memory bandwidth events :'
                            'pqos -m all:1 -u csv -o pqos_mon.csv -t 30',
            'expected_results': 'pqos executed to monitor local and remote memory bandwidth events'},
        9: {'step_details': 'Use Intel PCM to monitor local and remote socket memory bandwidth :'
                            './pcm-memory.x -csv > test.csv',
            'expected_results': 'Intel PCM executed to monitor local and remote socket memory bandwidth'},
        10: {'step_details': 'Check the average of MBR[MB/s] in pqos_mon.csv and average of Memory (MB/s) '
                             'in test.csv and stop membw.',
             'expected_results': 'Verified that the average of MBR[MB/s] is double of the average of Memory (MB/s)'},
        11: {'step_details': 'Run membw operation pinned to a core generating specified memory bandwidth '
                             'with the following command: numactl --membind=1 ./membw -c 1 -b 20000 --write',
             'expected_results': 'membw is successfully running in the background'},
        12: {'step_details': 'Use pqos to monitor local and remote memory bandwidth events :'
                             'pqos -m all:1 -u csv -o pqos_mon.csv -t 30',
             'expected_results': 'pqos executed to monitor local and remote memory bandwidth events'},
        13: {'step_details': 'Use Intel PCM to monitor local and remote socket memory bandwidth :'
                             './pcm-memory.x -csv > test.csv',
             'expected_results': 'Intel PCM executed to monitor local and remote socket memory bandwidth'},
        14: {'step_details': 'Check the average of MBR[MB/s] in pqos_mon.csv and average of Memory (MB/s) '
                             'in test.csv and stop membw.',
             'expected_results': 'Verified that the average of MBR[MB/s] is lesser than the average of Memory (MB/s)'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtCMbmMeasurementsMemBWTrafficvsPCM

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtCMbmMeasurementsMemBWTrafficvsPCM, self).__init__(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def prepare(self):  # type: () -> None
        """Test preparation/setup and install the stress tool to sut"""
        super(RdtCMbmMeasurementsMemBWTrafficvsPCM, self).prepare()

    def execute(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. Run membw pinned to a core generating specified memory bandwidth with the
           following command: ./membw -c 1 -b 20000 --nt-write
        4. Use pqos to monitor local and remote memory bandwidth events :
           pqos -m all:1 -u csv -o pqos_mon.csv -t 30
        5. Use Intel PCM to monitor local and remote socket memory bandwidth:
           ./pcm-memory.x -csv > test.csv
        6. Check the average of MBL[MB/s] in pqos_mon.csv and average of Memory (MB/s)
           in test.csv and stop membw
        7. Run membw write or nt-write operation pinned to a core generating specified
           memory bandwidth with the following command: numactl --membind=1 ./membw -c 1 -b 20000 --nt-write
        8. Use pqos to monitor local and remote memory bandwidth events :
           pqos -m all:1 -u csv -o pqos_mon.csv -t 30
        9. Use Intel PCM to monitor local and remote socket memory bandwidth:
           ./pcm-memory.x -csv > test.csv
        10.Check the average of MBR[MB/s] in pqos_mon.csv and average of Memory (MB/s)
           in test.csv and stop membw.
        11.Run membw pinned to a core generating specified
           memory bandwidth with the following command:numactl --membind=1 ./membw -c 1 -b 20000 --write
        12. Use pqos to monitor local and remote memory bandwidth events :
           pqos -m all:1 -u csv -o pqos_mon.csv -t 30
        13. Use Intel PCM to monitor local and remote socket memory bandwidth:
           ./pcm-memory.x -csv > test.csv
        14.Check the average of MBR[MB/s] in pqos_mon.csv and average of Memory (MB/s)
           in test.csv and stop membw.

        :raise : contentExceptions.TestFail if the testcase fails
        """
        self._test_content_logger.start_step_logger(1)
        self._rdt.install_rdt()
        pcm_tool_path = self._install_collateral.install_pcm_tool()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Run membw pinned to a core generating specified memory bandwidth with the
        # following command: ./membw -c 1 -b 20000 --nt-write
        self._test_content_logger.start_step_logger(3)
        # kill membw if its running else ignore
        self.os.execute_async(self._rdt.KILL_CMD.format(self._rdt.MEMBW_STR))
        membw_tool_path = self._rdt.get_membw_path()
        self._log.info("Run a membw instance on core 1")
        if not self._rdt.start_stress_tool(membw_tool_path,
                                           self._rdt.MEMBW_STRESS_CORE_CMD.format(self._rdt.CORE1)):
            raise content_exceptions.TestFail("Failed to run the membw stress tool on SUT")
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Use pqos to monitor local and remote memory bandwidth events :
        # pqos -m all:1 -u csv -o pqos_mon.csv -t 30
        self._test_content_logger.start_step_logger(4)
        self.os.execute_async(self.PQOS_CMD.format(self.PQOS_LOCAL))
        self._rdt.check_rdt_monitor_running_status(self.PQOS_CMD.format(self.PQOS_LOCAL))
        pqos_local_mbl_avg_value = self._rdt.get_average_values_from_pqos(self.PQOS_LOCAL, os.path.join(self.log_dir,
                                                                                                        self.PQOS_LOCAL.split(
                                                                                                            "/")[-1]),
                                                                          mbl=True)
        self._log.debug("Value fetched from {} file : {}".format(self.PQOS_LOCAL, pqos_local_mbl_avg_value))
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Use Intel PCM to monitor local and remote socket memory bandwidth:
        # ./pcm-memory.x -csv > test.csv
        self._test_content_logger.start_step_logger(5)
        pcm_local_average_memory = self._rdt.run_pcm_tool(self.PCM_CMD, self.PCM_LOCAL,
                                                          os.path.join(self.log_dir, self.PCM_LOCAL), pcm_tool_path)
        self._log.info(
            "Monitored local socket memory bandwidth value from Intel PCM tool: {}".format(pcm_local_average_memory))
        self._test_content_logger.end_step_logger(5, return_val=True)

        # Check the average of MBL[MB/s] in pqos_mon.csv and average of Memory (MB/s)
        # in test.csv and stop membw
        self._test_content_logger.start_step_logger(6)
        if not float(pqos_local_mbl_avg_value) - float(pqos_local_mbl_avg_value) * 0.1 <= float(
                pcm_local_average_memory) and not float(pcm_local_average_memory) <= float(
            pqos_local_mbl_avg_value) + float(
            pqos_local_mbl_avg_value) * 0.1:
            raise content_exceptions.TestFail("The average of MBL[MB/s] in pqos_mon.csv and average of Memory(MB/s)"
                                              " are not same as expected")
        self._log.info("The average of MBL[MB/s]:{} in pqos_mon.csv and average of Memory(MB/s):{} are "
                       "almost same as expected".format(pqos_local_mbl_avg_value, pcm_local_average_memory))
        self.os.execute_async(self._rdt.KILL_CMD.format(self._rdt.MEMBW_STR))
        self._test_content_logger.end_step_logger(6, return_val=True)

        # Run membw write or nt-write operation pinned to a core generating specified
        # memory bandwidth with the following command: numactl --membind=1 ./membw -c 1 -b 20000 --nt-write
        self._test_content_logger.start_step_logger(7)
        self._log.info(" Run a membw instance on core 1")
        if not self._rdt.start_stress_tool(membw_tool_path, self.NUMACTL_MEMBW_NT_WRITE_CMD):
            raise content_exceptions.TestFail("Failed to run the membw stress tool on SUT")
        self._test_content_logger.end_step_logger(7, return_val=True)

        # Use pqos to monitor local and remote memory bandwidth events :
        # pqos -m all:1 -u csv -o pqos_mon.csv -t 30
        self._test_content_logger.start_step_logger(8)
        self.os.execute_async(self.PQOS_CMD.format(self.PQOS_REMOTE_NT_WRITE))
        self._rdt.check_rdt_monitor_running_status(self.PQOS_CMD.format(self.PQOS_REMOTE_NT_WRITE))
        pqos_remote_ntwrite_mbr_avg_value = self._rdt.get_average_values_from_pqos(self.PQOS_REMOTE_NT_WRITE,
                                                                                   os.path.join(self.log_dir,
                                                                                                self.PQOS_REMOTE_NT_WRITE.split(
                                                                                                    "/")[-1]),
                                                                                   mbl=False)
        self._log.debug(
            "Value fetched from {} file : {}".format(self.PQOS_REMOTE_NT_WRITE, pqos_remote_ntwrite_mbr_avg_value))
        self._log.info("Average MBL[MB/s]")
        self._test_content_logger.end_step_logger(8, return_val=True)

        # Use Intel PCM to monitor local and remote socket memory bandwidth:
        # ./pcm-memory.x -csv > test.csv
        self._test_content_logger.start_step_logger(9)
        pcm_remote_ntwrite_average_memory = self._rdt.run_pcm_tool(self.PCM_CMD, self.PCM_REMOTE_NT_WRITE,
                                                                   os.path.join(self.log_dir, self.PCM_REMOTE_NT_WRITE),
                                                                   pcm_tool_path)
        self._log.info(
            "Monitored local socket memory bandwidth value from Intel PCM tool: {}".format(
                pcm_remote_ntwrite_average_memory))
        self._test_content_logger.end_step_logger(9, return_val=True)

        # Check the average of MBR[MB/s] in pqos_mon.csv and average of Memory (MB/s)
        # in test.csv and stop membw
        self._test_content_logger.start_step_logger(10)
        if not float(pqos_remote_ntwrite_mbr_avg_value) - float(pqos_remote_ntwrite_mbr_avg_value) * 0.1 \
               <= 2 * float(pcm_remote_ntwrite_average_memory) and not 2 * float(pcm_remote_ntwrite_average_memory) \
               <= float(pqos_remote_ntwrite_mbr_avg_value) + float(pqos_remote_ntwrite_mbr_avg_value) * 0.1:
            raise content_exceptions.TestFail("The average of MBR[MB/s] is not almost double the average of Memory("
                                              "MB/s) as Expected")
        self._log.info("The average of MBR[MB/s]: {} is double of the average of Memory (MB/s): {} as expected".
                       format(pqos_remote_ntwrite_mbr_avg_value, pcm_remote_ntwrite_average_memory))

        self.os.execute_async(self._rdt.KILL_CMD.format(self._rdt.MEMBW_STR))
        self._test_content_logger.end_step_logger(10, return_val=True)

        # Run membw write or nt-write operation pinned to a core generating specified
        # memory bandwidth with the following command: numactl --membind=1 ./membw -c 1 -b 20000 --write
        self._test_content_logger.start_step_logger(11)
        self._log.info(" Run a membw instance on core 1")
        if not self._rdt.start_stress_tool(membw_tool_path, self.NUMACTL_MEMBW_WRITE_CMD):
            raise content_exceptions.TestFail("Failed to run the membw stress tool on SUT")
        self._test_content_logger.end_step_logger(11, return_val=True)

        # Use pqos to monitor local and remote memory bandwidth events :
        # pqos -m all:1 -u csv -o pqos_mon.csv -t 30
        self._test_content_logger.start_step_logger(12)
        self.os.execute_async(self.PQOS_CMD.format(self.PQOS_REMOTE_WRITE))
        self._rdt.check_rdt_monitor_running_status(self.PQOS_CMD.format(self.PQOS_REMOTE_WRITE))
        pqos_remote_write_mbr_avg_value = self._rdt.get_average_values_from_pqos(self.PQOS_REMOTE_WRITE,
                                                                                 os.path.join(self.log_dir,
                                                                                              self.PQOS_REMOTE_WRITE.split(
                                                                                                  "/")[-1]), mbl=False)
        self._log.debug(
            "Value fetched from {} file : {}".format(self.PQOS_REMOTE_WRITE, pqos_remote_write_mbr_avg_value))
        self._test_content_logger.end_step_logger(12, return_val=True)

        # Use Intel PCM to monitor local and remote socket memory bandwidth:
        # ./pcm-memory.x -csv > test.csv
        self._test_content_logger.start_step_logger(13)
        pcm_remote_write_average_memory = self._rdt.run_pcm_tool(self.PCM_CMD, self.PCM_REMOTE_WRITE,
                                                                 os.path.join(self.log_dir, self.PCM_REMOTE_WRITE),
                                                                 pcm_tool_path)
        self._log.info(
            "Monitored local socket memory bandwidth value from Intel PCM tool: {}".format(
                pcm_remote_write_average_memory))
        self._test_content_logger.end_step_logger(13, return_val=True)

        # Check the average of MBR[MB/s] in pqos_mon.csv and average of Memory (MB/s)
        # in test.csv and stop membw
        self._test_content_logger.start_step_logger(14)
        if not float(pqos_remote_write_mbr_avg_value) <= float(pcm_remote_write_average_memory):
            raise content_exceptions.TestFail("The average of MBR[MB/s] is not lesser than the average of Memory("
                                              "MB/s) as Expected")
        self._log.info("The average of MBR[MB/s] : {} is lesser than the average of Memory (MB/s) : {} as Expected".
                       format(pqos_remote_write_mbr_avg_value, pcm_remote_write_average_memory))
        self.os.execute_async(self._rdt.KILL_CMD.format(self._rdt.MEMBW_STR))
        self._test_content_logger.end_step_logger(14, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtCMbmMeasurementsMemBWTrafficvsPCM.main() else Framework.TEST_RESULT_FAIL)
