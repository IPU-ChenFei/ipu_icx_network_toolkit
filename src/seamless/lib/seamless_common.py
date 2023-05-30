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
import ntpath
import subprocess

import io
import csv
import six
from abc import ABCMeta, abstractmethod
import re
import string
import serial
import time
import logging
import logging.handlers
import os
import glob
import threading
from requests import ConnectionError
from datetime import datetime, timedelta
from subprocess import Popen, PIPE
import urllib3
import concurrent.futures
import zipfile
from xml.etree import ElementTree as ET
from dtaf_core.lib.configuration import ConfigurationHelper
from dtaf_core.providers.flash_provider import FlashProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.internal.ssh_sut_os_provider import SshSutOsProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from dtaf_core.lib.os_lib import OsCommandResult
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib import content_exceptions
from dtaf_core.providers.bios_provider import BiosProvider
from src.lib.bios_util import BiosUtil
from dtaf_core.providers.console_log import ConsoleLogProvider
from dtaf_core.lib.base_test_case import BaseTestCase
from src.lib.content_configuration import ContentConfiguration
from src.seamless.tests.bmc.constants.ssd_constants import SsdWindows, NvmeConstants, ProxyConstants
from src.seamless.tests.bmc.constants.pmem_constants import PmemLinux, PmemWindows

from dtaf_core.providers.dc_power import DcPowerControlProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider

from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from src.lib.uefi_util import UefiUtil
from dtaf_core.providers.bios_menu import BiosSetupMenuProvider
from dtaf_core.lib.exceptions import OsCommandTimeoutException
from dtaf_core.lib.artifactory_lib import download_tool_to_host
from src.lib.content_base_test_case import ContentBaseTestCase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
path_zip_file_ipmi = r"C:\DPG_Automation\dtaf_content\src\lib\tools\ipmitool.zip"
path_unzip_file = r"C:\DPG_Automation\dtaf_content\src\lib\tools"


class ThreadWithReturn(threading.Thread):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
        super().__init__(group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)
        self._ret = None

    def run(self):
        try:
            if self._target:
                self._ret = self._target(*self._args, **self._kwargs)
        finally:
            del self._target, self._args, self._kwargs

    def join(self, timeout=None):
        super().join(timeout=timeout)
        return self._ret


