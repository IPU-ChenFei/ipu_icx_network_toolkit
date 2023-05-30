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
import platform
import re
import time
from abc import ABCMeta, abstractmethod
from importlib import import_module

import six
from six import add_metaclass
import shutil
import zipfile

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.provider.base_provider import BaseProvider
from src.lib.common_content_lib import CommonContentLib
from src.collaterals.collateral_constants import CollateralConstants
from src.lib.dtaf_content_constants import WindowsDiskBusType


@add_metaclass(ABCMeta)
class HostUsbDriveProvider(BaseProvider):

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new copyUtil object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(HostUsbDriveProvider, self).__init__(log, cfg_opts, os_obj)
        self._common_content_lib = CommonContentLib(log, os_obj, cfg_opts)


    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        """
        package = r"src.provider.host_usb_drive_provider"
        exec_os = platform.system()
        if OperatingSystems.WINDOWS in exec_os:
            mod_name = "HostUsbDriveWindows"
        elif OperatingSystems.LINUX in exec_os:
            mod_name = "HostUsbDriveLinux"
        else:
            raise NotImplementedError

        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(cfg_opts=cfg_opts, log=log, os_obj=os_obj)

    def get_hotplugged_usb_drive(self, phy_obj):
        phy_obj.connect_usb_to_sut(10)
        list_drives1 = self.get_mount_points()
        self._log.info("USB drives after hot unplug='{}'".format(list_drives1))
        phy_obj.connect_usb_to_host(10)
        time.sleep(15)
        list_drives2 = self.get_mount_points()
        self._log.info("USB drives after hot plug='{}'".format(list_drives2))

        hotplugged_drive = (list(list(set(list_drives1) - set(list_drives2)) +
                                 list(set(list_drives2) - set(list_drives1))))
        self._log.info("Hot-plugged USB drive list='{}'".format(hotplugged_drive))

        usb_drive = hotplugged_drive[0]
        return usb_drive

    @abstractmethod
    def get_mount_points(self):
        """
        To get the list of mount point(s)

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def format_drive(self, mount_point):
        """
        Formats the flash drive with Fat32 FS.

        :param mount_point: For windows - drive letter/linux mount name
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_drive_serial_number(self, mount_point):
        """
        Returns the USB drive serial number.

        :param mount_point: For windows - drive letter/linux mount name
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def copy_collateral_to_usb_drive(self, collateral_name, usb_mp):
        """
        This method will copy the collateral binary to SUT home path
        :param key_collateral: - key to collateral dict
        :param usb_mp: drive in windows and mount name in linux
        :raise RuntimeError: for any failures

        :return: path where binary copied to USB drive
        """
        raise NotImplementedError

    @abstractmethod
    def copy_file_to_usb(self, host_path, usb_path):
        """
        Copy file(s) usb drive

        :param host_path: source host path
        :param usb_path: destination usb path
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def copy_file_from_usb(self, usb_path, host_path):
        """
        Copy file(s) from usb drive to host

        :param host_path: host dest path
        :param usb_path: usb path
        :raise NotImplementedError
        """
        raise NotImplementedError


class HostUsbDriveWindows(HostUsbDriveProvider):
    KEY_DEVICE_ID = "DeviceID"
    KEY_PNP_DEVICE_ID = "PNPDeviceID"
    KEY_DRIVE_LETTERS = "DriveLetters"
    KEY_DRIVE_LETTER = "DriveLetter{}"
    KEY_SERIAL_NUMBER = "SerialNumber"
    KEY_BUS_TYPE = "BusType"
    KEY_STORAGE_DEVICE = "StorageDevice{}"
    MS_STORAGE_NAMESPACE = r"microsoft\windows\storage"

    def __init__(self, log, cfg_opts, os_obj):
        super(HostUsbDriveWindows, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        try:
            import wmi
            self._obj_wmi_cimv2 = wmi.WMI()
            self._obj_wmi_ms_storage = wmi.WMI(namespace=self.MS_STORAGE_NAMESPACE)
        except ImportError as ex:
            raise ImportError("Please install python modules 'PyWin32' and 'wmi' on Host. "
                              "Exception: '{}'".format(ex))

    def factory(self, log, cfg_opts, os_obj):
        pass

    def get_mount_points(self):
        """
        To get the mount point(s) of the usb drive(s).

        :return: the list of mount point(s)
        """
        list_usb_drives = []
        wql = "Select DeviceID from Win32_LogicalDisk where DriveType='2'"
        drives = self._obj_wmi_cimv2.query(wql)
        if len(drives) > 0:
            for drive in drives:
                list_usb_drives.append(drive.DeviceID)

        return list_usb_drives

    def format_drive(self, mount_point):
        """
        Formats the flash drive with Fat32 FS.

        :param mount_point: For windows - drive letter/linux mount name
        :raise NotImplementedError
        """
        # remove all non letter from mount_point
        regex = re.compile('[^a-zA-Z]')
        # First parameter is the replacement, second parameter is your input string
        drive_letter = regex.sub('', mount_point)
        cmd_line = 'powershell.exe "Format-Volume -DriveLetter {} -FileSystem Fat32"'.format(drive_letter)
        self._common_content_lib.execute_cmd_on_host(cmd_line)

    def get_drive_serial_number(self, mount_point):
        """
        Returns the USB drive serial number.

        :param mount_point: For windows - drive letter/linux mount name
        :raise NotImplementedError
        """
        list_usb_disks = self.__enumerate_usb_disks()

        serial_number = None
        drive_letter_found = False

        for each_usb_device in list_usb_disks:
            index = 0
            list_drive_letter = []
            for key, value in each_usb_device.items():
                if key == self.KEY_SERIAL_NUMBER:
                    serial_number = value
                if key == self.KEY_DRIVE_LETTERS:
                    if bool(value):
                        list_drive_letter.append(value[self.KEY_DRIVE_LETTER.format(index)])
                        print(list_drive_letter)
                        if mount_point in list_drive_letter:
                            drive_letter_found = True
            if serial_number is not None and drive_letter_found:
                # we found both drive letter and serial number, break from loop now
                break

        if not drive_letter_found:
            serial_number = None

        if serial_number is not None:
            serial_number = str(serial_number).lower()

        return serial_number

    def __enumerate_usb_disks(self):
        """
        This method gives the list of USB disk on Host.

        :return: List of Sata Disk : eg: [{'DeviceID': '\\\\.\\PHYSICALDRIVE0', 'PNPDeviceID':
        'SCSI\\DISK&VEN_INTEL&PROD_SSDSC2KG960G8\\4&2E24B7EF&0&000000', 'SerialNumber': 'PHYG9212021C960CGN',
        'DriveLetters': {}, 'BusType': 11}, {'DeviceID': '\\\\.\\PHYSICALDRIVE1', 'PNPDeviceID':
        'SCSI\\DISK&VEN_INTEL&PROD_SSDSC2KG480G7\\4&2E24B7EF&0&010000', 'SerialNumber': 'BTYM7404042R480BGN',
        'DriveLetters': {'DriveLetter0': 'C:'}, 'BusType': 11}
        :raise: None
        """
        dict_storage_devices = self.__enumerate_storage_disks()
        list_usb_disks = []
        for storage_key, storage_disk in dict_storage_devices.items():
            bus_type = int(storage_disk[self.KEY_BUS_TYPE])
            if bus_type == WindowsDiskBusType.BUS_TYPE_USB:
                list_usb_disks.append(storage_disk)

        return list_usb_disks

    def __enumerate_storage_disks(self):
        """
        This method is use to get the enumeration of storage device.

        :return: {StorageDevice0: {"DeviceID": "device id", "PnpDeviceID":"pnp device id",
                {"DriveLetters: "DeviceLetter0":"E:", "DeviceLetter1":"F:"}}
                {StorageDevice1:{"DeviceID": "device id", "PnpDeviceID": "pnp device id"
                {"DeriveLetters: "DeviceLetter0":"G", "DeviceLetter11": "D:"}}
        """
        index = 0
        dict_storage_devices = {}
        wql = "Select * from Win32_DiskDrive"
        list_disk_drives = self._obj_wmi_cimv2.query(wql)
        for disk in list_disk_drives:
            dict_disk_drives = {}
            dict_drive_letters = {}
            dict_disk_drives[self.KEY_DEVICE_ID] = disk.DeviceID
            dict_disk_drives[self.KEY_PNP_DEVICE_ID] = disk.PNPDeviceID
            dict_disk_drives[self.KEY_SERIAL_NUMBER] = disk.SerialNumber

            wql = 'ASSOCIATORS OF {Win32_DiskDrive.DeviceID="%s"} WHERE AssocClass=Win32_DiskDriveToDiskPartition'
            wql = wql % str(disk.DeviceID)
            list_disk_partitions = self._obj_wmi_cimv2.query(wql)
            for disk_part in list_disk_partitions:
                wql = 'ASSOCIATORS OF {Win32_DiskPartition.DeviceID="%s"} WHERE AssocClass=Win32_LogicalDiskToPartition'
                wql = wql % str(disk_part.DeviceID)
                list_logical_disks = self._obj_wmi_cimv2.query(wql)
                drive_letter_index = 0
                for logical_disk in list_logical_disks:
                    key_drive_letter = self.KEY_DRIVE_LETTER.format(drive_letter_index)
                    drive_letter_index = drive_letter_index + 1
                    dict_drive_letters[key_drive_letter] = str(logical_disk.DeviceID)

                dict_disk_drives[self.KEY_DRIVE_LETTERS] = dict_drive_letters

            key_storage_device = self.KEY_STORAGE_DEVICE.format(index)
            index = index + 1
            dict_storage_devices[key_storage_device] = dict_disk_drives

            for storage_key, storage_device in dict_storage_devices.items():
                # find the bustype from MSFT_Disk class
                wql = "Select BusType from MSFT_Disk where " \
                      "SerialNumber='{}'".format(storage_device[self.KEY_SERIAL_NUMBER])
                list_msft_disk = self._obj_wmi_ms_storage.query(wql)
                for msft_disk in list_msft_disk:
                    storage_device[self.KEY_BUS_TYPE] = msft_disk.BusType

        return dict_storage_devices

    def copy_collateral_to_usb_drive(self, collateral_name, usb_mp):
        """
        This method will copy the collateral binary to SUT home path
        :param collateral_name: - collateral name
        :param usb_mp: drive in windows and mount name in linux
        :raise RuntimeError: for any failures

        :return: path where binary copied to USB drive
        """
        proj_src_path = self._common_content_lib.get_project_src_path()
        dict_collateral = CollateralConstants.dict_collaterals[collateral_name]

        archive_relative_path = dict_collateral[CollateralConstants.RELATIVE_PATH]
        archive_file_name = dict_collateral[CollateralConstants.FILE_NAME]
        host_collateral_path = os.path.join(proj_src_path, r"src\collaterals", archive_relative_path, archive_file_name)
        if not os.path.exists(host_collateral_path):
            log_error = "The collateral archive '{}' does not exists..".format(host_collateral_path)
            self._log.error(log_error)
            raise FileNotFoundError(log_error)

        if self._os.os_type not in dict_collateral[CollateralConstants.SUPP_OS]:
            log_error = "This functionality is not supported for the OS '{}'..".format(self._os.os_type)
            self._log.error(log_error)
            raise NotImplementedError(log_error)

        usb_path = usb_mp + os.sep
        with zipfile.ZipFile(host_collateral_path, 'r') as zip:
            zip.extractall(usb_mp, )

        usb_path = os.path.join(usb_path, collateral_name)
        if not os.path.exists(usb_path):
            raise RuntimeError("Failed to copy collateral '{}' to USB drive '{}'..".format(collateral_name, usb_mp))

        self._log.info("Successfully copied collateral '{}' to USB path '{}'.".format(collateral_name, usb_path))

        return usb_path

    def copy_file_to_usb(self, host_path, usb_path):
        """
        Copy file(s) usb drive

        :param host_path: source host path
        :param usb_path: destination usb path
        :raise NotImplementedError
        """
        cmd_line = "xcopy {} {} /S /K /D /H /Y".format(host_path, usb_path)
        self._common_content_lib.execute_cmd_on_host(cmd_line)

    def copy_file_from_usb(self, usb_path, host_path):
        """
        Copy file(s) from usb drive to host

        :param host_path: host dest path
        :param usb_path: usb path
        :raise NotImplementedError
        """
        cmd_line = "xcopy {} {} /S /K /D /H /Y".format(usb_path, host_path)
        self._common_content_lib.execute_cmd_on_host(cmd_line)


class HostUsbDriveLinux(HostUsbDriveProvider):

    def __init__(self, log, cfg_opts, os_obj):
        super(HostUsbDriveLinux, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj

    def factory(self, log, cfg_opts, os_obj):
        pass

    def get_mount_points(self):
        """
        To get the mount point of the usb drive.

        :return: the list of mount point(s)
        """
        raise NotImplementedError

    def format_drive(self, mount_point):
        """
        Formats the flash drive with Fat32 FS.

        :param mount_point: For windows - drive letter/linux mount name
        :raise NotImplementedError
        """
        raise NotImplementedError

    def get_drive_serial_number(self, mount_point):
        """
        Returns the USB drive serial number.

        :param mount_point: For windows - drive letter/linux mount name
        :raise NotImplementedError
        """
        raise NotImplementedError

    def copy_collateral_to_usb_drive(self, collateral_name, usb_mp):
        """
        This method will copy the collateral binary to SUT home path
        :param key_collateral: - key to collateral dict
        :param usb_mp: drive in windows and mount name in linux
        :raise RuntimeError: for any failures

        :return: path where binary copied to USB drive
        """
        raise NotImplementedError

    def copy_file_to_usb(self, host_path, usb_path):
        """
        Copy file(s) usb drive

        :param host_path: source host path
        :param usb_path: destination usb path
        :raise NotImplementedError
        """
        raise NotImplementedError

    def copy_file_from_usb(self, usb_path, host_path):
        """
        Copy file(s) from usb drive to host

        :param host_path: host dest path
        :param usb_path: usb path
        :raise NotImplementedError
        """
        raise NotImplementedError


