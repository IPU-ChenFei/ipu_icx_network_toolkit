#!/usr/bin/env python
##########################################################################
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
##########################################################################

import sys
import os

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.test_content_logger import TestContentLogger
from src.network.networking_common import NetworkingCommon
from src.virtualization.virtualization_common import VirtualizationCommon
from src.provider.vm_provider import VMs


class FortvilleSriovWindows(NetworkingCommon, VirtualizationCommon):
    """
    Phoenix ID : 18014067835-PI_Networking_Fortville_SRIOV_W
    This Class is Used to Generate Fortville Virtual Network Adapters and assign Static IP and IPv6 Address to each
    Virtual Network Adapter Generated and Ping them. Reset Count of Virtual Network Adapters to there Default Value.
    """
    TEST_CASE_ID = ["18014067835", "PI_Networking_Fortville_SRIOV_W"]
    BIOS_CONFIG_FILE = 'hyperv_stress_bios_knobs.cfg'
    VM_TYPE = "RS5"
    VM = [VMs.WINDOWS]
    NETWORK_ASSIGNMENT_TYPE = "SRIOV"
    ETHERNET = "Ethernet 2"

    STEP_DATA_DICT = {
        1: {'step_details': "Install Hyper-V in SUT",
            'expected_results': "Hyper-V to be installed successfully"},
        2: {'step_details': "Install VM on the SUT",
            'expected_results': "Windows VM is installed Successfully"},
        3: {'step_details': "Assign SRIOV Network to the VM",
            'expected_results': "Assignment of SRIOV is successful and vm is pinging"},
        4: {'step_details': "Copy Fortville driver to VM and install it.",
            'expected_results': "Fortville driver installation is successfully"},
        }

    NUMBER_OF_VIRTUAL_ADAPTERS = 1

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of FortvilleSriovWindows
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(FortvilleSriovWindows, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.bios_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)

    def prepare(self):  # type: () -> None
        """
        PreChecks if the System is installed with fortvillle Network Adapter.
        """
        try:
            self.bios_util.load_bios_defaults()
            self.bios_util.set_bios_knob(bios_config_file=self.bios_file_path)
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
            self.bios_util.verify_bios_knob(bios_config_file=self.bios_file_path)
        except Exception as ex:
            self.os.wait_for_os(self.reboot_timeout)

        self._test_content_logger.start_step_logger(1)
        self._vm_provider.install_vm_tool()
        self._test_content_logger.end_step_logger(1, True)

    def execute(self):  # type: () -> bool
        """
        This Method is Used to.
        1) Generate Given Number of Virtual Network Adapters and Verify
        2) Assign Static Ip Address to each Virtual Network Adapter generated and Ping them.
        3) Assign Static IPv6 Address to each Virtual Network Adapter generated and Ping them.
        4) Reset Virtual Network Adapter Count to Its Default Value
        :return: True if all steps executes and getting the status as expected.
        """
        self._test_content_logger.start_step_logger(2)
        self._log.info("Creating VM on Hyper V")
        vm_name = self.VM[0] + "_" + str(0)
        self.LIST_OF_VM_NAMES.append(vm_name)
        self.create_hyperv_vm(vm_name, self.VM_TYPE)  # Create VM function
        self._vm_provider.wait_for_vm(vm_name)  # Wait for VM to boot

        self._test_content_logger.end_step_logger(2, True)

        self._test_content_logger.start_step_logger(3)
        # Assigning SRIOV network to VM
        self._vm_provider.add_vm_network_adapter(self.NETWORK_ASSIGNMENT_TYPE, vm_name,physical_adapter_name=self.ETHERNET,
                                             switch_name=self.VSWITCH_NAME)
        self._vm_provider.add_vm_ethernet_adapter(vm_name, self.VSWITCH_NAME)
        self.verify_hyperv_vm(vm_name, self.VM_TYPE)
        self._test_content_logger.end_step_logger(3, True)

        self._test_content_logger.start_step_logger(4)
        # Installing driver ini files in VM
        self.create_install_driver_vm_object(vm_name)
        self._test_content_logger.end_step_logger(4, True)

        return True

    def cleanup(self, return_status):
        """
        This Method is Used to Install Fortville driver and Reset Virtual Network Adapters to their Default Value.
        """
        super(ContentBaseTestCase, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if FortvilleSriovWindows.main()
             else Framework.TEST_RESULT_FAIL)
