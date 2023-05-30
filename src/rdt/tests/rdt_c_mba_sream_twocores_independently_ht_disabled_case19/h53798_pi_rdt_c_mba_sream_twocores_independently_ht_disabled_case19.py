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
import re
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib.content_base_test_case import ContentBaseTestCase
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions
from src.security.lib.cpu_device_info import CpuDeviceInfo


class RdtCMbaStreamTwoCoresIndependentlyHTDisabledCase19(ContentBaseTestCase):
    """
    HPALM ID : H53798-PI_RDT_C_MBA_Sream_TwoCores_Independently_HTDisabled_case19

    This test case aims to install RDT if it not installed and
    verify Run MBA one two independent cores, verify if return BW are independent.
    """
    TEST_CASE_ID = ["H53798", "PI_RDT_C_MBA_Sream_TwoCores_Independently_HTDisabled_case19"]
    HT_BIOS_CONFIG_FILE = "disable_ht_bios.cfg"
    PQOS_BEFORE_STRESS = "pqos_mon_before_stress.csv"
    PQOS_AFTER_50_STRESS = "pqos_mon_50.csv"
    PQOS_AFTER_10_STRESS = "pqos_mon_10.csv"
    PQOS_AFTER_90_STRESS = "pqos_mon_90.csv"

    STEP_DATA_DICT = {
        1: {'step_details': 'Disable Intel HT Technology through the BIOS.',
            'expected_results': 'Disabled Intel HT Technology through the BIOS Successfully'},
        2: {'step_details': 'Verify RDT is installed in sut',
            'expected_results': 'Installation of RDT is verified successfully'},
        3: {'step_details': 'Restore default monitoring',
            'expected_results': 'Restore to default monitoring is successful'},
        4: {'step_details': 'Install membw tool if not installed.',
            'expected_results': 'Successfully installed membw'},
        5: {'step_details': 'Run a STREAM benchmark instance on core 0 and core 1 on Socket 0',
            'expected_results': 'verified that STREAM benchmark instance is running on core 0 and core 1'},
        6: {'step_details': 'Monitor per-core memory bandwidth using the MBM feature of Intel RDT on Socket 0',
            'expected_results': 'Monitored per-core memory bandwidth'},
        7: {'step_details': 'Associate core 0 to CLOS[0] and core 1 to CLOS[1] on Socket 0',
            'expected_results': 'Core Association successfull'},
        8: {'step_details': 'Set CLOS[0] and CLOS[1] to 50 percent throttling on Socket 0',
            'expected_results': 'Set CLOS[0] and CLOS[1] to 50 percent throttling successfully'},
        9: {'step_details': 'Note the memory bandwidth for core 0 and core 1 on Socket 0',
            'expected_results': 'The MBL for core 0 and core 1 decreased to 50% as expected'},
        10: {'step_details': 'Modify CLOS[0] from 50 percent to 10 percent and then note the bandwidth on both the '
                             'cores on Socket 0',
             'expected_results': 'Observe that core 1’s bandwidth is NOT impacted'},
        11: {'step_details': 'Modify CLOS[0] from 50 percent to 90 percent and then note the bandwidth on both the '
                             'cores on Socket 0',
             'expected_results': 'Observe that core 1’s bandwidth is NOT impacted'},
        12: {'step_details': 'Restore default monitoring',
             'expected_results': 'Restore to default monitoring is successful'},
        13: {'step_details': 'Monitor per-core memory bandwidth using the MBM feature of Intel RDT on Socket 1',
             'expected_results': 'Monitored per-core memory bandwidth'},
        14: {'step_details': 'Associate core 0 to CLOS[0] and core 1 to CLOS[1] on Socket 1',
             'expected_results': 'Core Association successfull'},
        15: {'step_details': 'Set CLOS[0] and CLOS[1] to 50 percent throttling on Socket 1',
             'expected_results': 'Set CLOS[0] and CLOS[1] to 50 percent throttling successfully'},
        16: {'step_details': 'Note the memory bandwidth for core 0 and core 1 on Socket 1',
             'expected_results': 'The MBL for core 0 and core 1 decreased to 50% as expected'},
        17: {
            'step_details': 'Modify CLOS[0] from 50 percent to 10 percent and then note the bandwidth on both the on '
                            'cores Socket 1',
            'expected_results': 'Observe that core 1’s bandwidth is NOT impacted'},
        18: {'step_details': 'Modify CLOS[0] from 50 percent to 90 percent and then note the bandwidth on both the '
                             'cores on Socket 1',
             'expected_results': 'Observe that core 1’s bandwidth is NOT impacted'},
        19: {'step_details': 'Restore default monitoring',
             'expected_results': 'Restore to default monitoring is successful'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtCMbaStreamTwoCoresIndependentlyHTDisabledCase19

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.ht_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.HT_BIOS_CONFIG_FILE)
        super(RdtCMbaStreamTwoCoresIndependentlyHTDisabledCase19, self).__init__(test_log, arguments, cfg_opts,
                                                                                 bios_config_file_path=self.ht_bios_config_file)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def prepare(self):  # type: () -> None
        """Test preparation/setup and install the stress tool to sut"""
        self._test_content_logger.start_step_logger(1)
        super(RdtCMbaStreamTwoCoresIndependentlyHTDisabledCase19, self).prepare()
        # fetch the core numbers from lscpu command
        lscpu_cmd_output = self._common_content_lib.execute_sut_cmd("lscpu", "lscpu", self._command_timeout)
        lscpu_data = CpuDeviceInfo.parse_cpu_output_data(lscpu_cmd_output)
        if int(lscpu_data["Socket(s)"]) < 2:
            log_error = "This Test Only Supported on Systems which contains Atleast 2 Sockets"
            self._log.error(log_error)
            raise content_exceptions.TestFail(log_error)
        self.socket0_core0 = int(lscpu_data["NUMA node0 CPU(s)"].split("-")[0])
        self.socket1_core0 = int(lscpu_data["NUMA node1 CPU(s)"].split("-")[0])
        self.socket0_core1 = self.socket0_core0 + 1
        self.socket1_core1 = self.socket1_core0 + 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. Disable Intel HT Technology through the BIOS.,
        4. Make sure all the cores are set to default RMID/CLOS values.
            # pqos -R
        5. Run a STREAM benchmark instance on core 0 and core 1 with the following commands:
            ./membw -c 1 -b 20000 --nt-write
            Keep the stress running
        6. Monitor per-core memory bandwidth using the MBM feature of Intel RDT using the
           following command: # pqos -m all:0,1 -u csv -o pqos_mon.csv
        7. Associate core 0 to CLOS[0] and core 1 to CLOS[1] using the following command:
            # pqos -a 'llc:0=0;llc:1=1'
        8. Set CLOS[0] and CLOS[1] to 50 percent throttling using the following command;
            # pqos -e 'mba@0:0=50;mba@0:1=50'
        9. Note the memory bandwidth for core 0 and core 1. The MBL for core 0 and core 1 should
           be decreased to 50%
        10. Modify CLOS[0] from 50 percent to 10 percent using the following command, and then
           note the bandwidth on both the cores; # pqos -e 'mba@0:0=10'
        11. Modify CLOS[0] from 50 percent to 90 percent using the following command, and then
           note the bandwidth on both the cores; # pqos -e 'mba@0:0=90'
        12. change core number from 0/1 in socket0 to socket1 and repeat the test
        13. Restore default allocation:  pqos -R

        :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(2)
        self._rdt.install_rdt()
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Restore rdt monitor to default mode
        self._test_content_logger.start_step_logger(3)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Instal membw tool if not installed.
        self._test_content_logger.start_step_logger(4)
        membw_tool_path = self._rdt.get_membw_path()
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Run a STREAM benchmark instance on core 0 and core 1 with the following commands:
        # ./membw -c 1 -b 20000 --nt-write
        self._test_content_logger.start_step_logger(5)
        self._log.info(" Run a membw benchmark instance on core 0 and core 1")
        if not self._rdt.start_stress_tool(membw_tool_path, self._rdt.MEMBW_STRESS_CORE_CMD.format(self.socket0_core0)) :
            raise content_exceptions.TestFail("Failed to run the membw stress tool on SUT")
        if not self._rdt.start_stress_tool(membw_tool_path, self._rdt.MEMBW_STRESS_CORE_CMD.format(self.socket0_core1)) :
            raise content_exceptions.TestFail("Failed to run the membw stress tool on SUT")
        self._test_content_logger.end_step_logger(5, return_val=True)

        #  Monitor per-core memory bandwidth using the MBM feature of Intel RDT using the
        #  following command: # pqos -m all:0,1 -u csv -o pqos_mon.csv
        self._test_content_logger.start_step_logger(6)
        cores = [self.socket0_core0, self.socket0_core1]
        self.os.execute_async(
            self._rdt.MONITOR_TWO_CORES_CMD.format(self.socket0_core0, self.socket0_core1,
                                         self._rdt.PQOS_MON_FILE_IN_SUT))
        self._rdt.check_rdt_monitor_running_status(
            self._rdt.MONITOR_TWO_CORES_CMD.format(self.socket0_core0, self.socket0_core1,
                                         self._rdt.PQOS_MON_FILE_IN_SUT))
        res_list = self._rdt.read_mbl_values_from_pqos(self._rdt.PQOS_MON_FILE_IN_SUT,
                                                       os.path.join(self.log_dir, self.PQOS_BEFORE_STRESS), cores)
        self._log.info(
            "Monitored RDT values per-core memory bandwidth for core 0 :{} and core 1 : {}".format(res_list[0],
                                                                                                   res_list[1]))
        core0_value_when_throttling_is_100_percent = res_list[0]
        core1_value_when_throttling_is_100_percent = res_list[1]
        self._test_content_logger.end_step_logger(6, return_val=True)

        # Associate core 0 to CLOS[0] and core 1 to CLOS[1] using the following command:
        # pqos -a 'llc:0=0;llc:1=1'
        self._test_content_logger.start_step_logger(7)
        self._rdt.set_core_association(self.socket0_core0, self.socket0_core1)
        self._test_content_logger.end_step_logger(7, return_val=True)

        # Set CLOS[0] and CLOS[1] to 50 percent throttling using the following command;
        # pqos -e 'mba@0:0=50;mba@0:1=50'
        self._test_content_logger.start_step_logger(8)
        self._log.info("Set CLOS[0] and CLOS[1] to 50 percent throttling")
        self._rdt.set_throttling(50, 1, 0)
        self._test_content_logger.end_step_logger(8, return_val=True)

        # Note the memory bandwidth for core 0 and core 1 on Socket 0
        self._test_content_logger.start_step_logger(9)
        res_list = self._rdt.read_mbl_values_from_pqos(self._rdt.PQOS_MON_FILE_IN_SUT,
                                                       os.path.join(self.log_dir, self.PQOS_AFTER_50_STRESS), cores)
        self._log.info(
            "Monitored RDT values per-core memory bandwidth for core 0 :{} and core 1 : {}".format(res_list[0],
                                                                                                   res_list[1]))
        core0_value_when_throttling_is_50_percent = res_list[0]
        core1_value_when_throttling_is_50_percent = res_list[1]
        # check if the Core 0 and core 1 values are 50% as expected.
        if core0_value_when_throttling_is_100_percent==0 or core1_value_when_throttling_is_100_percent==0:
            raise content_exceptions.TestFail("The Core 0 and core 1 values are zero and not as expected")
        if core0_value_when_throttling_is_100_percent * 0.4 < core0_value_when_throttling_is_50_percent < core0_value_when_throttling_is_100_percent * 0.9:
            if core1_value_when_throttling_is_100_percent * 0.4 < core1_value_when_throttling_is_50_percent < core1_value_when_throttling_is_100_percent * 0.9:
                self._log.info("The Core 0 and core 1 values are almost 50% as expected.")
        else:
            raise content_exceptions.TestFail("The Core 0 and core 1 values are not 50% as expected")

        self._test_content_logger.end_step_logger(9, return_val=True)

        # Modify CLOS[0] from 50 percent to 10 percent and then note the bandwidth on both the
        # cores on Socket 0
        self._test_content_logger.start_step_logger(10)
        self._log.info("Set CLOS[0] from 50 percent to 10 percent throttling")
        self._rdt.set_throttling(10, 0, 0)
        res_list = self._rdt.read_mbl_values_from_pqos(self._rdt.PQOS_MON_FILE_IN_SUT,
                                                       os.path.join(self.log_dir, self.PQOS_AFTER_10_STRESS), cores)
        self._log.info(
            "Monitored RDT values per-core memory bandwidth for core 0 :{} and core 1 : {}".format(res_list[0],
                                                                                                   res_list[1]))
        core0_value_when_throttling_is_10_percent = res_list[0]
        core1_value_when_throttling_is_10_percent = res_list[1]
        # check if the Core 0 value is 10% as expected and core 1 value is not impacted
        if core1_value_when_throttling_is_10_percent==0 or core0_value_when_throttling_is_10_percent==0:
            raise content_exceptions.TestFail("The Core 0 and core 1 values are zero and not as expected")
        if not (core0_value_when_throttling_is_100_percent * 0 <= core0_value_when_throttling_is_10_percent <= core0_value_when_throttling_is_100_percent * 0.1):
            raise content_exceptions.TestFail("The Core 0 value is not 10% as expected")
        if core1_value_when_throttling_is_100_percent * 0.4 <= core1_value_when_throttling_is_10_percent <= core1_value_when_throttling_is_100_percent * 0.9:
            self._log.info("The core 1 value is almost 50% as expected and core 1's bandwidth is not impacted")
        else:
            raise content_exceptions.TestFail("The Core 0 and core 1 values are not 10% as expected")
        self._log.info("The Core 0 bandwidth value is 10% as expected")
        self._test_content_logger.end_step_logger(10, return_val=True)

        # Modify CLOS[0] from 50 percent to 90 percent using the following command, and then
        #  note the bandwidth on both the cores; # pqos -e 'mba@0:0=90'
        self._test_content_logger.start_step_logger(11)
        self._log.info("Set CLOS[0] from 50 percent to 90 percent throttling")
        self._rdt.set_throttling(90, 0, 0)
        res_list = self._rdt.read_mbl_values_from_pqos(self._rdt.PQOS_MON_FILE_IN_SUT,
                                                       os.path.join(self.log_dir, self.PQOS_AFTER_90_STRESS), cores)
        self._log.info(
            "Monitored RDT values per-core memory bandwidth for core 0 :{} and core 1 : {}".format(res_list[0],
                                                                                                   res_list[1]))
        core0_value_when_throttling_is_90_percent = res_list[0]
        core1_value_when_throttling_is_90_percent = res_list[1]
        # check if the Core 0 value is 90% as expected and core 1 value is not impacted
        if core0_value_when_throttling_is_90_percent==0 or core1_value_when_throttling_is_90_percent==0:
            raise content_exceptions.TestFail("The Core 0 and core 1 values are zero and not as expected")
        if not(core0_value_when_throttling_is_100_percent * 0.8 <= core0_value_when_throttling_is_90_percent):
            raise content_exceptions.TestFail("The Core 0 value is not 90% as expected")
        if core1_value_when_throttling_is_100_percent * 0.4 <= core1_value_when_throttling_is_90_percent <= core1_value_when_throttling_is_100_percent * 0.9:
            self._log.info("The core 1 value is almost 50% as expected and core 1's bandwidth is not impacted")
        else:
            raise content_exceptions.TestFail("The Core 0 and core 1 bandwidth values are not as expected")
        self._log.info("The Core 0 bandwidth value is almost 90% as expected.")
        self._test_content_logger.end_step_logger(11, return_val=True)

        # Restore rdt monitor to default mode
        self._test_content_logger.start_step_logger(12)
        self._rdt.restore_default_rdt_monitor()
        self._log.info(
            " Run a membw benchmark instance on core {} and core {}".format(self.socket1_core0, self.socket1_core1))
        if not self._rdt.start_stress_tool(membw_tool_path,
                                                 self._rdt.MEMBW_STRESS_CORE_CMD.format(self.socket1_core0)):
            raise content_exceptions.TestFail("Failed to run the membw stress tool on SUT")

        if not self._rdt.start_stress_tool(membw_tool_path,
                                                     self._rdt.MEMBW_STRESS_CORE_CMD.format(self.socket1_core1)):
            raise content_exceptions.TestFail("Failed to run the membw stress tool on SUT")
        self._test_content_logger.end_step_logger(12, return_val=True)

        #  Monitor per-core memory bandwidth using the MBM feature of Intel RDT using the
        #  following command: # pqos -m all:0,1 -u csv -o pqos_mon.csv
        self._test_content_logger.start_step_logger(13)
        # kill pqos if its running else ignore
        self.os.execute_async(self._rdt.KILL_PQOS_CMD)
        cores = [self.socket1_core0, self.socket1_core1]
        self.os.execute_async(
            self._rdt.MONITOR_TWO_CORES_CMD.format(self.socket1_core0, self.socket1_core1,
                                         self._rdt.PQOS_MON_FILE_IN_SUT))
        self._rdt.check_rdt_monitor_running_status(
            self._rdt.MONITOR_TWO_CORES_CMD.format(self.socket1_core0, self.socket1_core1,
                                         self._rdt.PQOS_MON_FILE_IN_SUT))
        res_list = self._rdt.read_mbl_values_from_pqos(self._rdt.PQOS_MON_FILE_IN_SUT,
                                                       os.path.join(self.log_dir, self.PQOS_BEFORE_STRESS), cores)
        self._log.info(
            "Monitored RDT values per-core memory bandwidth for core 0 :{} and core 1 : {}".format(res_list[0],
                                                                                                   res_list[1]))
        socket1_core0_value_when_throttling_is_100_percent = res_list[0]
        socket1_core1_value_when_throttling_is_100_percent = res_list[1]
        self._test_content_logger.end_step_logger(13, return_val=True)

        # Associate core 0 to CLOS[0] and core 1 to CLOS[1] using the following command:
        # pqos -a 'llc:0=0;llc:1=1'
        self._test_content_logger.start_step_logger(14)
        self._rdt.set_core_association(self.socket1_core0, self.socket1_core1)
        self._test_content_logger.end_step_logger(14, return_val=True)

        # Set CLOS[0] and CLOS[1] to 50 percent throttling using the following command;
        # pqos -e 'mba@0:0=50;mba@0:1=50'
        self._test_content_logger.start_step_logger(15)
        self._log.info("Set CLOS[0] and CLOS[1] to 50 percent throttling")
        self._rdt.set_throttling(50, 1, 1)
        self._test_content_logger.end_step_logger(15, return_val=True)

        # Note the memory bandwidth for core 0 and core 1 on Socket 1
        self._test_content_logger.start_step_logger(16)
        res_list = self._rdt.read_mbl_values_from_pqos(self._rdt.PQOS_MON_FILE_IN_SUT,
                                                       os.path.join(self.log_dir, self.PQOS_AFTER_50_STRESS), cores)
        self._log.info(
            "Monitored RDT values per-core memory bandwidth on socket 1 for core {} :{} and core {} : {}".format(
                self.socket1_core0, res_list[0],
                self.socket1_core1, res_list[1]))
        socket1_core0_value_when_throttling_is_50_percent = res_list[0]
        socket1_core1_value_when_throttling_is_50_percent = res_list[1]
        # check if the Core 0 and core 1 values are 50% as expected.
        if socket1_core0_value_when_throttling_is_100_percent==0 or socket1_core0_value_when_throttling_is_50_percent==0:
            raise content_exceptions.TestFail(
                "The Core {} and core {} values are not 50% as expected".format(self.socket1_core0, self.socket1_core1))
        if not (socket1_core0_value_when_throttling_is_100_percent * 0.4 <= socket1_core0_value_when_throttling_is_50_percent <= socket1_core0_value_when_throttling_is_100_percent * 0.9):
            raise content_exceptions.TestFail("The Core {} value is not 50% as expected".format(self.socket1_core0))
        if not (socket1_core1_value_when_throttling_is_100_percent * 0.4 <= socket1_core1_value_when_throttling_is_50_percent <= socket1_core1_value_when_throttling_is_100_percent * 0.9):
            raise content_exceptions.TestFail("The Core {} value is not 50% as expected".format(self.socket1_core1))
        else:
            self._log.info("The Core {} and core {} values are 50% as expected".format(self.socket1_core0, self.socket1_core1))
        self._test_content_logger.end_step_logger(16, return_val=True)

        # Modify CLOS[0] from 50 percent to 10 percent and then note the bandwidth on both the
        # cores on Socket 0
        self._test_content_logger.start_step_logger(17)
        self._log.info("Set CLOS[0] from 50 percent to 10 percent throttling")
        self._rdt.set_throttling(10, 0, 1)
        res_list = self._rdt.read_mbl_values_from_pqos(self._rdt.PQOS_MON_FILE_IN_SUT,
                                                       os.path.join(self.log_dir, self.PQOS_AFTER_10_STRESS), cores)
        self._log.info(
            "Monitored RDT values per-core memory bandwidth for core {} :{} and core {} : {}".format(self.socket1_core0,
                                                                                                     res_list[0],
                                                                                                     self.socket1_core1,
                                                                                                     res_list[1]))
        socket1_core0_value_when_throttling_is_10_percent = res_list[0]
        socket1_core1_value_when_throttling_is_10_percent = res_list[1]
        # check if the Core 0 value is 10% as expected and core 1 value is not impacted
        if socket1_core0_value_when_throttling_is_10_percent==0:
            raise content_exceptions.TestFail(
                "The Core {} and core {} values are zero and not as expected".format(self.socket1_core0, self.socket1_core1))
        if not (socket1_core0_value_when_throttling_is_100_percent * 0 <= socket1_core0_value_when_throttling_is_10_percent <= socket1_core0_value_when_throttling_is_100_percent * 0.1):
            raise content_exceptions.TestFail("The Core {} value is not 10% as expected".format(self.socket1_core0))
        if not (socket1_core1_value_when_throttling_is_100_percent * 0.4 <= socket1_core1_value_when_throttling_is_10_percent <= socket1_core1_value_when_throttling_is_100_percent * 0.9):
            raise content_exceptions.TestFail("The Core {} value is not 50% as expected".format(self.socket1_core1))
        self._log.info("The core {} bandwidth value is 10% as expected on socket 1 and core {} bandwidth value is not "
                       "impacted as expected".format(self.socket1_core0,self.socket1_core1))
        self._test_content_logger.end_step_logger(17, return_val=True)

        # Modify CLOS[0] from 50 percent to 90 percent using the following command, and then
        #  note the bandwidth on both the cores; # pqos -e 'mba@0:0=90'
        self._test_content_logger.start_step_logger(18)
        self._log.info("Set CLOS[0] from 50 percent to 90 percent throttling")
        self._rdt.set_throttling(90, 0, 1)
        res_list = self._rdt.read_mbl_values_from_pqos(self._rdt.PQOS_MON_FILE_IN_SUT,
                                                       os.path.join(self.log_dir, self.PQOS_AFTER_90_STRESS), cores)
        self._log.info(
            "Monitored RDT values per-core memory bandwidth on socket 1 for core {} :{} and core {} : {}".format(
                self.socket1_core0, res_list[0],
                self.socket1_core1, res_list[1]))
        socket1_core0_value_when_throttling_is_90_percent = res_list[0]
        socket1_core1_value_when_throttling_is_90_percent = res_list[1]
        # check if the Core 0 value is 90% as expected and core1 value is not impacted.
        if socket1_core0_value_when_throttling_is_90_percent==0:
            raise content_exceptions.TestFail(
                "The Core {} and core {} values are not as expected for 90% Throtthling on socket 1".format(
                    self.socket1_core0, self.socket1_core1))
        if not (socket1_core0_value_when_throttling_is_100_percent * 0.8 <= socket1_core0_value_when_throttling_is_90_percent):
            raise content_exceptions.TestFail("The Core {} value is not as expected for 90% Throtthling on socket 1".format(
                    self.socket1_core0))
        if not (socket1_core1_value_when_throttling_is_100_percent * 0.4 <= socket1_core1_value_when_throttling_is_90_percent <= socket1_core1_value_when_throttling_is_100_percent * 0.9):
            raise content_exceptions.TestFail(
                "The Core {} value is not as expected for 90% Throtthling on socket 1".format(self.socket1_core1))

        self._log.info("The Core {} value on socket 1 is almost 90% and Core {} bandwidth value is not"
                       " impacted as expected.".format(self.socket1_core0,self.socket1_core1))
        self._test_content_logger.end_step_logger(18, return_val=True)

        # Restore rdt monitor to default mode
        self._test_content_logger.start_step_logger(19)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(19, return_val=True)

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        # kill pqos and membw processes in SUT
        if self._rdt.check_rdt_monitor_running_status(self._rdt.PQOS_STR):
            self.os.execute_async(self._rdt.KILL_PQOS_CMD)
        if self._rdt.check_rdt_monitor_running_status(self._rdt.MEMBW_STR):
            self.os.execute_async(self._rdt.KILL_MEMBW_CMD)
        super(RdtCMbaStreamTwoCoresIndependentlyHTDisabledCase19, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if RdtCMbaStreamTwoCoresIndependentlyHTDisabledCase19.main() else Framework.TEST_RESULT_FAIL)
