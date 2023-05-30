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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon
from src.memory.tests.memory_cr.apache_pass.provisioning.pi_cr_2lm_osboot_l_w import PICR2lmOsBoot
from src.provider.partition_provider import PartitionProvider


class PICR2lmMemoryAppdirectStorgeCheck(CrProvisioningTestCommon):
    """
    HP QC  ID: 79524 (Linux) / 82159 (Windows)
    2LM Basic functionality check,verify new created volume healthy after formatting.
    """

    BIOS_CONFIG_FILE = "pi_cr_2lm_appdirect_basicflow_bios_knob.cfg"
    TEST_CASE_ID = "H79524/H82159-pi_cr_2lm_memory_appdirect_storage_resource_check"
    return_value = []
    PARTITION_TYPE = "primary"
    FILE_SYSTEM = "ntfs"

    step_data_dict = {1: {'step_details': 'Clear OS logs and Set the bios knobs, Restart the system, Boot to OS '
                                          'properly and verify the bios knobs, Check the detected DIMM in system.',
                          'expected_results': 'Clear ALL the system Os logs and BIOS setting done, Successfully boot '
                                              'to OS & Verified the bios knobs, Display all of installed DIMMs with '
                                              'correct attributes values Capacity: same as config & Health '
                                              'state:Healthy'},
                      2: {'step_details': 'Create Memory Allocation Goal on dimm,  reboot the system and goal '
                                          'verification',
                          'expected_results': 'AppDirect1Size is nearly as same  as DIMM capacity and ActionRequired '
                                              'is 0, system successfully boot to OS and goal is successfully verified'},
                      3: {'step_details': 'Check if CPS DIMM memory resource allocation is correct.',
                          'expected_results': 'AppDirectCapacity is nearly as same as dimm capacity'},
                      4: {'step_details': 'Verify if the region exists.',
                          'expected_results': 'Region exists with assigned ID, FreeCapacity = capacity'},
                      5: {'step_details': 'Create Storage namespace on AppDirect with max available namespace size, '
                                          'which should cover capacity of dimm',
                          'expected_results': 'The correct raw disk can be created after the namespace configured'},
                      6: {'step_details': 'Check the namespace created just now.',
                          'expected_results': 'Name spaces created successfully.'},
                      7: {'step_details': 'Create 2GB of primary partition and formatting with ntfs file system',
                          'expected_results': 'Created 2GB primary partition and ntfs file system'},
                      8: {'step_details': 'Create 15GB of primary partition and format with ntfs file system .',
                          'expected_results': 'Created 15Gb primary partition and formatted with ntfs file system'},
                      9: {'step_details': 'Delete 2GB and 15 GB partition.Create full size of primary partition and '
                                          'format with ntfs file system .',
                          'expected_results': 'Deleted 2GB and 15GB primary partition.'
                                              'Created full size of primary partition and formatted with ntfs file'
                                              ' system'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PICR2lmMemoryAppdirectStorgeCheck object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PICR2lmMemoryAppdirectStorgeCheck, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

        # For calling the reference test case as per steps.
        self._pi_cr_2lm_os_boot = PICR2lmOsBoot(self._log, arguments, cfg_opts)

        self._partition_provider = PartitionProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self._os)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        1. Verify dimm population is as per the configuration of this test case.
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._pi_cr_2lm_os_boot.prepare()
        self._pi_cr_2lm_os_boot.execute()

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Create goal memory mode = 50 and Appdirect = 50.
        2. Verify the provisioning with memory capacity.
        3. Check that detected DIMM in system has correct attribute values.
        4. Create and verify Namespace.
        5. Create partition for the pmem device.
        6. Create ntfs file system.
        7. Create mount point for the pmem device

        :return: True, if the test case is successful.
        :raise: None
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        # Get the DIMM information
        dimm_show = self._ipmctl_provider.get_memory_dimm_information()

        # Get available name space info
        namespace_output = self._ipmctl_provider.dcpmm_get_disk_namespace()

        # Clear the namespaces if exists
        self._ipmctl_provider.dcpmm_check_disk_namespace_initilize(namespace_output)

        self._ipmctl_provider.delete_pcd_data()
        self._log.info("Deleted pcd data ....")

        # Need a reboot after deleting the pcd data
        self._common_content_lib.perform_os_reboot(self._reboot_timeout)

        #  Configure the capacity on all installed DCPMM(s) with 50% as persistent memory and 50% Appdirect
        dcpmm_disk_goal = self._ipmctl_provider.dcpmm_configuration(
            cmd=r"ipmctl create -f -goal MemoryMode=50 PersistentMemoryType=appdirect",
            cmd_str="with 50% persistent and 50% volatile memory")

        #  Verify the mode provisioning
        self.return_value.append(
            self.verify_app_direct_mode_provisioning(mode="pmem", mode_percentage=50,
                                                     total_memory_result_data=dimm_show,
                                                     app_direct_result_data=dcpmm_disk_goal))

        self.return_value.append(
            self.verify_app_direct_mode_provisioning(mode="mem", mode_percentage=50,
                                                     total_memory_result_data=dimm_show,
                                                     app_direct_result_data=dcpmm_disk_goal))

        #  Restart the SUT
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._os.wait_for_os(self._reboot_timeout)

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        # Get the present memory resources
        mem_resources_output = self._ipmctl_provider.show_mem_resources()

        self._memory_common_lib.verify_provisioned_appdirect_capacity(mem_resources_output, r"AppDirect.*", 50)
        self._memory_common_lib.verify_provisioned_appdirect_capacity(mem_resources_output, r"Volatile.*", 50)

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        # To get region information with param "-a"
        region_data_with_a_param = self._ipmctl_provider.show_all_region_data()

        # To get region information
        region_data = self._ipmctl_provider.show_region()

        # To verify the Iset ID attribute
        self.return_value.append(self._memory_common_lib.verify_iset_id_existence(region_data))

        # To verify the default region attributes
        self._memory_common_lib.verify_region_default_attribs_mode(region_data_with_a_param)

        #  Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=all(self.return_value))

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        # Get the list of all regions
        region_data_list = self._ipmctl_provider.dcpmm_get_pmem_unused_region()

        # Create namespace for each regionX
        new_created_namespace_list = self._ipmctl_provider.dcpmm_new_pmem_disk(region_data_list)

        # Step logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=True)

        # Step logger start for Step 6
        self._test_content_logger.start_step_logger(6)

        # Show present namespaces
        namespace_info = self._ipmctl_provider.dcpmm_get_disk_namespace()

        # Verify namespace presence
        self.return_value.append(self.verify_pmem_device_presence(namespace_info))

        # To get the DCPMM disk list that needs to be partitioned
        disk_list = self._partition_provider.get_dcpmm_disk_list(new_created_namespace_list)

        self._log.info("{} DCPMM device(s) attached to this system board {}.".format(len(disk_list), disk_list))

        # Step logger end for Step 6
        self._test_content_logger.end_step_logger(6, return_val=all(self.return_value))

        # Step logger start for Step 7
        self._test_content_logger.start_step_logger(7)

        self._partition_provider.create_dcpmm_gpt_format(disk_list)

        # Create partition with memory size 2GB
        self._partition_provider.create_partition_dcpmm_disk(
            convert_type=self.FILE_SYSTEM, disk_lists=disk_list, mode=self.PARTITION_TYPE, size='2GB')

        # Disk information after creating 2GB primary partition and file system
        disk_info = self._partition_provider.get_disk_partition_information(disk_list)

        # Step logger end for step 7
        self._test_content_logger.end_step_logger(7, return_val=disk_info)

        # Step logger start for Step 8
        self._test_content_logger.start_step_logger(8)

        # Create primary partition of size 15GB
        self._partition_provider.create_partition_dcpmm_disk(
            convert_type=self.FILE_SYSTEM, disk_lists=disk_list, mode=self.PARTITION_TYPE, size='15GB')

        # Disk information after creating 15GB partition and file system
        disk_info = self._partition_provider.get_disk_partition_information(disk_list)

        # Step logger end for Step 8
        self._test_content_logger.end_step_logger(8, return_val=disk_info)

        # Step logger start for Step 9
        self._test_content_logger.start_step_logger(9)

        # Delete the partitions inside pmem
        self._partition_provider.delete_partition(disk_list)

        # Create partition with full size
        if OperatingSystems.LINUX == self._os.os_type:
            for index in range(0, len(disk_list)):
                self._memory_common_lib.create_partition_storage(disk_list[index], self.PARTITION_TYPE)
                partition_list = self._memory_common_lib.get_sub_partition(disk_list[index])
                self._memory_common_lib.create_file_system(partition_list[-1], self.FILE_SYSTEM)

        elif OperatingSystems.WINDOWS == self._os.os_type:
            self._partition_provider.create_partition_dcpmm_disk(
                convert_type='gpt', disk_lists=disk_list, mode="dax")

        # Disk information after creating full size partition and file system
        disk_info = self._partition_provider.get_disk_partition_information(disk_list)

        # Step logger end for Step 9
        self._test_content_logger.end_step_logger(5, return_val=disk_info)

        return all(self.return_value)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PICR2lmMemoryAppdirectStorgeCheck, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PICR2lmMemoryAppdirectStorgeCheck.main() else Framework.TEST_RESULT_FAIL)
