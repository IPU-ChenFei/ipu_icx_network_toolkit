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

from pathlib import Path

from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib import content_exceptions
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.dc_power import DcPowerControlProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems, ProductFamilies

from src.lib.bios_constants import BiosSerialPathConstants
from src.lib.content_base_test_case import ContentBaseTestCase
from pathlib2 import Path

from src.lib.bios_util import BiosUtil, SerialBiosUtil

from src.lib.common_content_lib import CommonContentLib
from src.lib.uefi_util import UefiUtil
from src.memory.lib.memory_common_lib import MemoryCommonLib
from src.lib.os_lib import WindowsCommonLib
from src.manageability.lib.redfish_test_common import RedFishTestCommon

from src.lib.windows_event_log import WindowsEventLog
from src.lib.content_configuration import ContentConfiguration
from src.lib.install_collateral import InstallCollateral
from src.lib.dmidecode_parser_lib import DmiDecodeParser
from src.lib.smbios_configuration import SMBiosConfiguration
from src.lib.mlc_utils import MlcUtils
from src.lib.stream_utils import StreamUtils
from src.provider.cpu_info_provider import CpuInfoProvider
from src.provider.ipmctl_provider import IpmctlProvider
from src.provider.stressapp_provider import StressAppTestProvider
from src.provider.memory_provider import MemoryProvider, MemoryInfo


