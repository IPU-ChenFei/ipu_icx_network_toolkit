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
from src.memory.tests.memory_ddr.ddr_common import DDRCommon
from src.lib import content_exceptions


class MemoryDDR8Channel(DDRCommon):
    """
    Configure this system with 2, 4, 6, and 8 channels DDR5 DIMM for each of the CPU sockets.

    """

    TEST_CASE_ID = ["H67504", "PI_Memory_DDR5_8Ch_Config_L"]

    def __init__(self, test_log, arguments, cfg_opts):

        """
        Create an instance MemoryDDR8Channel

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        :raises: None
        """

        super(MemoryDDR8Channel, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. To verify dmidecode install or not in SUT.
        2. To verify channel configuration.

        :return: None
        """

        self._memory_provider.verify_dmidecode_installed_or_not()

        # Configuration from dtaf content constants
        dict_config_channel_population = self._memory_provider.get_egs_channel_configuration()

        # Verification of channel population.
        dict_config_match = self._memory_provider.verify_channel_population(dict_config_channel_population)

        if not dict_config_match:
            raise content_exceptions.TestFail("Configuration not set correctly on this platform to support this test "
                                              "case.. please check the configuration and try again..")

    def execute(self):
        """
        Create an output file of the smbios information and verify them as per the test case procedures.

        :return: True, if the test case is successful.
        :raise: None.
        """
        dict_dmi_decode_from_tool = self._memory_provider.get_memory_slots_details()

        dict_dmi_decode_from_spec = self._smbios_config.get_smbios_table_dict()
        self._log.info("Template SMBIOS informaton.. \n {}".format(dict_dmi_decode_from_spec))
        num_dmi_type17 = 0
        dmi_comparision_results = True

        dict_dmi_decode_from_tool = self.update_ddr_from_dmidecode(dict_dmi_decode_from_tool)

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

                self._log.info("OS reported Memory Type information - {} || Configuration file reported Memory Type "
                               "information - {}"
                               .format(dict_dmi_decode_from_tool[key]['Type'],
                                       dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Type']))

                self._log.info("OS reported Memory Speed information - {} || Configuration file reported Memory Speed "
                               "information - {}"
                               .format(dict_dmi_decode_from_tool[key]['Speed'],
                                       dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Speed']))

                if dict_dmi_decode_from_tool[key]['Locator'] != \
                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Locator'] or \
                        dict_dmi_decode_from_tool[key]['Bank Locator'] != \
                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['BankLocator'] or \
                        (dict_dmi_decode_from_tool[key]['Type'] and dict_dmi_decode_from_tool[key]['Type'] !=
                         dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Type']) or (
                        dict_dmi_decode_from_tool[key]['Speed'] != 0 and
                        dict_dmi_decode_from_tool[key]['Speed'] != dict_dmi_decode_from_spec['MemoryDevices'][
                            memory_device_num]['Speed']):
                    self._log.error("DMI TYPE 17 on {} information are not correct!".format(memory_device_num))
                    dmi_comparision_results = False
                else:
                    self._log.info("DMI TYPE 17 on {} information has been verified "
                                   "successfully!".format(memory_device_num))

        return dmi_comparision_results

    def cleanup(self, return_status):

        # type: (bool) -> None
        """DTAF cleanup"""

        super(MemoryDDR8Channel, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MemoryDDR8Channel.main() else Framework.TEST_RESULT_FAIL)
