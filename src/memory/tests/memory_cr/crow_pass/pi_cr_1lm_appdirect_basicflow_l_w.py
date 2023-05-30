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

import pickle
import re
import sys

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_exceptions
from src.lib.dtaf_content_constants import CRFileSystems, SlotConfigConstant
from src.lib.memory_constants import MemoryTopology
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon
from src.memory.tests.memory_cr.crow_pass.cps_common import CpsTestCommon
from src.provider.partition_provider import PartitionProvider


class PiCR1LMAppDirectBasicFlow(CrProvisioningTestCommon):
    """
    HP QC ID: H101096:PI_CR_1LM_AppDirect_Basicflow_L and H101149:PI_CR_1LM_AppDirect_Basicflow_W

    1LM Basic functionality check,verify if system is able to boot into OS with CR DIMMs installed.
    """

    PARTITION_TYPE = "primary"
    FILE_SYSTEM_NTFS = "ntfs"
    FILE_SYSTEM_EXT4 = "ext4"
    TEST_CASE_ID = ["H101096", "PI_CR_1LM_AppDirect_Basicflow_L", "H101149", "PI_CR_1LM_AppDirect_Basicflow_W"]
    return_value = []
    SIZE_LIST = ["16GB", "8GB", "8GB"]
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
                      7: {'step_details': 'Delete existing partitions and create the partitions on DCPMM.',
                          'expected_results': 'Partitions created successfully.'},
                      8: {'step_details': 'make ext4 file system and Create a mount point for '
                                          'the newly created pmem disks.',
                          'expected_results': 'ext4 file system and new mount points has been created successfully.'},
                      9: {'step_details': 'Check pmem disk partitions are created ',
                          'expected_results': 'Disk partitions for newly created pmem disks verified successfully.'},
                      10: {'step_details': 'Check mount points created for Pmem disks ',
                           'expected_results': 'Able to detect newly created mount points.'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiCR1LMAppDirectBasicFlows object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        """
        # calling base class init
        super(PiCR1LMAppDirectBasicFlow, self).__init__(test_log, arguments, cfg_opts, mode=MemoryTopology.ONE_LM)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._partition_provider = PartitionProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self._os)
        self.cps_common = CpsTestCommon(test_log, arguments, cfg_opts, mode=MemoryTopology.ONE_LM)

    def prepare(self):
        # type: () -> None
        """
        1. Verify DDR + CPS with 8 + 8 configuration.
        2. Set the bios knobs as per the test case and Reboot the SUT and Verify the bios knobs that are set.
        3. Install ipmctl tool

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        # To verify given memory configuration
        ddr_cr_config = self._common_content_configuration.get_ddr_cr_population_from_config()
        if ddr_cr_config not in SlotConfigConstant.CR_DDR_REFERENCE:
            raise content_exceptions.TestFail("CR DDR population detail incorrect! Please provide CR DDR population "
                                              "details in content_configuration.xml file from the below list : "
                                              "{}".format(SlotConfigConstant.CR_DDR_REFERENCE))
        else:
            verify_func_call = getattr(self._memory_provider, "verify_" + ddr_cr_config + "_population")
            verify_func_call()

        self.cps_common.prepare()

        self._install_collateral.install_ipmctl()
        self._install_collateral.install_dmidecode()

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        FFunction is responsible for the below tasks,
        1. Create goal Appdirect = 100.
        2. Verify the provisioning with memory capacity.
        3. Check that detected DIMM in system has correct attribute values.
        4. Create and verify Namespace.
        5. Create partition for the pmem device.
        6. Create ext4 file system.
        7. Create mount point for the pmem device

        :return: True, if the test case is successful.
        :raise: None
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # Get the DIMM information
        dimm_show = self._ipmctl_provider.get_memory_dimm_information()

        self._ipmctl_provider.delete_pmem_device()

        # Configure the capacity on all installed DCPMM(s) with 100% as persistent memory
        dcpmm_disk_goal = self._ipmctl_provider.dcpmm_configuration(
            cmd=self.IPMCTL_CMD_FOR_100_PERCENT_APP_DIRECT, cmd_str="with 100% as persistent memory")

        # Verify the mode provisioning for App Direct 100%
        self.return_value.append(
            self.verify_app_direct_mode_provisioning(mode="pmem", mode_percentage=100,
                                                     total_memory_result_data=dimm_show,
                                                     app_direct_result_data=dcpmm_disk_goal))

        # Restart the SUT
        self._common_content_lib.perform_os_reboot(self._reboot_timeout)

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        # Get the present memory resources
        mem_resources_output = self._ipmctl_provider.show_mem_resources()

        self._memory_common_lib.verify_provisioned_appdirect_capacity(mem_resources_output, r"AppDirect.*", percent=100)

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        # Get region data
        dimm_region_info = self._ipmctl_provider.show_region()

        self.return_value.append(self._memory_common_lib.verify_iset_id_existence(dimm_region_info))

        free_capacity_list = self._memory_common_lib.get_capacity_region_data(dimm_region_info, 3)
        capacity_list = self._memory_common_lib.get_capacity_region_data(dimm_region_info, 4)

        if free_capacity_list == capacity_list:
            self._log.info("FreeCapacity equals to capacity..")
            self.return_value.append(True)
        else:
            self._log.info("FreeCapacity does not equals to capacity..")
            self.return_value.append(False)

        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=all(self.return_value))

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        # Get the list of all regionX device name
        region_data_list = self._ipmctl_provider.dcpmm_get_pmem_unused_region()

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        # Create namespace for each regionX
        self._ipmctl_provider.dcpmm_new_pmem_disk(region_data_list, mode=CRFileSystems.DAX)

        # Step logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=True)

        # Step logger start for Step 6
        self._test_content_logger.start_step_logger(6)

        # Show present namespaces
        namespace_info = self._ipmctl_provider.dcpmm_get_disk_namespace()

        # Verify namespace presence
        self._ipmctl_provider.verify_pmem_device_presence_cap(namespace_info)

        # Step logger end for Step 6
        self._test_content_logger.end_step_logger(6, return_val=True)

        # Step logger start for Step 7
        self._test_content_logger.start_step_logger(7)

        # To get the DCPMM disk list that needs to be partitioned
        disk_list = self._partition_provider.get_dcpmm_disk_list(namespace_info)

        self._log.info("{} DCPMM device(s) attached to this system board {}.".format(len(disk_list), disk_list))
        if len(disk_list) == 0:
            raise content_exceptions.TestFail("did not get any pmem device drives...")

        # Delete the partitions inside pmem
        self._partition_provider.delete_partition(disk_list)

        self._partition_provider.create_dcpmm_gpt_format(disk_list)

        for each_value in self.SIZE_LIST:
            if OperatingSystems.WINDOWS == self._os.os_type:
                # Create primary partition of size
                self._partition_provider.create_partition_dcpmm_disk(
                    convert_type=self.FILE_SYSTEM_NTFS, disk_lists=disk_list, mode=self.PARTITION_TYPE, size=each_value)
            elif OperatingSystems.LINUX == self._os.os_type:
                self._partition_provider.create_partition_dcpmm_disk(
                    convert_type=self.FILE_SYSTEM_EXT4, disk_lists=disk_list, mode=self.PARTITION_TYPE, size=each_value)
            # Disk information after creating primary partition and file system
            self._partition_provider.get_disk_partition_information(disk_list)

        sub_partitions_list = []
        if OperatingSystems.LINUX == self._os.os_type:
            for index in range(0, len(disk_list)):
                partition_list = self._memory_common_lib.get_sub_partition(disk_list[index])
                sub_partitions_list.append(partition_list)

            sub_partitions_list = self._common_content_lib.list_flattening(sub_partitions_list)
            self._log.info("Sub partition list : {}".format(sub_partitions_list))
            if not sub_partitions_list:
                raise RuntimeError("did not get sub partitions ..")
            pmem_list = []
            # To remove /dev
            for each_device in sub_partitions_list:
                if 'dev' in each_device:
                    pmem_list.append(re.findall(pattern='pmem.*', string=each_device))
            self._log.info("pmem device list : {}".format(pmem_list))
            pmem_list = self._common_content_lib.list_flattening(pmem_list)
            drive_letters = None
        elif OperatingSystems.WINDOWS == self._os.os_type:
            with open(self._partition_provider.DRIVE_LETTERS_FILE, "rb") as fp:
                drive_letters = pickle.load(fp)
                self._log.info("List of pmem volume drive letters: {}".format(drive_letters))
                pmem_list = disk_list
                self._log.info("pmem device list : {}".format(pmem_list))

        self._test_content_logger.end_step_logger(7, return_val=pmem_list)

        # Step logger start for Step 8
        self._test_content_logger.start_step_logger(8)

        self._partition_provider.create_ext4_filesystem(pmem_list)

        # Create mount point on each PM block dev device
        self._partition_provider.create_mount_point(pmem_list, mode=CRFileSystems.DAX)

        self._test_content_logger.end_step_logger(8, return_val=True)

        # Step logger start for Step 9
        self._test_content_logger.start_step_logger(9)

        # verify the new DCPMM disk partitions for healthy and showing correct drive letters.
        self.return_value.append(self._partition_provider.verify_device_partitions(pmem_list, drive_letters))

        # Step logger end for Step 9
        self._test_content_logger.end_step_logger(9, return_val=all(self.return_value))

        # Step logger start for Step 10
        self._test_content_logger.start_step_logger(10)

        # Verify mount is successful or not
        self.return_value.append(self._partition_provider.verify_mount_point(pmem_list))

        # Step logger end for Step 10
        self._test_content_logger.end_step_logger(10, return_val=all(self.return_value))

        return all(self.return_value)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""

        self._ipmctl_provider.delete_pmem_device()

        super(PiCR1LMAppDirectBasicFlow, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiCR1LMAppDirectBasicFlow.main() else Framework.TEST_RESULT_FAIL)
