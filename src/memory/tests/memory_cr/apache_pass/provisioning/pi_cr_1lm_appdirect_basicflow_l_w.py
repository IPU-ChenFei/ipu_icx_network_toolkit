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

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon
from src.provider.partition_provider import PartitionProvider


class PiCR1lmAppdirectBasicFlow(CrProvisioningTestCommon):
    """
    HP QC ID: 79514 (Linux) and 82149 (Windows)
    1LM Basic functionality check,verify if system is able to boot into OS with CR DIMMs installed.
    """

    BIOS_CONFIG_FILE = "pi_cr_1lm_appdirect_basicflow_bios_knob.cfg"
    TEST_CASE_ID = "H79514/H82149-PI_CR_1LM_AppDirect_Basicflow"
    return_value = []

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
                      7: {'step_details': 'Check the namespace created just now.',
                          'expected_results': 'Name spaces created successfully.'},
                      8: {'step_details': 'Create disk partition, make ext4 file system and Create a mount point for '
                                          'the newly created pmem disks.',
                          'expected_results': 'Disk partition, ext4 file system and new mount points has been created '
                                              'successfully.'},
                      9: {'step_details': 'Check pmem disk partitions are created ',
                          'expected_results': 'Disk partitions for the newly created pmem disks has been created '
                                              'successfully.'},
                      10: {'step_details': 'Check mount points created for Pmem disks ',
                           'expected_results': 'Able to detect newly created mount points.'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiCR1lmAppdirectBasicFlow object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiCR1lmAppdirectBasicFlow, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._partition_provider = PartitionProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self._os)

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        if not self.os.is_alive():
            self._log.error("System is not alive")
            self.perform_graceful_g3()  # To make the system alive

        self._common_content_lib.clear_all_os_error_logs()  # TO clear Os logs
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._common_content_lib.perform_os_reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

        #  Get the DIMM information
        dimm_show = self._ipmctl_provider.get_memory_dimm_information()

        # Get the list of dimms which are healthy and log them.
        self._ipmctl_provider.get_list_of_dimms_which_are_healthy()

        # Verify the list of dimms which are healthy
        self._ipmctl_provider.verify_all_dcpmm_dimm_healthy()

        # Get the Capacity of all dimms.
        sum_dimm_capacity_os = sum(self._memory_common_lib.get_total_dimm_memory_data(dimm_show))

        self._log.info("Total dimm capacity shown from OS level - {}..".format(float(sum_dimm_capacity_os)))
        self._log.info("Total dimm capacity as per configuration - {}..".format(float(self._dcpmm_mem_capacity)))

        # Memory total with variance
        memtotal_with_variance_config = (self._dcpmm_mem_capacity - (self._dcpmm_mem_capacity * self._variance_percent))

        self._log.info("Total dimm capacity as per configuration with variance - {}".format(
            memtotal_with_variance_config))

        if int(sum_dimm_capacity_os) < memtotal_with_variance_config or int(sum_dimm_capacity_os) > \
                self._dcpmm_mem_capacity:
            raise content_exceptions.TestFail("Total dcpmm dimm Capacity is not same as installed capacity from"
                                              " configuration.")
        elif int(sum_dimm_capacity_os) >= int(memtotal_with_variance_config):
            self._log.info("Total dcpmm dimm Capacity is same as installed capacity from configuration.")

        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=all(self.return_value))

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Check that detected DIMM in system has correct attribute values.

        :return: True, if the test case is successful.
        :raise: None
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        #  Get the DIMM information
        dimm_show = self._ipmctl_provider.get_memory_dimm_information()

        # Get available name space info
        namepsace_output = self._ipmctl_provider.dcpmm_get_disk_namespace()

        # Clear the namespaces if exists
        self._ipmctl_provider.dcpmm_check_disk_namespace_initilize(namepsace_output)

        self._ipmctl_provider.delete_pcd_data()

        self._log.info("Cleared PCD data on the dimms, restarting the SUT to apply the changes..")

        self._log.info("Platform has been restarted.. waiting to boot to OS...")

        #  Restart the SUT
        self._common_content_lib.perform_os_reboot(self._reboot_timeout)

        #  Configure the capacity on all installed DCPMM(s) with 100% as persistent memory
        dcpmm_disk_goal = self._ipmctl_provider.dcpmm_configuration(
            cmd=r"ipmctl create -f -goal persistentmemorytype=appdirect", cmd_str="with 100% as persistent memory")

        #  Verify the mode provisioning
        self.return_value.append(
            self.verify_app_direct_mode_provisioning(mode="pmem", mode_percentage=100,
                                                     total_memory_result_data=dimm_show,
                                                     app_direct_result_data=dcpmm_disk_goal))

        #  Restart the SUT
        self._common_content_lib.perform_os_reboot(self._reboot_timeout)

        #  Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        #  Get the present memory resources
        mem_resources_output = self._ipmctl_provider.show_mem_resources()

        self._memory_common_lib.verify_provisioned_appdirect_capacity(
            mem_resources_output, r"AppDirect.*", percent=100)

        #  Step logger end for Step 3
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
        else:
            self._log.info("FreeCapacity does not equals to capacity..")
            self.return_value.append(False)

        #  Get the list of all regionX device name
        region_data_list = self._ipmctl_provider.dcpmm_get_pmem_unused_region()

        #  Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=all(self.return_value))

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        #  Create namespace for each regionX
        new_created_namespace_list = self._ipmctl_provider.dcpmm_new_pmem_disk(region_data_list)

        #  Step logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=True)

        # Step logger start for Step 6
        self._test_content_logger.start_step_logger(6)

        # Show present namespaces
        namespace_info = self._ipmctl_provider.dcpmm_get_disk_namespace()

        #  Verify namespace presence
        self._ipmctl_provider.verify_pmem_device_presence_cap(namespace_info)

        #  Step logger end for Step 6
        self._test_content_logger.end_step_logger(6, return_val=True)

        # Step logger start for Step 7
        self._test_content_logger.start_step_logger(7)

        #  To get the DCPMM disk list that needs to be partitioned
        disk_list = self._partition_provider.get_dcpmm_disk_list(region_data_list)

        self._log.info("{} DCPMM device(s) attached to this system board {}.".format(len(disk_list), disk_list))

        #  Create the DCPMM disk partition
        self.return_value.append(self._partition_provider.create_partition_dcpmm_disk(
            convert_type="gpt", disk_lists=disk_list, mode='dax'))

        #  Create an file system on each enumerated PM blockdev device
        self._partition_provider.create_ext4_filesystem(new_created_namespace_list)

        #  Step logger end for Step 7
        self._test_content_logger.end_step_logger(7, return_val=True)

        # Step logger start for Step 8
        self._test_content_logger.start_step_logger(8)

        #  Create mount point on each PM blockdev device
        self._partition_provider.create_mount_point(new_created_namespace_list)

        #  Step logger end for Step 8
        self._test_content_logger.end_step_logger(8, return_val=True)

        # Step logger start for Step 9
        self._test_content_logger.start_step_logger(9)

        # verify the new DCPMM disk partitions for healthy and showing correct drive letters.
        self.return_value.append(self._partition_provider.verify_device_partitions(disk_lists=disk_list))

        #  Step logger end for Step 9
        self._test_content_logger.end_step_logger(9, return_val=all(self.return_value))

        # Step logger start for Step 10
        self._test_content_logger.start_step_logger(10)

        #  Verify mount is successful or not
        self.return_value.append(self._partition_provider.verify_mount_point(new_created_namespace_list))

        #  Step logger end for Step 10
        self._test_content_logger.end_step_logger(10, return_val=all(self.return_value))

        return all(self.return_value)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiCR1lmAppdirectBasicFlow, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiCR1lmAppdirectBasicFlow.main() else Framework.TEST_RESULT_FAIL)
