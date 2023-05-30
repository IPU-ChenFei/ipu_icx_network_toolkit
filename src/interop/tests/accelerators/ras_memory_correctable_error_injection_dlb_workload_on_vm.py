import os
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.provider_factory import ProviderFactory

from src.interop.lib.accelerator_library import AcceleratorLibrary
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.hqm.hqm_common import HqmBaseTest
from src.provider.vm_provider import VMs
from src.security.tests.qat.qat_common import QatBaseTest
from src.lib import content_exceptions                              
from src.lib.common_content_lib import CommonContentLib   
from src.lib.content_configuration import ContentConfiguration    
from src.interop.lib.common_library import CommonLibrary

class RasMemorycorrectableErrorInjectionDlbWorkloadOnVm(HqmBaseTest, QatBaseTest):

    NUMBER_OF_VMS = 1
    VM = [VMs.CENTOS] * 1
    ACC_CONFIG_FILE = "accelerator_config.cfg"
    GRUB_CMD = "intel_iommu=on,sm_on iommu=on no5lvl --update-kernel=ALL"
    ROOT_PATH = r"/root/{}"

    TEST_CASE_ID = ["16013249562-Ras_Memory_correctable_Error_Injection_Dlb_Workload_On_Vm"]

    step_data_dict = {1: {'step_details': 'Make necessary settings in Bios option.',
                          'expected_results': 'BIOS settings Installed successfully'},
                      2: {'step_details': 'Install DLB in VM',
                          'expected_results': 'DLB to be installed successfully in VM'},
                      3: {'step_details': 'Run DLB Workload in VM',
                          'expected_results': 'DLB Workload ran successfully'},
                      4: {'step_details': 'Run fisher in VM with DLB workload to inject errors.',
                          'expected_results': 'The error injection ran successfully for the given workload for the given runtime.'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        self._log = test_log
        self._cfg = cfg_opts
        self.sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        
        self._os = ProviderFactory.create(self.sut_os_cfg, test_log)  # type: SutOsProvider
        
        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg)  
        self.acc_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.ACC_CONFIG_FILE)
        super(RasMemorycorrectableErrorInjectionDlbWorkloadOnVm, self).__init__(test_log, arguments, cfg_opts, self.acc_bios_knobs)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._common_lib_acc = CommonLibrary(test_log, self._os, cfg_opts, arguments)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._accelerator_lib = AcceleratorLibrary(self._log, self._os, cfg_opts)
        self.dlb_enable_status = self._common_content_configuration.get_dlb_enabled().strip()
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._run_time = self._common_content_configuration.get_workload_time()
        self.port_num = self._common_content_configuration.get_port_number_for_vm()
        
        self.devices_list = ['-device intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode="modern",device-iotlb=on,aw-bits=48 '] # Added
        self.device_string = '-device vfio-pci,sysfsdev=/sys/bus/mdev/devices/{}' # Added

    def prepare(self):
        # type: () -> None
        """Test preparation/setup """
        if self._os.os_type == OperatingSystems.LINUX:
            self._log.info("We have Linux OS for test case... proceeding further..")
        else:
            raise content_exceptions.TestFail("This TC is implement for Linux OS")

        self._test_content_logger.start_step_logger(1)
        super(RasMemorycorrectableErrorInjectionDlbWorkloadOnVm, self).prepare()
        self._common_lib_acc.update_kernel_args_and_reboot([self.GRUB_CMD])
        self._test_content_logger.end_step_logger(1, True)

        self._common_lib_acc.execute_ssh_on_vm("rm -rf {}".format(self.ROOT_PATH.format("fisher_*")), "removing fisher output", self.port_num, self._command_timeout)

    def execute(self):

        index = 0

        self._test_content_logger.start_step_logger(2)

        if (self.dlb_enable_status.lower()=='true'):
            self._log.info("Installing HQM in Host")
            self.install_hqm_driver_libaray()

        hqm_uuid = self._common_lib_acc.get_dlb_uuid()

        hqm_device = self.device_string.format(hqm_uuid)

        self.devices_list.append(hqm_device)

        vm_name = self.VM[index] + "_" + str(index)
        self._log.info("Updating Grub in VM")
        self._common_lib_acc.update_kernel_args_and_reboot_on_vm(vm_name, [self.GRUB_CMD], self.port_num)
        time.sleep(10)  # For VM to shutdown after kernel agrs update
        self._log.info("Launching VM")
        self._common_lib_acc.create_qemu_vm(vm_name, self.port_num, self.devices_list)

        #Install HQM tools on VM
        if (self.dlb_enable_status.lower() == 'true'):
            self._common_lib_acc.install_hqm_driver_on_vm(self.port_num)

        self._test_content_logger.end_step_logger(2, True)

        self._log.info("Run DLB Workload in VM")
        self._test_content_logger.start_step_logger(3)
        self._common_lib_acc.execute_dlb(self.port_num, self._run_time)
        self._test_content_logger.end_step_logger(3, True)

        self._log.info("Run fisher in VM with DLB workload to inject errors")
        self._test_content_logger.start_step_logger(4)
        self._common_lib_acc.run_fisher_tool_on_vm(self.port_num, type_of_error="correctable", workload="DLB")
        self._test_content_logger.end_step_logger(4, return_val=True)

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        # copy logs to CC folder if provided
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

        self._common_lib_acc.execute_ssh_on_vm("rm -rf {}".format(self.ROOT_PATH.format("fisher_*")), "removing fisher output", self.port_num, self._command_timeout)

        super(RasMemorycorrectableErrorInjectionDlbWorkloadOnVm, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RasMemorycorrectableErrorInjectionDlbWorkloadOnVm.main() else Framework.TEST_RESULT_FAIL)