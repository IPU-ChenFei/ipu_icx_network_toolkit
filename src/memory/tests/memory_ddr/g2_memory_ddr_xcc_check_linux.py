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
import string
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions, dtaf_content_constants
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_ddr.ddr_common import DDRCommon


class G2MemoryDDRXccCheck(DDRCommon):
    """
    HP QC ID: 80039
    This case is used to change the capacity of the system memory in the Simics script, and check whether
    the change works.
    """

    TEST_CASE_ID = "H80039"
    _DDR_SNC2_BIOS_CONFIG_FILE = "g2_memory_bios_knobs_ddr_xcc_snc2_check.cfg"
    _DDR_SNC4_BIOS_CONFIG_FILE = "g2_memory_bios_knobs_ddr_xcc_snc4_check.cfg"
    _DDR_HEMI_BIOS_CONFIG_FILE = "g2_memory_bios_knobs_ddr_xcc_hemi_check.cfg"
    _DDR_QUAD_BIOS_CONFIG_FILE = "g2_memory_bios_knobs_ddr_xcc_quad_check.cfg"

    step_data_dict = {1: {'step_details': 'Clear OS logs, load default bios knobs, set new bios knobs, '
                                          'save and reboot',
                          'expected_results': 'Clear ALL the system Os logs, default bios knob setting, '
                                              'new bios knobs are set and verified.'},
                      2: {'step_details': 'Boot to Linux on system, check the node information.',
                          'expected_results': '1. Make sure number of numa node = socket number * 2 and Make sure '
                                              'memory total is equal the total amount of RAM present in the system;'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new G2MemoryDDRXccCheck object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(G2MemoryDDRXccCheck, self).__init__(test_log, arguments, cfg_opts)

        self.enable_snc2_bios_config_file_path = self.get_bios_config_file_path(self._DDR_SNC2_BIOS_CONFIG_FILE)
        self.enable_snc4_bios_config_file_path = self.get_bios_config_file_path(self._DDR_SNC4_BIOS_CONFIG_FILE)
        self.enable_hemi_bios_config_file_path = self.get_bios_config_file_path(self._DDR_HEMI_BIOS_CONFIG_FILE)
        self.enable_quad_bios_config_file_path = self.get_bios_config_file_path(self._DDR_QUAD_BIOS_CONFIG_FILE)

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        1. Clear system event logs and application event logs
        2. Checking pre - condition of the test case.
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self._common_content_lib.clear_os_log()  # TO clear Os logs

        self._test_content_logger.end_step_logger(1, return_val=True)

        # Configuration from dtaf content constants
        dict_config_channel_population = self._memory_provider.get_channel_configuration_list()

        # Verification between platform configuration and golden configuration info.
        dict_config_match = [self._memory_provider.verify_channel_population(dict_config_channel_population[config])
                             for config in range(len(dict_config_channel_population))]

        if not any(dict_config_match):
            raise content_exceptions.TestFail("Configuration not set correctly on this platform to support this test "
                                              "case.. please check the configuration and try again..")

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Check node information.
        2. Check serial log for clustering key pattern.
        3. Set the bios knobs to its default mode.
        4. Set the bios knobs as per the test case.
        5. Reboot the SUT to apply the new bios settings.
        6. Verify the bios knobs that are set.

        :return: True, if the test case is successful.
        :raise: TestFail
        """
        return_value = [self.snc_check(self.enable_snc2_bios_config_file_path,
                                       dtaf_content_constants.SncConstants.SNC2_CLUSTER),
                        self.snc_check(self.enable_snc4_bios_config_file_path,
                                       dtaf_content_constants.SncConstants.SNC4_CLUSTER),
                        self.uma_based_clustering_check(self.enable_hemi_bios_config_file_path,
                                                        dtaf_content_constants.UmaConstants.UMA2_CLUSTER)]

        # Once I get a sut which supports quad - 4 cluster, will uncomment this line.
        # self.uma_based_clustering_check(self.enable_quad_bios_config_file_path,
        # dtaf_content_constants.UmaConstants.UMA4_CLUSTER)

        return all(return_value)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(G2MemoryDDRXccCheck, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if G2MemoryDDRXccCheck.main() else Framework.TEST_RESULT_FAIL)
