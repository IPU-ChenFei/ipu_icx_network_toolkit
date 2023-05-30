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
import os
import threading
import time

from dtaf_core.lib.dtaf_constants import Framework

from src.memory.tests.memory_ddr.ddr_common import DDRCommon
from src.lib.test_content_logger import TestContentLogger
from src.lib.content_configuration import ContentConfiguration
from src.lib.os_lib import WindowsCommonLib
from src.lib import content_exceptions


class Mem_Iwvss_Memory_Stress(DDRCommon):
    """
    Glasgow ID: 63294

    Verify platform functional reliability with the maximum memory capacity as spec defined without unexpected
    errors under heavy stress with data integrity checking.

    """
    BIOS_CONFIG_FILE = "mem_iwvss_memory_stress.cfg"
    TEST_CASE_ID = "G63294"
    LIST_PROCESSES = ["mem64.exe"]
    return_value = []

    step_data_dict = {1: {'step_details': 'Clear system event logs and Application event logs and'
                                          'Setting & Verify BIOS knobs',
                          'expected_results': 'Clear ALL the system event logs and Application event logs and'
                                              ' BIOS setup options are updated with changes saved'},
                      2: {'step_details': 'Collecting system memory before and after bios '
                                          'and Comparing both the memories',
                          'expected_results': 'The amount of memory reported by the operating system matches to'
                                              'the amount of memory installed in the system.'},
                      3: {'step_details': 'Collecting CPU utilization level as load percentage',
                          'expected_results': 'Utilization Level should be less than 1'},
                      4: {'step_details': 'Collecting Memory utilization level',
                          'expected_results': 'Utilization Level should be less than 1'},
                      5: {'step_details': 'Executing the command related to baseboard product and iwVSS package',
                          'expected_results': 'Execute command without errors'},
                      6: {'step_details': 'Collecting the application event logs and os logs',
                          'expected_results': 'Display if errors or warnings are present in application and os logs'},
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new  DimmMaximumMemoryConfigReportingWindows object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.

        :return: None
        :raises: None
        """
        # calling base class init
        super(Mem_Iwvss_Memory_Stress, self).__init__(test_log, arguments, cfg_opts,
                                                      self.BIOS_CONFIG_FILE)

        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._common_content_configuration = ContentConfiguration(self._log)
        self.windows_lib_obj = WindowsCommonLib(self._log, self._os)
        self.cpu_threshold_config = self._common_content_configuration.get_cpu_utilization_percent()
        self.memory_threshold_config = self._common_content_configuration.get_mem_utilization_percent()

    def prepare(self):
        # type: () -> None
        """
        1. Clear system event logs and application event logs
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self._windows_event_log.clear_system_event_logs()  # Clear system even log
        self._windows_event_log.clear_application_logs()  # Clear Application log
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. Configure platform with CPUs, Memory and MS Windows OS with the iwVSS data integrity & stress application.
        2. Configure the iwVSS Data Integrity & Stress application for the platform.
        3. Check basic platform functionality while under stress
        4. Verify no unexpected errors were logged while executing stress.

        :return: True, if the test case is successful else false
        :raise: None
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # Total memory with variance
        memtotal_with_variance = (self._ddr4_mem_capacity_config - (self._ddr4_mem_capacity_config *
                                                                    self._variance_percent))

        self._log.info("Total Installed DDR capacity as per configuration with variance - {}".format(
            memtotal_with_variance))

        if self._post_mem_capacity_config < int(memtotal_with_variance) or self._post_mem_capacity_config > \
                self._ddr4_mem_capacity_config:
            raise content_exceptions.TestFail("Total Installed DDR Capacity is not same as configuration.")

        self._log.info("Total Installed DDR Capacity is same as configuration.")

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        # View the "CPU" utilization level.
        cpu_load_percentage = self.windows_lib_obj.task_manager_wmic_cpu_get(task_option="loadpercentage")
        cpu_load_percentage = float(cpu_load_percentage.split(' ')[2])
        self._log.info("CPU load percentage is {} ".format(cpu_load_percentage))

        # Verifying cpu level should be close to 1 percentage
        if cpu_load_percentage <= 1:
            self._log.info("CPU load percentage is less than 1 percentage and value is {}".format(cpu_load_percentage))
            self._test_content_logger.end_step_logger(3, return_val=True)
        else:
            self._log.error("CPU load percentage is more than 1 percentage and value is {}".format(cpu_load_percentage))

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=False)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)
        system_memory = self.get_total_memory_win()
        system_memory = (float(system_memory.split(" ")[0].replace(",", ""))) / 1024.0
        self._log.info("System Memory is {} ".format(system_memory))
        available_memory = self.get_available_memory_win()
        available_memory = (int(available_memory.split(" ")[0].replace(",", ""))) / 1024.0
        self._log.info("Total Available Memory is {} ".format(available_memory))

        # Calculating the utilization memory
        utilization_memory = 100 - ((available_memory / system_memory) * 100)
        self._log.info("Utilization Memory is {} ".format(utilization_memory))

        # Verifying memory utilization that should be close to 1 percentage
        if utilization_memory <= 1:
            self._log.info("Memory Usage percentage is less than 1 percentage and value is {}"
                           .format(utilization_memory))
            # Step logger end for Step 4
            self._test_content_logger.end_step_logger(4, return_val=True)

        else:
            self._log.error("Memory Usage percentage is more than 1 percentage and value is {}"
                            .format(utilization_memory))

        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=False)

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        # Executing the command: wmic MEMORYCHIP get BankLabel,DeviceLocator,Capacity,Tag,Speed >DIMM_Data.txt
        self.windows_lib_obj.task_manager_wmic_mem_get(task_option="BankLabel,DeviceLocator,Capacity,Tag,Speed "
                                                       ">DIMM_data.txt")
        product_info = self.windows_lib_obj.task_manager_wmic_baseboard_get(task_option="product").split()[1]

        # iwVSS tool installation and executing iwVSS package
        dict_product_info = {"WilsonPoint": "Whitely", "PURLEY": "Purley"}
        self._iwvss_path = self._install_collateral.install_iwvss()
        self.sut_platform_pkg_path = os.path.join(self._iwvss_path, dict_product_info[product_info])
        collateral_path = self._common_content_lib.get_collateral_path()
        self.host_platform_pkg_path = os.path.join(collateral_path, "{}.pkx".format(dict_product_info[product_info]))
        self._os.copy_local_file_to_sut(self.host_platform_pkg_path, self.sut_platform_pkg_path)
        iwvss_thread = threading.Thread(target=self.execute_iwvss,
                                        args=(
                                            r"cmd /C t.exe /pkg {}\{}.pkx /reconfig /pc {} "
                                            r"/flow S145 "
                                            r"/run "
                                            r"/minutes {} /RR iwvss.log".format(dict_product_info[product_info],
                                                                                dict_product_info[product_info],
                                                                                dict_product_info[product_info],
                                                                                self._iwvss_runtime),
                                            self._iwvss_path,))
        iwvss_thread.start()

        # For safety purpose - Just to wait for 10 more sec, so that the process will start in the background.
        time.sleep(10)
        self._memory_common_lib.verify_background_process_running(' '.join(map(str, self.LIST_PROCESSES)))

        self._log.info("Waiting for the iwVSS tool process to come to it's memory and cpu execution, to check system "
                       "stability..")

        # waiting for half of the execution time, so that we can validate the platform responsiveness
        time.sleep(20)
        self._log.info("Started to check the platform stability while iwVSS is running in the background..")
        cpu_utilization = self.windows_lib_obj.task_manager_wmic_cpu_get(task_option="loadpercentage").split()[-1]

        # Verify memory usage is high
        self.return_value.append(self._memory_common_lib.verify_cpu_utilization(cpu_utilization,
                                                                                self.cpu_threshold_config))

        # Get the total physical memory value from Os
        get_physical_memory_data_win = self.windows_lib_obj.get_system_memory()

        # Verify memory usage is high
        self.return_value.append(
            self._memory_common_lib.verify_memory_utilization(
                get_physical_memory_data_win, self.memory_threshold_config))

        # Check responsiveness of the platform by opening a command prompt.
        self._common_content_lib.execute_sut_cmd("start", "Open cmd", self._command_timeout)

        # Check responsiveness of the platform by creating a text file with some content.
        self._common_content_lib.execute_sut_cmd("echo testing the platform response > test.txt", "Creating a file",
                                                 self._command_timeout)

        # It will make this script wait till the process completes it's execution on the SUT
        self._memory_common_lib.verify_and_hold_until_background_process_finish(' '.join(map(str, self.LIST_PROCESSES)))

        # Step logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=True)

        # Step logger start for Step 6
        self._test_content_logger.start_step_logger(6)

        stress_test_result = []
        whea_logs = self._windows_event_log.get_whea_error_event_logs()

        # Check if there are any errors, warnings of category WHEA found
        if whea_logs is None or len(str(whea_logs)) == 0:
            self._log.info("No WHEA errors or warnings found in Windows System event log...")
            stress_test_result.append(True)
        else:
            self._log.error("Found WHEA errors or warnings in Windows System event log...")
            self._log.error("WHEA error logs: \n" + str(whea_logs))
            stress_test_result.append(False)

        application_logs = self._windows_event_log.get_application_event_error_logs("-Source iwVSS ,"
                                                                                    "iwVSS -EntryType Error,Warning")
        # Check if there are any errors, warnings
        if application_logs is None or len(str(application_logs)) == 0:
            self._log.info("No errors or warnings found in OS application log...")
            stress_test_result.append(True)
        else:
            self._log.error("Found errors or warnings in OS application log...")
            self._log.error("Error logs: \n" + str(application_logs))
            stress_test_result.append(False)

        log_file_path_host = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=str(self._iwvss_path), extension=".log")

        self.return_value.append(self._memory_common_lib.parse_log_for_error_patterns
                                 (log_path=os.path.join(log_file_path_host, "iwvss.log")))

        # Step logger end for Step 6
        self._test_content_logger.end_step_logger(6, return_val=True)

        return all(self.return_value)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if Mem_Iwvss_Memory_Stress.main() else Framework.TEST_RESULT_FAIL)
