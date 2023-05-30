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
"""DEPRECATION WARNING - Not included in agent scripts/libraries, which will become the standard test scripts."""
import warnings
warnings.warn("This module is not included in agent scripts/libraries.", DeprecationWarning, stacklevel=2)
import os
import re

import six
from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.lib.install_collateral import InstallCollateral

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

class DsaDriverUtility(object):
    """
    DSA driver utility class to build and and to do basic testing.
    """

    FIND_CMD = "find $(pwd) -type f -name {} | sort -r"
    DSA_PARENT_PATH = "/root/dtaf_sdsi_driver_source_code"
    INSTALLER_NAME = "idxd-config-accel-config*.zip"
    DSA_UNZIP_LOCATION = "/root/dtaf_sdsi_driver_source_code/dsa"
    REMOVE_OLD_DSA_SRC = "rm -rf /root/dtaf_sdsi_driver_source_code/dsa"

    LIST_OF_DSA_DIR = ['devices', 'drivers', 'drivers_autoprobe', 'drivers_probe', 'uevent']
    INSTALL_DEPENDENCY_PACKAGE = ["autoconf",
                                  "automake",
                                  "libtool",
                                  "pkgconf",
                                  "rpm-build",
                                  "rpmdevtools",
                                  "asciidoc",
                                  "xmlto",
                                  "libuuid-devel",
                                  "json-c-devel",
                                  "kmod-devel",
                                  "libudev-devel"
                                  ]

    LIST_FILES_CMD = "ls"
    DSA_DRIVER_DIR = "/sys/bus/dsa"        
    LSMOD_GREP_CMD = "lsmod | grep idxd"
    IDXD_LIST_DRIVER = ['idxd']# ['idxd_mdev']
    LSPCI_CMD = "lspci | grep 0b25"
    REGEX_OB25_CMD = "System peripheral: Intel Corporation Device 0b25"    
    REGEX_DSA_CMD = r"dsa\d+"
    DMESG_IDXD_CMD = "dmesg | grep idxd"
    ERROR_STR = "error"
    

    def __init__(self, log, sut_os, common_content_lib, common_content_config_lib,cfg_opts):
        """
        Create an instance of DsaDriverUtility.

        :param cfg_opts: Configuration Object of provider
        :param log: Log object
        :param os: sut_os object.
        :param common_content_config_lib: config lib
        :param common_content_lib: common content lib

        """
        self._log = log
        self._os = sut_os
        self._common_content_lib = common_content_lib
        self._common_content_config_lib = common_content_config_lib
        self._command_timeout = self._common_content_config_lib.get_command_timeout()
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)
        self._platform = self._common_content_lib.get_platform_family()
        if self._platform != ProductFamilies.SPR:
            raise RuntimeError("Unsupported platform: {}".format(self._platform))

        ''' 
        "_install_collateral.install_verify_accel_config()" automatically download the source code from
        artifactory and build it. So this is not required at present.
        '''
        #self.installer_dest_path = self.unzip_dsa_driver_source_package()


    def unzip_dsa_driver_source_package(self) -> str :
        """
        This method searches for the compressed DSA package in "/root/dtaf_sdsi_driver_source_code", and extract it.

        :raise: RuntimeError if unable to un-tar properly.

        :return: The extracted folder path in SUT
        """
        self._log.info("[IMPORTANT PRE-REQUEST] - Please make sure dsa utiltity source code *.zip are located in {}".format(self.DSA_PARENT_PATH))
        self._log.info("Searching for DSA utitltiy source code file in zip format")
        cmd = self.FIND_CMD.format(self.INSTALLER_NAME)
        self._log.debug("command to search driver zip file cmd {}".format(cmd))
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._command_timeout, self.DSA_PARENT_PATH)
        if not output.strip():
            log_error = "No DSA utility package(compressed) is found in the SUT path {}".format(self.DSA_PARENT_PATH)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.debug("find cmd output {}".format(output))
        zip_path = os.path.split(output.strip())[-1]
        source_path = os.path.split(output.strip())[0]
        directory_name = os.path.dirname(output.strip())
        self._log.debug("directory name {}, zip path {} , source path {} ".format(directory_name, zip_path, source_path))
        return self.extract_compressed_file(source_path, zip_path, directory_name)


    def extract_compressed_file(self, sut_folder_path, zip_file, folder_name) -> str:
        """
        This function Extract the compressed file.

        :param sut_folder_path : sut folder path
        :param folder_name : name of the folder in SUT
        :param zip_file : name of the zip file.
        :return: The extracted folder path in SUT.
        """
        self._log.info("Removing old dsa driver source code folder and files")
        output = self._common_content_lib.execute_sut_cmd(self.REMOVE_OLD_DSA_SRC, "remove old folder",
                                                 self._command_timeout, sut_folder_path)
        self._log.debug(output)

        self._log.info("extracts the compressed file")
        unzip_command = "unzip  {} -d {}".format(zip_file, self.DSA_UNZIP_LOCATION)

        self._common_content_lib.execute_sut_cmd(unzip_command, "unzip the folder", self._command_timeout, sut_folder_path)

        tool_path_sut = Path(os.path.join("/root", folder_name)).as_posix()

        self._log.debug("The file '{}' has been unzipped successfully ..".format(zip_file))
        self._log.debug("Set execution permission for the contents in extracted package.")
        self._os.execute("chmod -R 777 %s" % tool_path_sut, self._command_timeout)
        self._log.debug(tool_path_sut)
        return tool_path_sut

    def _update_grub_cmd_line_linux(self, isCENTOS, stringtoadd=None):
        """
        This method is using to update the /etc/degault/grub --> "GRUB_CMDLINE_LINUX" with a string

        """
        REBOOT_REQUIRED = 1
        REBOOT_NOT_REQUIRED = 0
        if (stringtoadd == None or isCENTOS == False):
            return True, REBOOT_NOT_REQUIRED
        cmd_to_check_env_string = "grub2-editenv - list | grep kernelopts"
        command_result = self._common_content_lib.execute_sut_cmd(cmd_to_check_env_string, cmd_to_check_env_string,
                                                                  self._command_timeout)
        self._log.debug("{}   output is '{}'".format(cmd_to_check_env_string, command_result))
        if(stringtoadd in command_result):
            self._log.info("The string ' {} ' already in the system")
            return True, REBOOT_NOT_REQUIRED

        #Updating grub environment
        update_command = 'grub2-editenv - set "$(grub2-editenv - list | grep kernelopts) {}"'.format(stringtoadd)
        command_result = self._common_content_lib.execute_sut_cmd(update_command, update_command,
                                                                  self._command_timeout)
        self._log.debug("{}   output is '{}'".format(update_command, command_result))
        return True, REBOOT_REQUIRED


    def install_dependency_packages(self) -> None:
        """ This method is using to install the dependency packages to build the DSA Utility Package

        SUT may/may not be really configured to work "yum install".
        """

        #set date time to SUT
        self._common_content_lib.set_datetime_on_linux_sut()

        # Installing Development tools
        cmd_to_install_dev_tools = 'echo y | yum group install "Development Tools"'
        try:
            command_result = self._common_content_lib.execute_sut_cmd(cmd_to_install_dev_tools, "Install development tools",
                                                                      self._command_timeout)
            self._log.debug("Installation of 'Development Tools' is done successfully with output '{}'".format(command_result))
        except:
            self._log.info("Failed to install the package ' {} '".format(cmd_to_install_dev_tools))

        for package in self.INSTALL_DEPENDENCY_PACKAGE:
            try:
                self._install_collateral.yum_install(package)
            except:
                self._log.info("Failed to install the package {}".format(package))


    def build_and_run_accel_config_test(self) -> bool:
        """
        This method is using to build and run the basic DSA acceleration utility.
        """

        # set date time to SUT
        self._common_content_lib.set_datetime_on_linux_sut()
        # Install accel config tool
        try:
            self._install_collateral.install_verify_accel_config()
        except Exception as exception:
            self._log.error("Exception while running the accel - config testing: {} ".format(str(exception)))
            self._log.error(exception, exc_info=True)
            return False

        return  True


    def check_idxd_device(self):
        """
        This function verify the idxd driver

        :raise: If not found idxd driver raise RuntimeError
        """
        no_dsa_modules = []
        self._log.info("Idxd driver state in the sut")
        cmd_output = self._common_content_lib.execute_sut_cmd(self.LSMOD_GREP_CMD, self.LSMOD_GREP_CMD, self._command_timeout)
        self._log.debug("lsmod command output results for idxd driver {}".format(cmd_output))
        for module in self.IDXD_LIST_DRIVER:
            if module not in cmd_output:
                no_dsa_modules.append(module)
        if no_dsa_modules:
            raise RuntimeError("%s idxd driver did not find", no_dsa_modules)


    def determine_device_state(self, expected_dsa_device_count: int) -> None:
        """
        This function determine dsa device state

        :raise: If getting error raise RuntimeError
        """
        self._log.info("Determine device state for 0b25")
        cmd_output = self._common_content_lib.execute_sut_cmd(self.LSPCI_CMD, "0b25 device information",
                                                              self._command_timeout)
        self._log.debug("lspci command output results for 0b25 device {}".format(cmd_output))
        device_count = len(re.findall(self.REGEX_OB25_CMD, cmd_output))
        if device_count != expected_dsa_device_count:
            raise RuntimeError("Failed to get all 0b25 device information")



    def driver_basic_check(self) -> None:
        """
        This function checks dsa driver basic check

        :raise: If getting error raise RuntimeError
        """
        self._log.info("idxd drier basic check")
        cmd_output = self._common_content_lib.execute_sut_cmd(self.DMESG_IDXD_CMD, "dmesg command for idxd drive",
                                                              self._command_timeout)
        self._log.debug("dmesg command output results for idxd driver {}".format(cmd_output))
        if self.ERROR_STR in cmd_output.lower():
            raise RuntimeError("idxd errors found in dmesg")


    def verify_dsa_driver_directory(self, expected_dsa_device_count: int) -> None:
        """
        This function verify the dsa device count form dsa0 to dsa7

        :raise: If dsa device is not available raise RuntimeError
        """
        dir_not_present = []
        command_result = self._common_content_lib.execute_sut_cmd(self.LIST_FILES_CMD, "list dsa dir folder/files",
                                                                  self._command_timeout, cmd_path=self.DSA_DRIVER_DIR)

        self._log.debug("DSA Driver directories are '{}' ".format(command_result))
        for item in self.LIST_OF_DSA_DIR:
            if item not in command_result.split():
                dir_not_present.append(item)

        if dir_not_present:
            raise RuntimeError("These dsa folders are not present {}".format(dir_not_present))

        dsa_device_dir_path = self.DSA_DRIVER_DIR + "/devices"
        command_result = self._common_content_lib.execute_sut_cmd(self.LIST_FILES_CMD, "list dsa device  files",
                                                                  self._command_timeout, cmd_path=dsa_device_dir_path)
        self._log.debug("DSA Device directory files '{}' ".format(command_result))
        dsa_files_count = len(re.findall(self.REGEX_DSA_CMD, command_result))

        if dsa_files_count != expected_dsa_device_count:
            raise RuntimeError("These dsa files are not present")
        self._log.info("DSA devices are present from dsa0 to dsa{}".format(expected_dsa_device_count))