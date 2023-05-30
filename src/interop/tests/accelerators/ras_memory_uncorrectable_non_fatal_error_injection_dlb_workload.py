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
from src.lib.install_collateral import InstallCollateral    
from src.security.tests.tdx.interop.ras.fisher.fisher_base_test import TdxRasFisherBaseTest

class RasMemoryUncorrectableNonFatalErrorInjectionDlbWorkload(HqmBaseTest, QatBaseTest):

    ACC_CONFIG_FILE = "../accelerator_config.cfg"
    WHEA_CONFIG_FILE = "../whea_error_injection_config.cfg"

    TEST_CASE_ID = ["16013044342-Ras_Memory_Uncorrectable_Non_Fatal_Error_Injection_Dlb_Workload"]

    step_data_dict = {1: {'step_details': 'Boot the SUT and enable the WHEA Error Injection Support in Bios option.',
                          'expected_results': 'BIOS settings Installed successfully'},
                      2: {'step_details': 'DLB driver Installation, DPDK Installation',
                          'expected_results': 'DLB driver Installation, DPDK Installation successful'},
                      3: {'step_details': 'Run DPDK test app',
                          'expected_results': 'DPDK Workload ran successfully'},
                      4: {'step_details': 'Run fisher tool for injecting Memory uncorrectable non fatal error with DLB workload.',
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

        super(RasMemoryUncorrectableNonFatalErrorInjectionDlbWorkload, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self.install_collateral_obj = InstallCollateral(self._log, self.os, cfg_opts)
        self._accelerator_lib = AcceleratorLibrary(self._log, self.os, cfg_opts)
        self._tdx_ras_fisher_base_test = TdxRasFisherBaseTest(test_log, arguments, cfg_opts)

        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestFail("This test is Supported only on Linux")

    def prepare(self):
        # type: () -> None

        self._test_content_logger.start_step_logger(1)
        super(RasMemoryUncorrectableNonFatalErrorInjectionDlbWorkload, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):

        self._log.info("DLB driver Installation, DPDK Installation")
        self._test_content_logger.start_step_logger(2)
        self.install_hqm_driver_libaray()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._log.info("Run DPDK test app")
        self._test_content_logger.start_step_logger(3)
        self._accelerator_lib.run_dpdk_workload_on_host()
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._log.info("Run fisher tool")
        self._test_content_logger.start_step_logger(4)
        self._accelerator_lib.run_fisher_tool_on_host(type_of_error="uncorrectable", workload="DLB")
        self._test_content_logger.end_step_logger(4, return_val=True)

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        # copy logs to CC folder if provided
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

        super(RasMemoryUncorrectableNonFatalErrorInjectionDlbWorkload, self).cleanup(return_status)



if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RasMemoryUncorrectableNonFatalErrorInjectionDlbWorkload.main() else Framework.TEST_RESULT_FAIL)