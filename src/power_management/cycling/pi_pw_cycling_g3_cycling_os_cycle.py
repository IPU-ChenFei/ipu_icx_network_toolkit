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
import threading

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory

import src.lib.content_exceptions as content_exceptions
from src.power_management.lib.reset_base_test import ResetBaseTest
from src.lib.dtaf_content_constants import ResetStatus


class VerifyG3PowerCyclingOSCycle(ResetBaseTest):
    """
    Testcase_id : H91197
    This TestCase is Used to Verify the G3 Power Cycles
    """
    _BIOS_CONFIG_FILE = "dpmo_cycling_bios_knobs.cfg"
    TEST_CASE_ID = ["H91197", "PI_PW_Cycling_G3_Cycling_OS_Cycle_L"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VerifyG3PowerCyclingOSCycle object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyG3PowerCyclingOSCycle, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Power on the SUT and boot to BIOS Setup.
            Modify this changes:
            EDKIT Menu > Platform Configuration > PCH IO configuration > State After G3 = S0
            Save changes and reboot the SUT
        2. Press the power button to boot to OS
        3. After system boot to OS open a terminal and run 'poweroff'
           After SUT is off remove AC cord from the system until all leds on the board are off.
        4. Connect the the AC back and system will  boot to OS automatically
        5. Repeat this process as per DPMO number defined on the SUT

        :return: None
        """
        super(VerifyG3PowerCyclingOSCycle, self).prepare()

    def execute(self):
        """
        This Method is Used to execute VerifyG3PowerCyclingOSCycleLinux and verifying status of MCE in
        every Cycle

        :return: True or False
        """
        test_status = True
        g3_cycles = self._common_content_configuration.get_num_of_g3_dpmo_cycles()
        ignore_mce_error = self._common_content_configuration.get_ignore_mce_errors_value()

        self._log.info("Number of G3 cycles to be executed: %d", g3_cycles)
        if self.health_check:
            self.baseline_pcie_health_check()

        self.cng_log.__exit__(None, None, None)
        for cycle_number in range(1, g3_cycles + 1):
            self._log.info("******* Cycle number %d started *******", cycle_number)
            self._failed_pc = None
            self._boot_flow = None
            if not ignore_mce_error:
                self._log.info("Clearing MCE logs")
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

        # print test summary here
        test_status = True
        if self._number_of_failures > 0:
            test_status = False
        self.print_result_summary()

        return test_status

    def cleanup(self, return_status):
        super(VerifyG3PowerCyclingOSCycle, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyG3PowerCyclingOSCycle.main() else Framework.TEST_RESULT_FAIL)

