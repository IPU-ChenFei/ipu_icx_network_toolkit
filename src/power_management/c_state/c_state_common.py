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

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.provider.stressapp_provider import StressAppTestProvider


class CStateCommon(ContentBaseTestCase):
    """
    Base class for all C-State Test Cases.
    This base class covers below Test Case IDs.

    1. G55961
    2. TODO
    3. TODO
    """
    TURBOSTAT_KILL_COMMAND = "killall -9 turbostat"
    GET_CPU_PERCENTAGE_COMMAND = "cat /proc/loadavg"
    CPU_POWER_COMMAND = "cpupower {}"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file):
        super(CStateCommon, self).__init__(test_log, arguments, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._stress_tool = StressAppTestProvider.factory(test_log, cfg_opts, self.os)

    def execute_cpu_power_tool(self, command_param):
        """
        This function to execute cpupower tool with the given command.

        :param command_param: cpupower command param
        :return command_output_data: output data of 'cpupower monitor' command
        :raise: RuntimeError.
        """
        self._log.info("Executing cpu power tool")
        command_output_data = self._common_content_lib.execute_sut_cmd(self.CPU_POWER_COMMAND.
                                                                       format(command_param),
                                                                       "run cpupower {}".format(command_param),
                                                                       self._command_timeout)
        if command_output_data == "":
            raise RuntimeError("'cpupower {}' command output doesn't contain any data".format(command_param))
        self._log.info("Successfully ran cpupower tool with the output \n{}" .format(command_output_data))
        return command_output_data

    def parse_turbostat_data(self, turbostat_data):
        """
        This function to parse the output of TurboStat tool

        :param turbostat_data: output of TurboStat tool
        :return busy_data_list, busy_mhz_data_list: a tuple of data list of %Busy & %Busy_MHz
        """
        busy_data_list = []
        busy_mhz_data_list = []
        float_digit_regex = re.compile(r'\d+(\.\d+)?')
        try:
            turbostat_data_list = turbostat_data.split("\n")
            for i in turbostat_data_list:
                turbostat_data_list = i.split()
                if len(turbostat_data_list) != 0:
                    if float_digit_regex.match(turbostat_data_list[4]):
                        busy_data_list.append(float(turbostat_data_list[4]))
                    if float_digit_regex.match(turbostat_data_list[5]):
                        busy_mhz_data_list.append(float(turbostat_data_list[5]))
            return busy_data_list, busy_mhz_data_list
        except Exception as ex:
            self._log.error("Encountered an error {} while running the parse_turbostat_data function".format(ex))
            raise ex

    def parse_cpu_monitor_data(self, cpu_power_data):
        """
        This function to parse the output of 'cpupower monitor' command and return the system's c-state residency
        values.

        :param cpu_power_data: output string of 'cpupower monitor' command.
        :return required_data: a dictionary of c-state residency value lists.
        """
        required_data = {}
        try:
            cpu_power_data = cpu_power_data.strip().splitlines()
            heading_data = [item.strip() for item in cpu_power_data[1].split("|") if item.strip() != ""]
            for item in range(2, len(cpu_power_data)):
                values = [item.strip() for item in cpu_power_data[item].split("|") if item.strip() != ""]
                for element in range(len(values)):
                    if values[element].strip() != "":
                        if heading_data[element] not in required_data.keys():
                            required_data[heading_data[element]] = []
                        required_data[heading_data[element]].append(float(values[element]))
            self._log.debug("CPU power data dictionary: {}\n".format(required_data))
            return required_data
        except Exception as ex:
            self._log.error("Encountered an error {} while running the parse_cpu_monitor_data function".format(ex))
            raise ex

    def evaluate_expression(self, condition, c_state_counter_data_lists):
        """
        This function to verify the c state residency counters are High or Low according to the given condition param &
        threshold value

        :param c_state_counter_data_lists: c-state residency value lists.
        :param condition: condition with the threshold value
        :return invalid_matches: list of unmatched values
        """
        invalid_matches = []
        for value in c_state_counter_data_lists:
            if not eval(condition % value):
                invalid_matches.append(value)
        return invalid_matches

    def set_and_verify_bios_knobs(self, bios_config_file):
        """
        This method is to set and verify the BIOS knobs from the given bios config file

        param bios_config_file: bios config file to set the bios knobs
        :return: None
        """
        self.bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self.bios_util.set_bios_knob(bios_config_file=bios_config_file)  # To set the bios knob setting.
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)  # To apply the new bios setting.
        self.bios_util.verify_bios_knob(bios_config_file=bios_config_file)  # To verify the bios knob settings.
