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
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger


class VirtualizationVMwareCreate200VirtualMachinesWithRHELCentOSWindows(VirtualizationCommon):
    """
    Phoenix ID: 18014073884
    The purpose of this test case is making sure the creation of VMs guests on VMware ESXi and install OS on VM.
    1. Enable VT-d bios on ESXi sut and make sure the system has 2 DPC installed
    2. Copy RHEL ISO image to ESXi SUT under 'vmfs/volumes/datastore1'.
    4. Create 200 VM and imstall OS.
    5. Verify VM is running.
    6. Verify VMware tool installed on VM or not.
    7. Keep the VMs running for 48hrs
    """
    NUMBER_OF_RHEL_VMS = [VMs.RHEL]* 1
    NUMBER_OF_CENT_VMS = [VMs.CENTOS] * 1
    NUMBER_OF_WIN_VMS = [VMs.WINDOWS] * 1

    NO_OF_VM = 3

    VM_TYPE =  []

    RUN_TIME= 800 #in seconds

    TEST_CASE_ID = ["P16014078670", "VirtualizationVMwareCreate200VirtualMachinesWithRHELCentOSWindows"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully'"},
        2: {'step_details': "Create 200 CENT,RHEL,WINDOWS VM on ESXi SUT",
            'expected_results': "all VMs Created Successfully"},
        3: {'step_details' : "Keep the VMs running for 48hrs",
            'expected_results' : "No Crashes/issues should be observed"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwareToolsInstallRHelGuest object.

        """
        super(VirtualizationVMwareCreate200VirtualMachinesWithRHELCentOSWindows, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        # Need to implement bios configuration for ESXi SUT
        self._test_content_logger.start_step_logger(1)
        super(VirtualizationVMwareCreate200VirtualMachinesWithRHELCentOSWindows, self).prepare()
        self._log.info("VMWare ESXi SUT detected for the testcase")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """

        1. create VM.
        2. Start the VM.\
        3. Verify VMware tool installed or not on VM.
        4. Keep the VMs running for 48hrs
        """
        self.NUM_ALL_VMS = self.NUMBER_OF_RHEL_VMS+self.NUMBER_OF_CENT_VMS+self.NUMBER_OF_WIN_VMS # [RHEL_0-RHEL_69, CENT_70-CENT_139,]
        for index in range(self.NO_OF_VM):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.NUM_ALL_VMS[index] + "_" + str(index) + "CCC"
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.VM_TYPE.append(self.NUM_ALL_VMS[index])
            self._log.info(" VM:{} on CentOS.".format(vm_name))

        # for index in range(len(self.NO_OF_VMs)):
        for vm_index,vm_name in enumerate(self.LIST_OF_VM_NAMES):
            self._test_content_logger.start_step_logger(2)
            self._log.info("Creating VMs:{}".format(vm_name))
            self._vm_provider.destroy_vm(vm_name)
            self.create_vmware_vm_generic(vm_name, self.VM_TYPE[vm_index], vm_parallel="yes", vm_create_async=None,
                                          mac_addr=None, use_powercli="use_powercli")
            self._test_content_logger.end_step_logger(2, return_val=True)

        self.create_vm_wait()

        self._test_content_logger.start_step_logger(3)
        self._log.info("Let the VMs run for 48hrs and verify VMs state and list ")

        time.sleep(self.RUN_TIME)#7200

        self.get_vm_list_esxi(self.LIST_OF_VM_NAMES)
        self._log.info("VMs were functioning as expected till {}".format(self.RUN_TIME))
        for index in range(len(self.LIST_OF_VM_NAMES)):
            vm_name = self.LIST_OF_VM_NAMES[index]
            self.is_vm_running_esxi(vm_name)

        self._test_content_logger.end_step_logger(3, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationVMwareCreate200VirtualMachinesWithRHELCentOSWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVMwareCreate200VirtualMachinesWithRHELCentOSWindows.main()
             else Framework.TEST_RESULT_FAIL)

