import os
import sys

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.provider_factory import ProviderFactory

from src.interop.lib.accelerator_library import AcceleratorLibrary
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.hqm.hqm_common import HqmBaseTest
from src.security.tests.qat.qat_common import QatBaseTest
from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib


class RasMemoryUncorrectableNonFatalErrorInjectionQatWorkload(HqmBaseTest, QatBaseTest):
    
    ACC_CONFIG_FILE = "../accelerator_config.cfg"
    WHEA_CONFIG_FILE = "../whea_error_injection_config.cfg"

    TEST_CASE_ID = ["16013046290-RAS_Memory_Uncorrectable_Non_Fatal_Error_Injection_with_QAT_Workload"]

    step_data_dict = {1: {'step_details': 'Boot the SUT, enable the WHEA Error Injection Support in Bios option & disable VT-d',
                          'expected_results': 'BIOS settings Installed successfully'},
                      2: {'step_details': 'QAT driver Installation',
                          'expected_results': 'QAT driver Installation successful'},
                      3: {'step_details': 'Run fisher tool for injecting Memory Uncorrectable non-fatal error with QAT workload.',
                          'expected_results': 'The error injection ran successfully for the given workload for the given cycles.'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        self._log = test_log
        self._cfg = cfg_opts
        self.sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self.os = ProviderFactory.create(self.sut_os_cfg, test_log)  # type: SutOsProvider
        self._common_content_lib = CommonContentLib(self._log, self.os, self._cfg)  
        self.acc_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.ACC_CONFIG_FILE)
        self.whea_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.WHEA_CONFIG_FILE)
        self.BIOS_CONFIG_FILE = self._common_content_lib.get_combine_config([self.acc_bios_knobs,self.whea_bios_knobs])
        
        super(RasMemoryUncorrectableNonFatalErrorInjectionQatWorkload, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._accelerator_lib = AcceleratorLibrary(self._log, self.os, cfg_opts)  
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestFail("This test is Supported only on Linux")

    def prepare(self):
        # type: () -> None
        
        self._log.info('Set BIOS knobs')
        self._test_content_logger.start_step_logger(1)
        super(RasMemoryUncorrectableNonFatalErrorInjectionQatWorkload, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):

        # Step logger start for Step 2
        self._log.info("QAT driver Installation")
        self._test_content_logger.start_step_logger(2)
        self.install_qat_tool(configure_spr_cmd='./configure --enable-icp-sriov=host')
        self._accelerator_lib.run_qat_workload_on_host()
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3 
        self._log.info("Run fisher tool for injecting Memory Uncorrectable non-fatal error with QAT workload for a single cycle.")
        self._test_content_logger.start_step_logger(3)
        self._accelerator_lib.run_fisher_tool_on_host(type_of_error="uncorrectable", workload = "QAT")
        self._test_content_logger.end_step_logger(3, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if RasMemoryUncorrectableNonFatalErrorInjectionQatWorkload.main() else Framework.TEST_RESULT_FAIL)