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

import src.lib.content_exceptions as ContentExceptions
import src.sdsi.lib.sdsi_exceptions as SDSiExceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


class InBandProvisioningUniqueFeaturesToMultiSocketTest(ContentBaseTestCase):
    """
    Glasgow_ID: 70138
    Phoenix_ID: 18014074921
    Test that DSA/DLB devices should work only after applying the corresponding licenses.
    """
    ROOT_FOLDER = "/"
    DLB2_DRIVER_NAME = "dlb2"
    DSA_PAYLOAD_NAME = 'DSA4'
    DLB_PAYLOAD_NAME = 'DLB4'
    IAX_DEVICES = {0: ['6f:02.0', '74:02.0', '79:02.0'],
                   1: ['ec:02.0', 'f1:02.0', 'f6:02.0']}
    DSA_DEVICES = {0: ['6f:01.0', '74:01.0', '79:01.0'],
                   1: ['ec:01.0', 'f1:01.0', 'f6:01.0']}
    DLB_DEVICES = {0: ['72:00.0', '77:00.0', '7c:00.0'],
                   1: ['ef:00.0', 'f4:00.0', 'f9:00.0']}
    IAX_DEFAULT_DEVICES = {0: ['6a:02.0'],
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
        Create an instance of OutOfBandDLBProvisionAndReturnToBaseFourDlbInst
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(InBandProvisioningUniqueFeaturesToMultiSocketTest, self).__init__(test_log, arguments, cfg_opts)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = self._get_common_lib()
        self.default_devices_found = set()
        if self._sdsi_obj.number_of_cpu < 2:
            error_msg = "Test requires minimum 2 cpu sockets"
            self._log.error(error_msg)
            raise ContentExceptions.TestUnSupportedError(error_msg)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(InBandProvisioningUniqueFeaturesToMultiSocketTest, self).prepare()
        self._sdsi_installer.verify_sdsi_installer()
        self._sdsi_obj.validate_default_registry_values()
        self._sdsi_obj.erase_payloads_from_nvram()
        self.perform_graceful_g3()
        self._log.info("DLB driver must be installed before test execution!")

    def verify_device_list_status(self, device_list: List[str], expected_status: bool = False) -> bool:
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
        return True

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

    def apply_payload(self, socket, payload_name):
        """
        This method is using to apply a payload to a socket.
        :param socket: socket number
        :param payload_name: payload name to be apply for a given socket
        """
        payload_info = self._sdsi_obj.get_capability_activation_payload(socket, payload_name)
        self._sdsi_obj.apply_capability_activation_payload(payload_info, socket)

    def execute(self):
        """
            Test case steps.
            pre: apply license, clear NVRAM.
            - Enable bios settings.
            - verify the default devices for dsa device list.
            - verify any dlb devices enumerated without dlb payload.
            - apply DSA4 license to socket 0 only.
            - appply dlb payload to socket 1 only.
            - verify both sockets and ensure the payload appllied properly.
            - enabled dsa and dlb on socket 1 only.
            - check payloads loaded each socket appropriately.
            - verify dsa devices loaded for socket 0.
            - load dlb traffic and ensure everything is OK.
        """
        # Enable BIOS settings
        self._log.info("Enable bios settings required for test.")
        enable_knobs = ['PcieEnqCmdSupport', 'ProcessorVmxEnable', 'DsaEn_0', 'DsaEn_1', 'DsaEn_2', 'DsaEn_3',
                        'DsaEn_4', 'DsaEn_5', 'DsaEn_6', 'DsaEn_7']
        disable_knobs = ['VTdSupport']
        [self.bios_util.set_single_bios_knob(knob, "0x1") for knob in enable_knobs]
        [self.bios_util.set_single_bios_knob(knob, "0x0") for knob in disable_knobs]
        self.perform_graceful_g3()

        # Verify the status of the default dsa device lists.
        self._log.info("Verify default devices are enumerated without DSA4 capability payload")
        for socket in range(self._sdsi_obj.number_of_cpu):
            for default_device in self.verify_default_device_list_status(self.IAX_DEFAULT_DEVICES[socket]):
                self.default_devices_found.add(default_device)
            for default_device in self.verify_default_device_list_status(self.DSA_DEFAULT_DEVICES[socket]):
                self.default_devices_found.add(default_device)
            for default_device in self.verify_default_device_list_status(self.DLB_DEFAULT_DEVICES[socket]):
                self.default_devices_found.add(default_device)
            self.verify_device_list_status(self.IAX_DEVICES[socket], False)
            self.verify_device_list_status(self.DSA_DEVICES[socket], False)
            self.verify_device_list_status(self.DLB_DEVICES[socket], False)

        # Apply DSA4 and DLB4 payload and start cold reboot
        self._log.info("Apply DSA4 payload on CPU 0.")
        self.apply_payload(0, self.DSA_PAYLOAD_NAME)
        self._log.info("Apply DLB4 payload on CPU 1 and start cold reboot")
        self.apply_payload(1, self.DLB_PAYLOAD_NAME)
        self._log.info("Starting a cold reset - to apply CAP files.")
        self.perform_graceful_g3()

        # Verify the DSA PCIes enumerated only in socket 0 and DLB devices enumerated only in socket 1
        for socket in range(self._sdsi_obj.number_of_cpu):
            for default_device in self.verify_default_device_list_status(self.IAX_DEFAULT_DEVICES[socket]):
                self.default_devices_found.add(default_device)
            for default_device in self.verify_default_device_list_status(self.DSA_DEFAULT_DEVICES[socket]):
                self.default_devices_found.add(default_device)
            for default_device in self.verify_default_device_list_status(self.DLB_DEFAULT_DEVICES[socket]):
                self.default_devices_found.add(default_device)
            self.verify_device_list_status(self.IAX_DEVICES[socket], False)
        self.verify_device_list_status(self.DSA_DEVICES[0], True)
        self.verify_device_list_status(self.DSA_DEVICES[1], False)
        self.verify_device_list_status(self.DLB_DEVICES[0], False)
        self.verify_device_list_status(self.DLB_DEVICES[1], True)

        # Check if dlb2 driver is loaded
        cmd_timeout = self._common_content_configuration.get_command_timeout()
        if self.DLB2_DRIVER_NAME not in self.os.execute("lsmod", cmd_timeout, self.ROOT_FOLDER).stdout:
            self._log.info("dlb2 driver is not running. Please ensure you have the dlb driver installed.")

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
    sys.exit(Framework.TEST_RESULT_PASS if InBandProvisioningUniqueFeaturesToMultiSocketTest.main()
             else Framework.TEST_RESULT_FAIL)