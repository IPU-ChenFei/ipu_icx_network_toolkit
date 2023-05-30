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
import time
import subprocess
from subprocess import Popen, PIPE, STDOUT

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.memory_hbm.memory_hbm_common import MemoryHbmCommon
from src.lib.memory_constants import MemoryTopology, MemoryClusterConstants
from src.memory.tests.memory_ddr.ddr_common import DDRCommon
from src.lib.memory_constants import PlatformMode


class PIMemoryFlatModeMemtest(MemoryHbmCommon):
    """
    Phoenix ID:16014741325 - PI_Memory_Flat_Mode_Memtest_L
    """

    TEST_CASE_ID = ["16014741325", "PI_Memory_Flat_Mode_Memtest_L"]
    BIOS_CONFIG_FILE = "one_lm_bios_knob.cfg"

    step_data_dict = {1: {'step_details': 'Clear OS logs and Set the bios knobs, Restart the system, Boot to OS',
                          'expected_results': 'Cleared os logs and bios settings is done.Successfully boot to os'
                                              'and verified the bios knobs'},
                      2: {'step_details': 'Verify memory displayed at POST and amount of memory reported by the '
                                          'EDKII Menu -> System Information with amount of memory installed in the '
                                          'system',
                          'expected_results': 'Verified POST memory and System Information matched with amount of '
                                              'memory installed in system'},
                      3: {'step_details': 'Run MemTest86 tool',
                          'expected_results': 'Should pass without any errors'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PIMemoryFlatModeMemtest object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        bios_config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)

        super(PIMemoryFlatModeMemtest, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path)

        self._ddr_common = DDRCommon(test_log, arguments, cfg_opts)
        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._usb_drive_name = None
        self._boot_select_path = "Boot Manager Menu"

    def prepare(self):
        # type: () -> None
        """
        1. To clear os log.
        2. Set the bios knobs to its default mode and 1LM bios setting.
        3. Power cycle the SUT to apply the new bios settings.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        super(PIMemoryFlatModeMemtest, self).prepare()
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. To check system memory in EDKII Menu --> System Information
        2. To check mce errors
        3. To check the number of nodes and node memory.

        :return: True, if the test case is successful.
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        self._memory_provider.verify_1dpc_or_2dpc_memory_configuration()

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        if not self.switch_usb_to_host():
            self._log.error("USB_DRIVE Is Not Connected To Host")
            return False

        usb_drive_name = self._common_content_configuration.get_usb_name_memtest86()
        self._usb_drive_name = self.check_usb_name(usb_drive_name)

        usb_drive_size = self._common_content_configuration.get_usb_size_memtest86()
        self.format_usb_drive(usb_drive_size)

        self._boot_select_path += "," + str(self._usb_drive_name)

        # Mandatory for USB To Be Connect To SUT
        if not self.switch_usb_to_target():
            self._log.error("USB_DRIVE Is Not Connected To Platform(SUT)")
            return False

        if not self.platform_ac_power_off():
            self._log.error("Failed To Platform Ac-Power OFF")
            return False

        if not self.platform_ac_power_on():
            self._log.error("Failed To Platform Ac-Power ON")
            return False

        # Enter Into bios and change boot order and select USB for Installation
        self._log.info("Entering Into Bios SETUP Page of Target Platform")
        if not self.enter_into_bios():
            self._log.error("Didn't Enter Into Bios_Setup Page")
            return False

        self._log.info("Entering Into Bios SETUP Page To Select USB For Mem Test")

        if self.bios_path_navigation(path=self._boot_select_path):
            self._log.info("Selecting USB To Proceed with MemTest Boot Successful")
        else:
            self._log.error("Unable To Enter Into Bios SETUP Page")
            return False

        self._log.info("MemTest86 In Progress Will Taken Some Time to Finish.")

        # Periodic check of memtest86 running
        start_time = time.time()
        seconds = 43200 #  12 hours in seconds
        while True:
            current_time = time.time()
            elapsed_time = current_time - start_time
            time.sleep(1800) #  Every 30 minutes
            self._log.info("Checking the MemTest86 execution progress via reading the serial console screen..")

            memtest86_screen_progress = self.setupmenu.get_current_screen_info()
            self._log.info(memtest86_screen_progress.result_value)

            if elapsed_time > seconds:
                self._log.info("Finished iterating in: {} Minute(s)".format(str(int(elapsed_time / 60) / 60)))
                break

        self.press_button("c", True, 15)
        self._log.info("Interrupted the execution, with letter 'C'")

        self.press_button("2", True, 15)
        self._log.info("Exiting the execution by selecting 2nd option..")

        memtest86_test_complete = self.setupmenu.get_current_screen_info()
        self._log.info(memtest86_test_complete.result_value)

        if "Test Complete" or "Test complete" in memtest86_test_complete.result_value:
            # Once we encounter Test complete, pressing any key to display the summary
            self._log.info("Test complete Page, Pressing any key to display the summary..")
            self.press_button("e", True, 15)

        memtest86_res_summary = self.setupmenu.get_current_screen_info()
        self._log.info(memtest86_res_summary.result_value)

        if "press any key to continue" in memtest86_res_summary.result_value:
            # Result summary page, Pressing any key to continue
            self._log.info("Result summary page, Pressing any key to continue..")
            self.press_button("e", True, 15)

        time.sleep(10)

        # Save report page, Pressing (y)es to save
        self._log.info("Save report page, Pressing (y)es to save the report..")
        self.press_button("y", True, 15)

        # wait till the control comes out of execution.
        time.sleep(10)

        if not self.platform_ac_power_off():
            self._log.error("Failed To Platform Ac-Power OFF")
            return False

        if not self.platform_ac_power_on():
            self._log.error("Failed To Platform Ac-Power ON")
            return False

        if not self.switch_usb_to_host():
            self._log.error("USB_DRIVE Is Not Connected To Host")
            return False

        cmd_line = "wmic LOGICALDISK LIST BRIEF | findstr MEMTEST86"

        process_obj = subprocess.Popen(cmd_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process_obj.communicate()

        if process_obj.returncode != 0:
            log_error = "The command '{}' failed with error '{}' ...".format(cmd_line, stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info("The command '{}' executed successfully..".format(cmd_line))
        self._log.info("The command output is: {}".format(stdout))
        stdout = stdout.decode()
        memtest_usb_letter = str(stdout).strip().split()[0].split(":")[0]
        self._log.info("Memtest86 usb drive letter is:{}".format(memtest_usb_letter))

        no_error = True
        with open("{}:\EFI\BOOT\MemTest86.log".format(memtest_usb_letter), "r") as log_read:
            for line in log_read.readlines():
                if "error count:" in line:
                    if "error count: 0" in line:
                        self._log.info(line)
                    else:
                        no_error = False
                        self._log.info("This line has error count --> {}".format(line))

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=no_error)
        return no_error

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PIMemoryFlatModeMemtest, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PIMemoryFlatModeMemtest.main() else Framework.TEST_RESULT_FAIL)
