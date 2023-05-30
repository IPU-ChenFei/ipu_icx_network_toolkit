import os
import sys
import threading
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.interop.lib.accelerator_library import AcceleratorLibrary
from src.interop.lib.common_library import CommonLibrary
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.hqm.hqm_common import HqmBaseTest
from src.security.tests.qat.qat_common import QatBaseTest
from src.lib import content_exceptions

from src.lib.common_content_lib import CommonContentLib
from threading import Thread


class QatDlbDsaIaaConcurrencyTestOnHostPtuMlcFioIperf(HqmBaseTest, QatBaseTest):
    BIOS_CONFIG_FILE = "../accelerator_config.cfg"
    INTEL_IOMMU_ON_STR = "intel_iommu=on,sm_on iommu=on"
    PTU_SUT_FOLDER_NAME = "ptu"
    PTU_INSTALLER_NAME = "unified_server_ptu.tar.gz"
    TEST_CASE_ID = ["16014303008-DLB+QAT+DSA+IAX Concurrency test on HOST+PTU+MLC+FIO+IPERF"]

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
                      6: {'step_details': 'PTU Driver',
                          'expected_results': 'PTU driver Installed successfully'},
                      7: {'step_details': 'MLC Driver',
                          'expected_results': 'MLC driver Installed successfully'},
                      8: {'step_details': 'FIO Driver',
                          'expected_results': 'FIO driver Installed successfully'},
                      9: {'step_details': 'IPERF Driver',
                          'expected_results': 'IPERF driver Installed successfully'},
                      10: {'step_details': 'Run 8 Accelerators workloads Concurrently for an hour',
                           'expected_results': 'Ran 8 Accelerators workloads Concurrently for an hour successfully'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        self.acc_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(QatDlbDsaIaaConcurrencyTestOnHostPtuMlcFioIperf, self).__init__(test_log, arguments, cfg_opts,
                                                                              self.acc_bios_knobs)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._accelerator_lib = AcceleratorLibrary(self._log, self.os, cfg_opts)  # ..
        self._library = CommonLibrary(self._log, self.os, cfg_opts)
        # self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestFail("This test is Supported only on Linux")

    def prepare(self):
        # type: () -> None
        self._test_content_logger.start_step_logger(1)
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        super(QatDlbDsaIaaConcurrencyTestOnHostPtuMlcFioIperf, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self._library.update_kernel_args_and_reboot([self.INTEL_IOMMU_ON_STR])
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        self._log.info("QAT Installation  .................................. ")
        self._test_content_logger.start_step_logger(3)
        self.install_qat_tool(configure_spr_cmd='./configure --enable-icp-sriov=host')
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._log.info("DLB Installation .................................. ")
        self._test_content_logger.start_step_logger(4)
        self.install_hqm_driver_libaray()
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._log.info("PTU Installation .................................. ")
        self._test_content_logger.start_step_logger(6)
        self._install_collateral.install_ptu(self.PTU_SUT_FOLDER_NAME, self.PTU_INSTALLER_NAME)
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._log.info("MLC Installation .................................. ")
        self._test_content_logger.start_step_logger(7)
        self._install_collateral.install_mlc()
        self._test_content_logger.end_step_logger(7, return_val=True)

        self._log.info("FIO Installation .................................. ")
        self._test_content_logger.start_step_logger(8)
        self._install_collateral.install_fio()
        self._test_content_logger.end_step_logger(8, return_val=True)

        self._log.info("IPERF Installation .................................. ")
        self._test_content_logger.start_step_logger(9)
        self._install_collateral.install_iperf_on_vm()
        self._test_content_logger.end_step_logger(9, return_val=True)

        self._test_content_logger.start_step_logger(10)
        self._log.info(" Workloads .................................. ")

        qat_workload_thread = threading.Thread(target=self._accelerator_lib.run_qat_workload_on_host)
        dlb_workload_thread = threading.Thread(target=self._accelerator_lib.run_dpdk_workload_on_host)
        dsa_workload_thread = threading.Thread(target=self._accelerator_lib.dsa_workload_on_host)
        iax_workload_thread = threading.Thread(target=self._accelerator_lib.iax_workload_on_host)

        ptu_workload_thread = threading.Thread(target=self._library.run_ptu_workload_on_host)
        mlc_workload_thread = threading.Thread(target=self._library.run_mlc_workload_on_host)
        fio_workload_thread = threading.Thread(target=self._library.run_fio_workload_on_host)

        qat_workload_thread.start()
        dlb_workload_thread.start()
        dsa_workload_thread.start()
        iax_workload_thread.start()
        ptu_workload_thread.start()
        mlc_workload_thread.start()
        fio_workload_thread.start()

        qat_workload_thread.join()
        dlb_workload_thread.join()
        dsa_workload_thread.join()
        iax_workload_thread.join()

        mlc_workload_thread.join()
        fio_workload_thread.join()
        ptu_workload_thread.join()

        self._test_content_logger.end_step_logger(10, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if QatDlbDsaIaaConcurrencyTestOnHostPtuMlcFioIperf.main() else Framework.TEST_RESULT_FAIL)
