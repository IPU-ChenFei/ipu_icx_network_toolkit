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
from src.provider.partition_provider import PartitionProvider


class PICR1lmAppDirectStorageResourceCheck(CrProvisioningTestCommon):
    """
    HP QC ID: 79517 (Linux) and 82152 (Windows)

    Description: Verify Disk/Storage information for CR DIMMs is correct in Linux
    """
    BIOS_CONFIG_FILE = "pi_cr_1lm_appdirect_basicflow_bios_knob.cfg"
    TEST_CASE_ID = "H79517/H82152-PI_CR_1LM_AppDirectStorageResourceCheck"
    PARTITION_TYPE = "primary"
    FILE_SYSTEM = "ntfs"

    step_data_dict = {1: {'step_details': 'Clear OS logs and Set the bios knobs, Restart the system, Boot to OS',
                          'expected_results': 'Cleared os logs and bios settings is done.Successfully boot to os'
                                              'and verified the bios knobs'},
                      2: {'step_details': 'To provision the crystal ridge with 1LM 100%AppDirect mode',
                          'expected_results': 'Successfully provisioned the crystal ridge with 1LM 100%AppDirect mode'},
                      3: {'step_details': 'Create 2GB of primary partition and formatting with ntfs file system',
                          'expected_results': 'Created 2GB primary partition and ntfs file system'},
                      4: {'step_details': 'Create 15GB of primary partition and format with ntfs file system .',
                          'expected_results': 'Created 15Gb primary partition and formatted with ntfs file system'},
                      5: {'step_details': 'Delete 2GB and 15 GB partition.Create full size of primary partition and '
                                          'format with ntfs file system .',
                          'expected_results': 'Deleted 2GB and 15GB primary partition.'
                                              'Created full size of primary partition and formatted with ntfs file'
                                              ' system'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PICR1lmAppDirectStorageResourceCheckLinux object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """

        # calling base class init
        super(PICR1lmAppDirectStorageResourceCheck, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._partition_provider = PartitionProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self._os)

    def prepare(self):
        # type: () -> None
        """
        1. To clear os log.
        2. Set the bios knobs to its default mode
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.

        :return: None
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._common_content_lib.clear_all_os_error_logs()  # To clear OS logs
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._common_content_lib.perform_os_reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Creating namespace
        2. Creating 2GB primary partition and formatting with ntfs file
        3. Creating 15GB primary partition and formatting with ntfs file
        4. Deleting previous created partition and creating new partition with full size
        and formatting with ntfs file system

        :return: True, if the test case is successful.
        """
        return_value = []

        # Step logger start for Step2
        self._test_content_logger.start_step_logger(2)

        #  Get the DIMM information
        dimm_show = self._ipmctl_provider.get_memory_dimm_information()

        # Get available name space info
        namespace_output = self._ipmctl_provider.dcpmm_get_disk_namespace()

        # Clear the namespaces if exists
        self._ipmctl_provider.dcpmm_check_disk_namespace_initilize(namespace_output)

        # To delete the pcd data
        self._ipmctl_provider.delete_pcd_data()

        # Need a reboot after deleting the pcd data
        self._common_content_lib.perform_os_reboot(self._reboot_timeout)

        #  Configure the capacity on all installed DCPMM(s) with 100% as persistent memory
        dcpmm_disk_goal = self._ipmctl_provider.dcpmm_configuration(
            cmd=r"ipmctl create -f -goal persistentmemorytype=appdirect",
            cmd_str="with 100% as persistent memory")

        #  Verify the mode provisioning
        return_value.append(
            self.verify_app_direct_mode_provisioning(mode="pmem", mode_percentage=100,
                                                     total_memory_result_data=dimm_show,
                                                     app_direct_result_data=dcpmm_disk_goal))

        #  Restart the SUT
        self._common_content_lib.perform_os_reboot(self._reboot_timeout)

        #  Get the present memory resources
        mem_resources_output = self._ipmctl_provider.show_mem_resources()

        self._memory_common_lib.verify_provisioned_appdirect_capacity(mem_resources_output, r"AppDirect.*")

        # Get region data
        dimm_region_info = self._ipmctl_provider.show_region()

        return_value.append(self._memory_common_lib.verify_iset_id_existence(dimm_region_info))

        free_capacity_list = self._memory_common_lib.get_capacity_region_data(dimm_region_info, 3)
        capacity_list = self._memory_common_lib.get_capacity_region_data(dimm_region_info, 4)

        if free_capacity_list == capacity_list:
            self._log.info("FreeCapacity equals to capacity..")
        else:
            self._log.info("FreeCapacity does not equals to capacity..")
            return_value.append(False)

        # Get the list of all regionX device name
        region_data_list = self._ipmctl_provider.dcpmm_get_pmem_unused_region()

        #  Create namespace for each regionX
        new_created_namespace_list = self._ipmctl_provider.dcpmm_new_pmem_disk(region_data_list)

        # Show present namespaces
        namespace_info = self._ipmctl_provider.dcpmm_get_disk_namespace()

        # Verify namespace presence
        return_value.append(self._ipmctl_provider.verify_pmem_device_presence_cap(namespace_info))

        # To get the DCPMM disk list that needs to be partitioned
        disk_list = self._partition_provider.get_dcpmm_disk_list(new_created_namespace_list)

        self._log.info("{} DCPMM device(s) attached to this system board {}.".format(len(disk_list), disk_list))

        # Step logger end for Step2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step3
        self._test_content_logger.start_step_logger(3)

        self._partition_provider.create_dcpmm_gpt_format(disk_list)

        # Create primary partition of size 2GB
        self._partition_provider.create_partition_dcpmm_disk(
            convert_type=self.FILE_SYSTEM, disk_lists=disk_list, mode=self.PARTITION_TYPE, size='2GB')

        # Disk information after creating 2GB primary partition and file system
        disk_info = self._partition_provider.get_disk_partition_information(disk_list)

        # Step logger end for Step3
        self._test_content_logger.end_step_logger(3, return_val=disk_info)

        # Step logger start for Step4
        self._test_content_logger.start_step_logger(4)

        # Create primary partition of size 15GB
        self._partition_provider.create_partition_dcpmm_disk(
            convert_type=self.FILE_SYSTEM, disk_lists=disk_list, mode=self.PARTITION_TYPE, size='15GB')

        # Disk information after creating 15GB partition and file system
        disk_info = self._partition_provider.get_disk_partition_information(disk_list)

        # Step logger end for Step4
        self._test_content_logger.end_step_logger(4, return_val=disk_info)

        # Step logger start for Step5
        self._test_content_logger.start_step_logger(5)

        # Delete the partitions inside pmem
        self._partition_provider.delete_partition(disk_list)

        # Create partition with full size
        if OperatingSystems.LINUX == self._os.os_type:
            for index in range(0, len(disk_list)):
                self._memory_common_lib.create_partition_storage(disk_list[index], self.PARTITION_TYPE)
                partition_list = self._memory_common_lib.get_sub_partition(disk_list[index])
                self._memory_common_lib.create_file_system(partition_list[index], self.FILE_SYSTEM)

        elif OperatingSystems.WINDOWS == self._os.os_type:
            self._partition_provider.create_partition_dcpmm_disk(
                convert_type='gpt', disk_lists=disk_list, mode="dax")

        # Disk information after creating full size partition and file system
        disk_info = self._partition_provider.get_disk_partition_information(disk_list)

        # Step logger end for Step5
        self._test_content_logger.end_step_logger(5, return_val=disk_info)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PICR1lmAppDirectStorageResourceCheck, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if PICR1lmAppDirectStorageResourceCheck.main() else Framework.TEST_RESULT_FAIL)
