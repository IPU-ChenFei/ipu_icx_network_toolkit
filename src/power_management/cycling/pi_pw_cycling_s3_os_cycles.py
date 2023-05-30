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
from dtaf_core.providers.provider_factory import ProviderFactory

import src.lib.content_exceptions as content_exceptions
from src.power_management.lib.reset_base_test import ResetBaseTest
from src.lib.dtaf_content_constants import ResetStatus


class PwCyclingS3OSCycles(ResetBaseTest):
    """
    HPQC ID : H82181

    This TestCase is Used to Perform shutdown for given Number of Cycles and verify is if sut is booted to Os Level
    in all the shutdown Cycles..
    """
    _BIOS_CONFIG_FILE = "dpmo_cycling_bios_knobs.cfg"
    TEST_CASE_ID = ["H82181"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PwCyclingS5OSCycles object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PwCyclingS3OSCycles, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Copy mcelog.conf file to sut and reboot
        2. Clear All Os Logs before Starting the Test Case
        3. Set the bios knobs to its default mode.
        4. Set the bios knobs as per the test case.
        5. Reboot the SUT to apply the new bios settings.
        6. Verify the bios knobs whether they updated properly.

        :return: None
        """
        super(PwCyclingS3OSCycles, self).prepare()

    def execute(self):
        """
        This Method is Used to execute SUT should be able to boot correctly the 10 times and also
        verify_machine_check_errors_in_various_dc_cycles and verifying status of MCE in every Cycle

        :return: True or False
        :raise: content_exceptions.TestFail
        """
        test_status = True
        s3_reset_cycles = self._common_content_configuration.get_num_of_s3_cycles()
        self._log.info("Number of S3 cycles to be executed: %d", s3_reset_cycles)
        if self.health_check:
            self.baseline_pcie_health_check()
        self.cng_log.__exit__(None, None, None)
        for cycle_number in range(1, s3_reset_cycles + 1):
            self._log.info("******* Cycle number %d started *******", cycle_number)
            self._failed_pc = None
            self._boot_flow = None
            self.set_register_before_reset(cycle_number=cycle_number, reset_type="warm_reset")

            if not self.ignore_mce_error:
                self._log.info("Clearing MCE logs")
                self._common_content_lib.clear_mce_errors()
            start_time = time.time()
            serial_log_file = os.path.join(self.serial_log_dir, "serial_log_iteration_%d.log" % cycle_number)
            with ProviderFactory.create(self.cng_cfg, self._log) as self.cng_log:
                self.cng_log.redirect(serial_log_file)
                # below function will update class variable self._failed_pc
                cycle_status = self.perform_s3_cycle()
                end_time = time.time()
                boot_time = int(end_time - start_time)
                self._log.info("Cycle #{} completed with status code {}. Boot time for the "
                               "cycle is {}.".format(cycle_number, cycle_status, boot_time))
                if cycle_status in self.reset_handlers.keys():
                    handler = self.reset_handlers[cycle_status]
                    ret_val = handler(cycle_number)
                else:
                    ret_val = self.default_reset_handler(cycle_number)
                if not ret_val:
                    self._log.error("Terminating the warm reset cycling test..")
                    break
        # end of cycle test for loop

        # print test summary here
        if self._number_of_failures > 0:
            test_status = False
        self.print_result_summary()

        return test_status


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PwCyclingS3OSCycles.main()
             else Framework.TEST_RESULT_FAIL)
