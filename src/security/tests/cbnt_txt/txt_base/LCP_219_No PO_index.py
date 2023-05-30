import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.security.tests.cbnt_txt.txt_base.LCP201 import LCP201


class LCP219(TxtBaseTest):
    ENTER = 'FS1:'
    COMMAND01 = 'Tpm2ProvTool.efi StartSession EmptyAuthPwSession.sDef 1'
    COMMAND02 = 'Tpm2ProvTool.efi NvUndefineSpace ExamplePO_Sha256.iDef 1'
    COMMAND03 = 'TxtBtgInfo.efi -c t > po-index-erase-check.txt'
    TEST_CASE_ID = ['22013488919', 'LCP 219 - No PO index, LCP OS data']
    READ_RESULT = 'cat po-index-erase-check.txt'
    STEP_DATA_DICT = {
        1: {'step_details': 'Follow lcp201 except for the last step. ', 'expected_results': ''},
        2: {'step_details': 'Remove the PO index by running the following commands Tpm2ProvTool.efi StartSession '
                            'EmptyAuthPwSession.sDef 1   Tpm2ProvTool.efi NvUndefineSpace ExamplePO_Sha256.iDef 1',
            'expected_results': ''},
        3: {'step_details': 'Verify that the PO index is now empty.', 'expected_results': 'PO index is empty'},
        4: {'step_details': 'Boot to TBOOT + Linux', 'expected_results':
            'SUT should fail to boot to the OS.  If the SUT boots to the OS successfully, fail the test.'},
        5: {'step_details': 'Gather failure data', 'expected_results': ''},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        super(LCP219, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self.lcp201 = LCP201(test_log, arguments, cfg_opts)
        self._trusted_boot_with_tboot = TrustedBootWithTboot(test_log, arguments, cfg_opts)

    def prepare(self):
        # super(LCP219, self).prepare()
        self._test_content_logger.start_step_logger(1)
        self.lcp201.prepare()
        self.lcp201.execute()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        self._test_content_logger.start_step_logger(2)
        # self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._uefi_util_obj.enter_uefi_shell()
        self._log.info("Wait till the system enter uefi shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)

        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.ENTER)
        # self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.COMMAND01)
        # self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.COMMAND02)
        self.clear_po_index_tpm2(['FS0:', 'FS1:'])
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        read_return_value = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.READ_RESULT)
        serialize_result = iter(read_return_value)
        for i in serialize_result:
            if 'Index not present' not in i:
                raise content_exceptions.TestFail('PO index is not empty.')
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        # self._trusted_boot_with_tboot.prepare()
        # self._trusted_boot_with_tboot.execute()
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        if self._os.is_alive():
            raise content_exceptions.TestFail("os is alive")
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        self._uefi_util_obj.enter_uefi_shell()
        self._log.info("Wait till the system enter uefi shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        error_code = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response('mem 0xfed30030 4')
        if 'FED30030: 11 34 00 c0' not in error_code:
            raise content_exceptions.TestFail('conditions are not met')
        self._test_content_logger.end_step_logger(5, return_val=True)
        return True

    def cleanup(self, return_status):
        """
        Reverting to previous boot order if current boot order is not same as previous boot order
        """
        super(LCP219, self).cleanup(return_status)


if __name__ == '__main__':
    sys.exit(Framework.TEST_RESULT_PASS if LCP219.main() else Framework.TEST_RESULT_FAIL)
