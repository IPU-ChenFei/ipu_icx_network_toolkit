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
"""Module containing SDSiFeatureLib class to interact with SDSi SKU-able features.

    Typical usage example:
        self.sdsi_feature_lib: SDSiFeatureLib = SDSiFeatureLib(self._log, self.os, config, self.sdsi_agent, self.ac)

        # Verify the status of the default device lists.
        self._log.info("Verify expected default QAT devices are enumerated.")
        self.sdsi_feature_lib.verify_qat_device_count(self.sdsi_agent.num_sockets)

        self._log.info("Verify expected default DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_dlb_device_count(self.sdsi_agent.num_sockets)

        self._log.info("Verify expected default DSA devices are enumerated.")
        self.sdsi_feature_lib.verify_dsa_device_count(self.sdsi_agent.num_sockets)
"""
import re
from logging import Logger
from math import isclose
from typing import Dict
from xml.etree.ElementTree import Element

from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider

import src.sdsi.lib.sdsi_exceptions as SDSiExceptions
from src.sdsi.lib.license.sdsi_license_names import FeatureNames
from src.sdsi.lib.sdsi_agent_lib import SDSiAgentLib
from src.sdsi.lib.tools.cycling_tool import CyclingTool
from src.sdsi.lib.tools.sut_os_tool import SutOsTool
from src.sdsi.lib.tools.xmlcli_tool import XmlCliTool


