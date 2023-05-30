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
import platform
import shutil
import socket
import subprocess
import time

import six
from configobj import ConfigObj

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.install_collateral import InstallCollateral
from src.provider.ptu_provider import PTUProvider
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.bios_util import BiosUtil
import src.lib.content_exceptions as content_exceptions

import montana as montana


class MivCommon(BaseTestCase):
    """
    Common base class for miv Montana test cases
    """

    # relative path for Montana
    MONTANA_RELATIVE_PATH = r"bin\montana.py"
    # miv configuration relative path
    MIV_CONFIG_RELATIVE_PATH = "configuration"

    PTU_CMD_TO_STRESS_CORES = "./ptu -mon -log -csv -logname loginfo -ct 3 -y -cpu {}"
    ALL_CPU = "ALL"
    AVG_STRING = "Avg"
    TDF_FILENAME = "statistics.tdf"
    GET_STATISTICS_ON_D1_CMD = r"\nativemodules\statistics.py -g -m 01 -d 01"
    # Default prepare flags
    use_ping = True
    use_getdeviceid = True
    start_ptu = False

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new miv Common object

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(MivCommon, self).__init__(test_log, arguments, cfg_opts)

        # miv test case arguments
        self.time = arguments.time
        self.tdf_filename = arguments.filename
        self.start_ptu = arguments.ptu
        self.memory_stress = arguments.memorystress
        self.bios_config_file = arguments.bios
        self._cc_log_path = arguments.outputpath
        self.__config_files_path = arguments.configfilespath  # config files path with comma separated

        montana_path = self.get_montana_path
        self._montana_abs_path = os.path.join(montana_path, self.MONTANA_RELATIVE_PATH)
        miv_config_abs_path = os.path.join(montana_path, self.MIV_CONFIG_RELATIVE_PATH)
        config_name = str(socket.gethostname()) + ".cfg"

        # we will check if the miv config path available in Automation folder first
        exec_os = platform.system()
        def_cfg_file = os.path.join(Framework.CFG_BASE[exec_os], config_name)
        alt_cfg_file = os.path.join(miv_config_abs_path, config_name)
        if os.path.exists(def_cfg_file):
            self.miv_config_file_path = def_cfg_file
        elif os.path.exists(alt_cfg_file):
            self.miv_config_file_path = alt_cfg_file
        else:
            log_error = "The MIV config file '{}' does exists. Please populate this file and " \
                        "run test again".format(def_cfg_file)
            self._log.error(log_error)
            raise FileNotFoundError(log_error)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

        self.log_dir = self._common_content_lib.get_log_file_dir()
        self.serial_log_dir = os.path.join(self.log_dir, "serial_logs")
        if not os.path.exists(self.serial_log_dir):
            os.makedirs(self.serial_log_dir)
        
        self._cc_log_path = arguments.outputpath
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()  # command timeout in seconds

        if not self._os.is_alive():
            self._log.error("System is not alive, wait for the sut online")
            self._common_content_lib.perform_graceful_ac_off_on(self._ac)
            try:
                self._os.wait_for_os(self._reboot_timeout)
            except Exception as ex:
                self._log.error("System is not alive, exception='{}'".format(ex))
                raise content_exceptions.TestFail("System is not alive")

        self._install_collateral = InstallCollateral(test_log, self._os, cfg_opts)  # type: InstallCollateral
        self._ptu_provider = PTUProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self._os)  # type: PTUProvider
        self.ptu_path = ""
        self._stress_app_provider = StressAppTestProvider.factory(test_log, cfg_opts,
                                                                  self._os)  # type: StressAppTestProvider
        stress_app_execute_time = 10000
        self.stress_app_name = "stressapptest"
        self.stress_cmd_line = "./stressapptest -s {} -M -m -W -l stress.log ".format(stress_app_execute_time)
        self.ptu_cmd = None

        self.sut_ip = None
        self.bmc_ip = None
        self.populate_bmc_and_sut_ip_address()

        if self.sut_ip is None or self.bmc_ip is None:
            log_error = "SUT or BMC IP address is not populated in config file '{}' the IP address and " \
                        "run the test again..".format(self.miv_config_file_path)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info("Found BMC IP: " + self.bmc_ip)
        self._log.info("Found Host IP: " + self.sut_ip)

        # Bios provider init
        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)
        self._bios_util = BiosUtil(cfg_opts, bios_obj=self._bios, log=test_log, common_content_lib=self._common_content_lib)

        # if TC changes BIOS knobs, below flag will be set to True
        self.set_default_bios = False

    def populate_bmc_and_sut_ip_address(self):
        try:
            cp = ConfigObj(self.miv_config_file_path)
            self.bmc_ip = cp["Section0"]["ipaddress"]
            self.sut_ip = cp["Section0"]["osip"]
        except Exception as ex:
            self._log.error("The config file '{}' is not populated with either "
                            "BMC IP or SUT IP.".format(self.miv_config_file_path))
            raise ex

    @property
    def get_montana_path(self):
        try:
            montana_path = Path(montana.__file__).parent
            self._log.info("Montana Framework Path='{}'".format(montana_path))
            return montana_path
        except Exception as ex:
            log_error = "Unable to get path to Montana framework due to exception = '{}'.Check if you have populated" \
                        " the 'PYTHONPATH' with correct path to Montana framework"
            self._log.error(log_error)
            raise ex

    def prepare(self):
        """
        1. Knobs (if requested)
        2. Ping BMC
        3. Get device id
        4. Start PTU (if requested)
        :return: None - Trigger exception on failure
        """

        # TODO - knobs for new Crashdump test case
        # Crasdump/EINJ knobs for DTAF:
        # [Lock Chipset]
        # Bios_Path =
        # Target = Disable, Enable
        # [EV DFX Features]
        # Bios_Path =
        # Target = Enable

        if self.use_ping:
            ip_list = (self.sut_ip, self.bmc_ip)
            for ip in ip_list:
                pingcommand = r"ping " + ip
                result = subprocess.call(pingcommand)
                self._log.info("ping result = " + str(result))
                if result != 0:
                    self._log.error("Error - ping " + ip + " failed")
                    raise RuntimeError("Error - ping " + ip + " failed")

        if self.use_getdeviceid:
            self.run_montana_tdf(tdf_filename="getdeviceid.tdf")

    @classmethod
    def add_arguments(cls, parser):
        super(MivCommon, cls).add_arguments(parser)
        # Use add_argument

        parser.add_argument('-f', '--filename', action="store", default="",
                            help="Test TDF name to be passed to Montana")

        # Minimal 1 minute default will allow a single full execution pass
        parser.add_argument('-t', '--time', action="store", default="",
                            help="Time to run Montana stress loop")

        parser.add_argument('-P', '--ptu', action="store_true", default=False,
                            help="Launch PTU CPU stress on SUT for power limiting tests")

        parser.add_argument('-M', '--memorystress', action="store_true", default=False,
                            help="Launch PTU and stressapptest memory stress on SUT for power limiting tests")

        # bios config file if any bios knobs to be set before test
        parser.add_argument('-b', '--bios', action="store", default="",
                            help="Bios config file to set any bios knobs")

        # output log file path to copy logs for command center consumption
        parser.add_argument('-o', '--outputpath', action="store", default="",
                            help="Log folder to copy log files to command center")

        # output log file path to copy logs for command center consumption
        parser.add_argument('-c', '--configfilespath', action="store", default="",
                            help="Config files")

    def cleanup(self, return_status):

        self.run_montana_tdf(tdf_filename="miv_automation_function_delete_all_policies.tdf", supress_errors=True)
        if self.ptu_cmd is not None:
            self._log.debug("PTU may be running, kill the process!!!")
            self._ptu_provider.kill_ptu_tool()

        if self.memory_stress:
            self._stress_app_provider.kill_stress_tool(self.stress_app_name, self.stress_cmd_line)

        # TODO - Call delete policy from Montana class instead of running tdf
        # sys.path.append(r"C:\miv-mivsoftware")
        # from montana.nativemodules import deletepolicy
        # dp = deletepolicy.deletepolicy()
        # dp.__init__()
        # error_count = dp.deleteall()
        self.copy_montana_logs()
        if self.set_default_bios:
            self._bios_util.load_bios_defaults()
            self._common_content_lib.perform_graceful_ac_off_on(self._ac)
            self._os.wait_for_os(self._reboot_timeout)

        super(MivCommon, self).cleanup(return_status)

    def copy_montana_logs(self):
        """
        Move all montana csv (log) files to DTAF LOG folder..

        :return: None
        :raise: None
        """

        current_dir = os.getcwd()
        dtaf_log_folder = Path(self._common_content_lib.get_log_file_path(self._log)).parent
        self._log.info("Current Dir: {} and dtaf_log_folder: {}.".format(current_dir, dtaf_log_folder))

        # move ptu logs if they are captured
        for ptu_log_file in self._ptu_provider.PTU_LOG_FILES:
            ptu_log_path = os.path.join(current_dir, ptu_log_file)
            if os.path.exists(ptu_log_path):
                dtaf_log_path = os.path.join(dtaf_log_folder, ptu_log_file)
                for i in range(3):
                    try:
                        shutil.move(ptu_log_path, dtaf_log_path)
                        break
                    except PermissionError:
                        self._log.info("Unable to move PTU logs due to Permission issue..")
                        time.sleep(120)
                self._log.info("PTU Log file location = '{}'..".format(dtaf_log_path))

        # move all csv (montana logs) from current running dir to dtaf log folder
        for log_file in os.listdir(current_dir):
            if log_file.endswith(".csv"):
                csv_log_path = os.path.join(current_dir, log_file)
                dtaf_log_path = os.path.join(dtaf_log_folder, log_file)
                for i in range(3):
                    try:
                        shutil.move(csv_log_path, dtaf_log_path)
                        break
                    except PermissionError:
                        self._log.info("Unable to move MIV logs due to Permission issue..")
                        time.sleep(120)
                self._log.info("MIV Log file location = '{}'..".format(dtaf_log_path))

        # copy any crashdump relates logs e.g. .txt and .json files
        for file_name in os.listdir(current_dir):
            if "crashdump" in file_name and (file_name.endswith(".txt") or file_name.endswith(".json")):
                crashdump_file = os.path.join(current_dir, file_name)
                if os.path.exists(crashdump_file):
                    dtaf_log_path = os.path.join(dtaf_log_folder, file_name)
                    for i in range(3):
                        try:
                            shutil.move(crashdump_file, dtaf_log_path)
                            break
                        except PermissionError:
                            self._log.info("Unable to move crashdump logs due to Permission issue..")
                            time.sleep(120)
            elif "serial" in file_name and file_name.endswith(".log"):
                serial_log_file = os.path.join(current_dir, file_name)
                if os.path.exists(serial_log_file):
                    dtaf_log_path = os.path.join(dtaf_log_folder, file_name)
                    for i in range(3):
                        try:
                            shutil.move(serial_log_file, dtaf_log_path)
                            break
                        except PermissionError:
                            self._log.info("Unable to move serial logs due to Permission issue..")
                            time.sleep(120)

        # copy logs to CC folder if provided
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

    def run_montana_tdf(self, tdf_filename="getdeviceid.tdf", time="", supress_errors=False):
        """
        Run a Montana framework test

        :return: Number of errors
        """
        dtaf_result = True
        montana_command = "py -3 " + self._montana_abs_path + " -f " + tdf_filename + " -s"

        if time != "":
            montana_command += " -t " + time

        # TODO - Integrate Montana class instead of calling subprocess
        self._log.debug("Calling Montana: " + montana_command)
        error_count = subprocess.call(montana_command)

        if 0 != error_count:
            if not supress_errors:
                self._log.error(montana_command + " returned " + str(error_count) + " # of errors")
                dtaf_result = False
            else:
                # Dont fail when built in policies in cleanup can not be deleted
                self._log.debug(montana_command + " returned " + str(error_count) + " as expected")

        return dtaf_result

    def run_ptu_stress_tool_on_given_cpu(self, cpu):
        """
        This method takes the cpu count per socket and executes ptu tool to stress given cpu.

        :param cpu: cpu count that needs to be stressed, any number or "ALL" if all CPU is to be stressed
        :raise: content_exception.TestUnSupportedError if percentage is greater than 100
        :return: True if ptu tool is running successfully else False
        """
        self._cpu_info_provider.populate_cpu_info()
        self._log.info("Stressing the CPU by running ptu tool")

        # It might be better to check if PTU is running before killing
        self._ptu_provider.kill_ptu_tool()

        # Run PTU stress tool on Given cpu
        if cpu == self.ALL_CPU:
            command_to_exec = self.PTU_CMD_TO_STRESS_CORES.replace("-cpu {}", "")
            self._os.execute_async(command_to_exec, cwd=self.ptu_path)
            self._log.info("Successfully ran ptu on all CPUs")
        else:
            command_to_exec = self.PTU_CMD_TO_STRESS_CORES.format(cpu)
            self._os.execute_async(command_to_exec, cwd=self.ptu_path)
            self._log.info("Successfully ran ptu on cpu {}".format(cpu))

        if self._ptu_provider.check_ptu_app_running():
            ret_val = True
        else:
            self._log.info("Failed to run ptu tool with {} cpu stressed".format(cpu))
            ret_val = False
        return ret_val

    def run_statistics_on_domain1(self):
        """
        Runs statistics.py on domain 1 Montana framework test and returns current power value

        :return: Average Power value
        """
        self._log.info("Run statistics.py on Domain 1")
        montana_command = r"py -3 " + str(self.get_montana_path) + self.GET_STATISTICS_ON_D1_CMD
        power_value = 0
        self._log.debug("Calling Montana: " + montana_command)
        process = subprocess.Popen(montana_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        statistics_results = process.communicate()
        self._log.info("Results of statistics.py : {}".format(statistics_results))
        for each_line in str(statistics_results).split("\\n"):
            if self.AVG_STRING in each_line:
                power_value = each_line.split(":")[1].strip().replace("\\r", "")
        self._log.info("Average Power Value: {}".format(power_value))
        return power_value
