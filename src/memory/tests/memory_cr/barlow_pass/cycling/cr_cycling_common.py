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

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.dc_power import DcPowerControlProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.memory.lib.memory_common_lib import MemoryCommonLib

from src.lib.content_configuration import ContentConfiguration
from src.lib.install_collateral import InstallCollateral


class CrCyclingCommon(BaseTestCase):
    """
    Base class for all memory CR cycling related test cases with eAdr enabled. This base class covers below glasgow IDs

    1. 59772
    2. 59994
    3. TBD
    4. TBD
    5. TBD
    """

    LINUX_PLATFORM_DC_CYCLER_LOG_PATH = "/platform_dc_ungraceful/logs/"
    LINUX_PLATFORM_DC_GRACEFUL_CYCLER_LOG_PATH = "/platform_dc_graceful/logs/"
    LINUX_USR_ROOT_PATH = "/root"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file):
        """
        Constructor of a class.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param bios_config_file: configuration file of BIOS

        :return: None
        :raises: None
        """
        super(CrCyclingCommon, self).__init__(test_log, arguments, cfg_opts)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)

        dc_power_cfg = cfg_opts.find(DcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._dc_power = ProviderFactory.create(dc_power_cfg, test_log)

        ac_power_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_power = ProviderFactory.create(ac_power_cfg, test_log)

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, bios_config_file)
        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)

        self._common_content_configuration = ContentConfiguration(self._log)

        self._num_of_cycles = self._common_content_configuration.memory_number_of_cycle()
        self._mem_parse_log = MemoryCommonLib(self._log, cfg_opts, self._os, self._num_of_cycles)

        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._next_reboot_wait_time = self._common_content_configuration.memory_next_reboot_wait_time()
        self._dc_on_time = self._common_content_configuration.memory_dc_on_time()
        self._test_execute_time = self._common_content_configuration.memory_test_execute_time()
        self._stress_app_execute_time = self._common_content_configuration.memory_stress_test_execute_time()

        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)

    def execute_installer_dc_stress_test_linux(self, tool_path, command):
        """
        Executing the installer file with specific cycle and waiting time.

        :param: tool_path: Platform cycler extracted path.
        :param: command: dcpmm command that needs to be executed.
        :return: None
        :raise: RuntimeError if stress test execution failed.
        """
        try:

            self._log.info("Starting the platform cycler test with number of cycles : {} and "
                           "amount of wait time after rebooting : {}".format(self._num_of_cycles,
                                                                             self._next_reboot_wait_time))
            self._log.info("Waiting for platform cycler installer test to complete....")
            self._common_content_lib.execute_platform_cycler(
                command, self._num_of_cycles, self._next_reboot_wait_time, self._command_timeout, tool_path)

            current_cycle = 0
            dc_cycling = True
            while dc_cycling:
                if self._os.is_alive():
                    self._log.info("Cycle {} test execution time is approximately "
                                   "{} seconds...".format(current_cycle, self._test_execute_time))
                    # wait time to finish stress test to finish its execution
                    time.sleep(self._test_execute_time)
                    self._log.info("Cycle {} execution has been completed"
                                   "... SUT will soon shutdown..".format(current_cycle))

                    if self._os.is_alive():
                        log_error = "SUT did not shutdown after the completion of dc test.."
                        self._log.error(log_error)
                        raise RuntimeError(log_error)

                if not self._os.is_alive():
                    if self._dc_power.dc_power_on():
                        current_cycle += 1
                        self._log.info("SUT is powering on... Approximate wait time is {} seconds..."
                                       .format(self._dc_on_time))
                        # wait time after dc power is on
                        self._os.wait_for_os(self._dc_on_time)
                        self._log.info("SUT booted to OS")
                    else:
                        err_log = "Failed to power on the system..."
                        self._log.error(err_log)
                        raise RuntimeError(err_log)

                if current_cycle == self._num_of_cycles:
                    dc_cycling = False

            self._log.info("The platform cycler test is completed....")

        except Exception as ex:
            log_error = "Cycler execution failed with exception '{}'...".format(ex)
            self._log.error(log_error)
            raise ex
