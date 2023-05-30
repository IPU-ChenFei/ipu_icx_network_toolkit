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
import ipccli

from dtaf_core.lib.dtaf_constants import Framework
from src.hsio.upi.hsio_upi_common import HsioUpiCommon
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib.platform_config import PlatformConfiguration
from src.provider.memory_provider import MemoryProvider
from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon
from src.multisocket.lib.multisocket_common import MultiSocketCommon
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.dtaf_content_constants import TimeConstants, StressAppTestConstants, RootDirectoriesConstants, \
    MLCToolConstants


class MultiSocketDefaultUPISpeedMLCStress(HsioUpiCommon):
    """
    phoenix ID: 16014283957 - Multisocket_default_upi_speed_MLC_Stress_W

    This test Stress test with Mixed UPI speeds on Linux.

    """
    TEST_CASE_ID = ["16014283957", "Multisocket_default_upi_speed_MLC_Stress_W"]

    step_data_dict = {1: {'step_details': 'unlock itp and verify UPI details',
                          'expected_results': 'successfully unlocked itp and verified UPI details'},
                      2: {'step_details': 'run mlc stress ',
                          'expected_results': 'mlc stress ran successfully...'}
                      }
    MLC_COMMAND = "mlc.exe"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new MultiSocketDefaultUPISpeedMLCStress object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(MultiSocketDefaultUPISpeedMLCStress, self).__init__(
            test_log, arguments, cfg_opts)
        self._memory_provider = MemoryProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self.os)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._io_pm_obj = IoPmCommon(test_log, arguments, cfg_opts, config=None)
        self.initialize_sv_objects()
        self.initialize_sdp_objects()
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self.mlc_tool_path = self._install_collateral.install_new_mlc_w()
        self._multisock_obj = MultiSocketCommon(test_log, arguments, cfg_opts)

    def execute(self):
        """
        This method is used to execute MultiSocketDefaultUPISpeedMLCStress

        :return: True if successful
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self._multisock_obj.check_topology_speed_lanes(self.SDP)
        self._test_content_logger.end_step_logger(1, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(2)
        self.execute_mlc_test()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._multisock_obj.check_topology_speed_lanes(self.SDP)
        return True

    def execute_mlc_test(self):
        """
        Function to execute the MLC and verify SUT state.

        """
        num_iter = self._common_content_configuration.get_mlc_exec_iterations()
        for i in range(1, num_iter+1):
            self._log.info("Starting MLC tool iteration no: {}".format(i))
            result = self._common_content_lib.execute_sut_cmd(self.MLC_COMMAND, self.MLC_COMMAND, self._command_timeout,
                                                              cmd_path=self.mlc_tool_path)
            self._log.debug("stdout of mlc.exe \n: {}".format(result))
            self._log.info("Successfully completed iteration {} of MLC".format(i))


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MultiSocketDefaultUPISpeedMLCStress.main() else Framework.TEST_RESULT_FAIL)