class DDRCommon(ContentBaseTestCase):
    """
    Base class for all memory stress test related test cases with fastboot enabled and disabled. This baselcass covers
    below glasgow IDs

    1. 57804
    2. 60841
    3. 59060
    4. 57805
    5. 59426
    6. 63306
    """
    # Linux tools
    PLATFORM_STRESS_CYCLER_LINUX_FILE = "platform_cycler_linux.tgz"
    PLATFORM_STRESS_LINUX_FILE = "stressapptest"

    # Windows tools
    PLATFORM_STRESS_CYCLER_WINDOWS_FILE = "platform_cycler_windows.zip"
    PRIME95_WINDOWS_FILE = "prime95.zip"

    # Directory names
    PLATFORM_CYCLER_FOLDER_NAME = "platform_cycler"
    PLATFORM_CYCLER_EXTRACT_FOLDER_NAME = "platform_cycler_linux_installer"
    COLLATERAL_DIR_NAME = "collateral"
    LOG_DIR_NAME = "logs"

    # Linux environment directory path
    LINUX_PLATFORM_CYCLER_LOG_FOLDER = "/platform_rebooter/"
    LINUX_USR_SBIN_PATH = "/usr/sbin"
    LINUX_PLATFORM_DC_CYCLER_LOG_PATH = "/platform_dc_graceful/logs/"
    LINUX_PLATFORM_REBOOTER_LOG_PATH = "/platform_rebooter/logs/"

    # Windows environment directory path
    PRIME95_SUT_WINDOWS_FILE_PATH = "c:\\"
    PLATFORM_CYCLER_WINDOWS_FOLDER_NAME_SUT = "platform_cycler_win"
    WINDOWS_PLATFORM_CYCLER_LOG_PATH = "c:\\platform_cycler\\logs"

    _collateral_path = None
    _path_log_file = None
    platform_cycler_extract_path = None

    C_DRIVE_PATH = "C:\\"

    MLC_COMMAND_LINUX = "./mlc -Z | tee -a ddr4_prefetch_mlc.log"
    STREAM_COMMAND = "./stream | tee -a ddr4_prefetch_stream.log"
    STREAM_THRESHOLD_VALUE = 30

    MLC_TOOL = 'mlc'
    WINDOWS = "Windows"
    COMMAND_TO_GET_TOTAL_MEMORY_WIN = r"systeminfo"
    COMMAND_TO_RUN_MLC = r'powershell.exe ".\mlc.exe | tee ddr4_mlc.log"'

    COMMAND_TO_GET_TOTAL_MEMORY = "cat /proc/meminfo"
    COMMAND_TO_GET_LOAD_AVERAGE = "cat /proc/loadavg"
    LINUX_USR_ROOT_PATH = "/root"
    CMP_LOAD_AVERAGE_BEFORE_STRESSAPP = 2
    CMP_LOAD_AVERAGE_AFTER_STRESSAPP = 50
    OPT_PATH = "/opt"

    dict_product_info = {"WHITLEY": "Whitley", "PURLEY": "Purley", "WilsonPoint": "Whitley"}
    dict_package_info = {"WHITLEY": "stress_whitley_ilvss.pkx", "PURLEY": "stress_purley_ilvss.pkx", "WilsonPoint": "stress_whitley_ilvss.pkx"}

    UEFI_CONFIG_PATH = 'suts/sut/providers/uefi_shell'
    BIOS_BOOTMENU_CONFIGPATH = "suts/sut/providers/bios_bootmenu"
    TOTAL_MEMORY_STR = "Total Memory"
    MEMORY_MODE = "Memory Mode"
    SYSTEM_MEMORY_SPEED = "System Memory Speed"
    INDEPENDENT = "Independent"
    WMIC_COMMAND = "wmic MEMORYCHIP get BankLabel,DeviceLocator,Capacity,Speed,Formfactor"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        super(DDRCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)

        self._cfg = cfg_opts
        self._arguments = arguments
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

        self._bios_util = BiosUtil(cfg_opts, self.get_bios_config_file_path(bios_config_file), self._bios, self._log,
                                   self._common_content_lib)

        self._common_content_configuration = ContentConfiguration(self._log)

        self._num_of_cycles = self._common_content_configuration.memory_number_of_cycle()

        self._windows_common_lib = WindowsCommonLib(self._log, self._os)
        self.windows_home_drive_path = None

        self._memory_common_lib = MemoryCommonLib(self._log, cfg_opts, self._os, self._num_of_cycles)
        self._windows_event_log = WindowsEventLog(self._log, self._os)
        self._ilvss_runtime = self._common_content_configuration.memory_ilvss_run_time()
        self._script_sleep_time_percent = self._common_content_configuration.memory_ilvss_script_sleep_time()
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._next_reboot_wait_time = self._common_content_configuration.memory_next_reboot_wait_time()
        self._dc_on_time = self._common_content_configuration.memory_dc_on_time()
        self._test_execute_time = self._common_content_configuration.memory_test_execute_time()
        self._stress_app_execute_time = self._common_content_configuration.memory_stress_test_execute_time()
        self._mlc_runtime = self._common_content_configuration.memory_mlc_run_time()

        self._post_mem_capacity_config = self._common_content_configuration.memory_bios_post_memory_capacity()
        self._dcpmm_mem_capacity_config = self._common_content_configuration.memory_bios_total_dcpmm_memory_capacity()
        self._variance_percent = self._common_content_configuration.get_memory_variance_percent()
        self.prime95_running_time = self._common_content_configuration.get_memory_prime95_running_time()
        self._iwvss_runtime = self._common_content_configuration.get_iwvss_run_time()

        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)
        self._dmidecode_path = self._install_collateral.install_dmidecode()
        self._dmidecode_parser = DmiDecodeParser(self._log, self._os)
        self._smbios_config = SMBiosConfiguration(self._log, self._os, self._dmidecode_path)
        self._mlc_utils = MlcUtils(self._log)
        self._stress_app_provider = StressAppTestProvider.factory(test_log, os_obj=self._os, cfg_opts=cfg_opts)
        self._product_family = self._common_content_lib.get_platform_family()

        self._uefi_util_obj = None
        self._uefi_obj = None
        self._bios_boot_menu_obj = None
        self._opt_obj = cfg_opts
        self._test_log_obj = test_log

        self.create_uefi_obj(cfg_opts, test_log)
        self._ipmctl_provider_uefi = IpmctlProvider.factory(
            test_log, self._os, execution_env="uefi", cfg_opts=cfg_opts, uefi_obj=self._uefi_util_obj)

        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._csp = None

        self._memory_provider = MemoryProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self._os)
        self.dram_memory_size_list = list()
        self.platform_based_config_check_highest_mem = \
            self._common_content_configuration.memory_supported_highest_capacity_dimm(self._product_family)

        # To get maximum supported capacity DIMM value from config file
        self.maximum_supported_dimm_value_config = int(self.platform_based_config_check_highest_mem['capacity'])

        self._cpu_info_provider = CpuInfoProvider.factory(self._log, cfg_opts, self._os)  # type: CpuInfoProvider
        self._serial_bios_util = SerialBiosUtil(self.ac_power, test_log, self._common_content_lib, cfg_opts)

    def get_bios_config_file_path(self, bios_config_file):
        """
        This function used to get the bios configuration path.

        :param bios_config_file: configuration file.
        :return: path of the config file.
        :raise: IOError: Bios config file is not found.
        """
        if bios_config_file is None:
            return bios_config_file

        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = os.path.join(cur_path, bios_config_file)
        if not os.path.isfile(bios_config_file_path):
            self._log.error("The bios config file '%s' does not exists." % bios_config_file)
            raise IOError("The bios config file '%s' does not exists." % bios_config_file)

        return bios_config_file_path

    def execute_installer_reboot_stress_test_linux(self, platform_cycler_extract_path):
        """
        Executing the installer file with specific cycle and waiting time.

        :return: None
        :raise: RuntimeError if stress test execution failed.
        """
        try:
            self._log.info("Starting the platform cycler test with number of cycles : {} and "
                           "amount of wait time after rebooting : {}".format(self._num_of_cycles,
                                                                             self._next_reboot_wait_time))

            command_line = "./installer --reboot -s -c {} -w {}".format(self._num_of_cycles,
                                                                        self._next_reboot_wait_time)
            self._log.info("Stress test command line is '{}'".format(command_line))
            self._log.info("Stress test is running from directory '{}'".format(platform_cycler_extract_path))

            self._log.info("Running the platform cycler installer test....")

            verify_result = self._os.execute(command_line, self._command_timeout,
                                             cwd=platform_cycler_extract_path)

            if verify_result.cmd_failed():
                self._log.error("Failed to execute the command {}".format(verify_result))
                raise RuntimeError("Failed to execute the command {} and the "
                                   "error is {}..".format(verify_result, verify_result.stderr))
            self._log.info("Waiting for platform cycler installer test to complete....")

            # calculate total time to wait until stress test completes
            total_wait_time = \
                self._num_of_cycles * self._command_timeout + self._next_reboot_wait_time * self._num_of_cycles + \
                self._num_of_cycles * self._reboot_timeout
            self._log.info("Total wait time is {} seconds...".format(total_wait_time))

            time.sleep(total_wait_time)  # wait for timeout
            self._log.info("The platform cycler test is completed....")

        except Exception as ex:
            self._log.error("Cycler execution failed with exception '{}'...".format(ex))
            raise RuntimeError("Cycler execution failed with exception '{}'...".format(ex))

    def execute_installer_dcgraceful_stress_test_linux(self, platform_cycler_extract_path):
        """
        Executing the installer file with specific cycle and waiting time.

        :return: None
        :raise: RuntimeError if stress test execution failed.
        """
        dc_power_cfg = self._opt_obj.find(DcPowerControlProvider.DEFAULT_CONFIG_PATH)
        _dc_power = ProviderFactory.create(dc_power_cfg, self._log)

        try:
            self._log.info("Starting the platform cycler test with number of cycles : {} and "
                           "amount of wait time after rebooting : {}".format(self._num_of_cycles,
                                                                             self._next_reboot_wait_time))

            command_line = "./installer --dcgraceful -s -c {} -w {}".format(self._num_of_cycles,
                                                                            self._next_reboot_wait_time)
            self._log.info("Stress test command line is '{}'".format(command_line))
            self._log.info("Stress test is running from directory '{}'".format(platform_cycler_extract_path))

            self._log.info("Running the platform cycler installer test....")

            verify_result = self._os.execute(command_line, self._command_timeout,
                                             cwd=platform_cycler_extract_path)

            if verify_result.cmd_failed():
                self._log.error("Failed to execute the command {}".format(verify_result))
                raise RuntimeError("Failed to execute the command {} and the "
                                   "error is {}..".format(verify_result, verify_result.stderr))

            self._log.info("Waiting for platform cycler installer test to complete....")

            current_cycle = 0
            dc_graceful = True
            while dc_graceful:
                if self._os.is_alive():
                    self._log.info("Cycle {} : Stress test execution time is approximately "
                                   "{} seconds...".format(current_cycle, self._test_execute_time))
                    # wait time to finish stress test to finish its execution
                    time.sleep(self._test_execute_time)
                    self._log.info("Cycle {} execution has been completed"
                                   "... SUT will soon shutdown..".format(current_cycle))

                    if self._os.is_alive():
                        log_error = "SUT did not shutdown after the completion of dc graceful test.."
                        self._log.error(log_error)
                        raise RuntimeError(log_error)

                if not self._os.is_alive():
                    if _dc_power.dc_power_on(3):
                        current_cycle += 1
                        self._log.info("SUT is powering on... Approximate wait time is {} seconds..."
                                       .format(self._dc_on_time))
                        # wait time after dc power is on
                        time.sleep(self._dc_on_time)
                    else:
                        err_log = "Failed to power on the system..."
                        self._log.error(err_log)
                        raise RuntimeError(err_log)

                if current_cycle == self._num_of_cycles:
                    dc_graceful = False

            self._log.info("The platform cycler test is completed....")

        except Exception as ex:
            self._log.error("Cycler execution failed with exception '{}'...".format(ex))
            raise

    def log_parsing(self, log_file_path):
        """
        Parsing all the necessary logs.

        :return: false if the test case is failed log parsing else true
        """
        final_result = [self._memory_common_lib.parse_platform_log
                        (log_path=os.path.join(log_file_path, "platform_dc_graceful.log")),
                        self._memory_common_lib.check_memory_log
                        (log_path=os.path.join(log_file_path, "memory.log")),
                        self._memory_common_lib.parse_log_for_error_patterns
                        (log_path=os.path.join(log_file_path, "mce.log")),
                        self._memory_common_lib.parse_log_for_error_patterns
                        (log_path=os.path.join(log_file_path, "dmesg.log")),
                        self._memory_common_lib.parse_log_for_error_patterns
                        (log_path=os.path.join(log_file_path, "journalctl.log"), encoding='UTF-8')]

        return all(final_result)

    def log_parsing_rebooter(self, log_file_path):
        """
        Parsing all the necessary logs.

        :return: false if the test case is failed log parsing else true
        """
        redfish_object = RedFishTestCommon(self._log, self._arguments, self._cfg)
        final_result = [self._memory_common_lib.parse_platform_log
                        (log_path=os.path.join(log_file_path, "platform_rebooter.log")),
                        self._memory_common_lib.check_memory_log
                        (log_path=os.path.join(log_file_path, "memory.log"))]
        logs_to_check = ["mce.log", "dmesg.log", "journalctl.log"]
        for log_file in logs_to_check:
            final_result.append(self._memory_common_lib.parse_log_for_error_patterns
                                (log_path=os.path.join(log_file_path, log_file), encoding='UTF-8'))

        final_result.append(redfish_object.check_sel())

        return all(final_result)

    def get_total_memory(self):
        """
        This function will fetch the Total System Memory Value from the Meminfo File

        :return: value of Total Memory
        :raise: RuntimeError: If Memtotal value is not present in the File
        """
        ret_cmd = self._os.execute(self.COMMAND_TO_GET_TOTAL_MEMORY, self._command_timeout)
        if ret_cmd.cmd_failed():
            log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..". \
                format(ret_cmd, ret_cmd.return_code, ret_cmd.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        mem_total = re.findall(r"MemTotal:.*", ret_cmd.stdout)[0].split(":")[1].strip()
        if not mem_total:
            self._log.error("MemTotal value is not present under the MemInfo file")
            raise RuntimeError("MemTotal value is not present under the MemInfo file")
        return mem_total

    def get_load_average(self):
        """
        This function will fetch the load average Value from the system

        :return: value of Load Average
        :raise: RuntimeError: If Load Average value is not present
        """
        ret_cmd = self._os.execute(self.COMMAND_TO_GET_LOAD_AVERAGE, self._command_timeout)
        if ret_cmd.cmd_failed():
            log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..". \
                format(ret_cmd, ret_cmd.return_code, ret_cmd.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        load_average_list = (ret_cmd.stdout.split())[0:3]

        if not load_average_list:
            log_text = "load_average value is not present in system"
            self._log.error(log_text)
            raise RuntimeError(log_text)
        return load_average_list

    def get_max_load_average(self, list_load_value):
        """
        This function will get max load average value

        :return: Max load average value from list
        :raise: RuntimeError: If Load average value is not present in the File
        """

        if list_load_value:
            max_load_value = max(list_load_value)
            self._log.info("Maximum load average value{}".format(max_load_value))
            return max_load_value

        else:
            self._log.error("Failed to get load average values")
            raise RuntimeError("Failed to get load average values")

    def execute_installer_stressapp_test_linux(self):
        """
        Execute the stress app test  file with specific waiting time.

        :return: None
        :raise: RuntimeError if stress test execution failed.
        """

        try:
            self._log.info("Starting the stress app  test")
            command_line = "./stressapptest -s {} -l stress.log ".format(self._stress_app_execute_time)
            result_verify = self._os.execute(command_line, self._command_timeout, cwd=self.LINUX_USR_ROOT_PATH)

            if result_verify.cmd_failed():
                log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..". \
                    format(result_verify, result_verify.return_code, result_verify.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)

        except Exception as ex:
            log_err = "Stress app test  execution failed with exception '{}'...".format(ex)
            self._log.error(log_err)
            raise log_err

    def log_parsing_stress_app_test(self, log_file_path):
        """
        Parsing all the necessary logs.

        :return: false if the test case is failed log parsing else true
        """
        final_result = [self._memory_common_lib.parse_log_for_error_patterns
                        (log_path=os.path.join(log_file_path, "stress.log")),
                        self._memory_common_lib.parse_log_for_error_patterns
                        (log_path=os.path.join(log_file_path, "dmesg.log")),
                        self._memory_common_lib.parse_log_for_error_patterns
                        (log_path=os.path.join(log_file_path, "journalctl.log"))]

        return all(final_result)

    def get_total_memory_win(self):
        """
        This function will fetch the Total System Memory Value from the Meminfo File
        :return: value of Total Memory
        :raise: RuntimeError: If Memtotal value is not present in the File
        """
        ret_cmd = self._os.execute(self.COMMAND_TO_GET_TOTAL_MEMORY_WIN, self._command_timeout)
        if ret_cmd.cmd_failed():
            self._log.error("Not able to run the command: {}".format(self.COMMAND_TO_GET_TOTAL_MEMORY_WIN))
            raise RuntimeError("Not able to run the command: {}".format(self.COMMAND_TO_GET_TOTAL_MEMORY_WIN))
        mem_total = re.findall(r"Total Physical Memory:.*", ret_cmd.stdout)
        if not mem_total:
            self._log.error("MemTotal value is not present under the MemInfo file")
            raise RuntimeError("MemTotal value is not present under the MemInfo file")
        total_memory = mem_total[0].split(":")[1].strip()
        self._log.info("The Amount of Memory reported by the SUT is : {}".format(total_memory))
        return total_memory

    def compare_memtotal(self, preval, postval):
        """
        This function will fetch the Total System Memory Value from the Meminfo File
        :return: value of Total Memory
        :raise: RuntimeError: If Memtotal values are not same
        """
        if preval != postval:
            self._log.error("The amounts of memory reported by the operating system are not consistent")
            raise RuntimeError("The amounts of memory reported by the operating system are not consistent")
        self._log.info("The amounts of memory reported by the operating system are consistent")
        return True

    def run_mlc_windows(self, mlc_tool_path):
        """
        Executing the tool and generate the output file.

        :return: True on success
        :raise: RuntimeError if MLC test execution failed.
        """
        # run the mlc tool and get the log file
        result = self._os.execute(self.COMMAND_TO_RUN_MLC, self._mlc_runtime, cwd=mlc_tool_path)
        if result.cmd_failed():
            error_msg = "Not able to run the command: {}".format(self.COMMAND_TO_RUN_MLC)
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully ran MLC Tool")
        return True

    def verify_mlc_log(self, file_path):
        """
        Verify the mlc log by calling the mlc utlis function

        :param file_path : mlc log file path
        :return: True on Success
        :raise: Exception: if log verification failed.
        """
        result = self._mlc_utils.verify_mlc_log_with_template_data(file_path, "utf-16")
        if not result:
            error_msg = "Failed to verify the MLC log"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully verified the MLC log")
        return result

    def execute_installer_windows_mem_reboot(self, windows_folder_name):
        """
        Executing the installer file with specific cycle and wait time

        :param windows_folder_name : folder name on SUT
        :return: None
        :raise: Exception: if Cycler execution failed.
        """
        try:
            self._log.info("Starting the test with number of cycles : {} and "
                           "amount of wait time after rebooting : {}".format(self._num_of_cycles,
                                                                             self._next_reboot_wait_time))

            command_line = "powershell -file install.ps1 /c {} /w {}".format(self._num_of_cycles,
                                                                             self._next_reboot_wait_time)
            self._log.info("Test command line is '{}'".format(command_line))

            self._log.info("Running the installer test....")
            _windows_sut_tool_installer_path = os.path.join(self.C_DRIVE_PATH, windows_folder_name)
            command_result = self._os.execute(command_line, self._command_timeout,
                                              cwd=_windows_sut_tool_installer_path)
            if command_result.cmd_failed():
                log_error = "failed to run the command {} with return value = '{}' and " \
                            "std error = '{}' ..".format(command_line,
                                                         command_result.return_code, command_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)
            self._log.info("Waiting for installer test to complete....")
            # calculate total time to wait until test completes
            total_wait_time = self._next_reboot_wait_time * self._num_of_cycles + self._num_of_cycles \
                * self._reboot_timeout
            self._log.info("Total wait time is {} seconds...".format(total_wait_time))
            time.sleep(total_wait_time)  # wait for timeout
            self._log.info("The installer test is completed....")
        except Exception as ex:
            log_error = "Cycler execution failed with exception '{}'...".format(ex)
            self._log.error(log_error)
            raise ex

    def execute_installer_dc_graceful_windows(self, windows_folder_name, command):
        """
        Executing the installer file with specific cycle and wait time

        :param windows_folder_name: executor folder name on SUT
        :param command: command to execute
        :return: None
        :raise: RuntimeError: SUT did not shutdown after the completion of dc graceful test
        :raise: Exception: if the Cycler execution failed
        """
        dc_power_cfg = self._opt_obj.find(DcPowerControlProvider.DEFAULT_CONFIG_PATH)
        _dc_power = ProviderFactory.create(dc_power_cfg, self._log)

        try:
            self._log.info("Starting the test with number of cycles : {} and "
                           "amount of wait time after rebooting : {}".format(self._num_of_cycles,
                                                                             self._next_reboot_wait_time))

            command_line = "powershell -file install.ps1 {} /c {} /w {}".format(command, self._num_of_cycles,
                                                                                self._next_reboot_wait_time)
            self._log.info("Test command line is '{}'".format(command_line))
            self._log.info("Running the installer test....")

            _windows_sut_tool_installer_path = os.path.join(self.C_DRIVE_PATH, windows_folder_name)
            command_result = self._os.execute(command_line, self._command_timeout,
                                              cwd=_windows_sut_tool_installer_path)
            if command_result.cmd_failed():
                log_error = "failed to run the command {} with return value = '{}' and " \
                            "std error = '{}' ..".format(command_line,
                                                         command_result.return_code, command_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)
            self._log.info("Waiting for installer test to complete....")

            current_cycle = 0
            dc_graceful = True
            while dc_graceful:
                if self._os.is_alive():
                    self._log.info("Cycle {} : Test execution time is approximately "
                                   "{} seconds...".format(current_cycle, self._test_execute_time))
                    # wait time to finish test to finish its execution
                    time.sleep(self._test_execute_time)
                    self._log.info("Cycle {} execution has been completed"
                                   "... SUT will soon shutdown..".format(current_cycle))

                    if self._os.is_alive():
                        log_error = "SUT did not shutdown after the completion of dc graceful test.."
                        self._log.error(log_error)
                        raise RuntimeError(log_error)

                if not self._os.is_alive():
                    current_cycle = current_cycle + 1
                    _dc_power.dc_power_on()
                    self._log.info("\n")
                    self._log.info("SUT is powering on... Approximate wait time is {} seconds..."
                                   .format(self._dc_on_time))
                    time.sleep(self._dc_on_time)  # wait time after dc power is on

                if current_cycle == self._num_of_cycles:
                    dc_graceful = False
            self._log.info("The installer test is completed....")

        except Exception as ex:
            log_error = "Cycler execution failed with exception '{}'...".format(ex)
            self._log.error(log_error)
            raise ex

    def execute_prime95_torture_windows(self, cmd, prime95_path):
        """
        Function to execute prime95 application.

        :param cmd: command to run prime95
        :param prime95_path: path of the executor.
        """
        self._log.info("Starting the prime95 test..")

        # -t refers to torture test
        self._log.info("prime95 test command line is '{}'".format(cmd))
        self._log.info("prime95 test is running from directory '{}'".format(prime95_path))

        prime95_execute_res = self._os.execute(cmd, self._command_timeout, prime95_path)

        if prime95_execute_res.cmd_failed():
            self._log.info("Prime95 execution thread has been stopped...")

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.

        :return: None
        """
        super(DDRCommon, self).prepare()

    def execute_mlc_test_linux(self, mlc_tool_path):
        """
        Executing the tool and generate the output file.

        :return: True on success
        :raise: RuntimeError if MLC test execution failed.
        """
        # run the mlc tool and get the log file
        result = self._os.execute(self.MLC_COMMAND_LINUX, self._mlc_runtime, cwd=mlc_tool_path)
        if result.cmd_failed():
            error_msg = "Not able to run the command: {}".format(self.MLC_COMMAND_LINUX)
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully ran MLC Tool")
        return True

    def execute_stream_test_linux(self, stream_tool_path):
        """
        Executing the tool and generate the output file.

        :return: True on success
        :raise: RuntimeError if STREAM test execution failed.
        """
        # run the stream tool and get the log file
        result = self._os.execute(self.STREAM_COMMAND, self._command_timeout, cwd=stream_tool_path)
        if result.cmd_failed():
            error_msg = "Not able to run the command: {}".format(self.STREAM_COMMAND)
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully ran STREAM Tool")
        return True

    def log_parsing_stream_mlc_app_test(self, log_file_path):
        """
        Parsing all the necessary logs.

        :return: false if the test case is failed log parsing else true
        """
        final_result = [self._memory_common_lib.parse_log_for_error_patterns
                        (log_path=os.path.join(log_file_path, "dmesg.log")),
                        self._memory_common_lib.parse_log_for_error_patterns
                        (log_path=os.path.join(log_file_path, "journalctl.log"))]

        return all(final_result)

    def mlc_read_write_register(self):
        """
        Function to  Load the msr driver to allow MLC to  read and write the model-specific registers (MSRs)

        :return: None
        :raise: RuntimeError: For Linux this exception will raise.
        """
        ret_val = self._os.execute("modprobe msr", self._command_timeout)
        if ret_val.cmd_failed():
            log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..". \
                format(ret_val, ret_val.return_code, ret_val.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return True

    def verify_stream_data(self, log_file_path):
        """
        Verify All the current Data with the Threshold value.

        :return: True in Success else False
        """
        try:
            stream_params = ["Copy:", "Scale:", "Add:", "Triad:"]
            stream_utils_obj = StreamUtils(self._log, log_file_path)
            for item in stream_params:
                result = stream_utils_obj.fetch_stream_data_by_function(item)
                if not float(min(result[1:2])) >= self.STREAM_THRESHOLD_VALUE:
                    error_msg = ("Failed as index {} value less than threshold value".format(result[1:2]))
                    self._log.error(error_msg)
                    raise RuntimeError(error_msg)
                self._log.info("Success as index {} value greater than threshold value".format(result[1:2]))
                return True

        except Exception as ex:
            self._log.error("Exception occurred while running the 'verify_stream_log' function")
            raise ex

    def execute_ilvss(self, cmd, cmd_ilvss_exe_path):
        """
        Function to run the ilVSS command on the SUT.

        :param cmd: ilvss command
        :param cmd_ilvss_exe_path: path of the ilvss executables
        :return None
        """
        self._common_content_lib.execute_sut_cmd(cmd, "execute ilVSS", (float((self._command_timeout *
                                                                               self._ilvss_runtime)) / 5),
                                                 cmd_path=str(cmd_ilvss_exe_path))

    def configure_ilvss_stress(self):
        """
        Execute the ilvss command

        :return: Stress pkg path
        """
        if OperatingSystems.LINUX == self._os.os_type:
            # To set the current date and time on SUT
            self._common_content_lib.set_datetime_on_sut()
            stress_pkg_path = Path(os.path.join(self.OPT_PATH, "ilvss.0/packages")).as_posix()
            # Copy the stress pkg under /opt/ilvss.0

            product_info = self._common_content_lib.execute_sut_cmd("sudo dmidecode -s system-product-name",
                                                                    "Product information", self._command_timeout,
                                                                    self.LINUX_USR_ROOT_PATH)
            product_info = product_info.split('\n')[0]

            host_tool_path = self._install_collateral.download_tool_to_host(self.dict_product_info[product_info])
            self._common_content_lib.copy_ilvss_pkx_file_from_host_to_linux_sut(stress_pkg_path,
                                                                                host_tool_path)
            self._log.info("ILVSS config file 'stress_whitley_ilvss.pkx' has been copied from host to sut"
                           "for ilvss execution of S145")
            self._os.execute("chmod +x %s" % self.dict_package_info[product_info],
                             self._command_timeout, stress_pkg_path)

            return stress_pkg_path
        else:
            log_error = "Stress configuration is not supcopy_local_file_to_sutported on OS '{}'".format(self._os.sut_os)
            self._log.error(log_error)
            raise NotImplementedError(log_error)

    def find_ilvss_task(self, str_process_name):
        """
        Function to find the process running on the SUT.

        :param str_process_name: name of the process to be found
        :return 0 if process is found in the task list else 1
        """
        ilvss_running = self._os.execute('ps -A | grep -i  "{}"'.format(str_process_name),
                                         self._command_timeout)

        return ilvss_running.return_code

    def wait_for_ilvss_process_finish(self, str_process_name):
        """
        Function verify and hold until background process finish running on the SUT.

        :param str_process_name: name of the process to be found
        :return None
        """
        self._log.info("Waiting for the ilVSS execution to complete..")
        while (self.find_ilvss_task(str_process_name)) == 0:
            self._log.debug("ilvss is still running in the background..")
            time.sleep(int(self._command_timeout / 2))

        self._log.info("ilVSS execution process  has been completed ..")

    def get_available_memory_win(self):
        """
        This function will fetch the Available Physical Memory Value from systeminfo

        :return: value of Available Memory
        :raise: RuntimeError: If available physical memory value is not present
        """
        ret_cmd = self._common_content_lib.execute_sut_cmd(self.COMMAND_TO_GET_TOTAL_MEMORY_WIN,
                                                           "Executing systeminfo cmd", self._command_timeout)
        mem_total = re.findall(r"Available Physical Memory:.*", ret_cmd)
        if not mem_total:
            log_error = "Available physical memory is not present under systeminfo"
            self._log.error(log_error)
            raise RuntimeError(log_error)
        available_memory = mem_total[0].split(":")[1].strip()
        self._log.debug("The Amount of Available Memory reported by the SUT is : {}".format(available_memory))
        return available_memory

    def get_partition_info_diskpart(self):
        """
        Function to get the partition info from diskpart command.

        @return: partition information
        """
        return self._common_content_lib.execute_sut_cmd(r"diskpart /s getpartition.txt", "get partition info",
                                                        self._command_timeout, self.C_DRIVE_PATH)

    def get_partition_info_ps(self):
        """
        Function to get the partition info from powershell command.

        @return: partition information
        """
        return self._common_content_lib.execute_sut_cmd(r"powershell Get-Partition", "get partition info powershell",
                                                        self._command_timeout, self.C_DRIVE_PATH)

    def store_partition_data_win(self):
        """
        Function to confirm partitions are present as expected in windows platform.

        """
        final_ps_list = []
        ps_size_list = []

        size_re_pattern = r"([\d.?]*\sGB|[\d.?]*\sMB)"

        # Get partition info from power shell command
        partition_info_from_ps = self.get_partition_info_ps()

        # Logging powershell partition info output
        self._log.info(partition_info_from_ps)

        for ps_list_filter in partition_info_from_ps.strip().split('\n'):
            if re.findall(size_re_pattern, ps_list_filter):
                ps_size_list.append(re.findall(size_re_pattern, ps_list_filter))
                final_ps_list.append(" ".join(ps_list_filter.split()))

        self._log.info("Final list of power shell partition details that will be used for comparision: \n{}".format(
            final_ps_list))

        # Create a powershell flat list of sizes
        ps_size_list = self._common_content_lib.list_flattening(ps_size_list)

        for list_inner in ps_size_list:
            if "." in list_inner:
                ps_size_list.append(list_inner.split(".")[0])

        # Get only numeric values of sizes from powershell command output
        ps_size_list = self._common_content_lib.get_list_of_digits(ps_size_list)

        ps_partition_numbers_list = []

        for line_ps in final_ps_list:
            ps_partition_numbers_list.append(re.findall(r"^[0-9]", line_ps))

        # Create a power shell flat list of partition numbers
        ps_partition_number_list = self._common_content_lib.list_flattening(ps_partition_numbers_list)

        return ps_size_list, ps_partition_number_list

    def create_prime95_preference_txt_file_win(self, prime95_path, physical_memory_data_win):
        """
        Function to create a prime95 torture test preference file

        @param physical_memory_data_win: System Memory information.
        @param prime95_path: path of the prime95 execute file.
        """
        need_90_percent = self._common_content_configuration.get_percent_of_total_memory_for_prime95_test()
        minimum_torture_mem_percent = self._common_content_configuration.\
            get_min_percent_of_total_memory_for_prime95_test()
        maximum_torture_mem_percent = self._common_content_configuration.\
            get_max_percent_of_total_memory_for_prime95_test()

        total_memory_data_win = int(physical_memory_data_win[0].split(":")[1].strip("MB").strip()
                                    .replace(",", ""))

        ninety_percent_memory = int(total_memory_data_win * need_90_percent)
        min_torture_memory = int(total_memory_data_win * minimum_torture_mem_percent)
        maxi_torture_memory = int(total_memory_data_win * maximum_torture_mem_percent)

        with open("prime.txt", "w+") as fp:
            list_commands = ["V24OptionsConverted=1\n", "WGUID_version=2\n", "StressTester=1\n", "UsePrimenet=0\n",
                             "MinTortureFFT={}\n".format(min_torture_memory),
                             "MaxTortureFFT={}\n".format(maxi_torture_memory),
                             "TortureMem={}\n".format(ninety_percent_memory),
                             "TortureTime=3\n", "TortureWeak=0\n", "Left=257\n", "Top=108\n", "Right=1217\n",
                             "Bottom=589\n", "W1=0 0 942 200 0 -1 -1 -1 -1\n", "W2=0 200 942 401 0 -1 -1 -1 -1\n",
                             "W3=0 267 942 401 0 -1 -1 -1 -1\n\n", "[PrimeNet]\n", "Debug=0"]
            fp.writelines(list_commands)

        self._os.copy_local_file_to_sut("prime.txt", prime95_path)

        self._log.info("Prime95 torture test execution preference text file has been copied under {}".format(
            prime95_path))

        if os.path.exists("prime.txt"):
            os.remove("prime.txt")

    def execute_iwvss(self, cmd, iwvss_path):
        """
        Function to run the iwVSS command on the SUT.

        :param cmd: iwvss command
        :param iwvss_path: path of the iwvss executables
        :return None
        """
        self._common_content_lib.execute_sut_cmd(cmd, "execute iwVSS", (float(
            (self._command_timeout * self._iwvss_runtime)) / 5), cmd_path=str(iwvss_path))

    def create_uefi_obj(self, _opt_obj, _test_log_obj):
        #  UEFI object creation
        uefi_cfg = self._opt_obj.find(self.UEFI_CONFIG_PATH)
        self._uefi_obj = ProviderFactory.create(uefi_cfg, self._test_log_obj)
        bios_boot_menu_cfg = self._opt_obj.find(self.BIOS_BOOTMENU_CONFIGPATH)
        self._bios_boot_menu_obj = ProviderFactory.create(
            bios_boot_menu_cfg, self._test_log_obj)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._uefi_util_obj = UefiUtil(self._log, self._uefi_obj, self._bios_boot_menu_obj, self.ac_power,
                                       self._common_content_configuration, self._os)

    @staticmethod
    def get_avail_start_addresses(list_of_address):
        """
        Function to get available start addresses.

        @param list_of_address: list if available addresses
        @return: list of start addresses
        """
        avail_start_addresses = []

        for add in list_of_address:
            avail_start_addresses.append(add.strip().split()[1].split("-")[0])

        return avail_start_addresses

    @staticmethod
    def get_avail_end_addresses(list_of_address):
        """
        Function to get available end addresses.

        @param list_of_address: list if available addresses
        @return: list of end addresses
        """
        avail_end_addresses = []

        for add in list_of_address:
            avail_end_addresses.append(add.strip().split()[1].split("-")[1])

        return avail_end_addresses

    def get_memmap_info(self):
        """
        Function to get memmap information

        @return: memmap output
        """
        return self._uefi_util_obj.execute_cmd_in_uefi_and_read_response('memmap')

    def verify_written_memory_location_data(self, pick_one_start_address_in_random, inner_mem_location_last_eight_hex,
                                            data_to_update_location):
        """
        Function to verify written data on memory location is retained or not.

        @param pick_one_start_address_in_random: address where we change the data
        @param inner_mem_location_last_eight_hex: memory address last eight hex value to use for data updation
        @param data_to_update_location: data to be written on the memory location.
        @return: True if verification is successfull.
        @raise: content_exceptions.TestFail if any one of memory location is not updated with expected data.
        """
        dmem_address_output_post_warm_reset = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            'dmem {}'.format(pick_one_start_address_in_random))

        dmem_address_output_post_warm_reset = ''.join(map(str, dmem_address_output_post_warm_reset)).split("\r")

        found_data_line = None

        for post_location in dmem_address_output_post_warm_reset:
            if inner_mem_location_last_eight_hex in post_location:
                found_data_line = post_location

                self._log.info("The memory address with updated data is {}".format(found_data_line))

        found_updated_data_list = found_data_line.split(":")[1].split()[:6]

        if found_updated_data_list != data_to_update_location:
            raise content_exceptions.TestFail("The data written on the memory locations does not match...")

        self._log.info("The data '{}' written on location '{}' has been verified successfully...!"
                       .format(data_to_update_location, found_data_line))

        return True

    @staticmethod
    def get_dict_off_loc_data(pick_one_dmem_address_in_random, data_to_update_location):
        """
        Function to get the dict with Keys as memory address and values as data.

        @param pick_one_dmem_address_in_random: pick one available memory address.
        @param data_to_update_location: data to be written on the memory location.
        @return: dict - Keys as memory address and values as data.
        """
        locations_to_update_data = []

        for location in range(6):
            locations_to_update_data.append(str(pick_one_dmem_address_in_random[:-1] + str(location)))

        tuple_data_location = zip(locations_to_update_data, data_to_update_location)

        # Convert tuples into a dictionary
        dict_data_location = {key: value for key, value in tuple_data_location}

        return dict_data_location

    def update_mem_location_with_data(self, dict_data_location):
        """
        Function to update the memory location with pre-defined data.

        @param dict_data_location: dict - Keys as memory address and values as data.
        @return: True if writing into memory location successful
        """
        for key in dict_data_location:
            self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
                'mm {} {}'.format(key, dict_data_location[key]))

            self._log.info("The location '{}' has been updated with data '{}' Successfully.."
                           .format(key, dict_data_location[key]))
        return True

    def get_available_addresses_list(self, memory_map_dump):
        """
        Function to get list of available addresses

        @param memory_map_dump: memory map dump output
        @return: list of addresses
        @raise: content_exceptions.TestFail if no available addresses
        """
        available_addresses = []

        for address in memory_map_dump:
            if re.findall(r"Available\s.?[\w]{16}-[\w]{16}", address):
                available_addresses.append(re.findall(r"Available\s.?[\w]{16}-[\w]{16}", address))

        flattened_list_addresses = self._common_content_lib.list_flattening(available_addresses)

        self._log.info("List of available addresses with start and end of each address... \n {}"
                       .format(flattened_list_addresses))

        if len(flattened_list_addresses) == 0:
            raise content_exceptions.TestFail("There are no available address to write the data on..")

        return flattened_list_addresses

    def get_avail_start_address_mem_locations(self, pick_one_start_address_in_random):
        """
        Function to get available start address mem locations where we will write the data on.

        @param pick_one_start_address_in_random: mem location where we will write the data on
        @return: inner mem location dump
        """
        return self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            'dmem {}'.format(pick_one_start_address_in_random))

    def verify_for_maximum_memory_population(self):
        """
        This function checks if all the slots are populated with highest capacity DIMM

        :return: None
        :raise: Testfail if all the slots are not populated with highest capacity DIMM
        """

        # Configuration from dtaf content constants
        dict_config_channel_population = self._memory_provider.get_2_dpc_channel_configuration()

        # Verification of channel population.
        channel_info_dict = self._memory_provider.verify_channel_population(dict_config_channel_population)

        if not channel_info_dict:
            raise content_exceptions.TestFail("Configuration not set correctly on this platform to support this test "
                                              "case.. please check the configuration and try again..")

        # To get populated number of memory devices in the SUT
        populated_memory_slots_list = self._memory_provider.get_populated_memory_slots()

        self._log.info("Maximum number of DIMM's are configured in the server...")

        # To get the size of the memory devices
        list_of_dict_populated_memory_size = []
        for each_memory_slot in populated_memory_slots_list:
            list_of_dict_populated_memory_size.append(
                self._memory_provider.get_locator_info(MemoryInfo.SIZE, each_memory_slot))
        self.dram_memory_size_list = [each[MemoryInfo.SIZE] for each in list_of_dict_populated_memory_size]
        self._log.info("Installed DDR in the SUT are {}".format(self.dram_memory_size_list))
        self._log.info("Supported Maximum DIMM capacity from the config file is {} GB".
                       format(self.maximum_supported_dimm_value_config))

        if "MB" in self.dram_memory_size_list[0]:
            # Remove the MB and take only numeric value (size) of dram
            self.dram_memory_size_list = \
                list(map(lambda sub: int(''.join([ele for ele in sub if ele.isnumeric()])) / 1024,
                         self.dram_memory_size_list))
        elif "GB" in self.dram_memory_size_list[0]:
            self.dram_memory_size_list = \
                list(map(lambda sub: int(''.join([ele for ele in sub if ele.isnumeric()])),
                         self.dram_memory_size_list))
        else:
            raise content_exceptions.TestFail("Not getting GB or MB in memory size list")
        self._log.info("Installed DDR in the SUT are {}".format(self.dram_memory_size_list))
        # To verify maximum DIMM capacity installed in the SUT or not.
        if all(cap != self.maximum_supported_dimm_value_config for cap in self.dram_memory_size_list):
            raise content_exceptions.TestFail("Maximum DIMM Capacity is not configured in the server, please make "
                                              "the system to have maximum DIMM capacity..")

        self._log.info("Installed and verified Maximum capacity DIMMs supported by the platform...")

    def verify_sytem_memory_speed_with_config(self, dimm_speed_config):
        """
        This function is used to verify the System memory speed from OS with the speed from the config file

        :param dimm_speed_config: DIMM speed from the configuration file
        :return: True if DIMM speed from the configuration file and OS matched
        :raise: TestFail
        """
        populated_memory_slots_list = self._memory_provider.get_populated_memory_slots()
        list_of_dict_populated_memory_speed = []
        for each_memory_slot in populated_memory_slots_list:
            list_of_dict_populated_memory_speed.append(
                self._memory_provider.get_locator_info(MemoryInfo.SPEED, each_memory_slot))

        dram_memory_speed_list = [int(each[MemoryInfo.SPEED]) for each in list_of_dict_populated_memory_speed]

        self._log.info("The memory speed list in MHz are : {}".format(dram_memory_speed_list))

        os_system_memory_frequency = min(dram_memory_speed_list)

        # To verify the OS system memory speed with the DIMM frequency from configuration file
        if os_system_memory_frequency != dimm_speed_config:
            raise content_exceptions.TestFail(
                "System memory speed from configuration file and OS are not same. From config file is {} , in OS is {}".
                format(dimm_speed_config, os_system_memory_frequency))

        self._log.info(
            "System memory speed from configuration file and OS are same.From config file is {} , in OS is {}".
            format(dimm_speed_config, os_system_memory_frequency))
        return True

    def log_parsing_mem_rebooter_windows(self, log_file_path):
        """
        Parsing all the necessary logs.

        :return: false if the test case is failed log parsing else true
        """
        final_result = [self._memory_common_lib.check_memory_log
                        (log_path=os.path.join(log_file_path, "memory.log")),
                        self._memory_common_lib.parse_log_for_error_patterns
                        (log_path=os.path.join(log_file_path, "Windows-Kernel.log")),
                        self._memory_common_lib.parse_log_for_error_patterns
                        (log_path=os.path.join(log_file_path, "sel.log"), encoding='UTF-8')]

        return all(final_result)

    def snc_check(self, bios_file_path, snc_number):
        """
        Function to check snc 2 and snc 4 bios knob has enabled correctly and nodes are present correctly.

        :param bios_file_path: bios knob path
        :param snc_number: snc number which we need to verify
        :return: True if check is successful
        :raise: content_exception.TestFail exception if verification fails
        """

        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._log.info("Bios knobs are set to its defaults.. ")
        self._bios_util.set_bios_knob(bios_file_path)
        self._common_content_lib.perform_os_reboot(self._reboot_timeout)  # To apply the new bios setting.
        try:
            self._bios_util.verify_bios_knob(bios_file_path)
        except Exception as ex:
            pass

        node_list = self._memory_provider.get_snc_node_info()

        self._cpu_info_provider.populate_cpu_info()
        socket_present = self._cpu_info_provider.get_number_of_sockets()

        self._log.debug("Number of sockets connected on the platform is : {}".format(socket_present))

        if len(node_list) != int(socket_present) * snc_number:
            error_statement = "The number of nodes in the system is not " \
                              "correct for SNC {} Bios setting with {} CPU(s) but only {} node(s) are present.." \
                .format(snc_number, socket_present, len(node_list))
            raise content_exceptions.TestFail(error_statement)

        self._log.debug("There are {} socket(s) with {} node(s)..".format(socket_present, len(node_list)))

        # To get the total physical memory and convert MB to GB
        total_system_memory_os = float(self._memory_provider.get_total_system_memory() / 1024)

        total_memory_variance = self._post_mem_capacity_config - (self._post_mem_capacity_config *
                                                                  self._variance_percent)

        self._log.debug("Total reported RAM capacity as per configuration with - {} % variance is : {} GB".format(
            self._variance_percent, total_memory_variance))

        if total_system_memory_os < int(total_memory_variance) or total_system_memory_os > \
                self._post_mem_capacity_config:
            raise content_exceptions.TestFail("Total Installed RAM memory Capacity from "
                                              "Configuration (vs) OS does not match.")

        self._log.info("Successfully verified SNC{} node information and the total amount of RAM ..".format(snc_number))
        return True

    def verify_uma_cluster_info(self, serial_log_path, uma_cluster_num):
        """
        This function is to find the specific keywords in serial log and verify it.

        :param serial_log_path: serial log path.
        :param uma_cluster_num: UMA cluster number which we need to verify
        :raise: content_exception.TestFail if unable to find the uma based clustering keywords
        """
        self._log.info("Check the specific keywords in serial log")
        uma_based_cluster_keyword_num = "UmaClustering: {}".format(uma_cluster_num)
        uma_based_cluster_keyword_hemi = "UMA-Based Clustering: Hemi"
        uma_based_cluster_keyword_quad = "UMA-Based Clustering: Quad"

        with open(serial_log_path, 'r') as log_file:
            logfile_data = log_file.read()
            key_search = re.search(uma_based_cluster_keyword_num, logfile_data)
            key_search_hemi = re.search(uma_based_cluster_keyword_hemi, logfile_data)
            key_search_quad = re.search(uma_based_cluster_keyword_quad, logfile_data)

            self._log.debug("Keyword search on UMA clustering are shown below, \n{} \n{} \n{}".format(
                key_search, key_search_hemi, key_search_quad))

            if not key_search or (not key_search_hemi and not key_search_quad):
                error_statement = "\nThe serial log did not have correct keyword" \
                                  "match for {}-Clustering UMA Bios setting..." \
                    .format(uma_cluster_num)
                raise content_exceptions.TestFail(error_statement)

    def uma_based_clustering_check(self, bios_file_path, uma_cluster_num):
        """
        Function to check uma cluster 2 and 4 bios knob has enabled correctly and serial log keywords are as expected.

        :param bios_file_path: bios knob path
        :param uma_cluster_num: UMA cluster number which we need to verify
        :return: True if check is successful
        :raise: content_exception.TestFail exception if verification fails
        """
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._log.info("Bios knobs are set to its defaults.. ")
        self._bios_util.set_bios_knob(bios_file_path)
        self._common_content_lib.perform_os_reboot(self._reboot_timeout)  # To apply the new bios setting.
        try:
            self._bios_util.verify_bios_knob(bios_file_path)
        except Exception as ex:
            pass

        # Serial log path
        serial_log_path = os.path.join(self.serial_log_dir, self._SERIAL_LOG_FILE)

        self.verify_uma_cluster_info(serial_log_path, uma_cluster_num)

        self._log.debug("The serial log have correct keyword match for {}-Clustering UMA based Bios setting...".
                        format(uma_cluster_num))

        # To get the total physical memory and convert MB to GB
        total_system_memory_os = float(self._memory_provider.get_total_system_memory() / 1024)

        total_memory_variance = self._post_mem_capacity_config - (self._post_mem_capacity_config *
                                                                  self._variance_percent)

        self._log.debug("Total reported RAM capacity as per configuration with - {} % variance is : {} GB".format(
            self._variance_percent, total_memory_variance))

        if total_system_memory_os < int(total_memory_variance) or total_system_memory_os > \
                self._post_mem_capacity_config:
            raise content_exceptions.TestFail("Total Installed RAM memory Capacity from "
                                              "Configuration (vs) OS does not match.")

        self._log.info("Successfully verified {}-Clustering UMA information and the total amount of RAM ..".
                       format(uma_cluster_num))

        return True

    def update_ddr_from_dmidecode(self, dict_dmi_decode_from_tool):
        """
        Function is used to update the DDR data based on the manufacturer

        :param dict_dmi_decode_from_tool: dmi decode data in the from of dictionary
        :return: dict_dmi_decode_from_tool
        """
        if OperatingSystems.WINDOWS == self._os.os_type:
            for dict_keys in dict_dmi_decode_from_tool.keys():
                if dict_dmi_decode_from_tool[dict_keys]['DMIType'] == 17:
                    if "No Module Installed" not in dict_dmi_decode_from_tool[dict_keys]["Size"]:
                        if "Intel" in dict_dmi_decode_from_tool[dict_keys]["Manufacturer"]:
                            memory_type = "Intel persistent memory"
                        else:
                            if ProductFamilies.SPR in self._product_family:
                                memory_type = "DDR5"
                            else:
                                memory_type = "DDR4"
                        dict_dmi_decode_from_tool[dict_keys]['Type'] = memory_type

            return dict_dmi_decode_from_tool
        elif OperatingSystems.LINUX == self._os.os_type:
            return dict_dmi_decode_from_tool

    def verify_for_minimum_memory_population(self):
        """
        This function checks if the slot is populated with minimum capacity DIMM

        :return: None
        :raise: TestFail if minimum number of DIMM with minimum capacity not populated
        """

        # To get the total number of memory devices in the SUT
        populated_memory_slots_list = self._memory_provider.get_populated_memory_slots()

        self._log.debug("populated memory slots {}".format(populated_memory_slots_list))

        # To verify minimum memory slot is populated or not
        if len(populated_memory_slots_list) != 1:
            raise content_exceptions.TestFail("Minimum number of DIMM populated has not configured in the SUT, "
                                              "only one DIMM should be populated in the SUT ...")

        self._log.info("Minimum number of DIMM populated in the SUT ...")

        populated_memory_slot_size_dict = self._memory_provider.get_locator_info(MemoryInfo.SIZE,
                                                                                 populated_memory_slots_list[0])
        dram_memory_size = populated_memory_slot_size_dict[MemoryInfo.SIZE]

        self._log.info("Populated dram memory size from OS : {}".format(dram_memory_size))

        if "MB" in dram_memory_size:
            memory_size = int(int(dram_memory_size.split()[0]) / 1024)
        else:
            memory_size = int(dram_memory_size.split()[0])

        self._log.info("Memory size in GB : {}".format(memory_size))

        platform_based_config_check_minimum_mem = \
            self._common_content_configuration.get_memory_supported_smallest_info(self._product_family)
        minimum_supported_dimm_value_config = int(platform_based_config_check_minimum_mem['capacity'])

        self._log.info("Supported Minimum DIMM capacity from the config file is : {} GB".
                       format(minimum_supported_dimm_value_config))

        # To verify minimum DIMM capacity installed in the SUT or not.
        if memory_size != minimum_supported_dimm_value_config:
            raise content_exceptions.TestFail("Minimum DIMM Capacity is not configured in the server, please make "
                                              "the system to have minimum DIMM capacity..")

        self._log.info("Installed and verified Minimum capacity DIMM supported by the platform...")

    def verify_installed_memory_in_os_level(self):
        """
        This function is to verify the amount of memory reported by the operating system matches the amount memory
        installed in the system

        return: True if matches
        """

        # Get memory size of DRAM
        dram_memory_size_list = self._memory_provider.get_dram_memory_size_list()

        # Sum of all the populated DRAM sizes
        total_dram_memory = sum(dram_memory_size_list)

        # Total memory with variance
        memtotal_variance_with_variance = (self._post_mem_capacity_config - (self._post_mem_capacity_config *
                                                                             self._variance_percent))

        self._log.info("Total memory capacity shown OS Level - {}".format(total_dram_memory))

        self._log.info("Total DDR capacity as per configuration - {}".format(self._post_mem_capacity_config))

        if total_dram_memory < int(memtotal_variance_with_variance) or \
                total_dram_memory != self._post_mem_capacity_config:
            raise content_exceptions.TestFail("Total Installed DDR Capacity is not same as configuration.")

        self._log.info("Total Installed DDR Capacity is same as configuration.")

        return True

    def verify_physical_memory_in_system_information_in_bios(self, speed_mode=None):
        """
        This function is used to get the Total Memory Information under EDKII Menu --> System Information and in Bios
        Front page.

        """
        try:
            # To Enter Bios page
            success, msg = self._serial_bios_util.navigate_bios_menu()
            if not success:
                raise content_exceptions.TestFail(msg)

            # Parse EDKII Menu screen
            screen_info = self._serial_bios_util.get_current_screen_info()
            self._log.info("Bios Front page Screen Info {}".format(screen_info))
            bios_front_page_memory = None
            for item in screen_info[0]:
                if "RAM" in item:
                    bios_front_page_memory = item
                    break
            self._log.info("Bios front page memory information :  {}".format(bios_front_page_memory))
            if not bios_front_page_memory:
                raise content_exceptions.TestFail("Not able to get POST memory ...")
            post_memory_size = re.findall(r"\s[0-9].*\sMB\sRAM", bios_front_page_memory)[0].strip().split(" ")[0]
            self._log.info("Bios front page memory in MB :  {}".format(post_memory_size))

            post_memory_size = int(int(post_memory_size) / 1024)
            self._log.info("Bios front page memory in GB : {}".format(post_memory_size))

            if self._post_mem_capacity_config != post_memory_size:
                raise content_exceptions.TestFail("Total Installed DDR Capacity is not same as configuration.")
            self._log.info("The memory displayed at POST is matched with physical memory installed in SUT.")

            # To Navigate to System Information in EDKII Menu
            serial_path = BiosSerialPathConstants.SYSTEM_INFORMATION_PATH[self._product_family.upper()]
            self._serial_bios_util.select_enter_knob(serial_path)

            bios_boot_menu_cfg = self._opt_obj.find(self.BIOS_BOOTMENU_CONFIGPATH)
            self._bios_boot_menu_obj = ProviderFactory.create(
                bios_boot_menu_cfg, self._test_log_obj)
            self._bios_boot_menu_obj.press_key("UP")
            time.sleep(60)
            screen_info = self._serial_bios_util.get_current_screen_info()
            self._log.info("Screen Info {}".format(screen_info))

            total_memory = None
            for item in screen_info[0]:
                if self.TOTAL_MEMORY_STR in item:
                    total_memory = item
            total_memory_in_mb = total_memory.split(self.TOTAL_MEMORY_STR)[1].strip().split("MB")[0].strip()
            # To convert into GB.
            total_memory_in_gb = int(int(total_memory_in_mb) / 1024)
            self._log.info("Total Physical memory in GB is : {}".format(total_memory_in_gb))

            if self._post_mem_capacity_config != total_memory_in_gb:
                raise content_exceptions.TestFail("Total Installed DDR Capacity is not same as configuration.")

            self._log.info("Total Installed DDR Capacity is same as configuration.")
            memory_mode = None
            system_memory_speed = None
            if speed_mode:
                ddr_frequency_config = self._common_content_configuration.get_ddr_freq_for_dpmo()
                for item in screen_info[0]:
                    if self.MEMORY_MODE in item:
                        memory_mode = item
                    if self.SYSTEM_MEMORY_SPEED in item:
                        system_memory_speed = item

                self._log.info("Memory mode from the Bios : {} and from config is : {}".format(memory_mode,
                                                                                               self.INDEPENDENT))
                self._log.info("Memory speed from the Bios : {} and from config is : {}".format(system_memory_speed,
                                                                                                ddr_frequency_config))
                if not (self.INDEPENDENT in memory_mode and str(ddr_frequency_config) in system_memory_speed):
                    raise content_exceptions.TestFail("memory mode or ddr frequency is not correct. "
                                                      "Please check the configuration...")

                self._log.info("System memory speed and memory mode match with configuration ...")
        except Exception as ex:
            self._log.error("An exception occurred:\n{}".format(str(ex)))
            self._log.error("An exception occurred:\n{}".format(str(ex)))
            raise ex
        finally:
            if not self.os.is_alive():
                self._log.info("SUT is not alive ...")
                self.perform_graceful_g3()
