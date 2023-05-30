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
import os

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib import content_exceptions
from src.lib.bios_util import PlatformConfigReader, ItpXmlCli
from src.lib.test_content_logger import TestContentLogger
from src.memory_hbm.memory_hbm_common import MemoryHbmCommon
from src.lib.dtaf_content_constants import FrequencyConstants
from src.lib.dtaf_content_constants import TimeConstants


class PiMemoryHBMModeDdrFrequencyCheck(MemoryHbmCommon):
    """
    Pheonix ID:16014743059 -PI_Memory_HBM_Mode_Frequency_Check_L

    Description: To change the memory frequency knob value, and check whether the change works both in BIOS and
    OS level.
    """

    TEST_CASE_ID = ["16014743059", "PI_Memory_HBM_Mode_Frequency_Check_L"]
    BIOS_CONFIG_FILE = "one_lm_bios_knob.cfg"

    step_data_dict = {1: {'step_details': 'Set the Bios knob - Go to EDKII menu -> Socket Configuration -> '
                                          'Memory Configuration -> Memory Map -> 1LM/HBM mode',
                          'expected_results': 'Bios knob has been set.'},
                      2: {'step_details': 'Verify the HBM memory frequency in OS level',
                          'expected_results': 'Successfully verified the HBM memory frequency and '
                                              'reflecting in OS level'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiMemoryFlatModeDdrFrequencyCheck object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        bios_config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)

        # calling base class init
        super(PiMemoryHBMModeDdrFrequencyCheck, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        1. To clear os log.
        2. Set the bios knobs to its default mode
        3. Power cycle the SUT to apply the new bios settings.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        super(PiMemoryHBMModeDdrFrequencyCheck, self).prepare()

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Setting memory frequency as per the frequency list based on platform
        2. Check both in BIOS and OS level whether the change works

        :return: True, if the test case is successful.
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # Get the list of configured memory speed of installed dimm
        configured_memory_speed_dict = self._memory_provider.get_configured_memory_speed_of_installed_dimm()
        ddr_dict, hbm_dict = self.get_ddr_hbm_hardware_component_information(configured_memory_speed_dict)

        hbm_memory_speed_list = list(hbm_dict.values())

        # Verification of memory frequency in OS level for HBM
        for freq in range(0, len(hbm_memory_speed_list)):
            if (FrequencyConstants.FREQUENCY_2800 or FrequencyConstants.FREQUENCY_3200) \
                    not in hbm_memory_speed_list[freq]:
                self._log.info("HBM Memory frequency is not matching in OS level with 2800 or 3200 MHz")
                raise content_exceptions.TestFail("HBM Memory frequency is not matching in OS level.. Exiting..")
            else:
                self._log.info("Success: HBM Memory frequency is : {}".format(hbm_memory_speed_list[freq]))
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiMemoryHBMModeDdrFrequencyCheck, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiMemoryHBMModeDdrFrequencyCheck.main() else Framework.TEST_RESULT_FAIL)
