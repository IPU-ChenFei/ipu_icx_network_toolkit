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
from dtaf_core.providers.ac_power import AcPowerControlProvider
from src.lib import content_exceptions
from src.lib.bios_util import ItpXmlCli, BootOptions
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_common import BootGuardValidator
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot
from src.security.tests.cbnt_boot_guard.cbnt_boot_guard_constants import CBnTConstants
from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_profile5 import BootGuardProfile5


class TPM2PCRvaluecheckGeneralUEFI(TxtBaseTest):
    """
    HPQLM ID : H79542-PI_Security_TPM2.0PCRvaluecheck_PCR4_UEFI

    Verifies the PCR4 value will be changed due to UEFI boot service change.
    """
    PCR_VALUE = 'PCR 04'
    FS0 = 'fs1:'
    TEST_CASE_ID = ["15010764633", "TPM2PCRvaluecheckGeneralUEFI"]
    STEP_DATA_DICT = {1: {'step_details': ' Go to UEFI Internal shell',
                          'expected_results': 'System can boot without any issue.PCRs is dumped'},
                      2: {'step_details': 'Reset the system and boot via Boot manager menu and collect PCR values',
                          'expected_results': 'Booted to UEFI and PCR values collected'},
                      3: {'step_details': 'Boot back to OS and compare the PCR values',
                          'expected_results': 'PCR should is same as expected'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        super(TPM2PCRvaluecheckGeneralUEFI, self).__init__(test_log, arguments, cfg_opts)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self.mount_point = self._copy_usb.get_mount_point(self._common_content_lib, self._common_content_configuration)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider
        self._common_content = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_config = ContentConfiguration(self._log)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(
            si_dbg_cfg, test_log)
        self._cbnt_const = CBnTConstants()
        self._profile5_enable = BootGuardProfile5(test_log, arguments, cfg_opts)
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self.ac_power = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider

    def prepare(self):
        """
         enable Boot Guard Profile 5 on the SUT.
        """
        # super(TPM2PCRvaluecheckGeneralUEFI, self).prepare()

    def regular_match(self, input_res):
        a = []
        for i in input_res:
            if 'TPM PCR' in i:
                a.append(i)
        return a

    def equal(self, list1, list2):
        for a in list1:
            if 'TPM PCR 7' in a:
                list1 = a
                for b in list2:
                    if 'TPM PCR 7' in b:
                        list2 = b
        if not list1 == list2:
            raise content_exceptions.TestFail("pcr 07  Values are not equal")

    def execute(self):
        """
        Execute test case steps(
        :return: True if Test case pass
        """
        self._test_content_logger.start_step_logger(1)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._uefi_util_obj.enter_uefi_shell()
        self._log.info("Wait till the system enter uefi shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        self._uefi_obj.execute(self.FS0)
        self._uefi_obj.execute('ServerPCRDumpTPM2.efi -v > 1.txt')
        output_first_boot = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response('cat 1.txt')
        output_first_boot = self.regular_match(output_first_boot)


        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._uefi_util_obj.enter_uefi_shell()
        self._log.info("Wait till the system enter uefi shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        self._uefi_obj.execute(self.FS0)
        self._uefi_obj.execute('ServerPCRDumpTPM2.efi -v > 2.txt')
        output_second_boot = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response('cat 2.txt')
        output_second_boot = self.regular_match(output_second_boot)

        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._uefi_util_obj.enter_uefi_shell()
        self._log.info("Wait till the system enter uefi shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        self._uefi_obj.execute(self.FS0)
        self._uefi_obj.execute('ServerPCRDumpTPM2.efi -v > 3.txt')
        output_three_boot = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response('cat 3.txt')
        output_three_boot = self.regular_match(output_three_boot)

        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._uefi_util_obj.enter_uefi_shell()
        self._log.info("Wait till the system enter uefi shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        self._uefi_obj.execute(self.FS0)
        self._uefi_obj.execute('ServerPCRDumpTPM2.efi -v > 4.txt')
        output_four_boot = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response('cat 4.txt')
        output_four_boot = self.regular_match(output_four_boot)

        self._test_content_logger.end_step_logger(1, return_val=True)



        self._test_content_logger.start_step_logger(2)
        self._uefi_util_obj.perform_uefi_warm_reset()
        self._uefi_util_obj.enter_uefi_shell()
        self._log.info("Wait till the system enter uefi shell")
        # self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        self._uefi_obj.execute(self.FS0)
        self._uefi_obj.execute('ServerPCRDumpTPM2.efi -v > 5.txt')
        output_five_boot = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response('cat 5.txt')
        output_five_boot = self.regular_match(output_five_boot)

        self._uefi_util_obj.perform_uefi_warm_reset()
        self._uefi_util_obj.enter_uefi_shell()
        self._log.info("Wait till the system enter uefi shell")
        # self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        self._uefi_obj.execute(self.FS0)
        self._uefi_obj.execute('ServerPCRDumpTPM2.efi -v > 6.txt')
        output_six_boot = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response('cat 6.txt')
        output_six_boot = self.regular_match(output_six_boot)

        self._uefi_util_obj.perform_uefi_warm_reset()
        self._uefi_util_obj.enter_uefi_shell()
        self._log.info("Wait till the system enter uefi shell")
        # self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        self._uefi_obj.execute(self.FS0)
        self._uefi_obj.execute('ServerPCRDumpTPM2.efi -v > 7.txt')
        output_seven_boot = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response('cat 7.txt')
        output_seven_boot = self.regular_match(output_seven_boot)

        self._uefi_util_obj.perform_uefi_warm_reset()
        self._uefi_util_obj.enter_uefi_shell()
        self._log.info("Wait till the system enter uefi shell")
        # self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        self._uefi_obj.execute(self.FS0)
        self._uefi_obj.execute('ServerPCRDumpTPM2.efi -v > 8.txt')
        output_eight_boot = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response('cat 8.txt')
        output_eight_boot = self.regular_match(output_eight_boot)
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self.equal(output_first_boot, output_five_boot)
        self.equal(output_second_boot, output_six_boot)
        self.equal(output_three_boot, output_seven_boot)
        self.equal(output_four_boot, output_eight_boot)
        self._test_content_logger.end_step_logger(3, return_val=True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Reverting to previous boot order if current boot order is not same as previous boot order
        """
        # checking if boot order is equal to previous boot order
        super(TPM2PCRvaluecheckGeneralUEFI, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TPM2PCRvaluecheckGeneralUEFI.main() else Framework.TEST_RESULT_FAIL)
