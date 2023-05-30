"""
!/usr/bin/env python
################################################################################
INTEL CONFIDENTIAL
Copyright Intel Corporation All Rights Reserved.

The source code contained or described herein and all documents related to
the source code ("Material") are owned by Intel Corporation or its suppliers
or licensors. Title to the Material remains with Intel Corporation or its
suppliers and licensors. The Material may contain trade secrets and proprietary
and confidential information of Intel Corporation and its suppliers and
licensors, and is protected by worldwide copyright and trade secret laws and
treaty provisions. No part of the Material may be used, copied, reproduced,
modified, published, uploaded, posted, transmitted, distributed, or disclosed
in any way without Intel's prior express written permission.

No license under any patent, copyright, trade secret or other intellectual
property right is granted to or conferred upon you by disclosure or delivery
of the Materials, either expressly, by implication, inducement, estoppel or
otherwise. Any license under such intellectual property rights must be express
and approved by Intel in writing.
#################################################################################
"""
import os
import csv
import glob
from pathlib import Path
from src.lib import content_exceptions
from src.lib.content_configuration import ContentConfiguration
from src.seamless.lib.seamless_common import SeamlessBaseTest
from src.seamless.tests.bmc.constants.pm_constants import PMWindows, PMLinux, \
    SocwatchWindows, SocwatchLinux, SocwatchConstants, CoreCStates
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.seamless.tests.bmc.constants import pm_constants
from collections import OrderedDict


