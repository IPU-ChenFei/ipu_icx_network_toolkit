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
"""Tool which provides functionality to interact with XMLCLI on the SUT.

    Typical usage example:
        self.xmlcli_tool: XmlCliTool = XmlCliTool(log, sut_os, config)
        self.xmlcli_tool.load_bios_defaults()
"""
from logging import Logger
from typing import Dict
from xml.etree.ElementTree import Element

from dtaf_core.lib.singleton import singleton
from dtaf_core.providers.bios_provider import XmlCliBiosProvider as XmlCliProvider
from dtaf_core.providers.provider_factory import ProviderFactory


@singleton
class XmlCliTool:
    """Class which interacts with XMLCLI on the SUT."""

    def __init__(self, log: Logger, config: Element) -> None:
        """Initialize the xmlcli tool.

        Args:
            log: logger to use for test logging.
            config: configuration options for test content.
        """
        self._log = log
        self._config = config
        self._bios: XmlCliProvider = ProviderFactory.create(config.find(XmlCliProvider.DEFAULT_CONFIG_PATH), log)

    def set_bios_knobs(self, bios_knobs: Dict[str, str]) -> None:
        """Set the specific bios knobs on the SUT. A reboot will be required to apply the BIOS changes.

        Args:
            bios_knobs: The bios knobs to be set, {knob_name: knob_value}
        """
        [self.set_bios_knob(knob_name, knob_value) for knob_name, knob_value in bios_knobs.items()]

    def set_bios_knob(self, knob_name: str, knob_value: str) -> None:
        """Set a single bios knob on the SUT. A reboot will be required to apply the BIOS changes.

        Args:
            knob_name: The name of the bios knob to set.
            knob_value: The value to set the bios knob to.
        """
        self._bios.set_bios_knobs(knob_name, knob_value, overlap=True)

    def verify_bios_knobs(self, bios_knobs: Dict[str, str]) -> None:
        """Verify that the given bios knobs are set to specified values. Recommended to call this method after reboot
        following a change of bios knobs.

        Args:
            bios_knobs: The bios knobs to be verified, {knob_name: expected_knob_value}
        """
        [self.verify_bios_knob(knob_name, knob_value) for knob_name, knob_value in bios_knobs.items()]

    def verify_bios_knob(self, knob_name: str, knob_value: str):
        """Verify a single bios knob on the SUT.

        Args:
            knob_name: The name of the bios knob to verify.
            knob_value: The expected value of the bios knob.
        """
        self._log.info(f"Verifying bios knob {knob_name}")
        current_knob_value = self.get_bios_knob_current_value(knob_name)
        numeric_current = int(''.join(v for v in current_knob_value if v.isdigit()))
        numeric_expected = int(''.join(v for v in knob_value if v.isdigit()))
        if numeric_current != numeric_expected:
            error_msg = f"{knob_name} bios knob is set to {numeric_current}, expected {numeric_expected}"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)

    def get_bios_knob_current_value(self, knob_name: str) -> str:
        """Reads the value of a single bios knob.

        Args:
            knob_name: The name of the bios knob to read the value of

        Raise:
            RuntimeError: If the bios knob cannot be read

        Return:
            str: The value of the bios knob.
        """
        ret_value = self._bios.read_bios_knobs(knob_name, hexa=True)
        if not ret_value:
            error_msg = f"Could not find {knob_name} bios knob"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        return ret_value[1][0].split()[-1].strip()

    def load_bios_defaults(self) -> None:
        """Load the default bios knobs according to the default platform configuration.

        Raise:
            RuntimeError: If the bios knob cannot be set to default
        """
        ret_val = self._bios.default_bios_settings()
        if not ret_val[0]:
            error_log = "Load bios defaults: Failed due to '{}'..".format(ret_val[1])
            self._log.error(error_log)
            raise RuntimeError(error_log)
        self._log.info("Load bios defaults: Successful...")
