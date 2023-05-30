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
"""Module containing the abstract sdsi base class for subclass implementation guidelines.

    Typical usage example:
        The sdsi base class is meant to be inherited by subclass test cases.
"""
import os
import platform
import shutil
from abc import ABCMeta, abstractmethod
from argparse import Namespace
from logging import Logger
from xml.etree.ElementTree import Element

from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.ac_power import AcPowerControlProvider as AcProvider
from dtaf_core.providers.console_log import ConsoleLogProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.sdsi.lib.sdsi_agent_lib import SDSiAgentLib
from src.sdsi.lib.sdsi_feature_lib import SDSiFeatureLib
from src.sdsi.lib.tools.automation_config_tool import AutomationConfigTool
from src.sdsi.lib.base_test_case import BaseTestCase
from src.sdsi.lib.tools.cycling_tool import CyclingTool
from src.sdsi.lib.tools.hsdes_tool import HSDESTool
from src.sdsi.lib.tools.sut_cpu_info_tool import SutCpuInfoTool
from src.sdsi.lib.tools.sut_os_tool import SutOsTool
from src.sdsi.lib.tools.xmlcli_tool import XmlCliTool


class SDSiBaseTestCase(BaseTestCase, metaclass=ABCMeta):
    """SDSiBaseTestCase is the base test class for all sdsi content test cases"""

    def __init__(self, log: Logger, args: Namespace, config: Element):
        """Initialize the SDSiBaseTestCase

        Args:
            log: logger to use for test logging.
            args: test case command line arguments.
            config: configuration options for test content.
        """
        super().__init__(log, args, config)
        # Initialize Test Utilities
        self.os: SutOsProvider = ProviderFactory.create(config.find(SutOsProvider.DEFAULT_CONFIG_PATH), log)
        self.ac: AcProvider = ProviderFactory.create(config.find(AcProvider.DEFAULT_CONFIG_PATH), log)
        self.cycling_tool: CyclingTool = CyclingTool(log, self.os, config, self.ac)
        self.sut_os_tool: SutOsTool = SutOsTool(log, self.os)
        if not self.os.is_alive(): self.cycling_tool.perform_ac_cycle()
        self.xmlcli_tool: XmlCliTool = XmlCliTool(log, config)
        self.sdsi_agent: SDSiAgentLib = SDSiAgentLib(self._log, self.os, self.ac, config)
        self.sdsi_feature_lib: SDSiFeatureLib = SDSiFeatureLib(self._log, self.os, config, self.sdsi_agent, self.ac)
        self.automation_config_tool: AutomationConfigTool = AutomationConfigTool(self._log)
        self.platform_info_tool: SutCpuInfoTool = SutCpuInfoTool.factory(self._log, self.os, config)
        self.hsdes_tool = HSDESTool(self._log)

        # Redirect serial logs
        if not os.path.exists(ser_log_dir := os.path.join(self.log_dir, "serial_logs")): os.makedirs(ser_log_dir)
        ser_log_file = os.path.join(ser_log_dir, "serial_log.log")
        ProviderFactory.create(config.find(ConsoleLogProvider.DEFAULT_CONFIG_PATH), self._log).redirect(ser_log_file)
        if args is not None: self._cc_log_path = args.outputpath
        self.sut_os_tool.clear_os_error_logs()

        # Log Test information
        if (test_id := self.get_phoenix_id()) != 0:
            self._log.info(f"{'#' * 20} Test Info {'#' * 20}")
            self._log.info(f"Article ID: {test_id}")
            self._log.info(f"Article Title: {self.hsdes_tool.get_test_title(test_id)}")
            self._log.info(f"Family Affected: {self.hsdes_tool.get_test_family_affected(test_id)}")
            self._log.info(f"Domain Affected: {self.hsdes_tool.get_test_domain_affected(test_id)}")
            self._log.info(f"Article Collaborators: {self.hsdes_tool.get_test_collaborators(test_id)}")
        else: self._log.info("Phoenix ID not provided.")

        # Log SUT information
        self._log.info(f"{'#' * 20} SUT Info {'#' * 20}")
        self._log.info(f"OS: {self.os.os_type}")
        self._log.info(f"Number of sockets: {self.platform_info_tool.get_number_of_sockets()}")
        self._log.info(f"Number of cores: {self.platform_info_tool.get_number_of_cores()}")
        self._log.info(f"Number of threads: {self.platform_info_tool.get_number_of_threads()}")
        self._log.info(f"CPU Frequency: {self.platform_info_tool.get_current_cpu_frequency()}")
        self._log.info(f"Stepping: {self.platform_info_tool.get_cpu_stepping()}")

        # Log Host information
        self._log.info(f"{'#' * 20} Host Info {'#' * 20}")
        self._log.info(f"OS: {platform.platform()}")
        self._log.info(f"Processor: {platform.processor()}")
        self._log.info(f"Architecture: {platform.architecture()}")
        self._log.info(f"Python Version: {platform.python_version()}")
        self._log.info(f"{'#' * 20}{'#' * len(' Host Info ')}{'#' * 20}")

    def prepare(self) -> None:
        """Method called when a test is initiated to perform setup and initialization tasks"""
        super().prepare()
        self.xmlcli_tool.load_bios_defaults()
        self.sdsi_agent.verify_agent()
        self.sdsi_agent.erase_provisioning()
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_agent.validate_default_registry_values()

    def execute(self) -> None:
        """Method with the main execution test logic - Perform the expected test steps"""
        super().execute()

    def cleanup(self) -> None:
        """Clean-up method called when execution ends - Revert platform to a stable state if required"""
        # Copy logs to command center
        if self._cc_log_path:
            self._log.info(f"Command center log folder: {self._cc_log_path}")
            folder_name = os.path.basename(self.log_dir)
            cc_folder_path = os.path.join(self._cc_log_path, folder_name)
            shutil.copytree(self.log_dir, cc_folder_path)

        # Store os logs
        if not self.os.is_alive():
            self.cycling_tool.perform_ac_cycle()

        self._log.info("Collecting logs")
        log_dir = os.path.join(self.log_dir, "os_logs")
        os.makedirs(log_dir, exist_ok=True)
        if self.os.os_type == OperatingSystems.LINUX:
            for command in ["dmesg", "/var/log"]:
                if self.os.check_if_path_exists(command):
                    self.os.copy_file_from_sut_to_local(command, os.path.join(log_dir, os.path.split(command)[-1]))
                elif self.os.check_if_path_exists(command, directory=True):
                    tar_file = command.replace("/", "_") + ".tar.gz"
                    self.os.execute("tar -czvf %s %s" % (tar_file, command), 1200, cwd=command)
                    self.os.copy_file_from_sut_to_local(command + "/" + tar_file, os.path.join(log_dir, tar_file))
                else:
                    log_file = "/tmp/%s.log" % command
                    self.os.execute("rm -rf %s" % log_file, 1200)
                    self.os.execute("%s > %s " % (command, log_file), 1200)
                    self.os.copy_file_from_sut_to_local(log_file, os.path.join(log_dir, os.path.split(log_file)[-1]))
        else:
            self._log.warning(f'OS Logs not supported for operating system {self.os.os_type}.')

        super().cleanup()

    @abstractmethod
    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test

        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
