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
import re
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.lib.content_base_test_case import ContentBaseTestCase

from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions


class RdtCMbmMeasurementsMemBWTrafficSNC(ContentBaseTestCase):
    """
    HPALM ID : H53800-PI_RDT_C_MBM_Measurements_MemBWTraffic_SNC

    This test case aims to install RDT if it not installed and
    verify Run MBA one two independent cores, verify if return BW are independent.
    """
    TEST_CASE_ID = ["H53800", "PI_RDT_C_MBM_Measurements_MemBWTraffic_SNC"]
    DISABLE_SNC_BIOS_CONFIG_FILE = "disable_snc_bios.cfg"
    ENABLE_SNC2_BIOS_CONFIG_FILE = "enable_snc2_bios.cfg"
    ENABLE_SNC4_BIOS_CONFIG_FILE = "enable_snc4_bios.cfg"
    PQOS_DATA_SNC_DISABLED = "pqos_mon_snc_disabled.csv"
    PQOS_DATA_SNC2_ENABLED = "pqos_mon_snc2_enabled.csv"
    PQOS_DATA_SNC4_ENABLED = "pqos_mon_snc4_enabled.csv"

    STEP_DATA_DICT = {
        1: {'step_details': 'Disable Intel HT Technology through the BIOS.',
            'expected_results': 'Disabled Intel HT Technology through the BIOS Successfully'},
        2: {'step_details': 'Verify RDT is installed in sut',
            'expected_results': 'Installation of RDT is verified successfully'},
        3: {'step_details': 'Restore default monitoring',
            'expected_results': 'Restore to default monitoring is successful'},
        4: {'step_details': 'Install mlc tool if not installed.',
            'expected_results': 'Successfully installed mlc'},
        5: {'step_details': 'Run mlc stress pinned to a core generating specified memory bandwidth',
            'expected_results': 'Mlc ran Successfully'},
        6: {'step_details': 'Enable SNC2 in BIOS',
            'expected_results': 'Enabled SNC2 Successfully'},
        7: {'step_details': 'Restore default monitoring',
            'expected_results': 'Restore to default monitoring is successful'},
        8: {'step_details': 'Run Mlc stress pinned to a core generating specified memory bandwidth',
            'expected_results': 'Mlc ran Successfully'},
        9: {'step_details': 'Enable SNC4 in BIOS',
            'expected_results': 'Enabled SNC4 Successfully'},
        10: {'step_details': 'Restore default monitoring',
             'expected_results': 'Restore to default monitoring is successful'},
        11: {'step_details': 'Run Mlc stress pinned to a core generating specified memory bandwidth',
             'expected_results': 'Mlc ran Successfully'},
        12: {'step_details': 'Check if Bandwidth is almost same no matter SNC Disabled or SNC2/SNC4 Enabled',
             'expected_results': 'Verified that the Bandwidth is almost same no matter SNC Disabled or SNC2/SNC4 Enabled'},
        13: {'step_details': 'Restore default monitoring',
             'expected_results': 'Restore to default monitoring is successful'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtCMbmMeasurementsMemBWTrafficSNC

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.DISABLE_SNC_BIOS_CONFIG_FILE)
        self.snc2_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.ENABLE_SNC2_BIOS_CONFIG_FILE)
        self.snc4_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.ENABLE_SNC4_BIOS_CONFIG_FILE)
        super(RdtCMbmMeasurementsMemBWTrafficSNC, self).__init__(test_log, arguments, cfg_opts,
                                                                 bios_config_file_path=self.bios_config_file)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self.socket0_core0 = 0
        self.socket0_core1 = 1
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def prepare(self):  # type: () -> None
        """Test preparation/setup and install the stress tool to sut"""
        self._test_content_logger.start_step_logger(1)
        super(RdtCMbmMeasurementsMemBWTrafficSNC, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. Disable Intel HT Technology through the BIOS.,
        4. Enabled SNC in BIOS
        5. Run mlc stress tool generating specified memory bandwidth
           with the following command: # ./mlc_internal -k1-1 --loaded_latency -d0 -T -B -b1g -R
        6. Use pqos to monitor local and remote memory bandwidth events, and
           then save the results to a CSV file using the following command:
           # pqos -u csv -o pqos_mon.csv
        7. Rerun the steps below but with SNC disabled. & compare the result
           of SNC enabled and disabled.
        8. Restore default allocation:  pqos -R

        :raise : content_exceptions.TestFail if failed
        :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(2)
        self._rdt.install_rdt()
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Restore rdt monitor to default mode
        self._test_content_logger.start_step_logger(3)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Install mlc tool if not installed.
        self._test_content_logger.start_step_logger(4)
        mlc_host_path = self._common_content_configuration.get_mlc_tool_path()
        mlc_tool_path = self._common_content_lib.copy_zip_file_to_linux_sut("mlc", mlc_host_path)
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Run mlc pinned to a core generating specified memory bandwidth
        # ./mlc_internal -k1-1 --loaded_latency -d0 -T -B -b1g -R
        self._test_content_logger.start_step_logger(5)
        self._log.info(" Run a mlc stress tool generating specified memory bandwidth")
        snc_disabled_bandwidth = float(self._rdt.run_mlc_stress(mlc_tool_path, self._rdt.MLC_STRESS_CMD))
        if not snc_disabled_bandwidth:
            raise content_exceptions.TestFail("Failed to run the mlc stress tool on SUT")
        self._log.info("Successfully started the mlc stress tool")
        self._log.info("Bandwidth when SNC is disabled is : {}".format(snc_disabled_bandwidth))
        self._test_content_logger.end_step_logger(5, return_val=True)

        # Enable SNC2 in BIOS
        self._test_content_logger.start_step_logger(6)
        self.bios_util.set_bios_knob(bios_config_file=self.snc2_bios_config_file)
        self.perform_graceful_g3()
        self.bios_util.verify_bios_knob(bios_config_file=self.snc2_bios_config_file)
        self._test_content_logger.end_step_logger(6, return_val=True)

        # Restore rdt monitor to default mode
        self._test_content_logger.start_step_logger(7)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(7, return_val=True)

        # Run mlc pinned to a core generating specified memory bandwidth
        # ./mlc_internal -k1-1 --loaded_latency -d0 -T -B -b1g -R
        self._test_content_logger.start_step_logger(8)
        self._log.info(" Run a mlc stress tool generating specified memory bandwidth")
        snc2_enabled_bandwidth = float(self._rdt.run_mlc_stress(mlc_tool_path, self._rdt.MLC_STRESS_CMD))
        if not snc2_enabled_bandwidth:
            raise content_exceptions.TestFail("Failed to run the mlc stress tool on SUT")
        self._log.info("Successfully started the mlc stress tool")
        self._log.info("Bandwidth when SNC2 is Enabled : {}".format(snc2_enabled_bandwidth))
        self._test_content_logger.end_step_logger(8, return_val=True)

        # Enable SNC4 in BIOS
        self._test_content_logger.start_step_logger(9)
        self.bios_util.set_bios_knob(bios_config_file=self.snc4_bios_config_file)
        self.perform_graceful_g3()
        self.bios_util.verify_bios_knob(bios_config_file=self.snc4_bios_config_file)
        self._test_content_logger.end_step_logger(9, return_val=True)

        # Restore rdt monitor to default mode
        self._test_content_logger.start_step_logger(10)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(10, return_val=True)

        # Run mlc pinned to a core generating specified memory bandwidth
        # ./mlc_internal -k1-1 --loaded_latency -d0 -T -B -b1g -R
        self._test_content_logger.start_step_logger(11)
        self._log.info(" Run a mlc stress tool generating specified memory bandwidth")
        snc4_enabled_bandwidth = float(self._rdt.run_mlc_stress(mlc_tool_path, self._rdt.MLC_STRESS_CMD))
        if not snc4_enabled_bandwidth:
            raise content_exceptions.TestFail("Failed to run the mlc stress tool on SUT")
        self._log.info("Successfully started the mlc stress tool")
        self._log.info("Bandwidth when SNC4 is Enabled is : {}".format(snc4_enabled_bandwidth))
        self._test_content_logger.end_step_logger(11, return_val=True)

        # check if core1_value_when_snc_is_disabled is same as core1_value_when_snc2_is_enabled or
        # core1_value_when_snc4_is_enabled
        self._test_content_logger.start_step_logger(12)
        if not (snc2_enabled_bandwidth - snc2_enabled_bandwidth * 0.1 <=
                snc_disabled_bandwidth <= snc2_enabled_bandwidth + snc2_enabled_bandwidth * 0.1):
            raise content_exceptions.TestFail("Bandwidth when snc is disabled is not almost same as the bandwidth when "
                                              "SNC2 is enabled")
        if not (snc4_enabled_bandwidth - snc4_enabled_bandwidth * 0.1 <=
                snc2_enabled_bandwidth <= snc4_enabled_bandwidth + snc4_enabled_bandwidth * 0.1):
            raise content_exceptions.TestFail("Bandwidth when snc2 is enabled is not almost same as the bandwidth when "
                                              "SNC4 is enabled")
        self._log.info("Bandwidth is almost same no matter the SNC is enabled or disabled")
        self._test_content_logger.end_step_logger(12, return_val=True)

        # Restore rdt monitor to default mode
        self._test_content_logger.start_step_logger(13)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(13, return_val=True)
        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        # kill pqos and membw processes in SUT
        if self._rdt.check_rdt_monitor_running_status(self._rdt.PQOS_STR):
            self.os.execute_async(self._rdt.KILL_CMD.format(self._rdt.PQOS_STR))
        super(RdtCMbmMeasurementsMemBWTrafficSNC, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if RdtCMbmMeasurementsMemBWTrafficSNC.main() else Framework.TEST_RESULT_FAIL)