class SDSiFeatureLib:
    """Library which holds common functionality for SDSi Feature operations."""
    ROOT_FOLDER = '/'
    PRM_KNOB_NAME = 'PrmSgxSize'
    MEMORY_DEVIATION = 0.15
    PRM_KNOBS = {1: "0x40000000", 2: "0x80000000", 4: "0x100000000", 8: "0x200000000", 16: "0x400000000",
                 32: "0x800000000", 64: "0x1000000000", 128: "0x2000000000", 256: "0x4000000000", 512: "0x8000000000"}
    PRM_SIZE_TO_APPLY = {FeatureNames.SG01.value: 8, FeatureNames.SG04.value: 32, FeatureNames.SG08.value: 64,
                         FeatureNames.SG10.value: 128, FeatureNames.BASE.value: 128, FeatureNames.SG20.value: 256,
                         FeatureNames.SG40.value: 512}
    DEVICE_COUNT_CMD = 'lspci -nn | grep {} | wc -l'
    IAA_DEVICE_ID = '8086:0cfe'
    DLB_DEVICE_ID = '8086:2710'
    DSA_DEVICE_ID = '8086:0b25'

    def __init__(self, log: Logger, sut_os: SutOsProvider, config: Element, sdsi_agent: SDSiAgentLib,
                 ac_power: AcPowerControlProvider) -> None:
        """Initialize the SDSiFeatureLib

        Args:
            log: logger to use for test logging.
            sut_os: OS provider used for test content to interact with SUT.
            config: configuration options for test content.
            sdsi_agent: The SDSi Agent library to provide sdsi-agent interaction.
            ac_power: AC provider used for test content to control AC power.
        """
        # Intialize test utilities
        self._log = log
        self._sdsi_agent = sdsi_agent
        self.xmlcli_tool: XmlCliTool = XmlCliTool(log, sut_os, config)
        self.cycling_tool: CyclingTool = CyclingTool(log, sut_os, config, ac_power)
        self.sut_os_tool: SutOsTool = SutOsTool(log, sut_os)

    def set_and_validate_prm_size(self, feature_name: str, expected_status: bool = True) -> None:
        """Attempt to set the SgxPrmSize knob to the size which matches the expected maximum size for the given feature.

        Args:
            feature_name: The name of the feature to validate PrmSize enabling.
            expected_status: whether the prm is expected to apply successfully.

        Raises:
            SDSiExceptions.SGXError: If the bios knob or memory reduction does not match expected status.
        """
        # Get previous Prm and memory information to compare after setting new knobs.
        previous_prm_size = int(self.xmlcli_tool.get_bios_knob_current_value(self.PRM_KNOB_NAME), 16) / pow(1024, 3)
        memory_before = self.get_total_memory_in_gb() + (previous_prm_size * self._sdsi_agent.num_sockets)

        # Set Prm knob and reboot
        expected_size_in_gb = self.PRM_SIZE_TO_APPLY[feature_name]
        self._log.info(f'Set the PrmSgxSize to {expected_size_in_gb}GB')
        self.xmlcli_tool.set_bios_knobs({self.PRM_KNOB_NAME: self.PRM_KNOBS[expected_size_in_gb]})
        self._log.info('Power cycle the SUT for the BIOS changes to take effect.')
        self.cycling_tool.perform_ac_cycle()

        # Validate knob was set as expected
        current_prm_size = int(self.xmlcli_tool.get_bios_knob_current_value(self.PRM_KNOB_NAME), 16) / pow(1024, 3)
        if expected_status != (current_prm_size == expected_size_in_gb):
            error_msg = f'Prm Size not set to {expected_size_in_gb} as expected.'
            self._log.error(error_msg)
            raise SDSiExceptions.SGXError(error_msg)
        self._log.info(f'Prm Size set to {expected_size_in_gb} as expected.')

        # Verify memory reduction
        memory_after = self.get_total_memory_in_gb()
        expected_size_in_gb = expected_size_in_gb * self._sdsi_agent.num_sockets
        self._log.info(f'Initial platform memory was {memory_before}GB.')
        self._log.info(f'Current system memory size available is {memory_after}GB.')
        if expected_status != isclose(memory_before - memory_after, expected_size_in_gb, rel_tol=self.MEMORY_DEVIATION):
            error_msg = f'Not within {self.MEMORY_DEVIATION}% of expected memory reduction: {expected_size_in_gb}GB.'
            self._log.error(error_msg)
            raise SDSiExceptions.SGXError(error_msg)
        self._log.info(f'Within {self.MEMORY_DEVIATION}% of expected memory reduction: {expected_size_in_gb}GB.')

    def verify_iaa_device_count(self, expected_device_count: int) -> None:
        """Verify the number of enumerated IAA devices on the platform.

        Args:
            expected_device_count: The expected number of devices.

        Raises:
            SDSiExceptions.DeviceError: If the enumerated existing device count does not match expected count.
        """
        # Verify expected device count
        device_count = int(self.sut_os_tool.execute_cmd(self.DEVICE_COUNT_CMD.format(self.IAA_DEVICE_ID)))
        if device_count != expected_device_count:
            error_msg = f'IAA device count of {device_count} does not match expected {expected_device_count}.'
            self._log.error(error_msg)
            raise SDSiExceptions.DeviceError(error_msg)

    def verify_dlb_device_count(self, expected_device_count: int) -> None:
        """Verify the number of enumerated DLB devices on the platform.

        Args:
            expected_device_count: The expected number of devices.

        Raises:
            SDSiExceptions.DeviceError: If the enumerated existing device count does not match expected count.
        """
        # Verify expected device count
        device_count = int(self.sut_os_tool.execute_cmd(self.DEVICE_COUNT_CMD.format(self.DLB_DEVICE_ID)))
        if device_count != expected_device_count:
            error_msg = f'DLB device count of {device_count} does not match expected {expected_device_count}.'
            self._log.error(error_msg)
            raise SDSiExceptions.DeviceError(error_msg)

    def verify_dsa_device_count(self, expected_device_count: int) -> None:
        """Verify the number of enumerated DSA devices on the platform.

        Args:
            expected_device_count: The expected number of devices.

        Raises:
            SDSiExceptions.DeviceError: If the enumerated existing device count does not match expected count.
        """
        # Verify expected device count
        device_count = int(self.sut_os_tool.execute_cmd(self.DEVICE_COUNT_CMD.format(self.DSA_DEVICE_ID)))
        if device_count != expected_device_count:
            error_msg = f'DSA device count of {device_count} does not match expected {expected_device_count}.'
            self._log.error(error_msg)
            raise SDSiExceptions.DeviceError(error_msg)

    def verify_qat_device_count(self, expected_device_count: int) -> None:
        """Verify the number of enumerated QAT devices on the platform.

        Args:
            expected_device_count: The expected number of devices.

        Raises:
            SDSiExceptions.DeviceError: If the enumerated existing device count does not match expected count.
        """
        # Run command to get device count
        qat_result = self.sut_os_tool.execute_cmd('service qat_service status')
        device_count = len(qat_result.strip().split('\n')) - 2

        # Verify expected device count
        if device_count != expected_device_count:
            error_msg = f'QAT device count of {device_count} does not match expected {expected_device_count}.'
            self._log.error(error_msg)
            raise SDSiExceptions.DeviceError(error_msg)

    def get_total_memory_in_gb(self) -> float:
        """This method will fetch the total system memory from the platform

        Returns:
            float: total memory in GB
        """
        mem_result = self.sut_os_tool.execute_cmd('cat /proc/meminfo')
        return int(re.findall(r"MemTotal:.*", mem_result)[0].split(":")[1].strip()[:-3]) / (1024 * 1024)

    def set_sgx_default_knobs(self) -> Dict[str, str]:
        """Set the default BIOS knobs for SGX testing. Reboot required for changes to take affect.

        Returns:
            Dict[str, str]: The bios knobs which have been set {knob_name: knob_value}
        """
        bios_knobs = {"EnableTme": "0x1",
                      "EnableSgx": "0x1",
                      "volMemMode": "0x0",
                      "UmaBasedClustering": "0x0"}
        self.xmlcli_tool.set_bios_knobs(bios_knobs)
        return bios_knobs

    def set_iaa_driver_default_knobs(self) -> Dict[str, str]:
        """Set the default BIOS knobs for IAA driver testing. Reboot required for changes to take affect.

        Returns:
            Dict[str, str]: The bios knobs which have been set {knob_name: knob_value}
        """
        bios_knobs = {"PcieEnqCmdSupport": "0x1",
                      "ProcessorVmxEnable": "0x1",
                      "InterruptRemap": "0x1",
                      "VTdSupport": "0x1"}
        self.xmlcli_tool.set_bios_knobs(bios_knobs)
        return bios_knobs