class PmCommon(SeamlessBaseTest):
    """
    This Class is Used as Common Class For all the PM Test Cases
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
         Create an instance of PmCommon
        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super().__init__(test_log, arguments, cfg_opts)
        self.reboot_timeout = \
            self._common_content_configuration.get_reboot_timeout()
        self.csv_file_path = os.path.join(self.log_dir, "PTU")
        os.makedirs(self.csv_file_path)
        self.ptu_tool_lin = self._common_content_configuration.get_ptu_lin_tool_file_path()
        self.ptu_tool_win = self._common_content_configuration.get_ptu_win_tool_file_path()

    def check_ptu_tool(self):
        """
        This function will check ptu tool is available in SUT
        :return: True if all files are present in PTU directory or False
        """
        self._log.info("Checking the PTU Tool in SUT")
        if self._os_type == OperatingSystems.WINDOWS:
            command = f"cd {PMWindows.PTU_TOOL_SUT_PATH}\\" \
                      f"{PMWindows.PTU_TOOL_FOLDER_NAME} && dir /b "
            output = self.run_ssh_command(command, timeout_seconds=pm_constants.TIMEOUT_SEC)
            file = list(output.stdout.split("\n"))
            if PMWindows.PTU_TOOL_FILE_NAME in file:
                self._log.info(f"{PMWindows.PTU_TOOL_FILE_NAME} is present")
            else:
                self._log.info(f"PTU TOOL is not present.{PMWindows.PTU_TOOL_FILE_NAME} "
                               f"is missing from PTU tool")
                return False
        else:
            command = f"cd {PMLinux.PTU_TOOL_SUT_PATH_LINUX}/{PMLinux.PTU_TOOL_FOLDER_NAME} && ls"
            output = self.run_ssh_command(command, timeout_seconds=pm_constants.TIMEOUT_SEC)
            self._log.debug(f"PTU Tool DIR output : {output.stdout}")
            for file_name in PMLinux.PTU_TOOL_CONTENT:
                if file_name in output.stdout:
                    self._log.info(f"{file_name} is present")
                else:
                    self._log.info(f"PTU TOOL is not present.{file_name} is missing from PTU tool")
                    return False
        return True

    def install_ptu_tool(self):
        """
        This method will copy and install ptu tool into sut
        """
        self._log.info("Installing PTU tool")
        if self._os_type == OperatingSystems.WINDOWS:
            self.run_ssh_command("mkdir {}".format(PMWindows.PTU_TOOL_SUT_PATH))
            self.os.copy_local_file_to_sut(self.ptu_tool_win,
                                           PMWindows.PTU_TOOL_SUT_PATH)
            command = f"cd {PMWindows.PTU_TOOL_SUT_PATH} && tar xvzf " \
                      f"{PMWindows.PTU_TOOL_ZIP_FILE_NAME}"
            self.run_ssh_command(command, timeout_seconds=pm_constants.TIMEOUT_SEC)
            cmd = f'cd {PMWindows.PTU_TOOL_SUT_FOR_INSTALLING} && ' \
                  f'"{PMWindows.PTU_TOOL_FILE_NAME}" -s'
            result = self.run_ssh_command(cmd, self._command_timeout)
            self._log.info(f"ptu tool deatils :{result.stdout}")
        else:
            self.run_ssh_command("cd {} && mkdir {} ".format(PMLinux.PTU_TOOL_SUT_PATH_LINUX, PMLinux.PTU_TOOL_FOLDER_NAME))
            self.os.copy_local_file_to_sut(self.ptu_tool_lin, PMLinux.PTU_TOOL_FOLDER_NAME)
            ptu_path = self.ptu_tool_lin.split('\\')[-1]
            command = "cd {} && tar -xvzf {}".format(PMLinux.PTU_CSV_FILE_PATH_SUT, ptu_path)
            self.run_ssh_command(command, timeout_seconds=pm_constants.TIMEOUT_SEC)

    def deleting_file(self):
        """
        This function will delete the previous csv log files which are present in SUT
        """
        if self._os_type == OperatingSystems.WINDOWS:
            command = f"cd {PMWindows.PTU_TOOL_SUT_PATH}\\ && del *.csv"
        else:
            command = f"cd {PMLinux.PTU_TOOL_SUT_PATH_LINUX}/" \
                      f"{PMLinux.PTU_TOOL_FOLDER_NAME} && rm *.csv"
        output = self.run_ssh_command(command, timeout_seconds=pm_constants.TIMEOUT_SEC)
        self._log.info(f"Older .csv files deleted: {output.stdout}")

    def execute_ptu_tool(self):
        """
        This function will execute the PTU tool application
        """
        if self._os_type == OperatingSystems.WINDOWS:
            self._log.info(f"Starting the PTU Tool command '{self.ptu_cmd.format(PMWindows.PTU_TOOL_SUT_PATH)}'")
            self.os.execute_async(self.ptu_cmd.format(PMWindows.PTU_TOOL_SUT_PATH), cwd=PMWindows.EXECUTOR_PATH)
            cmd_line = f'"{PMWindows.EXECUTOR_PATH}" {self.put_cmd.format(PMWindows.PTU_TOOL_SUT_PATH)}'
            self._log.info(f"PTU executing command %s: {cmd_line}")
        else:
            self._log.info(f"Starting the PTU Tool command '{self.ptu_cmd}'")
            self.os.execute_async(self.ptu_cmd, cwd=PMLinux.EXECUTOR_PATH)
            cmd_line = f'"{PMLinux.EXECUTOR_PATH}" {self.ptu_cmd}'
            self._log.info(f"PTU executing command %s: {cmd_line}")

    def check_ptu_app_running(self):
        """
        This method check whether application is running or not
        :return : check_app_running method returns False
        if particular application is not running else True
        """
        if self._os_type == OperatingSystems.WINDOWS:
            self._log.info("Checks the app status")
            process_running = self._common_content_lib.execute_sut_cmd(
                f'TASKLIST /FI "IMAGENAME eq {PMWindows.PTU_TOOL_FOLDER_NAME}*"'
                , "Checks the app status",
                self._command_timeout)
            if str(PMWindows.PTU_TOOL_FOLDER_NAME).lower() in str(process_running).lower():
                self._log.info("PTU application running")
                return True
            raise RuntimeError("PTU application not running")
        else:
            cmd_line = f"ps -ef |grep {PMLinux.PTU_TOOL_FILE_NAME}"
            command_result = self._common_content_lib.execute_sut_cmd\
                (cmd_line, "Checks the app status",
                 self._command_timeout)
            self._log.debug(command_result)
            if PMLinux.PTU_APP_NAME not in command_result:
                raise RuntimeError("PTU application not running")
            return True

    def kill_ptu_tool(self):
        """
        Terminate PTU process.
        :return : kill ptu app
        :raise: Raise RuntimeError Exception if failed to kill the PTU.
        """
        ret_code = None
        if self._os_type == OperatingSystems.WINDOWS:
            # we will ignore any exception
            ret_code = False
            try:
                if not PmCommon.check_ptu_app_running(self):
                    self._log.error(f"{PMWindows.PTU_TOOL_FOLDER_NAME} "
                                    f"stress tool is not running to kill")
                    return
                self._log.info(f"killing {PMWindows.PTU_TOOL_FOLDER_NAME} tool")
                kill_ptu = self.os.execute(f"taskkill /F /IM {PMWindows.PTU_TOOL_FOLDER_NAME}.exe",
                                           self._command_timeout)
                if kill_ptu.return_code == 0:
                    ret_code = True
                    self._log.debug(kill_ptu.stdout)
                else:
                    self._log.error(f"Failed to kill PTU application error:'{kill_ptu.stderr}'")
                kill_xpptumem = self.os.execute(f"taskkill /F /IM {PMWindows.PTU_XPPTMEM_FILE}.exe",
                                                self._command_timeout)
                if kill_xpptumem.return_code == 0:
                    ret_code = True
                    self._log.debug(kill_xpptumem.stdout)
                else:
                    self._log.error(f"Failed to kill PTU application error:'"
                                    f"{kill_xpptumem.stderr}'")
                self.stress_thread.join(pm_constants.COMMAND_TIMEOUT)
            except Exception as ex:
                self._log.debug(f"Failed to kill ptu with exception: '{ex}'")
        else:
            # we will ignore any exception
            try:
                if not PmCommon.check_ptu_app_running(self):
                    self._log.error(f"{PMLinux.PTU_TOOL_FILE_NAME} "
                                    f"stress tool is not running to kill")
                    return
                self._log.info(f"killing {PMLinux.PTU_TOOL_FILE_NAME} tool")
                ret_code = False
                path = PMLinux.PTU_CSV_FILE_PATH_SUT
                output = self._common_content_lib.execute_sut_cmd\
                    (PMLinux.KILL_PTU_CMD, PMLinux.KILL_PTU_CMD,
                     self._command_timeout, cmd_path=path)
                self._log.debug(f"PTU tool is killed in SUT: {output}")
                ret_code = output.return_code
                self._log.info(ret_code)
            except Exception as ex:
                self._log.debug(f"Failed to kill ptu with exception: '{ex}'")
        return ret_code

    def deleting_csv_files_in_host(self, cwd=None):
        """
        This function will delete the previous csv log files which are present in Host
        """
        if self._os_type == OperatingSystems.WINDOWS:
            command = f"cd {self.csv_file_path} && del *.csv"
            output = self._common_content_lib.execute_cmd_on_host(command, cwd=cwd)
            self._log.info(f"older .csv files deleted: {output}")

    def copy_csv_file_from_sut_to_host(self):
        """
        This method will copy csv file from sut to host
        """
        self._log.info("Copy the CSV file from SUT to Host")
        if self._os_type == OperatingSystems.WINDOWS:
            file1, file2 = PmCommon.finding_file(self)
            self.os.copy_file_from_sut_to_local(os.path.join(
                PMWindows.PTU_TOOL_SUT_PATH, file1), os.path.join(self.csv_file_path, file1))
            self.os.copy_file_from_sut_to_local(os.path.join(
                PMWindows.PTU_TOOL_SUT_PATH, file2), os.path.join(self.csv_file_path, file2))
            self._log.info(f"Files copied from SUT to HOST: {file1}, {file2}")
        else:
            file1, file2 = PmCommon.finding_file(self)
            file1path = "{}/{}".format(PMLinux.PTU_CSV_FILE_PATH_SUT, file1)
            file2path = "{}/{}".format(PMLinux.PTU_CSV_FILE_PATH_SUT, file1)
            self.os.copy_file_from_sut_to_local(file1path, os.path.join(self.csv_file_path, file1))
            self.os.copy_file_from_sut_to_local(file2path, os.path.join(self.csv_file_path, file2))
            self._log.info(f"Files copied from SUT to HOST: {file1}, {file2}")

    def finding_file(self):
        """
        The function will find the csv log files which are generated in SUT
        :return: The csv log file names
        """
        if self._os_type == OperatingSystems.WINDOWS:
            command = f"cd {PMWindows.PTU_TOOL_SUT_PATH} && dir /b "
            output = self.run_ssh_command(command, timeout_seconds=pm_constants.TIMEOUT_SEC)
            csv_files = list(filter(None, self.run_ssh_command(command).stdout.split(" ")))
        else:
            self._log.info("Checking file")
            cmd = f"cd {PMLinux.PTU_TOOL_SUT_PATH_LINUX}/{PMLinux.PTU_TOOL_FOLDER_NAME} && ls"
            self.run_ssh_command(cmd, self._command_timeout)
            csv_files = list(filter(None, self.run_ssh_command(cmd).stdout.split(" ")))
        if not csv_files[0]:
            raise RuntimeError("File is not present")
        csv_files1 = csv_files[0].split("\n")
        csv_files2 = list(filter(lambda f: f.endswith(".csv"), csv_files1))
        self._log.info(f"Print the .csv files: {csv_files2}")
        index_length = len(csv_files2)
        self._log.info(f"Print the file index length: {index_length}")
        if index_length == 2:
            file1 = csv_files2[0]
            file2 = csv_files2[1]
            return file1, file2
        else:
            self._log.info(f"Print the .csv files: {csv_files2}")
            raise RuntimeError("There are more than two files in the list")

    def read_csv_file(self):
        """
        This function reads the csv file and verify the cpu core and frequency values
        """
        if self._os_type == OperatingSystems.WINDOWS:
            path = self.csv_file_path
            files = glob.glob(path + "/*_ptumon.csv")
            files1 = files[0]
            self._log.info(files1)
            my_file = Path(files1)
            if my_file.is_file():
                self._log.info("File exist")
            else:
                raise RuntimeError("File does not exist")
            with open(files1, 'r') as file:
                #This to ignore the null values in the data
                reader = csv.reader(x.replace('\0', '') for x in file)
                header = next(reader)
                self._log.debug(header)
                count = count1 = count2 = count3 = count4 = 0
                for column in reader:
                    try:
                        values = (column[9], column[11], column[5], column[6])
                        C0 = int(float(column[9]))
                        C6 = int(float(column[11]))
                        p_state = int(float(column[5]))
                        uncore = int(float(column[6]))
                        if p_state > pm_constants.p_state_core_frequency:
                            self._log.debug("All the core frequencies"
                                            "are increased to max frequency")
                            count3 = count3 + 1
                            if not p_state > pm_constants.p_state_core_frequency:
                                raise RuntimeError("Core frequency values are not  as expected")
                        if uncore > pm_constants.uncore_frequency:
                            self._log.debug("Uncore value has been increased")
                            count4 = count4 + 1
                            if not uncore > pm_constants.uncore_frequency:
                                raise RuntimeError("UnCore frequency "
                                                   "values are not as expected")
                        if C0 <= int(self.c0_value) and C6 >= int(self.c6_value):
                            self._log.info("values are as expected")
                            count = count + 1
                            if not C0 <= self.c0_value and C6 >= self.c6_value:
                                raise RuntimeError("C0 & C6 values are not as expected")
                    except:
                        count2 = count2 + 1
            self._log.info(f"Number of column values as expected for c0 & c6: "
                           f"{count}")
            self._log.info(f"Number of total columns: {count2}")
            self._log.info(f"Number of all core frequencies are increased to max frequency: "
                           f"{count3}")
            self._log.info(f"Number of column values has been increased for uncore frequency: "
                           f"{count4}")
        else:
            my_file = Path("{}\\{}".format(self.csv_file_path, "xyz_ptumon.csv"))
            if my_file.is_file():
                self._log.info("File exist")
            else:
                raise RuntimeError("File does not exist")
            with open(my_file, 'r') as file:
                # This to ignore the null values in the data
                reader = csv.reader(x.replace('\0', '') for x in file)
                header = next(reader)
                self._log.debug(header)
                count = count1 = count2 = count3 = count4 = 0
                for column in reader:
                    try:
                        values = (column[9], column[11], column[5], column[6])
                        C0 = int(float(column[9]))
                        C6 = int(float(column[11]))
                        p_state = int(float(column[5]))
                        uncore = int(float(column[6]))
                        if p_state >= pm_constants.p_state_core_frequency:
                            self._log.debug("All the core frequencies are "
                                            "increased to max frequency")
                            count = count + 1
                            if not p_state > pm_constants.p_state_core_frequency:
                                raise RuntimeError("Core frequency values are not  as expected")
                        if uncore >= pm_constants.uncore_frequency:
                            self._log.debug("Uncore value has been increased increased")
                            count1 = count1 + 1
                            if not uncore >= pm_constants.uncore_frequency:
                                raise RuntimeError("UnCore frequency "
                                                   "values are not  as expected")
                        if C0 <= int(self.c0_value) and C6 >= int(self.c6_value):
                            self._log.info("values are as expected")
                            count2 = count2 + 1
                            if not C0 <= self.c0_value and C6 >= self.c6_value:
                                raise RuntimeError("C0 & C6 values are not as expected")
                    except:
                        count4 = count4 + 1
            self._log.info(f"Number of column values as expected for c0 & c6: "
                           f"{count2}")
            self._log.info(f"Number of total columns: {count4}")
            self._log.info(f"Number of all core frequencies are "
                           f"increased to max frequency: "
                           f"{count}")
            self._log.info(f"Number of column values has been "
                           f"increased for uncore frequency: "
                           f"{count1}")

    def ptu_prepare(self):
        if not PmCommon.check_ptu_tool(self):
            PmCommon.install_ptu_tool(self)
            if not PmCommon.check_ptu_tool(self):
                self._log.error("PTU tool is not available in SUT")
                raise RuntimeError("PTU tool is not available in SUT")
            self._log.info("PTU is Installed")

    def post_update(self):
        PmCommon.kill_ptu_tool(self)
        PmCommon.deleting_csv_files_in_host(self)
        PmCommon.copy_csv_file_from_sut_to_host(self)
        PmCommon.read_csv_file(self)


class SocwatchCommon(SeamlessBaseTest):
    """
    This Class is Used as Common Class For all the Socwatch Test Cases
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
         Create an instance of socwatch Common
        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super().__init__(test_log, arguments, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self.reboot_timeout = \
            self._common_content_configuration.get_reboot_timeout()
        self.socwatch_tool_lin = self._common_content_configuration.get_socwatch_lin_tool_file_path()
        self.socwatch_tool_win = self._common_content_configuration.get_socwatch_win_tool_file_path()

    def check_capsule_pre_conditions(self):
        # To-Do add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        # To-Do add workload output analysis
        return True

    def get_current_version(self, echo_version=True):
        pass

    def check_socwatch_tool(self):
        """
        This function will check socwatch tool is available in SUT
        :return: True if all files are present in SOCWATCH directory or False
        """
        self._log.info("Checking the SOCWATCH Tool in SUT")
        self.soc_csv_file_path = os.path.join(self.log_dir, "SOCWATCH")
        os.makedirs(self.soc_csv_file_path)
        if self._os_type == OperatingSystems.WINDOWS:
            command = f"cd {SocwatchWindows.SOCWATCH_TOOL_SUT_PATH}\\" \
                      f"{SocwatchWindows.SOCWATCH_TOOL_FOLDER_NAME} && dir"
            output = self.run_ssh_command(command, timeout_seconds=pm_constants.TIMEOUT_SEC)
            self._log.debug(f"SOCWATCH Tool DIR output : {output.stdout}")
            for file_name in SocwatchWindows.SOCWATCH_TOOL_CONTENT:
                if file_name in output.stdout:
                    self._log.info(f"{file_name} is present")
                else:
                    self._log.info(f"SOCWATCH TOOL  is not present. "
                                   f"{file_name} is missing from socwatch tool")
                    return False
        else:

            command = f"cd {SocwatchLinux.SOCWATCH_EXECUTOR_PATH_LINUX}/" \
                      f"{SocwatchLinux.SOCWATCH_CHECKING_FILE_CONTENT_LINUX} && ls "
            output = self.run_ssh_command(command, timeout_seconds=pm_constants.TIMEOUT_SEC)
            self._log.debug(f"SOCWATCH Tool DIR output : {output.stdout}")
            for file_name in SocwatchLinux.SOCWATCH_TOOL_CONTENT_LINUX:
                if file_name in output.stdout:
                    self._log.info(f"{file_name} is present")
                else:
                    self._log.info(f"SOCWATCH TOOL  is not present. "
                                   f"{file_name} is missing from socwatch tool")
                    return False
        return True

    def install_socwatch_tool(self):
        """
        This method will copy and install socwatch tool into sut
        """
        self._log.info("Installing socwatch tool")
        if self._os_type == OperatingSystems.WINDOWS:
            self.run_ssh_command("mkdir {}".format(SocwatchWindows.SOCWATCH_TOOL_SUT_PATH))
            self.copy_extract_file(self.socwatch_tool_win, SocwatchWindows.SOCWATCH_TOOL_SUT_PATH, SocwatchWindows.SOCWATCH_TOOL_FOLDER_NAME)
        else:
            self.run_ssh_command("cd {} && mkdir {} ".format(SocwatchLinux.SOCWATCH_TOOL_SUT_PATH_LINUX,
                                                             SocwatchLinux.SOCWATCH_TOOL_FOLDER_NAME_LINUX))
            self.os.copy_local_file_to_sut(self.socwatch_tool_lin, SocwatchLinux.SOCWATCH_TOOL_FOLDER_NAME_LINUX)
            socwatch_path = self.socwatch_tool_lin.split('\\')[-1]
            command = "cd {} && tar -xvzf {}".format(SocwatchLinux.SOCWATCH_EXECUTOR_PATH_LINUX, socwatch_path)
            self.run_ssh_command(command, timeout_seconds=pm_constants.TIMEOUT_SEC)
            self.run_ssh_command("find {} -name {}".format(SocwatchLinux.SOCWATCH_EXECUTOR_PATH_LINUX,
                                                           SocwatchLinux.SOCWATCH_TOOL_FOLDER_NAME_LINUX ))

    def execute_socwatch_tool(self):
        """
        This function will execute the Socwatch tool application
        """
        if self._os_type == OperatingSystems.WINDOWS:
            self._log.info(f"Starting the SOCWATCH Tool command '{SocwatchWindows.SOCWATCH_CMD.format(SocwatchWindows.SOCWATCH_TOOL_NAME)}'")
            self.os.execute_async(SocwatchWindows.SOCWATCH_CMD.format(SocwatchWindows.SOCWATCH_TOOL_NAME),
                                  cwd=SocwatchWindows.SOCWATCH_EXECUTOR_PATH)
            cmd_line = f'"{SocwatchWindows.SOCWATCH_EXECUTOR_PATH}" {SocwatchWindows.SOCWATCH_CMD.format(SocwatchWindows.SOCWATCH_TOOL_NAME)}'
            self._log.info(f"SOCWATCH executing command %s: {cmd_line}")
        else:
            cmd_line = SocwatchLinux.SOCWATCH_CMD_LINUX.format(SocwatchLinux.SOCWATCH_TOOL_SUT_PATH_LINUX)
            self.os.execute_async(cmd_line, cwd=SocwatchLinux.SOCWATCH_EXECUTOR_PATH_LINUX)
            self._log.info("SOCWATCH executing command %s", cmd_line)

    def copy_socwatch_csv_file_from_sut_to_host(self):
        """
        This method will copy csv file from sut to host
        """
        self._log.info("Copy the CSV file from SUT to Host")
        if self._os_type == OperatingSystems.WINDOWS:
            self.csv_file_sut = SocwatchWindows.SOCWATCH_TOOL_NAME + ".csv"
            self.csv_file_host = self.soc_csv_file_path + "/" + SocwatchWindows.SOCWATCH_TOOL_FOLDER_NAME_WINDOWS + ".csv"
            self.os.copy_file_from_sut_to_local(self.csv_file_sut, self.csv_file_host)

        else:
            self.csv_file_sut = SocwatchLinux.SOCWATCH_TOOL_SUT_PATH_LINUX + "/" + SocwatchLinux.SOCWATCH_TOOL_FOLDER_NAME_LINUX + ".csv"
            self.csv_file_host = self.soc_csv_file_path + "/" + SocwatchLinux.SOCWATCH_TOOL_FOLDER_NAME_LINUX + ".csv"
            self.os.copy_file_from_sut_to_local(self.csv_file_sut, self.csv_file_host)


    def read_csv_table(self, match, alternative_match=None):
        """
        Parse CSV file with the given string and return the dict
        :param match: table heading
        :param alternative_match: alternative table heading
        :return table_data: returns the particular table
        """
        self._log.info("Reading the CSV file")
        table_data_dict = OrderedDict()
        if self._os_type == OperatingSystems.WINDOWS:
            my_file = Path(self.csv_file_host)
            if my_file.is_file():
                self._log.info("File exist")
            else:
                raise RuntimeError("File does not exist")
            with open(self.csv_file_host, 'r') as csv_file_read:
                data = csv_file_read.read()
        else:
            my_file = Path(self.csv_file_host)
            if my_file.is_file():
                self._log.info("File exist")
            else:
                raise RuntimeError("File does not exist")
            with open(self.csv_file_host, 'r') as csv_file_read:
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
                "Table %s and %s not found in the socwatch_log" % match % alternative_match)
        table = data.split(match)[-1].split("\n\n")[0].strip().splitlines()
        table_heads = [item.strip() for item in table[0].split(",")]
        table_data = [item.strip() for item in table[2::]]
        return table_data

    def get_package_p_state_frequency(self):
        """
        Get package P-State Average Frequency table from csv file
        :return: Returns the Package P-State Average Frequency (excluding CPU idle time)
        """
        return self.read_csv_table(SocwatchConstants.CPU_P_STATE_FREQUENCY)

    def verify_pacakge_p_state_frequency(self):
        """
        Verify the package P-State Average Frequency
        :raise: content_exception.TestFail if not getting the expected values
        """
        table_data = self.get_package_p_state_frequency()
        if not len(table_data):
            raise content_exceptions.TestFail("Could not find the core "
                                              "p state frequency table in socwatch_log")
        invalid_matches = []
        for threads in table_data:
            index_num = threads.find(',')
            index_data = int(threads[index_num+1:])
            if index_data <= SocwatchConstants.CORE_FREQUENCY_MIN_VALUE:
                self._log.info(f"Condition core p state verified values are: {threads}")
            else:
                invalid_matches.append(threads)
        if len(invalid_matches):
            raise content_exceptions.TestFail(f"core core p state verification failed{invalid_matches}")
        self._log.info("core p state has been verified successfully")

    def read_socwatch_csv_file(self, match, alternative_match=None):
        """
        Parse CSV file with the given string and return the dict
        :param match: table heading
        :param alternative_match: alternative table heading
        :return table_data_dict: returns the particular table
        """
        self._log.info("Reading the CSV file")
        table_data_dict = OrderedDict()
        if self._os_type == OperatingSystems.WINDOWS:
            my_file = Path(self.csv_file_host)
            if my_file.is_file():
                self._log.info("File exist")
            else:
                raise RuntimeError("File does not exist")
            with open(self.csv_file_host, 'r') as csv_file_read:
                data = csv_file_read.read()
        else:
            my_file = Path(self.csv_file_host)
            if my_file.is_file():
                self._log.info("File exist")
            else:
                raise RuntimeError("File does not exist")
            with open(self.csv_file_host, 'r') as csv_file_read:
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

    def get_core_c_state_residency_time_summary_frequency(self):
        """
        Get core C-State residency percentage table from csv file

        :return: Returns the Core C-State Summary Residency (Percentage and Time)
        """
        return self.read_socwatch_csv_file(SocwatchConstants.CORE_C_STATE_RESIDENCY_TIME)

    def verify_core_c_state_residency_frequency(self, core_c_state, condition):
        """
        Verify the core C-State residency percentage

        :param core_c_state: get the core state
        :param condition: validate the condition with the core C-State
        :raise: content_exception.TestFail if not getting the expected values
        """
        self._log.info(f"Verify Core C-State residency {core_c_state} with threshold {condition}")
        core_c_state_table = self.get_core_c_state_residency_time_summary_frequency()
        if not len(core_c_state_table):
            raise content_exceptions.TestFail("Could not find the core c state r"
                                              "esidency table in SocWatchOutput")
        core_c_state_values = None
        try:
            core_c_state_values = core_c_state_table[core_c_state]
        except KeyError:
            raise content_exceptions.TestFail("%s core C state does not exist in SoCWatchOutput",
                                              core_c_state_values)
        invalid_matches = []
        for key, value in core_c_state_values.items():
            if SocwatchConstants.RESIDENCY_PERCENT_MATCH in key:
                if not eval(condition.replace(core_c_state, value)):
                    invalid_matches.append(key + ":" + condition.replace(core_c_state, value))
        if len(invalid_matches):
            raise content_exceptions.TestFail("{} core c state verification failed, check the threshold values {}".format(core_c_state, invalid_matches))
        self._log.info("%s core c state has been verified successfully" % core_c_state)

    def socwatch_prepare(self):
        if not SocwatchCommon.check_socwatch_tool(self):
            SocwatchCommon.install_socwatch_tool(self)
            if not SocwatchCommon.check_socwatch_tool(self):
                self._log.error("Socwatch tool is not available in SUT")
                raise RuntimeError("Socwatch tool is not available in SUT")
            self._log.info("Socwatch tool is Installed")
