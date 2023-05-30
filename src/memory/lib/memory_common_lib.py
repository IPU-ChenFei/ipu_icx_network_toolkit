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
import time
from datetime import datetime
from functools import reduce
import six

from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.lib.memory_constants import MemoryTopology

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

import pandas as pd

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.smbios_configuration import SMBiosConfiguration
from src.provider.memory_provider import MemoryProvider


class MemoryCommonLib:
    """
    Class is mainly used to parse different type of log files.
    """

    MEM_REGEX = r"Mem:\s*[0-9]*"
    SYSTEM_INFO_CMD = "Systeminfo"
    LINUX_PARTITION_CMD = "parted -s /dev/{0} mkpart {1} {2}{3} {4}{5}"
    LINUX_CMD_TO_CREATE_FILE_SYSTEM = "mkfs.{} -F {}"
    CMD_TO_GET_TOTAL_DISK_SIZE = r"parted -s /dev/{0} unit {1} print | grep '^Disk /dev/{2}:' | cut -f 3 -d ' '"
    CMD_TO_GET_THE_END_INDEX = r"parted -s /dev/{0} unit {1} print | tail -n2 | awk '{{print$3}}'"
    CMD_TO_GET_THE_PARTITION_NUMBER = r"ls -l /dev/{} | awk '{{print$6}}'"
    CMD_TO_DELETE_PARTITION = "parted -s /dev/{} rm {}"
    CMD_TO_GET_PARTITION_NUMBER = r"parted -s /dev/{} print | awk '{{print$1}}' | sed 's/[^0-9]*//g' | " \
                                  r"sed -r '/^\s*$/d'"
    CMD_TO_DISPLAY_DISK_INFORMATION = "parted -s /dev/{} unit GB print"
    PS_CMD_TO_CHECK_FILE_EXISTS_OR_NOT = "powershell Test-Path {}"
    FSUTIL_CMD_TO_CREATE_SPARSE_FILE = "fsutil file createnew {} {}"

    CMD_TO_CALCULATE_MD5_CHECKSUM_L = "md5sum {}"
    CMD_TO_CALCULATE_MD5_CHECKSUM_W = "certutil -hashfile {} md5"

    TEST_FILE_NAME = "5GB_TEST_FILE.txt"
    C_DRIVE_PATH = "C:\\"
    ROOT = "/root"
    COLD_REBOOT = "COLD_REBOOT"
    WARM_REBOOT = "WARM_REBOOT"
    S0_S5_S0 = "S0_S5_S0"
    POWER_CYCLE_STR = {"COLD_REBOOT": "cold_reboot_cycles",
                       "WARM_REBOOT": "warm_reboot_cycles",
                       "S0_S5_S0": "s0_s5_s0"}

    def __init__(self, log, cfg_opts, os_obj, number_of_cycle=0):
        self._log = log
        self._os = os_obj
        self._cfg_opts = cfg_opts
        self.sut_os = self._os.os_type
        self._number_of_cycle = number_of_cycle

        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()  # command timeout in seconds
        self._wait_time = self._common_content_configuration.make_filesystem_timeout()
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._stress_app_execute_time = self._common_content_configuration.memory_stress_test_execute_time()
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._mem_utilization = self._common_content_configuration.get_mem_utilization_percent()
        self._install_collateral = InstallCollateral(log, os_obj, cfg_opts)
        dmidecode_path = self._install_collateral.install_dmidecode()
        self._smbios_config = SMBiosConfiguration(log, os_obj, dmidecode_path)
        self._memory_provider = MemoryProvider.factory(log, cfg_opts=cfg_opts, os_obj=os_obj)
        self._post_mem_capacity = self._common_content_configuration.memory_bios_post_memory_capacity()
        self._dcpmm_mem_capacity = self._common_content_configuration.memory_bios_total_dcpmm_memory_capacity()
        self._variance_percent = float(self._common_content_configuration.get_memory_variance_percent())

    def parse_platform_log(self, log_path):
        """
        This function is used to parse the platform log.

        :log_path: Path of the log file to be parsed.
        :return: number of cycles ran.
        """
        platform_return_value = True
        num_of_cycle = self._number_of_cycle
        time_stamp_list = []
        time_delta_list = []
        platform_rebooter_file = log_path
        with open(platform_rebooter_file, "r+") as log_reboot_file_pointer:
            list_lines = log_reboot_file_pointer.readlines()
            for line in list_lines:
                match = re.match(r'\ABoot:', line)
                if match is not None:
                    matched_time_stamp = re.findall(r'\d{2}:\d{2}:\d{2}', line)[0]
                    matched_day_month = re.findall(r'\w{3}\s+\d+', line)[0]
                    matched_year = re.findall(r'2\d{3}', line)[0]
                    total_time_stamp = matched_day_month + " " + matched_year + " " + matched_time_stamp
                    time_stamp = datetime.strptime(total_time_stamp, '%b %d %Y %H:%M:%S')
                    time_stamp_list.append(time_stamp)
        for iterator in reversed(range(len(time_stamp_list))):
            time_delta = time_stamp_list[iterator] - time_stamp_list[iterator - 1]
            time_delta_list.append(time_delta)
        time_delta_list = time_delta_list[0:-1]
        avg_time_delta = reduce(lambda a, b: a + b, time_delta_list) / len(time_delta_list)
        threshold_time_floor, threshold_time_celling = (avg_time_delta - (avg_time_delta * .5)), (avg_time_delta +
                                                                                                  (avg_time_delta * .5))
        result = all(x > threshold_time_floor or x < threshold_time_celling for x in time_delta_list)
        if not result:
            self._log.error("Failure: As one or more cycle has been taken more time than the threshold time...")
            platform_return_value = False
        self._log.info("No error has been found in platform log file...")
        list_num_of_cycle = [int(number) for number in list_lines[-1].split() if number.isdigit()]
        executed_no_of_cycle = int(' '.join(map(str, list_num_of_cycle)))
        self._log.info("Executed test cycle(s): {}".format(executed_no_of_cycle))
        if int(num_of_cycle) != executed_no_of_cycle:
            self._log.error("Number of cycles executed is not matching with the configuration "
                            "that was set during the test...")
            platform_return_value = False
        if platform_return_value:
            self._log.info("Number of cycles executed is matching with the configuration "
                           "that was set during the test...")
        return platform_return_value

    def parse_log_for_error_patterns(self, log_path, encoding=None):
        """
        This function is used to parse the string pattern against the log.

        :log_path: Log file path
        :encoding: the encoding of the log file
        :return: False in case of any failure pattern is preset in the log else True
        """
        pattern_error_return_value = True
        log_file = log_path
        num_critical = 0
        re_critical = "(.*)({})(.*)".format(r"(^critical\s|\scritical\s)")
        num_hw_error = 0
        re_hw_error = "(.*)({})(.*)".format(r"(^Hardware Error\s|\sHardware Error\s)")
        num_un_correct_error = 0
        re_un_correct_error = "(.*)({})(.*)".format(r"(^Uncorrected error\s|\sUncorrected error\s)")
        num_correct_error = 0
        re_correct_error = "(.*)({})(.*)".format(r"(^Corrected error\s|\sCorrected error\s)")
        num_fatal = 0
        re_fatal = "(.*)({})(.*)".format(r"(^fatal\s|\sfatal\s)")
        num_ierr = 0
        re_ierr = "(.*)({})(.*)".format(r"(^IERR\s|\sIERR\s)")
        num_memory_error = 0
        re_memory_error = "(.*)({})(.*)".format(r"(^Memory\sError\s)")
        # SEL log will not generate if there were not ERROR reported, So to handle that this logic is required.
        if not os.path.exists(log_file):
            self._log.debug("{} file not present as no ERROR reported for the same".format(log_file))
            return pattern_error_return_value

        dict_list = ['critical', 'hardware', 'uncorrectable', 'correctable', 'fatal', 'ierr', 'memory']
        dict_error = {err_type: [] for err_type in dict_list}

        with open(log_file, "r+", encoding=encoding) as file_pointer:
            datafile = file_pointer.readlines()
            for line in datafile:
                if re.search(re_critical, line, re.IGNORECASE):
                    num_critical += 1
                    dict_error['critical'].append(line)

                if re.search(re_hw_error, line, re.IGNORECASE):
                    num_hw_error += 1
                    dict_error['hardware'].append(line)
                if re.search(re_un_correct_error, line, re.IGNORECASE):
                    num_un_correct_error += 1
                    dict_error['uncorrectable'].append(line)

                if re.search(re_correct_error, line, re.IGNORECASE):
                    num_correct_error += 1
                    dict_error['correctable'].append(line)

                if re.search(re_fatal, line, re.IGNORECASE):
                    num_fatal += 1
                    dict_error['fatal'].append(line)

                if re.search(re_ierr, line, re.IGNORECASE):
                    num_ierr += 1
                    dict_error['ierr'].append(line)

                if re.search(re_memory_error, line, re.IGNORECASE):
                    num_memory_error += 1
                    dict_error['memory'].append(line)

            if num_critical:
                self._log.error("The log file '{}' has reported '{}' critical errors...".format(log_file, num_critical))
                self._log.error("The errors are listed below.. \n {}".format(('\n'.join(dict_error['critical']))))

            if num_hw_error:
                self._log.error("The log file '{}' has reported '{}' hardware errors".format(log_file, num_hw_error))
                self._log.error("The errors are listed below.. \n {}".format(('\n'.join(dict_error['hardware']))))

            if num_un_correct_error:
                self._log.error("The log file '{}' has reported '{}' un-correctable errors...".
                                format(log_file, num_un_correct_error))
                self._log.error("The errors are listed below.. \n {}".format(('\n'.join(dict_error['uncorrectable']))))

            if num_correct_error:
                self._log.error("The log file '{}' has reported '{}' correctable errors...".format(log_file,
                                                                                                   num_correct_error))
                self._log.error("The errors are listed below.. \n {}".format(('\n'.join(dict_error['correctable']))))

            if num_fatal:
                self._log.error("The log file '{}' has reported '{}' fatal errors...".format(log_file, num_fatal))
                self._log.error("The errors are listed below.. \n {}".format(('\n'.join(dict_error['fatal']))))

            if num_ierr:
                self._log.error("The log file '{}' has reported '{}' IERR errors...".format(log_file, num_ierr))
                self._log.error("The errors are listed below.. \n {}".format(('\n'.join(dict_error['ierr']))))

            if num_memory_error:
                self._log.error("The log file '{}' has reported '{}' Memory errors...".format(log_file,
                                                                                              num_memory_error))
                self._log.error("The errors are listed below.. \n {}".format(('\n'.join(dict_error['memory']))))

            if num_critical or num_hw_error or num_un_correct_error or num_correct_error or num_fatal or num_ierr \
                    or num_memory_error:
                pattern_error_return_value = False

            if pattern_error_return_value:
                self._log.info("No error has been found in the log located in the below path \n '{}'..."
                               "".format(log_file))

            return pattern_error_return_value

    def check_memory_log(self, log_path):
        """
        This function is used to parse the memory log.

        :log_path: Log file path
        :return: False in Case of Critical Failures preset in the Log else True
        """
        memory_return_value = True
        memory_log_file = log_path
        result_memtotal = self.memtotal_verification(log=memory_log_file)
        result_memlog_params = self.verification_of_memlog_params(log=memory_log_file)
        if not result_memtotal or not result_memlog_params:
            memory_return_value = False

        if memory_return_value:
            self._log.info("Memory log has been passed without any errors...!")
        return memory_return_value

    def get_boot_index_and_memtotal(self, log):
        """
        To get the boot cycles index and memory total from memory log.

        :param log: log file path
        :return: boot index list, mem_total list
        """
        boot_list = []
        boot_index = []
        mem_total_list = []
        complete_list_final = []
        memory_log_file = log
        with open(memory_log_file, "r+") as memory_file_pointer:
            file_list_lines = memory_file_pointer.readlines()
            for line in file_list_lines:
                boot_handle = re.findall(r'Boot:.*', line)
                if boot_handle:
                    boot_value = boot_handle[0].split(":")[1].strip()
                    boot_list.append(boot_value)
                    boot_index.append(file_list_lines.index(line))

                    self._log.info("Boot Index {}".format(boot_value))
                mem_total_handle = re.findall(r'MemTotal:.*', line)
                if mem_total_handle:
                    mem_total_value = mem_total_handle[0].split(":")[1].strip()
                    mem_total_list.append(mem_total_value)
            boot_number = 0

            for i in boot_index:
                complete_list = ["Boot :" + str(boot_number), i]
                complete_list_final.append(complete_list)
                boot_number += 1

            self._log.info("Completed parsing the boot cycles {}".format(complete_list_final))
            return complete_list_final, mem_total_list

    def get_memory_log_values(self, start_index, stop_index, boot_index, log):
        """
        Function is make the data frame to parse the memory log.

        :param start_index: Index of the first boot
        :param stop_index: Index of the boot that used to compare against first boot
        :param boot_index: Index of boot
        :param log: log file path
        :return: data frame
        """
        handle_list = []
        dmi_list = []
        size_list = []
        locator_list = []
        flag = False
        memory_log_file = log
        with open(memory_log_file, "r+") as fp:
            for index, line in enumerate(fp):
                if start_index <= index <= stop_index:
                    handle_match = re.findall(r'Handle.*', line)  # Finding all the instances for Handle Param
                    if handle_match:
                        if ":" not in handle_match[0]:  # Removing the values of Array Handle
                            if flag:  # For Physical Memory Array values from each Boot
                                handle_value = handle_match[0].split(",")[0].split(" ")[1]
                                dmi_type = handle_match[0].split(",")[1].strip().split(" ")[2]
                                handle_list.append(handle_value)
                                dmi_list.append(dmi_type)
                            flag = True
                    size_match = re.findall(r'\tSize:.*', line)  # Finding all the instances for Size Param
                    if size_match:
                        size_value = size_match[0].split(":")[1].strip()
                        size_list.append(size_value)
                    locator_match = re.findall(r'\tLocator:.*', line)  # Finding all the instances for Locator Param
                    if locator_match:
                        locator_value = locator_match[0].split(":")[1]
                        locator_list.append(locator_value)
                elif index > int(stop_index):
                    break
        boot_details_df = pd.DataFrame({'Boot': boot_index, 'Handle': handle_list,
                                        'DMI Type': dmi_list, 'Locator': locator_list,
                                        'Size': size_list})
        return boot_details_df

    def verification_of_memlog_params(self, log):
        """
        To verify the memory log parameters.

        :param log: log file path
        :return: True if no errors on the log else false
        """
        memory_param_return_value = True
        memory_log_file = log
        complete_list_final = self.get_boot_index_and_memtotal(log=memory_log_file)[0]
        boot_index_number = 0
        flag = False
        template_data_frame = None
        for iteration in complete_list_final:
            end_index = 0
            start_index = complete_list_final[boot_index_number][1]
            boot_index = complete_list_final[boot_index_number][0].split(":")[1]
            if boot_index_number < len(complete_list_final) - 1:
                end_index = complete_list_final[boot_index_number + 1][1]
                boot_index_number += 1
            else:
                end_index = os.stat(memory_log_file).st_size  # capturing the last index of the file
            obtained_dataframe = self.get_memory_log_values(start_index, end_index, boot_index,
                                                            log=memory_log_file)  # getting the dataFramefor each Boot
            if flag:
                test_data_frame = obtained_dataframe.drop('Boot', axis=1)  # getting the dataFrame after the oth boot
                if not template_data_frame.equals(test_data_frame):
                    self._log.info(obtained_dataframe)
                    self._log.error("Found Error in Memory Log as Handle, Size and Locator values are "
                                    "Boot : %s" % boot_index)
                    memory_param_return_value = False
            else:
                self._log.info("Memory Log has been checked for Handle, Size and Locator values and they are "
                               "consistent through out the boot cycles.")
                template_data_frame = obtained_dataframe.drop('Boot',
                                                              axis=1)  # making the 0th Boot data to template data
                flag = True
        return memory_param_return_value

    def memtotal_verification(self, log):
        """
        To verify the total memory for the given log.

        :param log: log file path
        :return: True if total memory is verified successfully else false
        """
        memory_total_verify_return_value = True
        memory_log_file = log
        try:
            memtotal_value_list = self.get_boot_index_and_memtotal(log=memory_log_file)
            memtotal_without_unit = list(map(lambda x: int(x.split(" ")[0]), memtotal_value_list[
                1]))  # getting all the MemTotal Values in a list and typecasted it in int

            # for -1% variance
            threshold_memtotal_floor = (memtotal_without_unit[0] - (memtotal_without_unit[0] * 0.01))

            # for 1% variance
            threshold_memtotal_celling = (memtotal_without_unit[0] + (memtotal_without_unit[0] * 0.01))

            # comparing all the MemTotal values with the 2 threshold values
            comparision_result = all(threshold_memtotal_floor <= x <= threshold_memtotal_celling for x in
                                     memtotal_without_unit)
            if comparision_result:
                self._log.info("No error has been found while comparing the MemTotal values among boot cycles...")
            else:
                self._log.error("Raising the failure flag as value mismatch found in between the MemTotal values..")
                memory_total_verify_return_value = False

            return memory_total_verify_return_value
        except Exception as ex:
            self._log.error("Encountered an error {}, during verification of MemTotal: memtotal_verification".
                            format(ex))
            raise ex

    def memtotal_verification_windows(self, log):
        """
        To verify the total memory for the given log.

        :param log: log file path
        :return: True if total memory is verified successfully else false
        """
        memory_total_verify_return_value = True
        memory_log_file = log
        try:
            memtotal_value_list = self.get_boot_index_and_memtotal_windows(log=memory_log_file)
            memtotal_without_unit = list(map(lambda x: int(x.split(" ")[0]), memtotal_value_list[
                1]))  # getting all the MemTotal Values in a list and typecasted it in int

            # -1% variance
            threshold_memtotal_floor = (memtotal_without_unit[0] - (memtotal_without_unit[0] * 0.01))

            # +1% variance
            threshold_memtotal_celling = (memtotal_without_unit[0] + (memtotal_without_unit[0] * 0.01))

            # comparing all the MemTotal values with the 2 threshold values
            comparision_result = all(threshold_memtotal_floor <= x <= threshold_memtotal_celling for x in
                                     memtotal_without_unit)
            if comparision_result:
                self._log.info("No error has been found while comparing the MemTotal values among boot cycles...")
            else:
                self._log.error("Raising the failure flag as value mismatch found in between the MemTotal values..")
                memory_total_verify_return_value = False

            return memory_total_verify_return_value
        except Exception as ex:
            self._log.error(
                "Encountered an error {}, during verification of MemTotal: memtotal_verification".format(ex))
            raise ex

    def parse_memory_log_windows(self, log_path):
        """
        This function is used to parse the memory log.

        :log_path: Log file path
        :return: False in Case of Critical Failures preset in the Log else True
        """
        memory_return_value = True
        memory_log_file = log_path
        result_memtotal = self.memtotal_verification_windows(log=memory_log_file)
        result_memlog_params = self.verification_of_memlog_params_windows(log=memory_log_file)
        if not result_memtotal or not result_memlog_params:
            memory_return_value = False

        if memory_return_value:
            self._log.info("{} has been passed without any errors...!".format(log_path))
        return memory_return_value

    def get_boot_index_and_memtotal_windows(self, log):
        """
        To get the boot cycles index and memory total from memory log.

        :param log: log file path
        :return: boot index list, mem_total list
        """
        boot_list = []
        boot_index = []
        mem_total_list = []
        complete_list_final = []
        memory_log_file = log
        with open(memory_log_file, "r+", encoding="UTF-16") as memory_file_pointer:
            file_list_lines = memory_file_pointer.readlines()
            for line in file_list_lines:
                boot_handle = re.findall(r'.*boot:.*', line, re.IGNORECASE)
                if boot_handle:
                    boot_value = boot_handle[0].split(":")[1].strip()
                    boot_list.append(boot_value)
                    boot_index.append(file_list_lines.index(line))

                    self._log.info("Boot Index {}".format(boot_value))
                mem_total_handle = re.findall(r'Total Memory:.*', line)
                if mem_total_handle:
                    mem_total_value = mem_total_handle[0].split(":")[1].strip()
                    mem_total_list.append(mem_total_value)
            boot_number = 0

            for i in boot_index:
                complete_list = ["Boot :" + str(boot_number), i]
                complete_list_final.append(complete_list)
                boot_number += 1
            self._log.info("Completed parsing the boot cycles {}".format(complete_list_final))
            return complete_list_final, mem_total_list

    def get_memory_log_values_windows(self, start_index, stop_index, boot_index, log):
        """
        Function is make the data frame to parse the memory log.

        :param start_index: Index of the first boot
        :param stop_index: Index of the boot that used to compare against first boot
        :param boot_index: Index of boot
        :param log: log file path
        :return: data frame
        """
        capacity_list = []
        device_locator_list = []
        manufacture_list = []
        speed_list = []
        total_width_match_list = []
        configured_clock_speed_list = []
        part_number_list = []
        memory_log_file = log
        with open(memory_log_file, "r+", encoding="UTF-16") as fp:
            for index, line in enumerate(fp):
                if start_index <= index <= stop_index:

                    # Finding all the instances for device locator Param
                    device_locator_match = re.findall(r'Devicelocator.*', line)
                    if device_locator_match:
                        if ":" in device_locator_match[0]:  # Removing the values of Array Handle
                            device_locator_value = device_locator_match[0].split(":")[1]
                            device_locator_list.append(device_locator_value)

                    # Finding all the instances for Manufacturer Param
                    manufacture_match = re.findall(r'Manufacturer.*', line)
                    if manufacture_match:
                        if ":" in manufacture_match[0]:  # Removing the values of Array Handle
                            manufacture_match_value = manufacture_match[0].split(":")[1]
                            manufacture_list.append(manufacture_match_value)

                    # Finding all the instances for Speed Param
                    speed_match = re.findall(r'\ASpeed.*', line)
                    if speed_match:
                        if ":" in speed_match[0]:  # Removing the values of Array Handle
                            speed_match_value = speed_match[0].split(":")[1]
                            speed_list.append(speed_match_value)

                    # Finding all the instances for ConfiguredClockSpeed Param
                    configured_clock_speed_match = re.findall(r'ConfiguredClockSpeed.*', line)
                    if configured_clock_speed_match:
                        if ":" in configured_clock_speed_match[0]:  # Removing the values of Array Handle
                            configured_clock_speed_match_value = configured_clock_speed_match[0].split(":")[1]
                            configured_clock_speed_list.append(configured_clock_speed_match_value)

                    # Finding all the instances for TotalWidth Param
                    total_width_match = re.findall(r'TotalWidth.*', line)
                    if total_width_match:
                        if ":" in total_width_match[0]:  # Removing the values of Array Handle
                            total_width_match_match_value = total_width_match[0].split(":")[1]
                            total_width_match_list.append(total_width_match_match_value)

                    # Finding all the instances for Capacity Param
                    capacity_match = re.findall(r'Capacity.*', line)
                    if capacity_match:
                        if ":" in capacity_match[0]:  # Removing the values of Array Handle
                            capacity_value = capacity_match[0].split(":")[1]
                            capacity_list.append(capacity_value)

                    # Finding all the instances for PartNumber Param
                    part_number_match = re.findall(r'PartNumber.*', line)
                    if part_number_match:
                        if ":" in part_number_match[0]:  # Removing the values of Array Handle
                            part_number_match_value = part_number_match[0].split(":")[1]
                            part_number_list.append(part_number_match_value)

        boot_details_df = pd.DataFrame({'Boot': boot_index,
                                        "Devicelocator": device_locator_list,
                                        "Manufacturer": manufacture_list,
                                        "Speed": speed_list,
                                        "ConfiguredClockSpeed ": device_locator_list,
                                        "TotalWidth": total_width_match_list,
                                        "Capacity": capacity_list,
                                        "PartNumber": part_number_list})

        return boot_details_df

    def verification_of_memlog_params_windows(self, log):
        """
        To verify the memory log parameters.

        :param log: log file path
        :return: True if no errors on the log else false
        """
        memory_param_return_value = True
        memory_log_file = log
        complete_list_final = self.get_boot_index_and_memtotal_windows(log=memory_log_file)[0]
        boot_index_number = 0
        flag = False
        template_data_frame = None
        for iteration in complete_list_final:
            end_index = 0
            start_index = complete_list_final[boot_index_number][1]
            boot_index = complete_list_final[boot_index_number][0].split(":")[1]
            if boot_index_number < len(complete_list_final) - 1:
                end_index = complete_list_final[boot_index_number + 1][1]
                boot_index_number += 1
            else:
                end_index = os.stat(memory_log_file).st_size  # capturing the last index of the file
            # getting the dataFramefor each Boot
            obtained_dataframe = self.get_memory_log_values_windows(start_index, end_index, boot_index,
                                                                    log=memory_log_file)

            if flag:
                test_data_frame = obtained_dataframe.drop('Boot', axis=1)  # getting the dataFrame after the oth boot
                if not template_data_frame.equals(test_data_frame):
                    self._log.info(obtained_dataframe)
                    self._log.error("Found Error in Memory Log as Capacity , devicelocator are "
                                    "Boot : %s" % boot_index)
                    memory_param_return_value = False
            else:
                self._log.info("Memory Log has been checked for Devicelocator, Manufacturer,"
                               "Speed, ConfiguredClockSpeed, TotalWidth, Capacity ,PartNumber and they are "
                               "consistent through out the boot cycles.")
                template_data_frame = obtained_dataframe.drop('Boot',
                                                              axis=1)  # making the 0th Boot data to template data
                flag = True
        return memory_param_return_value

    def get_dcpmm_dirtyshutdown_log(self, start_index, stop_index, boot_index, log_file):
        """
        Function is make the data frame to the DCPMM DirtyShutDown log.

        :param start_index: Index of the first boot
        :param stop_index: Index of the boot that used to compare against first boot
        :param boot_index: Index of boot
        :param log_file: log file path
        :return: data frame
        """
        try:
            current_value = []
            dimmid = []
            type = []
            with open(log_file, "r", encoding="UTF-8") as file_pointer:
                for index, line in enumerate(file_pointer):
                    if start_index <= index <= stop_index:
                        match = re.findall("0x.*", line)
                        if match:
                            match_data = str(match[0]).split("|")
                            dimmid.append(match_data[0].strip())
                            type.append(match_data[1].strip())
                            current_value.append(match_data[2].strip())
                    elif index > int(stop_index):
                        break
            return pd.DataFrame({"Boot": boot_index, "DimmID": dimmid, "Type": type, "current_val": current_value})
        except Exception as ex:
            raise RuntimeError("Encountered an error '{}'".format(ex))

    def verification_of_dcpmm_dirtyshutdown_log(self, log_path):
        """
        Function to verify DCPMM Dirty Shutdown Log File

        :param log_path: log path of the DCPMM dirtyshutdown log file
        :return dcpmm_return_value: True on Success else False
        """
        dcpmm_return_value = True
        complete_list_final = self.get_boot_index(log=log_path)
        boot_index_number = 0
        flag = False
        template_data_frame = None
        for iteration in complete_list_final:
            end_index = 0
            start_index = complete_list_final[boot_index_number][1]
            boot_index = complete_list_final[boot_index_number][0].split(":")[1]
            if boot_index_number < len(complete_list_final) - 1:
                end_index = complete_list_final[boot_index_number + 1][1]
                boot_index_number += 1
            else:
                end_index = os.stat(log_path).st_size  # capturing the last index of the file
            obtained_dataframe = self.get_dcpmm_dirtyshutdown_log(start_index, end_index, boot_index,
                                                                  log_path)  # getting the data frame for each Boot

            if flag:
                test_data_frame = obtained_dataframe.drop('Boot', axis=1)  # getting the dataFrame after the oth boot
                if not template_data_frame.equals(test_data_frame):
                    self._log.error("Found Error in Boot {} and data is \n{}".format(boot_index, obtained_dataframe))
                    dcpmm_return_value = False
            else:
                self._log.info("DimmID, Type, CurrentValue, CurrentState are consistent through out the boot cycle.")
                template_data_frame = obtained_dataframe.drop('Boot',
                                                              axis=1)  # making the 0th Boot data to template data
                flag = True
        if dcpmm_return_value:
            self._log.info("Successfully verified DCPMM DirtyShutDown Log")
        return dcpmm_return_value

    def get_boot_index(self, log):
        """
        To get the boot cycles index from dcpmm log.

        :param log: log file path
        :return: boot index list, mem_total list
        """
        boot_list = []
        boot_index = []
        complete_list_final = []
        with open(log, "r+") as file_pointer:
            file_list_lines = file_pointer.readlines()
            for line in file_list_lines:
                boot_handle = re.findall(r'Boot:.*', line)
                if boot_handle:
                    boot_value = boot_handle[0].split(":")[1].strip()
                    boot_list.append(boot_value)
                    boot_index.append(file_list_lines.index(line))

                    self._log.info("Boot Index {}".format(boot_value))
            boot_number = 0

            for i in boot_index:
                complete_list = ["Boot :" + str(boot_number), i]
                complete_list_final.append(complete_list)
                boot_number += 1

            self._log.info("Completed parsing the boot cycles {}".format(complete_list_final))
            return complete_list_final

    def get_dcpmm_log(self, start_index, stop_index, boot_index, log_file):
        """
        Function is make the data frame to the DCPMM log.

        :param start_index: Index of the first boot
        :param stop_index: Index of the boot that used to compare against first boot
        :param boot_index: Index of boot
        :param log_file: log file path
        :return: data frame
        """
        try:
            dimmid = []
            dimm_capacity = []
            health_state = []
            action_required = []
            lock_state = []
            total_capacity = []
            memory_capacity = []
            app_direct_capacity = []
            un_configured_capacity = []
            inacessible_capacity = []
            reserved_capacity = []
            dev_regions = []
            size = []
            available_size = []
            type_1 = []
            iset_id = []
            persistence_domain = []
            with open(log_file, "r", encoding="UTF-8") as file_pointer:
                for index, line in enumerate(file_pointer):
                    if start_index <= index <= stop_index:
                        match = re.findall(r"^\s0x.*", line)
                        if match:
                            match_data = str(match[0]).split("|")
                            dimmid.append(match_data[0].strip())
                            dimm_capacity.append(match_data[1].strip())
                            health_state.append(match_data[2].strip())
                            action_required.append(match_data[3].strip())
                            lock_state.append(match_data[4].strip())
                            # fw_version.append(match_data[5].strip())
                        match = re.findall("^Capacity=.*", line)
                        if match:
                            total_capacity.append(match[0])

                        match = re.findall("^MemoryCapacity=.*", line)
                        if match:
                            memory_capacity.append(match[0])

                        match = re.findall("^AppDirectCapacity=.*", line)
                        if match:
                            app_direct_capacity.append(match[0])

                        match = re.findall("^UnconfiguredCapacity=.*", line)
                        if match:
                            un_configured_capacity.append(match[0])

                        match = re.findall("^InaccessibleCapacity=.*", line)
                        if match:
                            inacessible_capacity.append(match[0])

                        match = re.findall("^ReservedCapacity=.*", line)
                        if match:
                            reserved_capacity.append(match[0])

                        match = re.findall('"dev":.*', line)
                        if match:
                            match_data = str(match[0]).split(",")
                            dev_regions.append(match_data[0])

                        match = re.findall('"size":.*', line)
                        if match:
                            match_data = str(match[0]).split(",")
                            size.append(match_data[0])

                        match = re.findall('"available_size":.*', line)
                        if match:
                            match_data = str(match[0]).split(",")
                            available_size.append(match_data[0])

                        match = re.findall('"type":.*', line)
                        if match:
                            match_data = str(match[0]).split(",")
                            type_1.append(match_data[0])

                        match = re.findall('"iset_id":.*', line)
                        if match:
                            match_data = str(match[0]).split(",")
                            iset_id.append(match_data[0])

                        match = re.findall('"persistence_domain":.*', line)
                        if match:
                            match_data = str(match[0]).split(",")
                            persistence_domain.append(match_data[0])

                    elif index > int(stop_index):
                        break
            data_frame1 = pd.DataFrame(
                {"Boot": boot_index, "DimmID": dimmid, "DIMM capacity,MemoryType": dimm_capacity,
                 "Healthstate and capacity": health_state, "Actionrequired&physical ID": action_required,
                 "Lockstate & Physical ID": lock_state})

            data_frame2 = pd.DataFrame(
                {"Boot": boot_index, "Capacity": total_capacity, "MemoryCapacity": memory_capacity,
                 "AppDirectCapacity": app_direct_capacity, "UnconfiguredCapacity": un_configured_capacity,
                 "InaccessibleCapacity": inacessible_capacity, "ReservedCapacity": reserved_capacity
                 })
            data_frame3 = pd.DataFrame(
                {"Boot": boot_index, "dev": dev_regions, "size": size, "available_size": available_size,
                 "type": type_1, "iset_id": iset_id, "persistence_domain": persistence_domain})
            return data_frame1, data_frame2, data_frame3
        except Exception as ex:
            raise RuntimeError("Encountered an error '{}'".format(ex))

    def verification_dcpmm_log(self, log_path):
        """
        Function to verify the DCPMM log

        :param log_path: dcpmm log file path
        :return dcpmm_return_value: True on Success False on Failure
        """
        dcpmm_return_value = True
        complete_list_final = self.get_boot_index(log=log_path)
        boot_index_number = 0
        flag = False
        template_data_frame_1 = None
        template_data_frame_2 = None
        template_data_frame_3 = None
        for iteration in complete_list_final:
            end_index = 0
            start_index = complete_list_final[boot_index_number][1]
            boot_index = complete_list_final[boot_index_number][0].split(":")[1]
            if boot_index_number < len(complete_list_final) - 1:
                end_index = complete_list_final[boot_index_number + 1][1]
                boot_index_number += 1
            else:
                end_index = os.stat(log_path).st_size  # capturing the last index of the file
            obtained_dataframe = self.get_dcpmm_log(start_index, end_index, boot_index,
                                                    log_path)  # getting the data frame for each Boot
            if flag:
                test_data_frame_1 = obtained_dataframe[0].drop('Boot',
                                                               axis=1)  # getting the dataFrame after the oth boot
                test_data_frame_2 = obtained_dataframe[1].drop('Boot',
                                                               axis=1)  # getting the dataFrame after the oth boot
                test_data_frame_3 = obtained_dataframe[2].drop('Boot',
                                                               axis=1)  # getting the dataFrame after the oth boot
                if not template_data_frame_1.equals(test_data_frame_1) and \
                        template_data_frame_2.equals(test_data_frame_2) \
                        and template_data_frame_3.equals(test_data_frame_3):
                    self._log.error("Found Error in Boot {} and data is \n{}".format(boot_index, obtained_dataframe))
                    dcpmm_return_value = False
            else:
                self._log.info("Values are consistent through out the boot cycle.")
                template_data_frame_1 = obtained_dataframe[0].drop('Boot',
                                                                   axis=1)  # making the 0th Boot data to template data
                template_data_frame_2 = obtained_dataframe[1].drop('Boot',
                                                                   axis=1)  # making the 0th Boot data to template data
                template_data_frame_3 = obtained_dataframe[2].drop('Boot',
                                                                   axis=1)  # making the 0th Boot data to template data
                flag = True

        if dcpmm_return_value:
            self._log.info("Successfully verified DCPMM Log")

        return dcpmm_return_value

    def dcpmm_platform_log_parsing(self, log_path, encoding=None):
        """
        Function to verify the DCPMM Platform log

        :param log_path: dcpmm log file path
        :param encoding: Encoding of the log file (optional)
        :return result_val: True on Success False on Failure
        """
        check_ran_pattern = r"random.[\d]*[A-Z][A-Z]"
        check_ok_pattern = r"random.[\d]*[A-Z][A-Z]:\sOK"
        tot_random_gb_count = 0
        tot_ok_count = 0
        with open(log_path, "r+", encoding=encoding) as file_pointer:
            datafile = file_pointer.readlines()
            for line in datafile:
                if re.search(check_ran_pattern, line, re.IGNORECASE):
                    tot_random_gb_count += 1
                if re.search(check_ok_pattern, line, re.IGNORECASE):
                    tot_ok_count += 1

        if tot_ok_count != tot_random_gb_count:
            result_val = False
            self._log.error("The random parameter check is not 'OK' on one or more boot cycle.")
        else:
            result_val = True
            self._log.info("The random parameter verified that all boot shows 'OK'..")

        return result_val

    def get_total_system_memory_data_linux(self, ddr_memory_info):
        """
        Function to get the total system memory data from Os.

        :param ddr_memory_info: system memory data from Os
        :return mem_total_val: total current memory of the system in float type
        :raise: RuntimeError
        """
        mem_total_val = None
        if re.search(self.MEM_REGEX, ddr_memory_info):
            mem_match_data = re.findall(self.MEM_REGEX, ddr_memory_info)
            mem_total_val = mem_match_data[0].split(":")[1].strip()
        if not mem_total_val:
            raise RuntimeError("Fail to fetch the total memory value")
        self._log.debug("Successfully got the total memory value from OS: {}".format(mem_total_val))
        return float(mem_total_val)

    def get_system_memory_report_linux(self):
        """
        Function to get the system memory information for linux SUT

        :return: memory info
        """
        get_memory_info = self._common_content_lib.execute_sut_cmd(
            "free -m", "System Memory info", self._command_timeout)
        if get_memory_info != "":
            self._log.debug("Displaying System Memory information... \n {}".format(get_memory_info))

        return get_memory_info

    def verify_provisioned_appdirect_capacity(self, mem_resource_op, pattern, percent=100):
        """
        Function to verify_provisioned_appdirect_capacity

        :param mem_resource_op: mem_resource_op
        :param pattern: memory type
        :param percent: mode percent
        :return: boolean(True/False)
        """
        pattern_memtype = pattern
        pattern_tot_capacity = r"Physical.*"
        tot_capacity = 0
        memtype_capacity = 0

        match_data = re.findall(pattern_memtype, mem_resource_op)
        if len(match_data) != 0:
            for element in match_data:
                memtype_capacity = (float(element.split("|")[2].strip().split(" ")[0]))
        self._log.info("Total {} DCPMM capacity value: {}".format(pattern, memtype_capacity))

        match_data = re.findall(pattern_tot_capacity, mem_resource_op)
        if len(match_data) != 0:
            for element in match_data:
                tot_capacity = (float(element.split("|")[2].strip().split(" ")[0])) * (percent / 100)

        self._log.info("Total Physical DCPMM capacity value: {}".format(tot_capacity))

        # for -1% variance
        threshold_memtotal_floor = (tot_capacity - (tot_capacity * 0.01))

        # for 1% variance
        threshold_memtotal_celling = (tot_capacity + (tot_capacity * 0.01))

        # comparing all the MemTotal values with the 2 threshold values
        if (memtype_capacity > 0) and int(tot_capacity) > 0:
            if threshold_memtotal_floor <= memtype_capacity <= threshold_memtotal_celling:
                self._log.info("The provisioned capacity and total capacity are nearly equal, verification "
                               "successful.")
                ret_verify_mem_resource = True
            else:
                err_log = "The provisioned capacity and total capacity are not nearly equal, please re-provision " \
                          "the dimms and try verifying once again."
                self._log.error(err_log)
                raise RuntimeError(err_log)
        else:
            err_log = "The provisioned capacity or total capacity is zero, please re-provision " \
                      "the dimms and try verifying once again."
            self._log.error(err_log)
            raise RuntimeError(err_log)
        return ret_verify_mem_resource

    def verify_region_id_existence(self, dimm_region_info):
        """
        Function to check the region ID existence on the dimms.

        :param dimm_region_info: dimm region info
        :return True if region is exists else false
        """

        ret_value = True
        region_isetid_list = []
        match_data = re.findall("0x.*", dimm_region_info)
        if len(match_data) != 0:
            for element in match_data:
                isetid_check = element.split("|")[0].strip().split(" ")[0]
                if isetid_check:
                    region_isetid_list.append(isetid_check)

        self._log.info("Total DIMM region ID's are: {}".format(region_isetid_list))

        if len(match_data) == len(region_isetid_list):
            self._log.info("Number of region exists with ID is equal to number of regions..")
        else:
            self._log.error("Number of region exists with ID is not equal to number of regions..")
            ret_value = False

        return ret_value

    def get_capacity_region_data(self, result_data, index):
        """
        Function to get the Total DIMM capacity value after provisioning

        :param result_data: region information.
        :param index: which index that capacity resides in.
        :return: capacity_list
        """
        capacity_list = []
        try:
            match_data = re.findall("0x.*", result_data)
            if len(match_data) != 0:
                for element in match_data:
                    capacity_list.append(float(element.split("|")[index].strip().split(" ")[0]))
        except Exception as ex:
            raise RuntimeError("Encountered an error {}, while fetching capacity: get_capacity_region_data".format(ex))
        self._log.info("DCPMM region values are: {}".format(capacity_list))
        return capacity_list

    def verify_background_process_running(self, str_process_name):
        """
        Function to verify that the process is running in the background on SUT.

        :param str_process_name: name of the process to be found
        :return None
        """
        ret_code = self.task_finder(str_process_name)

        if ret_code == 0:
            self._log.info("{} has been started to execute in the background..".format(str_process_name))
        else:
            raise RuntimeError("{} is not launched in the background..".format(str_process_name))

    def task_finder(self, str_process_name):
        """
        Function to find the process running on the SUT.

        :param str_process_name: name of the process to be found
        :return 0 if process is found in the task list else 1
        """
        process_running = self._os.execute('TASKLIST | FINDSTR /I "{}"'.format(str_process_name),
                                           self._command_timeout)

        return process_running.return_code

    def verify_memory_utilization(self, physical_memory_data_win_os, percent_mem_utilization_config):
        """
        Function to verify memory utilization during VSS stress test.

        :param percent_mem_utilization_config: expected memory utilization percent
        :param physical_memory_data_win_os: total and available memory output
        :return True if memory utilization is reached
        """
        os_mem_utilization = False
        total_memory_data_win_os = int(physical_memory_data_win_os[0].split(":")[1].strip("MB").strip()
                                       .replace(",", ""))

        avail_memory_data_win_os = int(physical_memory_data_win_os[1].split(":")[1].strip("MB").strip()
                                       .replace(",", ""))
        total_memory_utilization = total_memory_data_win_os - avail_memory_data_win_os

        self._log.info("Memory utilization during test is {} MB out of {} MB..".format(total_memory_utilization,
                                                                                       total_memory_data_win_os))
        configured_value = total_memory_data_win_os * float(percent_mem_utilization_config)
        if total_memory_utilization > configured_value:
            self._log.info("Memory utilization value '{}' is higher than the expected configured "
                           "value '{}'.".format(total_memory_utilization, configured_value))
            os_mem_utilization = True
        else:
            self._log.info("Memory utilization value '{}' is less than the expected configured "
                           "value '{}'.".format(total_memory_utilization, configured_value))
        return os_mem_utilization

    def verify_cpu_utilization(self, cpu_utilization_os, cpu_utilization_percent_config):
        """
        Function to verify memory utilization during stress test.

        :param cpu_utilization_os: CPU Utilization value from OS
        :param cpu_utilization_percent_config: cpu utilization value from config file
        :return True if memory
        """

        os_cpu_utilization = False

        cpu_utilization_percent_os = ''.join([ele for ele in cpu_utilization_os if ele.isnumeric()])

        self._log.info("CPU utilization during test is {}% ..".format(cpu_utilization_percent_os))

        self._log.info("CPU utilization % value = '{}' and expected % "
                       "value='{}'".format(cpu_utilization_percent_os, cpu_utilization_percent_config))
        if int(cpu_utilization_percent_os) >= cpu_utilization_percent_config:
            self._log.info("CPU utilization is higher than the configured "
                           "value of '{}'".format(cpu_utilization_percent_config))
            os_cpu_utilization = True
        else:
            self._log.info("CPU utilization is less than the configured "
                           "value of '{}'".format(cpu_utilization_percent_config))

        return os_cpu_utilization

    def verify_and_hold_until_background_process_finish(self, str_process_name):
        """
        Function verify and hold until background process finish running on the SUT.

        :param str_process_name: name of the process to be found
        :return None
        """
        process_running = True
        while process_running:
            ret_code = self.task_finder(str_process_name)

            if ret_code == 0:
                self._log.info("PatIO.exe or mem64.exe is still running in the background..")
                self._log.info("Waiting for the iwVSS execution to complete..")
                time.sleep(int(self._command_timeout / 2))
            else:
                process_running = False

                self._log.info("iwVSS execution has been completed successfully..")
                self._log.info("{} has been started to execute in the background..".format(str_process_name))

    def verify_provisioning_mode(self, result_data):
        """
        Function to verify if ModesSupported=1LM, Memory Mode and App Direct are present within the IPMCTL App Direct
        Mode capability command

        :param result_data: Dimm information.
        :return: True on success
        :raise: RuntimeError
        """
        if not ("ModesSupported=1LM" and "Memory Mode" and "App Direct" in result_data):
            error_msg = "Expected provisioning mode is not supported.."
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully verified the expected provisioning mode..")
        return True

    def verify_region_default_attribs_mode(self, region_data, mode=None):
        """
        Function to verify region default attributes are included correctly or not.

        ---ISetID=0xdba9c3d029028888---
           SocketID=0x0000
           PersistentMemoryType=AppDirect
           Capacity=504.000 GiB
           FreeCapacity=0.000 GiB
           HealthState=Healthy
           DimmID=0x0001, 0x0101, 0x0201, 0x0301
        ---ISetID=0x495dc3d0ddfe8888---
           SocketID=0x0001
           PersistentMemoryType=AppDirect
           Capacity=504.000 GiB
           FreeCapacity=0.000 GiB
           HealthState=Healthy
           DimmID=0x1001, 0x1101, 0x1201, 0x1301


        :param region_data: show region output.
        :param mode: mode of the provisioning
        :raise: TestFail if all default attribs are not present
        """

        default_attribs_region = ["RegionID|ISetID", r"\sPersistentMemoryType", r"\sCapacity", r"\sFreeCapacity"]

        no_of_region_present = len(re.findall("RegionID|ISetID", region_data))

        if mode is not None:
            if len(re.findall("PersistentMemoryType={}".format(mode), region_data)) != no_of_region_present:
                raise content_exceptions.TestFail("Persistent memory type is not matching with AppDirect mode.. "
                                                  "Exiting..")

        for attribs in default_attribs_region:
            if len(re.findall(attribs, region_data)) != no_of_region_present:
                raise content_exceptions.TestFail("One or more default attributes are not included in the region info "
                                                  "PersistentMemoryType, Capacity & FreeCapacity.")

        self._log.info("Successfully verified the default attributes from region information...")

    def verify_created_namespace_params(self, no_of_regions, post_namespace_creation_report,
                                        namespace_create_list):
        """
        Function to verify the created namespace accuracy.

        :param no_of_regions: Total number of regions created
        :param post_namespace_creation_report: namespace information
        :param namespace_create_list: Each namespace information list when created.
        """
        found_healthy = 0
        found_namespace_id = 0
        store_namespace_capacity = []
        store_namespace_capacity_created = []
        for line in post_namespace_creation_report:
            if "HealthState=Healthy" in line:
                found_healthy = found_healthy + 1

            if re.findall(r"\sCapacity", line):
                store_namespace_capacity.append(line.replace("\r", ""))

            if "NamespaceId" in line:
                found_namespace_id = found_namespace_id + 1

        for index in range(0, len(namespace_create_list)):
            for cap in namespace_create_list[index].split("\r"):
                if re.findall(r"\sCapacity", cap):
                    store_namespace_capacity_created.append(cap)

        if len(no_of_regions) != found_healthy:
            raise content_exceptions.TestFail("The newly created namespaces are listed non-healthy.. Exiting..")

        if len(no_of_regions) != found_namespace_id:
            raise content_exceptions.TestFail("The newly created namespaces does not have NamespaceID.. Exiting..")

        if store_namespace_capacity != store_namespace_capacity_created:
            raise content_exceptions.TestFail("The newly created namespaces does not match the expected capacity.. "
                                              " Exiting..")

        self._log.info("Namespaces are listed with expected attributes such as: NamespaceID, Capacity, HealthState")

        self._log.info("Each of the newly created namespaces are listed healthy with expected capacity.")

    def get_region_data(self, region_data, index):
        """
        Function to get the data based on the index value from the region information

        :param region_data: region information.
        :param index: index to fetch the data.
        :return: list_info based on index
        """
        list_info = []
        try:
            match_data = re.findall("0x.*", region_data)
            if len(match_data) != 0:
                for element in match_data:
                    list_info.append(element.split("|")[index].strip().split(" ")[0])
        except Exception as ex:
            raise RuntimeError(
                "Encountered an error {}, while fetching the info: get_region_data".format(ex))
        self._log.debug("DCPMM value that was returned: {}".format(list_info))
        return list_info

    def get_device_total_size(self, device, unit="GB"):
        """
        Function to get the total size of the disk

        :param device: name of the device
        :param unit: unit of the output (GB/MB)
        :return: total size of the device
        """
        size = self._common_content_lib.execute_sut_cmd(self.CMD_TO_GET_TOTAL_DISK_SIZE.format(device, unit, device),
                                                        "Get the size of the disk", self._command_timeout)

        return size

    def create_partition_storage(self, device, fs_type="primary", size=None):
        """
        Function to run the command to do the partition by 'parted' on linux SUT

        :param device:
        :param fs_type: fs_type of the partition. possible values are "primary", "logical" or "extended"
        :param size: size of the partition
        :return: partition result
        """
        unit = ""

        if fs_type not in ("primary", "logical", "extended"):
            raise content_exceptions.TestFail("Incorrect partition type")

        if size is None:
            start_index = 0
            end_index = self.get_device_total_size(device)
        else:
            unit = "".join(re.split("[^a-zA-z]*", size))
            last_used_end_index = self._common_content_lib.execute_sut_cmd(
                self.CMD_TO_GET_THE_END_INDEX.format(device, unit),
                "Get the last used end index", self._command_timeout)

            if 'End' not in last_used_end_index:
                start_index = int(float(last_used_end_index.split(unit)[0]))
            else:
                start_index = 0

            end_index = start_index + int(''.join(map(str, re.findall(r"[\d]", size))))

        partition_result = self._common_content_lib.execute_sut_cmd(self.LINUX_PARTITION_CMD.format(
            device, fs_type, start_index, unit, end_index, unit),
            "Create a generic partition on each device"
            "using parted", self._command_timeout)

        if partition_result != "":
            self._log.info("Successfully created a generic partition on the device {}"
                           " using parted".format(device))
        elif 'Error' in partition_result:
            raise content_exceptions.TestFail("Couldn't create the partition")

        return partition_result

    def create_file_system(self, device, file_system="ext4"):
        """
        Function to create a Linux file system on each enumerated PM blockdev device on linux SUT

        :param: device : pmem device
        :param: file_system : ext2/ntfs
        :return: fs_result_data(stdout result)
        """
        self._log.info("Executing the command : {}".format(self.LINUX_CMD_TO_CREATE_FILE_SYSTEM.
                                                                  format(file_system, device)))
        fs_result_data = self._common_content_lib.execute_sut_cmd(self.LINUX_CMD_TO_CREATE_FILE_SYSTEM.
                                                                  format(file_system, device),
                                                                  "Create a {} file system on each "
                                                                  "enumerated ".format(file_system),
                                                                  self._wait_time)
        self._log.info("Disk {} is Formatted with {} file system".format(device, file_system))

        if len(fs_result_data) != 0:
            self._log.info("Successfully created a {} Linux file system on each enumerated block..\n{}".
                           format(file_system, fs_result_data))

        return fs_result_data

    def delete_partition(self, pmem_device_list):
        """
        Function to delete partition under pmem_device_list.

        :param: pmem_device_list: partition List to be deleted.
        :return True if partition is deleted successfully
        """

        for index in range(0, len(pmem_device_list)):
            partition_num_list = self.get_sub_partition_number_list(pmem_device_list[index])
            for num in partition_num_list:
                self.delete_partition_with_partition_number(pmem_device_list[index], num)
                self._log.info("Deleted partition under the device /dev/{},"
                               " having partition number {}".format(pmem_device_list[index], num))

        return True

    def get_sub_partition(self, pmem_device):
        """
        Function to get the sub partition under the pmem_device_list

        :param: pmem_device : pmem device
        :return: sub partition list
        """
        sub_partition = []
        ls_command = "ls -l /dev/{}*".format(pmem_device)
        self._log.info("Executing the command : {}".format(ls_command))
        dev_list = self._os.execute(ls_command, self._command_timeout)
        self._log.info("Device list : {}".format(dev_list.stdout))
        if dev_list.cmd_failed():
            # ls -l command returns non zero value, if No such file or directory
            self._log.info("There are no sub partition present under the device...")
            return True
        elif dev_list.return_code == 0:
            sub_part = re.findall("/dev/pmem[\d.*].+", dev_list.stdout)
            for index in range(0, len(sub_part)):
                sub_partition.append(sub_part[index])
            self._log.info("Sub Partition List : {}".format(sub_partition))
        if dev_list != "":
            self._log.info("Partition details..\n{}".format(dev_list.stdout))

        return sub_partition

    def get_sub_partition_number_list(self, device_name):
        """
        Function to get the number value of the partition

        :param device_name: Name of the device
        :return: list of partition number
        """
        partition_number_list = self._common_content_lib.execute_sut_cmd(
            self.CMD_TO_GET_PARTITION_NUMBER.format(device_name), "get the sub partition number",
            self._command_timeout).split()
        if partition_number_list != " ":
            self._log.info("Partition Number \n {}".format(partition_number_list))
        else:
            self._log.info("No partition is found under the device {}".format(device_name))

        return partition_number_list

    def delete_partition_with_partition_number(self, device_name, part_number):
        """
        Function to delete partition by partition number using parted command

        :param:device_name: name of the device
        :param:part_number: number of the partition
        :return: True if success
        """
        self._common_content_lib.execute_sut_cmd(self.CMD_TO_DELETE_PARTITION.format(device_name, part_number),
                                                 "to delete partition", self._command_timeout)
        self._log.info("Deleting partition with partition number {} under the device {}"
                       .format(part_number, device_name))

        return True

    def verify_iset_id_existence(self, dimm_region_info):
        """
        Function to check the Iset ID existence on the dimms.
        SocketID | ISetID             | PersistentMemoryType | Capacity    | FreeCapaci                                                                                        ty | HealthState
        ================================================================================                                                                                        =================
         0x0000   | 0xdba9c3d029028888 | AppDirect            | 504.000 GiB | 0.000 GiB                                                                                            | Healthy
         0x0001   | 0x495dc3d0ddfe8888 | AppDirect            | 504.000 GiB | 0.000 GiB

        :param dimm_region_info: dimm region info
        :return True if Iset ID is exists else false
        """

        ret_value = True
        region_isetid_list = []
        match_data = re.findall("0x.*", dimm_region_info)
        if len(match_data) != 0:
            for element in match_data:
                region_isetid_list.append(element.split("|")[1])

        self._log.info("Total DIMM Iset ID's are: {}".format(region_isetid_list))

        if len(match_data) == len(region_isetid_list):
            self._log.info("Number of Iset ID exists with ID is equal to number of regions..")
        else:
            self._log.error("Number of Iset ID exists with ID is not equal to number of regions..")
            ret_value = False

        return ret_value

    def generate_5gb_test_file(self):
        """
        This function is used to generate a 5GB test file.

        :return: True on success
        """
        try:
            if OperatingSystems.LINUX in self._os.os_type:
                self._common_content_lib.execute_sut_cmd(
                    "rm -rf {}".format(self.TEST_FILE_NAME), "To delete a 5GB test file",
                    self._command_timeout, self.ROOT)

                # To generate a 5GB test file in linux
                self._common_content_lib.execute_sut_cmd(
                    "head -c 5G </dev/urandom> {}".format(self.TEST_FILE_NAME), "To generate 5GB test file",
                    self._command_timeout, self.ROOT)

            elif OperatingSystems.WINDOWS in self._os.os_type:
                file_exists = self._common_content_lib.execute_sut_cmd(
                    self.PS_CMD_TO_CHECK_FILE_EXISTS_OR_NOT.format(self.TEST_FILE_NAME),
                    "To check whether file exists or not", self._command_timeout, self.C_DRIVE_PATH)
                if 'True' in file_exists:
                    self._common_content_lib.execute_sut_cmd("del /q {}".format(self.TEST_FILE_NAME),
                                                             "To delete existing test file in Windows",
                                                             self._command_timeout, self.C_DRIVE_PATH)

                # Generate a 5GB test file in windows
                self._common_content_lib.execute_sut_cmd(
                    self.FSUTIL_CMD_TO_CREATE_SPARSE_FILE.format(self.TEST_FILE_NAME, 5 * 1024 * 1024 * 1024),
                    "To generate 5GB test file", self._command_timeout, self.C_DRIVE_PATH)

            return True
        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise ex

    def diagnostic_check(self, diagnostic_data):
        """
        Function to verify the diagnostic data.

        :param diagnostic_data: diagnostic output
        :return:
        """
        list_values = set(re.findall(r"State\s=\s.*", diagnostic_data))

        state_ok_result = []
        for state in list_values:
            if "Ok" not in state:
                self._log.debug("State verification failed... The value is {}.. please check again..".format(state))
                state_ok_result.append(False)
            else:
                state_ok_result.append(True)

        if not all(state_ok_result):
            raise content_exceptions.TestFail("The state value is not OK.. Exiting..")

        self._log.debug("Successfully verified the State with value 'OK'...")

    def get_memresource_ddr_capacity(self, mem_resource_op, pattern):
        """
        Function to get_memresource_ddr_capacity

        :param mem_resource_op: mem_resource_op
        :param pattern: memory type

        :return: capacity
        """
        memtype_capacity = 0

        match_data = re.findall(pattern, mem_resource_op)
        if len(match_data) != 0:
            for element in match_data:
                memtype_capacity = (element.split("|")[1].strip().split(" ")[0])
        else:
            raise content_exceptions.TestFail(
                "There are no {} pattern in memory resources information..".format(pattern))
        self._log.info("Total {} DDR capacity value: {}".format(pattern, memtype_capacity))

        return memtype_capacity

    def get_memresource_dcpmm_capacity(self, mem_resource_op, pattern):
        """
        Function to get_memresource_dcpmm_capacity

        :param mem_resource_op: mem_resource_op
        :param pattern: memory type

        :return: capacity
        """
        memtype_capacity = 0

        match_data = re.findall(pattern, mem_resource_op)
        if len(match_data) != 0:
            for element in match_data:
                memtype_capacity = (element.split("|")[2].strip().split(" ")[0])
        else:
            raise content_exceptions.TestFail(
                "There are no {} pattern in memory resources information..".format(pattern))
        self._log.info("Total {} DCPMM capacity value: {}".format(pattern, memtype_capacity))

        return memtype_capacity

    def get_memresource_total_capacity(self, mem_resource_op, pattern):
        """
        Function to get_memresource_total_capacity

        :param mem_resource_op: mem_resource_op
        :param pattern: memory type

        :return: capacity
        """
        memtype_capacity = 0

        match_data = re.findall(pattern, mem_resource_op)
        if len(match_data) != 0:
            for element in match_data:
                memtype_capacity = (element.split("|")[3].strip().split(" ")[0])
        else:
            raise content_exceptions.TestFail("There is no {} pattern in memory resources information.."
                                              "".format(pattern))

        self._log.info("Total capacity value: {}".format(memtype_capacity))

        return memtype_capacity

    @staticmethod
    def get_list_off_topology(topology_op):
        """
        Function to get_memresource_capacity lists

        :param topology_op: topology_op
        :return: physical_id, capacity, locator
        """
        physical_id = []
        capacity = []
        locator = []
        match_data = re.findall("0x.*|N/A.*", topology_op)
        if len(match_data) != 0:
            for line in match_data:
                physical_id.append(line.split("|")[3].strip())
                capacity.append(int(float(line.split("|")[2].strip().split(" ")[0])))
                locator.append(line.split("|")[4].strip())
        else:
            raise content_exceptions.TestFail("There are no DIMMID in topology information..")
        return physical_id, capacity, locator

    @staticmethod
    def get_list_off_socket(socket_op):
        """
        Function to get socket lists

        :param socket_op: topology_op
        :return: socket_id, mapped_memory_limit, total_memory_limit
        """
        socket_id = []
        mapped_memory_limit = []
        total_memory_limit = []
        match_data = re.findall("0x.*", socket_op)
        if len(match_data) != 0:
            for line in match_data:
                socket_id.append(line.split("|")[0].strip())
                mapped_memory_limit.append(line.split("|")[1].strip().split()[0])
                total_memory_limit.append(line.split("|")[2].strip().split()[0])
        else:
            raise content_exceptions.TestFail("There are no Socket ID in socket information..")
        return socket_id, mapped_memory_limit, total_memory_limit

    @staticmethod
    def get_list_off_firmware(firmware_op):
        """
        Function to get firmware lists

        :param firmware_op: topology_op
        :return: activefwversion, staged FWVersion
        """
        active_fw_version = []
        staged_fw_version = []
        match_data = re.findall("0x.*", firmware_op)
        if len(match_data) != 0:
            for line in match_data:
                active_fw_version.append(line.split("|")[1].strip())
                staged_fw_version.append(line.split("|")[2].strip())
        else:
            raise content_exceptions.TestFail("There are no DIMMID in firmware information..")
        return active_fw_version, staged_fw_version

    def verify_memory_resource_information(self, mem_resources_data, mode="1LM", percent=100):
        """verify_memory_resource_information
        Function to verify ipmctl memory resources information.

        :param mem_resources_data: memory resources output
        :param mode: "1LM" or "2LM"
        :param percent: mode percentage
        :return: None
        """
        post_mem_capacity = self._common_content_configuration.memory_bios_post_memory_capacity()
        dcpmm_mem_capacity = int(self._common_content_configuration.memory_bios_total_dcpmm_memory_capacity() *
                                 (percent / 100))
        variance_percent = self._common_content_configuration.get_memory_variance_percent()

        self._log.info("Total DDR capacity as per configuration - {}".format(post_mem_capacity))
        self._log.info("Total DCPMM capacity as per configuration in {} {}%- {}".format(mode, percent,
                                                                                        dcpmm_mem_capacity))

        # ddr memory with variance
        ddr_memtotal_with_variance_config = (post_mem_capacity - (post_mem_capacity * variance_percent))
        # dcpmm memory with variance
        dcpmm_memtotal_with_variance_config = (dcpmm_mem_capacity - (dcpmm_mem_capacity * variance_percent))

        if mode == "1LM":
            volatile_capacity = float(self.get_memresource_ddr_capacity(mem_resources_data, r"Volatile.*"))
            if int(volatile_capacity) < ddr_memtotal_with_variance_config or int(volatile_capacity) > \
                    post_mem_capacity:
                raise content_exceptions.TestFail("Total DDR dimm Capacity does not match with topology info.")

            self._log.info("Successfully validated Volatile capacity with full DRAM size..")
        elif mode == "2LM":
            volatile_capacity = float(self.get_memresource_dcpmm_capacity(mem_resources_data, r"Volatile.*"))
            if int(volatile_capacity) < dcpmm_memtotal_with_variance_config or int(volatile_capacity) > \
                    dcpmm_mem_capacity:
                raise content_exceptions.TestFail("Total DCPMM dimm Capacity does not match with topology info.")

            self._log.info("Successfully validated Volatile capacity with full DCPMM size..")
        else:
            raise content_exceptions.TestFail("{} mode does not supported.. please check your mode..".format(mode))

        appdirect_capacity = float(self.get_memresource_dcpmm_capacity(mem_resources_data, r"AppDirect.*"))

        self._log.info("Total DCPMM capacity as per configuration with variance - {}".format(
            dcpmm_memtotal_with_variance_config))

        if mode == "1LM":
            if int(appdirect_capacity) < dcpmm_memtotal_with_variance_config or int(appdirect_capacity) > \
                    dcpmm_mem_capacity:
                raise content_exceptions.TestFail("Total Appdirect capacity does not match with full DCPMM capcaity "
                                                  "in topology.")

            self._log.info("Successfully validated AppDirect capacity with full DCPMM size..")
        elif mode == "2LM":
            if percent != 100:
                if int(appdirect_capacity) < dcpmm_memtotal_with_variance_config or int(appdirect_capacity) > \
                        dcpmm_mem_capacity:
                    raise content_exceptions.TestFail(
                        "Total Appdirect capacity does not match with {} DCPMM capcaity "
                        "in topology.".format(dcpmm_memtotal_with_variance_config))

                self._log.info("Successfully validated AppDirect capacity with {} DCPMM capcaity "
                               "in topology.".format(dcpmm_memtotal_with_variance_config))
            else:
                if int(appdirect_capacity) > 0:
                    raise content_exceptions.TestFail("Total Appdirect capacity is non-zero in topology.")

                self._log.info("Successfully validated AppDirect capacity with zero capacity..")
        else:
            raise content_exceptions.TestFail("{} mode does not supported.. please check your mode..".format(mode))

        # No cache capacity check on the topology information
        cache_ddr_capacity = float(self.get_memresource_ddr_capacity(mem_resources_data, r"Cache.*"))
        cache_dcpmm_capacity = self.get_memresource_dcpmm_capacity(mem_resources_data, r"Cache.*")

        if mode == "1LM":
            if cache_dcpmm_capacity != "-" or int(cache_ddr_capacity) > 0:
                raise content_exceptions.TestFail("Cache of DDR or DCPMM is showing non-zero capacity...")

            self._log.info("Successfully validated Cache capacity of DCPMM and DDR sizes..")
        elif mode == "2LM":
            if int(cache_ddr_capacity) < ddr_memtotal_with_variance_config or int(cache_ddr_capacity) > \
                    post_mem_capacity:
                raise content_exceptions.TestFail("Total DDR dimm Capacity does not match with topology info.")

            self._log.info("Successfully validated Cache capacity with full DRAM size..")
        else:
            raise content_exceptions.TestFail("{} mode does not supported.. please check your mode..".format(mode))

        # No Inaccessible capacity check on the topology information
        inaccessible_dcpmm_capacity = float(
            self.get_memresource_dcpmm_capacity(mem_resources_data, r"Inaccessible.*"))
        inaccessible_ddr_capacity = self.get_memresource_ddr_capacity(mem_resources_data, r"Inaccessible.*")
        if inaccessible_ddr_capacity != "-":
            inaccessible_ddr_capacity = float(self.get_memresource_ddr_capacity(mem_resources_data, r"Inaccessible.*"))
            if inaccessible_ddr_capacity != 0:
                raise content_exceptions.TestFail("Inaccessible capacity of DDR showing non-zero capacity...")

        max_reserved_capacity_gib = self._common_content_configuration.get_max_reserved_capacity_gib_memory()

        if int(inaccessible_dcpmm_capacity) > max_reserved_capacity_gib:
            raise content_exceptions.TestFail(
                "Inaccessible capacity DCPMM is greater than {}GiB capacity...".format(
                    max_reserved_capacity_gib))

        self._log.info("Successfully validated No Inaccessible of DCPMM and DDR sizes..")

        # Check Physical row capacities with Total column capacities
        physical_dcpmm_capacity = float(self.get_memresource_dcpmm_capacity(mem_resources_data, r"Physical.*"))
        physical_ddr_capacity = float(self.get_memresource_ddr_capacity(mem_resources_data, r"Physical.*"))

        total_physical_capacity = physical_dcpmm_capacity + physical_ddr_capacity
        self._log.info("Total physical capacity : {}".format(total_physical_capacity))

        appdirect_total_capacity = float(self.get_memresource_total_capacity(mem_resources_data, r"AppDirect.*"))
        volatile_total_capacity = float(self.get_memresource_total_capacity(mem_resources_data, r"Volatile.*"))
        cache_total_capacity = float(self.get_memresource_total_capacity(mem_resources_data, r"Cache.*"))
        inaccessible_total_capacity = float(self.get_memresource_total_capacity(mem_resources_data, r"Inaccessible.*"))

        total_mem_param_capacity = \
            appdirect_total_capacity + volatile_total_capacity + cache_total_capacity + inaccessible_total_capacity

        self._log.info("Total capacity of appdirect, volatile, cache and inaccessible : {}"
                       .format(total_mem_param_capacity))

        if total_physical_capacity != total_mem_param_capacity:
            raise content_exceptions.TestFail("Sum of Physical and Total capacity accross DDR and DCPMM "
                                              "does not match..")
        self._log.info("Successfully matched sum of Physical and total capacity accross DDR and DCPMM...")

    def verify_topology_information(self, topology_info, dmidecode_output_os):
        """
        Function to verify ipmctl topology information.

        :param topology_info: topology output
        :param dmidecode_output_os: dmidecode output
        :return: None
        """
        for handle in dmidecode_output_os:
            try:
                index_handle = topology_info[0].index(str(handle).lower())
                if "MB" in dmidecode_output_os[handle]["Size"]:
                    current_ddr_dimm_size = eval('int(int(dmidecode_output_os[handle]["Size"].split()[0]) / 1024)')
                else:
                    current_ddr_dimm_size = eval('int(dmidecode_output_os[handle]["Size"].split()[0])')

                if current_ddr_dimm_size != topology_info[1][index_handle]:
                    raise content_exceptions.TestFail(
                        "'{}' size from dmidecode is not matching with '{}' size from topology.."
                        "".format(current_ddr_dimm_size, topology_info[1][index_handle]))

                self._log.info("'{}' size from dmidecode is matching with '{}' size from topology.."
                               "".format(current_ddr_dimm_size, topology_info[1][index_handle]))

                if dmidecode_output_os[handle]["Locator"] != topology_info[2][index_handle]:
                    raise content_exceptions.TestFail(
                        "'{}' Locator from dmidecode is not matching with '{}' locator from topology.."
                        "".format(dmidecode_output_os[handle]["Locator"], topology_info[2][index_handle]))

                self._log.info("'{}' Locator from dmidecode is matching with '{}' locator from topology.."
                               "".format(dmidecode_output_os[handle]["Locator"], topology_info[2][index_handle]))
            except ValueError:
                self._log.debug("'{}' handle is not available in topology for checking.. proceeding to next handle "
                                "in the dmidecode".format(handle))

    def verify_ars_status_information(self, ars_status_info):
        """
        Function to verify ipmctl ARS status information.

        :param ars_status_info: ARS output
        :return: None
        """
        if re.findall(r"In\sprogress", ars_status_info):
            raise content_exceptions.TestFail("ARS status is not in Completed state after few "
                                              "minutes of execution..")

        self._log.info("Successfully ARS status is in completed state after few minutes of execution..")

    def verify_socket_information(self, socket_op, cpu_locators, mode="1LM", percent=100):
        """
        Function to verify ipmctl socket information.

        :param socket_op: socket output
        :param cpu_locators: list of cpu's
        :param mode: "1LM" or "2LM"
        :param percent:
        :return: None
        """
        dcpmm_mem_capacity = float(self._dcpmm_mem_capacity * (percent / 100))

        self._log.info("Total DDR capacity as per configuration - {}".format(self._post_mem_capacity))
        self._log.info("Total DCPMM capacity as per configuration in {} {}%- {}".format(mode, percent,
                                                                                        dcpmm_mem_capacity))

        # ddr memory with variance
        ddr_memtotal_with_variance_config = (self._post_mem_capacity - (self._post_mem_capacity *
                                                                        self._variance_percent))
        # dcpmm memory with variance
        dcpmm_memtotal_with_variance_config = (dcpmm_mem_capacity - (dcpmm_mem_capacity * self._variance_percent))

        socket_info = list(self.get_list_off_socket(socket_op))
        self._log.info("Socket Information : {}".format(socket_info))
        locators = []
        for loc in cpu_locators:
            locators.append(loc.split("_")[0])

        locator_cpu_number = list(set(self._common_content_lib.get_list_of_digits(locators)))
        self._log.info("CPU Sockets list : {}".format(locator_cpu_number))
        for socket in range(len(socket_info[0])):
            if locator_cpu_number[socket] != int(socket_info[0][socket].split("x")[-1]):
                raise content_exceptions.TestFail("{} from dmidecode does not match with {} socket id from socket "
                                                  "info. ".format(locator_cpu_number[socket], socket_info[0][socket]))

            self._log.info("Successfully validated {} from dmidecode with {} socket id from socket "
                           "info. ".format(locator_cpu_number[socket], socket_info[0][socket]))
            socket_memory_with_variance = None

            if mode == MemoryTopology.ONE_LM:
                socket_memory_with_variance = (ddr_memtotal_with_variance_config +
                                               dcpmm_memtotal_with_variance_config) / len(locator_cpu_number)
            elif mode == MemoryTopology.TWO_LM and percent == 100:
                socket_memory_with_variance = dcpmm_memtotal_with_variance_config / len(locator_cpu_number)
            elif mode == MemoryTopology.TWO_LM and percent != 100:
                socket_memory_with_variance = dcpmm_memtotal_with_variance_config

            self._log.info("Socket memory with variance : {}".format(socket_memory_with_variance))
            if int(float(socket_info[2][socket])) <= socket_memory_with_variance:
                log_error = "{}-TotalMappedMemory is does not match with {}-socket Capacity from " \
                            "configuration.".format(int(float(socket_info[2][socket])), socket_memory_with_variance)
                self._log.error(log_error)
                raise content_exceptions.TestFail(log_error)

            self._log.info("{}-TotalMappedMemory is match with {}-socket Capacity from configuration.".
                           format(int(float(socket_info[2][socket])), socket_memory_with_variance))

    def verify_firmware_information(self, firmware_data):
        """
        Function to verify ipmctl firmware information.

        :param firmware_data: firmware output
        :return: None
        """
        firmware_info = self.get_list_off_firmware(firmware_data)

        if len(set(firmware_info[0])) != 1:
            raise content_exceptions.TestFail("ActiveFwVersion does not aligned with all the DIMMS")

        self._log.info("ActiveFwVersion successfully aligned with all the DIMMS")

        if list(set(firmware_info[1]))[0] != "N/A":
            raise content_exceptions.TestFail("We have StagedFWVersion on the DIMMS.. please check again..")

        self._log.info("There were no StagedFWVersion on the DIMMS.. proceeding further..")

    def calculate_checksum(self, file_path):
        """
        Function to calculate the checksum value

        :param file_path: path of the file
        :return: checksum value
        """
        if OperatingSystems.LINUX in self._os.os_type:
            command_result = self._common_content_lib.execute_sut_cmd(self.CMD_TO_CALCULATE_MD5_CHECKSUM_L.
                                                                      format(file_path),
                                                                      "getting the checksum", self._command_timeout)
            self._log.info("MD5 checksum of the file {}:\n{}".format(file_path, command_result))
            return command_result.split()[0]

        elif OperatingSystems.WINDOWS in self._os.os_type:
            command_result = self._common_content_lib.execute_sut_cmd(self.CMD_TO_CALCULATE_MD5_CHECKSUM_W.
                                                                      format(file_path), "getting checksum value",
                                                                      self._command_timeout)
            self._log.info(command_result)
            return command_result.split('\n')[1]

        else:
            raise NotImplementedError("Not implemented for OS {}".format(self._os.os_type))

    def delete_file(self, filepath):
        """
        Function to delete a file.

        :param filepath: path of the file to be deleted
        :return: True if success
        """
        try:
            if OperatingSystems.LINUX in self._os.os_type:
                if self._os.check_if_path_exists(filepath):
                    self._common_content_lib.execute_sut_cmd("rm -rf {}".format(filepath),
                                                             "To delete a file", self._command_timeout, self.ROOT)
                else:
                    raise content_exceptions.TestFail("Cannot find the file {} to delete".format(filepath))
            elif OperatingSystems.WINDOWS in self._os.os_type:
                file_exists = self._common_content_lib.execute_sut_cmd(self.PS_CMD_TO_CHECK_FILE_EXISTS_OR_NOT.
                                                                       format(filepath),
                                                                       "To check whether file exists or not",
                                                                       self._command_timeout, self.C_DRIVE_PATH)
                if 'True' in file_exists:
                    self._common_content_lib.execute_sut_cmd("DEL /Q {}".format(filepath), "To delete a file",
                                                             self._command_timeout, self.C_DRIVE_PATH)
                else:
                    raise content_exceptions.TestFail("Can not find the file {}".format(filepath))
            self._log.info("Successfully deleted the file {} ".format(filepath))
            return True

        except Exception:
            raise content_exceptions.TestFail("Error while trying to delete the file {} . ".format(filepath))

    def get_total_ddr_memory_data(self, topology_data):
        """
        Function to verify if system is 2LM provisioned or not.

        :param topology_data: output from 'ipmctl show -topology command'
        :return ddr_capacity_list: list of DDR memory capacilty values
        """
        ddr_capacity_list = []
        match_data = re.findall("DDR.*", topology_data)
        if len(match_data) != 0:
            for element in match_data:
                ddr_capacity_list.append(float(element.split("|")[1].strip().split(" ")[0]))
        self._log.info("Total DDR memory capacity values are: {}".format(ddr_capacity_list))
        return ddr_capacity_list

    def get_memory_mode_data(self, result_data):
        """
        Function to get the AppDirect1Size value after provisioning

        :param result_data: Dimm information.
        :return: memory_mode_list
        """
        memory_mode_list = []
        match_data = re.findall("0x.*", result_data)
        if len(match_data) != 0:
            for element in match_data:
                memory_mode_list.append(float(element.split("|")[2].strip().split(" ")[0]))
        self._log.info("Memory mode values are: {}".format(memory_mode_list))

        return memory_mode_list

    def verify_lm_provisioning_configuration_win(self, dimm_data, mode):
        """
        Function to verify if system is LM provisioned or not for Windows SUT.

        :param dimm_data: output of DIMM info data from IPMCTL command
        :param mode: Provisioning mode expected values are "1LM" or "2LM"
        :return : true on success
        :raise: RuntimeError
        """
        total_dimm_memory = None
        if mode == "1LM":
            # Get total DIMM DDR memory value from Os
            total_dimm_memory = sum(self.get_total_ddr_memory_data(dimm_data))
        elif mode == "2LM":
            # Get total DIMM DCPMM memory value from Os
            total_dimm_memory = sum(self.get_memory_mode_data(dimm_data))
        else:
            err_msg = "{} mode is not supported".format(mode)
            self._log.error(err_msg)
            raise RuntimeError

        # Convert the DIMM memory value to MB unit
        dimm_capacity = total_dimm_memory * 1024.0

        # Get the total System memory value from Os
        get_total_memory_data_win = self.getting_system_memory()[0].split(":")[1].strip("MB").strip().replace(",", "")

        # Get the threshold floor value
        threshold_dimm_capacity_floor = (dimm_capacity - (dimm_capacity * 0.05))

        # Get the threshold celling value
        threshold_dimm_capacity_celling = (dimm_capacity + (dimm_capacity * 0.05))

        # Compare Total DIMM Memory mode values with System memory value
        if not (threshold_dimm_capacity_floor < float(get_total_memory_data_win) < threshold_dimm_capacity_celling):
            err_msg = "Fail to verify {} provisioning configuration".format(mode)
            self._log.error(err_msg)
            raise RuntimeError(err_msg)
        self._log.info("Successfully verified {} provisioning configuration".format(mode))
        return True

    def getting_system_memory(self):
        """
        This function is used to parse the total physical memory and Available physical memory from Systeminfo
        :return: total physical memory value, available physical memory value
        """
        cmd_result = self._os.execute(self.SYSTEM_INFO_CMD, self._command_timeout)
        if cmd_result.cmd_failed():
            log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..". \
                format(self.SYSTEM_INFO_CMD, cmd_result.return_code, cmd_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        memory_total_value = re.findall("Total Physical Memory:.*", cmd_result.stdout)
        if not memory_total_value:
            raise RuntimeError("Failed to get the Total Memory Value from System Info")
        self._log.info("The Amount of Total Physical Memory reported by the OS is : {}"
                       .format(memory_total_value[0].strip()))

        memory_free_value = re.findall("Available Physical Memory:.*", cmd_result.stdout)
        if not memory_free_value:
            raise RuntimeError("Failed to get the Available Physical Memory Value from System Info")
        self._log.info("The Amount of Available Physical Memory reported by the OS is : {}"
                       .format(memory_free_value[0].strip()))

        return memory_total_value[0].strip(), memory_free_value[0].strip()

    def verify_lm_provisioning_configuration_linux(self, dimm_data, system_total_memory, mode):
        """
        Function to verify if system is LM provisioned or not for Linux Os

        :param dimm_data: output of DIMM info data from IPMCTL command
        :param system_total_memory: system memory data from Os
        :param mode: Provisioning mode expected values are "1LM" or "2LM"
        :return : true on success
        :raise: RuntimeError
        """
        total_dimm_memory = None
        if mode == "1LM":
            # Get total DIMM DDR memory value from Os
            total_dimm_memory = sum(self.get_total_ddr_memory_data(dimm_data))
        elif mode == "2LM":
            # Get total DIMM DCPMM memory value from Os
            total_dimm_memory = sum(self.get_memory_mode_data(dimm_data))
        else:
            err_msg = "{} mode is not supported".format(mode)
            self._log.error(err_msg)
            raise RuntimeError

        # Convert the DIMM memory value to MB unit
        dimm_capacity = total_dimm_memory * 1024.0

        # Get the total System memory value from Os
        get_total_memory_data_linux = self.get_total_system_memory_data_linux(system_total_memory)

        # Get the threshold floor value
        threshold_dimm_capacity_floor = (dimm_capacity - (dimm_capacity * 0.05))

        # Get the threshold celling value
        threshold_dimm_capacity_celling = (dimm_capacity + (dimm_capacity * 0.05))

        # Compare Total DIMM Memory mode values with System memory value
        if not (threshold_dimm_capacity_floor < get_total_memory_data_linux < threshold_dimm_capacity_celling):
            err_msg = "Fail to verify {} provisioning configuration".format(mode)
            self._log.error(err_msg)
            raise RuntimeError(err_msg)
        self._log.info("Successfully verified {} provisioning configuration".format(mode))
        return True

    def copy_test_file_from_hard_disk_to_pmem_drive(self, pmem_list):
        """
        This function to copy the 5GB Test file from the hard disk to the persistent memory

        :param pmem_list: persistent memory list
        :return: True on success
        """

        if not pmem_list:
            raise content_exceptions.TestFail("Received empty list of pmem disk\n{}".format(pmem_list))
        else:
            if OperatingSystems.LINUX in self._os.os_type:
                # File path in Hard disk
                source_test_file_path = Path(os.path.join(self.ROOT, self.TEST_FILE_NAME)).as_posix()

                for each_mount_data in pmem_list:
                    # File path in pmem disk
                    destination_test_file_path = Path(os.path.join(each_mount_data, self.TEST_FILE_NAME)).as_posix()
                    self.copy_test_file_from_source_to_destination(source_test_file_path, destination_test_file_path)

                    self._log.info("Copied TEST FILE to the Hard disk from pmem disk mount point : {}".
                                   format(each_mount_data))

            elif OperatingSystems.WINDOWS in self._os.os_type:
                # File path in hard disk
                source_test_file_path = os.path.join(self.C_DRIVE_PATH, self.TEST_FILE_NAME)
                for each_drive_letter in pmem_list:
                    # File Path in Pmem Disk
                    destination_test_file_path = os.path.join(each_drive_letter + ':\\', self.TEST_FILE_NAME)
                    self.copy_test_file_from_source_to_destination(source_test_file_path, destination_test_file_path)
                    self._log.info("Successfully copied the file {}, from {} to {}".format(self.TEST_FILE_NAME,
                                                                                           self.C_DRIVE_PATH,
                                                                                           each_drive_letter))
        return True

    def copy_test_file_from_pmem_drive_to_hard_disk(self, pmem_list):
        """
        This function to copy the 5GB Test file from the persistent memory disk to the Hard disk.

        :param pmem_list: persistent memory list
        :return: True on success
        """

        if not pmem_list:
            raise content_exceptions.TestFail("Received empty list of pmem disk\n{}".format(pmem_list))
        else:
            if OperatingSystems.LINUX in self._os.os_type:
                # File path in Hard disk
                destination_test_file_path = Path(os.path.join(self.ROOT, self.TEST_FILE_NAME)).as_posix()

                for each_mount_data in pmem_list:
                    # File path in pmem disk
                    source_test_file_path = Path(os.path.join(each_mount_data, self.TEST_FILE_NAME)).as_posix()
                    self.copy_test_file_from_source_to_destination(source_test_file_path, destination_test_file_path)

                    self._log.info("Copied TEST FILE to the Hard disk from pmem disk mount point : {}".
                                   format(each_mount_data))

            elif OperatingSystems.WINDOWS in self._os.os_type:
                # File path in hard disk
                destination_test_file_path = os.path.join(self.C_DRIVE_PATH, self.TEST_FILE_NAME)
                for each_drive_letter in pmem_list:
                    # File Path in Pmem Disk
                    source_test_file_path = os.path.join(each_drive_letter + ':\\', self.TEST_FILE_NAME)
                    self.copy_test_file_from_source_to_destination(source_test_file_path, destination_test_file_path)
                    self._log.info("Successfully copied the file {}, from {} to {}".format(self.TEST_FILE_NAME,
                                                                                           each_drive_letter,
                                                                                           self.C_DRIVE_PATH))
        return True

    def copy_test_file_from_source_to_destination(self, source_test_file_path, destination_test_file_path):
        """
        This function to copy file from source path to destination path.

        :param source_test_file_path: source path , file to be copy
        :param destination_test_file_path: destination path , file to be copied
        :return: True on success
        """
        try:
            if OperatingSystems.LINUX in self._os.os_type:
                self._common_content_lib.execute_sut_cmd(
                    "yes | cp {} {}".format(source_test_file_path, destination_test_file_path),
                    "copy file from source to the destination", self._command_timeout)

            elif OperatingSystems.WINDOWS in self._os.os_type:
                self._common_content_lib.execute_sut_cmd(
                    "copy /Y {} {}".format(source_test_file_path, destination_test_file_path),
                    "copy file from source to the destination", self._command_timeout, self.C_DRIVE_PATH)
            return True

        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise ex

    def verify_size_with_smbios_config(self):
        """
        This function is used to verify size and locator output from dmidecode -t 17 with smbios_config.xml.
        """
        return_value = []
        dict_dmi_decode_from_tool = self._memory_provider.get_memory_slots_details()

        dict_dmi_decode_from_spec = self._smbios_config.get_smbios_table_dict()
        self._log.info("Template SMBIOS information.. \n {}".format(dict_dmi_decode_from_spec))
        num_dmi_type17 = 0
        dmi_comparison_results = True

        for key in dict_dmi_decode_from_tool.keys():
            if dict_dmi_decode_from_tool[key]['DMIType'] == 17:
                num_dmi_type17 = num_dmi_type17 + 1
                memory_device_num = 'MemoryDevice{}'.format(num_dmi_type17)

                self._log.info("{}".format(memory_device_num))

                self._log.info("OS reported Locator information - {} || Configuration file reported Locator "
                                "information  - {}"
                                .format(dict_dmi_decode_from_tool[key]['Locator'],
                                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Locator']))
                self._log.info("OS reported Size information - {} || Configuration file reported Size "
                                "information  - {}"
                                .format(dict_dmi_decode_from_tool[key]['Size'],
                                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Size']))

                if dict_dmi_decode_from_tool[key]['Locator'] != \
                         dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Locator'] or \
                         dict_dmi_decode_from_tool[key]['Size'] != \
                         dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Size']:
                     self._log.error("DMI TYPE 17 on {} information are not correct!".format(memory_device_num))
                     dmi_comparison_results = False
                else:
                     self._log.info("DMI TYPE 17 on {} information has been verified "
                                    "successfully!".format(memory_device_num))
        return_value.append(dmi_comparison_results)
        if not all(return_value):
            raise content_exceptions.TestFail("memory locator or size is incorrect ...")
        return all(return_value)

    def get_total_dimm_memory_data(self, result_data):
        """
        Function to get the Total DIMM capacity value before provisioning

        :param result_data: Dimm information.
        :return: capacity_list
        """
        capacity_list = []
        match_data = re.findall("0x.*", result_data)
        if len(match_data) != 0:
            for element in match_data:
                capacity_list.append(float(element.split("|")[1].strip().split(" ")[0]))
        self._log.info("Total DIMM DCPMM memory capacity values are: {}".format(capacity_list))
        return capacity_list

    def verify_cr_memory_with_config(self, show_dimm):
        """
        This function is used to verify the CR memory with the config.

        :param: show_dimm
        :return: True on success
        """
        # Get the Capacity of all dimms.
        total_dimm_capacity = sum(self.get_total_dimm_memory_data(show_dimm))

        self._log.info("Total dimm capacity shown from OS level - {}".format(int(total_dimm_capacity)))
        self._log.info("Total dimm capacity as per configuration - {}".format(self._dcpmm_mem_capacity))

        # memory with variance
        mem_total_with_variance_config = (self._dcpmm_mem_capacity - (self._dcpmm_mem_capacity * self._variance_percent))

        self._log.info("Total dimm capacity as per configuration with variance is - {}".format(
            mem_total_with_variance_config))

        if int(total_dimm_capacity) < mem_total_with_variance_config or int(total_dimm_capacity) > \
                self._dcpmm_mem_capacity:
            raise content_exceptions.TestFail("Total dcpmm dimm Capacity is not same as installed capacity from"
                                              " configuration.")
        elif int(total_dimm_capacity) >= int(mem_total_with_variance_config):
            self._log.info("Total dcpmm dimm Capacity is same as installed capacity from configuration.")

        return True
