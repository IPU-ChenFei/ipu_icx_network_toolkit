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
import re
import os

from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.flash import FlashDevices


class FlashUtil(object):
    """
    Flashes Firmware to the Sut and verifies newer version of Bios ID after Flashing the firmware to sut.
    """
    os_cmd_strings = {
        OperatingSystems.LINUX: 'dmidecode -s bios-version',
        OperatingSystems.WINDOWS: 'wmic bios get smbiosbiosversion'
    }

    cmd_parse_strings = {
        OperatingSystems.WINDOWS: r"SMBIOSBIOSVersion\s+(.+)$"
    }

    def __init__(self, log, os_obj, emulator_obj, common_content_lib_obj, common_content_config_obj):
        self._emulator_obj = emulator_obj
        self._os_obj = os_obj
        self._log = log
        self._common_content_conf_obj = common_content_config_obj
        self._common_content_lib_obj = common_content_lib_obj
        self._command_timeout = int(self._common_content_conf_obj.get_command_timeout())

    def flash_binary(self, image):
        """
        This function  flashes the ifwi binary file.

        :param image: Path of the binary ifwi image which needs to be programmed to sut.
        :return: None
        """

        self._log.info("Flashing Binary image")
        self._emulator_obj.flash_image(image, FlashDevices.PCH)

    def flash_ifwi_image(self, image):
        """
        This function  flashes the ifwi binary file.

        :param image: Ifwi image with full path
        """
        img_path = os.path.dirname(image)
        bin_file = os.path.basename(image)
        self._log.info("Flashing Binary image {}".format(bin_file))
        self._emulator_obj.flash_image(img_path+"\\", bin_file)

    def get_bios_version(self):
        """
        Get the BIOS version number of the BIOS image currently programmed on the SUT.

        :return: String with the version of the BIOS else None
        :raise: runtimeerror: if bios id is not availble.
        """
        # Get the BIOS ID from the OS
        try:
            bios_id = self._common_content_lib_obj.execute_sut_cmd(
                self.os_cmd_strings[self._os_obj.os_type], "Bios version", self._command_timeout)
            if self._os_obj.os_type == OperatingSystems.WINDOWS:
                bios_id = bios_id.strip()
                bios_id = re.match(self.cmd_parse_strings[self._os_obj.os_type], bios_id)
                bios_id = bios_id.group(1)
            if bios_id is None:
                raise RuntimeError("Could not find BIOS ID in the OS output!")
            else:
                return bios_id.strip()
        except KeyError:
            raise KeyError("This function does not currently support " + str(self._os_obj.os_type))
