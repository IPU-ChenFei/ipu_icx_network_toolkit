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

import csv
import os
import threading
import time

import six

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path
from abc import ABCMeta, abstractmethod
from importlib import import_module
from six import add_metaclass

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.install_collateral import InstallCollateral
from src.provider.base_provider import BaseProvider
from src.provider.cpu_info_provider import CpuInfoProvider
from src.lib.dtaf_content_constants import TimeConstants


@add_metaclass(ABCMeta)
class PTUProvider(BaseProvider):
    """ Class to provide stress test app functionality """

    WAIT_TIME = 30
    LOG_FILE_NAME = "loginfo_ptumon.csv"
    LOG_FILE_NAME1 = "loginfo_ptumsg.csv"
    PTU_LOG_FILES = [LOG_FILE_NAME, LOG_FILE_NAME1]
    PTU_SUT_FOLDER_NAME = "ptu"

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new PTUProvider object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        """
        super(PTUProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj
        self._cfg_opts = cfg_opts
        self._sut_os = self._os.os_type
        self._percent_cores_to_stress = 100
        self._present_cpu_to_stress = "0xFFFF"  # By Default Stress on All CPUs
        self._list_cpu_mask_values = ['0x1', '0x2', '0x3', '0x4', '0x5', '0x6', '0x7', '0x8']
        self._num_sockets = 0
        self._list_resolved_cores = []
        self._core_mask = 0
        self._list_core_mask = []
        self._ptu_path = None
        self._ptu_kill_path = None

        #  common_content_obj and config object
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.
        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param cfg_opts: cfg_opts

        :return: object
        """
        package = r"src.provider.ptu_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "WindowsPTU"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "LinuxPTU"
        else:
            raise NotImplementedError("Test is not implemented for %s" % os_obj.os_type)
        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(log=log, cfg_opts=cfg_opts, os_obj=os_obj)

    @abstractmethod
    def install_ptu(self):
        """
        This method will copy and install PTU tool

        :raise: NotImplementedError
        """
        raise NotImplementedError

    def set_percent_cores_to_stress(self, percent_value):
        """
        This method will set the % of CORES to be stressed. Valid values are from 1 to 100%

        :param percent_value: percent of cores to stress
        :raise: content_exceptions.TestUnSupportedError for invalid % value
        """
        if 0 < percent_value <= 100:
            self._percent_cores_to_stress = percent_value
        else:
            raise content_exceptions.TestUnSupportedError("Please specify percent_value between 1 and 100%")

    def set_cpu_mask(self, cpu_mask):
        """
        This method will set which CPU to be stressed. Valid values are from 0x1 to 0x8 CPUs

        :param cpu_mask: which CPU to stress.
        :raise: content_exceptions.TestUnSupportedError for invalid cpu hexa number
        """
        if 0 < cpu_mask <= 8:
            self._present_cpu_to_stress = "0x" + str(cpu_mask)
        else:
            raise content_exceptions.TestUnSupportedError("Please specify cpu_mask between 0x1 to 0x8.")

    def _set_core_mask(self):
        self._cpu_provider.populate_cpu_info()
        total_cores = int(self._cpu_provider.get_number_of_cores())
        no_sockets = int(self._cpu_provider.get_number_of_sockets())
        cores_per_socket = total_cores / no_sockets

        self._log.info("Cores per socket={}".format(cores_per_socket))

        num_cores_to_mask = cores_per_socket * self._percent_cores_to_stress / 100
        # bit mask value generation
        str_core_mask = '1' * int(num_cores_to_mask)
        self._core_mask = hex(int(str_core_mask, 2))
        self._log.info("Percent cores to stress:'{}' and "
                       "Core_mask value:'{}'.".format(self._percent_cores_to_stress, self._core_mask))

    @abstractmethod
    def execute_async_ptu_tool(self, ptu_cmd, executor_path=None):
        """
        Execute the PTU app test file with specific waiting time.

        :param ptu_cmd: command to run the ptu app test
        :param executor_path: Path of the ptu app tool.
        :return : None
        :raise: Testfail exception is failed to run ptu test
        """
        raise NotImplementedError

    @abstractmethod
    def check_ptu_app_running(self):
        """
        This method check whether application is running or not

        :return : check_app_running method returns False if particular application is not running e
        :raise: None
        """

        raise NotImplementedError

    @abstractmethod
    def kill_ptu_tool(self):
        """
        Terminate PTU process.

        :raise: Raise RuntimeError Exception if failed to kill the PTU.
        """
        raise NotImplementedError

    @abstractmethod
    def capture_ptu_logs(self, log_folder):
        """
        Copy PTU logs to specified folder in HOST system.

        :param log_folder: log folder name in host system

        :raise: Raise RuntimeError Exception if failed to copy log files.
        """
        raise NotImplementedError

    @abstractmethod
    def get_column_data(self, cpu, column, filename):
        """
        Get particular column data of the device.

        :param device: Device name
        :param column: column name.
        :param filename: csv file.
        :return: python dictionary format
        """
        raise NotImplementedError


