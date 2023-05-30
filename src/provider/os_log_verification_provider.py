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
import os
import json
from importlib import import_module
from abc import ABCMeta, abstractmethod
from six import add_metaclass

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
import src.lib.content_exceptions as content_exceptions
from src.provider.base_provider import BaseProvider
from src.lib.dtaf_content_constants import ExecutionEnv
from src.lib.dtaf_content_constants import OsLogVerificationConstant


@add_metaclass(ABCMeta)
class OsLogVerificationProvider(BaseProvider):

    def __init__(self, log, os_obj, cfg_opts=None):
        """
        Create a new OsLogVerification object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(OsLogVerificationProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._sut_os = self._os.os_type
        self._common_content_config = ContentConfiguration(self._log)
        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg_opts)
        self._cmd_time_out_in_sec = self._common_content_config.get_command_timeout()

    @staticmethod
    def factory(log, os_obj, cfg_opts=None):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        """
        package = r"src.provider.os_log_verification_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "OsLogVerificationProviderWindows"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "OsLogVerificationProviderLinux"
        else:
            raise NotImplementedError("Os Log Provider is not implemented for "
                                      "specified OS '{}'".format(os_obj.os_type))

        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(cfg_opts=cfg_opts, log=log, os_obj=os_obj)

    @abstractmethod
    def verify_os_log_error_messages(self, test_file, dut_os_error_log_file_name,
                                     passed_error_signature_list_to_parse, error_signature_list_to_log=None,
                                     check_error_not_found_flag=False):
        """
        This method is to verify the Os Log error messages.

        :param test_file
        :param dut_os_error_log_file_name
        :param passed_error_signature_list_to_parse
        :param error_signature_list_to_log
        :param check_error_not_found_flag
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def check_if_mce_errors(self):
        """
        This method is to check mce Error.

        :raise NotImplementedError
        """
        raise NotImplementedError


class OsLogVerificationProviderLinux(OsLogVerificationProvider):
    """
    This Class has different method of Storage Functionality on Windows Platform
    """

    def __init__(self, log, os_obj, cfg_opts=None):
        super(OsLogVerificationProviderLinux, self).__init__(log, os_obj, cfg_opts)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj

    def factory(log, os_obj, cfg_opts=None):
        pass

    def verify_os_log_error_messages(self, test_file, dut_os_error_log_file_name,
                                     passed_error_signature_list_to_parse, error_signature_list_to_log=None,
                                     check_error_in_log=False):
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
        :param check_error_in_log: Flag to check, no error found in dut os error flag.
        :type check_error_in_log: Boolean
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
        os_log_cmd_mapping_dictionary = {
            OsLogVerificationConstant.DUT_MESSAGES_FILE_NAME:
                "cat " + OsLogVerificationConstant.DUT_MESSAGES_PATH,
            OsLogVerificationConstant.DUT_JOURNALCTL_FILE_NAME:
                OsLogVerificationConstant.DUT_JOURNALCTL_FILE_NAME + " --no-pager",
                OsLogVerificationConstant.DUT_DMESG_FILE_NAME: OsLogVerificationConstant.DUT_DMESG_FILE_NAME,
                OsLogVerificationConstant.DUT_RAS_TOOLS_FILE_NAME: "cat exe.log",
                OsLogVerificationConstant.DUT_STRESS_FILE_NAME: "cat stress.log"}
        try:
            os_log_cmd_to_execute = os_log_cmd_mapping_dictionary[dut_os_error_log_file_name]
        except KeyError:
            raise ValueError("Invalid or unknown OS error log specified")

        output_file_log = self._os.execute(os_log_cmd_to_execute, self._cmd_time_out_in_sec)
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
        if not check_error_in_log:
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

    def check_if_mce_errors(self):
        """
        Checks the linux MCE Errors

        :return log
        """
        self._common_content_lib.install_abrt_cli_in_linux()
        self._log.debug("Checking for MCE logs")
        sut_cmd = self._os.execute(OsLogVerificationConstant.CMD_TO_GREP_MCE_ERROR,
                                   self._cmd_time_out_in_sec)
        self._log.debug("ABRT-CLI CMD output: %s", sut_cmd.stdout.strip())
        self._log.error("ABRT-CLI CMD Error: %s", sut_cmd.stderr.strip())
        if sut_cmd.stderr.strip() != "":
            raise RuntimeError("failed to execute abrt-cli: %s",
                               sut_cmd.stderr.strip())

        return sut_cmd.stdout.strip()


class OsLogVerificationProviderWindows(OsLogVerificationProvider):
    """
    This Class is having the method of storage functionality based on Linux.
    """

    def __init__(self, log, os_obj, cfg_opts=None):
        super(OsLogVerificationProviderWindows, self).__init__(log, os_obj, cfg_opts)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj

    def factory(log, os_obj, cfg_opts=None):
        pass

    def verify_os_log_error_messages(self, test_file, dut_os_error_log_file_name,
                                     passed_error_signature_list_to_parse, error_signature_list_to_log=None,
                                     check_error_in_log=False):
        """
        This method is to verify the Os Log Error Messages.

        :param test_file: The name of the test file used to create a similarly named test error log
        :type test_file: Full file name path
        :param dut_os_error_log_file_name: Error log file name, i.e. messages or dmesg_file
        :type dut_os_error_log_file_name: String
        :param passed_error_signature_list_to_parse: test error signature to verify in a list form
        :type passed_error_signature_list_to_parse: List

        :param error_signature_list_to_log: signature strings to place in test log(typical=mcelog)
        :type error_signature_list_to_log: List
        :param check_error_in_log: Flag to check, no error found in dut os error flag.
        :type check_error_in_log: Boolean
        """
        raise NotImplementedError("Not Implemented for Windows")

    def check_if_mce_errors(self):
        """
        This method is to get the mce logs.

        :return Log
        """
        return self._common_content_lib.check_if_mce_errors()
