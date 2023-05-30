from argparse import Namespace
from typing import Union, List
import xml.etree.ElementTree as ET
import sys

from src.lib import content_exceptions
from sgx_error_injection import SgxErrorInjectionBaseTest
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.os_lib import OsCommandResult

class CorrectableErrorEpcMetadata(SgxErrorInjectionBaseTest):
    TEST_CASE_ID: List[str] = ["18014073424", "Correctable single-bit error injection in EPC memory holding application code/data"]

    def __init__(self, test_log: str, arguments: Union[Namespace, None], cfg_opts: ET.ElementTree):
        super(CorrectableErrorEpcMetadata, self).__init__(test_log, arguments, cfg_opts)

    def execute(self) -> bool:
        self.unlock_injectors()

        self.run_semt(timeout=None)

        self._log.info("Injecting error to address 0x{}".format(hex(self.sgx_phys_addr+32*1024*1024)))
        self.correctable_error(phys_addr=self.sgx_phys_addr+32*1024*1024)

        try:
            self.correctable_error_verify()
        except:
            raise content_exceptions.TestFail("Failed to verify memory injection")

        try:
            semt_chk: OsCommandResult = self.os.execute("pgrep semt", timeout=60)
            if semt_chk.cmd_failed():
                raise content_exceptions.TestFail("semt app is no longer running")
            else:
                self._log.info("semt is still running")
        except Exception as e:
            raise content_exceptions.TestFail("Failed to check if semt is still running: {}".format(e))

        if not self.correctable_error_check():
            raise content_exceptions.TestFail("Something was missing from the serial logs")

        return True

    def cleanup(self, return_status) -> None:
        try:
            self.os.execute("pkill semt", timeout=self._command_timeout)
        except:
            # if the app isn't running, that's fine too
            pass
        return super().cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CorrectableErrorEpcMetadata.main() else
             Framework.TEST_RESULT_FAIL)