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


class OsLogVerifyCommon:
    """
    This Class is to verify the Os Log Error.
    1. var\log\messages
    2. dmesg
    3. journalctl
    4. ras tool
    """
    DUT_STRESS_FILE_NAME = "stress.log"
    DUT_RAS_TOOLS_FILE_NAME = "ras_tools"
    DUT_MESSAGES_FILE_NAME = "messages"
    DUT_MESSAGES_PATH = "/var/log/" + DUT_MESSAGES_FILE_NAME
    DUT_WINDOWS_WHEA_LOG = "Windows whea"

    DUT_JOURNALCTL_FILE_NAME = "journalctl"
    DUT_JOURNALCTL_NO_PROMPT = DUT_JOURNALCTL_FILE_NAME + " --no-pager"
    DUT_JOURNALCTL_DMESG_SINCE_30_SECONDS = DUT_JOURNALCTL_NO_PROMPT + " --dmesg --since '30 seconds ago'"
    DUT_JOURNALCTL_CURRENT_BOOT = DUT_JOURNALCTL_NO_PROMPT + " --boot"

    DUT_DMESG_FILE_NAME = "dmesg"

    RUNNER_CMD_NAME = "run-rasrunner -i 0x100 -pcie 0:0:0:0 -t 00:00:5"
    RUNNER_PATH = r'/runner/bin/scripts/run-rasrunner.py'
    MACHINE_CHECK_0_TOLERANT = r'/sys/devices/system/machinecheck/machinecheck0/tolerant'
    DUT_DMESG_FILE_GENERIC_ERROR_SIGNATURE = "Hardware Error"
    DUT_MESSAGES_GENERIC_ERROR_SIGNATURE = "mcelog"
    DUT_MESSAGES_DMESG_GENERIC_ERROR_SIGNATURE_LIST = (DUT_MESSAGES_GENERIC_ERROR_SIGNATURE + "," +
                                                       DUT_DMESG_FILE_GENERIC_ERROR_SIGNATURE).split(",")

    def __init__(self, log, os, content_config, content_lib =None):
        self._os = os
        self._log = log
        self._content_config = content_config
        self._content_lib = content_lib
        self._execute_cmd_timeout = self._content_config.get_command_timeout()

    def verify_os_log_error_messages(self, test_file, dut_os_error_log_file_name,
                                     passed_error_signature_list_to_parse, error_signature_list_to_log=None,
                                     check_error_not_found_flag = False, os_log_in_dtaf=True):
        """
        verify error signatures are present for given error log and error type in the Os Logs.

        :param test_file: The name of the test file used to create a similarly named test error log
        :type test_file: Full file name path
        :param dut_os_error_log_file_name: Error log file name, i.e. messages or dmesg_file
        :type dut_os_error_log_file_name: String
        :param passed_error_signature_list_to_parse: test error signature to verify in a list form
        :type passed_error_signature_list_to_parse: List

        :param error_signature_list_to_log: signature strings to place in test log(typical=mcelog)
        :type error_signature_list_to_log: List
        :param check_error_not_found_flag: Flag to check, no error found in dut os error flag.
        :type check_error_not_found_flag: Boolean
        :param os_log_in_dtaf: This falg to capture the OS log into dtaf log.
        :return: True if os logs were transferred to host and given error signature was discovered, false otherwise
        :rtype: Boolean
        """

        if error_signature_list_to_log is None:
            error_signature_list_to_log = []
        if error_signature_list_to_log is None:
            error_signature_list_to_log = []
        verified_os_log_error_messages_bool = False

        if not passed_error_signature_list_to_parse:
            raise ValueError("Error message list to parse is empty")
        if type(error_signature_list_to_log) != list:
            raise ValueError("Error_signature_list_to_log was not a list as expected")

        # Create copy of passed in list to ensure function is non-destructive to original!
        if type(passed_error_signature_list_to_parse) != list:
            error_signature_list_to_parse = [passed_error_signature_list_to_parse]
        else:
            error_signature_list_to_parse = list(passed_error_signature_list_to_parse)

        # Create the appropriate message file either from ras_tools or os to check key words
        os_log_cmd_mapping_dictionary = {self.DUT_MESSAGES_FILE_NAME: "cat " + self.DUT_MESSAGES_PATH,
                                         self.DUT_JOURNALCTL_FILE_NAME: self.DUT_JOURNALCTL_FILE_NAME + " --no-pager",
                                         self.DUT_JOURNALCTL_DMESG_SINCE_30_SECONDS: self.DUT_JOURNALCTL_NO_PROMPT + " --dmesg --since '30 seconds ago'",
                                         self.DUT_JOURNALCTL_CURRENT_BOOT: self.DUT_JOURNALCTL_FILE_NAME + " --boot",
                                         self.DUT_DMESG_FILE_NAME: self.DUT_DMESG_FILE_NAME,
                                         self.DUT_RAS_TOOLS_FILE_NAME: "cat exe.log",
                                         self.DUT_STRESS_FILE_NAME: "cat stress.log",
                                         self.DUT_WINDOWS_WHEA_LOG: """powershell.exe "(get-WinEvent @{logname='system'; ProviderName='*WHEA*'}) | """\
                                                                    """ foreach {'id: '+$_.Id; 'TimeCreated: '+$_.TimeCreated; $_.Message;"""\
                                                                    """([xml]$_.ToXml()).Event.EventData.ChildNodes | foreach {$_.Name + ': ' + $_.'#Text'}}" """}

        try:
            os_log_cmd_to_execute = os_log_cmd_mapping_dictionary[dut_os_error_log_file_name]
        except KeyError:
            raise ValueError("Invalid or unknown OS error log specified")

        output_file_log = self._os.execute(os_log_cmd_to_execute, self._execute_cmd_timeout)
        if os_log_in_dtaf:
            self._log.info("%s", output_file_log.stdout.strip())
        self._log.info("Check " + dut_os_error_log_file_name + " file content after error injection")

        found = 0
        for string_to_look in error_signature_list_to_parse:
            self._log.info("Looking for [%s]", string_to_look)
            if re.findall(string_to_look, output_file_log.stdout.strip(), re.IGNORECASE | re.MULTILINE):
                self._log.debug(" String found")
                found = found + 1
            else:
                self._log.debug(" String Not found")
        if not check_error_not_found_flag:
            if found == len(error_signature_list_to_parse):
                self._log.debug("All the strings from the list are found")
                self._log.debug("exp %d act %d", len(error_signature_list_to_parse), found)
                verified_os_log_error_messages_bool = True
            else:
                self._log.error("All the strings from the list are NOT found")
                self._log.error("exp %d act %d", len(error_signature_list_to_parse), found)
                verified_os_log_error_messages_bool = False
        else:
            if found > 0:
                self._log.error("Unexpected string Captured from OS Log")
                verified_os_log_error_messages_bool = False
            else:
                self._log.debug("strings from the list are NOT found as Expected")
                self._log.debug("exp 0 act %d", found)
                verified_os_log_error_messages_bool = True

        return verified_os_log_error_messages_bool

    def get_all_matches_from_log(self, test_file, dut_os_log_file_name,
                                     passed_signature_to_parse, os_log_in_dtaf=True):
        """
        This method parse the signature in the log file and return all matches.

        :param test_file: The name of the test file used to create a similarly named test error log
        :type test_file: Full file name path
        :param dut_os_error_log_file_name: Error log file name, i.e. messages or dmesg_file
        :type dut_os_error_log_file_name: String
        :param passed_signature_to_parse: Pattern to check in the log file
        :type passed_signature_to_parse: str
        :param os_log_in_dtaf: This flag to capture the OS log into dtaf log.
        :type os_log_in_dtaf: boolean
        :return: List contains the match values
        :rtype:  list
        """

        if type(passed_signature_to_parse) != str:
            raise ValueError("Passed signature is not string")

        # Create the appropriate message file either from ras_tools or os to check key words
        os_log_cmd_mapping_dictionary = {self.DUT_MESSAGES_FILE_NAME: "cat " + self.DUT_MESSAGES_PATH,
                                         self.DUT_JOURNALCTL_FILE_NAME: self.DUT_JOURNALCTL_FILE_NAME + " --no-pager",
                                         self.DUT_JOURNALCTL_DMESG_SINCE_30_SECONDS: self.DUT_JOURNALCTL_NO_PROMPT + " --dmesg --since '30 seconds ago'",
                                         self.DUT_JOURNALCTL_CURRENT_BOOT: self.DUT_JOURNALCTL_FILE_NAME + " --boot",
                                         self.DUT_DMESG_FILE_NAME: self.DUT_DMESG_FILE_NAME,
                                         self.DUT_RAS_TOOLS_FILE_NAME: "cat exe.log",
                                         self.DUT_STRESS_FILE_NAME: "cat stress.log",
                                         self.DUT_WINDOWS_WHEA_LOG: """powershell.exe "$a=(get-WinEvent @{logname='system'; ProviderName='*WHEA*'})[0]; """\
                                                                    """'id: '+$a.Id; 'TimeCreated: '+$a.TimeCreated; $a.Message;"""\
                                                                    """([xml]$a.ToXml()).Event.EventData.ChildNodes | foreach {$_.Name + ': ' + $_.'#Text'}" """}

        try:
            os_log_cmd_to_execute = os_log_cmd_mapping_dictionary[dut_os_log_file_name]
        except KeyError:
            raise ValueError("Invalid or unknown log type is specified")

        output_file_log = self._os.execute(os_log_cmd_to_execute, self._execute_cmd_timeout)
        if os_log_in_dtaf:
            self._log.info("%s", output_file_log.stdout.strip())
        self._log.info("Check " + dut_os_log_file_name + " file content")

        self._log.info("Looking for the regular expression pattern [%s]", passed_signature_to_parse)
        match = re.findall(passed_signature_to_parse, output_file_log.stdout.strip(), re.IGNORECASE | re.MULTILINE)
        return match
