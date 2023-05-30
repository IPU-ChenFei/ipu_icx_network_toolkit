import os
import sys
import threading
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.provider_factory import ProviderFactory

from src.interop.lib.accelerator_library import AcceleratorLibrary
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.hqm.hqm_common import HqmBaseTest
from src.provider.vm_provider import VMs
from src.interop.lib.thread_log_util import ThreadLogUtil
from src.security.tests.qat.qat_common import QatBaseTest
from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.interop.lib.common_library import CommonLibrary


class DlbQatDsaIaxConcurrencyInterruptVm(HqmBaseTest, QatBaseTest):
    NUMBER_OF_VMS = 1
    VM = [VMs.CENTOS] * 1
    BIOS_CONFIG_FILE = "accelerator_config.cfg"
    ACC_DEVICES = ["QAT", "DLB", "DSA", "IAX"]
    ACC_DEVICE_CODE = ["4940", "2710", "0b25", "0cfe"]
    CPA_SAMPLE_CODE = r"./cpa_sample_code"
    GRUB_CMD = "intel_iommu=on,sm_on iommu=on no5lvl --update-kernel=ALL"
    INTEL_IOMMU_ON_STR = "intel_iommu=on,sm_on iommu=on"

    TEST_CASE_ID = ["16014574821-DLB_QAT_DSA_IAX_Concurrency_Interrupt_VM"]

    step_data_dict = {1: {'step_details': 'BIOS Settings as per TC and update grub configs',
                          'expected_results': 'BIOS settings and gurb config setting are updated successfully'},
                      2: {'step_details': 'QAT Installation on Host',
                          'expected_results': 'Installation of QAT on host is successful'},
                      3: {'step_details': 'DLB Installation on Host',
                          'expected_results': 'Installation of DLB on host is successful'},
                      4: {'step_details': 'Configure SIOV QAT,IAX and DSA',
                          'expected_results': 'Configuration of SIOV QAT , IAX and DSA is successful'},
                      5: {'step_details': 'Launch Guest VM',
                          'expected_results': 'Guest VM launched successfully'},
                      6: {'step_details': 'Install QAT,DLB in VM',
                          'expected_results': 'QAT,DLB instalaltion in VM'},
                      7: {
                          'step_details': 'Run QAT workload on Guest VM and check for Interrupts from qat driver in Guest VM.',
                          'expected_results': 'Ran QAT workload on Guest VM and successfully checked for Interrupts from qat driver in Guest VM.'},
                      8: {
                          'step_details': 'Run DLB workload on Guest VM and check for Interrupts from dlb driver in Guest VM.',
                          'expected_results': 'Ran DLB workload on Guest VM and successfully checked for Interrupts from dlb driver in Guest VM.'},
                      9: {
                          'step_details': 'Run DSA workload on Guest VM and check for Interrupts from driver in Guest VM.',
                          'expected_results': 'Ran DSA workload on Guest VM and successfully checked for Interrupts from qat driver in Guest VM.'},
                      10: {
                          'step_details': 'Run IAX workload on Guest VM and check for Interrupts from driver in Guest VM.',
                          'expected_results': 'Ran IAX workload on Guest VM and successfully checked for Interrupts from qat driver in Guest VM.'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        self._log = test_log
        self._cfg = cfg_opts
        self.sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)

        self._os = ProviderFactory.create(self.sut_os_cfg, test_log)  # type: SutOsProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg)
        self.acc_bios_knobs = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                           self.BIOS_CONFIG_FILE)
        super(DlbQatDsaIaxConcurrencyInterruptVm, self).__init__(test_log, arguments, cfg_opts, self.acc_bios_knobs)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._common_lib_acc = CommonLibrary(test_log, self._os, cfg_opts, arguments)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._accelerator_lib = AcceleratorLibrary(self._log, self._os, cfg_opts)
        self._thread_logger = ThreadLogUtil(self._log, self.os, cfg_opts)

        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._run_time = self._common_content_configuration.get_workload_time()
        self.port_num = self._common_content_configuration.get_port_number_for_vm()

        self.dlb_enable_status = self._common_content_configuration.get_dlb_enabled().strip()
        self.qat_enable_status = self._common_content_configuration.get_qat_enabled().strip()
        self.dsa_enable_status = self._common_content_configuration.get_dsa_enabled().strip()
        self.iax_enable_status = self._common_content_configuration.get_iaa_enabled().strip()

    def prepare(self):
        # type: () -> None
        """Test preparation/setup """
        if self.os.os_type == OperatingSystems.LINUX:
            self._log.info("We have Linux OS for test case... proceeding further..")
        else:
            raise content_exceptions.TestFail("This TC is implement for Linux OS")

        self._test_content_logger.start_step_logger(1)
        super(DlbQatDsaIaxConcurrencyInterruptVm, self).prepare()
        self._common_lib_acc.update_kernel_args_and_reboot([self.GRUB_CMD])
        self._test_content_logger.end_step_logger(1, True)

    def execute(self):

        index = 0
        if (self.qat_enable_status.lower() == 'true'):
            self._test_content_logger.start_step_logger(2)
            self._log.info("Installing QAT in Host")
            self.install_qat_tool(configure_spr_cmd='./configure')
            self._test_content_logger.end_step_logger(2, True)

        if (self.dlb_enable_status.lower() == 'true'):
            self._test_content_logger.start_step_logger(3)
            self._log.info("Installing HQM in Host")
            self.install_hqm_driver_libaray()
            self._test_content_logger.end_step_logger(3, True)

        self._test_content_logger.start_step_logger(4)
        self._accelerator_lib.configure_driver_to_enable_siov()
        self._accelerator_lib.configure_dsa()
        self._accelerator_lib.configure_iax()
        self._test_content_logger.end_step_logger(4, True)

        self._test_content_logger.start_step_logger(5)

        if (self.qat_enable_status.lower() == 'true'):
            qat_uuid = self._common_lib_acc.get_qat_uuid()
            qat_device = self._common_lib_acc.device_string.format(qat_uuid)
            self._common_lib_acc.devices_list.append(qat_device)

        if (self.dlb_enable_status.lower() == 'true'):
            hqm_uuid = self._common_lib_acc.get_dlb_uuid()
            hqm_device = self._common_lib_acc.device_string.format(hqm_uuid)
            self._common_lib_acc.devices_list.append(hqm_device)

        if (self.dsa_enable_status.lower() == 'true'):
            dsa_uuid = self._common_lib_acc.get_dsa_uuid()
            dsa_device = self._common_lib_acc.device_string.format(dsa_uuid)
            self._common_lib_acc.devices_list.append(dsa_device)

        if (self.iax_enable_status.lower() == 'true'):
            iax_uuid = self._common_lib_acc.get_iax_uuid()
            iax_device = self._common_lib_acc.device_string.format(iax_uuid)
            self._common_lib_acc.devices_list.append(iax_device)

        vm_name = self.VM[index] + "_" + str(index)
        self._log.info("Updating Grub in VM")
        self._common_lib_acc.update_kernel_args_and_reboot_on_vm(vm_name, [self.GRUB_CMD], self.port_num)
        time.sleep(10)  # For VM to shutdown after kernel agrs update
        self._log.info("Launching VM")
        self._common_lib_acc.create_qemu_vm(vm_name, self.port_num, self._common_lib_acc.devices_list)
        self._test_content_logger.end_step_logger(5, True)

        self._test_content_logger.start_step_logger(6)
        # Install QAT and HQM tools on VM
        if (self.qat_enable_status.lower() == 'true'):
            self._common_lib_acc.install_qat_on_vm(self.port_num,
                                                   configure_spr_cmd='./configure --enable-icp-sriov=guest')
        if (self.dlb_enable_status.lower() == 'true'):
            self._common_lib_acc.install_hqm_driver_on_vm(self.port_num)
        self._test_content_logger.end_step_logger(6, True)

        # Check for QAT
        self._test_content_logger.start_step_logger(7)
        self._common_lib_acc.check_interrupt_from_driver_in_VM(self.port_num, workload='QAT', type_of_check='pre')
        if (self.qat_enable_status.lower() == 'true'):
            self._common_lib_acc.execute_cpa_sample(self.port_num, './cpa_sample_code runTests=1 signOfLife=1',
                                                    self._run_time)
        self._common_lib_acc.check_interrupt_from_driver_in_VM(self.port_num, workload='QAT', type_of_check='post')
        self._test_content_logger.end_step_logger(7, True)


        # Check for DLB
        self._test_content_logger.start_step_logger(8)
        self._common_lib_acc.check_interrupt_from_driver_in_VM(self.port_num, workload='DLB',type_of_check='pre')
        if (self.dlb_enable_status.lower() == 'true'):
            self._common_lib_acc.execute_dlb(self.port_num, self._run_time)
        self._common_lib_acc.check_interrupt_from_driver_in_VM(self.port_num, workload='DLB',type_of_check='post')
        self._test_content_logger.end_step_logger(8, True)

        # Check for DSA
        self._test_content_logger.start_step_logger(9)
        self._common_lib_acc.check_interrupt_from_driver_in_VM(self.port_num, workload='DSA',type_of_check='pre')
        if (self.dsa_enable_status.lower() == 'true'):
            self._common_lib_acc.run_dsa_iax_workload_on_vm("DSA", "-uc", "-o 0x3", self.port_num, self._run_time)
        self._common_lib_acc.check_interrupt_from_driver_in_VM(self.port_num, workload='DSA',type_of_check='post')
        self._test_content_logger.end_step_logger(9, True)

        # Check for IAX
        self._test_content_logger.start_step_logger(10)
        self._common_lib_acc.check_interrupt_from_driver_in_VM(self.port_num, workload='IAX',type_of_check='pre')
        if (self.iax_enable_status.lower() == 'true'):
            self._common_lib_acc.run_dsa_iax_workload_on_vm("IAX", "-uc", "-r", self.port_num, self._run_time)
        self._common_lib_acc.check_interrupt_from_driver_in_VM(self.port_num, workload='IAX',type_of_check='post')
        self._test_content_logger.end_step_logger(10, True)

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        # copy logs to CC folder if provided
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

        super(DlbQatDsaIaxConcurrencyInterruptVm, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if DlbQatDsaIaxConcurrencyInterruptVm.main() else Framework.TEST_RESULT_FAIL)