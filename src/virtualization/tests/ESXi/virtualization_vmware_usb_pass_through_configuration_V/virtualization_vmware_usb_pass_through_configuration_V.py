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
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.common_content_lib import CommonContentLib

from src.lib.test_content_logger import TestContentLogger

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon


class VirtualizationUSBPassThroughV(VirtualizationCommon):
    """
    Phoenix ID: P18014074344
    The purpose of this test case is making sure the creation of VMs
    guests on VMware ESXi and Perform USB passthrough.

    1. Enable VT-d bios on ESXi sut.
    2. Copy RHEL ISO image to ESXi SUT under 'vmfs/volumes/datastore1'.
    4. Create VM.
    5. Verify VM is running.
    6. Verify VMware tool installed on VM or not.
    7. Enable USB passthrough and verify USB in VM.
    """
    NUMBER_OF_VMS = 1
    VM = [VMs.RHEL] * 1
    VM_TYPE = "RHEL"
    TEST_CASE_ID = ["P18014074344", "PI_Virtualization_USBPass-through_V"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully"},
        2: {'step_details': "Check the USB device in sut present or not ",
            'expected_results': "the USB device is present in sut"},
        3: {'step_details': "Create Rhel VM on ESXi SUT",
            'expected_results': "VM Created Successfully"},
        4: {'step_details': "Verify VMware Tool installed on VM or not",
            'expected_results': "Successfully verified VMware Tool on VM"},
        5: {'step_details': "Enable usb passthrough in sut",
            'expected_results': "Enabled usb passthrough in sut successfully"},
        6: {'step_details': "Executing pass through command with vm_id and usb device name",
            'expected_results': "The usb passthrough in vm got executed succesfully"},
        7: {'step_details': "Verifying the usb passthrough in vm",
            'expected_results': "The usb passthrough in vm verified successfully"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationUSBPassThroughV object.

        """
        super(VirtualizationUSBPassThroughV, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # Need to implement bios configuration for ESXi SUT
        self._test_content_logger.start_step_logger(1)
        if self.os.os_type != OperatingSystems.ESXI:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._log.info("VMWare ESXi SUT detected for the testcase")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. create VM.
        2. Start the VM.
        3. Verify VMware tool installed or not on VM.
        4. Get VM and Device information.
        5. enable usb passthrough in vm.
        6. Pass through USB and verify USB information in VM.
        """
        vm_id = 0

        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on ESXi.".format(vm_name))

        vm_sut_obj_list = []
        vm_index = 0
        for vm_name in self.LIST_OF_VM_NAMES:
            self._test_content_logger.start_step_logger(3)
            self._vm_provider.destroy_vm(vm_name)
            self.create_vmware_vm(vm_name, self.VM_TYPE, mac_addr=True)
            self._test_content_logger.end_step_logger(3, return_val=True)
            self._test_content_logger.start_step_logger(4)
            self._vm_provider.install_vmware_tool_on_vm(vm_name)
            self._test_content_logger.end_step_logger(4, return_val=True)
            vm_id = self._vm_provider.get_esxi_vm_id_data(vm_name)
            vm_os_obj = self.create_esxi_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            device_data = self._vm_provider.enumerate_usb_from_esxi()
            device_info = str(int(device_data[1]))\
                          + ":" + str(int(device_data[3].split(":")[0])) \
                          + ":" + device_data[5]
            usb_device_id = device_data[5].split(":")
            usb_device_id = ("0x" + usb_device_id[0] + ":0x" + usb_device_id[1])
            self._test_content_logger.start_step_logger(5)
            self._vm_provider.enable_disable_usb_passthrough(device_info, enable=True)
            self._test_content_logger.end_step_logger(5, return_val=True)
            self._test_content_logger.start_step_logger(6)
            self._vm_provider.storage_device_vm_passthrough(vm_id, usb_device_id)
            self._test_content_logger.end_step_logger(6, return_val=True)
            self._test_content_logger.start_step_logger(7)
            time.sleep(20)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self._vm_provider.verify_usb_passthrough_in_vm(vm_name, common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(7, return_val=True)
        return True

    def cleanup(self, return_status):
        super(VirtualizationUSBPassThroughV, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationUSBPassThroughV.main()
             else Framework.TEST_RESULT_FAIL)
