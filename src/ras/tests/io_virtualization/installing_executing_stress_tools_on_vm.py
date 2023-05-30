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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.provider.vm_provider import VMs
from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib import content_exceptions


class InstallingExecutingStressToolsOnVM(IoVirtualizationCommon):
    """
    GLASGOW ID: G67412

    Download, install and execute stress tool to the VM for running stress

    Verify VM is still functional
    """
    VM = VMs.RHEL
    VM_NAME = None
    # BIOS_CONFIG_FILE = "vtd_bios_knobs.cfg"
    TEST_CASE_ID = ["G67412", "installing_executing_stress_tools_on_vm"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new InstallingExecutingStressToolsOnVM object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(InstallingExecutingStressToolsOnVM, self).__init__(test_log, arguments, cfg_opts)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.virtualization_obj = VirtualizationCommon(self._log, arguments, cfg_opts)
        
    def prepare(self):  # type: () -> None
        """
        To Setup prepare
        """
        super(InstallingExecutingStressToolsOnVM, self).prepare()

    def execute(self):
        """
        1. create VM
        2. check VM is functioning or not
        3. Run crunch stress tool on VM.
        4. Run libquantum stress tool on VM.
        5. Run prime95 stress tool on VM.

        :raise : content_exceptions.TestFail
        :return : True on Success
        """

        #  Create VM names dynamically according to the OS
        self.VM_NAME = self.VM

        vm_os_obj = self.create_and_verify_vm(vm_name=self.VM_NAME, vm_type=self.VM, crunch_tool=True,
                                              enable_yum_repo=True, libquantum_tool=True, mprime_tool=True)

        if not vm_os_obj.is_alive():
            raise content_exceptions.TestFail("VM is not alive after stress tools")
        self._log.info("VM is alive after stress tool runs as expected")

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        1. Destroy Created VM.
        """
        try:
            self.virtualization_obj.vm_provider.destroy_vm(self.VM_NAME)
        except Exception as ex:
            raise content_exceptions.TestFail("Unable to Destroy the VM")
        super(InstallingExecutingStressToolsOnVM, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if InstallingExecutingStressToolsOnVM.main()
             else Framework.TEST_RESULT_FAIL)
