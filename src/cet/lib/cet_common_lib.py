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


# add import statements
import os
import re
import time
import paramiko

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.console_log import ConsoleLogProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from configparser import ConfigParser


class CETCommon(BaseTestCase):
    """
    This Class is Used as Common Class For all the Pcie Test Cases

    """

    SET_CET_REGISTER_GLOBAL = 'reg add "HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\Control\SessionManager\Kernel" /v {} /t REG_BINARY /d "000000000000000000000000000000{}00000000000000000" /f'

    SET_CET_REGISTER_PER_PROGRAM = 'reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{}" /v {} /t REG_BINARY /d "000000000000000000000000000000{}00000000000000000" /f'

    GET_REGISTER_VALUE = r'powershell -command "Get-ItemPropertyValue {} -Name {}"'

    PER_PROGRAM_PATH = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\\{}"
    GLOBAL_PATH = "HKLM:\SYSTEM\ControlSet001\Control\SessionManager\Kernel"

    CET_GLOBAL_ENABLE_BITS = {"MitigationOption_bit": 3, "MitigationAuditOption_bit": 0}
    CET_GLOBAL_DISABLE_BITS = {"MitigationOption_bit": 2, "MitigationAuditOption_bit": 0}

    CET_COMMON_MIT_OPT = "MitigationOptions"
    CET_COMMON_MIT_AUDIT_OPT = "MitigationAuditOptions"

    SHADOWSTACK_RECURSE = "shadowstack.exe -ss_recurse"
    SHADOWSTACK_MISMATCHED_RET = "shadowstack.exe -ss_mismatched_ret"
    CET_ENABLE_STRICT_MODE = "runcetss.bat shadowstack -3"
    CET_ENABLE_AUDIT_MODE = "runcetss.bat shadowstack -a"
    CET_ENABLE_ENFORCEMENT_MODE = "runcetss.bat shadowstack -e"

    CET_FOLDER_NAME = "CET_20210419_"
    CET_QUICKTEST_PATH = "\CET_20210419_\CET\CETQuickTest\{}"
    CET_SIGMATEST_PATH = "\CET_20210419_\CET\SigmaTest\{}"
    CET_TEST_PATH = r"\CET_20210419_\CET\CETTest/rs_prerelease-20206.1000.200828-1431\CETTest\CETTest.exe"
    SPEC_TEST_PATH = r'\CET_20210419_\CET\CETQuickTest\shadowstack.exe -ss_spec_test'
    CET_TEST_INFINITE_LOOP_PATH = '\CET_20210419_\CET\CET.bat'

    CLEAR_EVENT_LOG_CMD = 'powershell -command "Get-EventLog -LogName * | ForEach {Clear-EventLog $_.Log}"'
    CHECK_EVENT_LOG_CMD = 'powershell -command "Get-EventLog -LogName Application -EntryType Error"'
    DEFAULT_DIR = r'C:\Users\Administrator\Desktop'

    WORDPAD_CMD = 'powershell.exe Set-Content -Path \'{}\' -Value \'{}\'; $content = Get-Content -Path \'{}\'; echo $content ;' \
                  '$newContent = $content -replace \'Lorem\', \'bar\'; echo $newContent; Set-Content -Path \'{}\' -Value $newContent'
    REMOVE_FILE_CMD = r'powershell.exe Remove-Item -Path {}'
    GET_VM_CMD = "powershell.exe Get-VM -Name '{}'"
    START_VM_CMD = "powershell.exe Start-VM -Name '{}'"
    SUSPEND_VM_CMD = "powershell.exe Suspend-VM -Name '{}'"
    RESUME_VM_CMD = "powershell.exe Resume-VM -Name '{}'"
    SHADOWSTACK_KILL_CMD = "TASKKILL /F /IM shadowstack.exe /T"
    BCD_EDIT_CMD = r'powershell.exe "bcdedit /set nointegritychecks true ; bcdedit /set testsigning on"'
    SIGMA_TEST_CMD = r"cd C:\Users\Administrator\Desktop\CET_20210419_\CET\SigmaTest && SigmaApp.exe 0xf 0x8ff 1000"
    SORT_SIGMA_TEST_OUTPUT_FILES_CMD = r'powershell -command "cd C:\Users\Administrator\Desktop\CET_20210419_\CET\SigmaTest ; ' \
                                       r'$latestfile = Get-ChildItem -Attributes !Directory *.txt ' \
                                       r'| Sort-Object -Descending -Property LastWriteTime | select -First 3 ; $latestfile.Name"'
    STRESS_WAIT_TIME = 7200
    WINDOWS_GEN1_LEVEL1_VM = 'Windows Gen1 L1A'
    WINDOWS_GEN1_LEVEL2_VM = 'Windows Gen1 L2A'
    WINDOWS_GEN2_LEVEL1_VM = 'Windows L1A'
    WINDOWS_GEN2_LEVEL2_VM = 'Windows L2A'
    LINUX_LEVEL1_VM = 'Linux VM'
    ROOT = 'SUT'

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CETCommonLib.

        """
        super(CETCommon, self).__init__(test_log, arguments, cfg_opts, )

        self._cfg = cfg_opts
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(
            sut_os_cfg, test_log)  # type: SutOsProvider
        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_obj = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider

        if not self._os.is_alive():
            self._log.error("System is not alive, wait for the sut online")
            self.perform_graceful_g3()  # To make the system alive

        if not self._os.is_alive():
            self._log.error("System is not alive")
            raise content_exceptions.TestFail("System is not alive")

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        cng_cfg = cfg_opts.find(ConsoleLogProvider.DEFAULT_CONFIG_PATH)
        self.cng_log = ProviderFactory.create(cng_cfg, self._log)
        self.log_dir = self._common_content_lib.get_log_file_dir()
        self.serial_log_dir = os.path.join(self.log_dir, "serial_logs")
        if not os.path.exists(self.serial_log_dir):
            os.makedirs(self.serial_log_dir)

    def check_os_type(self):
        """This program will check if the os is windows
        raise exception otherwise"""

        if self._os.os_type == "Windows":
            self._log.error("Windows Operating System")
            return True
        else:
            self._log.error("Operating System Not Windows")
            raise RuntimeError("Failed to run command '{}'".format(self.COLD_RESET_CMD))

    def clear_event_log(self):
        """This program will clear all event logs"""
        self._log.info("Clearing Event Viewer")
        self._os.execute(self.CLEAR_EVENT_LOG_CMD, self._command_timeout)

    def check_shadowstack_event_log(self, input):
        """This program will retrive event log information and check if Error 1000 exists"""
        if input == '':
            self._log.info("Checking Event Viewer")
            event_log_info = (self._os.execute(self.CHECK_EVENT_LOG_CMD, self._command_timeout)).stdout
        else:
            event_log_info = input

        temp = re.findall(r"Application Error.*\d+", str(event_log_info))
        res = temp[0].strip("Application Error            ")

        error_id = int(res)

        self._log.info("Error id: {}".format(error_id))
        return int(error_id)

    def search_folder_directory(self, fileName):
        """this function will search the directory for CET folder"""

        dir_line = (
            self._os.execute('dir /s *{}* | findstr "Directory.*"'.format(fileName), self._command_timeout)).stdout
        # self._log.info(dir_line)
        dir = dir_line.split(" ")
        direc = dir[len(dir) - 1]

        return direc.rstrip()

    def set_cet_global(self, type: str):
        """This program will set CET globally"""

        if type == "Enable":
            mit_opt = self.CET_GLOBAL_ENABLE_BITS["MitigationOption_bit"]
            mit_audit_opt = self.CET_GLOBAL_ENABLE_BITS["MitigationAuditOption_bit"]
        elif type == "Disable":
            mit_opt = self.CET_GLOBAL_DISABLE_BITS["MitigationOption_bit"]
            mit_audit_opt = self.CET_GLOBAL_DISABLE_BITS["MitigationAuditOption_bit"]

        self._log.info(mit_opt)
        self._log.info(mit_audit_opt)

        set_mitigation = self.SET_CET_REGISTER_GLOBAL.format(self.CET_COMMON_MIT_OPT, mit_opt)
        self._os.execute(set_mitigation, self._command_timeout)

        set_mitigation_audit = self.SET_CET_REGISTER_GLOBAL.format(self.CET_COMMON_MIT_AUDIT_OPT, mit_audit_opt)
        self._os.execute(set_mitigation_audit, self._command_timeout)

    def set_cet_per_program(self, program, mitigation_bit, mitigation_audit_bit):
        """This program sets cet for a specific program such as wordpad, notepad """
        set_mitigation = self.SET_CET_REGISTER_PER_PROGRAM.format(program, self.CET_COMMON_MIT_OPT, mitigation_bit)
        self._os.execute(set_mitigation, self._command_timeout)

        set_mitigation_audit = self.SET_CET_REGISTER_PER_PROGRAM.format(program, self.CET_COMMON_MIT_AUDIT_OPT,
                                                                        mitigation_audit_bit)
        self._os.execute(set_mitigation_audit, self._command_timeout)

    def set_cet_strict_mode(self):
        """This program will turn on the CET strict mode flag on"""
        cet_folder_directory = self.search_folder_directory("CET_20210419_")
        cet_strict_command = (cet_folder_directory + self.CET_QUICKTEST_PATH.format(self.CET_ENABLE_STRICT_MODE))

        self._log.info("Enabling CET Strict Mode On")
        result = (self._os.execute(cet_strict_command, self._command_timeout)).stdout
        self._log.info(result)

    def set_cet_audit_mode(self):
        """This program will turn on the CET Audit-mode on"""
        cet_folder_directory = self.search_folder_directory("CET_20210419_")
        cet_audit_command = (cet_folder_directory + self.CET_QUICKTEST_PATH.format(self.CET_ENABLE_AUDIT_MODE))

        self._log.info("Enabling CET Audit Mode On")
        result = (self._os.execute(cet_audit_command, self._command_timeout)).stdout
        self._log.info(result)

    def set_cet_enforcement_mode(self):
        """This program will turn enforcemnt mode"""
        cet_folder_directory = self.search_folder_directory("CET_20210419_")
        cet_enforcement_command = (
                cet_folder_directory + self.CET_QUICKTEST_PATH.format(self.CET_ENABLE_ENFORCEMENT_MODE))

        self._log.info("Enabling CET Enforced Mode On")
        result = (self._os.execute(cet_enforcement_command, self._command_timeout)).stdout
        self._log.info(result)

    def check_regisry_value(self, program):
        """Return the registry values"""

        if program == "Global":
            path = self.GLOBAL_PATH
        else:
            path = self.PER_PROGRAM_PATH.format(program)

        reg_values = []

        mit_opt = (self._os.execute(self.GET_REGISTER_VALUE.format(path, self.CET_COMMON_MIT_OPT),
                                    self._command_timeout)).stdout
        mit_a_opt = (self._os.execute(self.GET_REGISTER_VALUE.format(path, self.CET_COMMON_MIT_AUDIT_OPT),
                                      self._command_timeout)).stdout

        reg_values.append(mit_opt.replace("\n", ""))
        reg_values.append(mit_a_opt.replace("\n", ""))

        for i in range(len(reg_values)):
            if reg_values[i] == '000000000000000000000000':
                reg_values[i] = 0
            else:
                reg_values[i] = reg_values[i].strip("0")
                reg_values[i] = (int(reg_values[i]) / 16)

        return reg_values

    def cet_test(self, input):
        """This program perform a quick cet test"""

        if input == '':
            cet_folder_directory = self.search_folder_directory("CET_20210419_")
            cettest_command = (cet_folder_directory + self.CET_TEST_PATH)
            cet_test = (self._os.execute(cettest_command, self._command_timeout)).stdout
        else:
            cet_test = input

        self._log.info(cet_test)
        temp = re.findall(r"Failures.*\d+", str(cet_test))
        res = list(map(str, temp))

        fail_count = []
        for i in res:
            i.split(':')
            x = int(i[len(i) - 1])
            fail_count.append(x)

        if max(fail_count) is not 0:
            self._log.info("Failures in CetTest")
            return False
        else:
            self._log.info("CetTestPassed")
            return True

    def run_cet_quicktest(self):

        cet_folder_directory = self.search_folder_directory("CET_20210419_")
        cetquicktest_command = (cet_folder_directory + self.CET_QUICKTEST_PATH)

        shadowstack_recurse = cetquicktest_command.format("shadowstack.exe -ss_recurse")
        recurse_output = self._os.execute(shadowstack_recurse, self._command_timeout).stdout
        self._log.info(recurse_output)

        shadowstack_mismatched_ret = cetquicktest_command.format("shadowstack.exe -ss_mismatched_ret")
        ret_output = self._os.execute(shadowstack_mismatched_ret, self._command_timeout).stdout
        self._log.info(ret_output)

        return recurse_output

    def verify_Shadowstack_values(self, recurse_output):

        SSP_list = re.findall(r"(?<=SSP:).*(?=, RET_DS)", str(recurse_output))
        RET_DS_list = re.findall(r"(?<=RET_DS:).*(?=, RET_SS)", str(recurse_output))
        RET_SS_list = re.findall(r"(?<=RET_SS:).*", str(recurse_output))

        shadowstackEnabled = stackIsEqual = False

        for i in range(len(SSP_list)):
            Zero_equivalent = ' 0000000000000000'
            if (RET_SS_list[i] == Zero_equivalent or RET_DS_list[i] == Zero_equivalent or SSP_list[
                i] == Zero_equivalent):
                shadowstackEnabled = False
            else:
                shadowstackEnabled = True

        for i in range(len(RET_SS_list)):
            if RET_SS_list[i].__contains__("\r"):
                RET_SS_list[i] = RET_SS_list[i].replace("\r", '')

            if RET_SS_list[i] == RET_DS_list[i]:
                stackIsEqual = True

        self._log.info(shadowstackEnabled)
        self._log.info(stackIsEqual)

        if (shadowstackEnabled and stackIsEqual):
            return True
        else:
            self._log.info("Shadowstack not enabled ")
            return False

    def cet_quick_test(self):
        """This program performs a cet quick test"""

        cet_folder_directory = self.search_folder_directory("CET_20210419_")
        cetquicktest_command = (cet_folder_directory + self.CET_QUICKTEST_PATH)

        self._log.info("Test the default shadowstack enforcement mode")
        self.clear_event_log()

        recurse_output = self.run_cet_quicktest()

        default_quick_test = self.verify_Shadowstack_values(recurse_output)
        Error_id_default = self.check_shadowstack_event_log("")

        # enable Audit mode
        self._log.info("Test shadowstack Audit Mode")
        self.set_cet_audit_mode()

        recurse_output = self.run_cet_quicktest()

        audit_quick_test = self.verify_Shadowstack_values(recurse_output)

        # enable strict mode
        self._log.info("Test shadowstack Audit Mode")
        self.clear_event_log()
        self.set_cet_strict_mode()

        recurse_output = self.run_cet_quicktest()

        strict_quick_test = self.verify_Shadowstack_values(recurse_output)
        Error_id_strict = self.check_shadowstack_event_log("")

        if (Error_id_strict == Error_id_default == 1000):
            validError = True

        if (validError and audit_quick_test and strict_quick_test and default_quick_test):
            return True

    def create_quicktest_command_list(self):
        """
            This function puts together a list of commands required to perform a
            cet-quick test on windows hyper-V level 1 and Level 2.
            param: None
            returns : List of commands
        """
        quicktest_cmd_list = []
        quicktest_cmd_list.append(self.CLEAR_EVENT_LOG_CMD)
        path = (self.DEFAULT_DIR + self.CET_QUICKTEST_PATH)
        recurse = (path.format(self.SHADOWSTACK_RECURSE))
        ret = (path.format(self.SHADOWSTACK_MISMATCHED_RET))
        quicktest_cmd_list.extend([recurse, ret])
        audit_mode = (path.format(self.CET_ENABLE_AUDIT_MODE))
        quicktest_cmd_list.extend([audit_mode, recurse, ret])
        strict_mode = (path.format(self.CET_ENABLE_STRICT_MODE))
        quicktest_cmd_list.extend([strict_mode, recurse, ret, self.CHECK_EVENT_LOG_CMD])
        basic_mode = (path.format(self.CET_ENABLE_ENFORCEMENT_MODE))
        quicktest_cmd_list.append(basic_mode)

        return quicktest_cmd_list

    def test_wordpad_cet_enabled(self):
        """
            This program performs write, cut, copy, paste on wordpad app

            raise: RunTimeError
        """
        path = r"C:\Users\Administrator\Desktop\file.txt"
        value = r"Lorem ipsum dolor Lorem sit amet, Lorem consectetuer Lorem adipiscing Lorem elit " \
                r"Lorem ipsum dolor Lorem sit amet, Lorem consectetuer Lorem adipiscing Lorem elit "

        cmd = self.WORDPAD_CMD.format(path, value, path, path)
        exec_cmd = self._os.execute(cmd, self._command_timeout).stdout
        self._log.info('\n' + exec_cmd)

        if exec_cmd == "":
            return RuntimeError("Fail to execute wordpad command")
        elif value == exec_cmd:
            return False
        else:
            self._log.info("Removing test file")
            self._os.execute(self.REMOVE_FILE_CMD.format(path), self._command_timeout)
            return True

    def test_notepad_cet_enabled(self):
        """
            This program performs write, cut, copy, paste on wordpad app
        """
        self._log.info('')

    def get_ips(self):
        ips = self._os.execute('ipconfig | findstr "IPv4 Address.*"', self._command_timeout).stdout

        ip_list = ips.split('\n')

        for i in range(len(ip_list)):
            ip_list[i] = ip_list[i].strip("IPv4 Address. . . . . . . . . . . :")

        host_ip = ip_list[0]
        guest_ip = ip_list[1]

        return str(host_ip), str(guest_ip)

    def shadowstack_stress_test(self):
        """
            This program runs a spec stress test
        """
        cet_folder_directory = self.search_folder_directory("CET_20210419_")
        spec_test = (cet_folder_directory + self.SPEC_TEST_PATH)
        self._os.execute(spec_test, 8500)

    def set_bcdedit_setting(self):
        output = self._os.execute(self.BCD_EDIT_CMD, self._command_timeout).stdout
        self._log.info(output)

    def sigma_test(self):

        self._log.info("Executing Sigma Test")
        out = self._os.execute(self.SIGMA_TEST_CMD, 4000)
        self._log.info(out)
        output = self._os.execute(self.SORT_SIGMA_TEST_OUTPUT_FILES_CMD, self._command_timeout).stdout
        output_files = output.split("\n")
        self._log.info("The following test log files are produced {}."
                       "\nThese log files can be found inside CET folder with path {}".format(output_files,
                                                                                              self.CET_SIGMATEST_PATH))

        # TODO: Delete the files
        return output_files

    def check_vm_exists(self, vm_name):
        """
        Method to check if VM exists with the write name

            :param: vmName
            :raise: RuntimeError.
        """
        try:
            get_vm_cmd = self.GET_VM_CMD.format(vm_name)
            get_vm = (self._os.execute(get_vm_cmd, self._command_timeout)).stdout
            print("get vm result : {}".format(get_vm))
            if vm_name not in get_vm:
                self._log.info("VM Named '{}' name does not exist."
                               "Create vm using BKM document".format(vm_name))
            else:
                self._log.info("vm named '{}' exists".format(vm_name))
                return True
        except RuntimeError:
            self._log.error("Unable to check the VM : {}".format(vm_name))
            raise

    def start_vm(self, vm_name):
        """
        Method to start VM.

        :param vm_name: Name of the VM to start
        :raise: RuntimeError. It will raise error when failed in executing the START_VM_CMD.
        """
        state_str = "Running"
        try:
            vm_state = self.get_vm_state(vm_name)
            if state_str not in vm_state:
                self._log.info("{} is powered off. Powering on VM\n".format(vm_name))
                start_vm_cmd = self.START_VM_CMD.format(vm_name)
                start_vm_result = self._os.execute(start_vm_cmd, self._command_timeout).stdout
                time.sleep(60)
                self._log.info("Successfully started VM {}".format(vm_name))
            elif state_str in vm_state:
                self._log.info("WARNING: VM {} is already in running state.".format(vm_name))
        except RuntimeError:
            self._log.error("Unable to start the VM : {}".format(vm_name))
            raise

    def get_vm_state(self, vm_name):
        """
        Method to get state of the given VM

        :param vm_name: the name of the given VM
        :raise: RunTimeError
        :return: the state of cpus. Running/Off/Paused
        """
        try:
            get_vm_cmd = self.GET_VM_CMD.format(vm_name)
            vm_info = self._os.execute(get_vm_cmd, self._command_timeout).stdout
            str_list = vm_info.split('\n')
            state = None
            for str in str_list:
                if vm_name in str:
                    res = re.findall(r"\S+", str.strip(vm_name))
                    state = res[0]
            if state is None:
                return RuntimeError("Fail to get state info of the VM.")
            else:
                self._log.info("Get the state of {}:{}\n".format(vm_name, state))
                return state
        except RuntimeError:
            raise

    def parse_config(self, account):
        """
            This function parses the config file. Informations are entered manually

            returns: ip address, username and password for each level machine

        """
        config = ConfigParser()
        config.read('C:\Automation\cet_config.ini')

        _ip = config[account]['ip']
        _user = config[account]['user_name']
        _password = config[account]['password']
        _vm_name = config[account]['vm_name']

        return {'ip': _ip, 'user': _user, 'password': _password, 'vm_name': _vm_name}

    def ssh_execute_level1(self, platform, command):

        local = self.parse_config(self.ROOT)
        dest = self.parse_config(platform)

        local_ip, local_username, local_password = local.get('ip'), local.get('user'), local.get('password')
        dest_ip, dest_username, dest_password = dest.get('ip'), dest.get('user'), dest.get('password')

        stdout, stderr = '', ''
        with paramiko.SSHClient() as jhost:
            jhost.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                jhost.connect(hostname=local_ip, username=local_username, password=local_password)
                jhost_transport = jhost.get_transport()
                dest_addr = (dest_ip, 22)
                local_addr = (local_ip, 22)
                jhost_channel = jhost_transport.open_channel("direct-tcpip", dest_addr, local_addr)

                with paramiko.SSHClient() as target_server:
                    target_server.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    target_server.connect(hostname=dest_ip, username=dest_username, password=dest_password,
                                          sock=jhost_channel)

                    self._log.info(f"Invoking {command} on remote host {dest_ip} over SSH")
                    _, stdout, stderr = target_server.exec_command(command)
                    stdout = stdout.read().decode('utf-8')
                    stderr = stderr.read().decode('utf-8')
            except SSHException as ssh_ex:
                self._log.info(f"Failed to connect to {dest_ip} ")
                raise BaseException()
        return (stdout, stderr)

    def ssh_execute_level2(self, platform1, platform2, cmd):

        local = self.parse_config(self.ROOT)
        dest = self.parse_config(platform1)
        dest2 = self.parse_config(platform2)

        local_ip, local_username, local_password = local.get('ip'), local.get('user'), local.get('password')
        dest_ip, dest_username, dest_password = dest.get('ip'), dest.get('user'), dest.get('password')
        dest2_ip, dest2_username, dest2_password = dest2.get('ip'), dest2.get('user'), dest2.get('password')

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(local_ip, username=local_username, password=local_password)

        dest_addr = (dest_ip, 22)
        local_addr = (local_ip, 22)
        ssh_session = ssh_client.get_transport().open_channel("direct-tcpip", dest_addr, local_addr)

        jhost = paramiko.SSHClient()
        jhost.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jhost.connect(dest_ip, username=dest_username, password=dest_password, sock=ssh_session)

        dest_addr2 = (dest2_ip, 22)
        local_addr2 = (dest_ip, 22)
        ssh_session2 = ssh_client.get_transport().open_channel("direct-tcpip", dest_addr2, local_addr2)

        jhost2 = paramiko.SSHClient()
        jhost2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jhost2.connect(dest2_ip, username=dest2_username, password=dest2_password, sock=ssh_session)

        stdin, stdout, stderr = jhost2.exec_command(cmd)

        jhost2.close()
        jhost.close()
        ssh_client.close()

        return stdin, stdout, stderr

    def ping_system(self, platform):

        if platform == "root":
            ip = '10.165.92.99'
            ping_result = self._os.execute('ping {}'.format(ip), self._command_timeout).stdout
            self._log.info(ping_result)
        elif platform == "Windows L1A":
            ip = '10.165.92.164'
            ping_result = self.ssh_execute_level1('Windows L1A', 'ping {}'.format(ip))
