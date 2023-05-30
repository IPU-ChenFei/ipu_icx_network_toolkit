import os
import sys
import time
import glob

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_profile0 import BootGuardProfile0
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot



class GoldenPCR0hash(TxtBaseTest):

    FS0 = 'fs1:'
    TEST_CASE_ID = ['Golden PCR0 hash: BtG0T + TXT Enabled']
    STEP_DATA_DICT = {
        1: {'step_details': ' For Boot_Profileset the value to "0x0" to enable BootGuard profile 0.',
            'expected_results': 'Test Passed1'},
        2: {'step_details': 'Platform is able to boot into a trusted environment with BtG0 enabled.',
            'expected_results': 'Test Passed2'},
        3: {'step_details': ' Check the logfile and inspect the currently read value for PCR0. ',
            'expected_results': 'Test Passed3'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        super(GoldenPCR0hash, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._trusted_boot = TrustedBootWithTboot(test_log, arguments, cfg_opts)
        self._profile0_enable = BootGuardProfile0(test_log, arguments, cfg_opts)

    def prepare(self):

        self._test_content_logger.start_step_logger(1)
        super(GoldenPCR0hash, self).prepare()

    def regular_match(self, input_res):
        for i in iter(input_res):
            if 'TPM PCR 0:' in i:
                print(next(i))


    def execute(self):

        self._profile0_enable.prepare()
        self._profile0_enable.execute()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self._trusted_boot.prepare()
        self._trusted_boot.execute()
        if not self._trusted_boot.verify_trusted_boot():  # verify the sut boot with trusted env
            raise content_exceptions.TestFail("SUT did not boot to Trusted environment")
        self._log.info("SUT Booted to Trusted environment Successfully")
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        LOG_PATH = glob.glob(r'C:\Automation\dtaf_logs\BootGuardProfile0_*\serial_logs\serial_log.log')
        # abs_file_path = os.path.join(self.LOG_PATH[1])
        with open(LOG_PATH[1], 'r',) as fs:
            log_lines = fs.readlines()
            log_lines = [log_lines[index].split() for index in range(1, len(log_lines))]
            flag0 = 0
            flag1 = 0
            for log_line in log_lines:
                if "MSR_BOOT_GUARD_SACM_INFO" in log_line:
                    flag0 = 1
                if "BootGuardAcmError[0xFED30328]" in log_line:
                    flag1 = 1
            if not flag0 and flag1:
                raise content_exceptions.TestFail("Check that Fit_Table.log fail")

        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._uefi_util_obj.enter_uefi_shell()
        self._log.info("Wait till the system enter uefi shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        self._uefi_obj.execute(self.FS0)
        self._uefi_obj.execute('ServerPCRDumpTPM2.efi -v > 1.txt')
        output_boot = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response('cat 1.txt')
        self.regular_match(output_boot)
        self._test_content_logger.end_step_logger(3, return_val=True)



    def cleanup(self, return_status):

        super(GoldenPCR0hash, self).cleanup(return_status)


if __name__ == '__main__':
    sys.exit(Framework.TEST_RESULT_PASS if GoldenPCR0hash.main() else Framework.TEST_RESULT_FAIL)
