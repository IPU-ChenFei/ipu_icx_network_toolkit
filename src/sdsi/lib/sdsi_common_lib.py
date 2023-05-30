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
"""DEPRECATION WARNING - Not included in agent scripts/libraries, which will become the standard test scripts."""
import warnings
warnings.warn("This module is not included in agent scripts/libraries.", DeprecationWarning, stacklevel=2)
import os
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#################################################################################
import platform
import socket

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.config_util import ConfigUtil
from src.sdsi.lib.in_band_sdsi_common_lib import SDSICommonLib as InbandSDSICommonLib


class SDSICommonLib(InbandSDSICommonLib):
    """
    Base class extension for SDSICommonLib which holds common functionality for SDSi read write operations.
    Note: This class is under development. Changes are made on the go based on the requirement changes.
    """
    READ_HW_STATUS_CMD_OOB = 'https_proxy='' HTTPS_PROXY='' ./spr_sdsi_installer --read --socket {} --oob "url=https://{},username={},password={},insecure=true,peci-mode={}" | ./spr_output_parser'
    WRITE_CERTIFICATE_CMD_OOB = 'https_proxy='' HTTPS_PROXY='' ./spr_sdsi_installer --write -c --socket {} --oob url="https://{},username={},password={},insecure=true,peci-mode={}" -f {}'
    WRITE_LICENSE_CMD_OOB = 'https_proxy='' HTTPS_PROXY='' ./spr_sdsi_installer --write --socket {} -p --oob url="https://{},username={},password={},insecure=true,peci-mode={}" -f {}'
    PECI_MODE_MCTP = "mctp"
    PECI_MODE_WIRE = "wire"

    def __init__(self, log, sut_os, common_content_lib, common_content_config_lib, sdsi_installer, rasp_pi=None,
                 cfg_opts=None):
        """
        Create an instance of sut SDSICommonLib.
        """
        self._log = log
        self._os = sut_os
        self.cmd_timeout = common_content_config_lib.get_command_timeout()
        self.sdsi_installer_path = sdsi_installer.installer_dest_path

        # Get BMC info for OOB library
        self.bmc_ip = None
        self.bmc_user_name = None
        self.bmc_password = None
        self.populate_bmc_details()

        # We stopped using stepping to differentiate between peci_mode. This functionality may be obsolete.
        self.cpu_stepping = self._get_cpu_stepping()
        self._log.info("CPU Stepping: {}".format(str(self.cpu_stepping)))

        # OOB library defaults to peci_mode=mctp
        self.set_peci_mode_mctp()

        super(SDSICommonLib, self).__init__(log, sut_os, common_content_lib, common_content_config_lib, sdsi_installer,
                                            rasp_pi, cfg_opts)

    def populate_bmc_details(self):
        """
        This method will populate the bmc configuration.
        The information will be fetched from the MIV(BMC) configuration file located in 'C:\<host_name>.cfg'
        return:
        """
        host_name = socket.gethostname()
        config_file_name = host_name + ".cfg"
        exec_os = platform.system()
        bmc_config_file_path = os.path.join(Framework.CFG_BASE[exec_os], config_file_name)
        if not os.path.exists(bmc_config_file_path):
            log_error = "The MIV(BMC) config file '{}' does not exists," \
                        " populate this file and run this test again..".format(bmc_config_file_path)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        try:
            cp = ConfigUtil(bmc_config_file_path)
            self.bmc_ip = cp.get_key_value("Section0", "ipaddress")
            self.bmc_user_name = cp.get_key_value("Section0", "username")
            self.bmc_password = cp.get_key_value("Section0", "password")
            self._log.info("Found BMC IP: " + self.bmc_ip)
        except Exception as ex:
            log_error = "The MIV(BMC) config file '{}' configuration not correct. Please populate correctly and run " \
                        "the test again.".format(bmc_config_file_path)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def set_peci_mode_mctp(self):
        """
        This method changes the libary to use peci_mode=mctp during SDSi command operations
        """
        self._populate_oob_commands(self.PECI_MODE_MCTP)

    def set_peci_mode_wire(self):
        """
        This method changes the libary to use peci_mode=wire during SDSi command operations
        """
        self._populate_oob_commands(self.PECI_MODE_WIRE)

    def _populate_oob_commands(self, peci_mode):
        """
        This method populates the SDSi read and write commands with the specified peci_mode
        """
        self._log.info("Using peci_mode={}".format(peci_mode))
        # Fill OOB Commands to match with IB parameters
        self.WRITE_CERTIFICATE_CMD = self.WRITE_CERTIFICATE_CMD_OOB.format("{}", self.bmc_ip, self.bmc_user_name,
                                                                       self.bmc_password, peci_mode, "{}")
        self.READ_HW_STATUS_CMD = self.READ_HW_STATUS_CMD_OOB.format("{}", self.bmc_ip, self.bmc_user_name,
                                                                 self.bmc_password, peci_mode)
        self.WRITE_LICENSE_CMD = self.WRITE_LICENSE_CMD_OOB.format("{}", self.bmc_ip, self.bmc_user_name,
                                                               self.bmc_password, peci_mode, "{}")