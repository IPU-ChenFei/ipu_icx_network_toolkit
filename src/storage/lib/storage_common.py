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

from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.dtaf_content_constants import PcieSlotAttribute
from src.pcie.lib.slot_mapping_utils import SlotMappingUtils
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon
from src.lib.dtaf_content_constants import RaidConstants
from src.lib import content_exceptions
from src.environment.os_installation import OsInstallation


class StorageCommon(object):
    """
    Base class for all Storage related test cases.
    """

    C_DRIVE_PATH = "C:\\"
    DISK_INFO_REGEX = "Disk\s([0-9])"
    VOLUME_INFO = "Volume\s\d+\s+C\s+\S+.*\s*Boot"
    DEVICE_INDEX = 1

    def __init__(self, test_log, cfg_opts):

        self._cfg = cfg_opts
        self._log = test_log
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

        self._common_content_configuration = ContentConfiguration(self._log)
        self._product_family = self._common_content_lib.get_platform_family()
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)

    def verify_os_boot_device_type(self, device_type):
        """
        This Method is Used to verify from which device OS is booted.

        :param: Installed OS device type.
        :return: True if found OS booted from device of device_type
        :raise: content_exceptions.TestFail if OS failed to boot from required device.
        """
        diskpart_script_name = "check_disk.txt"
        with open(diskpart_script_name, "w+") as fp:
            list_commands = ["List Disk\n"]
            fp.writelines(list_commands)

        self._os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
        disk_info = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}".format(diskpart_script_name),
                                                             "List Disk",
                                                             self._command_timeout,
                                                             self.C_DRIVE_PATH)
        self._log.info("List Disk Command Output: {}".format(disk_info))
        disk_lists = re.findall(self.DISK_INFO_REGEX, disk_info)
        flag = False
        for digit in disk_lists:
            with open(diskpart_script_name, "w+") as fp:
                list_commands = ["select disk {}\n".format(digit), "detail disk"]
                fp.writelines(list_commands)

            self._os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
            detail_disk = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}".format(diskpart_script_name), "Select Disk",
                                                                   self._command_timeout,
                                                                   self.C_DRIVE_PATH)
            self._log.info("Detail Disk Command Output: {}".format(detail_disk))
            if "Type   : {}".format(device_type).lower() in detail_disk.lower() and \
                    "Boot Disk  : Yes".lower() in detail_disk.lower():
                volume_check = re.findall(self.VOLUME_INFO, detail_disk)
                self._log.info("OS Partition Details: {}".format(volume_check))
                if volume_check:
                    flag = True
                    break
        os.remove(diskpart_script_name)
        if not flag:
            raise content_exceptions.TestFail("OS failed to boot from {} device.".format(device_type))

        return flag

    def get_pcie_device_bus_id(self, pythonsv_obj, pcie_slot_device_list=None, generation=5):
        """
        This method is to get the U.2 PCIe device bus id

        :param pythonsv_obj
        :param pcie_slot_device_list
        :param generation

        :return: bus_output, socket, csp_path
        """
        socket = None
        csp_path = None
        self._log.info("PCIe Device details from Config: {}".format(pcie_slot_device_list))
        slot_name = pcie_slot_device_list[PcieSlotAttribute.SLOT_NAME]
        self._log.info("PCIe Slot Name: {}".format(slot_name))
        if slot_name == PcieCommon.SLOT_C:
            try:
                bus_output = pcie_slot_device_list['bus']
            except:
                raise content_exceptions.TestFail("Please Add bus tag for slot_c")
        else:
            csp_path_attribute = PcieSlotAttribute.PCIE_SLOT_CSP_PATH
            socket_attribute = PcieSlotAttribute.PCIE_SLOT_SOCKET
            pcie_slot_mapping_with_bus = SlotMappingUtils.get_slot_bus_mappping_dict()
            if self._product_family in ["SPR", "EMR"]:
                csp_path = pcie_slot_mapping_with_bus[slot_name][csp_path_attribute][self._product_family]\
                    .format(generation)
            else:
                csp_path = pcie_slot_mapping_with_bus[slot_name][csp_path_attribute][self._product_family]
            self._log.debug("csp register to get bus info is: {}".format(csp_path))
            socket = pcie_slot_mapping_with_bus[slot_name][socket_attribute][self._product_family]
            self._log.info("Socket for PCIe Slot: {} is {}".format(slot_name, socket))
            bus_output = pythonsv_obj.get_by_path(pythonsv_obj.SOCKET, csp_path, socket)
            if not bus_output:
                raise content_exceptions.TestFail("PCIe device bus is not captured with cscripts for slot:"
                                                  " {}".format(slot_name))
            self._log.debug("Slot Name: {} is mapped to bus: {}".format(slot_name, bus_output))
            bus_output = str(bus_output)[2:]  # Converting Register byte into string. Here, bus value in hexa required.

        return bus_output, socket, csp_path

    def verify_drives_and_get_drive_list_for_raid_level(nvme_drive_list, raid_level):
        """
        This method is to validate the number of drives to create the RAID

        :param nvme_drive_list list of nvme drives from content config
        :param raid_level : RAID0, RAID1, RAID5, RAID10
        :return nvme_drive_list required list of drives to create RAID level
        """
        if raid_level == RaidConstants.RAID0:
            if len(nvme_drive_list) in self.NUM_DRIVES_RAID0:
                nvme_drive_list = nvme_drive_list[:2]
            else:
                self._log.error("can not create RAID 0 with {}".format(len(nvme_drive_list)))
                raise content_exceptions.TestFail("can not create RAID 0 with {} Please verify the content config "
                                                  "atleast two drives should be updated")
        elif raid_level == RaidConstants.RAID1:
            if len(nvme_drive_list) in self.NUM_DRIVES_RAID1:
                nvme_drive_list = nvme_drive_list[:2]
            else:
                self._log.error("can not create RAID1 with {}".format(len(nvme_drive_list)))
                raise content_exceptions.TestFail("can not create RAID1 with {} Please verify the content config "
                                                  "atleast two drives should be updated")
        elif raid_level == RaidConstants.RAID5:
            if len(nvme_drive_list) in self.NUM_DRIVES_RAID5:
                nvme_drive_list = nvme_drive_list[:len(nvme_drive_list)]
            else:
                self._log.error("can not create RAID5 with {}".format(len(nvme_drive_list)))
                raise content_exceptions.TestFail("can not create RAID5 with {} Please verify the content config "
                                                  "atleast four drives should be updated")
        elif raid_level == RaidConstants.RAID10:
            if len(nvme_drive_list) in self.NUM_DRIVES_RAID10:
                nvme_drive_list = nvme_drive_list[:4]
            else:
                self._log.error("can not create RAID10 with {}".format(len(nvme_drive_list)))
                raise content_exceptions.TestFail("can not create RAID10 with {} Please verify the content config "
                                                  "atleast four drives should be updated")
        else:
            self._log.error("not supported RAID level for {}".format(raid_level))
            raise content_exceptions.TestFail("not supported RAID level for {}".format(raid_level))
        return nvme_drive_list

    def format_drive_win(self, device_type, format_type="ntfs", assign_letter="z", booted_format_drive=True):
        """
        This Method is to format nvme drive which is not having OS and assign it to the given drive letter

        :param: Installed OS device type.
        :param device_type: SATA or nvme
        :param booted_format_drive: If True it will format the first device in the list else it will format non booted
        storage devices connected in SUT and assign drive letter.
        :return: True if found OS booted from device of device_type
        :raise: content_exceptions.TestFail if OS failed to boot from required device.
        """
        diskpart_script_name = "check_disk.txt"
        with open(diskpart_script_name, "w+") as fp:
            list_commands = ["List Disk\n"]
            fp.writelines(list_commands)

        self._os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
        disk_info = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}".format(diskpart_script_name),
                                                             "List Disk",
                                                             self._command_timeout,
                                                             self.C_DRIVE_PATH)
        self._log.info("List Disk Command Output: {}".format(disk_info))
        disk_lists = re.findall(self.DISK_INFO_REGEX, disk_info)
        for digit in disk_lists:
            with open(diskpart_script_name, "w+") as fp:
                list_commands = ["select disk {}\n".format(digit), "detail disk"]
                fp.writelines(list_commands)

            self._os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
            detail_disk = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}"
                                                                   .format(diskpart_script_name),
                                                                   "Select Disk", self._command_timeout,
                                                                   self.C_DRIVE_PATH)
            self._log.info("Detail Disk Command Output: {}".format(detail_disk))
            if "Boot Disk  : Yes".lower() in detail_disk.lower() or \
                    "Type   : {}".format(device_type).lower() not in detail_disk.lower():
                disk_lists.remove(digit)
        os.remove(diskpart_script_name)
        # formatting the 1st drive from the list
        if booted_format_drive:
            with open(diskpart_script_name, "w+") as fp:
                list_commands = ["select disk {}\n".format(disk_lists[0]), "clean\n", "create partition primary\n",
                                 "format fs={} quick\n".format(format_type), "assign letter={}\n".format(
                        assign_letter)]
                fp.writelines(list_commands)

            self._os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
            format_disk = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}"
                                                                   .format(diskpart_script_name),
                                                                   "format Disk", self._command_timeout,
                                                                   self.C_DRIVE_PATH)
            self._log.info("Detail Disk Command Output: {}".format(format_disk))
            self._log.info("Successfully formatted the {} drive".format(device_type))
            os.remove(diskpart_script_name)
        else:
            with open(diskpart_script_name, "w+") as fp:
                for each in range(0, len(disk_lists)):
                    list_commands = ["select disk {}\n".format(disk_lists[each]), "clean\n",
                                     "create partition primary\n",
                                     "format fs={} quick\n".format(format_type), "assign letter={}\n".format(
                            self._common_content_lib.get_free_drive_letter)]
                    fp.writelines(list_commands)

                self._os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
                format_disk = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}"
                                                                       .format(diskpart_script_name),
                                                                       "format Disk", self._command_timeout,
                                                                       self.C_DRIVE_PATH)
                self._log.info("Detail Disk Command Output: {}".format(format_disk))
                self._log.info("Successfully formatted the {} drive".format(device_type))
            os.remove(diskpart_script_name)

    def get_model_no_of_device_from_inventory_file(self, device_type):
        """
        This method is to get the list of the storage device's model and serial no from the sut_inventory file
        of the given device_type
        param :
        """
        device_inventory = []
        # getting the pcie storage device names from the sut_inventory
        sut_inv_file_path = self._os_installation_lib.get_sut_inventory_file_path()
        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if device_type.lower() in line:
                    line = line.split("=")[1]
                    model_no = line.split()[2]
                    device_inventory.append(model_no.strip())
            if not device_inventory:
                raise content_exceptions.TestError("Unable to find {} device for verification, "
                                                   "please check the sut_inventory.cfg file "
                                                   "under {} and update it correctly".format(device_type,
                                                                                             sut_inv_file_path))

        self._log.info("{} device Name from config file : {}".format(device_type, device_inventory))
        return device_inventory
