#!/usr/bin/env python
###############################################################################
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
# otherwise. Any license under such intellectual property rights must be
# express and approved by Intel in writing.
###############################################################################

import sys
import os


class WindowsStorageDevice(object):
    KEY_DEVICE_ID = "DeviceID"
    KEY_PNP_DEVICE_ID = "PNPDeviceID"
    KEY_DRIVE_LETTERS = "DriveLetters"
    KEY_DRIVE_LETTER = "DriveLetter{}"
    KEY_SERIAL_NUMBER = "SerialNumber"
    KEY_BUS_TYPE = "BusType"
    KEY_STORAGE_DEVICE = "StorageDevice{}"
    MS_STORAGE_NAMESPACE = r"microsoft\windows\storage"

    def __init__(self):
        self.__install_packages()
        try:
            import wmi
            self._obj_wmi_cimv2 = wmi.WMI()
            self._obj_wmi_ms_storage = wmi.WMI(namespace=self.MS_STORAGE_NAMESPACE)

            self._dict_storage_devices = {}
        except ImportError as ex:
            print("Please install python modules 'PyWin32' and 'wmi' on SUT...")
            raise ImportError("Please install python modules 'PyWin32' and 'wmi' on SUT. "
                              "Exception: '{}'".format(ex))

    @staticmethod
    def __install_pip_package(package):
        general_proxy = "http://proxy-chain.intel.com:911"
        prc_proxy = "http://child-prc.intel.com:913"

        # first try with general proxy
        cmd_line = "pip install {} -q --proxy {}"
        ret_code = os.system(cmd_line.format(package, general_proxy))
        if ret_code != 0:
            # try with prc proxy
            ret_code = os.system(cmd_line.format(package, prc_proxy))

        return ret_code

    def __install_packages(self):
        # install pywin32 if not installed
        try:
            import win32api
        except ImportError:
            self.__install_pip_package("pywin32")

        # install wmi if not installed
        try:
            import wmi
        except ImportError:
            self.__install_pip_package("wmi")

    def enumerate_storage_devices(self):
        """
        This method is use to get the enumeration of storage device.

        :return: {StorageDevice0: {"DeviceID": "device id", "PnpDeviceID":"pnp device id",
                {"DriveLetters: "DeviceLetter0":"E:", "DeviceLetter1":"F:"}}
                {StorageDevice1:{"DeviceID": "device id", "PnpDeviceID": "pnp device id"
                {"DeriveLetters: "DeviceLetter0":"G", "DeviceLetter11": "D:"}}
        """
        index = 0
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
            self._dict_storage_devices[key_storage_device] = dict_disk_drives

            for storage_key, storage_device in self._dict_storage_devices.items():
                # find the bustype from MSFT_Disk class
                wql = "Select BusType from MSFT_Disk where " \
                      "SerialNumber='{}'".format(storage_device[self.KEY_SERIAL_NUMBER])
                list_msft_disk = self._obj_wmi_ms_storage.query(wql)
                for msft_disk in list_msft_disk:
                    storage_device[self.KEY_BUS_TYPE] = msft_disk.BusType

        return self._dict_storage_devices


if __name__ == "__main__":
    try:
        storage_device = WindowsStorageDevice()
        dict_storage_devices = storage_device.enumerate_storage_devices()
        if dict_storage_devices:
            print(dict_storage_devices)
            sys.exit(0)
        else:
            print("Failed to enumerate storage devices..")
            sys.exit(1)
    except Exception as ex:
        print(ex)
        sys.exit(1)
