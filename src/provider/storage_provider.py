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
import ast
import re
import os
import json
from importlib import import_module
from abc import ABCMeta, abstractmethod
from six import add_metaclass

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
import src.lib.content_exceptions as content_exceptions
from src.provider.base_provider import BaseProvider
from src.lib.dtaf_content_constants import ExecutionEnv
from src.lib.dtaf_content_constants import WindowsDiskBusType
from src.lib.install_collateral import InstallCollateral
from src.collateral_scripts.windows_disk_drives import WindowsStorageDevice


@add_metaclass(ABCMeta)
class StorageProvider(BaseProvider):

    def __init__(self, log, os_obj, uefi_util_obj=None, cfg_opts=None):
        """
        Create a new copyUtil object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(StorageProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._sut_os = self._os.os_type
        self.uefi_util_obj = uefi_util_obj
        self._common_content_config = ContentConfiguration(self._log)
        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg_opts)
        self._cmd_time_out_in_sec = self._common_content_config.get_command_timeout()
        self._reboot_time_out_in_sec = self._common_content_config.get_reboot_timeout()

        self._install_collateral = InstallCollateral(self._log, self._os, self._cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()

    @staticmethod
    def factory(log, os_obj, cfg_opts=None, execution_env=None, uefi_obj=None):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        """
        package = r"src.provider.storage_provider"
        if execution_env and execution_env not in {ExecutionEnv.OS, ExecutionEnv.UEFI}:
            raise ValueError("Invalid value has been provided for "
                             "argument 'execution_env'. it should be 'os' or 'uefi'")

        #   Getting the required module name
        if execution_env == ExecutionEnv.UEFI:
            if uefi_obj is None:
                raise ValueError('uefi util object can not be empty')

            mod_name = "StorageProviderUefi"
        else:
            if ExecutionEnv.OS == execution_env:
                execution_env = os_obj.os_type.lower()
            if OperatingSystems.WINDOWS == os_obj.os_type:
                mod_name = "StorageProviderWindows"
            elif OperatingSystems.LINUX == os_obj.os_type:
                mod_name = "StorageProviderLinux"
            elif OperatingSystems.ESXI == os_obj.os_type:
                mod_name = "StorageProviderESXi"
            else:
                raise NotImplementedError("Storage provider is not implemented for "
                                          "specified OS '{}'".format(os_obj.os_type))

        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(cfg_opts=cfg_opts, log=log, os_obj=os_obj, uefi_util_obj=uefi_obj)

    @abstractmethod
    def enumerate_sata_disks(self):
        """
        Call this function to get the list of all SATA device on SUT.

        :return: list of sata device on SUT
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def enumerate_nvme_disks(self):
        """
        Call this function to get the list of all NVME disks.

        :return: List of all NVME disks
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def enumerate_usb_disks(self):
        """
        Call this function to get the list of all USB disks.

        :return: List of all USB disk
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def mount_the_drive(self, mount_device_name, mount_point):
        """
        This method is to mount the device

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_usb_details(self):
        """
        This method is to get usb details

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def find_disk_size(self, partition_drive):
        """
        This method is to give the size of disk.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_diskdirves(self):
        """
        This method is to give the DiskDrive Information

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_booted_device(self):
        """
        This method is to give the booted devide Information

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_device_type(self, lsblk_res, name_ssd):
        """
        This method is to give the booted device type

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_booted_raid_disk(self):
        """
        this method is to get the booted raid disk
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_smartctl_drive_list(self):
        """
        Get smartctl drive list

        :param column: Non.
        :return: Drive list
        """

