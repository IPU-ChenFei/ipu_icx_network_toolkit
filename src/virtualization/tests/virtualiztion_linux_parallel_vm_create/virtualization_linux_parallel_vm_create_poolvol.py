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


class VirtualizationLinuxKvmParallelVmCreationPoolVol(VirtualizationCommon):
    """
    HPALM ID: 80292
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Install virt-install if not present.
    2. Copy RHEL ISO image to SUT under '/var/lib/libvirt/images'.
    4. Create VM.
    5. Verify VM is running.
    """
    NUMBER_OF_VMS = 8
    VM = [VMs.CENTOS] * NUMBER_OF_VMS

    VM_TYPE = "CENTOS"
    STORAGE_VOLUME = ["/home"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationLinuxKvmParallelVmCreationPoolVol object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationLinuxKvmParallelVmCreationPoolVol, self).__init__(test_log, arguments, cfg_opts)

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

        for index, vm_name in enumerate(self.LIST_OF_VM_NAMES):
            # destroy with default values
            self._vm_provider.destroy_vm(vm_name)
            self._log.info(" Destroy VM:{} on CentOS Called.".format(vm_name))

        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)

        vm_disk_size = 24 #GB
        pool_index = 0
        for pool_vol_index, vm_name in enumerate(self.LIST_OF_VM_NAMES):
            if self._vm_provider.find_storage_pool_available_size(self.LIST_OF_POOL[pool_index]) > (vm_disk_size*1073741824):
                # create vol per VM
                pool_id = self.LIST_OF_POOL[pool_index]
                pool_vol_id = "Storage" + "_" + str(index) + "_" + "Vol" + str(pool_vol_index)
                if self._vm_provider.find_if_storage_pool_vol_exist(pool_id, pool_vol_id):
                    self._vm_provider.delete_storage_pool_vol(pool_id, pool_vol_id)
                self._vm_provider.create_storage_pool_vol(pool_id, pool_vol_id, vm_disk_size)
                self.LIST_OF_POOL_VOL[pool_id].append(pool_vol_id)
            else:
                pool_index = pool_index+1
                if pool_index == len(self.LIST_OF_POOL):
                    self._log.info("Storage Space exhausted, total pools {}".format(pool_index))

        vm_sut_obj_list = []

        vm_index = 0
        pool_index = 0
        vol_index = 0
        for index, vm_name in enumerate(self.LIST_OF_VM_NAMES):
            # create with default values
            self._vm_provider.destroy_vm(vm_name, vm_resource_keep_safe = "yes")
            # free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
            #                                                                   self.VM_TYPE)
            # free_storage_pool = self.get_storage_pool_using_vol(pool_vol_id)
            pool_id = self.LIST_OF_POOL[pool_index]
            pool_vol_id = self.LIST_OF_POOL_VOL[pool_id][vol_index]

            self.create_vm_generic(vm_name, self.VM_TYPE, vm_parallel="yes", vm_create_async=None, mac_addr=True,
                                   pool_id=pool_id,
                                   pool_vol_id=pool_vol_id, cpu_core_list=None)
            self._log.info(" Create VM:{} on CentOS Called.".format(vm_name))
            vol_index = vol_index + 1
            if len(self.LIST_OF_POOL_VOL[pool_id]) == vol_index:
                pool_index = pool_index + 1
                if len(self.LIST_OF_POOL) == pool_index:
                    self._log.info(" Storage Pool Volume exhausted {} {}.".format(pool_index, vol_index))
                    break
                else:
                    vol_index = 0

        self.create_vm_wait()
        self._log.info("Wait for VMs to be stable for {} sec.".format(self.VM_WAIT_TIME))
        time.sleep(self.VM_WAIT_TIME)

        self._log.info("Verify If VMs created are stable and working...")
        for vm_name in self.LIST_OF_VM_NAMES:
            # vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            self._log.info(" Created VM:{} on CentOS successfully.".format(vm_name))

        self.cleanup_storage_pool_vol()

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationLinuxKvmParallelVmCreationPoolVol, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationLinuxKvmParallelVmCreationPoolVol.main()
             else Framework.TEST_RESULT_FAIL)
