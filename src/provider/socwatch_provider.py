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
import re

from abc import ABCMeta, abstractmethod
from importlib import import_module
from six import add_metaclass

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.provider.base_provider import BaseProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib import content_exceptions
from src.lib.content_configuration import ContentConfiguration
from src.lib.install_collateral import InstallCollateral


@add_metaclass(ABCMeta)
class SOCWatchProvider(BaseProvider):
    """
    Provides SoCWatch provider
    """
    CSV_FILE = "SoCWatchOutput.csv"
    SOCWATCH_WAIT_TIME = 2700

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new  SoCWatch object.

        :param log: Logger object to use for output messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param os_obj: os object
        """
        super(SOCWatchProvider, self).__init__(log, cfg_opts, os_obj)
        self._common_content_configuration = ContentConfiguration(log)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._common_content_lib = CommonContentLib(log, os_obj, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self.collateral_installer = InstallCollateral(self._log, self._os, self._cfg_opts)
        self.command_timeout = self._common_content_configuration.get_command_timeout()
        self.reboot_timeout = self._common_content_configuration.get_reboot_timeout()

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        """
        package = r"src.provider.socwatch_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "WindowsSoCWatch"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "LinuxSoCWatch"
        else:
            raise NotImplementedError("Test is not implemented for %s" % os_obj.os_type)
        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(log, cfg_opts, os_obj)

    @abstractmethod
    def install_socwatch_tool(self):
        """
        This function install socwatch tool
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def copy_csv_file_from_sut_to_host(self, host_log_path, socwatch_dir_path):
        """
        This function copy csv file from sut to host

        :param host_log_path: Host log path
        :param socwatch_dir_path: socwatch installed directory path
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def socwatch_command(self, run_time, dir_path):
        """
        This function execute the socwatch command

        :param run_time: run time value
        :param dir_path: socwatch dir path
        """
        raise content_exceptions.TestNotImplementedError


class WindowsSoCWatch(SOCWatchProvider):
    """
    Windows SoCWatch provider
    """

    SOCWATCH_CMD_WINDOWS = "socwatch -m -f cpu-cstate -f cpu-pstate -t {}"

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new windows SoCWatch provider object.

        :param os_obj: os object
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(WindowsSoCWatch, self).__init__(log, cfg_opts, os_obj)

    def install_socwatch_tool(self):
        """
        Socwatch tool installation
        """
        return self.collateral_installer.install_socwatch_windows()

    def copy_csv_file_from_sut_to_host(self, host_log_path, socwatch_dir_path):
        """
        Copy csv file from sut to host

        :param host_log_path: Host log path
        :param socwatch_dir_path: socwatch installed directory path
        """
        find_cmd = "where /R {} SoCWatchOutput.csv"

        self._log.info("Copy the CSV file from SUT to Host")
        csv_file_path = self._common_content_lib.execute_sut_cmd(
            find_cmd.format(socwatch_dir_path), "Finding path socwatch csv file", self.command_timeout,
            socwatch_dir_path)
        self._log.debug("csv file path {}".format(csv_file_path.strip()))
        if not csv_file_path.strip():
            raise content_exceptions.TestFail("SoCWatchOutput csv file not found ")
        self._os.copy_file_from_sut_to_local(csv_file_path.strip(), os.path.join(host_log_path, self.CSV_FILE))

    def socwatch_command(self, run_time, dir_path):
        """
        This function execute the socwatch tool

        :param run_time: run time value
        :param dir_path: socwatch dir path
        """
        regex_cmd = "Data written to:\s(.*)"
        exp_csv_file = "SoCWatchOutput"
        self._log.info("Execute the soc watch command : {}".format(self.SOCWATCH_CMD_WINDOWS.format(run_time)))

        command = "echo no | socwatch --update-usage-consent"
        self._log.debug("Executing the command : {}".format(command))
        cmd_result = self._common_content_lib.execute_sut_cmd(command, command, self.command_timeout, dir_path)
        self._log.debug(cmd_result)

        cmd_result = self._os.execute(self.SOCWATCH_CMD_WINDOWS.format(run_time), run_time + self.SOCWATCH_WAIT_TIME,
                                      dir_path)
        self._log.debug(cmd_result.stdout)
        self._log.debug(cmd_result.stderr)
        if "FATAL" in cmd_result.stderr:
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
            cmd_result = self._os.execute(self.SOCWATCH_CMD_WINDOWS.format(run_time), run_time +
                                          self.SOCWATCH_WAIT_TIME, dir_path)
            self._log.debug(cmd_result.stdout)
            self._log.debug(cmd_result.stderr)

        regex_search = re.search(regex_cmd, cmd_result.stdout)
        if not regex_search:
            raise content_exceptions.TestError("Soc watch command failed")

        if exp_csv_file not in regex_search.group(1):
            raise content_exceptions.TestError("SoCWatchOutput.csv file not generated")


