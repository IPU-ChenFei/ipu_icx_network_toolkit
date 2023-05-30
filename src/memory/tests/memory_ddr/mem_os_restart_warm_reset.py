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

from dtaf_core.lib.dtaf_constants import Framework
from src.memory.tests.memory_ddr.ddr_common import DDRCommon


class OsRestartWarmReset(DDRCommon):
    """
    Glasgow ID: 59060
    OS Restart testing, verify that the system can perform many OS restarts without error
    System maintains configuration settings without unexpected error conditions.
    pre-requisites:
    1.Microsoft Windows OS
    """
    BIOS_CONFIG_FILE = "memory_bios_knobs_59060_57805.cfg"  # Bios Configuration File
    WINDOWS_MEM_REBOOTER_LOG_FOLDER = "mem_rebooter_win"
    WINDOWS_MEM_REBOOTER_ZIP_FILE = "mem_rebooter_installer_win-20190206.zip"
    LOG_PATH = r"C:\mem_rebooter_win"
    SEL_ZIP_FILE = "SELViewer.zip"
    TEST_CASE_ID = "G59060"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance OsRestartWarmReset.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        :raises: None
        """

        # calling StressTestCommon init
        super(OsRestartWarmReset, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clearing the system event logs
        2. Setting the bios knobs to its default mode.
        3. Setting the bios knobs as per the test case.
        4. Rebooting the SUT to apply the new bios settings.
        5. Verifying the bios knobs that are set.
        6. Copy mem_rebooter_installer_win-20190206.zip and SELViewer.zip to Windows SUT.
        7. Unzip the mem_rebooter_installer_win-20190206.zip file and SELViewer.zip
        """

        self._windows_event_log.clear_system_event_logs()  # To clear system event logs
        self._bios_util.load_bios_defaults()  # # To set the Bios Knobs to its default mode
        self._bios_util.set_bios_knob()  # To set the bios knob setting
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set

        # Copy mem_rebooter_installer_win-20190206.zip file to windows SUT
        self._install_collateral.install_mem_rebooter()
        # Copy SELViewer.zip file to windows SUT
        self._install_collateral.install_selviewer()

    def execute(self):
        """
        This function is used to execute the installer and log parsing.

        :return: True if all log files parsed without any errors else false
        """

        self.execute_installer_windows_mem_reboot(windows_folder_name=self.WINDOWS_MEM_REBOOTER_ZIP_FILE.split(".")[0])

        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.LOG_PATH, extension=".log")

        stress_test_result = []
        # Get whea error, warning logs
        whea_logs = self._windows_event_log.get_whea_error_event_logs()
        # check if there are any errors, warnings of category WHEA found
        if whea_logs is None or len(str(whea_logs)) == 0:
            self._log.info("No WHEA errors or warnings found in Windows System event log...")
            stress_test_result.append(True)
        else:
            self._log.error("Found WHEA errors or warnings in Windows System event log...")
            self._log.error("WHEA error logs: \n" + str(whea_logs))
            stress_test_result.append(False)

        stress_test_result.append(self.parse_logs(windows_log_folder=log_path_to_parse))

        return all(stress_test_result)

    def parse_logs(self, windows_log_folder):
        """
        To Verify the errors in the log files

        :param windows_log_folder: Host log path
        :return: True if all log files parsed without any errors else false
        """

        self._log.info("Logs checking started....")

        final_result = [
            self._memory_common_lib.parse_log_for_error_patterns
            (log_path=os.path.join(windows_log_folder, "Windows-Kernel.log"), encoding='UTF-16'),
            self._memory_common_lib.parse_log_for_error_patterns
            (log_path=os.path.join(windows_log_folder, "HardWareEvents.log"), encoding='UTF-16'),
            self._memory_common_lib.parse_log_for_error_patterns
            (log_path=os.path.join(windows_log_folder, "sel.log"), encoding='UTF-8'),
            self._memory_common_lib.parse_memory_log_windows
            (log_path=os.path.join(windows_log_folder, "memory.log")),
            self._memory_common_lib.parse_log_for_error_patterns
            (log_path=os.path.join(windows_log_folder, "mem_rebooter_win.log"), encoding='UTF-16')]

        return all(final_result)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if OsRestartWarmReset.main() else Framework.TEST_RESULT_FAIL)
