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
from src.lib.memory_constants import MemoryTopology
from src.lib.dtaf_content_constants import SlotConfigConstant
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon
from src.provider.partition_provider import PartitionProvider
from src.memory.tests.memory_cr.crow_pass.cps_common import CpsTestCommon
from src.power_management.lib.reset_base_test import ResetBaseTest


class PiCR1LMAppDirectPMColdReboot(CrProvisioningTestCommon):
    """
    HP QC  ID: 101146-PI_CR_1LM_AppDirect_PM_ColdReboot_8+1_L and H101191-PI_CR_1LM_AppDirect_PM_ColdReboot_8+1_W

    To check system power sequence with 1LM CR: Cold reboot
    """

    TEST_CASE_ID = ["H101146", "PI_CR_1LM_AppDirect_PM_ColdReboot_8+1_L",
                    "H101191", "PI_CR_1LM_AppDirect_PM_ColdReboot_8+1_W"]
    NUMBER_OF_CYCLES = 10
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
                      3: {'step_details': 'Check if CPS DIMM memory resource allocation is correct and size and '
                                          'locator from dmidecode -t 17.',
                          'expected_results': 'AppDirectCapacity is nearly as same as dimm capacity and size and '
                                              'locator are verified'},
                      4: {'step_details': 'Cold reboot the SUT',
                          'expected_results': 'SUT should come to OS after cold reboot'},
                      5: {'step_details': 'Check if CPS DIMM memory resource allocation is correct and size and '
                                          'locator from dmidecode -t 17.',
                          'expected_results': 'AppDirectCapacity is nearly as same as dimm capacity and size and '
                                              'locator verified'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiCR1LMAppDirectPMColdReboot object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        """
        super(PiCR1LMAppDirectPMColdReboot, self).__init__(test_log, arguments, cfg_opts,
                                                           mode=MemoryTopology.ONE_LM)

        self.cps_common = CpsTestCommon(test_log, arguments, cfg_opts, mode=MemoryTopology.ONE_LM)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._partition_provider = PartitionProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self.os)
        self.cold_reboot_obj = ResetBaseTest(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Verify DDR + CPS with 8 + 1 configuration.
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

        # Get the DIMM information
        dimm_show = self._ipmctl_provider.get_memory_dimm_information()

        # Get the list of dimms which are healthy and log them.
        self._ipmctl_provider.get_list_of_dimms_which_are_healthy()

        # Verify the list of dimms which are healthy
        self._ipmctl_provider.verify_all_dcpmm_dimm_healthy()

        self._memory_common_lib.verify_cr_memory_with_config(show_dimm=dimm_show)

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Create the goal with 100 % App direct.
        2. checking the memory resources
        3. verify size and locator from dmideocode -t 17 with smbios_configuration.xml
        4. Install IO port package for Linux. Cold reboot the SUT.
        5. Repeat the process for 10 times.

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

        self._log.info("Cleared PCD data on the dimms, restarting the SUT to apply the changes..")

        # Restart the SUT
        self._common_content_lib.perform_os_reboot(self._reboot_timeout)

        # Configure the capacity on all installed DCPMM(s) with 100% as persistent memory
        dcpmm_disk_goal = self._ipmctl_provider.dcpmm_configuration(
            cmd=self.IPMCTL_CMD_FOR_100_PERCENT_APP_DIRECT, cmd_str="with 100% as persistent memory")

        # Verify the mode provisioning
        self.return_value.append(
            self.verify_app_direct_mode_provisioning(mode="pmem", mode_percentage=100,
                                                     total_memory_result_data=dimm_show,
                                                     app_direct_result_data=dcpmm_disk_goal))
        # Restart the SUT
        self._common_content_lib.perform_os_reboot(self._reboot_timeout)

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=all(self.return_value))

        for cycle in range(0, self.NUMBER_OF_CYCLES):
            self._log.info("Verifying memory resources before cold reboot cycle : {}".format(cycle + 1))

            # Step logger start for Step 3
            self._test_content_logger.start_step_logger(3)

            # Get the present memory resources
            mem_resources_output = self._ipmctl_provider.show_mem_resources()

            self._memory_common_lib.verify_provisioned_appdirect_capacity(
                mem_resources_output, r"AppDirect.*", percent=100)

            self.return_value.append(self._memory_common_lib.verify_size_with_smbios_config())

            # Step logger end for Step 3
            self._test_content_logger.end_step_logger(3, return_val=all(self.return_value))

            # Step logger start for Step 4
            self._test_content_logger.start_step_logger(4)

            # Copy and install IOPort rpm
            self._install_collateral.install_ioport()

            # To cold reboot the SUT.
            self._log.info("Executing Cold Reset")
            self.cold_reboot_obj.cold_reset()

            # Step logger end for Step 4
            self._test_content_logger.end_step_logger(4, return_val=True)

            # Step logger start for Step 5
            self._test_content_logger.start_step_logger(5)

            self._log.info("Verifying memory resources after cold reboot cycle : {}".format(cycle + 1))

            # Get the present memory resources
            mem_resources_output = self._ipmctl_provider.show_mem_resources()

            self._memory_common_lib.verify_provisioned_appdirect_capacity(
                mem_resources_output, r"AppDirect.*", percent=100)

            self.return_value.append(self._memory_common_lib.verify_size_with_smbios_config())

            # Step logger end for Step 5
            self._test_content_logger.end_step_logger(5, return_val=all(self.return_value))

        return all(self.return_value)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiCR1LMAppDirectPMColdReboot, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiCR1LMAppDirectPMColdReboot.main() else Framework.TEST_RESULT_FAIL)
