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
import datetime
import os
import sys
import pandas as pd
import shutil
import re
import random
import string
import platform
import time
import subprocess
import socket
from typing import Union

import six
from shutil import copy

from dtaf_core.providers.uefi_shell import UefiShellProvider

if six.PY2:
    from pathlib import Path
    import ConfigParser as config_parser
if six.PY3:
    from pathlib2 import Path
    import configparser as config_parser

from xml.etree import ElementTree
from zipfile import ZipFile
import multiprocessing as mp

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.dtaf_constants import ProductFamilies
from dtaf_core.lib.os_lib import LinuxDistributions
import dtaf_core.lib.log_utils as log_utils
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.content_configuration import ContentConfiguration
from src.lib.windows_event_log import WindowsEventLog
from src.lib.dtaf_content_constants import BootScriptConstants
from src.lib.dtaf_content_constants import ProviderXmlConfigs
from src.lib.dtaf_content_constants import NumberFormats
from src.lib.dtaf_content_constants import SutInventoryConstants
from src.lib.dtaf_content_constants import PowerStates
from src.lib.dtaf_content_constants import PlatformType
from src.lib.dtaf_content_constants import PlatformEnvironment
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import CpuFanSpeedConstants


class CommonContentLib(object):
    """
    This class implements common functions which can used across all test cases.
    """
    GET_CPU_PERCENTAGE_COMMAND = "cat /proc/loadavg"
    XMLCLI_BIOS_PROVIDER_XPATH = './suts/sut/providers/bios/driver/xmlcli'
    PLATFORM_CPU_FAMILY = './suts/sut/silicon/cpu/family'
    PLATFORM_NUMBER_OF_SOCKETS = './suts/sut/silicon/cpu/num_of_sockets'
    PLATFORM_CPU_STEPPING = './suts/sut/silicon/cpu/stepping'
    PLATFORM_CPU_QDF = './suts/sut/silicon/cpu/qdf'
    PLATFORM_PCH_FAMILY = './suts/sut/silicon/pch/family'
    PLATFORM_TYPE = './suts/sut/platform'
    CSCRIPTS_DEBUGGER_INTERFACE_TYPE = './suts/sut/providers/silicon_reg/driver/cscripts/debugger_interface_type'

    _LIST_OF_COLLECT_OS_LOGS_COMMANDS = ["dmesg | grep Hardware",
                                         "cat /var/log/messages | grep mcelog",
                                         "journalctl -u mcelog"]
    _STORE_LOGS_LINUX = ["dmesg", "/var/log"]
    _STORE_LOGS_ESXI = ["dmesg", "/var/log"]
    _STORE_LOGS_WINDOWS = ["System", "Application"]
    WINDOWS_SUT_EVENT_LOG_FOLDER = "event_logs"
    MODPROBE_AER_INJECT_CMD = "modprobe aer-inject"

    windows_home_drive_path = None

    SILICON_14NM_FAMILY = [ProductFamilies.SKX, ProductFamilies.CLX, ProductFamilies.CPX]
    SILICON_10NM_CPU = [ProductFamilies.ICX, ProductFamilies.SNR, ProductFamilies.SPR]

    C_DRIVE_PATH = "C:\\"
    ROOT_PATH = "/root"
    AURORA_TOOL_PATH = r'/opt/pv/'
    COLLATERAL_DIR_NAME = 'collateral'
    GOOD_PORT_STATE = [0xf, 0xd, 0x5]
    EINJCTL_REG_NAME = "rxeinjctl0"

    IPMCTL_WIN_EXECUTER = r".\ipmctl.exe"
    IPMCTL_LINUX_EXECUTER = "ipmctl"
    REMOVE_FILE = "rm {}"
    PORT_INFO_DICT = {}
    _PCIE_PORT_INFO = {}
    _CHECK_PORT_REGEX = "\|\s+(\d+)\s+\|\s+(\S+)\s+\|\s+(\S+)\s+\|"
    _REGEX_CMD_FOR_XCC = r"eXtreme\sCore\sCount\s.XCC."
    _REGEX_CMD_FOR_LCC = r"Low\sCore\sCount\s.LCC."
    _REGEX_CMD_FOR_HCC = r"High\sCore\sCount\s.HCC."
    LCC = "Low Core Count"
    HCC = "High Core Count"
    XCC = "eXtreme Core Count"
    _LINUX_BIN_LOCATION = "/usr/bin"

    NO_OF_BOOTSCRIPT_ATTEMPTS = 2
    KEY_RETVAL = "ret_val"
    KEY_LOG_PATH = "log_path"
    BIOS_POLL_INTERVAL = 0.5
    ESXI_DEFAULT_PATH = "/vmfs/volumes/datastore1"
    BIOS_MODE_CHECK_REFERENCE_PLATFORM = "EDKII"
    WAIT_TIME_IN_SEC = 20
    SLEEP_AFTER_ASYNC_CMD = 5
    XCOPY_COMMAND = "powershell.exe xcopy {} {} /S /K /D /H /Y"

    def __init__(self, log, os_obj, cfg_opts):

        self._log = log
        self._os = os_obj
        self.sut_os = self._os.os_type
        self._cfg = cfg_opts

        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()  # command timeout in seconds
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()  # reboot timeout in seconds
        if cfg_opts is not None:
            self.product = self.get_platform_family()
        self._windows_event_log_obj = None
        if self._os.os_type == OperatingSystems.WINDOWS:
            self._windows_event_log_obj = WindowsEventLog(self._log, self._os)
        if self._common_content_configuration.is_container_env():
            self.list_clear_linux_os_commands = [r"dmesg --clear",
                                                 r"chmod 777 /var/log/messages",
                                                 r"echo \"\" > /var/log/messages",
                                                 r"find /var/log/journal -type f -name *.journal* -exec rm  {} \;"]
        else:
            self.list_clear_linux_os_commands = [r"sudo dmesg --clear",
                                                 r"sudo chmod 777 /var/log/messages",
                                                 r"sudo echo \"\" > /var/log/messages",
                                                 r"sudo find /var/log/journal -type f -name *.journal* -exec rm  {} \;"]

    @staticmethod
    def get_project_src_path():
        project_folder_name = "src"
        cwd = os.path.dirname(__file__)
        counter = 1
        while os.path.exists(cwd):
            cwd = os.path.abspath(os.path.join(cwd, os.path.pardir))
            if project_folder_name in os.listdir(cwd):
                return cwd
            counter += 1
            if counter == 10:
                raise RuntimeError("Project path not found..")

    def get_config_file_path(self, folder_path, config_file):
        """
        Combines folder path and config file, checks if the file path is valid.

        :param folder_path: folder path where config_file is present
        :param config_file: config file name
        :return: config file path.
        :raises IOError: if config_file does not exists in specified folder path
        """
        if config_file is None:
            return config_file

        config_file_path = os.path.join(folder_path, config_file)
        if not os.path.isfile(config_file_path):
            error_log = "The config file '%s' does not exists." % config_file
            self._log.error(error_log)
            raise IOError(error_log)

        return config_file_path

    def get_system_configuration_file(self):
        """
        This function is used to get the default configuration path.

        :return: str - will return the path.
        """
        exec_os = platform.system()
        try:
            cfg_file_default = Framework.CFG_FILE_PATH[exec_os]
        except KeyError:
            self._log.error("Error - execution OS " + str(exec_os) + " not supported!")
            raise RuntimeError("Error - execution OS " + str(exec_os) + " not supported!")

        return cfg_file_default

    def get_default_bios_config_file_path(self):
        """
        This function is used to get the default bios configuration file path.

        :return: str - will return the path.
        :raise: AttributeError - if not able to find default bios config path.
        """
        # TODO : Need to find a better way to parse through the system configuration file, so that it will not break for
        #  different driver (e.g. serial implementation)
        # TODO : Suresh will add config_file as optional parameter to both read and set bios, then

        # default_system_config_file = self.get_system_configuration_file()
        # tree = ElementTree.parse(default_system_config_file)
        # root = tree.getroot()

        bios_root = self._cfg.find(self.XMLCLI_BIOS_PROVIDER_XPATH)
        cfg_path = bios_root.find(r"bios_cfgfilepath").text.strip()
        cfg_file_name = bios_root.find(r"bios_cfgfilename").text.strip()

        if cfg_file_name and cfg_path:
            default_bios_config_file_path = os.path.join(cfg_path, cfg_file_name)
            return default_bios_config_file_path
        else:
            raise AttributeError("Failed to get default bios config file, please update the value for XML attributes "
                                 "'bios_cfgfilepath' and 'bios_cfgfilename' in configuration file...")

    def is_bootscript_required(self):
        if self.product not in BootScriptConstants.SILICON_REQUIRES_BOOTSCRIPT.keys():
            return False
        list_stepping = BootScriptConstants.SILICON_REQUIRES_BOOTSCRIPT[self.product]
        cpu_stepping = self.get_platform_stepping()
        self._log.info("The platform family='{} and stepping='{}'...".format(self.product, cpu_stepping))
        if not cpu_stepping:
            # cpu stepping is not specified in configuration file,
            # let boot script find the stepping and decide whether bootscript required or not
            self._log.info("The stepping information is not specified in configuration file. "
                           "Boot script will find the stepping and run boot script if required..")
            return True
        if str(cpu_stepping).upper() in str(list_stepping).upper():
            self._log.info("For cpu stepping '{}' boot script may be required..".format(cpu_stepping))
            return True

        self._log.info("For cpu stepping '{}' boot script not required..".format(cpu_stepping))
        return False

    def perform_graceful_ac_off_on(self, ac_power):
        max_attempts = 5
        try:
            if self._os.is_alive():
                self._log.info("OS is alive, shutting down the SUT..")
                self._os.shutdown(10)  # To apply the new bios setting.
        except Exception as ex:
            self._log.error("Paramiko throws error sometime if OS is not alive. Ignoring this "
                            "exception '{}'...".format(ex))

        self._log.info("Powering off and powering on SUT...")
        no_attempts = 0
        while no_attempts < max_attempts:
            ret_val = ac_power.ac_power_off()
            self._log.info("Attempt #{} SUT Power off status='{}'".format(no_attempts, ret_val))
            try:
                ac_power.get_ac_power_state()
                if ret_val or not ac_power.get_ac_power_state():
                    break
            except NotImplementedError:
                if ret_val:
                    break

            no_attempts = no_attempts + 1
            time.sleep(5)

        try:
            if ac_power.get_ac_power_state():
                log_error = "Failed to AC power off the SUT. Please check your AC power configuration."
                self._log.error(log_error)
                raise content_exceptions.TestSetupError(log_error)
        except NotImplementedError:
            pass

        time.sleep(10)
        no_attempts = 0
        while no_attempts < max_attempts:
            ret_val = ac_power.ac_power_on()
            self._log.info("Attempt #{}: SUT Power on status='{}'".format(no_attempts, ret_val))
            no_attempts = no_attempts + 1
            try:
                ac_power.get_ac_power_state()
                if ret_val or not ac_power.get_ac_power_state():
                        break
            except NotImplementedError:
                if ret_val:
                    break

            time.sleep(5)

        try:
            if not ac_power.get_ac_power_state():
                log_error = "Failed to AC power on the SUT. Please check your AC power configuration."
                self._log.error(log_error)
                raise content_exceptions.TestSetupError(log_error)
        except NotImplementedError:
            pass

        time.sleep(10)

        if self.is_bootscript_required():
            # run boot script for EGS
            no_attempts = 0
            boot_script_status = False
            while no_attempts < self.NO_OF_BOOTSCRIPT_ATTEMPTS:
                boot_script_status = self.execute_boot_script()
                if boot_script_status:
                    break
                no_attempts = no_attempts + 1

            if not boot_script_status:
                raise RuntimeError("Boot script failed...")

    def perform_boot_script(self):
        """
        This function will check boot script is required to run on A0/A1 silicon

        :param raise: RuntimeError if boot script fail
        """
        if self.is_bootscript_required():
            # run boot script for EGS
            no_attempts = 0
            boot_script_status = False
            while no_attempts < self.NO_OF_BOOTSCRIPT_ATTEMPTS:
                boot_script_status = self.execute_boot_script()
                if boot_script_status:
                    break
                no_attempts = no_attempts + 1

            if not boot_script_status:
                raise RuntimeError("Boot script failed...")

    def boot_to_uefi(self):
        """
        This method is to boot he SUT to UEFI.

        :return previous_boot_order - previous boot order saved to var previous_boot_order.
        :raise content_exceptions
        """
        try:
            from src.lib.bios_util import ItpXmlCli, BootOptions
            #  Create itp xml cli util object
            itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)

            #  Create UEFI object
            uefi_cfg = self._cfg.find(UefiShellProvider.DEFAULT_CONFIG_PATH)
            uefi_obj = ProviderFactory.create(uefi_cfg, self._log)  # type: UefiShellProvider

            #  Get current boot order
            previous_boot_order = itp_xml_cli_util.get_current_boot_order_string()
            self._log.info("Previous boot order {}".format(previous_boot_order))

            #  Set UEFI boot order
            itp_xml_cli_util.set_default_boot(BootOptions.UEFI)

            try:
                self._os.reboot(self.WAIT_TIME_IN_SEC * 2)
            except:
                pass

            self._log.info("waiting for uefi shell..")
            uefi_obj.wait_for_uefi(self._common_content_configuration.bios_boot_menu_entry_wait_time())
            time.sleep(self.WAIT_TIME_IN_SEC)

            return previous_boot_order
        except Exception as ex:
            self._log.error("Please close all Putty Session before running Test")
            raise content_exceptions.TestFail("Failed during booting to UEFI with exception: {}".format(ex))

    def perform_os_reboot(self, reboot_time_out):
        if self.is_bootscript_required():
            try:
                self._os.reboot(10)
            except Exception as ex:
                self._log.info("For platform '{}' the exception '{}' is OK..".format(self.product, ex))

            no_attempts = 0
            boot_script_status = False
            while no_attempts < self.NO_OF_BOOTSCRIPT_ATTEMPTS:
                boot_script_status = self.execute_boot_script()
                if boot_script_status:
                    break
                no_attempts = no_attempts + 1

            if not boot_script_status:
                raise RuntimeError("Boot script failed...")

            self._log.info("Waiting for OS to be alive...")
            self._os.wait_for_os(reboot_time_out)
        else:
            self._log.info("Waiting for OS to be alive...")
            self._os.reboot(reboot_time_out)

    def _clear_all_linux_os_error_logs(self, set_date=True):
        """
        Clears OS logs on Linux - /var/log/messages, dmesg, journalctl

        :param self: For os provider to execute commands
        :param set_date: Whether or not to set the SUT date before clearing OS logs
        :return: None
        """
        self._log.info("Clearing of OS Logs Initiated ...")
        if set_date:
            self.set_datetime_on_linux_sut()

        # enable journal log is does not exists
        self._os.execute("mkdir -p /var/log/journal", self._command_timeout)
        for command_line in self.list_clear_linux_os_commands:
            cmd_result = self._os.execute(command_line, self._command_timeout)
            if cmd_result.cmd_failed():
                log_error = "Failed to run command '{}' with " \
                            "return value = '{}' and " \
                            "std_error='{}'..".format(command_line, cmd_result.return_code, cmd_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)
            else:
                self._log.info("The command '{}' executed successfully..".format(command_line))

        self._log.info("OS Logs are Cleared Successfully")

    def _clear_all_windows_os_error_logs(self, set_date=True):
        """
        Clears OS logs on Linux - /var/log/messages, dmesg, journalctl

        :param self: For os provider to execute commands
        :param set_date: Whether or not to set the SUT date before clearing OS logs
        :return: None
        """
        self._log.info("Clearing of OS Logs Initiated ...")
        if set_date:
            self.set_datetime_on_windows_sut()

        # clear windows system event log
        event_log = WindowsEventLog(self._log, self._os)
        event_log.clear_system_event_logs()

        self._log.info("OS Logs are Cleared Successfully")

    def collect_all_logs_from_linux_sut(self):
        """
        This Method is used to collect all the OS Level Logs such as mcelogs and dmesg logs

        :return None
        :raise RuntimeError if there is any error while collecting the logs
        """
        try:
            for command_line in self._LIST_OF_COLLECT_OS_LOGS_COMMANDS:
                cmd_result = self._os.execute(command_line, self._command_timeout)
                if cmd_result.cmd_failed():
                    log_error = "Failed to run command '{}' with " \
                                "return value = '{}' and " \
                                "std_error='{}'.."u''.format(command_line, cmd_result.return_code, cmd_result.stderr)
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
                else:
                    self._log.info("The command '{}' executed successfully.. and Output of '{}' log is {}"
                                   u''.format(command_line, command_line, cmd_result.stdout.strip()))
        except Exception as ex:
            log_error = "Unable to Collect OS Logs due to exception '{}'".format(ex)
            self._log.error(log_error)

    def clear_all_os_error_logs(self, set_date=True):
        """
        Clears OS logs on Both Linux and Windows

        :param self: For os provider to execute commands
        :param set_date: Whether or not to set the SUT date before clearing OS logs
        :return: None
        """
        if OperatingSystems.LINUX in self.sut_os:
            return self._clear_all_linux_os_error_logs(set_date)
        elif OperatingSystems.WINDOWS in self.sut_os:
            return self._clear_all_windows_os_error_logs(set_date)
        else:
            raise RuntimeError("Not yet implemented for OS '{}'".format(self.sut_os))

    def set_datetime_on_linux_sut(self):
        """
        This Method is Used to Set the Current Date and Time obtained from Host System on Linux SUT

        :return None
        """
        self._log.info("Setting the Date and Time in SUT ....")
        d = datetime.datetime.today()
        self._os.execute("date --set=" + '"' + str(d) + '"', self._command_timeout)

    def set_datetime_on_windows_sut(self):
        """
        This Method is Used to Set the Current Date and Time obtained from Host System on Linux SUT

        :return None
            """
        self._log.info("Setting the Date and Time in SUT ....")
        d = datetime.datetime.today()
        self._os.execute("powershell Set-Date -Date=" + '"' + str(d) + '"', self._command_timeout)

    def set_datetime_on_sut(self):
        """
        This Method is Used to Set the Current Date and Time obtained from Host System on SUT

        :return: None
        """
        if OperatingSystems.LINUX in self.sut_os:
            return self.set_datetime_on_linux_sut()
        elif OperatingSystems.WINDOWS in self.sut_os:
            return self.set_datetime_on_windows_sut()
        else:
            raise RuntimeError("Not yet implemented for OS '{}'".format(self.sut_os))

    def get_platform_family(self):
        """
        This function is used to platform cpu family from config file.

        :return: str - will return cpu family name.
        :raise: AttributeError - if not able to find cpu family name in configuration file.
        """

        cpu_family = self._cfg.find(self.PLATFORM_CPU_FAMILY)
        if cpu_family.text:
            return cpu_family.text
        else:
            raise AttributeError("Failed to get CPU family name, please update the value for XML attributes "
                                 "'family' in configuration file...")

    def get_platform_number_of_sockets(self):
        """
        This function is used to get platform number of sockets from config file.

        :return: str - will return the number of sockets.
        :raise: AttributeError - if not able to find number of sockets in configuration file.
        """
        num_of_skt = self._common_content_configuration.get_num_of_sockets()
        if num_of_skt:
            return num_of_skt
        else:
            raise AttributeError("Failed to get number of sockets, please update the value for XML attributes "
                                 "'no_of_sockets' in configuration file...")

    def get_platform_stepping(self):
        """
        This function is used to platform cpu stepping from config file.

        :return: str - will return cpu family name.
        """
        try:
            # default_system_config_file = self.get_system_configuration_file()
            # tree = ElementTree.parse(default_system_config_file)
            # root = tree.getroot()
            cpu_stepping = self._cfg.find(self.PLATFORM_CPU_STEPPING)
            if cpu_stepping.text:
                cpu_stepping = cpu_stepping.text
        except Exception as ex:
            cpu_stepping = None
            self._log.error("Failed to get CPU stepping due to exception '{}'".format(ex))
        return cpu_stepping

    def get_pch_family(self):
        """
        This function is used to platform pch family from config file.

        :return: str - will return pch family name.
        :raise: AttributeError - if not able to find pch family name in configuration file.
        """
        # default_system_config_file = self.get_system_configuration_file()
        # tree = ElementTree.parse(default_system_config_file)
        # root = tree.getroot()

        pch_family = self._cfg.find(self.PLATFORM_PCH_FAMILY)
        if pch_family.text:
            return pch_family.text
        else:
            raise AttributeError("Failed to get PCH family name, please update the value for XML attributes "
                                 "'family' in configuration file...")

    def get_platform_type(self):
        """
        This function is used to platform type from config file.

        :return: str - will return platform type - reference/dell/hp etc.
        :raise: AttributeError - if not able to find family type in configuration file.
        """

        family_type = self._cfg.find(self.PLATFORM_TYPE)
        if "type" in family_type.attrib.keys():
            return family_type.attrib["type"]
        else:
            raise AttributeError("Failed to get family type, please update the value for XML attributes "
                                 "'platform type' in configuration file...")

    def get_platform_environment(self):
        """
        This function is used to platform type from config file.

        :return: str - will return platform environment - Hardware, Simics etc.
        """
        platform_info = self._cfg.find(self.PLATFORM_TYPE)
        return platform_info.get(key="environment", default=PlatformEnvironment.HARDWARE)

    def get_cscripts_debugger_interface_type(self):
        """
        This function is used to get cscripts debugger type from config file.

        :return: str - will return debugger type - reference- ipc inband simics
        :raise: AttributeError - if not able to find debugger type in configuration file.
        """

        cscripts_debugger_interface_type = self._cfg.find(self.CSCRIPTS_DEBUGGER_INTERFACE_TYPE)
        try:
            return cscripts_debugger_interface_type.text
        except AttributeError:
            return None

    def get_processor_qdf(self):
        """
        This function is used to platform processor QDF name from config file.

        :return: str - will return processor QDF name.
        :raise: AttributeError - if not able to find processor QDF name in configuration file.
        """
        # default_system_config_file = self.get_system_configuration_file()
        # tree = ElementTree.parse(default_system_config_file)
        # root = tree.getroot()
        cpu_qdf = self._cfg.find(self.PLATFORM_CPU_QDF)
        if not cpu_qdf.text:
            raise AttributeError("Failed to get CPU QDF name, please update the value for XML attributes "
                                 "'qdf' in configuration file...")
        return cpu_qdf.text

    def execute_sut_cmd_no_exception(self, sut_cmd, cmd_str, execute_timeout, cmd_path=None, ignore_result=None):
        """
        This function returns execution details of OS commands.

        :param sut_cmd: Get OS commands like lsmem/lscpu/lspci
        :param cmd_str: Get the name of the command
        :param execute_timeout: timeout for execute command
        :param cmd_path: path of the execute commmand
        :return: returning the output of the OS commands
        """
        try:
            sut_cmd_result = self._os.execute(sut_cmd, execute_timeout, cmd_path)
            if sut_cmd_result.cmd_failed():
                if sut_cmd_result.stderr != "":
                    log_error = "Failed to run '{}' command with return value = '{}' and " \
                                "std_error='{}'..".format(cmd_str, sut_cmd_result.return_code, sut_cmd_result.stderr)
                    self._log.error(log_error)
                    if ignore_result is None:  # validate the result and raise exception
                        raise RuntimeError(log_error)
                else:
                    log_info = "Successful to Run '{}' command with return value = '{}' and " \
                               "std_error='{}'..".format(cmd_str, sut_cmd_result.return_code, sut_cmd_result.stderr)
                    self._log.debug(log_info)
            if sut_cmd_result.stdout:
                return sut_cmd_result.stdout
            else:
                return sut_cmd_result.stderr
        except Exception as ex:
            self._log.error("Error/Exception {} executing the cmd {} ".format(ex, sut_cmd))

    def execute_sut_cmd(self, sut_cmd, cmd_str, execute_timeout, cmd_path=None):
        """
        This function returns execution details of OS commands.

        :param sut_cmd: Get OS commands like lsmem/lscpu/lspci
        :param cmd_str: Get the name of the command
        :param execute_timeout: timeout for execute command
        :param cmd_path: path of the execute commmand
        :return: returning the output of the OS commands
        """
        sut_cmd_result = self._os.execute(sut_cmd, execute_timeout, cmd_path)
        if sut_cmd_result.cmd_failed():
            log_error = "Failed to run '{}' command with return value = '{}' and " \
                        "std_error='{}'..".format(cmd_str, sut_cmd_result.return_code, sut_cmd_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        else:
            self._log.debug(sut_cmd_result.stdout)

        return sut_cmd_result.stdout

    def execute_sut_cmd_async(self, sut_cmd, cmd_str, execute_timeout, cmd_path=None, ps_name=None):
        """
        This function returns execution details of OS commands.

        :param sut_cmd: Get OS commands like lsmem/lscpu/lspci
        :param cmd_str: Get the name of the command
        :param execute_timeout: timeout for execute command
        :param cmd_path: path of the execute commmand
        :param ps_name: ps name string for commmand
        :return: returning the output of the OS commands
        """
        if ps_name is not None:
            ps_name_new = "dtaf_fabric_{}".format(ps_name)
            sut_cmd_result = self._os.execute_async(sut_cmd, ps_name=ps_name_new)
        else:
            sut_cmd_result = self._os.execute_async(sut_cmd)
        time.sleep(self.SLEEP_AFTER_ASYNC_CMD)
        self._log.info("Command executed successfully\n")
        return sut_cmd_result

    def get_running_process_instances_on_host(self, process_name):
        """
        This function returns execution details of OS commands.

        :param process_name: specified process name string for powershell command
        :return: returning the ID's of the current running processes as list instances_pids
        """
        list_processes_cmd = 'powershell -Command "Get-Process | Select name, Id | where-Object {$_.name -eq \'%s\'}|format-list"'% process_name

        cmd_output = self.execute_cmd_on_host(list_processes_cmd).replace(b"\r\n", b" ").decode('utf-8')
        instances_pids = [data for data in cmd_output.split() if data.isdigit()]
        return instances_pids

    def terminate_process_instances_on_host(self, instances_pids):
        """
        This function executes termination of the current running processes as specified in instances_pids list

        :param instances_pids: list of ID's of current running processes
        """
        for pid in instances_pids:
            self.execute_cmd_on_host("taskkill /f /pid %s" % pid)

    def execute_cmd_on_host(self, cmd_line, cwd=None):
        """
        This function executes command line on HOST and returns the stdout.

        :param cmd_line: command line to execute

        :raises RunTimeError: if command line failed to execute or returns error
        :return: returns stdout of the command
        """
        if cwd:
            process_obj = subprocess.Popen(cmd_line, cwd=cwd ,stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        else:
            process_obj = subprocess.Popen(cmd_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                           shell=True)
        stdout, stderr = process_obj.communicate()

        if process_obj.returncode != 0:
            log_error = "The command '{}' failed with error '{}' ...".format(cmd_line, stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info("The command '{}' executed successfully..".format(cmd_line))
        return stdout

    def execute_boot_script(self):
        """
        This function executes boot script command line HOST and returns the result.

        :raises RunTimeError: if command line failed to execute or returns error
        :return: returns True if command executed successfully
        """
        self._log.info("In execute boot script function...")
        boot_script_status = False
        output = self.execute_cmd_on_host("where python")
        python_exe_path = str(output.decode('utf-8')).strip("\r\n")
        boot_script_path = os.path.join(self.get_project_src_path(), r"src\utils\execute_boot_script.py")

        cmd_line = python_exe_path + " " + boot_script_path

        process_obj = subprocess.Popen(cmd_line, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, shell=True)

        self._log.info("Boot script execution start...")
        for message in iter(process_obj.stdout.readline, b''):
            try:
                message = message.rstrip().decode("utf-8").strip()
                self._log.info(message)
                if (BootScriptConstants.BOOT_SCRIPT_PASSED in message or
                        BootScriptConstants.BOOT_SCRIPT_PASS_SCORE_1800 in message or
                        BootScriptConstants.BOOT_SCRIPT_PASS_SCORE_2200 in message or
                        BootScriptConstants.BOOT_SCRIPT_NOT_REQUIRED in message):
                    boot_script_status = True
                if message.startswith('>>> '):
                    process_obj.stdin.write('exit()\n')
                    time.sleep(5)
            except Exception as ex:
                self._log.error("Exception '{}' during process readline..".format(ex))

        self._log.info("Boot script execution end...")
        self._log.info("The boot script command '{}' executed with "
                       "return value '{}'..".format(cmd_line, boot_script_status))
        return boot_script_status

    def delete_testcaseid_folder_in_host(self, test_case_id):
        """
        This function deletes the test_case_id folder under Automation path if exists.

        :param test_case_id: To create a folder with the test case id name to store logs.
        :return: None.
        """
        host_automation_path = Framework.CFG_BASE[platform.system()]
        host_testcase_path = os.path.join(host_automation_path, test_case_id)

        if os.path.exists(host_testcase_path) and os.path.isdir(host_testcase_path):
            if OperatingSystems.WINDOWS in platform.system():
                os.system("rmdir /s /q {}".format(host_testcase_path))
            elif OperatingSystems.LINUX in platform.system():
                os.system("rm -rf {}".format(host_testcase_path))
            else:
                err_log = "Directory deletion is not supported on OS %s" % self._os.sut_os
                self._log.error(err_log)
                raise NotImplementedError(err_log)

            self._log.info("Existing directory and its contents have been removed...")
        else:
            self._log.info("Test case directory does not exists on the system, will be created shortly...")

    def copy_log_files_to_host(self, test_case_id, sut_log_files_path, extension):
        """
        This function is used to copy all the logs from the system under test to local host.

        :param test_case_id: To create a folder with the test case id name to store logs.
        :param sut_log_files_path: pass the path where the log files are located.
        :param extension: will take an extension of the file(s) that needs to be copied to host.
        :return: path of destination where log files are copied from SUT to HOST.
        """

        log_dir = self.get_log_file_dir()
        self._log.info(log_dir)
        host_testcase_path = os.path.join(log_dir, test_case_id)
        self._log.info(host_testcase_path)

        if not os.path.isdir(host_testcase_path):
            os.mkdir(host_testcase_path)
            self._log.info("Folder '% s' has been created to store the logs..." % host_testcase_path)

        logs_names = None

        if OperatingSystems.WINDOWS in self._os.os_type:
            logs_names = self._os.execute("dir /b *{}".format(extension), self._command_timeout,
                                          cwd=sut_log_files_path)
        if OperatingSystems.LINUX in self._os.os_type:
            logs_names = self._os.execute("ls *{}".format(extension), self._command_timeout, cwd=sut_log_files_path)
        sut_log_file_path = None

        if len(logs_names.stdout.strip().split()) != 0:
            for log_file in logs_names.stdout.strip().split():
                try:
                    if OperatingSystems.LINUX in self._os.os_type:
                        sut_log_file_path = Path(os.path.join(sut_log_files_path, log_file)).as_posix()

                    if OperatingSystems.WINDOWS in self._os.os_type:
                        sut_log_file_path = os.path.join(sut_log_files_path, log_file)

                    host_log_files_path = os.path.join(host_testcase_path, log_file)
                    self._os.copy_file_from_sut_to_local(sut_log_file_path, host_log_files_path)
                except Exception as ex:
                    self._log.error("File copying from SUT to local was failed due to '{}'...".format(ex))
                    raise ex
        else:
            err_log = "Log file path is not found, please check once again.."
            self._log.error(err_log)
            raise IOError(err_log)

        self._log.info("Log files have been copied from SUT to local was successful...")

        return host_testcase_path

    def get_bits(self, value, beginning_bit_index, ending_bit_index=None):
        """
        Get a bit or set of bits from a hex value

        :param value:
        :param beginning_bit_index:
        :param ending_bit_index:
        :return:
        """
        if ending_bit_index is None:
            ending_bit_index = beginning_bit_index

        mask = (1 << (ending_bit_index - beginning_bit_index + 1)) - 1
        value[0] >>= beginning_bit_index
        return int(value[0] & mask)

    @staticmethod
    def get_combine_config(file_list, filename="combinedconfig"):
        """
         This function combines files present in the list and returns one new single filename.

        :param file_list: multiple file name
        :param filename: default file name
        :type: list
        :return: new file
        """
        file_name_ext = os.path.splitext(file_list[0])[1]
        new_file = os.path.join(os.getcwd(), filename + file_name_ext)
        if os.path.exists(new_file):
            os.remove(new_file)
        try:
            with open(new_file, "w") as wfd:
                for individual_filename in file_list:
                    with open(individual_filename, "r") as fd:
                        shutil.copyfileobj(fd, wfd)
                        wfd.write(os.linesep)
        except Exception as e:
            raise e
        return new_file

    @staticmethod
    def get_complete_file_path(filename, modulepath):
        """
        This function returns complete file path of the passed filename.

        :param filename: only name of the file.
        :param modulepath: python module path
        :return: This will return the complete file path.
        :raise : IOError - If file is not found.
        """
        cur_path = os.path.dirname(os.path.realpath(modulepath))
        path = os.path.basename(filename)
        complete_file_path = os.path.join(cur_path, path)
        if not os.path.isfile(complete_file_path):
            raise IOError("The file '%s' does not exist." % path)
        return complete_file_path

    @staticmethod
    def combine_files(file_list, modulepath):
        """
        This function combines the files present in the file list.

        :param file_list: list of the files to be combined together.
        :param modulepath: python module path.
        :return: This will return the complete file path with combined files
        :raise : exception if unable to combine the files.
        """
        filenameext = os.path.splitext(file_list[0])[1]
        newfile = os.path.join(os.getcwd(), "combinedconfig" + filenameext)
        if os.path.exists(newfile):
            os.remove(newfile)
        try:
            with open(newfile, "wb") as wfd:
                for individualfilename in file_list:
                    individualfilename = CommonContentLib.get_complete_file_path(individualfilename, modulepath)
                    with open(individualfilename, "rb") as fd:
                        shutil.copyfileobj(fd, wfd)
        except Exception as e:
            raise e

        return newfile

    def windows_sut_delete_folder(self, path, folder_name):
        """
        To delete a folder in windows SUT

        :param path: Total path of the windows SUT folder
        :param folder_name: Folder name to delete
        :return: None
        """
        command_result = self._os.execute("Dir", self._command_timeout, cwd=path)

        for line in command_result.stdout.strip().split("\n"):
            if re.search("{}.(.*)".format(folder_name), line):
                pass
            else:
                if folder_name in line:
                    rmdir_value = self._os.execute("rmdir /Q/S {}".format(folder_name),
                                                   self._command_timeout,
                                                   cwd=path)
                    if rmdir_value.cmd_failed():
                        log_error = "failed to run the command 'rmdir /Q/S {}' with return value = '{}' and "
                        "std error = '{}' ..".format(folder_name, rmdir_value.return_code, rmdir_value.stderr)
                        self._log.error(log_error)
                        raise RuntimeError(log_error)
                    deleted_folder_path = os.path.join(path, folder_name)
                    self._log.info("Existing directory has been deleted: {} ".format(deleted_folder_path))

    def detect_pcie_card_on_linux_sut(self,pcie_id):
        """
        Function to run the command to clear the dmesg log

        :return: True if PCIE card is detected else False
        """
        return_status = False
        cmd_to_be_executed = "lspci | grep {}".format(pcie_id)
        os_cmd_response = self._os.execute(cmd_to_be_executed, 1.0)
        if os_cmd_response.return_code == 1:
            self._log.error("Error: Could not Detect PCIE card on SUT!")
        else:
            Command_output = os_cmd_response.stdout
            self._log.info("Command Output from OS = %s ",Command_output)
            return_status = True
        return return_status

    def detect_dimms_on_linux_sut(self):
        """
        Function to check if the SUT has DIMMS installed.

        :return: True if DIMMS are detected else False
        """
        return_status = False
        os_cmd_response = self._os.execute("ipmctl show -dimm", 1.5)
        if "No DIMMs in the system" in os_cmd_response.stdout:
            self._log.error("Error: Could not Detect DIMMs on SUT!")
        else:
            command_output = os_cmd_response.stdout
            self._log.info("Command Output from OS= %s", command_output)
            return_status = True
        return return_status

    def collect_all_logs_from_linux_sut(self):
        """
        This Method is used to collect all the OS Level Logs such as mcelogs and dmesg logs

        :return None
        :raise RuntimeError if there is any error while collecting the logs
        """
        try:
            for command_line in self._LIST_OF_COLLECT_OS_LOGS_COMMANDS:
                cmd_result = self._os.execute(command_line, self._command_timeout)
                if cmd_result.cmd_failed():
                    log_error = "Failed to run command '{}' with " \
                                "return value = '{}' and " \
                                "std_error='{}'.."u''.format(command_line, cmd_result.return_code, cmd_result.stderr)
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
                else:
                    self._log.info("The command '{}' executed successfully.. and Output of '{}' log is {}"
                                   u''.format(command_line, command_line, cmd_result.stdout.strip()))
        except Exception as ex:
            log_error = "Unable to Collect OS Logs due to exception '{}'".format(ex)
            self._log.error(log_error)

    def clear_dmesg_log(self):
        """
        Function to run the command to clear the dmesg log

        :return: None
        :raise: RunTimeError
        """
        ret = self._os.execute("dmesg --clear", 1.0)
        if ret.cmd_failed():
            log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..". \
                format(ret, ret.return_code, ret.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def collect_dmesg_hardware_error_log(self):
        """
        This method collects logs from dmesg | grep Hardware on SUT

        :return: None
        :raise: RunTimeError
        """
        ret = self._os.execute("dmesg | grep Hardware > dmesg.log", 1.0)
        if ret.cmd_failed():
            log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..". \
                format(ret, ret.return_code, ret.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def clear_os_log(self):
        """
        Function to run the command to clear the os log

        :return: None
        :raise: RunTimeError
        """
        ret = self._os.execute("echo " " > /var/log/messages", 1.0)
        if ret.cmd_failed():
            log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..". \
                format(ret, ret.return_code, ret.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("successfully cleared the Os log")

    def create_dmesg_log(self):
        """
        Function to run the command for starting the capture process of dmesg log

        :return: None
        :raise: RunTimeError
        """
        ret = self._os.execute("dmesg > dmesg.log", 1.0)
        if ret.cmd_failed():
            log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..". \
                format(ret, ret.return_code, ret.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def create_mce_log(self):
        """
        Function to run the command for starting the capture process of mce log

        :return: None
        :raise: RunTimeError
        """
        ret = self._os.execute("journalctl -u mcelog.service  > journalctl.log", 1.0)
        if ret.cmd_failed():
            log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..". \
                format(ret, ret.return_code, ret.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def set_ieh_register_access(self, csp, access_type):
        """
        This Method is used to set the Ieh Register Access based on the Access type Passed.

        :param csp: cscripts object
        :param access_type: Type of the Access
        """
        self._log.info("Check Register Access Method and Update the Access to '{}'".format(access_type))
        ieh_global_access = csp.get_sockets().uncore.ieh_global.get_access()
        if access_type not in ieh_global_access:
            self._log.info("Set the Ieh Global Register Access to '{}'".format(access_type))
            csp.get_sockets().uncore.ieh_global.set_access(access_type)

        self._log.info("Ieh Global Access is set to '{}' Successfully".format(access_type))
        iehs_access = csp.get_sockets().uncore.iehs.get_access()
        if access_type not in iehs_access:
            self._log.info("Set the Iehs Register Access to '{}'".format(access_type))
            csp.get_sockets().uncore.iehs.set_access(access_type)

        self._log.info("Iehs Access was set to '{}' Successfully".format(access_type))

    def copy_zip_file_to_sut(self, sut_folder_name, host_tool_path):
        """
        copy zip file to windows SUT and unzip

        :param : sut_folder_name : name of the folder in SUT
        :param : zip_file : path of the zip file in Host
        :return: The extracted folder path in SUT
        """
        zip_file = os.path.basename(host_tool_path)
        if not os.path.isfile(host_tool_path):
            raise IOError("{} does not found".format(host_tool_path))

        # copying file to windows SUT in C:\\ from host
        self._os.copy_local_file_to_sut(host_tool_path, self.C_DRIVE_PATH)

        # delete the folder in Window SUT
        self.windows_sut_delete_folder(self.C_DRIVE_PATH, sut_folder_name)

        # creating the folder and extract the zip file
        command_result = self._os.execute("mkdir {} && tar xf {} -C {}"
                                          .format(sut_folder_name, zip_file, sut_folder_name),
                                          timeout=self._command_timeout, cwd=self.C_DRIVE_PATH)
        if command_result.cmd_failed():
            log_error = "failed to run the command 'mkdir && tar' with return value = '{}' and " \
                        "std error = '{}' ..".format(command_result.return_code, command_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        sut_path_sut = os.path.join(self.C_DRIVE_PATH, sut_folder_name)

        self._log.info("The file '{}' has been unzipped successfully ..".format(zip_file))
        return sut_path_sut

    def get_free_drive_letter(self):
        """
        Function to get a free letter to assign to the new partition.

        :return: drive letter
        """
        letter_not_found = True
        free_letter = None

        while letter_not_found:
            compare_res = []
            free_letter = random.choice(string.ascii_uppercase)
            caption_verify = self.execute_sut_cmd("wmic logicaldisk get caption,drivetype", "get drive captions",
                                                  self._command_timeout)

            self._log.info("Available caption(s) : {}".format(caption_verify.strip().split("\n")))
            for cap in caption_verify.strip().split("\n"):
                if ":" in cap:
                    cap_letter = cap.replace(":", "").strip().split()
                    if free_letter != cap_letter[0]:
                        compare_res.append(True)
                    else:
                        compare_res.append(False)
                        self._log.error("Drive letter {} already exists".format(free_letter))

            if all(compare_res):
                letter_not_found = False

        if not letter_not_found:
            self._log.info("New drive letter {} has been generated...".format(free_letter))

        return free_letter

    def get_ipmctl_name(self):
        """
        This function is used to assign the ipmctl executer name based on OS.

        :return ipmctl_change_executer_name
        """

        if OperatingSystems.WINDOWS in self._os.os_type:
            ipmctl_change_executer_name = self.IPMCTL_WIN_EXECUTER
        elif OperatingSystems.LINUX in self._os.os_type:
            ipmctl_change_executer_name = self.IPMCTL_LINUX_EXECUTER
        else:
            self._log.error("IPMCTL tool is not supported for this OS %s" % self._os.os_type)
            raise NotImplementedError("IPMCTL tool is not supported for this OS %s" % self._os.os_type)

        return ipmctl_change_executer_name

    def get_number_of_cpu_win(self):
        no_of_total_cpu = 0
        command = "wmic cpu get NumberOfLogicalProcessors /Format:List"
        cmd_result = self.execute_sut_cmd(command, "To get no of Logical Processors", self._command_timeout)
        match_data = re.findall("NumberOfLogicalProcessors=.*", cmd_result)
        if match_data:
            for data in match_data:
                no = data.split("=")[1]
                no_of_total_cpu = no_of_total_cpu + int(no)

        return no_of_total_cpu

    def get_core_count_from_os(self):
        """
        Get core count from SUT - default is Linux, but windows(win) can also be used

        :return int core count
        """
        core_count = 0
        if OperatingSystems.WINDOWS in self._os.os_type:
            core_count = self.get_number_of_cpu_win()
            if core_count != 0:
                self._log.info("Core count from OS=%d", core_count)
                return_status = True
            else:
                return_status = False
        elif OperatingSystems.LINUX in self._os.os_type:
            os_cmd_response = self._os.execute("nproc --all", 1.0)
            if os_cmd_response.return_code == 1:
                self._log.error("Error: Could not get the available cores from OS")
                return_status = False
            else:
                core_count = int(os_cmd_response.stdout)
                self._log.info("Core count from OS=%d", core_count)
                return_status = True
        else:
            self._log.error("get_core_count_from_os() is not implemented for this OS %s" % self._os.os_type)
            raise NotImplementedError("get_core_count_from_os() is not implemented for this OS %s" % self._os.os_type)

        return int(core_count), return_status

    def get_itp_core_count(self, csp):
        """
        This Method is Used to get the Core Count from Itp Commands

        :param csp: cscripts object
        :return  ITP core count and raw ITP response
        """

        if self.product in self.SILICON_10NM_CPU:
            itp_core_cnt_raw = int(csp.get_sockets()[0].uncore.punit.resolved_cores_cfg)
        else:
            itp_core_cnt_raw = int(csp.get_sockets()[0].uncore0.pcu_cr_resolved_cores_cfg)

        itp_core_cnt = bin(itp_core_cnt_raw).count("1")

        return itp_core_cnt, itp_core_cnt_raw

    def get_log_file_path(self, test_case_id, filename):
        """
        # Get the Path for cscript log file

        :return: log file path
        """
        host_automation_path = Framework.CFG_BASE[platform.system()]
        host_testcase_path = os.path.join(str(host_automation_path), test_case_id)

        if not os.path.isdir(host_testcase_path):
            os.mkdir(host_testcase_path)
            self._log.info("Folder '% s' has been created to store the logs..." % host_testcase_path)

        log_file_path = os.path.join(host_testcase_path, filename)

        return log_file_path

    def get_collateral_path(self):
        """
        Function to get the collateral directory path

        :return: collateral_path
        """
        try:
            parent_path = Path(os.path.dirname(os.path.realpath(__file__)))
            collateral_path = os.path.join(str(parent_path), self.COLLATERAL_DIR_NAME)
            return collateral_path
        except Exception as ex:
            self._log.error("Exception occurred while running running the 'get_collateral_path' function")
            raise ex

    def copy_zip_file_to_esxi_sut(self, sut_folder_name, host_zip_file_path, dont_delete=None):
        """
        copy zip file to ESXi SUT and unzip

        :param : sut_folder_name : name of the folder in SUT
        :param : host_zip_file_path : name of the zip file in Host
        :return: The extracted folder path in SUT
        """
        return self.copy_zip_file_to_linux_sut(sut_folder_name=sut_folder_name, host_zip_file_path=host_zip_file_path,
                                               dont_delete=dont_delete)

    def copy_zip_file_to_linux_sut(self, sut_folder_name, host_zip_file_path, dont_delete=None):
        """
        copy zip file to Linux SUT and unzip

        :param : sut_folder_name : name of the folder in SUT
        :param : host_zip_file_path : name of the zip file in Host
        :return: The extracted folder path in SUT
        """
        if LinuxDistributions.Cnos.lower() in self._os.os_subtype.lower():
            self.ROOT_PATH = self.AURORA_TOOL_PATH
        file_name = os.path.basename(host_zip_file_path)
        if not os.path.isfile(host_zip_file_path):
            raise IOError("{} does not found".format(host_zip_file_path))

        if dont_delete is None:
            self.execute_sut_cmd("rm -rf {}".format(sut_folder_name), "To delete a "
                                                                  "folder",
                                 self._command_timeout, self.ROOT_PATH)

            self.execute_sut_cmd("mkdir -p {}".format(sut_folder_name), "To Create a "
                                                                        "folder",
                                 self._command_timeout, self.ROOT_PATH)
        else:
            sut_folder_name_find = self.execute_sut_cmd_no_exception("find / -type d -samefile {}".
                                                                                  format(sut_folder_name),
                                                                                  "find the sut folder path",
                                                                                  self._command_timeout,
                                                                                  cmd_path=self.ROOT_PATH,
                                                                                  ignore_result="ignore")
            self._log.debug("find sut folder path {} result {}".format(sut_folder_name, sut_folder_name_find))
            if sut_folder_name_find == "" or \
                    len(re.findall(r'.*No such file or directory.*', sut_folder_name_find, re.IGNORECASE)) > 0:
                self.execute_sut_cmd("mkdir -p '{}'".format(sut_folder_name), "To Create a "
                                                                            "folder",
                                     self._command_timeout, self.ROOT_PATH)

        sut_folder_path = Path(os.path.join(self.ROOT_PATH, sut_folder_name)).as_posix()

        # copying file to Linux SUT in root from host
        self._os.copy_local_file_to_sut(host_zip_file_path, sut_folder_path)

        return self.extract_compressed_file(sut_folder_path, file_name, sut_folder_name)


    def copy_zip_file_to_esxi(self, sut_folder_name, host_zip_file_path, dont_delete=None):
        file_name = os.path.basename(host_zip_file_path)
        if not os.path.isfile(host_zip_file_path):
            raise IOError("{} does not found".format(host_zip_file_path))

        if dont_delete is None:
            self.execute_sut_cmd("rm -rf {}".format(sut_folder_name), "To delete a "
                                                                  "folder",
                                 self._command_timeout, self.ESXI_DEFAULT_PATH)

            self.execute_sut_cmd("mkdir -p {}".format(sut_folder_name), "To Create a "
                                                                        "folder",
                                 self._command_timeout, self.ESXI_DEFAULT_PATH)
        else:
            sut_folder_name_find = self.execute_sut_cmd_no_exception("find / -type d -samefile {}".
                                                                                  format(sut_folder_name),
                                                                                  "find the sut folder path",
                                                                                  self._command_timeout,
                                                                                  cmd_path=self.ESXI_DEFAULT_PATH,
                                                                                  ignore_result="ignore")
            self._log.debug("find sut folder path {} result {}".format(sut_folder_name, sut_folder_name_find))
            if sut_folder_name_find == "" or \
                    len(re.findall(r'.*No such file or directory.*', sut_folder_name_find, re.IGNORECASE)) > 0:
                self.execute_sut_cmd("mkdir -p '{}'".format(sut_folder_name), "To Create a "
                                                                            "folder",
                                     self._command_timeout,self.ESXI_DEFAULT_PATH)

        sut_folder_path = Path(os.path.join(self.ESXI_DEFAULT_PATH, sut_folder_name)).as_posix()

        # copying file to Linux SUT in root from host
        self._os.copy_local_file_to_sut(host_zip_file_path, sut_folder_path)

        return self.extract_compressed_file_esxi(sut_folder_path, file_name, sut_folder_name)

    def extract_compressed_file_esxi(self, sut_folder_path, zip_file, folder_name):
        """
        This function Extract the compressed file.

        :param : sut_folder_path : sut folder path
        :param : folder_name : name of the folder in SUT
        :param : zip_file : name of the zip file.

        :return: The extracted folder path in SUT.
        """
        self._log.info("extracts the compressed file")
        expected_files_extn = (".tar.gz", ".tar.xz", ".tgz", ".txz", ".tar")
        unzip_command = "unzip -o {}".format(zip_file)
        if zip_file.endswith(expected_files_extn):
            unzip_command = "tar -xvf {}".format(zip_file)
        self.execute_sut_cmd(unzip_command, "unzip the folder",
                             self._command_timeout, sut_folder_path)
        tool_path_sut = Path(os.path.join(self.ESXI_DEFAULT_PATH, folder_name)).as_posix()

        # copying file to Linux SUT in root from host

        self._log.debug("The file '{}' has been unzipped successfully "
                        "..".format(zip_file))
        # Remove the zip file after decompressing
        command_extract_tar_file = self.REMOVE_FILE.format(tool_path_sut + "/" + zip_file)
        self.execute_sut_cmd(command_extract_tar_file, "remove zip file", self._command_timeout)
        self._log.debug("The zip file after decompressing is removed "
                        "successfully")
        self._os.execute("chmod -R 777 %s" % tool_path_sut,
                         self._command_timeout)

        return tool_path_sut



    def extract_compressed_file(self, sut_folder_path, zip_file, folder_name):
        """
        This function Extract the compressed file.

        :param : sut_folder_path : sut folder path
        :param : folder_name : name of the folder in SUT
        :param : zip_file : name of the zip file.

        :return: The extracted folder path in SUT.
        """
        self._log.info("extracts the compressed file")
        expected_files_extn = (".tar.gz", ".tar.xz", ".tgz", ".txz", ".tar")
        unzip_command = "unzip -o {}".format(zip_file)
        if zip_file.endswith(expected_files_extn):
            unzip_command = "tar -xvf {}".format(zip_file)
        if LinuxDistributions.Cnos.lower() in self._os.os_subtype.lower():
            self.execute_sut_cmd("zypper --non-interactive install unzip", "install unzip", self._command_timeout,
                                 sut_folder_path)
        self.execute_sut_cmd(unzip_command, "unzip the folder",
                             self._command_timeout, sut_folder_path)

        #self.execute_sut_cmd("unzip {}".format(zip_file), "unzip the folder", self._command_timeout,
        #                    sut_folder_path)

        tool_path_sut = Path(os.path.join(self.ROOT_PATH, folder_name)).as_posix()

        # copying file to Linux SUT in root from host

        self._log.debug("The file '{}' has been unzipped successfully "
                       "..".format(zip_file))
        # Remove the zip file after decompressing
        command_extract_tar_file = self.REMOVE_FILE.format(tool_path_sut + "/" + zip_file)
        self.execute_sut_cmd(command_extract_tar_file, "remove zip file", self._command_timeout)
        self._log.debug("The zip file after decompressing is removed "
                        "successfully")
        self._os.execute("chmod -R 777 %s" % tool_path_sut,
                         self._command_timeout)

        return tool_path_sut

    def execute_platform_cycler(self, feature, no_of_cycles, wait_time, command_timeout, tool_path):
        """
        Execute Platform Cycler tool with given cycle

        :param : feature : command with the particular feature ex: reboot, reboot s
        :param : no_of_cycles : no of cycles The test need to execute
        :param : wait_time : wait time for the feature to execute
        :param : command_timeout : timeout to execute the cycler command
        :param : tool_path : platform cycler installed tool path
        :return: True on Success
        :raise : RunTimeError
        """

        result = self.execute_sut_cmd("./installer {} -c {} -w {} -Y".format(feature, no_of_cycles, wait_time),
                                      "Executing Platform Cycler", command_timeout, cmd_path=tool_path)
        if not result:
            err_msg = "Fail to execute the Platform Cycler tool"
            self._log.error(err_msg)
            raise RuntimeError(err_msg)
        self._log.info("Successfully executed Platform Cycler tool")
        return True

    def recursive_file_search(self, folder_path, file_name):
        """
        This function searches for the given file in the given dir including sub directories and returns the complete path.

        :param name:
        :param tool_dir:
        :return: return the complete path of the file else none
        """

        for root, dirs, files in os.walk(folder_path):
            if file_name in files:
                return os.path.join(root, file_name)

    def verify_port_state(self, csp, socket, port):
        """
        Checking specific port link state

        :param csp: CScripts object
        :param socket:
        :param port:
        :return bool   True if current port is in a good state
        """

        good_state = [0xf, 0x5, 0xd]

        ph_css_path_dict = {ProductFamilies.CLX: "kti" + str(port) + "_reut_ph_css",
                            ProductFamilies.CPX: "kti" + str(port) + "_reut_ph_css",
                            ProductFamilies.ICX: "upi.upi" + str(port) + ".ktireut_ph_css",
                            ProductFamilies.SPR: "upi.upi" + str(port) + ".ktireut_ph_css"}
        rx_state = csp.get_field_value(csp.UNCORE,
                                       reg_path=ph_css_path_dict[csp.silicon_cpu_family],
                                       field="s_rx_state", socket_index=socket)
        tx_state = csp.get_field_value(csp.UNCORE,
                                       reg_path=ph_css_path_dict[csp.silicon_cpu_family],
                                       field="s_tx_state", socket_index=socket)
        if rx_state not in good_state or tx_state not in good_state:
            self._log.info("Unexpected link state found on S" + str(socket) + " port" + str(port) +
                           "(expected=" + str(good_state) + ")but found rx Link state=" +
                           str(rx_state) + " & tx link state=" + str(tx_state))
            return False
        else:
            return True

    def copy_ilvss_pkx_file_from_host_to_linux_sut(self, folder_name, host_folder_path):
        """
        Copy ilvss package file to Linux SUT

        :param : folder_name : name of the folder in SUT
        :param : file : name of the file in Host
        :return : None
        :raise : IOError
        """

        if not os.path.isfile(host_folder_path):
            log_error = "{} does not exist".format(host_folder_path)
            self._log.error(log_error)
            raise IOError(log_error)

        self._os.copy_local_file_to_sut(host_folder_path, folder_name)

    def check_platform_port_states(self, csp, socket_cnt, port_cnt, require=False):
        """
        Checking Link states. ICX and CPX have minimum 3 ports per socket if cfg'd correctly
        if require=True , this function will return a bool to indicate the requirement has been met

        :param csp: CScripts object
        :param socket_cnt:
        :param port_cnt:

        :param require: returns bool if True
        :return bool   if number of good ports >=3 to continue test # ICX and CPX have a min 3 ports/skt(6 on 4S CPX)
    """
        # Assuming max 8S
        good_port_cnt_per_skt = [0, 0, 0, 0, 0, 0, 0, 0]
        required_ports = {ProductFamilies.CLX: 2,
                          ProductFamilies.CPX: 3,
                          ProductFamilies.ICX: 2,  # LCC pkg1 has 2 ports
                          ProductFamilies.SPR: 3}
        for socket in range(socket_cnt):
            for port in range(port_cnt):
                ph_css_path_dict = {ProductFamilies.CLX: "kti" + str(port) + "_reut_ph_css",
                                    ProductFamilies.CPX: "kti" + str(port) + "_reut_ph_css",
                                    ProductFamilies.SKX: "kti" + str(port) + "_reut_ph_css",
                                    ProductFamilies.ICX: "upi.upi" + str(port) + ".ktireut_ph_css",
                                    ProductFamilies.SPR: "upi.upi" + str(port) + ".ktireut_ph_css",
                                    ProductFamilies.SNR: "upi.upi" + str(port) + ".ktireut_ph_css"}
                rx_state = csp.get_field_value(csp.UNCORE,
                                               reg_path=ph_css_path_dict[self.product],
                                               field="s_rx_state", socket_index=socket)
                tx_state = csp.get_field_value(csp.UNCORE,
                                               reg_path=ph_css_path_dict[self.product],
                                               field="s_tx_state", socket_index=socket)

                if rx_state not in self.GOOD_PORT_STATE or tx_state not in self.GOOD_PORT_STATE:
                    self._log.info("Unexpected link state found on S" + str(socket) + " port(" + str(port) +
                                   "(expected=" + str(self.GOOD_PORT_STATE) + ")but found Link state rx=" +
                                   str(rx_state) + " & tx=" + str(tx_state))
                else:
                    self._log.debug("Expected link state found(" + str(self.GOOD_PORT_STATE) + ")")
                    good_port_cnt_per_skt[socket] += 1
        if require:
            for socket in range(socket_cnt):
                if good_port_cnt_per_skt[socket] < required_ports[self.product]:
                    self._log.info("Socket" + str(socket) + " does not have the required ports available for test(" +
                                   str(good_port_cnt_per_skt[socket]) + " valid ports detected)")
                    self._log.info("Try AC cycling the platform - and run again")
                    return False
                else:
                    self._log.info(
                        "Socket" + str(socket) + " has " + str(good_port_cnt_per_skt[socket]) + " valid ports "
                                                                                                "available")
            return True, good_port_cnt_per_skt[0]

    def extract_regex_matches_from_file(self, output_log, list_regex):
        """
        Function to validate the output log as per the provided regular expression

        :param list_regex: List of regular expression for validation.
        :return: True if list of matches found all true.
        """
        try:
            regex_match_list = []
            #  Going to verify the output as per provided regular expression
            for regex_cmd in list_regex:
                validate_status = re.findall(regex_cmd, output_log)

                if validate_status:
                    print(validate_status)
                    self._log.info("Successfully found match for the regex: .. {} ".format(regex_cmd))
                    regex_match_list.append(True)
                else:
                    self._log.error("Failed to find match for the regex: .. {} ".format(regex_cmd))
                    regex_match_list.append(False)
            return all(regex_match_list)

        except Exception as e:
            self._log.error("An exception occurred:\n{}".format(str(e)))

    def get_error_inj_pcie_port_num(self, sdp, pcie):
        """
        This method returns the pcie port no using pcie_topology() and pcie_port_map()
        :param: sdp: silicon debugger object
        :param: pcie: pcie cscripts object

        :return: pcie_port no
        """
        try:
            sdp.start_log("pcie_topology.log")
            #   Doing pcie topology
            pcie.topology()
            sdp.stop_log()
            #   Getting the pcie topology log
            pcie_logfile = os.path.abspath("pcie_topology.log")
            pcie_file_handler = open(pcie_logfile, "r")
            pcie_dataframe_file_handler = open("pcie_dataframe_data.log", "w")
            root_port_list = []
            #   Reading the topology data and writing into the dataframe file
            pcie_port_topology = pcie_file_handler.readlines()
            for pcie_slot in pcie_port_topology:
                if re.match(r"Port (\S+) MBAS=", pcie_slot):
                    root_port_list.append(re.match(r"Port (\S+) MBAS=", pcie_slot).group(1))
                if "|" in pcie_slot:
                    pcie_dataframe_file_handler.write(pcie_slot)
            pcie_dataframe_file_handler.close()

            sdp.start_log("pcie_port.log")
            #   Doing pcie port map
            pcie.port_map()
            sdp.stop_log()
            logfile = os.path.abspath("pcie_port.log")
            log_file_header = open(logfile, "r")
            pcie_port_data = log_file_header.readlines()
            #   Getting the port information dictionary
            for pcie_slot in pcie_port_data:
                if re.match(self._CHECK_PORT_REGEX, pcie_slot.strip()):
                    port_info = re.match(self._CHECK_PORT_REGEX, pcie_slot.strip()).group(3)
                    value = re.match(self._CHECK_PORT_REGEX, pcie_slot.strip()).group(1)
                    key = re.match(self._CHECK_PORT_REGEX, pcie_slot.strip()).group(2)
                    self.PORT_INFO_DICT[key] = int(value)
                    self._PCIE_PORT_INFO[key] = port_info

            df = pd.read_csv("pcie_dataframe_data.log", delimiter="|", engine='python')
            df.to_csv('pcie.csv', index=False)
            pcie_csvfile = os.path.abspath("pcie.csv")
            #   Getting the pcie port dataframe
            pcie_port_df = pd.read_csv(pcie_csvfile, sep=",", encoding='utf8')
            pcie_port_df.columns = [col.strip() for col in pcie_port_df.columns]
            pcie_port_df = pcie_port_df.drop(pcie_port_df.columns[0], 1)
            #   If the root_port_list is empty then the pcie card is not connected and will return 0
            if len(root_port_list) == 0:
                self._log.info("SUT has No PCIE Card attached")
                self._log.info("0 will default to DMI port!")
                return 0
            #   Getting the required pcie port number

            for pcie_slot in root_port_list:
                pcie_port_column_vlues = [values[0].strip() for values in pcie_port_df[[pcie_slot]].values]
                if 'slot' in pcie_port_column_vlues:
                    return pcie_slot, self.PORT_INFO_DICT[pcie_slot], self._PCIE_PORT_INFO[pcie_slot]

        except Exception as ex:
            self._log.error("Exception occurred '{}'".format(ex))
            raise ex
        finally:
            sdp.go()

    def get_log_file_dir(self):
        """Gets the file handler from logger object"""
        for handler in self._log.handlers:
            if str(type(handler)) == "<class 'logging.FileHandler'>":
                return os.path.split(handler.baseFilename)[0]

    def get_linux_hostnamectl_info(self):
        """Gets the hostnamectl info"""
        cmd_result = self.execute_sut_cmd("hostnamectl", "hostname info", self._command_timeout)
        info = {}
        if cmd_result != "":
            lines = [line.strip() for line in cmd_result.splitlines() if line.strip() != ""]
            for line in lines:
                info[line.split(":")[0].strip().lower()] = ".".join(line.split(":")[1:]).strip()
        return info

    def get_linux_kernel(self):
        """Get kernel info"""
        info = self.get_linux_hostnamectl_info()
        if not len(info):
            raise RuntimeError("Failed to get hostnamectl info")
        return info["kernel"]

    def store_linux_logs(self, log_dir):
        """Store linux logs in the given location

        :param log_dir: log_dir
        """
        for command in self._STORE_LOGS_LINUX:
            if self._os.check_if_path_exists(command):
                self._os.copy_file_from_sut_to_local(command, os.path.join(log_dir, os.path.split(command)[-1]))
            elif self._os.check_if_path_exists(command, directory=True):
                tar_file = command.replace("/", "_") + ".tar.gz"
                self._os.execute("tar -czvf %s %s" % (tar_file, command), self._command_timeout, cwd=command)
                self._os.copy_file_from_sut_to_local(command + "/" + tar_file, os.path.join(log_dir, tar_file))
            else:
                log_file = "/tmp/%s.log" % command
                self._os.execute("rm -rf %s" % log_file, self._command_timeout)
                self._os.execute("%s > %s " % (command, log_file), self._command_timeout)
                self._os.copy_file_from_sut_to_local(log_file, os.path.join(log_dir, os.path.split(log_file)[-1]))

    def store_esxi_logs(self, log_dir):
        """Store esxi logs in the given location

        :param log_dir: log_dir
        """
        for command in self._STORE_LOGS_ESXI:
            if self._os.check_if_path_exists(command):
                self._os.copy_file_from_sut_to_local(command, os.path.join(log_dir, os.path.split(command)[-1]))
            elif self._os.check_if_path_exists(command, directory=True):
                tar_file = command.replace("/", "_") + ".tar.gz"
                self._os.execute("tar -czvf %s %s" % (tar_file, command), self._command_timeout, cwd=command)
                self._os.copy_file_from_sut_to_local(command + "/" + tar_file, os.path.join(log_dir, tar_file))
            else:
                log_file = "/tmp/%s.log" % command
                self._os.execute("rm -rf %s" % log_file, self._command_timeout)
                self._os.execute("%s > %s " % (command, log_file), self._command_timeout)
                self._os.copy_file_from_sut_to_local(log_file, os.path.join(log_dir, os.path.split(log_file)[-1]))

    def store_os_logs(self, log_dir):
        """Stores the logs

        :param log_dir: log_dir
        """
        self._log.info("Collecting logs")
        if not os.path.exists(os.path.join(log_dir, "system_logs")):
            log_dir = log_dir + "/" + "system_logs"
            os.makedirs(log_dir)
        if self._os.os_type == OperatingSystems.LINUX:
            self.store_linux_logs(log_dir)
        elif self._os.os_type == OperatingSystems.WINDOWS:
            self.get_windows_event_logs_from_sut(log_dir)
        elif self._os.os_type == OperatingSystems.ESXI:
            self.store_esxi_logs(log_dir)
        else:
            raise RuntimeError("store_logs is not implemented for %s" % self._os.os_type)

    def copy_directory_to_linux_sut(self, local_path, remote_path):
        """Copies the local directory to remote

        :param local_path: Local host path
        :param remote_path: Remote directory
        """
        directory = os.path.split(local_path)[-1].strip()
        files = [os.path.join(local_path, file) for file in
                 os.listdir(local_path)]
        remote_path = remote_path + "/" + directory
        self._log.info("Remote path: %s", remote_path)
        if not self._os.check_if_path_exists(remote_path, directory=True):
            sut_cmd = self._os.execute("mkdir -p %s" % remote_path,
                                       self._command_timeout)
            self._log.debug(sut_cmd.stdout)
            self._log.error(sut_cmd.stderr)
        for file in files:
            self._log.debug("Copying %s to %s", file, remote_path)
            self._os.copy_local_file_to_sut(file, remote_path)

    def get_cpu_physical_chop_info(self, csp, sdp, log_file_path):
        """
        This Method is Used to get the CPUChop Info by using Cscripts

        :return: LCC or HCC or XCC
        """
        self._log.info("")
        sdp.start_log(log_file_path, "w")
        csp.get_cscripts_utils().get_uncoreinfo_obj().dumpCapidRegs(0, 4)
        sdp.stop_log()
        with open(log_file_path, "r") as log_file:
            log_file_list = log_file.readlines()
            self._log.info("".join(log_file_list))
            regex_cmd_hcc = re.findall(self._REGEX_CMD_FOR_HCC, "".join(log_file_list))
            regex_cmd_xcc = re.findall(self._REGEX_CMD_FOR_XCC, "".join(log_file_list))
            regex_cmd_lcc = re.findall(self._REGEX_CMD_FOR_LCC, "".join(log_file_list))
            if regex_cmd_hcc:
                return self.HCC
            elif regex_cmd_xcc:
                return self.XCC
            else:
                return self.LCC

    def clear_mce_errors(self):
        """
        This Method check the OS platform and clear Machine check event logs.
        """
        if OperatingSystems.WINDOWS in self._os.os_type:
            return self.clear_windows_mce_logs()
        elif OperatingSystems.LINUX in self._os.os_type:
            return self.clear_linux_mce_logs()
        else:
            raise NotImplementedError(" Clear Machine Check Events logs is not Implemented for this OS %s"
                                      % self._os.os_type)

    def clear_linux_mce_logs(self):
        """Clears the linux mce logs"""
        from src.lib import install_collateral
        _install_collateral = install_collateral.InstallCollateral(self._log, self._os, self._cfg)
        _install_collateral.install_abrt_cli_in_linux()
        self._log.debug("clearing linux mce logs")
        sut_cmd = self._os.execute("abrt-cli rm /var/spool/abrt/*",
                                   self._command_timeout)
        self._log.debug(sut_cmd.stdout)
        self._log.error(sut_cmd.stderr)

    def clear_windows_mce_logs(self):
        """
        This function is used to clear both system logs and Hardware event logs in windows
        """
        self._log.debug("Clearing Windows MCE Logs")
        self._windows_event_log_obj.clear_system_event_logs()
        self._windows_event_log_obj.clear_hardware_event_logs()

    def check_if_linux_mce_errors(self):
        """Checks the linux MCE Errors"""
        from src.lib import install_collateral
        ignore_mce_error = self._common_content_configuration.get_ignore_mce_errors_value()
        _install_collateral = install_collateral.InstallCollateral(self._log, self._os, self._cfg)
        _install_collateral.install_abrt_cli_in_linux()
        self._log.debug("Checking for MCE logs")
        sut_cmd = self._os.execute('abrt-cli list | grep -i "mce"',
                                   self._command_timeout)
        self._log.debug("ABRT-CLI CMD output: %s", sut_cmd.stdout.strip())
        self._log.error("ABRT-CLI CMD Error: %s", sut_cmd.stderr.strip())
        if sut_cmd.stderr.strip() != "":
            raise RuntimeError("failed to execute abrt-cli: %s",
                               sut_cmd.stderr.strip())
        if not ignore_mce_error:
            return sut_cmd.stdout.strip()
        else:
            self._log.error("MCE ERRORS:{}\n".format(sut_cmd.stdout.strip()))
            return

    def check_if_mce_errors(self):
        """
        This Method check the OS platform and Machine check event status.
        """
        if OperatingSystems.WINDOWS in self._os.os_type:
            return self._windows_event_log_obj.check_windows_mce_logs()
        elif OperatingSystems.LINUX in self._os.os_type:
            return self.check_if_linux_mce_errors()
        else:
            raise NotImplementedError("Verification of Machine Check Events is not Implemented for this OS %s"
                                      % self._os.os_type)

    def get_windows_event_logs_from_sut(self, log_dir):
        """
         Store windows logs in the given location

        :param log_dir: Log Directory
        :return: None
        raise: RuntimeError
        """
        try:
            self.delete_windows_sut_event_logs()
            sut_log_file_path = os.path.join(self.C_DRIVE_PATH, self.WINDOWS_SUT_EVENT_LOG_FOLDER)
            for command in self._STORE_LOGS_WINDOWS:
                self.execute_sut_cmd(
                    'powershell.exe "Get-EventLog -LogName {} >> {}.log'.format(command, command),
                    "Execute the power shell command", self._command_timeout, cmd_path=sut_log_file_path)
            self.copy_log_files_to_host(log_dir, sut_log_file_path, extension=".log")
        except Exception as ex:
            raise RuntimeError("Error while executing the Store windows logs with exception = '{}'".format(ex))

    def delete_windows_sut_event_logs(self):
        """
        Delete the windows SUT event Log.

        :return None
        raise: RuntimeError
        """
        try:
            self._log.debug("To delete the existing log folder in SUT")
            self.windows_sut_delete_folder(self.C_DRIVE_PATH, self.WINDOWS_SUT_EVENT_LOG_FOLDER)
            self.execute_sut_cmd("mkdir {}".format(self.WINDOWS_SUT_EVENT_LOG_FOLDER), "Create a log folder",
                                 self._command_timeout, cmd_path=self.C_DRIVE_PATH)
        except Exception as ex:
            raise RuntimeError("Error while deleting windows logs folder on SUT with exception = '{}'".format(ex))

    def extract_zip_file_on_host(self, zip_file_path, dest_path):
        """
        This method extracts the zip file on specified destination folder on HOST.

        :param zip_file_path: zip file with path to be extracted
        :param dest_path: destination folder where zip file to be extracted

        :raises: RuntimeError - if failed to extract the zip file.
        :return: None
        """
        try:
            self._log.info("Extracting zip file '{}' to destination folder '{}'..".format(zip_file_path, dest_path))
            with ZipFile(zip_file_path, 'r') as zp:
                zp.extractall(path=dest_path)
                self._log.info("Extract zip file: Successful..")
        except Exception as ex:
            log_error = "Extract zip file: Failed due to exception '{}'..".format(ex)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def get_linux_flavour(self):
        """Get linux os subtype."""
        info = self.get_linux_hostnamectl_info()
        if not len(info):
            raise RuntimeError("Failed to get hostnamectl info")
        sub_os = info.get("operating system")
        if "Red Hat" in sub_os:
            return LinuxDistributions.RHEL
        elif "Ubuntu" in sub_os:
            return LinuxDistributions.Ubuntu
        elif "CentOS" in sub_os:
            return LinuxDistributions.CentOS
        elif "Fedora" in sub_os:
            return LinuxDistributions.Fedora
        elif "SLES" in sub_os:
            return LinuxDistributions.SLES
        elif "ClearLinux" in sub_os:
            return LinuxDistributions.ClearLinux
        elif "Compute Node" in sub_os:
            return LinuxDistributions.Cnos
        return None

    def execute_cmd_and_get_unmatched_result(self, cmd_to_execute, cmd_info, string_pattern_to_search,
                                             cmd_timeout, cwd_path=None):
        """
        This method executes the command and verifies the generated output with the input string pattern.

        :param cmd_to_execute: command to execute
        :param cmd_info: the command information
        :param string_pattern_to_search: string to be search
        :param cmd_timeout: timeout for execute command
        :param cwd_path: path of the execute command
        :raise: Content_exception if unable to find the match pattern
        :return: return the non matching strings
        """
        command_result = self.execute_sut_cmd(cmd_to_execute, cmd_info, cmd_timeout, cwd_path)
        self._log.debug("Output of the command '{} is '{}".format(cmd_to_execute, command_result))

        no_matches = []
        for string_item in string_pattern_to_search:
            if string_item not in command_result:
                no_matches.append(string_item)
        return no_matches

    @staticmethod
    def get_list_of_digits(list_of_elements):
        """
        Function to return a list of numeric values by removing all other alphabets.

        @param list_of_elements: takes a list of elements
        @return: list of numeric values
        """
        if isinstance(list_of_elements, list):
            return list(map(lambda sub: int(''.join([ele for ele in sub if ele.isnumeric()])),
                            list_of_elements))
        else:
            raise ValueError("List of elements must be a list..")

    @staticmethod
    def get_digit(element):
        """
        Function to return a numeric by removing all other alphabets.

        @param element: takes an elements
        @return: a string value
        """
        if isinstance(element, str):
            return ''.join([ele for ele in element if ele.isnumeric() or "." in ele])
        else:
            raise ValueError("Element must be a string..")

    @staticmethod
    def list_flattening(list_to_flatten):
        """
        Function to flatten a list - if you have a list inside list, this will change that to only one list

        @param list_to_flatten: list to be flattened
        @return: flattened list
        """
        return [item for elem in list_to_flatten for item in elem]

    def copy_tool_to_collateral(self, tool_path):
        """
        Function to copy tools from C:/Automation/BKC/Tools to src/lib/collateral folder

        @param tool_path: path of the tool from config file
        @return file_name: name of the file that was copied to collateral
        """
        file_name = os.path.split(tool_path)[-1].strip()
        try:
            # Copy file from C:/Automation/BKC/Tools to src/lib/collateral folder
            collateral_path = self.get_collateral_path()
            copy(tool_path, collateral_path)
        except Exception as ex:
            raise ex
        else:
            self._log.info("Successfully copied {} file to '{}' directory...".format(file_name, collateral_path))

        return file_name

    def get_cpu_utilization(self):
        """
        Function to get the SUT CPU utilization.

        :return: cpu utilization value
        :raise: None
        """
        result = self.execute_sut_cmd(sut_cmd=self.GET_CPU_PERCENTAGE_COMMAND, cmd_str=self.GET_CPU_PERCENTAGE_COMMAND,
                                      execute_timeout=self._command_timeout)
        return_output = result.strip().split(' ')
        self._log.debug(return_output)
        return float(return_output[0])

    def get_python_path(self):
        """
        Returns the default python path on host..

        :return: python path
        """
        output = self.execute_cmd_on_host("where python")
        python_exe_path = str(output.decode('utf-8')).strip("\r\n")
        return python_exe_path

    @staticmethod
    def get_log_file_path(log):
        """Gets the file handler from logger object"""
        for handler in log.handlers:
            if str(type(handler)) == "<class 'logging.FileHandler'>":
                return handler.baseFilename

    @staticmethod
    def execute_pythonsv_function_in_separate_process(queue, product, pch, log_path, list_sv_packages, function_obj):
        """
        :param: queue - queue for sending the commands results back to caller
        :param: product - product family e.g. ICX, SPR etc
        :param: pch - pch family e.g. LGB, EMT etc
        :param: log_path - log path to store the logs of pythonsv command execution
        :param: list_sv_packages - list of sv packages
        :param: function_obj - call back function, which executes specific pythonsv commands

        :return: True if command executed successfully else returns False
        """
        ret_val = False
        log_cfg = ElementTree.fromstring(ProviderXmlConfigs.LOG_XML_CONFIG.format(log_path))
        log = log_utils.create_logger(function_obj.__name__, True, log_cfg)
        log_file_path = CommonContentLib.get_log_file_path(log)

        try:
            # add python sv packages to sys path
            index = 1
            for package in list_sv_packages:
                sys.path.insert(index, package)
                index = index + 1

            si_cfg = ElementTree.fromstring(ProviderXmlConfigs.PYTHON_SV_XML_CONFIG.format(product, pch))
            sdp_cfg = ElementTree.fromstring(ProviderXmlConfigs.SDP_XML_CONFIG)
            pythonsv_log_path = os.path.join(log_path, "python_sv.log")
            with ProviderFactory.create(sdp_cfg, log) as sdp_obj:
                sdp_obj.start_log(pythonsv_log_path, "w")
                try:
                    with ProviderFactory.create(si_cfg, log) as si_reg:  # type: SiliconRegProvider
                        ret_val = function_obj(si_reg, log)
                    sdp_obj.stop_log()
                except Exception as e:
                    log.error(f"Exception caught - {e}")
                finally:
                    with open(pythonsv_log_path, "r") as fp:
                        var = fp.read()
                        log.info("PythonSV Log -\n{}".format(var))
                        fp.close()
                    os.remove(pythonsv_log_path)
        except Exception as ex:
            log_error = "Python SV function failed with exception '{}'".format(str(ex))
            log.error(log_error)
            raise RuntimeError(log_error)
        finally:
            dict_result = {CommonContentLib.KEY_RETVAL: ret_val, CommonContentLib.KEY_LOG_PATH: log_file_path}
            queue.put(dict_result)
            sys.exit(0)

    def execute_pythonsv_function(self, function_obj):
        """
        :param: function_obj - call back function, which executes specific pythonsv commands

        :return: True if command executed successfully else returns False
        """
        try:
            list_sv_packages = [r"{}\lib\site-packages", r"{}\lib\site-packages\win32",
                                r"{}\lib\site-packages\win32\lib", r"{}\lib\site-packages\win32",
                                r"{}\lib\site-packages\Pythonwin"]
            try:
                python_exe_path = self.get_python_path()
                python_path = os.path.split(python_exe_path)[0]
            except:
                python_exe_path = os.environ['PYTHON_EXE_PATH']
                python_path = os.environ['PYTHON_PATH']

            for index, item in enumerate(list_sv_packages):
                list_sv_packages[index] = item.format(python_path)

            ctx = mp.get_context('spawn')
            ctx.set_executable(python_exe_path)
            queue = ctx.Queue()

            log_path = self.get_log_file_dir()

            cpu_family = self.get_platform_family()
            pch = self.get_pch_family()
            p = ctx.Process(target=self.execute_pythonsv_function_in_separate_process,
                            args=(queue, cpu_family, pch, log_path, list_sv_packages, function_obj))
            p.start()
            p.join()
            dict_result = queue.get()
            ret_val = dict_result[self.KEY_RETVAL]
            log_path = dict_result[self.KEY_LOG_PATH]
            if os.path.isfile(log_path):
                with open(log_path) as log_file:
                    lines = log_file.readlines()
                    self._log.info("Start:Log from PythonSV command execution.")
                    for line in lines:
                        self._log.info(line.strip())
                    self._log.info("End:Log from PythonSV command execution.")
            return ret_val
        except Exception as ex:
            raise content_exceptions.TestError("Execute pythonSV command failed due to exception '{}'".format(ex))

    def check_for_bios_state(self, console_log):
        """
        check if the System has booted to BIOS
        """
        ret_value = False
        _init = _now = time.time()
        while self._common_content_configuration.get_reboot_timeout() > _now - _init:
            console_data = open(console_log).readlines()
            _now = time.time()

            if len(re.findall(self.BIOS_MODE_CHECK_REFERENCE_PLATFORM, "".join(console_data))) > 0:
                # TODO: need to handle for commercial platform
                ret_value = True
                self._log.info("System is Booted up to BIOS!")
                return ret_value
        time.sleep(self.BIOS_POLL_INTERVAL)
        self._log.error("System did not Boot up to BIOS!")
        return ret_value

    def escape_ansii_from_sequence(self, string):
        """ Remove the ansii characters from the given string

        :param string: string
        :return: string without ansii characters
        """
        reaesc = re.compile(r'\x1b[^m]*m')
        return reaesc.sub('', string)

    def convert_hexadecimal(self, numbers, to="binary", bit_width=64):
        """
        Converts the hexadecimal number to required format

        :param numbers: Numbers in list
        :param to: type to be converted
        :param bit_width: bit_width number

        :return: After converting this method will return a dictionary.
        """
        converted_numbers = {}
        for number in numbers:
            if to == NumberFormats.BINARY:
                con_bin_num = bin(int(number, 16))[2:]
                suffix_number = ""
                for i in range(bit_width - len(con_bin_num)):
                    suffix_number = suffix_number + "0"
                converted_numbers[number] = suffix_number + con_bin_num
            elif to == NumberFormats.DECIMAL:
                converted_numbers[number] = int(number, 16)
            elif to == NumberFormats.HEXADECIMAL:
                converted_numbers[number] = number
        self._log.debug("Converted values in %s format:%s", to, converted_numbers)
        return converted_numbers

    def get_binary_bit_range(self, number, bit_range):
        """
        Get Binary bit range values

        :param number: Binary Number
        :param bit_range: Bit Range

        :return: value in Bit Range.
        """
        binary_rev = number[::-1]
        return binary_rev[bit_range[0]: bit_range[-1] + 1][::-1]

    def convert_binary_to_decimal(self, number):
        """Convert the binary number to decimal"""
        return int(number, 2)

    def create_prime95_preference_txt_file(self, prime95_path, preference_prime_params):
        """
        Function to create a prime95 torture test preference file

        @param preference_prime_params: prime 95 preference
        @param prime95_path: path of the prime95 execute file.
        """

        with open("prime.txt", "w+") as fp:
            fp.writelines(preference_prime_params)

        self._os.copy_local_file_to_sut("prime.txt", prime95_path)

        self._log.info("Prime95 torture test execution preference text file has been copied under {}".format(
            prime95_path))

        if os.path.exists("prime.txt"):
            os.remove("prime.txt")

    def get_host_ip(self):
        """
        This method is to get the host ip.

        :return ip
        """
        try:
            host_name = socket.gethostname()
            ip_address = socket.gethostbyname(host_name)
            self._log.debug("Host ip is: {}".format(ip_address))
            return ip_address

        except Exception as ex:
            raise content_exceptions.TestFail("Exception Occurred during executing command to find ip: {}".format(ex))

    def get_sut_home_path(self):
        if self._os.os_type == OperatingSystems.WINDOWS:
            cmd_line = "echo %HOMEDRIVE%%HOMEPATH%"
            sut_home_path = self.execute_sut_cmd(cmd_line, cmd_line, self._command_timeout)
            sut_home_path = str(sut_home_path).strip().strip("\\n")
        elif self._os.os_type == OperatingSystems.LINUX:
            cmd_line = "echo $HOME"
            sut_home_path = self.execute_sut_cmd(cmd_line, cmd_line, self._command_timeout)
            sut_home_path = str(sut_home_path).strip().strip("\\n")
        else:
            raise NotImplementedError("This function not implemented for OS='{}'".format(self._os.os_type))
        return sut_home_path

    def get_linux_sut_ip(self):
        output =  self.execute_sut_cmd("hostname -I | awk '{print $1}'", "Get IP Address", 10.0)
        list_values = str(output).splitlines()
        return str(list_values[0]).strip()

    def get_windows_sut_ip(self):
        cmd_line = "PowerShell (Get-WmiObject -Query 'Select IPAddress from Win32_NetworkAdapterConfiguration " \
                   "where IpEnabled={}').IPAddress".format(r'"TRUE"')
        output = self.execute_sut_cmd(cmd_line, "Get IP Address", 10.0)
        list_values = str(output).splitlines()
        return str(list_values[0]).strip()

    def ping_ip(self, ip_addr):
        if OperatingSystems.WINDOWS in platform.system():
            ping_cmd = "ping -n 4 {}".format(ip_addr)
        elif OperatingSystems.LINUX in platform.system():
            ping_cmd = "ping -c 4 {}".format(ip_addr)

        response = os.system(ping_cmd)
        if 0 == response:
            self._log.info("Ping successful with IP address '{}...".format(ip_addr))
        else:
            self._log.info("Ping failed with IP address '{}...".format(ip_addr))

    def get_sut_ip(self):
        if self._os.os_type == OperatingSystems.LINUX:
            return self.get_linux_sut_ip()
        elif self._os.os_type == OperatingSystems.WINDOWS:
            return self.get_windows_sut_ip()
        else:
            raise RuntimeError("Specified OS '{}' not supported..".format(self._os.os_type))

    def ping_ip(self, ip_addr):
        if OperatingSystems.WINDOWS in platform.system():
            ping_cmd = "ping -n 4 {}".format(ip_addr)
        elif OperatingSystems.LINUX in platform.system():
            ping_cmd = "ping -c 4 {}".format(ip_addr)

        response = os.system(ping_cmd)
        if 0 == response:
            self._log.info("Ping successful with IP address '{}...".format(ip_addr))
        else:
            self._log.info("Ping failed with IP address '{}...".format(ip_addr))

    def copy_log_files_to_cc(self, cc_folder):
        dtaf_log_folder = Path(self.get_log_file_path(self._log)).parent
        folder_name = os.path.split(dtaf_log_folder)[1]
        cc_folder_path = os.path.join(cc_folder, folder_name)
        shutil.copytree(dtaf_log_folder, cc_folder_path)

    def set_itp_config(self, sdp_obj):
        """
        This Method is Used to set the ITP Config on EGS Platform for fixing msr read Issue on EGS platform.
        This is Just a Workaround.
        """
        try:
            if self.get_platform_family() == ProductFamilies.SPR:
                sdp_obj.halt()
                sdp_obj.itp.config.debugport0.PlatformControl.PrdyNotWired = "True"
        except Exception as ex:
            raise ex
        finally:
            sdp_obj.go()

    def is_itp_connected(self, sdp):
        """
        This method is used to find itp connected or not.

        :param sdp: silicon debug provider object
        :return: None
        """
        itp_connected = True
        try:
            sdp.start_log("test.log")
            sdp.stop_log()
        except Exception as e:
            self._log.debug("ITP not connected")
            itp_connected = False
        return itp_connected

    def execute_modprobe_aer_inject(self, cmd_path=None):
        """
        This method is to execute the modprobe command to inject the Error.

        :param cmd_path
        :return None
        """
        self._log.info("Execute the command : {}".format(self.MODPROBE_AER_INJECT_CMD))
        self.execute_sut_cmd(sut_cmd=self.MODPROBE_AER_INJECT_CMD, cmd_str=self.MODPROBE_AER_INJECT_CMD,
                             execute_timeout=self._command_timeout, cmd_path=cmd_path)
        self._log.info("Successfully executed the command: {}".format(self.MODPROBE_AER_INJECT_CMD))

    def get_pcie_device_bdf(self, pcie_device_name):
        """
        This method is to get the bdf value.

        :param pcie_device_name
        :return list - list is returned due to possibility of having multiple pcie devices with the same name
        """
        bdf_value_list = []
        if self._os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNotImplementedError("This Method is not implemented on : {}".format(
                self._os.os_type))

        cmd_out_put = self.execute_sut_cmd(sut_cmd="lspci | grep '{}'".format(pcie_device_name), cmd_str="pcie name",
                                           execute_timeout=self._command_timeout)
        for each_line in cmd_out_put.split('\n'):
            bdf_value_list.append(each_line.split(' ')[0])
        self._log.debug(
            "PCIe Device with name: {} is mapped with these bdf value: {}".format(pcie_device_name, bdf_value_list))

        return bdf_value_list

    def get_post_code(self, pc_phy):
        """
        returns post code, pc[0] - BIOS Post code, pc[1] - FPGA post code
        """
        bios_pc = None
        fpga_pc = None

        platform_type = self.get_platform_type()
        if platform_type in [PlatformType.HPE, PlatformType.MSFT]:
            # for HP, MSFT, post code is not available
            return bios_pc, fpga_pc

        if pc_phy:
            try:
                list_post_code = pc_phy.read_postcode()
                self._log.debug("Post Code List is : ".format(list_post_code[1:]))
                if len(list_post_code) > 1:
                    bios_pc = list_post_code[1]  # BIOS PC
                    if len(list_post_code) > 2:
                        fpga_pc = list_post_code[2]  # FPGA post code
            except Exception as ex:
                self._log.error("Unable to read the PostCode due to exception : '{}'".format(str(ex)))
        return bios_pc, fpga_pc

    def get_power_state(self, phy_obj):
        max_attempt = 5
        platform_type = self.get_platform_type()
        attempt = 0

        if platform_type == PlatformType.REFERENCE:
            while attempt < max_attempt:
                try:
                    return phy_obj.get_power_state()
                except Exception as ex:
                    self._log.error("Failed to get power state due to exception '{}'.".format(ex))
                    time.sleep(10)
                    pass
                attempt += 1
            raise RuntimeError("Failed to get power state, Please check the hardware connections.")
        elif platform_type in [PlatformType.DELL, PlatformType.HPE, PlatformType.MSFT]:
            while attempt < max_attempt:
                try:
                    power_state = PowerStates.G3
                    power_state = phy_obj.get_power_state()
                    if power_state:
                        return power_state
                except Exception as ex:
                    self._log.error("Failed to get power state due to exception '{}'.".format(ex))
                    time.sleep(10)
                attempt += 1
            return power_state
        else:
            raise NotImplementedError("For platform type {}, get_power_state is not implemented.".format(platform_type))

    def update_kernel_args_and_reboot(self, list_of_args):
        """
        This method is to update the grub config file by using kernel

        :param list_of_args: list of the arguments want to update
        """
        result_data = self.execute_sut_cmd("grubby --update-kernel=ALL --args='{}'".format(" ".join(list_of_args)),
                                           "updating grub config file",
                                           self._command_timeout)
        self._log.debug("Updated the grub config file with stdout:\n{}".format(result_data))
        # rebooting the system
        self.perform_os_reboot(self._reboot_timeout)

    def update_sut_inventory_file(self, storage_device_type, os_type):
        """
        This Method is Used to Update Sut Inventory Config File based on the device type and os we are going to install.

        :param storage_device_type: Type of Storage Device like NVME, SATA
        :param os_type: OS to be installed.
        :raise content_exceptions.TestSetupError: If sut_inventory.cfg is not available in given path
        """
        self._log.info("Updating Sut Inventory config file for {} device and {} OS".format(storage_device_type, os_type))
        cfg_parser = config_parser.ConfigParser()
        cfg_parser.read(SutInventoryConstants.SUT_INVENTORY_FILE_NAME)
        list_sections = cfg_parser.sections()
        if len(list_sections) == 0:
            raise content_exceptions.TestSetupError("Please Check Sut Inventory.cfg file")
        cfg_values_list = []
        list_options = [options for options in cfg_parser[list_sections[0]]]
        for option in cfg_parser[list_sections[0]]:
            cfg_values_list.append(cfg_parser.get(list_sections[0], option))
        sut_inventory_dict = dict(zip(list_options, cfg_values_list))
        configuration_key = [option for option in list_options if storage_device_type in option and os_type in option][0]
        configuration_value = sut_inventory_dict[configuration_key]
        configuration = configuration_key + " = " + configuration_value
        with open(SutInventoryConstants.SUT_INVENTORY_FILE_NAME, "r") as file:
            sut_inventory_list = file.readlines()
        config_index = [index for index, line in enumerate(sut_inventory_list)
                        if configuration_key in line][0]
        sut_inventory_list.pop(config_index)
        sut_inventory_list.insert(4, configuration + "\n")
        with open(SutInventoryConstants.SUT_INVENTORY_FILE_NAME, "w") as file:
            file.write("".join(sut_inventory_list).strip())
        self._log.debug("Sut Inventory config is Updated for device type {} and OS {}".format(storage_device_type, os_type))

    def install_screen_package_to_vm(self, vm_obj):
        """
        This method is to copy and install the screen package to VM.

        :param vm_obj
        """
        screen_pkg_name = "screen-4.1.0-0.25.20120314git3c2946.el7.x86_64.rpm"
        collateral_path = self.get_collateral_path()
        screen_path_in_host = os.path.join(collateral_path, screen_pkg_name)
        vm_obj.copy_local_file_to_sut(source_path=screen_path_in_host, destination_path=self.ROOT_PATH)
        cmd_result = vm_obj.execute("chmod 777 {}".format(screen_pkg_name),self._command_timeout, self.ROOT_PATH)
        self._log.info(cmd_result.stdout)
        cmd_result = vm_obj.execute("yum install -y {}".format(screen_pkg_name), self._command_timeout, self.ROOT_PATH)
        if cmd_result.cmd_failed():
            raise content_exceptions.TestFail("Failed to run command '{}' with " \
                                              "return value = '{}' and " \
                                              "std_error='{}'..".format(cmd_result,
                                                                        cmd_result.return_code, cmd_result.stderr))

        self._log.info(cmd_result.stdout)

    def get_sut_crediantials(self, cfg_opts):
        """
        Get SUT Username and password from system configuration file.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: username, password
        """
        crediantials_config_path = "suts/sut/providers/sut_os/driver/ssh/credentials"
        sut_os_cfg = cfg_opts.find(crediantials_config_path)
        self._log.info("Getting SUT username and password from system configuration file")
        username = sut_os_cfg.attrib["user"]
        password = sut_os_cfg.attrib["password"]
        self._log.debug("SUT username: {}and password:{} from system configuration file".format(username, password))
        return username, password

    def check_os_alive(self):
        try:
            if self._os.is_alive():
                return True
        except Exception as ex:
            self._log.error("Exception occurred when checking for OS is alive.")
        return False

    def shutdown_os(self):
        try:
            self._os.shutdown()
            return True
        except Exception as ex:
            self._log.error("Exception occurred during OS shutdown.")
        return False

    def get_time_format(self, seconds):
        """
        Convert seconds to days, hour, min & seconds

        :param seconds: input time in seconds
        :return: time in days, hour, min & sec format
        """
        min, sec = divmod(seconds, 60)
        hour, min = divmod(min, 60)
        days, hour = divmod(hour, 24)
        return "%02d:%02d:%02d:%02d" % (days, hour, min, sec)

    def enable_network_manager_using_startup(self):
        """
        This method is to enable the Network Manager in startup.
        """
        if self._os.os_type == OperatingSystems.LINUX:

            #  To check if Network enable command is already available in startup file: (/etc/rc.local)
            cmd_output = self._os.execute("grep \'systemctl start NetworkManager\' /etc/rc.local",
                                          self._command_timeout)
            self._log.debug(cmd_output.stdout)

            #  Writing the command into startup file if not available
            if "systemctl start NetworkManager" not in cmd_output.stdout:

                self._os.execute("echo \'sudo systemctl start NetworkManager\' >> /etc/rc.local", self._command_timeout)
                self._os.execute(
                    "echo \'systemctl status NetworkManager >> /root/network_manager_status\' >> /etc/rc.local"
                                 , self._command_timeout)

            self._os.execute("chmod +x /etc/rc.d/rc.local", self._command_timeout)
        else:
            pass

    def is_linux_fully_booted(self):
        try:
            return_status = False
            cmd_to_be_executed = "service NetworkManager status | grep \"Active: active\""
            os_cmd_response = self._os.execute(cmd_to_be_executed, 1.0)
            if "Active: active" not in os_cmd_response.stdout:
                self._log.info("Linux is not fully booted - networkmanager service is not up...")
            else:
                self._log.info("Linux - NetworkManager service is up")
            cmd_to_be_executed = "service systemd-logind status | grep \"Active: active\""
            os_cmd_response = self._os.execute(cmd_to_be_executed, 1.0)
            if "Active: active" not in os_cmd_response.stdout:
                self._log.info("Linux is not fully booted - logind service is not up")
            else:
                self._log.info("Linux is fully loaded....")
                return_status = True
        except Exception as e:
            self._log.error("Exception in is_linux_fully_loaded(): %s"%e)
        return return_status

    def wait_for_sut_to_boot_fully(self):
        """
        This method is to wait for SUT to boot fully.
        """
        if self._os.os_type == OperatingSystems.LINUX:
            self.wait_for_linux_to_boot_fully()
        elif self._os.os_type == OperatingSystems.WINDOWS:
            self.wait_for_windows_to_boot_fully()
        else:
            raise content_exceptions.TestFail("wait_for_sut_to_boot_fully() is not implemented for OS type- {}".format(
                self._os.os_type))

    def wait_for_linux_to_boot_fully(self):
        time_start = 0
        while not self.is_linux_fully_booted() and time_start <= 300:
            self._log.info("Waiting for linux to fully come up..., time elapsed = %d sec"%time_start)
            time.sleep(5)
            time_start += 5
            continue

    def is_windows_fully_booted(self):
        """
        This method is to check windows booted fully.

        :return True/False
        """
        # TODO: Need to implement to check SUT fully booted
        time.sleep(15)
        self._log.info("Windows is fully loaded....")
        return_status = True
        return return_status

    def wait_for_windows_to_boot_fully(self):
        """
        This method is to wait till SUT boot to OS.
        """
        time_start = 0
        while not self.is_windows_fully_booted() and time_start <= 300:
            self._log.info("Waiting for Windows to fully come up..., time elapsed = %d sec" % time_start)
            time.sleep(5)
            time_start += 5
            continue

    def wait_for_os(self, reboot_timeout):
        start_time = time.time()
        is_booted = False
        while time.time() - start_time <= reboot_timeout:
            if self.check_os_alive():
                is_booted = True
                break
        if not is_booted:
            raise content_exceptions.TestFail("failed to boot within %d seconds" % reboot_timeout)

    def collect_axon_logs(self, post_code, cycle_num, analyzers, sdp, sv):
        try:
            sdp.itp.unlock()
            # Create folder and copy axon archive and logs
            dtaf_log_folder = Path(self.get_log_file_path(self._log)).parent
            axon_folder_name = "axon_pc_" + str(post_code) + "_cycle" + str(cycle_num)
            axon_path = os.path.join(dtaf_log_folder, axon_folder_name)
            os.mkdir(axon_path)
            axon_log_path = os.path.join(axon_path, "axon.log")
            sdp.start_log(axon_log_path)
            status_scope = sv.get_status_scope_obj()
            axon_log_path = status_scope.run(collectors=['namednodes'], analyzers=analyzers, skip_login=True)
            if os.path.isfile(axon_log_path):
                folder, file_name = os.path.split(axon_log_path)
                dest_axon_log_path = os.path.join(axon_path, file_name)
                shutil.move(axon_log_path, dest_axon_log_path)
                self._log.info("Status scope logs location: '{}'".format(dest_axon_log_path))
                return True
            else:
                self._log.error("Failed to collect axon logs..")
        except Exception as ex:
            self._log.error("Failed to collect axon logs due to exception: '{}'.".format(ex))
        sdp.stop_log()
        return False

    def check_for_dmi_error(self, sv, sdp, dmi_log_file):
        """
        This method is to check dmi error.

        :param sv
        :param sdp
        :param dmi_log_file
        :return True/False
        """
        try:
            ltssm = sv.get_ltssm_object()
            sdp.start_log(dmi_log_file, "a")
            ret_val = ltssm.checkForErrors(0, "dmi")
            self._log.info("Check for DMI errors return value='0x{:X}'.".format(ret_val))
            sdp.stop_log()
            with open(dmi_log_file, 'a') as f:
                f.write("0x{:X}".format(ret_val))
            if ret_val == 0:
                return True
            else:
                return False
        except Exception as ex:
            self._log.error("Failed to collect dmi logs due to exception: '{}'.".format(ex))
            sdp.stop_log()
            return False

    def disable_quick_edit_mode(self):
        if platform.system() != OperatingSystems.WINDOWS:
            return
        self._log.info("Windows OS: Disable command prompt quick edit mode.")
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.WinDLL('kernel32')
        dword_for_std_input_handle = ctypes.wintypes.DWORD(-10)
        dword_for_enable_extended_flags = ctypes.wintypes.DWORD(0x0080)
        std_input_handle = kernel32.GetStdHandle(dword_for_std_input_handle)
        kernel32.SetConsoleMode(std_input_handle, dword_for_enable_extended_flags)
        le = kernel32.GetLastError()
        self._log.info("Windows OS: Disable command prompt quick edit mode completed with ret code:{}.".format(le))

    def get_os_dimm_configuration(self, sockets):
        """
        This method would get the number of DIMM installed on the SUT
        Based on number of DIMM installed and socket, DPC configuration would be decided
        1 DPC - 2S : 16 DIMM, 4S : 32 DIMM, 8S : 64 DIMM
        2 DPC - 2S : 32 DIMM, 4S : 64 DIMM, 8S: 128 DIMM

        param sockets: number of sockets in SUT.
        return: DPC configuration
        raise: Test Fail
        """

        if OperatingSystems.LINUX == self._os.os_type:
            installed_dimm = self._os.execute("sudo dmidecode --type 17 | grep -i speed | wc -l", self._common_content_configuration.get_command_timeout())
            empty_dimm_slot = self._os.execute("sudo dmidecode --type 17 | grep -i speed.*Unknown | wc -l",
                                               self._common_content_configuration.get_command_timeout())
            actual_installed_dimm = int(installed_dimm.stdout) - int(empty_dimm_slot.stdout)
            self._log.info("Installed DIMM - {}".format(actual_installed_dimm / 2))
            dpc_configuration_check = ((actual_installed_dimm) / 2) / int(sockets)
            if dpc_configuration_check == 8:
                dpc_configuration = 1
            elif dpc_configuration_check == 16:
                dpc_configuration = 2
            else:
                raise content_exceptions.TestFail("SUT isn't configured with 1 DIMM or 2 DIMM configuration")
            return dpc_configuration
        else:
            raise NotImplementedError(
                "Check DIMM configuration is not implemented in {} os".format(self._os.os_type))

    def get_os_dimm_speed(self):
        """
        This method is used to get the speed of the installed DDR

        return - speed
        raise: Test Fail
        """
        if OperatingSystems.LINUX == self._os.os_type:
            cmd_output = self._os.execute("sudo dmidecode --type 17 | grep -i speed", self._common_content_configuration.get_command_timeout())
            self._log.debug("Output of dmidecide -\n{}".format(cmd_output.stdout))
            frequency = re.findall(r'.*Speed:\s+(\d+).*', cmd_output.stdout, re.IGNORECASE | re.MULTILINE)
            if frequency:
                return(list(set(frequency)))
            else:
                raise content_exceptions.TestFail("SUT DIMM speed is not fetched")
        else:
            raise NotImplementedError(
                "Check DIMM Speed is not implemented in {} os".format(self._os.os_type))

    def get_os_available_memory(self):
        """
        This method is used to get the available memory in the SUT

        return - Available memory
        raise: Test Fail
        """
        if OperatingSystems.WINDOWS == self._os.os_type:
            command_result = self._os.execute('systeminfo | findstr /C:"Available Physical Memory"', self._common_content_configuration.get_command_timeout())
            if re.search(r'Available Physical Memory:\s([0-9,]*)\sMB', command_result.stdout):
                total_available_memory = re.search(r'Available Physical Memory:\s([0-9,]*)\sMB', command_result.stdout).group(1)
                memory_size = int(total_available_memory.replace(",", ""))
                self._log.info("Total Available Memory on SUT - {}".format(memory_size))
                return memory_size
            else:
                raise content_exceptions.TestFail("SUT Available memory is not fetched correctly")
        else:
            raise NotImplementedError(
                "Check Available memory is not implemented in {} os".format(self._os.os_type))

    def update_micro_code(self):
        """
        This method is to get the micro_code and update it

        return: True on Success
        """
        try:
            lib_firmware_path = "/lib/firmware"
            intel_ucode_folder_path = "/lib/firmware/intel-ucode"
            # get the current micro_code version
            micro_code_version = self.execute_sut_cmd("cat /proc/cpuinfo | grep micro",
                                                      "getting the current micro_code version",
                                                      self._common_content_configuration.get_command_timeout())
            micro_code_version = micro_code_version.split("\n")[0].split(":")[1].strip()
            self._log.info("Current micro_code version is {}".format(micro_code_version))

            # get the micro-code folder path for update
            micro_code_folder_path_host = self._common_content_configuration.get_micro_code_file_path()
            self._log.info("Folder path of micro_code on Host{}".format(micro_code_folder_path_host))

            # getting the microcode file name
            micro_code_file_name = os.listdir(micro_code_folder_path_host)[0]
            self._log.info("micro code file name {}".format(micro_code_file_name))

            micro_code_file_path_host = os.path.join(micro_code_folder_path_host, micro_code_file_name)
            self._log.info("Complete file path of micro code on Host: {}".format(micro_code_file_path_host))

            # checking the folder exsistance
            folders = self.execute_sut_cmd("ls", "getting the folders under /lib/firmware",
                                           self._common_content_configuration.get_command_timeout(),
                                           cmd_path="/lib/firmware")
            if "intel-ucode" in folders:
                self._log.info("/lib/firmware/intel-ucode is already present")
                self.delete_micro_code()
            else:
                self.execute_sut_cmd("mkdir intel-ucode", "creating intel-ucode folder",
                                     self._common_content_configuration.get_command_timeout(),
                                     cmd_path=lib_firmware_path)
                self.execute_sut_cmd("chmod 777 intel-ucode", "giving permission to  intel-ucode folder",
                                     self._common_content_configuration.get_command_timeout(),
                                     cmd_path=lib_firmware_path)
            # get the familyID , modelid & stepping id
            family_id = self.execute_sut_cmd("cat /proc/cpuinfo | grep 'cpu family'",
                                             "getting the cpu family id",
                                             self._common_content_configuration.get_command_timeout())
            family_id = family_id.split("\n")[0].split(":")[1].strip().zfill(2)
            self._log.info("Current Family ID is {}".format(family_id))

            model_id = self.execute_sut_cmd("cat /proc/cpuinfo | grep 'model'",
                                            "getting the cpu model id",
                                            self._common_content_configuration.get_command_timeout())
            model_id = (hex(int(model_id.split("\n")[0].split(":")[1].strip()))).split("x")[1]
            self._log.info("Current model id is {}".format(model_id))

            stepping_id = self.execute_sut_cmd("cat /proc/cpuinfo | grep 'stepping'",
                                               "getting the cpu stepping id",
                                               self._common_content_configuration.get_command_timeout())
            stepping_id = stepping_id.split("\n")[0].split(":")[1].strip().zfill(2)
            self._log.info("Current model id is {}".format(stepping_id))

            # create the name of the micro_code
            new_micro_code_file_name = family_id + "-" + model_id + "-" + stepping_id
            self._log.info("New micro code file name : {}".format(new_micro_code_file_name))

            #  copy the .pdb file to SUT
            self._os.copy_local_file_to_sut(micro_code_file_path_host, "/lib/firmware/intel-ucode")

            # renaming the micro_code_file
            self.execute_sut_cmd("ln -s {} {}".format(micro_code_file_name, new_micro_code_file_name),
                                 "getting the folders under /lib/firmware",
                                 self._common_content_configuration.get_command_timeout(),
                                 cmd_path=intel_ucode_folder_path)

            # issue OS patch load
            self.execute_sut_cmd("echo 1 > /sys/devices/system/cpu/microcode/reload",
                                 "issue the OS patch load",
                                 self._common_content_configuration.get_command_timeout())

            # get the new microcode version
            # get the current micro_code version
            micro_code_version = self.execute_sut_cmd("cat /proc/cpuinfo | grep micro",
                                                      "getting the current micro_code version",
                                                      self._common_content_configuration.get_command_timeout())
            micro_code_version = micro_code_version.split("\n")[0].split(":")[1].strip()
            self._log.info("Current micro_code version is {}".format(micro_code_version))
        except Exception as ex:
            raise RuntimeError("Exception occurred while updating the micro code due to {}".format(ex))

    def delete_micro_code(self):
        """
        This method is to delete the old micro code
        :return:
        """
        try:
            intel_ucode_folder_path = "/lib/firmware/intel-ucode"
            self._log.info("Delete the current micro code")
            self.execute_sut_cmd("rm -rf *", "deleting all the micro code files",
                                 self._common_content_configuration.get_command_timeout(),
                                 cmd_path=intel_ucode_folder_path)
            self._log.info("Successfully deleted the micro code files")
        except Exception as ex:
            raise RuntimeError("Exception occurred while deleting the micro code due to {}".format(ex))

    def set_and_verify_cpu_fan_speed(self, bmc_console_obj, speed_value):
        """
        Function to set and verify the CPU Fan speed by using the BMC Console.

        """

        try:
            bmc_console_obj.login()
            bmc_console_obj.in_console()
        except Exception as ex:
            self._log.error("Please check BMC serial COM port and exception is : {}".format(ex))
            raise ex

        for each in range(0, len(CpuFanSpeedConstants.SET_FAN_SPEED_PWM_15_16)):
            return_value = False
            set_command = CpuFanSpeedConstants.SET_FAN_SPEED_PWM_15_16[each].format(speed_value)
            get_command = CpuFanSpeedConstants.GET_FAN_SPEED_PWM_15_16[each]

            bmc_console_obj.execute(set_command, timeout=60, end_pattern=r"")

            time.sleep(30)
            for i in range(1, 10):
                self._log.info("Reading info with attempt : {}".format(i))
                res = bmc_console_obj.execute(get_command, timeout=60, end_pattern=r".")
                self._log.info("Fan speed command : {} output is : \n{}".format(get_command, res))
                if speed_value in res:
                    return_value = True
                    break
            if not return_value:
                raise content_exceptions.TestFail("Not able to set fan speed after 10 attempts")

    def find_test_case_value_from_config(self, config_file_path, file_name, attrib):
            """
            Function to find the content configuration file from a specific directory
            :param: file_name
            :return: path
            """
            config_file_src_path = None
            tree = ElementTree.ElementTree()
            for root, dirs, files in os.walk(str(config_file_path)):
                for name in files:
                    if name.startswith(file_name) and name.endswith(".xml"):
                        config_file_src_path = os.path.join(root, name)

            # Check if it goes to src configuration.
            if os.path.isfile(config_file_src_path):
                tree.parse(config_file_src_path)
            else:
                self._log.error("Configuration file does not exists, please check..")

            root = tree.getroot()
            return root.find(r".//{}".format(attrib)).text.strip()

    def get_dtaf_host(self):
        """
        This method gives dtaf hostname
        :param None
        :returns:  It returns the host name of the system where DTAF is running.
        """
        try:
            dtaf_host_name = socket.gethostname()

        except:
            self._log.error("Socket Library Not Found")
            dtaf_host_name = "NA"
        return dtaf_host_name

    def get_sut_bios_version(self):
        """
        This method is to get the bios version on SUT
        """
        try:
            if OperatingSystems.LINUX in self._os.os_type:
                cmd_output_bios_version = self.execute_sut_cmd(sut_cmd="dmidecode | grep -i -m 1 Version ",
                                                               cmd_str="Running dmidecode for bios version on SUT",
                                                               execute_timeout=self._command_timeout)
                bios_version = re.search('E\S+', cmd_output_bios_version).group(0)
            elif OperatingSystems.WINDOWS in self._os.os_type:
                cmd_output_bios_version = self.execute_sut_cmd(sut_cmd="wmic bios get smbiosbiosversion",
                                                               cmd_str="Running smbiosbiosversion to get bios version on SUT",
                                                               execute_timeout=self._command_timeout)
                bios_version = re.findall('\s(.*)', cmd_output_bios_version)
                bios_version = bios_version[2]
            return bios_version
        except Exception as e:
            self._log.debug(e)
            return "Failed to get Bios Version"

    def get_sut_kernel_version(self):
        """
        This method is to get the bios version on SUT
        """
        try:
            if OperatingSystems.LINUX in self._os.os_type:
                cmd_output_kernel_version = self.execute_sut_cmd(sut_cmd="uname -r",
                                                                 cmd_str="Running dmidecode for bios version on SUT",
                                                                 execute_timeout=self._command_timeout)

            elif OperatingSystems.WINDOWS in self._os.os_type:
                cmd_output_kernel_version = self.execute_sut_cmd(sut_cmd="wmic os get version",
                                                                 cmd_str="Running smbiososversion to get os version on SUT",
                                                                 execute_timeout=self._command_timeout)
                cmd_output_kernel_version = re.findall('\s(.*)', cmd_output_kernel_version)
                cmd_output_kernel_version = cmd_output_kernel_version[2]
            return cmd_output_kernel_version
        except Exception as e:
            self._log.debug(e)
            return "Failed to get Kernel Version"

    def get_sut_info(self):
        """
        This method is used to get the host and the SUT info
        """
        self._log.info("Parser_Tag: PLATFORM = {}".format(self.get_platform_family()))
        self._log.info("Parser_Tag: SILICON = {}".format(self.get_platform_stepping()))
        self._log.info("Parser_Tag: SUT_OS = {}".format(self._os.os_type))
        self._log.info("Parser_Tag: BIOS_VERSION = {}".format(self.get_sut_bios_version()))
        self._log.info("Parser_Tag: KERNEL_VERSION = {}".format(self.get_sut_kernel_version()))

    def get_host_info(self):
        self._log.info("Parser_Tag: HOST_NAME = {}".format(self.get_dtaf_host()))
        test_datetime = datetime.datetime.now()
        self._log.info("Parser_Tag: TIME_IN_SEC = {}".format(time.monotonic()))
        test_datetime = test_datetime.strftime("%d/%m/%Y %H:%M:%S")
        self._log.info("Parser_Tag: EXECUTION_START_TIME = {}".format(test_datetime))
        self._log.info("Parser_Tag: DTAF_LOG_PATH = {}".format(self.get_log_file_dir()))

    def parse_dtaf_content_log(self):
        """
        This method is used to parse the test content log file.This method would parse all the dtaf_log lines which has
        "Parser_Tag" in the beggining and creates a dictionary with all these data.This method would also append the
        error message or the exception message in case of any failure to the dictionary.

        return: Parser_data_dict : contains the parser tag and its value
        """
        try:
            parser_data_dict = {}
            log_file = os.path.join(self.get_log_file_dir(), "dtaf_log.log")
            with open(log_file, 'r') as dtaf_log_file:
                data = dtaf_log_file.read()
            parser_data = re.findall(r'Parser_Tag:(.*)', data, re.MULTILINE | re.IGNORECASE)
            for tag in parser_data:
                elements_list = tag.split("=")
                if elements_list[0].strip() not in parser_data_dict:
                    parser_data_dict[elements_list[0].strip()] = elements_list[1].strip()
                else:
                    parser_data_dict[elements_list[0].strip()] += ", " + elements_list[1].strip()
            if parser_data_dict['RESULT'] == "FAIL" and not "ERROR_MESSAGE" in parser_data_dict:
                error_message_parser = re.findall(r'.*ERROR\s+\[.*\](.*)', data, re.MULTILINE)
                if error_message_parser:
                    parser_data_dict["ERROR_MESSAGE"] = error_message_parser[-1].strip()
                else:
                    parser_data_dict["ERROR_MESSAGE"] = ""
            self._log.info(parser_data_dict)
            return parser_data_dict
        except Exception as e:
            self._log.debug(e)
            self._log.debug("Failed to Create Dataset from Parser Tags")

    def write_parser_data_to_db(self, parser_data_dict):
        """
        This method is used to write the parser data dict to mysql database.This method would write the parser_data_dictionary
        to the mysql database.Below tags in the content_configuration.xml should be present to use this method.
        <sql_powerbi_config>
            <start_sql_connection>True</start_sql_connection>
            <subsystem_name>HSIO-B</subsystem_name>
            <mysql_host>10.215.119.14</mysql_host>
            <mysql_user>superroot</mysql_user>
            <mysql_pwd>password</mysql_pwd>
            <mysql_db_name>testdb</mysql_db_name>
            <mysql_table_name>new_table</mysql_table_name>
        </sql_powerbi_config>
        :parser_data :  dictionary that contains the host,sut and test case related data which would be inserted into db.
        """
        try:
            test_datetime = datetime.datetime.now()
            test_datetime = test_datetime.strftime("%d/%m/%Y %H:%M:%S")
            time_delta = float("{:.2f}".format(time.monotonic() - float(parser_data_dict["TIME_IN_SEC"])))
            parser_data_dict["TIME_DELTA"] = time.strftime('%H:%M:%S', time.gmtime(time_delta))

            if self._common_content_configuration.get_sql_powerbi_config_flag():
                import mysql.connector
                mydb = mysql.connector.connect(
                    host=self._common_content_configuration.get_mysql_powerbi_host(),
                    user=self._common_content_configuration.get_mysql_powerbi_user(),
                    password=self._common_content_configuration.get_mysql_powerbi_pwd(),
                    database=self._common_content_configuration.get_mysql_powerbi_db()
                )
                try:
                    self._log.info(parser_data_dict['ERROR_MESSAGE'])
                except Exception as e:
                    parser_data_dict['ERROR_MESSAGE'] = "N.A"
                mycursor = mydb.cursor()
                table_name = self._common_content_configuration.get_mysql_powerbi_tablename()
                sql_string_list = ["INSERT INTO ", table_name,
                                   " (Subsystem,TestCase,Platform,IFWI,Failure_Message,Host_Name,Execution_Start_Time,Kernel,Verdict,Silicon,OS,Test_Duration,Dtaf_Log_Path) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"]
                sql_path = "".join(sql_string_list)
                val = (self._common_content_configuration.get_subsystem_name(), parser_data_dict['CONTENT_NAME'],
                       parser_data_dict['PLATFORM'], parser_data_dict['BIOS_VERSION'],
                       parser_data_dict['ERROR_MESSAGE'], parser_data_dict['HOST_NAME'],
                       parser_data_dict['EXECUTION_START_TIME'], parser_data_dict['KERNEL_VERSION'],
                       parser_data_dict['RESULT'], parser_data_dict['SILICON'], parser_data_dict['SUT_OS'],
                       parser_data_dict['TIME_DELTA'], parser_data_dict['DTAF_LOG_PATH'])
                mycursor.execute(sql_path, val)
                mydb.commit()
                if (mycursor.rowcount == 1):
                    self._log.info("1 Record inserted.")
            else:
                self._log.info("mySQL Connection not Active")
        except Exception as e:
            self._log.debug(e)

    def find_and_read_file_in_host_usb(self, filename):
        """
        This method read the file contents from usb folder on host and return the file contents.
        """
        get_disk = "wmic logicaldisk where drivetype=2 get volumename"
        cmd_output = self.execute_cmd_on_host(get_disk)
        self._log.debug("{} Command Output : {}".format(get_disk, cmd_output))
        usb_path_name  = cmd_output.strip().split()[1].decode('utf-8')
        with open(usb_path_name + r":\\" + filename, "r") as fh:
            file_contents = fh.readlines()
            self._log.debug("File contents : {}".format(file_contents))
            return file_contents

    def search_windows_file(self, folder_name: str, file_name: str) -> Union[str, bool]:
        """
        Function searches for the file is present in a path and returns the path if available.

        :param folder_name: Name of the folder where file is to be searched
        :param file_name: file to be searched.
        :raise: content exception if the OS is not Windows
        :return: complete path of the file if present else return False.
        """
        if not self._os.os_type.lower() == OperatingSystems.WINDOWS.lower():
            raise content_exceptions.TestFail("Applicable only for Windows os")
        WIN_SEARCH_CMD = "powershell.exe (get-childitem '{}' -File {} -recurse).fullname"
        cmd = WIN_SEARCH_CMD.format(folder_name, file_name)
        self._log.debug("windows powershell file search command {}".format(cmd))
        output = self.execute_sut_cmd(cmd, cmd, self._command_timeout)
        if not output.strip():
            self._log.error("{} file is not present in the location {}".format(file_name, folder_name))
            return False
        self._log.info("{} file is present in the location {}".format(file_name, folder_name))
        return output.strip()

    def copy_windows_file_in_sut(self, source_path: str, destination_path: str) -> None:
        """
        Function copies the files from one location of the sut to another location in sut in Windows os.

        :param source_path: source location of the file to copied from.
        :param destination_path: destination location of the file to be copied.
        :raise: content exception if the copy is un-successful.
        :return: True if successfully copied.
        """
        xcopy_output_str = "0 File(s) copied"
        xcopy_cmd = self.XCOPY_COMMAND.format(source_path, destination_path)
        xcopy_output = self.execute_sut_cmd(xcopy_cmd, xcopy_cmd, self._command_timeout)
        if xcopy_output_str in xcopy_output:
            raise content_exceptions.TestFail("unable to copy the files")
        self._log.info("Successfully copied file from {} to {}".format(source_path, destination_path))

class VmUserLin:
    """
    Store the linux vm user credentials username and password
    this is quick fix to unbreak existing scripts and not expose
    the password in clear text
    """
    # force key error, ensure the upper CI layers handle
    # setting up of the environment variables.
    USER = os.environ['vm_user_l']
    PWD = os.environ['vm_user_pwd_l']

    def __init__(self):
        # support ability to read secrets from cred management
        self.user = VmUserLin.USER
        self.pwd = VmUserLin.PWD


class VmUserWin:
    """
    Store the windows vm user credentials username and password
    this is quick fix to unbreak existing scripts and not expose
    the password in clear text
    """
    # force key error, ensure the upper CI layers handle
    # setting up of the environment variables.
    USER = os.environ['vm_user_w']
    PWD = os.environ['vm_user_pwd_w']

    def __init__(self):
        # support ability to read secrets from cred management
        self.user = VmUserWin.USER
        self.pwd = VmUserWin.PWD


class Sut2UserWin:
    """
    Store the SUT2 configuration credentials username and password
    this is quick fix to unbreak existing scripts and not expose
    the password in clear text
    """
    # force key error, ensure the upper CI layers handle
    # setting up of the environment variables.
    USER = os.environ['sut2_user_w']
    PWD = os.environ['sut2_pwd_w']

    def __init__(self):
        # support ability to read secrets from cred management
        self.user = Sut2UserWin.USER
        self.pwd = Sut2UserWin.PWD
