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
import pickle
import re
from importlib import import_module

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.provider.base_provider import BaseProvider
from abc import ABCMeta, abstractmethod
from six import add_metaclass

from src.lib.common_content_lib import CommonContentLib
from src.lib.dtaf_content_constants import CRFileSystems
from src.lib.content_configuration import ContentConfiguration
from src.memory.lib.memory_common_lib import MemoryCommonLib


@add_metaclass(ABCMeta)
class PartitionProvider(BaseProvider):
    DRIVE_LETTERS_FILE = "dcpmmdriveletters.txt"

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new Partition provider object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(PartitionProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._sut_os = self._os.os_type

        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg_opts)
        self._content_config_obj = ContentConfiguration(self._log)
        self._command_timeout = self._content_config_obj.get_command_timeout()
        self._reboot_timeout = self._content_config_obj.get_reboot_timeout()
        self._memory_common_lib = MemoryCommonLib(self._log, cfg_opts, self._os)

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        """
        package = r"src.provider.partition_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "PartitionProviderWindows"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "PartitionProviderLinux"
        else:
            raise NotImplementedError

        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(cfg_opts=cfg_opts, log=log, os_obj=os_obj)

    @abstractmethod
    def create_partition_dcpmm_disk(self, convert_type, disk_lists, mode=None, size=None):
        """
        This method is used to verify the show topology firmware output with pmem device output.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_dcpmm_disk_list(self, region_data_list):
        """
        This method is used to verify the show topology device locator output with pmem device output.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def create_ext4_filesystem(self, pmem_device_list):
        """
        Function to create an ext4 Linux file system on each enumerated PM blockdev device on linux SUT

        :param: pmem_device_list
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def create_mount_point(self, pmem_device_list, mode="block"):
        """
        Function to create mount point on each enumerated PM blockdev device on linux SUT

        :param: pmem_device_list, mode(optional param)
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def verify_mount_point(self, pmem_device_list):
        """
        Function to verify mount point on each enumerated PM blockdev device on linux SUT

        :param: pmem_device_list
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def verify_device_partitions(self, pmem_device_list, disk_letters=None):
        """
        Function to verify the device partition of PM block dev device on linux SUT

        :param pmem_device_list: device number list
        :param disk_letters: disk letters that are created.
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def create_dcpmm_gpt_format(self, disk_lists):
        """
        Function to create DCPMM with GPT format

        :param disk_lists: dcpmm disk list
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def delete_partition(self, pmem_device_list):
        """
        Function to delete partition under pmem_device_list.

        :param: pmem_device_list: partition List to be deleted.
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_disk_partition_information(self, disk_lists):
        """
        Function to get the disk(pmem,sda) information

        :param: disk_lists : name of the disk list(sda*,pmem*)
        :raise NotImplementedError
        """
        raise NotImplementedError


class PartitionProviderLinux(PartitionProvider):
    LINUX_PARTITION_CMD = "parted -s -a optimal /dev/{} mklabel gpt -- mkpart primay ext4 1MiB 32GB"
    NDCTL_CMD_TO_CREATE_NAMESPACE = "ndctl create-namespace --mode sector --region={}"
    LINUX_CMD_TO_CREATE_EX4_FILE_SYSTEM = "mkfs.ext4 -F /dev/{}"
    CREATE_DIRECTORY_MOUNT_POINT_CMD = "mkdir q /mnt/QM-{}"
    MOUNT_DAX_FILE_SYSTEM_CMD = "mount -o dax /dev/{} /mnt/QM-{}"
    MOUNT_BLOCK_FILE_SYSTEM_CMD = "mount /dev/{} /mnt/QM-{}"
    CREATE_AUTO_MOUNT_CMD = 'echo "/dev/{} /mnt/QM-{} ext4 defaults,nofail 0 1" >> /etc/fstab'
    GPRE_CMD_TO_GET_MOUNT_INFO = "mount | grep pmem"
    MOUNT_VERIFICATION_STR = "/dev/{} on "
    LINUX_CMD_TO_GET_PARTITION_INFO = "lsblk"
    LINUX_CMD_TO_DISPLAY_DISK_INFORMATION = "parted -s /dev/{} unit GB print"
    mount_list = []

    def __init__(self, log, cfg_opts, os_obj):
        super(PartitionProviderLinux, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj

    def get_dcpmm_disk_list(self, create_namespace_data):
        """
        Function to get dcpmm disk list on linux SUT

        :param create_namespace_data: namespace data
        :return: dcpmm disk list
        """

        pmem_list = []
        for index in range(0, len(create_namespace_data)):
            pmem_list.append(create_namespace_data[index]["blockdev"])

        return sorted(pmem_list)

    def create_partition_dcpmm_disk(self, convert_type, disk_lists, mode=None, size=None):
        """
        Function to run the command to do the partition by 'parted' on linux SUT

        :param convert_type: type of conversion required
        :param disk_lists: dcpmm disk list
        :param mode: type of mode to convert
        :param size: size of pmem disk
        :return: partition result
        """
        partition_result = ""
        for index in range(0, len(disk_lists)):
            if size:
                # Create partition with memory size
                partition_result = self._memory_common_lib.create_partition_storage(disk_lists[index], mode, size)

                partition_list = self._memory_common_lib.get_sub_partition(disk_lists[index])
                self._log.info("partition information :\n{}".format(partition_list))

                create_fs = self._memory_common_lib.create_file_system(partition_list[-1], convert_type)
                self._log.info("file system data : \n{}".format(create_fs))
            else:
                partition_result = self._common_content_lib.execute_sut_cmd(self.LINUX_PARTITION_CMD.format(
                    disk_lists[index]), "Create a generic "
                                        "partition on each PMEM device "
                                        "using parted", self._command_timeout)
        if partition_result != "":
            self._log.info("Successfully created a generic partition on each PMEM device using parted")

        return partition_result

    def create_ext4_filesystem(self, pmem_device_list):
        """
        Function to create an ext4 Linux file system on each enumerated PM blockdev device on linux SUT

        :param: pmem_device_list
        :return: stdout data
        """
        ext4_result_data = ""
        for index in range(0, len(pmem_device_list)):
            ext4_result_data = self._common_content_lib.execute_sut_cmd(self.LINUX_CMD_TO_CREATE_EX4_FILE_SYSTEM.
                                                                        format(pmem_device_list[index]),
                                                                        "Create an ext4 Linux file system on each "
                                                                        "enumerated ", self._command_timeout)
        if len(ext4_result_data) != 0:
            self._log.info("Successfully created an ext4 Linux file system on each enumerated block..\n{}".
                           format(ext4_result_data))

        return ext4_result_data

    def create_mount_point(self, pmem_device_list, mode="block"):
        """
        Function to create mount point on each enumerated PM blockdev device on linux SUT

        :param: pmem_device_list, mode(optional param)
        :return: stdout data
        """
        for index in range(0, len(pmem_device_list)):
            cmd_result = self._os.execute(self.CREATE_DIRECTORY_MOUNT_POINT_CMD.format(str(index)),
                                          self._command_timeout)
            if cmd_result.cmd_failed():
                self._common_content_lib.execute_sut_cmd("rmdir q ".format(str(index)),
                                                         "removing directory", self._command_timeout)

                self._common_content_lib.execute_sut_cmd("rmdir /mnt/QM-{} ".format(str(index)),
                                                         "removing directory", self._command_timeout)

                self._common_content_lib.execute_sut_cmd(self.CREATE_DIRECTORY_MOUNT_POINT_CMD.format(str(index)),
                                                         "Creating a directory", self._command_timeout)
            self.mount_list.append("/mnt/QM-{}".format(str(index)))

            self._log.info("Successfully created the directory mount point for the device {}".format(pmem_device_list[
                                                                                                         index]))
            with open(self.DRIVE_LETTERS_FILE, "wb") as fp:
                pickle.dump(self.mount_list, fp)

            if mode == CRFileSystems.DAX:
                cmd_result = self._common_content_lib.execute_sut_cmd(
                    self.MOUNT_DAX_FILE_SYSTEM_CMD.format(pmem_device_list[index], str(index)),
                    "Mount the Linux file system", self._command_timeout)
                self._log.info("Successfully mount the Linux file system with DAX Access\n{}".format(cmd_result))
            elif mode == CRFileSystems.BLOCK:
                cmd_result = self._common_content_lib.execute_sut_cmd(
                    self.MOUNT_BLOCK_FILE_SYSTEM_CMD.format(pmem_device_list[index], str(index)),
                    "Mount the Linux file system", self._command_timeout)
                self._log.info("Successfully  mount the Linux file system with Block Access\n{}".format(cmd_result))
            #  Write the pmem mount data in /etc/fstab
            self._common_content_lib.execute_sut_cmd(
                self.CREATE_AUTO_MOUNT_CMD.format(pmem_device_list[index], str(index)), "Create Auto Mount",
                self._command_timeout)
            self._log.info("Successfully Auto mounted the pmem device")

    def verify_mount_point(self, pmem_device_list):
        """
        Function to verify mount point on each enumerated PM blockdev device on linux SUT

        :param: pmem_device_list
        :return: return on Success
        :raise: RuntimeError
        """
        cmd_result = self._common_content_lib.execute_sut_cmd(self.GPRE_CMD_TO_GET_MOUNT_INFO, "Show mount "
                                                                                               "information",
                                                              self._command_timeout)
        verification_result = [index for index in range(0, len(pmem_device_list)) if self.MOUNT_VERIFICATION_STR.format(
            pmem_device_list[index]) in cmd_result]
        if not verification_result:
            error_msg = "Mount is Not successful on each device"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Mount is successful on each device..\n")
        return True

    def verify_device_partitions(self, pmem_device_list, disk_letters=None):
        """
        Function to verify the device partition of PM blockdev device on linux SUT

        :param pmem_device_list: device number list
        :param disk_letters: disk letters that are created.
        :return: return on Success
        :raise: RuntimeError
        """
        cmd_result = self._common_content_lib.execute_sut_cmd(self.LINUX_CMD_TO_GET_PARTITION_INFO, "Show partition "
                                                                                                    "information",
                                                              self._command_timeout)
        verification_result = [index for index in range(0, len(pmem_device_list)) if (pmem_device_list[index]) in
                               cmd_result]
        if not verification_result:
            error_msg = "Fail to verify the device partition"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully verified the device partitions...\n")
        return True

    def create_dcpmm_gpt_format(self, disk_lists):
        """
        Function to create DCPMM with GPT format

        :param disk_lists: dcpmm disk list

        """
        # create disk label in the device with no partition
        for index in range(0, len(disk_lists)):
            self._common_content_lib.execute_sut_cmd(
                "parted -s /dev/{} mklabel gpt".format(disk_lists[index]),
                "to create disk label without partition", self._command_timeout)

        # Disk information before creating any partition
        self.get_disk_partition_information(disk_lists)

    def delete_partition(self, pmem_device_list):
        """
        Function to delete partition under pmem_device_list.

        :param: pmem_device_list: partition List to be deleted.
        :return True if partition is deleted successfully
        """

        for index in range(0, len(pmem_device_list)):
            partition_num_list = self._memory_common_lib.get_sub_partition_number_list(pmem_device_list[index])
            for num in partition_num_list:
                self._memory_common_lib.delete_partition_with_partition_number(pmem_device_list[index], num)
                self._log.info("Deleted partition under the device /dev/{},"
                               " having partition number {}".format(pmem_device_list[index], num))

        return True

    def get_disk_partition_information(self, disk_lists):
        """
        Function to get the disk(pmem,sda) information

        :param: disk_name : name of the disk (sda*,pmem*)
        :return: disk_info : information of the disk
        """
        disk_info = ""
        for index in range(0, len(disk_lists)):
            self._log.debug("executing the command : {}".format(
                self.LINUX_CMD_TO_DISPLAY_DISK_INFORMATION.format(disk_lists[index])))

            disk_info = self._common_content_lib.execute_sut_cmd(
                self.LINUX_CMD_TO_DISPLAY_DISK_INFORMATION.format(disk_lists[index]),
                "To display the disk information", self._command_timeout)
            self._log.info(
                "Disk information and file system in the device {}:\n{}".format(disk_lists[index], disk_info))

        return disk_info


class PartitionProviderWindows(PartitionProvider):
    PS_CMD_GET_DCPMM_DISK_LIST = 'powershell.exe "Get-PmemDisk | select DiskNumber"'

    def __init__(self, log, cfg_opts, os_obj):
        super(PartitionProviderWindows, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self.store_generated_dcpmm_drive_letters = []

    def get_dcpmm_disk_list(self, create_namespace_data=None):
        """
        Function to get the DCPMM disk list that needs to be partitioned.

        :return: list of disk numbers
        """
        powershell_list_phy_device = self._common_content_lib.execute_sut_cmd(
            self.PS_CMD_GET_DCPMM_DISK_LIST, "get disk list", self._command_timeout,
            self._common_content_lib.C_DRIVE_PATH)
        digit_list = []

        for disk_num in powershell_list_phy_device.strip().split("\n"):
            disk_num_striped = disk_num.strip()
            if disk_num_striped.isdigit():
                digit_list.append(disk_num_striped)

        return sorted(digit_list)

    def create_partition_dcpmm_disk(self, convert_type, disk_lists, mode="block", size=None):
        """
        Function to create the new DCPMM disk partitions.

        :param convert_type: gpt / mbr
        :param disk_lists: number of DCPMM disks available.
        :param mode: Mode of DCPMM like DAX / Block
        :param size: size of pmem disk
        :return: true if the disk is available for partition else false
        """

        if len(disk_lists) != 0:
            if size is None:
                self._log.info("For Full Disk ...")
            elif "GB" in size:
                size = size.split('GB')[0]
                size = int(size) * 1024
            for digit in disk_lists:
                drive_letter = self._common_content_lib.get_free_drive_letter()
                self.store_generated_dcpmm_drive_letters.append(drive_letter)

                with open("createpartition.txt", "w+") as fp:
                    if size:
                        list_commands = ["select disk {}\n".format(digit), "attributes disk clear readonly\n",
                                         "create partition primary size={}\n".format(size),
                                         "assign letter={}\n".format(drive_letter)]
                        fp.writelines(list_commands)
                    else:
                        list_commands = ["select disk {}\n".format(digit), "attributes disk clear readonly\n",
                                         "convert {}\n".format(convert_type), "create partition primary\n",
                                         "assign letter={}\n".format(drive_letter)]
                        fp.writelines(list_commands)

                self._os.copy_local_file_to_sut("createpartition.txt", self._common_content_lib.C_DRIVE_PATH)
                create_partition = self._common_content_lib.execute_sut_cmd(r"diskpart /s createpartition.txt",
                                                                            "Partition creation",
                                                                            self._command_timeout,
                                                                            self._common_content_lib.C_DRIVE_PATH)
                self._log.info("A new partition has been created with letter {} and .."
                               "{}".format(drive_letter, create_partition))

                if mode == 'block':
                    mode_cmd = "/q /y"
                else:
                    mode_cmd = "/q /y /dax"
                format_disk = self._common_content_lib.execute_sut_cmd("format {}: {}".format(drive_letter, mode_cmd),
                                                                       "Format the new partition",
                                                                       self._command_timeout)
                self._log.info("{}".format(format_disk))

            with open(self.DRIVE_LETTERS_FILE, "wb") as fp:
                pickle.dump(self.store_generated_dcpmm_drive_letters, fp)

            if os.path.exists("createpartition.txt"):
                os.remove("createpartition.txt")

            return True
        else:
            err_log = "Unable to locate any DCPMM disks.."
            self._log.error(err_log)
            raise RuntimeError(err_log)

    def create_ext4_filesystem(self, pmem_device_list):
        """
        Function to create an ext4 Linux file system on each enumerated PM blockdev device on linux SUT

        :param: pmem_device_list
        :return: stdout data
        """
        self._log.info("Windows platform does not have separate file system creation process.. This has been"
                       " taken care in the diskpart")
        return True

    def create_mount_point(self, pmem_device_list, mode="block"):
        """
        Function to create mount point on each enumerated PM block dev device on linux SUT

        :param: pmem_device_list, mode(optional param)
        :return: stdout data
        """
        self._log.info("Windows platform does not have separate mount point creation process..This has been"
                       " taken care in the diskpart")
        return True

    def verify_mount_point(self, pmem_device_list):
        """
        Function to verify mount point on each enumerated PM blockdev device on linux SUT

        :param: pmem_device_list
        """
        self._log.info("Windows platform does not have the mount point verification process..This has been"
                       " taken care in the partition verification..")
        return True

    def verify_device_partitions(self, pmem_device_list, drive_letters=None):
        """
        Function to verify that the partitions are created correctly.

        :param pmem_device_list: number of DCPMM disks available.
        :param drive_letters: number of partition letters in list.
        :return: true if partitions are created else false
        """
        ret_val = []
        detail_disk = None

        if drive_letters:
            self.store_generated_dcpmm_drive_letters = list(drive_letters)

        if len(pmem_device_list) != 0:
            for digit in pmem_device_list:
                with open("verifypartition.txt", "w+") as file_listdisk:
                    list_commands = ["list volume\n", "list disk\n", "select disk {}\n".format(digit), "detail disk"]
                    file_listdisk.writelines(list_commands)

                self._os.copy_local_file_to_sut("verifypartition.txt", self._common_content_lib.C_DRIVE_PATH)

                detail_disk = self._common_content_lib.execute_sut_cmd("diskpart /s verifypartition.txt",
                                                                       "Partition information",
                                                                       self._command_timeout,
                                                                       self._common_content_lib.C_DRIVE_PATH)
                self._log.info(
                    "Information on the created disks are shown below... \n {}".format(detail_disk))

            rm_dup_list_current_drive_letters = []
            list_healthy_operational_drives = []

            if re.search("Partition", detail_disk):
                list_healthy_operational_drives = re.findall(r"Healthy", detail_disk, re.IGNORECASE)

                list_current_drive_letters = re.findall(r"\s[A-BD-Z]\s", detail_disk)

                rm_dup_list_current_drive_letters = list(dict.fromkeys(list_current_drive_letters))

                rm_dup_list_current_drive_letters = [ltr.strip(' ') for ltr in
                                                     rm_dup_list_current_drive_letters]

            self._log.info("Current drive letters present in the system, {}".format
                           (rm_dup_list_current_drive_letters))

            self._log.info("Partitioned drive letters, {}".format(self.store_generated_dcpmm_drive_letters))

            if len(list_healthy_operational_drives) >= len(rm_dup_list_current_drive_letters):
                self._log.info("The operational status is 'healthy' for all the drive letters..")
                ret_val.append(True)
            else:
                self._log.error("The operational status is not 'healthy' for all the drive letters..")
                ret_val.append(False)

            if len(self.store_generated_dcpmm_drive_letters) != 0:
                res = list(set(sorted(rm_dup_list_current_drive_letters)).intersection(sorted(
                    self.store_generated_dcpmm_drive_letters)))
                if len(res) == len(self.store_generated_dcpmm_drive_letters):
                    self._log.info("Pmem volumes/disks are listed showing correct drive letters..")
                    ret_val.append(True)
                else:
                    self._log.error("Pmem volumes/disks are listed not showing correct drive letters..")
                    ret_val.append(False)

            if os.path.exists("verifypartition.txt"):
                os.remove("verifypartition.txt")

            return all(ret_val)
        else:
            err_log = "Unable to locate any DCPMM disks.."
            self._log.error(err_log)
            raise RuntimeError(err_log)

    def create_dcpmm_gpt_format(self, disk_lists):
        """
        Function to create DCPMM with GPT format

        :param disk_lists: dcpmm disk list
        """
        file_name = "creategptformat.txt"
        if len(disk_lists) != 0:
            for digit in disk_lists:
                with open(file_name, "w+") as fp:
                    list_commands = ["select disk {}\n".format(digit), "attributes disk clear readonly\n",
                                     "convert gpt\n"]
                    fp.writelines(list_commands)
                self._log.info("commands for gpt are : {}".format(list_commands))
                self._os.copy_local_file_to_sut(file_name, self._common_content_lib.C_DRIVE_PATH)
                cmd_result = self._common_content_lib.execute_sut_cmd(
                    r"diskpart /s {}".format(file_name), "Create GPT format", self._command_timeout,
                    self._common_content_lib.C_DRIVE_PATH)
                self._log.info("GPT format : {}\n".format(cmd_result))
            if os.path.exists(file_name):
                os.remove(file_name)

    def delete_partition(self, pmem_device_list):
        """
        Function to delete partition under pmem_device_list.

        :param: pmem_device_list: partition List to be deleted.
        :return True if partition is deleted successfully
        """
        file_name = "deletepartition.txt"
        disk_lists = pmem_device_list
        if len(disk_lists) != 0:
            for digit in disk_lists:
                with open(file_name, "w+") as fp:
                    list_commands = ["select disk {}\n".format(digit), "clean"]
                    fp.writelines(list_commands)

                self._os.copy_local_file_to_sut(file_name, self._common_content_lib.C_DRIVE_PATH)
                delete_partition = self._common_content_lib.execute_sut_cmd(
                    r"diskpart /s {}".format(file_name), "Partition deletion", self._command_timeout,
                    self._common_content_lib.C_DRIVE_PATH)
                self._log.info("A new partition has been deleted for disk {} and {}".format(digit, delete_partition))

        if os.path.exists(file_name):
            os.remove(file_name)

    def get_disk_partition_information(self, disk_lists):
        """
        Function to get the disk(pmem,sda) information

        :param: disk_name : name of the disk (sda*,pmem*)
        :return: disk_info : information of the disk
        """
        file_name = "displaypartition.txt"
        disk_info = ""
        if len(disk_lists) != 0:
            for digit in disk_lists:
                with open(file_name, "w+") as fp:
                    list_commands = ["select disk {}\n".format(digit), "list partition\n"]
                    fp.writelines(list_commands)

                self._os.copy_local_file_to_sut(file_name, self._common_content_lib.C_DRIVE_PATH)

                disk_info = self._common_content_lib.execute_sut_cmd(
                    "diskpart /s {}".format(file_name), "Partition information",
                    self._command_timeout, self._common_content_lib.C_DRIVE_PATH)
                self._log.info("Information on the created disk partition are shown below... \n {}".format(disk_info))

        if os.path.exists(file_name):
            os.remove(file_name)

        return disk_info
