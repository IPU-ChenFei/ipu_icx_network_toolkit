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

from src.lib.test_content_logger import TestContentLogger
from src.lib.memory_constants import MemoryTopology
from src.lib import content_exceptions
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon
from src.memory.tests.memory_cr.crow_pass.pi_cr_2lm_osboot_l_w import PiCR2LMOsBoot


class PiCR2LMMemoryModeBasic(CrProvisioningTestCommon):
    """
    HP QC ID: H101109-PI_CR_2LM_MemoryModeBasic_L and H101154-PI_CR_2LM_MemoryModeBasic_W
    2LM Basic functionality check,verify 2LM: Memory mode provisioning.
    """

    TEST_CASE_ID = ["H101109", "PI_CR_2LM_MemoryModeBasic_L", "H101154", "PI_CR_2LM_MemoryModeBasic_W"]

    step_data_dict = {1: {'step_details': 'Boot the system with 2LM bios knobs.',
                          'expected_results': 'system booted with 2LM bios knobs.'},
                      2: {'step_details': 'Creating goal for 100% Memory mode.',
                          'expected_results': 'Created Goal for 100% Memory mode.'},
                      3: {'step_details': 'Verifying 100% memory mode goal in OS.',
                          'expected_results': 'Verified 100% memory mode goal in OS.'},
                      4: {'step_details': 'Reboot the system and boot to OS.',
                          'expected_results': 'Successfully boot to OS'},
                      5: {'step_details': 'Check if CR DIMM memory resource allocation across the host server '
                                          'is correct. ',
                          'expected_results': 'MemoryCapacity should be around 100% of CR DIMMS capacity.'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiCR2LMMemoryModeBasic object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiCR2LMMemoryModeBasic, self).__init__(test_log, arguments, cfg_opts)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._pi_cr_2lm_os_boot = PiCR2LMOsBoot(self._log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Verify DDR and CR dimm population as per configuration.
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._pi_cr_2lm_os_boot.prepare()
        result = self._pi_cr_2lm_os_boot.execute()

        if result:
            self._log.info("SUT booted with 2 LM ...")
        else:
            content_exceptions.TestFail("Got error in OS boot 2 LM test case ...")

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=result)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Check that detected DIMM in system has correct attribute values.
        2. Create goal for memory mode = 100.
        3. Verify the provisioning with memory capacity.

        :return: True, if the test case is successful.
        :raise: None
        """
        return_value = []

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # Get the DIMM information
        dimm_show = self._ipmctl_provider.get_memory_dimm_information()

        self._ipmctl_provider.delete_pmem_device()

        # Configure the capacity on all installed DCPMM(s) with 100% as memory mode
        dcpmm_disk_goal = self._ipmctl_provider.dcpmm_configuration(
            cmd=self.IPMCTL_CMD_FOR_100_PERCENT_MEMORY_MODE, cmd_str="with 100% memory mode")

        # Step Logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        # Verify the mode provisioning
        return_value.append(
            self.verify_app_direct_mode_provisioning(mode="mem", mode_percentage=100,
                                                     total_memory_result_data=dimm_show,
                                                     app_direct_result_data=dcpmm_disk_goal))

        self._log.info("Successfully provisioned crystal ridge DIMMS as 100% Memory Mode... Rebooting to apply the "
                       "changes ...")

        # Step Logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        # Restart the SUT
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        self._os.wait_for_os(self._reboot_timeout)

        # Step Logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        mem_resources_data = self._ipmctl_provider.show_mem_resources()
        self._log.debug("Memory resources info...{}".format(mem_resources_data))

        self._memory_common_lib.verify_provisioned_appdirect_capacity(mem_resources_data, r"Volatile.*")

        # Verify 2LM provisioning mode
        verify_provisioning_status = self._ipmctl_provider.verify_lm_provisioning_configuration(
            dcpmm_disk_goal, mode=MemoryTopology.TWO_LM)

        self._log.info("MemoryCapacity is around 100% of CR DIMMS' capacity..")

        # Step Logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=verify_provisioning_status)

        return return_value

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._ipmctl_provider.delete_pmem_device()
        super(PiCR2LMMemoryModeBasic, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiCR2LMMemoryModeBasic.main() else Framework.TEST_RESULT_FAIL)
