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
import random
import re
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.bios_util import BootOptions
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_ddr.ddr_common import DDRCommon
from src.lib.bios_util import ItpXmlCli


class PiWarmResetMemoryRetention(DDRCommon):
    """
    HP QC ID: 82182
    To make sure the memory retention post warm reset of the system.
    """

    _bios_config_file = "pi_warm_reset_memory_retention_linux_uefi_bios_knob.cfg"
    TEST_CASE_ID = "H82182"
    DATA_TO_UPDATE_LOCATION = ['AA', '55', 'AA', '55', 'AA', '55']

    step_data_dict = {1: {'step_details': 'Load default bios knobs, set and verify bios knobs',
                          'expected_results': 'Default, new settings and verification of bios knobs are '
                                              'done successfully.'},
                      2: {'step_details': 'Now boot into UEFi run the command memmap',
                          'expected_results': 'System has been booted to UEFI shell and command ran successfully.'},
                      3: {'step_details': 'From the previous step look for an available memory address '
                                          'and run the following command',
                          'expected_results': 'This will give the details about that memory.'},
                      4: {'step_details': 'Write to some of the valid memory addresses obtained in the previous step.',
                          'expected_results': 'Successfully written data on available valid memory address.'},
                      5: {'step_details': 'Perform warm reset from UEFI shell, reset -w and after reset is completed '
                                          'verify the same memory address and check that memory is retained '
                                          'and run the following command',
                          'expected_results': 'After reset it should retain the same value.'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiWarmResetMemoryRetention object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiWarmResetMemoryRetention, self).__init__(test_log, arguments, cfg_opts, self._bios_config_file)

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()
        self._cfg = cfg_opts

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Reboot the SUT to apply the new bios settings.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        super(PiWarmResetMemoryRetention, self).prepare()

        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Check memory information.

        :return: True, if the test case is successful.
        :raise: TestFail
        """
        return_value = True

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        self._itp_xmlcli = ItpXmlCli(self._log, self._cfg)
        platform_xml_file = self._itp_xmlcli.get_platform_config_file_path()
        self._log.info("The platform config file '{}' generated successfully...".format(platform_xml_file))

        current_boot_order_string = self._itp_xmlcli.get_current_boot_order_string()

        self._itp_xmlcli.set_default_boot(BootOptions.UEFI)

        self._uefi_util_obj.graceful_sut_ac_power_on()

        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)

        # To ignore the letter scrap from uefi while executing any command for the first time.
        self._uefi_obj.execute('\n')

        memory_map_dump = self.get_memmap_info()
        memory_map_dump = ''.join(map(str, memory_map_dump)).split("\r")

        # To get list of available addresses
        flattened_list_addresses = self.get_available_addresses_list(memory_map_dump)

        # To get start available addresses
        avail_start_addresses = self.get_avail_start_addresses(flattened_list_addresses)

        # Step Logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        # Pick one address from available addresses
        pick_one_start_address_in_random = str(avail_start_addresses[-1])

        self._log.info("We have randomly picked '{}' address for manipulation.."
                       .format(pick_one_start_address_in_random))

        dmem_address_output = self.get_avail_start_address_mem_locations(pick_one_start_address_in_random)

        dmem_address_output = ''.join(map(str, dmem_address_output)).split("\r")

        # Get the last 8 digit hex value of the memory location
        inner_mem_location_last_eight_hex = ''.join(map(str, random.choices(dmem_address_output))).split(":")[0].strip()

        # Make a memory location to write the data on
        pick_one_dmem_address_in_random = str(pick_one_start_address_in_random)[:8] + inner_mem_location_last_eight_hex

        self._log.info("Now we have randomly picked a memory location - '{}' which we change data on.."
                       .format(pick_one_dmem_address_in_random))

        # Step Logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        dict_data_location = self.get_dict_off_loc_data(pick_one_dmem_address_in_random, self.DATA_TO_UPDATE_LOCATION)

        # Write the data into the memory location
        self.update_mem_location_with_data(dict_data_location)

        # Pre verification of data.
        self.verify_written_memory_location_data(pick_one_start_address_in_random, inner_mem_location_last_eight_hex,
                                                 self.DATA_TO_UPDATE_LOCATION)

        # Step Logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        self._log.info("Warm reset has been issued from UEFI... Waiting to boot into UEFI Internal Shell ..")

        #  Warm reboot
        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response('reset -w')

        # Wait time to enter in to UEFI shell
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)

        # To ignore the letter scrap from uefi while executing any command for the first time.
        self._uefi_obj.execute('\n')

        self._log.info("Verification starts after warm reset of the system..")

        # Post verification of data
        self.verify_written_memory_location_data(pick_one_start_address_in_random, inner_mem_location_last_eight_hex,
                                                 self.DATA_TO_UPDATE_LOCATION)

        # Step Logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=True)

        # To change boot order to OS.
        self._itp_xmlcli.set_boot_order(current_boot_order_string)

        self._log.info("System has been rebooted..")

        self._uefi_util_obj.graceful_sut_ac_power_on()

        self._os.wait_for_os(self.reboot_timeout)

        self._log.info("Waiting for system to come to OS...")

        if not self._os.is_alive():
            log_error = "System did not come to OS within {} seconds after a reboot from UEFI shell...".format(
                self._reboot_timeout)
            raise RuntimeError(log_error)

        self._log.info("System came to OS after a reboot from UEFI shell")

        return return_value

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiWarmResetMemoryRetention, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiWarmResetMemoryRetention.main()
             else Framework.TEST_RESULT_FAIL)
