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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger


class VirtualizationVmwareToolsInstallLinuxGuest(VirtualizationCommon):
    """
    Phoenix ID: 18014072644
    The purpose of this test case is making sure the creation of VMs guests on VMware ESXi.
    1. Enable VT-d bios on ESXi sut.
    2. Copy RHEL ISO image to ESXi SUT under 'vmfs/volumes/datastore1'.
    4. Create VM.
    5. Verify VM is running.
    6. Verify VMware tool installed on VM or not.
    """
    VM = [VMs.RHEL]
    VM_TYPE = "RHEL"
    TEST_CASE_ID = ["P18014072644", "Virtualization_VMware_Tools_Install_on_a_Linux_Guest"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully'"},
        2: {'step_details': "Create RHel VM on ESXi SUT",
            'expected_results': "VM Created Successfully"},
        3: {'step_details': "Verify VMware Tool installed on VM or not",
            'expected_results': "Successfully verified VMware Tool on VM"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwareToolsInstallRHelGuest object.

        """
        super(VirtualizationVmwareToolsInstallLinuxGuest, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)

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
        """
        for index in range(len(self.VM)):
            self._test_content_logger.start_step_logger(2)
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_vmware_vm(vm_name, self.VM_TYPE, mac_addr=True)
            self._test_content_logger.end_step_logger(2, return_val=True)
            self._test_content_logger.start_step_logger(3)
            self._vm_provider.install_vmware_tool_on_vm(vm_name)
            self._test_content_logger.end_step_logger(3, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationVmwareToolsInstallLinuxGuest, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmwareToolsInstallLinuxGuest.main()
             else Framework.TEST_RESULT_FAIL)
