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
import time
import os

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.provider_factory import ProviderFactory

import src.lib.content_exceptions as content_exceptions
from src.power_management.lib.reset_base_test import ResetBaseTest


class PowerManagementG3CyclingOsCycle(ResetBaseTest):
    """
    Testcase_id's : H92948-PI_Powermanagement_G3_Cycling_OS_Cycle_L
    This TestCase is Used to Perform G3 for given Number of Cycles and verify is if sut is booted to Os Level
    in all the G3 Cycles.
    """
    _BIOS_CONFIG_FILE = "cycling_bios_knobs.cfg"
    TEST_CASE_IDs = ["H92948", "PI_Powermanagement_G3_Cycling_OS_Cycle_L",
                     "H92947", "PI_Powermanagement_G3_Cycling_OS_Cycle_W"]
    G3_CYCLES = 10

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PowerManagementG3CyclingOsCycle object

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PowerManagementG3CyclingOsCycle, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.

        :return: None
        """
        super(PowerManagementG3CyclingOsCycle, self).prepare()

    def execute(self):
        """
        This Method is Used to Perform G3 for given Number of Cycles and verify is if sut is booted to Os Level
        in all the G3 Cycles.

        :return: True or False
        """
        mce_errors = []
        self.cng_log.__exit__(None, None, None)
        for cycle_number in range(1, self.G3_CYCLES + 1):
            self._log.info("G3 Cycle Iteration: %d", cycle_number)
            self._log.debug("Clear Mce Logs before starting the Test Case")
            self._common_content_lib.clear_mce_errors()

            start_time = time.time()
            serial_log_file = os.path.join(self.serial_log_dir, "serial_log_iteration_%d.log" % cycle_number)
            with ProviderFactory.create(self.cng_cfg, self._log) as cng_log:
                cng_log.redirect(serial_log_file)
                cycle_status = self.graceful_g3()
                end_time = time.time()
                boot_time = int(end_time - start_time)
                self._log.info("Cycle #{} completed with status code {}. Boot time for the "
                               "cycle is {}.".format(cycle_number, cycle_status, boot_time))
                errors = self._common_content_lib.check_if_mce_errors()
                if errors:
                    mce_errors.append("MCE Errors during the G3 Cycle{} are '{}'".format(cycle_number, errors))
                if cycle_status in self.reset_handlers.keys():
                    handler = self.reset_handlers[cycle_status]
                    ret_val = handler(cycle_number)
                else:
                    ret_val = self.default_reset_handler(cycle_number)
                cng_log.__exit__(None, None, None)
                if not ret_val:
                    self._log.error("Terminating the G3 cycling test..")
                    break
        # end of cycle test for loop

        self.print_result_summary()
        if mce_errors:
            raise content_exceptions.TestFail(mce_errors)

        self._log.info("Sut is booted back to OS in all the {} G3 Cycles and there are no Machine Check Errors "
                       "Logged".format(self.G3_CYCLES))
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PowerManagementG3CyclingOsCycle.main() else Framework.TEST_RESULT_FAIL)
