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
import threading
import time
import six
from importlib import import_module

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib import content_exceptions
from src.lib.os_lib import WindowsCommonLib
from src.provider.base_provider import BaseProvider
from abc import ABCMeta, abstractmethod
from six import add_metaclass

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.install_collateral import InstallCollateral
from src.memory.lib.memory_common_lib import MemoryCommonLib
from src.lib.dtaf_content_constants import VssMode, TimeConstants


@add_metaclass(ABCMeta)
class VssProvider(BaseProvider):
    """ Class to provide Vss app functionalities """

    def __init__(self, log, cfg_opts, os_obj):
        """
        Constructor of the class VssProvider.

        :param log: Logger object to use for output messages
        :param cfg_opts: config object
        :param os_obj: OS object
        """
        super(VssProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj
        self._sut_os = self._os.os_type
        self._cfg_opts = cfg_opts

        #  Library objects creation
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)

        self._install_collateral = InstallCollateral(self._log, os_obj=self._os, cfg_opts=cfg_opts)
        self._memory_common_lib = MemoryCommonLib(self._log, cfg_opts, self._os)

        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self.host_platform_pkg_path = None
        self.sut_platform_pkg_path = None

        self.process_name = None

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.

        :param log: Logger object to use for output messages
        :param cfg_opts: config object
        :param os_obj: OS object
        :return: object
        """
        package = r"src.provider.vss_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "WindowsVss"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "LinuxVss"
        else:
            raise NotImplementedError("Test is not implemented for %s" % os_obj.os_type)
        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(log=log, cfg_opts=cfg_opts, os_obj=os_obj)

    def get_aep_pkg(self):
        """
        To copy the aep.pkx to the VSS platform based folder for execution
        """
        self.sut_platform_pkg_path = os.path.join(self._vss_path, self.DICT_PRODUCT_INFO[self.product_info])

        self.host_platform_pkg_path = self._install_collateral.download_tool_to_host("aep.pkx")
        self._os.copy_local_file_to_sut(self.host_platform_pkg_path, self.sut_platform_pkg_path)

    @abstractmethod
    def execute_vss_2lm_test_package(self):
        """
        To execute VSS tool with 2lm package

        :raise: NotImplementedError
        """

        raise NotImplementedError

    @abstractmethod
    def execute_vss_1lm_test_package(self):
        """
        To execute VSS tool with 1lm package

        :raise: NotImplementedError
        """

        raise NotImplementedError

    @abstractmethod
    def execute_vss_memory_test_package(self, flow_tree="S145"):
        """
        To execute VSS tool with memory package

        :raise: NotImplementedError
        """

        raise NotImplementedError

    @abstractmethod
    def execute_vss_storage_test_package(self, flow_tree="S2"):
        """
        To execute ilVSS tool with storage package

        :raise: NotImplementedError
        """
        raise NotImplementedError

    def __verify_process_running(self, str_process_name):
        """
        Function to find the process running on the SUT.

        :raise: NotImplementedError
        """

        raise NotImplementedError

    def verify_vss_running(self, vss_mode):
        """
        To verify whether the vss tool has started in the background

        :raise: NotImplementedError
        """

        raise NotImplementedError

    def wait_for_vss_to_complete(self, vss_mode):
        """
        To wait until the vss tool has completed its execution

        :raise: NotImplementedError
        """

        raise NotImplementedError

    def verify_vss_logs(self, log_name):
        """
        To verify the vss logs post execution

        :raise: NotImplementedError
        """

        raise NotImplementedError

    def configure_vss_stress(self):
        """
        To copy the packages to the SUT.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    def configure_vss_stress_storage(self):
        """
        To copy the packages to the SUT.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    def terminating_process(self, process_name):
        """
        To kill the ctc process

        """
        raise NotImplementedError


class WindowsVss(VssProvider):
    """ Class to provide Vss test app functionalities for windows platform """
    DICT_PRODUCT_INFO = {"WilsonPoint": "Whitley", "PURLEY": "Purley", "ArcherCity": "EGS", "EAGLESTREAM":"EGS", "ArcherCityM": "EGS"}
    PROCESS_TERMINATE_CMD = 'taskkill /F /IM "{}"'
    IWVSS_CTC_CMD = r"ctc.exe /pkg {}\{} /cfg {} /flow {} /run /minutes {} /rr iwvss_log.log"
    DICT_PACKAGE_INFO_STORAGE = {"EAGLESTREAM": "stress_egs_iwvss_storage_s2.pkx",
                                 "ArcherCity": "stress_egs_iwvss_storage_s2.pkx",
                                 "EAGLESTREAM_NVME": "EGS_NVME_storage_S2_flow.pkx",
                                 "ArcherCity_NVME": "EGS_NVME_storage_S2_flow.pkx"
                                 }

    def __init__(self, log, cfg_opts, os_obj):
        """
        Constructor of the class WindowsVss.

        :param log: Logger object to use for output messages
        :param cfg_opts: config object
        :param os_obj: OS object
        """
        super(WindowsVss, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self.windows_lib_obj = WindowsCommonLib(self._log, self._os)
        self._vss_runtime = self._common_content_configuration.get_iwvss_run_time()
        self.product_info = self.windows_lib_obj.task_manager_wmic_baseboard_get(task_option="product").split()[1]

        if self.DICT_PRODUCT_INFO[self.product_info] is None:
            raise content_exceptions.TestUnSupportedError("This test package is unavailable or not developed to "
                                                          "support this {} platform..".format(self.product_info))
        self.terminating_process(VssMode.IWVSS_MODE)
        self._vss_path = self._install_collateral.install_iwvss()

    def factory(self, log, cfg_opts, os_obj):
        pass

    def _execute_vss(self, cmd, vss_path):
        """
        Function to run the iwVSS command on the SUT.

        :param cmd: iwvss command
        :param vss_path: path of the iwvss executables
        :return None
        """

        self._common_content_lib.execute_sut_cmd(
            cmd, "execute iwVSS", (float((self._command_timeout * self._vss_runtime)) / 5), cmd_path=str(vss_path))

    def _execute_vss_ctc(self, cmd, vss_path):
        """
        Function to run the iwVSS command on the SUT.

        :param cmd: iwvss command
        :param vss_path: path of the iwvss executables
        :return None
        """
        try:
            self._common_content_lib.execute_sut_cmd(
                cmd, "execute iwVSS", (float((self._command_timeout * self._vss_runtime)) / 5), cmd_path=str(vss_path))
        except Exception as ex:
            self._log.debug("We are killing the ctc.exe tool after completion of the test, "
                            "so we will get as command failed")

    def execute_vss_2lm_test_package(self):
        """
        To execute iwVSS tool with 2lm package
        """
        if self.DICT_PRODUCT_INFO[self.product_info] == "Whitely":
            self.get_aep_pkg()

        # IwVss tool is running in a separate thread on SUT
        iwvss_thread = threading.Thread(target=self._execute_vss,
                                        args=(r"cmd /C t.exe /pkg {}\aep.pkx /reconfig /pc AEP /flow 2LM /run "
                                              r"/minutes {} /RR logall.log".
                                              format(self.DICT_PRODUCT_INFO[self.product_info], self._vss_runtime),
                                              self._iwvss_path,))
        # Thread has been started
        iwvss_thread.start()

        self.verify_vss_running(VssMode.MIXED_MODE_2LM)

    def execute_vss_1lm_test_package(self):
        """
        To execute iwVSS tool with 1lm package
        """
        if self.DICT_PRODUCT_INFO[self.product_info] == "Whitely":
            self.get_aep_pkg()

        # IwVss tool is running in a separate thread on SUT
        iwvss_thread = threading.Thread(target=self._execute_vss,
                                        args=(r"cmd /C t.exe /pkg {}\aep.pkx /reconfig /pc AEP /flow 1LM /run "
                                              r"/minutes {} /RR logall.log".
                                              format(self.DICT_PRODUCT_INFO[self.product_info], self._vss_runtime),
                                              self._iwvss_path,))
        # Thread has been started
        iwvss_thread.start()

        self.verify_vss_running(VssMode.MIXED_MODE_1LM)

    def execute_vss_memory_test_package(self, flow_tree="S145"):
        """
        To execute iwVSS tool with memory package based on platform.
        """
        # TODO : For iwvss 2.9.2 we are using this work around
        mem_exe_file_name = "mem64.exe"
        # To download mem64.exe file to Host from artifactory.
        mem64_host_path = self._install_collateral.download_tool_to_host(mem_exe_file_name)
        self._log.info("{} path in Host is : {}".format(mem_exe_file_name, mem64_host_path))
        # To copy mem64.exe file to SUT from the Host.
        self._os.copy_local_file_to_sut(source_path=mem64_host_path, destination_path=self._vss_path)

        # To download pkx file from artifactory.
        self.host_platform_pkg_path = self._install_collateral.download_tool_to_host("{}_NoBMC.pkx".format(
            self.DICT_PRODUCT_INFO[self.product_info]))
        self._log.info("Package path in Host is : {}".format(self.host_platform_pkg_path))
        if not os.path.isfile(self.host_platform_pkg_path):
            log_error = "{} does not exist".format(self.host_platform_pkg_path)
            self._log.error(log_error)
            raise IOError(log_error)

        self.sut_platform_pkg_path = os.path.join(self._vss_path, self.DICT_PRODUCT_INFO[self.product_info])
        self._log.info("Copying Package in the SUT under path : {}".format(self.sut_platform_pkg_path))
        # To copy .pkx file to SUT form the Host.
        self._os.copy_local_file_to_sut(self.host_platform_pkg_path, self.sut_platform_pkg_path)

        iwvss_command = r"cmd /C t.exe /pkg {}\{}_NoBMC.pkx /reconfig /pc {} /flow {} /run /minutes {} /RR iwvss.log".\
            format(self.DICT_PRODUCT_INFO[self.product_info], self.DICT_PRODUCT_INFO[self.product_info],
                   self.DICT_PRODUCT_INFO[self.product_info], flow_tree, self._vss_runtime)
        self._log.info("Executing the command : {}".format(iwvss_command))
        # IwVss tool is running in a separate thread on SUT
        iwvss_thread = threading.Thread(target=self._execute_vss, args=(iwvss_command, self._vss_path,))
        iwvss_thread.start()
        time.sleep(TimeConstants.ONE_MIN_IN_SEC/2)
        self.verify_vss_running(VssMode.MEMORY_MODE)

    def __verify_process_running(self, str_process_name):
        """
        Function to find the process running on the SUT.

        :param str_process_name: name of the process to be found
        :return 0 if process is found in the task list else 1
        """
        process_running = self._os.execute('TASKLIST | FINDSTR /I "{}"'.format(str_process_name),
                                           self._command_timeout)
        return process_running.return_code

    def verify_vss_running(self, vss_mode):
        """
        Function to verify that the process is running in the background on SUT.

        :param vss_mode: name of the process to be found
        :return None
        """
        if vss_mode in VssMode.MEMORY_MODE:
            self.process_name = "mem64.exe"
        elif vss_mode in VssMode.MIXED_MODE_1LM:
            self.process_name = "mem64.exe"
        elif vss_mode in VssMode.MIXED_MODE_2LM:
            self.process_name = "mem64.exe PatIO.exe"
        elif vss_mode in VssMode.IWVSS_MODE:
            self.process_name = "PatIO.exe"
        ret_code = self.__verify_process_running(self.process_name)

        if ret_code == 0:
            self._log.info("{} has been started to execute in the background..".format(self.process_name))
        else:
            raise RuntimeError("{} is not launched in the background..".format(self.process_name))

    def wait_for_vss_to_complete(self, vss_mode):
        """
        Function verify and hold until background process finish running on the SUT.

        :param vss_mode: name of the process to be found
        :return None
        """
        process_running = True

        if vss_mode in VssMode.MEMORY_MODE:
            self.process_name = "mem64.exe"
        elif vss_mode in VssMode.MIXED_MODE_1LM:
            self.process_name = "mem64.exe"
        elif vss_mode in VssMode.MIXED_MODE_2LM:
            self.process_name = "mem64.exe PatIO.exe"
        elif vss_mode in VssMode.IWVSS_MODE:
            self.process_name = "PatIO.exe"
            
        while process_running:
            ret_code = self.__verify_process_running(self.process_name)

            if ret_code == 0:
                self._log.info("PatIO.exe or mem64.exe is still running in the background..")
                self._log.info("Waiting for the iwVSS execution to complete..")
                time.sleep(TimeConstants.FIVE_MIN_IN_SEC)
            else:
                process_running = False

                self._log.info("iwVSS execution has been completed successfully..")
                self._log.info("{} has been started to execute in the background..".format(self.process_name))

    def verify_vss_logs(self, log_name):
        """
        To verify the vss logs post execution

        :param log_name: Name of the log to be parsed.
        :return: true if log has no errors else fail
        """
        log_dir = self._common_content_lib.get_log_file_dir()

        if not os.path.exists(os.path.join(log_dir, "testcase_logs")):
            log_dir = log_dir + "/" + "testcase_logs"
            os.makedirs(log_dir)

        log_file_path_host = self._common_content_lib.copy_log_files_to_host(
            test_case_id=log_dir, sut_log_files_path=str(self._vss_path), extension=".log")

        return self._memory_common_lib.parse_log_for_error_patterns(
            log_path=os.path.join(log_file_path_host, log_name))

    def execute_vss_storage_test_package(self, flow_tree="S2", nvme=False):
        """
        To execute iwVSS tool with storage package
        :param flow_tree: S2 Flow tree
        :param nvme: if nvme drive has to be stressed out True else False
        """
        if nvme:
            self.host_platform_pkg_path = self._install_collateral.download_tool_to_host \
                (self.DICT_PACKAGE_INFO_STORAGE[self.product_info + "_NVME"])
        else:
            self.host_platform_pkg_path = self._install_collateral.download_tool_to_host \
                (self.DICT_PACKAGE_INFO_STORAGE[self.product_info])
        self._log.info("Package path in Host is : {}".format(self.host_platform_pkg_path))
        if not os.path.isfile(self.host_platform_pkg_path):
            log_error = "{} does not exist".format(self.host_platform_pkg_path)
            self._log.error(log_error)
            raise IOError(log_error)

        self.sut_platform_pkg_path = os.path.join(self._vss_path, self.DICT_PRODUCT_INFO[self.product_info])
        self._log.info("Copying Package in the SUT under path : {}".format(self.sut_platform_pkg_path))
        # To copy .pkx file to SUT form the Host.
        self._os.copy_local_file_to_sut(self.host_platform_pkg_path, self.sut_platform_pkg_path)

        ret_code = self.__verify_process_running(VssMode.IWVSS_MODE)

        if ret_code == 0:
            self.terminating_process(VssMode.IWVSS_MODE)

        iwvss_command = self.IWVSS_CTC_CMD.format(
            self.DICT_PRODUCT_INFO[self.product_info], self.DICT_PACKAGE_INFO_STORAGE[self.product_info],
            self.DICT_PRODUCT_INFO[self.product_info],
            flow_tree, self._vss_runtime)
        if nvme:
            iwvss_command = self.IWVSS_CTC_CMD.format(
                self.DICT_PRODUCT_INFO[self.product_info], self.DICT_PACKAGE_INFO_STORAGE[self.product_info + "_NVME"],
                self.DICT_PRODUCT_INFO[self.product_info],
                flow_tree, self._vss_runtime)
        self._log.info("Executing the command : {}".format(iwvss_command))
        # IwVss tool is running in a separate thread on SUT
        iwvss_thread = threading.Thread(target=self._execute_vss_ctc, args=(iwvss_command, self._vss_path,))
        iwvss_thread.start()
        time.sleep(TimeConstants.ONE_MIN_IN_SEC/2)
        self.verify_vss_running(VssMode.IWVSS_MODE)

    def configure_vss_stress(self):
        """
        To copy the packages to the SUT.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    def configure_vss_stress_storage(self):
        """
        To copy the packages to the SUT.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    def terminating_process(self, process_name):
        """
        Killing the process

        :param process_name: name of the process
        """
        ret_code = self.__verify_process_running(process_name)
        if ret_code == 0:
            output = self._os.execute(self.PROCESS_TERMINATE_CMD.format(process_name), self._vss_runtime)
            self._log.info("Process {} has been terminated {}".format(process_name, output.stdout))


class LinuxVss(VssProvider):
    """ Class to provide Vss app functionalities for linux platform """

    OPT_PATH = "/opt"
    OPT_IVLSS = "/opt/ilvss.0"
    ILVSS_PCIE_SUCCESS_STR = "PASS LXPCIE.PCIELINK_AND_SLOT_STATUS"
    LINUX_USR_ROOT_PATH = "/root"
    DICT_PRODUCT_INFO = {"WLYD": "Whitley", "PLYD": "Purley", "EGSD": "EGS"}
    DICT_PACKAGE_INFO = {"WLYD": "stress_whitley_ilvss.pkx", "PLYD": "stress_purley_ilvss.pkx",
                         "EGSD": "stress_egs_ilvss_memory.pkx"}
    DICT_PACKAGE_INFO_STORAGE = {"EGSD": "stress_egs_ilvss_storage_s2.pkx"}

    def __init__(self, log, cfg_opts, os_obj):
        """
        Constructor of the class LinuxVss.

        :param log: Logger object to use for output messages
        :param cfg_opts: config object
        :param os_obj: OS object
        """
        super(LinuxVss, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj
        self._cfg_opts = cfg_opts

        self.bios_version = self._common_content_lib.execute_sut_cmd("dmidecode -t 0 | grep 'Version:'",
                                                                     "Get the platform name", self._command_timeout,
                                                                     self.LINUX_USR_ROOT_PATH)
        self.product_info = self.bios_version.split(":")[1][0:5:].strip()
        if self.DICT_PRODUCT_INFO[self.product_info] is None:
            raise content_exceptions.TestUnSupportedError("This test package is unavailable or not developed to "
                                                          "support this {} platform..".format(self.product_info))

        self._ilvss_runtime = self._common_content_configuration.memory_ilvss_run_time()
        self._vss_path = self._install_collateral.install_ilvss()

    def factory(self, log, cfg_opts, os_obj):
        pass

    def execute_vss_2lm_test_package(self):
        """
        To execute ilVSS tool with 2lm package

        :raise: TestNotImplementedError
        """

        raise content_exceptions.TestNotImplementedError("The function '{}' is not implemented for "
                                                         "Linux platform..".format("execute_vss_2lm_test_package"))

    def execute_vss_1lm_test_package(self):
        """
        To execute ilVSS tool with 1lm package

        :raise: TestNotImplementedError
        """

        raise content_exceptions.TestNotImplementedError("The function '{}' is not implemented for "
                                                         "Linux platform..".format("execute_vss_1lm_test_package"))

    def execute_vss_memory_test_package(self, flow_tree="S145"):
        """
        To execute ilVSS tool with memory package
        """
        ilvss_command = r"./t /pkg /opt/ilvss.0/packages/{} /reconfig /pc {} /flow {} /run /minutes {} /rr " \
                        r"ilvss_log.log".format(self.DICT_PACKAGE_INFO[self.product_info],
                                                self.DICT_PRODUCT_INFO[self.product_info], flow_tree,
                                                self._ilvss_runtime)
        self._log.info("Executing the command : {}".format(ilvss_command))
        self._os.execute_async(ilvss_command, self.OPT_IVLSS)

        self.verify_vss_running(VssMode.ILVSS_MODE)

    def execute_vss_storage_test_package(self, flow_tree="S2"):
        """
        To execute ilVSS tool with storage package
        """
        ilvss_command = r"./t /pkg /opt/ilvss.0/packages/{} /reconfig /pc {} /flow {} /run /minutes {} /rr " \
                        r"ilvss_log.log".format(self.DICT_PACKAGE_INFO_STORAGE[self.product_info],
                                                self.DICT_PRODUCT_INFO[self.product_info], flow_tree,
                                                self._ilvss_runtime)
        self._log.info("Executing the command : {}".format(ilvss_command))
        self._os.execute_async(ilvss_command, self.OPT_IVLSS)

        self.verify_vss_running(VssMode.ILVSS_MODE)

    def __verify_process_running(self, str_process_name):
        """
        Function to find the process running on the SUT.

        :param str_process_name: name of the process to be found
        :return 0 if process is found in the task list else 1
        """
        process_running = self._os.execute("ps -A | grep -i '{}'".format(str_process_name), self._command_timeout,
                                           self.LINUX_USR_ROOT_PATH)

        return process_running.return_code

    def verify_vss_running(self, vss_mode):
        """
        Function to verify that the process is running in the background on SUT.

        :param vss_mode: name of the process to be found
        :return None
        """
        if vss_mode in VssMode.MEMORY_MODE:
            self.process_name = "mem64.exe"
        elif vss_mode in VssMode.MIXED_MODE_1LM:
            self.process_name = "mem64.exe"
        elif vss_mode in VssMode.MIXED_MODE_2LM:
            self.process_name = "mem64.exe PatIO.exe"
        elif vss_mode in VssMode.ILVSS_MODE:
            self.process_name = "texec"

        ret_code = self.__verify_process_running(self.process_name)

        if ret_code == 0:
            self._log.info("{} has been started to execute in the background..".format(self.process_name))
        else:
            raise RuntimeError("{} is not launched in the background..".format(self.process_name))

    def wait_for_vss_to_complete(self, vss_mode):
        """
        Function verify and hold until background process finish running on the SUT.

        :param vss_mode: name of the process to be found
        :return None
        """

        process_running = True

        if vss_mode in VssMode.MEMORY_MODE:
            self.process_name = "mem64.exe"
        elif vss_mode in VssMode.MIXED_MODE_1LM:
            self.process_name = "mem64.exe"
        elif vss_mode in VssMode.MIXED_MODE_2LM:
            self.process_name = "mem64.exe PatIO.exe"
        elif vss_mode in VssMode.ILVSS_MODE:
            self.process_name = "texec"

        while process_running:
            ret_code = self.__verify_process_running(self.process_name)

            if ret_code == 0:
                self._log.info("'texec' is still running in the background..")
                self._log.info("Waiting for the ilVSS execution to complete..")
                time.sleep(TimeConstants.FIVE_MIN_IN_SEC)
            else:
                process_running = False

                self._log.info("ilVSS execution has been completed successfully..")
                self._log.info("{} has been started to execute in the background..".format(self.process_name))

    def verify_vss_logs(self, log_name):
        """
        To verify the vss logs post execution

        :param log_name: Name of the log to be parsed.
        :return: true if log has no errors else fail
        """
        log_dir = self._common_content_lib.get_log_file_dir()

        if not os.path.exists(os.path.join(log_dir, "testcase_logs")):
            log_dir = log_dir + "/" + "testcase_logs"
            os.makedirs(log_dir)

        log_file_path_host = self._common_content_lib.copy_log_files_to_host(
            test_case_id=log_dir, sut_log_files_path=self.OPT_IVLSS, extension=".log")

        return self._memory_common_lib.parse_log_for_error_patterns(
            log_path=os.path.join(log_file_path_host, log_name))

    def configure_vss_stress(self):
        """
        To copy the packages to the SUT.

        :raise: IOError
        """

        stress_pkg_path = Path(os.path.join(self.OPT_PATH, "ilvss.0/packages")).as_posix()

        # folder path in host
        host_folder_path = self._install_collateral.download_tool_to_host(self.DICT_PACKAGE_INFO[self.product_info])
        if not os.path.isfile(host_folder_path):
            log_error = "{} does not exist".format(host_folder_path)
            self._log.error(log_error)
            raise IOError(log_error)

        self._os.copy_local_file_to_sut(host_folder_path, stress_pkg_path)

        self._log.info("ilvss package file '{}' has been copied from host to sut "
                       "for ilvss execution".format(self.DICT_PACKAGE_INFO[self.product_info]))
        self._os.execute("chmod +x %s" % self.DICT_PACKAGE_INFO[self.product_info],
                         self._command_timeout, stress_pkg_path)

        return stress_pkg_path

    def configure_vss_stress_storage(self):
        """
        To copy the packages to the SUT.

        :raise: IOError
        """

        stress_pkg_path = Path(os.path.join(self.OPT_PATH, "ilvss.0/packages")).as_posix()

        # folder path in host
        host_folder_path = self._install_collateral.download_tool_to_host(
            self.DICT_PACKAGE_INFO_STORAGE[self.product_info])
        if not os.path.isfile(host_folder_path):
            log_error = "{} does not exist".format(host_folder_path)
            self._log.error(log_error)
            raise IOError(log_error)

        self._os.copy_local_file_to_sut(host_folder_path, stress_pkg_path)

        self._log.info("ilvss package file '{}' has been copied from host to sut "
                       "for ilvss execution".format(self.DICT_PACKAGE_INFO[self.product_info]))
        self._os.execute("chmod +x %s" % self.DICT_PACKAGE_INFO[self.product_info],
                         self._command_timeout, stress_pkg_path)

        return stress_pkg_path

    def terminating_process(self, process_name):
        """
        To kill the ctc process

        """
        raise NotImplementedError
