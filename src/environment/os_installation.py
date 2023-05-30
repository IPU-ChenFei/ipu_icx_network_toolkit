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
import platform
import subprocess
import sys

import six
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from src.lib.content_configuration import ContentConfiguration
from src.environment.environment_constants import OsInstallConstants
from src.environment.os_prerequisites import OsPreRequisitesLib
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import InventoryConstants


class OsInstallation:
    """
    This class implementation has os installation methods for rhel.
    """
    OFFLINE = "offline"
    ONLINE = "online"
    BMC = "bmc"

    def __init__(self, log, cfg_opts):
        self._log = log
        self._cfg_opts = cfg_opts

        self._common_content_configuration = ContentConfiguration(self._log)
        sut_os_cfg = self._cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, self._log)  # type: SutOsProvider
        self.os_pkg_path = self._common_content_configuration.get_os_pkg_path(self._os.os_subtype.lower())
        self.sft_pkg_path = self._common_content_configuration.get_sft_pkg_path(self._os.os_subtype.lower())
        self.atf_iso_path = self._common_content_configuration.get_atf_iso_path(self._os.os_subtype.lower())
        self.cfg_file_name = self._common_content_configuration.get_cfg_file_name(self._os.os_subtype.lower())

    def get_environment_path(self, required_dir_name, mode="offline"):
        config_file_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
        config_file_src_path = None
        self._log.info("Path from framework till source: '{}'".format(config_file_path))
        for root, dirs, files in os.walk(str(config_file_path)):
            for name in dirs:
                if name.startswith("environment"):
                    config_file_src_path = os.path.join(root, name)
                    for root, dirs, files in os.walk(str(config_file_src_path)):
                        for name in dirs:
                            if name.startswith(required_dir_name):
                                config_file_src_path = os.path.join(root, name)
                                for root, dirs, files in os.walk(str(config_file_src_path)):
                                    for name in files:
                                        if mode in name:
                                            config_file_src_path = os.path.join(root, name)

        if not config_file_src_path.endswith(".py"):
            self._log.error("Unable to find the execution file under the path : {}, please check provided directory "
                            "name is accurate...".format(config_file_src_path))
            raise RuntimeError

        print("Path of the execution file: '{}'".format(config_file_src_path))
        return config_file_src_path

    @staticmethod
    def get_sut_inventory_file_path():
        """
        Function to get the sut_inventory file from Inventory directory.
        """
        if not os.path.exists(InventoryConstants.SUT_INVENTORY_FILE_NAME):
            raise content_exceptions.TestNAError("sut inventory config file does not exists...")

        return InventoryConstants.SUT_INVENTORY_FILE_NAME

    def rhel_os_installation(self, installation_mode="offline", os_extract=True, software_extract=True):
        """
        Function to install the OS

        :param installation_mode : mode of the installation ex: bmc/offline/online
        :param os_extract: to skip os package extraction step by making param to False
        :param software_extract: to skip software package extraction step by making param to False
        :return : True if success else false
        """
        ret_value = False
        cmd = None
        exec_file_path = self.get_environment_path(OsInstallConstants.DIR_NAME_RHEL_OS, installation_mode)
        if installation_mode == self.BMC:
            cmd = "python " + exec_file_path + " --ATF_ISO_PATH {}".format(self.atf_iso_path)
        elif installation_mode == self.OFFLINE:
            cmd = "python " + exec_file_path + " --LOCAL_OS_PACKAGE_LOCATION {} --LOCAL_SOFTWARE_PACKAGE_LOCATION " \
                                               "{} --RHEL_CFG_FILE_NAME {} --EXTRACT_OS_TO_USB {} --EXTRACT_SOFTWARE_TO_USB {}".format(
                self.os_pkg_path,
                self.sft_pkg_path, self.cfg_file_name, os_extract, software_extract)

        cmd_res = os.system(cmd)
        if cmd_res == 0:
            ret_value = True
        return ret_value

    def windows_os_installation(self, installation_mode="offline"):
        """
        Function to install the Windows OS

        :param installation_mode : mode of the installation ex: bmc/online/offline
        :return : True if success else false
        """
        ret_value = False
        cmd = None
        exec_file_path = self.get_environment_path(OsInstallConstants.DIR_NAME_WIN_OS, installation_mode)
        if installation_mode == self.BMC:
            cmd = "python " + exec_file_path + " --ATF_ISO_PATH {}".format(self.atf_iso_path)
        elif installation_mode == self.OFFLINE:
            cmd = "python " + exec_file_path + " --LOCAL_OS_PACKAGE_LOCATION {}".format(self.os_pkg_path)

        cmd_res = os.system(cmd)
        if cmd_res == 0:
            ret_value = True
        return ret_value

    def centos_os_installation(self, installation_mode="bmc", os_extract=True, software_extract=True):
        """
        Function to install centos OS

        :param installation_mode : mode of the installation ex: bmc/online
        :return : True if success else false
        """
        ret_value = False
        if installation_mode != "bmc":
            exec_file_path = self.get_environment_path(OsInstallConstants.DIR_NAME_CENTOS)

            cmd = "python " + exec_file_path + " --LOCAL_OS_PACKAGE_LOCATION {} --LOCAL_SOFTWARE_PACKAGE_LOCATION " \
                                               "{} --CENTOS_CFG_FILE_NAME {} --EXTRACT_OS_TO_USB {} --EXTRACT_SOFTWARE_TO_USB {}".format(
                self.os_pkg_path, self.sft_pkg_path, self.cfg_file_name, os_extract, software_extract)
        else:
            exec_file_path = self.get_environment_path(OsInstallConstants.DIR_NAME_CENTOS, installation_mode)
            cmd = "python " + exec_file_path + " --ATF_ISO_PATH {}".format(self.atf_iso_path)

        cmd_res = os.system(cmd)
        if cmd_res == 0:
            ret_value = True
        return ret_value
