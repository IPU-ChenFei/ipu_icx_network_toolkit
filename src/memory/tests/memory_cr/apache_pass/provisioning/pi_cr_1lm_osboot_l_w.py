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
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon
from src.lib import content_exceptions


class PlCR1lmOsBoot(CrProvisioningTestCommon):
    """
    HP QC ID: H79516 (Linux) and H82151 (Windows)
    1LM Basic functionality check,verify if system is able to boot into OS with CR DIMMs installed.
    """

    BIOS_CONFIG_FILE = "pi_cr_1lm_osboot_bios_knob.cfg"
    TEST_CASE_ID = "H79516/H82151_PI_CR_1LM_OSBoot"

    step_data_dict = {1: {'step_details': 'Clear OS logs and Set the bios knobs',
                          'expected_results': 'Clear ALL the system Os logs and BIOS setting done.'},
                      2: {'step_details': 'Restart the system, Boot to OS properly and verify the bios knobs.',
                          'expected_results': 'Successfully boot to OS & Verified the bios knobs.'},
                      3: {'step_details': 'Check the detected DIMM in system.',
                          'expected_results': 'Display all of installed DIMMs with correct attributes values '
                                              'Capacity: same as config & Health state:Healthy'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PICR1lmOsBoot object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PlCR1lmOsBoot, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

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
        self._common_content_lib.clear_all_os_error_logs()  # TO clear Os logs
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        self._common_content_lib.perform_os_reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        # Step Logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Check that detected DIMM in system has correct attribute values.

        :return: True, if the test case is successful.
        :raise: None
        """
        return_value = True

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        #  Get the DIMM information
        dimm_show = self._ipmctl_provider.get_memory_dimm_information()

        # Get the list of dimms which are healthy and log them.
        self._ipmctl_provider.get_list_of_dimms_which_are_healthy()

        # Verify the list of dimms which are healthy
        self._ipmctl_provider.verify_all_dcpmm_dimm_healthy()

        # Get the Capacity of all dimms.
        sum_dimm_capacity = sum(self._memory_common_lib.get_total_dimm_memory_data(dimm_show))

        self._log.info("Total dimm capacity shown from OS level - {}".format(int(sum_dimm_capacity)))
        self._log.info("Total dimm capacity as per configuration - {}".format(self._dcpmm_mem_capacity))

        # memory with variance
        memtotal_with_variance_config = (self._dcpmm_mem_capacity - (self._dcpmm_mem_capacity *
                                                                         self._variance_percent))

        self._log.info("Total dimm capacity as per configuration with variance is - {}".format(
            memtotal_with_variance_config))

        if int(sum_dimm_capacity) < memtotal_with_variance_config or int(sum_dimm_capacity) > \
                self._dcpmm_mem_capacity:
            raise content_exceptions.TestFail("Total dcpmm dimm Capacity is not same as installed capacity from"
                                              " configuration.")
        elif int(sum_dimm_capacity) >= int(memtotal_with_variance_config):
            self._log.info("Total dcpmm dimm Capacity is same as installed capacity from configuration.")

        # Step Logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        return return_value

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PlCR1lmOsBoot, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PlCR1lmOsBoot.main()
             else Framework.TEST_RESULT_FAIL)
