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

import threading
import time
import os
import re
import six

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from importlib import import_module
from abc import ABCMeta, abstractmethod
from six import add_metaclass

from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.provider.base_provider import BaseProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.dtaf_content_constants import Mprime95ToolConstant, BurnInConstants, CvCliToolConstant
from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import TimeConstants
from src.lib import content_exceptions
from src.provider.storage_provider import StorageProvider
from src.storage.test.storage_common import StorageCommon


@add_metaclass(ABCMeta)
class StressAppTestProvider(BaseProvider):
    """ Class to provide stress test app functionality """

    LINUX_USR_ROOT_PATH = "/root"
    WAIT_TIME = 10
    NUM_RETRIES = 3

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new StressAppTestProvider object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        """
        super(StressAppTestProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj
        self._sut_os = self._os.os_type

        #  common_content_obj and config object
        self.common_content_lib_obj = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self.command_timeout = self._common_content_configuration.get_command_timeout()
        self._storage_provider = StorageProvider.factory(self._log, self._os, cfg_opts, "os")

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.
        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param cfg_opts: cfg_opts

        :return: object
        """
        package = r"src.provider.stressapp_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "WindowsStressAppTest"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "LinuxStressAppTest"
        elif OperatingSystems.ESXI == os_obj.os_type:
            mod_name = "EsxiStressAppTest"
        else:
            raise NotImplementedError("Test is not implemented for %s" % os_obj.os_type)
        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(log=log, cfg_opts=cfg_opts, os_obj=os_obj)

    @abstractmethod
    def execute_installer_stressapp_test(self, stress_test_command):
        """
        Execute the stress app test file with specific waiting time.

        :param stress_test_command: command to run the stress app test
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def execute_burnin_test(self, log_dir, timeout, bit_location, config_file=None, vm_name=None):
        """
        Execute the burnin app test file with specific waiting time.

        :param log_dir: Log directory path
        :param timeout: run time for burnin test
        :param bit_location: burnin test directory
        :param config_file: work load set burnin config file
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def execute_async_stress_tool(self, stress_tool_cmd, stress_tool_name, executor_path):
        """
        Execute the stress app test file with specific waiting time.

        :param stress_tool_cmd: command to run the stress app test
        :param stress_tool_name: name of the stress tool
        :param executor_path:  Path of the stress tool
        :raise: NotImplementedError
        """
        raise NotImplementedError

    def check_app_running(self, app_name, stress_test_command=None):
        """
        This method check whether application is running or not

        :param app_name: name of the application.
        :param stress_test_command: Command to execute
        :return : None
        :raise: None
        """

        raise NotImplementedError

    @abstractmethod
    def kill_stress_tool(self, stress_tool_name, stress_test_command=None):
        """
        Terminate the stress tool process.

        :param stress_tool_name: Name of the stress tool.
        :param stress_test_command: Command to execute
        :return: None
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def execute_mprime(self, arguments, execution_time, cmd_dir):
        """
        This method is to execute mprime tool.

        :param cmd_dir
        :param arguments
        :param execution_time
        :return unexpected_expect and successful test
        :raise NotImplementedError
        """
        raise NotImplementedError


class WindowsStressAppTest(StressAppTestProvider):
    """ Class to provide stress test app functionality for windows platform """

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new WindowsStressAppTest object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param cfg_opts: cfg_opts
        """
        super(WindowsStressAppTest, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj

    def factory(self, log, cfg_opts, os_obj):
        pass

    def execute_installer_stressapp_test(self, stress_test_command):
        """
        Execute the stress tool test file with specific waiting time.

        :param stress_test_command: command to run the stress app test
        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Linux platform..".format("execute_installer_stressapp_test"))

    def execute_burnin_test(self, log_dir, timeout, bit_location, config_file=None, vm_name=None, copy_log_to_host=True):
        """
        Execute the burnin app test file with specific waiting time.

        :param log_dir: Log directory path
        :param timeout: run time for burnin test
        :param bit_location: burnin test directory
        :param config_file: work load set burnin config file
        :param copy_log_to_host: copy log file to host.
        :raise: NotImplementedError
        """

        bit_log_path = os.path.join(bit_location, BurnInConstants.BURNIN_BIT_LOG)

        # Copy the config file to the folder
        self._log.info("Copy the config file to the burnin tool folder")
        self._os.copy_local_file_to_sut(config_file, bit_location)

        self._log.info("Execute burnin test tool command {}".format(
            BurnInConstants.BURNIN_TEST_CMD_WINDOWS.format(os.path.basename(config_file), timeout)))

        self.execute_async_stress_tool(
            stress_tool_cmd=BurnInConstants.BURNIN_TEST_CMD_WINDOWS.format(os.path.basename(config_file), timeout),
            stress_tool_name=BurnInConstants.BIT_EXE_FILE_NAME_WINDOWS, executor_path=bit_location,
            timeout=timeout * 60)

        if copy_log_to_host:
            time.sleep((timeout * 60) + BurnInConstants.BURNIN_TEST_THRESHOLD_TIMEOUT)

            self.kill_stress_tool(BurnInConstants.BIT_EXE_FILE_NAME_WINDOWS.split('.')[0])

            self._os.copy_file_from_sut_to_local(bit_log_path.strip(), os.path.join(log_dir,
                                                                                    BurnInConstants.BURNIN_BIT_LOG))
            with open(os.path.join(log_dir, BurnInConstants.BURNIN_BIT_LOG)) as f:
                data = f.read()
                if BurnInConstants.BURNIN_TEST_FAIL_CMD in data:
                    raise content_exceptions.TestFail("BurnIn Test ended with failures")

            self._log.info("BurnIn test started and ended successfully")

    def _execute_stress_tool(self, cmd, stress_path, timeout=60):
        """
        Function to execute stress application.

        :param cmd: command to run stress tool
        :param stress_path: path of the executor.
        """
        self._log.info("Starting the stress test..")

        # -t refers to torture test
        self._log.debug("stress test command line is '{}'".format(cmd))
        self._log.debug("stress test is running from directory '{}'".format(stress_path))

        stress_execute_res = self._os.execute(cmd, (timeout + self.command_timeout), stress_path)

        if stress_execute_res.cmd_failed():
            self._log.info("Stress test execution thread has been stopped")

    def execute_async_stress_tool(self, stress_tool_cmd, stress_tool_name, executor_path=None, timeout=60):
        """
        Execute the stress app test file with specific waiting time.

        :param stress_tool_cmd: command to run the stress app test
        :param stress_tool_name: name of the stress tool
        :param executor_path: Path of the stress app tool.
        :param timeout: run time for tool.
        :return : None
        :raise: check_app_running method will fail test if no application running with stress_tool_name
        """

        stress_thread = threading.Thread(target=self._execute_stress_tool,
                                         args=(stress_tool_cmd, executor_path, timeout, ))
        # Thread has been started
        stress_thread.start()
        time.sleep(self.WAIT_TIME)
        if self.check_app_running(stress_tool_name, stress_tool_cmd):
            raise content_exceptions.TestFail("{} stress tool is not running ".format(stress_tool_name))

    def check_app_running(self, app_name, stress_test_command=None):
        """
        This method check whether application is running or not

        :param app_name: name of the application.
        :param stress_test_command : Command to execute
        :return : If application is running return 0 else return 1
        :raise: None
        """
        process_running = self._os.execute('TASKLIST | FINDSTR /I "{}"'.format(app_name),
                                           self.command_timeout)

        return process_running.return_code

    def kill_stress_tool(self, stress_tool_name, stress_test_command=None):
        """
        Terminate the stress test process after running for configured time.

        :param stress_tool_name: Name of the stress tool.
        :param stress_test_command: Command to execute
        :return: None
        :raise: execute_sut_cmd and check_app_running will fail test if no application running with stress_tool_name
        """
        if self.check_app_running(stress_tool_name, stress_test_command):
            self._log.error("{} stress tool is not running to kill ".format(stress_tool_name))
            return
        else:
            self._log.info("killing {} tool".format(stress_tool_name))
            self.common_content_lib_obj.execute_sut_cmd("taskkill /F /IM {}.exe".format(stress_tool_name),
                                                        "killing stress tool", self.command_timeout)

    def execute_mprime(self, arguments, execution_time, cmd_dir):
        """
        This method is to execute mprime tool.

        :param cmd_dir
        :param arguments
        :param execution_time
        :return unexpected_expect and successful test
        :raise NotImplementedError
        """
        raise NotImplementedError


class LinuxStressAppTest(StressAppTestProvider):
    """ Class to provide stress test app functionality for linux platform """

    CAT_COMMAND = "cat {}"
    TEMP = "/tmp"
    RAID_REG = "md\d+.*"
    VERIFY_RAID_CMD = "cat /proc/mdstat"

    def __init__(self, log, cfg_opts, os_obj, arguments=None):
        """
        Create a new LinuxStressAppTest object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param cfg_opts: cfg_opts
        """
        super(LinuxStressAppTest, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)
        self._storage_provider = StorageProvider.factory(self._log, self._os, cfg_opts, "os")

    def factory(self, log, cfg_opts, os_obj):
        pass

    def execute_installer_stressapp_test(self, stress_test_command, timeout=None):
        """
        Execute the stress app test file with specific waiting time.

        :param stress_test_command: command to run the stress app test
        :raise: RuntimeError if stress test execution failed.
        """
        try:
            self._log.info("Starting the stress app test")
            if not timeout:
                timeout = self.command_timeout

            self.common_content_lib_obj.execute_sut_cmd(
                stress_test_command, "Start stress app test", timeout, self.LINUX_USR_ROOT_PATH)
        except Exception as ex:
            raise RuntimeError("Stress app test execution failed with exception '{}'".format(ex))

    def execute_async_stress_tool(self, stress_tool_cmd, stress_tool_name, executor_path=None):
        """
        Execute the stress app test file with specific waiting time.

        :param stress_tool_cmd: command to run the stress app test
        :param stress_tool_name: name of the stress tool
        :param executor_path: Path of the stress app tool.
        :return : None
        :raise: Testfail exception is failed to run stress test
        """
        self._log.info("Starting the Stress Tool command '{}'".format(stress_tool_cmd))
        self._os.execute_async(stress_tool_cmd, cwd=executor_path)
        time.sleep(self.WAIT_TIME)
        if not self.check_app_running(stress_tool_name, stress_tool_cmd):
            raise content_exceptions.TestFail("{} stress tool is not running ".format(stress_tool_name))

    def check_app_running(self, app_name, stress_test_command=None):
        """
        This method check whether application is running or not

        :param app_name: name of the application.
        :param stress_test_command: Stress command
        :return : False if particular application is not running else True
        :raise: None
        """
        check_app_sut_cmd = "ps -ef |grep {}|grep -v grep".format(app_name)
        command_result = self._os.execute(check_app_sut_cmd, self.command_timeout)
        self._log.debug(command_result.stdout)
        if stress_test_command not in command_result.stdout:
            return False
        return True

    def kill_stress_tool(self, stress_tool_name, stress_test_command=None):
        """
        Terminate stress tool process.

        :param stress_tool_name: Name of the stress app tool.
        :param stress_test_command: Command to execute stress tool
        :return : None
        :raise: Raise RuntimeError Exception if failed to kill the stress tool process.
        """
        if not self.check_app_running(stress_tool_name, stress_test_command):
            self._log.debug("{} tool is not running ".format(stress_tool_name))
            return

        self._log.info("killing {} tool".format(stress_tool_name))
        self._os.execute("pkill {}".format(stress_tool_name), self.command_timeout)
        not_killed = True
        num_of_retries = self.NUM_RETRIES
        while not_killed and num_of_retries != 0:
            time.sleep(60)  # give some time for app to terminate itself
            if self.check_app_running(stress_tool_name, stress_test_command):
                self._log.info("{} tool is still running... killing again..".format(stress_tool_name))
                self._os.execute("killall {}".format(stress_tool_name), self.command_timeout)
                num_of_retries -= 1
                continue
            else:
                not_killed = False
        if self.check_app_running(stress_tool_name, stress_test_command):
            raise RuntimeError('{} tool not killed'.format(stress_tool_name))

    def execute_burnin_test(self, log_dir, timeout, bit_location, config_file=None, vm_name=None, copy_log_to_host=True):
        """
        Execute BurnInTest in SUT or VM as per the value of vm_name

        :param copy_log_to_host - Copy log to host
        :raise: content_exception.TestFail if not getting the expected values
        :raise: content_exception.TestError if not generated the bit log file
        """
        self._log.info("Execute burnin test tool")
        find_path = "find /tmp -type f -name 'BiTLog*'"
        bit_location = bit_location + "/" + "burnintest/64bit"
        bit_log_file_loc = self.common_content_lib_obj.execute_sut_cmd(find_path, find_path, self.command_timeout)

        # Delete BiTLog2.log if exists
        delete_file_cmd = "rm -rf {}".format(bit_log_file_loc)
        self._os.execute(delete_file_cmd, self.command_timeout, self.TEMP)

        # Copy the config file to the folder
        self._log.info("Copy the config file to the burnin tool folder")
        self._os.copy_local_file_to_sut(config_file, bit_location)

        lsblk_res = (self._storage_provider.get_booted_device()).strip()
        self._log.info("OS Booted from the device : {}".format(lsblk_res))
        sda_1 = "sda1"
        if not (sda_1 in lsblk_res):
            sed_command = "sed -i 's/{}/{}/' {}".format(sda_1, lsblk_res, os.path.basename(config_file))
            self._log.info("Executing the command : {}".format(sed_command))
            self.common_content_lib_obj.execute_sut_cmd(sed_command, sed_command, self.command_timeout, bit_location)
        self._log.info("Executing the Burn In test command : {}".format(
            BurnInConstants.BURNIN_TEST_CMD_LINUX % (timeout, os.path.basename(config_file))))
        sut_cmd = self._os.execute(BurnInConstants.BURNIN_TEST_CMD_LINUX % (timeout, os.path.basename(config_file)),
                                   self.command_timeout + (
                                           (timeout * 60) + BurnInConstants.BURNIN_TEST_THRESHOLD_TIMEOUT),
                                   bit_location)
        self._log.debug(sut_cmd.stdout.strip())
        self._log.debug(sut_cmd.stderr.strip())
        if BurnInConstants.BURNIN_TEST_START_MATCH not in sut_cmd.stderr.strip():
            raise content_exceptions.TestFail("Looks like BurnInTest is not started")

        debug_log_path = BurnInConstants.BURNIN_TEST_DEBUG_LOG
        if not (vm_name is None):
            debug_log_path = BurnInConstants.BURNIN_TEST_DEBUG_LOG_VM.format(str(vm_name))
        if copy_log_to_host:
            if self._os.check_if_path_exists(Path(os.path.join(bit_location,
                                                               BurnInConstants.BURNIN_TEST_DEBUG_LOG)).as_posix()):
                self._os.copy_file_from_sut_to_local(
                    Path(os.path.join(bit_location, BurnInConstants.BURNIN_TEST_DEBUG_LOG)).as_posix(),
                    os.path.join(log_dir, debug_log_path))
            with open(os.path.join(log_dir, debug_log_path)) as f:
                data = f.read()
                if BurnInConstants.BURNIN_TEST_END_MATCH not in data:
                    raise content_exceptions.TestFail("Looks like BurnInTest not ended successfully")

            bit_log_path = self.common_content_lib_obj.execute_sut_cmd(find_path, "bit log path", self.command_timeout,
                                                                       self.TEMP)
            self._log.info("Bit Log path in SUT is : {}".format(bit_log_path))
            if not bit_log_path.strip():
                raise content_exceptions.TestError("BurnIn test log is not generated")

            bit_log_file = BurnInConstants.BURNIN_BIT_LOG
            if not (vm_name is None):
                bit_log_file = BurnInConstants.BURNIN_BIT_LOG_VM.format(str(vm_name))

            self._os.copy_file_from_sut_to_local(
                bit_log_path.strip(), os.path.join(log_dir, bit_log_file))
            with open(os.path.join(log_dir, bit_log_file)) as f:
                data = f.read()
                if BurnInConstants.BURNIN_TEST_FAIL_CMD in data:
                    raise content_exceptions.TestFail("BurnIn Test ended with failures")

            self._log.info("BurnIn test started and ended successfully")

    def execute_burnin_stresstest(self, log_dir, timeout, bit_location, config_file=None, copy_log_to_host=True,
                                  stress_boot=True):
        """
        Execute BurnInTest in SATA SSD

        :param copy_log_to_host - Copy log to host
        :raise: content_exception.TestFail if not getting the expected values
        :raise: content_exception.TestError if not generated the bit log file
        """
        self._log.info("Execute burnin test tool")
        find_path = "find /tmp -type f -name 'BiTLog*'"
        bit_location = bit_location + "/" + "burnintest/64bit"
        bit_log_file_loc = self.common_content_lib_obj.execute_sut_cmd(find_path, find_path, self.command_timeout)

        # Delete BiTLog2.log if exists
        delete_file_cmd = "rm -rf {}".format(bit_log_file_loc)
        self._os.execute(delete_file_cmd, self.command_timeout, self.TEMP)

        # Copy the config file to the folder
        self._log.info("Copy the config file to the burnin tool folder")
        self._os.copy_local_file_to_sut(config_file, bit_location)
        lsblk_res = (self._storage_provider.get_booted_device()).strip()
        self._log.info("OS Booted from the device : {}".format(lsblk_res))
        sda_1 = "/dev/sda1"

        if stress_boot:
            if not (sda_1 in lsblk_res):
                sed_command = "sed -i 's/{}/{}/' {}".format(sda_1, lsblk_res, os.path.basename(config_file))
                self._log.info("Executing the command : {}".format(sed_command))
                self.common_content_lib_obj.execute_sut_cmd(sed_command, sed_command, self.command_timeout,
                                                            bit_location)
        else:
            sata_ssd = list(set(self._storage_provider.get_smartctl_drive_list()))
            import re
            booted_device = self._storage_provider.get_booted_device()
            booted_device = re.findall("[a-zA-Z]*", booted_device)[0]
            booted_device_drive = "/dev/" + str(booted_device)
            sata_ssd.remove(booted_device_drive)
            non_os_disk = " "
            MNT_POINT = "/mnt/Q{}"
            for each in sata_ssd:
                non_os_disk = non_os_disk + each + " "
                self._storage_provider.mount_the_drive(each, MNT_POINT.format(sata_ssd.index(each)))
                if not (sda_1 in sata_ssd):
                    sed_command = "sed -i 's|{}|{}|g' {}".format(sda_1, non_os_disk, os.path.basename(config_file))
                    self._log.info("Executing the command : {}".format(sed_command))
                    self.common_content_lib_obj.execute_sut_cmd(sed_command, sed_command, self.command_timeout, bit_location)

                self._log.info("Executing the Burn In test command : {}".format(
                    BurnInConstants.BURNIN_TEST_CMD_LINUX % (timeout, os.path.basename(config_file))))
                sut_cmd = self._os.execute(BurnInConstants.BURNIN_TEST_CMD_LINUX % (timeout, os.path.basename(config_file)),
                                           self.command_timeout + (
                                                   (timeout * 60) + BurnInConstants.BURNIN_TEST_THRESHOLD_TIMEOUT),
                                           bit_location)
                self._log.debug(sut_cmd.stdout.strip())
                self._log.debug(sut_cmd.stderr.strip())
                if BurnInConstants.BURNIN_TEST_START_MATCH not in sut_cmd.stderr.strip():
                    raise content_exceptions.TestFail("Looks like BurnInTest is not started")

                debug_log_path = BurnInConstants.BURNIN_TEST_DEBUG_LOG
                if copy_log_to_host:
                    if self._os.check_if_path_exists(Path(os.path.join(bit_location,
                                                                       BurnInConstants.BURNIN_TEST_DEBUG_LOG)).as_posix()):
                        self._os.copy_file_from_sut_to_local(
                            Path(os.path.join(bit_location, BurnInConstants.BURNIN_TEST_DEBUG_LOG)).as_posix(),
                            os.path.join(log_dir, debug_log_path))
                    with open(os.path.join(log_dir, debug_log_path)) as f:
                        data = f.read()
                        if BurnInConstants.BURNIN_TEST_END_MATCH not in data:
                            raise content_exceptions.TestFail("Looks like BurnInTest not ended successfully")

                    bit_log_path = self.common_content_lib_obj.execute_sut_cmd(find_path, "bit log path", self.command_timeout,
                                                                               self.TEMP)
                    self._log.info("Bit Log path in SUT is : {}".format(bit_log_path))
                    if not bit_log_path.strip():
                        raise content_exceptions.TestError("BurnIn test log is not generated")

                    bit_log_file = BurnInConstants.BURNIN_BIT_LOG
                    self._os.copy_file_from_sut_to_local(
                        bit_log_path.strip(), os.path.join(log_dir, bit_log_file))
                    with open(os.path.join(log_dir, bit_log_file)) as f:
                        data = f.read()
                        if BurnInConstants.BURNIN_TEST_FAIL_CMD in data:
                            raise content_exceptions.TestFail("BurnIn Test ended with failures")

            self._log.info("BurnIn test started and ended successfully")

    def execute_burnin_stresstest_on_raid(self, log_dir, timeout, bit_location, config_file=None, copy_log_to_host=True):
        """
        Execute BurnInTest on Raid volume

        :param log_dir: Log directory
        :param timeout: timeout for burnin stress on raid
        :param bit_location: Location of the burnin tool
        :param config_file: config file for burnin tool
        :param copy_log_to_host - Copy log to host
        :raise: content_exception.TestFail if not getting the expected values
        :raise: content_exception.TestError if not generated the bit log file
        """
        self._log.info("Execute burnin test tool")
        find_path = "find /tmp -type f -name 'BiTLog*'"
        bit_location = bit_location + "/" + "burnintest/64bit"
        bit_log_file_loc = self.common_content_lib_obj.execute_sut_cmd(find_path, find_path, self.command_timeout)

        # Delete BiTLog2.log if exists
        delete_file_cmd = "rm -rf {}".format(bit_log_file_loc)
        self._os.execute(delete_file_cmd, self.command_timeout, self.TEMP)

        # Copy the config file to the folder
        self._log.info("Copy the config file to the burnin tool folder")
        self._os.copy_local_file_to_sut(config_file, bit_location)
        lsblk_res = (self._storage_provider.get_booted_device()).strip()
        self._log.info("OS Booted from the device : {}".format(lsblk_res))
        sda_1 = "/dev/sda1"
        verify_raid = self.common_content_lib_obj.execute_sut_cmd(self.VERIFY_RAID_CMD, "Verify RAID",
                                                                  self.command_timeout)
        self._log.debug("Verify raid command output".format(verify_raid))
        import re
        new_raid_list = []
        raid_list = re.findall(self.RAID_REG, verify_raid)
        for each_raid in raid_list:
            if "active" in each_raid and "inactive" not in each_raid:
                raid = each_raid.split(":")[0].strip()
                new_raid_list.append("/dev/{}".format(raid))
        self._log.info("Active raid in the system are {}".format(new_raid_list))
        MNT_POINT = "/mnt/raid_{}"
        num = 1

        for each_raid in new_raid_list:
            self._storage_provider.mount_the_drive(each_raid, MNT_POINT.format(num))
            self._log.debug("Raid volume {} mount successfully to {}".format(each_raid, MNT_POINT.format(num)))
            sed_command = "sed -i 's|{}|{}|g' {}".format(sda_1, MNT_POINT.format(num), os.path.basename(config_file))
            self._log.info("Executing the command : {}".format(sed_command))
            self.common_content_lib_obj.execute_sut_cmd(sed_command, sed_command, self.command_timeout, bit_location)
            num = num+1

            self._log.info("Executing the Burn In test command : {}".format(
                BurnInConstants.BURNIN_TEST_CMD_LINUX % (timeout, os.path.basename(config_file))))
            sut_cmd = self._os.execute(BurnInConstants.BURNIN_TEST_CMD_LINUX % (timeout, os.path.basename(config_file)),
                                       self.command_timeout + (
                                               (timeout * 60) + BurnInConstants.BURNIN_TEST_THRESHOLD_TIMEOUT),
                                       bit_location)
            self._log.debug(sut_cmd.stdout.strip())
            self._log.debug(sut_cmd.stderr.strip())
            if BurnInConstants.BURNIN_TEST_START_MATCH not in sut_cmd.stderr.strip():
                raise content_exceptions.TestFail("Looks like BurnInTest is not started")

            debug_log_path = BurnInConstants.BURNIN_TEST_DEBUG_LOG
            if copy_log_to_host:
                if self._os.check_if_path_exists(Path(os.path.join(bit_location,
                                                                   BurnInConstants.BURNIN_TEST_DEBUG_LOG)).as_posix()):
                    self._os.copy_file_from_sut_to_local(
                        Path(os.path.join(bit_location, BurnInConstants.BURNIN_TEST_DEBUG_LOG)).as_posix(),
                        os.path.join(log_dir, debug_log_path))
                with open(os.path.join(log_dir, debug_log_path)) as f:
                    data = f.read()
                    if BurnInConstants.BURNIN_TEST_END_MATCH not in data:
                        raise content_exceptions.TestFail("Looks like BurnInTest not ended successfully")

                bit_log_path = self.common_content_lib_obj.execute_sut_cmd(find_path, "bit log path", self.command_timeout,
                                                                           self.TEMP)
                self._log.info("Bit Log path in SUT is : {}".format(bit_log_path))
                if not bit_log_path.strip():
                    raise content_exceptions.TestError("BurnIn test log is not generated")

                bit_log_file = BurnInConstants.BURNIN_BIT_LOG
                self._os.copy_file_from_sut_to_local(
                    bit_log_path.strip(), os.path.join(log_dir, bit_log_file))
                with open(os.path.join(log_dir, bit_log_file)) as f:
                    data = f.read()
                    if BurnInConstants.BURNIN_TEST_FAIL_CMD in data:
                        raise content_exceptions.TestFail("BurnIn Test ended with failures")

        self._log.info("BurnIn test started and ended successfully")

    def execute_mprime(self, arguments, execution_time, cmd_dir, check_mprime=False):
        """
        This method is to execute mprime tool.

        :param cmd_dir
        :param arguments
        :param execution_time
        :param check_mprime: check mprime memory use
        :return unexpected_expect and successful test
        :raise content_exception
        """
        self._install_collateral.install_python_package('pexpect')
        args = ""
        cpu_utilisation_old_value = 0
        try:
            for key, value in arguments.items():
                args = args + '"%s"="%s" ' % (key, value)
            args = args.strip()
            self._log.debug(args)
            self._log.debug("Execute : mprime_linux.py {}".format(args))
            self._os.execute_async("python3 mprime_linux.py %s > %s" % (args, Mprime95ToolConstant.MPRIME_LOG_FILE),
                                   cmd_dir)

            # Waiting for some time to complete mprime questions
            time.sleep(TimeConstants.FIVE_MIN_IN_SEC)
            prev_total_mem_in_use = 0
            start_time = time.time()
            while time.time() - start_time <= execution_time:
                if not self.check_app_running(app_name=Mprime95ToolConstant.MPRIME_TOOL_NAME,
                                              stress_test_command="./" + Mprime95ToolConstant.MPRIME_TOOL_NAME):
                    raise content_exceptions.TestFail('mprime95 tool is not executing')
                self._log.debug('mprime process is executing...')
                if check_mprime:
                    current_total_mem_in_use = float(self._os.execute("numastat mprime", self.command_timeout, cmd_dir).stdout.split()[-1])
                    if int(prev_total_mem_in_use/1E3) > int(current_total_mem_in_use/1E3):
                        raise content_exceptions.TestFail("Test Failed, as mprime memory usage not as expected - {}".
                                                          format(current_total_mem_in_use))
                    self._log.info("mprime has The expected memory usage , current value - {}".
                                   format(current_total_mem_in_use))
                    prev_total_mem_in_use = current_total_mem_in_use
                    time.sleep(TimeConstants.FIVE_MIN_IN_SEC)
                cpu_utilisation = self.common_content_lib_obj.get_cpu_utilization()
                if cpu_utilisation < cpu_utilisation_old_value:
                    raise content_exceptions.TestFail('Unexpected CPU utilization is Captured and old cpu utilization '
                                                      'value {} and new CPU utilization value is {} '.format(
                        cpu_utilisation_old_value, cpu_utilisation))
                time.sleep(TimeConstants.ONE_MIN_IN_SEC)
            self._log.info("Terminate the mprime process")
            self.kill_stress_tool(stress_tool_name=Mprime95ToolConstant.MPRIME_TOOL_NAME, stress_test_command=
            "./" + Mprime95ToolConstant.MPRIME_TOOL_NAME)
            output = self.common_content_lib_obj.execute_sut_cmd(sut_cmd=self.CAT_COMMAND.format(
                Mprime95ToolConstant.MPRIME_LOG_FILE), cmd_str="check mprime log file",
                execute_timeout=self.command_timeout, cmd_path=cmd_dir)

            self._log.debug(output)

            unexpected_expect_regex = re.search(Mprime95ToolConstant.REGEX_FOR_UNEXPECTED_EXPECTS, output.strip())
            successfull_test_regex = re.search(Mprime95ToolConstant.REGEX_FOR_SUCCESSFULL_EXPECTS, output.strip())
            if not successfull_test_regex:
                raise content_exceptions.TestFail('Unknown Error while executing prime95')
            unexpected_expect_test = []
            successfull_test = eval(successfull_test_regex.group(1).strip())
            if unexpected_expect_regex:
                unexpected_expect_test = eval(unexpected_expect_regex.group(1).strip())

            return unexpected_expect_test, successfull_test
        except Exception as ex:
            raise content_exceptions.TestFail(ex)

    def execute_cv_cli_test(self, arguments, execution_time, cv_app_dir, host_log_dir):
        """
        This method is to execute CXL_CV_CLI tool.

        :param cv_app_dir
        :param arguments
        :param execution_time
        :param host_log_dir
        :return json_file_path_on_host
        :raise content_exception
        """
        self._install_collateral.install_python_package('pexpect')
        args = ""
        try:
            for value in arguments:
                args = args + '"%s" ' % value
            args = args.strip()
            self._log.debug(args)
            self._log.debug("Execute : cxl_cv_linux.py {}".format(args))
            start_time = time.time()
            self._os.execute_async("python cxl_cv_linux.py %s > %s" % (args, CvCliToolConstant.CV_CLI_LOG_FILE),
                                   cv_app_dir)
            self._log.info("Wait for 5 minutes for CV_CLI test app to run...")
            while time.time() - start_time <= execution_time:
                time.sleep(TimeConstants.TEN_SEC)
            self._log.info("Terminate the cv_cli process")
            self.kill_stress_tool(stress_tool_name=CvCliToolConstant.CV_CLI_TOOL_NAME, stress_test_command=
                                  "./" + CvCliToolConstant.CV_CLI_TOOL_NAME)
            output = self.common_content_lib_obj.execute_sut_cmd(sut_cmd=self.CAT_COMMAND.format(
                CvCliToolConstant.CV_CLI_LOG_FILE), cmd_str="check cv_cli log file",
                execute_timeout=self.command_timeout, cmd_path=cv_app_dir)
            self._log.info(output)
            if not output:
                raise content_exceptions.TestFail("No output data received from cv_cli_linux.py....")
            json_file = output.strip().split()[-1]
            self._log.info("Json output file = {}".format(json_file))

            if self._os.check_if_path_exists(Path(os.path.join(cv_app_dir, json_file)).as_posix()):
                self._os.copy_file_from_sut_to_local(
                    Path(os.path.join(cv_app_dir, json_file)).as_posix(),
                    Path(os.path.join(host_log_dir, json_file)).as_posix())

            return Path(os.path.join(host_log_dir, json_file)).as_posix()

        except Exception as ex:
            raise content_exceptions.TestFail(ex)


class EsxiStressAppTest(StressAppTestProvider):
    """ Class to provide stress test app functionality for esxi platform """

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new EsxiStressAppTest object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param cfg_opts: cfg_opts
        """
        super(EsxiStressAppTest, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj

    def factory(self, log, cfg_opts, os_obj):
        pass

    def execute_installer_stressapp_test(self, stress_test_command):
        """
        Execute the stress tool test file with specific waiting time.

        :param stress_test_command: command to run the stress app test
        :raise: NotImplementedError
        """
        raise NotImplementedError

    def execute_burnin_test(self, log_dir, timeout, bit_location, config_file=None, vm_name=None, copy_log_to_host=True,
                            vm_os_obj=None, common_content_lib_obj=None):
        """
        Execute the burnin app test file with specific waiting time.

        :param log_dir: Log directory path
        :param timeout: run time for burnin test
        :param bit_location: burnin test directory
        :param config_file: work load set burnin config file
        :param copy_log_to_host: copy log file to host.
        :raise: NotImplementedError
        """
        os_libobj = self._os
        common_content_libobj = self.common_content_lib_obj
        if vm_os_obj != None:
            os_libobj = vm_os_obj
        if common_content_lib_obj != None:
            common_content_libobj = common_content_lib_obj

        print(vm_name)
        if "RHEL" in vm_name or "CENTOS" in vm_name:
            self._log.info("Execute burnin test tool")
            find_path = "find /tmp -type f -name 'BiTLog*'"
            bit_location = bit_location + "/" + "burnintest/64bit"
            bit_log_file_loc = common_content_libobj.execute_sut_cmd(find_path, find_path, self.command_timeout)
            self.TEMP = "/tmp"
            # Delete BiTLog2.log if exists
            delete_file_cmd = "rm -rf {}".format(bit_log_file_loc)
            os_libobj.execute(delete_file_cmd, self.command_timeout, self.TEMP)

            # Copy the config file to the folder
            self._log.info("Copy the config file to the burnin tool folder")
            os_libobj.copy_local_file_to_sut(config_file, bit_location)

            lsblk_res = (self._storage_provider.get_booted_device(common_content_libobj)).strip()
            self._log.info("OS Booted from the device : {}".format(lsblk_res))
            sda_1 = "sda1"
            if not (sda_1 in lsblk_res):
                sed_command = "sed -i 's/{}/{}/' {}".format(sda_1, lsblk_res, os.path.basename(config_file))
                self._log.info("Executing the command : {}".format(sed_command))
                common_content_libobj.execute_sut_cmd(sed_command, sed_command, self.command_timeout,
                                                      bit_location)
            self._log.info("Executing the Burn In test command : {}".format(
                BurnInConstants.BURNIN_TEST_CMD_LINUX_VM.format(timeout, os.path.basename(config_file))))
            sut_cmd = os_libobj.execute(
                BurnInConstants.BURNIN_TEST_CMD_LINUX_VM.format(timeout, os.path.basename(config_file)),
                self.command_timeout + (
                        (timeout * 60) + BurnInConstants.BURNIN_TEST_THRESHOLD_TIMEOUT),
                bit_location)
            self._log.debug(sut_cmd.stdout.strip())
            self._log.debug(sut_cmd.stderr.strip())
            print("out", sut_cmd.stdout.strip())
            print("err ", sut_cmd.stderr.strip())
            time.sleep(30)
            # print(os_libobj.os_type)
            if BurnInConstants.BURNIN_TEST_START_MATCH not in sut_cmd.stderr.strip():
                raise content_exceptions.TestFail("Looks like BurnInTest is not started")

            debug_log_path = BurnInConstants.BURNIN_TEST_DEBUG_LOG
            if not (vm_name is None):
                debug_log_path = BurnInConstants.BURNIN_TEST_DEBUG_LOG_VM.format(str(vm_name))
            if copy_log_to_host:
                if os_libobj.check_if_path_exists(Path(os.path.join(bit_location,
                                                                    BurnInConstants.BURNIN_TEST_DEBUG_LOG)).as_posix()):
                    os_libobj.copy_file_from_sut_to_local(
                        Path(os.path.join(bit_location, BurnInConstants.BURNIN_TEST_DEBUG_LOG)).as_posix(),
                        os.path.join(log_dir, debug_log_path))
                with open(os.path.join(log_dir, debug_log_path)) as f:
                    data = f.read()
                    if BurnInConstants.BURNIN_TEST_END_MATCH not in data:
                        raise content_exceptions.TestFail("Looks like BurnInTest not ended successfully")

                bit_log_path = common_content_libobj.execute_sut_cmd(find_path, "bit log path",
                                                                     self.command_timeout,
                                                                     self.TEMP)
                self._log.info("Bit Log path in SUT is : {}".format(bit_log_path))
                if not bit_log_path.strip():
                    raise content_exceptions.TestError("BurnIn test log is not generated")

                bit_log_file = BurnInConstants.BURNIN_BIT_LOG
                if not (vm_name is None):
                    bit_log_file = BurnInConstants.BURNIN_BIT_LOG_VM.format(str(vm_name))

                os_libobj.copy_file_from_sut_to_local(
                    bit_log_path.strip(), os.path.join(log_dir, bit_log_file))
                with open(os.path.join(log_dir, bit_log_file)) as f:
                    data = f.read()
                    if BurnInConstants.BURNIN_TEST_FAIL_CMD in data:
                        raise content_exceptions.TestFail("BurnIn Test ended with failures")

                self._log.info("BurnIn test started and ended successfully")
        elif "WINDOWS" in vm_name:
            bit_log_path = bit_location + "\\" + BurnInConstants.BURNIN_BIT_LOG_VM_WIN
            # Copy the config file to the folder
            self._log.info("Copy the config file to the burnin tool folder")
            print(bit_location, "$$$$$$$$$$$$")
            os_libobj.copy_local_file_to_sut(config_file, bit_location)
            # self._os.copy_local_file_to_sut(config_file, bit_location)
            self._log.info("Execute burnin test tool command {}".format(
                BurnInConstants.BURNIN_TEST_CMD_WINDOWS.format(os.path.basename(config_file), timeout)))

            self.execute_async_stress_tool(
                stress_tool_cmd=BurnInConstants.BURNIN_TEST_CMD_WINDOWS.format(os.path.basename(config_file), timeout),
                stress_tool_name=BurnInConstants.BIT_EXE_FILE_NAME_WINDOWS, executor_path=bit_location,
                timeout=timeout * 60, os_obj=os_libobj)

            if copy_log_to_host:
                time.sleep((timeout * 60) + BurnInConstants.BURNIN_TEST_THRESHOLD_TIMEOUT)

                self.kill_stress_tool(BurnInConstants.BIT_EXE_FILE_NAME_WINDOWS.split('.')[0], os_obj=os_libobj,
                                      common_content_obj=common_content_libobj)
                bit_log_path = bit_location + "\\" + BurnInConstants.BURNIN_BIT_LOG_VM_WIN
                log_path = Path("C:\\Automation\\burner\\")
                print(Path(os.path.join(log_path, BurnInConstants.BURNIN_BIT_LOG_VM_WIN)))
                print(os.path.join(log_dir, BurnInConstants.BURNIN_BIT_LOG_NEW.format(vm_name)))
                file_name = os_libobj.execute(r"where /r C:\Automation\burner BIT_log_*.log", 10)
                os_libobj.copy_file_from_sut_to_local(Path(file_name.stdout.strip()),
                                                      os.path.join(log_dir,
                                                                   BurnInConstants.BURNIN_BIT_LOG_NEW.format(vm_name)))
                with open(os.path.join(log_dir, BurnInConstants.BURNIN_BIT_LOG_NEW.format(vm_name))) as f:
                    data = f.read()
                    if BurnInConstants.BURNIN_TEST_FAIL_CMD in data:
                        self._log.info("BurnIn Test ended with failures")

                self._log.info("BurnIn test started and ended successfully")
        else:
            self._log.error("This function is not implemented for OS {}".format(vm_name))
            raise NotImplementedError

    def _execute_stress_tool(self, cmd, stress_path, timeout=60, os_obj=None):
        """
        Function to execute stress application.

        :param cmd: command to run stress tool
        :param stress_path: path of the executor.
        """
        if os_obj == None:
            os_obj = self._os
        self._log.info("Starting the stress test..")
        print("test start")
        # -t refers to torture test
        self._log.debug("stress test command line is '{}'".format(cmd))
        self._log.debug("stress test is running from directory '{}'".format(stress_path))

        stress_execute_res = os_obj.execute(cmd, (timeout + self.command_timeout), stress_path)

        if stress_execute_res.cmd_failed():
            self._log.info("Stress test execution thread has been stopped")

    def execute_async_stress_tool(self, stress_tool_cmd, stress_tool_name, executor_path=None, timeout=60, os_obj=None):
        """
        Execute the stress app test file with specific waiting time.

        :param stress_tool_cmd: command to run the stress app test
        :param stress_tool_name: name of the stress tool
        :param executor_path: Path of the stress app tool.
        :param timeout: run time for tool.
        :return : None
        :raise: check_app_running method will fail test if no application running with stress_tool_name
        """
        if os_obj == None:
            os_obj = self._os
        stress_thread = threading.Thread(target=self._execute_stress_tool,
                                         args=(stress_tool_cmd, executor_path, timeout, os_obj))
        # Thread has been started
        stress_thread.start()
        time.sleep(self.WAIT_TIME)
        if self.check_app_running(stress_tool_name, stress_tool_cmd, os_obj=os_obj):
            raise content_exceptions.TestFail("{} stress tool is not running ".format(stress_tool_name))

    def check_app_running(self, app_name, stress_test_command=None, os_obj=None):
        """
        This method check whether application is running or not

        :param app_name: name of the application.
        :param stress_test_command : Command to execute
        :return : If application is running return 0 else return 1
        :raise: None
        """
        if os_obj == None:
            os_obj = self._os
        process_running = os_obj.execute('TASKLIST | FINDSTR /I "{}"'.format(app_name),
                                         self.command_timeout)

        return process_running.return_code

    def kill_stress_tool(self, stress_tool_name, stress_test_command=None, os_obj=None, common_content_obj=None):
        """
        Terminate the stress test process after running for configured time.

        :param stress_tool_name: Name of the stress tool.
        :param stress_test_command: Command to execute
        :return: None
        :raise: execute_sut_cmd and check_app_running will fail test if no application running with stress_tool_name
        """
        # raise NotImplementedError
        if common_content_obj == None:
            common_content_obj = self.common_content_lib_obj
        if os_obj == None:
            os_obj = self._os
        if self.check_app_running(stress_tool_name, stress_test_command, os_obj=os_obj):
            self._log.error("{} stress tool is not running to kill ".format(stress_tool_name))
            return
        else:
            self._log.info("killing {} tool".format(stress_tool_name))
            common_content_obj.execute_sut_cmd("taskkill /F /IM {}.exe".format(stress_tool_name),
                                               "killing stress tool", self.command_timeout)

    def execute_mprime(self, arguments, execution_time, cmd_dir):
        """
        This method is to execute mprime tool.

        :param cmd_dir
        :param arguments
        :param execution_time
        :return unexpected_expect and successful test
        :raise NotImplementedError
        """
        raise NotImplementedError


