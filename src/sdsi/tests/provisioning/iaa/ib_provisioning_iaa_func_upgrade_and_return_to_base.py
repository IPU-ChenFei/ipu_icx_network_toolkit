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
import sys
from typing import List

from dtaf_core.lib.dtaf_constants import Framework

import src.sdsi.lib.sdsi_exceptions as SDSiExceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


class InBandIAAFuncProvisionAndReturnToBase(ContentBaseTestCase):
    """
    Glasgow_ID: NA
    Phoenix_ID: NA - OOB 18014074695
    Expectation is that IAA devices should works only after applying the IAA4 licenses (except default devices)
    """
    IAA_PAYLOAD_NAME = 'IAA4'
    RTB_PAYLOAD_NAME = 'BASE'
    ROOT_FOLDER = '/'
    IAA_DEVICES = {0: ['6f:02.0', '74:02.0', '79:02.0'],
                   1: ['ec:02.0', 'f1:02.0', 'f6:02.0']}
    DSA_DEVICES = {0: ['6f:01.0', '74:01.0', '79:01.0'],
                   1: ['ec:01.0', 'f1:01.0', 'f6:01.0']}
    DLB_DEVICES = {0: ['72:00.0', '77:00.0', '7c:00.0'],
                   1: ['ef:00.0', 'f4:00.0', 'f9:00.0']}
    IAA_DEFAULT_DEVICES = {0: ['6a:02.0'],
                           1: ['e7:02.0']}
    DSA_DEFAULT_DEVICES = {0: ['6a:01.0'],
                           1: ['e7:01.0']}
    DLB_DEFAULT_DEVICES = {0: ['6d:00.0'],
                           1: ['ea:00.0']}

    def _get_common_lib(self):
        self._log.info("Using In Band Common Library")
        from src.sdsi.lib.in_band_sdsi_common_lib import SDSICommonLib
        return SDSICommonLib(self._log, self.os, self._common_content_lib, self._common_content_configuration,
                             self._sdsi_installer, self.ac_power)

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of InBandIAAFuncProvisionAndReturnToBase
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super().__init__(test_log, arguments, cfg_opts)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = self._get_common_lib()
        self.default_devices_found = set()

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super().prepare()
        self._sdsi_installer.verify_sdsi_installer()
        self._sdsi_obj.validate_default_registry_values()
        self._sdsi_obj.erase_payloads_from_nvram()
        self.perform_graceful_g3()
        self._common_content_lib.set_datetime_on_linux_sut()

    def _enable_initial_bios_settings(self) -> None:
        """
        This method is using to update all initial bios settings
        """
        self._log.info("Updating bios knob settings Items.")
        for knob_name in ['PcieEnqCmdSupport', 'ProcessorVmxEnable','InterruptRemap', 'VTdSupport']:
            self.bios_util.set_single_bios_knob(knob_name, "0x1")
        self._log.info("Update the basic BIOS settings")

    def apply_payload(self, socket, payload_name):
        """
        This method is using to apply the payload to a socket.
        :param socket: socket number
        :param payload_name: payload name to be apply for a given socket
        """
        payload_info = self._sdsi_obj.get_capability_activation_payload(socket, payload_name)
        self._sdsi_obj.apply_capability_activation_payload(payload_info, socket)

    def verify_device_list_status(self, device_list: List[str], expected_status: bool = False):
        """
        This method is using to check the status of the pcie device status.
        :param device_list: the device list should be in bus:device.function mode.
        :param expected_status: expected status means device should be present or not
        """
        for device in device_list:
            command = "lspci -s " + device
            dlb_pci_response = self._sdsi_obj._os.execute(command, self._sdsi_obj.cmd_timeout, self.ROOT_FOLDER)
            if dlb_pci_response.cmd_failed(): self._log.error(dlb_pci_response.stderr)
            if (device in dlb_pci_response.stdout) == expected_status:
                self._log.info(f"{device} device enumerated: {str(expected_status)}")
            else:
                log_error = f"{device} device enumeration does not match expected value: {str(expected_status)}"
                self._log.error(log_error)
                raise SDSiExceptions.DeviceError(log_error)

    def verify_default_device_list_status(self, device_list: List[str]) -> List[str]:
        """
        This method is using to check the status of the pcie device status.
        :param device_list: the device list should be in bus:device.function mode.
        :param expected_status: expected status means device should be present or not
        """
        found_default_devices = []
        for device in device_list:
            command = "lspci -s " + device
            dlb_pci_response = self._sdsi_obj._os.execute(command, self._sdsi_obj.cmd_timeout, self.ROOT_FOLDER)
            if dlb_pci_response.cmd_failed(): self._log.error(dlb_pci_response.stderr)
            if device in dlb_pci_response.stdout:
                found_default_devices.append(device)
        return found_default_devices

    def execute(self):
        """
            Test case steps.
            pre: apply license, clear NVRAM.
            - Verify any IAA devices enumerated without IAA4 payload
            - Apply IAA4 payload
            - Verify 4 devices from each cpu enumerated.
            - Reapply IAA0 to rebase to default
            - Verify any IAA devices enumerated with IAA0 payload.
        """
        # Enable BIOS settings
        self._log.info("#3 - Enable new bios settings")
        self._enable_initial_bios_settings()
        self._log.info("Starting a cold reset - to apply the new BIOS settings.")
        self.perform_graceful_g3()

        # Verify the status of the default IAA device lists.
        self._log.info("#5 Verify non expected IAA devices are enumerated without IAA4 capability payload")
        for socket in range(self._sdsi_obj.number_of_cpu):
            for default_device in self.verify_default_device_list_status(self.IAA_DEFAULT_DEVICES[socket]):
                self.default_devices_found.add(default_device)
            for default_device in self.verify_default_device_list_status(self.DSA_DEFAULT_DEVICES[socket]):
                self.default_devices_found.add(default_device)
            for default_device in self.verify_default_device_list_status(self.DLB_DEFAULT_DEVICES[socket]):
                self.default_devices_found.add(default_device)
            self.verify_device_list_status(self.IAA_DEVICES[socket], False)
            self.verify_device_list_status(self.DSA_DEVICES[socket], False)
            self.verify_device_list_status(self.DLB_DEVICES[socket], False)

        # Install IAA 4 capability.
        self._log.info("#6 - Apply IAA4 payload on CPUs and start cold reboot")
        for socket in range(self._sdsi_obj.number_of_cpu):
            self.apply_payload(socket, self.IAA_PAYLOAD_NAME)
        self.perform_graceful_g3()

        # Verify IAA devices are numerated.
        self._log.info("#11 - Verify IAA devices are enumerated after applying capability payload")
        for socket in range(self._sdsi_obj.number_of_cpu):
            for default_device in self.verify_default_device_list_status(self.IAA_DEFAULT_DEVICES[socket]):
                self.default_devices_found.add(default_device)
            for default_device in self.verify_default_device_list_status(self.DSA_DEFAULT_DEVICES[socket]):
                self.default_devices_found.add(default_device)
            for default_device in self.verify_default_device_list_status(self.DLB_DEFAULT_DEVICES[socket]):
                self.default_devices_found.add(default_device)
            self.verify_device_list_status(self.IAA_DEVICES[socket], True)
            self.verify_device_list_status(self.DSA_DEVICES[socket], False)
            self.verify_device_list_status(self.DLB_DEVICES[socket], False)

        # Apply RTB payload license
        self._log.info("#8 - Apply RTB payload on sockets and start cold reboot")
        for socket in range(self._sdsi_obj.number_of_cpu):
            self.apply_payload(socket, self.RTB_PAYLOAD_NAME)
        self._log.info("Starting a cold reset - to check the CAP file updated properly.")
        self.perform_graceful_g3()

        # Verify any IAA devices enumerated
        self._log.info("#9 - Verify default IAA devices are enumerated with default capability payload")
        for socket in range(self._sdsi_obj.number_of_cpu):
            for default_device in self.verify_default_device_list_status(self.IAA_DEFAULT_DEVICES[socket]):
                self.default_devices_found.add(default_device)
            for default_device in self.verify_default_device_list_status(self.DSA_DEFAULT_DEVICES[socket]):
                self.default_devices_found.add(default_device)
            for default_device in self.verify_default_device_list_status(self.DLB_DEFAULT_DEVICES[socket]):
                self.default_devices_found.add(default_device)
            self.verify_device_list_status(self.IAA_DEVICES[socket], False)
            self.verify_device_list_status(self.DSA_DEVICES[socket], False)
            self.verify_device_list_status(self.DLB_DEVICES[socket], False)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._log.info("Perform graceful G3 for resetting the counters after test irrespective of pass/fail.")
        self.perform_graceful_g3()
        super().cleanup(return_status)
        # Message user if default devices were found, these devices can change per CPU.
        if self.default_devices_found:
            device_warning = f"DEFAULT DEVICES WERE ENUMERATED ON THIS DEVICE. " \
                             f"ENSURE THESE DEVICES ARE CORRECT ACCORDING TO YOUR CPU: {self.default_devices_found}"
            self._log.info(device_warning)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if InBandIAAFuncProvisionAndReturnToBase.main()
             else Framework.TEST_RESULT_FAIL)