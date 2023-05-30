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

import re
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.install_collateral import InstallCollateral
from src.power_management.lib.reset_base_test import ResetBaseTest
import src.lib.content_exceptions as content_exceptions


class StabilityS3CyclingWindows(ResetBaseTest):
    """
    Testcase_id : H98429-PI_Stability_S3Cycling_W
    This TestCase is Used to Perform S3 Cycles and execute stress tool and verify whether stress tool is running
    after every iteration.
    """
    TEST_CASE_ID = ["H98429", "PI_Stability_S3Cycling_W"]
    STRESS_COMMAND_DICT = {"prime95": "prime95.exe -t"}
    SLEEP_VERIFICATION_CMD = "powercfg /a"
    REGEX_FOR_SLEEP_MODE = r"Standby.*S3.*"
    REGEX_FOR_AVAILABLE_SLEEP_MODES = r"The following sleep states are not available on this system:"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StabilityS3CyclingWindows object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(StabilityS3CyclingWindows, self).__init__(test_log, arguments, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._log.info("Installing the stress test")
        self._stress_app_path, self._stress_tool_name = self._install_collateral.install_prime95(app_details=True)

    def prepare(self):
        # type: () -> None
        """
        This Method is Used to Start the Stress tool Before Execution of Test Case and Verify whether S3 Mode is
        Enabled in the System.
        """
        self._log.info("Verifying whether S3 State is Enabled in the System")
        cmd_result = self._common_content_lib.execute_sut_cmd(self.SLEEP_VERIFICATION_CMD, self.SLEEP_VERIFICATION_CMD,
                                                              self._command_timeout)
        self._log.debug("Command Output is : {}".format(cmd_result))
        available_state_log = cmd_result.split(self.REGEX_FOR_AVAILABLE_SLEEP_MODES)[0]
        if not re.search(self.REGEX_FOR_SLEEP_MODE, available_state_log).group():
            raise content_exceptions.TestSetupError("S3 Mode is Not Enabled in this System")
        self._log.info("S3 Mode is Enabled in this System")
        self._log.info("Starting Stress test process")
        self._stress_provider.execute_async_stress_tool(self.STRESS_COMMAND_DICT[self._stress_tool_name],
                                                        self._stress_tool_name,
                                                        self._stress_app_path)
        self._log.debug("Stress test process has successfully started.")

    def execute(self):
        """
        This Method is Used to execute S3 Cycles for given number of time and Verify whether it is booted back to
        OS after every Iteration.

        :raise content_exceptions.TestFail: Whether Stress App is Not Running after S3 Cycle.
        :return: True or False
        """
        for iteration in range(self._common_content_configuration.get_num_of_s3_cycles()):
            self._log.info("Performing S3 cycle {}".format(iteration + 1))
            self.perform_s3_cycle()
            self._log.debug("Sut is Booted Back to OS after S3 Cycle Iteration{}".format(iteration + 1))
            self._log.info("Keeping System in OS Level for {} Seconds before verifying Stress App Running Status"
                           .format(self._common_content_configuration.get_waiting_time_of_s3_cycles()))
            time.sleep(self._common_content_configuration.get_waiting_time_of_s3_cycles())
            self._log.info("Verifying Stress App Running Status")
            if self._stress_provider.check_app_running(self._stress_tool_name):
                raise content_exceptions.TestFail("Stress App is Not Running after Performing S3 Cycle")
            self._log.debug("Stress App is Running after S3 Iteration {}".format(iteration+1))

        self._log.info("Sut is booted back to OS in all the '{}' S3 Cycles."
                       .format(self._common_content_configuration.get_num_of_s3_cycles()))

        return True

    def cleanup(self, return_status):
        """
        This Method is Used to Kill Stress Tool.
        """
        self._log.info("Killing Stress Tool")
        self._stress_provider.kill_stress_tool(self._stress_tool_name,
                                               self.STRESS_COMMAND_DICT[self._stress_tool_name])
        self._log.info("Stress Tool Execution is Stopped Successfully")
        super(StabilityS3CyclingWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StabilityS3CyclingWindows.main() else Framework.TEST_RESULT_FAIL)