class LinuxSoCWatch(SOCWatchProvider):
    """
    Linux SoCWatch provider
    """
    NO_MCE_ERRORS = "No MCE errors"
    SOCWATCH_CMD_LINUX = "echo y | ./socwatch -m -f cpu-cstate -f cpu-pstate -t %d"

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new Linux SoCWatch provider object.

        :param os_obj: os object
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(LinuxSoCWatch, self).__init__(log, cfg_opts, os_obj)

    def install_socwatch_tool(self):
        """
        Install Socwatch tool

        :return: Socwatch directory path
        """
        return self.collateral_installer.install_socwatch()

    def socwatch_command(self, run_time, dir_path):
        """
        This function execute the socwatch command on provided time and generate the Socwatchoutput.csv file

        :param run_time: socwatch execute time
        :param dir_path: socwatch installed directory path
        :raise: content_exception.TestFail if not generating the csv file
        """
        regex_cmd = "Data written to:\s(.*)"
        exp_csv_file = "./SoCWatchOutput"
        self._log.info("Execute the soc watch command to collect the data")
        cmd_result = self._common_content_lib.execute_sut_cmd(self.SOCWATCH_CMD_LINUX % run_time,
                                                              "SOCWATCH data command", run_time +
                                                              self.SOCWATCH_WAIT_TIME, dir_path)
        self._log.debug(cmd_result)
        regex_search = re.search(regex_cmd, cmd_result)
        if not regex_search:
            raise content_exceptions.TestError("Socwatch command failed")
        if exp_csv_file not in regex_search.group(1):
            raise content_exceptions.TestError("SoCWatchOutput.csv file not generated")

    def copy_csv_file_from_sut_to_host(self, log_dir, socwatch_dir_path):
        """
        This function copy the socwatchoutput.csv file from SUT to HOST

        :param log_dir: Log directory
        :param socwatch_dir_path: socwatch installed directory path
        :raise: content_exception.TestFail if not getting csv file path
        """
        find_cmd = "find $(pwd) -type f -name 'SoCWatchOutput.csv'"

        self._log.info("Copy the CSV file from SUT to Host")
        csv_file_path = self._common_content_lib.execute_sut_cmd(find_cmd, "Finding path socwatch csv file",
                                                                 self.command_timeout, socwatch_dir_path)
        self._log.debug("csv file path {}".format(csv_file_path.strip()))
        if not csv_file_path.strip():
            raise content_exceptions.TestFail("SoCWatchOutput csv file not found ")
        self._os.copy_file_from_sut_to_local(csv_file_path.strip(), os.path.join(log_dir, self.CSV_FILE))


