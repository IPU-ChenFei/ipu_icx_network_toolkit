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

from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon


class VirtualizationLinuxKvmParallelVmCreation(VirtualizationCommon):
    """
    HPALM ID: 80292
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Install virt-install if not present.
    2. Copy RHEL ISO image to SUT under '/var/lib/libvirt/images'.
    4. Create VM.
    5. Verify VM is running.
    """
    NUMBER_OF_VMS = 2
    VM = [VMs.CENTOS]*NUMBER_OF_VMS
    VM_TYPE = "CENTOS"
    STORAGE_VOLUME = ["/home"]
    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationLinuxKvmParallelVmCreation object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationLinuxKvmParallelVmCreation, self).__init__(test_log, arguments, cfg_opts)

    def execute(self):
        """
        1. create VM
        2. check VM is functioning or not
        """
        self._install_collateral.screen_package_installation()

        self._vm_provider.create_bridge_network("virbr0")

        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on CentOS.".format(vm_name))
            
        for index in range(len(self.STORAGE_VOLUME)):
                pool_id = "Storage" + "_" + str(index)
                self.LIST_OF_POOL.append(pool_id)
                mount_dev = self.STORAGE_VOLUME[index]
                self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
                if self._vm_provider.find_if_storage_pool_exist(pool_id):
                    self._vm_provider.delete_storage_pool(pool_id)
                self._vm_provider.create_storage_pool(pool_id, mount_dev)

        # for pool_index, vm_name in enumerate(self.LIST_OF_VM_NAMES):
        #     for index, pool_id in enumerate(self.LIST_OF_POOL):
        #         # create vol per VM
        #         if self._vm_provider.find_if_storage_pool_exist(pool_id):
        #             self._vm_provider.delete_storage_pool(pool_id)
        #         self._vm_provider.create_storage_pool(pool_id, mount_dev)
        #         self.LIST_OF_POOL_VOL.append(pool_id)



        vm_sut_obj_list = []

        vm_index = 0
        for index, vm_name in enumerate(self.LIST_OF_VM_NAMES):
            # create with default values
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                              self.VM_TYPE)
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_parallel="yes", vm_create_async=True, mac_addr=True, pool_id=free_storage_pool,
                                   pool_vol_id=None, cpu_core_list=None, nw_bridge="virbr0")
            self._log.info(" Create VM:{} on CentOS Called.".format(vm_name))

        self.create_vm_wait()
        # time.sleep(900)
        for vm_name in self.LIST_OF_VM_NAMES:
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            self._log.info(" Created VM:{} on CentOS successfully.".format(vm_name))

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationLinuxKvmParallelVmCreation, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationLinuxKvmParallelVmCreation.main()
             else Framework.TEST_RESULT_FAIL)
