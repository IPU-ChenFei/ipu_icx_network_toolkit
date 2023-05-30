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
import re
from abc import ABCMeta, abstractmethod
from importlib import import_module
from six import add_metaclass
import zipfile
import time

from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.content_configuration import ContentConfiguration
from src.lib import content_exceptions
from src.provider.base_provider import BaseProvider
from src.lib.common_content_lib import CommonContentLib
from src.provider.host_usb_drive_provider import HostUsbDriveProvider


class NetworkDrivers(object):
    JACKSONVILLE_DRIVER_NAME = "JACKSONVILLE"
    JACKSONVILLE_DRIVER_CODE = 'igc'
    FOXVILLE_DRIVER_NAME = "FOXVILLE"
    FOXVILLE_DRIVER_CODE = 'igc'
    FORTVILLE_DRIVER_NAME = "FORTVILLE"
    FORTVILLE_DRIVER_CODE = "i40e"
    COLUMBIAVILLE_DRIVER_NAME = "COLUMBIAVILLE"
    COLUMBIAVILLE_DRIVER_CODE = "ice"
    CARLSVILLE_DRIVER_CODE = "i40e"
    CARLSVILLE_DRIVER_NAME = "CARLSVILLE"
    FOXVILLE_DEVICE_ID = "DEV_15F2"
    JACKSONVILLE_DEVICE_ID = "DEV_15F4"
    FORTVILLE_DEVICE_ID = "DEV_1583"
    CARLSVILLE_DEVICE_ID = "DEV_15FF"
    COLUMBIAVILLE_DEVICE_ID = "DEV_1593"
    SFP_LOOPBACK = [FORTVILLE_DRIVER_NAME, FORTVILLE_DEVICE_ID, COLUMBIAVILLE_DRIVER_NAME, COLUMBIAVILLE_DEVICE_ID]


