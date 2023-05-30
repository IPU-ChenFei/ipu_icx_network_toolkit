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
import os
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import VmTypeAttribute

from src.provider.vm_provider import VMProvider, VMs
from src.hsio.io_virtualization.io_virtualization_common import IoVirtualizationCommon

from src.hsio.io_virtualization.virtualization_common import VirtualizationCommon


class InterleaveBaseTest(IoVirtualizationCommon):
    """
    This Class is Used as Common Class For InterleaveBaseTest
    """

    NETWORK_ASSIGNMENT_TYPE = "DDA"
    VSWITCH_NAME = "ExternalSwitch"
    ADAPTER_NAME = None
    NUM_VMS = 4  # Number of VMs each for each Interleave bios

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts,
            bios_config_file=None
    ):
        """
        Create an instance of InterleaveBaseTest

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(
            IoVirtualizationCommon,
            self).__init__(
            test_log,
            arguments,
            cfg_opts, bios_config_file_path=bios_config_file)
        self.cfg_opts = cfg_opts
        self.virtualization_obj = VirtualizationCommon(self._log, arguments, cfg_opts)
        self._vm_provider_obj = VMProvider.factory(test_log, cfg_opts, self.os)
        self.VM_OS = []
        self.LIST_OF_VM_NAMES = []

    def enable_interleave_bios_knobs(self, bios_config_file):
        """
        This method is to set the bios knobs and verify it.

        :param bios_config_file
        """
        if bios_config_file:
            bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), bios_config_file)
        self.bios_util.load_bios_defaults()
        self.bios_util.set_bios_knob(bios_config_file)  # To set the bios knob setting.
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)
        self.bios_util.verify_bios_knob(bios_config_file)

    def execute(self, bios_file_name_list=None):  # type: () -> bool
        """
        This method is to
        1. Create VM
        2. Verify VM
        3. Set the bios Knobs
        4. Verify SUT booted to OS.

        :param  bios_file_name_list
        """
        self.VM_OS = [VMs.WINDOWS]
        for index in range(self.NUM_VMS):
            self._log.info("Performing Bios Setting of file- {}".format(bios_file_name_list[index]))

            # Setting the Bios Knobs.
            self.enable_interleave_bios_knobs(bios_file_name_list[index])

            # Creates VM names dynamically according to the OS and its resources
            self._log.info("Creating VM on Hyper V")
            vm_name = self.VM_OS[0] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            try:
                self.virtualization_obj.create_hyperv_vm(vm_name, VmTypeAttribute.RS_5.value)  # Create VM function
                self._vm_provider_obj.wait_for_vm(vm_name)  # Wait for VM to boot
                # Assign Network Adapter to VM using Direct Assignment method
                self._vm_provider_obj.add_vm_network_adapter(self.NETWORK_ASSIGNMENT_TYPE, vm_name, self.ADAPTER_NAME,
                                                             self.VSWITCH_NAME)
                self.virtualization_obj.verify_hyperv_vm(vm_name, VmTypeAttribute.RS_5.value)
            except:
                raise content_exceptions.TestFail("Failed during VM creation and functionality check")
            finally:
                self._vm_provider_obj.destroy_vm(vm_name)

    def cleanup(self, return_status):
        """
        :param return_status
        """
        super(InterleaveBaseTest, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if InterleaveBaseTest.main()
             else Framework.TEST_RESULT_FAIL)
