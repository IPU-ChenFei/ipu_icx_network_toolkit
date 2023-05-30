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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_ddr.ddr_common import DDRCommon
from src.lib import content_exceptions


class PIMemoryHighMemoryBoot(DDRCommon):
    """
    HP ALM ID: 81115 (Linux) and 81118 (Windows)

    This test case is to check whether high memory address is being reported in the OS.
    """

    _bios_config_file = "pi_memory_high_bios_knbos.cfg"
    TEST_CASE_ID = ["H81115/H81118 - PI_Memory_HighMeomryBoot"]

    step_data_dict = {1: {'step_details': 'Set and verify BIOS knobs',
                          'expected_results': 'BIOS setup options are updated with changes saved.'},
                      2: {'step_details': 'Clear OS logs, save and boot to Linux OS',
                          'expected_results': 'Cleared OS system logs and no errors while Booting post bios '
                                              'settings..'},
                      3: {'step_details': 'run command: cat /proc/iomem |grep -i RAM to check the highest memory..',
                          'expected_results': 'There were a print out there:'
                                              '8000000000000-800007fffffff : System RAM'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PIMemoryHighMemoryBoot object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        # calling base class init
        super(PIMemoryHighMemoryBoot, self).__init__(test_log, arguments, cfg_opts, self._bios_config_file)

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._common_content_lib.clear_all_os_error_logs()  # TO clear Os logs
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()

        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.

        self._bios_util.verify_bios_knob()

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        Function is responsible to check whether the OS is showing highest memory

        :return: True, if the test case is successful else false
        :raise: content_exceptions.TestFail
        """

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        if OperatingSystems.LINUX == self.os.os_type:
            starting_add_range = "8000000000000"
            ending_add_range = "fffffffffffff"
            ram_address = self._common_content_lib.execute_sut_cmd("cat /proc/iomem |grep -i RAM",
                                                                   "Get memory address of Ram", self._command_timeout)

            ram_address_list = ram_address.strip().split("\n")[-1].split(":")[0].strip().split("-")

            # /prox/iomem file shows you the current map of the system's memory for each physical device.
            # As we have enabled 51 bit addressing, at least one "System RAM" segment is expected to occupy this range.
            # Check for segment using this range. Ex: 8 0000 0000 0000 - 8 0007 7fff ffff

            self._log.debug("Current starting address range is '{}' with in the range of '{}'.".format(
                ram_address_list[0], starting_add_range))
            self._log.debug("Current ending address range is '{}' with in the range of '{}'.".format(
                ram_address_list[1], ending_add_range))

            if int(ram_address_list[0], 16) < int(starting_add_range, 16) or int(ram_address_list[1], 16) > \
                    int(ending_add_range, 16):
                raise content_exceptions.TestFail("The platform is not showing the high memory address.. "
                                                  "please check..")

        elif OperatingSystems.WINDOWS == self.os.os_type:

            dict_dmi_decode_from_tool = self._memory_provider.get_memory_slots_details()
            dict_dmi_decode_from_spec = self._smbios_config.get_smbios_table_dict()
            self._log.info("Template SMBIOS informaton.. \n {}".format(dict_dmi_decode_from_spec))

            num_dmi_type17 = 0
            memory_device_compare_res = True

            for key in dict_dmi_decode_from_tool.keys():
                num_dmi_type17 = num_dmi_type17 + 1
                memory_device_num = 'MemoryDevice{}'.format(num_dmi_type17)

                self._log.debug("{}".format(memory_device_num))

                self._log.debug("OS reported Locator information - {} || Configuration file reported Locator "
                               "information  - {}"
                               .format(dict_dmi_decode_from_tool[key]['Locator'],
                                       dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Locator']))

                self._log.debug("OS reported Locator information - {} || Configuration file reported Locator "
                                "information  - {}"
                                .format(dict_dmi_decode_from_tool[key]['Size'],
                                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Size']))

                if dict_dmi_decode_from_tool[key]['Size'] != \
                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Size'] or \
                         dict_dmi_decode_from_tool[key]['Locator'] != \
                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Locator']:
                    memory_device_compare_res = False

                    self._log.error("DMI TYPE 17 on {} information are not "
                                    "correct!".format(memory_device_num))
                else:
                    self._log.info("DMI TYPE 17 on {} information has been verified "
                                   "successfully!".format(memory_device_num))

            if not memory_device_compare_res:
                raise content_exceptions.TestFail("The platform is not showing the high memory address.. "
                                                  "please check..")

        self._log.info("Successfully verified the configuration of high memory boot.")

        #  Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PIMemoryHighMemoryBoot, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PIMemoryHighMemoryBoot.main() else Framework.TEST_RESULT_FAIL)
