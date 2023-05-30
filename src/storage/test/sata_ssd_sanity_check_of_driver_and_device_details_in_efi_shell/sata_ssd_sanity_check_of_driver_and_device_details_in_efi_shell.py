#!/usr/bin/env python
##########################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and
# proprietary and confidential information of Intel Corporation and its
# suppliers and licensors, and is protected by worldwide copyright and trade
# secret laws and treaty provisions. No part of the Material may be used,copied,
# reproduced, modified, published, uploaded, posted, transmitted, distributed,
# or disclosed in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################
import sys
import time
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.uefi_shell import UefiShellProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.bios_util import ItpXmlCli
from src.lib.bios_util import BootOptions
from src.lib.install_collateral import InstallCollateral
from src.lib.uefi_util import UefiUtil
from src.lib import content_exceptions
from src.storage.lib.storage_common import StorageCommon
from src.lib.test_content_logger import TestContentLogger


class PIStorageSanityTestThroughUEFIDrive(ContentBaseTestCase):
    """
    Phoenix ID : 16013780405-SATASSD-Sanity check of Driver and Device details in EFI shell
    1. Changes the Boot order to UEFI shell.
    2. Navigate to UEFI shell.
    3. Executes command Drivers and Devices in UEFI shell and verify the output.
    4. Changes boot order to default.
    5. Navigates to Os.
    """

    TEST_CASE_ID = ["16013780405", "SATA_SSD_SanityCheck_of_Driver_and_Device_In_UEFI"]
    WAIT_TIME_OUT = 5
    DRIVERS_CMD = "DRIVERS"
    DEVICES_CMD = "DEVICES"
    SATA_DRIVERS_STR = r"Serial ATA Controller Initializatio"
    STEP_DATA_DICT = {
        1: {'step_details': 'Boot to UEFI',
            'expected_results': 'System booted to UEFI'},
        2: {'step_details': 'Run the command Drivers',
            'expected_results': 'Verify SATA driver is present in the output'},
        3: {'step_details': 'Run the command Devices',
            'expected_results': 'Verify SATA devices are present in the output'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of PIStorageSanityTestThroughUEFIDrive.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(PIStorageSanityTestThroughUEFIDrive, self).__init__(test_log, arguments, cfg_opts)
        self.install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        uefi_cfg = cfg_opts.find(UefiShellProvider.DEFAULT_CONFIG_PATH)
        self._uefi_obj = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider
        bios_boot_menu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self._bios_boot_menu_obj = ProviderFactory.create(bios_boot_menu_cfg,
                                                          test_log)  # type: BiosBootMenuProvider
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_obj = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider
        self._uefi_util_obj = UefiUtil(
            self._log,
            self._uefi_obj,
            self._bios_boot_menu_obj,
            self.ac_power,
            self._common_content_configuration, self.os)
        self.previous_boot_order = None
        self.current_boot_order = None
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._csp = ProviderFactory.create(self._csp_cfg, self._log)
        self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)
        self.storage_common_lib = StorageCommon(self._log, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """
        Executing the prepare.
        """
        super(PIStorageSanityTestThroughUEFIDrive, self).prepare()

    def execute(self):
        """
        Navigates to UEFI shell navigates, executes like PCI, Drivers and Devices
        command and identifies the Bus, Mass Storage Controller - Non-volatile memory subsystem, NVM Express Driver,
        and NVMe Devices info and sets the boot order to initial boot order and boot to os.

        :return True else false
        :raise: content_exceptions.TestFail
        """
        # Step logger Start for Step 1
        self._test_content_logger.start_step_logger(1)
        self._log.info("Getting current boot order")
        self.previous_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Current boot order {}".format(self.previous_boot_order))
        self._log.info("Setting the default boot order to {}".format(BootOptions.UEFI))
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("waiting for UEFI shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, True)
        time.sleep(self.WAIT_TIME_OUT)

        # Step logger Start for Step 2
        self._test_content_logger.start_step_logger(2)
        drivers_cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.DRIVERS_CMD)
        sata_drivers_list = []
        for each in drivers_cmd_output:
            if self.SATA_DRIVERS_STR in each:
                sata_drivers_list.append(each[:-1])
        self._log.debug("All drivers info:{}".format(drivers_cmd_output))
        self._log.info("Identifies the SATA Drivers:{}".format(sata_drivers_list))
        if not drivers_cmd_output:
            self._log.error("unable to execute command in uefi ")
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, True)
        time.sleep(self.WAIT_TIME_OUT)

        # Step logger Start for Step 3
        self._test_content_logger.start_step_logger(3)
        devices_cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.DEVICES_CMD)
        sata_device_list = []
        device_list_from_inventory_file = \
            self.storage_common_lib.get_model_no_of_device_from_inventory_file(device_type="sata")
        for each in devices_cmd_output:
            for device in device_list_from_inventory_file:
                if device in each:
                    sata_device_list.append(each[:-1])
        self._log.debug("All Devices info:{}".format(devices_cmd_output))
        self._log.info("Identifies the disk either by model or mark:{}".format(sata_device_list))
        if not devices_cmd_output:
            raise content_exceptions.TestFail("Unable to execute command in uefi ")
        self.itp_xml_cli_util.set_boot_order(self.previous_boot_order)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("waiting for os to be alive")
        self.os.wait_for_os(self.reboot_timeout)
        self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        if self.itp_xml_cli_util is None:
            self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)
        if str(self.current_boot_order) != str(self.previous_boot_order):
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_order)
            self.perform_graceful_g3()
        super(PIStorageSanityTestThroughUEFIDrive, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PIStorageSanityTestThroughUEFIDrive.main()
             else Framework.TEST_RESULT_FAIL)
