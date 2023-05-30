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


class DcCyclingColdResetGraceful(DDRCommon):
    """
    Glasgow ID: 57805
    Platform maintains configuration settings, and system does not fail with any unexpected error conditions.
    Verify that a system can perform DC system reset cycles including OS boot and shutdown without unexpected errors.
    pre-requisites:
    1.Microsoft Windows OS
    """
    BIOS_CONFIG_FILE = "memory_bios_knobs_59060_57805.cfg"  # Bios Configuration File
    WINDOWS_PLATFORM_CYCLER_LOG_FOLDER = r"platform_cycler\logs"
    WINDOWS_PLATFORM_CYCLER_FOLDER = "platform_cycler_win"
    WINDOWS_PLATFORM_CYCLER_ZIP_FILE = "platform_cycler_win-20191115.zip"
    SEL_ZIP_FILE = "SELViewer.zip"
    PRIME95_ZIP_FILE = "p95v298b6.win64.zip"
    TEST_CASE_ID = "G57805"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance DcCyclingColdResetGraceful
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        :raises: None
        """
        # calling StressTestCommon init
        super(DcCyclingColdResetGraceful, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clearing the system event logs
        2. Setting the bios knobs to its default mode.
        3. Setting the bios knobs as per the test case.
        4. Rebooting the SUT to apply the new bios settings.
        5. Verifying the bios knobs that are set.
        6. Copy platform_cycler_win-20191115.zip, selviewer.zip, p5v298b6.win.64.zip to Windows SUT.
        7. Unzip the platform_cycler_win-20191115.zip, selviewer.zip, p5v298b6.win.64.zipfile
        """
        self._windows_event_log.clear_system_event_logs()  # To clear system event logs
        self._bios_util.load_bios_defaults()  # # To set the Bios Knobs to its default mode
        self._bios_util.set_bios_knob()  # To set the bios knob setting
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set

        # Copy the platform_cycler_win.zip file to windows SUT
        self._install_collateral.install_platform_cycler()
        # Copy sel viewer.zip file to windows SUT
        self._install_collateral.install_selviewer()
        # Copy p95v298b6.win64.zip file to windows SUT
        self._install_collateral.install_prime95()

    def execute(self):
        """
        This function is used to execute the dc graceful installer and log parsing.
        :return: True if all log files parsed without any errors else false
        """
        self.execute_installer_dc_graceful_windows(
            windows_folder_name=self.WINDOWS_PLATFORM_CYCLER_ZIP_FILE.split(".")[0], command="dcgraceful -prime")

        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.WINDOWS_PLATFORM_CYCLER_LOG_FOLDER,
            extension=".log")

        stress_test_result = []
        # Get whea error,warning logs
        whea_logs = self._windows_event_log.get_whea_error_event_logs()
        # Check if there are any errors, warnings of category WHEA found
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
            (log_path=os.path.join(windows_log_folder, "platform_cycler.log"), encoding='UTF-16')]

        return all(final_result)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if DcCyclingColdResetGraceful.main() else Framework.TEST_RESULT_FAIL)
