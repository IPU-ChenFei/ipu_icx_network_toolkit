import os
import sys
import threading

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.interop.lib.accelerator_library import AcceleratorLibrary
from src.interop.lib.common_library import CommonLibrary
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.hqm.hqm_common import HqmBaseTest
from src.security.tests.qat.qat_common import QatBaseTest
from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.interop.lib.thread_log_util import ThreadLogUtil


class QatDlbDsaIaaConcurrencyTestOnHost(HqmBaseTest, QatBaseTest):
    BIOS_CONFIG_FILE = "../accelerator_config.cfg"

    INTEL_IOMMU_ON_STR = "intel_iommu=on,sm_on iommu=on"

    TEST_CASE_ID = ["16014303008-DLB+QAT+DSA+IAX Concurrency test on HOST"]

    step_data_dict = {1: {'step_details': 'BIOS Settings',
                          'expected_results': 'BIOS settings Installed successfully'},
                      2: {'step_details': 'Kernel Settings',
                          'expected_results': 'Kernel Settings Installed successfully'},
                      3: {'step_details': 'QAT Driver Installation',
                          'expected_results': 'QAT Driver  Installed successfully'},
                      4: {'step_details': 'DLB driver Installation, DPDK Installation',
                          'expected_results': 'DLB driver Installation, DPDK Installation successful'},
                      5: {'step_details': 'Accel Config',
                          'expected_results': 'Accel config install successful'},
                      6: {'step_details': 'Run 4 Accelerators workloads Concurrently for an hour',
                          'expected_results': 'Ran 4 Accelerators workloads Concurrently for an hour successfully'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        self.acc_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(QatDlbDsaIaaConcurrencyTestOnHost, self).__init__(test_log, arguments, cfg_opts, self.acc_bios_knobs)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._accelerator_lib = AcceleratorLibrary(self._log, self.os, cfg_opts)  # ..
        self._library = CommonLibrary(self._log, self.os, cfg_opts) # ..
        self._common_content_lib = CommonContentLib(self._log, self.os, self._cfg)
        self._thread_logger = ThreadLogUtil(self._log, self.os, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestFail("This test is Supported only on Linux")

    def prepare(self):
        # type: () -> None

        self._test_content_logger.start_step_logger(1)
        super(QatDlbDsaIaaConcurrencyTestOnHost, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self._library.update_kernel_args_and_reboot([self.INTEL_IOMMU_ON_STR])
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        # Step logger start for Step 1

        self._log.info("QAT Installation")
        self._test_content_logger.start_step_logger(3)
        self.install_qat_tool(configure_spr_cmd='./configure --enable-icp-sriov=host')
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._log.info("DLB Installation")
        self._test_content_logger.start_step_logger(4)
        self.install_hqm_driver_libaray()
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        # Place holder for copying accel-random scripts to SUT
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)

        qat_workload_thread = threading.Thread(target=self._accelerator_lib.run_qat_workload_on_host)
        dlb_workload_thread = threading.Thread(target=self._accelerator_lib.run_dpdk_workload_on_host)
        dsa_workload_thread = threading.Thread(target=self._accelerator_lib.dsa_workload_on_host)
        iax_workload_thread = threading.Thread(target=self._accelerator_lib.iax_workload_on_host)

        qat_th_log_handler = self._thread_logger.thread_logger(qat_workload_thread)
        qat_workload_thread.start()
        dlb_th_log_handler = self._thread_logger.thread_logger(dlb_workload_thread)
        dlb_workload_thread.start()
        dsa_th_log_handler = self._thread_logger.thread_logger(dsa_workload_thread)
        dsa_workload_thread.start()
        iax_th_log_handler = self._thread_logger.thread_logger(iax_workload_thread)
        iax_workload_thread.start()

        qat_workload_thread.join()
        dlb_workload_thread.join()
        dsa_workload_thread.join()
        iax_workload_thread.join()
        self._thread_logger.stop_thread_logging(qat_th_log_handler)
        self._thread_logger.stop_thread_logging(dlb_th_log_handler)
        self._thread_logger.stop_thread_logging(dsa_th_log_handler)
        self._thread_logger.stop_thread_logging(iax_th_log_handler)

        error_str_list = self._common_content_configuration.get_accelerator_error_strings()
        self._thread_logger.verify_workload_logs(error_str_list)

        self._test_content_logger.end_step_logger(6, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if QatDlbDsaIaaConcurrencyTestOnHost.main() else Framework.TEST_RESULT_FAIL)