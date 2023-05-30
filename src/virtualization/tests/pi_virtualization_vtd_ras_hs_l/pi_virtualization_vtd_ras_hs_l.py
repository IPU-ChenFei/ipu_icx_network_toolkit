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
import threading
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.lib.common_content_lib import CommonContentLib
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger


class VirtualizationVtdRasHsL(VirtualizationCommon):
    """
    Phoenix ID: 18014075031
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Install virt-install if not present.
    2. Copy CentOS ISO image to SUT under '/var/lib/libvirt/images'.
    4. Create VM.
    5. Verify VM is running.
    """
    TEST_CASE_ID = ["P18014075031", "PI_Virtualization_VTd_RAS_HS_L"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Enable IOMMU using kernel command line params in SUT',
            'expected_results': 'Kernel command line params updated to enable iommu in SUT'},
        2: {'step_details': 'Create the VM using storage pool',
            'expected_results': 'VM creation successfully done'},
        3:  {'step_details': "Get the Network adapter device name in VM",
             'expected_results': "Network adapter name in VM obtained successfully"},
        4: {'step_details': "Execute the PING test from VM to SUT",
             'expected_results': "PING test passed"},
        5: {'step_details': "Copy File from SUT to VM",
            'expected_results': "File Copied Successfully from SUT to VM using SCP command"},
        6: {'step_details': "Check if copied file exists in VM",
            'expected_results': "File is found in VM"}
    }

    NUMBER_OF_VMS = 1
    VM = [VMs.CENTOS]*NUMBER_OF_VMS
    VM_TYPE = "CENTOS"
    STORAGE_VOLUME = ["/home"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVtdRasHsL object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationVtdRasHsL, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._cfg_opt = cfg_opts
        self._test_log = test_log

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.

        :return: None
        """
        # Check the for the Linux OS in the SUT
        if self.os.os_type == OperatingSystems.LINUX:
            self._log.info("We have Linux OS for test case... proceeding further..")
        else:
            raise content_exceptions.TestFail("Target is not booted with Linux")
        super(VirtualizationVtdRasHsL, self).prepare()
        self._vm_provider.create_bridge_network("virbr0")

    def execute(self):
        """
        This function executes the below steps:
        1. Enable intel IOMMU.
        2. Create VM and verify its running.
        3. get network adapter name from vm and run dhclient.
        4. ping SUT from VM.
        5. Copy file from SUT to VM and verify the file existence.
        """
        self._test_content_logger.start_step_logger(1)
        self.enable_intel_iommu_by_kernel()
        self._test_content_logger.end_step_logger(1, True)
        self._test_content_logger.start_step_logger(2)
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on CentOS.".format(vm_name))
            # create with default values
            self._vm_provider.destroy_vm(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL,
                                                                                  self.VM_TYPE)
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_create_async=None, mac_addr=True,
                                   pool_id=free_storage_pool,
                                   pool_vol_id=None, nw_bridge="virbr0")
            self._test_content_logger.end_step_logger(2, True)
            self._test_content_logger.start_step_logger(3)
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._test_log, vm_os_obj, self._cfg_opt)

            network_interface_name_vm = self._vm_provider._get_current_network_interface(
                common_content_lib_vm_obj)
            common_content_lib_vm_obj.execute_sut_cmd("dhclient {}".format(
                network_interface_name_vm), "Executing dhclient for VM", self._command_timeout)
            self._test_content_logger.end_step_logger(3, True)
            self._test_content_logger.start_step_logger(4)
            sut_ip = self.sut_ip
            self._log.info("pinging {} from VM".format(sut_ip))
            ping_result = common_content_lib_vm_obj.execute_sut_cmd("ping -c 4 {}".format(sut_ip),
                                                                    "ping -c 4 {}".format(sut_ip),
                                                                    self._command_timeout)
            self._log.info("Ping result data :\n{}".format(ping_result))
            self._log.info("Successfully pinged the SUT from VM")
            self._test_content_logger.end_step_logger(4, True)
            self._test_content_logger.start_step_logger(5)
            file_name = self.TEST_VM_FILE_NAME

            file_path = self.ROOT_PATH + "/" + self.TEST_VM_FILE_NAME
            self._common_content_lib.execute_sut_cmd("touch {}".format(file_path),
                                                     "create file", self._command_timeout)
            self._log.info("Copying the Test file to VM")
            vm_test_file_host_path = self._install_collateral.download_tool_to_host(file_name)
            vm_os_obj.copy_local_file_to_sut(vm_test_file_host_path, self.ROOT_PATH)
            self._test_content_logger.end_step_logger(5, True)
            self._test_content_logger.start_step_logger(6)
            no_of_file = common_content_lib_vm_obj.execute_sut_cmd("ls -1 {} | grep -i {}|wc -l".format(
                                                                        self.ROOT_PATH, file_name),
                                                                        "list of all files",
                                                                        self._command_timeout)
            if no_of_file == 1:
                self._log.info("File copied Successfully and verified in VM")
            else:
                self._log.error("Error in copying the file from SUT to VM")
            self._test_content_logger.end_step_logger(6, True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationVtdRasHsL, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVtdRasHsL.main()
             else Framework.TEST_RESULT_FAIL)
