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
from abc import ABCMeta, abstractmethod
from importlib import import_module
from six import add_metaclass
import re
from shutil import copy
from pathlib import Path

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_configuration import ContentConfiguration
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.provider.base_provider import BaseProvider
from src.lib.common_content_lib import CommonContentLib


@add_metaclass(ABCMeta)
class SpsinfoProvider(BaseProvider):
    """
    Spsinfo tool provider for collecting spsinfo firmware version and to verify with content configuration file.
    """
    SPSMANUF_SUCCESS_STR = "spsManuf Test Passed"
    SPSMANUF_FAILURE_STR = "spsManuf Test Failed"
    SPSMANUF_ACTUAL_CFG = "spsmanuf_actual.cfg"
    SPSMANUF_WRONG_CFG = "spsmanuf_wrong.cfg"
    SPS_MANUF_CFG = 'spsManuf.cfg'

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create spsinfo provider tool for collect firmware version

        :param os_obj: os object
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(SpsinfoProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._sut_os = self._os.os_type
        self._common_content_lib = CommonContentLib(log, os_obj, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self.execution_timeout = self._common_content_configuration.get_command_timeout()
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on different os.

        :return: object
        """
        package = r"src.provider.spsinfo_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "VerifySpsinfoWindows"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "VerifySpsinfoLinux"
        else:
            raise NotImplementedError("Test is not implemented for %s" % os_obj.os_type)
        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(log, cfg_opts, os_obj)

    def get_spsmanuf_cfg_path(self, path):
        """
        This function used to find absolute path

        :param path: zipe file host path
        :return: file path
        """
        config_path = None
        for path in Path(os.path.dirname(path)).rglob(self.SPS_MANUF_CFG):
            if self._os.os_type in str(path.absolute()):
                config_path = str(path.absolute())
        if not config_path:
            raise content_exceptions.TestFail("Unable to find sps manf config file")
        self._log.debug("Sps manuf config file path is {}".format(config_path))
        return config_path

    def modify_cfg(self, spsmanu_path, sps_version, sps_file_name):
        """
        This function creates the  sps.manuf config files with the provided sps_version value

        :param spsmanu_path: sps_info tool path on host
        :param sps_version: provided firmware version
        :param sps_file_name: spsmanuf file name

        :raise: content_exception.TestFail if not able to create spsmanuf.cfg with provided fw_version
        """
        cfg_path = self.get_spsmanuf_cfg_path(spsmanu_path)
        search_str = 'SubTestName="Runtime Image FW Version", ReqVal="1.2.3.4", ErrAction="ErrorStop"'
        replace_str = 'SubTestName="Runtime Image FW Version", ReqVal="{}", ErrAction="ErrorStop"'
        replace_status = False
        out_file = os.path.join(os.path.dirname(cfg_path), sps_file_name)
        with open(cfg_path, 'r') as input_file, open(out_file, 'w') as output_file:
            for line in input_file:
                if search_str in line.strip():
                    line = line.replace("//", "")
                    line = line.replace(search_str, replace_str.format(sps_version))
                    output_file.write(line)
                    replace_status = True
                else:
                    output_file.write(line)
        if not replace_status:
            raise content_exceptions.TestFail("unable to modify the cfg file")

    @abstractmethod
    def get_sps_version(self, sut_folder_path):
        """
        execute the command for sps_info tool
        verify firm ware version with the content configuration file
        :param sut_folder_path: sps_info tool path on sut

        :return: actual version
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def spsmanuf_tool_success_test(self, sut_folder_path):
        """
        execute the command for spsmanuf tool and verify firm ware version test success full test results
        of  configuration file

        :param sut_folder_path: spsmanuf tool path on sut
        :raise: content_exception.TestFail if spsmanufwin64 execution did not get success result
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def spsmanuf_tool_success_test_verbose(self, sut_folder_path):
        """
        execute the command for spsmanuf tool and verify fw_version test success test results of configuration file

        :param sut_folder_path: spsmanuf tool path on sut
        :raise: content_exception.TestFail if spsmanufwin64 execution did not get success result
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def spsmanuf_tool_fail_test(self, sut_folder_path):
        """
        execute the command for spsmanuf tool and verify test fail test results of  configuration file
        :param sut_folder_path: spsmanuf tool path on sut
        :raise: content_exception.TestFail if spsmanufwin64 execution did not get failure result
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def spsmanuf_tool_fail_test_verbose(self, sut_folder_path):
        """
        execute the command for spsmanuf tool and verify value of fw_ver test fail test results of  configuration file

        :param sut_folder_path: spsmanuf tool path on sut
        :raise: content_exception.TestFail if spsmanufwin64 execution did not get failure result
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def copy_spstool_sut(self, sps_tool_zip_file_path, sps_info_file_name):
        """
        Copy file from C:/Automation/BKC/Tools to src/lib/collateral folder
        :param sps_tool_zip_file_path: spstool zip file path
        :param sps_info_file_name: sps_tool file name

        :return: spstool folder path on sut
        """
        raise content_exceptions.TestNotImplementedError


class VerifySpsinfoLinux(SpsinfoProvider):
    """
    SPSinfo provider object to verify firmware version with content configuration file
    """
    SPS_EXEC_CMD = 'spsInfoLinux64'
    SPSMANUF_EXEC = "spsManufLinux64"
    CMD_LINUX = 'find $(pwd) -type f -name {}'.format(SPS_EXEC_CMD)
    SPS_FOLDER_NAME = "sps_tools_linux"
    SPS_IMAGE_FW_VERSION = r"((\d+)\.)+\d+\s\(Recovery\)"
    RESULT_FIRMWARE_VER = r"((\d+)\.)+\d+"
    SPSMANUF_EXE_SEARCH_CMD = 'find $(pwd) -type f -name {}'.format(SPSMANUF_EXEC)

    def __init__(self, log, cfg_opts, os_obj):
        """
          Create an instance of verifyspsinfowindows

          :param cfg_opts: Configuration Object of provider
          :param log: Log object
          :param os_obj: os object
        """
        super(VerifySpsinfoLinux, self).__init__(log, cfg_opts, os_obj)

    def get_sps_version(self, sut_folder_path):
        """
        This function returns the actual firmware version after execution.
        :param sut_folder_path: spstool path on sut

        :return : firmware version after execution
        """
        cmd_exe_file, cmd_folder = self.__execute_spstool(sut_folder_path)
        std_out_result = self._common_content_lib.execute_sut_cmd(cmd_exe_file, "Execution", self.execution_timeout,
                                                                  cmd_path=cmd_folder)
        self._log.debug("result after execution of spsInfoLinux64 {}".format(std_out_result))
        res = re.search(self.SPS_IMAGE_FW_VERSION, std_out_result)
        if not res:
            raise content_exceptions.TestFail("Not found the firmware version after executing spstool")
        firmware_ver_exec = re.search(self.RESULT_FIRMWARE_VER, res[0])
        sps_img_fw_version = firmware_ver_exec[0]
        self._log.debug("collecting SPS Image FW version after execution :{}".format(sps_img_fw_version))
        return sps_img_fw_version

    def __execute_spstool(self, sut_folder_path):
        """
        Execute SPS tool
        1. Copy the file from host to SUT and verify
        2. Execute the spsInfoLinux64 and collect firmware version
        3.verify firmware version with configuration version

        :return: executable file, tool_folder path
        """
        # Collecting actual firmware version after execution
        find_executable_path_spsinfo = self._common_content_lib.execute_sut_cmd(
            self.CMD_LINUX, "executable_file", self.execution_timeout, sut_folder_path)
        self._log.debug("Executable file path on sut {}".format(find_executable_path_spsinfo))
        cmd_folder = os.path.dirname(find_executable_path_spsinfo)  # collect directory path for Linux64
        spsinfo_executable_file_name = os.path.basename(find_executable_path_spsinfo)  # collect executable file name
        cmd_exe_file = "./{}".format(spsinfo_executable_file_name)
        return cmd_exe_file, cmd_folder

    def spsmanuf_tool_success_test(self, sut_folder_path):
        """
        Execute the command for spsmanuf tool and verify test successful with test results of  configuration file

        :param sut_folder_path: spsmanuf tool path on sut
        :raise: content_exception.TestFail if spsManufLinux64 execution did not get success result
        """
        try:
            spsmanuf_exe_cmd = "./" + self.SPSMANUF_EXEC + " -f {}".format(self.SPSMANUF_ACTUAL_CFG)
            cmd_exec_folder = self.__execute_spsmanuf_tool(sut_folder_path)
            self._log.info("Result after execution folder path: {}".format(cmd_exec_folder))
            std_out_result = self._os.execute(spsmanuf_exe_cmd, self.execution_timeout, cmd_exec_folder).stdout.strip()
            self._log.debug("Result after execution of spsInfoLinux64 {}".format(std_out_result))
            res = re.search(self.SPSMANUF_SUCCESS_STR, std_out_result)
            if not res:
                raise content_exceptions.TestFail("Sps version is incorrect : {}".format(std_out_result))
            self._log.debug("Spsmanuf tool success test passed: {}".format(res.group(0)))
        except Exception as ex:
            self._log.error("Spsmanuf tool success test failed due to exception : {0}".format(
                    ex))

    def spsmanuf_tool_success_test_verbose(self, sut_folder_path):
        """
        Execute the command for spsmanuf tool and verify fw_version test success test results of configuration file

        :param sut_folder_path: spsmanuf tool path on sut
        :raise: content_exception.TestFail if spsManufLinux64 execution did not get success result
        """
        try:
            spsmanuf_exe_cmd = "./" + self.SPSMANUF_EXEC + " -f {} -verbose".format(self.SPSMANUF_ACTUAL_CFG)
            cmd_exec_folder = self.__execute_spsmanuf_tool(sut_folder_path)
            std_out_result = self._os.execute(spsmanuf_exe_cmd, self.execution_timeout, cwd=cmd_exec_folder).stdout.strip()
            self._log.debug("Result after execution of {}".format(std_out_result))
            res = re.search(self.SPSMANUF_SUCCESS_STR, std_out_result)
            if not res:
                raise content_exceptions.TestFail("Sps version is incorrect: {}".format(std_out_result))
            self._log.debug("Spsmanuf tool success test passed: {}".format(res.group(0)))
        except Exception as ex:
            self._log.error("Spsmanuf tool success test failed due to exception : {0}".format(
                    ex))

    def spsmanuf_tool_fail_test(self, sut_folder_path):
        """
        Execute the command for spsmanuf tool and verify fw_version test fail test results of  configuration file

        :param sut_folder_path: spsmanuf tool path on sut
        :raise: content_exception.TestFail if spsManufLinux64 execution did not get failure result
        """
        try:
            spsmanuf_exe_cmd = "./" + self.SPSMANUF_EXEC + " -f {}".format(self.SPSMANUF_WRONG_CFG)
            cmd_exec_folder = self.__execute_spsmanuf_tool(sut_folder_path)
            std_out_result = self._os.execute(spsmanuf_exe_cmd, self.execution_timeout, cmd_exec_folder)
            self._log.debug("Sps manuf failure execution output {}".format(std_out_result.stdout.strip()))
            res = re.search(self.SPSMANUF_FAILURE_STR, std_out_result.stdout.strip())
            if not res:
                raise content_exceptions.TestFail("Spsmanuf tool did not execute successfully: "
                                                  "{}".format(std_out_result.stdout.strip()))
            self._log.debug("Spsmanuf tool fail test passed: {}".format(res.group(0)))
        except Exception as ex:
            self._log.error("Spsmanuf tool fail test failed due to exception : {0}".format(
                    ex))

    def spsmanuf_tool_fail_test_verbose(self, sut_folder_path):
        """
        Execute the command for spsmanuf tool and verify fw_version test fail test results of  configuration file

        :param sut_folder_path: spsmanuf tool path on sut
        :raise: content_exception.TestFail if spsManufLinux64 execution did not get failure result
        """
        try :
            spsmanuf_exe_cmd = "./" + self.SPSMANUF_EXEC + " -f {} -verbose".format(self.SPSMANUF_WRONG_CFG)
            cmd_exec_folder = self.__execute_spsmanuf_tool(sut_folder_path)
            std_out_result = self._os.execute(spsmanuf_exe_cmd, self.execution_timeout, cmd_exec_folder)
            self._log.debug("Sps manuf failure execution output {}".format(std_out_result.stdout.strip()))
            res = re.search(self.SPSMANUF_FAILURE_STR, std_out_result.stdout.strip())
            if not res:
                raise content_exceptions.TestFail("Spsmanuf tool did not execute successfully: "
                                                  "{}".format(std_out_result.stdout.strip()))
            self._log.debug("Spsmanuf tool fail test passed: {}".format(res.group(0)))
        except Exception as ex:
            self._log.error("Spsmanuf tool fail test failed due to exception : {0}".format(
                    ex))

    def copy_spstool_sut(self, sps_tool_zip_file_path, sps_info_file_name):
        """
        Copy file from C:/Automation/BKC/Tools to src/lib/collateral folder
        :param sps_tool_zip_file_path: sps_tool zipfile
        :param sps_info_file_name: spstool_filename

        return: spstool folder path on sut
        """
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(self.SPS_FOLDER_NAME, sps_tool_zip_file_path)
        self._log.debug("Copying file to sut location {}".format(sut_folder_path))
        return sut_folder_path

    def __execute_spsmanuf_tool(self, sut_folder_path):
        """
        Execute SPSManuf tool for windows

        1. Copy the file from host to Linux SUT and verify
        2. Gets the path of spsInfoLinux64.exe file path

        :param sut_folder_path : spstool path on sut
        :return: spstool Linux64 folder path
        """
        find_exe_path_spsinfo = self._common_content_lib.execute_sut_cmd(self.SPSMANUF_EXE_SEARCH_CMD,
                                                                         "find_folderpath",
                                                                         self.execution_timeout, sut_folder_path)
        self._log.debug("After cmd execution  {}".format(find_exe_path_spsinfo))
        sps_info_folder_name = os.path.dirname(find_exe_path_spsinfo.strip())  # collecting directory path linux
        self._log.debug("Spsinfolinux64 file path {}".format(sps_info_folder_name))
        return sps_info_folder_name


class VerifySpsinfoWindows(SpsinfoProvider):
    """
    verifyspsinfo windows provider object to verify firmware version with content configuration file
    """
    SPSINFO_EXEC_CMD = "spsInfoWin64.exe"
    SPSMANUF_EXEC = "spsManufWin64.exe"
    SPS_IMAGE_FW_VERSION = r"((\d+)\.)+\d+\s\(Recovery\)"
    RESULT_FIRMWARE_VER = r"((\d+)\.)+\d+"
    SPS_FOLDER_NAME = r"C:\sps_tool_windows"
    WIN_FILE_SEARCH_CMD = "powershell.exe (get-childitem '{}' -File {} -recurse).fullname".format(
        SPS_FOLDER_NAME, SPSINFO_EXEC_CMD)
    SPSMANUF_EXE_SEARCH_CMD = "powershell.exe (get-childitem '{}' -File {} -recurse).fullname".format(
        SPS_FOLDER_NAME, SPSMANUF_EXEC)

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create an instance of verifyspsinfowindows

        :param cfg_opts: Configuration Object of provider
        :param log: Log object
        :param os_obj: os object
        """
        super(VerifySpsinfoWindows, self).__init__(log, cfg_opts, os_obj)

    def get_sps_version(self, sut_folder_path):
        """
        This function returns the actual firmware version after execution

        :param sut_folder_path: spstool path on sut
        :return: firmware version after execution
        """
        cmd_exec_folder = self.__execute_spstool(sut_folder_path)
        std_out_result = self._common_content_lib.execute_sut_cmd(
            self.SPSINFO_EXEC_CMD, "Execution", self.execution_timeout, cmd_path=cmd_exec_folder)
        self._log.debug("result after execution of spsInfoWindows64 {}".format(std_out_result))
        res = re.search(self.SPS_IMAGE_FW_VERSION, std_out_result)
        if not res:
            raise content_exceptions.TestFail("Not found the firmware version after executing spstool: {}"
                                              .format(res))
        firmware_ver_exec = re.search(self.RESULT_FIRMWARE_VER, res[0])
        sps_img_fw_version = firmware_ver_exec[0]
        self._log.debug("Collecting SPS Image FW version after execution :{}".format(sps_img_fw_version))
        return sps_img_fw_version

    def copy_spstool_sut(self, sps_tool_zip_file_path, sps_info_file_name):
        """
        Copy file from C:/Automation/BKC/Tools to src/lib/collateral folder
        :param sps_tool_zip_file_path : zip file path
        :param sps_info_file_name : spstool file name

        :return: spsinfo tool  folder path
        """
        sut_folder_path = self._install_collateral.download_and_copy_zip_to_sut(os.path.split(self.SPS_FOLDER_NAME)[-1].strip(),
                                                                        sps_info_file_name)
        self._log.debug("Copy sps_tools zip file to windows sut {}".format(sut_folder_path))
        return sut_folder_path

    def spsmanuf_tool_success_test(self, sut_folder_path):
        """
        Execute the command for spsmanuf tool and verify fw_version test success test results of configuration file

        :param sut_folder_path: spsmanuf tool path on sut
        :raise: content_exception.TestFail if spsmanufwin64 execution did not get success result
        """
        try:
            spsmanuf_exe_cmd = self.SPSMANUF_EXEC + " -f {}".format(self.SPSMANUF_ACTUAL_CFG)
            cmd_exec_folder = self.__execute_spsmanuf_tool(sut_folder_path)
            self._log.info("Result after execution folder path: {}".format(cmd_exec_folder))
            std_out_result = self._os.execute(spsmanuf_exe_cmd, self.execution_timeout, cwd=cmd_exec_folder).stdout.strip()
            self._log.debug("Result after execution of spsManufWin64 {}".format(std_out_result))
            res = re.search(self.SPSMANUF_SUCCESS_STR, std_out_result)
            if not res:
                raise content_exceptions.TestFail("Sps version is incorrect : {}".format(std_out_result))
            self._log.debug("Spsmanuf tool success test passed: {}".format(res.group(0)))
        except Exception as ex:
            self._log.error("Spsmanuf tool fail test failed due to exception : {0}".format(
                    ex))

    def spsmanuf_tool_success_test_verbose(self, sut_folder_path):
        """
        Execute the command for spsmanuf tool and verify fw_version test success test results of configuration file

        :param sut_folder_path: spsmanuf tool path on sut
        :raise: content_exception.TestFail if spsmanufwin64 execution did not get success result
        """
        try:
            spsmanuf_exe_cmd = self.SPSMANUF_EXEC + " -f {} -verbose".format(self.SPSMANUF_ACTUAL_CFG)
            cmd_exec_folder = self.__execute_spsmanuf_tool(sut_folder_path)
            std_out_result = self._os.execute(spsmanuf_exe_cmd, self.execution_timeout, cwd=cmd_exec_folder).stdout.strip()
            self._log.debug("Result after execution of spsManufWin64 {}".format(std_out_result))
            res = re.search(self.SPSMANUF_SUCCESS_STR, std_out_result)
            if not res:
                raise content_exceptions.TestFail("Sps version is incorrect: {}".format(std_out_result))
            self._log.debug("Spsmanuf tool success test passed: {}".format(res.group(0)))
        except Exception as ex:
            self._log.error("Spsmanuf tool success test failed due to exception : {0}".format(
                    ex))

    def spsmanuf_tool_fail_test(self, sut_folder_path):
        """
        Execute the command for spsmanuf tool and verify fw_version test fail test results of  configuration file

        :param sut_folder_path: spsmanuf tool path on sut
        :raise: content_exception.TestFail if spsmanufwin64 execution did not get failure result
        """
        try:
            spsmanuf_exe_cmd = self.SPSMANUF_EXEC + " -f {}".format(self.SPSMANUF_WRONG_CFG)
            cmd_exec_folder = self.__execute_spsmanuf_tool(sut_folder_path)
            std_out_result = self._os.execute(spsmanuf_exe_cmd, self.execution_timeout, cmd_exec_folder)
            self._log.debug("Sps manuf failure execution output {}".format(std_out_result.stdout.strip()))
            res = re.search(self.SPSMANUF_FAILURE_STR, std_out_result.stdout.strip())
            if not res:
                raise content_exceptions.TestFail("Spsmanuf tool did not execute successfully: "
                                                  "{}".format(std_out_result.stdout.strip()))
            self._log.debug("Spsmanuf tool fail test passed: {}".format(res.group(0)))
        except Exception as ex:
            self._log.error("Spsmanuf tool fail test failed due to exception : {0}".format(
                    ex))

    def spsmanuf_tool_fail_test_verbose(self, sut_folder_path):
        """
        Execute the command for spsmanuf tool and verify fw_version test fail test results of  configuration file

        :param sut_folder_path: spsmanuf tool path on sut
        :raise: content_exception.TestFail if spsmanufwin64 execution did not get failure result
        """
        try:
            spsmanuf_exe_cmd = self.SPSMANUF_EXEC + " -f {} -verbose".format(self.SPSMANUF_WRONG_CFG)
            cmd_exec_folder = self.__execute_spsmanuf_tool(sut_folder_path)
            std_out_result = self._os.execute(spsmanuf_exe_cmd, self.execution_timeout, cmd_exec_folder)
            self._log.debug("Sps manuf failure execution output {}".format(std_out_result.stdout.strip()))
            res = re.search(self.SPSMANUF_FAILURE_STR, std_out_result.stdout.strip())
            if not res:
                raise content_exceptions.TestFail("Spsmanuf tool did not execute successfully: "
                                                  "{}".format(std_out_result.stdout.strip()))
            self._log.debug("Spsmanuf tool fail test passed: {}".format(res.group(0)))
        except Exception as ex:
            self._log.error("Spsmanuf tool fail test failed due to exception : {0}".format(
                    ex))

    def __execute_spstool(self, sut_folder_path):
        """
        Execute SPS tool for windows

        1. Copy the file from host to WindowsSUT and verify
        2. Execute the spsInfowin64.exe and collect firm version
        sut_folder_path : spstool path on sut

        :return: spstool windows64 folder path
        """
        find_exe_path_spsinfo = self._common_content_lib.execute_sut_cmd(self.WIN_FILE_SEARCH_CMD, "find_folderpath",
                                                                         self.execution_timeout, sut_folder_path)
        self._log.debug("after cmd_win execution  {}".format(find_exe_path_spsinfo))
        sps_info_folder_name = os.path.dirname(find_exe_path_spsinfo.strip())  # collecting directory path Windows64
        self._log.debug("spsinfowin64 file path {}".format(sps_info_folder_name))
        return sps_info_folder_name

    def __execute_spsmanuf_tool(self, sut_folder_path):
        """
        Execute SPSManuf tool for windows

        1. Copy the file from host to WindowsSUT and verify
        2. Gets the path of spsInfowin64.exe file path

        :param sut_folder_path : spstool path on sut
        :return: spstool windows64 folder path
        """
        find_exe_path_spsinfo = self._common_content_lib.execute_sut_cmd(self.SPSMANUF_EXE_SEARCH_CMD,
                                                                         "find_folderpath",
                                                                         self.execution_timeout, sut_folder_path)
        self._log.debug("After cmd_win execution  {}".format(find_exe_path_spsinfo))
        sps_info_folder_name = os.path.dirname(find_exe_path_spsinfo.strip())  # collecting directory path Windows64
        self._log.debug("Spsinfowin64 file path {}".format(sps_info_folder_name))
        return sps_info_folder_name
