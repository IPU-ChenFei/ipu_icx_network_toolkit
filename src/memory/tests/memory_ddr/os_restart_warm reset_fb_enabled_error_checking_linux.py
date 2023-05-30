#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import subprocess
import codecs

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_ddr. ddr_common import DDRCommon
from src.manageability.lib.redfish_test_common import RedFishTestCommon


class StressTestRebootFastBootEnableddr5(DDRCommon):
    """
    Glasgow ID : 63306.0

    This test case is to demonstrate OS warm Restart and verify that the system can perform many OS warm restarts
    without error with a given ddr5 memory configuration.
    Operating System: Linux
    This testing covers the below tasks..
    1. OS warm restart testing of a Memory configuration.
    2. Memory "Fast" Warm and Cold reset are enabled, forcing a platform memory reconfiguration by the MRC on each boot
    cycle.
    3. Stress apptest is executed for about two minutes on each cycle to exercise system memory.
    """
    # Bios knob config file to set the appropriate knobs.
    BIOS_CONFIG_FILE = "os_restart_bios_knobs_warm_reset_fb_enabled_error_checking_linux.cfg"

    TEST_CASE_ID = "G63306"
    IPMCTL_TOOL_FILE = "ipmitool_file"

    step_data_dict = {1: {'step_details': 'Clear OS logs , dmesg logs and Set & Verify BIOS knobs',
                          'expected_results': 'Clear ALL the OS ,dmesg logs and BIOS setup options '
                                              'are updated with changes saved'},
                      2: {'step_details': 'Clear SEL log with ipmitool and BMC',
                          'expected_results': 'Successfully cleared sel log'},
                      3: {'step_details': 'Installing platform cycler in linux SUT ',
                          'expected_results': 'Successfully done without errors'},
                      4: {'step_details': 'Executing the platform cycler command in SUT to check warm fast reboot '
                                          'working or not',
                          'expected_results': 'Successfully should reboot and generate the logs'},
                      5: {'step_details': 'Copying log files SUT to Local system and should do log parsing',
                          'expected_results': 'Successfully done without errors in logs'},
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new StressTestRebootFastBootEnableddr5 object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        super(StressTestRebootFastBootEnableddr5, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._redfish_obj = RedFishTestCommon(test_log, arguments, cfg_opts)
        self._platform_cycler_extract_path = None

    def prepare(self):
        # type: () -> None
        """
        1. Clear OS , dmesg logs
        2. Setting the bios knobs to its default mode.
        3. Setting the bios knobs as per the test case.
        4. Rebooting the SUT to apply the new bios settings.
        5. Verifying the bios knobs that are set.
        6. Clear SEL logs
        7. Copy platform cycler tool tar file to Linux SUT.
        8. Unzip tar file under user home folder.
        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self._common_content_lib.clear_os_log()  # To clear os logs
        self._common_content_lib.clear_dmesg_log()  # To clear dmesg logs
        self._bios.default_bios_settings()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        # Step Logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # clear sel log
        self._log.info("Clear the sel log using BMC command through redfish")
        self._redfish_obj.clear_sel()

        # Step Logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        # Install platform cycler tool in SUT
        self._platform_cycler_extract_path = self._install_collateral.install_platform_cycler()
        # Step Logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

    def execute(self):
        """
        Execution of platform cycler installer tool

        Also, checks whether operating system is alive or not and wait till the operating system to boot up.
        :return: True, if the test case is successful.
        :raise: SystemError: Os is not alive even after specified wait time.
        """
        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        # call installer reboot stress test
        self.execute_installer_reboot_stress_test_linux(self._platform_cycler_extract_path)

        # Step Logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        if self._os.is_alive():
            self._log.info("SUT is alive after stress test ...")
        else:
            self._log.info("SUT is not alive after stress test and we will wait for reboot "
                           "timeout for SUT to come up ...")
            self._os.wait_for_os(self._reboot_timeout)  # should check this for os timeout.

        if not self._os.is_alive():
            self._log.error("SUT did not come-up even after waiting for specified time...")
            raise RuntimeError("SUT did not come-up even after waiting for specified time...")

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        # Deleting the test case log folder in host if present
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        # Copying log files from sut to host
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.LINUX_PLATFORM_REBOOTER_LOG_PATH, extension=".log")

        # Step Logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=log_path_to_parse)

        return self.log_parsing_rebooter(log_file_path=log_path_to_parse)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StressTestRebootFastBootEnableddr5.main() else Framework.TEST_RESULT_FAIL)
