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
from src.lib.dtaf_content_constants import TimeConstants
from src.lib import content_exceptions


@add_metaclass(ABCMeta)
class SolarProvider(BaseProvider):
    """ Class to provide solar test functionality """

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new SolarProvider object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        """
        super(SolarProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj
        self._sut_os = self._os.os_type

        #  common_content_obj and config object
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param cfg_opts: cfg_opts

        :return: object
        """
        package = r"src.provider.solar_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "WindowsSolarToolProvider"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "LinuxSolarToolProvider"
        else:
            raise NotImplementedError("Test is not implemented for %s" % os_obj.os_type)
        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(log=log, cfg_opts=cfg_opts, os_obj=os_obj)

    @abstractmethod
    def execute_installer_solar_test(self, xml_file_name, sut_folder_path, command):
        """
        Execute the solar test

        :param sut_folder_path: installed path in the SUT
        :param xml_file_name: xml file name to run the solar test
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def install_solar_tool(self):
        """
        To install the solar tool

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @staticmethod
    def verify_solar_tool_output(result, solar_pass_flow_list):
        """
        To verify the solar tool output

        :return: True if solar execution on success.
        """
        for pass_info in solar_pass_flow_list:
            if pass_info not in result:
                raise content_exceptions.TestFail("Solar execution failed")
        return True


class WindowsSolarToolProvider(SolarProvider):
    """ Class to provide solar test functionality for windows platform """

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new WindowsSolar object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param cfg_opts: cfg_opts
        """
        super(WindowsSolarToolProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj

    def factory(self, log, cfg_opts, os_obj):
        pass

    def execute_installer_solar_test(self, xml_file_name, sut_folder_path, command):
        """
        Execute the solar test

        :param sut_folder_path: installed path in the SUT
        :param xml_file_name: xml file to run the solar test
        :param command:
        :raise: NotImplementedError
        """

        # Copy .xml file into solar folder in sut.
        host_folder_path = self._install_collateral.download_tool_to_host(xml_file_name)
        self._os.copy_local_file_to_sut(host_folder_path, sut_folder_path)
        self._log.info("Copied {} file into sut under path :{}".format(xml_file_name, sut_folder_path))

        command = command.format(xml_file_name)

        # Run solar using the command ./Solar.exe /cfg .xml
        self._log.info("Executing solar command:{}".format(command))

        command_result = self._common_content_lib.execute_sut_cmd(
            command, "executing solar command", TimeConstants.ONE_HOUR_IN_SEC, sut_folder_path)
        self._log.debug("Successfully run Solar result: \n{}".format(command_result))

        return command_result

    def install_solar_tool(self):
        """
        To install the solar tool

        :return: solar tool installed path in the SUT.
        """
        return self._install_collateral.install_solar_hwp_native()


class LinuxSolarToolProvider(SolarProvider):
    """ Class to provide solar test functionality for linux platform """

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new LinuxSolarTest object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param cfg_opts: cfg_opts
        """
        super(LinuxSolarToolProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj

    def factory(self, log, cfg_opts, os_obj):
        pass

    def execute_installer_solar_test(self, xml_file_name, sut_folder_path, command):
        """
        Execute the solar test

        :param sut_folder_path: installed path in the SUT
        :param xml_file_name: command to run the solar test
        :param command:
        :return command_result: The output of the command
        """

        # Copy .xml file into  solar folder in sut.
        host_folder_path = self._install_collateral.download_tool_to_host(xml_file_name)
        self._os.copy_local_file_to_sut(host_folder_path, sut_folder_path)
        self._log.info("Copied {} file into sut under path :{}".format(xml_file_name, sut_folder_path))

        command = command.format(xml_file_name)

        # Run solar using the command ./solar.sh /cfg .xml
        self._log.info("Executing solar command:{}".format(command))
        command_result = self._common_content_lib.execute_sut_cmd(
            command, "executing solar command", TimeConstants.ONE_HOUR_IN_SEC, sut_folder_path)
        self._log.debug("Successfully run Solar result: \n{}".format(command_result))

        return command_result

    def install_solar_tool(self):
        """
        To install the solar tool

        :return: solar tool installed path in the SUT.
        """
        return self._install_collateral.install_solar_hwp_native()
