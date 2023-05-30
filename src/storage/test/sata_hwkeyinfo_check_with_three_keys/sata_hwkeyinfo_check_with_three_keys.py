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
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.exceptions import TimeoutException
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.physical_control import PhysicalControlProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.bios_util import BootOptions, ItpXmlCli
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.lib.tools_constants import ArtifactoryName, ArtifactoryTools
from src.lib.uefi_util import UefiUtil
from src.provider.copy_usb_provider import UsbRemovableDriveProvider
from src.provider.host_usb_drive_provider import HostUsbDriveProvider
from src.provider.stressapp_provider import StressAppTestProvider
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.storage.lib.storage_common import StorageCommon
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions


class SataHWKeyInfoCheckWithThreeKeys(ContentBaseTestCase):
    """
    Phoenix ID : 16013584909 - SATA-HWKeyinfo check with Three keys(premium,standard and Intel)

    """
    BIOS_CONFIG_FILE_NAME = "raid_mode_enable.cfg"
    CHECK_VROC_EFI_FILE = "HWKeyCheckVROC.efi -a"
    MAP_CMD = "map -r"
    HW_INFO_FILE = "hw_vroc_details.txt"
    EFI_FILE_PATH = "vroc_files\PreOS-1168\efi_standalone_vroc_rs"
    UEFI_CONFIG_PATH = 'suts/sut/providers/uefi_shell'
    SUCCESS_STR = "{} Intel(R) VROC HW Key verified"
    SEARCH_FILE = "ls -r -a -b {}"
    CWD = "cd"
    TEST_CASE_ID = ["16013584909", "SATA-HWKeyinfo check with Three keys(premium,standard and Intel)"]
    step_data_dict = {1: {'step_details': 'Set the bios knob SATA Mode Selection to RAID',
                          'expected_results': 'Bios Knob Set as per requirement'},
                      2: {'step_details': 'Copy HWKeyCheckVROC.efi to USB.',
                          'expected_results': 'HWKeyCheckVROC.efi copied to USB.'},
                      3: {'step_details': 'Execute HWKeyCheckVROC.efi in UEFI and verify the Hardware Key.',
                          'expected_results': 'Correct Hardware key info displayed for the connected Key respectively!'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new SataHWKeyInfoCheckWithThreeKeys object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts
        super(SataHWKeyInfoCheckWithThreeKeys, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE_NAME)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self.storage_common_lib = StorageCommon(self._log, cfg_opts)
        self._copy_usb = UsbRemovableDriveProvider.factory(test_log, cfg_opts, self.os)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._host_usb_provider = HostUsbDriveProvider.factory(test_log, cfg_opts, self.os)
        phy_cfg = cfg_opts.find(PhysicalControlProvider.DEFAULT_CONFIG_PATH)
        self._phy = ProviderFactory.create(phy_cfg, test_log)  # type: PhysicalControlProvider
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._csp = ProviderFactory.create(self._csp_cfg, self._log)
        self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)
        self.previous_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        uefi_cfg = cfg_opts.find(self.UEFI_CONFIG_PATH)
        self._uefi_obj = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider
        bios_boot_menu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self._bios_boot_menu_obj = ProviderFactory.create(bios_boot_menu_cfg, test_log)  # type: BiosBootMenuProvider
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()
        self._uefi_util_obj = UefiUtil(
            self._log,
            self._uefi_obj,
            self._bios_boot_menu_obj,
            self.ac_power,
            self._common_content_configuration, self.os, cfg_opts=self._cfg)

    def uefi_find_file(self, eficmd):
        """
        This function navigates to a folder and executes the file.

        :param eficmd: The command which is to be executed
        :raise: RuntimeError if unable to execute efi search for the file
        :return: None
        """
        efi_file_name = eficmd.split(" ")[0].strip()
        efi_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.SEARCH_FILE.format(efi_file_name))
        if efi_output:
            for output in efi_output:
                drivepath = self._uefi_util_obj.get_drive_path(efi_output)
                if drivepath and (efi_file_name in output) and ("ls" not in output):
                    try:
                        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.CWD + " " + '"' + drivepath + '"')
                    except TimeoutException:
                        self._log.debug("Ignoring timeout exception")
        else:
            self._log.error("Unable to execute efi search for the file")
            raise RuntimeError("Unable to execute efi search for the file")

    def get_hwkey_details_from_uefi(self):
        """
        This Method boots to uefi shell and selects the usb drive where .efi files are present and then executes
        pcrdump command.

        :param pcr_dump_cmd: pcr command to execute
        :param pcr_dump_dir: directory name where efi file is present
        :raise: content exception if unable to get result after running pcr command
        :return: result of the pcrdump command
        """
        self._log.info("Collecting HWVROCKeyCheck from uefi shell")
        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.MAP_CMD)
        usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
        for each_drive in usb_drive_list:
            self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.MAP_CMD)
            self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(each_drive)
            self.uefi_find_file(self.CHECK_VROC_EFI_FILE)
            self._log.info("Executing command {}".format(self.CHECK_VROC_EFI_FILE))
            try:
                self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.CHECK_VROC_EFI_FILE + " >> " + self.HW_INFO_FILE)
            except TimeoutException:
                self._log.debug("Ignoring timeout exception")
                break
        return self.HW_INFO_FILE

    def prepare(self):
        # type: () -> None
        """
        This method is to do the below tasks
        1. Verifying the sata devices are connected in the SUT
        2. Setting the bios knob SATA Mode Selection to AHCI
        3. Copy and install burin tool.
        4. Execute burin tool in SSD where OS not installed.

        :return None
        """
        # start of step 1
        self._test_content_logger.start_step_logger(1)

        super(SataHWKeyInfoCheckWithThreeKeys, self).prepare()

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, True)

    def execute(self, host_usb_provider=None):
        """
        This method is used to install and execute burnin tool.
        """
        # start of step 2
        self._test_content_logger.start_step_logger(2)
        # Copy HWKeyCheckVROC.efi to USB.
        artifactory_name = ArtifactoryName.DictUEFITools[ArtifactoryTools.VROC_ZIP_FILE]
        zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name, exec_env="Uefi")
        drive = self._host_usb_provider.get_mount_points()[0]
        self._host_usb_provider.copy_file_to_usb(zip_file_path, drive)
        self._common_content_lib.execute_cmd_on_host(
            r"powershell.exe Expand-Archive -Force {}\{} {}\vroc_files".format(drive, artifactory_name, drive))
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, True)

        # start of step 3
        self._test_content_logger.start_step_logger(3)
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("waiting for uefi shell..")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        self.usb_set_time = self._common_content_configuration.get_usb_set_time_delay()
        self._phy.disconnect_usb(self.usb_set_time)  # USB disconnecting
        self._phy.connect_usb_to_sut(self.usb_set_time)
        time.sleep(self.usb_set_time)
        hw_key_file = self.get_hwkey_details_from_uefi()
        hw_check_vroc_key = self._common_content_configuration.get_vroc_key_info()
        self._phy.disconnect_usb(self.usb_set_time)
        self._phy.connect_usb_to_host(self.usb_set_time)
        time.sleep(self.usb_set_time)
        cmd_output = self._common_content_lib.execute_cmd_on_host(
            "type {}\{}\{}".format(drive, self.EFI_FILE_PATH, hw_key_file))
        self._log.debug("HWCheckVROCKey.efi file contents : {}".format("cmd_output"))
        if self.SUCCESS_STR.format(hw_check_vroc_key) not in str(cmd_output):
            raise content_exceptions.TestFail("Failed to Verify Hardware Key Information!")
        self._log.info("Sucessfully Verified Hardware Key information of the Connected VROC Key!")
        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(3, True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """Test Cleanup"""
        # checking if boot order is equal to previous boot order
        try:
            current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
            if str(current_boot_order) != str(self.previous_boot_order):
                current_boot_list = current_boot_order.split("-")
                previous_boot_list = self.previous_boot_order.split("-")
                if previous_boot_list[0] in current_boot_list:
                    current_boot_list.remove(previous_boot_list[0])
                current_boot_list.insert(0, previous_boot_list[0])
                required_boot_order = "-".join(current_boot_list)
                self.itp_xml_cli_util.set_boot_order(required_boot_order)
                self.perform_graceful_g3()
                time.sleep(self.WAIT_TIME)
        except Exception as ex:
            raise ex
        super(SataHWKeyInfoCheckWithThreeKeys, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SataHWKeyInfoCheckWithThreeKeys.main() else Framework.TEST_RESULT_FAIL)
