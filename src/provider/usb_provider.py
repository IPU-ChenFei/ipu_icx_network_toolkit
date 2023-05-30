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
import datetime
import re
import os
from importlib import import_module
from abc import ABCMeta, abstractmethod
from six import add_metaclass

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib import content_exceptions

from src.lib.cbnt_constants import LinuxOsTypes
from src.lib.windows_event_log import WindowsEventLog
from src.provider.base_provider import BaseProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.install_collateral import InstallCollateral
from src.provider.storage_provider import StorageProvider


@add_metaclass(ABCMeta)
class USBProvider(BaseProvider):
    """Provides USB driver provider"""

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new USB Provider object.

        :param log: Logger object to use for output messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration
        options for execution environment
        :param os_obj: os object
        """
        super(USBProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._sut_os = self._os.os_type
        self._common_content_lib = CommonContentLib(log, os_obj, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self.execution_timeout = self._common_content_configuration.get_command_timeout()
        self.install_collateral = InstallCollateral(self._log, self._os, self._cfg_opts)
        self._storage_provider = StorageProvider.factory(self._log, self._os, cfg_opts)  # type: StorageProvider

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        """
        package = r"src.provider.usb_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "WindowsUSBDriver"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "LinuxUSBDriver"
        else:
            raise NotImplementedError("Test is not implemented for %s" % os_obj.os_type)
        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(log, cfg_opts, os_obj)

    @abstractmethod
    def verify_hub_bcd_value(self):
        """
        Retrieves the hub details connected to the SUT and compares the bcd value retrieved from content configuration
        with actual hub bcd value

        :raise: content_exceptions.TestFail if bcd value of hub actual and configuration does not match.
        :return: None
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def get_device_details(self, device_name=None):
        """
        Retrieves the device details connected to the SUT

        :param: device_name name of the device
        :return: device connected details.
        :raise: content_exceptions.TestFail when no device detected.
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def verify_device_bcd_value(self, device_name, device_bcd_parm):
        """
        Compares the bcd value retrieved from content configuration with actual mouse/keyboard bcd value

        :param: device_name name of the device whose bcd value to be compared with configuration file
        :param: device_bcd_param bcd key value for specific device
        :raise: content_exceptions.TestFail if bcd value of device actual and configuration
        does not match.
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def verify_usb_key_bcd_value(self):
        """
        Retrieves the usb key details connected to the SUT and compares the bcd value retrieved from content
        configuration with actual usb key bcd value

        :return: None
        :raise: content_exceptions.TestFail if bcd value of usb key actual and configuration
        does not match.
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def verify_hdd_bcd_value(self):
        """
        Retrieves the hdd details connected to the SUT and compares the bcd value retrieved from content
        configuration with actual hdd bcd value

        :return: None
        :raise: content_exceptions.TestFail if bcd value of hdd actual and configuration does not match or
         HDD is not connected
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def install_loopback_driver(self):
        """
        Install Loopback driver on Windows

        :raise: content_exceptions.TestFail if loopback driver is not found or unsuccessful
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def execute_passmark_loopback(self, mode="Loopback", endpoint="Bulk", time_duration=30):
        """
        Install USB3Console for use in conjunction with Passmark’s USB3 test device
        Command line usage :- USB3Console.exe -h --help

        :param: mode Specifies the test mode. "LOOPBACK" or "BENCHMARK". Default value: LOOPBACK
        :param: endpoint Specifies the endpoint type. "BULK" or "ISO" or "INT". Default value: BULK
        :param: time_duration Specifies the test duration in seconds. Default value: 30 seconds
        :raise: content_exceptions.TestSetupError if loopback device is not found or
                                   TestFail if any error occurred during the test
        :return: Output of Loopback Test
        """
        raise content_exceptions.TestNotImplementedError


