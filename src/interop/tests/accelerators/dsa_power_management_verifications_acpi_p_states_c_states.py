import os
import sys

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.provider_factory import ProviderFactory

from src.interop.lib.accelerator_library import AcceleratorLibrary
from src.interop.lib.common_library import CommonLibrary
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.hqm.hqm_common import HqmBaseTest
from src.security.tests.qat.qat_common import QatBaseTest
from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral  


class DsaPowerManagementVerificationsAcpiPstatesCstatesL(HqmBaseTest, QatBaseTest):
    
    ACC_CONFIG_FILE = "../accelerator_config.cfg"

    INTEL_IOMMU_ON_STR = "intel_iommu=on,sm_on iommu=on"

    TEST_CASE_ID = ["16014287180-DSA_Power_Management_Verifications_of_ACPI_P_States_C_States_CentOS"]

    step_data_dict = {1: {'step_details': 'Enable VT-d & C State Control Support in Bios option. Boot to OS',
                          'expected_results': 'BIOS settings Installed successfully'},
                      2: {'step_details': 'Kernel Settings',
                          'expected_results': 'Kernel Settings Installed successfully'},
                      3: {'step_details': 'Clear MCE Logs',
                          'expected_results': 'MCE Logs cleared'},
                      4: {'step_details': 'Install the Socwatch tool',
                          'expected_results': 'Socwatch tool Installed'},
                      5: {'step_details': 'Run the Socwatch tool',
                          'expected_results': 'Socwatch tool successfully ran.'},
                      6: {'step_details': 'Collect the logs and check for PC6 Residency value',
                          'expected_results': 'PC6 Residency value more than 98 %'},
                      7: {'step_details': 'Download and build accel-config tool. Download DSA/IAX random config scripts, Configure all DSA devices with user type work-queues and run DSA test',
                          'expected_results': 'accel-config tool built successful. DSA Test executed succesfully'},
                      8: {'step_details': 'Run the Socwatch tool',
                          'expected_results': 'Socwatch tool successfully ran.'},
                      9: {'step_details': 'Collect the logs and check for PC6 Residency value',
                          'expected_results': 'PC6 Residency value more than 98 %'},
                      10: {'step_details': 'Check whether MCE occured or not.',
                          'expected_results': 'There are no MCE errors or dmesg log errors.'},
                      11: {'step_details': 'C state with DSA workload Interrupt',
                          'expected_results': './Setup_Randomize_DSA_Conf.sh stopped proccessing successfully.'},
                      12: {'step_details': 'Run the Socwatch tool',
                          'expected_results': 'Socwatch tool successfully ran.'},
                      13: {'step_details': 'Collect the logs and check for PC6 Residency value',
                          'expected_results': 'PC6 Residency value more than 98 %'},
                      14: {'step_details': 'Check whether MCE occured or not.',
                          'expected_results': 'There are no MCE errors or dmesg log errors.'},
                          }

    def __init__(self, test_log, arguments, cfg_opts):
        self._log = test_log
        self._cfg = cfg_opts
        self.sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self.os = ProviderFactory.create(self.sut_os_cfg, test_log)  # type: SutOsProvider
        self._common_content_lib = CommonContentLib(self._log, self.os, self._cfg)  
        self.acc_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.ACC_CONFIG_FILE)
        super(DsaPowerManagementVerificationsAcpiPstatesCstatesL, self).__init__(test_log, arguments, cfg_opts,
                                                                              self.acc_bios_knobs)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self.install_collateral_obj = InstallCollateral(self._log, self.os, cfg_opts)
        self._accelerator_lib = AcceleratorLibrary(self._log, self.os, cfg_opts)
        self._library = CommonLibrary(self._log, self.os, cfg_opts)

        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestFail("This test is Supported only on Linux")

    def prepare(self):
        # type: () -> None

        self._log.info('Set BIOS knobs')
        self._test_content_logger.start_step_logger(1)
        super(DsaPowerManagementVerificationsAcpiPstatesCstatesL, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._log.info('Set Kernel Settings')
        self._test_content_logger.start_step_logger(2)
        self._library.update_kernel_args_and_reboot([self.INTEL_IOMMU_ON_STR])
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):

        self._test_content_logger.start_step_logger(3)
        self._accelerator_lib.check_mce_log()
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self.install_collateral_obj.install_socwatch()
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        cmd= "x86_energy_perf_policy -all balance-performance"
        self._common_content_lib.execute_sut_cmd(cmd, cmd,self._command_timeout, "/root/")
        self._accelerator_lib.run_socwatch_tool_on_host()
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        self._accelerator_lib.check_c6_residency_value_on_host(cc6_value=95, pc6_value=75)
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        # Place holder for copying accel-random scripts to SUT
        self._accelerator_lib.dsa_workload_on_host()
        self._test_content_logger.end_step_logger(7, return_val=True)

        self._test_content_logger.start_step_logger(8)
        self._accelerator_lib.run_socwatch_tool_on_host()
        self._test_content_logger.end_step_logger(8, return_val=True)

        self._test_content_logger.start_step_logger(9)
        self._accelerator_lib.check_c6_residency_value_on_host(cc6_value=95, pc6_value=75)
        self._test_content_logger.end_step_logger(9, return_val=True)

        self._test_content_logger.start_step_logger(10)
        self._accelerator_lib.check_mce_on_host()
        self._test_content_logger.end_step_logger(10, return_val=True)

        self._test_content_logger.start_step_logger(11)
        self._accelerator_lib.run_workload_with_interrupt_on_host(workload='DSA')
        self._test_content_logger.end_step_logger(11, return_val=True)

        self._test_content_logger.start_step_logger(12)
        self._accelerator_lib.run_socwatch_tool_on_host()
        self._test_content_logger.end_step_logger(12, return_val=True)

        self._test_content_logger.start_step_logger(13)
        self._accelerator_lib.check_c6_residency_value_on_host(cc6_value=95, pc6_value=75)
        self._test_content_logger.end_step_logger(13, return_val=True)

        self._test_content_logger.start_step_logger(14)
        self._accelerator_lib.check_mce_on_host()
        self._test_content_logger.end_step_logger(14, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if DsaPowerManagementVerificationsAcpiPstatesCstatesL.main() else Framework.TEST_RESULT_FAIL)