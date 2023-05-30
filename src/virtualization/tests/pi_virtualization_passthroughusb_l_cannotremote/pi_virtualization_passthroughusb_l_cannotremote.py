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
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.exceptions import OsStateTransitionException

from src.provider.vm_provider import VMs
from src.lib.content_exceptions import *
from src.virtualization.virtualization_common import VirtualizationCommon
from src.provider.storage_provider import StorageProvider
from src.provider.copy_usb_provider import UsbRemovableDriveProvider
from src.lib.common_content_lib import CommonContentLib


class PiVirtualizationPassthroughUsbLCannotRemote(VirtualizationCommon):
    """
    HPALM ID: 79623- PI_Virtualization_PassThroughUSB_L_CannotRemote
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Create VM.
    2. Verify VM is running.
    3. Hotplug USB drive.
    4. attach the usb drive to VM.
    5. Copy file to attached usb drive in VM
    6. detach it from VM.
    7. Hotunplug usb drive from SUT
    """
    TC_ID = ["H79623-PI_Virtualization_PassThroughUSB_L_CannotRemote"]
    VM = [VMs.RHEL]
    USB_TYPE = "type"
    USB_BCD = "bcd"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiVirtualizationPassthroughUsbLCannotRemote object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiVirtualizationPassthroughUsbLCannotRemote, self).__init__(test_log, arguments, cfg_opts)
        self._storage_provider = StorageProvider.factory(self._log, self.os, cfg_opts)  # type: StorageProvider
        self.usb_set_time = self._common_content_configuration.get_usb_set_time_delay()
        self.usb_connected = self._common_content_configuration.get_usb_device()
        self._cfg_opt = cfg_opts

    def execute(self):
        """
        1. Create VM.
        2. Verify VM is running.
        3. Hotplug USB drive.
        4. attach the usb drive to VM.
        5. Copy file to attached usb drive in VM
        6. detach it from VM.
        7. Hotunplug usb drive from SUT
        """
        # Hotplugging USB drive
        self._log.info("USB disconnecting")
        self.phy.disconnect_usb(self.usb_set_time)
        usb_detail_before = self._storage_provider.get_usb_details()
        self._log.debug("Output before usb connect {}".format(usb_detail_before))
        self._log.info("USB connecting")
        self.phy.connect_usb_to_sut(self.usb_set_time)
        time.sleep(self.usb_set_time)
        usb_detail_after = self._storage_provider.get_usb_details()
        self._log.debug("Output after usb connect {}".format(usb_detail_after))
        difference = self.get_lsusb_difference(usb_detail_before, usb_detail_after)
        self._log.debug("Connected USB device bus information : {}".format(difference))
        device_connected = self._storage_provider.get_bus_device_type_info(difference)
        self._log.debug('Connected USB bcd and type data : {}'.format(device_connected))
        self.verify_hotplug_device_status(device_connected, self.usb_connected)
        device_connected_data = self._storage_provider.get_vendor_id_product_id(difference)
        self._log.debug('Connected USB  idVendor and idProduct : {}'.format(device_connected_data))
        for index in range(len(self.VM)):
            # create VM names dynamically according to the OS
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            # if VM exists with the domain name then we are getting error Example :Guest name 'RHEL_0' is already in use
            # So checking VM exists or not. If VM is available then destroying the VM.
            self._vm_provider.destroy_vm(vm_name)
            self.create_vm(vm_name, self.VM[index], mac_addr=True)
            self.verify_vm_functionality(vm_name, self.VM[index])
            vm_os_obj = self.create_vm_host(vm_name, self.VM[index])
            storage_provider_vm = StorageProvider.factory(self._log, vm_os_obj, self._cfg_opt)
            vm_usb_detail_before = storage_provider_vm.get_usb_details()
            self._log.debug("Output before usb connect to VM {}".format(vm_usb_detail_before))
            self._vm_provider.attach_usb_device_to_vm(device_connected_data, vm_name)
            # wait time to attach USB to the VM
            time.sleep(self.usb_set_time)
            vm_usb_detail_after = storage_provider_vm.get_usb_details()
            self._log.debug("Output after usb connect to VM {}".format(vm_usb_detail_after))
            self.get_lsusb_difference(vm_usb_detail_before, vm_usb_detail_after)
            self._log.info("Successfully verified the USB device is attached with the VM {}".format(vm_name))
            self.copy_file_to_vm_usb(vm_os_obj)
            self._log.info("Restarting the VM {}".format(vm_name))
            # After issuing the reboot command VM coming to OS with in 20 seconds.
            try:
                vm_os_obj.reboot(self.reboot_timeout)
            except OsStateTransitionException:
                self._log.info("After issuing the reboot command VM coming to OS with in 20 seconds.")
            self._log.info("VM {} came back to OS after restart".format(vm_name))
            self.copy_file_to_vm_usb(vm_os_obj)
            vm_usb_detail_before = storage_provider_vm.get_usb_details()
            self._log.debug("Output before usb disconnect to VM {}".format(vm_usb_detail_before))
            self._vm_provider.detach_usb_device_from_vm(vm_name)
            # wait time to detach USB from the VM
            time.sleep(self.usb_set_time)
            vm_usb_detail_after = storage_provider_vm.get_usb_details()
            self._log.debug("Output after usb connect to VM {}".format(vm_usb_detail_after))
            self.get_lsusb_difference(vm_usb_detail_before, vm_usb_detail_after, action="unplug")
            self._log.info("Successfully verified the USB device is detached with the VM {}".format(vm_name))
        usb_detail_before = self._storage_provider.get_usb_details()
        self._log.debug("Output after usb disconnect {}".format(usb_detail_before))
        self._log.info("USB disconnecting")
        self.phy.disconnect_usb(self.usb_set_time)
        usb_detail_after = self._storage_provider.get_usb_details()
        self._log.debug("Output after usb disconnect {}".format(usb_detail_after))
        self.get_lsusb_difference(usb_detail_before, usb_detail_after, action="unplug")
        self._log.info("Successfully UnPlug the USB device")

        return True

    def get_lsusb_difference(self, before_action, after_action, action="plug"):
        """
        Retrieves the lsusb device after hot-plug and return the difference device information which before and lsusb
        after disconnection

        :param before_action: device connected before action
        :param after_action: device connected after action
        :param action: optional param,expecting plug or unplug
        :return diff:returns the difference of device connected before and after action.
        :raise :content_exceptions.TestFail when no device detected before and after action.
        """
        diff = None
        before_set = set(before_action.strip().split("\n"))
        after_set = set(after_action.strip().split("\n"))
        if action == "plug":
            diff = ", ".join(after_set.difference(before_set))
        elif action == "unplug":
            diff = ", ".join(before_set.difference(after_set))
        else:
            raise NotImplementedError("{} action is not implemented".format(action))
        if not diff:
            raise TestFail("No device is connected after hot{}".format(action))
        return diff

    def verify_hotplug_device_status(self, hotplug_device_info, config_device_info):
        """
        Compares the device type and bcd value retrieved from content configuration with hot plugged device type and
        bcd value

        :param hotplug_device_info: device type and bcd value of hot plugged device
        :param config_device_info: device type and bcd value from configuration file
        :raise :content_exceptions.TestFail if device type and bcd value of hot plugged device and configuration
        does not match.
        """
        self._log.info("checking for hot plug device status")
        for key, value in hotplug_device_info.items():
            if key == self.USB_TYPE:
                res = [i for i in value if config_device_info.get(key).lower() in i.lower()]
                self._log.debug("Device type connected after hot plug %s" % res)
                if not res:
                    raise TestFail("No device type {} is detected after hot plug". format(
                        config_device_info.get(key)))
            elif key == self.USB_BCD:
                if not config_device_info.get(key) == value:
                    raise TestFail("{} value of the device type {} does not match after hot plug".
                                   format(key, config_device_info.get(key)))
        self._log.info("Device type : {} and bcd value : {} detected after hot plug".format(config_device_info.get(
            self.USB_TYPE), config_device_info.get(self.USB_BCD)))

    def copy_file_to_vm_usb(self, vm_os_obj):
        """
        This method is to copy the test file to VM USB from HOST

        :param vm_os_obj: os object for VM
        """
        self._log.info("Copying the Test file to VM USB")
        copy_usb = UsbRemovableDriveProvider.factory(self._log, self._cfg_opt, vm_os_obj)
        common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, None)
        vm_test_file_host_path = self._install_collateral.download_tool_to_host( self.TEST_VM_FILE_NAME)
        vm_os_obj.copy_local_file_to_sut(vm_test_file_host_path, self.ROOT_PATH)
        file_path = self.ROOT_PATH + "/" + self.TEST_VM_FILE_NAME
        copy_usb.copy_file_from_sut_to_usb(common_content_lib_vm_obj, self._common_content_configuration,
                                           file_path, vm_usb=True)
        # check file presence
        if not vm_os_obj.check_if_path_exists(file_path):
            raise TestError("Fail to verify {} file presence in VM".format(file_path))
        self._log.info("Successfully verified {} file presence in VM".format(file_path))
        self._log.info("Successfully copied the Test file to VM USB")

    def cleanup(self, return_status):  # type: (bool) -> None
        super(PiVirtualizationPassthroughUsbLCannotRemote, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiVirtualizationPassthroughUsbLCannotRemote.main()
             else Framework.TEST_RESULT_FAIL)
