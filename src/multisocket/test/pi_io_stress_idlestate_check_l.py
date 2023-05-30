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
import re
import os
import time
from dtaf_core.lib.dtaf_constants import Framework
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions
from src.provider.pm_provider import PmProvider
from src.lib.test_content_logger import TestContentLogger
from src.provider.vss_provider import VssProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import PowerManagementConstants
from src.multisocket.lib.multisocket_common import MultiSocketCommon


class PiIOStressIdleStateCheck(ContentBaseTestCase):
    """
    Phoenix 18014074894, PI_IO_stress_idlestate check_L

    The intention is the check the system behavior when the system is  IO- stressed using ILVSS tool and ensure the all
    CPU cores comes back to idle state after the test.
    """

    TEST_CASE_ID = ["18014074894", "PI_IO_stress_idlestate check_L"]
    PROCESS_NAME = "texec"
    CLOCK_COMMAND_LINUX = r"cat /sys/devices/system/clocksource/clocksource0/current_clocksource"
    ILVSS_CMD = "./t /pkg /opt/ilvss.0/packages/stress_egs.pkx /reconfig /pc EGS /flow S145 /run /minutes {} /rr {}"
    LOG_NAME = "ilvss_log.log"
    TOP_CMD = r"top -1 -n 5 -b| grep 'load average:'"
    REGEX_TOP_CMD_OUTPUT = r"load\saverage\:\s0\.00\,\s0\.00\,\s0\.00"
    WAIT_TIME_OUT = 5
    MINUTE = 60
    step_data_dict = {1: {'step_details': 'check the clock source.',
                          'expected_results': 'clock health checked successfully'},
                      2: {'step_details': 'Select package in ilVSS and run workload ',
                          'expected_results': 'ilvss stress applied successfully'},
                      3: {'step_details': ' let CPU idle over night',
                          'expected_results': 'Successfully completed system Idle state over night.'},
                      4: {'step_details': 'check load avg value',
                          'expected_results': 'verified load avg value successfully'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance IOPCHIOIODevicesStressL

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        :raises: None
        """

        # calling base class init
        super(PiIOStressIdleStateCheck, self).__init__(test_log, arguments, cfg_opts)
        self.health_check_log_dir = os.path.join(self.log_dir, "health_check")
        # Object of TestContentLogger class
        self._pm_provider = PmProvider.factory(test_log, cfg_opts, self.os)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._vss_provider_obj = VssProvider.factory(self._log, cfg_opts=cfg_opts, os_obj=self.os)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._ilvss_runtime = self._common_content_configuration.memory_ilvss_run_time()
        self._silicon_family = self._common_content_lib.get_platform_family()
        self.initialize_sv_objects()
        self.initialize_sdp_objects()
        self._multisock_obj = MultiSocketCommon(test_log, arguments, cfg_opts)

    def prepare(self):  # type: () -> None
        """
        execute prepare

        return None
        """
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNotImplementedError("Test not implemented for OS {}".format(self.os.os_type))
        self._multisock_obj.check_topology_speed_lanes(self.SDP)

    def execute(self):
        """
        1. check clock health
        2. apply ilvss stress
        3. check load avg value

        :return: True, if the test case is successful.
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(1)
        if self.os.os_type == OperatingSystems.LINUX:
            cmd_out_put = self._common_content_lib.execute_sut_cmd(sut_cmd=self.CLOCK_COMMAND_LINUX,
                                                                   cmd_str=self.CLOCK_COMMAND_LINUX,
                                               execute_timeout=self._command_timeout)
            if "tsc" not in cmd_out_put:
                self._log.error("Clock health check failed. Output of cmd %s execution is %s"%(self.CLOCK_COMMAND_LINUX,cmd_out_put))
            else:
                self._log.info("Clock health check Passed.")

        else:
            raise content_exceptions.TestNotImplementedError("not implemented for {}".format(self.os.os_type))

        self._test_content_logger.end_step_logger(1, return_val=True)

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        # installing screen package
        self._install_collateral.screen_package_installation()
        self.os.execute_async(self.ILVSS_CMD.format(self._ilvss_runtime, self.LOG_NAME),
                              self._vss_provider_obj.OPT_IVLSS)
        time.sleep(self._command_timeout)
        ilvss_hostfilepath = self.log_dir + "\\" + self.LOG_NAME
        self.os.copy_file_from_sut_to_local(self._vss_provider_obj.OPT_IVLSS + "/" + self.LOG_NAME, ilvss_hostfilepath)

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._pm_provider.set_power_scheme("Balanced")
        self._pm_provider.set_sleep_timeout(PowerManagementConstants.SLEEP_TIMEOUT_NEVER)
        self._pm_provider.set_screen_saver_blank(PowerManagementConstants.BLANK_SCREEN_TIMEOUT)
        self._log.info("System is set to Idle state for {} minutes".
                       format(PowerManagementConstants.SYSTEM_IDLE_TIME_12_HRS // self.MINUTE))
        start_time = time.time()
        current_time = time.time() - start_time
        while current_time <= PowerManagementConstants.SYSTEM_IDLE_TIME_12_HRS:
            if not self.os.is_alive():
                raise RuntimeError("SUT is not responding at %d secs during the idle time", current_time)
            self._log.debug("Waiting for %d seconds", PowerManagementConstants.WAIT_TIME)
            time.sleep(PowerManagementConstants.WAIT_TIME)
            current_time = time.time() - start_time
        self._log.info("Successfully completed system Idle state for {} minutes".
                       format(PowerManagementConstants.SYSTEM_IDLE_TIME_12_HRS // self.MINUTE))
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)
        # step logger start for step 4
        self._test_content_logger.start_step_logger(4)
        # Executing top command and validating load average value
        usage_data = []
        output_txt = self._common_content_lib.execute_sut_cmd(self.TOP_CMD, self.TOP_CMD, self._command_timeout)
        time.sleep(self.WAIT_TIME_OUT)
        self._log.debug("Result of top command is :{}".format(output_txt))
        top_cmd_data = [cmd_data.strip() for cmd_data in output_txt.split("\n") if cmd_data != ""]
        # for valid_data in top_cmd_data:
        usage_data.append(str(bool(ele for ele in top_cmd_data if ele not in self.REGEX_TOP_CMD_OUTPUT)))
        if all(usage_data):

            self._log.info("Load average is showing output in top command")
        else:

            self._log.error("Load average is showing 0 output in top command")

        self._multisock_obj.check_topology_speed_lanes(self.SDP)
        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiIOStressIdleStateCheck.main() else Framework.TEST_RESULT_FAIL)
