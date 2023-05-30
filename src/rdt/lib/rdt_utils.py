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
import time
import os
import pandas as pd
import numpy as np
from io import StringIO
import matplotlib.pyplot as plt

from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import RDTConstants, RootDirectoriesConstants


class RdtUtils(object):
    """
    This class contains RDT tool's utility functions which can be used across many test cases.
    """
    DATA_TO_IGNORE = ("TIME", "NOTE", "CAT", "CMT/MBM", "WARN:")
    MBR_STR = "MBR[MB/s]"
    CORES_SELECTED = "0,1,2,3"
    ERROR_LIST = ["error", "warning"]
    BIT_MASKING_SUCCESSFUL_INFO = "Allocation configuration altered"
    BIT_MASKING_ERROR_INFO = "Allocation configuration error"
    UNKNOWN_PID_ERROR_INFO = "Task ID number or class id is out of bounds!"
    CHANGE_BIT_MASK_INFO = "l3ca bit mask cmd"
    RESTORE_DEFAULT_CMD = "pqos -R"
    INTERFACE_OPTION = "-I"
    RESTORE_DEFAULT_MONITORING_CMD = "pqos -r -t 10"
    RESTORE_SUCCESSFUL_INFO = ["Allocation reset successful"]
    RESTORE_CMD_INFO = "Restore default monitor cmd"
    CHECK_L3CA_CMD = "pqos -s"
    CHECK_L3CA_MBA_CMD = "pqos -I -s"
    PQOS_SUCCESSFULL_INFO = "MBA\sCOS\d+\s\=\>\s{}\%\savailable"
    PQOS_INVALID_SUCCESFUL_INFO = "Invalid\sRDT\sparameters"
    CHECK_L3CA_VERBOSE = "pqos -s -v"
    L3CA_SUCCESS_MESSAGE = ["L3CA capability detected", "INFO: L3 CAT details: CDP support=1"]
    CHECK_L3CA_VERBOSE_INTERFACE = "pqos -s -v -I"
    VERIFY_MBA_CAPABILITY = "pqos -s -v"
    CHANGE_BIT_MASK_CMD = "pqos -e 'mba:{}={}'"
    MBA_COS_RATE_SUCESS_INFO = "SOCKET {} MBA COS{} => {}% requested, {}% applied"
    MBA_COS_OUT_OF_RANGE_INFO = "MBA COS{} rate out of range (from 1-100)!"
    MBA_CAPABILITY_INFO = "MBA capability check command"
    MBA_SUCCESFUL_INFO = ["MBA capability detected"]
    L3CA_CMD_INFO = "check L3CA COS definition"
    GET_SOCKET_REGEX = "SOCKET(\s\d+)"
    SOCKET_STR = "SOCKET"
    CORE_REGEX = "Core\s(\d+)*"
    COS_REGEX = "COS\d+"
    MASK_VAL_REGEX = "MASK\s(0x.*)"
    KILL_STRESS_CMD = "pkill -INT stress"
    KILL_MEMTESTER_CMD = "pkill -INT memtester"
    RDT_MONITOR_CMD = "pqos -m 'all:{}' -t 0"
    ALLOCATION_SUCCESSFUL_INFO = ["Allocation configuration altered"]
    ALLOCATE_L3CACHE_INFO = "Allocate l3 cache cmd"
    PQOS_CMD = " pqos -t 10"
    EVENT_CORE = "CORE"
    GRAPH_FILENAME = 'output.png'
    RDT_EVENT_PARAMETERS_LIST = ["IPC", "MISSES", "LLC[KB]", "MBL[MB/s]", "MBR[MB/s]"]
    EVENT_MISS = "MISSES"
    KILL_PQOS_CMD = "pkill -INT pqos"
    KILL_TASKSET_CMD = "pkill -INT stream"
    KILL_MEMBW_CMD = "pkill -INT membw"
    KILL_CMD = "pkill -INT {}"
    MSR_VALUES = [10, 11, 19, 20, 21, 29, 30, 31, 39]
    REGISTER_VALUES = ["0xd50", "0xd51", "0xd52", "0xd53", "0xd54", "0xd55", "0xd56", "0xd57"]
    READ_MSR_VALUES = []
    MSR_OUTPUT_VALUES = []
    EXPECTED_OUTPUT_VALUES = ["a", "14", "1e"]
    PACKAGE_NUMACTL = "numactl"
    NUMACTL_CMD = "numactl --hardware"
    EXPECTED_NODE_STR = "node 0"
    INTERFACE_CMD = "pqos -I -R"
    INTERFACE_L3CA_CMD = "pqos -I -s"
    CMT_EVENTS_PLATFORM = "Cache Monitoring Technology .CMT. events:\s+LLC Occupancy .LLC."
    CMT_EVENT_PARAMETERS_LIST = ["CORE", "IPC", "MISSES"]
    PID_VALUE_CMD = "pgrep memtester"
    PID = "PID"
    TIME_STR = "TIME"
    STRESS_STR = "stress"
    CURR_PROCESS_RUNNING_CMD = "ps -ef | grep -i {}"
    ITERATION = 5
    HCC_CORES_DEC = ['0x800', '0xc00', '0xe00', '0xf00', '0xf80', '0xfc0', '0xfe0', '0xff0', '0xff8', '0xffc', '0xffe']
    LCC_CORES_DEC = ['0x400', '0x600', '0x700', '0x780', '0x7c0', '0x7e0', '0x7f0', '0x7f8', '0x7fc', '0x7fe']
    HCC_CORES_INC = ['0x7ff', '0x3ff', '0x1ff', '0xff', '0x7f', '0x3f', '0x1f', '0xf', '0x7', '0x3', '0x1']
    LCC_CORES_INC = ['0x3ff', '0x1ff', '0xff', '0x7f', '0x3f', '0x1f', '0xf', '0x7', '0x3', '0x1']
    CLOS0_LLC_CBM = ['0x4000', '0x6000', '0x7000', '0x7800', '0x7C00', '0x7E00', '0x7F00', '0x7F80', '0x7FC0', '0x7FE0',
                     '0x7FF0', '0x7FF8', '0x7FFC', '0x7FFE']
    CLOS1_LLC_CBM = ['0x3fff', '0x1fff', '0x0fff', '0x07ff', '0x03ff', '0x01ff', '0x00FF', '0x007F', '0x003F', '0x001F',
                     '0x000F', '0x0007', '0x0003', '0x0001']
    TASKSET_MULTICHASE = "taskset -c {} ./multichase"
    TASKSET_STREAM = "taskset -c {} ./stream"
    CDP_ON = "on"
    CDP_OFF = "off"
    L3_CDP_ENABLE_DISABLE = "pqos -R l3cdp-{} -v"
    CDP_TURNED_ON_MESSAGE = ["Turning L3 CDP ON", "L3 CDP is enabled"]
    CDP_TURNED_OFF_MESSAGE = ["Turning L3 CDP OFF", "L3 CDP is disabled"]
    CDP_ENABLED = "enabled"
    CDP_DISABLED = "disabled"
    SOCKET_CHECK = "grep 'physical id' /proc/cpuinfo | sort -u | wc -l"
    COS_ARG1_VALUE = "0xf"
    COS_ARG2_VALUE = "0xf0"
    COS_ARG3_VALUE = "0xffffffff"
    COS_ARG4_VALUE = "0xffff"
    ITERATION_NUM = 3
    CORES_PER_SOCKET = "lscpu | grep -i 'Core(s) per socket' | awk '{print substr($0,length,1)}'"
    VAL_OF_CORE = "0"
    VALUES_OF_CORE2 = "1,2,3,4,5"
    ALLOCATE_CACHE_TO_CORE_CMD = "pqos -a 'llc:{}={}'"
    ALLOCATE_CACHE_TO_CORE2_CMD = "pqos -a 'llc:{}={}'"
    SET_COS1_TO_LLC_CBM_BIT = "pqos -e 'llc@{}={}'"
    SET_COS2_TO_ENTIRE_LLC_BIT = "pqos -e 'llc@{}={}'"
    COS1_VALUE = "COS1"
    COS2_VALUE = "COS2"
    COS_VALUE_LIST = [('0x4000', '0x3fff'), ('0x6000', '0x1fff'), ('0x7000', '0x0fff'), ('0x7800', '0x7ff'),
                      ('0x7C00', '0x03ff'), ('0x7E00', '0x01ff'), ('0x7F00', '0x00FF'), ('0x7F80', '0x007F'),
                      ('0x7FC0', '0x003F'), ('0x7FE0', '0x001F'), ('0x7FF0', '0x000F'), ('0x7FF8', '0x0007'),
                      ('0x7FFC', '0x0003'), ('0x7FFE', '0x0001')]
    MLC_STRESS_CMD = "./mlc_internal -k1-1 --loaded_latency -d0 -T -B -b1g -R"
    MEMBW_STRESS_CORE_CMD = "./membw -c {} -b 20000 --nt-write"
    MEMBW_STR = "membw"
    PQOS_STR = "pqos"
    MEMTESTER_STR = "memtester"
    STREAM_STR = "stream"
    PCM_CHECK = "pcm"
    EXEC_TIME = 30
    CORE_ASSOCIATION_CMD = "pqos -a 'llc:0={};llc:1={}'"
    MBA_CMD = "mba@{}:{}={}"
    SET_THROTTLING_CMD = "pqos -e '{}'"
    SUCCESSFULY_SET_THROTTLING_MESSAGE = "SOCKET {} MBA COS{} => {}% requested, {}% applied"
    MONITOR_CMD = "pqos -r all:{},{},{},{} -u csv -o {}"
    MONITOR_TWO_CORES_CMD = "pqos -r all:{},{} -u csv -o {}"
    PQOS_MON_FILE_IN_SUT = "/root/pqos_mon.csv"
    CORE0 = "0"
    CORE1 = "1"
    PQOS_MON_CMD = "pqos -u csv -o {}"
    CORE_COL_NAME = "Core"
    LLC_COL_NAME = "LLC[KB]"
    SET_CLOS_CMD = 'pqos -e llc@0:{}={}'

    def __init__(self, log, common_content_lib, common_content_config, os_obj, cfg_opts):
        self._log = log
        self._os = os_obj
        self._common_content_lib = common_content_lib
        self._cfg = cfg_opts
        self._common_content_configuration = common_content_config
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._install_collateral = InstallCollateral(self._log, self._os, self._cfg)
        self._platform = self._common_content_lib.get_platform_family()
        self.default_cos_val = RDTConstants.DEFAULT_COS_MASK_VAL[self._platform]
        self.log_dir = self._common_content_lib.get_log_file_dir()

    def install_rdt_tool(self):
        """
        This method installs RDT tool on sut

        :return: None
        """
        self._install_collateral.install_rdt()

    def install_msr_tool(self):
        """
        This method installs MSR tool on sut

        :return: None
        """
        find_rdt_tool = "find $(pwd) -type d -name 'RDT'"
        rdt_tool_path = self._common_content_lib.execute_sut_cmd(find_rdt_tool, find_rdt_tool,
                                                                 self._command_timeout).strip()
        find_cmd = "find $(pwd) -name 'msr-tools*'"
        msr_tool_path = self._common_content_lib.execute_sut_cmd(find_cmd, find_cmd,
                                                                 self._command_timeout,
                                                                 cmd_path=rdt_tool_path).strip()
        self._log.debug("Msr tools package path is {}".format(msr_tool_path))
        self._install_collateral.yum_install("msr-tools*", cmd_path=os.path.dirname(msr_tool_path))

    def check_core_status(self, result):
        """
        This Function parse the whole output and checks core status is showing as expected "pqos -r 'all:0,1,2,3'"

        :param result: RDT monitoring data as input
        :return: True if all core is as expected
        """
        result_list = []
        event_df = self.__parse_monitoring_data(result)
        for val in (event_df[self.EVENT_CORE]):
            if str(val) in self.CORES_SELECTED:
                result_list.append(True)
        return all(result_list)

    def __parse_monitoring_data(self, data):
        """
        This Function parse the whole output from command by filtering unwanted data and consolidating whole data in
        a table. This data is passed to a data frame to figure the MBR range value( which should not exceed 1)
        This converts the data of below format and checks the MBR val.
        CORE   IPC   MISSES     LLC[KB]   MBL[MB/s]   MBR[MB/s]
           0  0.08       0k        84.0         0.0         0.0
           1  0.06       0k         0.0         0.0         0.0
           2  0.05       0k         0.0         0.0         0.0
           3  0.05       0k         0.0         0.0         0.0

        :param data: RDT monitoring data as input
        :return: return a data frame which contains values for all events
        :raise: Content_exception if unable to get data frame from output
        """
        monitor_data_val = []
        data_header = ""
        cmd_res_list = data.split("\n")
        self._log.info("Getting monitoring events data in a data frame")
        for data in cmd_res_list:
            if not data.strip().startswith(self.DATA_TO_IGNORE):
                if "CORE" in data.strip():
                    data_header = data
                else:
                    monitor_data_val.append(data)
        formatted_data_table = data_header + "\n" + '\n'.join(monitor_data_val)
        monitor_data_df = pd.read_csv(StringIO(formatted_data_table), sep='\s+')
        if monitor_data_df.empty:
            raise content_exceptions.TestFail("Unable to get the data frame with the command output")
        self._log.debug("The monitoring data frame is:'{}'".format(monitor_data_df))

        return monitor_data_df

    def compare_event_statistic_data(self, event_result_before_stress, event_result_after_stress, event_name):
        """
        This Function parse the whole output and checks the RDT event range value after running stress should be greater
        than RDT event values before running stress

        :param event_result_before_stress: event monitoring data before stress was run
        :param event_result_after_stress: event monitoring data after stress was run
        :param event_name: event which is to be compared
        :raise: Content_exception input event values are not greater than before running stress
        :return: None
        """
        self._log.info("Comparing {} values of before and after running stress tool".format(event_name))
        event_df1 = self.__parse_monitoring_data(event_result_before_stress)
        event_df2 = self.__parse_monitoring_data(event_result_after_stress)
        comparison_column = np.where(event_df1[event_name] < event_df2[event_name], True, False)
        if not all(comparison_column):
            raise content_exceptions.TestFail("{} values are not greater than before running stress".format(event_name))
        self._log.info("All {} values are significantly increased after running stress".format(event_name))

    def check_l3ca_core_definitions(self, command, core, expect_val):
        """
        Check L3CA COS definitions and core information before and after L3CA cache allocation.

        :param command: 'pqos -s'
        :param core: Core value which need to be checked
        :param expect_val: Value to be checked
        :raise: Content_exception if match did not find
        """
        self._log.info("Checking actual L3CA COS definitions for '{}".format(core))
        cos_regex_exp = "{},.*,.* => {},.*".format(core, expect_val)
        command_result = self._common_content_lib.execute_sut_cmd(command, "check L3CA COS definition",
                                                                  self._command_timeout)
        self._log.debug("Output of the command '{} is '{}".format(command, command_result))
        out_val = re.search(cos_regex_exp, command_result)
        if not out_val:
            raise content_exceptions.TestFail("The expected value '{}' does not matches with the resultant "
                                              "value '{}'".format(expect_val, out_val))
        self._log.info("L3CA COS definitions and Core information is verified")

    def turn_on_rdt_monitoring(self):
        """
        Turn on RDT monitoring to view the core status for 10 second by running pqos -m 'all:0,1,2,3' -t 10
        and Checks the core status is same as given in command.

        :raise: Content_exception if cores are different
        """
        self._log.info("Turning on RDT monitor by executing command "
                       "{}".format(self.RDT_MONITOR_CMD.format(self.CORES_SELECTED)))

        command_result = self._common_content_lib.execute_sut_cmd(self.RDT_MONITOR_CMD.format(self.CORES_SELECTED),
                                                                  "rdt monitoring cmd", self._command_timeout)
        self._log.debug("Output of the RDT monitoring command '{} is '{}".format(self.RDT_MONITOR_CMD.format(
            self.CORES_SELECTED), command_result))
        if not self.check_core_status(command_result):
            raise content_exceptions.TestFail("Core status pattern are different than expected")
        self._log.info("Core status pattern looks fine")

    def install_rdt(self):
        """
        Checks if the RDT is installed in sut, If not then it will install

        :return: None
        """
        pqos_cmd = "pqos -t 0"
        pqos_fail_msg = "pqos: command not found"
        pqos_fail_msg_centos = "pqos: error while loading shared libraries"
        self._log.info("Verifying RDT is installed in sut by executing rdt command {}".format(pqos_cmd))
        result = self._os.execute(pqos_cmd, self._command_timeout)
        self._log.debug("pqos command output is '{},{}'".format(result.stdout, result.stderr))
        if result.stderr:
            if pqos_fail_msg in result.stderr or pqos_fail_msg_centos in result.stderr:
                self._log.debug("pqos command is not recognized, Installing RDT in sut")
                self.install_rdt_tool()
            else:
                raise content_exceptions.TestFail("Test case fail due to reason '{}'".format(result.stderr))
        else:
            self._log.info("RDT is already installed in sut")

    def verify_msr_tools(self):
        """
            Checks if the RDT is installed in sut, If not then it will install

            :return: None
            """
        msr_cmd = "rdmsr -p 0 0xd51"
        msr_fail_msg = "rdmsr: command not found"
        self._log.info("Verifying MSR is installed in sut")
        result = self._os.execute(msr_cmd, self._command_timeout)
        self._log.debug("rdmsr command output is '{},{}'".format(result.stdout, result.stderr))
        if result.stderr:
            if msr_fail_msg in result.stderr:
                self._log.debug("rdmsr command is not recognized, Installing RDT in sut")
                self.install_msr_tool()
            else:
                raise content_exceptions.TestFail("Test case fail due to reason '{}'".format(result.stderr))
        else:
            self._log.info("RDT is already installed in sut")

    def execute_pqos_cmd(self, pqos_command_list):
        """
        This method takes the command to execute as a list and checks if any error or warnings are found
        in the output.

        :param pqos_command_list: pqos commands to execute in sut.
        :return: None
        """
        for cmd_item in pqos_command_list:
            self._log.info("Executing command '{}' to check for any error".format(cmd_item[0]))
            command_result = self._common_content_lib.execute_sut_cmd(cmd_item[0], cmd_item[1], self._command_timeout)
            self._log.debug("Output of command '{}' is '{}'".format(cmd_item[0], command_result))
            for string_item in self.ERROR_LIST:
                if string_item in command_result.lower():
                    raise content_exceptions.TestFail("Error found in result {}".format(command_result))

            self._log.info("No error were found by executing command '{}'".format(cmd_item[0]))

    def check_all_cos_val(self, cos_dict, expect_cos_val):
        """
        This method checks for COS definition mask values for all available sockets

        :param cos_dict: Dictionary which contains all COS definition and mask values for all available sockets
        :param expect_cos_val: expected value for all COS definition
        :raise: Content_exception if expected mask value match is not found
        :return: None
        """
        for k, v in cos_dict.items():
            if isinstance(v, dict):
                self.check_all_cos_val(v, expect_cos_val)
            else:
                if cos_dict[k] != expect_cos_val:
                    raise content_exceptions.TestFail("COS Value is not matching as expected, Expected is {} and "
                                                      "got {}".format(expect_cos_val, cos_dict[k]))
                self._log.debug("Verified successfully, Expected for COS {} is {} and got {} "
                                "".format(k, expect_cos_val, cos_dict[k]))

    def get_cos_definition_dictionary(self, l3ca_command_result):
        """
        This method takes input for command pqos -s and returns a dictionary which contains all COS
        definitions as key and mask value as values for all sockets.

        :return: Dictionary of all COS definitions for all sockets
        """
        cos_definition_dict = {}
        socket = ""
        cos_definition_str = "L3CA/MBA COS definitions"
        l3ca_str = "L3CA"
        mask_str = "MASK"
        l3ca_command_result_list = l3ca_command_result.split("\n")
        for command_line in l3ca_command_result_list:
            if cos_definition_str in command_line:
                socket = re.search(self.GET_SOCKET_REGEX, command_line, re.IGNORECASE).group(1).strip()
                cos_definition_dict[socket] = {}
            elif l3ca_str in command_line and mask_str in command_line:
                cos_definition_dict[socket][(re.search(self.COS_REGEX, command_line))[0].strip()] = \
                    (re.search(self.MASK_VAL_REGEX, command_line)).group(1).strip()
        self._log.debug("All COS definitions with mapped mask value is {}".format(cos_definition_dict))

        return cos_definition_dict

    def verify_l3ca_cos_definitions_for_input_socket(self, l3ca_cos_command_result, mask_val, cos_num=None,
                                                     socket_num=""):
        """
        This method checks the COS value for input socket. If cos_num is none it checks mask value
        for all COS definitions for the input socket.

        :param l3ca_cos_command_result: pqos -s command output
        :param mask_val: expected COS mask value
        :param cos_num: COS number to be verified
        :param socket_num: socket number if any specific

        :raise: Content_exception if mask value match is not found
        :return: None
        """
        self._log.info("Verifying mask value of COS definitions for socket {}".format(socket_num))
        cos_definition_dict = self.get_cos_definition_dictionary(l3ca_cos_command_result)
        if not cos_num:
            self.check_all_cos_val(cos_definition_dict[socket_num], mask_val)
            self._log.info("All cos values are matching as {}".format(mask_val))
        else:
            if cos_definition_dict[socket_num].get(cos_num) != mask_val:
                raise content_exceptions.TestFail("COS Value is not matching as expected, Expected is {} and got "
                                                  "{}".format(mask_val,
                                                              cos_definition_dict[socket_num].get(cos_num)))
            self._log.info("Verified successfully, Expectation for {} is {} for socket {} and got {}"
                           "".format(cos_num, mask_val, socket_num, cos_definition_dict[socket_num].get(cos_num)))

    def verify_l3ca_cos_definitions_for_all_sockets(self, l3ca_cos_command_result, mask_val, cos_num=None):
        """
        This method checks the COS value for all available socket. If cos_num is none it checks mask value
        for all COS definitions.

        :param l3ca_cos_command_result: pqos -s command output
        :param mask_val: expected COS mask value
        :param cos_num: COS number to be verified

        :raise: Content_exception if mask value match is not found
        :return: None
        """
        self._log.info("Verifying mask value for COS definitions")
        cos_definition_dict = self.get_cos_definition_dictionary(l3ca_cos_command_result)
        if not cos_num:
            self.check_all_cos_val(cos_definition_dict, mask_val)
            self._log.info("All cos values are matching as {}".format(mask_val))
        else:
            for k, v in cos_definition_dict.items():
                if cos_definition_dict[k].get(cos_num) != mask_val:
                    raise content_exceptions.TestFail("COS Value not matching as expected, Expected is "
                                                      "{} and got {}".format(mask_val,
                                                                             cos_definition_dict[k].get(cos_num)))
                self._log.debug("Expectation for {} is {} for socket {} and got "
                                "{}".format(cos_num, mask_val, k, cos_definition_dict[k].get(cos_num)))
            self._log.info("All values are verified successfully")

    def restore_default_rdt_monitor(self, interface=None):
        """
        This method executes command pqos -R, which restores the rdt monitor to default.

        :param: interface if interface is true, changes the restore default command to pqos -R -I
        :raise: Content_exception if unable to find success info message while doing rdt monitor to default
        :return: None
        """
        command_to_exec = self.INTERFACE_CMD if interface else self.RESTORE_DEFAULT_CMD
        self._log.info("Restoring default monitor by executing rdt restore command {}".format(command_to_exec))
        unmatched_value = self._common_content_lib.execute_cmd_and_get_unmatched_result(command_to_exec,
                                                                                        self.RESTORE_CMD_INFO,
                                                                                        self.RESTORE_SUCCESSFUL_INFO,
                                                                                        self._command_timeout)
        if unmatched_value:
            raise content_exceptions.TestFail("Failed to restore RDT default monitor")
        self._log.info("RDT monitor is restored to default")

    def run_l3ca_cmd_and_verify_default_cos_val(self):
        """
        This method run pqos -s command and verifies the COS definition mask value is default value (0xfff)

        :return: None
        """
        self._log.info("Executing command {}".format(self.CHECK_L3CA_CMD))
        l3ca_command_result = self._common_content_lib.execute_sut_cmd(self.CHECK_L3CA_CMD, self.L3CA_CMD_INFO,
                                                                       self._command_timeout)
        self._log.debug("Output of the command '{} is '{}".format(self.CHECK_L3CA_CMD, l3ca_command_result))
        self.verify_l3ca_cos_definitions_for_all_sockets(l3ca_command_result, self.default_cos_val)

    def change_bit_mask_value(self, bit_mask_cmd):
        """
        This method runs the command pqos -e and changes the mask value of COS definitions.

        :param bit_mask_cmd: pqos -e command output
        :raise: Content_exception if fails to change the bit mask value
        :return: returns result of pqos -e command
        """
        self._log.info("Executing command {} to change mask values".format(bit_mask_cmd))
        bit_mask_result = self._common_content_lib.execute_sut_cmd(bit_mask_cmd, self.CHANGE_BIT_MASK_INFO,
                                                                   self._command_timeout)

        if not re.search(self.BIT_MASKING_SUCCESSFUL_INFO, bit_mask_result):
            raise content_exceptions.TestFail("Failed to change the mask value, Result is {}:".format(bit_mask_result))

        self._log.debug("Bit Mask value command {} output is {}".format(bit_mask_cmd, bit_mask_result))
        self._log.debug("Bit masking is successful")

        return bit_mask_result

    def verify_bit_mask_value(self, bit_mask_cmd_res, interface=None):
        """
        This method verifies the mask value is changed after running pqos -e command, the mask value is checked by
        running pqos -s command.

        :param bit_mask_cmd_res: pqos -e command output
        :param: interface if interface is true, changes the command to be executed to "pqos -s -I"
        :return: None
        """
        # Check allocation is done to all COS Successfully
        command_to_exec = RdtUtils.CHECK_L3CA_CMD
        if interface:
            command_to_exec = RdtUtils.INTERFACE_L3CA_CMD
        self._log.info("Verifying the mask value is changed for COS definitions after running pqos -e command")
        command_result = self._common_content_lib.execute_sut_cmd(command_to_exec, RdtUtils.L3CA_CMD_INFO,
                                                                  self._command_timeout)
        self._log.debug("Output of the command '{} is '{}".format(command_to_exec, command_result))
        for line in bit_mask_cmd_res.split("\n"):
            if RdtUtils.SOCKET_STR in line:
                self.verify_l3ca_cos_definitions_for_input_socket \
                    (command_result, (re.search(RdtUtils.MASK_VAL_REGEX, line)).group(1).strip(), cos_num=(re.search(
                        RdtUtils.COS_REGEX, line))[0].strip(),
                     socket_num=(re.search(RdtUtils.GET_SOCKET_REGEX, line, re.IGNORECASE)).group(1).strip())

    def execute_rdt_monitoring_cmd(self, rdt_monitor_cmd):
        """
        Turn on RDT monitoring to view the core status for 10 second.

        :param rdt_monitor_cmd: rdt monitor command pqos -m 'all:0,1,2,3' -t 10
        :return: returns command output
        """
        self._log.info("Turning on RDT monitor")

        command_result = self._common_content_lib.execute_sut_cmd(rdt_monitor_cmd, "rdt monitoring cmd",
                                                                  self._command_timeout)
        self._log.debug("Output of the command '{} is '{}".format(rdt_monitor_cmd, command_result))
        return command_result

    def collect_rdt_monitored_events(self, start_core_val=None, end_core_val=None, pqos_cmd=None, stress=False):
        """
        This method executes the pqos command to collect RDT event statistics for the input core ranges.

        :param start_core_val: core range start value
        :param end_core_val: core range end value
        :param pqos_cmd: pqos command to execute
        :param stress: true if statistic result is needed while stress is running
        :return: RDT events statistic result
        """
        if not pqos_cmd:
            pqos_cmd = self.PQOS_CMD
        self._log.info("Collecting RDT Event statistic by running command".format(pqos_cmd))
        event_result = self._common_content_lib.execute_sut_cmd(pqos_cmd, pqos_cmd, self._command_timeout)
        self._log.debug("Event result is '{}'".format(event_result))
        if stress:
            event_df = self.collect_rdt_statistic_data(event_result, stress_run=True)
        else:
            event_df = self.collect_rdt_statistic_data(event_result)

        if end_core_val:
            event_df = event_df.loc[(event_df[self.EVENT_CORE] >= int(start_core_val)) & (event_df[self.EVENT_CORE] <=
                                                                                          int(end_core_val))]
        self._log.debug("RDT Event statistic is {}".format(event_df))

        return event_df

    def strip_data(self, event_data):
        """ Get the event result and strips K from the MISSES column

        :param event_data: event monitoring data result
        :return: return the event data by string k from MISSES column
        """
        event_data.loc[:, self.EVENT_MISS] = event_data[self.EVENT_MISS].apply(lambda x: int(x.strip("k")))

        return event_data

    def get_time_index(self, event_output):
        """This method takes event output and returns the index of TIME string

        :param event_output: event monitoring data result
        :return: return list of indices of TIME
        """
        return [index for index, data in enumerate(event_output.split("\n")) if re.search(self.TIME_STR, data)]

    def collect_rdt_statistic_data(self, event_result, stress_run=False):
        """
        This method get the collects the event data while stress is running

        :param event_result: event monitoring data result
        :param stress_run: True if stress is running
        :return: Actual stress data
        """
        time_index = self.get_time_index(event_result)
        time_index.append(len(event_result.split("\n")) - 1)
        monitor_data = pd.DataFrame()
        for first, second in zip(time_index, time_index[1:]):
            event_res = "\n".join(event_result.split("\n")[first:second])
            data = self.strip_data(self.__parse_monitoring_data(event_res))
            if stress_run:
                monitor_data = self.get_max_data(monitor_data, data)
            else:
                monitor_data = self.get_min_data(monitor_data, data)

        return monitor_data

    def get_max_data(self, event_df_new, event_df_old):
        """
        This method get the maximum value from input data frames

        :param event_df_new: event monitoring data result 1
        :param event_df_old: event monitoring data result 2
        :return: Actual stress data
        """

        if event_df_new.empty:
            return event_df_old
        for event_col in self.RDT_EVENT_PARAMETERS_LIST:
            # create new column in df1 to check if value match
            event_df_new[event_col] = np.where(event_df_new[event_col] > event_df_old[event_col],
                                               event_df_new[event_col], event_df_old[event_col])
        return event_df_new

    def get_min_data(self, event_df_new, event_df_old):
        """
        This method get the minimum value from input data frames

        :param event_df_new: event monitoring data result 1
        :param event_df_old: event monitoring data result 2
        :return: Actual default data
        """

        if event_df_new.empty:
            return event_df_old
        for event_col in self.RDT_EVENT_PARAMETERS_LIST:
            # create new column in df1 to check if value match
            event_df_new[event_col] = np.where(event_df_new[event_col] < event_df_old[event_col],
                                               event_df_new[event_col], event_df_old[event_col])
        return event_df_new

    def check_rdt_event_statistics_increased(self, data_without_stress, data_with_stress):
        """
        This Function compares two data frames of rdt event values and checks whether
        event values increased after running stress.

        :param data_without_stress: rdt monitoring data with normal condition(without stress)
        :param data_with_stress: rdt monitoring data while running stress
        :raise: Content_exception RDT events values are not increased after running stress
        :return: None
        """
        self._log.info("Comparing values before and after running stress tool")

        for each_event in self.RDT_EVENT_PARAMETERS_LIST:
            if each_event == "MBL[MB/s]":
                if data_without_stress[each_event].mean() > data_with_stress[each_event].mean():
                    raise content_exceptions.TestFail("Event {} values are not increased after starting stress".format(each_event))

        self._log.info("All RDT event values are significantly increased after starting stress")

    def check_rdt_event_statistics_decreased(self, data_with_stress, data_without_stress):
        """
        This Function compares two data frames of rdt monitored event values and checks
        event values decreased after stopping stress

        :param data_with_stress: rdt monitoring data while running stress
        :param data_without_stress: rdt monitoring data after stopping stress
        :raise: Content_exception RDT events values are not decreased after stopping stress
        :return: None
        """
        self._log.info("Comparing values after stopping stress")
        for each_event in self.RDT_EVENT_PARAMETERS_LIST:
            if each_event == "MBL[MB/s]":
                if data_without_stress[each_event].mean() > data_with_stress[each_event].mean():
                    raise content_exceptions.TestFail("Event {} values are not increased after starting stress".format(each_event))

        self._log.info("All RDT event values are significantly decreased after stopping stress")

    def write_read_msr(self, READ_MSR_VALUES=None):
        """
        This function write and read values greater than or equal to 10 and less than 39 into MSR
        :param READ_MSR_VALUES:
        :return: READ_MSR_VALUES (List containing read values)
        """
        for register_value in self.REGISTER_VALUES:
            for msr_value in self.MSR_VALUES:
                WRITE_MSR_CMD = "wrmsr -p 0 {} {}".format(register_value, msr_value)
                self._os.execute(WRITE_MSR_CMD, self._command_timeout)
                READ_MSR_CMD = "rdmsr -p 0 {}".format(register_value)
                READ_MSR_VALUES.append(self._common_content_lib.execute_sut_cmd(READ_MSR_CMD, "Reading MSR Values",
                                                                                self._command_timeout))
        return [READ_MSR_VALUES[i: i + len(self.MSR_VALUES)] for i in
                range(0, len(READ_MSR_VALUES), len(self.MSR_VALUES))]

    def compare_write_read_msr(self, PARSE_MSR_VALUES):
        """
        Compare the output of read mba msr values with expected values.
        Raise exception if any read msr value not match the expected output value
        """
        # self.PARSE_MSR_VALUES = PARSE_MSR_VALUES
        self._log.info(PARSE_MSR_VALUES)
        if not all(i.strip() == self.EXPECTED_OUTPUT_VALUES[0] for i in PARSE_MSR_VALUES[0:2]) or \
                not all(i.strip() == self.EXPECTED_OUTPUT_VALUES[1] for i in PARSE_MSR_VALUES[3:5]) or \
                not all(i.strip() == self.EXPECTED_OUTPUT_VALUES[2] for i in PARSE_MSR_VALUES[6:8]):
            raise content_exceptions.TestFail("Output {} did not match the expected output values {}".format(
                PARSE_MSR_VALUES, self.EXPECTED_OUTPUT_VALUES))

    def verify_node0(self):
        """
        This method Checks available memory nodes on the system and verifies if node 0 is available

        :raise: Content_exception if node 0 is not present
        """
        self._log.info("Checking available memory nodes on the system")
        self._install_collateral.yum_install(self.PACKAGE_NUMACTL)
        unmatched_value = self._common_content_lib.execute_cmd_and_get_unmatched_result(self.NUMACTL_CMD,
                                                                                        self.NUMACTL_CMD,
                                                                                        self.EXPECTED_NODE_STR,
                                                                                        self._command_timeout)
        if unmatched_value:
            raise content_exceptions.TestFail("{} did not find in the {} output".format(unmatched_value,
                                                                                        self.NUMACTL_CMD))
        self._log.info("{} is available".format(self.EXPECTED_NODE_STR))

    def stop_memtester_tool(self):
        """
        This method stop the stress tool running on system by killing the stress process
        """
        self._log.info("Stopping memtester tool running on system")
        self._common_content_lib.execute_sut_cmd(self.KILL_MEMTESTER_CMD, self.KILL_MEMTESTER_CMD,
                                                 self._command_timeout)
        self._log.info("Memtester tool is stopped successfully")

    def verify_l3ca_rdt_capability_detection(self, expected_messages):
        """
        This method run pqos -s -v command and verifies L3 CAT capability is detected on platform

        :param expected_messages: string which is expected to be in pqos -s -v output
        :return: None
        """
        self._log.info("Executing command {}".format(self.CHECK_L3CA_VERBOSE))
        l3ca_command_result = self._common_content_lib.execute_sut_cmd(self.CHECK_L3CA_VERBOSE, self.L3CA_CMD_INFO,
                                                                       self._command_timeout)
        self._log.debug("Output of the command '{} is '{}".format(self.CHECK_L3CA_VERBOSE, l3ca_command_result))
        if any(message not in l3ca_command_result for message in expected_messages):
            raise content_exceptions.TestFail("{} not found in the {} output".format(expected_messages,
                                                                                     l3ca_command_result))

        self._log.info("L3 CAT capability is detected on platform")

    def check_allocation_config_error(self, bit_mask_cmd):
        """
        This method runs the command pqos -e and changes the mask value of COS definitions and
        checks if error appears in the command output.

        :param bit_mask_cmd: pqos -e command output
        :raise: Content_exception if failed to get the error
        :return: returns result of pqos -e command
        """
        self._log.info("Executing command {} to change mask values".format(bit_mask_cmd))
        bit_mask_result = self._os.execute(bit_mask_cmd, self._command_timeout)
        self._log.debug(
            "{} Command output is {},{}".format(bit_mask_cmd, bit_mask_result.stdout, bit_mask_result.stderr))
        if bit_mask_result.stdout and self.BIT_MASKING_ERROR_INFO in bit_mask_result.stdout:
            self._log.debug("Output: %s", bit_mask_result.stdout)
            self._log.error("Error: %s", bit_mask_result.stderr)
            if self.BIT_MASKING_ERROR_INFO not in bit_mask_result.stdout:
                raise content_exceptions.TestFail(
                    "Expected '| Allocation configuration error' but could not see it while setting COS bitmask more "
                    "than 28 bits")

    def verify_mba_capability(self):
        """
        This function verifies MBA Capability

        :raise: raise exception if MBA capability fails to detect.
        """
        self._log.info("Verifying MBA capability is detected on platform {}".format(self.VERIFY_MBA_CAPABILITY))
        command_result = self._common_content_lib.execute_cmd_and_get_unmatched_result(self.VERIFY_MBA_CAPABILITY,
                                                                                       self.MBA_CAPABILITY_INFO,
                                                                                       self.MBA_SUCCESFUL_INFO,
                                                                                       self._command_timeout)
        self._log.debug("MBA capability output is {}".format(command_result))
        if command_result:
            raise content_exceptions.TestFail("{} did not find in the {} output".format(command_result,
                                                                                        self.VERIFY_MBA_CAPABILITY))
        self._log.info("Succesfully Detected MBA Capability")

    def set_mba_rate(self, cos_value, mba_rate, socket_num):
        """
        This function sets MBA rate

        :param cos_value: setting cos definition to percentage
        :param mba_rate : setting mba rate to cos value
        :param socket_num: number of sockets
        :return: True
        raise: content_exception.Test Fail
        """
        self._log.info("Executing command {} to change mask values".format(self.CHANGE_BIT_MASK_CMD.
                                                                           format(cos_value, mba_rate)))
        command_result = self._os.execute(self.CHANGE_BIT_MASK_CMD.format(cos_value, mba_rate), self._command_timeout)
        self._log.debug("MBA rate output is {},{}".format(command_result.stdout, command_result.stderr))
        if self.MBA_COS_OUT_OF_RANGE_INFO.format(cos_value) in command_result.stdout:
            self._log.info(self.MBA_COS_OUT_OF_RANGE_INFO.format(cos_value))
            return True
        if self.BIT_MASKING_SUCCESSFUL_INFO not in command_result.stdout:
            raise content_exceptions.TestFail(
                "Failed to change the mask value, Result is {}:".format(command_result.stdout))

        self._log.debug(
            "Bit masking is successful and output of the command '{} is '{}".format(self.CHANGE_BIT_MASK_CMD.
                                                                                    format(cos_value, mba_rate),
                                                                                    command_result.stdout))

        for socket in range(0, socket_num):
            if self.MBA_COS_RATE_SUCESS_INFO.format(socket, cos_value, mba_rate, mba_rate) not in command_result.stdout:
                raise content_exceptions.TestFail("Unable to set MBA COS Definition to 50%, '{}'".format(
                    self.MBA_COS_RATE_SUCESS_INFO.format(socket, cos_value, mba_rate, mba_rate)))
        self._log.info("MBA rate set Succesfully")
        return True

    def is_stress_running(self):
        """
        This method Checks if the stress tool is running on sut or not

        :raise: Content_exception if stress is not running on sut
        :return: True if stress running
        """
        self._log.info("Checking if stress tool is running in system")
        command_res = self._common_content_lib.execute_sut_cmd(self.CURR_PROCESS_RUNNING_CMD.format(self.STRESS_STR),
                                                               self.CURR_PROCESS_RUNNING_CMD.format(self.STRESS_STR),
                                                               self._command_timeout)

        self._log.debug("Current Process output is {}".format(command_res))
        stress_count = command_res.count(self.STRESS_STR)
        if stress_count <= 2:
            self._log.debug("Stress tool is not running on System")
            return False
        self._log.info("Stress tool is running on System")
        return True

    def stop_stress_tool(self):
        """
        This method stop the stress tool running on system by killing the stress process
        """
        self._log.info("Stopping stress tool running on system")
        self._common_content_lib.execute_sut_cmd(self.KILL_STRESS_CMD, self.KILL_STRESS_CMD, self._command_timeout)
        self._log.info("Stress tool is stopped successfully")

    def install_dep_packages(self, install_dep_packages, commands):
        """
        This function execute script to install dependency packages

        :param install_dep_packages: Directory where setup packages are present
        :param commands: Commands to perform setup of packages
        """

        install_dep_packages_cmd = "cd " + install_dep_packages + "/;"
        self._log.info("install_dep_packages_cmd {}".format(install_dep_packages_cmd + commands))
        self._common_content_lib.execute_sut_cmd(install_dep_packages_cmd + commands,
                                                 "Install dep packages", self._command_timeout)

    def run_multichase_on_core(self, taskset_cmd, zip_file_path, current_core):
        """
        This function run multichase command on associated cores using taskset
        :param taskset_cmd : Contains taskset command
        :param zip_file_path : Path where packages are contained
        :param current_core : Current core
        :return: result from taskset cmd
        """

        multichase_dir_path = self.find_package(zip_file_path, "multichase*").split("\n")[1]
        taskset_cmd_per_core = taskset_cmd.format(current_core)
        multichase_result = self._common_content_lib.execute_sut_cmd(taskset_cmd_per_core,
                                                                      "executing multichase",
                                                                      self._command_timeout,
                                                                      multichase_dir_path)
        self._log.debug("{} command output : {}".format(taskset_cmd_per_core,multichase_result))
        return multichase_result

    def associate_assign_cores(self, cores, zip_file_path):
        """
        This function assign cores to cos0 and cos1

        :param cores: values of core
        """
        multichase_result_list = []
        self._common_content_lib.execute_sut_cmd("pqos -a llc:0=0-0", "executing pqos", self._command_timeout)
        self._common_content_lib.execute_sut_cmd("pqos -a llc:1=1-" + cores, "executing pqos", self._command_timeout)
        for core in range(len(self.CLOS0_LLC_CBM)):
            clos0_output = self._common_content_lib.execute_sut_cmd(
                self.SET_CLOS_CMD.format(0, self.CLOS0_LLC_CBM[core]),
                "Configure CLOS[0] to have access to a single LLC CBM bit",
                self._command_timeout)
            self._log.debug(
                "{} Command output : {}".format(self.SET_CLOS_CMD.format(0, self.CLOS0_LLC_CBM[core]), clos0_output))
            clos1_output = self._common_content_lib.execute_sut_cmd(
                self.SET_CLOS_CMD.format(1, self.CLOS1_LLC_CBM[core]),
                "Configure CLOS[1] to have access to a single LLC CBM bit",
                self._command_timeout)
            self._log.debug(
                "{} Command output : {}".format(self.SET_CLOS_CMD.format(1, self.CLOS1_LLC_CBM[core]), clos1_output))
            result = self.run_multichase_on_core(self.TASKSET_MULTICHASE, zip_file_path, 0)
            self._log.debug("{} command output : {}".format(self.TASKSET_MULTICHASE,result))
            multichase_result_list.append(result)
            time.sleep(10)
        return multichase_result_list

    def find_package(self, zip_file_path, package):
        """
        This function find package directory and return the same
        :param zip_file_path: Folder path which contains packages for installation and
        :param package:  name to find particular package
        :return: package directory path
        """
        package_dir = "find " + zip_file_path + " -type d -name " + package
        package_dir_path = self._common_content_lib.execute_sut_cmd(package_dir,
                                                                    "find package", \
                                                                    self._command_timeout)
        return package_dir_path

    def verify_l3ca_capability(self, cdp_check=None, cdp="", interface=None):
        """
        This method run pqos -s -v command and verifies L3 CAT capability is detected on platform
        if cdp_check is True it verifies if L3 CDP capability is detected on platform.

        :param cdp_check: boolean
        :param cdp: "enabled" or "disabled" to check if cdp is enabled or disabled respectively.
        :return: None
        :raise : content_exceptions.TestFail if failed.
        """
        self._log.info("Executing command {}".format(self.CHECK_L3CA_VERBOSE))
        command_to_exec = self.CHECK_L3CA_VERBOSE
        if interface:
            command_to_exec = self.CHECK_L3CA_VERBOSE_INTERFACE

        l3ca_command_result = self._common_content_lib.execute_sut_cmd(command_to_exec, self.L3CA_CMD_INFO,
                                                                       self._command_timeout)
        self._log.debug("Output of the command '{} is '{}".format(self.CHECK_L3CA_VERBOSE, l3ca_command_result))
        if self.L3CA_SUCCESS_MESSAGE[0] not in l3ca_command_result:
            raise content_exceptions.TestFail("{} not found in the {} output".format(self.L3CA_SUCCESS_MESSAGE,
                                                                                     l3ca_command_result))
        if cdp_check:
            if self.L3CA_SUCCESS_MESSAGE[1] not in l3ca_command_result:
                raise content_exceptions.TestFail("{} not found in the {} output".format(self.L3CA_SUCCESS_MESSAGE,
                                                                                         l3ca_command_result))
            self._log.info("L3 CDP capability is detected on platform")
        if cdp == self.CDP_ENABLED:
            if self.CDP_TURNED_ON_MESSAGE[1] not in l3ca_command_result:
                raise content_exceptions.TestFail("{} not found in the {} output".format(self.CDP_TURNED_ON_MESSAGE[1],
                                                                                         l3ca_command_result))
            self._log.info(self.CDP_TURNED_ON_MESSAGE[1])
        elif cdp == self.CDP_DISABLED:
            if self.CDP_TURNED_OFF_MESSAGE[1] not in l3ca_command_result:
                raise content_exceptions.TestFail("{} not found in the {} output".format(self.CDP_TURNED_OFF_MESSAGE[1],
                                                                                         l3ca_command_result))
            self._log.info(self.CDP_TURNED_OFF_MESSAGE[1])

        self._log.info("L3 CAT capability is detected on platform")

    def set_platform_l3cdp(self, enable=True):
        """
        This method enables or disables L3 CDP capability on platform

        :param enable: boolean
        :raise : content_exceptions.TestFail if failed.
        """
        command_to_exec = self.L3_CDP_ENABLE_DISABLE.format(self.CDP_OFF)
        success_message = self.CDP_TURNED_OFF_MESSAGE
        if enable:
            command_to_exec = self.L3_CDP_ENABLE_DISABLE.format(self.CDP_ON)
            success_message = self.CDP_TURNED_ON_MESSAGE

        command_result = self._common_content_lib.execute_sut_cmd(command_to_exec, command_to_exec,
                                                                  self._command_timeout)
        self._log.debug("Output of the command '{} is '{}".format(command_to_exec, command_result))

        if success_message[0] in command_result or success_message[1] in command_result:
            self._log.info("{} found in the {} output".format(success_message, command_result))
        else:
            raise content_exceptions.TestFail("{} not found in the {} output".format(",".join(success_message),
                                                                                     command_result))

    def verify_l3ca_cat_cos_definitions(self, cmd, expected_result, no_of_sockets):
        """
        This method executes given cmd and verified L3 CAT COS definition is set for Code or Data based on the
        expected result

        :param cmd: command to be executed
        :param expected_result: Expected result to check from the command output
        :param no_of_sockets: integer - No of sockets in the system.
        :raise : content_exceptions.TestFail if failed.
        """
        expected_result = "SOCKET {} " + expected_result
        command_result = self._common_content_lib.execute_sut_cmd(cmd, cmd,
                                                                  self._command_timeout)
        self._log.debug("Output of the command '{} is '{}".format(cmd, command_result))

        for socket in range(0, no_of_sockets):
            regex_result = re.findall(expected_result.format(socket), command_result)
            if not regex_result:
                raise content_exceptions.TestFail("{} not found in the {} output".format(expected_result.format(socket),
                                                                                         command_result))
            self._log.info("{} found in {} output".format(regex_result, cmd))

    def verify_cmt_capability(self, command):
        """
        This method executes command and Verifies CMT capability is detected on platform

        :param : command to be execute for verifying cmt capabilities detected on the platform
        :raise: Content_exception if unable to find CMT capability message on platform
        :return: None
        """
        self._log.info("Verifying CMT capability is detected on platform by executing command {}".format(command))
        cmd_output = self._common_content_lib.execute_sut_cmd(command, command, self._command_timeout)
        self._log.debug("CMT Capability command output {}".format(cmd_output))
        regex_match_value = re.findall(self.CMT_EVENTS_PLATFORM, cmd_output)

        if not regex_match_value:
            raise content_exceptions.TestFail("{} did not find in the {} output".format(self.CMT_EVENTS_PLATFORM,
                                                                                        cmd_output))
        self._log.info("CMT capability is detected on platform")

    def check_cmt_event_core(self, pqos_cmd, core_value, event):
        """
        This method executes command and verifies CMT values for core and checks if all events have higher value for the
        core value

        :param : pqos_command-command to be execute for verifying CMT values for core
        :param : core_value - core number
        :param : event - list of event whose values to be verified if they are higher for core number
        :raise: Content_exception if values for all events are not higher for the core value
        :return: None
        """
        self._log.info("Collecting RDT Event statistic by running command".format(pqos_cmd))
        event_result = self._common_content_lib.execute_sut_cmd(pqos_cmd, pqos_cmd, self._command_timeout)

        # For collecting the last time stamp event values
        time_index = [index for index, data in enumerate(event_result.split("\n")) if re.search(self.TIME_STR, data)]
        event_result = "\n".join(event_result.split("\n")[time_index[-1]:])

        # Passing result to a data frame
        event_df = self.__parse_monitoring_data(event_result)
        event_df.loc[:, self.EVENT_MISS] = event_df[self.EVENT_MISS].apply(lambda x: int(x.strip("k")))

        self._log.debug("RDT Event statistic is {}".format(event_df))
        dict_max_value = {}
        self.CMT_EVENTS_PARAMAETRS_LIST = self.CMT_EVENT_PARAMETERS_LIST.extend(event)
        df_core_value = event_df[event_df[self.EVENT_CORE] == core_value]
        event_df.drop(event_df.index[event_df[self.EVENT_CORE] == core_value], inplace=True)
        for each_event in self.CMT_EVENT_PARAMETERS_LIST:
            if each_event != self.EVENT_CORE:
                dict_max_value[each_event] = event_df[each_event].max()
        self._log.debug("Dictionary of max values obtained from the dataframe {}".format(dict_max_value))
        self._log.debug("Dataframe of core {} {}".format(core_value, df_core_value))
        for event in self.CMT_EVENT_PARAMETERS_LIST[1:]:
            if not (dict_max_value[event] < df_core_value[event]).bool():
                raise content_exceptions.TestFail("The core {} value is not higher than other cores".format(core_value))
        self._log.debug("All the events are higher for core {}".format(core_value))

    def get_pid_value(self):
        """
        This method returns the pid_value while memtester process is in progress.

        :raise: Content_exception if Memtester process is not in progress
        :return: pid_value
        """
        pid_value = self._common_content_lib.execute_sut_cmd(self.PID_VALUE_CMD, self.PID_VALUE_CMD,
                                                             self._command_timeout)
        if not pid_value:
            raise content_exceptions.TestFail("Memtester process not started!!!")
        self._log.info("The Pid Value is {}".format(pid_value.strip()))
        return pid_value.strip()

    def check_cmt_event_taskid(self, cmt_task_cmd, task_id, event):
        """
        This method executes command and Verifies CMT values for task id

        :param : cmt_task_cmd - command to be execute for verifying CMT values for core
        :param : task_id - memtester pid value
        :param : event - list of event whose values to be verified if they are higher for memtester pid value
        :raise: Content_exception if LLC[KB] values is not higher for the task id
        :return: None
        """
        self._log.info("Collecting RDT Event statistic by running command".format(cmt_task_cmd))
        event_result = self._common_content_lib.execute_sut_cmd(cmt_task_cmd, cmt_task_cmd, self._command_timeout)

        # For collecting the last time stamp event values
        time_index = [index for index, data in enumerate(event_result.split("\n")) if re.search(self.TIME_STR, data)]
        event_result = "\n".join(event_result.split("\n")[time_index[-1]:])

        # Passing result to a data frame
        event_df = self.__parse_monitoring_data(event_result)
        event_df.loc[:, self.EVENT_MISS] = event_df[self.EVENT_MISS].apply(lambda x: int(x.strip("k")))

        self._log.debug("RDT Event statistic is {}".format(event_df))
        for each_event in event:
            event_max = event_df[each_event].max()
            self._log.debug("Maximum value of {} is {}".format(each_event, event_max))
            df_pid_value = event_df[event_df[self.PID] == int(task_id)]
            self._log.debug("RDT Event statistic {} is for task id {}".format(df_pid_value, task_id))
            if not (df_pid_value[each_event] == event_max).bool():
                raise content_exceptions.TestFail("The LLC {} value is not higher than other cores for task id {}".
                                                  format(event_max, df_pid_value[each_event]))
            self._log.info("The {} value {} is higher for PID value {}".format(each_event, event_max, task_id))

    def stop_memtester_tool(self):
        """
        This method stop the memtester tool running on system by killing the memtester process
        """
        self._log.info("Stopping memtester tool running on system")
        self._common_content_lib.execute_sut_cmd(self.KILL_MEMTESTER_CMD, self.KILL_MEMTESTER_CMD,
                                                 self._command_timeout)
        self._log.info("Memtester tool is stopped successfully")

    def restore_default_monitoring(self, interface=None):
        """
        This method executes command pqos -r, which restores the rdt monitor to default.

        :param: interface if interface is true, changes the restore default command to pqos -r -I
        :raise: Content_exception if failed to do default monitoring
        :return: None
        """
        command_to_exec = self.RESTORE_DEFAULT_MONITORING_CMD
        if interface:
            command_to_exec = ' '.join([self.RESTORE_DEFAULT_MONITORING_CMD, self.INTERFACE_OPTION])
        self._log.info("Restoring default monitor by executing rdt restore command {}".format(command_to_exec))
        command_result = self._common_content_lib.execute_sut_cmd(command_to_exec, "rdt default monitoring cmd",
                                                                  self._command_timeout)
        if not command_result:
            raise content_exceptions.TestFail("Failed to restore RDT default monitoring")
        self._log.debug("Output of the command '{} is '{}".format(command_to_exec, command_result))

    def check_allocation_config_error_for_unknown_pid(self, bit_mask_cmd):
        """
        This method runs the commandpqos -I -a pid:id=unknown_pid and changes the mask value of COS definitions and
        checks if error appears in the command output.

        :param bit_mask_cmd: pqos command to execute
        :raise: Content_exception if failed to get the error
        """
        self._log.info("Executing command {} to change mask values".format(bit_mask_cmd))
        bit_mask_result = self._os.execute(bit_mask_cmd, self._command_timeout)
        self._log.debug(
            "Command {} output : {},{}".format(bit_mask_cmd, bit_mask_result.stdout, bit_mask_result.stderr))
        if bit_mask_result.stdout:
            self._log.debug("Output: %s", bit_mask_result.stdout)
            self._log.debug("Error: %s", bit_mask_result.stderr)
            if self.UNKNOWN_PID_ERROR_INFO not in bit_mask_result.stdout:
                raise content_exceptions.TestFail(

                    "Expected '| {}' but could not see it while allocating COS with unknown pids".format(
                        self.UNKNOWN_PID_ERROR_INFO))
            self._log.info("Expected '{}' while allocating COS with unknown pids found and verified".format(
                self.UNKNOWN_PID_ERROR_INFO))
            "Expected '| {}' but could not see it while allocating COS with unknown pids".format(
                self.UNKNOWN_PID_ERROR_INFO)
            self._log.info("Expected '{}' while allocating COS with unknown pids found and verified".format(
                self.UNKNOWN_PID_ERROR_INFO))

    def verify_mbm_capability(self, mbm_capability_command):
        """
        This method executes command and Verifies MBM capability is detected on platform

        :param mbm_capability_command: command to be execute for verifying MBM capabilities detected on the platform
        :raise: Content_exception if unable to find MBM capability message on platform
        """
        start_info_search = "Memory Bandwidth Monitoring"
        end_info_search = "PMU events"
        expected_str = ["Total Memory Bandwidth", "Local Memory Bandwidth"]
        self._log.info(
            "Verifying MBM capability is detected on platform by executing command {}".format(mbm_capability_command))
        cmd_output = self._common_content_lib.execute_sut_cmd(mbm_capability_command, mbm_capability_command,
                                                              self._command_timeout)
        self._log.debug("MBM Capability command output {}".format(cmd_output))
        search_regex = r'(?=' + start_info_search + ').*?(?=' + end_info_search + ')'
        match_info = re.findall(search_regex, cmd_output, flags=re.S)
        if not match_info:
            raise content_exceptions.TestFail("Search expression {} is not found in result {}".format(search_regex,
                                                                                                      cmd_output))
        for each_data in expected_str:
            if each_data not in match_info[0]:
                raise content_exceptions.TestFail("MBM capability is not verified successfully")
        self._log.info("Verifying MBM capability is successful {} and {} are present".format(expected_str[0],
                                                                                             expected_str[1]))

    def get_membw_path(self):
        """
        This method returns the membw tool path in the sut.

        return : membw tool directory path
        """
        self._log.info("Find the membw Tool path in SUT")
        path = ""
        membw_exp_dir = "/tools/membw"
        find_membw_tool = "find {} | grep {}".format(RootDirectoriesConstants.LINUX_ROOT_DIR, membw_exp_dir)
        command_result = self._common_content_lib.execute_sut_cmd(find_membw_tool,
                                                                  "find membw path cmd", self._command_timeout,
                                                                  cmd_path=RootDirectoriesConstants.LINUX_ROOT_DIR)
        self._log.debug("find command output is :'{}'".format(command_result))
        for each_line in command_result.split("\n"):
            if membw_exp_dir in each_line:
                path = each_line
                break
        if not command_result:
            self._log.error("could not find the membw tool path reinstalling rdt")
            self.install_rdt_tool()
            path = self.get_membw_path()
        return path

    def check_cmd_running(self, cmd):
        """
        This method checks if the membw command is running currently in the SUT or not

        :param cmd: cmd which runs the benchmark instance
        :raise: Content_exception if stress tool isn't running
        """
        self._log.info("Check if {} is running currently".format(cmd))
        cmd = self.CURR_PROCESS_RUNNING_CMD.format("\"" + cmd + "\"")
        command_results = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._command_timeout)
        self._log.debug("{} command results : {}".format(cmd, command_results))
        if len(command_results.strip().split("\n")) > 1:
            self._log.info("{} is running in the system".format(cmd))
            return True

        log_error = "{} is not running in the system".format(cmd)
        self._log.error(log_error)
        raise content_exceptions.TestFail(log_error)

    def start_stress_tool(self, tool_path, cmd):
        """
        This method starts the membw stress tool in async mode for both cores

        :param tool_path: Path of directory where membw tool exists
        :param cmd: Command that needs to be executed..
        :raise: Content_exception if stress tool isn't running
        """
        self._log.info("Starting the stress tool")
        self._os.execute_async(cmd, cwd=tool_path)
        if self.check_cmd_running(cmd):
            self._log.info("The stress instance is running on given core successfully")
            return True
        log_error = "{} Failed to run on given core in the system".format(cmd)
        self._log.error(log_error)
        raise content_exceptions.TestError(log_error)

    def set_core_association(self, core0, core1):
        """
        Associate core 0 to CLOS[0] and core 1 to CLOS[1] using the following command:
        pqos -a 'llc:0=0;llc:1=1'

        :param core0: Core number from Socket
        :param core1: Core number from Socket
        :raise: Content_exception.TestError if failed
        """
        command = self.CORE_ASSOCIATION_CMD.format(core0, core1)
        self._log.info(
            "Associate core 0 to CLOS[0] and core 1 to CLOS[1] using the command: {}".format(command))
        command_results = self._common_content_lib.execute_sut_cmd(command,
                                                                   command, self._command_timeout)
        self._log.info("{} Command results : {}".format(command, command_results))

        if self.BIT_MASKING_SUCCESSFUL_INFO in command_results:
            self._log.info(
                "Successfully Associated cores {} to CLOS[0] and core {} to CLOS[1]".format(core0,core1))
            return True
        log_error = "Failed to Associate core 0 to CLOS[0] and core 1 to CLOS[1]"
        self._log.error(log_error)
        raise content_exceptions.TestError(log_error)

    def set_throttling(self, percentage, core, socket):
        """
        This method Sets CLOS[0] and CLOS[1] to given percentage of throttling.

        :param percentage: Integer that represents the percentage of throttling to be set
        :param core: 0 or 1 if 1 then Throttling percentage would be set to both CLOS[0] and CLOS[1]
        :param socket: Socket where it has to be set
        :raise: Content_exception.TestError if failed
        """
        self._log.info("Set CLOS[0] and CLOS[1] to {} percentage of throttling".format(percentage))
        if core:
            core0_cmd = self.MBA_CMD.format(socket, self.CORE0, percentage)
            core1_cmd = self.MBA_CMD.format(socket, self.CORE1, percentage)
            cmd = self.SET_THROTTLING_CMD.format(core0_cmd + ";" + core1_cmd)
        else:
            core0_cmd = self.MBA_CMD.format(socket, self.CORE0, percentage)
            cmd = self.SET_THROTTLING_CMD.format(core0_cmd)

        command_results = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._command_timeout)
        self._log.debug("command results : {}".format(command_results))
        if self.BIT_MASKING_SUCCESSFUL_INFO in command_results:
            if core:
                success_str1 = self.SUCCESSFULY_SET_THROTTLING_MESSAGE.format(socket, self.CORE1, percentage,
                                                                              percentage)
                if success_str1 in command_results:
                    self._log.info("Successfully Set CLOS[1] to {} percent throttling".format(percentage))
                else:
                    log_error = "{} notpresent in the {} cmd output".format(success_str1, cmd)
                    self._log.error(log_error)
                    raise content_exceptions.TestError(log_error)

            success_str0 = self.SUCCESSFULY_SET_THROTTLING_MESSAGE.format(socket, self.CORE0, percentage, percentage)
            if success_str0 not in command_results:
                log_error = "{} not present in the {} cmd output".format(success_str0, cmd)
                self._log.error(log_error)
                raise content_exceptions.TestError(log_error)
            self._log.info("Successfully Set CLOS[0] to {} percent throttling".format(percentage))

    def check_rdt_monitor_running_status(self, cmd):
        """
        This method checks if the given command is running in the system or not

        :param cmd: cmd is the command whose running status has to be check
        :raise: content_exceptions.TestError
        """
        self._log.info("checks if the command  {} is running in the system or not".format(cmd))
        command = self.CURR_PROCESS_RUNNING_CMD + " | grep '" + cmd + "'"
        command_results = self._common_content_lib.execute_sut_cmd(command, command, self._command_timeout)

        if len(command_results.split("\n")) <= 1:
            log_error = "{} is not running in the System".format(cmd)
            self._log.error(log_error)
            raise content_exceptions.TestError(log_error)
        self._log.info("{} is running in the System".format(cmd))
        return True

    def read_mbl_values_from_pqos(self, csv_file, host_path, cores=[], mbr=False):
        """
        This method reads the pqos_mon.csv file and returns the A list containing core0 MBL value and Core 1's MBL value

        :param csv_file: csv file path in SUT to be copied
        :param host_path: csv file path in host to be copied into
        :param cores: A list containing two cores from given socket
        :param mbr: if True it returns A list containing MBR value else MBL value
        :return: A list containing core0 MBL value and Core 1's MBL value
        """
        self._log.info("Copy pqos_mon.csv file to Host to read the data")
        # wait for 30 seconds before reading the csv file to fetch the consistent data.
        time.sleep(30)
        self._os.copy_file_from_sut_to_local(csv_file, host_path)
        df = pd.read_csv(host_path)
        self._log.debug("Data read from csv file : {}".format(df))
        if len(cores) == 1:
            # Fetch core 0 value from pqos output
            core0_df = df.loc[df[RDTConstants.RDT_CORE_STR] == int(cores[0])]
            core0_df = core0_df.iloc[[-1]]
            socket0_core0 = core0_df[RDTConstants.RDT_MBL_STR].tolist()[0]
            if mbr:
                socket0_core0 = core0_df[RDTConstants.RDT_MBR_STR].tolist()[0]
            return [socket0_core0]

        # Fetch core 0 value from pqos output
        core0_df = df.loc[df[RDTConstants.RDT_CORE_STR] == int(cores[0])]
        core0_df = core0_df.iloc[[-1]]
        core0 = core0_df[RDTConstants.RDT_MBL_STR].tolist()[0]

        # Fetch core 1 value from pqos output
        core1_df = df.loc[df[RDTConstants.RDT_CORE_STR] == int(cores[1])]
        core1_df = core1_df.iloc[[-1]]
        core1 = core1_df[RDTConstants.RDT_MBL_STR].tolist()[0]

        return [core0, core1]

    def run_pcm_tool(self, cmd, filename, host_path, cwd):
        """
        This method runs pcm tool for 30 seconds and returns the average memory [MB/s] data read from the file

        :param cmd : pcm command to be executed
        :param filename : filename where the output is to be saved.
        :param host_path : Host Path where the file has to be copied into
        :param cwd : PCM directory where the pcm command has to be executed.
        :return : Average of memory [MB/s] data value
        :raise : contentExceptions.TestError if failed
        """
        command = cmd.format(RootDirectoriesConstants.LINUX_ROOT_DIR + filename)
        # kill the pcm tool if its already running
        self._log.info("Stop the pcm tool if its already running")
        if self.check_cmd_running(command):
            self._os.execute_async(self.KILL_CMD.format(self.PCM_CHECK))
        self._log.info("Run command : {}".format(command))
        # Run the pcm command given in async mode
        self._log.debug("Run the pcm command {} in async mode".format(command))
        self._os.execute_async(command, cwd=cwd)
        if not self.check_cmd_running(command):
            raise content_exceptions.TestError("{} failed to execute".format(command))
        self._log.debug("wait for {} seconds".format(self.EXEC_TIME))
        time.sleep(self.EXEC_TIME)
        # check if the command is running and kill if its still running
        if self.check_cmd_running(command):
            self._os.execute_async(self.KILL_CMD.format(self.PCM_CHECK))
        # copy the csv file genrated from the command to Host for reading
        self._log.debug("copy the csv file generated from the {} to Host for reading".format(command))
        self._os.copy_file_from_sut_to_local(RootDirectoriesConstants.LINUX_ROOT_DIR + filename, host_path)
        # convert the data in csv format to a dataframe
        df = pd.read_csv(host_path, skiprows=3)
        self._log.debug("Data read from csv file : {}".format(df))
        # Return the average of Memory [MB/s]value from pcm output
        return sum(df['Memory']) / len(df['Memory'])

    def get_average_values_from_pqos(self, csv_file, host_path, mbl=True):
        """
        This method reads the pqos_mon.csv file and returns the last updated core 0 and core 1 MBL values

        :param csv_file: csv file path in SUT to be copied
        :param host_path: csv file path in host to be copied into
        :param mbl: if True it returns MBL average value else MBR average value
        :return: MBL[MB/s] average value
        """
        self._log.info("Copy pqos_mon.csv file to Host to read the data")
        time.sleep(self.EXEC_TIME)
        self._os.copy_file_from_sut_to_local(csv_file, host_path)
        # read the csv file content into a dataframe.
        df = pd.read_csv(host_path)
        self._log.debug("Data read from csv file : {}".format(df))
        # Fetch Required value from pqos output
        if mbl:
            return sum(df[RDTConstants.RDT_MBL_STR]) / len(df[RDTConstants.RDT_MBL_STR])
        if not mbl:
            return sum(df[RDTConstants.RDT_MBR_STR]) / len(df[RDTConstants.RDT_MBR_STR])

    def run_taskset_file(self, stream_file_path):
        """

        This method creates a sample file and pass stream command  and runs the file continuously
        :param stream_file_path:file path where stream tool exists on SUT
        """
        sample_file = "example.sh"
        touch_command = "touch {}".format(sample_file)
        self._log.info("Creating a sample file and sending the data into sample file")
        result = self._os.execute(touch_command, self._command_timeout, stream_file_path)
        if result.cmd_failed():
            raise content_exceptions.TestError("Failed to run the touch command {} with error {}".
                                               format(touch_command, result.stderr))
        input_file = ["./stream", "sh example.sh", " "]
        for each_line in input_file:
            echo_command = "echo {} >> {}".format(each_line, sample_file)
            self._os.execute(echo_command, self._command_timeout, stream_file_path)
        result = self._os.execute("cat {}".format(sample_file), self._command_timeout, stream_file_path)
        self._log.debug("Displays the data {}".format(result.stdout))
        self._os.execute("chmod 777 {}".format(sample_file), self._command_timeout, stream_file_path)

    def set_cache_to_core(self, clos1, clos2):
        """
          This method is used Allocate Cache memory to core 1 and Core 2

          :param clos1: Allocates cache memory to Clos1 Value
          :param clos2: Allocates cache memory to Clo2 Value
          :raise: Content_exception if string is not present
        """
        self._log.info("Allocating cache memory for '{}' to '{}'".format(self.VAL_OF_CORE, self.COS1_VALUE))
        cmd = self.ALLOCATE_CACHE_TO_CORE_CMD.format(clos1, self.VAL_OF_CORE)
        allocate_cache_to_core = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._command_timeout)
        self._log.debug("command output is:{}".format(allocate_cache_to_core))
        if self.ALLOCATION_SUCCESSFUL_INFO[0] not in allocate_cache_to_core:
            raise content_exceptions.TestFail("Failed to find the {} in {} output".format(
                self.ALLOCATION_SUCCESSFUL_INFO[0], allocate_cache_to_core))
        self._log.info("Allocating cache memory for '{}' to '{}'".
                       format(self.VALUES_OF_CORE2, self.COS2_VALUE))
        cmd = self.ALLOCATE_CACHE_TO_CORE2_CMD.format(clos2, self.VALUES_OF_CORE2)
        allocate_cache_to_core2 = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._command_timeout)
        self._log.debug("command output is:{}".format(allocate_cache_to_core2))
        if self.ALLOCATION_SUCCESSFUL_INFO[0] not in allocate_cache_to_core2:
            raise content_exceptions.TestFail("Failed to find the {} in {} output".format(
                self.ALLOCATION_SUCCESSFUL_INFO[0], allocate_cache_to_core2))

    def allocate_core1_core2_with_cos_values(self, cos_value1, cos_value2, llc_allocation1, llc_allocation2):
        """
        This method is used to allocate cos values to core 1 & core 2 to have
        access to entire LLC CBM bit.

        :param cos_value1:Allocates Cos values to Core1
        :param cos_value2:Allocates Cos values to Core2
        :param llc_allocation1:Allocates core values to LLC
        :param llc_allocation2:Allocates core values to LLC
        :raise: Content_exception if string is not present
        """
        self._log.info("Allocating Cos values to Core 1")
        cmd = self.SET_COS1_TO_LLC_CBM_BIT.format(llc_allocation1, cos_value1)
        assign_cos_values_to_core1 = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._command_timeout)
        self._log.info("Assigning cos values {} to core 1 was successful".format(cos_value1))
        self._log.debug("command output is:{}".format(assign_cos_values_to_core1))
        if self.ALLOCATION_SUCCESSFUL_INFO[0] not in assign_cos_values_to_core1:
            raise content_exceptions.TestFail("Failed to find the {} in {} output".format(
                self.ALLOCATION_SUCCESSFUL_INFO[0], assign_cos_values_to_core1))
        self._log.info("Assigning Cos values to Core2 to have access to entire LLC CBM Bit")
        cmd = self.SET_COS2_TO_ENTIRE_LLC_BIT.format(llc_allocation2, cos_value2)
        assign_cos_values_to_core2 = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._command_timeout)
        self._log.debug("command output is:{}".format(assign_cos_values_to_core2))
        if self.ALLOCATION_SUCCESSFUL_INFO[0] not in assign_cos_values_to_core2:
            raise content_exceptions.TestFail("Failed to find the {} in {} output".format(
                self.ALLOCATION_SUCCESSFUL_INFO[0], assign_cos_values_to_core2))
        self._log.info("Assigning cos Values {} to core2 was successful".format(cos_value2))

    def copy_and_read_csv_file(self, csv_file, host_path):
        """
        This method copies the pqos_mon.csv file from sut to host and read
         the pqos_mon.csv file and fetches the required values from pqos output  and
         returns  core 0, core 1,2,3,4,5, sum of both values

        :param csv_file: csv file path in SUT to be copied
        :param host_path: csv file path in host to be copied into
        :return:
        """
        self._log.info("Copy pqos_mon.csv file to Host to read the data")
        self._os.copy_file_from_sut_to_local(RootDirectoriesConstants.LINUX_ROOT_DIR + csv_file, host_path)
        df = pd.read_csv(host_path)
        df_core0 = df.loc[df[self.CORE_COL_NAME] == 0]
        df_core1 = df.loc[df[self.CORE_COL_NAME] == 1]
        df_core2 = df.loc[df[self.CORE_COL_NAME] == 2]
        df_core3 = df.loc[df[self.CORE_COL_NAME] == 3]
        df_core4 = df.loc[df[self.CORE_COL_NAME] == 4]
        df_core5 = df.loc[df[self.CORE_COL_NAME] == 5]

        df_core0 = df_core0.reset_index()[self.LLC_COL_NAME]
        df_core1 = df_core1.reset_index()[self.LLC_COL_NAME]
        df_core2 = df_core2.reset_index()[self.LLC_COL_NAME]
        df_core3 = df_core3.reset_index()[self.LLC_COL_NAME]
        df_core4 = df_core4.reset_index()[self.LLC_COL_NAME]
        df_core5 = df_core5.reset_index()[self.LLC_COL_NAME]

        df_multiple = df_core1 + df_core2 + df_core3 + df_core4 + df_core5
        df_sum = df_core0 + df_core1 + df_core2 + df_core3 + df_core4 + df_core5

        df_req = pd.merge(df_core0, df_multiple, right_index=True, left_index=True)
        df_req = pd.merge(df_req, df_sum, right_index=True, left_index=True)
        column_list = df_req.columns
        for each in column_list:
            ax = plt.gca()
            df_req.plot(y=each, kind='line', ax=ax)
        plt.savefig(self.log_dir + os.sep + self.GRAPH_FILENAME)

    def check_rdt_monitor_command_running_status(self, cmd):
        """
        This method checks if the given command is running in the system or not

        :param cmd: cmd is the command whose running status has to be check
        :raise: content_exceptions.TestError
        """
        self._log.info("checks if the command  {} is running in the system or not".format(cmd))
        command = self.CURR_PROCESS_RUNNING_CMD.format(cmd)
        command_results = self._common_content_lib.execute_sut_cmd(command, command, self._command_timeout)
        if command_results.count(cmd) <= 2:
            log_error = "{} is not running in the System".format(cmd)
            self._log.error(log_error)
            raise content_exceptions.TestError(log_error)
        self._log.info("{} is running in the System".format(cmd))
        return True

    def run_mlc_stress(self, mlc_tool_path, cmd):
        """
        This method runs the mlc command in the system and checks if i
        t ran successfully and returns the bandwidth obtained

        :param cmd: cmd is the command whose running status has to be check
        :param mlc_tool_path: MLC stress tool path in SUT.
        :raise: content_exceptions.TestError
        :returns : Bandwidth
        """
        self._log.info("Run Mlc stress tool in the system")
        find_cmd = "find $(pwd) -type d -name 'Linux'"
        mlc_tool_path_in_sut = (self._common_content_lib.execute_sut_cmd(find_cmd, find_cmd,self._command_timeout,
                                                                         cmd_path = mlc_tool_path)).strip()
        self._log.debug("mlc_tool_path == {}".format(mlc_tool_path_in_sut))
        command_results = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._command_timeout, cmd_path = mlc_tool_path_in_sut)
        if not command_results:
            log_error = "{} is not running in the System".format(cmd)
            self._log.error(log_error)
            raise content_exceptions.TestError(log_error)
        self._log.info("Command Output : {}".format(command_results))
        bandwidth = command_results.strip().split("\n")[-1]
        return bandwidth
