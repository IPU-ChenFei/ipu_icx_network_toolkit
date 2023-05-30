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

from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon


class VirtualizationRHELKvmVmModifySettings(VirtualizationCommon):
    """
    Phoenix ID : 18014073452
    HPALM ID: 80290
    Glasgow ID: 56933
    The purpose of this test case is making sure Virtual Machine settings can be modified using command line tool.
    1. Create VM.
    2. Verify VM is running.
    3. Enable AutoStart in VM.
    4. Verify it.
    5. Shutdown the VM.
    5. Change the MaxMemory of the VM
    6. Start the VM and verify the MaxMemory value is changed or not.
    """
    VM = [VMs.RHEL]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationRHELKvmVmModifySettings object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationRHELKvmVmModifySettings, self).__init__(test_log, arguments, cfg_opts)

    def execute(self):
        """
        1. create VM
        2. check VM is functioning or not
        """
        self._vm_provider.create_bridge_network("virbr0")
        for index in range(len(self.VM)):
            # create VM names dynamically according to the OS
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_vm(vm_name, self.VM[index], mac_addr=True)
            self.verify_vm_functionality(vm_name, self.VM[index])
            # verify the AutoStart state is enabled or not
            current_state = self.get_auto_start_state(vm_name)
            if current_state != self.STR_ENABLE:
                self._log.info("AutoStart is on disable state, enabling AutoStart on {} VM".format(vm_name))
                # Enable AutoStart
                cmd_result = self._common_content_lib.execute_sut_cmd(self.ENABLE_AUTO_START_CMD.format(vm_name),
                                                                      "enable autostart of {}".format(vm_name),
                                                                      self._command_timeout)
                self._log.debug(cmd_result)
                # get the current VM AutoStart State
                current_state = self.get_auto_start_state(vm_name)
                if current_state != self.STR_ENABLE:
                    raise RuntimeError("Failed to enable AutoStart on {} VM".format(vm_name))
            self._log.info("Successfully enabled AutoStart on {} VM".format(vm_name))
            # shutdown VM
            self.shutdown_vm(vm_name)
            # get the current VM Max memory
            memory_size = self._common_content_configuration.get_vm_memory_size(self._sut_os, self.VM[index])
            # modify maximum memory settings
            updated_memory_size = int(memory_size) + 1000
            self._log.info("Setting Max memory to {} Mb on {} VM".format(updated_memory_size, vm_name))
            self._common_content_lib.execute_sut_cmd(self.SET_MAX_MEMORY_CMD.format(vm_name,
                                                                                    updated_memory_size),
                                                     "Set MaxMemory", self._command_timeout)
            # start VM
            self.start_vm(vm_name)
            # verify maximum memory data of VM is set or not
            max_memory = self.get_max_memory_size(vm_name).split()[0].strip()
            self._log.debug("Current max memory of the {} VM is {} Kib".format(vm_name, max_memory))
            if updated_memory_size*1024 != int(max_memory):
                raise RuntimeError("MaxMemory is not updated to {} Mib on the {} VM".format(updated_memory_size,
                                                                                            vm_name))
            self._log.info("Successfully verified the MaxMemory is set as {} MiB".format(updated_memory_size))

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationRHELKvmVmModifySettings, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationRHELKvmVmModifySettings.main()
             else Framework.TEST_RESULT_FAIL)
