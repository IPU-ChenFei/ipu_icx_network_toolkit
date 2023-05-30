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

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.lib.dtaf_content_constants import TimeConstants, MLCToolConstants
from src.lib.install_collateral import InstallCollateral
from src.lib.platform_config import PlatformConfiguration
from src.lib.test_content_logger import TestContentLogger
from src.provider.stressapp_provider import StressAppTestProvider
from src.memory_hbm.memory_hbm_common import MemoryHbmCommon


class PiMemoryFlatQuadMlcLinux(MemoryHbmCommon):
    """
    HP QC ID: H109158 - PI_Memory_Flat_Mode_Quad_Mode_MLC_L and pheonix id : 16014741616

    """

    TEST_CASE_ID = ["16014741616", "PI_Memory_Flat_Mode_Quad_Mode_MLC_L"]
    EXECUTE_TIME = TimeConstants.ONE_HOUR_IN_SEC
    MLC_COMMAND = MLCToolConstants.MLC_PEAK_INJECTION_BANDWIDTH_CMD.format(EXECUTE_TIME)
    BIOS_CONFIG_FILE = "one_lm_quad_mode_bios_knob.cfg"
    QUAD_EXPECTED_VALUE = "0xe"
    step_data_dict = {1: {'step_details': 'To verify SUT has 1DPC or 2DPC memory configuration and '
                                          'To Load default bios settings and quad mode bios knobs',
                          'expected_results': 'SUT has 1DPC or 2DPC memory configuration and '
                                              'Default Bios and Quad mode bios setting done.'},
                      2: {'step_details': 'To Check Quad mode enabled or not by Python sv commands',
                          'expected_results': 'Quad mode enabled.'},
                      3: {'step_details': 'Install MLC tool and Run MLC Tool for 1 hour',
                          'expected_results': 'SUT did not hang after running MLC tool for 1 hour'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiMemoryFlatQuadMlcLinux object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        # calling base class init
        super(PiMemoryFlatQuadMlcLinux, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._install_collateral = InstallCollateral(test_log, self.os, cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._silicon_family = self._common_content_lib.get_platform_family()

    def prepare(self):
        # type: () -> None
        """
        1. Verify 1DPC or 2DPC memory configuration, Load default bios and Set the bios knobs.
        2. Reboot the SUT to apply the new bios settings.

        :return: None
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._memory_provider.verify_1dpc_or_2dpc_memory_configuration()
        super(PiMemoryFlatQuadMlcLinux, self).prepare()

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Check Quad mode information.
        2. Install MLC and run the MLC tool for 1 Hour.

        :return: True, if the test case is successful.
        :raise: TestFail
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        self.initialize_sv_objects()
        self.initialize_sdp_objects()
        self.SDP.itp.unlock()

        sockets_count = self.SV.get_socket_count()
        self._log.info("Socket count : {}".format(sockets_count))

        for each_socket in range(0, sockets_count):
            value = self.SV.get_by_path(self.SV.UNCORE, PlatformConfiguration.MEMORY_SNC_CONFIG[self._silicon_family],
                                        socket_index=each_socket)
            self._log.info("Socket {} value is :{}".format(each_socket, value))

            if self.QUAD_EXPECTED_VALUE not in hex(value):
                raise content_exceptions.TestFail("Quad mode value: {} not matched with expected value : {} for "
                                                  "socket{}".format(value, self.QUAD_EXPECTED_VALUE, each_socket))
            self._log.error("Quad mode value: {} matched with expected value : {} for socket{}".
                            format(value, self.QUAD_EXPECTED_VALUE, each_socket))

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        mlc_installed_path = self._install_collateral.install_mlc()
        self._install_collateral.screen_package_installation()
        self._stress_provider.execute_async_stress_tool(self.MLC_COMMAND, MLCToolConstants.MLC_TOOL_NAME,
                                                        mlc_installed_path)
        mlc_execute_time = time.time() + self.EXECUTE_TIME
        while time.time() < mlc_execute_time:
            time.sleep(TimeConstants.ONE_MIN_IN_SEC)
            if not (self.os.is_alive() and
                    self._stress_provider.check_app_running(MLCToolConstants.MLC_TOOL_NAME, self.MLC_COMMAND)):
                raise content_exceptions.TestFail("System is not pinging during MLC stress")
            self._log.info("SUT is in OS and MLC tool is running ...")

        self._stress_provider.kill_stress_tool(MLCToolConstants.MLC_TOOL_NAME, self.MLC_COMMAND)

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._stress_provider.kill_stress_tool(MLCToolConstants.MLC_TOOL_NAME, self.MLC_COMMAND)
        super(PiMemoryFlatQuadMlcLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiMemoryFlatQuadMlcLinux.main() else Framework.TEST_RESULT_FAIL)
