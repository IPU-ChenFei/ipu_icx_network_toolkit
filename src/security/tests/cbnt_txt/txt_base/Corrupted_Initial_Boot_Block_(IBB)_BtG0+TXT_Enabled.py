import os
import re
import sys

from dtaf_core.lib.configuration import ConfigurationHelper
from dtaf_core.lib.dtaf_constants import Framework, ProductFamilies
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.uefi_shell import UefiShellProvider
from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.content_configuration import ContentConfiguration
from src.lib.flash_util import FlashUtil
from src.lib.test_content_logger import TestContentLogger
from src.lib.uefi_util import UefiUtil
from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_common import BootGuardValidator
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.security.tests.cbnt_txt.txt_base.Golden_PCR0_hash_BtG0T import GoldenPCR0hash


class CorruptedInitialBootBlock(TxtBaseTest):
    TEST_CASE_ID = ['22012311834', 'Corrupted Initial Boot Block (IBB): BtG0 + TXT Enabled']
    STEP_DATA_DICT = {
        1: {'step_details': 'Golden PCR0 Hash: BtG0 + TXT Enabled ', 'expected_results': ''},
        2: {'step_details': 'Change profile0.bin Change byte 00 --> F3', 'expected_results': ''},
        3: {'step_details': 'Flash BIOS image,decode the value of the register .Shell> mem 0xfed30328 4,',
            'expected_results': 'The expected errror code should be:0xC0039910 or '
                                '"FED30328: 10 99 03 C0" as printed by the UEFI shell'},
        4: {'step_details': 'Shell> mem 0xfed300a0', 'expected_results':'Bits 30 and 63 should be 0.'},
        5: {'step_details': 'From the UEFI shell, again use ServerPcrDumpTpm2 and redirect output to a new logfile.',
            'expected_results': 'PCR0 measurements from first and second IFWIs do not match.'},
        6: {'step_details': 'Allow the platform to boot to the operating system. '
                            ' From the CLI, issue the command ''txt-stat | less''.',
            'expected_results': 'TXT measured launch: FALSE'},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        self.pcr0 = GoldenPCR0hash(test_log, arguments, cfg_opts)
        self._log = test_log
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        uefi_cfg = cfg_opts.find(UefiShellProvider.DEFAULT_CONFIG_PATH)
        self._uefi_obj = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider
        bios_boot_menu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self._bios_boot_menu_obj = ProviderFactory.create(bios_boot_menu_cfg, test_log)  # type: BiosBootMenuProvider
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_obj = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider
        self._common_content_configuration = ContentConfiguration(self._log)
        self.boot_guard = BootGuardValidator(self._log, arguments, cfg_opts)
        self.sut = ConfigurationHelper.get_sut_config(cfg_opts)
        banino_flash_cfg = ConfigurationHelper.filter_provider_config(sut=self.sut,
                                                                      provider_name=r"flash",
                                                                      attrib=dict(id="2"))
        banino_flash_cfg = banino_flash_cfg[0]
        self._flash = ProviderFactory.create(banino_flash_cfg, test_log)  # type: FlashProvider
        self._flash_obj = FlashUtil(self._log, self._os, self._flash, self._common_content_lib,
                                    self._common_content_configuration)  # type: FlashUtil
        self._uefi_util_obj = UefiUtil(
            self._log,
            self._uefi_obj,
            self._bios_boot_menu_obj,
            self._ac_obj,
            self._common_content_configuration, self._os)
        super(CorruptedInitialBootBlock, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(
            si_dbg_cfg, test_log)  # type: SiliconDebugProvider

    def prepare(self):
        self._test_content_logger.start_step_logger(1)
        self.pcr0.prepare()
        self.pcr0.execute()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def pcr0_value(self, target_list):
        list_str = ''.join([str(elem.replace("\r", "")) for elem in target_list])
        pcr = re.findall(f'(?<=TPM PCR 0:)(.*?)(?=TPM PCR 1:)', list_str, re.DOTALL)
        return pcr[0]

    def execute(self):
        self._test_content_logger.start_step_logger(2)
        first_tpm_value = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self._EXECUTE_SERVERPCRDUMP_TPM2)
        first_pcr0_value = self.pcr0_value(first_tpm_value)
        self._log.info(first_pcr0_value)
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        ifwi_btg_image = "C:\IFWI_Image\P01.bin"
        self._flash_obj.flash_ifwi_image(ifwi_btg_image)

        self._os.execute('efibootmgr -n 0001', self._command_timeout)
        self._os.execute('reboot', self._command_timeout)
        # self._uefi_util_obj.enter_uefi_shell()
        # self._log.info("Wait till the system enter uefi shell")
        # self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        mem_res = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response('mem 0xfed30328 4')
        self._log.info(mem_res)
        print(mem_res)
        if '0xC0039910' or 'FED30328: 10 99 03 C0' not in mem_res:
            raise content_exceptions.TestFail('expected error code do not match')
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        mem_res = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response('mem 0xfed300a0')
        self._log.info(mem_res)
        print(mem_res)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        second_tpm_value = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self._EXECUTE_SERVERPCRDUMP_TPM2)
        second_pcr0_vaule = self.pcr0_value(second_tpm_value)
        if first_pcr0_value == second_pcr0_vaule:
            raise content_exceptions.TestFail('PCR0 measurements from first and second IFWIs same')

        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        txt_stat = self._common_content_lib.execute_sut_cmd('txt-stat | less', 'txt-stat reports',
                                                            self._command_timeout)
        self._log.info(txt_stat)
        print(txt_stat)
        if 'TXT measured launch: FALSE' not in txt_stat:
            raise content_exceptions.TestFail('The platform is able to boot to the OS and the environment is trusted')
        self._test_content_logger.end_step_logger(6, return_val=True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(CorruptedInitialBootBlock, self).cleanup(return_status)


if __name__ == '__main__':
    sys.exit(Framework.TEST_RESULT_PASS if CorruptedInitialBootBlock.main() else Framework.TEST_RESULT_FAIL)
