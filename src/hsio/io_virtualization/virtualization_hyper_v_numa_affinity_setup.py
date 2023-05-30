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
import os
import sys
import re
import time

from collections import Counter

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.hsio.lib.ras_upi_util import RasUpiUtil

from src.lib.common_content_lib import CommonContentLib

from src.lib.dtaf_content_constants import ErrorTypeAttribute
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.lib.os_lib import WindowsCommonLib
from src.provider.vm_provider import VMProvider, VMs
from src.hsio.io_virtualization.cscripts_pcie_error_injection_base_test import VmmCscriptsPcieErrorInjectionBaseTest


class VirtualizationHyperNumaAffinitySetup(VmmCscriptsPcieErrorInjectionBaseTest):
    """
    GLASGOW ID: G67987_W

    This test cases will help put a virtual machine on a Numa node and another virtual machine on another.
    """
    BIOS_CONFIG_FILE = "virtualisation_hyperv_numa_affinity_setup.cfg"
    C_DRIVE_PATH = "C:\\"

    def __init__(self, test_log, arguments, cfg_opts, bios_config=None):
        """
        Create a new VirtualizationHyperNumaAffinitySetup object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        if bios_config:
            bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), bios_config)
        else:
            # calling base class init
            bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), self.BIOS_CONFIG_FILE)
        super(VirtualizationHyperNumaAffinitySetup, self).__init__(test_log, arguments, cfg_opts,
                                                                                 bios_config_file=bios_config_file)
        self._windows_common_lib = WindowsCommonLib(self._log, self.os)

    def prepare(self, vm_os_type=VMs.WINDOWS):  # type: () -> None
        """
        To Setup prepare
        1. Install vm tools
        2. check number of numa nodes
        3. Uncheck "Allow Virtual Machines to span physical NUMA nodes"
        4. Create VM based on the number of numa nodes
        """
        super(VirtualizationHyperNumaAffinitySetup, self).prepare()
        self._vm_provider_obj.install_vm_tool()
        no_of_numa_nodes = self._windows_common_lib.get_os_numa_nodes()
        self.num_vms = len(no_of_numa_nodes)

        self._log.info("Disable - Allow Virtual Machines to span physical NUMA nodes")
        self._windows_common_lib.configure_os_vm_span_numa_node(vm_spanning_numa_nodes=False)
        self.create_hyperv_vms(vm_os_type)

    def execute(self):
        """
        1. Check the Physical numa node info of each VM

        :return : True on Success
        """
        return self.check_vm_physical_numa_nodes()

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        1. Destroy Created VM.
        """
        self._log.info("Enable - Allow Virtual Machines to span physical NUMA nodes")
        self._windows_common_lib.configure_os_vm_span_numa_node(vm_spanning_numa_nodes=True)
        super(VirtualizationHyperNumaAffinitySetup, self).cleanup(return_status)

    def create_hyperv_vms(self, vm_os_type=VMs.WINDOWS):
        """
        This method is used to create the windows VM

        return: None
        """
        if vm_os_type.lower() == OperatingSystems.WINDOWS.lower():
            self.VM_OS = [VMs.WINDOWS]
            for vm in range(self.num_vms):
                #  Create VM names dynamically according to the OS
                vm_name = self.VM_OS[0] + "_" + str(vm)
                self.virtualization_obj.create_hyperv_vm(vm_name, self.VM_TYPE)
                self._vm_provider_obj.wait_for_vm(vm_name)
                self._vm_provider_obj.add_vm_network_adapter(self.NETWORK_ASSIGNMENT_TYPE, vm_name, self.ADAPTER_NAME,
                                                             self.VSWITCH_NAME, mac_addr=True)
                self.virtualization_obj.verify_hyperv_vm(vm_name, self.VM_TYPE)

        elif vm_os_type.lower() == OperatingSystems.LINUX.lower():
            self.VM_OS = [VMs.RHEL]
            self._vm_provider_obj.create_bridge_network(self.VSWITCH_NAME)

            for vm in range(self.num_vms):
                #  Create VM names dynamically according to the OS
                vm_name = self.VM_OS[0] + "_" + str(vm)

                self.virtualization_obj.create_hyperv_vm(vm_name, self.VM_OS[0])

                #  Sleep time to wait that VM to reach OS
                time.sleep(self._common_content_configuration.get_wait_for_vm_os_time_out())

                self._vm_provider_obj.add_vm_network_adapter(self.NETWORK_ASSIGNMENT_TYPE, vm_name, self.ADAPTER_NAME,
                                                             self.VSWITCH_NAME, vm_type=self.VM_OS[0])

                self.virtualization_obj.verify_hyperv_vm(vm_name, self.VM_OS[0])

                vm_os_obj = self.virtualization_obj.create_linux_vm_object_in_hyperv(vm_name, self.VM_OS[0],
                                                                                     enable_yum_repo=True)

                vm_common_content_lib = CommonContentLib(self._log, vm_os_obj, self._cfg)

                #  Install Screen package on VM SUT
                vm_install_collateral = InstallCollateral(self._log, vm_os_obj, self._cfg)
                vm_install_collateral.screen_package_installation(vm_os_linux=True)

                vm_ras_upi_util = RasUpiUtil(vm_os_obj, self._log, self._cfg, vm_common_content_lib, self.args)

                vm_ras_upi_util.execute_crunch_tool()

    def check_vm_physical_numa_nodes(self):
        """
        This method is used to check the physical numa node across each VM

        return: True on success
        raise : content_exceptions.TestFail
        """
        # Copy the Numa node script to SUT
        numa_node_host_path = self._install_collateral.download_tool_to_host("GetBackingPhyNumaNode.ps1")
        self.os.copy_local_file_to_sut(numa_node_host_path, self.C_DRIVE_PATH)

        # Check NUMA info of VM
        physical_numa_node_list = []
        for vm in range(self.num_vms):
            vm_name = self.VM_OS[0] + "_" + str(vm)
            cmd_otput = self.os.execute("powershell .//GetBackingPhyNumaNode.ps1 -VmName {}".format(vm_name),
                                        self._command_timeout, cwd=self.C_DRIVE_PATH)
            self._log.debug("Numa info of VM - {}: \n{}".format(vm_name, cmd_otput.stdout))
            physical_numa_node = re.search(r'PhyNUMANode\s+:\s+(\d+)', cmd_otput.stdout, re.I)
            if physical_numa_node:
                physical_numa_node_list.append(physical_numa_node.group(1))
            else:
                raise content_exceptions.TestFail("Fail to extract the physical numa node of VM{}".format(self.VM_NAME))

        self._log.info("Physical Numa Nodes of VM's are {}".format(physical_numa_node_list))
        for node, count in Counter(physical_numa_node_list).items():
            if count > 1:
                raise content_exceptions.TestFail("More than one VM has same PHYSICAL NUMA NODE configured")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationHyperNumaAffinitySetup.main()
             else Framework.TEST_RESULT_FAIL)
