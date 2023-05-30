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


class PIStorageSanityTestthroughUEFIdrive(ContentBaseTestCase):
    """
    HPQC ID : H80280-PI_Storage_SanityTest_through_UEFI_drive
    GLASGOW ID : 57140.0
    1. Changes the Boot order to UEFI shell.
    2. Navigate to UEFI shell.
    3. Executes command like PCI, Drivers and Devices in UEFI shell.
    4. Changes boot order to default.
    5. Navigates to Os.
    """

    TEST_CASE_ID = ["H80280", "PI_Storage_SanityTest_through_UEFI_drive"]
    WAIT_TIME_OUT = 5
    PCI_CMD = "PCI"
    DRIVERS_CMD = "DRIVERS"
    DEVICES_CMD = "DEVICES"
    MASS_NON_VOLATILE_STR = "Mass Storage Controller - Non-volatile memory subsystem"
    NVM_DRIVERS_STR = "NVM Express Driver"
    NVME_MODEL_OR_MARK_STR = "NVMe"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of PIStorageSanityTestthroughUEFIdrive.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(PIStorageSanityTestthroughUEFIdrive, self).__init__(test_log, arguments, cfg_opts)
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
        csp = ProviderFactory.create(self._csp_cfg, self._log)  # type: SiliconRegProvider
        self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)

    def prepare(self):
        # type: () -> None
        """
        Executing the prepare.
        """
        super(PIStorageSanityTestthroughUEFIdrive, self).prepare()

    def execute(self):
        """
        Navigates to UEFI shell navigates, executes like PCI, Drivers and Devices
        command and identifies the Bus, Mass Storage Controller - Non-volatile memory subsystem, NVM Express Driver,
        and NVMe Devices info and sets the boot order to initial boot order and boot to os.

        :return True else false
        :raise: content_exceptions.TestFail
        """
        self._log.info("Getting current boot order")
        self.previous_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Current boot order {}".format(self.previous_boot_order))
        self._log.info("Setting the default boot order to {}".format(BootOptions.UEFI))
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("waiting for UEFI shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        time.sleep(self.WAIT_TIME_OUT)
        pci_cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
             self.PCI_CMD)
        non_volatile_list = []
        for each in pci_cmd_output:
            if self.MASS_NON_VOLATILE_STR in each:
                non_volatile_list.append(each[:-1])
        self._log.debug("All pci ports info:{}".format(pci_cmd_output))
        self._log.info("Identfies the pci bus and Mass Storage Controller-Non-volatile memory subsystem info:{}".format(
            non_volatile_list))
        if not pci_cmd_output:
            self._log.error("unable to execute command in uefi ")
        time.sleep(self.WAIT_TIME_OUT)
        drivers_cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.DRIVERS_CMD)
        nvme_drivers_list = []
        for each in drivers_cmd_output:
            if self.NVM_DRIVERS_STR in each:
                nvme_drivers_list.append(each[:-1])
        self._log.debug("All drivers info:{}".format(drivers_cmd_output))
        self._log.info("Identifies the NVM Drivers:{}".format(nvme_drivers_list))
        if not drivers_cmd_output:
            self._log.error("unable to execute command in uefi ")
        time.sleep(self.WAIT_TIME_OUT)
        devices_cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.DEVICES_CMD)
        nvme_device_list = []
        for each in devices_cmd_output:
            if self.NVME_MODEL_OR_MARK_STR in each:
                nvme_device_list.append(each[:-1])
        self._log.debug("All Devices info:{}".format(devices_cmd_output))
        self._log.info("Identifies the disk either by model or mark:{}".format(nvme_device_list))
        if not devices_cmd_output:
            raise content_exceptions.TestFail("Unable to execute command in uefi ")
        self.itp_xml_cli_util.set_boot_order(self.previous_boot_order)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("waiting for os to be alive")
        self.os.wait_for_os(self.reboot_timeout)
        self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        if self.itp_xml_cli_util is None:
            self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)
        if str(self.current_boot_order) != str(self.previous_boot_order):
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_order)
            self.perform_graceful_g3()
        super(PIStorageSanityTestthroughUEFIdrive, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PIStorageSanityTestthroughUEFIdrive.main()
             else Framework.TEST_RESULT_FAIL)
