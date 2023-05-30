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

from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral


class DsaBaseTest(ContentBaseTestCase):
    """
    Base class extension for DsaBaseTest which holds common functions.
    """
    LIST_OF_DSA_DIR = ['devices', 'drivers', 'drivers_autoprobe', 'drivers_probe', 'uevent']
    INSTALL_DEPENDENCY_PACKAGE = ["libuuid-devel", "json-c-devel", "kmod-devel", "libudev-devel", "xmlto*", "git"]
    LIST_FILES_CMD = "ls"
    DSA_DRIVER_DIR = "/sys/bus/dsa"
    HOST_VALIDATE_CMD = "virt-host-validate"
    INTEL_IOMMU_ON_STR = "intel_iommu=on,sm_on"
    INTEL_IOMMU_ON_WITH_PARAMETERS = "intel_iommu=on,sm_on no5lvl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce"
    CHECK_INTEL_IOMMU_REGEX = "Checking if IOMMU is enabled by kernel.*PASS"
    LSMOD_GREP_CMD = "lsmod | grep idxd"
    IDXD_LIST_DRIVER = ['idxd', 'idxd_mdev']
    LSPCI_CMD = "lspci | grep 0b25"
    REGEX_OB25_CMD = "System peripheral: Intel Corporation Device 0b25"
    REGEX_0CFE_CMD = "System peripheral: Intel Corporation Device 0cfe"
    DSA_DEVICE_COUNT = 8
    DSA_WQ_COUNT_DICT = {"2S": 16, "4S" : 32, "8S" : 64}
    DSA_OPCODE_TEST_DICT = {"2S": "16 of 16", "4S": "32 of 32", "8S": "64 of 64"}
    LSPCI_IAX_CMD = "lspci | grep 0cfe"
    REGEX_DSA_CMD = r"dsa\d+"
    REGEX_IAX_CMD = r"iax\d+"
    DMESG_IDXD_CMD = "dmesg | grep idxd"
    ERROR_STR = "error"
    DSA_DEVICE_WQ_LIST = ["dsa0", "wq0.0", "wq0.1"]
    DSA_DEVICE_WQ_STATUS_LIST = ["enabled", "enabled", "enabled"]
    DSA_DEVICE_DICT = {}
    ROOT_FOLDER = "/root"
    DSA_IAX_BKC_FOLDER = "pv-dsa-iax-bkc-tests"
    PROXY_COMMANDS = [
        "git config --global http.https://github.com.proxy http://proxy-dmz.intel.com:912",
        "git config --global http.https://lfs.github.com.proxy http://proxy-dmz.intel.com:912",
        "git config --global http.https://github-cloud.s3.amazonaws.com.proxy http://proxy-dmz.intel.com:912",
        "git config --global http.https://github-cloud.githubusercontent.com.proxy http://proxy-dmz.intel.com:912"
        ]
    GIT_CONFIG_FILE_NAME = "config_git.cfg"
    REGEX_VERIFY_DISABLE = r"disabled.* device.*"
    REGEX_VERIFY_ENABLE = r"enabled.*device.*"
    REGEX_VERIFY_WQ_DISABLE = r"disabled.* wq.*"
    REGEX_VERIFY_WQ_ENABLE = r"enabled.*wq.*"
    REGEX_TOT_THREADS = r"Total Threads[^A-Za-z0-9]*(\S+)"
    REGEX_THREADS_PASSED = r"Threads Passed[^A-Za-z0-9]*(\S+)"
    REGEX_TEST_PASSED = r"\d+\d+.+?(?=tests passed)"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file_path=None):
        """
        Create an instance of sut DsaBaseTest.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(DsaBaseTest, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._platform = self._common_content_lib.get_platform_family()
        if self._platform != ProductFamilies.SPR:
            raise content_exceptions.TestFail("Unsupported platform: {}".format(self._platform))

    def prepare(self):
        # type: () -> None
        """
        Prepare the test setup.
        """
        super(DsaBaseTest, self).prepare()

    def check_idxd_device(self):
        """
        This function verify the idxd driver

        :raise: If not found idxd driver raise content_exceptions.TestFail
        """
        no_dsa_modules = []
        self._log.info("Idxd driver state in the sut")
        cmd_output = self._common_content_lib.execute_sut_cmd(self.LSMOD_GREP_CMD, self.LSMOD_GREP_CMD,
                                                              self._command_timeout)
        self._log.debug("lsmod command output results for idxd driver {}".format(cmd_output))
        for module in self.IDXD_LIST_DRIVER:
            if module not in cmd_output:
                no_dsa_modules.append(module)
        if no_dsa_modules:
            raise content_exceptions.TestFail("%s idxd driver did not find", no_dsa_modules)

    def determine_device_state(self, iax=False):
        """
        This function determine dsa device state

        :raise: If getting error raise content_exceptions.TestFail
        """
        if iax:
            cmd = self.LSPCI_IAX_CMD
            regex_cmd = self.REGEX_0CFE_CMD
        else:
            cmd = self.LSPCI_CMD
            regex_cmd = self.REGEX_OB25_CMD
        self._log.info("Determine device state")
        cmd_output = self._common_content_lib.execute_sut_cmd(cmd, "device information",
                                                              self._command_timeout)
        self._log.debug("lspci command output results for given device {}".format(cmd_output))
        device_count = len(re.findall(regex_cmd, cmd_output))
        if device_count != self.DSA_DEVICE_COUNT:
            raise content_exceptions.TestFail("Failed to get the device information")

    def driver_basic_check(self):
        """
        This function check dsa driver basic check

        :raise: If getting error raise content_exceptions.TestFail
        """
        self._log.info("idxd drier basic check")
        cmd_output = self._common_content_lib.execute_sut_cmd(self.DMESG_IDXD_CMD, "dmesg command for idxd drive",
                                                              self._command_timeout)
        self._log.debug("dmesg command output results for idxd driver {}".format(cmd_output))
        if self.ERROR_STR in cmd_output.lower():
            raise content_exceptions.TestFail("idxd errors found in dmesg")

    def verify_dsa_driver_directory(self):
        """
        This function verify the dsa device count form dsa0 to dsa7

        :raise: If dsa device is not available raise content_exceptions.TestFail
        """
        dir_not_present = []
        command_result = self._common_content_lib.execute_sut_cmd(self.LIST_FILES_CMD, "list dsa dir folder/files",
                                                                  self._command_timeout, cmd_path=self.DSA_DRIVER_DIR)
        self._log.debug("DSA Driver directories are '{}' ".format(command_result))
        for item in self.LIST_OF_DSA_DIR:
            if item not in command_result.split():
                dir_not_present.append(item)
        if dir_not_present:
            raise content_exceptions.TestFail("These dsa folders are not present {}".format(dir_not_present))
        dsa_device_dir_path = self.DSA_DRIVER_DIR + "/devices"
        command_result = self._common_content_lib.execute_sut_cmd(self.LIST_FILES_CMD, "list dsa device  files",
                                                                  self._command_timeout, cmd_path=dsa_device_dir_path)
        self._log.debug("DSA Device directory files '{}' ".format(command_result))
        dsa_files_count = len(re.findall(self.REGEX_DSA_CMD, command_result))
        if dsa_files_count != self.DSA_DEVICE_COUNT:
            raise content_exceptions.TestFail("These dsa files are not present")
        self._log.info("DSA devices are present from dsa0 to dsa7")

    def enable_intel_iommu_by_kernel(self):
        """
        This method is to enable intel_iommu by using grub menu

        :return: True on Success else False
        """
        if self.is_intel_iommu_enabled():
            self._log.info("Intel IOMMU is already enabled by kernel")
            return True
        else:
            self._log.info("Enabling Intel IOMMU")
            self._log.info("Updating the grub config file")
            self._common_content_lib.update_kernel_args_and_reboot([self.INTEL_IOMMU_ON_STR])
            self._log.info("Successfully enabled intel_iommu by kernel")
            return self.is_intel_iommu_enabled()

    def is_intel_iommu_enabled(self):
        """
        This method is to verify if intel IOMMU is enabled by Kernel or not

        :return : True on Success else False
        """
        self._log.info("Checking if intel_iommu is enabled by kernel or not")
        host_validate_result = self.os.execute(self.HOST_VALIDATE_CMD, self._command_timeout)
        self._log.debug("stdout of command {} :\n{}".format(self.HOST_VALIDATE_CMD,
                                                            host_validate_result.stdout))
        self._log.debug("stderr of command {} :\n{}".format(self.HOST_VALIDATE_CMD,
                                                            host_validate_result.stderr))
        # although return code is not 0 still the data feed will be on stdout only
        host_validate_result_data = host_validate_result.stdout
        check_intel_iommu = re.search(self.CHECK_INTEL_IOMMU_REGEX, host_validate_result_data)
        if check_intel_iommu:
            self._log.info("Intel IOMMU is enabled by kernel")
            return True
        else:
            self._log.error("Intel IOMMU is not enabled by kernel")
            return False

    def update_git_proxy(self):
        """
        This method is to update the proxy commands

        :return : True on Success else raise exception
        """
        self._log.info("updating git proxy commands")
        for proxy in self.PROXY_COMMANDS:
            cmd_output = self._common_content_lib.execute_sut_cmd(proxy, "updating proxy {}".format(proxy),
                                                                  self._command_timeout)
            if self.ERROR_STR in cmd_output.lower():
                raise content_exceptions.TestFail("updating proxy failed. Please verify proxy or git")
            self._log.debug("proxy {} updated successfully".format(proxy))
        return True

    def clone_git_repo(self):
        """
        This method is to clone the repo from github

        :return : True on Success else raise exception
        """
        try:
            dsa_path = self.ROOT_FOLDER + "/" + self.DSA_IAX_BKC_FOLDER
            repo_name = self._common_content_configuration.get_git_repo_name()
            token = self._common_content_configuration.get_access_token()
            if "https" in repo_name and token != 'None':
                oauth_token_str = "https://{}:x-oauth-basic@".format(token)
                oauth_git_repo_name = repo_name.replace("https://", oauth_token_str)
                clone_repo_str = "git clone {}".format(oauth_git_repo_name)
                dsa_folder_name_find = self._common_content_lib.execute_sut_cmd_no_exception("find / -type d -samefile "
                                                                                             "{}".format(dsa_path),
                                                                                             "find the sut folder path",
                                                                                             self._command_timeout,
                                                                                             cmd_path=self.ROOT_FOLDER,
                                                                                          ignore_result="ignore")
                dsa_folder_name_find = dsa_folder_name_find.strip()
                if dsa_folder_name_find == dsa_path:
                    repo_str = dsa_folder_name_find

                    self._common_content_lib.execute_sut_cmd("rm -rf {}".format(repo_str),
                                                             "removing existing repo {}".format(repo_str),
                                                             self._command_timeout, self.ROOT_FOLDER)

                cmd_output = self._common_content_lib.execute_sut_cmd(clone_repo_str,
                                                                      "cloning repo {}".format(clone_repo_str),
                                                                      self._command_timeout)
                if self.ERROR_STR in cmd_output.lower():
                    raise content_exceptions.TestFail("cloning repo failed. Please check authentication")
            else:
                raise content_exceptions.TestFail("Implementation supports only https and please check the access "
                                                  "token")

        except Exception as ex:
            raise content_exceptions.TestFail("Failed due to {}".format(ex))
        return True

    def execute_shell_script(self, script_name, path):
        """
        This method is to execute the shell script

        :param script_name: shell script file name
        :param path: path for shll script file
        :return : sut_cmd_result
        """
        try:
            sut_cmd_result = self._common_content_lib.execute_sut_cmd_no_exception(script_name, "executing script "
                                                                                                "{}".format(script_name),
                                                                                   self._command_timeout,
                                                                                   cmd_path=path,
                                                                                   ignore_result="ignore")

        except Exception as ex:
            raise content_exceptions.TestFail("Failed to run sut command {} with exception {}".format(script_name, ex))
        return sut_cmd_result

    def verify_iax_driver_directory(self):
        """
        This function verify the iax device count present in the system.

        :raise: If iax device is not available raise content_exceptions.TestFail
        """
        dir_not_present = []
        command_result = self._common_content_lib.execute_sut_cmd(self.LIST_FILES_CMD, "list iax dir folder/files",
                                                                  self._command_timeout, cmd_path=self.DSA_DRIVER_DIR)
        self._log.debug("IAX Driver directories are '{}' ".format(command_result))
        for item in self.LIST_OF_DSA_DIR:
            if item not in command_result.split():
                dir_not_present.append(item)
        if dir_not_present:
            raise content_exceptions.TestFail("These iax folders are not present {}".format(dir_not_present))
        dsa_device_dir_path = self.DSA_DRIVER_DIR + "/devices"
        command_result = self._common_content_lib.execute_sut_cmd(self.LIST_FILES_CMD, "list iax device  files",
                                                                  self._command_timeout, cmd_path=dsa_device_dir_path)
        self._log.debug("IAX Device directory files '{}' ".format(command_result))
        iax_files = re.findall(self.REGEX_IAX_CMD, command_result)
        if len(iax_files) != self.DSA_DEVICE_COUNT:
            raise content_exceptions.TestFail("These iax files are not present")
        self._log.info("IAX devices that are present in the system : {}".format(iax_files))
