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
import re
import time
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib import content_exceptions
from src.lib.content_configuration import ContentConfiguration
from src.seamless.lib.seamless_common import SeamlessBaseTest
from src.seamless.tests.bmc.constants.ras_constants import RasWindows, RasConstants, RasLinux
from src.ras.lib.os_log_verification import OsLogVerifyCommon

class RasCommon(SeamlessBaseTest):
    """
    This Class is Used as Common Class For all the RAS Test Cases
    """

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file_path=None):
        """
         Create an instance of RasCommon
        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super().__init__(test_log, arguments, cfg_opts)
        self.bios_config_file_path = bios_config_file_path
        self.reboot_timeout = \
            self._common_content_configuration.get_reboot_timeout()
        self.error_type = arguments.error_type
        self._os_log_obj = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration,
                                             self._common_content_lib)

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument('--error_type', action='store_true',
                            help="Add argument if error_type workload to be performed")

    def check_wheahct_tool(self):
        """
        This function will check WHEAHCT tool is available in Windows SUT
        :return: True if all files are present in WHEACT directory or False
        """
        self._log.info("Checking the WHEAHCT Tool in SUT")
        command = f"cd {RasWindows.WHEAHCT_TOOL_SUT_PATH_WINDOWS}\\" \
                  f"{RasWindows.WHEAHCT_TOOL_FOLDER_NAME} && dir "
        output = self.run_ssh_command(command, timeout_seconds=RasConstants.TIME_OUT_SEC)
        self._log.debug(f"WHEAHCT Tool DIR output : {output.stdout}")
        for file_name in RasWindows.WHEAHCT_TOOL_CONTENT:
            if file_name in output.stdout:
                self._log.info(f"{file_name} is present")
            else:
                self._log.info(f"WHEAHCT TOOL  is not present. {file_name} "
                               f"is missing from wheahct tool")
                raise RuntimeError("WHEAHCT TOOL  is not present")
        return True

    def install_wheahct_tool(self):
        """
        This method will copy and install wheahct tool into sut
        """
        self._log.info("Installing wheahct tool")
        self.os.copy_local_file_to_sut(RasWindows.WHEAHCT_TOOL_HOST_PATH,
                                       RasWindows.WHEAHCT_TOOL_SUT_PATH_WINDOWS)
        command = f"cd {RasWindows.WHEAHCT_TOOL_SUT_PATH_WINDOWS} && tar xvzf " \
                  f"{RasWindows.WHEAHCT_TOOL_ZIP_FILE_NAME}"
        output = self.run_ssh_command(command, timeout_seconds=RasConstants.TIME_OUT_SEC)
        if output.stderr:
            raise RuntimeError(f"Unable to run the command with the below error \n {output.stderr}")
        if "Invalid or unexpected" in output.stdout:
            raise RuntimeError(f"Unable to run the command with the below error \n {output.stdout}")
        return output.stdout

    def injection_error(self):
        """
        This function injecting error on windows OS and verify the results
        :return: True if getting Total and Passed values are matching
        """
        regex_cmd = "Summary: Total=(\d+), Passed=(\d+)"
        cmd_output = self.run_ssh_command(f"cd {RasWindows.WHEAHCT_TOOL_SUT_PATH_WINDOWS}\\"
                                          f"{RasWindows.WHEAHCT_TOOL_FOLDER_NAME} "
                                          f"&& Clear_whea_evts.cmd")
        self._log.info(f"clear whea evts cmd output : {cmd_output.stdout}")
        cmd_output = self.run_ssh_command(f"cd {RasWindows.WHEAHCT_TOOL_SUT_PATH_WINDOWS}\\"
                                          f"{RasWindows.WHEAHCT_TOOL_FOLDER_NAME} "
                                          f"&& installPlugin.bat")
        self._log.info(f"Installing whea plug in : {cmd_output.stdout}")
        cmd_output = self.run_ssh_command(
            f"{RasWindows.WHEAHCT_TOOL_SUT_PATH_WINDOWS}\\{RasWindows.WHEAHCT_TOOL_FOLDER_NAME}\\"
            f"{RasWindows.WHEAHCT_TOOL_FILE_NAME} {self.ERR_INJ_CMD}")
        self._log.info(f"Injecting error output : {cmd_output.stdout}")
        regex_result = re.search(regex_cmd, cmd_output.stdout)
        if regex_result.group(1) != regex_result.group(2):
            self._log.error("Total and Passed values are not matching")
            raise RuntimeError(f"Expected Total {regex_result.group(1)} and Passed {regex_result.group(2)} values are not matching")

        self._log.info(f"Expected Total and Passed values are matching {regex_result.group(0)}")
        return True

    def set_err_inj_cmd(self, cmd):
        """
        This method will provide the error injection command for both OS
        :cmd: Erroj injection command list
        """
        self.ERR_INJ_CMD = cmd

    def einj_prepare_injection_linux(self):
        """
        Prepare SUT for EINJ error injection for Linux OS
        :return: Bool
        """
        try:
            # Update the date to ensure injection logging can occur properly
            self._log.info("Updating date to ensure proper error logging")
            self._common_content_lib.set_datetime_on_sut()
            # Load einj module to check whether error injection
            # related BIOS knobs are enabled or not
            self._log.info("Mounting debugFS...")
            self.os.execute("mount -t debugfs none /sys/kernel/debug", self.BMC_STD_COMMAND_TIMEOUT)
            self._log.info("Loading einj module:")
            result = self.os.execute("sudo modprobe einj", self.BMC_STD_COMMAND_TIMEOUT)
            self._log.info(result.stdout)
            # Check if the load was successful or not
            if re.match(r"modprobe: FATAL:", result.stdout):
                self._log.error("einj module cannot be loaded - "
                                "Check BIOS knob setting - Exiting the test!!!")
                return False
            else:
                self._log.info("einj module loaded successfully!!!")
                return True
        except Exception as ex:
            log_error = f"An exception occurred : {str(ex)}"
            self._log.error(log_error)
            raise ex

    def error_inject_commands_linux(self):
        """
        Error injection commands for linux sut
        """
        self._log.info("Starting the error injection commands")
        path = self.ERR_INJ_CMD[0]
        for error_cmd in range(1, len(self.ERR_INJ_CMD)):
            try:
                cmd = f"{path} && {self.ERR_INJ_CMD[error_cmd]}"
                self._log.info(f"Executing command = {cmd}")
                self.run_ssh_command(cmd, timeout_seconds=RasConstants.COMMAND_TIMEOUT_SEC)
            except Exception as ex:
                self._log.error(f"Getting exception {ex}")

    def check_os_log_error_message(self, error):
        """
        Verify the error messages for both OS
        """
        if self._os_type == OperatingSystems.WINDOWS:
            if self.error == "UNC_NFATAL":
                if not self._os_log_obj.verify_os_log_error_messages(__file__, RasWindows.WINDOWS_WHEA_LOG,
                                                              RasWindows.ERROR_MESSAGE):
                    raise RuntimeError("Expected error string is not matching")
            elif self.error == "CRT_ERR":
                if not self._os_log_obj.verify_os_log_error_messages(__file__, RasWindows.WINDOWS_WHEA_LOG,
                                                              RasWindows.ERROR_MESSAGE):
                    raise RuntimeError("Expected error string is not matching")
            elif self.error == "UNC_ERR":
                if not self._os_log_obj.verify_os_log_error_messages(__file__, RasWindows.WINDOWS_WHEA_LOG,
                                                              RasWindows.ERROR_MESSAGE):
                    raise RuntimeError("Expected error string is not matching")
            elif self.error == "UNC_FATAL":
                if not self._os_log_obj.verify_os_log_error_messages(__file__, RasWindows.WINDOWS_WHEA_LOG,
                                                              RasWindows.ERROR_MESSAGE):
                    raise RuntimeError("Expected error string is not matching")
            # else:
            #     self._log.error("Expected error string is not matching")
            #     raise RuntimeError("Expected error string is not matching")
        else:
            if self.error == "UNC_NFATAL":
                if not self._os_log_obj.verify_os_log_error_messages(__file__, RasLinux.LINUX_ERROR_LOG,
                                                              RasLinux.UNCORRECT_NON_FATAL_ERR_LIN):
                    raise RuntimeError("Expected error string is not matching")
            elif self.error == "UNC_FATAL":
                if not self._os_log_obj.verify_os_log_error_messages(__file__, RasLinux.LINUX_ERROR_LOG,
                                                              RasLinux.UNCORRECT_FATAL_ERR_LIN):
                    raise RuntimeError("Expected error string is not matching")
            elif self.error == "CRT_ERR":
                if not self._os_log_obj.verify_os_log_error_messages(__file__, RasLinux.LINUX_ERROR_LOG,
                                                              RasLinux.CORRECT_ERR_LIN):
                    raise RuntimeError("Expected error string is not matching")
            # else:
            #     raise RuntimeError("Invalid input:{}".format(error))

    def error_type_command(self, error):
        if self._os_type == OperatingSystems.WINDOWS:
            if error == "UNC_NFATAL":
                self.set_err_inj_cmd(RasWindows.ERR_INJ_CMD_NON_FATAL)
            elif error == "UNC_FATAL":
                self.set_err_inj_cmd(RasWindows.ERR_INJ_CMD_FATAL)
            elif error == "CRT_ERR":
                self.set_err_inj_cmd(RasWindows.CRT_ERR_INJ_CMD)
            elif error == "UNC_ERR":
                self.set_err_inj_cmd(RasWindows.UNCRT_ERR_INJ_CMD)
            else:
                raise RuntimeError("Invalid input:{}".format(error))
        else:
            if self.error == "UNC_NFATAL":
                self.set_err_inj_cmd(RasLinux.ERR_INJ_NON_FATAL_CMD_LINUX)
            elif self.error == "UNC_FATAL":
                self.set_err_inj_cmd(RasLinux.ERR_INJ_FATAL_CMD_LINUX)
            elif self.error == "CRT_ERR":
                self.set_err_inj_cmd(RasLinux.CRT_ERR_INJ_CMD_LINUX)
            else:
                raise RuntimeError("Invalid input:{}".format(error))

    def ras_prepare(self):
        """
        This function will check and instal wheahct tool for windows os
        """
        if self._os_type == OperatingSystems.WINDOWS:
            if not self.check_wheahct_tool():
                self.install_wheahct_tool()
                self._log.info("WHEA tool is copied")
                if not self.check_wheahct_tool():
                    self._log.error("WHEA tool is not available in SUT")
                    raise RuntimeError("WHEA tool is not available in SUT")
        else:
            self.einj_prepare_injection_linux()

    def ras_execute(self):
        """
        This function will inject the error while staging the sps capsules
        """
        self.error_type_command(self.error_type)
        if self.capsule_type == 'sps':
            for count in range(self.loop_count):
                self._log.info("Loop Number:{}".format(count))
                if self.capsule_path != "":
                    self.update_type = "SPS"
                    self.error_inj_flag = True
                    self.STAGING_REBOOT = False
                    self._log.info("sending nth version capsule {}".format(self.expected_ver))
                    if self.expected_ver != self.get_current_version():
                        self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload,
                                          self.expected_ver)
                        if self.ac_on_off:
                            if not self.os.is_alive():
                                self._log.error("System is not alive, wait for the sut online")
                                self._common_content_lib.perform_graceful_ac_off_on(
                                    self.ac_power)  # To make the system alive
                                self.os.wait_for_os(self.reboot_timeout)
                    else:
                        raise RuntimeError("Expected version and current version are same")

                if self.capsule_path2 != "":
                    self.update_type = "SPS"
                    self.error_inj_flag = True
                    self.STAGING_REBOOT = False
                    if self.expected_ver2 != self.get_current_version():
                        self.send_capsule(self.capsule_path2, self.CAPSULE_TIMEOUT, self.start_workload,
                                          self.expected_ver2)
                    else:
                        raise RuntimeError("Expected version and current version are same")

                if self.ac_on_off:
                    if not self.os.is_alive():
                        self._log.error("System is not alive, wait for the sut online")
                        self._common_content_lib.perform_graceful_ac_off_on(
                            self.ac_power)  # To make the system alive
                        self.os.wait_for_os(self.reboot_timeout)

                if self.capsule_path3 != "":
                    self.update_type = "SPS"
                    self.error_inj_flag = True
                    self.STAGING_REBOOT = False
                    if self.expected_ver3 != self.get_current_version():
                        self.send_capsule(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload,
                                          self.expected_ver3)
                    else:
                        raise RuntimeError("Expected version and current version are same")
                if self.ac_on_off:
                    if not self.os.is_alive():
                        self._log.error("System is not alive, wait for the sut online")
                        self._common_content_lib.perform_graceful_ac_off_on(
                            self.ac_power)  # To make the system alive
                        self.os.wait_for_os(self.reboot_timeout)

        self.check_os_log_error_message(self.error_type)
