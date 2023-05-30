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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.provider.vm_provider import VMs
from src.lib.content_exceptions import *
from src.virtualization.virtualization_common import VirtualizationCommon


class VirtualizationHyperVGuestOsInstallandConfig(VirtualizationCommon):
    """
    Glassgow ID: G44773
    The purpose of this test case is making sure the creation of VMs guests on Hyper-V.
    1. Create VM.
    2. Verify VM is running.
    3. Change Basic VM configuration. Ex: Memory, Processor, and Storage.
    4. Verify VM after Config change.
    """
    TC_ID = ["G44773", "Virtualization-Hyper-V-Guest-OS-Install_and_Config"]
    BIOS_CONFIG_FILE = r"virtualization_hyper_v_guest_os_install_and_config.cfg"
    VM = [VMs.WINDOWS]
    VM_TYPE = "RS5"
    VSWITCH_NAME = "ExternalSwitch"
    ADAPTER_NAME = None
    CPU_CONFIG = 4      # in GB
    MEMORY_CONFIG = 32  # in GB

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationHyperVGuestOsInstallandConfig object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationHyperVGuestOsInstallandConfig, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opt = cfg_opts
        if self.os.os_type != OperatingSystems.WINDOWS:
            raise TestNotImplementedError("This Test case is not supported on {} OS".format(self.os.os_type))

    def prepare(self):  # type: () -> None
        """
        1. Enabling BIOS knobs VMX and VT-d
        2. Install Hyper-V module on SUT
        3. Create vSwitch from existing NIC
        """
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        self._vm_provider.install_vm_tool()
        self._vm_provider.create_bridge_network(self.VSWITCH_NAME)
        pass

    def execute(self):
        """
        1. Create VM.
        2. Verify VM is running.
        3. Change Basic VM configuration. Ex: Memory, Processor, and Storage.
        4. Verify VM after Config change.
        """
        for index in range(len(self.VM)):
            # Creates VM names dynamically according to the OS and its resources
            self._log.info("Creating VM on Hyper V")
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_hyperv_vm(vm_name, self.VM_TYPE)  # Create VM function
            self._vm_provider.wait_for_vm(vm_name)  # Wait for VM to boot
            self._vm_provider.add_vm_ethernet_adapter(vm_name, self.VSWITCH_NAME, vm_type=self.VM_TYPE)
            # Method to update CPU and Memory configuration on VM
            self._vm_provider.update_vm_num_of_cpus(vm_name, self.CPU_CONFIG)
            self._vm_provider.update_vm_memory_info(vm_name, self.MEMORY_CONFIG)
            self.verify_hyperv_vm(vm_name, self.VM_TYPE)
            self._vm_provider._shutdown_vm(vm_name)
            self._log.info("Successfully tested Memory and CPU config change on VM:{}".format(vm_name))

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationHyperVGuestOsInstallandConfig, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationHyperVGuestOsInstallandConfig.main()
             else Framework.TEST_RESULT_FAIL)
