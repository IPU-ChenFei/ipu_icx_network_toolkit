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


class EsxiVmCreate(VirtualizationCommon):
    """
    VMX + VT-d + Stress/Stability

    The purpose of this test case is making sure the creation of 200 VMs guest on KVM Hypervisor, and test
    basic functionality ex. VM Power cycle, MLC workload and SRIOV workload.

    cmd for vmtool
    ./setup64.exe /S /v "/qn msi_args ADDLOCAL=ALL"
    """
    NUMBER_OF_VMS = 1
    VM = [VMs.RHEL]
    VM_TYPE = "RHEL"
    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new KvmVmResetStress object.

        """
        super(EsxiVmCreate, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        #Need to implement bios config
        pass

    def execute(self):

        if self.os.os_type != OperatingSystems.ESXI:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._log.info("VMWare esxi detected")
        for index in range(self.NUMBER_OF_VMS):
            vm_name = self.VM[index] + "_" + str(index)
            self.create_vm(vm_name, self.VM_TYPE)

    def cleanup(self, return_status):  # type: (bool) -> None
        super(EsxiVmCreate, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if EsxiVmCreate.main()
             else Framework.TEST_RESULT_FAIL)