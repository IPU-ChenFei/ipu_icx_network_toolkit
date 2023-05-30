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

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.provider.base_provider import BaseProvider
from abc import ABCMeta, abstractmethod
from six import add_metaclass

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration


@add_metaclass(ABCMeta)
class MlcProvider(BaseProvider):
    """ Class to provide mlc app functionalities """

    def __init__(self, log, cfg_opts, os_obj):
        """
        Constructor of the class MlcProvider.

        :param log: Logger object to use for output messages
        :param cfg_opts: config object
        :param os_obj: OS object
        """
        super(MlcProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj
        self._sut_os = self._os.os_type
        self._cfg_opts = cfg_opts

        #  common_content_obj and config object
        self.common_content_lib_obj = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self.command_timeout = self._common_content_configuration.get_command_timeout()
        self.mlc_runtime = self._common_content_configuration.memory_mlc_run_time()
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)
        self.mlc_path = self._install_collateral.install_mlc()

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.

        :param log: Logger object to use for output messages
        :param cfg_opts: config object
        :param os_obj: OS object
        :return: object
        """
        package = r"src.provider.mlc_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "WindowsMlc"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "LinuxMlc"
        else:
            raise NotImplementedError("Test is not implemented for %s" % os_obj.os_type)
        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(log=log, cfg_opts=cfg_opts, os_obj=os_obj)

    @abstractmethod
    def execute_mlc_test(self, mlc_e, mlc_cmd_log_path):
        """
        Executing the tool and generate the output file.

        :param mlc_cmd_log_path: Path of the mlc log folder
        :raise: TestNotImplementedError
        """

        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def execute_mlc_test_with_2_greater_amp_1_error_param(self, mlc_e, mlc_cmd_log_path):
        """
        Executing the tool with 2>&1 param and generate the output file.

        :param mlc_cmd_log_path: Path of the mlc log folder
        :raise: TestNotImplementedError
        """

        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def get_mlc_latency_info(self, mlc_e, mlc_cmd_log_path):
        """
        This function is used to get_mlc_latency_info the MLC commands

        :param mlc_cmd_log_path: Path of the mlc log folder

        :raise: TestNotImplementedError
        """

        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def get_mlc_loaded_latency_info(self, mlc_e, mlc_cmd_log_path):
        """
        This function is used to get_mlc_loaded_latency_info the MLC commands

        :param mlc_cmd_log_path: Path of the mlc log folder

        :raise: TestNotImplementedError
        """

        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def get_idle_latency(self, mlc_e, mount_list, mlc_cmd_log_path):
        """
        This function is uses to execute idle_latency cmd with 2 mount points

        :param mount_list: mount points
        :param mlc_cmd_log_path: Path of the mlc log folder

        :raise: TestNotImplementedError
        """

        raise content_exceptions.TestNotImplementedError


class WindowsMlc(MlcProvider):
    """ Class to provide Mlc test app functionalities for windows platform """

    MLC_EXE = "mlc.exe"
    MLC_LATENCY_MATRIX_COMMAND = "./mlc {} -Z --latency_matrix -x0 2>&1 >> {}"
    MLC_LOADED_LATENCY_COMMAND = "./mlc {} -Z --loaded_latency -T -d0 -operthreadfile.txt 2>&1 >> {}"

    def __init__(self, log, cfg_opts, os_obj):
        """
        Constructor of the class WindowsMlc.

        :param log: Logger object to use for output messages
        :param cfg_opts: config object
        :param os_obj: OS object
        """
        super(WindowsMlc, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj

    def factory(self, log, cfg_opts, os_obj):
        pass

    def execute_mlc_test(self, mlc_e, mlc_cmd_log_path):
        """
        Executing the tool and generate the output file.

        :param mlc_cmd_log_path: Path of the mlc log folder
        """
        command = "{} > {}".format(self.MLC_EXE, mlc_cmd_log_path)
        self._log.info("Executing mlc command : {}".format(command))
        self.common_content_lib_obj.execute_sut_cmd(command, "mlc command", self.mlc_runtime, cmd_path=self.mlc_path)

    def execute_mlc_test_with_2_greater_amp_1_error_param(self, mlc_e, mlc_cmd_log_path):
        """
        Executing the tool with 2>&1 param and generate the output file.

        :param mlc_cmd_log_path: Path of the mlc log folder
        :raise: TestNotImplementedError
        """

        raise content_exceptions.TestNotImplementedError("The function '{}' is supported only from "
                                                         "Linux platform..".format("execute_mlc_test_with_param"))

    def get_mlc_latency_info(self, mlc_e, mlc_cmd_log_path):
        """
        This function is used to get_mlc_latency_info using the MLC commands

        :param: mlc_cmd_log_path: log file name
        :return: True if MLC command is executed.
        """
        try:
            mlc_cmd = self.MLC_LATENCY_MATRIX_COMMAND.format(mlc_e, mlc_cmd_log_path)
            self._log.info("Executing MLC Command : {}".format(mlc_cmd))
            self.common_content_lib_obj.execute_sut_cmd(mlc_cmd, "Executing MLC Command", self.mlc_runtime,
                                                        self.mlc_path)
            return True
        except Exception as ex:
            self._log.error("Exception occur while running mlc command")
            raise ex

    def get_mlc_loaded_latency_info(self, mlc_e, mlc_cmd_log_path):
        """
        This function is used to get_mlc_loaded_latency_info using the MLC commands

        :param: mlc_cmd_log_path: log file name
        :return: True if MLC command is executed.
        """
        try:
            mlc_cmd = self.MLC_LOADED_LATENCY_COMMAND.format(mlc_e, mlc_cmd_log_path)
            self._log.info("Executing MLC loaded latency Command : {}".format(mlc_cmd))
            self.common_content_lib_obj.execute_sut_cmd(mlc_cmd, "Executing MLC loaded latency Command",
                                                        self.mlc_runtime, self.mlc_path)
            return True
        except Exception as ex:
            self._log.error("Exception occur while running mlc command")
            raise ex

    def get_idle_latency(self, mlc_e, drive_letters, mlc_cmd_log_path):
        """
        This function is uses to measure the idle latencies for each persistent memory

        :param mlc_cmd_log_path: Path of the mlc log folder
        :param drive_letters:  Drive letters for the persistent memory
        :return: All latency log files of DCPMM
        """
        log_files_list = []
        for each_drive_letter in drive_letters:
            total_log_path = os.path.join(mlc_cmd_log_path, "1lm_latency_{}.log".format(mlc_e, each_drive_letter))
            log_file_name = "1lm_latency_{}.log".format(each_drive_letter)
            log_files_list.append(log_file_name)
            command = "{} -Z --idle_latency -c0 -J{}: >> {}".format(self.MLC_EXE, each_drive_letter, total_log_path)
            self._log.info("Executing the command  : {}".format(command))
            self.common_content_lib_obj.execute_sut_cmd(command, "Idle latency for each Pmem DIMM",
                                                        self.command_timeout, cmd_path=self.mlc_path)

        return log_files_list


class LinuxMlc(MlcProvider):
    """ Class to provide mlc app functionalities for linux platform """

    MLC_COMMAND_WITH_PARAM = "./mlc {} -Z 2>&1 | tee -a {}"
    MLC_LATENCY_MATRIX_COMMAND = "./mlc {} -Z --latency_matrix -x0 2>&1 | tee -a {}"
    MLC_IDLE_LATENCY_COMMAND = "./mlc {} -Z --idle_latency -c0 -J{} 2>&1 | tee -a  {}"
    MLC_LOADED_LATENCY_COMMAND = "./mlc {} -Z --loaded_latency -T -d0 -operthreadfile.txt 2>&1 | tee -a {}"
    MLC_COMMAND = "./mlc {} -Z | tee -a {}"

    def __init__(self, log, cfg_opts, os_obj):
        """
        Constructor of the class LinuxMlc.

        :param log: Logger object to use for output messages
        :param cfg_opts: config object
        :param os_obj: OS object
        """
        super(LinuxMlc, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj
        self._cfg_opts = cfg_opts

        try:
            self.common_content_lib_obj.execute_sut_cmd("chmod +x mlc", "Assigning executable privileges ",
                                                        self.command_timeout, self.mlc_path)
            self._log.info("Executable privileges has been assigned successfully...")
        except Exception as ex:
            raise RuntimeError("Mlc execution permission has failed with exception '{}'...".format(ex))

    def factory(self, log, cfg_opts, os_obj):
        pass

    def execute_mlc_test_with_2_greater_amp_1_error_param(self, mlc_e, mlc_cmd_log_path):
        """
        Executing the tool with 2>&1 param and generate the output file.

        :param: mlc_cmd_log_path: log file name
        :return: True on success
        """
        # run the mlc tool and get the log file
        mlc_cmd = self.MLC_COMMAND_WITH_PARAM.format(mlc_e, mlc_cmd_log_path)
        self._log.info("Executing MLC Command : {}".format(mlc_cmd))
        self.common_content_lib_obj.execute_sut_cmd(mlc_cmd, "Executing mlc", self.mlc_runtime, cmd_path=self.mlc_path)

        self._log.info("MLC app has ran successfully..")
        return True

    def execute_mlc_test(self, mlc_e, mlc_cmd_log_path):
        """
        Executing the tool and generate the output file.

        :param: mlc_cmd_log_path: log file name
        :return: True on success
        """
        # run the mlc tool and get the log file
        mlc_cmd = self.MLC_COMMAND.format(mlc_e, mlc_cmd_log_path)
        self._log.info("Executing MLC Command : {}".format(mlc_cmd))
        self.common_content_lib_obj.execute_sut_cmd(mlc_cmd, "Executing mlc", self.mlc_runtime, cmd_path=self.mlc_path)

        self._log.info("MLC app has ran successfully..")
        return True

    def get_mlc_latency_info(self, mlc_e, mlc_cmd_log_path):
        """
        This function is used to get_mlc_latency_info using the MLC commands

        :param: mlc_cmd_log_path: log file name
        :return: True if MLC command is executed.
        """
        try:
            mlc_cmd = self.MLC_LATENCY_MATRIX_COMMAND.format(mlc_e, mlc_cmd_log_path)
            self._log.info("Executing MLC Command : {}".format(mlc_cmd))
            self.common_content_lib_obj.execute_sut_cmd(mlc_cmd, "Executing MLC Command", self.mlc_runtime,
                                                        self.mlc_path)
            return True
        except Exception as ex:
            self._log.error("Exception occur while running mlc command")
            raise ex

    def get_mlc_loaded_latency_info(self, mlc_e, mlc_cmd_log_path):
        """
        This function is used to get_mlc_loaded_latency_info using the MLC commands

        :param: mlc_cmd_log_path: log file name
        :return: True if MLC command is executed.
        """
        try:
            mlc_cmd = self.MLC_LOADED_LATENCY_COMMAND.format(mlc_e, mlc_cmd_log_path)
            self._log.info("Executing MLC loaded latency Command : {}".format(mlc_cmd))
            self.common_content_lib_obj.execute_sut_cmd(mlc_cmd, "Executing MLC loaded latency Command",
                                                        self.mlc_runtime, self.mlc_path)
            return True
        except Exception as ex:
            self._log.error("Exception occur while running mlc command")
            raise ex

    def get_idle_latency(self, mlc_e, mount_list, mlc_cmd_log_path):
        """
        This function is uses to execute idle_latency cmd with 2 mount points

        :param: mount_list: list of mount points
        :param: mlc_cmd_log_path: mlc executer path
        :param: mlc_cmd_log_path: log file name
        """
        for each_mount_list in mount_list:
            mlc_idle_latency_cmd = self.MLC_IDLE_LATENCY_COMMAND.format(mlc_e, each_mount_list, mlc_cmd_log_path)
            self._log.info("Executing MLC Command {}".format(mlc_idle_latency_cmd))
            self.common_content_lib_obj.execute_sut_cmd(mlc_idle_latency_cmd, "Executing mlc idle latency cmd",
                                                        self.mlc_runtime, self.mlc_path)
