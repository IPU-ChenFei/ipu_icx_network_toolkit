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

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_ddr.ddr_common import DDRCommon


class PiMemoryDdrDimmMaxmiumMemory(DDRCommon):
    """
    HP ID: 65920
    To ensure maximum supported range of memory capacity configurations from BIOS and operating system perspectives.

    """
    TEST_CASE_ID = "H65920"
    dram_memory_size_list = []

    step_data_dict = {1: {'step_details': 'Clear OS logs and load default bios knobs',
                          'expected_results': 'Clear all the system OS logs and default bios knob setting done.'},
                      2: {'step_details': 'Verify the memory displayed at POST is the amount of memory installed in '
                                          'the system.',
                          'expected_results': 'POST displays the amount of physical memory installed in system.'},
                      3: {'step_details': 'Verify the amount of memory reported by the operating system matches the '
                                          'amount of memory installed in the system.',
                          'expected_results': 'OS displays the amount of memory installed in system.'},
                      4: {'step_details': 'Install latest version of stressapptest and run memory stress for 10s.',
                          'expected_results': 'Post running stress app test, no error has been reported.'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiMemoryDdrDimmMaxmiumMemory object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiMemoryDdrDimmMaxmiumMemory, self).__init__(test_log, arguments, cfg_opts)

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self.platform_based_config_check = self._common_content_configuration.memory_supported_highest_capacity_dimm(
            self._product_family)

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Reboot the SUT to apply the new bios settings.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        dmi_cmd = "dmidecode -t 17 > dmi.txt"
        self._common_content_lib.execute_sut_cmd(dmi_cmd, "get dmi dmidecode -t 17 type output", self._command_timeout,
                                                 cmd_path=self.LINUX_USR_ROOT_PATH)

        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(test_case_id=self.TEST_CASE_ID,
                                                                            sut_log_files_path=self.LINUX_USR_ROOT_PATH,
                                                                            extension=".txt")

        # Check whether the dmi.txt exists in the folder has been done inside the "dmidecode_parser" function.
        dict_dmi_decode_from_tool = self._dmidecode_parser.dmidecode_parser(log_path_to_parse)

        dram_memory_size_list_with_gb = []

        for key in dict_dmi_decode_from_tool.keys():
            if dict_dmi_decode_from_tool[key]['Size'] != "No Module Installed":
                if dict_dmi_decode_from_tool[key]['Memory Technology'] == "DRAM":
                    dram_memory_size_list_with_gb.append(dict_dmi_decode_from_tool[key]['Volatile Size'])

                    self._log.info("The size of DRAM is {} located at {}".format(
                        dict_dmi_decode_from_tool[key]['Volatile Size'], dict_dmi_decode_from_tool[key]['Locator']))

        # Remove the GB and take only numeric value (size) of dram
        self.dram_memory_size_list = list(map(lambda sub: int(''.join([ele for ele in sub if ele.isnumeric()])),
                                              dram_memory_size_list_with_gb))

        if all(cap < int(self.platform_based_config_check['capacity']) for cap in self.dram_memory_size_list):
            raise content_exceptions.TestFail("Maximum RDIMM Capacity is not configured in the server, please make "
                                              "the system to have maximum RDIMM capacity..")

        self._log.info("Installed and verified Maximum capacity DIMMs supported by the platform...")

        self._common_content_lib.clear_os_log()  # TO clear Os logs
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._log.info("Bios knobs are set to its defaults.. ")
        self._os.reboot(int(self._reboot_timeout))  # To apply the new bios setting.
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Check memory information.

        :return: True, if the test case is successful.
        :raise: TestFail
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        self._log.info("POST displays the amount of physical memory installed in system  - {}".format(
            self._post_mem_capacity_config))

        self._log.info("DDR memory capacity as per configuration - {}".format(self._ddr4_mem_capacity_config))

        #  Total memory with variance
        total_memory_variance = (self._ddr4_mem_capacity_config - (self._ddr4_mem_capacity_config * self._variance_percent))

        self._log.info("Total Installed DDR memory capacity with variance - {}".format(
            total_memory_variance))

        if self._post_mem_capacity_config < int(total_memory_variance) or self._post_mem_capacity_config > \
                self._ddr4_mem_capacity_config:
            raise content_exceptions.TestFail("Total Installed DDR Capacity is not same as configuration.")

        self._log.info("Total Installed DDR memory Capacity is same as configuration.")

        # Step Logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        # Sum of all the populated DRAM sizes
        total_dram_memory = sum(self.dram_memory_size_list)

        self._log.info("Total memory capacity shown OS Level - {}".format(total_dram_memory))

        self._log.info("Total DDR capacity as per configuration - {}".format(self._ddr4_mem_capacity_config))

        if total_dram_memory < int(total_memory_variance) or total_dram_memory > self._ddr4_mem_capacity_config:
            raise content_exceptions.TestFail("Total Installed DDR Capacity is not same as configuration.")

        self._log.info("Total Installed DDR Capacity is same as configuration.")

        # Step Logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        self._install_collateral.install_stress_test_app()

        self._stress_app_provider.execute_installer_stressapp_test(
            "./stressapptest -s {} -M -m -W -l stress.log ".format(self._stress_app_execute_time))

        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(test_case_id=self.TEST_CASE_ID,
                                                                            sut_log_files_path=self.LINUX_USR_ROOT_PATH,
                                                                            extension=".log")
        # Step Logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        return self._memory_common_lib.parsing_log_for_error_patterns(log_path=os.path.join(log_path_to_parse,
                                                                                            "stress.log"))

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiMemoryDdrDimmMaxmiumMemory, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiMemoryDdrDimmMaxmiumMemory.main()
             else Framework.TEST_RESULT_FAIL)
