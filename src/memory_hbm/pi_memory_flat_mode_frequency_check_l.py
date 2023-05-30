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


class PiMemoryFlatModeDdrFrequencyCheck(MemoryHbmCommon):
    """
    HP QC ID:H109185, Pheonix ID:16014741001 -PI_Memory_Flat_Mode_Frequency_Check_L

    Description: To change the memory frequency knob value, and check whether the change works both in BIOS and
    OS level.
    """

    TEST_CASE_ID = ["16014741249", "PI_Memory_Flat_Mode_Frequency_Check_L"]
    REG_EX = r'0x[0-9A-F]+'
    BIOS_CONFIG_FILE = "one_lm_bios_knob.cfg"
    MEMORY_FREQUENCY_KNOB = "DdrFreqLimit"

    step_data_dict = {1: {'step_details': 'Get the memory frequency list from XML file based on processor',
                          'expected_results': 'Got the memory frequency list from XML'},
                      2: {'step_details': 'Clear OS logs and Set the bios knobs, Restart the system, Boot to OS',
                          'expected_results': 'Cleared os logs and bios settings is done.Successfully boot to os'
                                              'and verified the bios knobs'},
                      3: {'step_details': 'Get the memory frequency list to be set',
                          'expected_results': 'Got the memory frequency list values to be set'},
                      4: {'step_details': 'Get the hexadecimal value of memory frequency to be set. Set the value,'
                                          ' save and ac cycle',
                          'expected_results': 'Got the hexadecimal value, Successfully set the memory frequency and'
                                              ' restarted the system'},
                      5: {'step_details': 'Verify the memory frequency changes in bios level',
                          'expected_results': 'Memory frequency is set properly'},
                      6: {'step_details': 'Verify the memory frequency change in OS level',
                          'expected_results': 'Successfully set the memory frequency and reflecting in OS level'}}

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
        super(PiMemoryFlatModeDdrFrequencyCheck, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._itp_xmlcli = ItpXmlCli(test_log, cfg_opts)
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._memory_provider.verify_1dpc_or_2dpc_memory_configuration()
        # Get the list of memory frequency to be tested based on platform
        self.frequency_list = self._common_content_configuration.get_supported_ddr_frequencies(
            self._common_content_lib. get_platform_family())
        self._log.info("List of supported frequencies for the processor {}\n{}".
                       format(self._common_content_lib.get_platform_family(), self.frequency_list))

        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._csp = None
        self.platform_config_read = None
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def prepare(self):
        # type: () -> None
        """
        1. To clear os log.
        2. Set the bios knobs to its default mode
        3. Power cycle the SUT to apply the new bios settings.

        :return: None
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        super(PiMemoryFlatModeDdrFrequencyCheck, self).prepare()

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Setting memory frequency as per the frequency list based on platform
        2. Check both in BIOS and OS level whether the change works

        :return: True, if the test case is successful.
        """

        list_of_hex_value_of_frequency = []

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        new_locator_size_dict = self._memory_provider.get_dict_off_loc_size()

        locator_list = self._memory_provider.get_list_off_locators(hbm=False)
        self._log.info("Locators list : {}".format(locator_list))
        channel_info_dict = self._memory_provider.get_populated_channel_configuration(
            new_locator_size_dict, locator_list)

        self._log.info("Channel information : \n {}".format(channel_info_dict))

        # Checking for 1 DIMM Per Channel or not, if 1 DPC then 4800 MHz will support else 4800 MHz will not support
        # for EGS.
        for each_cpu, each_channel in channel_info_dict.items():
            for each_value in each_channel:
                if each_channel[each_value] > 1:
                    if FrequencyConstants.FREQUENCY_4800 in self.frequency_list:
                        self.frequency_list.remove(FrequencyConstants.FREQUENCY_4800)  # 4800 MHz will support for 1
                        # DPC in EGS.
        self._log.info("Frequencies to be tested : {}".format(self.frequency_list))

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._csp = ProviderFactory.create(self._csp_cfg, self._log)  # type: SiliconRegProvider
        self.platform_config_read = PlatformConfigReader(self._itp_xmlcli.get_platform_config_file_path(),
                                                         test_log=self._log)
        time.sleep(TimeConstants.ONE_MIN_IN_SEC)

        for index in range(0, len(self.frequency_list)):
            # Step logger start for Step 4
            self._test_content_logger.start_step_logger(4)

            # Get the hexadecimal value of frequency text
            list_of_hex_value_of_frequency.append(
                self.platform_config_read.get_hexadecimal_value(self.frequency_list[index]))
            self._log.info("Hexadecimal value of {} is {}".format(self.frequency_list[index],
                                                                  list_of_hex_value_of_frequency[index]))

            # Set the memory frequency
            self.bios_util.set_single_bios_knob(self.MEMORY_FREQUENCY_KNOB, list_of_hex_value_of_frequency[index])

            # To reflect the changes
            self.perform_graceful_g3()

            # Step logger end for Step 4
            self._test_content_logger.end_step_logger(4, return_val=True)

            # Step logger start for Step 5
            self._test_content_logger.start_step_logger(5)

            # Get the current memory frequency from Platform config
            ret_value = self.bios_util.get_bios_knob_current_value(self.MEMORY_FREQUENCY_KNOB)

            current_memory_frequency = re.findall(self.REG_EX, ret_value)[0]  # To get memory frequency BIOS knob value
            current_memory_frequency = int(current_memory_frequency, 16)  # To convert to integer

            # Verification of memory frequency in bios level
            if current_memory_frequency == int(list_of_hex_value_of_frequency[index], 16):
                self._log.info("Success: Memory frequency is matching in bios level..")
            else:
                raise content_exceptions.TestFail("In Bios level, current Memory frequency is not matching with the "
                                                  "set frequency.. Exiting.")

            # Step logger end for Step 5
            self._test_content_logger.end_step_logger(5, return_val=True)

            # Step logger start for Step 6
            self._test_content_logger.start_step_logger(6)

            # Get the list of configured memory speed of installed dimm
            configured_memory_speed_dict = self._memory_provider.get_configured_memory_speed_of_installed_dimm()
            ddr_dict, hbm_dict = self.get_ddr_hbm_hardware_component_information(configured_memory_speed_dict)
            ddr_configured_memory_speed_list = list(ddr_dict.values())
            hbm_memory_speed_list = list(hbm_dict.values())

            # Verification of memory frequency in OS level for DDR
            for freq in range(0, len(ddr_configured_memory_speed_list)):
                if self.frequency_list[index] <= ddr_configured_memory_speed_list[freq]:
                    self._log.info("Success: Memory frequency is set properly. Changes is reflecting in OS level")
                else:
                    self._log.info("Change in memory frequency is not reflecting in OS level")
                    raise content_exceptions.TestFail("Memory frequency is not matching in OS level.. Exiting..")

            # Verification of memory frequency in OS level for HBM
            for freq in range(0, len(hbm_memory_speed_list)):
                if (FrequencyConstants.FREQUENCY_2800 or FrequencyConstants.FREQUENCY_3200) \
                        not in hbm_memory_speed_list[freq]:
                    self._log.info("HBM Memory frequency is not matching in OS level with 2800 or 3200 MHz")
                    raise content_exceptions.TestFail("HBM Memory frequency is not matching in OS level.. Exiting..")
                else:
                    self._log.info("Success: HBM Memory frequency is : {}".format(hbm_memory_speed_list[freq]))
            # Step logger end for Step 6
            self._test_content_logger.end_step_logger(6, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiMemoryFlatModeDdrFrequencyCheck, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiMemoryFlatModeDdrFrequencyCheck.main() else Framework.TEST_RESULT_FAIL)
