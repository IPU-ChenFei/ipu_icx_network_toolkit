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

import src.sdsi.lib.sdsi_exceptions as SDSiExceptions

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path


class SDSIInstallerLib():
    """SPR SDSI Installer Installation provider object"""
    FIND_CMD = "find $(pwd) -type f -name {} | sort -r"
    LIST_ITEMS_CMD = "ls -t"
    CHMOD_CMD = "chmod +x {}"
    SDSI_HELP_CMD = "./spr_sdsi_installer --help"
    FIND_LICENSE_CMD = "find -maxdepth 1 -name '{}*.bin'"
    COPY_CMD = "yes | cp {} {}"
    SDSI_ROOT_PATH = "/root/SDSi_Installer"
    INSTALLER_NAME = "spr_sdsi_installer*.gz"
    LICENSE_KEY_NAME = "LicenseSPRTestPublic_signed"
    ERASE_LICENSE_KEY = "EraseCertDebugBit0Request_signed"

    def __init__(self, log, sut_os, common_content_lib, common_content_config_lib, rasp_pi=None):
        """
        Create an instance of sut SDSIInstallerLib.

        """
        self._log = log
        self._os = sut_os
        self._common_content_lib = common_content_lib
        self._common_content_config_lib = common_content_config_lib
        self._ac_power = rasp_pi
        self.cmd_timeout = self._common_content_config_lib.get_command_timeout()
        self.untar_sdsi_package()
        self.installer_dest_path = self.get_sdsi_installer_and_output_parser()

    def untar_sdsi_package(self):
        """
        This method searches for the compressed SDSi package in "/root/SDSi_Installer", and extracts it.
        :raise: content_exception.TestFail if unable to un-tar properly.
        """
        self._log.info("Searching for SDSi installer tar file")
        find_cmd = self.FIND_CMD.format(self.INSTALLER_NAME)
        output = self._common_content_lib.execute_sut_cmd(find_cmd, find_cmd, self.cmd_timeout, self.SDSI_ROOT_PATH)
        if not output.strip():
            log_error = "No SDSi Intaller package(compressed) is found in the SUT path {}".format(self.SDSI_ROOT_PATH)
            self._log.error(log_error)
            raise SDSiExceptions.InstallerError(log_error)

        zip_path = os.path.split(output.strip())[-1]
        source_path = os.path.split(output.strip())[0]
        directory_name = os.path.dirname(output.strip())
        self.extract_compressed_file(source_path, zip_path, directory_name)

    def extract_compressed_file(self, sut_folder_path, zip_file, folder_name):
        """
        This function Extract the compressed file.
        :param : sut_folder_path : sut folder path
        :param : folder_name : name of the folder in SUT
        :param : zip_file : name of the zip file.
        :return: The extracted folder path in SUT.
        """
        self._log.info("Extracting the compressed installer file")
        unzip_command = "tar -xvf {}".format(zip_file)
        self._common_content_lib.execute_sut_cmd(unzip_command, unzip_command, self.cmd_timeout, sut_folder_path)
        tool_path_sut = Path(os.path.join("/root", folder_name)).as_posix()
        self._os.execute("chmod -R 777 %s" % tool_path_sut, self.cmd_timeout)
        self._log.info("The file '{}' has been unzipped successfully.".format(zip_file))
        return tool_path_sut

    def get_sdsi_installer_and_output_parser(self):
        """
        This method will look for the SPR_SDSi_Installer and spr_output_parser in the
        latest available installer package located in /root/SDSi_Installer/ path.
        :return: The installer path of SDSi installer package
        """
        find_cmd = self.FIND_CMD.format("spr_sdsi_installer")
        installer = self._common_content_lib.execute_sut_cmd(find_cmd, find_cmd, self.cmd_timeout, self.SDSI_ROOT_PATH)
        if not installer.strip():
            log_error = "SPR_Installer is not found in the package. Please verify the latest package contents."
            self._log.error(log_error)
            raise SDSiExceptions.InstallerError(log_error)

        find_cmd = self.FIND_CMD.format("spr_output_parser")
        parser = self._common_content_lib.execute_sut_cmd(find_cmd, find_cmd, self.cmd_timeout, self.SDSI_ROOT_PATH)
        if not parser.strip():
            log_error = "SPR Output parser is not found in the package. Please verify the latest package contents."
            self._log.error(log_error)
            raise SDSiExceptions.InstallerError(log_error)

        installer_path = os.path.split(installer.strip())[0]
        parser_path = os.path.split(parser.strip())[0]
        self._log.info("spr_sdsi_installer is available in '{}'".format(installer_path))
        self._log.info("spr_output_parser is available in '{}'".format(parser_path))
        return installer_path

    def verify_sdsi_installer(self):
        """
        This method is used to verify the SPR SDSi Installer package by executing the help command.
        :return: None
        """
        self._log.info("Verifying the installer package by running help command and verifying the output.")
        verify_output = self._os.execute(self.SDSI_HELP_CMD, self.cmd_timeout, self.installer_dest_path)
        if verify_output.cmd_failed():
            log_error = "Failed to verify SPR_SDSi_Installer, std_error: {}".format(verify_output.stderr)
            self._log.error(log_error)
            raise SDSiExceptions.InstallerError(log_error)
        sdsi_installer_version = re.search(r'(?=SDSi Installer Tool)[^\n]*', verify_output.stderr.strip()).group()
        self._log.info("SPR SDSi Installer is verified successfully with version {}.".format(sdsi_installer_version))

    def populate_available_payloads_for_cpu(self, cpu_hw_id):
        """
        This method is to get the list of available license blobs for the processor ppin in the installer directory.

        param:  cpu_hardware_id: to find and load the applicable payloads.
        return: The available list of license payloads for the CPU PPIN located in the CPU
        """
        available_payloads = {}
        sorted_cap_payloads = {}
        sorted_rtb_payloads = {}
        find_payload_cmd = self.FIND_LICENSE_CMD.format(cpu_hw_id)
        license_result = self._os.execute(find_payload_cmd, self.cmd_timeout, self.SDSI_ROOT_PATH)

        if license_result.cmd_failed() or not license_result.stdout:
            log_error = "No license CAPs found for CPU PPIN {} in SUT path {}".format(cpu_hw_id, self.SDSI_ROOT_PATH)
            self._log.error(log_error)
            raise SDSiExceptions.MissingCapError(log_error)

        if not self._os.execute("ls *_corrupted.bin", self.cmd_timeout, self.installer_dest_path).cmd_failed():
            self._log.info("Removing existing corrupted CAP keys.")
            self._os.execute("rm -f *_corrupted.bin", self.cmd_timeout, self.installer_dest_path)

        for license_blob in license_result.stdout.strip().splitlines():
            available_payloads[re.search(r'key_id_\d_(.*?).bin', license_blob).group(1)] = license_blob
            copy_cmd = self.COPY_CMD.format(license_blob, self.installer_dest_path)
            self._common_content_lib.execute_sut_cmd(copy_cmd, copy_cmd, self.cmd_timeout, self.SDSI_ROOT_PATH)

        sorted_keys = sorted(available_payloads.keys(), key=lambda x: int(re.search(r'rev_(.*?)_', x).group(1), 16))
        for rtb_key in [key for key in sorted_keys if "BASE" in key]:
            sorted_rtb_payloads[rtb_key] = available_payloads[rtb_key]
        for cap_key in [key for key in sorted_keys if "BASE" not in key]:
            sorted_cap_payloads[cap_key] = available_payloads[cap_key]
        return sorted_cap_payloads, sorted_rtb_payloads

    def get_license_certificate(self):
        """
        This method is used to get the license key certificate from the installer directory.
        return: The license_key_certificate for the CPU located in the SDSi parent directory /root/SDSi_Installer
        """
        find_license_cmd = self.FIND_LICENSE_CMD.format(self.LICENSE_KEY_NAME)
        certificate_result = self._os.execute(find_license_cmd, self.cmd_timeout, self.SDSI_ROOT_PATH)

        if certificate_result.cmd_failed():
            log_error = "No valid license key certificate is found in SUT path {}.".format(self.SDSI_ROOT_PATH)
            self._log.error(log_error)
            raise SDSiExceptions.MissingLicenseKeyError(log_error)

        key_certificate = certificate_result.stdout.strip()
        copy_cmd = self.COPY_CMD.format(key_certificate, self.installer_dest_path)
        self._common_content_lib.execute_sut_cmd(copy_cmd, copy_cmd, self.cmd_timeout, self.SDSI_ROOT_PATH)
        self._log.info("License key certificate {} is found in {}.".format(key_certificate, self.SDSI_ROOT_PATH))
        return key_certificate

    def get_erase_license_certificate(self):
        """
        This method is used to get the erase license key certificate from the installer directory.
        return: The erase_license_key_certificate for the CPU located in the SDSi parent directory /root/SDSi_Installer
        """
        find_license_command = self.FIND_LICENSE_CMD.format(self.ERASE_LICENSE_KEY)
        certificate_result = self._os.execute(find_license_command, self.cmd_timeout, self.SDSI_ROOT_PATH)

        if certificate_result.cmd_failed():
            log_error = "No valid Erase license key certificate is found in SUT path {}.".format(self.SDSI_ROOT_PATH)
            self._log.error(log_error)
            raise SDSiExceptions.MissingEraseKeyError(log_error)

        erase_license = certificate_result.stdout.strip()
        copy_cmd = self.COPY_CMD.format(erase_license, self.installer_dest_path)
        self._common_content_lib.execute_sut_cmd(copy_cmd, copy_cmd, self.cmd_timeout, self.SDSI_ROOT_PATH)
        self._log.info("Erase license key certificate {} is found in {}.".format(erase_license, self.SDSI_ROOT_PATH))
        return erase_license

    def install_dependencies(self):
        """
        This method is used to install the prerequisites for installing the SPR SDSi Installer.
        :return: None
        """
        install_efivar = "echo y | yum install efivar"
        install_efivar_libs = "echo y | yum install efivar-libs"
        install_bash = "echo y | yum install bash-completion"

        self._log.info("Installing efivar...")
        self._common_content_lib.execute_sut_cmd(install_efivar, "Installing efivar.", self.cmd_timeout)
        self._log.info("Installing efivar-libs...")
        self._common_content_lib.execute_sut_cmd(install_efivar_libs, "Installing efivar-libs.", self.cmd_timeout)
        self._log.info("Installing bash-completion...")
        self._common_content_lib.execute_sut_cmd(install_bash, "Installing bash-completion.", self.cmd_timeout)
