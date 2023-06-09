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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.bios_util import BootOptions
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_common import BootGuardValidator
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.provider.host_usb_drive_provider import HostUsbDriveProvider
from dtaf_core.providers.physical_control import PhysicalControlProvider
from src.lib.dtaf_content_constants import UefiTool
from src.lib.bios_util import ItpXmlCli
from src.lib.dtaf_content_constants import TimeConstants
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

class TPMPCRvaluecheckPCR0W(TxtBaseTest):
    """
    Verifies the PCR4 value will be changed due to UEFI boot service change.
    """
    PCR_VALUE = 'PCR 00'
    TEST_CASE_ID = ["15010764633", "TPMPCRvaluecheckPCR0W"]
    STEP_DATA_DICT = {1: {'step_details': 'Copies ServerPCRDumpTPM2.efi to USB',
                          'expected_results': 'ServerPCRDumpTPM2.efi copied successfully to USB'},
                      2: {'step_details': 'Flash a N-1 version BIOS capsule. Enable TPM and reboot to EFI shell and collect PCR values',
                          'expected_results': 'Booted to UEFI and PCR values collected'},
                      3: {'step_details': 'Boot back to OS and compare the PCR values',
                          'expected_results': 'PCR should is different as expected'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of TPMPCRvaluecheckPCR0W.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(TPMPCRvaluecheckPCR0W, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._host_usb_provider = HostUsbDriveProvider.factory(test_log, cfg_opts, self._os)
        phy_cfg = cfg_opts.find(PhysicalControlProvider.DEFAULT_CONFIG_PATH)
        self._flash = BootGuardValidator(test_log, arguments, cfg_opts)
        self._phy = ProviderFactory.create(phy_cfg, test_log)  # type: PhysicalControlProvider
        self.IFWI_IMAGE = "IFWI Previous Version"
        self.IFWI_IMAGE_CURRENT = "IFWI Current Version"

    def prepare(self):
        # type: () -> None
        """
        Copy pcrdump64.zip to USB drive and change the Boot order to UEFI shell.
        """
        self._test_content_logger.start_step_logger(1)
        super(TPMPCRvaluecheckPCR0W, self).prepare()
        # copying the zip .efi from collateral to usb
        self.copy_file_from_collateral_to_usb(self._phy, UefiTool.PCR_TOOL_DIR, self._host_usb_provider)
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This method collect the initial PCR values and boot again to uefi
        Flash a N-1 version BIOS capsule. Enable TPM and reboot and collect PCR values. Boot back to OS and Compare PCR Dump values
        generated by pcrdump64 before and after

        :raise: Test fail exception if SUT failed to boot in UEFI shell
        :raise: content Exception if PCR values are same
        :return: True
        """
        self._test_content_logger.start_step_logger(2)
        self._flash.flash_binary_image(self.IFWI_IMAGE_CURRENT)
        self._uefi_util_obj.perform_uefi_warm_reset()
        self._log.info("Waiting for UEFI shell")
        if not self._uefi_util_obj.enter_uefi_shell():
            raise RuntimeError("SUT did not enter to UEFI Internal Shell")
        output_first_boot = self.get_pcrdump_from_uefi(
            pcr_dump_cmd=self._EXECUTE_PCRDUMP_64, pcr_dump_dir=UefiTool.PCR_TOOL_DIR)
        self._log.debug("PCR dump via boot order change to UEFI is: {}".format(output_first_boot))
        pcr_values_first_boot = self.pcrdump64_data_formatting(output_first_boot)
        print("***********************************************")
        print(pcr_values_first_boot)
        print("***********************************************")

        self._flash.flash_binary_image(self.IFWI_IMAGE)
        self._uefi_util_obj.perform_uefi_warm_reset()
        self._log.info("Waiting for UEFI shell")
        if not self._uefi_util_obj.enter_uefi_shell():
            raise RuntimeError("SUT did not enter to UEFI Internal Shell")
        output_second_boot = self.get_pcrdump_from_uefi(
            pcr_dump_cmd=self._EXECUTE_PCRDUMP_64, pcr_dump_dir=UefiTool.PCR_TOOL_DIR)
        self._log.debug("PCR dump values via Boot manager to UEFI is: {}".format(output_second_boot))
        pcr_values_second_boot = self.pcrdump64_data_formatting(output_second_boot)
        print("***********************************************")
        print(pcr_values_second_boot)
        print("***********************************************")
        # pcr_values_second_boot = self.pcrdump64_data_formatting(output_second_boot)
        time.sleep(TimeConstants.ONE_MIN_IN_SEC)
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._test_content_logger.start_step_logger(3)
        self.perform_graceful_g3()
        if self.verify_pcr_values_equal(output_first_boot, output_second_boot, self.PCR_VALUE):
            raise content_exceptions.TestFail("Pcr value {} for first boot and second boot is same".format(
                self.PCR_VALUE))
        self._log.info("Pcr value {} for first and second boot is different as expected".format(self.PCR_VALUE))
        self._test_content_logger.end_step_logger(3, return_val=True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Reverting to previous boot order if current boot order is not same as previous boot order
        """
        # checking if boot order is equal to previous boot order
        super(TPMPCRvaluecheckPCR0W, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TPMPCRvaluecheckPCR0W.main() else Framework.TEST_RESULT_FAIL)
