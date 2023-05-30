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

from src.provider.vm_provider import VMs
from src.lib.content_exceptions import *
from src.virtualization.virtualization_common import VirtualizationCommon


class PiVirtualizationVMSaveStateAndRestoreL(VirtualizationCommon):
    """
    HPALM ID: H79627-PI_Virtualization_VM Save_State_and_Restore_L
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Create VM.
    2. Verify VM is running.
    3. Save the VM configuration.
    4. Perform AC cycle.
    5. Restore the VM and verify it.
    """
    TC_ID = ["H79627-PI_Virtualization_VM Save_State_and_Restore_L"]
    VM = [VMs.RHEL]
    TEST_FILE = "test.txt"
    __BIOS_CONFIG_FILE = r"..\..\kvm_unittests_bios_knobs.cfg"
    vm_config_file = None

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiVirtualizationVMSaveStateAndRestoreL object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiVirtualizationVMSaveStateAndRestoreL, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))

    def prepare(self):
        self.bios_util.set_bios_knob(self.__BIOS_CONFIG_FILE)
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        self.bios_util.verify_bios_knob(self.__BIOS_CONFIG_FILE)

    def execute(self):
        """
        1. create VM
        2. check VM is functioning or not
        """
        for index in range(len(self.VM)):
            # create VM names dynamically according to the OS
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_vm(vm_name, self.VM[index], mac_addr=True)
            self.verify_vm_functionality(vm_name, self.VM[index])
            # create Test file in the VM
            vm_os_obj = self.create_vm_host(vm_name, self.VM[index])
            vm_os_obj.execute("touch {}".format(self.TEST_FILE), self._command_timeout, cwd=self.ROOT_PATH)
            # save current VM config
            self.vm_config_file = self._vm_provider.save_vm_configuration(vm_name)
            time.sleep(self.VM_WAIT_TIME)
            # do AC cycle
            self._log.info("Performing AC Power cycle")
            self.perform_graceful_g3()
            self._log.info("Successfully performed AC Power cycle")
            time.sleep(self.VM_WAIT_TIME)
            self._vm_provider.restore_vm_configuration(vm_name, self.vm_config_file)
            self._log.info("Waiting {} seconds for VM to boot to OS".format(self.VM_WAIT_TIME))
            time.sleep(self.VM_WAIT_TIME)
            # verify VM is running or not
            if self.get_vm_power_state(vm_name) != self.STR_RUNNING:
                raise TestFail("{} VM is not running".format(vm_name))
            self._log.info("Successfully verified {} VM is running".format(vm_name))
            self._log.info("Checking the file presence")
            cmd_result = vm_os_obj.execute("ls", self._command_timeout, cwd=self.ROOT_PATH)
            self._log.debug(cmd_result.stdout)
            self._log.error(cmd_result.stderr)
            if self.TEST_FILE not in cmd_result.stdout:
                raise TestFail("Failed to restore the VM {}".format(vm_name))
            self._log.info("Test File {} is present under the {} VM, hence {} VM restored successfully".format(
                           self.TEST_FILE, vm_name, vm_name))
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        self._log.info("Deleting the {} config file".format(self.vm_config_file))
        self._common_content_lib.execute_sut_cmd("rm -rf {}".format(self.vm_config_file), "delete vm config file",
                                                 self._command_timeout)
        self._log.info("Successfully deleted the {} config file".format(self.vm_config_file))
        super(PiVirtualizationVMSaveStateAndRestoreL, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiVirtualizationVMSaveStateAndRestoreL.main()
             else Framework.TEST_RESULT_FAIL)
