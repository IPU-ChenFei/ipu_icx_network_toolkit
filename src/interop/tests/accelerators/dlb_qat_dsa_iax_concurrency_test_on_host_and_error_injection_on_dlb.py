import os
import sys
import threading

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.lib.dtaf_constants import Framework
from src.interop.lib.error_injection import InjectErrors
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.content_configuration import ContentConfiguration
from src.interop.lib.accelerator_library import AcceleratorLibrary
from src.interop.lib.common_library import CommonLibrary
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib.common_content_lib import CommonContentLib


class ErrorInjectionOnDlb(ContentBaseTestCase):
    BIOS_CONFIG_FILE = "../accelerator_config.cfg"

    INTEL_IOMMU_ON_STR = "intel_iommu=on,sm_on iommu=on"

    TEST_CASE_ID = ["16014644458-DLB+QAT+DSA+IAX Concurrency test on HOST and Error Injection on DLB"]

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
                      6: {'step_details': 'Run 4 Accelerators workloads Concurrently for an hour and inject DLB error',
                          'expected_results': 'Ran 4 Accelerators workloads Concurrently for an hour successfully and injected DLB error'}

                      }

    def __init__(self, test_log, arguments, cfg_opts):
        self.acc_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(ErrorInjectionOnDlb, self).__init__(test_log, arguments, cfg_opts, self.acc_bios_knobs)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._accelerator_lib = AcceleratorLibrary(self._log, self.os, cfg_opts)  # ..
        self._library = CommonLibrary(self._log, self.os, cfg_opts)  # ..
        self._common_content_lib = CommonContentLib(self._log, self.os, self._cfg)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider
        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._log.info('Initializing cscripts from here.............')
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._run_time = self._common_content_configuration.get_workload_time()
        self._error_injection = InjectErrors(self._log, self._os, cfg_opts, self._sdp, self._cscripts, self._run_time, self._reboot_timeout)

    def prepare(self):
        # type: () -> None

        self._test_content_logger.start_step_logger(1)
        super(ErrorInjectionOnDlb, self).prepare()
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._test_content_logger.start_step_logger(2)
        self._library.update_kernel_args_and_reboot([self.INTEL_IOMMU_ON_STR])
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        # Step logger start for Step 1

        self._log.info("QAT Installation")
        self._test_content_logger.start_step_logger(3)
        self._install_collateral.install_qat(configure_spr_cmd='./configure --enable-icp-sriov=host')
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._log.info("DLB Installation")
        self._test_content_logger.start_step_logger(4)
        self._install_collateral.install_hqm_driver()
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        # Place holder for copying accel-random scripts to SUT
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)

        qat_workload_thread = threading.Thread(target=self._accelerator_lib.run_qat_workload_on_host)
        dlb_workload_thread = threading.Thread(target=self._accelerator_lib.run_dpdk_workload_on_host)
        dsa_workload_thread = threading.Thread(target=self._accelerator_lib.dsa_workload_on_host)
        iax_workload_thread = threading.Thread(target=self._accelerator_lib.iax_workload_on_host)
        dlb_error_injection = threading.Thread(target=self._error_injection.inject_ce_errors, args=("DLB",))

        qat_workload_thread.start()
        dlb_workload_thread.start()
        dsa_workload_thread.start()
        iax_workload_thread.start()
        dlb_error_injection.start()

        qat_workload_thread.join()
        dlb_workload_thread.join()
        dsa_workload_thread.join()
        iax_workload_thread.join()
        dlb_error_injection.join()

        self._test_content_logger.end_step_logger(6, return_val=True)

        # self._error_injection.inject_ce_errors("DLB")
        return True


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if ErrorInjectionOnDlb.main() else Framework.TEST_RESULT_FAIL)
