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
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.uefi_shell import UefiShellProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.network.networking_common import NetworkingCommon
from src.provider.driver_provider import NetworkDrivers, DriverProvider
from src.lib import content_exceptions
from src.lib.content_configuration import ContentConfiguration
from src.lib.bios_util import ItpXmlCli, BootOptions
from src.lib.uefi_util import UefiUtil
from src.lib.test_content_logger import TestContentLogger


class ColumbiavilleNvmeUpgradeLinux(NetworkingCommon):
    """
    phoneix ID: 18014075692 - PI_Networking_Columbiaville_NVMUpgrade_EFI
    HPQC ID : H80137-PI_Networking_Columbiaville_NVMUpgrade_EFI
    This test case is used for NIC NVM firmware upgrade through Lanconfig.
    Description : 1. Download and unzip the NIC NVM firmware and Lanconfig tool on USB disk.
                 2. Boot unit to EFI shell
                 3. go to tool folder, run lanconfig.efi tool in EFi shell
    """
    TEST_CASE_ID = ["18014075692", "PI_Networking_Columbiaville_NVMUpgrade_EFI"]
    WAIT_TIME_OUT = 5
    USB_CMD = "FS0:"
    NVME_UPDATE_EFI_PATH = r"cd E810\EFI2x64"
    NVME_UPDATE_EFI_FILE_NAME = "nvmupdate64e.efi"
    STEP_DATA_DICT = {1: {'step_details': 'Download and unzip the NIC NVM firmware and Lanconfig tool on USB disk.',
                          'expected_results': 'NVM firmware and Lanconfig files are unzipped on USB disk'},
                      2: {'step_details': 'Boot unit to EFI shell',
                          'expected_results': 'verify unit boot to EFI shell. '},
                      3: {'step_details': 'go to tool folder, run lanconfig.efi tool in EFi shell',
                          'expected_results': 'Lanconfig tool can be launched. '}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of ColumbiavilleNvmeUpgradeLinux.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(ColumbiavilleNvmeUpgradeLinux, self).__init__(test_log, arguments, cfg_opts)
        self._driver_provider = DriverProvider.factory(self._log, cfg_opts, self.os)  # type: DriverProvider
        self._content_configuration = ContentConfiguration(self._log)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._driver_provider.install_driver(
            NetworkDrivers.COLUMBIAVILLE_DRIVER_CODE, NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)

        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider

        uefi_cfg = cfg_opts.find(UefiShellProvider.DEFAULT_CONFIG_PATH)
        self._uefi_obj = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider
        bios_boot_menu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self._bios_boot_menu_obj = ProviderFactory.create(bios_boot_menu_cfg,
                                                          test_log)  # type: BiosBootMenuProvider
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

        self.itp_xml_cli_util = ItpXmlCli(self._log)

    def prepare(self):  # type: () -> None
        """
        Pre-checks if the OS is Linux as this Test Case is Applicable only for Linux Os.
        :raise: content_exception.TestFail if the Sut is not in linux os.
        """
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError(
                "{} installation is not implemented for the os: {}".format(
                    NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME, self.os.os_type))

    def execute(self):  # type: () -> bool
        """
         This Method is Used to.
         1. Download and unzip the NIC NVM firmware and Lanconfig tool on USB disk.
         2. Boot unit to EFI shell
         3. go to tool folder, run lanconfig.efi tool in EFi shell

         :return: True if all steps executes and getting the status as expected.
         """
        self._test_content_logger.start_step_logger(1)
        self.copy_columbiaville_files(self.phy)
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        self._log.info("Getting current boot order")
        self.previous_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Current boot order {}".format(self.previous_boot_order))
        self._log.info("Setting the default boot order to {}".format(BootOptions.UEFI))
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("waiting for UEFI shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        time.sleep(self.WAIT_TIME_OUT)

        usb_cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.USB_CMD)
        self._log.info(usb_cmd_output)
        if not usb_cmd_output:
            self._log.error("unable to execute {} command in uefi ".format(self.USB_CMD))
        self._test_content_logger.end_step_logger(2, True)

        self._test_content_logger.start_step_logger(3)
        nvme_cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.NVME_UPDATE_EFI_PATH)
        self._log.info(nvme_cmd_output)
        if not nvme_cmd_output:
            self._log.error("unable to execute {} command in uefi ".format(self.NVME_UPDATE_EFI_PATH))

        efi_cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.NVME_UPDATE_EFI_FILE_NAME)
        self._log.info(efi_cmd_output)
        if not efi_cmd_output:
            self._log.error("unable to execute {} command in uefi ".format(self.NVME_UPDATE_EFI_FILE_NAME))
        self.itp_xml_cli_util.set_boot_order(self.previous_boot_order)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("waiting for os to be alive")
        self.os.wait_for_os(self.reboot_timeout)
        self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        return True

    def cleanup(self, return_status):  # type: (bool) -> None

        super(ColumbiavilleNvmeUpgradeLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ColumbiavilleNvmeUpgradeLinux.main()
             else Framework.TEST_RESULT_FAIL)

