from argparse import Namespace
from typing import Union, List
import xml.etree.ElementTree as ET
import sys

from src.lib import content_exceptions
from sgx_error_injection import SgxErrorInjectionBaseTest
from dtaf_core.lib.dtaf_constants import Framework

class UCErrorEpcMetadata(SgxErrorInjectionBaseTest):
    TEST_CASE_ID: List[str] = ["18014073462", "Uncorrectable single-bit error injection in EPC memory holding application code/data"]

    def __init__(self, test_log: str, arguments: Union[Namespace, None], cfg_opts: ET.ElementTree):
        super(UCErrorEpcMetadata, self).__init__(test_log, arguments, cfg_opts)

    def execute(self) -> bool:
        self.run_semt(timeout=None)

        self.unlock_injectors()

        self._log.info("Injecting error to address 0x{}".format(hex(self.sgx_phys_addr+32*1024*1024)))
        self.uncorrectable_error(phys_addr=self.sgx_phys_addr+32*1024*1024)

        try:
            self.uncorrectable_error_verify()
        except:
            raise content_exceptions.TestFail("Failed to verify memory injection")

        if not self.uncorrectable_error_check():
            raise content_exceptions.TestFail("Could not find indication of Uncorrectable Errors in the log. Log path {}".format(self.serial_log_path))

        return True

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UCErrorEpcMetadata.main() else
             Framework.TEST_RESULT_FAIL)
