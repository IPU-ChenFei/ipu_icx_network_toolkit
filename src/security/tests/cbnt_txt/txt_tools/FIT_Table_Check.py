import os
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot
from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_profile5 import BootGuardProfile5


class FITTableCheck(TxtBaseTest):

    TEST_CASE_ID = ['FIT Table Check (Legacy TXT + Legacy BtG)']
    SUT_CMD = "python /root/val_tools/SIV/NonProjectSpecific/TestContent/LogAcmLinux_BtG.py --Fit_Record_Type Acm_Header"
    LOG_PATH = "/root/val_tools/SIV/NonProjectSpecific/TestContent/Fit_Table.log"
    STEP_DATA_DICT = {
        1: {'step_details': ' enable Boot Guard Profile 5 on the SUT.Enable TXT', 'expected_results': 'Test Passed'},
        2: {'step_details': 'Execute python CMD', 'expected_results': 'Successfully located the Fit Record'},
        3: {'step_details': ' Check that Fit_Table.log ',
            'expected_results': 'All types should have a non-zero/FF entry in the FIT table.'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        super(FITTableCheck, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._trusted_boot = TrustedBootWithTboot(test_log, arguments, cfg_opts)
        self._profile5_enable = BootGuardProfile5(test_log, arguments, cfg_opts)

    def prepare(self):

        super(FITTableCheck, self).prepare()

    def execute(self):
        self._test_content_logger.start_step_logger(1)
        # self._os.execute(self.FSCK_CMD.format(self.mount_point), self._command_timeout)
        self._profile5_enable.prepare()
        self._profile5_enable.execute()
        self._trusted_boot.prepare()
        self._trusted_boot.execute()
        if not self._trusted_boot.verify_trusted_boot():  # verify the sut boot with trusted env
            raise content_exceptions.TestFail("SUT did not boot to Trusted environment")
        self._log.info("SUT Booted to Trusted environment Successfully")
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._test_content_logger.start_step_logger(2)
        self._common_content_lib.execute_sut_cmd(self.SUT_CMD, "execute python file",self._command_timeout)
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._test_content_logger.start_step_logger(3)
        abs_file_path = os.path.join(self.LOG_PATH)
        with open(abs_file_path, 'r',) as fs:
            log_lines = fs.readlines()
            log_lines = [log_lines[index].split() for index in range(1, len(log_lines))]
            flag0 = 0
            flag1 = 0
            flag2 = 0
            for log_line in log_lines:
                if "02" in log_line:
                    flag0 = 1
                if "0b" in log_line:
                    flag1 = 1
                if "0c" in log_line:
                    flag1 = 1
            if not flag0 and flag1 and flag2:
                raise content_exceptions.TestFail("Check that Fit_Table.log fail")
        self._test_content_logger.end_step_logger(3, return_val=True)


    def cleanup(self, return_status):
        super(FITTableCheck, self).cleanup(return_status)


if __name__ == '__main__':
    sys.exit(Framework.TEST_RESULT_PASS if FITTableCheck.main() else Framework.TEST_RESULT_FAIL)
