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
# property right is granted to or conferred upon you b.y disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#################################################################################

import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions


class VirtualizationCreateVMRhelCentosWinRunTest(VirtualizationCommon):
    """
    This test case executes the following:
    1. Sets and verifies host is CentOS + Intel next
    2. Requires Fully populated memory config - 2 DPC with Max Storage (2 - PCIe gen 4 NVMe )
    3. VT-d is enabled
    4. sets intel_iommu=on,sm_on thru kernel command line parameters
    5. Creates VM.
    5. Verifies VM is running for 48 hours.

    """
    TEST_CASE_ID = "P16014084970"
    TEST_CASE_DETAILS = ["P16014084970",
                         "Virtualization - KVM - Create 200 Virtual Machines with RHEL CentOS Windows and run 48 hours"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully'"},
        2: {'step_details': "Enable INTEL_IOMMU=on on SUT",
            'expected_results': "Successfully enabled INTEL_IOMMU on SUT"},
        3: {'step_details': "Create CentOS VM's",
            'expected_results': "VM's Created Successfully"},
        4: {'step_details': "Start CentOS VM's",
            'expected_results': "Successfully started Cent OS VMs and executed for 48 hrs"}
    }

    BIOS_CONFIG_FILE = "virtualization_vm_run_test_bios.cfg"
    NUMBER_OF_CENT_VMS = [VMs.CENTOS] * 70
    NUMBER_OF_RHEL_VMS = [VMs.RHEL] * 70
    NUMBER_OF_WIN_VMS = [VMs.WINDOWS] * 60
    STORAGE_VOLUME = ["/home"]
    MAC_ID = True
    CENT_VM_TYPE = "CENTOS"
    RHEL_VM_TYPE = "RHEL"
    WIN_VM_TYPE = "WINDOWS"
    RUN_TEST_WAIT_TIME_OUT = 7200
    LIST_OF_VM_NAMES_WIN = []
    VM_WAIT_TIME_OUT = 10

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationCreateVMRhelCentosWinRunTest object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationCreateVMRhelCentosWinRunTest, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        if self.os.os_type != OperatingSystems.LINUX:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(test_log, self.os, cfg_opts)

    def prepare(self):
        self._test_content_logger.start_step_logger(1)
        super(VirtualizationCreateVMRhelCentosWinRunTest, self).prepare()
        self._test_content_logger.end_step_logger(1, True)
        self._vm_provider.create_bridge_network("virbr0")

    def execute(self):
        try:
            self._test_content_logger.start_step_logger(2)
            #  To check and enable intel_iommu by using grub menu
            if not self.enable_intel_iommu_by_kernel():
                raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")
            self._test_content_logger.end_step_logger(2, True)
            self._install_collateral.screen_package_installation()
            for index in range(len(self.STORAGE_VOLUME)):
                pool_id = "Storage" + "_" + str(index)
                self.LIST_OF_POOL.append(pool_id)
                mount_dev = self.STORAGE_VOLUME[index]
                self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
                if self._vm_provider.find_if_storage_pool_exist(pool_id):
                    self._vm_provider.delete_storage_pool(pool_id)
                self._vm_provider.create_storage_pool(pool_id, mount_dev)

            self._test_content_logger.start_step_logger(3)
            for index in range(len(self.NUMBER_OF_CENT_VMS)):
                vm_name = self.NUMBER_OF_CENT_VMS[index] + "_" + str(index)
                self._log.info(" Creating VM:{} on CentOS".format(vm_name))
                self.LIST_OF_VM_NAMES.append(vm_name)
            for index in range(len(self.NUMBER_OF_RHEL_VMS)):
                vm_name = self.NUMBER_OF_RHEL_VMS[index] + "_" + str(index)
                self._log.info(" Creating VM:{} on RhelOS".format(vm_name))
                self.LIST_OF_VM_NAMES.append(vm_name)
            for index in range(len(self.NUMBER_OF_WIN_VMS)):
                vm_name = self.NUMBER_OF_WIN_VMS[index] + "_" + str(index)
                self._log.info(" Creating VM:{} on WinOS".format(vm_name))
                self._vm_provider.destroy_vm(vm_name)
                free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                                  self.NUMBER_OF_WIN_VMS[index])
                self.create_vm_generic(vm_name, self.WIN_VM_TYPE, vm_parallel="yes", vm_create_async=True,
                                       mac_addr=True, pool_id=free_storage_pool, pool_vol_id=None,
                                       cpu_core_list=None, nw_bridge="virbr0")
                self.LIST_OF_VM_NAMES_WIN.append(vm_name)

            for index, vm_name in zip(range(len(self.LIST_OF_VM_NAMES)), self.LIST_OF_VM_NAMES):
                vm_type = vm_name.split("_")[0]
                self._log.info(" Creating VM:{}".format(vm_name))
                self._vm_provider.destroy_vm(vm_name)
                free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL, vm_type)
                self.create_vm_generic(vm_name, vm_type, vm_parallel="yes", vm_create_async=True,
                                       mac_addr=True, pool_id=free_storage_pool,
                                       pool_vol_id=None, cpu_core_list=None,
                                       nw_bridge="virbr0")
            self._test_content_logger.end_step_logger(3, True)
            self.create_vm_wait()
            time.sleep(self.VM_WAIT_TIME)
            self._test_content_logger.start_step_logger(4)
            self._log.info("Waiting for 48 Hours..")
            time.sleep(self.RUN_TEST_WAIT_TIME_OUT)
            for vm_name_win in self.LIST_OF_VM_NAMES_WIN:
                vm_status = self.get_vm_power_state(vm_name_win)
                print(vm_name_win + ": " + vm_status)
                if not vm_status.lower() == 'running':
                    raise content_exceptions.TestFail("Vm is not running after wait time.......")
                self._log.info("VM's are running.....")
                time.sleep(self.VM_WAIT_TIME_OUT)
            for vm_name in self.LIST_OF_VM_NAMES:
                vm_status = self.get_vm_power_state(vm_name)
                print(vm_name + ": " + vm_status)
                if not vm_status.lower() == 'running':
                    raise content_exceptions.TestFail("Vm is not running after wait time.......")
                self._log.info("VM's are running.....")
                time.sleep(self.VM_WAIT_TIME_OUT)
            self._test_content_logger.end_step_logger(4, True)
            return True
        except Exception as ex:
            raise Exception("Error Occurred: "+str(ex))

    def cleanup(self, return_status):  # type: (bool) -> None
        self.LIST_OF_VM_NAMES = self.LIST_OF_VM_NAMES_WIN + self.LIST_OF_VM_NAMES
        super(VirtualizationCreateVMRhelCentosWinRunTest, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationCreateVMRhelCentosWinRunTest.main()
             else Framework.TEST_RESULT_FAIL)
