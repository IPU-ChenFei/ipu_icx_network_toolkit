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
import threading
import time

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.memory.tests.memory_ddr.ddr_common import DDRCommon
from src.lib.memory_constants import PowerScheme


class MemoryModeStress(DDRCommon):
    """
    Glasgow ID: 63309
    To verify the memory subsystem functionality and reliability under Windows with heavy stress on a 64 bit platform.

    1. Design Verification of the memory sub-system.
    2. System Stability of DDRx DIMMs.
    3. Prime 95 is used as a memory subsystem workload stress tool.
    """
    _bios_config_file = "memory_bios_knobs_prime_stress.cfg"
    TEST_CASE_ID = "G63309"
    _prime95_executer_path = None
    LIST_PROCESSES = ["prime95.exe"]
    return_value = []

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new MemoryModeStress object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(MemoryModeStress, self).__init__(test_log, arguments, cfg_opts, self._bios_config_file)
        self.system_memory_info = None
        self.partition_data_before_stress = None
        self.partition_data_after_stress = None

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.
        5. Copy prime 95 tool zip file to Windows SUT.
        6. Unzip the file under C drive.

        :return: None
        """
        self._windows_event_log.clear_system_event_logs()  # Clear system even log
        self._windows_event_log.clear_application_logs()  # Clear Application log

        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob settings.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios settings.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

        # Confirm the power scheme is set to "High Performance".
        self._windows_common_lib.set_power_scheme(option=PowerScheme.HIGH_PERFORMANCE)

        #  Set the display to never turn off (Disable screen blanking and / or the screen saver).
        self._windows_common_lib.screen_awake_settings()

        # To get the total physical memory
        total_dram_memory_os = self.get_total_memory_win().split(" ")[0].replace(",", "")

        # To convert MB to GB
        total_dram_memory_os = int(float(total_dram_memory_os) / 1024)

        self._log.info("Total memory capacity shown OS Level : {} GB".format(total_dram_memory_os))

        total_memory_variance_post = self._post_mem_capacity_config - (self._post_mem_capacity_config *
                                                                       self._variance_percent)

        total_memory_variance_dram = self._ddr4_mem_capacity_config - (self._ddr4_mem_capacity_config *
                                                                       self._variance_percent)

        self._log.info("Total POST reported DDR capacity as per configuration with - {} % variance is : {} GB".format(
            self._variance_percent, total_memory_variance_post))

        if total_dram_memory_os < int(total_memory_variance_post) or total_dram_memory_os > \
                self._post_mem_capacity_config:
            raise content_exceptions.TestFail("Total Installed DDR memory Capacity reported during POST "
                                              "Configuration (vs) OS does not match.")

        self._log.info("Total Installed DDR memory Capacity reported during POST Configuration (vs) OS matches.")

        if total_dram_memory_os < int(total_memory_variance_dram) or total_dram_memory_os > \
                self._ddr4_mem_capacity_config:
            raise content_exceptions.TestFail("Total Installed DDR memory Capacity reported in BIOS Configuration (vs)"
                                              "OS does not match.")

        self._log.info("Total Installed DDR memory Capacity reported during BIOS Configuration (vs) OS matches.")

        # Store partition data before stress test.
        self.partition_data_before_stress = self.store_partition_data_win()

        # Task Manager to confirm system memory reports.
        mem_value_before_torture_test = self._windows_common_lib.task_manager_wmic_mem_get(task_option="capacity")

        self._log.info("Total system memory before torture test in {}".format(mem_value_before_torture_test))

        # The amount of "Total Physical Memory" reported by System Information utility
        self.system_memory_info = self._windows_common_lib.get_system_memory()

        self._prime95_executer_path = self._install_collateral.install_prime95()

    def execute(self):
        """
        Used to get number of cycles, wait time and timeout.
        Also, checks whether operating system is alive or not and wait till the operating system to boot up.

        :return: True, if the test case is successful.
        :raise: SystemError: Os is not alive even after specified wait time.
        """

        self.create_prime95_preference_txt_file_win(self._prime95_executer_path, self.system_memory_info)

        # Execute the prime95 / update the prime.txt file with the configuration.
        prime95_thread = threading.Thread(target=self.execute_prime95_torture_windows,
                                          args=("prime95.exe -t", self._prime95_executer_path,))
        # Thread has been started
        prime95_thread.start()

        # For safety purpose - Just to wait for 10 more sec, so that the process will start in the background.
        time.sleep(10)

        # Verify the background process is running
        self._memory_common_lib.verify_background_process_running(self.LIST_PROCESSES)

        self._log.info("Running the prime95 test...\n "
                       "Waiting while the prime95 torture test to run for some time frame .....")

        # Running time of the prime95 tool
        time.sleep(self.prime95_running_time)

        # Get the Cpu utilization
        cpu_utilization = self._windows_common_lib.task_manager_wmic_cpu_get(task_option="loadpercentage")

        # Verify cpu usage is high
        cpu_utilization_percent_config = self._common_content_configuration.\
            get_cpu_utilization_percent_for_prime95_test()
        self.return_value.append(self._memory_common_lib.verify_cpu_utilization(cpu_utilization,
                                                                                cpu_utilization_percent_config))

        # Get the total physical memory value from Os
        get_physical_memory_data_win = self._windows_common_lib.get_system_memory()

        # Verify memory usage is high
        percentage_mem_util_config = self._common_content_configuration.get_mem_utilization_percent_for_prime95_test()
        self.return_value.append(self._memory_common_lib.verify_memory_utilization(get_physical_memory_data_win,
                                                                                   percentage_mem_util_config))

        # To stop the test by ending the Prime95 tasks in Task Manager.
        task_kill_cmd_verify = self._os.execute("taskkill /F /IM prime95.exe /T", self._command_timeout)

        if task_kill_cmd_verify.cmd_failed():
            self._log.error("Failed to execute the command {}".format(task_kill_cmd_verify))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(task_kill_cmd_verify, task_kill_cmd_verify.stderr))
        else:
            self._log.info("Prime95 execution has been terminated successfully..")

        # Store partition data after stress test.
        self.partition_data_after_stress = self.store_partition_data_win()

        self._log.debug("Partition details before stress test execution is shown below.. Presentation of data is "
                        ".. \n ****([Partition Sizes], [Partition Numbers])**** \n{}"
                        .format(self.partition_data_before_stress))
        self._log.debug("Partition details after stress test execution is shown below.. Presentation of data is "
                        ".. \n ****([Partition Sizes], [Partition Numbers])**** \n{}"
                        .format(self.partition_data_after_stress))

        if self.partition_data_after_stress != self.partition_data_after_stress:
            raise content_exceptions.TestFail("The system partitions are not as expected after the stress test, \n"
                                              "please check the Sizes of each partition and the partition numbers...")

        # Collecting & Displaying the application event logs.
        application_logs = self._windows_event_log.get_application_event_error_logs(
            "-Source prime95.exe,Application Hang,Application Fault -EntryType Error,Warning")

        # Check if there are any errors, warnings
        if application_logs is None or len(str(application_logs)) == 0:
            self._log.info("No errors or warnings found in OS application log...")
        else:
            self._log.error("Error logs: \n" + str(application_logs))
            raise content_exceptions.TestFail("Found errors or warnings in OS application log...")

        # Collecting & Displaying the system event logs.
        system_logs = self._windows_event_log.get_whea_error_event_logs()

        # Check if there are any errors, warnings
        if system_logs is None or len(str(system_logs)) == 0:
            self._log.info("No errors or warnings found in OS system log...")
        else:
            self._log.error("Error logs: \n" + str(system_logs))
            raise content_exceptions.TestFail("Found errors or warnings in OS system log...")

        return all(self.return_value)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(MemoryModeStress, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MemoryModeStress.main() else Framework.TEST_RESULT_FAIL)
