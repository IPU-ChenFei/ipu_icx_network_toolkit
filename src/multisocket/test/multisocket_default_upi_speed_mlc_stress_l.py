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
from src.multisocket.lib.multisocket_common import MultiSocketCommon
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib.platform_config import PlatformConfiguration
from src.provider.memory_provider import MemoryProvider
from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon


class MultiSocketDefaultUPISpeedMLCStress(HsioUpiCommon):
    """
    phoenix ID: 16014283917 - Multisocket_default_upi_speed_MLC_Stress_L

    This test Stress test with Mixed UPI speeds on Linux.

    """
    TEST_CASE_ID = ["16014283917", "Multisocket_default_upi_speed_MLC_Stress_L"]

    step_data_dict = {1: {'step_details': 'verify 1 DPC memory config',
                          'expected_results': 'verified 1 DPC memory config successfully'},
                      2: {'step_details': 'unlock itp',
                          'expected_results': 'successfully unlocked itp'},
                      3: {'step_details': 'verify UPI details',
                          'expected_results': 'verified UPI details successfully...'},
                      4: {'step_details': 'run mlc stress ',
                          'expected_results': 'mlc stress ran successfully...'}
                      }

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
        self._rdt = RdtUtils(test_log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._io_pm_obj = IoPmCommon(test_log, arguments, cfg_opts, config=None)
        self._multisock_obj = MultiSocketCommon(test_log, arguments, cfg_opts)
        self._silicon_family = self._common_content_lib.get_platform_family()
        self.initialize_sv_objects()
        self.initialize_sdp_objects()

    def prepare(self):
        # type: () -> None
        """
        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        dict_config_channel_population_for_1dpc = self._memory_provider.get_1_dpc_channel_configuration()
        dict_config_channel_population_for_1dps = self._memory_provider.get_1_dps_channel_configuration()
        dict_config_channel_population_for_2dpc = self._memory_provider.get_2_dpc_channel_configuration()
        # Verification
        dict_config_match_1dpc = self._memory_provider.verify_channel_population(
            dict_config_channel_population_for_1dpc)
        dict_config_match_2dpc = self._memory_provider.verify_channel_population(
            dict_config_channel_population_for_2dpc)
        dict_config_match_1dps = self._memory_provider.verify_channel_population(
            dict_config_channel_population_for_1dps)

        if not (dict_config_match_1dpc or dict_config_match_2dpc or dict_config_match_1dps):
            raise content_exceptions.TestFail("Configuration not set correctly on this platform to support this test "
                                              "case.. please check the configuration and try again..")

        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This method is used to execute MultiSocketDefaultUPISpeedMLCStress

        :return: True if successful
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        # check total Memory size before stress
        total_mem_before_stress = self._multisock_obj.get_mem_details()
        self._log.info("Total Memory before Stress : {}".format(total_mem_before_stress))

        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        self._multisock_obj.check_topology_speed_lanes(self.SDP)
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)
        mlc_tool_path = self._install_collateral.install_mlc_internal_linux()
        num_iter = self._common_content_configuration.get_mlc_exec_iterations()
        for iter in range(1, num_iter):
            self._log.info("executing mlc stress {} iteration".format(iter))
            self._rdt.run_mlc_stress(mlc_tool_path, self.MLC_STRESS_CMD)

        # Run sv.sockets.uncore.ubox.ncevents.mcerrloggingreg.show() and check logs
        self.SDP.start_log("mlc_topology.log")
        pysv_output = self.SV.get_by_path(
            self.SV.UNCORE, PlatformConfiguration.MCE_EVENTS_CHECK_CONFIG[self._silicon_family])
        if str(pysv_output) != "0x0":
            self._log.error("Mce logging check output : {}".format(pysv_output))
            raise content_exceptions.TestFail("Mce error check returned non zero value")
        self.SDP.stop_log()
        self._multisock_obj.print_topology_logs("mlc_topology.log")

        self._multisock_obj.check_topology_speed_lanes(self.SDP)
        total_mem_after_stress = self._multisock_obj.get_mem_details()
        self._log.info("Total Memory before Stress : {}".format(total_mem_after_stress))
        self._test_content_logger.end_step_logger(4, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MultiSocketDefaultUPISpeedMLCStress.main() else Framework.TEST_RESULT_FAIL)