@six.add_metaclass(ABCMeta)
class SeamlessBaseTest(BaseTestCase):
    AC_TIMEOUT = WAIT_TIME = 30
    _SERIAL_LOG_FILE = "serial_log.log"
    _BRING_SUT_UP = True
    BMC_USER_PROMPT = "intel-obmc login: "
    BMC_PASSWORD_PROMPT = "Password:"
    BMC_COMMAND_PROMPT = "intel-obmc:~#"
    AT_NO_PROMPT = 0
    AT_USERNAME_PROMPT = 1
    AT_PASSWORD_PROMPT = 2
    AT_COMMAND_PROMPT = 3
    BMC_STD_SERIAL_TIMEOUT = 5
    BMC_STD_PROMPT_TIMEOUT = 15
    BMC_STD_COMMAND_TIMEOUT = 15
    BMC_STD_BOOT_TIMEOUT = 300
    BIOS_BOOT_TIMEOUT = 300
    CAPSULE_TIMEOUT = 600
    SPS_UPDATE_TIMEOUT = 360
    WARM_RESET_TIMEOUT = 800
    SUT_SETTLING_TIME = 50
    DC_POWER_DELAY = 6
    POST_SLEEP_DELAY = 30
    AC_POWER_DELAY = 4
    SLEEP_TIME = 30
    LSPCICMD = "lspci"
    WINLSPCI = "powershell driverquery /v"
    REDFISH_BMC_PATH = r"suts/sut/providers/flash/driver/redfish"
    UEFI_CONFIG_PATH = r"suts/sut/providers/uefi_shell"
    PLATFORM_CPU_FAMILY = r"suts/sut/silicon/cpu"
    BMC_ROOT = r"root"

    """
    Base class extension for Seamless Update
    """

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file_path=None):
        super(SeamlessBaseTest, self).__init__(test_log, arguments, cfg_opts)

        self.bios_config_file_path = bios_config_file_path

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self.os = ProviderFactory.create(sut_os_cfg, test_log)

        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        default_system_config_file = self._common_content_lib.get_system_configuration_file()
        self._log.info("default_system_config_file {}".format(default_system_config_file))
        root = ET.parse(default_system_config_file).getroot()
        sut = ConfigurationHelper.get_sut_config(root)
        sut_bmc_ipmi = ConfigurationHelper.filter_provider_config(sut=sut, provider_name=r"dc",
                                                                  attrib=dict(id="2"))
        sut_bmc_ipmi = sut_bmc_ipmi[0]
        self.STAGING_REBOOT = None
        redfish_root = root.find(self.REDFISH_BMC_PATH)
        baud_rate = redfish_root.find(r"baudrate").text.strip()
        bmc_port = redfish_root.find(r"bmcport").text.strip()
        product_root = root.find(self.PLATFORM_CPU_FAMILY)
        self._product = product_root.find(r"family").text.strip()
        sut_bmc_redfish = cfg_opts.find(FlashProvider.DEFAULT_CONFIG_PATH)  # type: RedfishProvider
        self._bmc_redfish = ProviderFactory.create(sut_bmc_redfish, test_log)
        self._bmc_user = self._bmc_redfish._config_model.driver_cfg.username
        self._bmc_password = self._bmc_redfish._config_model.driver_cfg.password
        self._bmc_ip = self._bmc_redfish._config_model.driver_cfg.ip
        self._bmc_ipmi = ProviderFactory.create(sut_bmc_ipmi, test_log)
        self._bmc_ipmi._ip = self._bmc_ipmi._config_model.driver_cfg.ip
        sut_ssh_cfg = cfg_opts.find(SshSutOsProvider.DEFAULT_CONFIG_PATH)
        self.sut_ssh = ProviderFactory.create(sut_ssh_cfg, test_log)  # type: SutOsProvider
        self.bmc_ssh =  ProviderFactory.create(sut_bmc_redfish, test_log)
        self._serial_output = ""
        self._initial_sel_log = []
        self.bmc_critical_errors = []
        self._last_bios_version = ""
        self._os_user = self.sut_ssh._config_model.driver_cfg.user
        self._os_pass = self.sut_ssh._config_model.driver_cfg.password
        self._os_ip = self.sut_ssh._config_model.driver_cfg.ip
        self._os_type = self._common_content_lib.sut_os
        self._workload_path = os.getcwd() + "\\src\\seamless\\tests\\bmc\\collateral\\"
        self._orchestator_validator_path = os.getcwd() + "\\src\\seamless\\tools\\OrchestratorValidator\\orchestrator.py"
        self.system_path = "C:\\Windows\\System32\\"
        self._powershell_credentials = "-computer " + self._os_ip + " -user " + self._os_user + " -password " + self._os_pass
        self._powershell_credentials_bmc = "-BmcUser " + self.BMC_ROOT + " -BmcPassword " + self._bmc_password
        self.powershell = None
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1" + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1" + self._powershell_credentials
        self.workloads_started = False
        self.time_start_test = None
        self.time_staging = None
        self.time_boot_sut = None
        self.time_capsule_sent = None
        self.time_capsule_staged = None
        self.time_capsule_complete = None
        self.time_activation = None
        self.sps_ver = ""
        self.bios_ver = ""
        self.ucode_ver = ""
        self.win_ucode_ver = ""
        self.sut_mode = ""
        self.fw_type = ""
        self._bmc_version = None
        self.spi_access = None
        self.output = ""
        self.get_ucode_command = self._workload_path + "GetUcodeVersion.ps1 " + self._powershell_credentials
        self.get_bios_command = self._workload_path + "GetBiosVersion.ps1 " + self._powershell_credentials
        self.get_sps_command = self._workload_path + "GetSPSVersion.ps1 " + self._powershell_credentials
        self.get_error_command = self._workload_path + "WindowsErrorLogs.ps1 " + self._powershell_credentials
        self.get_config_command = self._workload_path + "PlatformConfig.ps1 " + self._powershell_credentials
        self.start_vm_command = self._workload_path + "StartVms.ps1 " + self._powershell_credentials
        self.stop_vm_command = self._workload_path + "StopVms.ps1 " + self._powershell_credentials
        self.shutdown_sut_command = self._workload_path + "ShutdownSut.ps1 " + self._powershell_credentials
        self.get_spi_access_command = self._workload_path + "GetSPIAccess.ps1 " + self._powershell_credentials
        self.whea_correctable_error_command = self._workload_path + "WHEA_Correctable_Error.ps1 " + self._powershell_credentials
        self.whea_uncorrectable_error_command = self._workload_path + "WHEA_Uncorrectable_Error.ps1 " + self._powershell_credentials
        self._bmc_redfish.verbose = False
        self.loop_count = ""
        self.run_orchestrator = False
        self.orchestrator_xml = None
        self.kpi_failed = False
        self.stressors = False
        self.HDE_16015195100 = True

        self.show_cred = False  # Change to True to print credentials in case of debug
        self.sensitive_credentials = [self._os_pass, self._bmc_password]

        # self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self.reboot_timeout = \
            self._common_content_configuration.get_reboot_timeout()

        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self.ac_power = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider

        if not self.os.is_alive():
            self._log.error("System is not alive, wait for the sut online")
            self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)  # To make the system alive
            self.os.wait_for_os(self.reboot_timeout)

        if not self.os.is_alive():
            self._log.error("System is not alive")
            raise content_exceptions.TestFail("System is not alive")

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self.bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider

        self.log_dir = self._common_content_lib.get_log_file_dir()

        self._command_timeout = \
            self._common_content_configuration.get_command_timeout()

        self._sut_shutdown_delay = self._common_content_configuration. \
            sut_shutdown_delay()

        self.bios_util = BiosUtil(cfg_opts, bios_config_file=self.bios_config_file_path, bios_obj=self.bios,
                                  log=self._log, common_content_lib=self._common_content_lib)

        dc_power_cfg = cfg_opts.find(DcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._dc_power = ProviderFactory.create(dc_power_cfg, test_log)  # type: DcPowerControlProvide

        cng_cfg = cfg_opts.find(ConsoleLogProvider.DEFAULT_CONFIG_PATH)
        self.cng_log = ProviderFactory.create(cng_cfg, self._log)

        self.serial_log_dir = os.path.join(self.log_dir, "serial_logs")
        self._inventory_xml_path = os.path.join(self.log_dir, "inventory\\")
        self._log.info("Inventory xml path {}".format(self._inventory_xml_path))
        if not os.path.exists(self.serial_log_dir):
            os.makedirs(self.serial_log_dir)
        self.serial_log_path = os.path.join(self.serial_log_dir,
                                            self._SERIAL_LOG_FILE)
        self.cng_log.redirect(self.serial_log_path)

        uefi_cfg = cfg_opts.find(self.UEFI_CONFIG_PATH)
        self._uefi_obj = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider
        bios_boot_menu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self._bios_boot_menu_obj = ProviderFactory.create(bios_boot_menu_cfg, test_log)  # type: BiosBootMenuProvider
        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._uefi_util_obj = UefiUtil(
            self._log,
            self._uefi_obj,
            self._bios_boot_menu_obj,
            self.ac_power,
            self._common_content_configuration, self.os, cfg_opts)

        setupmenu_cfg = cfg_opts.find(BiosSetupMenuProvider.DEFAULT_CONFIG_PATH)
        self.setupmenu = ProviderFactory.create(setupmenu_cfg, test_log)
        bootmenucfg = ConfigurationHelper.get_provider_config(sut=sut, provider_name='bios_bootmenu')
        self.bootmenu = ProviderFactory.create(bootmenucfg, test_log)
        self._os_log_obj = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration, self._common_content_lib)
        self.ezfio_tool_path = self._common_content_configuration.get_ezfio_tool_path()

    @classmethod
    def add_arguments(cls, parser):
        """
            Function to add the argument which is common to all test case
        """
        super(SeamlessBaseTest, cls).add_arguments(parser)
        # Use add_argument for cc
        parser.add_argument('-o', '--outputpath', action="store", default="",
                            help="Log folder to copy log files to command center")

    def credential_censoring(self, explicit_string):
        """
        Censors passwords, usernames, or any other desired confidential information
        Use the sensitive_credentials array to censor more information
        :param explicit_string: uncensored/original string
        :return censored_str: censored string
        """
        censored_str = explicit_string
        if not self.show_cred:
            for cred in self.sensitive_credentials:
                if (cred in censored_str):
                    censored_str = censored_str.replace(cred, "****")
        return censored_str

    def find_cap_path(self, capsule_name):
        cap = ""
        for root, dirs, files in os.walk("C:\\Artifactory"):
            if capsule_name in files:
                cap = os.path.join(root, capsule_name)
        return cap

    def find_exp_ver(self, capsule):
        self.expected_ver = []
        if self.update_type == "inband":
            ver = capsule.split('.')[0].split('-')[-1]
            for letter in ver:
                self.expected_ver.append(letter)
            self.expected_ver.insert(1, 'x')
            self.expected_ver = ''.join(self.expected_ver)
        elif self.update_type == "fit_ucode":
            ver = capsule.split('.')[0].split('-')[-1].split('_')[0]
            for letter in ver:
                self.expected_ver.append(letter)
            self.expected_ver.insert(1, 'x')
            self.expected_ver = ''.join(self.expected_ver)
            self._log.info("expected ver {}".format(self.expected_ver))
        elif self.update_type == "bios":
            self.expected_ver = capsule.split('.')[0:-1][-1].split('_')[0]
        elif self.update_type == "sps":
            ver = capsule.split('_')[0:-1][2].split('.')[0:-1]
            for letter in ver:
                self.expected_ver.append(letter.lstrip('0'))
            self.expected_ver = '.'.join(self.expected_ver)
        return self.expected_ver

    def run_ssh_command(self, command, log_output=True, timeout_seconds=600):
        """
        Execute command over ssh connection
        :param command: Command to be executed
        :param log_output: True if output added to log file
        :param timeout_seconds: timeout for connection
        :return Command output
        """
        self._log.info("Running command '" + command + "' - timeout is " + str(timeout_seconds) + " seconds")
        result = self.sut_ssh.execute(cmd=command, timeout=timeout_seconds)
        if log_output:
            self._log.info("Output of command '" + command + "':\n" + result.stdout)
        return result

    def run_bmc_ssh_command(self, command, log_output=True, timeout_seconds=600):
        """
        Execute command over ssh connection
        :param command: Command to be executed
        :param log_output: True if output added to log file
        :param timeout_seconds: timeout for connection
        :return Command output
        """
        self._log.info("Running command '" + command + "' - timeout is " + str(timeout_seconds) + " seconds")
        result = self.bmc_ssh.execute(cmd=command, timeout=timeout_seconds)
        if log_output:
            self._log.info("Output of command '" + command + "':\n" + result.stdout)
        return result

    def bios_knob_change(self, bios_config_file):
        """
        This function will set the bios knobs and
        verify the bios knobs
        """
        self._log.info("=========SETTING BIOS KNOB AS PER CONFIG FILE=========")
        self.bios_util.set_bios_knob(bios_config_file)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)  # To make the system alive
        self.os.wait_for_os(self.reboot_timeout)
        self._log.info("VERIFYING THE CHANGED BIOS KNOB")
        self.bios_util.verify_bios_knob(bios_config_file)

    def get_uefi_shell_cmd(self, cmd):
        command_result = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(cmd)
        self._log.info(command_result)
        return command_result

    def wait_for_bios_boot(self, serial_port, timeout_seconds=BIOS_BOOT_TIMEOUT):
        """
        Wait till BIOS boots
        :param serial_port: Port number for bios
        :param timeout_seconds: timeout for connecion
        """
        time_end = datetime.now() + timedelta(seconds=timeout_seconds)
        self._log.info("Waiting for BIOS boot. Timeout is " + str(timeout_seconds))
        serial_data = ""
        self._last_bios_version = ""
        while True:
            if datetime.now() > time_end:
                self._log.info("Timeout waiting for BIOS boot")
                return False

            serial_data += serial_port.read(1)

            if len(self._last_bios_version) == 0:
                # Bios ID: WLYDCRB1.SFU.0013.D27.1911260642
                m = re.search("Bios ID: [A-Z0-9]+\\.[A-Z]+\\.[0-9]+\\.[0-9A-Z]+\\.[0-9]+(.)*\\n", serial_data)
                # match_string = ""
                if m is not None:
                    try:
                        match_string = m.group(0)
                        self._last_bios_version = string.strip(string.split(match_string, ' ')[2])
                        self._log.info("Found BIOS version: " + self._last_bios_version)
                        break
                    except:
                        self._log.debug("Error matching BIOS version")

        self.locate_bmc_ip(is_post_power_cycle=True)

    def wait_for_serial_prompt(self, serial_port, timeout_seconds=BMC_STD_PROMPT_TIMEOUT, clear_first=True):
        """
        Wait till serial connection established
        :param serial_port: Serial port number
        :param timeout_seconds:Timeout
        :param clear_first: Clear old output
        :return return code
        """
        time_end = datetime.now() + timedelta(seconds=timeout_seconds)
        self._log.info("Waiting for prompt. Timeout is " + str(timeout_seconds))
        return_code = self.AT_NO_PROMPT
        if clear_first:
            self._serial_output = ""

        while True:
            if datetime.now() > time_end:
                self._log.info("Timeout waiting for prompt")
                break

            self._serial_output += serial_port.read(1)
            if self.BMC_USER_PROMPT in self._serial_output:
                self._log.info("Found user name prompt")
                return_code = self.AT_USERNAME_PROMPT
                break
            if self.BMC_PASSWORD_PROMPT in self._serial_output:
                self._log.info("Found password prompt")
                return_code = self.AT_PASSWORD_PROMPT
                break
            if self.BMC_COMMAND_PROMPT in self._serial_output:
                self._log.info("Found command prompt")
                return_code = self.AT_COMMAND_PROMPT
                break

        return return_code

    def get_sel(self, show_log=False):
        """
        Get system event log from BMC
        :param show_log: True if log to be displayed
        :return event log output
        """
        self.summary_log.info("Getting SEL entries from the BMC")
        sel_log = self._bmc_redfish.get_bmc_sel()
        entries = sel_log["Members"]
        return_list = []
        self.summary_log.info("Retrieved SEL log - Found [" + str(len(entries)) + "] entries")
        for e in entries:
            msg = "ID: " + str(e["Id"]) + " - " + str(
                e["Message"] + " Created: " + str(e["Created"]) + " Severity: " + str(e["Severity"]))
            self.summary_log.info("Got new BMC SEL entry: " + str(msg))
            if "Severity: Warning" in msg:
                self.summary_log.info("BMC sel log indicates warning, event log entry: " + str(msg))
            if "Severity: Critical" in msg and not (
                    'Seamless' in msg and 'update' in msg and ('started' in msg or 'completed' in msg)):
                # raise RuntimeError("BMC sel log containes Warning/Error, event log entry: " + str(msg))
                self.summary_log.info("BMC sel log indicates critical error, event log entry: " + str(msg))
                self.bmc_critical_errors.append(msg)

            return_list.append(msg)
            if show_log:
                self._log.debug(msg)

        return return_list

    def get_jnl(self, show_log=False):
        """
        Get Journal log from BMC
        :param show_log: True if log to be displayed
        :return event log output
        """
        sel_log = self._bmc_redfish.get_bmc_jnl()
        entries = sel_log["Members"]
        return_list = []
        self.summary_log.info("Retrieved Journal  log - Found [" + str(len(entries)) + "] entries")
        for e in entries:
            msg = str(("ID: " + str(e["Id"].encode('utf-8')) + " - " + e["Message"] + " Created: " + e["Created"] + " Severity: " + e["Severity"]).encode('utf-8'))
            self.summary_log.info("Got new BMC Journal entry: " + (msg))
            if "Severity: Warning" in msg:
                self.summary_log.info("BMC sel log indicates warning, journal log entry: " + (msg))
            elif "Severity: Critical" in msg and not (
                    'Seamless' in msg and 'update' in msg and ('started' in msg or 'completed' in msg)):
                # raise RuntimeError("BMC sel log containes Warning/Error, journal log entry: " + str(msg))
                self._log.info("BMC sel log indicates critical error, journal log entry: " + (msg))
                self.bmc_critical_errors.append(msg)

            if ("Seamless" in (e["Message"])):
                time = e["Created"]
                self._log.info(e["Message"])
            # Look for event markers for performance benchmarking
            if "BMC_BEGIN_CAPSULE_STAGING" in (e["Message"]):

                self._log.info("=========SENT===========")
                if hasattr(self,'crossproduct_whea_correctable_sps') and self.crossproduct_whea_correctable_sps:
                    import time as t
                    self._log.info("wheahct /err 8 /param1 2 /param2 0x1000000 /param3 0x40 /param4 0")
                    self.run_ssh_command(r"cd C:\Users\Administrator\WHEAHCT_Tool && Clear_whea_evts.cmd ")
                    t.sleep(1)
                    self.run_ssh_command(r"cd C:\Users\Administrator\WHEAHCT_Tool && installPlugin.bat")
                    t.sleep(1)
                    self.run_ssh_command(r"C:\Users\Administrator\WHEAHCT_Tool\wheahct /err 8 /param1 2 /param2 0x1000000 /param3 0x40 /param4 0")
                elif hasattr(self,"crossproduct_whea_uncorrectable_sps") and self.crossproduct_whea_uncorrectable_sps:
                    self._log.info("Executing WHEA command: wheahct /err 32 /param1 2 /param2 0x1000000 /param3 0x40 /param4 0")
                    #output = self.run_powershell_command(self.whea_uncorrectable_error_command, get_output=True)
                    try:
                        output = self.run_ssh_command(r"C:\Users\Administrator\WHEAHCT_Tool\wheahct /err 32 /param1 2 /param2 0x1000000 /param3 0x40 /param4 0", timeout_seconds=1)
                    except OsCommandTimeoutException :
                        pass
                elif hasattr(self,"crossproduct_whea_uncorrectable_nf_sps") and self.crossproduct_whea_uncorrectable_nf_sps:
                    self._log.info("Executing WHEA command: wheahct /err 16 /param1 2 /param2 0x1000000 /param3 0x40 /param4 0")
                    try:
                        output = self.run_ssh_command(r"C:\Users\Administrator\WHEAHCT_Tool\wheahct /err 16 /param1 2 /param2 0x1000000 /param3 0x40 /param4 0", timeout_seconds=1)
                    except OsCommandTimeoutException :
                        pass
                elif hasattr(self, "crossproduct_cstate_sps") and self.crossproduct_cstate_sps:
                    import time as time_
                    self._log.info("Executing PTU utility commands.")
                    self._log.info("Checking for C6.")
                    self.run_ssh_command(r'cd "C:\Program Files\Intel\Power Thermal Utility - Server Edition" && ptu.exe -log -filter 9 -t 2 -csv')
                    output = self.run_ssh_command("powershell -Command \"Get-Content (Get-ChildItem -Path C:\PTU\*_ptumon.csv | Sort-Object LastWriteTime | Select-Object -Last 1).FullName\"")
                    if output:
                        csv_response = csv.DictReader(io.StringIO(output.stdout))
                        c6 = all(float(row['C6']) > 90 for row in csv_response)
                        self._log.info("C6 > 90: {}".format(c6))
                    else:
                        return False
                    if c6:
                        self._log.info("Running stress for 1 minute.")
                        self.run_ssh_command(r'cd "C:\Program Files\Intel\Power Thermal Utility - Server Edition" && ptu.exe -ct 1 -b 0 -t 60 -log -filter 9 -csv')
                        self._log.info("Checking for C0.")
                        output = self.run_ssh_command("powershell -Command \"Get-Content (Get-ChildItem -Path C:\PTU\*_ptumon.csv | Sort-Object LastWriteTime | Select-Object -Last 1).FullName\"")
                        if output:
                            csv_response = csv.DictReader(io.StringIO(output.stdout))
                            c0 = all(float(row['C0']) > 90 for row in csv_response)
                            self._log.info("C0 > 90: {}".format(c0))
                        else:
                            return False
                        if c0:
                            self._log.info("Checking for C6.")
                            time_.sleep(10)
                            self.run_ssh_command(r'cd "C:\Program Files\Intel\Power Thermal Utility - Server Edition" && ptu.exe -log -filter 9 -t 2 -csv')                           
                            output = self.run_ssh_command("powershell -Command \"Get-Content (Get-ChildItem -Path C:\PTU\*_ptumon.csv | Sort-Object LastWriteTime | Select-Object -Last 1).FullName\"")
                            if output:
                                csv_response = csv.DictReader(io.StringIO(output.stdout))
                                c6 = all(float(row['C6']) > 90 for row in csv_response)
                                self._log.info("C6 > 90: {}".format(c6))
                            else:
                                return False
                            if not c6:
                                raise RuntimeError("C6 state not reached")
                            self._log.info("Executed PTU utility commands successfully.")
                        else:
                            raise RuntimeError("C0 state not reached.")
                    else:
                        raise RuntimeError("Initial state is not C6.")
                timestr = e["Created"]
                self.time_capsule_sent = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")
            elif "BMC_CAPSULE_STAGED" in str(e["Message"]):
                self._log.info("=========STAGED===========")
                timestr = e["Created"]
                self.time_capsule_staged = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")
            elif "CPLD_SPI_OWNED" in str(e["Message"]):
                """
                TC :- 66094.2
                cmd :- SEAM_BMC_0004_send_bios_update_capsule.py 
                --capsule_path "capsule path of BIOS "
                --expected_ver " version of BIOS capsule eg:- P03" 
                --spi_access

                TC :- 64973
                cmd :- SEAM_BMC_0003_send_sps_update_capsule.py 
                --capsule_path "capsule path of BIOS "
                --expected_ver " version of BIOS capsule eg:- P03" 
                --spi_access
                Prerequisites: 'SPI_ACCESS' file should be copied in C folder inside SUT(Windows): 'C:\SPI_ACCESS\set_timeout.bat'.
                """
                if self.spi_access:
                    self._log.info("=========STARTING THE BATCH FILE, TRYING TO ACCESS SPI===========\n")
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self.run_powershell_command, self.get_spi_access_command, get_output=True)
                        self.output = future.result()
                    self._log.info("=====OUTPUT OF THE BATCH FILE======= {}".format(self.output))
                    ver = re.search(r"Access is denied", self.output)
                    if ver is not None:
                        self._log.info("Access is denied, messages are expected during staging\n")
                    else:
                        raise RuntimeError("Not getting expected Access denied message")
                if self.STAGING_REBOOT:
                    self._log.info("\tWarm reset the system")
                    self.time_activation = datetime.now()
                    if self._os_type != OperatingSystems.LINUX and not self.sut_ssh.is_alive():
                        self.run_powershell_command(command=self.restart_sut_command, get_output=True)
                    else:
                        self._log.info("\tWarm reset through SSH")
                        self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)
                    self.time_activation = datetime.now() - self.time_activation
                    self.time_activation = self.time_activation - timedelta(seconds=30)
                    # TODO: Verify that this is still a required workaround for Windows. Adds an extreme delay per run.
                    if self._os_type != OperatingSystems.LINUX and not self.sut_ssh.is_alive():
                        self._log.info("\t\tSIMULATION - Wait for system restart")
                        self.time_activation = datetime.now()
                        time.sleep(self.WARM_RESET_TIMEOUT)
                        self.time_activation = datetime.now() - self.time_activation
                    self.summary_log.info("System warm reset complete in " + str(self.WARM_RESET_TIMEOUT) + " seconds")
                    self._log.info("\tSystem warm reset complete in " + str(self.WARM_RESET_TIMEOUT) + " seconds")
                    if ((self.time_activation) > timedelta(minutes=11)):
                        #raise RuntimeError("Failed Activation period in less then 10 minutes")
                        self.kpi_failed = True
                        self._log.info("KPI failed SPS activation in less than 10 minutes")
                if hasattr(self, "error_inj_flag") and self.error_inj_flag:
                    if self._os_type == OperatingSystems.WINDOWS:
                        if not self.injection_error():
                            raise RuntimeError("Error injection failed")
                    else:
                        if not self.einj_prepare_injection():
                            raise RuntimeError(
                                "einj module cannot be loaded - Check BIOS knob setting - Exiting the test!!!")
                        self.error_inject_commands_linux()
                    self.error_inj_flag = False
            elif "SPS_RESET_INITIATED" in str(e["Message"]):
                timestr = e["Created"]
                self.time_sps_reset = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")
            elif "SPS_RESET_OK" in str(e["Message"]):
                timestr = e["Created"]
                self.time_sps_ok = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")
            elif "SEAMLESS_UPDATE_COMPLETE" in str(e["Message"]):
                self._log.info("=========COMPLETE===========")
                timestr = e["Created"]
                self.time_capsule_complete = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")
            return_list.append(msg)
            if show_log:
                self._log.debug(msg)
            return_list.append(msg)
            if show_log:
                self._log.debug(msg)
        return return_list

    def get_jnl_ac(self, show_log=False):
        """
        Get Journal log from BMC
        :param show_log: True if log to be displayed
        :return event log output
        """
        sel_log = self._bmc_redfish.get_bmc_jnl()
        entries = sel_log["Members"]
        return_list = []
        self.summary_log.info("Retrieved Journal  log - Found [" + str(len(entries)) + "] entries")
        for e in entries:
            msg = "ID: " + str(e["Id"]) + " - " + str(
                e["Message"] + " Created: " + str(e["Created"]) + " Severity: " + str(e["Severity"]))
            self.summary_log.info("Got new BMC Journal entry: " + str(msg))
            if "Severity: Warning" in msg:
                self.summary_log.info("BMC sel log indicates warning, journal log entry: " + str(msg))
            if "Severity: Critical" in msg and not (
                    'Seamless' in msg and 'update' in msg and ('started' in msg or 'completed' in msg)):
                # raise RuntimeError("BMC sel log containes Warning/Error, journal log entry: " + str(msg))
                self._log.info("BMC sel log indicates critical error, journal log entry: " + str(msg))
                self.bmc_critical_errors.append(msg)
            if ("Seamless" in str(e["Message"])):
                time = e["Created"]
                self._log.info(str(e["Message"]))
            # Look for event markers for performance benchmarking
            if "BMC_BEGIN_CAPSULE_STAGING" in str(e["Message"]):
                self._log.info("=========SENT===========")
            elif "CPLD_SPI_OWNED" in str(e["Message"]):
                if self.ac_while_staging:
                    self._log.info("Performing Ac Power cycle")
                    self._log.info("Removed Ac Power from the system..")
                    self.ac_power.ac_power_off(self.AC_POWER_DELAY)
                    self._log.info("Connected back Ac Power to the system, booting initiated..\n")
                    self.ac_power.ac_power_on(self.AC_POWER_DELAY)
                    self._log.info("Waiting for system to boot into OS..")
                    self.os.wait_for_os(self.reboot_timeout)
                    self.ac_while_staging = False
                    self.get_jnl(show_log=True)
                    self.booted_after_ac = True

            elif "SPS_RESET_INITIATED" in str(e["Message"]):
                timestr = e["Created"]
                self.time_sps_reset = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")
            elif "SPS_RESET_OK" in str(e["Message"]):
                timestr = e["Created"]
                self.time_sps_ok = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")

            elif "SEAMLESS_UPDATE_COMPLETE" in str(e["Message"]):
                self._log.info("=========COMPLETE===========")
                timestr = e["Created"]
                self.time_capsule_complete = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")

            return_list.append(msg)
            if show_log:
                self._log.debug(msg)
            return_list.append(msg)
            if show_log:
                self._log.debug(msg)
        return return_list

    def get_jnl_check_sps_mode(self, show_log=False):
        """
        Get Journal log from BMC
        :param show_log: True if log to be displayed
        :return event log output
        """
        sel_log = self._bmc_redfish.get_bmc_jnl()
        entries = sel_log["Members"]
        return_list = []
        self.summary_log.info("Retrieved Journal  log - Found [" + str(len(entries)) + "] entries")
        for e in entries:
            msg = "ID: " + str(e["Id"]) + " - " + str(
                e["Message"] + " Created: " + str(e["Created"]) + " Severity: " + str(e["Severity"]))
            self.summary_log.info("Got new BMC Journal entry: " + str(msg))
            if "Severity: Warning" in msg:
                self._log.info("BMC sel log indicates warning, journal log entry: " + str(msg))
            elif "Severity: Critical" in msg and not (
                    'Seamless' in msg and 'update' in msg and ('started' in msg or 'completed' in msg)):
                # raise RuntimeError("BMC sel log containes Warning/Error, journal log entry: " + str(msg))
                self._log.info("BMC sel log indicates critical error, journal log entry: " + str(msg))
                self.bmc_critical_errors.append(msg)

            if ("Seamless" in str(e["Message"])):
                time = e["Created"]
                self._log.info(str(e["Message"]))
            # Look for event markers for performance benchmarking
            if "BMC_BEGIN_CAPSULE_STAGING" in str(e["Message"]):
                self._log.info("=========SENT===========")
                timestr = e["Created"]
                self.time_capsule_sent = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")
            elif "BMC_CAPSULE_STAGED" in str(e["Message"]):
                self._log.info("=========STAGED===========")
                timestr = e["Created"]
                self.time_capsule_staged = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")

            elif "SPS_RESET_INITIATED" in str(e["Message"]):
                timestr = e["Created"]
                self.time_sps_reset = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")
            elif "SPS_RESET_OK" in str(e["Message"]):
                timestr = e["Created"]
                self.time_sps_ok = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")

            elif "SEAMLESS_UPDATE_COMPLETE" in str(e["Message"]):
                self._log.info("=========COMPLETE===========")
                timestr = e["Created"]
                self.time_capsule_complete = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")

            return_list.append(msg)
            if show_log:
                self._log.debug(msg)

            if "SPS_RECOVERY_MODE_ENTERED" in str(e["Message"]):
                if self.sps_mode:
                    self._log.info("============cheking sps current mode during Staging=======================")
                    if self._os_type == OperatingSystems.WINDOWS:
                        sps_info = self.run_powershell_command(self.get_sps_command, get_output=True)
                    else:
                        cmd = './spsInfoLinux64'
                        result = self.run_ssh_command(cmd)
                        sps_info = result.stdout
                    sps_state_info = re.search(r"Current ?State\s\(\d+:\d+\)\:\s+(.*)\s\(\d+\)", sps_info)
                    current_state = sps_state_info.group(1)
                    self._log.info("Current state : {}".format(current_state))
                    if current_state.strip() != "Recovery":
                        self._log.error("Current state : {}, not Recovery....".format(current_state))
                        exit()
            return_list.append(msg)
            if show_log:
                self._log.debug(msg)
        return return_list

    def get_jnl_parallel(self, show_log=False):
        """
        Get Journal log from BMC
        :param show_log: True if log to be displayed
        :return event log output
        """
        sel_log = self._bmc_redfish.get_bmc_jnl()
        entries = sel_log["Members"]
        return_list = []
        for e in entries:
            msg = "ID: {} - {}".format(e["Id"], e["Message"])
            if ("Seamless" in str(e["Message"])):
                time = e["Created"]
                self._log.info(str(e["Message"]))
            if "BMC_BEGIN_CAPSULE_STAGING" in str(e["Message"]):
                self._log.info("=========SENT===========\n")
                timestr = e["Created"]
                self.time_capsule_sent = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")
                if self.capsule_path3 or self.capsule_path2:
                    if self.capsule_path3:
                        self._log.info("=========INITIATING (N-1) FV1 EFI CAPSULE UPDATE===========\n")
                        self.send_capsule_parallel(self.capsule_path3, self.CAPSULE_TIMEOUT)
                    else:
                        self._log.info("=========INITIATING CAPSULE2 SENDING===========\n")
                        self.send_capsule_parallel(self.capsule_path2, self.CAPSULE_TIMEOUT)
            elif "BMC_CAPSULE_STAGED" in str(e["Message"]):
                self._log.info("=========STAGED===========")
                timestr = e["Created"]
                self.time_capsule_staged = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")
                self._log.info("Capsule Staging Time: {}".format(self.time_capsule_staged - self.time_capsule_sent))
                if ((self.time_capsule_staged - self.time_capsule_sent) > timedelta(minutes=5)):
                    raise RuntimeError("Failed to stage in less then 5 minutes")
            elif "SPS_RESET_INITIATED" in str(e["Message"]):
                timestr = e["Created"]
                self.time_sps_reset = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")
            elif "SPS_RESET_OK" in str(e["Message"]):
                timestr = e["Created"]
                self.time_sps_ok = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")

            elif "SEAMLESS_UPDATE_COMPLETE" in str(e["Message"]):
                self._log.info("=========COMPLETE===========")
                timestr = e["Created"]
                self.time_capsule_complete = datetime.strptime(timestr[:-6], "%Y-%m-%dT%H:%M:%S")

            return_list.append(msg)
            if show_log:
                self._log.debug(msg)

        return return_list

    def sel_log(self, sel, done_staging=False):
        self.summary_log.info("Got new SEL entry: {}".format(sel))

        if "firmware update" in sel and "started" in sel:
            self.summary_log.info("SEL entry indicates capsule staging has started")
            self._log.info(
                "\tSEL entry indicates capsule staging has started. Waiting till staging completes...")
        elif "Seamless" in sel and "update" in sel and "completed successfully" in sel:
            self._log.info("\tSEL entry indicates capsule is done staging")
            self.summary_log.info("SEL entry indicates capsule is done staging")
            done_staging = True
        elif "fixme failed" in sel:
            self.summary_log.error("SEL entry indicates capsule staging failed")
            self._log.error("\tSEL entry indicates capsule staging failed")
            raise RuntimeError("BMC update did not complete: version transition failed")
        return done_staging

    def run_serial_command(self, serial_port, command, timeout_seconds=BMC_STD_COMMAND_TIMEOUT):
        """
        Execute command over serial connection
        :param serial_port: Port number
        :param command: Command to be executed
        :param timeout_seconds:Timeout for serail connection
        :return command output
        """
        self._log.info("Running command '" + command + "'")
        serial_port.write(command + "\n")
        prompt = self.wait_for_serial_prompt(serial_port, timeout_seconds)
        if not prompt == self.AT_COMMAND_PROMPT:
            self._log.info("Failed to find command prompt after command.")

        command_output = self._serial_output
        self._log.info(command_output)
        return command_output

    def locate_bmc_ip(self, is_post_power_cycle=False):
        """
        Fetch BMC IP over serial connection
        :param is_post_power_cycle: True if power cycle performed
        :return True if get BMC IP successful
        """
        serial_port = serial.Serial(self._bmc_com_port, baudrate=self._bmc_baud_rate,
                                    timeout=self.BMC_STD_SERIAL_TIMEOUT)
        self._log.info("Locating IP for BMC.")
        prompt_timeout = self.BMC_STD_COMMAND_TIMEOUT
        if is_post_power_cycle:
            prompt_timeout = self.BMC_STD_BOOT_TIMEOUT
        else:
            serial_port.write("\n")

        self._log.info("Locating BMC serial data state")
        prompt = self.wait_for_serial_prompt(serial_port, prompt_timeout)
        if prompt == self.AT_NO_PROMPT:
            serial_port.close()
            return False

        prompt_timeout = self.BMC_STD_COMMAND_TIMEOUT
        while not prompt == self.AT_COMMAND_PROMPT:
            if prompt == self.AT_USERNAME_PROMPT:
                self._log.info("Sending BMC user")
                serial_port.write(self._bmc_user + "\n")
                prompt = self.wait_for_serial_prompt(serial_port, prompt_timeout)
            elif prompt == self.AT_PASSWORD_PROMPT:
                self._log.info("Sending BMC password")
                serial_port.write(self._bmc_password + "\n")
                prompt = self.wait_for_serial_prompt(serial_port, prompt_timeout)
            elif prompt == self.AT_NO_PROMPT:
                self._log.info("Failed to find prompt. Exiting.")
                serial_port.close()
                return False

        self._log.info("Getting IP from BMC")
        command_output = self.run_serial_command(serial_port, "ip addr | grep 'inet .*global'")

        self._log.info("Closing serial port")
        serial_port.close()

        if len(command_output) == 0:
            self._log.info("Got no command output")
        else:
            self._log.info("Examining serial output")
            m = re.search("inet [0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+", command_output)
            match_string = ""
            if m is not None:
                try:
                    match_string = m.group(0)
                except RuntimeError as e:
                    self._log.info("Failed to match IP address")

            if len(match_string) > 0:
                line = string.split(match_string, ' ')[1]
                self._log.info("Found new BMC IP " + line)
                self._bmc_redfish.set_new_path(line)
                return True

        return False

    def verify_bmc_ip(self):
        """
        Verify BMC IP before and after update
        :return: True is BMC IP unchanged
        """
        self.summary_log.info("Get BMC IP Address from lan channel 3")
        bmc_ip = self._bmc_ipmi.get_bmc_lan()
        self.summary_log.info("BMC IP before update: {}".format(self._bmc_ipmi._ip))
        self.summary_log.info("BMC IP after update: {}".format(bmc_ip))
        if bmc_ip != self._bmc_ipmi._ip:
            self.summary_log.error("BMC IP changed after update")
            result = False
        else:
            result = True

        return result

    def cold_reset_bmc(self):
        """
        Power cycle SUT to perform cold reset of BMC
        :return True if cold reset successful
        """
        self._log.info("Performing a power cycle of the SUT")
        self._wps.power_cycle()
        if not self.locate_bmc_ip(is_post_power_cycle=True):
            self._log.error("BMC IP could not be determined after power cycle")
            return False
        return True

    def warm_reset_bmc(self):
        """
        Perform warm reset of BMC
        :return True if reset successful
        """
        self._log.info("Performing a warm reset of the BMC")
        self._bmc_redfish.reset_bmc()
        SLEEP_TIME = 60
        self._log.info("Sleeping for " + str(SLEEP_TIME) + "secs")
        time.sleep(SLEEP_TIME)
        if not self.locate_bmc_ip(is_post_power_cycle=True):
            self._log.error("BMC IP could not be determined after BMC reset")
            return False
        return True

    def refresh_bmc_version(self, allow_bmc_recovery=True, echo_version=True, raise_error=False):
        """
        Get bmc_version from redfish
        Reset BMC if version not available - temporary fix
        :param allow_bmc_recovery: True if BMC should be reset
        :param echo_version: True if display output
        :param raise_error: True if error to be raised when BMC version not available on reset
        """
        self._bmc_version = ""

        try:
            self._bmc_version = self._bmc_redfish.get_bmc_version()
        except (RuntimeError, ConnectionError) as e:
            self._log.debug(e)

        wasReset = False
        if allow_bmc_recovery:
            # todo - remove when https://hsdes.intel.com/appstore/article/#/2209857016 is resolved
            if self._bmc_redfish.last_resp_status_code == self._bmc_redfish.BMC_HTTP_SCREWED_UP:
                wasReset = True
                if not self.warm_reset_bmc():
                    raise RuntimeError("Failed to warm reset the BMC")
            elif self._bmc_redfish.last_resp_status_code == self._bmc_redfish.NO_HTTP_RESPONSE:
                wasReset = True
                if not self.cold_reset_bmc():
                    raise RuntimeError("Failed to cold reset the SUT")

            if wasReset:
                try:
                    self._bmc_version = self._bmc_redfish.get_bmc_version()
                except (RuntimeError, ConnectionError) as e:
                    self._log.debug(e)

        if echo_version:
            self._log.info("BMC version = '" + str(self._bmc_version) + "'")

        if len(self._bmc_version) == 0 and raise_error:
            raise RuntimeError("Failed to determine the BMC version")

    @abstractmethod
    def check_capsule_pre_conditions(self):
        raise NotImplementedError

    @abstractmethod
    def get_current_version(self, echo_version=True):
        raise NotImplementedError

    @abstractmethod
    def evaluate_workload_output(self, output):
        raise NotImplementedError

    # Check pre update versions
    def get_pre_versions(self, str1=''):
        """
        Read pre-update ME, bios and ucode versions
        """
        self.sps_ver = self.get_sps_ver(False)
        self.ucode_ver = self.get_ucode_ver(False)
        self.bios_ver = self.get_bios_ver(False)
        if self._os_type != OperatingSystems.LINUX:
            self.win_ucode_ver = self.get_win_ucode_ver(False)
        self._log.info(str1 + "\t\tSPS version: " + str(self.sps_ver))
        self._log.info(str1 + "\t\tBIOS version: " + str(self.bios_ver))
        self._log.info(str1 + "\t\tuCode version: " + str(self.ucode_ver))

    def get_platform_config(self):
        """
        Get platform configuration
        :return platform configuration
        """
        if self._os_type == OperatingSystems.LINUX:
            self._log.info("\tVerifying Platform configuration from Linux agent")
            self.linux_plat_config()
        else:
            self._log.info("\tVerifying Platform configuration from windows agent")
            plat_config = self.run_powershell_command(self.get_config_command, get_output=True)
            self.summary_log.info("\t\tPlatform configuration from windows agent: ")
            plat_config = plat_config.split('\n')
            for line in plat_config[6:-5]:
                self.summary_log.info("\t\t" + line)

    def get_platform_name_from_bmc(self):
        """
        Gets the Platform Name from the BMC version string.
        :return: Platform Name String
        """
        try:
            bmc_ver = self._bmc_redfish.get_bmc_version()
        except RuntimeError:
            bmc_ver = self._bmc_ipmi.get_bmc_version()

        plat_substring = bmc_ver[0:3].lower()

        if plat_substring == "wht":
            return "WHITLEY"
        elif plat_substring == "egs":
            return "EAGLESTREAM"
        else:
            return "UNKNOWN"

    def examine_post_update_conditions(self, update_type=None):
        """
        Check post update conditions
        :param update_type: Firmware to be updated
        :return True if all features checked
        """
        result = True

        # Post-Update ESRT Check
        if update_type == "inband":
            result = self.esrt_check()

        # Check BMC IP post update
        self._log.info("\t\tBMC IP unchanged after update: " + str(self.verify_bmc_ip()))

        # Get BMC device id
        # self.summary_log.info("BMC devide ID: " + str(self._bmc_ipmi.get_device_id()))

        # # # get fw inventory
        fw_inv = self._bmc_redfish.get_firmwareinventory()
        self.summary_log.info('Firmware inventory from BMC: ')
        self._log.info('\t\tChecking Firmware inventory from BMC')
        for each in fw_inv:
            self.summary_log.info(
                '\t\t\tID: ' + each['Id'] + '; Description: ' + each['Description'] + '; Version: ' + each['Version'])

        # check sensor data
        sensor_data = self._bmc_ipmi.get_sensor_data()
        self.summary_log.info("\t\tsensor data {}".format(sensor_data))
        self.summary_log.info('Sensor data from BMC:')
        self._log.info("\t\tReading sensor data from BMC")
        for each in sensor_data:
            sensor = each.split(b'|')
            if each:
                self.summary_log.info(
                    "Sensor name = " + str(sensor[0]) + "Sensor reading = " + str(sensor[1]) + "Sensor status = " + str(
                        sensor[3]))
                if str(sensor[3]) == 'cr':
                    self.summary_log.error("Sensor " + str(sensor[0]) + "is critical")

        # Get redfish event log
        self._log.info("\t\tChecking post update BMC sel entries")
        event_log = self.get_sel()

        for sel in event_log:
            # self._log.info("Got new sel entry")
            self.summary_log.info("Got new SEL entry: " + str(sel))
        self._log.info("\t\tChecking post update BMC journal entries")
        self.get_jnl()

        if not (self.sut_mode == "uefi" or self.sut_mode == "S5"):
            # verify fw versions
            self._log.info("\t\tChecking post update firmware versions")
            self.get_pre_versions(str1='\t')
            flag = 0
            if update_type != 'SPS' and self.sps_ver != self.get_sps_ver():
                self.summary_log.error("SPS version changed after update")
                flag = 1
            if update_type != 'oob_ucode' and self.ucode_ver != self.get_ucode_ver():
                self.summary_log.error("OOB ucode version changed after update")
                flag = 1
            if self._os_type != OperatingSystems.LINUX:
                if update_type != 'win_ucode' and self.win_ucode_ver != self.get_win_ucode_ver():
                    self.summary_log.error("Windows ucode version changed after update")
                    flag = 1
            if update_type != 'bios' and self.bios_ver != self.get_bios_ver(False):
                self.summary_log.error("Bios version changed after update")
                flag = 1

            if flag == 0:
                self._log.info('\t\tPost update firmware versions are as expected')

            # OS error logs
            self._log.info("\t\tChecking for OS errors")
            if self._os_type == OperatingSystems.LINUX:
                command = "dmesg | egrep -i 'error|fail'"
                result_ssh = self.sut_ssh.execute(cmd=command, timeout=10)
                self.summary_log.error("System and Application Error logs: ")
                self.summary_log.error('\n' + result_ssh.stdout)
            else:
                date = (datetime.now() - timedelta(days=0)).strftime("\"%m/%d/%Y %H:%M:%S\"")
                error_logs = self.run_powershell_command(self.get_error_command + " -time " + date, get_output=True)
                self.summary_log.error("System and Application Error logs: ")
                self.summary_log.error(error_logs)

        if self.bmc_critical_errors:
            for each in self.bmc_critical_errors:
                self._log.info("BMC CRITICAL ERROR: " + str(each))
            # result = False

        return result

    def linux_plat_config(self):
        """
        Get platform configuration for Linux
        :return platform configuration
        """
        self.summary_log.info("Platform configuration from Linux agent: ")
        command = "dmidecode -t 4 | egrep -i 'core enabled|thread count'"
        result = self.sut_ssh.execute(cmd=command, timeout=10)
        self.summary_log.info("\n ****PROCESSOR INFORMATION**** \n")
        self.summary_log.info('\n' + result.stdout)
        command = "lscpu | egrep -i 'numa node'"
        result = self.sut_ssh.execute(cmd=command, timeout=10)
        self.summary_log.info('\n' + result.stdout)
        command = "numactl --hardware"
        result = self.sut_ssh.execute(cmd=command, timeout=10)
        self.summary_log.info('\n' + result.stdout)

        command = "cat /proc/cpuinfo | grep -im 1 micro"
        result = self.sut_ssh.execute(cmd=command, timeout=10)
        self.summary_log.info("\n ****Microcode INFORMATION**** \n" + result.stdout)

        command = "cat /proc/meminfo | grep -im 1 memtotal"
        result = self.sut_ssh.execute(cmd=command, timeout=10)
        self.summary_log.info("\n ****MEMORY INFORMATION**** \n" + result.stdout)

        command = "hostnamectl  | egrep -i 'operating | kernel'"
        result = self.sut_ssh.execute(cmd=command, timeout=10)
        self.summary_log.info("\n ****OS INFORMATION**** \n" + result.stdout)

        command = "dmidecode -t 0 | egrep -i 'vendor|release|version|smbios|efi'"
        result = self.sut_ssh.execute(cmd=command, timeout=10)
        self.summary_log.info("\n ****BIOS INFORMATION**** \n" + result.stdout)

    def get_sps_ver(self, echo_version=True, compile_output=True):
        """
        Read sps version
        :param echo_version: True if display output
        :param compile_output: Flattens return to String if True, Dict if False.
        :return: ME version
        """

        if self._os_type != OperatingSystems.LINUX:
            output = self.run_powershell_command(self.get_sps_command, get_output=True)
        else:
            cmd = './spsInfoLinux64'
            result = self.run_ssh_command(cmd, log_output=False)
            output = result.stdout

        version = "NONE"
        # me_svn = "NONE"
        me_svn = "0"
        me_heci = "NONE"
        me_mode = "NONE"
        for line in output.split('\n'):
            if "SPS Image FW version" in line:
                version = line.split(':')[1]

            elif "Anti Rollback SVN" in line:
                if "ERROR" not in line:
                    me_svn = line.split(':')[1]

            elif "HECI Interface Version" in line:
                me_heci = line.split(':')[1]

            elif "Current State" in line or "CurrentState" in line:
                me_mode = line.split('):')[1].strip().split(' ')[0]

        try:
            me_svn = int(me_svn.strip())
        except ValueError:
            me_svn = None

        me_heci = me_heci.strip()

        try:
            rec_ver = version.split('(Recovery)')[0].strip()
            opr_ver = version.split('(Recovery)')[1].split('(Operational)')[0].replace(',', '').strip()

        except IndexError:
            self._log.info("SPS version not properly retrieved from system")
            self._log.info("Recieved output results:" + version)

            if (me_mode != "NONE"):
                self._log.info("ME_mode: " + me_mode)

            alive = self.sut_ssh.is_alive()
            self._log.info("SUT is alive: {}".format(alive))
            if alive == False:
                raise RuntimeError('SUT is Offline or Unreachable')

        if me_mode == 'Normal':
            me_mode = 'Operational'

        version = 'Operational: ' + opr_ver + ' Recovery: ' + rec_ver + ' Current State: ' + me_mode

        if echo_version:
            self._log.info("\tVersion detected: " + version)

        if compile_output:
            return version
        else:
            return {
                "Operational": opr_ver,
                "Recovery": rec_ver,
                "Current": me_mode,
                "SVN": me_svn,
                "HECI": me_heci
            }

    def get_ucode_ver(self, echo_version=True):
        """
        Read ucode version
        :param echo_version: True if display output
        :return bios version
        """
        cmd = 'cat /proc/cpuinfo | grep -im 1 microcode'
        if self._os_type != OperatingSystems.LINUX:
            output = self.run_powershell_command(self.get_ucode_command, get_output=True)
        else:
            result = self.run_ssh_command(cmd)
            version = result.stdout.split('\n')[0].split(' ')
            if echo_version:
                self._log.info("Version detected: " + version[1])
            return version[1]
        version = "NONE"
        for line in output.split('\n'):
            if "msr[8b] =" in line:
                version = line.split(" = ")[1].split('`')[0]
                break
            elif "Previous" in line or "BIOS" in line:
                version = line.split(":")[1].strip()
        if echo_version:
            self._log.info("Version detected: " + version)
        return version

    def get_win_ucode_ver(self, echo_version=True):
        """
        Read windows ucode version
        :param echo_version: True if display output
        :return bios version
        """
        output = self.run_powershell_command(self.get_ucode_command, get_output=True)
        version = "NONE"
        for line in output.split('\n'):
            if "msr[8b] =" in line:
                version = line.split(" = ")[1].split('`')[0]
                break
            elif "Current" in line:
                version = line.split(":")[1].strip()
        if echo_version:
            self._log.info("Version detected: " + version)
        return version

    def get_bios_ver(self, echo_version=True):
        """
        Read bios version
        :param echo_version: True if display output
        :return bios version
        """
        # cmd = 'dmidecode | grep "Version: ' + str(self._product)[0] + '"'
        cmd = 'dmidecode -s bios-version'
        if self._os_type != OperatingSystems.LINUX:
            output = self.run_powershell_command(self.get_bios_command, get_output=True)
        else:
            result = self.run_ssh_command(cmd)
            version = result.stdout
            if echo_version:
                self._log.info("Version detected: {}".format(version))
            return version
        version = "NONE"
        for line in output.split('\n'):
            if "SMBIOSBIOSVersion : " in line:
                version = line.split(' : ')[1]
                break
        if echo_version:
            self._log.info("Version detected: " + version)
        return version

    def block_until_complete(self, pre_version, update_type=""):
        """
        Add a delay for SPS update till it completes
        Reboot SUT for other updates
        :param pre_version: firmware version before update
        :param update_type: Firmware to be updated
        :returns: tuple (post_version, error_encountered)
        :rtype: (str, bool)
        """
        error_encountered = False

        if update_type == "SPS":
            if self.warm_reset:
                self._log.info("\tWarm reset the system")

                if self._os_type != OperatingSystems.LINUX and not self.sut_ssh.is_alive():
                    self.run_powershell_command(command=self.restart_sut_command, get_output=True)
                else:
                    self._log.info("\tWarm reset through SSH")
                    self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)

            if self.capsule_type == 'two capsule':
                time.sleep(self.WARM_RESET_TIMEOUT)
            self._log.info("\tWaiting until version switch. Timeout is " + str(self.SPS_UPDATE_TIMEOUT) + " seconds")
            time_end = datetime.now() + timedelta(seconds=self.SPS_UPDATE_TIMEOUT)
            self.time_activation = self.time_sps_ok - self.time_sps_reset
            self._log.info("SPS Activation Time: " + str(self.time_activation))
            self.KPI_log.info("SPS Activation Time: " + str(self.time_activation))
            if ((self.time_activation) > timedelta(seconds=10)):
                # raise RuntimeError("Failed SPS activation in less then 10 seconds")
                self.kpi_failed = True
                self._log.info("KPI failed SPS activation in less than 10 seconds")
            if pre_version == self.expected_ver:
                time.sleep(2)
                return self.get_current_version(echo_version=True), error_encountered
            post_version = pre_version

            while pre_version == post_version:
                if datetime.now() >= time_end:
                    raise RuntimeError(
                        "The version did not transition from '" + pre_version + "' within the timeout period")
                post_version = self.get_current_version(echo_version=True)
            self._log.info("\t\tThe version transitioned to '" + post_version)
            self.summary_log.info("The version transitioned to '" + post_version)
            self.summary_log.info("SPS version updated without any state transitions")
            return post_version, error_encountered
        else:
            # Run ESRT Check before Reboot
            if update_type == "inband":
                if not self.esrt_check():
                    return self.get_current_version(), True

            if self.warm_reset:
                self._log.info("\tWarm reset the system")
                self.time_activation = datetime.now()

                if self._os_type != OperatingSystems.LINUX and not self.sut_ssh.is_alive():
                    self.run_powershell_command(command=self.restart_sut_command, get_output=True)
                else:
                    if hasattr(self, "start_workloads"):
                        self._log.info("Stopping the workloads and VMs")
                        result = self.stop_workloads()
                        self._log.info("{}".format(result))
                        self.stop_VM()
                    self._log.info("\tWarm reset through SSH")
                    self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)
                self.time_activation = datetime.now() - self.time_activation
                self.time_activation = self.time_activation - timedelta(seconds=30)
                self.KPI_log.info("Time activation : " + str(self.time_activation - timedelta(seconds=30)))

                if self.fw_type == "efi_utility":
                    self._log.info(
                        "\tCheck EFI utility version in smbios table, continue to boot system to windows. Timeout is " + str(
                            self.reboot_timeout) + " seconds")
                    self.os.wait_for_os(self.reboot_timeout)
                    # time.sleep(self.SLEEP_TIME)
                    # time.sleep(self.WARM_RESET_TIMEOUT)
                    time.sleep(300)
                    post_version = "EFI utility"

                else:
                    # TODO: Verify that this is still a required workaround for Windows. Adds an extreme delay per run.
                    if self._os_type != OperatingSystems.LINUX and not self.sut_ssh.is_alive():
                        # SIMULATION --------------------------------
                        self._log.info("\t\tSIMULATION - Wait for system restart")
                        self.time_activation = datetime.now()
                        time.sleep(self.WARM_RESET_TIMEOUT)
                        self.time_activation = datetime.now() - self.time_activation

                        # SIMULATION --------------------------------
                    post_version = self.get_current_version()
                    self.summary_log.info("System warm reset complete in " + str(self.WARM_RESET_TIMEOUT) + " seconds")
                    self._log.info("\tSystem warm reset complete in " + str(self.WARM_RESET_TIMEOUT) + " seconds")
                if ((self.time_activation) > timedelta(minutes=11)):
                    # raise RuntimeError("Failed Activation period in less then 10 minutes")
                    self.kpi_failed = True
                    self._log.info("KPI failed SPS activation in less than 10 minutes")

            elif self.STAGING_REBOOT:
                post_version = self.get_current_version()

            else:
                self._log.info("\tSkip warm reset")
                self.summary_log.info("System did not perform any state transitions")
                self._log.info("\tSystem did not perform any state transitions")
                post_version = pre_version

        return post_version, error_encountered

    def patch_ucode(self, version):
        """
        Patch windows ucode image
        :param version: patch version number
        :return: True if patch was success
        """
        self._log.info("Patching the ucode image")
        # patch_path = self.system_path + 'Ucode\\' + ('rollback' if self.flow_type == 'rollback' else str(version))
        self.run_powershell_command(
            command=self._workload_path + 'CopyFile.ps1 ' + self._powershell_credentials + " " + str(version),
            get_output=True)
        return True

    def SSD_config(self, cmd):
        """
        Configure the SSD to obtain the driver location and name of the drive
        :return: output from powershell driver index and driver location
        """
        if self._os_type != OperatingSystems.LINUX:
            return self.run_powershell_command(
                command=self._workload_path + 'SSD_Config.ps1 ' + self._powershell_credentials + " " + str(
                    self.version), get_output=True)
        else:
            return self.run_ssh_command(cmd)

    def SSD_flash(self, path, version="", drive=""):
        """
        Flash SSD
        :param path: SSD file path
        """
        cmd = 'intelmas load -force -source ' + path + ' -intelssd ' + str(
            version) + ' CommitAction = 3 FirmwareSlot = 1'
        if self._os_type != OperatingSystems.LINUX:
            self.run_powershell_command(
                command=self._workload_path + 'SSD_Flash.ps1 ' + self._powershell_credentials + " " + str(
                    version) + " " + str(path), get_output=True)
        else:
            result = self.run_ssh_command(cmd)

    def SSD_update(self, path, version="", drive=""):
        """
        Execute SSD update
        :param path: Path to SSD file
        # :param start_workloads: True if workloads to be started
        :return True if update successful
        """
        result = False
        self._log.info("Flashing SSD drive")
        if self.fio:
            self._log.info("Running FIO in the Background")
            if self._os_type == OperatingSystems.LINUX:
                cmd = 'fio ' + self.fio + ' &'
                self.sut_ssh.execute(cmd)
            else:
                self.run_powershell_command(
                    command=self._workload_path + 'SSD_Fio.ps1 ' + self._powershell_credentials + " " + str(self.fio),
                    get_output=True)

        self._initial_sel_log = self.get_sel(show_log=True)
        try:

            initial_version = self.get_current_version()
            if initial_version == self.expected_ver:
                self._log.info("The initial version '" + initial_version + "' is already the expected version")
                return result

            self._log.info("The initial version '" + initial_version)
            self._log.info("Flashing SSD '" + path + "'")
            self.SSD_flash(path, version, drive)
            post_version = self.get_current_version()
            if not post_version == self.expected_ver:
                self._log.error(
                    "The version '" + post_version + "' is not the expected version '" + self.expected_ver + "'")
                result = False
            else:
                self._log.info("The version '" + post_version + "' is expected version '" + self.expected_ver + "'")
                self._log.info("Checking post-update conditions")
                result = self.examine_post_update_conditions()

        except RuntimeError as e:
            self._log.exception(e)
        return result

    def send_capsule_ac_while_staging(self, path, timeout_seconds, start_workloads=False, update_type="",
                                      capsule_path2=""):
        """
        Send staging capsule for Seamless update
        :param path: Path location of capsule.
        :param timeout_seconds: Amount of time to wait (in seconds) before canceling out of BMC update process.
        :param start_workloads: Spin up workloads during test.
        :param update_type: Update Handler type.
        :param capsule_path2: Secondary Capsule path to send to slot 2.
        :return: True if capsule staging is complete
        """
        result = False
        self.booted_after_ac = False
        self._log.info("\tClear previous BMC Journal and Event log entries")
        self._initial_sel_log = self.get_jnl_ac(show_log=True)

        self._initial_sel_log = self.get_sel(show_log=True)
        try:
            initial_version = None
            if not (self.sut_mode == "uefi" or self.sut_mode == "S5"):
                initial_version = self.get_current_version()
                if initial_version == self.expected_ver:
                    self._log.info(
                        "\tThe initial version '" + initial_version + "' is already the expected version: Proceeding with the update")
                elif self.expected_ver in initial_version:
                    self._log.info(
                        "\tThe expected version '" + self.expected_ver + "' is already in the initial version: Proceeding with the update")
            if start_workloads:
                if self._os_type == OperatingSystems.LINUX:
                    self.summary_log.info("\tStart workloads: {}".format(start_workloads))
                    self._log.info("\tStarting workloads, wait two minutes till workloads stabilize...")
                    self.begin_workloads_lin()
                else:
                    self.summary_log.info("\tStart workloads: {}".format(start_workloads))
                    self._log.info("\tStarting workloads, wait two minutes till workloads stabilize...")
                    self.begin_workloads()

            if not (self.activation):
                self._log.info("\tSending capsule image")
                self.summary_log.info("Sending capsule '" + path + "'")
                self._bmc_redfish.stage_capsule_update(path)

                self._bmc_redfish.verbose = False
                time_start = datetime.now()
                time_end = datetime.now() + timedelta(seconds=timeout_seconds)

                self._log.info("\tWaiting until BMC indicates capsule has completed staging. Timeout is " + str(
                    timeout_seconds) + " seconds ")
                done_staging = False
                while datetime.now() < time_end and not done_staging:
                    time.sleep(1)

                    if (self.stressors):
                        self._log.info("check access to BMC: " + str(self.verify_bmc_ip()))
                        self._log.info("check access to ME: " + str(self.get_sps_ver()))

                    for sel in self.get_jnl_ac(show_log=True):

                        self.summary_log.info("Got new SEL entry: " + str(sel))
                        # self._log.info("Got new SEL entry: " + str(sel))

                        if "firmware update" in sel and "started" in sel:
                            self.summary_log.info("SEL entry indicates capsule staging has started")
                            self._log.info(
                                "\tSEL entry indicates capsule staging has started. Waiting till staging completes...")
                        elif self.booted_after_ac:
                            self._log.info("\tBooted after AC cycle")
                            self.summary_log.info("Booted after AC cycle")
                            done_staging = True
                        elif "fixme failed" in sel:
                            self.summary_log.error("SEL entry indicates capsule staging failed")
                            self._log.error("\tSEL entry indicates capsule staging failed")
                            raise RuntimeError("BMC update did not complete: version transition failed")
                        elif "SEAMLESS_UPDATE_FAILED" in sel:
                            self.summary_log.error("SEL entry indicates Seamless update failed")
                            self._log.error("\tSEL entry indicates Seamless update failed")
                            raise RuntimeError("Seamless update failed")

                    # for sel, event_sel in zip(self.get_jnl_ac(show_log=True),self.get_sel(show_log=True)):
                    for event_sel in self.get_sel(show_log=True):
                        # self.summary_log.info("Got new SEL entry: " + str(sel))
                        self.summary_log.info("Got new SEL entry: " + str(event_sel))

                # self._log.info("Capsule Staging Time: " + str(self.time_capsule_staged - self.time_capsule_sent))

                if not done_staging:
                    self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count - 500
                    self._bmc_redfish.eve_skip_sel_count = self._bmc_redfish.eve_skip_sel_count - 500
                    if self.sps_mode:
                        for sel in self.get_jnl_check_sps_mode(show_log=True):
                            self.summary_log.info("Got new SEL entry: " + str(sel))
                            # self._log.info("Got new SEL entry: " + str(sel))

                            if "firmware update" in sel and "started" in sel:
                                self.summary_log.info("SEL entry indicates capsule staging has started")
                                self._log.info(
                                    "\tSEL entry indicates capsule staging has started. Waiting till staging completes...")
                            elif "Seamless" in sel and "update" in sel and "completed successfully" in sel:
                                self._log.info("\tSEL entry indicates capsule is done staging")
                                self.summary_log.info("SEL entry indicates capsule is done staging")
                                done_staging = True
                            elif "fixme failed" in sel:
                                self.summary_log.error("SEL entry indicates capsule staging failed")
                                self._log.error("\tSEL entry indicates capsule staging failed")
                                raise RuntimeError("BMC update did not complete: version transition failed")
                            elif "SEAMLESS_UPDATE_FAILED" in sel:
                                self.summary_log.error("SEL entry indicates Seamless update failed")
                                self._log.error("\tSEL entry indicates Seamless update failed")
                                raise RuntimeError("Seamless update failed")
                    else:
                        for sel in self.get_jnl_ac(show_log=True):
                            self.summary_log.info("Got new SEL entry: " + str(sel))
                            # self._log.info("Got new SEL entry: " + str(sel))

                            if "firmware update" in sel and "started" in sel:
                                self.summary_log.info("SEL entry indicates capsule staging has started")
                                self._log.info(
                                    "\tSEL entry indicates capsule staging has started. Waiting till staging completes...")
                            elif "Seamless" in sel and "update" in sel and "completed successfully" in sel:
                                self._log.info("\tSEL entry indicates capsule is done staging")
                                self.summary_log.info("SEL entry indicates capsule is done staging")
                                done_staging = True
                            elif "fixme failed" in sel:
                                self.summary_log.error("SEL entry indicates capsule staging failed")
                                self._log.error("\tSEL entry indicates capsule staging failed")
                                raise RuntimeError("BMC update did not complete: version transition failed")
                            elif "SEAMLESS_UPDATE_FAILED" in sel:
                                self.summary_log.error("SEL entry indicates Seamless update failed")
                                self._log.error("\tSEL entry indicates Seamless update failed")
                                raise RuntimeError("Seamless update failed")

                    for event_sel in self.get_sel(show_log=True):
                        self._log.info("Got new SEL entry: " + str(event_sel))

                    self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count + 500
                    self._bmc_redfish.eve_skip_sel_count = self._bmc_redfish.eve_skip_sel_count + 500
                # todo - If the BMC does not yet support triggering a warm reset, perform one here.
                if not done_staging:
                    raise RuntimeError(
                        "The SEL did not contain a message indicating a complete transmission and staging of the capsule")
                self.time_staging = datetime.now() - time_start
                self._log.info("\t\tDone with BMC Flashing. Approx time was " + str(self.time_staging))
                # self.time_staging = self.time_capsule_staged - self.time_capsule_sent

            # post_version
            if not (self.sut_mode == "uefi" or self.sut_mode == "S5"):
                post_version, errors = self.block_until_complete(initial_version, update_type)
                if post_version == self.expected_ver:
                    result = True
                elif self.expected_ver in post_version:
                    result = True
                if not post_version == self.expected_ver:
                    if self.expected_ver not in post_version:
                        self._log.error(
                            "\tThe version '" + str(post_version) + "' is not the expected version '" + str(
                                self.expected_ver) + "'")
                        result = False
                elif post_version == 'NONE':
                    self.summary_log.error("Failed to detect version: reboot system or flash bios image")
                    self._log.error("\tFailed to detect version: reboot system or flash bios image")
                    result = False
                else:
                    self._log.info(
                        "\t\tThe version '" + str(post_version) + "' is expected version '" + str(
                            self.expected_ver) + "'")
                    if self.warm_reset and self.workloads_started and self._os_type == OperatingSystems.WINDOWS:
                        self.begin_workloads()
                    if not (self.loop_count):
                        self._log.info("\tChecking post-update conditions")
                        result = self.examine_post_update_conditions(update_type)
                        self._log.info("\tPost update conditions checked")
            else:
                self._log.info("\tChecking post-update conditions")
                result = self.examine_post_update_conditions(update_type)
                self._log.info("\tPost update conditions checked")

        except RuntimeError as e:
            self._log.exception(e)

            if self.workloads_started:
                if self._os_type == OperatingSystems.LINUX and not self.warm_reset:
                    self.stop_workloads_lin()
                elif self._os_type == OperatingSystems.WINDOWS:
                    self._log.info('\tStopping workloads')
                    wl_output = self.stop_workloads()
                    self._log.error("Evaluating workload output")
                    if not self.evaluate_workload_output(wl_output):
                        result = False

        return result

    def send_capsule(self, path, timeout_seconds, start_workloads=False, update_type="", capsule_path2=""):
        """
        Send staging capsule for Seamless update
        :param path: Path location of capsule.
        :param timeout_seconds: Amount of time to wait (in seconds) before canceling out of BMC update process.
        :param start_workloads: Spin up workloads during test.
        :param update_type: Update Handler type.
        :param capsule_path2: Secondary Capsule path to send to slot 2.
        :return: True if capsule staging is complete
        """
        result = False
        self._log.info("\tClear previous BMC Journal and Event log entries")
        if self.sps_mode:
            self._initial_sel_log = self.get_jnl_check_sps_mode(show_log=True)
        else:
            self._initial_sel_log = self.get_jnl(show_log=True)
        self._initial_sel_log = self.get_sel(show_log=True)
        try:
            initial_version = None
            if not (self.sut_mode == "uefi" or self.sut_mode == "S5"):
                initial_version = self.get_current_version()
                if initial_version == self.expected_ver:
                    self._log.info(
                        "\tThe initial version '" + initial_version + "' is already the expected version: Proceeding with the update")
                elif self.expected_ver in initial_version:
                        self._log.info(
                        "\tThe expected version '" + self.expected_ver + "' is already in the initial version: Proceeding with the update")

            # Check with OrchestratorValidator
            if self.run_orchestrator:
                if not self.run_orchestrator_validation(self.capsule_xml):
                    return False

            if start_workloads:
                if self._os_type == OperatingSystems.LINUX:
                    self.summary_log.info("\tStart workloads: {}".format(start_workloads))
                    self._log.info("\tStarting workloads, wait two minutes till workloads stabilize...")
                    self.begin_workloads_lin()
                else:
                    self.summary_log.info("\tStart workloads: {}".format(start_workloads))
                    self._log.info("\tStarting workloads, wait two minutes till workloads stabilize...")
                    self.begin_workloads()

            if not (self.activation):
                self._log.info("\tSending capsule image")
                self.summary_log.info("Sending capsule '" + path + "'")
                self._bmc_redfish.stage_capsule_update(path)

                self._bmc_redfish.verbose = False
                time_start = datetime.now()
                time_end = datetime.now() + timedelta(seconds=timeout_seconds)

                self._log.info("\tWaiting until BMC indicates capsule has completed staging. Timeout is " + str(
                    timeout_seconds) + " seconds ")
                done_staging = False
                while datetime.now() < time_end and not done_staging:
                    time.sleep(1)

                    if (self.stressors):
                        self._log.info("check access to BMC: " + str(self.verify_bmc_ip()))
                        self._log.info("check access to ME: " + str(self.get_sps_ver()))

                    if self.sps_mode:
                        for sel in self.get_jnl_check_sps_mode(show_log=True):

                            self.summary_log.info("Got new SEL entry: " + str(sel))
                            # self._log.info("Got new SEL entry: " + str(sel))

                            if "firmware update" in sel and "started" in sel:
                                self.summary_log.info("SEL entry indicates capsule staging has started")
                                self._log.info(
                                    "\tSEL entry indicates capsule staging has started. Waiting till staging completes...")
                            elif "Seamless" in sel and "update" in sel and "completed successfully" in sel:
                                self._log.info("\tSEL entry indicates capsule is done staging")
                                self.summary_log.info("SEL entry indicates capsule is done staging")
                                done_staging = True
                            elif "fixme failed" in sel:
                                self.summary_log.error("SEL entry indicates capsule staging failed")
                                self._log.error("\tSEL entry indicates capsule staging failed")
                                raise RuntimeError("BMC update did not complete: version transition failed")
                            elif "SEAMLESS_UPDATE_FAILED" in sel:
                                self.summary_log.error("SEL entry indicates Seamless update failed")
                                self._log.error("\tSEL entry indicates Seamless update failed")
                                raise RuntimeError("Seamless update failed")
                    else:
                        for sel in self.get_jnl(show_log=True):

                            self.summary_log.info("Got new SEL entry: " + str(sel))
                            # self._log.info("Got new SEL entry: " + str(sel))

                            if "firmware update" in sel and "started" in sel:
                                self.summary_log.info("SEL entry indicates capsule staging has started")
                                self._log.info(
                                    "\tSEL entry indicates capsule staging has started. Waiting till staging completes...")
                            elif "Seamless" in sel and "update" in sel and "completed successfully" in sel:
                                self._log.info("\tSEL entry indicates capsule is done staging")
                                self.summary_log.info("SEL entry indicates capsule is done staging")
                                done_staging = True
                            elif "fixme failed" in sel:
                                self.summary_log.error("SEL entry indicates capsule staging failed")
                                self._log.error("\tSEL entry indicates capsule staging failed")
                                raise RuntimeError("BMC update did not complete: version transition failed")
                            elif "SEAMLESS_UPDATE_FAILED" in sel:
                                self.summary_log.error("SEL entry indicates Seamless update failed")
                                self._log.error("\tSEL entry indicates Seamless update failed")
                                raise RuntimeError("Seamless update failed")

                    # for sel, event_sel in zip(self.get_jnl(show_log=True),self.get_sel(show_log=True)):
                    for event_sel in self.get_sel(show_log=True):
                        # self.summary_log.info("Got new SEL entry: " + str(sel))
                        self.summary_log.info("Got new SEL entry: " + str(event_sel))
                self.capsule_staging_time = self.time_capsule_staged - self.time_capsule_sent
                self.KPI_log.info("Capsule Staging Time: " + str(self.capsule_staging_time))
                self._log.info("Capsule Staging Time: " + str(self.capsule_staging_time))
                if (self.capsule_staging_time > timedelta(minutes=5)):
                    # raise RuntimeError("Failed to stage in less then 5 minutes")
                    self.kpi_failed = True
                    self._log.info("KPI fail: failed to stage in less than 5 minutes")

                if not done_staging:
                    self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count - 500
                    self._bmc_redfish.eve_skip_sel_count = self._bmc_redfish.eve_skip_sel_count - 500
                    if self.sps_mode:
                        for sel in self.get_jnl_check_sps_mode(show_log=True):
                            self.summary_log.info("Got new SEL entry: " + str(sel))
                            # self._log.info("Got new SEL entry: " + str(sel))

                            if "firmware update" in sel and "started" in sel:
                                self.summary_log.info("SEL entry indicates capsule staging has started")
                                self._log.info(
                                    "\tSEL entry indicates capsule staging has started. Waiting till staging completes...")
                            elif "Seamless" in sel and "update" in sel and "completed successfully" in sel:
                                self._log.info("\tSEL entry indicates capsule is done staging")
                                self.summary_log.info("SEL entry indicates capsule is done staging")
                                done_staging = True
                            elif "fixme failed" in sel:
                                self.summary_log.error("SEL entry indicates capsule staging failed")
                                self._log.error("\tSEL entry indicates capsule staging failed")
                                raise RuntimeError("BMC update did not complete: version transition failed")
                            elif "SEAMLESS_UPDATE_FAILED" in sel:
                                self.summary_log.error("SEL entry indicates Seamless update failed")
                                self._log.error("\tSEL entry indicates Seamless update failed")
                                raise RuntimeError("Seamless update failed")
                    else:
                        for sel in self.get_jnl(show_log=True):
                            self.summary_log.info("Got new SEL entry: " + str(sel))
                            # self._log.info("Got new SEL entry: " + str(sel))

                            if "firmware update" in sel and "started" in sel:
                                self.summary_log.info("SEL entry indicates capsule staging has started")
                                self._log.info(
                                    "\tSEL entry indicates capsule staging has started. Waiting till staging completes...")
                            elif "Seamless" in sel and "update" in sel and "completed successfully" in sel:
                                self._log.info("\tSEL entry indicates capsule is done staging")
                                self.summary_log.info("SEL entry indicates capsule is done staging")
                                done_staging = True
                            elif "fixme failed" in sel:
                                self.summary_log.error("SEL entry indicates capsule staging failed")
                                self._log.error("\tSEL entry indicates capsule staging failed")
                                raise RuntimeError("BMC update did not complete: version transition failed")
                            elif "SEAMLESS_UPDATE_FAILED" in sel:
                                self.summary_log.error("SEL entry indicates Seamless update failed")
                                self._log.error("\tSEL entry indicates Seamless update failed")
                                raise RuntimeError("Seamless update failed")

                    for event_sel in self.get_sel(show_log=True):
                        self._log.info("Got new SEL entry: " + str(event_sel))

                    self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count + 500
                    self._bmc_redfish.eve_skip_sel_count = self._bmc_redfish.eve_skip_sel_count + 500
                # todo - If the BMC does not yet support triggering a warm reset, perform one here.
                if not done_staging:
                    raise RuntimeError(
                        "The SEL did not contain a message indicating a complete transmission and staging of the capsule")
                self.time_staging = datetime.now() - time_start
                self._log.info("\t\tDone with BMC Flashing. Approx time was " + str(self.time_staging))
                self.time_staging = self.time_capsule_staged - self.time_capsule_sent

                if update_type == 'ucode':
                    self._log.info("\tSending FV2 capsule image")
                    self.summary_log.info("Sending capsule '" + capsule_path2 + "'")
                    self._bmc_redfish.stage_capsule_update(capsule_path2)
                    self._bmc_redfish.verbose = False
                    time_start = datetime.now()
                    time_end = datetime.now() + timedelta(seconds=timeout_seconds)

                    self._log.info("\tWaiting until BMC indicates capsule has completed staging. Timeout is " + str(
                        timeout_seconds) + " seconds ")
                    done_staging = False
                    while datetime.now() < time_end and not done_staging:
                        time.sleep(1)
                        for sel in self.get_jnl(show_log=True):

                            self.summary_log.info("Got new SEL entry: " + str(sel))
                            # self._log.info("Got new SEL entry: " + str(sel))

                            if "firmware update" in sel and "started" in sel:
                                self.summary_log.info("SEL entry indicates capsule staging has started")
                                self._log.info(
                                    "\tSEL entry indicates capsule staging has started. Waiting till staging completes...")
                            elif "Seamless" in sel and "update" in sel and "completed successfully" in sel:
                                self._log.info("\tSEL entry indicates capsule is done staging")
                                self.summary_log.info("SEL entry indicates capsule is done staging")
                                done_staging = True
                            elif "fixme failed" in sel:
                                self.summary_log.error("SEL entry indicates capsule staging failed")
                                self._log.error("\tSEL entry indicates capsule staging failed")
                                raise RuntimeError("BMC update did not complete: version transition failed")
                            elif "SEAMLESS_UPDATE_FAILED" in sel:
                                self.summary_log.error("SEL entry indicates Seamless update failed")
                                self._log.error("\tSEL entry indicates Seamless update failed")
                                raise RuntimeError("Seamless update failed")

                        # for sel, event_sel in zip(self.get_jnl(show_log=True),self.get_sel(show_log=True)):
                        for event_sel in self.get_sel(show_log=True):
                            # self.summary_log.info("Got new SEL entry: " + str(sel))
                            self.summary_log.info("Got new SEL entry: " + str(event_sel))
                    self.capsule_staging_time = self.time_capsule_staged - self.time_capsule_sent
                    self.KPI_log.info(
                        "Capsule Staging Time ucode: " + str(self.capsule_staging_time))
                    self._log.info("Capsule Staging Time: " + str(self.capsule_staging_time))
                    if ((self.capsule_staging_time) > timedelta(minutes=5)):
                        # raise RuntimeError("Failed to stage in less then 5 minutes")
                        self.kpi_failed = True
                        self._log.info("KPI fail: failed to stage in less than 5 minutes")

                    if not done_staging:
                        self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count - 500
                        self._bmc_redfish.eve_skip_sel_count = self._bmc_redfish.eve_skip_sel_count - 500
                        for sel in self.get_jnl(show_log=True):
                            self.summary_log.info("Got new SEL entry: " + str(sel))
                            # self._log.info("Got new SEL entry: " + str(sel))

                            if "firmware update" in sel and "started" in sel:
                                self.summary_log.info("SEL entry indicates capsule staging has started")
                                self._log.info(
                                    "\tSEL entry indicates capsule staging has started. Waiting till staging completes...")
                            elif "Seamless" in sel and "update" in sel and "completed successfully" in sel:
                                self._log.info("\tSEL entry indicates capsule is done staging")
                                self.summary_log.info("SEL entry indicates capsule is done staging")
                                done_staging = True
                            elif "fixme failed" in sel:
                                self.summary_log.error("SEL entry indicates capsule staging failed")
                                self._log.error("\tSEL entry indicates capsule staging failed")
                                raise RuntimeError("BMC update did not complete: version transition failed")
                            elif "SEAMLESS_UPDATE_FAILED" in sel:
                                self.summary_log.error("SEL entry indicates Seamless update failed")
                                self._log.error("\tSEL entry indicates Seamless update failed")
                                raise RuntimeError("Seamless update failed")

                        for event_sel in self.get_sel(show_log=True):
                            self._log.info("Got new SEL entry: " + str(event_sel))

                        self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count + 500
                        self._bmc_redfish.eve_skip_sel_count = self._bmc_redfish.eve_skip_sel_count + 500
                    # todo - If the BMC does not yet support triggering a warm reset, perform one here.
                    if not done_staging:
                        raise RuntimeError(
                            "The SEL did not contain a message indicating a complete transmission and staging of the capsule")
                    self.time_staging = datetime.now() - time_start
                    self._log.info("\t\tDone with staging FV2. Approx time was " + str(self.time_staging))

            if not (self.sut_mode == "uefi" or self.sut_mode == "S5"):
                post_version, errors = self.block_until_complete(initial_version, update_type)
                if post_version == self.expected_ver:
                    result = True
                elif self.expected_ver in post_version:
                    result = True
                if not post_version == self.expected_ver:
                    if self.expected_ver not in post_version:
                        self._log.error(
                            "\tThe version '" + str(post_version) + "' is not the expected version '" + str(
                                self.expected_ver) + "'")
                        result = False
                elif post_version == 'NONE':
                    self.summary_log.error("Failed to detect version: reboot system or flash bios image")
                    self._log.error("\tFailed to detect version: reboot system or flash bios image")
                    result = False
                else:
                    self._log.info(
                        "\t\tThe version '" + str(post_version) + "' is expected version '" + str(
                            self.expected_ver) + "'")
                    if self.warm_reset and self.workloads_started and self._os_type == OperatingSystems.WINDOWS:
                        self.begin_workloads()
                    if not (self.loop_count):
                        self._log.info("\tChecking post-update conditions")
                        result = self.examine_post_update_conditions(update_type)
                        self._log.info("\tPost update conditions checked")
            else:
                self._log.info("\tChecking post-update conditions")
                result = self.examine_post_update_conditions(update_type)
                self._log.info("\tPost update conditions checked")

        except RuntimeError as e:
            self._log.exception(e)

        if self.workloads_started:
            if self._os_type == OperatingSystems.LINUX and not self.warm_reset:
                self.stop_workloads_lin()
            elif self._os_type == OperatingSystems.WINDOWS:
                self._log.info('\tStopping workloads')
                wl_output = self.stop_workloads()
                self._log.error("Evaluating workload output")
                if not self.evaluate_workload_output(wl_output):
                    result = False

        if self.run_orchestrator:
            try:
                self._bmc_redfish.reset_bmc()
            except Exception:
                self._log.error(
                    "bmc reset operation failed, please reset the bmc manually before proceeding to next test case")

        return result

    def send_capsule_negative(self, path, timeout_seconds, start_workloads=False, update_type="", capsule_path2="",
                              capsule_type=""):
        """
        Send staging capsule for Seamless update
        :param path: Path location of capsule.
        :param timeout_seconds: Amount of time to wait (in seconds) before canceling out of BMC update process.
        :param start_workloads: Spin up workloads during test.
        :param update_type: Update Handler type.
        :param capsule_path2: Secondary Capsule path to send to slot 2.
        :return: True if capsule staging is complete
        """
        result = False
        self._log.info("\tClear previous BMC Journals entries")
        self._initial_sel_log = self.get_jnl(show_log=True)
        try:
            initial_version = None
            if not (self.sut_mode == "uefi" or self.sut_mode == "S5"):
                initial_version = self.get_current_version()
                self._log.info(
                    "\tThe initial version is {} : Proceeding with the update".format(initial_version))

            if start_workloads:
                self.summary_log.info("\tStart workloads: {}".format(start_workloads))
                self._log.info("\tStarting workloads, wait two minutes till workloads stabilize...")
                self.begin_workloads()

            self._log.info("\tSending capsule image")
            self.summary_log.info("Sending capsule {}".format(path))
            self._bmc_redfish.stage_capsule_update(path)

            self._bmc_redfish.verbose = False
            time_start = datetime.now()
            time_end = datetime.now() + timedelta(seconds=timeout_seconds)

            self._log.info("\tWaiting until BMC indicates capsule has completed staging. Timeout is {} seconds".format
                           (timeout_seconds))
            done_staging = False
            while datetime.now() < time_end and not done_staging:
                time.sleep(1)

                for sel in self.get_jnl():
                    done_staging = self.sel_log(sel, done_staging)

            if not done_staging:
                self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count - 500
                for sel in self.get_jnl():
                    done_staging = self.sel_log(sel, done_staging)
                self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count + 500

            if not done_staging:
                self._log.info("The SEL did not contain a message indicating a complete transmission "
                               "and staging of the capsule")
                self.time_staging = datetime.now() - time_start
                if capsule_type == 'negative':
                    if self.get_current_version() == initial_version:
                        self._log.info(
                            "\t\tThe version {} is expected version {}".format(self.get_current_version(),
                                                                               initial_version))
                        self.time_staging = datetime.now() - time_start
                        self._log.info("\tFLASHING FAILED AS EXPECTED AS WE ARE SENDING CORRUPTED CAPSULE. "
                                       "Approx time was {}".format(self.time_staging))
                        return True

            if update_type == 'ucode':
                self._log.info("\tSending FV2 capsule image")
                self.summary_log.info("Sending capsule {}".format(capsule_path2))
                self._bmc_redfish.stage_capsule_update(capsule_path2)
                self._bmc_redfish.verbose = False
                time_start = datetime.now()
                time_end = datetime.now() + timedelta(seconds=timeout_seconds)

                self._log.info("\tWaiting until BMC indicates capsule has completed staging. Timeout is {} seconds"
                               .format(timeout_seconds))
                done_staging = False
                while datetime.now() < time_end and not done_staging:
                    time.sleep(1)

                    for sel in self.get_jnl():
                        self.summary_log.info("Got new SEL entry: {}".format(sel))
                        if "fixme started" in sel:
                            done_staging = self.sel_log(sel, done_staging)

                if not done_staging:
                    self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count - 500
                    for sel in self.get_jnl():
                        done_staging = self.sel_log(sel, done_staging)
                    self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count + 500

                if not done_staging:
                    self._log.info("The SEL did not contain a message indicating a complete transmission and "
                                   "staging of the capsule")
                self.time_staging = datetime.now() - time_start
                if capsule_type == 'negative':
                    if self.get_current_version() == initial_version:
                        self._log.info(
                            "\t\tThe version {} is expected version {}".format(self.get_current_version(),
                                                                               initial_version))
                        self.time_staging = datetime.now() - time_start
                        self._log.info("\tFLASHING FAILED AS EXPECTED AS WE ARE SENDING CORRUPTED CAPSULE. "
                                       "Approx time was {}".format(self.time_staging))
                        return True

            if not (self.sut_mode == "uefi" or self.sut_mode == "S5"):
                post_version, errors = self.block_until_complete(initial_version, update_type)
                self._log.info("post version is {}".format(post_version))
                if post_version == initial_version:
                    result = True
                if not post_version == initial_version:
                    if initial_version not in post_version:
                        self._log.error(
                            "\tThe version {} is not the expected version {}".format(post_version, self.expected_ver))
                        result = False
                elif post_version == 'NONE':
                    self.summary_log.error("Failed to detect version: reboot system or flash bios image")
                    self._log.error("\tFailed to detect version: reboot system or flash bios image")
                    result = False
                else:
                    self._log.info(
                        "\t\tThe version {} is expected version {}".format(post_version, self.expected_ver))
                    if self.warm_reset and self.workloads_started:
                        self.begin_workloads()
                    if not (self.loop_count):
                        self._log.info("\tChecking post-update conditions")
                        result = self.examine_post_update_conditions(update_type)
                        self._log.info("\tPost update conditions checked")
            else:
                self._log.info("\tChecking post-update conditions")
                result = self.examine_post_update_conditions(update_type)
                self._log.info("\tPost update conditions checked")
        except RuntimeError as e:
            self._log.exception(e)

        if self.workloads_started:
            self._log.info('\tStopping workloads')
            wl_output = self.stop_workloads()
            self._log.error("Evaluating workload output")
            if not self.evaluate_workload_output(wl_output):
                result = False

        return result

    def send_capsule_parallel(self, path, timeout_seconds, start_workloads=False, update_type="", capsule_path2=""):
        """
        Send staging capsule for Seamless update
        :param path: Path location of capsule.
        :param timeout_seconds: Amount of time to wait (in seconds) before canceling out of BMC update process.
        :param start_workloads: Spin up workloads during test.
        :param update_type: Update Handler type.
        :param capsule_path2: Secondary Capsule path to send to slot 2.
        :return: True if capsule staging is complete
        """
        result = False
        self._log.info("\tClear previous BMC Journals entries")
        self._initial_sel_log = self.get_jnl_parallel(show_log=True)
        try:
            initial_version = None
            if not (self.sut_mode == "uefi" or self.sut_mode == "S5"):
                initial_version = self.get_current_version()
                if initial_version == self.expected_ver:
                    self._log.info(
                        "\tThe initial version {} is already the expected version: Proceeding with the update".format(
                            initial_version))
                elif self.expected_ver in initial_version:
                    self._log.info(
                        "\tThe expected version {} is already in the initial version: Proceeding with the update".format(
                            self.expected_ver))

            # Check with OrchestratorValidator
            if self.run_orchestrator:
                if not self.run_orchestrator_validation(self.capsule_xml):
                    return False

            if start_workloads:
                self.summary_log.info("\tStart workloads: {}".format(start_workloads))
                self._log.info("\tStarting workloads, wait two minutes till workloads stabilize...")
                self.begin_workloads()

            self._log.info("\tSending capsule image")
            self.summary_log.info("Sending capsule {}".format(path))
            self._bmc_redfish.stage_capsule_update(path)

            self._bmc_redfish.verbose = False
            time_start = datetime.now()
            time_end = datetime.now() + timedelta(seconds=timeout_seconds)

            self._log.info("\tWaiting until BMC indicates capsule has completed staging. Timeout is {} seconds".format(
                timeout_seconds))
            done_staging = False
            while datetime.now() < time_end and not done_staging:
                time.sleep(1)

                for sel in self.get_jnl_parallel():
                    done_staging = self.sel_log(sel, done_staging)

            if not done_staging:
                self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count - 500
                for sel in self.get_jnl_parallel():
                    done_staging = self.sel_log(sel, done_staging)

                self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count + 500
            if not done_staging:
                raise RuntimeError(
                    "The SEL did not contain a message indicating a complete transmission and staging of the capsule")
            self.time_staging = datetime.now() - time_start
            self._log.info("\t\tDone with BMC Flashing. Approx time was {}".format(self.time_staging))
            self.time_staging = self.time_capsule_staged - self.time_capsule_sent

            if update_type == 'ucode':
                self._log.info("\tSending FV2 capsule image")
                self.summary_log.info("Sending capsule {}".format(capsule_path2))
                self._bmc_redfish.stage_capsule_update(capsule_path2)
                self._bmc_redfish.verbose = False
                time_start = datetime.now()
                time_end = datetime.now() + timedelta(seconds=timeout_seconds)

                self._log.info(
                    "\tWaiting until BMC indicates capsule has completed staging. Timeout is {} seconds".format(
                        timeout_seconds))
                done_staging = False
                while datetime.now() < time_end and not done_staging:
                    time.sleep(1)

                    for sel in self.get_jnl_parallel():
                        self.summary_log.info("Got new SEL entry: {}".format(sel))
                        if "fixme started" in sel:
                            done_staging = self.sel_log(sel, done_staging)

                if not done_staging:
                    self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count - 500
                    for sel in self.get_jnl_parallel():
                        done_staging = self.sel_log(sel, done_staging)

                    self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count + 500
                if not done_staging:
                    raise RuntimeError(
                        "The SEL did not contain a message indicating a complete transmission and staging of the capsule")
                self.time_staging = datetime.now() - time_start
                self._log.info("\t\tDone with staging FV2. Approx time was {}".format(self.time_staging))

            if not (self.sut_mode == "uefi" or self.sut_mode == "S5"):
                post_version, errors = self.block_until_complete(initial_version, update_type)
                if post_version == self.expected_ver:
                    result = True
                elif self.expected_ver in post_version:
                    result = True
                if not post_version == self.expected_ver:
                    if self.expected_ver not in post_version:
                        self._log.error(
                            "\tThe version {} is not the expected version {}".format(post_version, self.expected_ver))
                        result = False
                elif post_version == 'NONE':
                    self.summary_log.error("Failed to detect version: reboot system or flash bios image")
                    self._log.error("\tFailed to detect version: reboot system or flash bios image")
                    result = False
                else:
                    self._log.info("\t\tThe version {} is expected version {}".format(post_version, self.expected_ver))
                    if self.warm_reset and self.workloads_started:
                        self.begin_workloads()
                    if not (self.loop_count):
                        self._log.info("\tChecking post-update conditions")
                        result = self.examine_post_update_conditions(update_type)
                        self._log.info("\tPost update conditions checked")
            else:
                self._log.info("\tChecking post-update conditions")
                result = self.examine_post_update_conditions(update_type)
                self._log.info("\tPost update conditions checked")

        except:
            self._log.info("Exiting this capsule update since already an update is under staging..!!\n")
            self._log.info(
                "======LATEST CAPSULE UPDATE REQUEST REJECTED, MOVING FORWARD WITH THE EXISTING CAPSULE UPDATE=======\n")

        if self.workloads_started:
            self._log.info('\tStopping workloads')
            wl_output = self.stop_workloads()
            self._log.error("Evaluating workload output")
            if not self.evaluate_workload_output(wl_output):
                result = False

        return result

    def send_capsule_without_version_check(self, path, timeout_seconds, start_workloads=False, update_type="",
                                           capsule_path2=""):
        result = False
        self._log.info("\tClear previous BMC Journals entries")
        self._initial_sel_log = self.get_jnl(show_log=True)
        try:
            initial_version = None
            if not (self.sut_mode == "uefi" or self.sut_mode == "S5"):
                initial_version = self.get_current_version()
                self._log.info("\tThe initial version is {}".format(initial_version))
            if start_workloads:
                self.summary_log.info("\tStart workloads: {}".format(start_workloads))
                self._log.info("\tStarting workloads, wait two minutes till workloads stabilize...")
                self.begin_workloads()

            self._log.info("\tSending capsule image")
            self.summary_log.info("Sending capsule {}".format(path))
            self._bmc_redfish.stage_capsule_update(path)

            self._bmc_redfish.verbose = False
            time_start = datetime.now()
            time_end = datetime.now() + timedelta(seconds=timeout_seconds)

            self._log.info("\tWaiting until BMC indicates capsule has completed staging. Timeout is {} seconds".format(
                timeout_seconds))
            done_staging = False
            while datetime.now() < time_end and not done_staging:
                time.sleep(1)

                for sel in self.get_jnl():
                    done_staging = self.sel_log(sel, done_staging)

            if not done_staging:
                self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count - 500
                for sel in self.get_jnl():
                    done_staging = self.sel_log(sel, done_staging)
                self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count + 500

            if not done_staging:
                raise RuntimeError(
                    "The SEL did not contain a message indicating a complete transmission and staging of the capsule")
            self.time_staging = datetime.now() - time_start
            self._log.info("\t\tDone with BMC Flashing. Approx time was {}".format(self.time_staging))
            self.time_staging = self.time_capsule_staged - self.time_capsule_sent

            if update_type == 'ucode':
                self._log.info("\tSending FV2 capsule image")
                self.summary_log.info("Sending capsule {}".format(capsule_path2))
                self._bmc_redfish.stage_capsule_update(capsule_path2)
                self._bmc_redfish.verbose = False
                time_start = datetime.now()
                time_end = datetime.now() + timedelta(seconds=timeout_seconds)

                self._log.info(
                    "\tWaiting until BMC indicates capsule has completed staging. Timeout is {} seconds".format(
                        timeout_seconds))
                done_staging = False
                while datetime.now() < time_end and not done_staging:
                    time.sleep(1)

                    for sel in self.get_jnl():
                        self.summary_log.info("Got new SEL entry: {}".format(sel))
                        # if "fixme started" in sel:
                        #     done_staging = self.sel_log(sel, done_staging)
                        done_staging = self.sel_log(sel, done_staging)

                if not done_staging:
                    self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count - 500
                    for sel in self.get_jnl():
                        done_staging = self.sel_log(sel, done_staging)
                    self._bmc_redfish._skip_sel_count = self._bmc_redfish._skip_sel_count + 500

                if not done_staging:
                    raise RuntimeError(
                        "The SEL did not contain a message indicating a complete transmission and staging of the capsule")
                self.time_staging = datetime.now() - time_start
                self._log.info("\t\tDone with staging FV2. Approx time was {}".format(str(self.time_staging)))

            if not (self.sut_mode == "uefi" or self.sut_mode == "S5"):
                post_version, errors = self.block_until_complete(initial_version, update_type)
                result = True
                if self.warm_reset and self.workloads_started:
                    self.begin_workloads()

                if not (self.loop_count):
                    self._log.info("\tChecking post-update conditions")
                    result = self.examine_post_update_conditions(update_type)
                    self._log.info("\tPost update conditions checked")
            else:
                self._log.info("\tChecking post-update conditions")
                result = self.examine_post_update_conditions(update_type)
                self._log.info("\tPost update conditions checked")

        except RuntimeError as e:
            self._log.exception(e)

        if self.workloads_started:
            self._log.info("\tStopping workloads")
            wl_output = self.stop_workloads()
            self._log.error("Evaluating workload output")
            if not self.evaluate_workload_output(wl_output):
                result = False

        return result

    def send_capsule_inband(self, path, start_workloads=False, update_type="", capsule_type=""):
        """
        Send staging capsule for Seamless update using In-Band methods
        :param path: Path location of capsule.
        :param start_workloads: Spin up workloads during test.
        :param update_type: Update Handler type.
        :param capsule_type: Update capsule type if it is negative.
        :return: True if capsule staging is complete
        """
        result = False
        errors = False

        try:
            initial_version = self.get_current_version()

            if initial_version == self.expected_ver:
                self._log.info("\tThe initial version '" + initial_version + "' is already the expected version: "
                                                                             "Proceeding with the update")

            if start_workloads:
                self.summary_log.info("\tStart workloads: " + str(start_workloads))
                self._log.info("\tStarting workloads, wait two minutes till workloads stabilize...")
                self.begin_workloads()

            time_start = datetime.now()

            self._log.info("\tSending capsule image")
            self.summary_log.info("Sending capsule '" + path + "'")
            self.stage_inband_capsule_update(path)

            self.time_staging = datetime.now() - time_start
            self._log.info("\t\tDone with staging. Approx time was " + str(self.time_staging))

            post_version, errors = self.block_until_complete(initial_version, update_type)
            if capsule_type == 'negative':
                if post_version == initial_version:
                    self._log.info("\t\tThe version {} is expected version {}".format(post_version, initial_version))
                    self._log.info("ERRORS ARE EXPECTED AS WE ARE UPDATING THE BAD CAPSULE.")
                    result, errors = True, False
                    return result and not errors
            elif not errors and self.skip_reset:
                if post_version == initial_version:
                    self._log.info("\t\tThe version {} is expected version {}".format(post_version, initial_version))
                    result = True
                    return result
            if not post_version == self.expected_ver:
                self._log.error(
                    "\tThe version {} is not the expected version {}".format(post_version, self.expected_ver))
                result = False
            elif post_version == 'NONE':
                self.summary_log.error("Failed to detect version: reboot system or flash bios image")
                self._log.error("\tFailed to detect version: reboot system or flash bios image")
            else:
                self._log.info(
                    "\t\tThe version '" + post_version + "' is expected version '" + self.expected_ver + "'")
                if self.warm_reset and self.workloads_started:
                    self.begin_workloads()
                self._log.info("\tChecking post-update conditions")
                result = self.examine_post_update_conditions(update_type)
                self._log.info("\tPost update conditions checked")
                if capsule_type == 'negative' and errors == True:
                    self._log.info("ERRORS ARE EXPECTED AS WE ARE UPDATING THE BAD CAPSULE.")
                    result, errors = True, False

        except Exception as e:
            self._log.exception(e)

        if self.workloads_started:
            self._log.info('\tStopping workloads')
            wl_output = self.stop_workloads()
            self._log.error("Evaluating workload output")
            if not self.evaluate_workload_output(wl_output):
                result = False

        return result and not errors

    def send_capsule_inband_parallel(self, path, start_workloads=False, update_type="", capsule_type="",
                                     capsule_path2=""):
        """
        Send staging capsule for Seamless update using In-Band methods
        :param path: Path location of capsule.
        :param start_workloads: Spin up workloads during test.
        :param update_type: Update Handler type.
        :param capsule_type: Update capsule type if it is negative.
        :return: True if capsule staging is complete
        """
        result = False
        errors = False

        try:
            initial_version = self.get_current_version()

            if initial_version == self.expected_ver:
                self._log.info("\tThe initial version '" + initial_version + "' is already the expected version: "
                                                                             "Proceeding with the update")

            if start_workloads:
                self.summary_log.info("\tStart workloads: " + str(start_workloads))
                self._log.info("\tStarting workloads, wait two minutes till workloads stabilize...")
                self.begin_workloads()

            time_start = datetime.now()
            self._log.info("\tSending capsule image")
            self.summary_log.info("Sending capsule '" + path + "'")
            self.stage_inband_capsule_update_parallel(path, capsule_path2)
            self.time_staging = datetime.now() - time_start
            self._log.info("\t\tDone with staging. Approx time was " + str(self.time_staging))
            post_version, errors = self.block_until_complete(initial_version, update_type)

            if capsule_type == 'negative':
                if post_version == initial_version:
                    self._log.info("\t\tThe version {} is expected version {}".format(post_version, initial_version))
                    self._log.info("ERRORS ARE EXPECTED AS WE ARE UPDATING THE BAD CAPSULE.")
                    result, errors = True, False
                    return result and not errors
            elif not errors and self.skip_reset:
                if post_version == initial_version:
                    self._log.info("\t\tThe version {} is expected version {}".format(post_version, initial_version))
                    result = True
                    return result
            if not post_version == self.expected_ver:
                self._log.error(
                    "\tThe version {} is not the expected version {}".format(post_version, self.expected_ver))
                result = False
            elif post_version == 'NONE':
                self.summary_log.error("Failed to detect version: reboot system or flash bios image")
                self._log.error("\tFailed to detect version: reboot system or flash bios image")
            else:
                self._log.info(
                    "\t\tThe version '" + post_version + "' is expected version '" + self.expected_ver + "'")
                if self.warm_reset and self.workloads_started:
                    self.begin_workloads()
                self._log.info("\tChecking post-update conditions")
                result = self.examine_post_update_conditions(update_type)
                self._log.info("\tPost update conditions checked")
                if capsule_type == 'negative' and errors == True:
                    self._log.info("ERRORS ARE EXPECTED AS WE ARE UPDATING THE BAD CAPSULE.")
                    result, errors = True, False

        except Exception as e:
            self._log.exception(e)

        if self.workloads_started:
            self._log.info('\tStopping workloads')
            wl_output = self.stop_workloads()
            self._log.error("Evaluating workload output")
            if not self.evaluate_workload_output(wl_output):
                result = False

        return result and not errors

    def stage_inband_capsule_update(self, path):
        """
        Pushes a Capsule Update to the SUT using in-band methods.
        :param path: Path to Capsule File
        """
        if self._os_type == "Linux":
            # Send Capsule to SUT
            filename = ntpath.basename(path)  # Assumes NUC is Windows-based. Might be wise to check this.
            # self.pscp_send_file_to_sut(path, "/tmp/" + filename, self._os_user, self._os_pass, self._os_ip)
            self.sut_ssh.copy_local_file_to_sut(path, "/tmp/" + filename)
            self.run_ssh_command("sudo cat /tmp/" + filename + " > /dev/efi_capsule_loader", True, 60)
            time.sleep(10)  # Wait to make sure Capsule takes.
        else:
            raise NotImplementedError("This function is not yet enabled for non-Linux usage.")

    def stage_inband_capsule_update_parallel(self, path, path2):
        """
        Pushes a Capsule Update to the SUT using in-band methods.
        :param path: Path to Capsule File
        """
        if self._os_type == "Linux":
            # Send Capsule to SUT
            filename = ntpath.basename(path)  # Assumes NUC is Windows-based. Might be wise to check this.
            filename2 = ntpath.basename(path2)
            # self.pscp_send_file_to_sut(path, "/tmp/" + filename, self._os_user, self._os_pass, self._os_ip)
            self.sut_ssh.copy_local_file_to_sut(path, "/tmp/" + filename)
            self.sut_ssh.copy_local_file_to_sut(path2, "/tmp/" + filename2)
            t1 = threading.Thread(target=self.run_ssh_command,
                                  kwargs=dict(command="sudo cat /tmp/" + filename + " > /dev/efi_capsule_loader",
                                              log_output=True, timeout_seconds=60))
            t2 = threading.Thread(target=self.run_ssh_command,
                                  kwargs=dict(command="sudo cat /tmp/" + filename2 + " > /dev/efi_capsule_loader",
                                              log_output=True,
                                              timeout_seconds=60))
            t1.start()
            time.sleep(1)
            t2.start()
            # self.run_ssh_command("sudo cat /tmp/" + filename + " > /dev/efi_capsule_loader", True, 60)
            time.sleep(10)  # Wait to make sure Capsule takes.
        else:
            raise NotImplementedError("This function is not yet enabled for non-Linux usage.")

    def pscp_send_file_to_sut(self, source, dest, user, pw, ip):
        """
        Sends a file to the SUT using PSCP.
        :param source: Source file path.
        :type source: str
        :param dest: Destination file path.
        :type dest: str
        :param user: Username of SUT account.
        :type user: str
        :param pw: Password of SUT account.
        :type pw: str
        :param ip: SUT IP or URL.
        :type ip: str
        :return: PSCP Result
        """
        self._log.info("Copying %s from HOST to SUT at %s", source, dest)
        copy_cmd = "pscp -batch -pw \"" + pw + "\" \"" + source + "\" " + user + "@" + ip + ":" + dest
        copy_cmd.replace("\\", "\\\\")
        result = self.run_powershell_command(copy_cmd)
        return result

    # def start_powershell(self):
    #     """
    #     Start remote powershell on SUT
    #     """
    #     if self.powershell is None:
    #         self._log.info("\tStarting powershell")
    #         self.powershell = Popen(["powershell"], stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def run_powershell_command(self, command, get_output=False, echo_output=True):
        """
        Run command on remote powershell of SUT
        :param command: command to be executed
        :param get_output: True if read output from remote powershell
        :param echo_output: True if print output to host console
        :return output: command output
        """
        cmd = ["powershell"]
        self.summary_log.info("Starting powershell command: {}".format(self.credential_censoring(command)))
        command = command.split()
        cmd.extend(command)
        self.powershell = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output = ""
        if get_output:
            DONE_TRIGGER = "remote powershell complete"
            while True:
                line = self.powershell.stdout.readline()
                line = line.decode("utf-8", errors='ignore')
                if not line:
                    break
                output = output + line.rstrip() + '\n'
                # output = output + str(line)

                if self._os_pass in line:
                    line = self.credential_censoring(line)

                if echo_output:
                    self.summary_log.info(line.rstrip())

                if DONE_TRIGGER in line:
                    break
        return output

    def start_VM(self):
        """
        Restore VMs
        """
        self._log.info("Starting the VMs")
        self.run_powershell_command(command=self.start_vm_command, get_output=True)

    def stop_VM(self):
        """
        Stopping the  VMs
        """
        self._log.info("Stopping the VMs")
        self.run_powershell_command(command=self.stop_vm_command, get_output=True)

    def make_inventory_xml(self, versions, strings=None, numbers=None):
        """
        Converts a pile of Dicts of Inventory objects to an XML block that can then be written to file.
        :param versions: Version Inventory Dict. Key being component, Value being version.
        :type versions: dict
        :param strings: String Value Dict.
        :type strings: dict
        :param numbers: Number Value Dict.
        :type numbers: dict
        :rtype: str
        """
        out = "<component_meta>\n\t<configuration>\n"

        for key, value in versions.items():
            out += "\t\t<version name=\"{0}\" value=\"{1}\"/>\n".format(key, value)

        if strings is not None:
            for key, value in strings.items():
                out += "\t\t<string name=\"{0}\" value=\"{1}\"/>\n".format(key, value)

        if numbers is not None:
            for key, value in numbers.items():
                out += "\t\t<number name=\"{0}\" value=\"{1}\"/>\n".format(key, value)

        out += "\t</configuration>\n</component_meta>"

        return out

    def build_inventory_xml(self):
        """
        Creates the Inventory XML files from the SUT that are required by OrchestratorValidator to check if an update
        for Orchestrator is valid.
        """
        xml = self.get_inventory_xml()
        self.orchestrator_xml = os.path.join(self._inventory_xml_path, "inventory.xml")

        # Ensure "inventory" directory exists
        if not os.path.exists(self._inventory_xml_path):
            os.makedirs(self._inventory_xml_path)

        # Write out XML stuff
        f = open(self.orchestrator_xml, "w")
        f.write(xml)
        f.close()

    def get_inventory_xml(self):
        """
        Retrieves the Inventory XML for component versions pulled from the BMC first, falling back to the OS if
        unavailable. Required for OrchestratorValidator checking.
        """

        try:
            bmc = self._bmc_redfish.get_bmc_version()
        except RuntimeError:
            bmc = self._bmc_ipmi.get_bmc_version()

        try:
            bios = self._bmc_redfish.get_bmc_bios_version()
        except RuntimeError:
            bios = self.get_bios_ver(False)

        sps_info = self.get_sps_ver(False, False)

        versions = {
            "INTEL_ME_OPR": sps_info["Operational"],
            "INTEL_ME_RECV": sps_info["Recovery"],
            "INTEL_ME_HECI": sps_info["HECI"],
            "INTEL_BMC": bmc,
            "INTEL_BIOS": bios,
            "INTEL_CPLD": self._bmc_redfish.get_bmc_cpld_version()
        }

        strings = {
            "INTEL_PLATFORM": self.get_platform_name_from_bmc()
        }

        numbers = {
            "INTEL_ME_SVN": sps_info["SVN"],
            "INTEL_ME_OPR_SVN": sps_info["SVN"],
            "INTEL_ME_RCV_SVN": sps_info["SVN"],
            "INTEL_ME_ACTIVE_SVN": sps_info["SVN"],
            "INTEL_MCU": self.get_ucode_ver(False)
        }

        return self.make_inventory_xml(versions, strings, numbers)

    def validate_for_orchestrator(self, capsule_xml, *settings_xmls):
        """
        Runs the OrchestratorValidator to check if the given Capsule XML and compiled Settings XML files are ready
        for execution.
        :param capsule_xml: Path to Capsule XML file.
        :type capsule_xml: str
        :param settings_xmls: All Inventory XML files to check against Capsule requirements.
        :type settings_xmls: varargs
        """
        # Build arguments list
        args = ""
        for arg in settings_xmls:
            args += "\"" + arg + "\" "

        callstr = "py \"{0}\" {1} \"{2}\"".format(self._orchestator_validator_path, args, capsule_xml)
        return subprocess.call(callstr) == 0

    def run_orchestrator_validation(self, capsule_xml):
        """
        Calls all of the OrchestratorValidator stuff for a validation run.
        :param capsule_xml: Path to Capsule XML file.
        :type capsule_xml: str
        :return: True if validation is successful.
        """
        self._log.info("\tCompiling Inventory XML files for Orchestrator...")
        self.build_inventory_xml()

        self._log.info("\tValidating Inventory XML against Capsule XML via OrchestratorValidator...")

        # Verify XML file inputs
        if capsule_xml is None or capsule_xml == "" or not os.path.exists(capsule_xml):
            err = "ERROR: No valid Capsule XML file given! Define a valid file with \"--capsule_xml\"."
            self.summary_log.error(err)
            raise IOError(err)

        if self.orchestrator_xml is None or self.orchestrator_xml == "" or not os.path.exists(self.orchestrator_xml):
            err = "ERROR: Could not generate Inventory XML file!"
            self.summary_log.error(err)
            raise IOError(err)

        # Actually run OrchestratorValidator
        if self.validate_for_orchestrator(capsule_xml, self.orchestrator_xml):
            self.summary_log.info("\tOrchestrator Validation passed.")
            return True
        else:
            self.summary_log.error("\tOrchestrator Validation failed!")
            return False

    def get_efi_var(self, name):
        """
        Runs the efivar utility and dumps the named variable's data into an array. Currently Linux-only.
        :param name: Variable name.
        :type name: str
        :return: Array of bytes from the given efivar.
        :rtype: dict
        """
        if self._os_type == OperatingSystems.LINUX:
            cmd = "efivar -n {} -d".format(name)
            varbytes = list(filter(None, self.run_ssh_command(cmd).stdout[:-1].split(" ")))

            # Convert to Ints
            for i in range(0, len(varbytes)):
                varbytes[i] = int(varbytes[i])
        else:
            raise NotImplementedError("This function doesn't yet work outside of Linux.")

        return varbytes

    def get_int_from_efi_var(self, efivar, offset_start, offset_end=None):
        """
        Gets a number from the byte array retrieved from get_efi_var(), based on the given offset range.
        :param efivar: Array of bytes from get_efi_var().
        :type efivar: dict
        :param offset_start: Starting offset to begin building integer from.
        :type offset_start: int
        :param offset_end: Ending offset to scan to when building integer.
        :type offset_end: int
        :return: Built integer.
        :rtype: int
        """
        if offset_end is None:
            offset_end = offset_start

        out = 0
        bit_offset = offset_end - offset_start
        for i in range(offset_start, offset_end + 1):
            out += efivar[i] << bit_offset * 8
            bit_offset -= 1

        return out

    def esrt_check(self):
        """
        Runs the ESRT Check against the SUT. Dumps errors to log.

        :return: Success.
        :rtype: bool
        """

        persist_across_reset = 0b0001  # 0x01
        populate_system_table = 0b0010  # 0x02
        initiate_reset = 0b0100  # 0x04

        efivar = self.get_efi_var("b122a263-3661-4f68-9929-78f8b0d62180-EfiSystemResourceTable")
        last_attempt_status = self.get_int_from_efi_var(efivar, 0x34, 0x37)
        capsuleflags = self.get_int_from_efi_var(efivar, 0x2D)

        self._log.info("Last Attempt Status: " + hex(last_attempt_status))
        self._log.info("CapsuleFlags: " + hex(capsuleflags))

        result = True

        if last_attempt_status != 0:
            self.summary_log.info(
                "ESRT Check Fail: LastAttemptStatus reported " + hex(last_attempt_status) + "!")
            result = False

        if capsuleflags & persist_across_reset != 0:
            self.summary_log.info("ESRT Check Fail: CapsuleFlag PERSIST_ACROSS_RESET detected!")
            result = False

        if capsuleflags & populate_system_table != 0:
            self.summary_log.info("ESRT Check Fail: CapsuleFlag POPULATE_SYSTEM_TABLE detected!")
            result = False

        if capsuleflags & initiate_reset != 0:
            self.summary.info("ESRT Check Fail: CapsuleFlag INITIATE_RESET detected!")
            result = False

        self.summary_log.info("ESRT Check: " + ("PASSED" if result else "FAILED"))
        return result

    def begin_workloads(self):
        """
        Launch workloads within VMs through Windows agent
        """
        if self._os_type != OperatingSystems.WINDOWS:
            self._log.info("OS not Windows --Start_workload")
            return
        self.start_VM()
        time.sleep(30)
        if len(self.start_workload_command) == 0:
            return
        self.workloads_started = True
        if hasattr(self, 'start_network_workload') and self.start_network_workload:
            self.start_workload_command += " -network_workload $true"

            self._log.info("Starting network workload on SUT: " + self.censored_command(self.start_workload_command))
        self._log.info("{}".format(self.start_workload_command))
        result = self.run_powershell_command(command=self.start_workload_command, get_output=True)
        self._log.info("{}".format(result))
        self._log.info("Waiting for two minutes till workloads stabilize")
        time.sleep(120)

    def begin_workloads_lin(self, cmd=None):
        """
        Launch workloads and send capsule on Linux machine
        """
        try:
            if self._os_type == OperatingSystems.LINUX:
                self._log.info("OS is Linux --Start_workload")
                self.access_permission()
                self.workloads_started = True
                if cmd:
                    start_load = threading.Thread(target=self.workload_lin, args=(cmd,))
                else:
                    start_load = threading.Thread(target=self.workload_lin)
                self._log.info("=========INITIATING WORKLOAD===========\n")
                start_load.start()
                self._log.info("Waiting for some seconds for stabilizing workload..")
                time.sleep(self.SUT_SETTLING_TIME)
            else:
                self._log.info("OS detected is not Linux..!!")
                return False
        except Exception as e:
            self._log.exception(e)

    def stop_workloads_lin(self):
        cmd1 = "killall fio"
        cmd2 = "ps -ef | grep fio"
        try:
            self._log.info("Stopping workload for RHEL")
            self.run_ssh_command(command=cmd1, timeout_seconds=30)
            time.sleep(2)
            self.run_ssh_command(command=cmd2, timeout_seconds=30)

        except Exception as e:
            self._log.exception(e)

    def stop_workloads(self):
        """
        Stop workloads within VMs through Windows agent
        """
        if not self.workloads_started or len(self.stop_workload_command) == 0:
            return ""
        self.workloads_started = False
        if hasattr(self, 'start_network_workload') and self.start_network_workload:
            self.stop_workload_command += " -network_workload $true"
        self._log.info("Stopping workload on SUT: " + self.credential_censoring(self.stop_workload_command))
        output = self.run_powershell_command(command=self.stop_workload_command, get_output=True)
        return output

    def access_permission(self):
        if self._os_type != OperatingSystems.LINUX:
            return True
        else:
            cmd = "chmod 777 *"
            result = self.run_ssh_command(cmd)
            return result

    def workload_lin(self,
                     cmd="fio -filename=test_file -direct=1 -iodepth 256 -rw=read -ioengine=libaio -size=10G -numjobs=50 -name=fio_read"):
        if self._os_type == OperatingSystems.LINUX:
            result = self.run_ssh_command(cmd)
            output = result.stdout
            return output
        else:
            self._log.info("OS is not Linux")

    def boot_to_entery_Menu(self):
        self._log.info("Rebooting the SUT and entering into BIOS Entry Menu...")
        try:
            try:
                ret = self.os.execute("uname", self.SUT_SETTLING_TIME).stdout
                if "Linux" in ret:
                    self._log.info("Executing 'systemctl reboot' command...")
                    try:
                        self.os.execute("systemctl reboot", 30)
                    except Exception as e:
                        self._log.error('{}'.format(e))
                    time.sleep(30)
                    if self.os.is_alive():
                        self._log.error("Failed to Reboot the SUT, Exiting the process...!! ")
                        return False
                    else:
                        self._log.error("Reboot command executed successfully..!!")
                else:
                    self._log.info("Executing 'shutdown /r' command...")
                    try:
                        self.os.execute("shutdown /r", 30)
                    except Exception as e:
                        self._log.error('{}'.format(e))
                    time.sleep(40)
                    if self.os.is_alive():
                        self._log.error("Failed to Reboot the SUT, Executing the process...!! ")
                        return False
                    else:
                        self._log.error("Reboot command executed successfully...!! ")
            except Exception as e:
                self._log.error('{}'.format(e))
                return False
            self._log.info("Waiting for the BIOS Entry Menu...")
            if self.setupmenu.wait_for_entry_menu(800):
                f2_state = self.setupmenu.press(r'F2')
                time.sleep(0.3)
                if f2_state:
                    self._log.info("Entry Menu detected")
                    ret = self.setupmenu.wait_for_bios_setup_menu(60)
                    ret_page = self.setupmenu.get_page_information()
                    self._log.info("====== Entry Menu Page Info ======")
                    self._log.info('{}'.format(ret_page.result_value))
                    return (ret_page.result_value)
                else:
                    self._log.error("Failed to detect 'BIOS Entry Menu'..!!")
                    return False
            else:
                self._log.error("Failed to enter into 'BIOS Entry Menu'..!! ")
                return False
        except Exception as e:
            self._log.error('{}'.format(e))
            return False

    def bios_navigation_to_page(self, bios_path):
        ret = self.boot_to_entery_Menu()
        total_memory = None
        if ret:
            path = bios_path.split(',')
            try:
                for i in range(len(path)):
                    time.sleep(10)
                    ret = self.setupmenu.get_page_information()
                    ret = self.setupmenu.select(str(path[i]), None, 60, True)
                    self._log.info(self.setupmenu.get_selected_item().return_code)
                    self.setupmenu.enter_selected_item(ignore=False, timeout=10)
                    self._log.info("Entered into {0} ".format(path[i]))
                    time.sleep(5)
                    total_memory = self.setupmenu.get_current_screen_info()
                return total_memory
            except Exception as ex:
                self._log.error("{0} Issues Observed".format(ex))
                return False

    def get_logs(self, name, filename):
        """
        Create a logger object
        :param name:log name
        :param filename: log filename
        :return logger object
        """
        # Gets or creates a logger
        logger = logging.getLogger(name)

        # set log level
        logger.setLevel(logging.DEBUG)

        # set dir and file name
        log_dir_name = "C:/seamless-logs/"
        log_file_name = log_dir_name + filename + self.__class__.__name__ + datetime.now().strftime(
            "%Y-%m-%d_%H.%M") + ".log"
        if not os.path.exists(log_dir_name):
            os.makedirs(log_dir_name)

        # define file handler and set formatter
        file_handler = logging.FileHandler(log_file_name)
        # Define message format
        ptv_log_fmt = logging.Formatter(
            fmt='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p')
        file_handler.setFormatter(ptv_log_fmt)

        # add file handler to logger
        logger.addHandler(file_handler)

        return logger

    def get_Kpi_logs(self, name, filename):
        """
        Create a logger object
        :param name:log name
        :param filename: log filename
        :return logger object
        """
        # Gets or creates a logger
        logger = logging.getLogger(name)

        # set log level
        logger.setLevel(logging.DEBUG)

        # set dir and file name
        file = os.path.join(self.log_dir, "kpi_data.log")
        log_dir_name = file
        log_file_name = log_dir_name + filename + self.__class__.__name__ + datetime.now().strftime(
            "%Y-%m-%d_%H.%M") + ".log"
        # define file handler and set formatter
        file_handler = logging.FileHandler(log_file_name)
        # Define message format
        ptv_log_fmt = logging.Formatter(
            fmt='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p')
        file_handler.setFormatter(ptv_log_fmt)

        # add file handler to logger
        logger.addHandler(file_handler)

        return logger

    def get_test_summary(self, return_status):
        """
        Summarize test results with update durations in a separate log file
        :param return_status: test status pass or fail
        :return: log file
        """
        total_test_time = datetime.now() - self.time_start_test
        self._log.info("Test Summary:")
        self._log.info("\tTotal test execution time: " + str(total_test_time))
        self._log.info("\tTotal time for staging the capsule: " + str(self.time_staging))
        if self.warm_reset:
            self._log.info("\tActivation time for SUT to restart after update: " + str(self.time_activation))
        elif self.update_type == "efi_utility":
            pass
        else:
            self._log.info("\tVersion updated without system warm reset")
            self._log.info("\tActivation time without warm_reset: " + str(self.time_activation))
        if self.bmc_critical_errors:
            for each in self.bmc_critical_errors:
                self._log.info("BMC CRITICAL ERROR: " + str(each))
        if self.kpi_failed:
            self._log.info("KPI failed, please check logs")
        self._log.info("\tTest status: " + ("Test Passed" if return_status else "Test failed"))

    def prepare(self):
        """
        Create test summary logger object
        Check for command line arguments
        """
        super(SeamlessBaseTest, self).prepare()
        self.time_start_test = datetime.now()
        self._log.info(" \tCreating a log file to log data")
        self.summary_log = self.get_logs("Test Summary", "Test_Summary_")
        self.summary_log.info("Test Summary: ")

        self._log.info(" \tCreating a log file to log data of KPI")
        self.KPI_log = self.get_Kpi_logs("KPI Summary", "KPI_Summary_")
        self.KPI_log.info("KPI Log Summary: ")

        if not (self.sut_mode == "uefi" or self.sut_mode == "S5"):
            self.start_workloads = False
            # self.start_powershell()
            self.get_platform_config()
            self._log.info(' \tGet firmware versions prior to update:')
            self.get_pre_versions()

        if not hasattr(self, 'expected_ver'):
            raise RuntimeError("No expected version was specified")

        if not self.check_capsule_pre_conditions():
            raise RuntimeError("The condition pre-check of capsule has failed")

        try:
            self._common_content_lib.clear_all_os_error_logs()
        except RuntimeError as e:
            self._log.error("failed to clear the logs, error is %s", str(e))
        if self.os.os_type.lower() == OperatingSystems.LINUX.lower():
            self.os.execute("rm -rf /var/log/*", self._command_timeout)
        # try:
        #     download_tool_to_host("ipmi_C")
        #     with zipfile.ZipFile(path_zip_file_ipmi,'r') as zip_ref:
        #         zip_ref.extractall(path_unzip_file)
        # except RuntimeError as e:
        #     self._log.error("failed to download ipmitool")
        if self.bios_config_file_path:
            self._log.info("Loading default bios settings")
            self.bios_util.load_bios_defaults()
            self._log.info("Setting required bios settings")
            self.bios_util.set_bios_knob()
            # self.perform_graceful_g3()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        if self.bios_config_file_path:
            self._log.info("Verifying bios settings")
            self.bios_util.verify_bios_knob()

    def cleanup(self, return_status):
        super(SeamlessBaseTest, self).cleanup(return_status)
        if self.powershell is not None:
            self.run_powershell_command(command="exit")
            self.powershell.stdin.close()
            self._log.info("Waiting for powershell to exit")
            self.powershell.wait()
            self.powershell = None
        if return_status:
            self.get_test_summary(return_status)

    def verify_device_mount(self, device_name):
        """
        Function to verify mount the ssd

        :device_name: device name
        :return: mount path
        """
        cmd = "lsblk | grep {}p".format(device_name)
        result = self.run_ssh_command(cmd, True)
        if result != "":
            res = re.findall(f"{device_name}p\d", result.stdout)
            res2 = re.findall("/[a-z]+[a-z]+[a-z]/", result.stdout)
            if not res2:
                return False
        else:
            self._log.info("Unable to find the partition")
            return False
        if len(res) != 1:
            self._log.info("More partition are present/No partition is present")
            return False
        else:
            return res[0]

    def mount_device(self, mount_device_part, device_name):
        """
        This function will mount ssd hw

        :mount_device_part: ssd device partition
        :device_name: ssd device name
        """
        try:
            cmd = "umount /mnt/{}".format(device_name)
            self.run_ssh_command(cmd)
            cmd = "cd /mnt && ls"
            result = self.run_ssh_command(cmd)
            if mount_device_part not in result.stdout:
                cmd = "mkdir /mnt/{}".format(device_name)
                self.run_ssh_command(cmd)
            cmd = "mount {} /mnt/{}".format(mount_device_part, device_name)
            self.run_ssh_command(cmd)

        except Exception as ex:
            self._log.error("{} Issues Observed".format(ex))
            raise RuntimeError("Unable to mount ssd")

    def copy_vm_file(self, artifactory_link, source="/root", destination="/mnt/nvme0n1", file_name="centos8.qcow2"):
        """
        copying the vm file to nvme device
        if not exist it copy from hdd to nvme device
        if not exist in hdd it will download from artifactory to hdd

        :source: sut source path
        :destination: mount path
        :file_name: vm os file name
        """
        cmd = 'cd {} && ls'.format(destination)
        result = self.run_ssh_command(cmd, False)
        if file_name not in result.stdout:
            cmd2 = 'cd {} && ls'.format(source)
            result2 = self.run_ssh_command(cmd2, False)
            if file_name not in result2.stdout:
                cmd3 = 'cd {} && wget {}'.format(source, artifactory_link)
                self.run_ssh_command(cmd3)
                cmd = 'cd {} && ls'.format(source)
                result = self.run_ssh_command(cmd, False)
                if file_name not in result.stdout:
                    raise RuntimeError("Unable to download {}".format(file_name))
            cmd4 = "cd {} && cp {} {}".format(source, file_name, destination)
            result4 = self.run_ssh_command(cmd4, False)
            if result4.stderr != "":
                raise RuntimeError("Unable to copy {} to {}".format(file_name, destination))
            cmd = 'cd {} && ls'.format(destination)
            result = self.run_ssh_command(cmd, False)
            if file_name not in result.stdout:
                raise RuntimeError("Unable to download {}".format(file_name))

    def vm_installation_linux(self, destination="/mnt/nvme0n1", file_name="centos8.qcow2",
                              server_name="CentOS_8_Server"):
        """
        This function will install vm

        :destination: mount path
        :file_name: vm os file name
        :server_name: vm name
        """
        vm_cmd = f"virt-install --name {server_name} --memory 4096 --vcpus 2 --disk {destination}/{file_name},bus=sata --import --os-variant centos8 --network default"
        self.sut_ssh.execute_async(vm_cmd)

    def run_vm_linux(self, server_name):
        """
        Function to run vm

        :server_name; VM server name
        """
        vm_cmd = f"virsh --connect qemu:///system start {server_name}"
        result_vm = self.run_ssh_command(vm_cmd)
        if result_vm.stderr:
            if "Domain is already active" not in result_vm.stderr:
                raise RuntimeError(f"Unable to run the VM {result_vm.stderr}")

    def verify_vm(self, server_name):
        """
        Function to verify the status of VM
        :server_name: VM server name
        :return: True if VM is running
        """
        if self._os_type != OperatingSystems.WINDOWS:
            vm_cmd = "virsh list"
            result_vm = self.run_ssh_command(vm_cmd)
            for line in result_vm.stdout.split('\n'):
                if server_name in line and "running" in line:
                    return True
            return False
        else:
            vm_state = self.run_ssh_command(SsdWindows.GET_VM_STATE.format(server_name))
            for line in vm_state.stdout.split('\n'):
                if server_name in line and "Running" in line:
                    self._log.info("Hyperv is running")
                    return True
            return False

    def stop_vm_linux(self, server_name):
        """
        Function to Stop vm

        :server_name; VM server name
        """
        vm_cmd = f"virsh shutdown {server_name}"
        result_vm = self.run_ssh_command(vm_cmd)
        if result_vm.stderr:
            if "domain is not running" not in result_vm.stderr:
                self._log.debug(f"Unable to stop the VM {result_vm.stderr}")
        if not self.verify_vm(server_name):
            self._log.debug("VM is stopped")

    def get_nvme_version(self):
        """
        this function will get the NVME version in the floating point version

        :return: nvme version
        """
        cmd = "nvme version"
        result = self.run_ssh_command(cmd)
        version = re.findall("\d+\.\d+", result.stdout)[0]
        return float(version)

    def install_fio(self):
        """
        This function will check and install the FIO tool
        """
        self._log.info("Installing the FIO Tool")
        # install fio
        result = self.sut_ssh.execute(r"fio --version", 60)
        self._log.info("Output of fio verion {}".format(result.stderr))
        if result.stderr:
            try:
                self.run_ssh_command("yum -y install fio")
            except Exception as ex:
                self._log.info("Exception while installing FIO {}".format(ex))
                self.setup_sut_proxy()
                self.run_ssh_command("yum -y install fio")
                result = self.sut_ssh.execute(r"fio --version", PmemLinux.TIMEOUT)
                if result.stderr:
                    raise RuntimeError("Unable to install FIO tool")
        else:
            self._log.info("FIO Tool is already installed")

    def create_namespace(self):

        """
        This function will create a new namespace
        """
        result = self.run_ssh_command(PmemLinux.NAMESPACE_LIST)
        self._log.info("Output for list of namespace {}".format(result.stdout))
        if result:
            self._log.info("Creating a Namespace")
            self.run_ssh_command(PmemLinux.CREATE_NAMESPACE)
        result2 = self.run_ssh_command(PmemLinux.NAMESPACE_LIST, PmemLinux.TIMEOUT)

        if result2.stdout:
            self._log.info("Output of fio verion {}".format(result2.stderr))
        else:
            self._log.info("Namespace creation failed")

    def del_namespace(self):
        """
        This function will delete all the namespaces which are exist
        """

        self.run_ssh_command(PmemLinux.DELETE_NAMESPACE)
        result1 = self.run_ssh_command(PmemLinux.NAMESPACE_LIST)
        if result1 == '':
            self._log.info("Deleted the name spaces sucessfully")
        else:
            self._log.info("Failed to delete namespace")

    def start_fio(self):
        """
        This function will start the Fio tool
        """
        result = self.run_ssh_command(PmemLinux.HARD_DISK_LIST)
        regex = re.findall(r"/*/pmem\d", result.stdout)
        self._log.info(regex)
        file_path = self.check_filepath_sut(PmemLinux.EZFIO_FOLDER, PmemLinux.EZFIO_FILE)
        base_dir = list(os.path.split(file_path))
        ezfio_path = base_dir[0]
        for i in regex:
            cmd = "cd {} && ./ezfio.py -d /dev{} -u 1 --yes".format(ezfio_path, i)
            self._log.info(cmd)
            self.os.execute_async(cmd)
            time.sleep(self.SUT_SETTLING_TIME)
        result = self.run_ssh_command(PmemLinux.RUNNING_ACTIVITY)
        if result.stdout == "":
            raise RuntimeError("Fio Tool has not started")
        else:
            self._log.info("output of a {}".format(result.stdout))

    def kill_fio(self):
        """
        This Function will kill the Fio tool
        """

        self.os.execute(PmemLinux.KILL_FIO,
                                   PmemLinux.TIMEOUT)
        result = self.run_ssh_command(PmemLinux.RUNNING_ACTIVITY)
        if result.stdout == "":
            self._log.info("killed the FIO tool")
        else:
            self.run_ssh_command(PmemLinux.KILL_EZFIO,
                                       PmemLinux.TIMEOUT)
            kill_fio_1 = self.run_ssh_command(PmemLinux.RUNNING_ACTIVITY)
            if kill_fio_1.stdout == "":
                self._log.info("killed the FIO tool")
            else:
                raise RuntimeError("Failed to kill FIO tool")

    def check_ezfio_tool(self):
        """
        This function will check if ezfio tool exists
        return: it return true if file exist
        """
        folder_name = list(os.path.split(PmemLinux.EZFIO_FOLDER))
        try:
            file_path = self.check_filepath_sut(PmemLinux.EZFIO_FOLDER, PmemLinux.EZFIO_FILE)
        except:
            self.copy_extract_file(source=self.ezfio_tool_path, destination=folder_name[0],
                                   extract_folder=folder_name[1])
            file_path = self.check_filepath_sut(PmemLinux.EZFIO_FOLDER, PmemLinux.EZFIO_FILE)
        base_dir = list(os.path.split(file_path))
        command = f"cd {base_dir[0]} && ls"
        output = self.run_ssh_command(command, timeout_seconds=PmemLinux.TIMEOUT)
        self._log.debug(f"EZFIO Tool DIR output : {output.stdout}")
        for file_name in PmemLinux.FIO_TOOL_CONTENT:
            if file_name in output.stdout:
                self._log.info(f"{file_name} is present")
            else:
                self._log.info(f"EZFIO TOOL is not present.{file_name} is missing from EZFIO tool")
                return False
        return True

    def setup_sut_proxy(self):
        """
        This function will do linux sut proxy settings
        """
        # Copy the repo file
        # if not self.sut_ssh.check_if_path_exists("/etc/yum.repos.d/test.repo"):
        #     #download_tool_to_host("Repo_L")
        #     #self.sut_ssh.copy_local_file_to_sut("/etc/yum.repos.d", "C:\Automation\Tools")
        result = self.run_ssh_command("cat /etc/yum.conf")
        self._log.info("output of yum.conf file {}".format(result.stdout))
        if ProxyConstants.PROXY_STR not in result.stdout:
            self.run_ssh_command(ProxyConstants.UPDATE_YUM_FILE.format(ProxyConstants.PROXY_STR))
            res = self.run_ssh_command("cat /etc/yum.conf")
            self._log.info("updated the yum conf file {}".format(res))
        # export commands
        self.run_ssh_command(ProxyConstants.EXPORT_HTTP)
        self.run_ssh_command(ProxyConstants.EXPORT_HTTPS)

    def get_iostat(self, device_name):
        """
        This function will check the iostat for ssd fw

        :device_name: SSD Disk name
        :return: List of iostat values
        """
        cmd = "iostat"
        result = self.run_ssh_command(cmd)
        if result.stderr:
            raise RuntimeError("Unable to run iostat")
        for line in result.stdout.split("\n"):
            if device_name in line.strip(" "):
                list = re.split('\s+', line)
                return list

    def bios_knob_change(self, bios_config_file):
        """
        This method will enable bios provide in the bios_config_file

        :bios_config_file: bios config file with required bios knobs for the test case
        """
        self._log.info("SETTING BIOS KNOB AS PER CONFIG FILE")
        self.bios_util.set_bios_knob(bios_config_file)
        self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)
        self._log.info("VERIFYING THE CHANGED BIOS KNOB")
        self.bios_util.verify_bios_knob(bios_config_file)

    def get_disk_drive_partition(self, device_caption, drive_letter):
        """
        This function will get ssd disk partition

        :device_caption: Device name/id
        :drive_letter: SSD Disk drive letter
        """
        regx_device_id = "PHYSICALDRIVE(\d)"
        physical_device_number = None
        self._log.info("Initiate disk drive partition")
        result = self.run_ssh_command(SsdWindows.WMIC_GET_DEVICEID)
        device_found = False
        for line in result.stdout.split("\n"):
            if device_caption in line:
                physical_device_number = re.search(regx_device_id, line)
                self._log.info("device number for partition {}".format(physical_device_number.group(1)))
                device_found = True
                break
        if not device_found:
            raise RuntimeError("SSD Device {} not found".format(device_caption))
        result = self.run_ssh_command(
            SsdWindows.PARTITION_DRIVE_CHECK.format(physical_device_number.group(1), drive_letter))
        if result.stdout == "":
            result = self.run_ssh_command(SsdWindows.DRIVE_CHECK.format(drive_letter))
            if result.stdout:
                raise RuntimeError("This Drive is already present, please provide different Drive Letter")
            clear_disk_result = self.run_ssh_command(SsdWindows.CLEAR_DISK_CMD.format(physical_device_number.group(1)))
            if clear_disk_result.stderr:
                raise RuntimeError("Unable to format the ssd drive with error {}".format(clear_disk_result.stderr))
            self.run_ssh_command(SsdWindows.INITIALIZE_CMD.format(physical_device_number.group(1)))
            result = self.run_ssh_command(
                SsdWindows.PARTITION_CMD.format(physical_device_number.group(1), drive_letter))
            if result.stderr:
                raise RuntimeError("Unable to partition with error {}".format(result.stderr))
        else:
            self._log.info("SSD already mounted with given drive letter {}".format(drive_letter))

    def create_hyper_v_windows(self, vm_name, os_path):
        """
        This function will create hyper V in windows SUT
        :vm_name: vm name
        :os_path: windows vhdx file location
        """
        self._log.info("Creating HyperV for windows")
        self.run_ssh_command(SsdWindows.CREATE_VM_CMD.format(vm_name, os_path))
        result = self.run_ssh_command(SsdWindows.GET_VM_CMD)
        reg_result = re.search(vm_name, result.stdout)
        if vm_name not in reg_result.group(0):
            raise RuntimeError("Hyper-V VM is not created on this SUT")
        self._log.info("Hyper-V Virtualization created successfully")

    def install_iometer(self, tool_path):
        """
        This function with installing IOmeter tool
        :tool_path: Host tool path from content_configuration file
        """
        folder_name = "IOMeter"
        find_cmd = "where /R {} {}"
        self._log.info("IOMeter tool installation started")
        iometer_tool_path = self.run_ssh_command(find_cmd.format(SsdWindows.C_DRIVE_PATH, SsdWindows.IOMETER_TOOL))
        if iometer_tool_path.stderr:
            self._log.info("IOmeter tool path error {}".format(iometer_tool_path.stderr))
            self.sut_ssh.copy_local_file_to_sut(tool_path, SsdWindows.C_DRIVE_PATH)
            zip_file_name = os.path.split(tool_path)[-1].strip()
            command_result = self.os.execute("mkdir {} && tar xf {} -C {}"
                                             .format(folder_name, zip_file_name, folder_name),
                                             timeout=60, cwd=SsdWindows.C_DRIVE_PATH)
            if command_result.cmd_failed():
                log_error = "failed to run the command 'mkdir && tar' with return value = '{}' and " \
                            "std error = '{}' ..".format(command_result.return_code, command_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)
            self._log.info("IOMeter tool is copied successfully")
            iometer_tool_path = self.run_ssh_command(find_cmd.format(SsdWindows.C_DRIVE_PATH, SsdWindows.IOMETER_TOOL))
            self._log.info("IOMeter tool path {}".format(iometer_tool_path.stdout))
        else:
            self._log.info("IOMeter tool is available in the SUT")
        self.os.execute_async(SsdWindows.EXECUTE_IOMETER_CMD, cwd=os.path.split(iometer_tool_path.stdout)[0])
        self._log.info("IOMeter tool installed/executed successfully")

    def check_iometer_status(self):
        """
        This function will check the iometer tool status
        """
        result = self.run_ssh_command(SsdWindows.IOMETER_STATUS)
        if "IOmeter.exe" not in result.stdout:
            raise RuntimeError("IOmeter tool is not running")
        self._log.info("IOmeter is running")

    def kill_iometer_tool(self):
        """
        This funciton kill the iometer tool
        """
        result = self.run_ssh_command(SsdWindows.IOMETER_KILL_CMD)
        if result.stderr:
            raise RuntimeError("Not able to kill IOmeter tool and find the below error \n {}".format(result.stderr))

    def start_hyperv_vm(self, win_vm_name):
        """
        This function will start the VM
        """
        self._log.info("Start the VM")
        result = self.run_ssh_command(SsdWindows.START_VM_CMD.format(win_vm_name))
        if "WARNING" in result.stdout:
            self._log.info("VM is already running state")

    def stop_hyperv_vm(self, win_vm_name):
        """
        This function will stop the VM
        """
        self._log.info("Stop the VM")
        result = self.run_ssh_command(SsdWindows.STOP_VM_CMD.format(win_vm_name))
        if "WARNING" in result.stdout:
            self._log.info("VM is already stopped state")

    def install_Iperf_server(self):
        self._log.info("Installing the IPERF Tool")
        # install IPERF TOOL
        result = self.sut_ssh.execute(r"iperf3 --version", 10)
        self._log.info("Output of IPERF version {}".format(result.stderr))
        if result.stderr:
            try:
                command = "yum update"
                self.sut_ssh.execute(cmd=command, timeout=20)
                self.run_ssh_command("yum install iperf3* -y")
            except Exception as ex:
                self._log.info("Exception while installing IPERF {}".format(ex))
                self.setup_sut_proxy()
                self.run_ssh_command("yum install iperf3* -y")
        else:
            self._log.info("IPERF Tool is already installed")

    def running_server(self):
        self._log.info("Starting the server !!")
        result = self.sut_ssh.execute_async(r"iperf3 -s")
        self._log.info("iperf result {}".format(result))
        self._log.info("Server Started")
        time.sleep(10)

    def install_iperf_win(self):
        self._log.info("Installing the IPERF Tool and making this as client")
        # install IPERF TOOL and making it as client configured
        # path to where the iperf.zip file is present navigate to that directory
        targetPattern = "C:\Automation\\tools\iperf*.zip"
        if (glob.glob(targetPattern)):
            self._log.info("IPERF installer zip file exists")
        else:
            self._log.info("IPERF installer zip file does not exists . Please download it")
            return False
        path = self._common_content_configuration.get_iperf_tool_path()
        self._log.info("File path {}".format(path))
        if os.path.isfile(path):
            self._log.info("File exists and is readable")
            with zipfile.ZipFile(path, "r") as zip_ref:
                tool_dir = os.path.split(path)[0].strip()
                zip_ref.extractall(tool_dir)
            chdir_path = path.replace(".zip", "")
            os.chdir(chdir_path)
            self._log.info("ip {}".format(self._os_ip))
            if not (os.system('start cmd /k "iperf3.exe -c {}'.format(self._os_ip))):
                self._log.info("client created successfully")
            else:
                self._log.info("server did not create")
        return True

    def reboot(self):
        if self._os_type != OperatingSystems.LINUX and not self.sut_ssh.is_alive():
            self.run_powershell_command(command=self.restart_sut_command, get_output=True)
        else:
            self._log.info("\tWarm reset through SSH")
            self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)
        self._log.info("Waiting for system to boot into OS..")
        self.os.wait_for_os(self.reboot_timeout)

    def dc_cycle(self):
        self.os.wait_for_os(self.reboot_timeout)
        self._log.info("Performing DC Power cycle")
        self._dc_power.dc_power_off()
        time.sleep(self.DC_POWER_DELAY)
        if self.os.is_alive():
            raise RuntimeError("Unable to dc power off the SUT")
        self._log.info("Connected back DC Power to the system, booting initiated..\n")
        self._dc_power.dc_power_on()
        self._log.info("Waiting for system to boot into OS..")
        self.os.wait_for_os(self.reboot_timeout)

    def ac_cycle(self):
        self._log.info("Performing Ac Power cycle")
        self._log.info("Removed Ac Power from the system..")
        self.ac_power.ac_power_off(self.AC_POWER_DELAY)
        time.sleep(self.AC_POWER_DELAY)
        if self.os.is_alive():
            raise RuntimeError("Unable to ac power off the SUT")
        self._log.info("Connected back Ac Power to the system, booting initiated..\n")
        self.ac_power.ac_power_on(self.AC_POWER_DELAY)
        self._log.info("Waiting for system to boot into OS..")
        self.os.wait_for_os(self.reboot_timeout)

    def check_filepath_sut(self, find_path, file_name):
        """
            This Function will find the full file path of the file.
            find_path: initial folder where file need to be checked
            file_name: file name which need to be search

            return: full path of the file
        """
        if self._os_type == OperatingSystems.LINUX:
            cmd = "find {} -name {}".format(find_path, file_name)
        else:
            cmd = "where /R {} {}".format(find_path, file_name)
        result = self.run_ssh_command(cmd)
        if result.stderr:
            if self._os_type == OperatingSystems.LINUX:
                raise RuntimeError("Unable to get the {} folder list with the error \n{}".format(find_path, result.stderr))
        if result.stdout:
            result2 = result.stdout.split("\n")
            for list1 in result2:
                if file_name in list1:
                    return list1
                    break
            return False
        else:
            return False

    def copy_extract_file(self, source, destination, extract_folder):
        """
            Function to check copy and extract file
            source: zip file path in host
            destination: folder path to extract
        """
        file_name = source.split('\\')[-1]
        try:
            self.sut_ssh.copy_local_file_to_sut(source, destination)
        except Exception as e:
            raise RuntimeError("Unable to copy the file with the below error \n",e)
        if self._os_type == OperatingSystems.WINDOWS:
            cmd = r"cd {} && tar xvzf {} -C {}".format(destination, file_name, extract_folder)
        else:
            cmd = r"cd {} && unzip {} -d {}".format(destination, file_name, extract_folder)
        self.run_ssh_command("cd {} && mkdir {}".format(destination, extract_folder))
        result = self.run_ssh_command(cmd)
        if self._os_type == OperatingSystems.LINUX:
            if result.stderr:
                raise RuntimeError("Unable to extract the {} file  with the error \n".format(source, result.stderr))

    def dsa_worload(self):
        """
           This function will call the DSA workload
           which can be used along with the PMEM firmware update
        """
        destination_path = self.dsa_sut_path
        dsa_timeout = self.timeout.dsa
        sh_cmd = '"end=\$((SECONDS+{}))\\nwhile [ \$SECONDS -lt \$end ]; do ./Setup_Randomize_DSA_Conf.sh -o 0x3 ; done"'.format(dsa_timeout)
        dsa_file_name = self.dsa_file_name_pmem
        self._log.info("Waiting for the SUT to boot to OS")
        alive = self.sut_ssh.is_alive()
        self._log.info("SUT is alive: {}".format(alive))
        if alive == False:
            raise RuntimeError('SUT is Offline or Unreachable')
        if self._os_type == OperatingSystems.LINUX:
            self._log.info("\t Verying the OS type")
            command = "lsmod  | grep idxd"
            result_ssh = self.sut_ssh.execute(cmd=command, timeout=10)
            self.summary_log.error("System and Application Error logs: ")
            self.summary_log.error('\n' + result_ssh.stdout)
            folder_name = "dsa_tool"
            self.run_ssh_command("rm -rf {}".format(folder_name))
            self.run_ssh_command("mkdir {}".format(folder_name))
            file_path = os.path.join(destination_path, folder_name)
            self.copy_extract_file(self.dsa_windows_zip, file_path, dsa_file_name)
            folder_name_1 = dsa_file_name + "/" + dsa_file_name
            cmd2 = "cd {}/{} && ./Setup_Randomize_DSA_Conf.sh -ua".format(file_path, folder_name_1)
            res2 = self.run_ssh_command(cmd2)
            if res2.stderr:
                raise RuntimeError("Unable to run the file {}".format(res2.stderr))
            file_path = destination_path + folder_name + "/" + folder_name_1
            cmd4 = "cd {} && printf {} > dsa_cmd.sh".format(file_path, sh_cmd)
            self.run_ssh_command(cmd4)
            access_cmd = "cd {} && chmod u+r+x dsa_cmd.sh".format(file_path)
            self.run_ssh_command(access_cmd)
            cmd3 = "cd {} && ./dsa_cmd.sh".format(file_path)
            self.os.execute_async(cmd3)
