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
import time
import re

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs, VMProvider
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.provider.memory_provider import MemoryProvider
from src.lib import content_exceptions
from src.lib.content_artifactory_utils import ContentArtifactoryUtils
from src.memory.lib.memory_common_lib import MemoryCommonLib
from pathlib2 import Path


class ilvssutil(VirtualizationCommon):
    """
    VMX + VT-d + Stress/Stability

    The purpose of this test case is making sure the creation of 200 VMs guest on KVM Hypervisor, and test
    basic functionality ex. VM Power cycle, MLC workload and SRIOV workload.
    """
    PROCESS_NAME = "texec"
    LOG_NAME = "ilvss_log.log"

    util_constants = {
        "COLLATERAL_DIR_NAME": 'collateral',
        "LINUX_USR_SBIN_PATH": "/usr/sbin",
        "SEL_ZIP_FILE": "SELViewer.zip",
        "WINDOWS_MEM_REBOOTER_ZIP_FILE": "mem_rebooter_installer_win-20190206.zip",
        "LINUX_USR_ROOT_PATH": "/root"
    }
    OPT = "/opt"
    ILVSS_CONSTANTS = {"VSS_FILE": "VSS.zip", "OPT_PATH": "/opt", "OPT_IVLSS": "/opt/ilvss.0"}
    DICT_PACKAGE_INFO = {"WLYD": "stress_whitley_ilvss.pkx", "PLYD": "stress_purley_ilvss.pkx",
                         "EGSD": "stress_egs.pkx"}
    LINUX_USR_ROOT_PATH = "/root"
    DICT_PRODUCT_INFO = {"WLYD": "Whitley", "PLYD": "Purley", "EGSD": "EGS"}
    ILVSS_MODE = "texec"
    OPT_IVLSS = "/opt/ilvss.0"
    MEMORY_MODE = "memory mode"  # memory mode
    MIXED_MODE_1LM = "mixed mode 1LM"  # 1LM
    MIXED_MODE_2LM = "mixed mode 2LM"  # 2LM
    FLOW_TREE = "s3"
    MEM_FLOW = "Mem"
    COLLATERAL_DIR_NAME = 'collateral'
    ILVSS_RUNTIME = 30

    SCREEN_ZIP_NAME = "screen.zip"
    SCREEN_RPM_NAME = "screen-4.1.0-0.25.20120314git3c2946.el7.x86_64.rpm"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new KvmVmResetStress object.

        """
        super(ilvssutil, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        if self.os.os_type != OperatingSystems.LINUX:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self._artifactory_obj = ContentArtifactoryUtils(self._log, self.os, self._common_content_lib, cfg_opts)
        self._mlc_runtime = self._common_content_configuration.memory_mlc_run_time()
        self._memory_provider = MemoryProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self.os)
        self._ilvss_runtime = self._common_content_configuration.memory_ilvss_run_time()
        self._memory_common_lib = MemoryCommonLib(self._log, cfg_opts, self.os)
        self.bios_version = self._common_content_lib.execute_sut_cmd("dmidecode -t 0 | grep 'Version:'",
                                                                     "Get the platform name", self._command_timeout,
                                                                     self.LINUX_USR_ROOT_PATH)
        self.product_info = self.bios_version.split(":")[1][0:5:].strip()
        self._vm_provider = VMProvider.factory(test_log, self._cfg_opts, self.os)
        if self.DICT_PRODUCT_INFO[self.product_info] is None:
            raise content_exceptions.TestUnSupportedError("This test package is unavailable or not developed to "
                                                          "support this {} platform..".format(self.product_info))

    def install_ilvss(self, common_content_vm, vm_os):
        """
        To Install ilvss tool

        :return: None
        """
        """
          To Install ilvss tool

          :return: None
          """
        if OperatingSystems.LINUX == self.os.os_type:
            # To set the current date and time on SUT
            common_content_vm.set_datetime_on_sut()
            # ilvss_file_name = "ilvss-3.6.25.run"
            ilvss_file_name, ilvss_license_key_file_name = self._common_content_configuration.get_ilvss_file_name_license_name()
            self._log.info("ilvss man file name from config is : {}".format(ilvss_file_name))
            self._log.info("ilvss licence key file name from config is : {}".format(ilvss_license_key_file_name))
            ilvss_file_path_host = self._artifactory_obj.download_tool_to_automation_tool_folder(ilvss_file_name)
            self._log.info("ilvss file path in Host : {}".format(ilvss_file_path_host))
            ilvss_license_key_path_host = self._artifactory_obj.download_tool_to_automation_tool_folder(
                ilvss_license_key_file_name)
            self._log.info("ilvss licence key path in Host : {}".format(ilvss_license_key_path_host))
            # To delete existing ilvss tool
            common_content_vm.execute_sut_cmd("rm -rf {}".format(ilvss_file_name),
                                                     "To delete tool", self._command_timeout)
            self._log.info("Copying {} file to SUT ....".format(ilvss_file_name))
            vm_os.copy_local_file_to_sut(source_path=ilvss_file_path_host,
                                            destination_path=self.util_constants["LINUX_USR_ROOT_PATH"])
            # To give chmod permission
            common_content_vm.execute_sut_cmd(
                sut_cmd="chmod +x {}".format(ilvss_file_name), cmd_str="To give chmod permission",
                execute_timeout=self._command_timeout, cmd_path=self.util_constants["LINUX_USR_ROOT_PATH"])
            # Remove the existing installed ilvss tool
            common_content_vm.execute_sut_cmd(
                "rm -rf ilvss.* *.log", "Removing the existing installed ilvss tool", self._command_timeout, self.OPT)

            self._log.info("Existing ilvss logs has been deleted")
            self._log.info("Installing ilvss tool in the SUT ...")
            # To install ilvss
            common_content_vm.execute_sut_cmd("VSS=I ./{}".format(ilvss_file_name), "To install ilvss tool",
                                                     self._command_timeout, self.util_constants["LINUX_USR_ROOT_PATH"])
            self._log.info("ILVSS tool has been installed successfully")

            self._log.info("Copying licence key : {} to SUT ....".format(self.OPT))
            # To copy license key
            vm_os.copy_local_file_to_sut(source_path=ilvss_license_key_path_host,
                                        destination_path=self.OPT)
            vm_os.copy_local_file_to_sut(source_path=ilvss_license_key_path_host,
                                            destination_path="{}/{}/".format(self.OPT,"ilvss.0"))
        else:
            self._log.error("ILVSS is not supported on OS '%s'" % self.os.sut_os)
            raise NotImplementedError("ILVSS is not supported on OS '%s'" % self.os.sut_os)

    def execute_vss_memory_test_package(self, vm_os_obj, common_content_vm, run_time):
        """
        To execute ilVSS tool with memory package
        """

        common_content_vm.set_datetime_on_sut()
        vm_os_obj.execute_async(r"./t /pkg /opt/ilvss.0/packages/{} /reconfig /pc {} /flow {} /run /minutes {} /rr "
                               r"ilvss_log.log".
                               format(self.DICT_PACKAGE_INFO[self.product_info],
                                      self.DICT_PRODUCT_INFO[self.product_info], self.MEM_FLOW,
                                      run_time), self.OPT_IVLSS)

        self.verify_vss_running(self.ILVSS_MODE, vm_os_obj)

    def trigger_vss_memory_test_package(self, vm_os_obj, common_content_vm, run_time):
        """
        To execute ilVSS tool with memory package
        """

        common_content_vm.set_datetime_on_sut()
        common_content_vm.execute_sut_cmd(r"./t /pkg /opt/ilvss.0/packages/{} /reconfig /pc {} /flow {} /run /minutes {} /rr "
                               r"ilvss_log.log".
                               format(self.DICT_PACKAGE_INFO[self.product_info],
                                      self.DICT_PRODUCT_INFO[self.product_info], self.MEM_FLOW,
                                      run_time), cmd_str="Run Ilvss Tool",
                                        execute_timeout=(self._command_timeout + (run_time * 60)),
                                        cmd_path=self.OPT_IVLSS)

        # self.verify_vss_running(self.ILVSS_MODE, vm_os_obj)

    def verify_vss_running(self, vss_mode, vm_os_obj):
        """
        Function to verify that the process is running in the background on SUT.

        :param vss_mode: name of the process to be found
        :return None
        """
        if vss_mode in self.MEMORY_MODE:
            self.process_name = "mem64.exe"
        elif vss_mode in self.MIXED_MODE_1LM:
            self.process_name = "mem64.exe"
        elif vss_mode in self.MIXED_MODE_2LM:
            self.process_name = "mem64.exe PatIO.exe"
        elif vss_mode in self.ILVSS_MODE:
            self.process_name = "texec"

        ret_code = self.__verify_process_running(self.process_name, vm_os_obj)

        if ret_code == 0:
            self._log.info("{} has been started to execute in the background..".format(self.process_name))
        else:
            raise RuntimeError("{} is not launched in the background..".format(self.process_name))

    def __verify_process_running(self, str_process_name, vm_os_obj):
        """
        Function to find the process running on the SUT.

        :param str_process_name: name of the process to be found
        :return 0 if process is found in the task list else 1
        """
        process_running = vm_os_obj.execute("ps -A | grep -i '{}'".format(str_process_name), self._command_timeout,
                                           self.LINUX_USR_ROOT_PATH)

        return process_running.return_code

    def get_collateral_path(self):
        """
        Function to get the collateral directory path

        :return: collateral_path
        """
        try:
            parent_path = Path(os.path.dirname(os.path.realpath(__file__)))
            collateral_path = os.path.join(str(parent_path), self.COLLATERAL_DIR_NAME)
            return collateral_path
        except Exception as ex:
            self._log.error("Exception occurred while running running the 'get_collateral_path' function")
            raise ex

    def wait_for_vss_to_complete(self, vss_mode, vm_os_obj, run_time=15):
        """
        Function verify and hold until background process finish running on the SUT.

        :param vss_mode: name of the process to be found
        :return None
        """

        process_running = True

        if vss_mode in self.MEMORY_MODE:
            self.process_name = "mem64.exe"
        elif vss_mode in self.MIXED_MODE_1LM:
            self.process_name = "mem64.exe"
        elif vss_mode in self.MIXED_MODE_2LM:
            self.process_name = "mem64.exe PatIO.exe"
        elif vss_mode in self.ILVSS_MODE:
            self.process_name = "texec"

        start_time = time.time()
        seconds = run_time * 60

        while process_running:
            ret_code = self.verify_vss_running_no_exception(self.process_name, vm_os_obj)
            current_time = time.time()
            elapsed_time = current_time - start_time

            if ret_code == 0:
                self._log.info("'texec' is still running in the background..")
                self._log.info("Waiting for the ilVSS execution to complete..")
                time.sleep(30)
            elif elapsed_time > seconds:
                self._vm_provider.kill_running_tool_in_vm(self.process_name, vm_os_obj)
                time.sleep(2)
            else:
                process_running = False
                self._log.info("ilVSS execution has been completed successfully..")
                self._log.info("{} has been started to execute in the background..".format(self.process_name))

        return ret_code

    def verify_vss_running_no_exception(self, vss_mode, vm_os_obj):
        """
        Function to verify that the process is running in the background on SUT.

        :param vss_mode: name of the process to be found
        :return None
        """
        if vss_mode in self.MEMORY_MODE:
            self.process_name = "mem64.exe"
        elif vss_mode in self.MIXED_MODE_1LM:
            self.process_name = "mem64.exe"
        elif vss_mode in self.MIXED_MODE_2LM:
            self.process_name = "mem64.exe PatIO.exe"
        elif vss_mode in self.ILVSS_MODE:
            self.process_name = "texec"

        ret_code = self.__verify_process_running(self.process_name, vm_os_obj)

        if ret_code == 0:
            self._log.info("{} has been started to execute in the background..".format(self.process_name))
        else:
            self._log.info("{} has been stopped..".format(self.process_name))

        return ret_code

    def wait_for_vss_to_complete_kill(self, vss_mode, vm_os_obj, max_wait_time_min):
        """
        Function verify and hold until background process finish running on the SUT.

        :param vss_mode: name of the process to be found
        :return None
        """
        process_running = True

        if vss_mode in self.MEMORY_MODE:
            self.process_name = "mem64.exe"
        elif vss_mode in self.MIXED_MODE_1LM:
            self.process_name = "mem64.exe"
        elif vss_mode in self.MIXED_MODE_2LM:
            self.process_name = "mem64.exe PatIO.exe"
        elif vss_mode in self.ILVSS_MODE:
            self.process_name = "texec"

        start_time = time.clock()
        while process_running:
            ret_code = self.__verify_process_running(self.process_name, vm_os_obj)
            cur_time = time.clock()
            elapsed_time = cur_time - start_time
            if elapsed_time >= (max_wait_time_min * 60):
                self._vm_provider.kill_running_tool_in_vm(self.process_name, vm_os_obj)
                break
            check_running_cmd = vm_os_obj.execute("ps -A | grep -i '{}'".format(self.process_name), self._command_timeout,
                              self.LINUX_USR_ROOT_PATH)
            check_tool = re.search("{}".format(self.process_name), check_running_cmd.stdout, flags=re.IGNORECASE | re.M)
            if check_tool is None:
                self._log.warning("Warn: killing {} tool not needed as process does not exists!".format(self.process_name))
                break
            if ret_code == 0:
                self._log.debug("'texec' is still running in the background..")
                self._log.debug("Waiting for the ilVSS execution to complete..")
                time.sleep(2)
            else:
                process_running = False

                self._log.info("ilVSS execution has been completed successfully..")
                self._log.info("{} has been started to execute in the background..".format(self.process_name))

    def verify_vss_logs(self, log_name, vm_os_obj, common_content_lib_vm):
        """
        To verify the vss logs post execution

        :param log_name: Name of the log to be parsed.
        :return: true if log has no errors else fail
        """
        log_dir = self._common_content_lib.get_log_file_dir()

        if not os.path.exists(os.path.join(log_dir, "testcase_logs")):
            log_dir = log_dir + "/" + "testcase_logs"
            os.makedirs(log_dir)

        log_file_path_host = common_content_lib_vm.copy_log_files_to_host(
            test_case_id=log_dir, sut_log_files_path=self.OPT_IVLSS, extension=".log")

        return self._memory_common_lib.parse_log_for_error_patterns(
            log_path=os.path.join(log_file_path_host, log_name))

    def verify_vss_logs_vm(self, log_name, vm_os_obj, common_content_lib_vm):
        """
        To verify the vss logs post execution

        :param log_name: Name of the log to be parsed.
        :return: true if log has no errors else fail
        """
        log_dir = self._common_content_lib.get_log_file_dir()

        if not os.path.exists(os.path.join(log_dir, "testcase_logs")):
            log_dir = log_dir + "\\" + "testcase_logs"
            os.makedirs(log_dir)

        log_file_path_host = common_content_lib_vm.copy_log_files_to_host(
            test_case_id=log_dir, sut_log_files_path=self.OPT_IVLSS, extension=".log")

        return self._memory_common_lib.parse_log_for_error_patterns(
            log_path=os.path.join(log_file_path_host, log_name))
