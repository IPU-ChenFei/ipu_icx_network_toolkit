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
from src.lib.dmidecode_verification_lib import DmiDecodeVerificationLib
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_ddr.ddr_common import DDRCommon


class MemoryDDRDimmMinimumMemoryConfigReportingLinux(DDRCommon):
    """
    Glasgow ID: 63282

    This test case is to demonstrate stress app Memory Stress.
    This testing covers the below tasks..
    1. Verify platform functional reliability with the a memory configuration as spec defined without unexpected errors
       under heavy stress with data integrity checking.
    2. Configure the stress app Data Integrity & Stress application for the platform.
    3. Execute memory focused stress for specified period of time.
    4. Check basic platform functionality while under stress.
    5. Verify no unexpected errors were logged while executing stress.
    """

    _bios_config_file = "memory_ddr_dimm_minimum_memory_config_reporting_linux.cfg"
    TEST_CASE_ID = "G63282"

    VAR_LOG_MSG_CMD = "cat /var/log/messages >& message.log"
    JOURNAL_CTL_CMD = "journalctl -u mcelog.service >& journalctl.log"
    DMESG_CMD = "dmesg >& dmesg.log"
    dmi_cmd = "dmidecode > dmi.txt"
    step_data_dict = {1: {'step_details': 'Set and verify BIOS knobs and verify the Total memory before and after '
                                          '    BIOS knobs setting',
                          'expected_results': 'BIOS setup options are updated with changes saved and the memory '
                                              'reported by OS is consistent '},

                      2: {'step_details': 'Execute "dmidecode" cmd and create an output file of the smbios information '
                                          'and clear OS logs & dmegs logs',
                          'expected_results': 'Dmidecode output file is creted with smbios information .'
                                              'and OS logs & dmegs logs are cleared '},

                      3: {'step_details': 'Verify the dmidecode output file and check the required fields in '
                                          'each entry',
                          'expected_results': 'All the required fields in dmidecode output file are verified'
                                              'in parsing '},

                      4: {'step_details': 'Display the "Load Average" is closer to zero ',
                          'expected_results': 'Load Average readings are closer to zero '},

                      5: {'step_details': 'Install the stress app and if stress app is already '
                                          'installed, delete the existing log files ',
                          'expected_results': 'Successfully Installed the stress app tool.'
                                              'and Pre-existing stress app logs are deleted '},

                      6: {'step_details': 'Execute stress app tool on SUT',
                          'expected_results': 'Stress app tool executed without any errors'},

                      7: {'step_details': 'Execute Load Average" value should be around 50 or greater',
                          'expected_results': 'Load Average   is significantly greater after Stress app tool'
                                              ' begins execution '},

                      8: {'step_details': 'Parse the stress log, OS log, dmesg log and journalctl logs for any '
                                          'unexpected errors and warnings ',
                          'expected_results': 'No unexpected errors were logged during stress log, '
                                              ' and OS log,  dmesg log and journalctl logs'},
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new stress app Memory Stress object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        # calling base class init
        super(MemoryDDRDimmMinimumMemoryConfigReportingLinux, self).__init__(test_log, arguments, cfg_opts,
                                                                             self._bios_config_file)
        self._dmi_decode_verification_lib = DmiDecodeVerificationLib(test_log, self._os)
        self.platform_based_config_check = self._common_content_configuration.get_memory_supported_smallest_info(
            self._product_family)

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.
        5. Verifying total memory before and after bios setting

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
        dram_memory_location_list = []

        for key in dict_dmi_decode_from_tool.keys():
            if dict_dmi_decode_from_tool[key]['Size'] != "No Module Installed":
                if dict_dmi_decode_from_tool[key]['Memory Technology'] == "DRAM":
                    dram_memory_size_list_with_gb.append(dict_dmi_decode_from_tool[key]['Volatile Size'])
                    dram_memory_location_list.append(dict_dmi_decode_from_tool[key]['Locator'])

                    self._log.info("The size of DRAM is {} located at {}".format(
                        dict_dmi_decode_from_tool[key]['Volatile Size'], dict_dmi_decode_from_tool[key]['Locator']))

        # Remove the GB and take only numeric value (size) of dram
        dram_memory_size_list = list(map(lambda sub: int(''.join([ele for ele in sub if ele.isnumeric()])),
                                         dram_memory_size_list_with_gb))

        if all(cap != int(self.platform_based_config_check['capacity']) for cap in dram_memory_size_list):
            raise content_exceptions.TestFail("Minimum RDIMM Capacity is not configured in the server, please make "
                                              "the system to have minimum RDIMM capacity..")

        if all(loc in self.platform_based_config_check['locator'] for loc in dram_memory_location_list):
            raise content_exceptions.TestFail("Minimum RDIMM Capacity is not configured in the server, please make "
                                              "the system to have minimum RDIMM capacity..")

        self._log.info("Installed and verified minimum capacity DIMMs supported by the platform...")

        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        total_memory_before_bios = self.get_total_memory()
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        total_memory_after_bios = self.get_total_memory()
        self.compare_memtotal(total_memory_before_bios, total_memory_after_bios)

        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,

        1. Clear dmegs log.
        2. Clear OS logs and verify the load average value.
        3. Execute dmidecode command and verifying memory devices
        4. Checking load average before system under stress
        5. Install stress app tool.
        6. Verifying no unexpected errors were logged while executing stress under the specified conditions.
        7. Verifying the load average after the stress app tool.
        8. Copy log files to Host
        9. Verifying no unexpected errors were logged in /var/log/messages.
        10. Verifying no unexpected errors were logged in dmegs.
        11. Verifying no unexpected errors were logged in journal ctl.

        :return: True, if the test case is successful else false
        :raise: Runtime error
        """
        return_value = []
        logs_flag = []
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # Execute the dmidecode command and copy dmi.txt file from SUT to Host
        self._common_content_lib.execute_sut_cmd(self.dmi_cmd, "get dmi dmidecode output", self._command_timeout,
                                                 cmd_path=self.LINUX_USR_ROOT_PATH)
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(test_case_id=self.TEST_CASE_ID,
                                                                            sut_log_files_path=self.LINUX_USR_ROOT_PATH,
                                                                            extension=".txt")
        dict_dmi_decode_from_tool = self._dmidecode_parser.dmidecode_parser(log_path_to_parse)
        dict_dmi_decode_from_spec = self._smbios_config.get_smbios_table_dict()

        # To clear the os logs messages in SUT
        self._common_content_lib.clear_os_log()

        # Clear dmesg logs in SUT
        self._common_content_lib.clear_dmesg_log()

        #  Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        # Checking the Desktop Management Interface Type 17
        return_value.append(self._dmi_decode_verification_lib.verify_memory_device(
            dict_dmi_decode_from_tool, dict_dmi_decode_from_spec))

        #  Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=all(return_value))

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        # Load average before system under stress
        load_avg_value = self.get_load_average()
        max_load_avg = self.get_max_load_average(load_avg_value)
        self._log.info("Correct load average value {}".format(max_load_avg))
        if float(max_load_avg) <= self.CMP_LOAD_AVERAGE_BEFORE_STRESSAPP:
            self._log.info("Success as maximum value of load average value is less than threshold value")
        else:
            log_err = "Failed as maximum value of load average value more than threshold value"
            self._log.error(log_err)
            raise RuntimeError(log_err)

        #  Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)
        #
        # Install latest version of stress app
        self._install_collateral.install_stress_test_app()

        #  Step logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=True)

        # Step logger start for Step 6
        self._test_content_logger.start_step_logger(6)

        # Execute stress app test tool
        self.execute_installer_stressapp_test_linux()

        #  Step logger end for Step 6
        self._test_content_logger.end_step_logger(6, return_val=True)

        # Step logger start for Step 7
        self._test_content_logger.start_step_logger(7)

        # To check max load avg after stress
        load_avg_value = self.get_load_average()
        max_load_avg = self.get_max_load_average(load_avg_value)
        self._log.info("Correct load average value {}".format(max_load_avg))
        if float(max_load_avg) >= self.CMP_LOAD_AVERAGE_AFTER_STRESSAPP:
            self._log.info("Correct load average value...")
        else:
            log_error = "Incorrect load average value"
            self._log.error(log_error)
            raise RuntimeError(log_error)

        #  Step logger end for Step 7
        self._test_content_logger.end_step_logger(7, return_val=True)

        # Step logger start for Step 8
        self._test_content_logger.start_step_logger(8)

        self._common_content_lib.execute_sut_cmd(self.VAR_LOG_MSG_CMD,
                                                 "redirect /var/log/messages to message.log ",
                                                 self._command_timeout, self.LINUX_USR_ROOT_PATH)
        self._common_content_lib.execute_sut_cmd(self.JOURNAL_CTL_CMD,
                                                 "To execute journalctl command ",
                                                 self._command_timeout, self.LINUX_USR_ROOT_PATH)
        self._common_content_lib.execute_sut_cmd(self.DMESG_CMD,
                                                 "To execute demsg command ",
                                                 self._command_timeout, self.LINUX_USR_ROOT_PATH)

        #  Copy all stress, dmesg, journalctl and message logs from SUT to Host
        file_path_host = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.LINUX_USR_ROOT_PATH, extension=".log")

        logs_to_check = ["stress.log", "dmesg.log", "journalctl.log", "message.log"]
        for log_file in logs_to_check:
            logs_flag.append(self._memory_common_lib.parse_log_for_error_patterns
                             (log_path=os.path.join(file_path_host, log_file), encoding='UTF-8'))

        return_value.append(all(logs_flag))

        #  Step logger end for Step 8
        self._test_content_logger.end_step_logger(8, return_val=all(logs_flag))

        return all(return_value)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(MemoryDDRDimmMinimumMemoryConfigReportingLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MemoryDDRDimmMinimumMemoryConfigReportingLinux.main()
             else Framework.TEST_RESULT_FAIL)
