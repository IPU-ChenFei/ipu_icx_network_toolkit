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
import threading

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.os_lib import WindowsCommonLib
from src.lib.install_collateral import InstallCollateral
from src.provider.pm_provider import PmProvider
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.dtaf_content_constants import PowerManagementConstants


class PowerManagementACPIDeviceCheckAfterSystemIdleForLongTimeWindows(ContentBaseTestCase):
    """
    Glasgow ID : 44017.3
    Verify all the system devices work well after Windows system idle for long time.

    1. ENABLE all available C States BIOS knobs
    2. Clear all Os logs.
    3. configure Power Options are properly.
    4. Launch the OS embedded performance monitor tool (e.g. Performance Monitor) to monitor system C state residency.
    5. Go to SUT device manager, make sure all installed devices are recognized and make a full list of them.
    6. Leave the SUT idle for 24 hours.
    7. Check the SUT device manager for any devices displaying warnings and make a full list of all recognized devices.
    8. Compare step 5 & step 6 data.
    """
    BIOS_CONFIG_FILE = "enable_c_state_bios_knobs.cfg"
    TEST_CASE_ID = "G44017"
    PERFORMANCE_MANAGER_PYTHON_FILE = "performance_counter.py"
    RUN_PERFORMANCE_MANAGER_CMD = r'python performance_counter.py "\Processor(*)\% {}" "%s {}" "{}.txt"'
    COUNTER_VALUE_DICT = {"C1 Time": ">0", "C2 Time": ">0", "C3 Time": "==0", "Idle Time": ">0"}
    C_DRIVE = "C:\\"
    MINUTE = 60

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PowerManagementACPIDeviceCheckAfterSystemIdleForLongTimeWindows object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PowerManagementACPIDeviceCheckAfterSystemIdleForLongTimeWindows, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._os_lib = WindowsCommonLib(test_log, self.os)
        self._pm_provider = PmProvider.factory(test_log, cfg_opts, self.os)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):  # type: () -> None
        super(PowerManagementACPIDeviceCheckAfterSystemIdleForLongTimeWindows, self).prepare()

    def execute(self):
        # set sleep time to 0
        self._pm_provider.set_sleep_timeout(PowerManagementConstants.SLEEP_TIMEOUT_NEVER)
        complete_python_file_path = self._install_collateral.download_tool_to_host(self.PERFORMANCE_MANAGER_PYTHON_FILE)
        self.os.copy_local_file_to_sut(complete_python_file_path, self.C_DRIVE)
        # running Performance Manager script to capture the C-State residency counters
        command_timeout = PowerManagementConstants.SYSTEM_IDLE_TIME_24_HRS + 100
        for key, value in self.COUNTER_VALUE_DICT.items():
            self._log.info("Executing {} Performance Manager script".format(key))
            execute_performance_manager_thread = threading.Thread(target=self.run_performance_manager,
                                                                  args=(key, value, command_timeout, ))
            execute_performance_manager_thread.start()
            self._log.info("{} Performance Manager script thread is started".format(key))
        # capture the error devices before Idle time
        pre_idle_error_device_set = set(self._os_lib.get_error_devices())
        # sleep time for 24hrs
        self._log.info("System is set to Idle state for {} minutes".
                       format(PowerManagementConstants.SYSTEM_IDLE_TIME_24_HRS // self.MINUTE))
        start_time = time.time()
        current_time = time.time() - start_time
        while current_time <= PowerManagementConstants.SYSTEM_IDLE_TIME_24_HRS:
            if not self.os.is_alive():
                raise RuntimeError("SUT is not responding at %d secs during the idle time", current_time)
            self._log.debug("Waiting for %d seconds", PowerManagementConstants.WAIT_TIME)
            time.sleep(PowerManagementConstants.WAIT_TIME)
            current_time = time.time() - start_time
        self._log.info("Successfully completed system Idle state for {} minutes".
                       format(PowerManagementConstants.SYSTEM_IDLE_TIME_24_HRS // self.MINUTE))

        # kill the powershell.exe to stop the performance manager process
        self._os_lib.kill_process("powershell.exe")
        # capture the error devices after Idle time
        post_idle_error_device_set = set(self._os_lib.get_error_devices())

        # check the C-state residency counters after Idle time
        error_list = []
        for key, value in self.COUNTER_VALUE_DICT.items():
            log_file_name = key.replace(" ", "_").lower()
            out_put_data = self._common_content_lib.execute_sut_cmd("type {}.txt".format(log_file_name), "print {}.txt "
                                                                    "file".format(log_file_name + ".txt"),
                                                                    self._command_timeout, cmd_path=self.C_DRIVE)
            self._log.debug("output data of {} file:\n {}".format(log_file_name + ".txt", out_put_data))
            if key == "C3 Time":
                if "False" in out_put_data:
                    error_list.append("{} state residency value is not expected, check the logs for more info".
                                      format(key))
                    self._log.error("{} counter data is not meeting the threshold".format(key))
            else:
                if "True" not in out_put_data:
                    error_list.append("{} state residency value is not expected, check the logs for more info".
                                      format(key))
                    self._log.error("{} counter data is not meeting the threshold".format(key))
        if error_list:
            raise RuntimeError("\n".join(error_list))
        self._log.info("Successfully verified all the C-State residency counter values")
        # checking if any new error device got detected after Idle time
        if post_idle_error_device_set-pre_idle_error_device_set:
            raise RuntimeError("Few devices are detected after idle time with errors")
        self._log.info("No new Device Manager issues after idle time")
        return True

    def run_performance_manager(self, counter_name, condition, command_timeout):
        """Function to run the performance manager python script file on SUT
        :param counter_name: c-state counter name
        :param condition: condition to check the c-state counter
        :param command_timeout: command time to run the performance manager script
        :return: None
        :raise: None
        """
        self.os.execute(self.RUN_PERFORMANCE_MANAGER_CMD.format(counter_name, condition,
                                                                counter_name.replace(" ", "_").lower()),
                        command_timeout, cwd=self.C_DRIVE)

    def cleanup(self, return_status):
        """cleanup"""
        self.os.reboot(self.reboot_timeout)
        super(PowerManagementACPIDeviceCheckAfterSystemIdleForLongTimeWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PowerManagementACPIDeviceCheckAfterSystemIdleForLongTimeWindows.main()
             else Framework.TEST_RESULT_FAIL)
