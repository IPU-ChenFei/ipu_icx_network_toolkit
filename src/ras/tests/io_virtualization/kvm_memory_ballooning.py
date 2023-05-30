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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.provider.vm_provider import VMs
from src.lib.common_content_lib import CommonContentLib
from src.ras.lib.ras_upi_util import RasUpiUtil
from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import StressMprimeTool


class KVMMemoryBallooning(IoVirtualizationCommon):
    """
    GLASGOW ID: G69487

    Verify Memory ballooning works as expected

    Verify VM is still functional

    Note: Change "virtualization/{}/{}/ISO/memory_size" to 10240 in content_configuration.xml
    """
    VM = VMs.RHEL
    VM_NAME = None
    TEST_CASE_ID = ["G69487", "kvm_memory_ballooning"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new KVMMemoryBallooning object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(KVMMemoryBallooning, self).__init__(test_log, arguments, cfg_opts)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.virtualization_obj = VirtualizationCommon(self._log, arguments, cfg_opts)


    def prepare(self):  # type: () -> None
        """
        To Setup prepare
        """
        super(KVMMemoryBallooning, self).prepare()

    def execute(self):
        """
        1. create VM
        2. check VM is functioning or not
        3. Create VM
        4. Modify vm parameters
              a. set lower memory than max
              b. enable autodeflate
        5. start vm
        6. run a stress tool such as prime95
        7. verify memory is reallocated as stress tool runs and requires more memory

        :raise : content_exceptions.TestFail
        :return : True on Success
        """
        #  Create VM names dynamically according to the OS
        self.VM_NAME = self.VM
        vm_os_obj = self.create_and_verify_vm(vm_name=self.VM_NAME, vm_type=self.VM, enable_yum_repo=True)

        # Edit VM and get ip
        self.edit_vm_for_kvm_balloon(vm_os_obj, self.VM_NAME, self.MEM_2G)
        vm_ip = vm_os_obj.execute("hostname -I | awk '{print $1}'", self._command_timeout).stdout.strip("\n")

        # Opening VM Console and start prime tool
        self.start_mprime_tool_for_stress_kvm_balloon(vm_os_obj, self.VM_NAME)

        self._log.info("Checking for memory increase......")
        self.curmem = self.get_current_memory_value(self.os, self.VM_NAME)
        flag_check_for_mem_increase = self.check_for_memory_increase(self.os, self.VM_NAME, self.curmem, self.NUM_OF_CHECKS)
        if flag_check_for_mem_increase:
            self._log.info("Current Memory increases. Verified for 20 checks at 5 second intervals.......")

        try:
            cmd_output = vm_os_obj.execute(StressMprimeTool.CHECK_MPRIME_RUN_CMD, self._command_timeout).stdout
            if StressMprimeTool.STRING_TO_CHECK not in cmd_output:
                raise content_exceptions.TestFail("mprime tool is not executing")
            self._log.info("Confirming - mprime Tool was Successfully Started")
        except:
            self._log.info("Couldn't get prime tool status due to load")

        # wait for system to get stable after memory saturation
        time.sleep(self.WAIT_TIME * 20)
        vm_ping_status = self.check_vm_ping_linux(vm_os_obj, self.VM_NAME, vm_ip)

        if not (flag_check_for_mem_increase and vm_ping_status):
            return False
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
        super(KVMMemoryBallooning, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if KVMMemoryBallooning.main()
             else Framework.TEST_RESULT_FAIL)
