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

from src.memory.tests.memory_ddr.ddr_common import DDRCommon
from src.lib.test_content_logger import TestContentLogger
from src.lib.content_configuration import ContentConfiguration
from src.lib.os_lib import WindowsCommonLib
from src.lib import content_exceptions


class DimmMaximumMemoryConfigReportingWindows(DDRCommon):
    """
    Glasgow ID: 59427

    Verify that Platform can function without errors when the maximum memory capacity is installed as spec defined.

    """
    BIOS_CONFIG_FILE = "memory_ddr4_dimm_maximum_memory_config_reporting_windows.cfg"
    TEST_CASE_ID = "G59427"
    MEMORY_THRESHOULD = 10

    step_data_dict = {1: {'step_details': 'Clear system event logs and Application event logs and'
                                          'Setting & Verify BIOS knobs.',
                          'expected_results': 'Clear ALL the system event logs and Application event logs and'
                                              ' BIOS setup options are updated with changes saved.'},
                      2: {'step_details': 'Verify the Post Memory of the SUT.',
                          'expected_results': 'Post Memory should be accurately equal to install memory.'},
                      3: {'step_details': 'Collecting the dimm value as install memory and system memory '
                                          'and Comparing both the memories.',
                          'expected_results': 'The amount of memory reported by the operating system matches to'
                                              'the amount of memory installed in the system.'},
                      4: {'step_details': 'Collecting the highest speed of the dimm.',
                          'expected_results': 'The speed off the dimm should be match with the '
                                              'expected speed that should be highest.'},
                      5: {'step_details': 'Collecting the form factor of a dimm.',
                          'expected_results': 'The form factor of the output should be match with the '
                                              'expected value of dimm.'},
                      6: {'step_details': 'Collecting CPU utilization level as load percentage.',
                          'expected_results': 'Utilization Level should be lessthan 1.'},
                      7: {'step_details': 'Collecting Memory utilization level.',
                          'expected_results': 'Utilization Level should be lessthan 1.'},
                      8: {'step_details': 'Collecting the application event logs.',
                          'expected_results': 'Display if errors or warnings are present in application logs.'},
                      9: {'step_details': 'Collecting the os system event logs.',
                          'expected_results': 'Display if errors or warnings are present in os system logs.'},
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
        super(DimmMaximumMemoryConfigReportingWindows, self).__init__(test_log, arguments, cfg_opts,
                                                                      self.BIOS_CONFIG_FILE)

        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._common_content_configuration = ContentConfiguration(self._log)
        self.windows_lib = WindowsCommonLib(self._log, self._os)
        self.product = self._common_content_lib.get_platform_family()
        self.skx = self._common_content_configuration.memory_supported_highest_capacity_dimm(self.product)

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

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        self._log.info("Total memory capacity shown in POST - {}".format(self._post_mem_capacity_config))

        self._log.info("Total DDR capacity as per configuration - {}".format(self._ddr4_mem_capacity_config))

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

    def execute(self):
        """
        1. Executing the "System Information" utillity and verify the amount of system memory reported is correct.
        2. View the "CPU" and "Memory" utilization levels should be close to 1%.
        3. Executing the command: wmic MEMORYCHIP get BankLabel,DeviceLocator,Capacity,Tag,Speed >DIMM_Data.txt
        4. Collecting & Displaying the os system logs and application logs.

        :return: True, if the test case is successful else false
        :raise: None
        """
        final_result = []

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        # Executing the command: wmic MEMORYCHIP get Capacity
        install_memory = self.windows_lib.task_manager_wmic_mem_get(task_option="Capacity")
        install_memory = install_memory.split(" ")
        total_install_memory = 0
        single_dimm = []
        single_dimm_value = self.skx['capacity']

        # Calculating the highest single dimm in SUT
        for index in install_memory:
            if index.isdigit():
                single_dimm.append((int(index) / (1024 * 1024 * 1024)))
                total_install_memory = total_install_memory + (int(index) / (1024 * 1024 * 1024))
        self._log.info("Installed Total Memory to SUT is {} ".format(total_install_memory))

        for value in single_dimm:
            if value == float(single_dimm_value):
                self._log.info("DIMM is matching with installed dimm {} ".format(single_dimm_value))
            else:
                raise content_exceptions.TestFail("DIMM is not matching with installed dimm {} ".
                                                  format(single_dimm_value))

        # Executing the "System Information" utillity.
        system_memory = self.get_total_memory_win()
        system_memory = (float(system_memory.split(" ")[0].replace(",", ""))) / 1024.0
        self._log.info("System Memory is {} ".format(system_memory))

        # verify the amount of system memory reported is correct.
        if total_install_memory >= system_memory:
            self._log.info("System memory {} and install memory {} are approximately equal "
                           .format(system_memory, total_install_memory))
        else:
            raise content_exceptions.TestFail("System memory {} and install memory {} are not equal ".
                                              format(system_memory, total_install_memory))
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=system_memory)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        # Executing the command: wmic MEMORYCHIP get Speed
        result = self.windows_lib.task_manager_wmic_mem_get(task_option="Speed")
        result = result.split(" ")
        speed_list = []
        for eachdata in result:
            if eachdata.isdigit():
                speed_list.append(eachdata)
        speed_value = self.skx['speed']
        for value in speed_list:
            if value == speed_value:
                self._log.info("Speed is taken as highest value only that is {} ".format(speed_value))
            else:
                raise content_exceptions.TestFail("Speed is not taken as highest value only that is {} ".
                                                  format(speed_value))

        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        # Executing the command: wmic MEMORYCHIP get FormFactor
        form_result = self.windows_lib.task_manager_wmic_mem_get(task_option="formfactor")
        form_result = form_result.split(" ")
        form_factor = []
        for var in form_result:
            if var.isdigit():
                if var == '8':
                    form_factor.append("DIMM")
                else:
                    form_factor.append("NotDIMM")
        self._log.info("Form Factor is {} ".format(form_factor))
        form_factor_value = self.skx['formfactor']
        for value in form_factor:
            if value == form_factor_value:
                self._log.info("Form Factor is equal with expected value {} ".format(form_factor_value))
            else:
                raise content_exceptions.TestFail("Form Factor is not equal with expected value {} ".
                                                  format(form_factor_value))
        # Step logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=True)

        # Step logger start for Step 6
        self._test_content_logger.start_step_logger(6)

        # View the "CPU" utilization level.
        cpu_load_percentage = self.windows_lib.task_manager_wmic_cpu_get(task_option="loadpercentage")
        cpu_load_percentage = float(cpu_load_percentage.split(' ')[2])
        self._log.info("CPU load percentage is {} ".format(cpu_load_percentage))

        # Verifying cpu level should be close to 1 percentage
        if cpu_load_percentage <= 1:
            self._log.info("CPU load percentage is less than 1 percentage and value is {}".format(cpu_load_percentage))
        else:
            raise content_exceptions.TestFail("CPU load percentage is more than 1 percentage and value is {}".
                                              format(cpu_load_percentage))
        # Step logger end for Step 6
        self._test_content_logger.end_step_logger(6, return_val=True)

        # Step logger start for Step 7
        self._test_content_logger.start_step_logger(7)

        # Viewing the "Memory" utilization level.
        available_memory = self.get_available_memory_win()
        available_memory = (float(available_memory.split(" ")[0].replace(",", ""))) / 1024.0
        self._log.info("Total Available Memory is {} ".format(available_memory))

        # Calculating the utilization memory
        utilization_memory = 100 - ((available_memory / system_memory) * 100)
        self._log.info("Utilization Memory is {} ".format(utilization_memory))

        # Verifying memory utilization that should be close to 1 percentage
        if utilization_memory <= self.MEMORY_THRESHOULD:
            self._log.info("Memory Usage percentage is lessthan {} percentage and value is {}"
                           .format(self.MEMORY_THRESHOULD, utilization_memory))
        else:
            raise content_exceptions.TestFail("Memory Usage percentage is morethan {} percentage and value is {}"
                                              .format(self.MEMORY_THRESHOULD, utilization_memory))
        # Step logger end for Step 7
        self._test_content_logger.end_step_logger(7, return_val=True)

        # Step logger start for Step 8
        self._test_content_logger.start_step_logger(8)

        # Collecting & Displaying the application event logs.
        application_logs = self._windows_event_log.get_application_event_error_logs(
            "-Source Application Hang,Application Fault -EntryType Error,Warning")

        # Check if there are any errors, warnings
        if application_logs is None or len(str(application_logs)) == 0:
            self._log.info("No errors or warnings found in OS application log...")
            final_result.append(True)
        else:
            self._log.error("Found errors or warnings in OS application log...")
            self._log.error("Error logs: \n" + str(application_logs))
            final_result.append(False)

        # Step logger end for Step 8
        self._test_content_logger.end_step_logger(8, return_val=all(final_result))

        # Step logger start for Step 8
        self._test_content_logger.start_step_logger(9)

        # Collecting & Displaying the system event logs.
        system_logs = self._windows_event_log.get_whea_error_event_logs()

        # Check if there are any errors, warnings
        if system_logs is None or len(str(system_logs)) == 0:
            self._log.info("No errors or warnings found in OS system log...")
            final_result.append(True)
        else:
            self._log.error("Found errors or warnings in OS system log...")
            self._log.error("Error logs: \n" + str(system_logs))
            final_result.append(False)

        # Step logger end for Step 8
        self._test_content_logger.end_step_logger(9, return_val=all(final_result))

        return all(final_result)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if DimmMaximumMemoryConfigReportingWindows.main() else Framework.TEST_RESULT_FAIL)
