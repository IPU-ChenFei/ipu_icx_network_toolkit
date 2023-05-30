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
import pandas as pd

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider

from src.lib.common_content_lib import CommonContentLib
from src.lib.memory_dimm_info_lib import MemoryDimmInfo
from src.lib.bios_util import BiosUtil
from src.lib.install_collateral import InstallCollateral
from src.lib.content_configuration import ContentConfiguration
from src.lib.windows_event_log import WindowsEventLog
from src.lib.mlc_utils import MlcUtils
from src.lib.fio_utils import FIOCommonLib


class CrPerformance(BaseTestCase):
    """
    Base class for all CR Performance test cases
    """

    IPMCTL_CMD_CREATE_DISK_SPD_FILE = " show -dimm -performance"
    IPMCTL_CMD_SHOW_ERROR_THERMAL = " show -error Thermal -dimm"
    IPMCTL_CMD_SHOW_ERROR_MEDIA = " show -error Media -dimm"
    C_DRIVE_PATH = "C:\\"
    ROOT = "/root"

    DISK_SPD_CMD = r'.\diskspd.exe -r -c8192K -b8K -o4 -t4 -h -d900 -w25 -Z1G -L {0}:\iotest.dat > DiskSpeedOut_{0}.txt'
    DISK_SPD_LOG_FILE = "DiskSpeedOut_{}.txt"
    DISK_SPD_TEMPLATE_FILE = r"DiskSpeedOut.txt"
    DISK_SPD_INDEX_PARAMS = ["Total IO", "Read IO", "Write IO", "%-ile"]
    PARAM_NAMES = ["bytes", "I/Os", "MiB/s", "I/O per s"]

    VC_RE_DIST_EXE = "vcredist_"
    STREAM_REGEX_LIST = [r'\ACopy.*', r'\AScale.*', r'\AAdd.*', r'\ATriad.*']

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file):
        """
        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param bios_config_file: configuration file of BIOS

        :return: None
        :raises: None
        """
        super(CrPerformance, self).__init__(test_log, arguments, cfg_opts)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)

        self._common_content_lib = CommonContentLib(self._log, self._os)

        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, bios_config_file)
        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)

        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._mlc_runtime = self._common_content_configuration.memory_mlc_run_time()
        self._stream_runtime = self._common_content_configuration.memory_stream_threshold_value()
        self._stream_threshold_value = self._common_content_configuration.memory_stream_threshold_value()
        self._disk_spd_command_timeout = self._common_content_configuration.get_disk_spd_command_time_out()
        self._stream_mp_command_timeout = self._common_content_configuration.stream_mp_run_time()
        self._stream_mp_threshold_value = self._common_content_configuration.stream_mp_threshold_value()
        self._stream_threshold_value = self._common_content_configuration.memory_stream_threshold_value()

        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)
        self._windows_event_log = WindowsEventLog(self._log, self._os)
        self.ipmctl_cmd_name = self._common_content_lib.get_ipmctl_name()

        self._mlc = MlcUtils(self._log)
        self._fio = FIOCommonLib(self._log, self._os, cfg_opts)

    def verify_pre_post_stress_performance_result(self, pre_data_frame, post_data_frame):
        """
        This function is used to verify pre DCPMM performance and post DCPMM performance

        :param pre_data_frame : Pre DCPMM Data frame
        :param post_data_frame : Post DCPMM Data frame

        :return : True if verified successfully else False
        """
        param_names = ['MediaReads', 'MediaWrites', 'ReadRequests', 'WriteRequests', 'TotalMediaReads',
                       'TotalMediaWrites', 'TotalReadRequests', 'TotalWriteRequests']
        flag_data = False
        for element in param_names:
            performance_data_pre = pre_data_frame[0][element].values.tolist()
            performance_data_post = post_data_frame[0][element].values.tolist()
            for iteration in range(0, len(performance_data_pre)):
                if not (int(performance_data_post[iteration], 16) > int(performance_data_pre[iteration], 16)):
                    flag_data = True
                    self._log.error("Pre Stress value of {} was {} ".format(element, performance_data_pre[iteration]))
                    self._log.error("Post Stress value of {} is {} ".format(element, performance_data_post[iteration]))
        if flag_data:
            self._log.error("Failed to verify Pre and Post Stress Performance result Data due to above data."
                            "As Post stress Performance data is smaller than Pre stress Performance data")
            return False
        self._log.info("Successfully verified Pre and Post Stress Performance result Data."
                       "As Post stress Performance data is greater than Pre stress Performance data")
        return True

    def create_dimm_performance_result(self, mode):
        """
        This function is used to measure DCPMM performance

        :Param mode:  post or pre
        """
        result = self._common_content_lib.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_CREATE_DISK_SPD_FILE,
            "create {} Stress Dimm Performance result".format(mode), self._command_timeout)
        if result:
            self._log.info("Successfully created the {} Stress Dimm Performance result".format(mode))
            memory_info_obj = MemoryDimmInfo(result, performance=True)

            return memory_info_obj.df_dimm_performance_data

    def idle_latency_mlc(self, mlc_path, mlc_log_folder_path, drive_letters):
        """
        This function is uses to measure the idle latencies for each persistent memory

        :param mlc_path: path of the mlc tool
        :param mlc_log_folder_path: Path of the mlc log folder
        :param drive_letters:  Drive letters for the persistent memory

        :return: All latency log files of DCPMM
        """
        log_files_list = []
        for each_drive_letter in drive_letters:
            total_log_path = os.path.join(mlc_log_folder_path, "1lm_latency_{}.log".format(each_drive_letter))
            log_file_name = "1lm_latency_{}.log".format(each_drive_letter)
            log_files_list.append(log_file_name)
            command = "mlc.exe -Z --idle_latency -c0 -J{}: >> {}".format(each_drive_letter,
                                                                         total_log_path)
            self._log.info("Executing the command  : {}".format(command))
            self._common_content_lib.execute_sut_cmd(
                command, "Idle latency for each Pmem DIMM", self._command_timeout, cmd_path=mlc_path)

        return log_files_list

    def execute_disk_spd_command(self, drive_letter, executable_path):
        """
        This function is used to execute the DiskSpd command and store it into a log file

        :param drive_letter : drive letter of the DCPMM drive
        :param executable_path : installed path of DiskSpd tool

        :return : True and DiskSpd log file name
        """
        try:
            self._common_content_lib.execute_sut_cmd(
                self.DISK_SPD_CMD.format(drive_letter),
                "Executing DiskSpd command",
                self._disk_spd_command_timeout,
                cmd_path=executable_path)
            self._log.info("Successfully ran DiskSpd command for {} drive".format(drive_letter))
            return True, self.DISK_SPD_LOG_FILE.format(drive_letter)
        except Exception as ex:
            self._log.error("Exception occurs while running 'execute_disk_spd_command' function")
            raise ex

    def get_all_index(self, result_file_path):
        """
        This function is used to get all the index lines from the result files according to the params

        :param result_file_path : DiskSpd log file path
        :return : index_list
        :raise: ex if exception occurs
        """
        try:
            index_list = list()
            with open(result_file_path, 'r+') as file_pointer:
                for index, line in enumerate(file_pointer):
                    for element in self.DISK_SPD_INDEX_PARAMS:
                        match = re.findall(element, line)
                        if match:
                            if element == "%-ile":
                                index_list.append(index - 3)
                            else:
                                index_list.append(index)
            return index_list
        except Exception as ex:
            self._log.error("Exception occurred while running the 'get_all_index' function")
            raise ex

    def create_disk_spd_data_frame(self, log_file_path):
        """
        This function is used to filter out all the data according to the indexes and put in to a dataframe

        :param log_file_path : DiskSpd log file path
        :return final_df: Data frame with all the combined data
        :raise: ex if exception occurs
        """
        flag = False
        final_df = None
        data_list = list()
        try:
            index_list_inner = self.get_all_index(log_file_path)
            with open(log_file_path, 'r+') as file_pointer:
                for index, line in enumerate(file_pointer):
                    for i in range(0, len(index_list_inner)):
                        start_index = index_list_inner[i]
                        if i == len(index_list_inner) - 1:
                            break
                        else:
                            end_index = index_list_inner[i + 1]
                        if start_index < index < end_index - 1:
                            if "--" not in line and "total: " not in line:
                                data = line.strip().split("|")
                                if "thread " in data:
                                    if not flag:
                                        data_list.append(data)
                                        flag = True
                                else:
                                    data_list.append(data)
                            final_df = pd.DataFrame(data_list)
            final_df.columns = final_df.iloc[0]
            final_df = final_df.drop(final_df.index[0])
            final_df.columns = [col.strip() for col in final_df.columns]
            return final_df
        except Exception as ex:
            self._log.error("Exception occurred while running the 'create_disk_spd_data_frame' function")
            raise ex

    def verify_disk_spd_data(self, test_file):
        """
        This function is used to verify the current DiskSpd log file with the Template log file

        :param test_file : DiskSpd log file path
        :return:True in success
        :raise: RuntimeError
        """
        result = False

        #  Get Template DiskSpd log file path
        template_file = self._install_collateral.download_tool_to_host(tool_name=self.DISK_SPD_TEMPLATE_FILE)

        #  Get the template DiskSpd Data Frame
        template_data_frame = self.create_disk_spd_data_frame(template_file)
        self._log.info("Template DiskSpd Data Frame: \n{}".format(template_data_frame))

        #  Get the Current DiskSpd Data Frame
        test_data_frame = self.create_disk_spd_data_frame(test_file)
        self._log.info("Current Test DiskSpd Data Frame: \n{}".format(test_data_frame))
        for elements in self.PARAM_NAMES:
            template_data_list = template_data_frame[elements].values.tolist()
            threshold_data_list = list(map(lambda x: float(x) * 0.5, template_data_list))
            test_data_list = test_data_frame[elements].values.tolist()
            result = all(float(test_data_list[index]) > threshold_data_list[index] for index in
                         range(0, len(test_data_frame)))
        if not result:
            error_msg = "DiskSpd log verification failed due to all the parameter values are not satisfying the " \
                        "passing condition"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully verified the DiskSpd log file as all parameter values are satisfying the "
                       "passing condition")
        return True

    def create_fiotest_mount_points(self, mount_list_data):
        """
        Function to create a list of drive letters concatenated with fio test string.

        :param mount_list_data: pmem drives
        :return mount_data: all mount points
        """
        letter_list = []

        for each_mount_data in mount_list_data:
            letter_list.append(r"--filename={}/fiotest ".format(each_mount_data))

        mount_data = "".join(letter_list)
        return mount_data

    def disk_partition_linux(self, pmem_device_list, partition_command):
        """
        Function to run the command to do the partition by 'parted' on linux SUT

        :param: pmem_device_list
        :return: partition result
        """
        partition_result = ""
        for index in range(0, len(pmem_device_list)):
            partition_result = self._common_content_lib.execute_sut_cmd(partition_command.format(
                pmem_device_list[index]), "Create a generic "
                "partition on each PMEM device "
                "using parted", self._command_timeout)
        if partition_result != "":
            self._log.info("Successfully created a generic partition on each PMEM device using parted")
        return partition_result

    def create_ext4_filesystem(self, pmem_device_list, command):
        """
        Function to create an ext4 Linux file system on each enumerated PMEM  device on linux SUT

        :param: pmem_device_list
        :return: stdout data
        """
        ext4_result_data = ""
        for index in range(0, len(pmem_device_list)):
            ext4_result_data = self._common_content_lib.execute_sut_cmd(
                command.format(pmem_device_list[index]), "Create an ext4 Linux file system on each enumerated",
                self._command_timeout)
        if len(ext4_result_data) != 0:
            self._log.info("Successfully created an ext4 Linux file system on each enumerated block..\n{}".
                           format(ext4_result_data))
        return ext4_result_data

    def execute_stream_supported_files_win(self, file_path):
        """
        Function to execute vcredist installers, which will support Stream_MP to generate log files

        :param file_path: folder path where these executable files are present
        :return: None
        """
        self._common_content_lib.execute_sut_cmd("{}x64.exe /q".format(self.VC_RE_DIST_EXE),
                                                 "Execute {}x64.exe file".format(self.VC_RE_DIST_EXE),
                                                 self._command_timeout, cmd_path=file_path)
        self._log.info("Successfully executed {}x64.exe\n".format(self.VC_RE_DIST_EXE))
        self._common_content_lib.execute_sut_cmd("{}x86.exe /q".format(self.VC_RE_DIST_EXE),
                                                 "Execute {}x86.exe file".format(self.VC_RE_DIST_EXE),
                                                 self._command_timeout, cmd_path=file_path)
        self._log.info("Successfully executed {}x86.exe\n".format(self.VC_RE_DIST_EXE))

    def execute_stream_mp_tool_win(self, stream_tool_path):
        """
        Function to execute Stream_MP tool and generate the log files

        :param stream_tool_path: folder path where Stream_Mp file is present
        :return: True on Success
        :raise: RuntimeError
        """

        #  Get the decimal no of logical CPUs
        no_of_cpu_dec_val = self._common_content_lib.get_core_count_from_os()[0]

        #  Convert the no of logical CPU values to HEX patterns
        no_of_cpu_hex_val = int(no_of_cpu_dec_val / 4) * 'f'

        #  Execute Stream Mp batch file to generate the log files
        result = self._common_content_lib.execute_sut_cmd("launch_mpstream_256.bat {} {}".format(no_of_cpu_hex_val,
                                                                                                 no_of_cpu_dec_val),
                                                          "Execute launch_spstream_256.bat file",
                                                          self._stream_mp_command_timeout, cmd_path=stream_tool_path)
        if result == "":
            error_msg = "Fail to execute launch_mpstream_256.bat file"
            self._log.error(error_msg)
            raise RuntimeError

        self._log.info("Successfully executed launch_mpstream_256.bat\n {}".format(result))
        return True

    def verify_stream_opt_logs(self, file_path):
        """
        Function to verify Stream_MP output log files

        :param file_path: folder path where Stream_Mp log file is present
        :return: True on Success
        :raise: RuntimeError
        """
        stream_measurement_values = []
        with open(file_path, 'r+') as stream_fp:
            stream_data_list = stream_fp.readlines()
            for stream_data in stream_data_list:
                #  Get the matched data from the Stream log files
                stream_data_match = self.find_given_string(self.STREAM_REGEX_LIST, stream_data)
                if stream_data_match:
                    stream_measurement_values.append(stream_data_match[0].split("\t")[1].strip())

        #  Verify the current values with the given threshold values
        if float(min(stream_measurement_values)) < self._stream_mp_threshold_value:
            err_msg = "Stream memory bandwidth values are lesser than the given threshold values on Stream log file" \
                      ": {}".format(file_path)
            self._log.error(err_msg)
            raise RuntimeError(err_msg)

        self._log.info("Successfully verified the Stream Log file : {}".format(file_path))
        return True

    @staticmethod
    def find_given_string(regex_list, target_string):
        """
        Method to verify Stream_MP output log files

        :param regex_list: list of regular expressions
        :param target_string: the string where the search operation will happen
        :return return_match_data: list of the matched data
        """
        return_match_data = []
        for regex in regex_list:
            if re.match(regex, target_string):
                match_data = re.findall(regex, target_string)
                return_match_data = [data for data in match_data]
        return return_match_data

    def execute_mlc_command(self, mlc_command, mlc_cmd_log_path, mlc_execute_path):
        """
        This function is used to execute the MLC commands

        :param: mlc_command: mlc command to be executed
        :param: mlc_cmd_log_path: log file name
        :param: mlc_execute_path: path of the mlc tool

        :return: True if MLC command is executed.
        """
        try:
            mlc_cmd = mlc_command.format(mlc_cmd_log_path)
            self._log.info("Executing MLC Command : {}".format(mlc_cmd))
            self._common_content_lib.execute_sut_cmd(mlc_cmd,
                                                     "Executing MLC Command", self._mlc_runtime, mlc_execute_path)
            return True
        except Exception as ex:
            self._log.error("Exception occur while running mlc command")
            raise ex

    def execute_stream_command(self, stream_cmd, stream_cmd_log_path, stream_path):
        """
        This function is used to execute the Stream commands

        :param stream_cmd: stream command to be executed
        :param stream_cmd_log_path: stream log file name
        :param stream_path: path of the stream tool

        :return: True if stream command is executed.
        """
        try:
            stream_cmd = stream_cmd.format(stream_cmd_log_path)
            self._log.info("Executing Stream Command : {}".format(stream_cmd))
            self._common_content_lib.execute_sut_cmd(stream_cmd,
                                                     "Executing stream cmd", self._stream_runtime, stream_path)
            return True
        except Exception as ex:
            self._log.error("Exception occur while running stream command")
            raise ex

    def verify_stream_data_linux(self, file_path):
        """
        Verify All the current Data with the Threshold value for stream runme.sh.

        :param file_path: log file path in host
        :return: True in Success else False
        """
        result_flag = True
        stream_measurement_values = []
        with open(file_path, 'r+') as stream_fp:
            stream_data_list = stream_fp.readlines()
            for stream_data in stream_data_list:
                #  Get the matched data from the Stream log files
                stream_data_match = self.find_given_string(self.STREAM_REGEX_LIST, stream_data)
                for each_match in stream_data_match:
                    stream_measurement_values.append(float(each_match.split(":")[1].strip().split(" ")[0].strip()))

        self._log.info("Stream output values in GB/s for copy, Scale, Add, Triad are : {}"
                       .format(stream_measurement_values))

        #  Verify the current values with the given threshold values
        if min(stream_measurement_values) < self._stream_threshold_value:
            err_msg = "Stream output values are less than the given threshold value {} (GB/s) in log file" \
                      " :\n{}".format(self._stream_threshold_value, file_path)
            self._log.error(err_msg)
            result_flag = False
        else:
            self._log.info("Success as Stream values greater than threshold value {} (GB/s) in log file : \n{} ".
                           format(self._stream_threshold_value, file_path))
        return result_flag
