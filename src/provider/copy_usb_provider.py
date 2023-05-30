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
import time
from importlib import import_module
import six

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.provider.base_provider import BaseProvider
from abc import ABCMeta, abstractmethod
from six import add_metaclass


class MountCheckConstants(object):
    """String that needs to be conditioned while mounting a usb device to the sut"""
    LOGICAL_NAME_STR = "logical name:"
    CAPABILITIES_REM_STR = "capabilities: removable"
    CAPABILITIES_REM_STR_REGX = r"capabilities:\sremovable$"
    FILE_SYSTEM_STR = "/dev/"


@add_metaclass(ABCMeta)
class UsbRemovableDriveProvider(BaseProvider):

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new copyUtil object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(UsbRemovableDriveProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._sut_os = self._os.os_type

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        """
        package = r"src.provider.copy_usb_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "UsbRemovableDriveWindows"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "UsbRemovableDriveLinux"
        else:
            raise NotImplementedError

        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(cfg_opts=cfg_opts, log=log, os_obj=os_obj)

    @abstractmethod
    def get_mount_point(self, common_content_obj, common_configuration_obj):
        """
        To get the mount point

        :param common_content_obj: common content object
        :param common_configuration_obj: common configuration object
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def copy_file_from_sut_to_usb(self, common_content_obj, common_configuration_obj, sut_folder_to_copy, vm_usb):
        """
        Linux environment copy host to sut usb.
        1. Copy tar file to Linux SUT from there to USB drive.
        2. Decompress tar file under mounted file directory.

        :param sut_folder_to_copy: file that needs to be copied to usb drive
        :param common_content_obj: common content object
        :param common_configuration_obj: common configuration object
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def copy_file_from_usb_to_sut(self, common_content_obj, common_configuration_obj, usb_folder_to_copy):
        """
        Linux environment copy host to sut usb.
        1. Copy tar file to Linux SUT from there to USB drive.
        2. Decompress tar file under mounted file directory.

        :param usb_folder_to_copy: file that needs to be copied to sut
        :param common_content_obj: common content object
        :param common_configuration_obj: common configuration object
        :raise NotImplementedError
        """
        raise NotImplementedError


class UsbRemovableDriveWindows(UsbRemovableDriveProvider):

    C_DRIVE_PATH = "C:\\"

    def __init__(self, log, cfg_opts, os_obj):
        super(UsbRemovableDriveWindows, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj

    def factory(self, log, cfg_opts, os_obj):
        pass

    def get_mount_point(self, common_content_obj, common_configuration_obj):
        """
        To get the mount point of the usb drive.

        :param common_content_obj: common content object
        :param common_configuration_obj: common configuration object
        :return: the mount point
        """
        result = common_content_obj.execute_sut_cmd("wmic logicaldisk where drivetype=2 get deviceid",
                                                    "Get the USB Drive", common_configuration_obj.get_command_timeout())
        if "No Instance(s) Available." in result:
            self._log.error("USB drive is not present in the SUT...")
            self._log.error("Please connect the USB drive and rerun..")
            raise RuntimeError

        drive_name = re.findall("[A-Z]:", result)[0] + "\\"

        return drive_name

    def copy_file_from_sut_to_usb(self, common_content_obj, common_configuration_obj,
                                  sut_folder_to_copy, usb_path_for_copy=None, vm_usb=None):
        """
        This function get the USB location and copies files from the specified folder path in sut to usb

        :param sut_folder_to_copy: file that needs to be copied to usb drive
        :param common_content_obj: common content object
        :param common_configuration_obj: common configuration object
        :param usb_path_for_copy: optional dest dir in USB drive
        :return: True if copy is successful else false
        """
        # Get the drive letter
        usb_drive_letter = self.get_mount_point(common_content_obj, common_configuration_obj)

        usb_folder_path = usb_drive_letter
        if usb_path_for_copy:
            usb_folder_path = os.path.join(usb_drive_letter, usb_path_for_copy)

        # Copy the file(s) from SUT to USB
        result = common_content_obj.execute_sut_cmd("xcopy {} {} /S /K /D /H /Y".format(sut_folder_to_copy,
                                                                                     usb_folder_path),
                                                    "Copy file from SUT to "
                                                    "USB", common_configuration_obj.get_command_timeout())
        if not result:
            err_msg = "Fail to copy the file from SUT to USB drive"
            self._log.error(err_msg)
            raise RuntimeError(err_msg)
        self._log.info("Successfully copied the file(s) from SUT to USB folder '{}'".format(usb_folder_path))

        return usb_folder_path

    def copy_file_from_usb_to_sut(self, common_content_obj, common_configuration_obj, usb_folder_to_copy):
        """
        This function get the Sut location and copies files from the specified folder path in usb to sut

        :param usb_folder_to_copy: file that needs to be copied to Sut
        :param common_content_obj: common content object
        :param common_configuration_obj: common configuration object
        :return: sut_dir_path: the path of the folder that has copied files
        """
        # Get the drive letter
        sut_dir_path = Path(os.path.join(self.C_DRIVE_PATH, "usb_files"))

        # Copy the file from SUT to USB
        result = common_content_obj.execute_sut_cmd("xcopy {} {} /S /K /D /H /Y".format(usb_folder_to_copy,
                                                                                     sut_dir_path),
                                                    "Copy file from USB to SUT",
                                                    common_configuration_obj.get_command_timeout())
        if not result:
            err_msg = "Fail to copy the file from USB to SUT"
            self._log.error(err_msg)
            raise RuntimeError(err_msg)
        self._log.info("Successfully copied the file from USB to SUT")
        return sut_dir_path


class UsbRemovableDriveLinux(UsbRemovableDriveProvider):
    USB_FILE_PATH = "/mnt"
    GET_DISK_INFO = "lshw -class disk"
    ROOT_PATH = "/root"

    def __init__(self, log, cfg_opts, os_obj):
        super(UsbRemovableDriveLinux, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj

    def factory(self, log, cfg_opts, os_obj):
        pass

    def get_mount_point(self, common_content_obj, common_configuration_obj):
        """
        To get the mount point of the usb drive.

        :param common_content_obj: common content object
        :param common_configuration_obj: common configuration object
        :return: the mount point
        """
        # To mount the usb to directory /mnt

        # install lshw
        lshw_package = "lshw"
        self._log.info("Installing lshw package")
        from src.lib import install_collateral
        install_collateral = install_collateral.InstallCollateral(self._log, self._os, self._cfg)
        install_collateral.yum_install(lshw_package)

        result = common_content_obj.execute_sut_cmd(self.GET_DISK_INFO, "get disk info",
                                                    common_configuration_obj.get_command_timeout())
        fdisk_list = result.strip().split("\n")
        out_str = None
        medium_found = False
        medium_disk_info_list = []
        mount_point = True

        # unmount /mnt path if usb is already mounted
        mnt_unmount = self._os.execute("umount {}".format(self.USB_FILE_PATH),
                                       common_configuration_obj.get_command_timeout())

        if mnt_unmount.return_code != 0:
            self._log.info("Path {} can be used for usb mounting...".format(self.USB_FILE_PATH))
        else:
            self._log.info("Unmounted the path {} for usb mounting...".format(self.USB_FILE_PATH))

        while mount_point:
            for disk in fdisk_list:
                mount_point = False
                if MountCheckConstants.LOGICAL_NAME_STR in disk:
                    out_str = disk.split(":")[1]

                if MountCheckConstants.CAPABILITIES_REM_STR in disk:
                    if MountCheckConstants.FILE_SYSTEM_STR not in out_str:
                        # unmount the usb first
                        unmount_command = "umount {}".format(out_str)
                        common_content_obj.execute_sut_cmd(unmount_command, "unmount command",
                                                           common_configuration_obj.get_command_timeout())
                        self._log.info("Existing mount point has been unmounted. Checking again for another mount "
                                       "points..")
                        mount_point = True
                    else:
                        mount_point = False

        self._log.info("All mount points has been unmounted..")

        # just to be safe, taking the fresh hardware class output and fetching the logical name.
        result = common_content_obj.execute_sut_cmd(self.GET_DISK_INFO, "get disk info",
                                                    common_configuration_obj.get_command_timeout())
        self._log.debug("Command : {} output is : {}".format(self.GET_DISK_INFO, result))
        fdisk_list = result.strip().split("\n")

        for disk in fdisk_list:

            if medium_found:
                re_for_path = r"logical\sname:\s\/[a-z]*\/[a-z]*"
                if re.search(re_for_path, disk.strip()):
                    medium_disk_info_list.append(disk)
                    break

            if "*-medium" in disk:
                medium_found = True

        if len(medium_disk_info_list) == 0:
            for disk in fdisk_list:

                if MountCheckConstants.LOGICAL_NAME_STR in disk:
                    out_str = disk.split(":")[1]

                # We are getting cdrom in the VM with capabilities: removable audio dvd and
                # USB will come with capabilities: removable. so using regex up to removable word to get the USB.
                removable_usb = re.search(MountCheckConstants.CAPABILITIES_REM_STR_REGX, disk)
                if removable_usb:
                    self._log.info("Found the string for USB : {}".format(removable_usb.group()))
                    break
            self._log.info("Using 'Hardware -class disk' way to find the usb logical name...")
        else:
            self._log.info("Using 'Hardware -class medium' way to find the usb logical name...")
            for usb in medium_disk_info_list:
                re_for_path = r"logical\sname:\s\/[a-z]*\/[a-z]*"
                if re.search(re_for_path, usb.strip()):
                    out_str = re.findall(re_for_path, usb.strip())
                    out_str = out_str[0].split(":")[1]

        usb_media_pos = out_str

        if usb_media_pos is None:
            self._log.error("No logical/partition name found for USB removable drive, please make sure USB is "
                            "connected properly..")
            raise RuntimeError

        cmd = "ls {}?".format(usb_media_pos)
        mnt_point_list = self._os.execute(cmd, common_configuration_obj.get_command_timeout())

        if mnt_point_list.return_code != 0:
            self._log.info("There are no additional file system present under{}..".format(usb_media_pos))
            return usb_media_pos
        else:
            return mnt_point_list.stdout.split("\n")[0]

    def copy_file_from_sut_to_usb(self, common_content_obj, common_configuration_obj, sut_folder_to_copy,
                                  usb_path_for_copy=None, vm_usb=None):
        """
        This function get the USB location and copies files from the specified folder path in sut to usb

        :param sut_folder_to_copy: file that needs to be copied to usb drive
        :param common_content_obj: common content object
        :param common_configuration_obj: common configuration object
        :param usb_path_for_copy: path of where the copied folder from SUT is copied on the usb
        :param vm_usb: 
        :return: None
        """
        usb_media_pos = self.get_mount_point(common_content_obj, common_configuration_obj)
        self._log.info("USB device name is : {}".format(usb_media_pos))

        # mount the usb
        mount_command = "mount {} {}".format(usb_media_pos, self.USB_FILE_PATH)
        common_content_obj.execute_sut_cmd(mount_command, "mount command",
                                           common_configuration_obj.get_command_timeout())
        self._log.info("The USB media is mounted successfully..")

        usb_file_path = self.USB_FILE_PATH
        # copy to usb
        if usb_path_for_copy is not None:
            usb_file_path = Path(os.path.join(self.USB_FILE_PATH, usb_path_for_copy)).as_posix()
        if vm_usb:
            cmd_line = "cp -Rf {} {}".format(str(sut_folder_to_copy), usb_file_path)
        else:
            cmd_line = "cp -RT {} {}".format(str(sut_folder_to_copy), usb_file_path)
        common_content_obj.execute_sut_cmd(cmd_line, "copy", common_configuration_obj.get_command_timeout())

        self._log.info("The file '{}' has been copied successfully to the USB "
                       "Drive {} ..".format(sut_folder_to_copy, usb_file_path))

        # Mount point is busy, so waiting for 30 seconds..
        time.sleep(30)

        # unmount the usb
        unmount_command = "umount {}".format(self.USB_FILE_PATH)
        common_content_obj.execute_sut_cmd(unmount_command, "unmount command",
                                           common_configuration_obj.get_command_timeout())
        self._log.info("The USB media is unmounted successfully..")

        return usb_file_path

    def copy_file_from_usb_to_sut(self, common_content_obj, common_configuration_obj, usb_folder_to_copy):
        """
        This function get the USB location and copies files from the specified folder path in sut to usb

        :param usb_folder_to_copy: file that needs to be copied to sut
        :param common_content_obj: common content object
        :param common_configuration_obj: common configuration object
        :return: sut_dir_path: Path of the copied files
        """
        mount_point = "/mnt/"
        # Will create a directory
        sut_dir_path = Path(os.path.join(self.ROOT_PATH, "usb_files")).as_posix()

        usb_media_pos = self.get_mount_point(common_content_obj, common_configuration_obj)

        # mount the usb
        mount_command = "mount {} {}".format(usb_media_pos, self.USB_FILE_PATH)
        common_content_obj.execute_sut_cmd(mount_command, "mount command",
                                           common_configuration_obj.get_command_timeout())
        self._log.info("The USB media is mounted successfully..")

        # copy to usb
        common_content_obj.execute_sut_cmd(
            "cp -RT {} {}".format(mount_point+str(usb_folder_to_copy), str(sut_dir_path)), "copy",
            common_configuration_obj.get_command_timeout())

        self._log.info("The file(s) '{}' has been copied "
                       "successfully to the SUT {} ..".format(usb_folder_to_copy, sut_dir_path))

        # unmount the usb
        unmount_command = "umount {}".format(self.USB_FILE_PATH)
        common_content_obj.execute_sut_cmd(unmount_command, "unmount command",
                                           common_configuration_obj.get_command_timeout())
        self._log.info("The USB media is unmounted successfully..")

        return sut_dir_path
