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

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.lib.dmidecode_parser_lib import DmiDecodeParser
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.lib.common_content_lib import CommonContentLib


class CheckBadCoreDeallocationWithTrustedBoot(TxtBaseTest):
    """
    Glasgow ID : 59137
    Phoneix ID : 18014069446
    This Test case is to obtain CPU with bad core and verify ability to boot trusted environment.
    pre-requisites:
    1.Ensure that the system is in sync with the latest BKC.
    2.Ensure that you have a Linux ras_interopOS image or hard drive with tboot installed.
    3.Ensure that the platform has a TPM provisioned with an ANY policy installed
        and active
    """
    _BIOS_CONFIG_FILE = "../security_txt_bios_knobs_enable.cfg"
    _BIOS_CONFIG_FILE_BAD_CORE = "bad_core_enable.cfg"
    _TEST_CASE_ID = ["P18014069446-Bad Core Deallocation", "G59137-Bad Core Deallocation"]
    ROOT = "/root"
    CPU0 = "CPU0"
    step_data_dict = {1: {'step_details': 'enabling TXT BIOS Knobs and CoreDisableMask_0 to min and CoreDisableMask_1'
                                          'to max',
                          'expected_results': 'Verifying TXT BIOS Knobs'},
                      2: {'step_details': 'Get core and Uncore value', 'expected_results':
                          'Able to get the core and uncore value using ITP'},
                      3: {'step_details': 'Get Enabled Socket core value from os',
                          'expected_results': 'Successfully got Enabled socket core value from Os'},
                      4: {'step_details': 'Verify Enabled Socket for CPU0 is 1 ', 'expected_results':
                          'Enabled Socket core should be 1 for CPU0'},
                      5: {'step_details': 'Verify System Booting to Tboot',
                          'expected_results': 'SUT entered to Tboot'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of BadCoreDeallocationWithTrustedBoot

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.bios_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._BIOS_CONFIG_FILE)
        self.bad_core_bios_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._BIOS_CONFIG_FILE_BAD_CORE)
        combined_ini_file = CommonContentLib.get_combine_config([self.bios_config_path, self.bad_core_bios_config_path])
        super(CheckBadCoreDeallocationWithTrustedBoot, self).__init__(test_log, arguments, cfg_opts, combined_ini_file)
        self._dmidecode_parser = DmiDecodeParser(self._log, self._os)
        self._test_content_logger = TestContentLogger(test_log, self._TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        1. Get the Tboot index menu from grub menu and setting it has default boot.
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case according to Tboot
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        self._test_content_logger.start_step_logger(1)
        self.tboot_index = self.get_tboot_boot_position()  # Get the Tboot_index from grub menu entry
        self.set_default_boot_entry(self.tboot_index)  # Set Tboot as default boot
        self.enable_and_verify_bios_knob()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This function is used to check SUT did not boot in Untrusted environment

        1. Get socket uncore pch info from uncore pcu cr resolved core info for socket0 and socket1
        2. Get Enabled socket core count using dmidecode command.
        3. Verify if the Enabled socket core count is 1
        4. Verify if the system booted in Trusted environment if not booted verifying using expect_ltreset flag

        :return: True if Test case is passed else False if the Test case is failed.
        """
        self._test_content_logger.start_step_logger(2)
        socket_core_count_itp = self.get_core_uncore_value()
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._test_content_logger.start_step_logger(3)
        socket_core_count_os = self.get_enabled_socket_core_os()
        self._test_content_logger.end_step_logger(3, return_val=True)
        self._test_content_logger.start_step_logger(4)
        if not socket_core_count_itp.get(self.CPU0) == 1:
            raise content_exceptions.TestFail("Socket Core CPU0 is not 1 from ITP")
        if not socket_core_count_os.get(self.CPU0) == 1:
            raise content_exceptions.TestFail("Socket Core CPU0 is not 1 from OS")
        self._test_content_logger.end_step_logger(4, return_val=True)
        self.compare_enabled_socket_core(socket_core_count_itp, socket_core_count_os)
        self._test_content_logger.start_step_logger(5)
        self.verify_sut_booted_in_tboot_mode(self.tboot_index)  # verify if the system booted in Trusted mode.
        if not self.verify_trusted_boot():  # verify the sut boot with trusted env
            raise content_exceptions.TestFail("SUT did not boot to Trusted environment")
        self._log.info("SUT Booted to Trusted environment Successfully")
        self._test_content_logger.end_step_logger(5, return_val=True)

    def get_enabled_socket_core_os(self):
        """
        This function verifies if the socket zero is enable with one core and socket 1 is enabled with maximum core
        :raise: content_exceptions if Enabled Socket core from ITP and Socket core from OS does not match.
        :return:
        """
        dmi_cmd = "dmidecode > dmi.txt"
        dmi_name = 'DMIName'
        processor_information = 'Processor Information'
        socket_information = 'Socket Designation'
        core_enabled = 'Core Enabled'
        cpu_count_os = {}
        self._log.info("Executing Dmidecode to get Enabled socket core value from OS")
        self._common_content_lib.execute_sut_cmd(dmi_cmd, "get dmi dmidecode output", 10,  cmd_path=self.ROOT)
        self.log_dir = self._common_content_lib.get_log_file_dir()
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.log_dir, sut_log_files_path=self.ROOT, extension=".txt")
        # Check whether the dmi.txt exists in the folder has been done inside the "dmidecode_parser" function.
        dict_dmi_decode_from_tool = self._dmidecode_parser.dmidecode_parser(log_path_to_parse)
        for key in dict_dmi_decode_from_tool.keys():
            if dict_dmi_decode_from_tool[key][dmi_name] == processor_information:
                cpu_number = dict_dmi_decode_from_tool[key].get(socket_information)
                core_count = dict_dmi_decode_from_tool[key].get(core_enabled)
                self._log.info("socket {} has Core count for the {}".format(cpu_number, core_count))
                cpu_count_os[cpu_number] = int(core_count)
        if not cpu_count_os:
            raise content_exceptions.TestFail("Unable to get the Socket core Enabled information using dmidecode")
        self._log.info("Enabled Socket core count in Os {}".format(cpu_count_os))
        return cpu_count_os

    def compare_enabled_socket_core(self, cpu_count_itp, cpu_count_os):
        """
        This function compares the Socket core Enabled Count from the OS to ITP command.

        :param cpu_count_itp: Enabled Socket core from ITP
        :param cpu_count_os: Enabled Socket core from OS
        :raise: content_exceptions if Enabled Socket core from ITP and Socket core from OS does not match.
        """
        for socket_number in cpu_count_os.keys():
            cpu_count_individual_socket_itp = cpu_count_itp.get(socket_number)
            cpu_count_individual_socket_os = cpu_count_os.get(socket_number)
            self._log.info(type(cpu_count_individual_socket_itp))
            self._log.info(type(cpu_count_individual_socket_os))
            if not cpu_count_individual_socket_itp == cpu_count_individual_socket_os:
                raise content_exceptions.TestFail("Socket value {} is not matching for the OS {} and from ITP {}".format(
                    socket_number, cpu_count_individual_socket_os, cpu_count_individual_socket_itp))
            self._log.info("Socket value {} is matching for the OS {} and from ITP {}".format(socket_number,
                                                                                     cpu_count_individual_socket_os,
                                                                                     cpu_count_individual_socket_itp))
        self._log.info("Enabled Socket core is matching between OS and ITP")

    def cleanup(self, return_status):  # type: (bool) -> None
        """"""
        self._bios_util.load_bios_defaults()  # To set Bios knobs to default.
        self.perform_graceful_g3()
        super(CheckBadCoreDeallocationWithTrustedBoot, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CheckBadCoreDeallocationWithTrustedBoot.main()
             else Framework.TEST_RESULT_FAIL)
