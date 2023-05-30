import os
import sys
import threading
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.lib.dtaf_constants import Framework
from src.interop.lib.error_injection import InjectErrors
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.content_configuration import ContentConfiguration
from src.interop.lib.accelerator_library import AcceleratorLibrary
from src.interop.lib.common_library import CommonLibrary
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib.common_content_lib import CommonContentLib


class UncorrectableFatalErrorOnDlbDevices(ContentBaseTestCase):
    BIOS_CONFIG_FILE = "../accelerator_config.cfg"

    INTEL_IOMMU_ON_STR = "intel_iommu=on,sm_on iommu=on"

    TEST_CASE_ID = ["16013360819-RAS PCIe DLB Uncorrectable Fatal Error Injection for all DLB devices"]

    step_data_dict = {
        1: {'step_details': 'DLB driver Installation, DPDK Installation',
            'expected_results': 'DLB driver Installation, DPDK Installation successful'},

        2: {'step_details': 'Inject uncorrectable error into all DLB devices.',
            'expected_results': 'Injected uncorrectable error into all DLB devices.'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        self.acc_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(UncorrectableFatalErrorOnDlbDevices, self).__init__(test_log, arguments, cfg_opts, self.acc_bios_knobs)
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

    def execute(self):
        self._log.info("DLB Installation")
        self._test_content_logger.start_step_logger(1)
        self._install_collateral.install_hqm_driver()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self._error_injection.inject_uce_errors("DLB")
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if UncorrectableFatalErrorOnDlbDevices.main() else Framework.TEST_RESULT_FAIL)
