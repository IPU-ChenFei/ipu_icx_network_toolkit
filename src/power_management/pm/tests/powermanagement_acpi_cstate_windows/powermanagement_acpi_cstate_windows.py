#!/usr/bin/env python
###############################################################################
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
###############################################################################
import sys
import os
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.ptu_provider import PTUProvider
from src.provider.cpu_info_provider import CpuInfoProvider
from src.lib.dtaf_content_constants import PTUToolConstants, TimeConstants
from src.lib.test_content_logger import TestContentLogger


class PowerManagementACPICStateWindows(ContentBaseTestCase):
    """
    HPALM/HPQC ID : H87939/G57643-PI_Power Management - ACPI C-States on Windows
    Install PTU tool and run the c-state commands
    """
    TEST_CASE_ID = ["H87939", "G57643", "PI_Power Management - ACPI C-States on Windows"]
    BIOS_CONFIG_FILE_ENABLE = "enable_cstate.cfg"
    BIOS_CONFIG_FILE_DISABLE = "disable_cstate.cfg"
    CSTATE_ENABLE_LOG_FOLDER = "cstate_enable"
    CSTATE_DISABLE_LOG_FOLDER = "cstate_disable"
    TURBO_ENABLE_LOG_FOLDER = "Turbo_enable"
    step_data_dict = {
        1: {'step_details': 'BIOS Setup and ENABLE all available C States',
            'expected_results': 'All available C-states are ENABLED'},
        2: {'step_details': 'Complete Configuration Setup steps',
            'expected_results': 'Install PTU tool successfully'},
        3: {'step_details': 'Run the Intel Power Thermal Utility (PTU) without test inputs',
            'expected_results': 'simply use this to observe C-state residency'},
        4: {'step_details': 'Observe the C-state residency counters displayed by the PTU',
            'expected_results': 'C6-state residency should be greater than 90%'},
        5: {'step_details': 'Run Intel Power Thermal Utility (PTU) and perform and turbo settings',
            'expected_results': 'PTU is running and CPU utilization should be at or near 100%'},
        6: {'step_details': 'Observe the C-state residency counters displayed by the PTU',
            'expected_results': 'PTU is running and CPU(C6) utilization should be at or near 0%'},
        7: {'step_details': 'BIOS Setup and DISABLE all available C States',
            'expected_results': 'All available C-states are DISABLED'},
        8: {'step_details': 'Run the Intel Power Thermal Utility (PTU) without test inputs',
            'expected_results': 'simply use this to observe C-state residency'},
        9: {'step_details': 'Observe the C-state residency counters displayed by the PTU',
            'expected_results': 'C-states(C6) should show a residency of 0%'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of PowerManagementACPICStateWindows

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        self.cstate_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               self.BIOS_CONFIG_FILE_ENABLE)
        super(PowerManagementACPICStateWindows, self).__init__(test_log, arguments, cfg_opts,
                                                               self.cstate_bios_enable)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        if self.os.os_type != OperatingSystems.WINDOWS:
            raise NotImplementedError("Not implemented for {} OS".format(self.os.os_type))

        self._ptu_provider = PTUProvider.factory(self._log, cfg_opts, self.os)
        self.cstate_bios_disable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                self.BIOS_CONFIG_FILE_DISABLE)
        self._cpu_provider = CpuInfoProvider.factory(test_log, cfg_opts, self.os)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        super(PowerManagementACPICStateWindows, self).prepare()
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def _get_cpu_values_common_code(self, sut_folder_path, host_log_folder_name):
        """
        This method will add CPU column name as key and column row value as value into a dictionary

        :param sut_folder_path: ptu tool path in sut
        :param host_log_folder_name: Log folder name
        :return: CPU values
        """
        total_cpu_dict = {}
        log_path_in_host = os.path.join(self.log_dir, host_log_folder_name)
        dict_cpu_column_values = {}
        self._log.info("Copying SUT log into the HOST")
        file_name = self._common_content_lib.copy_log_files_to_host(
            log_path_in_host, sut_log_files_path=sut_folder_path, extension=PTUToolConstants.extension)
        absolute_log_path = file_name + os.sep + os.listdir(file_name)[PTUToolConstants.ZERO]
        self._log.debug("Absolute log file name in HOST %s ", absolute_log_path)
        self._cpu_provider.populate_cpu_info()
        socket_info = int(self._cpu_provider.get_number_of_sockets())  # To get on board socket info
        for number in range(socket_info):
            self._log.info("Checking for CPU{} utilization for C-state C0,C1,C6 values".format(number))
            dict_cpu_column_values[PTUToolConstants.STR_UTIL] = self._ptu_provider.get_column_data(
                self._ptu_provider.PTU_CPU.format(number),
                PTUToolConstants.UTILIZATION,
                absolute_log_path)
            dict_cpu_column_values[PTUToolConstants.STR_C0] = self._ptu_provider.get_column_data(
                self._ptu_provider.PTU_CPU.format(number),
                PTUToolConstants.C0,
                absolute_log_path)
            dict_cpu_column_values[PTUToolConstants.STR_C1] = self._ptu_provider.get_column_data(
                self._ptu_provider.PTU_CPU.format(number),
                PTUToolConstants.C1,
                absolute_log_path)
            dict_cpu_column_values[PTUToolConstants.STR_C6] = self._ptu_provider.get_column_data(
                self._ptu_provider.PTU_CPU.format(number),
                PTUToolConstants.C6,
                absolute_log_path)
            if not total_cpu_dict:
                total_cpu_dict.update(dict_cpu_column_values)
            else:
                for key in total_cpu_dict.keys():
                    total_cpu_dict[key].extend(dict_cpu_column_values[key])
            self._log.info("{} {} value is: {}".format(self._ptu_provider.PTU_CPU.format(number),
                                                       PTUToolConstants.UTILIZATION,
                                                       dict_cpu_column_values[PTUToolConstants.STR_UTIL]))
            self._log.info("{} {} value is: {}".format(self._ptu_provider.PTU_CPU.format(number),
                                                       PTUToolConstants.C0,
                                                       dict_cpu_column_values[PTUToolConstants.STR_C0]))
            self._log.info("{} {} value is: {}".format(self._ptu_provider.PTU_CPU.format(number),
                                                       PTUToolConstants.C1,
                                                       dict_cpu_column_values[PTUToolConstants.STR_C1]))
            self._log.info("{} {} value is: {}".format(self._ptu_provider.PTU_CPU.format(number),
                                                       PTUToolConstants.C6,
                                                       dict_cpu_column_values[PTUToolConstants.STR_C6]))
        self._log.debug("Total CPU info : {}".format(total_cpu_dict))
        c0_list = total_cpu_dict[PTUToolConstants.STR_C0]
        c1_list = total_cpu_dict[PTUToolConstants.STR_C1]
        # Adding C0 and C1 Values
        sum_of_c0_c1 = [(float(c0_list[each_value]) + float(c1_list[each_value]))
                        for each_value in range(0, len(c0_list))]
        self._log.debug("Sum of C0 and C1 is : {}".format(sum_of_c0_c1))
        total_cpu_dict[PTUToolConstants.STR_C0_C1_SUM] = sum_of_c0_c1
        self._log.debug("Total CPU info : {}".format(total_cpu_dict))
        return total_cpu_dict

    def execute(self):
        """
        This function install ptu tool, execute ptu tool
        Copy CSV file to host, read and verify the C-state values
        Setting the C-state bios to disable

        :return: True if test completed successfully, False otherwise.
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        sut_log_folder_path_sut = self._ptu_provider.install_ptu()  # Installing PTU tool
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        self._log.info("Delete the existing log file in SUT")
        self._common_content_lib.execute_sut_cmd(
            sut_cmd=PTUToolConstants.SUT_DELETE_FILE, cmd_str="delete file", execute_timeout=self._command_timeout)
        # To keep the system idle
        time.sleep(150)
        self._log.info("Running PTU tool with default command for System becomes idle")
        self._ptu_provider.execute_async_ptu_tool(ptu_cmd=self._ptu_provider.PTU_DEFAULT_CMD)
        time.sleep(TimeConstants.TEN_MIN_IN_SEC)
        # To kill the PTU Tool
        self._ptu_provider.kill_ptu_tool()
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)
        dict_cup_values = self._get_cpu_values_common_code(sut_log_folder_path_sut, self.CSTATE_ENABLE_LOG_FOLDER)

        # Any one of C0+C1 > 15%, C6 < 85%, CPU Utilization > 15% FAIL
        error_values = [(float(value_util), float(value_c0_c1), float(value_c6))
                        for value_util, value_c0_c1, value_c6 in zip(dict_cup_values[PTUToolConstants.STR_UTIL],
                                                                     dict_cup_values[PTUToolConstants.STR_C0_C1_SUM],
                                                                     dict_cup_values[PTUToolConstants.STR_C6])
                        if float(value_util) > 15 or float(value_c0_c1) > 15 or float(value_c6) < 85]

        self._log.error("ERROR Values : {}".format(error_values))
        if error_values:
            raise content_exceptions.TestFail("\n Any one of C0+C1 > 15% or C6 < 85% or CPU Utilization > 15% FAIL \n"
                                              " C-state residency counters value is not matching expected result")
        self._log.debug("C-state residency counters is matching expected result "
                        "C0+C1 < 15% and C6 > 85% , CPU Utilization < 15%")
        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._log.info("Delete the existing log file in SUT")
        self._common_content_lib.execute_sut_cmd(
            sut_cmd=PTUToolConstants.SUT_DELETE_FILE, cmd_str="delete file", execute_timeout=self._command_timeout)
        self._log.info("Running PTU tool with work load command")
        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)
        self._ptu_provider.execute_async_ptu_tool(ptu_cmd=self._ptu_provider.PTU_TURBO_CMD)
        time.sleep(TimeConstants.TEN_MIN_IN_SEC)
        # To kill the PTU Tool
        self._ptu_provider.kill_ptu_tool()
        # Step logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=True)

        dict_cup_values = self._get_cpu_values_common_code(sut_log_folder_path_sut, self.TURBO_ENABLE_LOG_FOLDER)
        # Step logger start for Step 6
        self._test_content_logger.start_step_logger(6)

        # Any one of CPU utilization < 90%, C0+C1 < 85%, C6 > 15% is FAIL
        error_values = [(float(value_util), float(value_c0_c1), float(value_c6))
                        for value_util, value_c0_c1, value_c6 in zip(dict_cup_values[PTUToolConstants.STR_UTIL],
                                                                     dict_cup_values[PTUToolConstants.STR_C0_C1_SUM],
                                                                     dict_cup_values[PTUToolConstants.STR_C6])
                        if float(value_util) < 90 or float(value_c0_c1) < 85 or float(value_c6) > 15]
        self._log.error("ERROR Values : {}".format(error_values))
        if error_values:
            raise content_exceptions.TestFail("\n Few CPU utilization < 90%, C0+C1 < 85%, C6 > 15% FAIL \n"
                                              " C-state residency counters value is not matching expected result")
        self._log.debug("C-state residency counters is matching expected result "
                        "CPU Utilization > 90%, C0+C1 > 85% and C6 < 15%")
        # Step logger end for Step 6
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._log.info("Disable the C-state bios knobs")
        # Step logger start for Step 7
        self._test_content_logger.start_step_logger(7)
        self.set_and_verify_bios_knobs(self.cstate_bios_disable)
        # Step logger end for Step 7
        self._test_content_logger.end_step_logger(7, return_val=True)
        self._log.info("Delete the existing log file in SUT")
        self._common_content_lib.execute_sut_cmd(
            sut_cmd=PTUToolConstants.SUT_DELETE_FILE, cmd_str="delete file", execute_timeout=self._command_timeout)
        # Step logger start for Step 8
        self._test_content_logger.start_step_logger(8)
        # To keep the system idle
        time.sleep(150)
        self._ptu_provider.execute_async_ptu_tool(ptu_cmd=self._ptu_provider.PTU_DEFAULT_CMD)
        time.sleep(TimeConstants.TEN_MIN_IN_SEC)
        # To kill the PTU Tool
        self._ptu_provider.kill_ptu_tool()
        # Step logger end for Step 8
        self._test_content_logger.end_step_logger(8, return_val=True)

        dict_cup_values = self._get_cpu_values_common_code(sut_log_folder_path_sut, self.CSTATE_DISABLE_LOG_FOLDER)

        # Step logger start for Step 9
        self._test_content_logger.start_step_logger(9)
        # Any one of CPU Utilization > 15%, C0+C1 < 85%, C6 > 15% FAIL
        error_values = [(float(value_util), float(value_c0_c1), float(value_c6))
                        for value_util, value_c0_c1, value_c6 in zip(dict_cup_values[PTUToolConstants.STR_UTIL],
                                                                     dict_cup_values[PTUToolConstants.STR_C0_C1_SUM],
                                                                     dict_cup_values[PTUToolConstants.STR_C6])
                        if float(value_util) > 15 or float(value_c0_c1) < 85 or float(value_c6) > 15]
        self._log.error("ERROR Values : {}".format(error_values))
        if error_values:
            raise content_exceptions.TestFail("\n Few Util > 15%, C0+C1 > 85%, C6 > 15% FAIL \n"
                                              " C-state residency counters value is not matching expected result")
        self._log.debug("C-state residency counters is matching expected result "
                        "CPU Utilization < 15%, C0+C1 > 85% and C6 < 15%")
        # Step logger end for Step 9
        self._test_content_logger.end_step_logger(9, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PowerManagementACPICStateWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PowerManagementACPICStateWindows.main() else Framework.TEST_RESULT_FAIL)
