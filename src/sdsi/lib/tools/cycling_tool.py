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
"""Tool which provides various cycling functionalities.

    Typical usage example:
        self.cycling_tool = CyclingTool(log, sut_os, config, ac_power)
        self.cycling_tool.perform_os_cycle()
        self.cycling_tool.perform_ac_cycle()
        self.cycling_tool.perform_dc_cycle()
"""
import time
from logging import Logger
from xml.etree.ElementTree import Element

from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.sdsi.lib.tools.redfish_tool import RedFishTool
from src.sdsi.lib.tools.sut_os_tool import SutOsTool


class CyclingTool:
    """Class to perform cycling operations."""

    def __init__(self, log: Logger, sut_os: SutOsProvider, config: Element, ac_power: AcPowerControlProvider) -> None:
        """Initialize the cycling tool.

        Args:
            log: logger to use for test logging.
            sut_os: OS provider used for test content to interact with SUT.
            config: configuration options for test content.
            ac_power: AC provider used for test content to control AC power.
        """
        self._log = log
        self._config = config
        self._ac_power = ac_power
        self._sut_os_tool: SutOsTool = SutOsTool(log, sut_os)

    def perform_dc_cycle(self) -> None:
        """Performs a DC cycle on the SUT."""
        self._log.info('Powering down SUT with system command.')
        self._sut_os_tool.execute_cmd('systemctl poweroff')
        time.sleep(30)

        self._log.info('Sending request to BMC to power on SUT.')
        power_control_url = "/redfish/v1/Systems/system/Actions/ComputerSystem.Reset"
        power_on_cmd = r"{\"ResetType\": \"On\"}"
        RedFishTool(self._log, self._config).curl_post(power_control_url, power_on_cmd)

        self._sut_os_tool.wait_for_os()
        self._log.info("SUT successfully booted through RedFish POST request.")

    def perform_ac_cycle(self):
        """Performs an AC cycle on the SUT."""
        self._log.info("Performing AC cycle on the SUT.")

        # Power OFF
        max_attempts = 5
        for current_attempt in range(max_attempts):
            current_attempt += 1
            self._log.info(f"Attempt #{current_attempt} to power off SUT.")
            if self._ac_power.ac_power_off():
                break
            if current_attempt == max_attempts:
                error_msg = f'Failed to power off SUT after {max_attempts} attempts'
                self._log.error(error_msg)
                raise RuntimeError(error_msg)

        # Power ON
        for current_attempt in range(max_attempts):
            current_attempt += 1
            self._log.info(f"Attempt #{current_attempt} to power on SUT.")
            if self._ac_power.ac_power_on():
                break
            if current_attempt == max_attempts:
                error_msg = f'Failed to power on SUT after {max_attempts} attempts'
                self._log.error(error_msg)
                raise RuntimeError(error_msg)

        self._sut_os_tool.wait_for_os()

    def perform_os_cycle(self):
        """Perform an OS cycle on the SUT."""
        self._sut_os_tool.perform_reboot()
