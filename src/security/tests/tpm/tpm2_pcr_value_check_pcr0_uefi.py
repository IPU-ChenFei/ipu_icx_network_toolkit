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
import ipccli

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.bios_util import BootOptions
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_common import BootGuardValidator
from src.lib.bios_util import ItpXmlCli


class Tpm2PcrValueCheckPcr0Uefi(TxtBaseTest):
    """
    HPQLM ID : H79540-PI_Security_TPM2.0 PCR value check_PCR0_UEFI

    Verifies the PCR0 value will be changed between different BIOS version.
    """
    PCR_VALUE = 'PCR 00'
    WAIT_TIME = 60
    PREVIOUS_VERSION = "IFWI Previous Version"
    CURRENT_VERSION = "IFWI Current Version"
    FSCK_CMD = "fsck -a {}"
    SYNC_CMD = "sync"
    UMOUNT_CMD = "umount {}"
    TEST_CASE_ID = ["H79540", "PI_Security_TPM2.0_PCR_value_check_PCR0_UEFI"]
    STEP_DATA_DICT = {1: {'step_details': 'Copies pcrdump64.zip to SUT and then to USB',
                          'expected_results': 'pcrdump64.zip copied successfully to SUT and then to USB'},
                      2: {'step_details': 'Set boot order to UEFI shell and execute pcrdump64.efi files '
                                          'for current ifwi version.',
                          'expected_results': 'pcrdump64.efi command executed successfully for current ifwi version'},
                      3: {'step_details': 'Flash the N-1(previous) bios version',
                          'expected_results': 'N-1 version BIOS flashed successfully'},
                      4: {'step_details': 'Set boot order to UEFI shell and execute pcrdump64.efi files '
                                          'for N-1(previous) ifwi version.',
                          'expected_results': 'pcrdump64.efi command executed successfully for previous ifwi version'},
                      5: {'step_details': 'Compare PCR 00 value will different for both the BIOS version',
                          'expected_results': 'PCR 00 is different for both BIOS version as expected'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of Tpm2PcrValueCheckPcr0Uefi.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(Tpm2PcrValueCheckPcr0Uefi, self).__init__(test_log, arguments, cfg_opts)
        self.mount_point = self._copy_usb.get_mount_point(self._common_content_lib, self._common_content_configuration)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._boot_guard_obj = BootGuardValidator(test_log, arguments, cfg_opts)
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._csp = ProviderFactory.create(self._csp_cfg, test_log)
        self.itp_xml_cli_util = self._boot_guard_obj.itp_xml_cli_util
        self._flash_obj = self._boot_guard_obj._flash_obj
        self.itp = ipccli.baseaccess()

    def prepare(self):
        # type: () -> None
        """
        Copy pcrdump64.zip to SUT and then to USB drive
        """
        # copying the zip .efi from host to usb
        self._test_content_logger.start_step_logger(1)
        self._os.execute(self.FSCK_CMD.format(self.mount_point), self._command_timeout)
        self.copy_file(self._PCR_DUMP_64_ZIP_FILE)
        self._os.execute(self.SYNC_CMD, self._command_timeout)
        self._os.execute(self.UMOUNT_CMD.format(self.mount_point), self._command_timeout)
        time.sleep(self._command_timeout)
        try:
            self.previous_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        except Exception as e:  # catching IPC_Error which is in IPC library
            self._log.debug("Caught IPC_Error where IPC failed.  Attempting to initiate forcereconfig.  "
                            "Exception data: {}".format(e))
            self._log.debug("Reconfiguring IPC connection.")
            self.itp.forcereconfig()
            self._log.debug("Attempting to set BIOS knobs.")
            self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Previous boot order {}".format(self.previous_boot_order))
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Compare PCR0 Dump values generated by pcrdump64 before and after flashing
        1. Set boot order to UEFI shell and execute pcrdump64.efi files for current ifwi version.
        2. Flash the N-1 bios version(previous version)
        3. Set boot order to UEFI shell and execute pcrdump64.efi files for previous(N-1) ifwi version.
        4. Compare the pcr0 value between two different BIOS version(current and previous(N-1))

        :raise: Test fail exception if SUT does not boot to uefi shell or PCR value is same for both BIOS version
        :return: True if both the version has different pcr 00 value
        """
        self._test_content_logger.start_step_logger(2)
        pcr_dump_folder = ''
        for pcr_folder_name, pcr_zip_folder in self._PCR_DUMP_64_ZIP_FILE.items():
            pcr_dump_folder = pcr_folder_name
        # get PCR value for current IFWI
        try:
            self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        except Exception as e:  # catching IPC_Error which is in IPC library
            self._log.debug("Caught IPC_Error where IPC failed.  Attempting to initiate forcereconfig.  "
                            "Exception data: {}".format(e))
            self._log.debug("Reconfiguring IPC connection.")
            self.itp.forcereconfig()
            self._log.debug("Attempting to set BIOS knobs.")
            self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._log.info("waiting for UEFI shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        output_before_flash = self.get_pcrdump_from_uefi(
            pcr_dump_cmd=self._EXECUTE_PCRDUMP_64, pcr_dump_dir=pcr_dump_folder)
        self._log.debug("PCR dump for current ifwi version: {}".format(output_before_flash))
        pcr_values_for_current_ifwi = self.pcrdump64_data_formatting(output_before_flash)
        time.sleep(60)
        try:
            boot_order_before_setting = self.itp_xml_cli_util.get_current_boot_order_string()
        except Exception as e:  # catching IPC_Error which is in IPC library
            self._log.debug("Caught IPC_Error where IPC failed.  Attempting to initiate forcereconfig.  "
                            "Exception data: {}".format(e))
            self._log.debug("Reconfiguring IPC connection.")
            self.itp.forcereconfig()
            self._log.debug("Attempting to set BIOS knobs.")
            self.itp_xml_cli_util.get_current_boot_order_string()
        current_boot_list = boot_order_before_setting.split("-")
        previous_boot_list = self.previous_boot_order.split("-")
        if previous_boot_list[0] in current_boot_list:
            current_boot_list.remove(previous_boot_list[0])
        current_boot_list.insert(0, previous_boot_list[0])
        required_boot_order = "-".join(current_boot_list)
        self._log.info("Current boot order before setting it with new boot order : {} and the new boot order : {}"
                       "".format(boot_order_before_setting, required_boot_order))
        try:
            self.itp_xml_cli_util.set_boot_order(required_boot_order)
        except Exception as e:  # catching IPC_Error which is in IPC library
            self._log.debug("Caught IPC_Error where IPC failed.  Attempting to initiate forcereconfig.  "
                            "Exception data: {}".format(e))
            self._log.debug("Reconfiguring IPC connection.")
            self.itp.forcereconfig()
            self._log.debug("Attempting to set BIOS knobs.")
            self.itp_xml_cli_util.set_boot_order(required_boot_order)
        self._uefi_util_obj.graceful_sut_ac_power_on()
        self._os.wait_for_os(self._reboot_timeout)
        self._os.execute(self.FSCK_CMD.format(self.mount_point), self._command_timeout)
        self.copy_file(self._PCR_DUMP_64_ZIP_FILE)
        self._os.execute(self.SYNC_CMD, self._command_timeout)
        self._os.execute(self.UMOUNT_CMD.format(self.mount_point), self._command_timeout)
        time.sleep(self._command_timeout)
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self._boot_guard_obj.flash_binary_image(self.PREVIOUS_VERSION)
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        # get PCR value after flashing N-1 ifwi
        try:
            self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        except Exception as e:  # catching IPC_Error which is in IPC library
            self._log.debug("Caught IPC_Error where IPC failed.  Attempting to initiate forcereconfig.  "
                            "Exception data: {}".format(e))
            self._log.debug("Reconfiguring IPC connection.")
            self.itp.forcereconfig()
            self._log.debug("Attempting to set BIOS knobs.")
            self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._log.info("waiting for UEFI shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        output_after_flash = self.get_pcrdump_from_uefi(
            pcr_dump_cmd=self._EXECUTE_PCRDUMP_64, pcr_dump_dir=pcr_dump_folder)
        self._log.debug("PCR dump for previous ifwi version: {}".format(output_after_flash))
        pcr_values_for_previous_ifwi = self.pcrdump64_data_formatting(output_after_flash)
        try:
            boot_order_before_setting = self.itp_xml_cli_util.get_current_boot_order_string()
        except Exception as e:  # catching IPC_Error which is in IPC library
            self._log.debug("Caught IPC_Error where IPC failed.  Attempting to initiate forcereconfig.  "
                            "Exception data: {}".format(e))
            self._log.debug("Reconfiguring IPC connection.")
            self.itp.forcereconfig()
            self._log.debug("Attempting to set BIOS knobs.")
            boot_order_before_setting = self.itp_xml_cli_util.get_current_boot_order_string()
        current_boot_list = boot_order_before_setting.split("-")
        previous_boot_list = self.previous_boot_order.split("-")
        if previous_boot_list[0] in current_boot_list:
            current_boot_list.remove(previous_boot_list[0])
        current_boot_list.insert(0, previous_boot_list[0])
        required_boot_order = "-".join(current_boot_list)
        self._log.info("Current boot order before setting it with new boot order : {} and the new boot order : {}"
                       "".format(boot_order_before_setting, required_boot_order))
        try:
            self.itp_xml_cli_util.set_boot_order(required_boot_order)
        except Exception as e:  # catching IPC_Error which is in IPC library
            self._log.debug("Caught IPC_Error where IPC failed.  Attempting to initiate forcereconfig.  "
                            "Exception data: {}".format(e))
            self._log.debug("Reconfiguring IPC connection.")
            self.itp.forcereconfig()
            self._log.debug("Attempting to set BIOS knobs.")
            self.itp_xml_cli_util.set_boot_order(required_boot_order)
        self.perform_graceful_g3()
        self._os.execute(self.FSCK_CMD.format(self.mount_point), self._command_timeout)
        self.copy_file(self._PCR_DUMP_64_ZIP_FILE)
        self._os.execute(self.SYNC_CMD, self._command_timeout)
        self._os.execute(self.UMOUNT_CMD.format(self.mount_point), self._command_timeout)
        time.sleep(self._command_timeout)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        # compare the pcr 00 value current ifwi and previous(N-1) ifwi version
        if not self.compare_pcr_value(pcr_values_for_current_ifwi, pcr_values_for_previous_ifwi, self.PCR_VALUE):
            raise content_exceptions.TestFail("Pcr value {} for current and previous(N-1) ifwi version is same!!!".
                                              format(self.PCR_VALUE))
        self._log.info("Pcr value {} for current and previous(N-1) ifwi version is different as expected".
                       format(self.PCR_VALUE))
        self._test_content_logger.end_step_logger(5, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """Test Cleanup
        1. Reverting to previous boot order if current boot order is not same as previous boot order
        2. Flashing back current IFWI
        """
        # checking if boot order is equal to previous boot order
        try:
            # self.itp_xml_cli_util = ItpXmlCli(self._log)
            current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
            if str(current_boot_order) != str(self.previous_boot_order):
                current_boot_list = current_boot_order.split("-")
                previous_boot_list = self.previous_boot_order.split("-")
                if previous_boot_list[0] in current_boot_list:
                    current_boot_list.remove(previous_boot_list[0])
                current_boot_list.insert(0,previous_boot_list[0])
                required_boot_order = "-".join(current_boot_list)
                self.itp_xml_cli_util.set_boot_order(required_boot_order)
                self.perform_graceful_g3()
                time.sleep(self.WAIT_TIME)
            # reverting to current IFWI
            current_ifwi_version = self._flash_obj.get_bios_version()
            if current_ifwi_version != self._boot_guard_obj.before_flash_bios_version:
                self._boot_guard_obj.flash_binary_image(self.CURRENT_VERSION)
                current_ifwi_version = self._flash_obj.get_bios_version()
                # check if the current IFWI version flashing is same as earlier, before flashing N-1 version
                if self._boot_guard_obj.before_flash_bios_version == current_ifwi_version:
                    self._log.info(
                        "Current Version IFWI has been successfully reverted with system IFWI version: {}".format(
                            current_ifwi_version))
                else:
                    raise content_exceptions.TestFail("Original IWFI is not restored to continue the execution")
        except Exception as ex:
            raise ex
        super(Tpm2PcrValueCheckPcr0Uefi, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if Tpm2PcrValueCheckPcr0Uefi.main() else Framework.TEST_RESULT_FAIL)
