#!/usr/bin/env python
#################################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and proprietary
# and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#################################################################################

import sys
import os
import threading
import time
from shutil import copy

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.virtualization.virtualization_common import VirtualizationCommon
from src.provider.vm_provider import VMs
from src.lib.common_content_lib import CommonContentLib
from src.lib.test_content_logger import TestContentLogger

from src.lib.dtaf_content_constants import TimeConstants, DynamoToolConstants, IOmeterToolConstants
from src.lib.install_collateral import InstallCollateral
from src.provider.storage_provider import StorageProvider

from src.lib import content_exceptions
from src.provider.stressapp_provider import StressAppTestProvider

class VirtualizationRhelNWAndNVMeTOStress(VirtualizationCommon):
    """
    Phoenix ID : 16014085032-VirtualizationRhelNWAndNVMeTOStress
    This class is to Test the SUT and VM is stable or not after the stress loading using fio, dynamo, burnin and iometer.

        Drive stress IO on all the drives for one hour:
        1. Prepare a Windows OS host and install IOMeter tool, connect it LAN as target Linux SUT;
        2. Copy Dynamo tool into Linux target SUT and run ./dyname -i host_IP_address -m target_IP_address;
        3. On Windows Host system, run 'iometer -t xxx' under cmd shell (xxx is time number);
        4. Run FIO and IO meter workload test on host on two different NVMe Storage
        5. Run stress network load e.g. ping/iperf/burn-in workloads
        6. Run SUT snf VM with stress load for min 4 hours
        7. Check after execution of stress loading tools if system is stable along with VM and responding

    """
    TEST_CASE_ID = ["P1601408532", "VirtualizationRhelNWAndNVMeTOStress"]
    STEP_DATA_DICT = {
        1: {'step_details': "Set and Verify bios knobs settings.",
            'expected_results': "BIOS knobs set as per knobs file and verified."},
        2: {'step_details': "Create the name of All VMs to be created",
            'expected_results': "VM names created successfully"},
        3: {'step_details': "Create the VM with VM name",
             'expected_results': "VM created and verified"},
        4: {'step_details': "Yum repo creation and tools installation started",
            'expected_results': "Yum repo and dependencies installed on VM successfully"},
        5: {'step_details': "Burnin Tool installation started on VM",
            'expected_results': "Burnin Tool installation completed on VM"},
        6: {'step_details': "Execute the ping flooding at SUT.",
            'expected_results': "Ping flood test on SUT started"},
        7: {'step_details': "Execute the ping flooding on VM",
            'expected_results': "Ping flood test on VM started successfully"},
        8: {'step_details': "Install fio tool on SUT",
            'expected_results': "Fio Tool installed successfully on SUT"},
        9: {'step_details': "Start fio tool execution on SUT",
            'expected_results': "Fio tool started successfully on SUT"},
        10: {'step_details': "Execute the dynamo tool on SUT...",
            'expected_results': "Dynamo tool started on SUT..."},
        11: {'step_details': "Attach VF PCIe device to VM",
             'expected_results': "Virtual function adapter attached to VM"},
        12: {'step_details': "Verify the attached VFs in VMs",
             'expected_results': "Virtual function verified in VM"},
        13: {'step_details': "Get the VF adpater device name in VM",
             'expected_results': "Virtual function adapter name in VM obtained successfully"},
        14: {'step_details': "Assign Static IP to VF in VM",
             'expected_results': "Static IP assigned to VF adpater of VM"},
        15: {'step_details': "Copy config file for IOmeter tool and configure it on host",
             'expected_results': "IOMeter tool configured on host"},
        16: {'step_details': "Execute the IOMeter Tool on the Host machine",
             'expected_results': "IOMeter Tools started successfully on the host"},
        17: {'step_details': "Install Burnin Test on SUT",
             'expected_results': "Burnin test tools installed on SUT successfully"},
        18: {'step_details': "Execute Burnin Test on SUT",
             'expected_results': "Burnin test execution completed successfully on SUT"},
        19: {'step_details': "Wait for all threads to join and kill all tool execution threads",
             'expected_results': "All waiting threads joined and removed successfully"},
        20: {'step_details': "Verify the SUT and VM if both are running and stable",
             'expected_results': "SUT and VMs are running fine"},
    }
    BIOS_CONFIG_FILE = "virtualization_rhel_host_network_and_nvme_storage_io_stress.cfg"
    NUMBER_OF_VMS = 1
    VM = [VMs.RHEL] * 1
    LIST_OF_VM_NAMES = []
    VM_TYPE = "RHEL"
    IPERF_EXEC_TIME = 120 #14400 #30
    TEST_TIMEOUT = 5 #120  # 5 in minutes
    BURNING_80_WORKLOAD_CONFIG_FILE = "cmdline_config_80_workload.txt"
    BIT_TIMEOUT = 5 #120  # 5 in minutes
    SUT_BIT_LOCATION = None
    REPOS_FOLDER_PATH_SUT = "/etc/yum.repos.d"
    VM_NAME = None
    bit_location = None
    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new object for VirtualizationRhelNWAndNVMeTOStress

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VirtualizationRhelNWAndNVMeTOStress, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("This Test Case is Only Supported on Linux")
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self._storage_provider = StorageProvider.factory(self._log, self.os, cfg_opts)  # type: StorageProvider
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self.stress_app_provider = StressAppTestProvider.factory(self._log, os_obj=self.os, cfg_opts=cfg_opts)
        self._cfg_opt = cfg_opts

        self.sut_ip = self.get_ip(self._common_content_lib)
        self.vm_ip = None


    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.
        6. Uninstalling xterm

        :return: None
        """
        # Check the for the Windows OS in the SUT
        if self.os.os_type == OperatingSystems.LINUX:
            self._log.info("We have Linux OS for test case... proceeding further..")
        else:
            raise content_exceptions.TestFail("Target is not booted with Linux")

        self._test_content_logger.start_step_logger(1)
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        self._test_content_logger.end_step_logger(1, True)
        super(VirtualizationRhelNWAndNVMeTOStress, self).prepare()

    def execute(self):
        """"
        This method installs different stress tools, fio, burnin, dynamo, ping/iperf and iometer
        tool, execute for min 4 hours and validate the resulting log out put

        Checks whether SUT and VM both are stable the stress load test.

        :return: True or False
        :raise: if non zero errors raise content_exceptions.TestFail
        """
        self.collateral_installer.screen_package_installation()
        self._test_content_logger.start_step_logger(2)
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" Creating VM:{} on RHEL.".format(vm_name))
        self._test_content_logger.end_step_logger(2, True)

        install_collateral_vm_obj = None
        common_content_lib_vm_obj = None
        for vm_name in self.LIST_OF_VM_NAMES:
            # create with default values
            # reconfig with max capacity of disk and ram
            self._test_content_logger.start_step_logger(3)
            self._vm_provider.destroy_vm(vm_name)
            self.create_vm(vm_name, self.VM_TYPE, mac_addr=True)
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            vm_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            self._test_content_logger.end_step_logger(3, True)

            self._test_content_logger.start_step_logger(4)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_obj, self._cfg_opt)
            self.get_yum_repo_config(vm_obj, common_content_lib_vm_obj, os_type="centos",machine_type="vm")
            self._test_content_logger.end_step_logger(4, True)

            self._test_content_logger.start_step_logger(5)
            self.install_burnin_dependencies_linux(vm_obj, common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(5, True)

            install_collateral_vm_obj = InstallCollateral(self._log, vm_obj, self._cfg_opt)

        # ===================================================================================================
        self._log.info('Starting the ping flodding test at SUT and VM')
        self._test_content_logger.start_step_logger(6)
        self._log.info('Execute the ping flooding at SUT {}...'.format(self.get_ip(self._common_content_lib)))
        sut_ping_thread = threading.Thread(target=self.execute_ping_flood_test,
                                         args=(self._common_content_lib, self.get_ip(common_content_lib_vm_obj),
                                               self.TEST_TIMEOUT,))
        sut_ping_thread.start()
        self._test_content_logger.end_step_logger(6, True)
        time.sleep(self.WAITING_TIME_IN_SEC)

        self._log.info('Execute the ping flooding at VM {}...'.format(self.get_ip(common_content_lib_vm_obj)))
        self._test_content_logger.start_step_logger(7)
        vm_ping_thread = threading.Thread(target=self.execute_ping_flood_test,
                                         args=(common_content_lib_vm_obj, self.get_ip(self._common_content_lib),
                                               self.TEST_TIMEOUT,))
        vm_ping_thread.start()
        self._test_content_logger.end_step_logger(7, True)
        #====================================================================================================
        self._test_content_logger.start_step_logger(8)
        self._install_collateral.install_fio(install_fio_package=True)
        self._test_content_logger.end_step_logger(8, True)
        self._log.info('Execute the fio command on SUT...')
        fio_thread = None
        self._test_content_logger.start_step_logger(9)
        fio_thread = threading.Thread(target=self.fio_execute_thread,
                                      args=(self.FIO_CMD, self.FIO_CMD, self.TEST_TIMEOUT,))
        fio_thread.start()
        self._test_content_logger.end_step_logger(9, True)
        self._log.info("Successfully tested fio Stress on SUT")
        #====================================================================================================
        self._log.info('Execute the dynamo command on SUT...')
        dynamo_thread = None
        self._test_content_logger.start_step_logger(10)
        dynamo_thread = threading.Thread(target=self.execute_dynamo,
                                         args=(self.TEST_TIMEOUT,))
        dynamo_thread.start()
        self._test_content_logger.end_step_logger(10, True)
        self._log.info("Successfully started dynamo test on SUT")
        # ====================================================================================================
        self._log.info("Starting Iometer on host machine")
        self._test_content_logger.start_step_logger(11)
        iometer_tool_path, bkc_config_file_path = self._install_collateral.install_iometer_tool_on_host_win()

        # iometer_tool_path = os.path.join(self._common_content_lib.get_collateral_path(),
        #                                  IOmeterToolConstants.IOMETER_TOOL_FOLDER)
        # bkc_config_file_path = self._common_content_configuration.get_iometer_tool_config_file()
        copy(bkc_config_file_path, iometer_tool_path)
        self._test_content_logger.end_step_logger(11, True)
        # Executing import iometer.reg command
        self._test_content_logger.start_step_logger(12)
        reg_output = self._common_content_lib.execute_cmd_on_host(IOmeterToolConstants.REG_CMD, iometer_tool_path)
        self._log.debug("Successfully run iometer org file: {}".format(reg_output))
        # Executing IOMETER Tool on host
        config_file_name = self._common_content_configuration.get_iometer_tool_config_file_name()
        self._log.info("Executing iometer command:{}".format(IOmeterToolConstants.EXECUTE_IOMETER_CMD.format(config_file_name)))
        io_output = self._common_content_lib.execute_cmd_on_host(IOmeterToolConstants.EXECUTE_IOMETER_CMD.format(
            config_file_name),iometer_tool_path)
        self._test_content_logger.end_step_logger(12, True)
        self._log.debug("Successfully run iometer tool: \n{}".format(io_output))

        #===================================================================================================
        self._test_content_logger.start_step_logger(13)
        self.bit_location = self.collateral_installer.install_burnintest()  # install burnin tool
        self._test_content_logger.end_step_logger(13, True)
        # execute burnin test on SUT
        self._log.info("Starting Burnin stress test on SUT")
        burnin_thread = None
        self._test_content_logger.start_step_logger(14)
        burnin_thread = threading.Thread(target=self.stress_app_provider.execute_burnin_test,
                                         args=(self.log_dir, self.TEST_TIMEOUT, self.bit_location,
                                               self.BURNING_80_WORKLOAD_CONFIG_FILE,))
        # Thread has been started
        burnin_thread.start()
        self._test_content_logger.end_step_logger(14, True)
        self._log.info("Successfully tested Burnin Stress on SUT")

        # ====================================================================================================
        self._log.info('Executing and waiting for stress tools to complete the stress test')
        time.sleep((self.TEST_TIMEOUT) + TimeConstants.FIVE_MIN_IN_SEC)
        self._log.info('Stress Test completed successfully, starting cleanup...')

        self._test_content_logger.start_step_logger(15)
        self._log.info("Killing SUT ping Thread")
        vm_ping_thread.join()
        self._log.info("Killing VM ping Thread")
        sut_ping_thread.join()

        self._log.info("Killing fio Thread")
        fio_thread.join()
        self._log.info("Killing Dynamo Thread")
        dynamo_thread.join()
        self._log.info("Killing Brunin Thread")
        burnin_thread.join()
        self._test_content_logger.end_step_logger(15, True)

        self._test_content_logger.start_step_logger(16)
        for vm_name in self.LIST_OF_VM_NAMES:
            self.verify_vm_functionality(vm_name, self.VM_TYPE)

        self._log.error("Linux VM is alive!")

        if not self.os.is_alive():
            self._log.error("Linux SUT is not alive")
            return False

        self._log.error("Linux SUT is alive!")
        self._test_content_logger.end_step_logger(16, True)

        return True

    def cleanup(self, return_status):
        """
        # type: (bool) -> None
        Executing the cleanup.
        """
        super(VirtualizationRhelNWAndNVMeTOStress, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationRhelNWAndNVMeTOStress.main()
             else Framework.TEST_RESULT_FAIL)