class StorageProviderWindows(StorageProvider):
    """
    This Class has different method of Storage Functionality on Windows Platform

    :return None
    :raise None
    """
    CMD_TO_FIND_FREE_SPACE = "WMIC LOGICALDISK GET Name,FreeSpace | find /i \"{}\""
    CONST_TO_CONVERT_IN_MB = 1024 * 1024
    C_DRIVE_PATH = "C:\\"
    DISKDRIVE_INFO = "wmic diskdrive"

    def __init__(self, log, os_obj, uefi_util_obj=None, cfg_opts=None):
        super(StorageProviderWindows, self).__init__(log, os_obj, uefi_util_obj, cfg_opts)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj

    def factory(log, os_obj, cfg_opts=None, execution_env=None, uefi_obj=None):
        pass

    def __enumerate_storage_disks(self):
        """
        This method is to get enumerator for all device.
        """
        cmd_line = "echo %HOMEDRIVE%%HOMEPATH%"
        collateral_script = "windows_disk_drives.py"
        sut_home_path = self._common_content_lib.execute_sut_cmd(cmd_line, cmd_line, self._cmd_time_out_in_sec)
        sut_home_path = str(sut_home_path).strip().strip("\\n")
        sut_path = os.path.join(sut_home_path, collateral_script)
        self._install_collateral.copy_collateral_script(collateral_script, sut_home_path)

        cmd_line = "python {}".format(sut_path)
        # Getting  the storage disks info
        storage_disks = self._common_content_lib.execute_sut_cmd(cmd_line, cmd_line, self._cmd_time_out_in_sec)
        storage_disks = str(storage_disks).replace("\'", "\"")
        dict_storage_disks = ast.literal_eval(storage_disks)
        # dict_storage_disks = json.loads(storage_disks)

        return dict_storage_disks

    def enumerator_storage_device(self):
        """
        This method gives the list of  disk drive information on SUT.

        :return: Dict of  Disk drive info: eg: {'StorageDevice0': {'DeviceID': '\\\\.\\PHYSICALDRIVE1',
        'PNPDeviceID': 'SCSI\\DISK&VEN_&PROD_KINGSTON_SA400S3\\4&2E24B7EF&0&010000',
        'SerialNumber': '50026B738073DD91', 'DriveLetters': {'DriveLetter0': 'C:'}, 'BusType': 11}
        :raise: None
        """

        return self.__enumerate_storage_disks()

    def enumerate_sata_disks(self):
        """
        This method gives the list of sata disk on SUT.

        :return: List of Sata Disk : eg: [{'DeviceID': '\\\\.\\PHYSICALDRIVE0', 'PNPDeviceID':
        'SCSI\\DISK&VEN_INTEL&PROD_SSDSC2KG960G8\\4&2E24B7EF&0&000000', 'SerialNumber': 'PHYG9212021C960CGN',
        'DriveLetters': {}, 'BusType': 11}, {'DeviceID': '\\\\.\\PHYSICALDRIVE1', 'PNPDeviceID':
        'SCSI\\DISK&VEN_INTEL&PROD_SSDSC2KG480G7\\4&2E24B7EF&0&010000', 'SerialNumber': 'BTYM7404042R480BGN',
        'DriveLetters': {'DriveLetter0': 'C:'}, 'BusType': 11}
        :raise: None
        """
        dict_storage_devices = self.__enumerate_storage_disks()
        list_sata_disks = []
        for storage_key, storage_disk in dict_storage_devices.items():
            bus_type = int(storage_disk[WindowsStorageDevice.KEY_BUS_TYPE])
            if bus_type == WindowsDiskBusType.BUS_TYPE_SATA:
                list_sata_disks.append(storage_disk)

        return list_sata_disks

    def enumerate_nvme_disks(self):
        """
        This method is to get list of NVMe Disk on SUT

        :result: list of NVMe Disk on SUT :- [{'DeviceID': '\\\\.\\PHYSICALDRIVE2', 'PNPDeviceID': pnp_ID,
         'SerialNumber': '3727014E2C23DE6231463', 'DriveLetters': {'DriveLetter0': 'G:'}, 'BusType': 17}]
        :raise: None
        """
        dict_storage_devices = self.__enumerate_storage_disks()
        list_nvme_disks = []
        for storage_key, storage_disk in dict_storage_devices.items():
            bus_type = int(storage_disk[WindowsStorageDevice.KEY_BUS_TYPE])
            if bus_type == WindowsDiskBusType.BUS_TYPE_NVME:
                list_nvme_disks.append(storage_disk)

        return list_nvme_disks

    def enumerate_usb_disks(self):
        """
        This method is to get list of USB Disk on SUT

        :result: list of USB Disk :- [{'DeviceID': '\\\\.\\PHYSICALDRIVE2',
        'PNPDeviceID': 'USBSTOR\\DISK&VEN_FLASH&PROD_USB_DISK&REV_2.10\\3727014E2C23DE6231463&0',
        'SerialNumber': '3727014E2C23DE6231463', 'DriveLetters': {'DriveLetter0': 'G:'}, 'BusType': 7}]
        :raise: None
        """
        dict_storage_devices = self.__enumerate_storage_disks()
        list_usb_disks = []
        for storage_key, storage_disk in dict_storage_devices.items():
            bus_type = int(storage_disk[WindowsStorageDevice.KEY_BUS_TYPE])
            if bus_type == WindowsDiskBusType.BUS_TYPE_USB:
                list_usb_disks.append(storage_disk)

        return list_usb_disks

    def find_disk_size(self, partition_drive):
        """
        This method is to get the partition drive size.

        :return size
        """
        cmd = 'WMIC LOGICALDISK GET Name,Size| find /i "{}"'.format(partition_drive)
        data = self._common_content_lib.execute_sut_cmd(cmd, "Get disk size", self._cmd_time_out_in_sec,
                                                        self.C_DRIVE_PATH).strip()
        return data.split()[-1].strip()

    def get_diskdirves(self):
        """
        This method is to give the DiskDrive Information

        :return diskdirve_info
        """
        diskdirve_info = self._common_content_lib.execute_sut_cmd(self.DISKDRIVE_INFO, self.DISKDRIVE_INFO,
                                                                  self._cmd_time_out_in_sec)
        return diskdirve_info

    def mount_the_drive(self, mount_device_name, mount_point):
        """
        This method is to mount the drive.

        :param mount_device_name
        :param mount_point
        :raise content_exception-TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for Windows")

    def get_usb_details(self):
        """
        This method is to get usb details

        :raise NotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for Windows")

    def get_booted_device(self):
        """
        This method is to give the booted device Information

        :raise TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for Windows")

    def get_device_type(self, lsblk_res, name_ssd):
        """
        This method is to give the booted device type

        :raise TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for Windows")

    def get_booted_raid_disk(self):
        """
        this method is to get booted raid_disk
        :raise TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for Windows")

    def get_smartctl_drive_list(self):
        """
        Get smartctl drive list

        :param column: Non.
        :return: Drive list
        """
        drive_list_cmd = "smartctl.exe --scan"
        path = r"C:\smart_tools\bin"

        self._log.info("Executing smartctl scan command: {}".format(drive_list_cmd))
        execute_cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=drive_list_cmd,
                                                                      cmd_str=drive_list_cmd,
                                                                      execute_timeout=self._command_timeout,
                                                                      cmd_path=path)
        self._log.debug("Smartctl scan command: {} Output: {}".format(drive_list_cmd, execute_cmd_output))
        drive_list = [line.split(" ")[0] for line in execute_cmd_output.split("\n")]
        drive_list = ' '.join(drive_list).split()
        self._log.debug("Drive list: {}".format(drive_list))

        return drive_list


class StorageProviderLinux(StorageProvider):
    """
    This Class is having the method of storage functionality based on Linux.

    :return None
    :raise None
    """
    USB = "usb"
    SATA = "sata"
    NAME = "NAME"
    LVM = "LVM"
    DEV = "/dev/"
    MNT_DEV = "/mnt/dev/"
    MNT = "/mnt/"
    NVM = "nvm"
    SWAP = "swap"
    KEY_DISK_NAME = "DiskName"
    KEY_BUS_TYPE = "BusType"
    KEY_PARTITION_NAME = "PartitionName"
    KEY_PARTITION_DISK_NAME = "PartitionName{}"
    KEY_MOUNT_POINT = "MountPoint"
    KEY_AVAILABLE_DISK_SIZE = "AvailableDiskSize"
    REGEX_TO_GET_AVAILABLE_SIZE = r"\/dev\S+\s+\S+\s+\S+\s+(\S+)\s+.*"
    REGEX_TO_GET_AVAIL_SIZE = r"devtmpfs\s+\S+\s+\S\s+(\S+).*"
    CMD_TO_GET_SIZE_OF_DISK = "df --si {}"
    CMD_TO_INSTALL_NVME_CLI = r"echo y|yum install nvme-cli"
    REGEX_TO_GET_NVM_DISK_PATH = r"\/dev\/nvme[0-9][a-z][0-9]"
    CMD_TO_GET_NVM_DISK = r"nvme list | egrep /dev/nvme"
    CMD_TO_GET_LIST_OF_INFORMATION_OF_DEVICES = r"lsblk -S"
    CMD_TO_GET_BUS_DEVICE_PARTITION = r"lsblk | egrep {}"
    CMD_TO_SCAN_LVM_DISK_SCAN = "lvmdiskscan | egrep {}"
    CMD_TO_CREATE_DIR = r"mkdir -p {}"
    CMD_TO_REMOVE_DIR = r"rm -rf {}"
    CMD_TO_MOUNT_DEVICE = "mount {} {}"
    CMD_TO_CHECK_NTFS_DRIVE = "fdisk -l /dev/{}"
    CMD_TO_GET_SMART_LOG = r"nvme smart-log {}"
    CMD_TO_GET_ERROR_LOG = r"nvme error-log {}"
    CMD_TO_GET_LOG = r"nvme get-log {} --log-len={} --log-id={}"
    CMD_ID_CTRL = r"nvme id-ctrl {}"
    CMD_TO_FORMAT = r"nvme format {}"
    CMD_TO_RESET = r"nvme reset {}"

    CHECK_UNIT_IN_GB = "G"
    BCD_STR = "bcdUSB"
    USB_INTERFACE = "bInterfaceClass"
    USB_PROTOCAL = "bInterfaceProtocol"
    LSUSB_DEV_CMD = "lsusb -D /dev/bus/usb/{}/{}"
    REGEX_BUS_DEVICE = "Bus (\d+) Device (\d+)"
    ID_VENDOR_STR = "idVendor"
    ID_PRODUCT_STR = "idProduct"
    CMD_HDPARM = "hdparm -I /dev/{} | grep 'Serial Number:\|Transport:'"
    CMD_LSBLK = "lsblk -l | grep '/boot$'"
    CMD_MDSTAT = "cat /proc/mdstat"
    REGEX_RAID_LEVEL = "active\s(raid\d+)"

    def __init__(self, log, os_obj, uefi_util_obj=None, cfg_opts=None):
        super(StorageProviderLinux, self).__init__(log, os_obj, uefi_util_obj, cfg_opts)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj

    def factory(log, os_obj, cfg_opts=None, execution_env=None, uefi_obj=None):
        pass

    def enumerator_storage_device(self):
        """
        This method is to get enumerator for all device.

        return: [{"Disk_Name":"/dev/sda", "BusType":"SATA", "Partion0":{"Partion_Name":"/dev/sda1",
        "MountPoint": "/mnt/dev_sda1", "available_disk_size":"1000"},
        "Partition1":{"Partion_Name: "/dev/sda1", "MountPoint":"/mnt/dev_sda2", "available_disk_size":"700"}}]
        """
        list_of_storage_device = []
        self._common_content_lib.execute_sut_cmd(sut_cmd=self.CMD_TO_INSTALL_NVME_CLI,
                                                 cmd_str=self.CMD_TO_INSTALL_NVME_CLI,
                                                 execute_timeout=self._cmd_time_out_in_sec)
        cmd_out_put = self._os.execute(self.CMD_TO_GET_LIST_OF_INFORMATION_OF_DEVICES, self._cmd_time_out_in_sec)
        for line in cmd_out_put.stdout.split('\n'):
            dict_contain_device_info = {}
            disk_name = line.split('\s')[0].split(' ')[0]
            if disk_name == self.NAME or disk_name == "":
                continue
            cmd_output_to_check_windows = self._common_content_lib.execute_sut_cmd(sut_cmd=
            self.CMD_TO_CHECK_NTFS_DRIVE.format(
                disk_name), cmd_str="check ntfs device", execute_timeout=self._cmd_time_out_in_sec)
            if OperatingSystems.WINDOWS in cmd_output_to_check_windows:
                continue
            cmd_output = self._os.execute(self.CMD_TO_GET_BUS_DEVICE_PARTITION.format(disk_name),
                                          self._cmd_time_out_in_sec)
            if self.USB in line:
                dict_contain_device_info[self.KEY_BUS_TYPE] = self.USB
            elif self.SATA in line:
                dict_contain_device_info[self.KEY_BUS_TYPE] = self.SATA
            dict_contain_device_info[self.KEY_DISK_NAME] = self.DEV + disk_name
            partition_list = re.findall(disk_name + '\S', cmd_output.stdout.strip())
            for index, partition in enumerate(list(set(partition_list))):
                partition_dict = {}
                cmd_out_put_result = self._os.execute(self.CMD_TO_SCAN_LVM_DISK_SCAN.format(partition),
                                                      self._cmd_time_out_in_sec)
                if self.LVM in cmd_out_put_result.stdout.strip():
                    partition_dict[self.KEY_MOUNT_POINT] = self.LVM
                else:
                    try:
                        self.mount_the_drive(self.DEV + partition, self.MNT_DEV + partition)
                        partition_dict[self.KEY_MOUNT_POINT] = self.MNT_DEV + partition
                    except Exception as ex:
                        if "ntfs" in ex.__str__():
                            partition_dict[self.KEY_MOUNT_POINT] = self.SWAP
                            self._log.error("Skipping mount for Windows SSD")
                        else:
                            raise content_exceptions.TestFail("Failed during mount with exception: {}".format(ex))
                partition_dict[self.KEY_PARTITION_NAME] = self.DEV + partition
                partition_dict[self.KEY_AVAILABLE_DISK_SIZE] = self.get_the_size_of_storage_device(self.DEV +
                                                                                                   partition)
                dict_contain_device_info[self.KEY_PARTITION_DISK_NAME.format(index)] = partition_dict
            list_of_storage_device.append(dict_contain_device_info)
        cmd_output = self._os.execute(self.CMD_TO_GET_NVM_DISK, self._cmd_time_out_in_sec)
        if cmd_output.stderr == "":
            nvm_list_output = re.findall(self.REGEX_TO_GET_NVM_DISK_PATH, cmd_output.stdout.strip())
            nvm_storage_disk_list = list(set(nvm_list_output))
        else:
            log_error = "Failed to run '{}' command with return value = '{}' and " \
                        "std_error='{}'..".format(self.CMD_TO_GET_NVM_DISK, cmd_output.return_code,
                                                  cmd_output.stderr)
            raise content_exceptions.TestFail(log_error)
        dict_contain_device_info = {}
        for each_nvm in nvm_storage_disk_list:
            dict_contain_device_info[self.KEY_BUS_TYPE] = self.NVM
            dict_contain_device_info[self.KEY_DISK_NAME] = each_nvm
            cmd_output = self._os.execute(self.CMD_TO_GET_BUS_DEVICE_PARTITION.format(each_nvm[5:]),
                                          self._cmd_time_out_in_sec)
            partition_list = re.findall(each_nvm[5:] + '\S+', cmd_output.stdout.strip())
            if not partition_list:
                # NVMe device has not partition. So, Not required to go process for mounting. so skipping
                self._log.error("NVMe device {} has no partition".format(each_nvm[5:0]))
                continue
            for index, partition in enumerate(list(set(partition_list))):
                partition_dict = {}
                cmd_out_put_result = self._os.execute(self.CMD_TO_SCAN_LVM_DISK_SCAN.format(partition),
                                                      self._cmd_time_out_in_sec)
                out_put = self._os.execute("blkid |grep swap", self._cmd_time_out_in_sec)
                if self.LVM in cmd_out_put_result.stdout.strip():
                    partition_dict[self.KEY_MOUNT_POINT] = self.LVM
                elif partition in out_put.stdout.strip():
                    partition_dict[self.KEY_MOUNT_POINT] = self.SWAP
                else:
                    self.mount_the_drive(self.DEV + partition, self.MNT_DEV + partition)
                    partition_dict[self.KEY_MOUNT_POINT] = self.MNT_DEV + partition
                partition_dict[self.KEY_PARTITION_NAME] = self.DEV + partition
                partition_dict[self.KEY_AVAILABLE_DISK_SIZE] = self.get_the_size_of_storage_device(self.DEV +
                                                                                                   partition)
                dict_contain_device_info[self.KEY_PARTITION_DISK_NAME.format(index)] = partition_dict
            list_of_storage_device.append(dict_contain_device_info)
        return list_of_storage_device

    def enumerate_sata_disks(self):
        """
        This method is to give the list of sata device details.

        :return : [{"Disk_Name":"/dev/sda", "BusType":"SATA", "Partion0":
        {"Partion_Name":"/dev/sda1", "MountPoint": "/mnt/dev_sda1", "available_disk_size":"1000"},
        "Partition1":{"Partion_Name: "/dev/sda1", "MountPoint":"/mnt/dev_sda2", "disk_size":"700"}}]
        """
        sata_storage_disk_list = []
        for device_dict in self.enumerator_storage_device():
            for device_key, value in device_dict.items():
                if value == self.SATA:
                    sata_storage_disk_list.append(device_dict)
        return sata_storage_disk_list

    def enumerate_nvme_disks(self):
        """
        This method give the list of NVMe disk+ on SUT

        return: List of NVMe disk eg:- [{"Disk_Name":"/dev/nvme0n1", "BusType":"nvm", "Partion0":
        {"Partion_Name":"/dev/nvme0n1p1", "MountPoint": "/mnt/dev/nvme0n1p1", "available_disk_size":"1000"},
        "Partition1":{"Partion_Name: "/dev/nvme0n2", "MountPoint":"/mnt/dev/nvme0n1p2", "disk_size":"700"}}]
        """
        nvm_storage_disk_list = []
        for device_dict in self.enumerator_storage_device():
            for device_key, value in device_dict.items():
                if value == self.NVM:
                    nvm_storage_disk_list.append(device_dict)
        return nvm_storage_disk_list

    def enumerate_usb_disks(self):
        """
        This method give the list of usb disk on SUT.

        return: List of USB disk eg:-  [{"Disk_Name":"/dev/sda", "BusType":"usb", "Partion0":
        {"Partion_Name":"/dev/sda1", "MountPoint": "/mnt/dev/sda1", "available_disk_size":"1000"},
        "Partition1":{"Partion_Name: "/dev/sda2", "MountPoint":"/mnt/dev/sda2", "disk_size":"700"}}]
        raise: content_exception -TestFail
        """
        usb_storage_disk_list = []
        for device_dict in self.enumerator_storage_device():
            for device_key, value in device_dict.items():
                if value == self.USB:
                    usb_storage_disk_list.append(device_dict)
        return usb_storage_disk_list

    def mount_the_drive(self, mount_device_name, mount_point):
        """
        This method is to mount the drive.

        :param mount_device_name
        :param mount_point
        :return None
        :raise content_exception-TestError
        """
        self._os.execute("umount {}".format(mount_point), self._cmd_time_out_in_sec)
        cmd_output = self._os.execute(self.CMD_TO_REMOVE_DIR.format(mount_point), self._cmd_time_out_in_sec)
        if cmd_output.stderr == "":
            self._log.info("Removed the mount directory if exist")
        else:
            log_err = "Failed to remove the mount directory"
            self._log.error(log_err)
            raise content_exceptions.TestError(log_err)
        cmd_output = self._os.execute(self.CMD_TO_CREATE_DIR.format(mount_point), self._cmd_time_out_in_sec)
        if cmd_output.stderr == "":
            self._log.info("Mount directory is created {}".format(mount_point))
        else:
            log_err = "Unable to create the directory"
            self._log.error(log_err)
            raise content_exceptions.TestError(log_err)

        cmd_output = self._os.execute(self.CMD_TO_MOUNT_DEVICE.format(mount_device_name, mount_point),
                                      self._cmd_time_out_in_sec)
        if cmd_output.cmd_failed():
            # Checking if mounting failed because of wrong fs type, then creating mkfs.ext4 type and proceeding for
            # mounting
            if "wrong fs type" not in cmd_output.stderr:
                raise content_exceptions.TestFail("Failed to run with return code: {} and return stderr: {}".format(
                    cmd_output.return_code, cmd_output.stderr
                ))
            self._common_content_lib.execute_sut_cmd(sut_cmd="mkfs.ext4 {}".format(mount_device_name),
                                                     cmd_str="change partition type to mkfs.ext4 type",
                                                     execute_timeout=self._cmd_time_out_in_sec)
            cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.CMD_TO_MOUNT_DEVICE.format(
                mount_device_name, mount_point), cmd_str=self.CMD_TO_MOUNT_DEVICE.format(mount_device_name, mount_point)
                , execute_timeout=self._cmd_time_out_in_sec)
            self._log.info(cmd_output.strip())

    def get_the_size_of_storage_device(self, device_partitioned_name):
        """
        This method is to get the size of partition

        :param device_partitioned_name
        :return size in mb
        :raise content_exception-TestError
        """
        cmd_out_put = self._os.execute(self.CMD_TO_GET_SIZE_OF_DISK.format(device_partitioned_name),
                                       self._cmd_time_out_in_sec)
        self._log.info(cmd_out_put.stdout.strip())
        if cmd_out_put.cmd_failed():
            log_error = "failed to run the command with return value = '{}' and " \
                        "std error = '{}' ..".format(cmd_out_put.return_code, cmd_out_put.stderr)
            self._log.error(log_error)
            raise content_exceptions.TestError(log_error)

        available_size = re.findall(self.REGEX_TO_GET_AVAILABLE_SIZE, cmd_out_put.stdout.strip())
        if len(available_size) == 0:
            available_size = re.findall(self.REGEX_TO_GET_AVAIL_SIZE, cmd_out_put.stdout.strip())
        if self.CHECK_UNIT_IN_GB in available_size[0]:
            available_size_in_mb = float(available_size[0][:-1]) * 1024
        elif available_size[0] == str(0):
            available_size_in_mb= available_size[0]
        else:
            available_size_in_mb = float(available_size[0][:-1])
        return available_size_in_mb

    def get_usb_details(self):
        """
        This method is to get usb details

        :raise content_exceptions.TestFail if lsusb output is null
        """
        self._log.info("lsusb command running")
        usb_cmd_out_before = self._common_content_lib.execute_sut_cmd("lsusb",
                                                                      "USB devices connected",
                                                                      self._cmd_time_out_in_sec)
        self._log.debug("Usb connect {}".format(usb_cmd_out_before))
        if not usb_cmd_out_before.strip():
            raise content_exceptions.TestFail("Unable to get the lsusb information")
        return usb_cmd_out_before

    def get_bus_device_type_info(self, usb_dev_info):
        """
        Get the usb bus type info and bcd info from the hot plug device connected.

        :param usb_dev_info: usb hot plugged device info
        :return :returns the difference of device connected before and after hot plug.
        :raise :content_exceptions.TestFail unable to get bus and device from hot plug.
        """
        usb_bcd = "bcd"
        usb_type = "type"
        usb_output = 2
        device_type = {}
        device_list = []
        self._log.info("Get usb bus device information")
        out_val = re.search(self.REGEX_BUS_DEVICE, usb_dev_info.strip())
        if not out_val:
            raise content_exceptions.TestFail("Unable to get bus and device info")
        cmd = self.LSUSB_DEV_CMD.format(out_val.group(1), out_val.group(2))
        self._log.debug("Bus device cmd {}".format(cmd))
        cmd_output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._cmd_time_out_in_sec)
        self._log.debug("Lsusb -D command output %s" % cmd_output.strip())
        if not cmd_output.strip():
            raise content_exceptions.TestFail("Unable to get the device information for the cmd {}".format(cmd_output))
        for usb_device in cmd_output.split("\n"):
            if usb_device.strip() and self.BCD_STR in usb_device:
                device_type[usb_bcd] = usb_device.partition(self.BCD_STR)[-1].strip()
            elif usb_device.strip() and self.USB_INTERFACE in usb_device:
                device_list.append(usb_device.split(self.USB_INTERFACE)[-1].strip())
                device_type[usb_type] = device_list
            elif usb_device.strip() and self.USB_PROTOCAL in usb_device:
                device_list.append(usb_device.split(self.USB_PROTOCAL)[-1].strip())
                device_type[usb_type] = device_list
        self._log.debug("Device type and bcd connected after hot plug {} ".format(device_type))
        if len(device_type) != usb_output:
            raise content_exceptions.TestFail("Unable to get bus and device info {}".format(device_type))

        return device_type

    def get_vendor_id_product_id(self, usb_dev_info):
        """
        This method is to get the vendor id and product id of the USB device

        :param usb_dev_info: usb hot plugged device info.
        :raise: content_exceptions.TestFail
        :return device_type: information about idVendor and idProduct
        """
        usb_vendor = "idVendor"
        usb_product = "idProduct"
        usb_output = 2
        device_type = {}
        out_val = re.search(self.REGEX_BUS_DEVICE, usb_dev_info.strip())
        if not out_val:
            raise content_exceptions.TestFail("Unable to get bus and device info")
        cmd = self.LSUSB_DEV_CMD.format(out_val.group(1), out_val.group(2))
        self._log.debug("Bus device cmd {}".format(cmd))
        cmd_output = self._common_content_lib.execute_sut_cmd(cmd, cmd, self._cmd_time_out_in_sec)
        self._log.debug("Lsusb -D command output %s" % cmd_output.strip())
        if not cmd_output.strip():
            raise content_exceptions.TestFail("Unable to get the device information for the cmd {}".format(cmd_output))
        for usb_device in cmd_output.split("\n"):
            if usb_device.strip() and self.ID_VENDOR_STR in usb_device:
                device_type[usb_vendor] = usb_device.partition(self.ID_VENDOR_STR)[-1].strip().split()[0]
            elif usb_device.strip() and self.ID_PRODUCT_STR in usb_device:
                device_type[usb_product] = usb_device.split(self.ID_PRODUCT_STR)[-1].strip().split()[0]

        self._log.debug("Device idVendor and idProduct connected after hot plug {} ".format(device_type))
        if len(device_type) != usb_output:
            raise content_exceptions.TestFail("Unable to get idVendor and idProduct info {}".format(device_type))

        return device_type

    def find_disk_size(self, partition_drive):
        """
        This method is to get the partition drive size.

        :raise NotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for Linux")

    def get_diskdirves(self):
        """
        This method is to give the DiskDrive Information.

        :raise content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for Linux")

    def get_booted_device(self):
        """
        This method is to give the booted device Information

        :return lsblk_res
        """

        lsblk_res = self._common_content_lib.execute_sut_cmd(self.CMD_LSBLK, "Run lsblk", self._cmd_time_out_in_sec)

        lsblk_res = lsblk_res.strip().split()[0]

        self._log.debug("The file system that booted to OS is '{}'".format(lsblk_res))

        return lsblk_res

    def get_booted_raid_disk(self):
        """
        this method is to get booted raid_disk
        return raid  level info
        """
        md_stat_res = self._common_content_lib.execute_sut_cmd(self.CMD_MDSTAT, "Run mdstat", self._cmd_time_out_in_sec)
        md_list_output = re.findall(self.REGEX_RAID_LEVEL, md_stat_res)
        md_disk_name = list(set(md_list_output))[0]
        return md_disk_name

    def get_device_type(self, lsblk_res, name_ssd):
        """
        This method is to give the booted device type

        :return True if successful
        """

        hdparm_command_line = self.CMD_HDPARM.format(lsblk_res)

        cmd_result = self._common_content_lib.execute_sut_cmd(hdparm_command_line, "Run hdparm",
                                                              self._cmd_time_out_in_sec).strip("\r\n\t ")

        device_info = {"serial": None, "usb_type": None}

        if "Serial Number:" in cmd_result:
            device_info["serial"] = cmd_result.splitlines()[0].split("Serial Number:")[-1].strip("\r\n\t ")
        if "Transport:" in cmd_result:
            device_info["usb_type"] = cmd_result.splitlines()[-1].split("Transport:")[-1].strip("\r\n\t ").split()[2].strip("\r\n\t ")

        self._log.info(device_info)

        return device_info

    def get_smartctl_drive_list(self):
        """
        Get smartctl drive list

        :param column: Non.
        :return: Drive list
        """
        drive_list_cmd = "smartctl --scan"
        path = "/root"

        self._log.info("Executing smartctl scan command: {}".format(drive_list_cmd))
        execute_cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=drive_list_cmd,
                                                                      cmd_str=drive_list_cmd,
                                                                      execute_timeout=self._command_timeout,
                                                                      cmd_path=path)
        self._log.debug("Smartctl scan command: {} Output: {}".format(drive_list_cmd, execute_cmd_output))
        drive_list = [line.split(" ")[0] for line in execute_cmd_output.split("\n")]
        drive_list = ' '.join(drive_list).split()
        self._log.debug("Drive list: {}".format(drive_list))

        return drive_list

class StorageProviderUefi(StorageProvider):
    """
    This Class have different method of Storage functionality on UEFI Platform

    :result None
    :raise None
    """
    SATA_PATTERN = "Sata"
    USB_PATTERN = "USB"
    REG_MAP = "^FS[0-9]"
    MAP_CMD = "map -r"

    def __init__(self, log, os_obj, uefi_util_obj=None, cfg_opts=None):
        super(StorageProviderUefi, self).__init__(log, os_obj, uefi_util_obj, cfg_opts)
        self._log = log
        self._os = os_obj
        self._uefi_util_obj = uefi_util_obj

    def enumerate_sata_disks(self):
        """
        This method is get the list of SATA disk on SUT.

        :result: list of SATA device
        :raise: None
        """
        uefi_sata_drive_device_list = []
        if not self._uefi_util_obj.enter_uefi_shell():
            raise content_exceptions.TestSetupError("Unable to enter into uefi shell")
        uefi_cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.MAP_CMD)
        self._log.info("UEFI command output {} ".format(uefi_cmd_output))

        for linenumber, data in enumerate(uefi_cmd_output):
            output = re.search(self.REG_MAP, data.strip(), re.IGNORECASE)
            if output:
                if self.SATA_PATTERN in uefi_cmd_output[linenumber + 1]:
                    uefi_sata_drive_device_list.append(output.group() + ":")

        if uefi_sata_drive_device_list:
            self._log.info("Number of USB drive list : {} ".format(uefi_sata_drive_device_list))
        else:
            self._log.info("No USB device List is available on SUT : {}".format(uefi_sata_drive_device_list))
        return uefi_sata_drive_device_list

    def enumerate_nvme_disks(self):
        """
        This method is to get list of nvme disk

        :return: list of nvme disk
        :raise: content_exception- TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("Not Implemented for UEFI")

    def enumerate_usb_disks(self):
        """
        This method is to get the list usb disk

        :return: list of usb disk
        :raise: None
        """
        uefi_usb_drive_device_list = []
        if not self._uefi_util_obj.enter_uefi_shell():
            raise content_exceptions.TestSetupError("Unable to enter into uefi shell")
        uefi_cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.MAP_CMD)
        self._log.info("UEFI command output {} ".format(uefi_cmd_output))

        for linenumber, data in enumerate(uefi_cmd_output):
            output = re.search(self.REG_MAP, data.strip())
            if output:
                if self.USB_PATTERN in uefi_cmd_output[linenumber + 1]:
                    uefi_usb_drive_device_list.append(output.group() + ":")

        if uefi_usb_drive_device_list:
            self._log.info("Number of uefi usb drive device list is {} ".format(uefi_usb_drive_device_list))
        else:
            self._log.info("No USB Derive is available on Disk : {}".format(uefi_usb_drive_device_list))
        return uefi_usb_drive_device_list

    def mount_the_drive(self, mount_device_name, mount_point):
        """
        This method is to mount the drive the drive.

        :param mount_device_name
        :param mount_point
        :raise content_exception- TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This method is not for UEFI drive")

    def get_usb_details(self):
        """
        This method is to get usb details

        :raise NotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for Windows")

    def find_disk_size(self, partition_drive):
        """
        This method is to get the partition drive size.

        :raise NotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for Linux")

    def get_diskdirves(self):
        """
        This method is to give the DiskDrive Information.

        :raise content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for Linux")

    def get_booted_device(self):
        """
        This method is to give the booted device Information

        :raise TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for UEFI")

    def get_device_type(self, lsblk_res, name_ssd):
        """
        This method is to give the booted device type

        :raise TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for UEFI")

    def get_booted_raid_disk(self):
        """
        this method is to get booted raid disk
        :raise TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for UEFI")


class StorageProviderESXi(StorageProvider):
    """
    This Class has different method of Storage Functionality on ESXi Platform

    :return None
    :raise None
    """
    CMD_TO_FIND_FREE_SPACE = "WMIC LOGICALDISK GET Name,FreeSpace | find /i \"{}\""
    CONST_TO_CONVERT_IN_MB = 1024 * 1024
    C_DRIVE_PATH = "C:\\"
    DISKDRIVE_INFO = "wmic diskdrive"

    def __init__(self, log, os_obj, uefi_util_obj=None, cfg_opts=None):
        super(StorageProviderESXi, self).__init__(log, os_obj, uefi_util_obj, cfg_opts)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj

    def factory(log, os_obj, cfg_opts=None, execution_env=None, uefi_obj=None):
        pass

    def __enumerate_storage_disks(self):
        """
        This method is to get enumerator for all device.
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for ESXi")

    def enumerator_storage_device(self):
        """
        This method gives the list of  disk drive information on SUT.

        :return: Dict of  Disk drive info: eg: {'StorageDevice0': {'DeviceID': '\\\\.\\PHYSICALDRIVE1',
        'PNPDeviceID': 'SCSI\\DISK&VEN_&PROD_KINGSTON_SA400S3\\4&2E24B7EF&0&010000',
        'SerialNumber': '50026B738073DD91', 'DriveLetters': {'DriveLetter0': 'C:'}, 'BusType': 11}
        :raise: None
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for ESXi")

    def enumerate_sata_disks(self):
        """
        This method gives the list of sata disk on SUT.

        :return: List of Sata Disk : eg: [{'DeviceID': '\\\\.\\PHYSICALDRIVE0', 'PNPDeviceID':
        'SCSI\\DISK&VEN_INTEL&PROD_SSDSC2KG960G8\\4&2E24B7EF&0&000000', 'SerialNumber': 'PHYG9212021C960CGN',
        'DriveLetters': {}, 'BusType': 11}, {'DeviceID': '\\\\.\\PHYSICALDRIVE1', 'PNPDeviceID':
        'SCSI\\DISK&VEN_INTEL&PROD_SSDSC2KG480G7\\4&2E24B7EF&0&010000', 'SerialNumber': 'BTYM7404042R480BGN',
        'DriveLetters': {'DriveLetter0': 'C:'}, 'BusType': 11}
        :raise: None
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for ESXi")

    def enumerate_nvme_disks(self):
        """
        This method is to get list of NVMe Disk on SUT

        :result: list of NVMe Disk on SUT :- [{'DeviceID': '\\\\.\\PHYSICALDRIVE2', 'PNPDeviceID': pnp_ID,
         'SerialNumber': '3727014E2C23DE6231463', 'DriveLetters': {'DriveLetter0': 'G:'}, 'BusType': 17}]
        :raise: None
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for ESXi")

    def enumerate_usb_disks(self):
        """
        This method is to get list of USB Disk on SUT

        :result: list of USB Disk :- [{'DeviceID': '\\\\.\\PHYSICALDRIVE2',
        'PNPDeviceID': 'USBSTOR\\DISK&VEN_FLASH&PROD_USB_DISK&REV_2.10\\3727014E2C23DE6231463&0',
        'SerialNumber': '3727014E2C23DE6231463', 'DriveLetters': {'DriveLetter0': 'G:'}, 'BusType': 7}]
        :raise: None
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for ESXi")

    def find_disk_size(self, partition_drive):
        """
        This method is to get the partition drive size.

        :return size
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for ESXi")

    def get_diskdirves(self):
        """
        This method is to give the DiskDrive Information

        :return diskdirve_info
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for ESXi")

    def mount_the_drive(self, mount_device_name, mount_point):
        """
        This method is to mount the drive.

        :param mount_device_name
        :param mount_point
        :raise content_exception-TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for ESXi")

    def get_usb_details(self):
        """
        This method is to get usb details

        :raise NotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for ESXi")


    def get_booted_device(self, common_content_lib):
        """
        This method is to give the booted device Information

        :raise TestNotImplementedError
        """
        self.CMD_LSBLK = "lsblk -l | grep '/boot$'"
        lsblk_res = common_content_lib.execute_sut_cmd(self.CMD_LSBLK, "Run lsblk -l | grep '/boot$'",
                                                       self._cmd_time_out_in_sec)

        lsblk_res = lsblk_res.strip().split()[0]

        self._log.debug("The file system that booted to OS is '{}'".format(lsblk_res))

        return lsblk_res

    def get_device_type(self, lsblk_res, name_ssd):
        """
        This method is to give the booted device type

        :raise TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for ESXi")

    def get_booted_raid_disk(self):
        """
        this method is to get booted raid_disk
        :raise TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for ESXi")

    def get_smartctl_drive_list(self):
        """
        Get smartctl drive list

        :param column: Non.
        :return: Drive list
        """
        raise content_exceptions.TestNotImplementedError("This Function is not implemented for ESXi")
