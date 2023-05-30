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
from src.lib.dtaf_content_constants import SlotConfigConstant
from src.lib.test_content_logger import TestContentLogger
from src.lib.memory_constants import MemoryTopology
from src.memory.tests.memory_cr.crow_pass.cps_common import CpsTestCommon


class PiCR2LMOsBoot(CpsTestCommon):
    """
    HP QC  ID: 101113-PI_CR_2LM_OSBoot_L (linux) and H101158-PI_CR_2LM_OSBoot_W (Windows)

    2LM Basic functionality check,verify if system is able to boot into OS with CR DIMMs installed.
    """

    TEST_CASE_ID = ["H101113", "PI_CR_2LM_OSBoot_L", "H101158", "PI_CR_2LM_OSBoot_W"]

    step_data_dict = {1: {'step_details': 'verify SUT has 8+8 (CPS + memory)in SUT.Clear OS logs and Set the bios '
                                          'knobs and verify bios knobs',
                          'expected_results': 'verified 8+8 config. Clear ALL the system Os logs and BIOS setting '
                                              'done and Verified the bios knobs.'},
                      2: {'step_details': 'Check the detected DIMM in system.',
                          'expected_results': 'Display all of installed DIMMs with correct attributes values '
                                              'Capacity: same as config & Health state:Healthy'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiCR2LMOsBoot object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        """
        # calling base class init
        super(PiCR2LMOsBoot, self).__init__(test_log, arguments, cfg_opts, mode=MemoryTopology.TWO_LM)

        self.cps_common = CpsTestCommon(test_log, arguments, cfg_opts, mode=MemoryTopology.TWO_LM)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        1. Verify DDR + CPS with 8 + 8 configuration.
        2. Set the bios knobs as per the test case and Reboot the SUT and Verify the bios knobs that are set.
        3. Install ipmctl tool.

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

        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Check that detected DIMM in system has correct attribute values.

        :return: True, if the test case is successful.
        :raise: None
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # Get the DIMM information
        dimm_show = self._ipmctl_provider.get_memory_dimm_information()

        # Get the list of dimms which are healthy and log them.
        self._ipmctl_provider.get_list_of_dimms_which_are_healthy()

        # Verify the list of dimms which are healthy
        self._ipmctl_provider.verify_all_dcpmm_dimm_healthy()

        return_value = self._memory_common_lib.verify_cr_memory_with_config(show_dimm=dimm_show)

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=return_value)

        return return_value

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiCR2LMOsBoot, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiCR2LMOsBoot.main() else Framework.TEST_RESULT_FAIL)
