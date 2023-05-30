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
from pathlib import Path
from dtaf_core.lib.dtaf_constants import Framework
from src.hsio.upi.hsio_upi_common import HsioUpiCommon
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions
from src.lib.platform_config import PlatformConfiguration
from src.provider.memory_provider import MemoryProvider
from src.memory.tests.memory_ddr.stress_app_test_stress import StressAppTestStress


class UpiStressAppTestUpiMaxLinkSpeed(HsioUpiCommon):
    """
    Phoenix 16014692076, upi_stressapptest_UPI_max_linkspeed

    stressapp test on Linux
    """
    TEST_CASE_ID = ["16014692076", "upi_stressapptest_UPI_max_linkspeed"]

    step_data_dict = {1: {'step_details': 'verify 1 DPC memory config',
                          'expected_results': 'verified 1 DPC memory config successfuly'},
                      2: {'step_details': 'Print UPI details',
                          'expected_results': 'Printed UPI details successfully...'},
                      3: {'step_details': 'run the stressapptest ',
                          'expected_results': 'stress applied successfully ...'},
                      4: {'step_details': 'Print UPI details',
                          'expected_results': 'Printed UPI details successfully...'},
                      5: {'step_details': 'Check MCE Error logs for Errors ',
                          'expected_results': 'No errors should be reported ...'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance UpiStressAppTestUpiMaxLinkSpeed

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        :raises: None
        """

        # calling base class init
        super(UpiStressAppTestUpiMaxLinkSpeed, self).__init__(test_log, arguments, cfg_opts)
        self._memory_provider = MemoryProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self.os)
        self._stress_test = StressAppTestStress(test_log, arguments, cfg_opts)
        self._install_collateral.install_stress_test_app()
        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._silicon_family = self._common_content_lib.get_platform_family()
        self.initialize_sv_objects()
        self.initialize_sdp_objects()

    def prepare(self):
        # type: () -> None
        """
        To clear OS logs and load default bios settings.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        dict_config_channel_population_for_1dpc = self._memory_provider.get_1_dpc_channel_configuration()
        dict_config_channel_population_for_1dps = self._memory_provider.get_1_dps_channel_configuration()
        dict_config_channel_population_for_2dpc = self._memory_provider.get_2_dpc_channel_configuration()
        # Verification
        dict_config_match_1dpc = self._memory_provider.verify_channel_population(dict_config_channel_population_for_1dpc)
        dict_config_match_2dpc = self._memory_provider.verify_channel_population(dict_config_channel_population_for_2dpc)
        dict_config_match_1dps = self._memory_provider.verify_channel_population(dict_config_channel_population_for_1dps)

        if not (dict_config_match_1dpc or dict_config_match_2dpc or dict_config_match_1dps):
            raise content_exceptions.TestFail("Configuration not set correctly on this platform to support this test "
                                              "case.. please check the configuration and try again..")

        self._test_content_logger.end_step_logger(1, return_val=True)

    def print_verify_upi_details(self):
        """

        """
        self.print_upi_topology()
        self.print_upi_link_speed()
        self.print_link()
        pysv_output = self.SV.get_by_path(
            self.SV.UNCORE, PlatformConfiguration.UPI_KTIREUT_PH_CSS[self._silicon_family])
        self._log.debug("link lane : {}".format(pysv_output))
        # verification
        self.verify_upi_topology()
        self.verify_max_link_speed_set()
        self.lanes_operational_check()
        if not self.verify_no_upi_errors_indicated():
            raise content_exceptions.TestFail("UPI errors detected")

    def execute(self):
        """
        1. print and verify upi details
        2. run stressapptest
        3. log mce errors

        :return: True, if the test case is successful.
        """
        return_value = []

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        self.print_verify_upi_details()
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        self._stress_test.execute_installer_stressapp_test_linux()

        load_avg_value = self._stress_test.get_load_average()
        max_load_avg = self._stress_test.get_max_load_average(load_avg_value)
        self._log.info("Correct load average value {}".format(max_load_avg))
        if float(max_load_avg) >= self._stress_test.CMP_LOAD_AVERAGE_AFTER_STRESSAPP:
            self._log.info("Correct load average value...")
        else:
            log_error = "Incorrect load average value"
            self._log.error(log_error)
            raise RuntimeError(log_error)
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID[0], sut_log_files_path=self._stress_test.LINUX_USR_ROOT_PATH,
            extension=".log")

        return_value.append(self._stress_test.log_parsing_stress_app_test(log_file_path=log_path_to_parse))

        self._test_content_logger.end_step_logger(3, return_val=True)
        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(4)
        self.print_verify_upi_details()
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Step logger start for Step 6
        self._test_content_logger.start_step_logger(5)

        pysv_output = self.SV.get_by_path(
            self.SV.UNCORE, PlatformConfiguration.MCE_EVENTS_CHECK_CONFIG[self._silicon_family])
        if str(pysv_output) != "0x0":
            self._log.error("Mce logging check output : {}".format(pysv_output))
            raise content_exceptions.TestFail("Mce error check returned non zero value")

        self._test_content_logger.end_step_logger(5, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UpiStressAppTestUpiMaxLinkSpeed.main() else Framework.TEST_RESULT_FAIL)
