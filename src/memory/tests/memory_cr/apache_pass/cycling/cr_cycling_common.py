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
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider

from src.lib.common_content_lib import CommonContentLib
from src.lib.bios_util import BiosUtil
from src.lib.install_collateral import InstallCollateral
from src.lib.content_configuration import ContentConfiguration
from src.memory.lib.memory_common_lib import MemoryCommonLib


class CrCyclingCommon(BaseTestCase):
    """
    Base class for all CR Cycling test cases
    This base class covers below glasgow IDs.

    1. 59995
    2. 57081
    """

    LINUX_PLATFORM_REBOOTER_LOG_PATH = "/platform_rebooter/logs/"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file):
        """
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

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, bios_config_file)
        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)

        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()

        self._num_of_cycles = self._common_content_configuration.memory_number_of_cycle()
        self._next_reboot_wait_time = self._common_content_configuration.memory_next_reboot_wait_time()

        self._mem_parse_log = MemoryCommonLib(self._log, cfg_opts, self._os, self._num_of_cycles)

        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)

    def execute_dcpmm_reboot_cycler(self, tool_path):
        """
        Function to execute DCPMM Reboot Cycler

        :param: tool_path: DCPMM Platform Cycler tool path
        :return: false if the test case is failed log parsing else true
        """
        self._log.info("Running the platform cycler installer test....")

        #  Execute DCPMM Reboot Cycler
        self._common_content_lib.execute_platform_cycler("--dcpmm --reboot", self._num_of_cycles,
                                                         self._next_reboot_wait_time, self._command_timeout, tool_path)
        self._log.info("Waiting for dcpmm reboot platform cycler test to complete....")

        # calculate total time to wait until stress test completes
        total_wait_time = \
            self._next_reboot_wait_time * self._num_of_cycles + \
            self._num_of_cycles * self._reboot_timeout
        self._log.info("Total wait time is {} seconds...".format(total_wait_time))

        time.sleep(total_wait_time)  # wait for dcpmm pltform cycler to perform the reboot cycling
        if not self._os.is_alive():
            log_error = "SUT did not come back after the completion of reboot cycle test.."
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info("The dcpmm platform cycler reboot test is completed....")
        return True

    def execute_dcpmm_soft_reboot_cycler(self, tool_path):
        """
        Function to execute DCPMM Soft Reboot Cycler

        :param: tool_path: DCPMM Platform Cycler tool path
        :return: false if the test case is failed log parsing else true
        """
        self._log.info("Running the platform cycler installer test....")

        result = self._common_content_lib.execute_platform_cycler("--dcpmm --reboot -s", self._num_of_cycles,
                                                                  self._next_reboot_wait_time, self._command_timeout,
                                                                  tool_path)
        self._log.info("Waiting for dcpmm soft reboot platform cycler test to complete....")
        # calculate total time to wait until stress test completes
        total_wait_time = \
            self._next_reboot_wait_time * self._num_of_cycles + \
            self._num_of_cycles * self._reboot_timeout
        self._log.info("Total wait time is {} seconds...".format(total_wait_time))

        time.sleep(total_wait_time)  # wait for timeout
        if not self._os.is_alive():
            log_error = "SUT did not come back after the completion of soft reboot cycle test.."
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info("The dcpmm platform cycler soft reboot test is completed....")
        return True

    def log_parsing_rebooter(self, log_file_path):
        """
        Parsing all the necessary logs.

        :param: log_file_path: folder path for all the logs
        :return: false if the test case is failed log parsing else true
        """
        final_result = [self._mem_parse_log.dcpmm_platform_log_parsing
                        (log_path=os.path.join(log_file_path, "platform_rebooter.log")),
                        self._mem_parse_log.verification_of_dcpmm_dirtyshutdown_log
                        (log_path=os.path.join(log_file_path, "dcpmm_dirtyshutdowns.log")),
                        self._mem_parse_log.verification_dcpmm_log
                        (log_path=os.path.join(log_file_path, "dcpmm.log")),
                        self._mem_parse_log.check_memory_log
                        (log_path=os.path.join(log_file_path, "memory.log")),
                        self._mem_parse_log.parse_log_for_error_patterns
                        (log_path=os.path.join(log_file_path, "mce.log")),
                        self._mem_parse_log.parse_log_for_error_patterns
                        (log_path=os.path.join(log_file_path, "dmesg.log")),
                        self._mem_parse_log.parse_log_for_error_patterns
                        (log_path=os.path.join(log_file_path, "journalctl.log"), encoding='UTF-8'),
                        self._mem_parse_log.parse_log_for_error_patterns
                        (log_path=os.path.join(log_file_path, "sel.log"), encoding='UTF-8')]

        return all(final_result)
