import os
import re
import sys

from dtaf_core.lib.dtaf_constants import Framework, ProductFamilies
from src.lib import content_exceptions
from src.security.tests.cbnt_txt.txt_base.Golden_PCR0_hash_BtG0T import GoldenPCR0hash
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest


class CorruptedInitialBootBlock(TxtBaseTest):
    TEST_CASE_ID = ['22012311834', 'Corrupted Initial Boot Block (IBB): BtG0 + TXT Enabled']
    STEP_DATA_DICT = {
        1: {'step_details': 'Golden PCR0 Hash: BtG0 + TXT Enabled ', 'expected_results': ''},
        2: {'step_details': 'Change profile0.bin Change byte 00 --> F3', 'expected_results': ''},
        3: {'step_details': 'Flash BIOS image,decode the value of the register .Shell> mem 0xfed30328 4,',
            'expected_results': 'The expected errror code should be:0xC0039910 or '
                                '"FED30328: 10 99 03 C0" as printed by the UEFI shell'},
        4: {'step_details': 'Shell> mem 0xfed300a0', 'expected_results':'Bits 30 and 63 should be 0.'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        super(CorruptedInitialBootBlock, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self.pcr0 = GoldenPCR0hash(test_log, arguments, cfg_opts)

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
        ifwi_btg_image = "C:\IFWI_Image\P02.bin"
        self._flash_obj.flash_ifwi_image(ifwi_btg_image)

        self._uefi_util_obj.enter_uefi_shell()
        self._log.info("Wait till the system enter uefi shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        first_mem_value = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response('mem 0xfed30328')
        self._log.info(first_mem_value)
        if '0xC002A110' not in first_mem_value:
            self._log.info("Value of 0xfed30328 should report 0xC002A110 ")

        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        second_tpm_value = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self._EXECUTE_SERVERPCRDUMP_TPM2)
        second_pcr0_vaule = self.pcr0_value(second_tpm_value)
        if first_pcr0_value == second_pcr0_vaule:
            raise content_exceptions.TestFail('PCR0 measurements from first and second IFWIs same')
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        txt_stat = self._common_content_lib.execute_sut_cmd('txt-stat | less', 'txt-stat reports',
                                                            self._command_timeout)
        print(txt_stat)
        if 'TXT measured launch: FALSE' not in txt_stat:
            raise content_exceptions.TestFail('The platform is able to boot to the OS and the environment is trusted')
        self._test_content_logger.end_step_logger(4, return_val=True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(CorruptedInitialBootBlock, self).cleanup(return_status)


if __name__ == '__main__':
    sys.exit(Framework.TEST_RESULT_PASS if CorruptedInitialBootBlock.main() else Framework.TEST_RESULT_FAIL)
