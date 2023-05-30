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

import re
import os
import subprocess

import requests
import six
import platform

from src.lib.tools_constants import Artifactory, ArtifactoryFolderNames

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.lib.dtaf_constants import OperatingSystems, Framework
from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration


class ContentArtifactoryUtils(object):
    """
    Class to download Tools from Artifactory.
    """

    FILE_NOT_FOUND_ERROR = "404 Not Found"
    ROOT_PATH = "/root"

    def __init__(self, test_log, os=None, common_content_lib=None, cfg_opts=None):
        self._os = os
        self._common_content_lib = common_content_lib
        self._common_content_configuration = ContentConfiguration(test_log)
        self._log = test_log
        self._cfg = cfg_opts
        pass

    def artifactory_download_tool_to_host(self, artifactory_tool_path, host_tool_path, host_tool_folder_path):
        """
        Helper methods that performs the artifactory tool download to the host

        :param artifactory_tool_path
        :param host_tool_path
        :param host_tool_folder_path
        """
        self._log.info("Downloading the Tools from Artifactory...")
        full_command = Artifactory.DOWNLOADING_CMD.format(artifactory_tool_path, host_tool_path)
        self._log.info("Curl Command to copy Tools to Host- {}".format(full_command))
        try:
            std_out = self._execute_cmd_on_host(cmd_line=full_command)
        except Exception as exception:
            if self.FILE_NOT_FOUND_ERROR in str(exception):
                log_error = "Please Upload the Tools in Artifactory Under Path- '{}'".format(artifactory_tool_path)
                self._log.error(log_error)
                raise content_exceptions.TestSetupError(log_error)
            else:
                raise content_exceptions.TestSetupError(exception)

        self._log.info("Downloading output - {}".format(std_out))
        self._log.info("Tools got Downloaded from Artifactory to the Host path- {}".format(host_tool_folder_path))

    def download_tool_to_automation_tool_folder(self, tool_name, exec_env=None):
        """
        This method is to Download the tools from artifactory to C:\Automation\Tool

        :param tool_name
        :param exec_env
        :return tool path
        """
        exec_os = platform.system()

        try:
            cfg_file_default = Framework.CFG_BASE
        except KeyError:
            err_log = "Error - execution OS " + str(exec_os) + " not supported!"
            self._log.error(err_log)
            raise err_log

        #  Get the Automation folder config file path based on OS and execution env.
        if exec_env:
            artifactory_tool_path = Artifactory.Artifactory_Path[ArtifactoryFolderNames.UEFI].format(
                self._get_platform_family(), tool_name)
        else:
            artifactory_tool_path = Artifactory.Artifactory_Path[self._os.os_type].format(
                self._get_platform_family(), tool_name)

        if exec_env:
            #  Get the Host Path
            host_tool_folder_path = Artifactory.Host_Tool_Path[exec_os][ArtifactoryFolderNames.UEFI].format(
                self._get_platform_family())
        else:
            #  Get the Host Path
            host_tool_folder_path = Artifactory.Host_Tool_Path[exec_os][self._os.os_type].format(
                self._get_platform_family())

        self._log.info("Host Tool Folder under which tools need to copy- {}".format(host_tool_folder_path))

        #  Create folder Host Path
        if not os.path.isdir(host_tool_folder_path):
            os.makedirs(host_tool_folder_path)

        #  Find Host Tools Path
        if not host_tool_folder_path == self.ROOT_PATH:
            if tool_name[0] == '/':
                tool_name = tool_name[1:]
        if exec_os == OperatingSystems.LINUX:
            host_tool_path = Path(os.path.join(host_tool_folder_path, tool_name)).as_posix()
        elif exec_os == OperatingSystems.ESXI:
            host_tool_path = Path(os.path.join(host_tool_folder_path, tool_name)).as_posix()
        elif exec_os == OperatingSystems.WINDOWS:
            host_tool_path = os.path.join(host_tool_folder_path, tool_name)
        else:
            raise NotImplementedError("Not Implemented for os type- {}".format(exec_os))

        self._log.info("Host Tools Path to Copy {} Tools at {}".format(tool_name, host_tool_path))

        if not os.path.isfile(host_tool_path):
            self.artifactory_download_tool_to_host(artifactory_tool_path, host_tool_path, host_tool_folder_path)
        else:
            if self._common_content_configuration.artifactory_tool_overwrite():
                self.artifactory_download_tool_to_host(artifactory_tool_path, host_tool_path, host_tool_folder_path)
            else:
                self._log.info("Tools Already available under the Host Folder- {}".format(host_tool_folder_path))
        self._log.info(host_tool_path)
        return host_tool_path.strip()

    def _execute_cmd_on_host(self, cmd_line, cwd=None):
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

    def _get_platform_family(self):
        """
        This function is used to platform cpu family from config file.

        :return: str - will return cpu family name.
        :raise: AttributeError - if not able to find cpu family name in configuration file.
        """
        # default_system_config_file = self.get_system_configuration_file()
        # tree = ElementTree.parse(default_system_config_file)
        # root = tree.getroot()
        if not self._cfg:
            return self._common_content_lib.get_platform_family()

        cpu_family = self._cfg.find(CommonContentLib.PLATFORM_CPU_FAMILY)
        if cpu_family.text:
            return cpu_family.text
        else:
            raise AttributeError("Failed to get CPU family name, please update the value for XML attributes "
                                 "'family' in configuration file...")
