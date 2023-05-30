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


class DsaBaseTest_virtualization(ContentBaseTestCase):
    """
    Base class extension for DsaBaseTest_virtualization which holds common functions.
    """
    LIST_OF_DSA_DIR = ['devices', 'drivers', 'drivers_autoprobe', 'drivers_probe', 'uevent']
    INSTALL_DEPENDENCY_PACKAGE = ["libuuid-devel", "json-c-devel", "kmod-devel", "libudev-devel", "xmlto*","systemd-devel"]
    LIST_FILES_CMD = "ls"
    DSA_DRIVER_DIR = "/sys/bus/dsa"
    HOST_VALIDATE_CMD = "virt-host-validate"
    INTEL_IOMMU_ON_STR = "intel_iommu=on,sm_on"
    CHECK_INTEL_IOMMU_REGEX = "Checking if IOMMU is enabled by kernel.*PASS"
    LSMOD_GREP_CMD = "lsmod | grep idxd"
    IDXD_LIST_DRIVER = ['idxd', 'idxd_mdev']
    LSPCI_CMD = "lspci | grep 0b25"
    REGEX_OB25_CMD = "System peripheral: Intel Corporation Device 0b25"
    REGEX_0CFE_CMD = "System peripheral: Intel Corporation Device 0cfe"
    LSPCI_IAX_CMD = "lspci | grep 0cfe"
    DSA_DEVICE_COUNT = 8
    REGEX_DSA_CMD = r"dsa\d+"
    REGEX_IAX_CMD = r"iax\d+"
    DMESG_IDXD_CMD = "dmesg | grep idxd"
    ERROR_STR = "error"
    DSA_DEVICE_WQ_LIST = ["dsa0", "wq0.0", "wq0.1"]
    DSA_DEVICE_WQ_STATUS_LIST = ["enabled", "enabled", "enabled"]
    DSA_DEVICE_DICT = {}
    ROOT_FOLDER = "/root"
    INTEL_IOMMU_ON_WITH_PARAMETERS = "intel_iommu=on,sm_on iommu=on no5lvl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file_path=None):
        """
        Create an instance of sut DsaBaseTest.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(DsaBaseTest_virtualization, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._platform = self._common_content_lib.get_platform_family()
        if self._platform != ProductFamilies.SPR:
            raise content_exceptions.TestFail("Unsupported platform: {}".format(self._platform))

    def prepare(self):
        # type: () -> None
        """
        Prepare the test setup.
        """
        super(DsaBaseTest_virtualization, self).prepare()

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
