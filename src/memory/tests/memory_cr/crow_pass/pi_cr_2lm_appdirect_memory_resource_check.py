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

from src.lib import content_exceptions
from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon
from src.memory.tests.memory_cr.crow_pass.pi_cr_2lm_appdirect_basicflow_l_w import PiCR2LMAppDirectBasicFlow


class PICR2LMAppDirectMemoryResourceCheck(CrProvisioningTestCommon):
    """
    HP QC ID: H101115-PI_CR_2LM_Memory_AppDirect_MemoryResourceCheck_L and
    H101160-PI_CR_2LM_Memory_AppDirect_MemoryResourceCheck_W

    To Verify Memory information for CR DIMMs is correct.
    """

    TEST_CASE_ID = ["H101115", "PI_CR_2LM_Memory_AppDirect_MemoryResourceCheck_L",
                    "H101160", "PI_CR_2LM_Memory_AppDirect_MemoryResourceCheck_W"]
    FIFTY_PERCENT = 50
    step_data_dict = {1: {'step_details': 'To check basic memory mode.',
                          'expected_results': 'Successfully checked basic memory mode. '},
                      2: {'step_details': 'Check OS memory. ',
                          'expected_results': 'Successfully verified OS memory ...'},
                      3: {'step_details': 'Check if DCPMM DIMM memory resource allocation across the host '
                                          'server is correct. ',
                          'expected_results': 'Successfully verified, there are no segmentation fault...'},
                      4: {'step_details': 'Check other information related to DCPMM..',
                          'expected_results': 'Successfully verified, there are no segmentation fault...'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PICR2LMAppDirectMemoryResourceCheck object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        # Provisioning test case
        self._cr_2lm_appdirect_basic = PiCR2LMAppDirectBasicFlow(test_log, arguments, cfg_opts)
        self._cr_2lm_appdirect_basic.prepare()
        self._cr_2lm_appdirect_basic_result = self._cr_2lm_appdirect_basic.execute()

        # calling base class init
        super(PICR2LMAppDirectMemoryResourceCheck, self).__init__(test_log, arguments, cfg_opts, bios_config_file=None)

        if self._cr_2lm_appdirect_basic_result:
            self._log.info("App Direct basic check has been done successfully!")
        else:
            raise content_exceptions.TestFail("App Direct basic check has failed!")

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=self._cr_2lm_appdirect_basic_result)

    def prepare(self):
        # type: () -> None
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # Get the Capacity of all dimms.
        memory_capacity_os = self._memory_provider.get_total_system_memory()

        if isinstance(memory_capacity_os, list):
            memory_capacity_os = int(memory_capacity_os[0].split(":")[1].strip("MB").strip().replace(",", "")) / 1024
        else:
            memory_capacity_os = memory_capacity_os / 1024

        self._log.info("Total DCPMM capacity as per configuration - {}".format(self._dcpmm_mem_capacity))
        self._dcpmm_mem_capacity = self._dcpmm_mem_capacity * (self.FIFTY_PERCENT / 100)
        self._log.info("Total DCPMM capacity as per configuration with {}% is - {}".format(self.FIFTY_PERCENT,
                                                                                           self._dcpmm_mem_capacity))
        self._log.info("Total memory capacity from OS is: {}".format(memory_capacity_os))
        # ddr memory with variance
        dcpmm_memtotal_with_variance_config = (self._dcpmm_mem_capacity - (self._dcpmm_mem_capacity *
                                                                           self._variance_percent))

        self._log.info("Total DCPMM capacity as per configuration with variance - {}".format(
            dcpmm_memtotal_with_variance_config))

        if int(memory_capacity_os) < int(dcpmm_memtotal_with_variance_config) or int(memory_capacity_os) > \
                self._dcpmm_mem_capacity:
            raise content_exceptions.TestFail("Total DCPMM dimm Capacity is not same as configuration.")

        self._log.info("Total memory Capacity is same as DCPMM memory capacity.")

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        Function is responsible to verify various ipmctl commands.

        :return: True, if the test case is successful.
        :raise: None
        """

        dmidecode_output_os = self._memory_provider.get_memory_slots_details()

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        self._ipmctl_provider.show_dimm_pcd()
        self._log.info("Successfully executed ipmctl PCD command..")

        self._ipmctl_provider.show_system()
        self._log.info("Successfully executed ipmctl SYSTEM command..")

        self._ipmctl_provider.get_system_capability()
        self._log.info("Successfully executed ipmctl SYSTEM CAPABILITIES command..")

        mem_resources_data = self._ipmctl_provider.show_mem_resources()
        self._log.info("Successfully executed ipmctl MEMORY RESOURCES command..")

        # Verify memory resources information
        self._memory_common_lib.verify_memory_resource_information(mem_resources_data, "2LM", self.FIFTY_PERCENT)

        self._ipmctl_provider.show_dimm_performance()
        self._log.info("Successfully executed ipmctl DIMM PERFORMANCE command..")

        topology_op = self._ipmctl_provider.show_topology()
        self._log.info("Successfully executed ipmctl TOPOLOGY command..")

        topology_info = self._memory_common_lib.get_list_off_topology(topology_op)

        # Verify topology information
        self._memory_common_lib.verify_topology_information(topology_info, dmidecode_output_os)

        ars_status_info = self._ipmctl_provider.show_ars_status()
        self._log.info("Successfully executed ipmctl ARS Status command..")

        # Verify topology information
        self._memory_common_lib.verify_ars_status_information(ars_status_info)

        #  Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        socket_op = self._ipmctl_provider.show_socket()
        self._log.info("Successfully executed ipmctl SOCKET command..")

        cpu_locators = self._memory_provider.get_list_off_locators()

        # Verify socket information
        self._memory_common_lib.verify_socket_information(socket_op, cpu_locators, "2LM", 50)

        self._ipmctl_provider.show_sensors()
        self._log.info("Successfully executed ipmctl SENSOR command..")

        firmware_data = self._ipmctl_provider.show_firmware()
        self._log.info("Successfully executed ipmctl FIRMWARE command..")

        # Verify Firmware information
        self._memory_common_lib.verify_firmware_information(firmware_data)

        self._ipmctl_provider.show_preferences()
        self._log.info("Successfully executed ipmctl PREFERENCE command..")

        self._ipmctl_provider.show_dimm_thermal_error()
        self._log.info("Successfully executed ipmctl THERMAL ERROR command..")

        self._ipmctl_provider.show_dimm_media_error()
        self._log.info("Successfully executed ipmctl MEDIA ERROR command..")

        self._ipmctl_provider.system_nfit()
        self._log.info("Successfully executed ipmctl NFIT command..")

        self._ipmctl_provider.get_system_pcat()
        self._log.info("Successfully executed ipmctl SYSTEM PCAT command..")

        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PICR2LMAppDirectMemoryResourceCheck, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if PICR2LMAppDirectMemoryResourceCheck.main() else Framework.TEST_RESULT_FAIL)