class WindowsUSBDriver(USBProvider):
    """Windows USB provider"""
    C_DRIVE_PATH = "C:\\"
    WIN_64 = "\\x64"
    EXPECTED_DEVICES = ["mouse", "Keyboard", "Disk drive", "USB Root Hub"]
    SET_FOR_PATH_USB = "set PATH=%PATH%;"
    DEV_CONNECTED_LOG_PATH = "UsbTreeView.exe -R:usb_dev_connected.log"
    LOG_FILE_PATH = "\\usb_dev_connected.log"
    DEVICE_KEYWORDS = '(Port Chain|Usb300|Child Device)'
    CHECK_DEVICE_CAPABILITIES = "wmic diskdrive get Capabilities"
    DISK_DRIVE = "Disk drive"
    USB_2 = "0 (no)"
    USB_3 = "1 (yes)"
    CONNECTED_DEVICES = []
    ACTUAL_DEVICES = []
    ACCESSIBLE = "3"
    WRITABLE = "4"
    LOOPBACK_DRIVER_FOLDER = "usb3loopdriver_1.2.3.zip"
    LOOPBACK_DRIVER_NAME = "cyusb3.inf"
    USB3_CONSOLE_FOLDER = "USB3Console_1.0.1004.zip"
    WIN_SEARCH_CMD = "powershell.exe (get-childitem '{}' -File {} -recurse).fullname"
    PNP_INSTALL_DRIVER_CMD = "pnputil /add-driver {} /install"
    WIN_10 = "win7-8-10{}".format(WIN_64)
    USB3_CONSOLE = "USB3Console.exe"
    FIND_LOOPBACK_DEVICE = "{} -f".format(USB3_CONSOLE)
    TEST_CMD = "{} -d {} -m {} -e {} -t {}"
    LOOPBACK_ERROR_STR = "Error: Device not found."
    LOW_ERROR_COUNT = "Low-Level Error Count=0"
    HIGH_ERROR_COUNT = "High-Level Error Count=0"
    MODE = ["LOOPBACK", "BENCHMARK"]
    END_POINT = ["BULK", "ISO", "INT"]
    SYSTEM_LOG = "System"
    SOURCES = ["*Loopback*"]

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new Windows USB Provider object.

        :param log: Logger object to use for output messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration
        :param os_obj: os object
        """
        super(WindowsUSBDriver, self).__init__(log, cfg_opts, os_obj)
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self.log_dir = self._common_content_lib.get_log_file_dir()
        self.event_log = WindowsEventLog(log, os_obj)

    def verify_hub_bcd_value(self):
        """
        Retrieves the hub details connected to the SUT and compares the bcd value retrieved from content configuration
        with actual hub bcd value

        :raise: content_exceptions.TestFail if bcd value of hub actual and configuration does not match.
        :return: None
        """
        raise NotImplementedError("get hub details not implemented for windows")

    def get_device_details(self, device_name=None):
        """
        Retrieves the devices details connected to the SUT

        :param: device_name name of the device
        :return: device connected details.
        :raise: content_exceptions.TestFail when no or expected device not detected.
        """
        self.verify_usb_device_details()

    def verify_device_bcd_value(self, device_name, device_bcd_parm):
        """
        Compares the bcd value retrieved from content configuration with actual mouse/keyboard bcd value

        :param: device_name name of the device whose bcd value to be compared with configuration file
        :param: device_bcd_param bcd key value for specific device
        :raise: content_exceptions.TestFail if bcd value of device actual and configuration
        does not match.
        """
        raise NotImplementedError("Verify bcd value for device not implemented for windows")

    def verify_usb_key_bcd_value(self):
        """
        Retrieves the usb key details connected to the SUT and compares the bcd value retrieved from content
        configuration with actual usb key bcd value

        :return: None
        :raise: content_exceptions.TestFail if bcd value of usb key actual and configuration
        does not match.
        """
        raise NotImplementedError("Verify bcd value for usb key not implemented for windows")

    def get_usb_device_details(self):
        """
        Generate usbtreeview log file and copy to host from sut

        :return: log file name
        """
        self._log.info("Copying zip USBTREE file to SUT and "
                       "Execute USBTREE.exe file to get details of USB devices")
        self.zip_file = self.install_collateral.download_and_copy_zip_to_sut(self.install_collateral.USBTREEVIEW,
                                                                      self.install_collateral.USBTREEVIEW_ZIP_FILE)
        self._os.execute(self.DEV_CONNECTED_LOG_PATH, timeout=self._command_timeout, cwd=self.zip_file)
        log_file = self.zip_file + self.LOG_FILE_PATH
        self._log.info("Copying USBTREE log files from SUT to local")
        self._os.copy_file_from_sut_to_local(log_file, os.path.join(self.log_dir, os.path.split(log_file)[-1]))
        return log_file

    def verify_usb_device_details(self):
        """
        Parse the generated usbtreeview log file and verify device are enumerated, writable and usb port is 3.0
        as expected

        :raise: content_exceptions.TestFail when no device are enumerated or not writable or usb port is not 3.0.
        """
        log_file = self.get_usb_device_details()
        check_devices = re.compile(self.DEVICE_KEYWORDS)
        self._log.info("Parsing the USBTREE log file to check the connected devices.")
        for line in open(os.path.join(self.log_dir, os.path.split(log_file)[-1]), encoding="utf-16"):
            if check_devices.findall(line):
                connected_device = line.split(":", 1)
                self.CONNECTED_DEVICES.append(connected_device)

        self._log.info("Checking the devices that are connected are as expected.")
        for no_of_devices in range(len(self.CONNECTED_DEVICES)):
            for expected_device in self.EXPECTED_DEVICES:
                if expected_device in self.CONNECTED_DEVICES[no_of_devices][1]:
                    self.ACTUAL_DEVICES.append(expected_device)
                    self._log.info("Checking if the connected devices are expected devices")
                    if self.CONNECTED_DEVICES[no_of_devices + 1][1].strip() == self.USB_2 or \
                            self.CONNECTED_DEVICES[no_of_devices + 1][1].strip() == self.USB_3:
                        self.ACTUAL_DEVICES.append(self.CONNECTED_DEVICES[no_of_devices + 1][1].strip())
                        self._log.info(self.ACTUAL_DEVICES)
                else:
                    continue
        for expected_device in self.EXPECTED_DEVICES:
            if expected_device not in self.ACTUAL_DEVICES:
                raise content_exceptions.TestFail("Connected devices are not expected or usb port is not 3.0")

    def check_devices_writable(self):
        """
        Check the diskdrives are writable
        :raise: content_exceptions.TestFail when diskdrives are not writable.
        """
        self._log.info("Check if the USB disk drive are writable")
        for expected_device in self.EXPECTED_DEVICES:
            if expected_device == self.DISK_DRIVE:
                command_result = self._os.execute(self.CHECK_DEVICE_CAPABILITIES,
                                                  timeout=self._command_timeout, cwd=self.C_DRIVE_PATH)
                device_write_check = []
                for access_rights in command_result.stdout.split('\n'):
                    if access_rights.strip():
                        device_write_check.append(access_rights)
                self._log.debug("List containing disk writable details {}".format(device_write_check[1:]))
                for access_rights in device_write_check[1:]:
                    if self.ACCESSIBLE in access_rights and self.WRITABLE in access_rights:
                        self._log.info("Devices on hub function are as expected, accessible and writable in system.")
                    else:
                        raise content_exceptions.TestFail("Devices are not writable {}".format(access_rights))

    def verify_hdd_bcd_value(self):
        """
        Retrieves the hdd details connected to the SUT and compares the bcd value retrieved from content
        configuration with actual hdd bcd value

        :return: None
        :raise: content_exceptions.TestFail if bcd value of hdd actual and configuration does not match or
         HDD is not connected
        """
        raise NotImplementedError("Verify bcd value for hdd not implemented for windows")

    def install_loopback_driver(self):
        """
        Install Loopback driver on Windows

        :raise: content_exceptions.TestFail if loopback driver is not found or unsuccessful
        """
        self._log.info("Copying Loopback Driver tool to SUT")
        self.install_collateral.download_and_copy_zip_to_sut(os.path.splitext(os.path.basename(self.LOOPBACK_DRIVER_FOLDER))[0],
                                                      os.path.basename(self.LOOPBACK_DRIVER_FOLDER))

        cmd = self.WIN_SEARCH_CMD.format(self.C_DRIVE_PATH, self.LOOPBACK_DRIVER_NAME)
        search_output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout)
        self._log.debug("File directory path is {}".format(search_output))
        if not search_output.strip():
            raise content_exceptions.TestFail("Could not find {} on SUT".format(self.LOOPBACK_DRIVER_NAME))
        driver_path = ''
        for each_path in search_output.split("\n"):
            if self.WIN_10 in each_path:
                driver_path = each_path.strip()
                break

        self._log.info("Installing loopback driver {}".format(self.LOOPBACK_DRIVER_NAME))
        install_cmd_output = self._os.execute(self.PNP_INSTALL_DRIVER_CMD.format(driver_path), self.execution_timeout)

        if not install_cmd_output.stdout.strip():
            self._log.error(install_cmd_output.stderr)
            self._log.debug(install_cmd_output.stdout)
            raise content_exceptions.TestFail("Loopback driver installation {} is unsuccessful".
                                              format(install_cmd_output.stdout))
        self._log.debug("Loopback driver installation {} is successful".format(install_cmd_output.stdout))

    def execute_passmark_loopback(self, mode=MODE[0], endpoint=END_POINT[0], time_duration=30):
        """
        Install USB3Console for use in conjunction with Passmark’s USB3 test device
        Command line usage :- USB3Console.exe -h --help

        :param: mode Specifies the test mode. "LOOPBACK" or "BENCHMARK". Default value: LOOPBACK
        :param: endpoint Specifies the endpoint type. "BULK" or "ISO" or "INT". Default value: BULK
        :param: time_duration Specifies the test duration in seconds. Default value: 30 seconds
        :raise: content_exceptions.TestSetupError if loopback device is not found or
                                   TestFail if any error occurred during the test
        :return: Output of Loopback Test
        """
        self._log.info("Copying USB 3 Console tool to SUT")
        usb3_tool_path = self.install_collateral.download_and_copy_zip_to_sut(
            os.path.splitext(os.path.basename(self.USB3_CONSOLE_FOLDER))[0],
            os.path.basename(self.USB3_CONSOLE_FOLDER))

        device_output = self._common_content_lib.execute_sut_cmd(self.FIND_LOOPBACK_DEVICE, "find loopback device",
                                                                 self.execution_timeout, usb3_tool_path)
        self._log.debug(device_output)
        if self.LOOPBACK_ERROR_STR in device_output:
            raise content_exceptions.TestSetupError("Passmark Loopback device not found")
        device_name = device_output.split("=")[-1].strip()
        self._log.info("Loopback device connected is : {}".format(device_name))

        self._log.info("Starting {} Testing for {}sec".format(mode, time_duration))
        cmd = self.TEST_CMD.format(self.USB3_CONSOLE, device_name, mode, endpoint, time_duration)
        output = self._common_content_lib.execute_sut_cmd(cmd, "loopback device testing", self.execution_timeout,
                                                                 usb3_tool_path)
        self._log.debug(output)
        if self.LOW_ERROR_COUNT not in output or self.HIGH_ERROR_COUNT not in output:
            raise content_exceptions.TestFail("Loopback Test Failed with below output: {}".format(output))
        self._log.info("Loop back Test executed successfully")
        return output

    def check_for_windows_error_log(self):
        """
        Check for windows event log for any errors for Loopback

        :raise: content_exceptions.TestFail if any error found in windows log
        """
        error_logs = self.event_log.get_event_logs(self.SYSTEM_LOG, self.SOURCES)
        # Check if there are any errors, warnings of category Loopback found
        if error_logs:
            raise content_exceptions.TestFail("Found errors or warnings in Windows System event log".
                                              format(str(error_logs)))
        self._log.info("No errors were generated in the Windows event log")


class LinuxUSBDriver(USBProvider):
    """Linux USB provider object"""
    REGEX_BUS_DEVICE = "Bus (\d+) Device (\d+)"
    REGEX_DEVICE_NUM = "Dev (\d+)"
    LSUSB_SPECIFIC_DEVICE = "lsusb -v -s {}:{}"
    LSUSB_TREE = "lsusb -t"
    DRIVER_STRING = "Driver=uas"
    DRIVER_STRING_CENTOS = "Driver=hub"
    BCD_STR = "bcdUSB"
    DEVICE_CLASS = "bDeviceClass"
    INTERFACE_CLASS = "bInterfaceClass"
    INTERFACE_PROTOCOL = "bInterfaceProtocol"
    I_PRODUCT = "iProduct"
    DEVICE_CLASS_STR = "Hub"
    INTERFACE_CLASS_STR = "8 Mass Storage"
    USB_NAME = "name"
    MOUSE = "Mouse"
    USB_BCD = "bcd"
    HUB_BCD = "bcd_hub"
    MOUSE_BCD = "bcd_mouse"
    KEYBOARD_BCD = "bcd_keyboard"
    USB_KEY_BCD = "bcd_usb_key"
    HDD_BCD = "bcd_hdd"
    HDD_BCD_CENTOS = "bcd_hdd_centos"
    KEYBOARD = "Keyboard"
    LSBLK_CMD = "lsblk --nodeps --output NAME,TRAN,RM"
    HDPARM_CMD = cmd = "hdparm -I /dev/{}"
    WRITE_CACHE_STR = "Write cache"
    USB_STR = "usb"
    RM_ID = "0"
    MODEL = "Model"
    SERIAL = "Serial"
    GREP = " | grep "
    SUCESS_STR = "Writing superblocks and filesystem accounting information"

    FINDMNT_CMD = "findmnt -lo source,target"
    UMOUNT_CMD = "umount {}"
    RM_CMD = "rm -rf {}"
    FORMAT_CMD = "printf 'y' | mkfs -t ext4 /dev/{}"
    HDD_MOUNT_POINT = "/media/hdd"
    MKDIR_CMD = "mkdir {}"
    MOUNT_CMD = "mount /dev/{} {}"
    FAILURE_STR = "fallocate failed"
    FALOCATE_CMD = "fallocate -l 50G 50Gigfile"
    BULK_FILE = "/50Gigfile"

    def __init__(self, log, cfg_opts, os_obj):
        super(LinuxUSBDriver, self).__init__(log, cfg_opts, os_obj)
        self.usb_set_time = self._common_content_configuration.get_usb_set_time_delay()
        self.usb_device_connected = self._common_content_configuration.get_usb_device()

    def verify_hub_bcd_value(self):
        """
        Retrieves the hub details connected to the SUT and compares the bcd value retrieved from content configuration
        with actual hub bcd value

        :raise: content_exceptions.TestFail if bcd value of hub actual and configuration does not match.
        :return: True, if bcdusb value matched the configuration file
        """
        self._log.info("Checking hub details")
        device_dict = {}
        device_connected = self._storage_provider.get_usb_details()
        for line in device_connected.split("\n"):
            out_val = re.search(self.REGEX_BUS_DEVICE, line.strip())
            if not out_val:
                raise content_exceptions.TestFail("Unable to get usb hub info")
            cmd = self.LSUSB_SPECIFIC_DEVICE.format(out_val.group(1), out_val.group(2))
            self._log.debug("Bus device cmd {}".format(cmd))
            cmd_output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout)
            self._log.debug("Lsusb -s command output %s" % cmd_output.strip())

            for usb_device in cmd_output.strip().split("\n"):
                if usb_device.strip() and self.BCD_STR in usb_device:
                    device_dict[self.HUB_BCD] = float(usb_device.partition(self.BCD_STR)[-1].strip())
                elif usb_device.strip() and self.DEVICE_CLASS in usb_device:
                    device_dict[self.DEVICE_CLASS] = usb_device.split(" ")[-1].strip()
            self._log.debug("Usb connected device bcd value and class {}".format(device_dict))
            if device_dict[self.HUB_BCD] == float(self.usb_device_connected.get(self.HUB_BCD)) and \
                    device_dict[self.DEVICE_CLASS] == self.DEVICE_CLASS_STR:
                self._log.info("Hub bcd value {} detected".format(self.usb_device_connected.get(self.HUB_BCD)))
                return True

        raise content_exceptions.TestFail("Bcd value of Hub did not match {} ".
                                          format(self.usb_device_connected.get(self.HUB_BCD)))

    def get_device_details(self, device_name=None):
        """
        Retrieves the device details connected to the SUT

        :param: device_name name of the device
        :return: device connected details.
        :raise: content_exceptions.TestFail when no device detected.
        """
        cmd_output = ''
        device_connected = self._storage_provider.get_usb_details()
        for line in device_connected.split("\n"):
            if re.search(device_name, line.strip()):
                out_val = re.search(self.REGEX_BUS_DEVICE, line.strip())
                if not out_val:
                    raise content_exceptions.TestFail("Unable to get {} connected info".format(device_name))
                self._log.info("{} is accessible".format(device_name))
                cmd = self.LSUSB_SPECIFIC_DEVICE.format(out_val.group(1), out_val.group(2))
                self._log.info("Command {} for {}".format(cmd, device_name))
                cmd_output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout)
                self._log.debug("Lsusb -s command output %s" % cmd_output.strip())
        return cmd_output.strip()

    def verify_device_bcd_value(self, device_name, device_bcd_parm):
        """
        Compares the bcd value retrieved from content configuration with actual mouse/keyboard bcd value

        :param: device_name name of the device whose bcd value to be compared with configuration file
        :param: device_bcd_param bcd string specific device
        :raise: content_exceptions.TestFail if bcd value of device actual and configuration
        does not match.
        """
        self._log.info("Checking {} details".format(device_name))
        device_dict = {}
        device_connected = self._storage_provider.get_usb_details()
        for line in device_connected.split("\n"):
            out_val = re.search(self.REGEX_BUS_DEVICE, line.strip())
            if not out_val:
                raise content_exceptions.TestFail("Unable to get {} info".format(device_name))
            cmd = self.LSUSB_SPECIFIC_DEVICE.format(out_val.group(1), out_val.group(2))
            self._log.debug("Bus device cmd {}".format(cmd))
            cmd_output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout)
            self._log.debug("Lsusb -s command output %s" % cmd_output.strip())

            interface_protocol_list = []
            for usb_device in cmd_output.strip().split("\n"):
                if usb_device.strip() and self.BCD_STR in usb_device:
                    device_dict[device_bcd_parm] = float(usb_device.partition(self.BCD_STR)[-1].strip())
                elif usb_device.strip() and self.INTERFACE_PROTOCOL in usb_device:
                    if self.INTERFACE_PROTOCOL in device_dict.keys():
                        interface_protocol_list.append(usb_device.split(" ")[-1].strip())
                        device_dict[self.INTERFACE_PROTOCOL] = interface_protocol_list
                    else:
                        interface_protocol_list = [usb_device.split(" ")[-1].strip()]
                        device_dict[self.INTERFACE_PROTOCOL] = interface_protocol_list
                elif usb_device.strip() and self.I_PRODUCT in usb_device:
                    device_dict[self.I_PRODUCT] = usb_device.partition(self.I_PRODUCT)[-1].strip()
            self._log.debug("Usb connected device bcd value and class {}".format(device_dict))
            if device_dict[device_bcd_parm] == float(self.usb_device_connected.get(device_bcd_parm)) and \
                    device_name in device_dict[self.INTERFACE_PROTOCOL] and \
                    device_name in device_dict[self.I_PRODUCT]:
                self._log.info("{} is accessible and bcd value is {}".format(device_name, self.usb_device_connected.get(
                device_bcd_parm)))
            return True
        raise content_exceptions.TestFail("Bcd value of {} did not match expected bcd value{} ".
                                          format(device_name, self.usb_device_connected.get(device_bcd_parm)))

    def verify_usb_key_bcd_value(self):
        """
        Retrieves the usb key details connected to the SUT and compares the bcd value retrieved from content
        configuration with actual usb key bcd value

        :return: True, if bcdusb value matched the configuration file
        :raise: content_exceptions.TestFail if bcd value of usb key actual and configuration
        does not match.
        """
        self._log.info("Checking usb key details")
        device_dict = {}
        device_connected = self._storage_provider.get_usb_details()
        for line in device_connected.split("\n"):
            out_val = re.search(self.REGEX_BUS_DEVICE, line.strip())
            if not out_val:
                raise content_exceptions.TestFail("Unable to get usb key info")
            cmd = self.LSUSB_SPECIFIC_DEVICE.format(out_val.group(1), out_val.group(2))
            self._log.debug("Bus device cmd {}".format(cmd))
            cmd_output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout)
            self._log.debug("Lsusb -s command output %s" % cmd_output.strip())

            for usb_device in cmd_output.strip().split("\n"):
                if usb_device.strip() and self.BCD_STR in usb_device:
                    device_dict[self.USB_KEY_BCD] = float(usb_device.partition(self.BCD_STR)[-1].strip())
                elif usb_device.strip() and self.INTERFACE_CLASS in usb_device:
                    device_dict[self.INTERFACE_CLASS] = usb_device.partition(self.INTERFACE_CLASS)[-1].strip()
            self._log.info("Usb connected device bcd value and class {}".format(device_dict))
            if device_dict[self.USB_KEY_BCD] == float(self.usb_device_connected.get(self.USB_KEY_BCD)) and \
                    device_dict[self.INTERFACE_CLASS] == self.INTERFACE_CLASS_STR:
                self._log.info("Usb key is accessible and bcd value is {}".format(self.usb_device_connected.get(
                    self.USB_KEY_BCD)))
                return True

        raise content_exceptions.TestFail("Bcd value of usb key did not match expected bcd value{} ".
                                          format(self.usb_device_connected.get(self.USB_KEY_BCD)))

    def verify_hdd_bcd_value(self):
        """
        Retrieves the hdd details connected to the SUT and compares the bcd value retrieved from content
        configuration with actual hdd bcd value

        :return: True, if bcdusb value matched the configuration file
        :raise: content_exceptions.TestFail if bcd value of hdd actual and configuration does not match or
         HDD is not connected
        """
        global hdd_key
        self._log.info("Checking hdd details")
        device_num = ''
        device_dict = {}
        device_connected = self._storage_provider.get_usb_details()
        cmd_output = self._common_content_lib.execute_sut_cmd(self.LSUSB_TREE, self.LSUSB_TREE, self.execution_timeout)
        for line in cmd_output.split("\n"):
            if self.DRIVER_STRING in line.strip() or self.DRIVER_STRING_CENTOS in line.strip():
                out_val = re.search(self.REGEX_DEVICE_NUM, line.strip())
                device_num = out_val.group(1)

        if self._os.os_subtype == LinuxOsTypes.CENTOS:
            hdd_key = self.HDD_BCD_CENTOS
        if self._os.os_subtype == LinuxOsTypes.RHEL:
            hdd_key = self.HDD_BCD
        for line in device_connected.split("\n"):
            out_put = re.search(self.REGEX_BUS_DEVICE, line.strip())
            if out_put:
                if int(device_num) == int(out_put.group(2)):
                    cmd = self.LSUSB_SPECIFIC_DEVICE.format(out_put.group(1), out_put.group(2))
                    self._log.debug("Bus device cmd {}".format(cmd))
                    cmd_output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout)
                    self._log.debug("Lsusb -s command output %s" % cmd_output.strip())
                    for usb_device in cmd_output.strip().split("\n"):
                        if usb_device.strip() and self.BCD_STR in usb_device:
                            device_dict[hdd_key] = float(usb_device.partition(self.BCD_STR)[-1].strip())

                    self._log.info("Usb connected device bcd value {}".format(device_dict))
                    if device_dict[hdd_key] != float(self.usb_device_connected.get(hdd_key)):
                        raise content_exceptions.TestFail("Bcd value of HDD did not match {} ".
                                                          format(self.usb_device_connected.get(hdd_key)))
                    self._log.info("HDD bcd value {} detected".format(self.usb_device_connected.get(hdd_key)))
                    return True
        raise content_exceptions.TestFail("HDD not connected!!!")

    def get_hdd_drive_path_in_sut(self):
        """
        Return the drive path of the HDD connected in the system.

        :return: Required drive
        """
        required_drive = ''
        cmd_output = self._common_content_lib.execute_sut_cmd(self.LSBLK_CMD, self.LSBLK_CMD, self.execution_timeout)
        self._log.debug("Output of the command {} is {}".format(self.LSBLK_CMD, cmd_output))
        for line in cmd_output.strip().split("\n"):
            rm_list = []
            for each in line.strip().split(" "):
                if each:
                    rm_list.append(each)
            if rm_list[1] == self.USB_STR and rm_list[2] == self.RM_ID:
                required_drive = rm_list[0]
        return required_drive

    def copy_bulk_file_to_hdd(self):
        """
        Check the diskdrives are writable and copy a 50GB bulk file into HDD

        :raise: content_exceptions.TestFail when diskdrives are not writable.
        """
        # Get the path of Required HDD drive
        required_drive = self.get_hdd_drive_path_in_sut()
        mounted_dev_list = self._common_content_lib.execute_sut_cmd(self.FINDMNT_CMD, self.FINDMNT_CMD,
                                                                    self.execution_timeout)
        mount_point = ""
        for each in mounted_dev_list.split("\n"):
            if "/dev/{}".format(required_drive) in each:
                mount_point = re.findall(r"/dev/{}\s+(\S+)".format(required_drive), each)[0]
                self._log.info("Found a mount device {} on the required drive {}".format(mount_point, required_drive))

        if mount_point:
            self._common_content_lib.execute_sut_cmd(self.UMOUNT_CMD.format(mount_point),
                                                     self.UMOUNT_CMD.format(mount_point), self.execution_timeout)
            self._common_content_lib.execute_sut_cmd(self.RM_CMD.format(mount_point), self.RM_CMD.format(mount_point),
                                                     self.execution_timeout)
        format_cmd_output = self._common_content_lib.execute_sut_cmd(self.FORMAT_CMD.format(required_drive),
                                                                     self.FORMAT_CMD.format(required_drive),
                                                                     self.execution_timeout)
        success = False
        for each in format_cmd_output.split("\n"):
            if self.SUCESS_STR in each.strip():
                self._log.info(each)
                self._log.info("HDD Format Successfull")
                success = True
        if not success:
            raise content_exceptions.TestFail("HDD Format Failed")
        self._common_content_lib.execute_sut_cmd(self.RM_CMD.format(self.HDD_MOUNT_POINT),
                                                 self.RM_CMD.format(self.HDD_MOUNT_POINT), self.execution_timeout)
        self._common_content_lib.execute_sut_cmd(self.MKDIR_CMD.format(self.HDD_MOUNT_POINT),
                                                 self.MKDIR_CMD.format(self.HDD_MOUNT_POINT), self.execution_timeout)
        self._common_content_lib.execute_sut_cmd(self.MOUNT_CMD.format(required_drive, self.HDD_MOUNT_POINT),
                                                 self.MOUNT_CMD.format(required_drive, self.HDD_MOUNT_POINT),
                                                 self.execution_timeout)

        # Create a 50GB file locally
        fallocate_cmd_output = self._common_content_lib.execute_sut_cmd(self.FALOCATE_CMD, self.FALOCATE_CMD,
                                                                        self.execution_timeout)
        if self.FAILURE_STR in fallocate_cmd_output:
            raise content_exceptions.TestFail("50GB file creation Failed")
        cmd_output = self._common_content_lib.execute_sut_cmd("pwd", "pwd",
                                                              self.execution_timeout)
        bulk_file_path = cmd_output.strip() + self.BULK_FILE
        cp_cmd = "cp {} {}".format(bulk_file_path, self.HDD_MOUNT_POINT)

        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")

        # copying file from OS to HDD
        self._log.info("Started copying the 50GB file from OS to HDD , current time : {}".format(current_time))
        self._common_content_lib.execute_sut_cmd(cp_cmd, cp_cmd, self.execution_timeout)
        later = datetime.datetime.now()
        post_copy_time = later.strftime("%H:%M:%S")
        self._log.info("Time after copying the 50GB file from OS to HDD , current time : {}".format(post_copy_time))
        self._log.info("Total Time taken to copy 50GB file from OS to HDD is {}".format(later - now))
        if not later - now <= datetime.timedelta(minutes=7):
            raise content_exceptions.TestFail("50GB file copy took more than 7 minutes")
        if not self._os.check_if_path_exists(self.HDD_MOUNT_POINT + self.BULK_FILE):
            raise content_exceptions.TestFail("50GB file copy Failed")
        self._log.info("Successfully copied the 50GB file from OS to the USB3.0 HDD in {} Minutes".format(later - now))

    def check_devices_writable(self):
        """
        Check the diskdrives are writable
        :raise: content_exceptions.TestFail when diskdrives are not writable.
        """
        required_drive = ''
        self._log.info("Checking hdd is writable")
        cmd_output = self._common_content_lib.execute_sut_cmd(self.LSBLK_CMD, self.LSBLK_CMD, self.execution_timeout)
        self._log.debug("Output of the command {} is {}".format(self.LSBLK_CMD, cmd_output))
        for line in cmd_output.strip().split("\n"):
            rm_list = []
            for each in line.strip().split(" "):
                if each:
                    rm_list.append(each)
            if rm_list[1] == self.USB_STR and rm_list[2] == self.RM_ID:
                required_drive = rm_list[0]
        cmd = self.HDPARM_CMD.format(required_drive)
        cmd_out = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout)
        self._log.debug("Output of the command {} is {}".format(self.HDPARM_CMD, cmd_out))
        hdd_model_number = self._common_content_configuration.hdd_model_number()
        model_cmd = self.HDPARM_CMD.format(required_drive) + self.GREP + self.MODEL
        model_number = self._common_content_lib.execute_sut_cmd(model_cmd, model_cmd, self.execution_timeout)
        model_number = model_number.split(":")[1].strip()
        if hdd_model_number == str(model_number):
            self._log.info("HDD Model Number is {} and Matches with HDD".format(model_number))
        else:
            raise content_exceptions.TestFail("HDD Model Number does not match as per the specification")

        hdd_serial_number = self._common_content_configuration.hdd_serial_number()
        serial_cmd = self.HDPARM_CMD.format(required_drive) + self.GREP + self.SERIAL
        serial_number = self._common_content_lib.execute_sut_cmd(serial_cmd, serial_cmd, self.execution_timeout)
        serial_number = serial_number.split(":")[1].strip().split("\n")[0]
        if hdd_serial_number == serial_number:
            self._log.info("HDD Serial Number is {} and Matches".format(serial_number))
        else:
            raise content_exceptions.TestFail("HDD Serial Number does not match as per the specification")

        for line in cmd_out.strip().split("\n"):
            if line.strip().startswith('*'):
                if self.WRITE_CACHE_STR in line.strip():
                    self._log.info("Hard Disk Drive is writable")
                    return True
        raise content_exceptions.TestFail("Hard Disk Drive is not writable")

    def install_loopback_driver(self):
        """
        Install Loopback driver on Windows

        :raise: content_exceptions.TestFail if loopback driver is not found or unsuccessful
        """
        raise NotImplementedError("Installation of loopback driver not implemented for Linux")

    def execute_passmark_loopback(self, mode="Loopback", endpoint="Bulk", time_duration=30):
        """
        Install USB3Console for use in conjunction with Passmark’s USB3 test device
        Command line usage :- USB3Console.exe -h --help

        :param: mode Specifies the test mode. "LOOPBACK" or "BENCHMARK". Default value: LOOPBACK
        :param: endpoint Specifies the endpoint type. "BULK" or "ISO" or "INT". Default value: BULK
        :param: time_duration Specifies the test duration in seconds. Default value: 30 seconds
        :raise: content_exceptions.TestSetupError if loopback device is not found or
                                   TestFail if any error occurred during the test
        :return: Output of Loopback Test
        """
        raise NotImplementedError("Execution of loopback driver not implemented for Linux")


