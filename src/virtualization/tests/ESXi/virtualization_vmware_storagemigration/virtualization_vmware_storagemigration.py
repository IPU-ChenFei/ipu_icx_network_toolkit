import os
import sys
import time
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from pathlib import Path
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.provider.mlc_provider import MlcProvider
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger


class virtualizationstoragemigration(VirtualizationCommon):
    """
       Phoenix ID: 18014073440
       Ensures that VMware's live storage migration feature functions w/o any issues or having to turn off the VM.
       1. Create a virtual machine and do some ping test
       2. Create new datastore using any disk given in the config file
       3. A Migrate Virtual Machine to a new datastore
       4. Chek if the Virtual machine is up and running
       """

    VM = [VMs.RHEL]
    VM_TYPE = "RHEL"
    DATASTORE_NAME = "datastore_new"

    TEST_CASE_ID = ["P18014073440", "virtualizationstoragemigration"]
    STEP_DATA_DICT = {
        1: {'step_details': "Create a virtual machine and do some ping test ",
            'expected_results': "Should be successfull"},
        2: {'step_details': " Create new datastore using any disk given in the config file",
            'expected_results': "Creation of datastore should be successful"},
        3: {'step_details': "A Migrate Virtual Machine to a new datastore.",
            'expected_results': "Migration Should be successfull"},
        4: {'step_details': "Check if the Virtual machine is up and running",
            'expected_results': "Should be successfull"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new virtualizationstoragemigration object.
        """
        super(virtualizationstoragemigration, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)


    def prepare(self):
        # Need to implement bios configuration for ESXi SUT
        self._test_content_logger.start_step_logger(1)
        if self.os.os_type != OperatingSystems.ESXI:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._log.info("VMWare ESXi SUT detected for the testcase")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. Create a virtual machine and do some ping test
        2. Create new datastore using any disk given in the config file
        3. A Migrate Virtual Machine to a new datastore
        4. Check if the Virtual machine is up and running
        """
        self._test_content_logger.start_step_logger(1)
        vm_sut_obj_list =[]
        for index in range(len(self.VM)):
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_vmware_vm(vm_name, self.VM_TYPE, mac_addr=True, use_powercli="use_powercli")
            self._test_content_logger.end_step_logger(2, return_val=True)
            self._vm_provider.install_vmware_tool_on_vm(vm_name)
            vm_os_obj = self.create_esxi_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            self._test_content_logger.end_step_logger(1, return_val=True)
            disk_name_esxi = self._common_content_configuration.get_disk_esxi()
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self._test_content_logger.start_step_logger(2)
            get_powerstate = "vim-cmd  vmsvc/power.getstate {}"
            vm_id = self.get_vm_id_esxi(vm_name)
            output = self._common_content_lib.execute_sut_cmd(get_powerstate.format(vm_id),
                                                              "Get powerstate of VM", self._command_timeout)
            if "Powered on" in output:
                self._log.info("VM is up and running".format(vm_name))
            else:
                raise RuntimeError("VM not up and running ")
            self._test_content_logger.end_step_logger(2, return_val=True)
            self._test_content_logger.start_step_logger(3)
            self.create_datastore(self.DATASTORE_NAME,disk_name_esxi)
            self._test_content_logger.end_step_logger(3, return_val=True)
            self._test_content_logger.start_step_logger(4)
            self.migrate_vm_to_new_datastore(vm_name,self.DATASTORE_NAME)
            self._test_content_logger.end_step_logger(4, return_val=True)
            self.get_datastore_of_vm(vm_name,self.DATASTORE_NAME)
            time.sleep(40)
            get_all_vms = "vim-cmd vmsvc/getallvms |grep {}"
            output_all_vms = self._common_content_lib.execute_sut_cmd(get_all_vms.format(vm_name),
                                                              "Get list of VM", self._command_timeout)
            vm_id_after_migration = self.get_vm_id_esxi(vm_name)
            get_powerstate = "vim-cmd  vmsvc/power.getstate {}"
            output = self._common_content_lib.execute_sut_cmd(get_powerstate.format(vm_id_after_migration),
                                                              "Get powerstate of VM", self._command_timeout)
            print(output_all_vms)
            print(output)
            if "Powered on" in output:
                self._log.info("VM is up and running".format(vm_name))
            else:
                raise RuntimeError("VM not up and running ")

            return True

    def cleanup(self, return_status):
        super(virtualizationstoragemigration, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if virtualizationstoragemigration.main()
             else Framework.TEST_RESULT_FAIL)