from argparse import Namespace
from typing import Union, List
import xml.etree.ElementTree as ET
import sys

from src.lib import content_exceptions
from sgx_error_injection import SgxErrorInjectionBaseTest
from dtaf_core.lib.os_lib import OsCommandResult
from dtaf_core.lib.dtaf_constants import Framework

class CorrectableErrorOutsidePrmrr(SgxErrorInjectionBaseTest):
    TEST_CASE_ID: List[str] = ["22012589003", "Correctable single-bit error injection outside of PRMRR region with SGX enabled and SGX traffic running"]
    INJ_ADDR_OFFSET: int = 32*1024*1204

    def __init__(self, test_log: str, arguments: Union[Namespace, None], cfg_opts: ET.ElementTree):
        super(CorrectableErrorOutsidePrmrr, self).__init__(test_log, arguments, cfg_opts)

    def execute(self) -> bool:
        self.run_semt(timeout=None)

        wtchdog_cmd: str = "echo 60 > /proc/sys/kernel/watchdog_thresh"
        self._log.info("Setting watchdog threshold to 60")
        cmd_output: OsCommandResult = self.os.execute(cmd=wtchdog_cmd, timeout=60)

        if cmd_output.cmd_failed():
            raise content_exceptions.TestFail("{} failed with exit code {}".format(wtchdog_cmd, cmd_output.return_code))

        try:
            ec = self.srp.get_err_injection_obj()
        except Exception as e:
            content_exceptions.TestFail("Failed to get error injection object with: {}".format(e))

        inj_addr: int = self.sgx_phys_addr - self.INJ_ADDR_OFFSET

        self._log.info("Injecting error into 0x{}".format(hex(inj_addr)))
        try:
            (ret_code, _, _, _, _, _) = ec.consume_ecc(inj_addr,  inj_addr, dev0=0x1, dev1=0x2, dev0xormask=0x2, dev1xormask = 0x0, verbose=1)
            if ret_code != ec.mu._NO_ERROR:
                content_exceptions.TestFail("Memory injection failed with {}".format(ec.mu.errorDict[ret_code]))
        except Exception as e:
            content_exceptions.TestFail("Failed to injection memory error with {}".format(e))

        if not self.correctable_error_check():
            raise content_exceptions.TestFail("Something was missing from the serial logs")

        return True

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CorrectableErrorOutsidePrmrr.main() else
             Framework.TEST_RESULT_FAIL)

