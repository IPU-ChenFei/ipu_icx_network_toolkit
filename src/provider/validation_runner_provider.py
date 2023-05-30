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

from importlib import import_module
from abc import ABCMeta, abstractmethod
from six import add_metaclass

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.provider.base_provider import BaseProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions


@add_metaclass(ABCMeta)
class ValidationRunnerProvider(BaseProvider):
    """
    This ValidationRunnerProvider is implemented for linux and windows environment to handle validation runner tool.

    """

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new ValidationRunnerProvider object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param log: Logger object to use for output message.
        :param os_obj: OS object.
        """
        super(ValidationRunnerProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._sut_os = self._os.os_type
        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg_opts)
        self._content_config_obj = ContentConfiguration(self._log)
        self._command_timeout = self._content_config_obj.get_command_timeout()
        self._install_collateral = InstallCollateral(self._log, self._os, self._cfg_opts)

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        :Raise: NotImplementedError
        """
        package = r"src.provider.validation_runner_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "ValidationRunnerProviderWindows"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "ValidationRunnerProviderLinux"
        else:
            raise NotImplementedError

        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(cfg_opts=cfg_opts, log=log, os_obj=os_obj)

    @abstractmethod
    def install_validation_runner(self):
        """
        Install Validation runner.

        :return: None.
        :Raise: NotImplementedError.
        """
        raise NotImplementedError

    @abstractmethod
    def get_runner_script_path(self, filename):
        """
        Gets the runner script path

        :param filename: filename to find the location
        :return: None.
        :Raise: NotImplementedError.
        """
        raise NotImplementedError

    @abstractmethod
    def run_runner_script(self, command, execution_timeout, cwd):
        """
        run the runner script

        :param command: command
        :param execution_timeout: execution timeout
        :param cwd: current working directory
        :return: None.
        :Raise: NotImplementedError
        """
        raise NotImplementedError


class ValidationRunnerProviderLinux(ValidationRunnerProvider):
    """
    This provider is implemented for linux environment to handle validation runner tool.
    """

    __RUNNER_PASSED = '[End Script] Status : PASSED '
    __ZERO_ERRORS = '0 errors'
    __FIND_RUNNERFILE_PATH = "find $(pwd) -type f -name {}"

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new ValidationRunnerProviderLinux object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param log: Logger object to use for output message.
        :param os_obj: OS object.
        """
        super(ValidationRunnerProviderLinux, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj

    def install_validation_runner(self):
        """Installs the validation runner"""
        self._install_collateral.install_validation_runner()

    def get_runner_script_path(self, filename):
        """
        gets the runner script path

        :param filename: file name to find the location
        :return: None.
        :raise: RuntimeError.
        """
        runner_path = self._common_content_lib.execute_sut_cmd(self.__FIND_RUNNERFILE_PATH.format(filename),
                                                               "finding runner script path",
                                                               self._command_timeout)
        self._log.debug("Path of {} file: {}".format(filename, runner_path))
        return os.path.split(runner_path)[0].strip() + "/"

    def run_runner_script(self, command, execution_timeout, cwd=None):
        """
        run the runner script

        :param command: command
        :param execution_timeout: execution timeout
        :param cwd: current working directory
        :return: None.
        :Raise: RuntimeError
        """
        self._log.debug("Executing command {}".format(command))
        command_result = self._os.execute(command, execution_timeout + self._command_timeout, cwd)
        self._log.debug("Result of {}:\n {}".format(command, command_result.stdout))
        self._log.error("std err of {}:\n {}".format(command, command_result.stderr))
        if command_result.stdout.strip() == "":
            raise RuntimeError("Fail to get the output of command")
        if self.__RUNNER_PASSED not in command_result.stdout and self.__ZERO_ERRORS not in command_result.stdout:
            raise content_exceptions.TestFail("%s Failed" % command)
        self._log.info("Successfully Executed {}".format(command))


class ValidationRunnerProviderWindows(ValidationRunnerProvider):
    """
    This provider is implemented for windows environment to handle validation runner tool.
    """

    __RUNNER_PASSED = '[End Script] Status : PASSED '
    __ZERO_ERRORS = '0 errors'
    __FIND_RUNNERFILE_PATH = "where {}"

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new ValidationRunnerProviderWindows object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param log: Logger object to use for output message.
        :param os_obj: OS object.
        """
        super(ValidationRunnerProviderWindows, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj

    def install_validation_runner(self):
        """Installs the validation runner"""
        self._install_collateral.install_validation_runner()

    def get_runner_script_path(self, filename):
        """
        gets the runner script path

        :param filename: file name to find the location
        :return: None.
        :raise: RuntimeError.
        """
        runner_path = self._common_content_lib.execute_sut_cmd(self.__FIND_RUNNERFILE_PATH.format(filename),
                                                               "finding runner script path",
                                                               self._command_timeout)
        self._log.debug("Path of {} file: {}".format(filename, runner_path))
        return runner_path.split("\n")[0]

    def run_runner_script(self, command, execution_timeout, cwd):
        """"
        run the runner script

        :param command: command
        :param execution_timeout: execution timeout
        :param cwd: current working directory
        :return: None.
        :Raise: RuntimeError
        """
        self._log.debug("Executing command {}".format(command))
        command_result = self._os.execute(command, execution_timeout + self._command_timeout, cwd)
        self._log.debug("Result of {}:\n {}".format(command, command_result.stdout))
        if command_result.cmd_failed():
            self._log.error("Error of {}:\n {}".format(command, command_result.stderr))
        if command_result.stdout.strip() == "":
            raise RuntimeError("Fail to get the output of command")
        if self.__RUNNER_PASSED not in command_result.stdout and self.__ZERO_ERRORS not in command_result.stdout:
            raise content_exceptions.TestFail("%s Failed" % command)
        self._log.info("Successfully Executed {}".format(command))