class SocWatchCSVReader(object):
    """
    Reads the socwatch output which is in CSV format
    """

    __PACKAGE_C_STATE_RESIDENCY_TIME = "Package C-State Summary: Residency (Percentage and Time)"
    __CORE_C_STATE_RESIDENCY_TIME = "Core C-State Summary: Residency (Percentage and Time)"
    __CORE_P_STATE_FRQ_RESIDENCY_TIME = "Core P-State/Frequency Summary: Residency (Percentage)"
    __ALTERNATIVE_CORE_P_STATE_FRQ_RESIDENCY_TIME = "Core P-State/Frequency Summary: Residency (Percentage and Time)"
    __ALTERNATIVE_CPU_P_STATE_FRQ_RESIDENCY_TIME = "CPU P-State/Frequency Summary: Residency (Percentage and Time)"

    _RESIDENCY_PERCENT_MATCH = "Residency (%)"

    def __init__(self, log, csv_file):
        """
        Constructor of SocWatchCSVReader

        :param log: Logger object to use for output messages
        :param csv_file: full path to the csv fil
        """
        self._log = log
        self.csv_file = csv_file

    def update_csv_file(self, csv_file):
        """
        Updates the CSV file at runtime

        :param csv_file: full path to the csv file
        """
        self.csv_file = csv_file

    def read_csv_table(self, match, alternative_match=None):
        """
        Parse CSV file with the given string and return the dict

        :param match: table heading
        :param alternative_match: alternative table heading
        :return table_data_dict: returns the particular table
        """
        self._log.info("Reading the CSV file")
        from collections import OrderedDict
        table_data_dict = OrderedDict()
        with open(self.csv_file) as csv_file_read:
            data = csv_file_read.read()
            if data.split(match)[-1].strip() == "":
                return table_data_dict
            if match not in data:
                if alternative_match:
                    for table_data in alternative_match:
                        if table_data in data:
                            match = table_data
                            break
            if match not in data:
                raise content_exceptions.TestFail(
                    "Table %s and %s not found in the socwatch output" % match % alternative_match)
            table = data.split(match)[-1].split("\n\n")[0].strip().splitlines()
            table_heads = [item.strip() for item in table[0].split(",")]
            table_data = [item.strip() for item in table[2::]]
            self._log.debug("Table heads for pacakge {}".format(table_heads))
            self._log.debug("Table data for pacakge {}".format(table_data))
            for j in range(len(table_data)):
                pstate_data = [item.strip() for item in table_data[j].split(",")]
                pstate = pstate_data[0]
                if pstate not in table_data_dict.keys():
                    table_data_dict[pstate] = {}
                if len(table_data_dict[pstate]):
                    pstate = pstate + "_%s" % j
                    table_data_dict[pstate] = {}
                for i in range(1, len(pstate_data)):
                    table_data_dict[pstate][table_heads[i]] = pstate_data[i]
        self._log.debug("Package table data dict {}".format(table_data_dict))
        return table_data_dict

    def get_package_c_state_residency_time_summary(self):
        """
        Get package C-State residency table from csv file

        :return: Returns the Package C-State Summary Residency (Percentage and Time)
        """
        return self.read_csv_table(self.__PACKAGE_C_STATE_RESIDENCY_TIME)

    def verify_pacakge_c_state_residency(self, package_c_state, condition):
        """
        Verify the package C-State residency percentage

        :param package_c_state: get the package state
        :param condition: validate the condition with the package C-State
        :raise: content_exception.TestFail if not getting the expected values
        """
        self._log.info("Verifying the package c-state of {} with threshold {}".format(package_c_state, condition))
        package_c_state_table = self.get_package_c_state_residency_time_summary()
        if not len(package_c_state_table):
            raise content_exceptions.TestFail("Could not find the package c state residency table in SocWatchOutput")
        package_c_state_values = None
        try:
            package_c_state_values = package_c_state_table[package_c_state]
        except KeyError:
            raise content_exceptions.TestFail("%s package C state does not exist in SoCWatchOutput",
                                              package_c_state_values)
        invalid_matches = []
        for key, value in package_c_state_values.items():
            if self._RESIDENCY_PERCENT_MATCH in key:
                if not eval(condition.replace(package_c_state, value)):
                    invalid_matches.append(key + ":" + condition.replace(package_c_state, value))
        if len(invalid_matches):
            raise content_exceptions.TestFail("{} package c state verification failed, check the threshold "
                                                    "values {}".format(package_c_state, invalid_matches))
        self._log.info("%s package c state has been verified successfully" % package_c_state)

    def get_core_c_state_residency_time_summary(self):
        """
        Get core C-State residency percentage table from csv file

        :return: Returns the Core C-State Summary Residency (Percentage and Time)
        """
        return self.read_csv_table(self.__CORE_C_STATE_RESIDENCY_TIME)

    def verify_core_c_state_residency(self, core_c_state, condition, cc0_cc1_sum=False):
        """
        Verify the core C-State residency percentage

        :param core_c_state: get the core state
        :param condition: validate the condition with the core C-State
        :param cc0_cc1_sum: if we need add CC0 & CC1 then True else False
        :raise: content_exception.TestFail if not getting the expected values
        """
        self._log.info("Verify Core C-State residency {} with threshold {}".format(core_c_state, condition))
        core_c_state_table = self.get_core_c_state_residency_time_summary()
        if not len(core_c_state_table):
            raise content_exceptions.TestFail("Could not find the core c state residency table in SocWatchOutput")
        core_c_state_values = None
        try:
            if cc0_cc1_sum:
                dict_core_c_state_values = {}
                core_cc0_values = core_c_state_table[CoreCStates.CORE_C_STATE_CC0]
                self._log.info("Core CC0 values : {}".format(core_cc0_values))
                core_cc1_values = core_c_state_table[CoreCStates.CORE_C_STATE_CC1]
                self._log.info("Core CC1 values : {}".format(core_cc1_values))
                for each_key in core_cc0_values:
                    if self._RESIDENCY_PERCENT_MATCH in each_key:
                        dict_core_c_state_values[each_key] = \
                            str(float(core_cc0_values[each_key]) + float(core_cc1_values[each_key]))
                core_c_state_values = dict_core_c_state_values
                self._log.info("Core C-state values : {}".format(core_c_state_values))
            else:
                core_c_state_values = core_c_state_table[core_c_state]
                self._log.info("Core C-state values : {}".format(core_c_state_values))
        except KeyError:
            raise content_exceptions.TestFail("%s core C state does not exist in SoCWatchOutput",
                                              core_c_state_values)
        invalid_matches = []
        for key, value in core_c_state_values.items():
            if self._RESIDENCY_PERCENT_MATCH in key:
                if not eval(condition.replace(core_c_state, value)):
                    invalid_matches.append(key + ":" + condition.replace(core_c_state, value))
        if len(invalid_matches):
            raise content_exceptions.TestFail("{} core c state verification failed, check the threshold values"
                                  "{}".format(core_c_state, invalid_matches))
        self._log.info("%s core c state has been verified successfully" % core_c_state)

    def get_package_p_state_residency_time_summary(self):
        """
        Get package C-State residency table from csv file

        Returns the Package C-State Summary: Residency (Percentage and Time)
        """
        return self.read_csv_table(self.__CORE_P_STATE_FRQ_RESIDENCY_TIME,
                                   [self.__ALTERNATIVE_CORE_P_STATE_FRQ_RESIDENCY_TIME,
                                    self.__ALTERNATIVE_CPU_P_STATE_FRQ_RESIDENCY_TIME])

    def verify_package_p_state_residency(self, package_p_state, pstate_table, condition):
        """
        Verify the package P-State residency percentage

        :param core_c_state: get the package state
        :param condition: validate the condition with the pacakge C-State
        :raise: content_exception.TestFail if not getting the expected values
        """
        core_c_state_values = None
        try:
            core_c_state_values = pstate_table[package_p_state]
        except KeyError:
            raise content_exceptions.TestFail("%s package C state does not exist in SoCWatchOutput",
                                              core_c_state_values)
        matches = []
        for key, value in core_c_state_values.items():
            if self._RESIDENCY_PERCENT_MATCH in key:
                if eval(condition.replace(package_p_state, value)):
                    matches.append(key + ":" + condition.replace(package_p_state, value))
        return matches


class PackageCStates():
    """
    Package C-State Constant Variables
    """
    PACKAGE_C_STATE_PC0 = "PC0"
    PACKAGE_C_STATE_PC2 = "PC2"
    PACKAGE_C_STATE_PC3 = "PC3"
    PACKAGE_C_STATE_PC6 = "PC6"
    PACKAGE_C_STATE_PC7 = "PC7"


class CoreCStates():
    """
    Core C-State Constant Variables
    """
    CORE_C_STATE_CC0 = "CC0"
    CORE_C_STATE_CC1 = "CC1"
    CORE_C_STATE_CC6 = "CC6"
    CORE_C_STATE_CC0_CC1 = "CC0+CC1"


class PacakgePState():
    """
    Package P-State constant variables
    """
    PACKAGE_P_STATE_P0 = "P0"
    PACKAGE_P_STATE_P1 = "P1"
    PACKAGE_P_STATE_CPU_IDLE = "CPU Idle"
