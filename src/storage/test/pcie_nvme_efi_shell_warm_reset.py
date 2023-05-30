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
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.bios_util import ItpXmlCli, BootOptions, BiosUtil
from src.lib.dtaf_content_constants import SutInventoryConstants
from src.lib.os_installation_lib import OsInstallationLib
from src.lib.test_content_logger import TestContentLogger
from src.lib.install_collateral import InstallCollateral

from src.environment.os_installation import OsInstallation
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.lib import content_exceptions
from src.storage.test.storage_common import StorageCommon


class PcieNvmeEfiShellWarmReset(TxtBaseTest):
    """  Phoenix ID : 16013536806 Pcie Nvme - EFI shell reset(warm)

    This Testcase aims at Efi shell warm reset on U.2 Nvme
    """
    TEST_CASE_ID = ["16013536806", "Pcie Nvme - EFI shell reset(warm)"]
    ROOT_DIR = "/root"
    WAIT_TIME = 60
    WARM_RESET_ZIP_FILE = "warmreset.zip"
    step_data_dict = {
        1: {'step_details': 'Copy the startup.nsh file to the pcie nvme from the EFI shell.',
            'expected_results': 'Successfully copied the startup.nsh file to pcie nvme from EFI shell.'},
        2: {'step_details': 'Change the boot  order and make the UEFI shell as the first boot.',
            'expected_results': 'Successfully booted the system to UEFI'},
        3: {'step_details': 'Execute the startup.nsh for 100 cycles',
            'expected_results': 'Successfully performed 100 cycles of warm reset'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PcieNvmeEfiShellWarmReset object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieNvmeEfiShellWarmReset, self).__init__(test_log, arguments, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._csp = ProviderFactory.create(self._csp_cfg, self._log)
        self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)
        self.previous_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        self._os_install = OsInstallation(test_log, cfg_opts)
        self._os_installation_lib = OsInstallationLib(test_log, cfg_opts)  # type: OsInstallationLib
        self._storage_common = StorageCommon(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        super(PcieNvmeEfiShellWarmReset, self).prepare()

    def execute(self):
        """
        This method functionality is to execute EFI shell warm reset( reset -w) to
        be triggered on pcie nvme.

        :return: True
        :raise: If installation failed raise content_exceptions.TestFail
        """
        # Step logger Start for Step 1
        self._test_content_logger.start_step_logger(1)
        self._storage_common.verify_disks_in_sut_and_host()

        # Download the file from artifactory and copy it to SUT
        self._os.execute("mkdir /mnt/", self._command_timeout)
        zip_file_path = self._install_collateral.download_and_copy_zip_to_sut(self.ROOT_DIR + "/reset", self.WARM_RESET_ZIP_FILE)
        self._copy_usb.copy_file_from_sut_to_usb(self._common_content_lib, self._common_content_configuration,
                                                 zip_file_path + "/.")
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, True)

        # Step logger Start for Step 2
        self._test_content_logger.start_step_logger(2)
        cycles = self._common_content_configuration.get_reset_count()
        timeout = self._common_content_configuration.get_timeout_for_powercycles()
        self._log.info("Previous boot order {}".format(self.previous_boot_order))
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._log.info("waiting for uefi shell..")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
        startup_cmd = "startup.nsh"
        self._log.info("Executing '{}' command to perform warm reset".format(startup_cmd))
        count = 1
        usb_drive_path = ""
        while count < cycles:
            for usb_drive in usb_drive_list:
                self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(usb_drive)
                try:
                    self._uefi_obj.execute(startup_cmd, 3600)
                    usb_drive_path = usb_drive
                except TimeoutError:
                    pass
                self._log.info("Warm Reset successfull!!")
                time.sleep(timeout)
                if not self._os_installation_lib.switch_usb_to_host():
                    self._log.error("USB_DRIVE Is Not Connected To HostMachine")
                    raise content_exceptions.TestFail("USB_DRIVE Is Not Connected To Host Machine")
                count = int(self._common_content_lib.find_and_read_file_in_host_usb("count.txt")[0])
                self._log.info("warm reset count : {} times".format(count))
                if count < cycles:
                    if not self._os_installation_lib.switch_usb_to_target():
                        self._log.error("USB_DRIVE Is Not Connected To DUT")
                        raise content_exceptions.TestFail("USB_DRIVE Is Not Connected To DUT")

        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._log.info("waiting for uefi shell..")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        self._uefi_obj.execute(r'ESC')
        self._uefi_obj.execute(usb_drive_path)
        self._uefi_obj.execute("rm {}".format(startup_cmd))
        self._uefi_obj.exit_uefi()
        time.sleep(self._bios_boot_menu_entry_wait_time)
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, True)
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
            if not self._os_installation_lib.switch_usb_to_target():
                self._log.error("USB_DRIVE Is Not Connected To DUT")
                raise content_exceptions.TestFail("USB_DRIVE Is Not Connected back To DUT")
        except Exception as ex:
            raise ex
        super(PcieNvmeEfiShellWarmReset, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieNvmeEfiShellWarmReset.main() else Framework.TEST_RESULT_FAIL)
