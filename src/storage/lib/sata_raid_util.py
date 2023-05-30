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

from src.lib import content_exceptions
from src.lib.bios_constants import BiosSerialPathConstants
from dtaf_core.lib.private.cl_utils.adapter import data_types

from src.lib.dtaf_content_constants import RaidConstants


class SataRaidUtil(object):
    """
    SataRaidUtil class is to create the RAID in SATA
    """
    _BIOS_CONFIG_FILE = "raid_bios_knobs.cfg"
    REGEX_FOR_RAID_LEVELS = r'(RAID\d+\(.*?\))'
    REGEX_FOR_RAID_VOLUME = r'(Volume\d+.*RAID\d+\(.*?\).*)'
    NUM_DRIVES_RAID0 = [2, 4, 8]
    NUM_DRIVES_RAID1 = [2, 4, 8]
    NUM_DRIVES_RAID5 = [4, 8]
    NUM_DRIVES_RAID10 = [4, 8]

    def __init__(self, log, common_content_lib, common_content_configuration, bios_util, serial_bios_util,
                 ac_power):
        self._common_content_lib = common_content_lib
        self._common_content_configuration = common_content_configuration
        self._log = log
        self._bios_util_obj = bios_util
        self._serial_bios_util = serial_bios_util
        self._ac_power = ac_power
        self._bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self._BIOS_CONFIG_FILE)
        self._product_family = self._common_content_lib.get_platform_family()

    def set_sata_mode_selection(self):
        """
        This method is to set the to RAID.
        return None
        """
        self._log.info("Set the BIOS Knobs SATA Mode Selection to RAID")
        self._bios_util_obj.set_bios_knob(self._bios_config_file)

    def get_supported_raid_levels(self):
        """
        This method is to get the raid levels from BIOS page
        return : list of supported raid levels
        """
        create_raid_volume = "Create RAID Volume"
        self.set_sata_mode_selection()
        self._log.info("Navigating to the BIOS Page")
        status, ret_val = self._serial_bios_util.navigate_bios_menu()
        if not status:
            content_exceptions.TestFail("Bios Knobs did not navigate to the Bios Page")

        serial_path = BiosSerialPathConstants.INTEL_VROC_SATA_CONTROLLER[self._product_family.upper()]
        self._serial_bios_util.select_enter_knob(serial_path)
        screen_info = self._serial_bios_util.get_current_screen_info()
        for each_line in screen_info[0]:
            regex_output_raid = re.findall(self.REGEX_FOR_RAID_VOLUME, str(each_line))
            if len(regex_output_raid) != 0:
                for each_reg_out in regex_output_raid:
                    self._log.info("Deleting {}".format(each_line))
                    each_reg_out = each_reg_out.replace("(", "\(").replace(")", "\)")
                    select_raid_vol_to_delete = {each_reg_out: data_types.BIOS_UI_DIR_TYPE}
                    self._serial_bios_util.select_enter_knob(select_raid_vol_to_delete)
                    select_delete_knob_dict = {"Delete": data_types.BIOS_UI_DIR_TYPE}
                    self._serial_bios_util.select_enter_knob(select_delete_knob_dict)
                    select_yes_knob_dict = {"Yes": data_types.BIOS_UI_DIR_TYPE}
                    self._serial_bios_util.select_enter_knob(select_yes_knob_dict)
                    self._log.debug("Deleted {} Successfully".format(each_line))

        select_raid_vol = {create_raid_volume: data_types.BIOS_UI_DIR_TYPE}
        self._serial_bios_util.select_enter_knob(select_raid_vol)
        select_raid0_vol = {"RAID Level:": data_types.BIOS_UI_OPT_TYPE}
        self._serial_bios_util.select_enter_knob(select_raid0_vol)
        raid_level_screen_info = self._serial_bios_util.get_current_screen_info()
        raid_level_list = list()
        for each_line in raid_level_screen_info[0]:
            regex_output = re.findall(self.REGEX_FOR_RAID_LEVELS, str(each_line))
            # checking for list has some value in it
            if len(regex_output) != 0:
                # getting the value from list and removing the duplicate entries
                if regex_output[0] not in raid_level_list:
                    raid_level_list.append(regex_output[0])
        self._serial_bios_util.go_back_a_screen()
        return raid_level_list

    def delete_raid(self, raid_level, non_raid_disk):
        """
        This method is to delete RAID Volume
        :param raid_level: used for selecting the raid level in while deletion ex: RAID0(Stripe), RAID1(Mirror),
        RAID5(Parity), RAID10(RAID1+0)
        :param non_raid_disk: used to boot from non raid disk after RAID deletion.
        :return None
        """
        raid_level = raid_level.replace("(", "\(").replace(")", "\)").replace("+", "\+")
        non_raid_disk = non_raid_disk.strip()
        self._log.info("Navigating to the BIOS Page")
        status, ret_val = self._serial_bios_util.navigate_bios_menu()
        if not status:
            content_exceptions.TestFail("Bios Knobs did not navigate to the Bios Page")
        serial_path = BiosSerialPathConstants.INTEL_VROC_SATA_CONTROLLER[self._product_family.upper()]
        self._serial_bios_util.select_enter_knob(serial_path)
        self._log.info("Selecting {} to  delete".format(raid_level))
        select_volume_knob_dict = {".*" + raid_level + ".*": data_types.BIOS_UI_DIR_TYPE}
        self._serial_bios_util.select_enter_knob(select_volume_knob_dict)
        select_delete_knob_dict = {"Delete": data_types.BIOS_UI_DIR_TYPE}
        self._serial_bios_util.select_enter_knob(select_delete_knob_dict)
        select_yes_knob_dict = {"Yes": data_types.BIOS_UI_DIR_TYPE}
        self._serial_bios_util.select_enter_knob(select_yes_knob_dict)
        self._log.debug("Successfully deleted {} Volume".format(raid_level.split("\\")[0]))
        self._log.info("Navigating back to root")
        self._serial_bios_util.go_back_to_root()
        select_boot_manager_knob_dict = {r"Boot Manager Menu": data_types.BIOS_UI_DIR_TYPE}
        select_non_raid_disk_dict = {non_raid_disk: data_types.BIOS_UI_DIR_TYPE}
        self._log.info("Selecting and Entering into Boot Manager Menu")
        self._serial_bios_util.select_enter_knob(select_boot_manager_knob_dict)
        self._log.info("Selecting {} to  proceed with  Boot Successful".format(non_raid_disk))
        self._serial_bios_util.select_enter_knob(select_non_raid_disk_dict)

    def get_supported_sata_drive_list(self, raid_level, sata_drive_list):
        """
        This method is used to get supported number of sata drive list to create RAID
        :param raid_level: raid_level Ex: RAID0(Stripe)/ RAID1(Mirror)/ RAID5(Parity)/ RAID10(RAID1+0)
        :param sata_drive_list: sata_drive list from content config
        :return supported number of drive list
        """
        supported_sata_drive_list = []
        if raid_level == RaidConstants.RAID0:
            if len(sata_drive_list) in self.NUM_DRIVES_RAID0:
                supported_sata_drive_list = sata_drive_list[:2]
            else:
                self._log.error("can not create RAID 0 with {}".format(len(sata_drive_list)))
                raise content_exceptions.TestFail("can not create RAID 0 with {} Please verify the content config "
                                                  "atleast two drives should be updated")
        elif raid_level == RaidConstants.RAID1:
            if len(sata_drive_list) in self.NUM_DRIVES_RAID1:
                supported_sata_drive_list = sata_drive_list[:2]
            else:
                self._log.error("can not create RAID1 with {}".format(len(sata_drive_list)))
                raise content_exceptions.TestFail("can not create RAID1 with {} Please verify the content config "
                                                  "atleast two drives should be updated")
        elif raid_level == RaidConstants.RAID5:
            if len(sata_drive_list) in self.NUM_DRIVES_RAID5:
                supported_sata_drive_list = sata_drive_list[:len(sata_drive_list)]
            else:
                self._log.error("can not create RAID5 with {}".format(len(sata_drive_list)))
                raise content_exceptions.TestFail("can not create RAID5 with {} Please verify the content config "
                                                  "atleast four drives should be updated")
        elif raid_level == RaidConstants.RAID10:
            if len(sata_drive_list) in self.NUM_DRIVES_RAID10:
                supported_sata_drive_list = sata_drive_list[:4]
            else:
                self._log.error("can not create RAID10 with {}".format(len(sata_drive_list)))
                raise content_exceptions.TestFail("can not create RAID10 with {} Please verify the content config "
                                                  "atleast four drives should be updated")
        else:
            self._log.error("not supported RAID level for {}".format(raid_level))
            raise content_exceptions.TestFail("not supported RAID level for {}".format(raid_level))

        return supported_sata_drive_list

    def create_raid(self, raid_level):
        """
        This Method is to create RAID for SATA
        :param raid_level: used for selecting  the raid level  while RAID creation ex: RAID0(Stripe), RAID1(Mirror)
        return  current_screen_info of RAID volume details
        """
        create_volume = "Create Volume"
        create_raid_volume = "Create RAID Volume"
        self.set_sata_mode_selection()
        self._log.info("Navigating to the BIOS Page")
        status, ret_val = self._serial_bios_util.navigate_bios_menu()
        if not status:
            content_exceptions.TestFail("Bios Knobs did not navigate to the Bios Page")

        serial_path = BiosSerialPathConstants.INTEL_VROC_SATA_CONTROLLER[self._product_family.upper()]
        self._serial_bios_util.select_enter_knob(serial_path)
        self._log.info("Creating Volume for {}".format(raid_level))
        select_raid_vol = {create_raid_volume: data_types.BIOS_UI_DIR_TYPE}
        self._serial_bios_util.select_enter_knob(select_raid_vol)
        self._serial_bios_util.set_bios_knob("RAID Level:", data_types.BIOS_UI_OPT_TYPE, raid_level)
        self._log.info("Getting SATA Name info from config file")
        sata_drive_list = self._common_content_configuration.get_sata_storage_device()
        self._log.info("sata drive list from config is : {}".format(sata_drive_list))
        supported_sata_drive_list = self.get_supported_sata_drive_list(raid_level=raid_level,
                                                                       sata_drive_list=sata_drive_list)
        self._log.info("Supported sata drive list for {} is {} ".format(raid_level, supported_sata_drive_list))
        # Creating the RAID volumes
        for each_sata in supported_sata_drive_list:
            each_sata = ".*" + each_sata.replace(" ", ".*") + ".*"
            self._serial_bios_util.set_bios_knob(each_sata, data_types.BIOS_UI_OPT_TYPE, "X")
        raid_level = raid_level.replace("(", "\(").replace(")", "\)").replace("+", "\+")

        create_volume_knobs_dict = {create_volume: data_types.BIOS_UI_DIR_TYPE}
        self._serial_bios_util.save_bios_settings()
        raid_level_info_dict = {".*" + raid_level + ".*": data_types.BIOS_UI_DIR_TYPE}

        self._serial_bios_util.select_enter_knob(create_volume_knobs_dict)
        select_yes_knob_dict = {"Yes": data_types.BIOS_UI_DIR_TYPE}
        self._serial_bios_util.select_enter_knob(select_yes_knob_dict)
        self._serial_bios_util.select_enter_knob(raid_level_info_dict)
        self._serial_bios_util.select_knob("Name.*", data_types.BIOS_UI_OPT_TYPE)
        current_screen_info = self._serial_bios_util.get_current_screen_info()
        self._log.debug("{} is created successfully".format(raid_level.split("\\")[0]))
        self._serial_bios_util.save_bios_settings()
        self._serial_bios_util.reset_sut()

        return current_screen_info
