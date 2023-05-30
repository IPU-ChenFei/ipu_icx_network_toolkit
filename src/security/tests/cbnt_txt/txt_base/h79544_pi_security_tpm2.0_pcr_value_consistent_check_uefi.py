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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib import content_exceptions
from src.lib.bios_util import BootOptions, ItpXmlCli
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest


class Tpm2PcrValueConsistentCheckUefi(TxtBaseTest):
    """
    HPALM ID : H79544-PI_Security_TPM2.0 PCR value consistent check_UEFI
    When a system performs trusted boot, BIOS performs measurements at various stages and stores them in PCR 0-7
    (Platform config registers) in TPM. The PCR 0-7 values need to be consistent on each system from boot to boot.
     The values also need to be consistent on identically configured systems. If there is any change in the
     measurement, then it may indicate a malware attack. This is the premise in which trusted boot operates.
    """

    TEST_CASE_ID = ["H79544","PI_Security_TPM2.0_PCR_value_consistent_check_UEFI"]
    NO_OF_REBOOT = 4
    STEP_DATA_DICT = {1: {'step_details': 'Copy pcrdump64.efi files to usb',
                          'expected_results': 'pcrdump64.efi files are copied successfully'},
                      2: {'step_details': 'Navigate to UEFI shell and execute pcrdump64.efi and reset and reboot '
                                          'to UEFI shell ',
                          'expected_results': 'Output of the pcr dump64 collected successfully'},
                      3: {'step_details': 'Navigate to UEFI shell and execute pcrdump64.efi and reset -s and shutdown '
                                          'and wakeup to UEFI shell ',
                          'expected_results': 'Output of the pcr dump64 collected successfully'},
                      4: {'step_details': 'Boot to OS and compare result of reset and reset -s pcrdump64 output for '
                                          'PCR0-7 ',
                          'expected_results': 'Output of pcrdump64.efi for reset and reset -s matched successfully'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of Tpm2PcrValueConsistentCheckUefi.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(Tpm2PcrValueConsistentCheckUefi, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.previous_boot_order = None
        self.current_boot_order = None
        self._csp = ProviderFactory.create(self._csp_cfg, test_log)
        self.itp_xml_cli_util = ItpXmlCli(test_log, self._cfg)

    def prepare(self):
        # type: () -> None
        """
        Copy pcrdump64.zip to SUT and then to USB drive
        """
        super(Tpm2PcrValueConsistentCheckUefi, self).prepare()
        self._test_content_logger.start_step_logger(1)
        # copying the zip .efi from host to usb
        self.copy_file(self._PCR_DUMP_64_ZIP_FILE)
        self._test_content_logger.end_step_logger(1, return_val=True)
        self.previous_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Previous boot order {}".format(self.previous_boot_order))

    def compare_pcr_after_reset_shutdown(self, after_reset, after_shutdown):
        """
        This methods compares dictionary of pcr values of after reset and after shutdown
         and returns error dictionary of all unmatched pcr values

        :param: after_reset pcr value
        :param: after_shutdown value
        :return: error dictionary of unmatched all pcr value
        """
        self._log.info("Comparing PCR dump after reset and after shutdown")
        error_dict = {}

        for keys in after_reset.keys():
            if after_reset[keys] != after_shutdown[keys]:
                self._log.debug("The PCR values after reset:{} and after shutdown:{} are different for {}"
                                .format(after_reset[keys], after_shutdown[keys], keys))
                error_dict["after_reset_{}".format(keys)] = after_reset[keys]
                error_dict["after_shutdown_{}".format(keys)] = after_shutdown[keys]
            else:
                self._log.debug("The PCR values after reset:{} and after shutdown:{} are same for {}"
                                .format(after_reset[keys], after_shutdown[keys], keys))
        error_list = list(error_dict.items())

        return error_list

    def execute(self):
        """
        Compare PCR Dump values executing pcr dump64 in each cycle of reset and shutdown of the system
        1. Set the boot order to UEFI shell and reset the system and boot to uefi shell
        2. reset and boot to uefi shell and execute pcrdump64.efi
        3. reset -s and shutdown the system. And wakeup in UEFI shell and execute pcrdump64.efi
        4. Boot to OS and compare the PCR 0-7 value collected from after reset and shutdown the system

        :raise: TestFail if PCR 0-7 values does match each other after reset and shutdown for each reboot cycle
        :return: True, if PCR 0-7 values matched
        """
        dict_pcr_reset = {}
        dict_pcr_shutdown = {}
        err_status = []
        error_dict = {}
        pcr_dump_folder = ''
        for key, value in self._PCR_DUMP_64_ZIP_FILE.items():
            pcr_dump_folder = key

        self._test_content_logger.start_step_logger(2)
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._log.info("waiting for UEFI shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)

        for reboot in range(1, self.NO_OF_REBOOT + 1):
            self._uefi_util_obj.perform_uefi_warm_reset()
            self._log.info("waiting for UEFI shell")
            self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
            self._log.info("Executing command {}".format(self._EXECUTE_PCRDUMP_64))
            dict_pcr_reset["reboot{}".format(reboot)] = self.get_pcrdump_from_uefi(
                pcr_dump_cmd=self._EXECUTE_PCRDUMP_64, pcr_dump_dir=pcr_dump_folder)
        self._log.debug("PCR values after reset: {}".format(dict_pcr_reset))
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        for reboot in range(1, self.NO_OF_REBOOT + 1):
            self._log.info("System shutting down")
            self._uefi_obj.shutdown()
            self._common_content_configuration.sut_shutdown_delay()
            self._uefi_util_obj.graceful_sut_ac_power_on()
            self._log.info("waiting for uefi shell")
            self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
            self._log.info("Executing command {}".format(self._EXECUTE_PCRDUMP_64))
            dict_pcr_shutdown["reboot{}".format(reboot)] = self.get_pcrdump_from_uefi(
                pcr_dump_cmd=self._EXECUTE_PCRDUMP_64, pcr_dump_dir=pcr_dump_folder)
        self._log.debug("PCR values after shutdown: {}".format(dict_pcr_shutdown))
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self.itp_xml_cli_util.set_boot_order(self.previous_boot_order)
        self.perform_graceful_g3()

        for reboot in range(1, self.NO_OF_REBOOT + 1):
            pcr_reset = self.pcrdump64_data_formatting(dict_pcr_reset["reboot{}".format(reboot)])
            pcr_shutdown = self.pcrdump64_data_formatting(dict_pcr_shutdown["reboot{}".format(reboot)])
            err_list = self.compare_pcr_after_reset_shutdown(pcr_reset, pcr_shutdown)
            if err_list:
                err_status.append(False)
            else:
                err_status.append(True)
            error_dict["reboot{}".format(reboot)] = err_list

        if not all(err_status):
            raise content_exceptions.TestFail("PCR value did not match for {}".format(error_dict))
        self._test_content_logger.end_step_logger(4, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        if str(self.current_boot_order) != str(self.previous_boot_order):
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_order)
            self.perform_graceful_g3()
        super(Tpm2PcrValueConsistentCheckUefi, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if Tpm2PcrValueConsistentCheckUefi.main() else Framework.TEST_RESULT_FAIL)