@add_metaclass(ABCMeta)
class DriverProvider(BaseProvider):
    """Driver provider for driver installation, un-installation and re-installation."""

    DRIVER_DEST_PATH_LINUX = "/usr/local/src"
    _DEVICE_EXECUTION_TIMEOUT = 240
    _COMMAND_TIMEOUT = 30

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new Driver Provider object.

        :param os_obj: os object
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(DriverProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._sut_os = self._os.os_type
        self._common_content_lib = CommonContentLib(log, os_obj, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self.execution_timeout = self._common_content_configuration.get_command_timeout()
        self._host_usb_provider = HostUsbDriveProvider.factory(self._log, self._cfg_opts,
                                                               self._os)  # type: HostUsbDriveProvider
        self.usb_set_time = self._common_content_configuration.get_usb_set_time_delay()
        self._command_timeout = 30

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        """
        package = r"src.provider.driver_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "WindowsDriverInstallation"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "LinuxDriverInstallation"
        else:
            raise NotImplementedError("Test is not implemented for %s" % os_obj.os_type)
        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(cfg_opts=cfg_opts, log=log, os_obj=os_obj)

    @abstractmethod
    def install_driver(self, driver_code, driver_name):
        """
        This function install driver specified

        :param driver_code: driver code
        :param driver_name: name of the driver installing.
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def uninstall_driver(self, driver_code, driver_name):
        """
        This function un-install driver specified

        :param driver_code: driver code
        :param driver_name: name of the driver installing.
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def load_driver(self, driver_code, driver_name):
        """
        This function re-install driver specified

        :param driver_code: driver code
        :param driver_name: name of the driver installing.
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def is_driver_installed(self, driver_inf_file, driver_name=None):
        """
        This method checks if particular inf file name related network driver is installed in sut.

        :param driver_inf_file: Driver inf file name
        :param driver_name: Driver Name for Linux
        :return: Returns the oem file name if driver is installed, if not returns None
        """
        raise content_exceptions.TestNotImplementedError

    def copy_driver_files(self, phy):
        """
        Copy the driver zip files to sut by getting the path from content configuration file.

        :param phy: physical control provider object
        """
        self._log.info("Copying network driver file to sut")
        driver_source_path = self._common_content_configuration.get_network_drivers()
        usb_drive = self._host_usb_provider.get_hotplugged_usb_drive(phy)
        self._log.debug("Hot-plugged USB drive='{}'".format(usb_drive))
        self._host_usb_provider.format_drive(usb_drive)
        self._log.debug("USB disconnecting")
        phy.disconnect_usb(self.usb_set_time)
        self._log.debug("USB connecting to HOST")
        phy.connect_usb_to_host(self.usb_set_time)
        time.sleep(15)
        self._log.debug("Copying Network Driver zip file to sut")
        with zipfile.ZipFile(driver_source_path.strip(), 'r') as zip:
            zip.extractall(usb_drive + os.sep, )
        self._log.debug("USB disconnecting")
        phy.disconnect_usb(self.usb_set_time)
        self._log.debug("USB connecting to SUT")
        phy.connect_usb_to_sut(self.usb_set_time)
        self._log.info("Network files copied successfully")

    @abstractmethod
    def get_ethernet_devices(self):
        """
        Get the Ethernet devices from the SUT

        :raise: content_exception.TestFail if not getting the Ethernet devices
        :return: ethernet_devices
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def identify_device_controller(self, ethernet_device_list, driver_code):
        """
        Identify the device controller and verify the driver code with expected driver code

        :param driver_code: driver code
        :param ethernet_device_list: Ethernet devices list
        :raise: content_exception.TestFail if not getting the driver code which is expected
        """
        raise content_exceptions.TestNotImplementedError


class WindowsDriverInstallation(DriverProvider):
    """Windows Driver Installation provider object"""
    WMIC_GETDEVICEID_CMD = "wmic path Win32_PnpEntity where 'DeviceID Like '%{}%'' get"
    WMIC_USB_CMD = "wmic logicaldisk where drivetype=2 get deviceid, description"
    PNP_INSTALL_DRIVER_CMD = "pnputil /add-driver {} /install"
    PNP_UNINSTALL_DRIVER_CMD = "pnputil /delete-driver {} /uninstall"
    WIN_FILE_SEARCH_CMD = "powershell.exe (get-childitem '{}' -File {} -recurse).fullname"
    PNP_ENUM_DRIVER_CMD = "pnputil /enum-drivers"
    REMOVABLE_DISK_REGEX = r"Removable\sDisk\s+([A-Z]:)"
    DEVCON_UNINSTALL_DRIVER_CMD = "devcon /r remove =net *{}*"

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new windows Driver Provider object.

        :param os_obj: os object
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(WindowsDriverInstallation, self).__init__(log, cfg_opts, os_obj)

    def install_driver(self, driver_inf_file, device_id):
        """
        This function install driver specified

        :param driver_inf_file: Driver inf file to be installed
        :param device_id: Device id for corresponding driver
        :raise: Content Exception if USB is not connected
        """
        if not self.is_driver_installed(driver_inf_file):
            self._log.info("Installing the network driver")
            # Checking if device id is available in the compatible device iDs of SUT
            device_output = self._common_content_lib.execute_sut_cmd(self.WMIC_GETDEVICEID_CMD.format(device_id),
                                                                     self.WMIC_GETDEVICEID_CMD.format(device_id),
                                                                     self._command_timeout)
            if device_id in device_output:
                self._log.debug("Device ID {} is compatible with the sut".format(device_id))
                wmic_out = self._common_content_lib.execute_sut_cmd(self.WMIC_USB_CMD, self.WMIC_USB_CMD,
                                                                    self._command_timeout)
                drive_name = (re.search(self.REMOVABLE_DISK_REGEX, str(wmic_out))).group(1)
                if not drive_name:
                    raise content_exceptions.TestFail("USB is not detected in SUT")
                self._log.debug("USB drive name in sut {}".format(drive_name))
                search_output = self._common_content_lib.execute_sut_cmd(
                    self.WIN_FILE_SEARCH_CMD.format(drive_name, driver_inf_file),
                    self.WIN_FILE_SEARCH_CMD.format(drive_name, driver_inf_file),
                    self._command_timeout)

                install_cmd_output = self._common_content_lib.execute_sut_cmd(
                    self.PNP_INSTALL_DRIVER_CMD.format(search_output),
                    self.PNP_INSTALL_DRIVER_CMD.format(search_output),
                    self._command_timeout)

                self._log.debug("Network driver is installed successfully and output is {}".format(install_cmd_output))
        self._log.info("Network Driver is Successfully Installed")

    def uninstall_driver(self, driver_inf_file, device_id):
        """
        This function checks if system is having the driver installed and then
        un-install driver specified

        :param driver_inf_file: driver inf file name
        :param device_id: name of the driver.
        :raise: content exception if driver is not installed.
        """
        self._log.info("Uninstalling the driver")
        oem_file = self.is_driver_installed(driver_inf_file)
        if not oem_file:
            raise content_exceptions.TestFail("Driver is not installed as expected")

        output = self._common_content_lib.execute_sut_cmd(self.DEVCON_UNINSTALL_DRIVER_CMD.format(device_id),
                                                          self.DEVCON_UNINSTALL_DRIVER_CMD.format(device_id),
                                                          self._command_timeout)
        self._log.info("Driver is uninstalled successfully and output is {}".format(output))

    def load_driver(self, driver_code, driver_name):
        """
        This function re-install driver specified

        :param driver_code: driver code
        :param driver_name: name of the driver installing.
        """
        raise content_exceptions.TestNotImplementedError

    def is_driver_installed(self, driver_inf_file, driver_name=None):
        """
        This method checks if particular inf file name related network driver is installed in sut.

        :param driver_inf_file: Driver inf file name
        :param driver_name: None for Windows
        :return: Returns the oem file name if driver is installed, if not returns None
        """
        self._log.info("Checking if driver is installed")
        enum_driver_dict = {}
        driver_dict_count = 0
        ret_val = None
        pnp_util_str = "Microsoft PnP Utility"
        publish_name_str = "Published Name"
        original_name_str = "Original Name"
        command_output = self._common_content_lib.execute_sut_cmd(self.PNP_ENUM_DRIVER_CMD,
                                                                  self.PNP_ENUM_DRIVER_CMD, self._command_timeout)
        self._log.info("List of Drivers in system is {}".format(command_output))
        command_result_list = [driver_info.strip() for driver_info in command_output.split("\n") if
                               driver_info.strip() not in pnp_util_str]
        for output in command_result_list:
            if publish_name_str in output:
                enum_driver_dict[driver_dict_count + 1] = {}
                driver_dict_count += 1
            enum_driver_dict[driver_dict_count][output.split(":")[0].strip()] = output.split(":")[1].strip()
        for driver_parameters, driver_info_value in enum_driver_dict.items():
            if (driver_info_value.get(original_name_str)) == driver_inf_file:
                self._log.info("Driver with inf file {} is installed in system".format(driver_inf_file))
                ret_val = driver_info_value.get(publish_name_str)
        self._log.info("The oem file name for uninstalling the driver is {}".format(ret_val))
        return ret_val

    def get_ethernet_devices(self):
        """
        Get the Ethernet devices from the SUT

        :raise: content_exception.TestFail if not getting the Ethernet devices
        :return: ethernet_devices
        """
        raise content_exceptions.TestNotImplementedError

    def identify_device_controller(self, ethernet_device_list, driver_code):
        """
        Identify the device controller and verify the driver code with expected driver code

        :param driver_code: driver code
        :param ethernet_device_list: Ethernet devices list
        :raise: content_exception.TestFail if not getting the driver code which is expected
        """
        raise content_exceptions.TestNotImplementedError


class LinuxDriverInstallation(DriverProvider):
    """Linux Driver Installation provider object"""
    TAR_CMD = "tar -xvf {}"
    MAKE_INSTALL_CMD = "make install"
    MODPROBE_CMD = "modprobe {}"
    MODPROBE_UNINSTALL_CMD = "rmmod {}"
    LSMOD_CMD = "lsmod | grep {}"
    LSPCI_CMD = "lspci | grep {}"
    RMMOD_CMD = "rmmod {}"
    FIND_CMD = "find $(pwd) -type f -name {}*.gz"
    FIND_UNZIPPED_DIRECTORY = "find $(pwd) -type d -name {}*"
    INSTALL_ELFUTILS = "echo y | yum install elfutils-libelf-devel"
    SRC = "src"
    ETHERNET_CMD = "Ethernet"
    LSPCI_IDENTITY_CMD = "lspci -s {} -vvv"
    REGEX_CMD_FOR_FORTVILLE_DRIVER = r".*\sEthernet\sController\s.*710.*"
    REGEX_CMD_FOR_COLUMBIAVILLE_DRIVER = r".*\sEthernet\sController\sE810-C.*"
    NETWORK_DRIVER_CODES_LIST = [NetworkDrivers.COLUMBIAVILLE_DRIVER_CODE, NetworkDrivers.CARLSVILLE_DRIVER_CODE,
                                 NetworkDrivers.FOXVILLE_DRIVER_CODE]

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new Linux Driver Provider object.

        :param os_obj: os object
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(LinuxDriverInstallation, self).__init__(log, cfg_opts, os_obj)
        self.PSW_DIR = None

    def is_driver_installed(self, driver_code, driver_name=None):
        """
        This function check if driver is installed or not.

        :raise: content_exception.TestFail if not driver installed properly.
        """
        self._log.info("Checking driver installation with lsmod command ")
        cmd = self.LSMOD_CMD.format(driver_code)
        self._log.debug("lsmod command {}".format(cmd))
        output = self._os.execute(cmd, self.execution_timeout, self.PSW_DIR)
        self._log.debug(output.stdout)
        self._log.error(output.stderr)
        if not re.search("^{}".format(driver_code), output.stdout):
            return False
        self._log.info("Successfully installed {} driver".format(driver_name))
        return True

    def check_driver_uninstalled(self, driver_code, driver_name):
        """
        This function checks the driver is uninstalled or not and returns the bool value

        :raise: content_exception.TestFail if not driver uninstalled properly.
        """
        self._log.info("Executing lsmod command for uninstallation")
        cmd = self.LSMOD_CMD.format(driver_code)
        self._log.debug("lsmod command for uninstallation{}".format(cmd))
        output = self._os.execute(cmd, self.execution_timeout, self.PSW_DIR)
        self._log.debug(output.stdout)
        self._log.error(output.stderr)
        if driver_code in output.stdout.strip():
            raise content_exceptions.TestFail("%s driver is not uninstalled properly" % driver_name)
        self._log.info("Successfully uninstalled {} driver".format(driver_name))

    def untar_driver_files(self, driver_code):
        """
        This function searches for driver folder un-tar the driver files.

        :raise: content_exception.TestFail if unable to un-tar properly.
        """
        self._log.info("Searching for driver tar file")
        cmd = self.FIND_CMD.format(driver_code)
        self._log.debug("Searching Driver tar file cmd {}".format(cmd))
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout, self.DRIVER_DEST_PATH_LINUX)
        if not output.strip():
            raise content_exceptions.TestFail("could not find %s on SUT" % driver_code)
        self._log.debug("find cmd output {}".format(output))
        zip_path = os.path.split(output.strip().split("\n")[-1])[-1] \
            if driver_code == NetworkDrivers.COLUMBIAVILLE_DRIVER_CODE else os.path.split(output.strip())[-1]
        source_path = os.path.split(output.strip())[0].split("\n")[1] \
            if driver_code == NetworkDrivers.COLUMBIAVILLE_DRIVER_CODE else os.path.split(output.strip())[0]
        directory_name = os.path.dirname(output.strip())
        self._log.debug(
            "directory name {}, zip path {} , source path {} ".format(directory_name, zip_path, source_path))
        self._common_content_lib.extract_compressed_file(source_path, zip_path, directory_name)

    def set_driver_cwd(self, driver_code):
        """
        This function sets driver binary directory as current working directory.

        :raise: content_exception.TestFail if unable to find the directory.
        """
        self._log.debug("getting current working directory")
        cmd = self.FIND_UNZIPPED_DIRECTORY.format(driver_code)
        self._log.debug("find command for searching directory  {}".format(cmd))
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout, self.DRIVER_DEST_PATH_LINUX)
        if not output.strip():
            raise content_exceptions.TestFail("Could not find untared folder %s on SUT" % driver_code)
        self.PSW_DIR = output.strip() + "/" + self.SRC
        self._log.debug("Current Working directory {} ".format(self.PSW_DIR))

    def install_prerequisites(self):
        """
        This function install prerequisites for installing driver.
        """
        self._log.debug(self.INSTALL_ELFUTILS)
        output = self._common_content_lib.execute_sut_cmd(
            self.INSTALL_ELFUTILS, self.INSTALL_ELFUTILS, self.execution_timeout)
        self._log.debug(output)

    def install_make(self, driver_name):
        """
        This function install make command

        :raise: content_exception.TestFail if not unable to install make command.
        """
        self._log.info("Make install command for the driver {}".format(driver_name))
        output = self._common_content_lib.execute_sut_cmd(
            self.MAKE_INSTALL_CMD, self.MAKE_INSTALL_CMD, self.execution_timeout, self.PSW_DIR)
        self._log.debug(output)
        if not output.strip():
            raise content_exceptions.TestFail("failed to install driver %s" % driver_name)

    def install_driver(self, driver_code, driver_name):
        """
        This function install driver specified

        :param driver_code: driver code
        :param driver_name: name of the driver installing.
        """
        if not self.is_driver_installed(driver_code, driver_name):
            self._log.info("Installing the {} network driver".format(driver_name))
            self._common_content_lib.execute_sut_cmd(self.MODPROBE_CMD.format(driver_code), self.MODPROBE_CMD.format(
                driver_code), self._COMMAND_TIMEOUT)
            self.load_driver(driver_code, driver_name)
            self._log.debug("{} Network Driver is Installed and Loaded".format(driver_name))
        self._log.info("{} Network Driver is Installed".format(driver_name))

    def uninstall_driver(self, driver_code, driver_name):
        """
        This function uninstall driver specified

        :param driver_code: driver code
        :param driver_name: name of the driver to un-install.
        """
        self._log.info("Uninstalling {} network driver".format(driver_name))
        self._common_content_lib.execute_sut_cmd(self.MODPROBE_UNINSTALL_CMD.format(driver_code),
                                                 self.MODPROBE_UNINSTALL_CMD.format(driver_code),
                                                 self._COMMAND_TIMEOUT)
        self._log.debug("{} Network Driver is Uninstalled Successfully".format(driver_name))

    def load_driver(self, driver_code, driver_name):
        """
        This function loads driver specified.

        :param driver_code: driver code
        :param driver_name: name of the driver installing.
        """
        self._log.info("Loading {} driver".format(driver_name))
        cmd = self.MODPROBE_CMD.format(driver_code)
        self._log.debug("Checking for modprobe command {}".format(cmd))
        output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self.execution_timeout)
        self._log.debug(output)
        self.is_driver_installed(driver_code, driver_name)

    def get_ethernet_devices(self):
        """
        Get the Ethernet devices from the SUT

        :raise: content_exception.TestFail if not getting the Ethernet devices
        :return: ethernet_devices
        """
        self._log.info("Identify the Ethernet Device")
        # Get Ethernet devices command
        ethernet_devices = self._common_content_lib.execute_sut_cmd(self.LSPCI_CMD.format(self.ETHERNET_CMD),
                                                                    self.LSPCI_CMD.format(self.ETHERNET_CMD),
                                                                    self._COMMAND_TIMEOUT)
        if not ethernet_devices:
            raise content_exceptions.TestFail("Could not get the info of Ethernet devices")
        self._log.info("Ethernet device list {}".format(ethernet_devices))
        return ethernet_devices

    def identify_device_controller(self, ethernet_device_list, driver_code):
        """
        Identify the device controller and verify the driver code with expected driver code

        :param driver_code: driver code
        :param ethernet_device_list: Ethernet devices list
        :raise: content_exception.TestFail if not getting the driver code which is expected
        """
        ethernet_device_id = []
        ethernet_controller_manufacturer = []
        if driver_code in self.NETWORK_DRIVER_CODES_LIST:
            regex_cmd = r"(\d+):(\d+.*) Ethernet controller"
        else:
            regex_cmd = r"(\d+):(\d+.:.*) Ethernet controller"
        regex_kernel_cmd = r"Kernel\sdriver\sin\suse.*({})".format(driver_code)
        self._log.info("Identify the driver used in the SUT")
        if driver_code == NetworkDrivers.FORTVILLE_DRIVER_CODE or driver_code == NetworkDrivers.CARLSVILLE_DRIVER_CODE:
            ethernet_devices_info = re.compile(self.REGEX_CMD_FOR_FORTVILLE_DRIVER) \
                .findall("".join(ethernet_device_list))
        elif driver_code == NetworkDrivers.COLUMBIAVILLE_DRIVER_CODE:
            ethernet_devices_info = re.compile(self.REGEX_CMD_FOR_COLUMBIAVILLE_DRIVER) \
                .findall("".join(ethernet_device_list))
        else:
            ethernet_devices_info = [info for info in ethernet_device_list.split("\n") if info != ""]
        for device in ethernet_devices_info:
            regex_search = re.search(regex_cmd, device.strip(), re.M)
            if not regex_search:
                raise content_exceptions.TestError("Could not get the info of Ethernet devices")
            if driver_code == NetworkDrivers.CARLSVILLE_DRIVER_CODE or \
                    driver_code == NetworkDrivers.COLUMBIAVILLE_DRIVER_CODE:
                ethernet_device_id.append(regex_search.group().split(" ")[0])
            else:
                ethernet_device_id.append(regex_search.group(1))
            ethernet_controller_manufacturer.append(regex_search.group(2))
        self._log.debug("Ethernet device id {}".format(ethernet_device_id))
        self._log.debug("Ethernet Controller/Manufacturer id {}".format(ethernet_controller_manufacturer))
        for device_id in ethernet_device_id:
            driver_used_output = self._common_content_lib.execute_sut_cmd(self.LSPCI_IDENTITY_CMD.format(device_id),
                                                                          self.LSPCI_IDENTITY_CMD.format(device_id),
                                                                          self._DEVICE_EXECUTION_TIMEOUT)
            self._log.debug("Ethernet device id used in the SUT {} ".format(driver_used_output))
        for controller_id in ethernet_controller_manufacturer:
            controller_device_id = self._common_content_lib.execute_sut_cmd(self.LSPCI_IDENTITY_CMD.format(
                controller_id), self.LSPCI_IDENTITY_CMD.format(controller_id), self._COMMAND_TIMEOUT)
            self._log.debug("Ethernet Controller/Manufacturer used in the SUT {}".format(controller_device_id))
            regex_kernel_driver_search = re.search(regex_kernel_cmd, controller_device_id.strip(), re.M)
            if not regex_kernel_driver_search:
                raise content_exceptions.TestError("Could not get the info of Ethernet devices")
            self._log.info("Ethernet driver code name {}".format(regex_kernel_driver_search.group(1)))
            if regex_kernel_driver_search.group(1) != driver_code:
                raise content_exceptions.TestFail("Network driver Code is not matching")
