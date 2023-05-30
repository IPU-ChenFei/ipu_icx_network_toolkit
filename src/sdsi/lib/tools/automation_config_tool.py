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
"""Provides an interface to interact with dtaf Automation config.

    Typical usage example:
        automation_config_tool = AutomationConfigTool(self._log)
        bmc_ip = automation_config_tool.get_config_value("Section0", "ipaddress")
        bmc_user = automation_config_tool.get_config_value("Section0", "username")
        bmc_pass = automation_config_tool.get_config_value("Section0", "password")
"""
import configparser
import os
import platform
import socket
from logging import Logger

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.singleton import singleton


class AutomationConfigError(RuntimeError):
    """Raise when automation config is invalid"""

@singleton
class AutomationConfigTool:
    """Tool to parse the automation config file for config values."""

    def __init__(self, log: Logger) -> None:
        """Initialize the automation config tool. Configuration will be parsed and saved into a dictionary, so the
            config file only needs parsed a single time.

        Args:
            log: logger to use for test logging.
        """
        automation_config_path = os.path.join(Framework.CFG_BASE[platform.system()], socket.gethostname() + ".cfg")
        if not os.path.exists(automation_config_path):
            error_msg = f"The BMC config '{automation_config_path}' does not exist, populate this file and run again."
            log.error(error_msg)
            raise AutomationConfigError(error_msg)

        cp = configparser.SafeConfigParser()
        cp.read(automation_config_path)
        self._config_dict = {sn: {c: v for c, v in s.items()} for sn, s in cp.items()}

    def get_config_value(self, section: str, config_key: str) -> str:
        """Retrieve the specified value from the automation configuration file.

        Args:
            section: section name in configuration file.
            config_key: key name in configuration file.

        Return:
            str: value of the config according to given keys.
        """
        return self._config_dict[section][config_key]
