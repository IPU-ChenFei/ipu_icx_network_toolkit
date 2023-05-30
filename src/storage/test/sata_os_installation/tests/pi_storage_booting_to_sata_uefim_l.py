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

import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.uefi_shell import UefiShellProvider

from src.environment.os_installation import OsInstallation
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib import content_exceptions
from src.lib.os_installation_lib import OsInstallationLib
from src.lib.test_content_logger import TestContentLogger
from src.lib.uefi_util import UefiUtil
from src.provider.storage_provider import StorageProvider
from src.lib.dtaf_content_constants import SutInventoryConstants


class StorageBootingToSataUEFIMLinux(BaseTestCase):
    """
    HPALM : H80259-PI_Storage_BootingToSATA_UEFIM_L.

    Install RHEL OS on the platform
    """
    USB_CMD = "FS0:"
    MAPR_CMD = "map -r"
    EFI_CMD = "CD EFI"
    BOOT_CMD = "CD BOOT"
    GRUB_INSTALL = "grubx64.efi"
    WAIT_TIME_OUT = 5

    TEST_CASE_ID = ["H80259", "PI_Storage_BootingToSATA_UEFIM_L"]

    step_data_dict = {1: {'step_details': 'Copy and extract os and software packages into USB',
                          'expected_results': 'Successfully copied and extracted os and software packages into USB'},
                      2: {'step_details': 'Change 1st BOOT ORDER to SATA drive and select UEFI shell for grub install',
                          'expected_results': 'Successfully changed BOOT ORDER to SATA and selected UEFI shell for '
                                              'grub install'},
                      3: {'step_details': 'Execute grub install command in UEFI shell for os installation',
                          'expected_results': 'Successfully executed commands for os installation'},
                      4: {'step_details': 'Verify OS is successfully installed in SATA or not',
                          'expected_results': 'Verified OS installation is successful in SATA or not'},
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageBootingToSataUEFIMLinux object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts
        self._cc_log_path = arguments.outputpath
        super(StorageBootingToSataUEFIMLinux, self).__init__(test_log, arguments, cfg_opts)
        self._os_install = OsInstallation(test_log, cfg_opts)
        self._os_installation_lib = OsInstallationLib(test_log, self._cfg_opts)  # type: OsInstallationLib
        self._common_content_configuration = ContentConfiguration(self._log)
        uefi_cfg = cfg_opts.find(UefiShellProvider.DEFAULT_CONFIG_PATH)
        self._uefi_obj = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider
        bios_boot_menu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self._bios_boot_menu_obj = ProviderFactory.create(bios_boot_menu_cfg,
                                                          test_log)  # type: BiosBootMenuProvider
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self.ac_power = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider
        self._common_content_configuration = ContentConfiguration(self._log)
        self.sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(self.sut_os_cfg, test_log)  # type: SutOsProvider
        self._uefi_util_obj = UefiUtil(
            self._log,
            self._uefi_obj,
            self._bios_boot_menu_obj,
            self.ac_power,
            self._common_content_configuration, self._os)
        self.name_ssd = None
        self._storage_provider = StorageProvider.factory(self._log, self._os, self._cfg_opts, "os")
        self._common_content_lib = CommonContentLib(self._log, self._os, None)
        self.log_dir = None
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()  # reboot timeout in seconds
        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    @classmethod
    def add_arguments(cls, parser):
        super(StorageBootingToSataUEFIMLinux, cls).add_arguments(parser)
        # Use add_argument
        parser.add_argument('-o', '--outputpath', action="store", default="",
                            help="Log folder to copy log files to command center")

    def prepare(self):
        # type: () -> None
        """
        1. Find the ssd name from the sut inventory config file

        :return: None
        """
        sut_inv_file_path = self._os_install.get_sut_inventory_file_path()
        self.name_ssd = None

        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if "sata_ssd_name_rhel" in line:
                    self.name_ssd = line
                    break

        if not self.name_ssd:
            raise content_exceptions.TestError("Unable to find ssd name, please check the file under "
                                               "{}".format(sut_inv_file_path))
        self.name_ssd = self.name_ssd.split("=")[1]

        self._log.info("SSD Name from config file : {}".format(self.name_ssd))
        self._common_content_lib.update_sut_inventory_file(SutInventoryConstants.SATA, SutInventoryConstants.RHEL)

    def execute(self):
        """
        This function is responsible for below tasks
        1. Switch USB to Host
        2. Copying and extracting os and sw packages to USB
        3. Switch USB to DUT
        4. Changing first boot order to SATA
        5. Executing commands in UEFI shell for os installation
        6. Verifying os installation in SATA

        :return: True, if the test case is successful.
        :raise: TestFail
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        # Mandatory for USB To Be Connect To Host
        if not self._os_installation_lib.switch_usb_to_host():
            self._log.error("USB_DRIVE Is Not Connected To HostMachine")
            raise content_exceptions.TestFail("USB_DRIVE Is Not Connected To HostMachine")
        time.sleep(5)  # Mandatory Sleep

        # Downloading And Extracting OS Image to USB_DRIVE
        if not self._os_installation_lib.download_extract_os_image(self._os_installation_lib.extract_os_package,
                                                                self._os_installation_lib.format_pendrive):
            self._log.error("Os Package Extraction TO USB Failed")
            raise content_exceptions.TestFail("Os Package Extraction TO USB Failed")

        # Downloading And Extracting SW Image to USB_DRIVE
        if not self._os_installation_lib.download_extract_sft_package(self._os_installation_lib.extract_sft_package,
                                                                   self._os_installation_lib.format_pendrive):
            self._log.error("Software Package Extraction TO USB Failed")
            raise content_exceptions.TestFail("Software Package Extraction TO USB Failed")

        if self._os_installation_lib.os_install:
            # Mandatory for USB To Be Connect To SUT
            if not self._os_installation_lib.switch_usb_to_target():
                self._log.error("USB_DRIVE Is Not Connected To Platform(SUT)")
                raise content_exceptions.TestFail("USB_DRIVE Is Not Connected To Platform(SUT)")

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # Enter into BIOS SETUP Page to change BIOS BOOTORDER AND Select SATA For OS-Installation
        self._os_installation_lib.platform_ac_power_off()
        self._os_installation_lib.platform_ac_power_on()
        self._os_installation_lib.enter_into_bios()

        self._log.info(
            "Entering Into Bios SETUP Page To Change BIOS BOOTORDER AND Select SATA For OS-Installation")
        if self._os_installation_lib.bios_path_navigation(path=self._os_installation_lib.bios_path):
            self._os_installation_lib.setupmenu.change_order([str(self._os_installation_lib.hardisk_drive_name)])
            self._log.info("BOOT Order Change Done {0} First Boot Order".format(self._os_installation_lib.
                                                                                hardisk_drive_name))
            if self._os_installation_lib.bios_path_navigation(path=self._os_installation_lib.save_knob_name):
                self._log.info("Changing and Saving Boot-Order Successful")
                self._os_installation_lib.setupmenu.back_to_root(10, False)
            else:
                self._log.error("Unable To Change or Find BootOrder")
                raise content_exceptions.TestFail("Unable To Change or Find BootOrder")

            self._log.info("waiting for entering to uefi shell..")
            if self._os_installation_lib.bios_path_navigation(path=self._os_installation_lib.boot_select_uefi_path):
                self._log.info("Selecting SATA To Proceed with Boot is Successful")
            else:
                self._log.error("Unable To Enter Into Bios SETUP Page")
                raise content_exceptions.TestFail("Unable To Enter Into Bios SETUP Page")
        else:
            self._log.error("Unable To Change Boot-Order and FAILED To Proceed With OS Installation")

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        # Execute command in UEFI shell for os installation
        map_cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.MAPR_CMD)
        self._log.info(map_cmd_output)
        if not map_cmd_output:
            self._log.error("unable to execute {} command in uefi ".format(self.MAPR_CMD))

        drivers_cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.USB_CMD)
        self._log.info(drivers_cmd_output)
        if not drivers_cmd_output:
            self._log.error("unable to execute {} command in uefi ".format(self.USB_CMD))

        efi_cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.EFI_CMD)
        self._log.info(efi_cmd_output)
        if not efi_cmd_output:
            self._log.error("unable to execute the command {} in uefi ".format(self.EFI_CMD))

        boot_cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.BOOT_CMD)
        self._log.info(boot_cmd_output)
        if not boot_cmd_output:
            self._log.error("unable to execute the command {} in uefi ".format(self.BOOT_CMD))

        self._uefi_util_obj.execute_grub_install_cmd_in_uefi(self.GRUB_INSTALL)

        self._log.info("OS-Installation In Progress Will Taken Some Time")

        # verifying OS installation
        for i in range(0, 200):
            time.sleep(60)
            if self._os.is_alive():
                self._log.info("Booted Os And Entered Into OS Successfully")
                break
            elif i == 120:
                self._log.info("Os Installation Had Issues")
                raise content_exceptions.TestFail("Os Installation Had Issues.System is not alive")
            else:
                self._log.debug("OS Installation Is IN-Progress")

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        # Verifying if os installed in SATA or not
        self.log_dir = self._common_content_lib.get_log_file_dir()
        lsblk_res = self._storage_provider.get_booted_device()
        self._log.info("booted device is {}".format(str(lsblk_res)))
        device_info = self._storage_provider.get_device_type(lsblk_res, self.name_ssd)

        if not device_info["usb_type"]:
            raise content_exceptions.TestFail("Unable to fetch the SATA device type..")

        if not device_info["serial"]:
            raise content_exceptions.TestFail("Unable to fetch the serial number information of the device..")

        if "SATA" not in device_info["usb_type"].upper():
            raise content_exceptions.TestFail("OS not installed on the SATA SSD, please try again..")

        self._log.info("Successfully verified that OS installed in SATA device..")

        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)
        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        # copy logs to CC folder if provided
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

        super(StorageBootingToSataUEFIMLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageBootingToSataUEFIMLinux.main() else Framework.TEST_RESULT_FAIL)
