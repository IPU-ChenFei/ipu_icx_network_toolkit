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
import threading
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.lib.test_content_logger import TestContentLogger
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon


class VirtualizationRhelSlesNetworkVirtualizationTest(VirtualizationCommon):
    """
    Phoenix ID: P18014072996 ["Virtualization_Rhel_Sles_Network_Virtualization"]
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Enabling libvirtd
    2. Creating Network Bridge
    3. Create VM.
    4. Sending & Recieving Network Traffic from SUT to VM
    5. Sending & Recieving Network Traffic from VM to SUT
    """
    STEP_DATA_DICT = {
        1: {'step_details': "Libvirtd should be Enable in the SUT.",
            'expected_results': "Enabled Libvirtd in the SUT"},
        2: {'step_details': "Screen packakge should be install in the SUT.",
            'expected_results': "Screen package installed in the SUT"},
        3: {'step_details': "Need to create Network bridge in the SUT.",
            'expected_results': "Created Network bridge in the SUT"},
        4: {'step_details': "Need to create CENTOS VM with bridge.",
            'expected_results': "Created CENTOS VM with bridge"},
        5: {'step_details': "iperf3 tool should be install in the SUT.",
            'expected_results': "Installed iperf3 tool in the SUT"},
        6: {'step_details': "Need to disable the firewalld in the VM.",
            'expected_results': "Disabeld the firewalld in the VM"},
        7: {'step_details': "Screen packakge should be install in the VM.",
            'expected_results': "Screen package installed in the VM"},
        8: {'step_details': "iperf3 tool should be install in the VM.",
            'expected_results': "Installed iperf3 tool in the VM"},
        9: {'step_details': "Need to send & receive the network traffic between SUT and VM.",
            'expected_results': "Sending & Receive the network traffice between SUT and VM"},
        10: {'step_details': "Need to send & receive the network traffic between VM and SUT.",
            'expected_results': "Sending & Receive the network traffice between VM and SUT"}}
    VM = [VMs.CENTOS]
    VM_NAME = None
    SNAPSHOT_NAME = None
    BIOS_CONFIG_FILE = "virtualization_rhel_sles_network_virtualization_test_l.cfg"
    exec_time = 60
    TEST_CASE_ID = ["P18014072996", "Virtualization_Rhel_Sles_Network_Virtualization_Test"]
    REGEX_FOR_DATA_LOSS = r".*sec.*0.00.*Bytes.*0.00.*bits.sec$"
    _port = None

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationRhelSlesNetworkVirtualizationTestVirtualization object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        super(VirtualizationRhelSlesNetworkVirtualizationTest, self).__init__(test_log, arguments, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self.common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._cfg_opt = cfg_opts
        if self.os.os_type != OperatingSystems.LINUX:
             raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs as per the test case.
        2. Reboot the SUT to apply the new bios settings.
        3. Verify the bios knobs whether they updated properly.

        :return: None
        """
        # Check the for the Linux OS in the SUT
        if self.os.os_type != OperatingSystems.LINUX:
            raise TestNotImplementedError("This Test case is not supported on {} OS".format(self.os.os_type))
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        super(VirtualizationRhelSlesNetworkVirtualizationTest, self).prepare()

    def execute(self):
        """
        1. Enabling libvirtd
        2. Installing Screen Package in the SUT
        3. Creating Network Bridge
        4. Creating VM with Bridge
        5. Installing iperf3 in the SUT
        6. Disabling the firewalld in the VM
        7. Installing Screen Package in the VM
        8. Installing iperf3 in the VM
        9. Sending & Receive the network traffice between SUT and VM
        10. Sending & Receive the network traffice between VM & SUT
        """
        self._test_content_logger.start_step_logger(1)
        self.vm_provider.install_kvm_vm_tool()
        self._test_content_logger.end_step_logger(1, True)
        self._test_content_logger.start_step_logger(2)
        self._install_collateral.screen_package_installation()
        self._test_content_logger.end_step_logger(2, True)
        self._test_content_logger.start_step_logger(3)
        self.vm_provider.create_bridge_network("virbr0")
        self._test_content_logger.end_step_logger(3, True)
        self._test_content_logger.start_step_logger(4)
        for index in range(len(self.VM)):
            # create VM names dynamically according to the OS
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._vm_provider.destroy_vm(vm_name)
            self.create_vm_with_bridge(vm_name, self.VM[index], mac_addr=True)
            self.verify_vm_functionality(vm_name, self.VM[index], enable_yum_repo=True)
            self._test_content_logger.end_step_logger(4, True)
            self._test_content_logger.start_step_logger(5)
            self.collateral_installer.install_iperf_on_linux()
            self.stop_and_disable_frewalld_l(self.common_content_lib)
            self._test_content_logger.end_step_logger(5, True)
            vm_os_obj = self.create_vm_host(vm_name, self.VM[index])
            common_content_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opt)
            install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opt)
            self._test_content_logger.start_step_logger(6)
            self.stop_and_disable_frewalld_l(common_content_vm_obj)
            self._test_content_logger.end_step_logger(6, True)
            self._test_content_logger.start_step_logger(7)
            install_collateral_vm_obj.screen_package_installation()
            self._test_content_logger.end_step_logger(7, True)
            self._test_content_logger.start_step_logger(8)
            repo_folder_path = self._common_content_configuration.get_yum_repo_name(self._sut_os, self.VM[0])
            self._enable_yum_repo_in_vm(vm_os_obj, repo_folder_path)
            install_collateral_vm_obj.install_iperf_on_linux()
            self._test_content_logger.end_step_logger(8, True)
            self._test_content_logger.start_step_logger(9)
            server_thread = threading.Thread(target=self.execute_sut_as_iperf_server,
                                             args=(self.exec_time, None))
            client_thread = threading.Thread(target=self.execute_vm_as_iperf_client,
                                             args=(vm_os_obj, common_content_vm_obj, self.exec_time))
            server_thread.start()
            client_thread.start()
            time.sleep(self.exec_time)
            # stop iperf process at SUT
            self.stop_iperf()
            server_thread.join()
            client_thread.join()
            self._test_content_logger.end_step_logger(9, True)
            self._test_content_logger.start_step_logger(10)
            server_thread1 = threading.Thread(target=self.execute_vm_as_iperf_server,
                                             args=(vm_os_obj, common_content_vm_obj, self.exec_time))
            client_thread1 = threading.Thread(target=self.execute_sut_as_iperf_client,
                                             args=(vm_name,self.exec_time))
            server_thread1.start()
            client_thread1.start()
            time.sleep(self.exec_time)
            # stop iperf process at VM
            self.stop_iperf(common_content_vm_obj)
            server_thread1.join()
            client_thread1.join()
            self._test_content_logger.end_step_logger(10, True)

        return True

    def cleanup(self, return_status):
         super(VirtualizationRhelSlesNetworkVirtualizationTest, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationRhelSlesNetworkVirtualizationTest.main()
             else Framework.TEST_RESULT_FAIL)