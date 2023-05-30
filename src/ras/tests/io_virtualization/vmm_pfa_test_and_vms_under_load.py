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

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.install_collateral import InstallCollateral

from src.lib.common_content_lib import CommonContentLib
from src.ras.lib.ras_upi_util import RasUpiUtil
from src.ras.lib.ras_einj_common import RasEinjCommon
from src.provider.vm_provider import VMs
from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon
from src.lib import content_exceptions


class VmmPfaTestAndVmsUnderLoadLinux(IoVirtualizationCommon):
    """
    While running stress on multiple VMs, Run PFA test on VMM host. Verify VMs are still functional.
    """

    bios_file_name = "pfa_bios_knobs.cfg"
    VM = [VMs.RHEL]

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts
    ):
        """
        Create an instance of VmmPfaTestAndVmsUnderLoadLinux

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(
            VmmPfaTestAndVmsUnderLoadLinux,
            self).__init__(
            test_log,
            arguments,
            cfg_opts, self.bios_file_name)
        self._ras_einj_util = RasEinjCommon(self._log, self.os, self._common_content_lib,
                              self._common_content_configuration, self.ac_power, cfg_opts)

    def prepare(self):  # type: () -> None
        """
        This method is to execute prepare.
        """
        super(VmmPfaTestAndVmsUnderLoadLinux, self).prepare()

    def execute(self):  # type: () -> bool
        """
        This method is to
        1. Create VM
        2. Verify VM
        3. Set the bios Knobs
        4. Verify SUT booted to OS.

        """
        for index in range(self.num_vms):
            #  Create VM names dynamically according to the OS
            vm_name = self.VM[0] + "_" + str(index)

            self.create_and_verify_vm(vm_name, self.VM[0], crunch_tool=True, enable_yum_repo=True)

        ret_val = self._ras_einj_util.einj_inject_and_check(error_type=self._ras_einj_util.EINJ_MEM_CORRECTABLE)
        if not ret_val:
            raise content_exceptions.TestFail("Failed during PFA Test")

        for index in range(self.num_vms):
            vm_name = self.VM[0] + "_" + str(index)
            self.virtualization_obj.verify_vm_functionality(vm_name, self.VM[0])

        return True

    def cleanup(self, return_status):
        for index in range(self.num_vms):
            vm_name = self.VM[0] + "_" + str(index)
            self._vm_provider_obj.destroy_vm(vm_name)
        super(VmmPfaTestAndVmsUnderLoadLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VmmPfaTestAndVmsUnderLoadLinux.main()
             else Framework.TEST_RESULT_FAIL)
