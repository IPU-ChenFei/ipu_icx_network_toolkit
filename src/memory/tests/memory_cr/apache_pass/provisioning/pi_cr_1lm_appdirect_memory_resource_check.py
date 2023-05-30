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
from src.memory.tests.memory_cr.apache_pass.provisioning.pi_cr_1lm_appdirect_basicflow_l_w \
    import PiCR1lmAppdirectBasicFlow


class PICR1lmAppDirectMemoryResourceCheck(CrProvisioningTestCommon):
    """
    HP QC ID: 79518 (Linux) and 82153 (Windows)

    To Verify Memory information for CR DIMMs is correct in linux
    """

    TEST_CASE_ID = ["PI_CR_1LM_AppDirect_MemoryResourceCheck_L", "PI_CR_1LM_AppDirect_MemoryResourceCheck_W"]

    step_data_dict = {1: {'step_details': 'To provision the crystal ridge with 1LM 100% AppDirect mode',
                          'expected_results': 'Successfully provisioned crystal ridge with 1LM 100% AppDirect mode '},
                      2: {'step_details': 'Check if DCPMM DIMM memory resource allocation across the host '
                                          'server is correct.',
                          'expected_results': 'Successfully verified memory capacity = DDR5 memory capacity..'},
                      3: {'step_details': 'Check if DCPMM DIMM memory resource allocation across the host '
                                          'server is correct. ',
                          'expected_results': 'Successfully verified, there are no segmentation fault...'},
                      4: {'step_details': 'Check other information related to DCPMM..',
                          'expected_results': 'Successfully verified, there are no segmentation fault...'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PICR1lmAppDirectMemoryResourceCheck object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        # Provisioning test case
        self._cr_provisioning_100appdirect = PiCR1lmAppdirectBasicFlow(test_log, arguments, cfg_opts)
        self._cr_provisioning_100appdirect.prepare()
        self._provisioning_result = self._cr_provisioning_100appdirect.execute()

        # calling base class init
        super(PICR1lmAppDirectMemoryResourceCheck, self).__init__(test_log, arguments, cfg_opts, bios_config_file=None)

        if self._provisioning_result:
            self._log.info("Provisioning of DCPMM with 100% app direct has been done successfully!")
        else:
            raise content_exceptions.TestFail("Provisioning of DCPMM with 100% app direct mode failed!")

        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=self._provisioning_result)

        self.ddr_memtotal_with_variance_config = None

    def prepare(self):
        # type: () -> None
        """
        Function to verify ddr installed is equal to what os reports.

        :return: None
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # Get the Capacity of all dimms.
        ddr_capacity_os = self._memory_provider.get_total_system_memory()

        if isinstance(ddr_capacity_os, list):
            ddr_capacity_os = int(ddr_capacity_os[0].split(":")[1].strip("MB").strip().replace(",", "")) / 1024
        else:
            ddr_capacity_os = ddr_capacity_os / 1024

        self._log.info("Total DDR capacity as per configuration - {}".format(self._post_mem_capacity))

        # ddr memory with variance
        self.ddr_memtotal_with_variance_config = (self._post_mem_capacity - (self._post_mem_capacity *
                                                                             self._variance_percent))

        self._log.info("Total ddr capacity as per configuration with variance - {}".format(
            self.ddr_memtotal_with_variance_config))

        if int(ddr_capacity_os) < int(self.ddr_memtotal_with_variance_config) or int(ddr_capacity_os) > \
                self._post_mem_capacity:
            raise content_exceptions.TestFail("Total ddr dimm Capacity is not same as configuration.")

        self._log.info("Total memory Capacity is same as DDR memory capacity.")

        #  Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,

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
        self._log.info("Successfully executed ipmctl MEMORYRESOURCES command..")

        # Verify memory resources information
        self._memory_common_lib.verify_memory_resource_information(mem_resources_data)

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
        self._memory_common_lib.verify_socket_information(socket_op, cpu_locators)

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

        #  Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PICR1lmAppDirectMemoryResourceCheck, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if PICR1lmAppDirectMemoryResourceCheck.main() else Framework.TEST_RESULT_FAIL)
