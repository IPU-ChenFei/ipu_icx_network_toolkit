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
import time
import re
from typing import List

from src.lib.common_content_lib import CommonContentLib
from src.lib import content_exceptions


class UefiUtil(object):
    """
    This class contains UEFI Utilities which is having common functionality for execution of UEFI command

    1. Boot to UEFI Shell
    2. Execute command on the UEFI Shell and return the values
    """
    ANSI_REG = r'(?:\x1b\[[0-9;]*[mGKHF])'
    UEFI_INTERNAL_SHELL = 'UEFI Internal Shell'
    BIOS_UI = 'BIOS_UI_OPT_TYPE'
    MAP_CMD = "map -r"
    REG_MAP = "^FS[0-9]"
    SEARCH_FILE = "ls -r -a -b {}"
    CWD = "cd"
    USB_PATTERN = "USB"
    DIRECTORY_KWD = "Directory"
    FILE_NOT_FOUND_KWD = "File Not Found"

    def __init__(self, log, uefi_obj, bios_bootmenu_obj, ac_obj, common_content_config_obj, os, cfg_opts=None):
        """
        Create instance for UefiUtil

        :param log: Log object
        :param uefi_obj: uefi shell object
        :param bios_bootmenu_obj: bios boot menu object
        :param ac_obj: ac power on/off object
        :param common_content_config_obj: common content configuration object
        """
        self._uefi_obj = uefi_obj
        self._bios_bootmenu_obj = bios_bootmenu_obj
        self._ac_obj = ac_obj
        self._log = log
        self._os = os
        self._cfg_opts = cfg_opts
        self._common_content_configuration = common_content_config_obj
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()
        self._f7_key_wait_time = self._common_content_configuration.bios_boot_menu_select_time_in_sec()
        self._uefi_command_timeout = self._common_content_configuration.uefi_command_timeout()
        self._sut_shutdown_delay = self._common_content_configuration.sut_shutdown_delay()
        self._press_f7_key = self._common_content_configuration.get_uefi_select_key()
        self._ac_timeout_delay_in_sec = self._common_content_configuration.ac_timeout_delay_in_sec()
        self.uefi_cmd_exec_delay = self._common_content_configuration.get_uefi_exec_delay_time()
        self._common_content_lib = CommonContentLib(log, self._os, self._cfg_opts)

    def enter_uefi_shell(self, is_power=True):
        """
        This function boot to UEFI Internal Shell.

        :return: True is the sut entered to UEFI else return False.
        """
        ret_value = False
        self._log.info("Attempt to boot SUT to UEFI Shell...")
        if is_power:
            self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._log.info("Waiting for menu entry...")
        self._bios_bootmenu_obj.wait_for_entry_menu(int(self._bios_boot_menu_entry_wait_time))
        self._log.info("Will press F7 now...")
        self._bios_bootmenu_obj.press_key(str(self._press_f7_key))  # Pressing F7
        self._log.info("F7 pressed now...")
        time.sleep(int(self._f7_key_wait_time))
        self._bios_bootmenu_obj.select(self.UEFI_INTERNAL_SHELL, self.BIOS_UI, int(
            self._f7_key_wait_time), False)
        self._bios_bootmenu_obj.enter_selected_item(
            int(self._f7_key_wait_time), True)
        self._uefi_obj.execute('\n', 0)
        if self._uefi_obj.in_uefi():
            self._log.info("sut enter to UEFI Internal Shell")
            ret_value = True
        else:
            self._log.error("sut did not enter to UEFI Internal Shell")

        return ret_value

    def execute_cmd_in_uefi_and_read_response(self, uefi_cmd, end_line=None):
        """
        This function executes the command in UEFI shell then reads the response and returns results.
        Results are stripped of ANSI characters added from UEFI shell

        :param: ueficmd command which needs to be executed in UEFI Shell.
        :return: returns the formatted output
        """
        time.sleep(self.uefi_cmd_exec_delay)  # Delay before executing the command in uefi
        self._log.info("Execute the command {} in UEFI shell".format(uefi_cmd))
        output = self._uefi_obj.execute(uefi_cmd,
                                        int(self._uefi_command_timeout), end_line)
        ansi_stripper = re.compile(self.ANSI_REG)
        formatted_output = ansi_stripper.sub('', str(output))
        self._log.debug("Response data from UEFI shell is {}".format(formatted_output))
        return formatted_output.split("\n")

    def execute_grub_install_cmd_in_uefi(self, uefi_cmd, end_line=None):
        """
        This function executes the grub install command in UEFI shell without waiting for the response
        from the shell

        :param: ueficmd command which needs to be executed in UEFI Shell.
        :return: returns True if successful
        """
        time.sleep(self.uefi_cmd_exec_delay)  # Delay before executing the command in uefi
        self._log.info("Execute the command {} in UEFI shell".format(uefi_cmd))
        self._uefi_obj.execute(uefi_cmd, 0, end_line)
        return True

    def graceful_sut_ac_power_on(self):
        """
        This function performs ac power off and then on.

        :return: return the power state True/False
        """
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)

    def get_uefi_path_for_disk(self, guid: str) -> List:
        """
        This function return the List of USB devices connected to the SUT in UEFI environment.
        :param guid: uuid of a disk
        :return: List of Usb drive in uefi internal shell
        """
        uefi_drive_device_list = []
        uefi_cmd_output = self.execute_cmd_in_uefi_and_read_response(self.MAP_CMD)
        self._log.debug("UEFI command output {} ".format(uefi_cmd_output))

        for linenumber, data in enumerate(uefi_cmd_output):
            output = re.search(self.REG_MAP, data.strip())
            if output:
                if guid.upper() in uefi_cmd_output[linenumber + 1]:
                    uefi_drive_device_list.append(output.group() + ":")

        if len(uefi_drive_device_list) != 1:
            raise content_exceptions.TestFail(f"{len(uefi_drive_device_list)} number of devices found with the uuid "
                                              f"{guid}")
        else:
            self._log.debug(f"Disk uuid {guid} found.")
            return uefi_drive_device_list

    def get_usb_uefi_drive_list(self):
        """
        This function return the List of USB devices connected to the SUT in UEFI environment.

        :return: List of Usb drive in uefi internal shell
        """
        uefi_usb_drive_device_list = []
        uefi_cmd_output = self.execute_cmd_in_uefi_and_read_response(self.MAP_CMD)
        self._log.debug("UEFI command output {} ".format(uefi_cmd_output))

        for linenumber, data in enumerate(uefi_cmd_output):
            output = re.search(self.REG_MAP, data.strip())
            if output:
                if self.USB_PATTERN in uefi_cmd_output[linenumber + 1]:
                    uefi_usb_drive_device_list.append(output.group() + ":")

        if uefi_usb_drive_device_list:
            self._log.debug("Number of uefi usb drive device list is {} ".format(uefi_usb_drive_device_list))
        else:
            self._log.error(
                "unable to get the usb drive in uefi shell make sure you have connected at least one usb device")
            raise RuntimeError(
                "unable to get the usb drive in uefi shell make sure you have connected at least one usb device")
        return uefi_usb_drive_device_list

    def execute_efi_cmd(self, usb_drive_list, eficmd, efisearchstr, end_line=None):
        """
        This function searches for .efi, .sh and other files in UEFI,
        Navigates and True if the command executed successful
        and result matches with the expected string.

        :return:True if the search pattern is found, else False
        """
        ret_flag = False
        for usb_drive in usb_drive_list:
            self.execute_cmd_in_uefi_and_read_response(usb_drive, None)
            self.uefi_navigate_to_usb(eficmd)
            efi_cmd_output = self.execute_cmd_in_uefi_and_read_response(eficmd, end_line)
            if efi_cmd_output:
                for efi_output in efi_cmd_output:
                    if efisearchstr in efi_output:
                        ret_flag = True
            else:
                self._log.error("eficmd command did not return any value")
                raise RuntimeError("eficmd command did not return any value")

            self.execute_cmd_in_uefi_and_read_response(self.CWD + " " + "\\", None)
            return ret_flag

    def uefi_navigate_to_usb(self, eficmd):
        """
        This function navigates to a folder and executes the file.

        :param eficmd: The command which is to be executed
        :raise: RuntimeError if unable to execute efi search for the file
        :return: None
        """
        efi_file_name = eficmd.split(" ")[0].strip()
        efi_output = self.execute_cmd_in_uefi_and_read_response(self.SEARCH_FILE.format(efi_file_name))
        if efi_output:
            for output in efi_output:
                drivepath = self.get_drive_path(efi_output)
                if drivepath and (efi_file_name in output) and ("ls" not in output):
                    self.execute_cmd_in_uefi_and_read_response(self.CWD + " " + '"' + drivepath + '"')

        else:
            self._log.error("Unable to execute efi search for the file")
            raise RuntimeError("Unable to execute efi search for the file")

    def get_drive_path(self, efi_output):
        """
        This Function to get the full path of the file used in uefi command

        :param efi_output: Takes the output of command running in uefi shell
        :raise: RuntimeError if File not found from the USB drive
        :return: return the path of the file used in uefi command
        """
        drivepath = None
        for output in efi_output:
            if self.DIRECTORY_KWD in output:
                drivepath = output.split(": ")[-1].strip()
            if self.FILE_NOT_FOUND_KWD in output:
                self._log.error("File not found from the USB drive")
                raise RuntimeError("File not found from the USB drive")
        return drivepath

    def get_usb_folder_path(self, usb_drive_list, folder_name):
        """
        This Function searches the required folder in the usb driver list

        :param usb_drive_list: takes the list of usb driver connected to SUT
        :param folder_name: searches the folder name in each usb drive connected to SUT
        :raise: RuntimeError if Folder not found from the USB drive
        :return: return the path of the the usb drive which contains the folder
        """
        for each_usb in usb_drive_list:
            self.execute_cmd_in_uefi_and_read_response(each_usb)
            uefi_cmd_output = self.execute_cmd_in_uefi_and_read_response("ls")
            self._log.debug("UEFI command output {} ".format(uefi_cmd_output))
            for linenumber, data in enumerate(uefi_cmd_output):
                if re.search(folder_name, data.strip()):
                    return each_usb
        raise content_exceptions.TestFail("Folder not found in the USB driver list")

    def perform_uefi_warm_reset(self):
        """This method performs warm reset in uefi shell"""
        # Exiting out from UEFI shell
        self._log.info("Performing warm reset")
        self._uefi_obj.warm_reset()
        self._common_content_lib.perform_boot_script()
