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

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions
from src.provider.memory_provider import MemoryProvider
from src.lib.smbios_configuration import SMBiosConfiguration


class MemoryDDR8Channels2DPCLinux(ContentBaseTestCase):
    """
    Configure the system with 8 channels 2 DPC DDR for each of the sockets.

    """

    TEST_CASE_ID = ["H80038", "PI_Memory_DDR5_8Ch_Config_L"]

    step_data_dict = {1: {'step_details': 'To verify dmidecode installed or not',
                          'expected_results': 'dmidecode tool installed'},
                      2: {'step_details': 'To verify DDR populated with 2DPC memory configuration',
                          'expected_results': 'DDR populated with 2 DPC memory configuration.'},
                      3: {'step_details': 'To check Locator and BankLocator from dmidecode -t 17 command',
                          'expected_results': 'Verified Locator and BankLocator from dmidecode -t 17 command output '
                                              'with the configuration'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):

        """
        Create an instance MemoryDDR8Channels2DPCLinux

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        :raises: None
        """

        super(MemoryDDR8Channels2DPCLinux, self).__init__(test_log, arguments, cfg_opts)
        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._memory_provider = MemoryProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self.os)
        self._smbios_config = SMBiosConfiguration(self._log, self.os)

    def prepare(self):
        # type: () -> None
        """
        1. To verify dmidecode install or not in SUT.
        2. To verify 2 DPC memory channel configuration.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._memory_provider.verify_dmidecode_installed_or_not()

        self._test_content_logger.end_step_logger(1, return_val=True)
        # Step Logger end for Step 1

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # Configuration from dtaf content constants
        dict_config_channel_population = self._memory_provider.get_2_dpc_channel_configuration()

        # Verification of channel population.
        channel_info_dict = self._memory_provider.verify_channel_population(dict_config_channel_population)

        if not channel_info_dict:
            raise content_exceptions.TestFail("Configuration not set correctly on this platform to support this test "
                                              "case.. please check the configuration and try again..")

        self._test_content_logger.end_step_logger(2, return_val=True)
        # Step Logger end for Step 2

    def execute(self):
        """
        Create an output file of the smbios information and verify them as per the test case procedures.

        :return: True, if the test case is successful.
        :raise: None.
        """
        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        dict_dmi_decode_from_tool = self._memory_provider.get_memory_slots_details()

        dict_dmi_decode_from_spec = self._smbios_config.get_smbios_table_dict()
        self._log.info("Template SMBIOS information.. \n {}".format(dict_dmi_decode_from_spec))
        num_dmi_type17 = 0
        dmi_comparison_results = True

        for key in dict_dmi_decode_from_tool.keys():
            if dict_dmi_decode_from_tool[key]['DMIType'] == 17:
                num_dmi_type17 = num_dmi_type17 + 1
                memory_device_num = 'MemoryDevice{}'.format(num_dmi_type17)

                self._log.info("{}".format(memory_device_num))

                self._log.info("OS reported Locator information - {} || Configuration file reported Locator "
                               "information  - {}"
                               .format(dict_dmi_decode_from_tool[key]['Locator'],
                                       dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Locator']))

                self._log.info("OS reported Bank Locator information - {} || Configuration file reported "
                               "Bank Locator information - {}"
                               .format(dict_dmi_decode_from_tool[key]['Bank Locator'],
                                       dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['BankLocator']))

                if dict_dmi_decode_from_tool[key]['Locator'] != \
                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Locator'] or \
                        dict_dmi_decode_from_tool[key]['Bank Locator'] != \
                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['BankLocator']:
                    self._log.error("DMI TYPE 17 on {} information are not correct!".format(memory_device_num))
                    dmi_comparison_results = False
                else:
                    self._log.info("DMI TYPE 17 on {} information has been verified "
                                   "successfully!".format(memory_device_num))

        # Step Logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=dmi_comparison_results)

        return dmi_comparison_results

    def cleanup(self, return_status):

        # type: (bool) -> None
        """DTAF cleanup"""

        super(MemoryDDR8Channels2DPCLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MemoryDDR8Channels2DPCLinux.main() else Framework.TEST_RESULT_FAIL)