class LinuxPTU(PTUProvider):
    """ Class to provide PTU tool functionality for linux platform """

    PTU_VER = "2.5.6"  # update this version when we check-in new version of PTU
    ROOT_PATH = "/root"
    PTU_INSTALLER_NAME = "unified_server_ptu.tar.gz"
    PTU_SUT_FOLDER_NAME = "ptu"

    PTU_CPU = "CPU{}"

    PTU_POWER = "Power"
    PTU_UTILS = "Utils"
    SUT_LOG_FILE_PATH = "/root/ptu/log"

    SUT_PTU_LOG_FOLDER = "/root/ptu/log/"
    KILL_PTU_CMD = "sh ./killptu.sh"
    DEVICE_INDEX = 1

    PTU_APP_NAME = "./ptu"
    PTU_DEFAULT_CMD = "-mon -t {} -log -csv".format(TimeConstants.TEN_MIN_IN_SEC)
    PTU_TURBO_CMD = "–cp 100 -ct 4 –avx 2 –b 1 -t {} -log -csv".format(TimeConstants.TEN_MIN_IN_SEC)
    PTUMON_DEFAULT = "{} -mon -log -csv -logname loginfo -y".format(PTU_APP_NAME)
    PTUMON_CPU_CT1 = "{} -mon -log -csv -logname loginfo -ct 1 -y".format(PTU_APP_NAME)
    PTUMON_CPU_CT3 = "{} -mon -log -csv -logname loginfo -ct 3 -y".format(PTU_APP_NAME)
    PTUMON_CPU_CT6 = "{} -mon -log -csv -logname loginfo -ct 6 -y".format(PTU_APP_NAME)
    PTUMON_CPU_MEM_CT1_MT3 = "{} -mon -log -csv -logname loginfo -ct 1 -mt 3 -y".format(PTU_APP_NAME)
    PTUMON_CPU_MEM_CT3_MT3 = "{} -mon -log -csv -logname loginfo -ct 3 -mt 3 -y".format(PTU_APP_NAME)
    PTUMON_CPU_MEM_CT6_MT3 = "{} -mon -log -csv -logname loginfo -ct 3 -mt 6 -y".format(PTU_APP_NAME)
    PTUMON_MEM_MT3 = "{} -mon -log -csv -logname loginfo -mt 3 -y".format(PTU_APP_NAME)

    SUPPORTED_PTU_CMD_LINE = [PTUMON_DEFAULT, PTUMON_CPU_CT1, PTUMON_CPU_CT3, PTUMON_CPU_CT6, PTUMON_CPU_MEM_CT1_MT3,
                              PTUMON_CPU_MEM_CT3_MT3, PTUMON_CPU_MEM_CT6_MT3, PTUMON_MEM_MT3, PTU_DEFAULT_CMD,
                              PTU_TURBO_CMD]

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new LinuxPTU object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param cfg_opts: cfg_opts
        """
        super(LinuxPTU, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj
        self._cfg_opts = cfg_opts
        self._install_collateral = InstallCollateral(self._log, self._os, self._cfg_opts)
        self._cpu_provider = CpuInfoProvider.factory(log, cfg_opts, self._os)

        self._ptu_path = Path(os.path.join(self.ROOT_PATH, self.PTU_SUT_FOLDER_NAME)).as_posix()

    def factory(self, log, cfg_opts, os_obj):
        pass

    def is_ptu_installed(self):
        try:
            cmd_line = "ls {}".format(self._ptu_path)
            result = self._os.execute(cmd_line, self._command_timeout, self._ptu_path)
            if result.cmd_failed():
                print("PTU not installed")
                return False
            cmd_line = self.PTU_APP_NAME + " -v"
            result = self._os.execute(cmd_line, self._command_timeout, self._ptu_path)
            self._log.info("The PTU version details:{}.".format(result.stdout))
            if self.PTU_VER in result.stdout:
                return True
            self._log.info("PTU is not installed.")
            return False
        except Exception as ex:
            self._log.debug("is_ptu_installed failed with exception: '{}'.".format(ex))
            return False

    def install_ptu(self):
        """
        This method will copy and install ptu application into sut

        """
        # if self.is_ptu_installed():
        #     self._log.info("PTU version '{}' is already installed.".format(self.PTU_VER))
        #     return self._ptu_path
        # else:
        return self._install_collateral.install_ptu(self.PTU_SUT_FOLDER_NAME, self.PTU_INSTALLER_NAME)

    def install_ptusys(self, put_path):
        """
        This method installs ptusys.ko

        :param put_path: path to ptu folder
        :return: True if ptusys installed else False
        """
        try:
            putsys_path = Path(os.path.join(put_path, "driver", "ptusys")).as_posix()
            self._log.info("Ptusys driver path='{}'".format(putsys_path))
            cmd_line = "make clean all"
            cmd_result = self._os.execute(cmd_line, self._command_timeout, putsys_path)
            if cmd_result.cmd_failed():
                self._log.error("Failed to execute '{}' with error:'{}'.".format(cmd_line, cmd_result.stderr))
                return False
            # remove the ptusys from kernel
            cmd_line = "rmmod ptusys"
            cmd_result = self._os.execute(cmd_line, self._command_timeout, putsys_path)
            if cmd_result.cmd_failed():
                self._log.debug("Failed to execute '{}' with error:'{}'.".format(cmd_line, cmd_result.stderr))
            else:
                self._log.info("The driver 'ptusys.ko' removed from kernel module.")
            # install the ptusys kernel driver
            cmd_line = "make install"
            cmd_result = self._os.execute(cmd_line, self._command_timeout, putsys_path)
            if cmd_result.cmd_failed():
                self._log.error("Failed to execute '{}' with error:'{}'.".format(cmd_line, cmd_result.stderr))
                return False
            self._log.info("The kernel driver 'ptusys.ko' successfully installed.")
            return True
        except Exception as ex:
            self._log.error("Failed to install ptusys.ko driver with exception: '{}'".format(ex))
            return False

    def execute_async_ptu_tool(self, ptu_cmd, executor_path=None):
        """
        Execute the PTU app test file with specific waiting time.
        :param ptu_cmd: command to run the ptu app test
        :param executor_path: Path of the ptu app tool.
        :return : None
        :raise: TestSetupError exception if failed to run ptu test
        """
        if executor_path is None:
            raise content_exceptions.TestSetupError("PTU path should not be NULL.")
        if not self.install_ptusys(executor_path):
            self._log.error("Failed to install 'ptusys.ko' kernel driver.")
        if ptu_cmd not in self.SUPPORTED_PTU_CMD_LINE:
            raise content_exceptions.TestSetupError("Specified ptu command '{}' is not supported.".format(ptu_cmd))

        if (0 < self._percent_cores_to_stress < 100) and (str(self._present_cpu_to_stress) in
                                                          str(self._list_cpu_mask_values)):
            self._set_core_mask()
            ptu_cmd = ptu_cmd + " -cpucore " + str(self._core_mask)
            ptu_cmd = ptu_cmd + " -cpu " + str(self._present_cpu_to_stress)
        elif 0 < self._percent_cores_to_stress < 100:
            self._set_core_mask()
            ptu_cmd = ptu_cmd + " -cpucore " + str(self._core_mask)
        elif str(self._present_cpu_to_stress) in str(self._list_cpu_mask_values):
            ptu_cmd = ptu_cmd + " -cpu " + str(self._present_cpu_to_stress)

        self._log.info("Starting the PTU Tool command '{}'".format(ptu_cmd))
        self._os.execute_async(ptu_cmd, cwd=executor_path)
        time.sleep(self.WAIT_TIME)
        if not self.check_ptu_app_running():
            raise content_exceptions.TestSetupError("Failed to launch {} tool..".format(ptu_cmd))

    def check_ptu_app_running(self):
        """
        This method check whether application is running or not

        :return : check_app_running method returns False if particular application is not running e
        :raise: None
        """
        cmd_line = "ps -ef |grep {}".format(self.PTU_SUT_FOLDER_NAME)
        command_result = self._common_content_lib.execute_sut_cmd(cmd_line, "Checks the app status",
                                                                  self._command_timeout)
        self._log.debug(command_result)
        if self.PTU_APP_NAME in command_result:
            self._log.info("PTU application running.")
            return True
        self._log.info("PTU application not running.")
        return False

    def kill_ptu_tool(self):
        """
        Terminate PTU process.

        :raise: Raise RuntimeError Exception if failed to kill the PTU.
        """
        # we will ignore any exception
        ret_code = False
        try:
            ret_val = self._os.execute(self.KILL_PTU_CMD, self._command_timeout, self._ptu_path)
            if ret_val.return_code == 0:
                ret_code = True
                self._log.debug(ret_val.stdout)
            else:
                self._log.error("Failed to kill PTU application error:'{}'".format(ret_val.stderr))
        except Exception as ex:
            self._log.debug("Failed to kill ptu with exception: '{}'".format(ex))
        return ret_code

    def parse_ptu_monitor_csv_data(self, filename):
        """
        parse the PTU mon data

        :param filename: csv file
        :return: python dictionary format
        """
        data = {}
        with open(filename, 'r') as csvfile:
            # creating a csv reader object
            csvreader = csv.reader(csvfile)
            # extracting field names through first row
            fields = next(csvreader)

            # extracting each data row one by one
            for row in csvreader:

                if row[self.DEVICE_INDEX].strip() not in data.keys():
                    data[row[self.DEVICE_INDEX].strip()] = []
                for i in range(2, len(row)):
                    data[row[self.DEVICE_INDEX].strip()].append({fields[i].strip(): row[i].strip()})

        return data

    def capture_ptu_logs(self, log_folder):
        """
        Copy PTU logs to specified folder in HOST system.

        :param log_folder: log folder name in host system

        :raise: Raise RuntimeError Exception if failed to copy log files.
        """
        cmd_line = "ls {}"
        for log_name in self.PTU_LOG_FILES:
            try:
                log_file = Path(os.path.join(self.SUT_PTU_LOG_FOLDER, log_name)).as_posix()
                cmd_line = cmd_line.format(log_file)
                result = self._os.execute(cmd_line, self._command_timeout)
                if result.cmd_passed():
                    host_dest_path = Path(os.path.join(log_folder, log_name)).as_posix()
                    self._os.copy_file_from_sut_to_local(log_file, host_dest_path)
                else:
                    self._log.error("Failed to copy PTU log file '{}' to host system with "
                                    "error:'{}'.".format(log_file, result.stderr))
            except Exception as ex:
                self._log.error("Failed to copy PTU logs to host system due to "
                                "exception: '{}'.".format(ex))

    def get_column_data(self, device, column, filename):
        """
        Get particular column data of the device.

        :param device: Device name
        :param column: column name.
        :param filename: csv file.
        :return: python dictionary format
        """
        data = self.parse_ptu_monitor_csv_data(filename)
        required_data = []
        try:
            cpu_data = data[device]
            for item in cpu_data:
                if column in item.keys():
                    required_data.append(item[column])
        except KeyError:
            raise content_exceptions.TestFail("%s is not found in the PTU mon data" % device)
        return required_data


class WindowsPTU(PTUProvider):
    """ Class to provide PTU test app functionality for windows platform """

    PTU_INSTALLER_NAME = "Intel_Power_Thermal_Utility.zip"
    DEVICE_INDEX = 1
    PTU_CPU = "CPU{}"
    C_PATH = "C:\\"

    PTU_APP_NAME = "PTU.exe"
    PTU_DEFAULT_CMD = "-mon -t {} -log -csv".format(TimeConstants.TEN_MIN_IN_SEC)
    PTU_TURBO_CMD = "–cp 100 -ct 4 –avx 2 –b 1 -t {} -log -csv".format(TimeConstants.TEN_MIN_IN_SEC)
    PTUMON_DEFAULT = " -mon -log -csv -log"
    PTUMON_CPU_CT1 = " -ct 1"
    PTUMON_CPU_CT3 = " -mon -log -csv -ct 3"
    PTUMON_CPU_CT6 = " -mon -log -csv -ct 6"
    PTUMON_CPU_MEM_CT1_MT3 = " -mon -log -csv -ct 1 -mt 3"
    PTUMON_CPU_MEM_CT3_MT3 = " -mon -log -csv -ct 3 -mt 3"
    PTUMON_CPU_MEM_CT6_MT3 = " -mon -log -csv -ct 3 -mt 6"
    PTUMON_MEM_MT3 = " -mon -log -csv -mt 3"

    SUPPORTED_PTU_CMD_LINE = [PTUMON_DEFAULT, PTUMON_CPU_CT1, PTUMON_CPU_CT3, PTUMON_CPU_CT6, PTUMON_CPU_MEM_CT1_MT3,
                              PTUMON_CPU_MEM_CT3_MT3, PTUMON_CPU_MEM_CT6_MT3, PTUMON_MEM_MT3, PTU_DEFAULT_CMD,
                              PTU_TURBO_CMD]

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new WindowsPTU object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param cfg_opts: cfg_opts
        """
        super(WindowsPTU, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj
        self._cfg_opts = cfg_opts
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)

        self._cpu_provider = CpuInfoProvider.factory(log, cfg_opts, self._os)

        self.stress_thread = None

    def factory(self, log, cfg_opts, os_obj):
        pass

    def find_ptu_installed_path(self):
        """
        This method will get the path of the installed PTU tool

        :return config_file_src_path
        """
        try:
            cmd_line = "where /R {} {}".format(self.C_PATH, self.PTU_APP_NAME)
            result = self._os.execute(cmd_line, self._command_timeout)
            if result.cmd_failed():
                self._log.error("PTU not installed")
                return False

            # If multiple PTU.exe available in C:, will pick the one that has the below string in the path
            for line in result.stdout.split("\n"):
                if "Power Thermal Utility".lower() in str(line).lower():
                    return line
            return False
        except Exception as ex:
            self._log.debug("find_ptu_installed_path failed with exception: '{}'.".format(ex))
            return False

    def install_ptu(self):
        """
        This method will copy and install PTU tool
        """
        return self._install_collateral.install_ptu(self.PTU_SUT_FOLDER_NAME, self.PTU_INSTALLER_NAME)

    def _execute_stress_tool(self, cmd, stress_path, timeout=60):
        """
        Function to execute stress application.

        :param cmd: command to run stress tool
        :param stress_path: path of the executor.
        """
        self._log.info("Starting the stress test..")

        # -t refers to torture test
        self._log.debug("stress test command line is '{}'".format(cmd))
        self._log.info("stress test is running from directory '{}'".format(stress_path))

        stress_execute_res = self._os.execute('"{}" {}'.format(stress_path, cmd), (timeout + self._command_timeout))

        self._log.info("Stress test execution is completed with return code: {}.".format(stress_execute_res.return_code))

    def execute_async_ptu_tool(self, ptu_cmd, executor_path=None):
        """
        Execute the PTU app test file with specific waiting time.

        :param ptu_cmd: ptu tool C state and Util commands
        :param executor_path: Path of the ptu app tool.
        :return : None
        :raise: TestFail exception is failed to run ptu test
        """
        executor_path = (self.find_ptu_installed_path()).strip()
        if not executor_path:
            raise content_exceptions.TestFail("PTU Tool Not installed in the SUT ...")

        if ptu_cmd not in self.SUPPORTED_PTU_CMD_LINE:
            raise content_exceptions.TestSetupError("Specified ptu command '{}' is not supported.".format(ptu_cmd))

        if (0 < self._percent_cores_to_stress < 100) and (str(self._present_cpu_to_stress) in
                                                          str(self._list_cpu_mask_values)):
            self._set_core_mask()
            ptu_cmd = ptu_cmd + " -cpucore " + str(self._core_mask)
            ptu_cmd = ptu_cmd + " -cpu " + str(self._present_cpu_to_stress)
        elif 0 < self._percent_cores_to_stress < 100:
            self._set_core_mask()
            ptu_cmd = ptu_cmd + " -cpucore " + str(self._core_mask)
        elif str(self._present_cpu_to_stress) in str(self._list_cpu_mask_values):
            ptu_cmd = ptu_cmd + " -cpu " + str(self._present_cpu_to_stress)

        self._log.info("Starting the PTU Tool command '{}'".format(ptu_cmd))

        cmd_line = '"{}" {}'.format(executor_path, ptu_cmd)
        self._log.info("PTU executing command %s", cmd_line)
        self.stress_thread = threading.Thread(target=self._execute_stress_tool,
                                              args=(ptu_cmd, executor_path, 84600))
        # Thread has been started
        self.stress_thread.start()
        self._log.info("Sleep for {} second(s) before checking the process running.".format(self.WAIT_TIME))
        time.sleep(self.WAIT_TIME)
        if not self.check_ptu_app_running():
            raise content_exceptions.TestFail("{} stress tool is not running ".format("ptu"))

    def check_ptu_app_running(self):
        """
        This method check whether application is running or not

        :return : check_app_running method returns False if particular application is not running else True
        :raise: None
        """
        self._log.info("Checks the app status")
        process_running = self._common_content_lib.execute_sut_cmd(
            'TASKLIST /FI "IMAGENAME eq {}*"'.format(self.PTU_SUT_FOLDER_NAME), "Checks the app status",
            self._command_timeout)

        if str(self.PTU_SUT_FOLDER_NAME).lower() in str(process_running).lower():
            self._log.info("PTU application running.")
            return True
        self._log.info("PTU application not running.")
        return False

    def kill_ptu_tool(self):
        """
        Terminate PTU process.

        :return : kill ptu app
        :raise: Raise RuntimeError Exception if failed to kill the PTU.
        """
        # we will ignore any exception
        ret_code = False
        try:
            if not self.check_ptu_app_running():
                self._log.error("{} stress tool is not running to kill ".format(self.PTU_SUT_FOLDER_NAME))
                return
            self._log.info("killing {} tool".format(self.PTU_SUT_FOLDER_NAME))
            kill_ptu = self._os.execute("taskkill /F /IM {}.exe".format(self.PTU_SUT_FOLDER_NAME),
                                        self._command_timeout)

            if kill_ptu.return_code == 0:
                ret_code = True
                self._log.debug(kill_ptu.stdout)
            else:
                self._log.error("Failed to kill PTU application error:'{}'".format(kill_ptu.stderr))

            self.stress_thread.join(120)

        except Exception as ex:
            self._log.debug("Failed to kill ptu with exception: '{}'".format(ex))

        return ret_code

    def parse_ptu_monitor_csv_data(self, filename):
        """ parse the PTU mon data

        :param filename: csv file
        :return: python dictionary format
        """
        data = {}
        with open(filename, 'r') as csvfile:
            # creating a csv reader object
            csvreader = csv.reader(csvfile)
            # extracting field names through first row
            fields = next(csvreader)

            # extracting each data row one by one
            for row in csvreader:

                if row[self.DEVICE_INDEX].strip() not in data.keys():
                    data[row[self.DEVICE_INDEX].strip()] = []
                for i in range(2, len(row)):
                    data[row[self.DEVICE_INDEX].strip()].append({fields[i].strip(): row[i].strip()})

        return data

    def capture_ptu_logs(self, log_folder):
        """
        Copy PTU logs to specified folder in HOST system.

        :param log_folder: log folder name in host system

        :raise: Raise RuntimeError Exception if failed to copy log files.
        """
        pass

    def get_column_data(self, device, column, filename):
        """
        Get particular column data of the device.

        :param device: Device name
        :param column: column name.
        :param filename: csv file.
        :return: python dictionary format
        """
        data = self.parse_ptu_monitor_csv_data(filename)
        required_data = []
        try:
            cpu_data = data[device]
            for item in cpu_data:
                if column in item.keys():
                    required_data.append(item[column])
        except KeyError:
            raise content_exceptions.TestFail("%s is not found in the PTU mon data" % device)
        return required_data
