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

import os
import sys
import time
import threading

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.install_collateral import InstallCollateral
from src.lib.common_content_lib import CommonContentLib
from src.provider.vm_provider import VMs
from src.virtualization.base_qat_util import BaseQATUtil


class VirtualizationCrossSocketTopologyNICPassthrough(BaseQATUtil,VirtualizationCommon):
    """
    Phoenix ID : 16014131634
    Purpose of this test case is to validate the cross socket topology of NIC and VMs using Passthru.
    """

    NUMBER_OF_VMS = 2
    VM = [VMs.CENTOS]*2
    VM_TYPE = "CENTOS"
    TEST_CASE_ID = ["P16014131634", "VirtualizationCrossSocketTopologyNICPassthrough"]
    BIOS_CONFIG_FILE = "virt_siov_dlb_cross_socket_topo_bios.cfg"
    STORAGE_VOLUME = ["/home"]
    IPERF_EXEC_TIME = 120  # 14400 #30
    TEST_TIMEOUT = 5
    BASE_PORT = 5000
    gen4_cross_topology = "true"

    STEP_DATA_DICT = {
        1: {'step_details': 'Check Gen4 NIC PF ID and Unbind PF from host',
            'expected_results': 'Should be  successfull'},
        2: {'step_details': 'Load the drivers vfio and vfio-pci',
            'expected_results': 'Should be successfull'},
        3: {'step_details': 'Get the CPU socket, core and threads per core info',
            'expected_results': 'CPU core information retrieved'},
        4: {'step_details': 'Create VMs configured on differernt sockets',
            'expected_results': 'VMs creation should be successfull'},
        5: {'step_details': 'Attach the Gen4 PCIe device to VM',
            'expected_results': 'Device attached to VM should be successfull'},
        6: {'step_details': 'Run Iperf stress test between host and VM and repeat for second VM',
            'expected_results': 'Should be successfull'},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of Instance of virtualization_bios_knobs and enable the BIOS settings

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.virtualization_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(VirtualizationCrossSocketTopologyNICPassthrough, self).__init__(test_log, arguments, cfg_opts, self.virtualization_bios_knobs)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(test_log, self.os, cfg_opts)
        self._cfg_opt = cfg_opts
        self._arg_tc = arguments
        self._test_log = test_log

    def prepare(self):
        # type: () -> None
        """Test preparation/setup """

        if self.os.os_type == OperatingSystems.LINUX:
            self._log.info("We have Linux OS for test case... proceeding further..")
        else:
            raise content_exceptions.TestFail("Target is not booted with Linux")

        super(VirtualizationCrossSocketTopologyNICPassthrough, self).prepare()

    def execute(self):
        """
         Purpose of this test case is to validate the cross socket topology of NIC and VMs using Passthrough
        """
        dbdf_list = self.get_vf_device_dbdf_by_devid(devid="E810-C", common_content_object=self._common_content_lib)
        adapter_list1 = dbdf_list[2:3]
        new = dbdf_list[3]
        adapter_list1.append(new)
        adapter_list2 = dbdf_list[6:]

        self._test_content_logger.start_step_logger(1)
        self.load_vfio_driver()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        for index1 in range(len(dbdf_list)):
            self.host_vfio_driver_unbind(dbsf_value=dbdf_list[index1],
                                         common_content_object=self._common_content_lib)
            self.guest_vfio_pci_gen4_bind(dbsf_value=dbdf_list[index1],
                                            common_content_object=self._common_content_lib)
        self._test_content_logger.end_step_logger(2, return_val=True)

        self.enable_intel_iommu_by_kernel()
        self.get_yum_repo_config(self.os, self._common_content_lib,os_type="centos")

        self._test_content_logger.start_step_logger(3)
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)

            socket, core_socket, threads_per_core = self.get_cpu_core_info()
            total_cpus = socket * core_socket * threads_per_core
            mdev_per_socket = 4
            total_mdev = socket * mdev_per_socket
            cpus_per_vm = int(total_cpus/total_mdev)
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on CentOS.".format(vm_name))


        vm_number = 1
        vm_index = 0
        adapter_index = 0
        flag = 0
        for vm_name in self.LIST_OF_VM_NAMES:
            # create with default values
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
            end_index = (total_cpus - 1) - (vm_index * cpus_per_vm)
            cpu_list = (end_index + 1) / 2
            cpulist1 = "0-{}".format(int(cpu_list))
            cpulist2 = "{}-{}".format(int(cpu_list),int(end_index))
            # start_index = end_index - ((vm_index + 1) * cpus_per_vm) + 1
            start_index = end_index - cpus_per_vm + 1

            if vm_number == 1:
                dbdf_list = adapter_list1
                self._log.info(" Adapter list for 1st VM:{} on CentOS.".format(dbdf_list))
                cpu_list = cpulist1
                self._log.info(" CPULIST for  1st VM:{} on CentOS.".format(cpu_list))
                vm_number = vm_number + 1

            else:
                dbdf_list = adapter_list2
                self._log.info("Adapter list for 2nd VM:{} on CentOS.".format(dbdf_list))
                cpu_list = cpulist2
                self._log.info("CPULIST for for 2nd VM:{} on CentOS.".format(cpu_list))

            self.create_vm_generic(vm_name, self.VM_TYPE, mac_addr=True, pool_id=free_storage_pool,
                                   cpu_core_list=cpu_list)
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm = CommonContentLib(self._test_log, vm_os_obj, self._cfg_opt)
            install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opt)
            install_collateral_vm_obj.install_iperf_on_linux()
            self._log.info(" Created VM:{} on CentOS.".format(vm_name))
            self._test_content_logger.end_step_logger(4, return_val=True)
            self._test_content_logger.start_step_logger(5)
            domain_value, bus_value, device_value, function_value = self.get_split_hex_bdf_values_from_dbdf(
                                                                    dbdf_list[adapter_index])
            self.attach_vfiopci_device_using_dbdf_to_vm(vm_name, domain_value, bus_value, device_value,
                                                        function_value)
            self.verify_gen4_vm(vm_os_obj)
            vf_adapter_name = self.get_virtual_adapter_name_in_vm(common_content_lib_vm)
            network_interface_dict = self.assign_static_ip_to_cross_topology_adapters([vf_adapter_name], flag, common_content_lib_vm)
            flag = flag + 1
            self._test_content_logger.end_step_logger(5, return_val=True)
            self._test_content_logger.start_step_logger(6)
            self._log.info("Executing iperf test on SUT and VM's")

            server_thread = threading.Thread(target=self.execute_sut_as_iperf_server,
                                             args=(self.TEST_TIMEOUT,))
            server_thread.start()
            time.sleep(60)

            self._log.info('Execute the iperf tool with VM as client {}...'.format(self.get_ip(common_content_lib_vm)))
            client_thread = threading.Thread(target=self.execute_vm_as_iperf_client,
                                             args=(vm_os_obj, common_content_lib_vm, self.TEST_TIMEOUT,))
            client_thread.start()
            time.sleep(60)
            self.stop_iperf(common_content_lib_vm)
            server_thread.join()
            client_thread.join()
            self._test_content_logger.end_step_logger(6, return_val=True)


        return True

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationCrossSocketTopologyNICPassthrough.main() else Framework.TEST_RESULT_FAIL)

