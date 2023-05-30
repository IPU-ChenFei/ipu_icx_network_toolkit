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

from src.lib.dtaf_content_constants import IOmeterToolConstants, TimeConstants
from src.storage.test.storage_common import StorageCommon
from src.provider.socwatch_provider import SocWatchCSVReader

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

class VirtualizationCentosSRIOVNWAndNVMePassThruIOStress(VirtualizationCommon):
    """
    Phoenix ID : 16014085036-VirtualizationCentosSRIOVNWAndNVMePassThruIOStress
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
    TEST_CASE_ID = ["P16014085036", "VirtualizationCentosSRIOVNWAndNVMePassThruIOStress"]

    STEP_DATA_DICT = {
        1: {'step_details': "Set and Verify bios knobs settings.",
            'expected_results': "BIOS knobs set as per knobs file and verified."},
        2: {'step_details': "Create the name of All VMs to be created",
            'expected_results': "VM names created successfully"},
        3: {'step_details': "Create the Windows VM with VM name",
            'expected_results': "VM with Windows created and verified"},
        4: {'step_details': "Create NVMe0 passthrough for Windows VM",
            'expected_results': "Passthrough for VM created successfulyy"},
        5: {'step_details': "Install iometer tool and start in thread",
            'expected_results': "Iometer tool started in thread"},
        6: {'step_details': "Create the Centos VM with VM name",
            'expected_results': "VM with Centos created and verified"},
        7: {'step_details': "Create NVMe1 passthrough for Linux VM",
            'expected_results': "Passthrough for VM created successfulyy"},
        8: {'step_details': "Yum repo creation and tools installation started",
            'expected_results': "Yum repo and dependencies installed on VM successfully"},
        9: {'step_details': "Install fio tool on SUT",
            'expected_results': "Fio Tool installed successfully on SUT"},
        10: {'step_details': "Start fio tool execution on SUT",
             'expected_results': "Fio tool started successfully on SUT"},

        11: {'step_details': "Install Tools for SIOV for NW card",
             'expected_results': "Tools installed successfully"},
        12: {'step_details': "Create the NW card instances for VMs",
             'expected_results': "NW card instances created"},
        13: {'step_details': "Attach the NW card instances to VMs",
             'expected_results': "NW card instances attached to VMs"},

        14: {'step_details': "Execute the ping flooding at SUT.",
             'expected_results': "Ping flood test on SUT started"},
        15: {'step_details': "Execute the ping flooding on VM",
             'expected_results': "Ping flood test on VM started successfully"},

        16: {'step_details': "Execute the dynamo tool on SUT...",
             'expected_results': "Dynamo tool started on SUT..."},
        17: {'step_details': "Attach VF PCIe device to VM",
             'expected_results': "Virtual function adapter attached to VM"},
        18: {'step_details': "Verify the attached VFs in VMs",
             'expected_results': "Virtual function verified in VM"},
        19: {'step_details': "Get the VF adpater device name in VM",
             'expected_results': "Virtual function adapter name in VM obtained successfully"},
        20: {'step_details': "Assign Static IP to VF in VM",
             'expected_results': "Static IP assigned to VF adpater of VM"},
        21: {'step_details': "Wait for all threads to join and kill all tool execution threads",
             'expected_results': "All waiting threads joined and removed successfully"},
        22: {'step_details': "Verify the SUT and VM if both are running and stable",
             'expected_results': "SUT and VMs are running fine"},
    }
    BIOS_CONFIG_FILE = "virt_nw_sriov_nvme_pthru_bios_knobs.cfg"
    NUMBER_OF_VMS = 2
    VM = [VMs.WINDOWS, VMs.CENTOS]
    LIST_OF_VM_NAMES = []
    VM_TYPE = ["WINDOWS", "CENTOS"]
    REPOS_FOLDER_PATH_SUT = "/etc/yum.repos.d"
    C_DRIVE_PATH = "C:\\"
    YUM_REPO_FILE_NAME = r"intel-yum-rhel.repo"
    REPOS_FOLDER_PATH_SUT = "/etc/yum.repos.d"
    ENABLE_YUM_REPO_COMMAND = "yum repolist all"
    TEST_TIME_SLEEP = 7200
    STORAGE_VOLUME = ["/home"]
    BUS_TYPE = "NVMe"
    SCSI_CONTROLLER = "SAS"
    DEVICE_TYPE = "NVMe"
    CSV_FILE = "result.csv"
    IPERF_EXEC_TIME = 120  # 14400 #30
    TEST_TIMEOUT = 5  # 120  # 5 in minutes
    BURNING_80_WORKLOAD_CONFIG_FILE = "cmdline_config_80_workload_centos_nw_nvme_stress.txt"
    BIT_TIMEOUT = 5  # 120  # 5 in minutes
    SUT_BIT_LOCATION = None
    VM_NAME = None
    bit_location = None
    NETWORK_ASSIGNMENT_TYPE = "SRIOV"
    VSWITCH_NAME = "ExternalSwitch"
    ADAPTER_NAME = None
    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new object for VirtualizationCentosSRIOVNWAndNVMePassThruIOStress

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VirtualizationCentosSRIOVNWAndNVMePassThruIOStress, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("This Test Case is Only Supported on Linux")
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self._storage_provider = StorageProvider.factory(self._log, self.os, cfg_opts)  # type: StorageProvider
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self.stress_app_provider = StressAppTestProvider.factory(self._log, os_obj=self.os, cfg_opts=cfg_opts)
        csv_file_path = os.path.join(self.log_dir, self.CSV_FILE)
        self.csv_reader_obj = SocWatchCSVReader(self._log, csv_file_path)

        self._cfg_opt = cfg_opts
        self._cfg_arg = arguments
        self._cfg_log = test_log
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

        super(VirtualizationCentosSRIOVNWAndNVMePassThruIOStress, self).prepare()
        self._test_content_logger.start_step_logger(1)
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        self._vm_provider.create_bridge_network("virbr0")
        self._test_content_logger.end_step_logger(1, True)

    def execute_iometer_thread(self, vm_name, sut_folder_path, common_content_lib_obj, os_obj):
        self.execute_iometer(sut_folder_path, common_content_lib_obj, os_obj)
        # Copy Csv file from host to sut
        vm_ip = self._vm_provider.get_vm_ip(vm_name)

        # cmd = r"powershell.exe pscp -scp -pw intel@123 Administrator@{}:{}/{} .".format(vm_ip, sut_folder_path, self.CSV_FILE)
        # common_content_lib_vm_obj.execute_sut_cmd(cmd,
        #                                        self._command_timeout,
        #                                        sut_folder_path)
        self.copy_csv_file_from_sut_to_host_w(self.log_dir, sut_folder_path, self.CSV_FILE,
                                              common_content=common_content_lib_obj, os_obj=os_obj)
        # Update the csv file to the csv reader provider
        self.csv_reader_obj.update_csv_file(os.path.join(self.log_dir, self.CSV_FILE))
        absolute_log_path = self.log_dir + os.sep + self.CSV_FILE
        read_errors_values = self.get_column_data_w(IOmeterToolConstants.READ_ERROR, absolute_log_path)
        self._log.info("Iometer {} values :{}".format(IOmeterToolConstants.READ_ERROR, read_errors_values))

        write_errors_values = self.get_column_data_w(IOmeterToolConstants.WRITE_ERROR, absolute_log_path)
        self._log.info("Iometer {} values :{}".format(IOmeterToolConstants.WRITE_ERROR, write_errors_values))
        read_errors_values = [float(value) for value in read_errors_values if
                              float(value) > float(IOmeterToolConstants.ERROR_LIMIT)]
        errors = []
        if read_errors_values:
            errors.append("Few {} values are greater than {}".format(IOmeterToolConstants.READ_ERROR,
                                                                     IOmeterToolConstants.ERROR_LIMIT))
        write_errors_values = [float(value) for value in write_errors_values if
                               float(value) > float(IOmeterToolConstants.ERROR_LIMIT)]
        if write_errors_values:
            errors.append("Few {} values are greater than {}".format(IOmeterToolConstants.WRITE_ERROR,
                                                                     IOmeterToolConstants.ERROR_LIMIT))

        if errors:
            raise content_exceptions.TestFail("\n".join(errors))

    def execute_iometer(self, sut_folder_path, common_content_lib_obj, os_obj):
        """
        1. Run execute_iometer.reg file in SUT machine to Once run.
        2. IOmeter will run for one hour
        3. Perform an reboot and checks iometer in task manager

        :raise: content_exceptions.TestFail
        :return: None
        """
        # Adding iometer command to regedit
        common_content_lib_obj.execute_sut_cmd(IOmeterToolConstants.ADD_IOMETER_REG,
                                               IOmeterToolConstants.ADD_IOMETER_REG, self._command_timeout,
                                               sut_folder_path)

        # Adding Autologon command to regedit
        self._log.info("Executing {} command".format(IOmeterToolConstants.EXECUTE_AUTOLOGON_REG))
        common_content_lib_obj.execute_sut_cmd(IOmeterToolConstants.EXECUTE_AUTOLOGON_REG,
                                               IOmeterToolConstants.EXECUTE_AUTOLOGON_REG, self._command_timeout,
                                               sut_folder_path)

        common_content_lib_obj.perform_os_reboot(self.reboot_timeout)
        time.sleep(TimeConstants.ONE_MIN_IN_SEC)
        process_running = os_obj.execute(IOmeterToolConstants.TASKFIND_CMD.format("Iometer"),
                                         self._command_timeout)

        self._log.info("Task list output: {}".format(process_running.stdout))
        if process_running.return_code:
            raise content_exceptions.TestFail("IOMeter stress tool is not running")
        self._log.info("Successfully launched IOmeter tool")
        time.sleep(TimeConstants.ONE_HOUR_IN_SEC + TimeConstants.ONE_MIN_IN_SEC)
        process_running = os_obj.execute(
            IOmeterToolConstants.TASKFIND_CMD.format("Iometer"),
            self._command_timeout)
        if not process_running.return_code:
            raise content_exceptions.TestFail("IOMeter stress tool is failed to close still running")
        self._log.info("Successfully launched and Ended IOmeter tool")

    def execute(self):
        """"
        This method installs different stress tools, fio, burnin, dynamo, ping/iperf and iometer
        tool, execute for min 4 hours and validate the resulting log out put

        Checks whether SUT and VM both are stable the stress load test.

        :return: True or False
        :raise: if non zero errors raise content_exceptions.TestFail
        """
        # Enabling the Intel iommu in kernel
        if not self.enable_intel_iommu_by_kernel():
            raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")

        self._test_content_logger.start_step_logger(1)
        self._install_collateral.screen_package_installation()
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)
        self._test_content_logger.end_step_logger(1, True)

        #=======================================================================================
        self._test_content_logger.start_step_logger(1)
        network_device_name = self._common_content_configuration.get_columbiaville_nic_device_name()
        nw_device_list = self.get_sriovf_enabled_nw_adapters(network_device_name)
        if len(nw_device_list) == 0:
            network_device_name = self._common_content_configuration.get_fortville_nic_device_name()
            nw_device_list = self.get_sriovf_enabled_nw_adapters(network_device_name)
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        nw_adapter_name = nw_device_list[0]
        self.remove_virtual_function(nw_adapter_name)
        self._test_content_logger.end_step_logger(2, True)

        self._test_content_logger.start_step_logger(2)
        opt_dict = self.assign_static_ip_to_nw_adapters(nw_device_list)
        self._test_content_logger.end_step_logger(2, True)

        nw_adapter_name = nw_device_list[0]
        self._test_content_logger.start_step_logger(3)
        # create VF
        self.create_virtual_function(self.NUMBER_OF_VMS, nw_adapter_name)
        # virt_function_list = self.generate_virtual_functions(num_of_adapters=self.NUMBER_OF_VMS)
        # opt_dict = self.assign_static_ip_to_nw_adapters(nw_device_list)
        self._test_content_logger.end_step_logger(3, True)

        self._test_content_logger.start_step_logger(4)
        # get the VF adapter details
        vfs_data_list = self.get_vf_adapter_details()
        self._test_content_logger.end_step_logger(4, True)

        # VF module details
        self._test_content_logger.start_step_logger(5)
        self.get_and_verify_vf_module_details()
        self._test_content_logger.end_step_logger(5, True)

        # get VF mac ids & assign it
        self._test_content_logger.start_step_logger(6)
        vf_mac_id_details = self.get_vf_mac_details()
        self._test_content_logger.end_step_logger(6, True)

        self._test_content_logger.start_step_logger(7)
        mac_id_list = self.assign_macs_to_vfs(self.NUMBER_OF_VMS, vf_mac_id_details, nw_adapter_name)
        self._test_content_logger.end_step_logger(7, True)
        # MAC id details of VM list
        self._test_content_logger.start_step_logger(8)
        self.verify_vf_mac_details(mac_id_list)
        # VF module details
        self.get_and_verify_vf_module_details()
        self._test_content_logger.end_step_logger(8, True)
        #=======================================================================================

        self._common_content_lib = CommonContentLib(self._log, self.os, self._cfg_opt_tc)
        self.get_yum_repo_config(self.os, self._common_content_lib, os_type="centos")

        iometer_thread = None
        vm_ping_thread1 = None
        vm_ping_thread1 = None
        sut_ping_thread = None
        vm_sut_obj_list = []
        stressapp_provider_obj_list = []
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            self._test_content_logger.start_step_logger(2)
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on CENTOS.".format(vm_name))
            ip, subnet = opt_dict[nw_device_list[0]]
            ip = ip[:-2] + str(int(ip[-2:]) + 5 + index)

            if index == 0:
                self.create_hyperv_vm(vm_name, self.VM_TYPE[index])  # Create VM function
                self._vm_provider.wait_for_vm(vm_name)  # Wait for VM to boot
                self._vm_provider.add_vm_network_adapter(self.NETWORK_ASSIGNMENT_TYPE, vm_name, self.ADAPTER_NAME,
                                                         self.VSWITCH_NAME)
                self.verify_hyperv_vm(vm_name, self.VM_TYPE[index])
                self.create_ssh_vm_object(vm_name)
                vm_os_obj = self.windows_vm_object(vm_name, self.VM_TYPE[index])
                vm_sut_obj_list.append(vm_os_obj)
                install_collateral_vm_obj = InstallCollateral(log=self._cfg_log, os_obj=vm_os_obj,
                                                              cfg_opts=self._cfg_opt)
                stress_app_provider_vm = StressAppTestProvider.factory(self._log, os_obj=vm_os_obj,
                                                                       cfg_opts=self._cfg)
                stressapp_provider_obj_list.append(stress_app_provider_vm)
                # NVMe disk pass through
                common_content_lib_vm_obj = CommonContentLib(log=self._cfg_log, os_obj=vm_os_obj,
                                                             cfg_opts=self._cfg_opt)
                # detach NVMe from SUT
                device_id = self._vm_provider.enumerate_storage_device(self.BUS_TYPE, index,
                                                                       self._common_content_lib)
                self._vm_provider.set_disk_offline(device_id, self._common_content_lib)
                # attach the NVMe to VM
                self._vm_provider.add_storage_device_to_vm(vm_name, device_id, storage_size=None)
                vm_os_obj = self.windows_vm_object(vm_name, self.VM_TYPE)
                common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, None)
                install_collateral_vm_obj = InstallCollateral(log=self._cfg_log, os_obj=vm_os_obj,
                                                              cfg_opts=self._cfg_opt)
                vm_device_list = self._vm_provider.enumerate_storage_device(self.SCSI_CONTROLLER,
                                                                            self.DISK_LIST_VALUE,
                                                                            common_content_lib_vm_obj)
                self._vm_provider.set_disk_online(vm_device_list, common_content_lib_vm_obj)
                self._test_content_logger.end_step_logger(2, True)
                # ===================================================================================================
                self._test_content_logger.start_step_logger(1)
                self.verify_os_device_info(self.DEVICE_TYPE)
                self._log.info("OS Successfully booted from {}".format(self.DEVICE_TYPE))
                self._test_content_logger.end_step_logger(1, True)
                self._test_content_logger.start_step_logger(2)
                sut_folder_path = install_collateral_vm_obj.install_iometer_tool_windows()
                iometer_thread = threading.Thread(target=self.execute_iometer_thread,
                                                  args=(
                                                      vm_name, sut_folder_path, common_content_lib_vm_obj,
                                                      vm_os_obj,
                                                      self.TEST_TIMEOUT,))
                iometer_thread.start()

                self._test_content_logger.end_step_logger(2, True)
                #====================================================================================================
                # attach VF to VMs
                # attaching the VF device to the VM
                self.attach_pci_nw_device_to_vm(vfs_data_list[index], vm_name)
                nw_list = self._vm_provider._get_vm_network_adapter(vm_name)

                # get vf adapter name in VM and assign static IP to it
                # vf_adapter_name = self.get_vf_adapter_name_in_vm(vm_name, mac_id_list[index])
                # self.assign_ip_to_vf_in_vm(vm_os_obj, ip, subnet, vf_adapter_name, vm_name)

                #====================================================================================================
                # ====================================================================================================
                self._log.info('Starting the ping flodding test at VM')
                self._log.info('Execute the ping flooding at VM {}...'.format(self.get_ip(common_content_lib_vm_obj)))
                self._test_content_logger.start_step_logger(7)
                vm_ping_thread1 = threading.Thread(target=self.execute_ping_flood_test,
                                                  args=(
                                                      common_content_lib_vm_obj, self.get_ip(self._common_content_lib),
                                                      self.TEST_TIMEOUT,))
                vm_ping_thread1.start()
                self._test_content_logger.end_step_logger(7, True)

                # =====================================================================================================
            else:
                # create with default values
                self._test_content_logger.start_step_logger(2)
                self._vm_provider.destroy_vm(vm_name)
                free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                                  self.VM_TYPE[index])
                self.create_vm_pool_nested(vm_name, self.VM_TYPE[index], vm_create_async=None, mac_addr=True,
                                           pool_id=free_storage_pool,
                                           extra_disk_space=None)
                self.verify_vm_functionality(vm_name, self.VM_TYPE[index])
                self._log.info(" Created VM:{} on CENTOS.".format(vm_name))
                # create VM os object
                vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE[index])
                vm_sut_obj_list.append(vm_os_obj)
                stress_app_provider_vm = StressAppTestProvider.factory(self._log, os_obj=vm_os_obj,
                                                                       cfg_opts=self._cfg)
                stressapp_provider_obj_list.append(stress_app_provider_vm)
                common_content_lib_vm_obj = CommonContentLib(log=self._cfg_log, os_obj=vm_os_obj,
                                                             cfg_opts=self._cfg_opt)
                install_collateral_vm_obj = InstallCollateral(log=self._cfg_log, os_obj=vm_os_obj,
                                                              cfg_opts=self._cfg_opt)

                self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, os_type="centos", machine_type="vm")
                install_collateral_vm_obj.screen_package_installation()
                # detach NVMe from SUT
                # nvme_info = self.get_nvm_info()
                device_id = self.enumerate_storage_device(self.BUS_TYPE, index, self._common_content_lib)
                self.set_disk_offline(device_id[0], self._common_content_lib)
                # attach the NVMe to VM
                self.attach_pci_device_to_vm(device_id[0], vm_name)
                common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, None)
                vm_device_list = self.enumerate_storage_device(self.SCSI_CONTROLLER, self.DISK_LIST_VALUE,
                                                               common_content_lib_vm_obj)
                self.set_disk_online(vm_device_list[0], common_content_lib_vm_obj)
                self._test_content_logger.end_step_logger(2, True)
                # ====================================================================================================
                self._test_content_logger.start_step_logger(8)
                install_collateral_vm_obj.install_fio(install_fio_package=True)
                self._test_content_logger.end_step_logger(8, True)
                self._log.info('Execute the fio command on VM...')
                fio_thread = None
                self._test_content_logger.start_step_logger(9)
                fio_thread = threading.Thread(target=self.fio_execute_thread,
                                              args=(self.FIO_CMD, self.FIO_CMD, self.TEST_TIMEOUT,
                                                    common_content_lib_vm_obj,))
                fio_thread.start()
                self._test_content_logger.end_step_logger(9, True)
                self._log.info("Successfully tested fio Stress on VM")

                # ====================================================================================================
                # create VFs for NW and assign to VMs
                # attaching the VF device to the VM
                self._test_content_logger.start_step_logger(11)
                self.attach_pci_nw_device_to_vm(vfs_data_list[index], vm_name)
                self.reboot_linux_vm_sleep(vm_name)
                self._test_content_logger.end_step_logger(11, True)

                # verify VF in VM
                self._test_content_logger.start_step_logger(12)
                self.verify_vf_in_vm(vm_os_obj)
                self._test_content_logger.end_step_logger(12, True)

                # get vf adapter name in VM
                self._test_content_logger.start_step_logger(13)
                vf_adapter_name = self.get_vf_adapter_name_in_vm(vm_name, mac_id_list[index])
                self._test_content_logger.end_step_logger(13, True)

                # assign the IP to the VM
                self._test_content_logger.start_step_logger(14)
                self.assign_ip_to_vf_in_vm(vm_os_obj, ip, subnet, vf_adapter_name, vm_name)
                self._test_content_logger.end_step_logger(14, True)
                # ====================================================================================================
                # ====================================================================================================
                self._log.info('Starting the ping flodding test at SUT and VM')
                self._test_content_logger.start_step_logger(6)
                self._log.info('Execute the ping flooding at SUT {}...'.format(self.get_ip(self._common_content_lib)))
                sut_ping_thread = threading.Thread(target=self.execute_ping_flood_test,
                                                   args=(
                                                   self._common_content_lib, self.get_ip(common_content_lib_vm_obj),
                                                   self.TEST_TIMEOUT,))
                sut_ping_thread.start()
                self._test_content_logger.end_step_logger(6, True)
                time.sleep(self.WAITING_TIME_IN_SEC)

                self._log.info('Execute the ping flooding at VM {}...'.format(self.get_ip(common_content_lib_vm_obj)))
                self._test_content_logger.start_step_logger(7)
                vm_ping_thread2 = threading.Thread(target=self.execute_ping_flood_test,
                                                  args=(
                                                  common_content_lib_vm_obj, self.get_ip(self._common_content_lib),
                                                  self.TEST_TIMEOUT,))
                vm_ping_thread2.start()
                self._test_content_logger.end_step_logger(7, True)

                # =====================================================================================================

        self._log.info('Executing and waiting for stress tools to complete the stress test')
        time.sleep((self.TEST_TIMEOUT) + TimeConstants.FIVE_MIN_IN_SEC)
        self._log.info('Stress Test completed successfully, starting cleanup...')

        self._test_content_logger.start_step_logger(15)
        self._log.info("Killing VM ping Thread")
        vm_ping_thread1.join()
        vm_ping_thread2.join()
        self._log.info("Killing SUT ping Thread")
        sut_ping_thread.join()

        self._log.info("Killing IOmeter Thread")
        iometer_thread.join()

        self._log.info("Killing fio Thread")
        fio_thread.join()

        self._test_content_logger.end_step_logger(15, True)

        self._test_content_logger.start_step_logger(16)

        for index, vm_name_nest in zip(range(len(self.LIST_OF_VM_NAMES)), self.LIST_OF_VM_NAMES):
            if index == 0:
                self.verify_hyperv_vm(vm_name, self.VM_TYPE[index])
            else:
                self.verify_vm_functionality(vm_name, self.VM_TYPE[index])
            # detach the VF from the VM
            self._test_content_logger.start_step_logger(17)
            self.detach_pci_nw_device_from_vm(vfs_data_list[index], vm_name)
            self._test_content_logger.end_step_logger(17, True)
        self._log.error("Linux VM is alive!")

        if not self.os.is_alive():
            self._log.error("Linux SUT is not alive")
            return False

        self._log.error("Linux SUT is alive!")
        self._test_content_logger.end_step_logger(16, True)

        # remove VF
        self._test_content_logger.start_step_logger(19)
        self.remove_virtual_function(nw_adapter_name)
        self._test_content_logger.end_step_logger(19, True)

        return True

    def cleanup(self, return_status):
        """
        # type: (bool) -> None
        Executing the cleanup.
        """
        super(VirtualizationCentosSRIOVNWAndNVMePassThruIOStress, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationCentosSRIOVNWAndNVMePassThruIOStress.main()
             else Framework.TEST_RESULT_FAIL)
