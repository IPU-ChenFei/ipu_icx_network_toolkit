#!/usr/bin/env python
##########################################################################
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
##########################################################################

import sys
import re
import platform
import os

from dtaf_core.lib.dtaf_constants import OperatingSystems


class UefiCmdtoolLib(object):
    """
    Provides cmdtool APIs to get BMC IP address, add debuguser1 user and set password
    """
    CMDTOOL_SET_ROOT_PWD = "cmdtool.efi 20 c0 5f 0 30 70 65 6e 42 6d 63 31"
    CMDTOOL_GET_IP = "cmdtool.efi 20 30 02 03 03 00 00"
    # create 'debuguser' in IPMI user id2
    CMDTOOL_CREATE_USER = "cmdtool.efi 20 18 45 2 64 65 62 75 67 75 73 65 72 0 0 0 0 0 0 0"
    # set password for user id 2 to '0penBmc1'
    CMDTOOL_SET_PWD = "cmdtool.efi 20 18 47 2 2 30 70 65 6e 42 6d 63 31 0 0 0 0 0 0 0 0"
    # Enable user id 2
    CMDTOOL_ENABLE_USER_ID_2 = "cmdtool.efi 20 18 47 2 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
    # Enable admin access to user id 2 in channel 1
    CMDTOOL_ACCESS_TO_CH1_CMD1 = "cmdtool.efi 20 18 44 1 2"
    CMDTOOL_ACCESS_TO_CH1_CMD2 = "cmdtool.efi 20 18 43 91 2 4 0"
    # Enable admin access to user id 2 in channel 3
    CMDTOOL_ACCESS_TO_CH3_CMD1 = "cmdtool.efi 20 18 44 3 2"
    CMDTOOL_ACCESS_TO_CH3_CMD2 = "cmdtool.efi 20 18 43 93 2 4 0"
    # Enable MTM mode
    CMDTOOL_ENABLE_MTM = "cmdtool.efi 20 C0 B4 3 2"

    CHANNEL_1 = "1"
    CHANNEL_3 = "3"

    ansi_reg_expr = re.compile(r'(?:\x1b\[[0-9;]*[mGKHF])')
    hexa_reg_expr = re.compile(r"^[0-9A-Fa-f ]+$")

    def __init__(self, uefi_obj, log, usb_map, cmdtool_folder):
        self._uefi_obj = uefi_obj
        self._log = log
        self._usb_map = usb_map
        self._timeout = 10
        self._cmdtool_folder = cmdtool_folder
        # change drive to usb
        self.__execute_uefi_cmd(self._usb_map)
        self.__execute_uefi_cmd("cd " + self._cmdtool_folder)
        #load ipmi driver
        self.__execute_uefi_cmd("load ipmi.efi")

    def get_bmc_ip(self):
        uefi_output = self.__execute_uefi_cmd(self.CMDTOOL_GET_IP)
        list_cmdtool_bytes = self.__get_cmdtool_response_bytes(uefi_output)
        self._log.info("Get IP Address cmdtool output={}".format(list_cmdtool_bytes))
        # IP address command should return six bytes
        no_bytes = len(list_cmdtool_bytes)
        if no_bytes != 6:
            log_error = "Get IP Address command did not return the expected output.."
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return_code = int(list_cmdtool_bytes[0], 16)
        if 0 != return_code:
            log_error = "Get IP Address command failed with return code={}..".format(return_code)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("Get IP Address command executed successfully..")
        start_index = no_bytes - 4
        ip_address = str(int(list_cmdtool_bytes[start_index], 16)) + "." + \
                     str(int(list_cmdtool_bytes[start_index + 1], 16)) + "." + \
                     str(int(list_cmdtool_bytes[start_index + 2], 16)) + "." + \
                     str(int(list_cmdtool_bytes[start_index + 3], 16))

        return ip_address

    def create_and_enable_debuguser(self):
        self.__set_root_password()
        self.__create_debuguser()
        self.__set_password()
        self.__enable_userid_2()
        self.__enable_administrator_access(self.CHANNEL_1)
        self.__enable_administrator_access(self.CHANNEL_3)
        self.__enable_mtm_mode()

    def __create_debuguser(self):
        uefi_output = self.__execute_uefi_cmd(self.CMDTOOL_CREATE_USER)
        list_cmdtool_bytes = self.__get_cmdtool_response_bytes(uefi_output)
        self._log.info("Create debuguser cmdtool output={}".format(list_cmdtool_bytes))
        no_bytes = len(list_cmdtool_bytes)
        if no_bytes != 1:
            log_error = "Create debuguser cmdtool did not return the expected output.."
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return_code = int(list_cmdtool_bytes[0], 16)
        if 0 != return_code:
            log_error = "Create debuguser cmdtool failed with return code={}..".format(return_code)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("Create debuguser cmdtool successful..")

    def __set_root_password(self):
        uefi_output = self.__execute_uefi_cmd(self.CMDTOOL_SET_ROOT_PWD)
        list_cmdtool_bytes = self.__get_cmdtool_response_bytes(uefi_output)
        self._log.info("Set root password cmdtool output={}".format(list_cmdtool_bytes))
        no_bytes = len(list_cmdtool_bytes)
        if no_bytes != 1:
            log_error = "Set root password cmdtool did not return the expected output.."
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return_code = int(list_cmdtool_bytes[0], 16)
        if 0 != return_code:
            log_error = "Set root password cmdtool failed with return code={}..".format(return_code)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("Set root password cmdtool successful..")

    def __set_password(self):
        uefi_output = self.__execute_uefi_cmd(self.CMDTOOL_SET_PWD)
        list_cmdtool_bytes = self.__get_cmdtool_response_bytes(uefi_output)
        self._log.info("Set password cmdtool output={}".format(list_cmdtool_bytes))
        no_bytes = len(list_cmdtool_bytes)
        if no_bytes != 1:
            log_error = "Set password cmdtool did not return the expected output.."
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return_code = int(list_cmdtool_bytes[0], 16)
        if 0 != return_code:
            log_error = "Set password cmdtool failed with return code={}..".format(return_code)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("Set password cmdtool successful..")

    def __enable_userid_2(self):
        uefi_output = self.__execute_uefi_cmd(self.CMDTOOL_ENABLE_USER_ID_2)
        list_cmdtool_bytes = self.__get_cmdtool_response_bytes(uefi_output)
        self._log.info("Enable userid 2 cmdtool output={}".format(list_cmdtool_bytes))
        no_bytes = len(list_cmdtool_bytes)
        if no_bytes != 1:
            log_error = "Enable userid 2 cmdtool did not return the expected output.."
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return_code = int(list_cmdtool_bytes[0], 16)
        if 0 != return_code:
            log_error = "Enable userid 2 cmdtool failed with return code={}..".format(return_code)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("Enable userid 2 cmdtool successful..")

    def __enable_mtm_mode(self):
        uefi_output = self.__execute_uefi_cmd(self.CMDTOOL_ENABLE_MTM)
        list_cmdtool_bytes = self.__get_cmdtool_response_bytes(uefi_output)
        self._log.info("Enable MTM mode cmdtool output={}".format(list_cmdtool_bytes))
        no_bytes = len(list_cmdtool_bytes)
        if no_bytes != 1:
            log_error = "Enable MTM mode cmdtool did not return the expected output.."
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return_code = int(list_cmdtool_bytes[0], 16)
        if 0 != return_code:
            log_error = "Enable MTM mode cmdtool failed with return code={}..".format(return_code)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("Enable MTM mode cmdtool successful..")

    def __enable_administrator_access(self, channel):
        """
        This function enables administrator access to debuguser for
        channel 1 and channel 3
        """
        if channel != self.CHANNEL_1 and channel != self.CHANNEL_3:
            log_error = "Invalid channel number '{}' specified..".format(channel)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info("Running commands to enable administrator access to channel='{}'".format(channel))

        if channel == self.CHANNEL_1:
            admin_access_cmd1 = self.CMDTOOL_ACCESS_TO_CH1_CMD1
            admin_access_cmd2 = self.CMDTOOL_ACCESS_TO_CH1_CMD2
        else:
            admin_access_cmd1 = self.CMDTOOL_ACCESS_TO_CH3_CMD1
            admin_access_cmd2 = self.CMDTOOL_ACCESS_TO_CH3_CMD2
        #
        # execute cmd1 for admin access
        #
        uefi_output = self.__execute_uefi_cmd(admin_access_cmd1)
        list_cmdtool_bytes = self.__get_cmdtool_response_bytes(uefi_output)
        self._log.info("Enable administrator access to channel '{}' cmdtool-1 "
                       "output={}".format(channel,list_cmdtool_bytes))
        no_bytes = len(list_cmdtool_bytes)
        if no_bytes != 5:
            log_error = "Enable administrator access to channel '{}' cmdtool-1 did not return the expected " \
                        "output..".format(channel)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return_code = int(list_cmdtool_bytes[0], 16)
        if 0 != return_code:
            log_error = "Enable administrator access to channel '{}' cmdtool-1 failed with return " \
                        "code={}..".format(channel, return_code)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("Enable administrator access to channel '{}' cmdtool-1 successful..".format(channel))
        #
        # execute cmd2 for admin access
        #
        uefi_output = self.__execute_uefi_cmd(admin_access_cmd2)
        list_cmdtool_bytes = self.__get_cmdtool_response_bytes(uefi_output)
        self._log.info("Enable administrator access to channel '{}' cmdtool-2 "
                       "output={}".format(channel,list_cmdtool_bytes))
        no_bytes = len(list_cmdtool_bytes)
        if no_bytes != 1:
            log_error = "Enable administrator access to channel '{}' cmdtool-2 did not return the expected " \
                        "output..".format(channel)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return_code = int(list_cmdtool_bytes[0], 16)
        if 0 != return_code:
            log_error = "Enable administrator access to channel '{}' cmdtool-2 failed with return " \
                        "code={}..".format(channel, return_code)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("Enable administrator access to channel '{}' cmdtool-2 successful..".format(channel))

    def __execute_uefi_cmd(self, cmd_line):
        uefi_output = self._uefi_obj.execute(cmd_line, self._timeout)
        formatted_output = self.ansi_reg_expr.sub('', str(uefi_output))
        return formatted_output

    def __get_cmdtool_response_bytes(self, uefi_output):
        list_lines = uefi_output.splitlines()
        cmdtool_output = None
        for line in list_lines:
            match = re.findall(self.hexa_reg_expr, line)
            if match:
                cmdtool_output = match[0]
                break
        if cmdtool_output is None:
            log_error = "No response from cmdtool.efi..."
            self._log.error(log_error)
            raise RuntimeError(log_error)
        list_cmdtool_bytes = str(cmdtool_output).split(" ")
        return list_cmdtool_bytes