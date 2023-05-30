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
from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.provider.base_provider import BaseProvider
from src.lib.install_collateral import InstallCollateral


@add_metaclass(ABCMeta)
class RdmsrAndCpuidProvider(BaseProvider):

    def __init__(self, log, os_obj, cfg_opts=None):
        """
        Create a new RdmsrAndCpuidProvider object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        :param os_obj: Os Obj to Perform Os related operations
        """
        super(RdmsrAndCpuidProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)
        self._common_content_config = ContentConfiguration(self._log)
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._command_timeout = self._common_content_config.get_command_timeout()

    @staticmethod
    def factory(log, os_obj, cfg_opts=None):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        """
        package = r"src.provider.rdmsr_and_cpuid_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "RdmsrAndCpuidProviderWindows"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "RdmsrAndCpuidProviderLinux"
        else:
            raise NotImplementedError("Rdmsr and Cpuid Provider is not implemented for "
                                      "specified OS '{}'".format(os_obj.os_type))

        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(cfg_opts=cfg_opts, log=log, os_obj=os_obj)

    @abstractmethod
    def install_msr_tools(self):
        """
        This Method is Used to Install Msr-Tools Package on SUT.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def execute_rdmsr_command(self, command):
        """
        This Method is Used to Execute rdmsr Command on Sut using msr-tools Package.

        :param command: rdmsr command which needs to be executed on SUT.
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def install_cpuid(self):
        """
        This Method is Used to Install Cpuid on SUT.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def execute_cpuid_command(self, command):
        """
        This Method is Used to Execute CPUID Command on Sut.

        :param command: CPUID Command which needs to execute on Sut
        :raise NotImplementedError
        """
        raise NotImplementedError


class RdmsrAndCpuidProviderWindows(RdmsrAndCpuidProvider):
    """
    This Class is Used to Read MSR Data and Execute CPUID Command and fetch cpu info on Windows Platform.
    """
    EAX = "eax"
    LOW_CONTENT = "low_content"
    HIGH_CONTENT = "high_content"
    CMD_FOR_HOME_PATH = "echo %HOMEDRIVE%%HOMEPATH%"

    def __init__(self, log, os_obj, cfg_opts=None):
        super(RdmsrAndCpuidProviderWindows, self).__init__(log, os_obj, cfg_opts)
        self._log = log
        self._os = os_obj
        self.msr_data_dict = {}

    def install_msr_tools(self):
        """
        This Method is Used to Install MSR Tools on Linux Sut
        """
        self._install_collateral.install_ccbhwapi_in_sut()

    def execute_rdmsr_command(self, msr_address):
        """
        This Method is Used to Execute Rdmsr Command on Linux Sut.

        :param msr_address: Msr address which needs to be executed on sut
        :return: rdmsr_cmd_output
        """
        collateral_script = "ccbsdk_windows.py"
        sut_home_path = self._common_content_lib.execute_sut_cmd(self.CMD_FOR_HOME_PATH, self.CMD_FOR_HOME_PATH,
                                                                 self._command_timeout)
        sut_home_path = str(sut_home_path).strip().strip("\\n")
        sut_path = os.path.join(sut_home_path, collateral_script)
        self._install_collateral.copy_collateral_script(collateral_script, sut_home_path)
        cmd_line = "python {} -r {}".format(sut_path, msr_address)
        msr_data = self._common_content_lib.execute_sut_cmd(cmd_line, cmd_line, self._command_timeout)
        self._log.info("msr data value {}".format(msr_data))
        msr_data = msr_data.replace("'", "").replace("{", "").replace("}", "").strip().split(",")
        for info in msr_data:
            if ":" in info:
                self.msr_data_dict[info[:info.index(":")]] = info[info.index(":") + 1:]
        high_content_value = self.msr_data_dict[self.HIGH_CONTENT].replace("L", "")
        low_content_value = self.msr_data_dict[self.LOW_CONTENT].replace("L", "")
        low_content_value = hex(int(low_content_value.strip())).replace("0x", "")
        if len(low_content_value) < 8:
            low_content_value = low_content_value.strip().zfill(8)
        rdmsr_output = hex(int(high_content_value)) + low_content_value
        return rdmsr_output

    def install_cpuid(self):
        """
        This Method is Used to Install CPUID on Linux SUT

        :raise NotImplementedError
        """
        raise NotImplementedError

    def execute_cpuid_command(self, command, cpu_num=0):
        """
        This Method is Used to Execute CPUID Commands on SUT

        :param command: Cpuid Command in hex
        :param cpu_num: Cpu Number on which Cpuid Command needs to Execute
        :raise NotImplementedError
        """
        raise NotImplementedError


class RdmsrAndCpuidProviderLinux(RdmsrAndCpuidProvider):
    """
    This Class is Used to Read Msr Data and CPU info by CPUID Commands in Linux Sut.
    """

    def __init__(self, log, os_obj, cfg_opts=None):
        super(RdmsrAndCpuidProviderLinux, self).__init__(log, os_obj, cfg_opts)
        self._log = log
        self._os = os_obj

    def install_msr_tools(self):
        """
        This Method is Used to Install MSR Tools on Linux Sut
        """
        self._install_collateral.install_msr_tools_linux()

    def execute_rdmsr_command(self, command):
        """
        This Method is Used to Execute Rdmsr Command on Linux Sut.

        :param command: rdmsr command which needs to be executed on sut
        :return: rdmsr_cmd_output
        """
        rdmsr_cmd_output = self._common_content_lib.execute_sut_cmd(command, command, self._command_timeout)
        self._log.debug("Output of rdmsr Command is '{}'".format(rdmsr_cmd_output.strip()))
        return rdmsr_cmd_output

    def install_cpuid(self):
        """
        This Method is Used to Install CPUID on Linux SUT
        """
        self._install_collateral.install_cpuid()

    def execute_cpuid_command(self, command):
        """
        This Method is Used to Execute CPUID Commands on SUT

        :param command: CPUID Command which needs to be executed on Sut
        :raise NotImplementedError
        """
        raise NotImplementedError
