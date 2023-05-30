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

import src.lib.content_exceptions as content_exceptions
from src.power_management.lib.reset_base_test import ResetBaseTest


class PowerManagementAcCycles(ResetBaseTest):
    """
    Testcase_id : H72221
    This TestCase is Used to Verify MCE Logged Status by Performing AC Cycles and verifying the status in Every Cycle.
    """
    _BIOS_CONFIG_FILE = "cycling_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PowerManagementAcCycles object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PowerManagementAcCycles, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

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
        super(PowerManagementAcCycles, self).prepare()

    def execute(self):
        """
        This Method is Used to execute verify_machine_check_errors_in_various_ac_cycles and verifying status of MCE in
        every Cycle

        :return: True or False
        """
        for cycle_number in range(self._common_content_configuration.get_num_of_ac_cycles()):
            self.surprise_g3()
            if self._common_content_lib.check_if_linux_mce_errors():
                log_error = "Machine Check errors are Logged in Ac Cycle '{}'".format(cycle_number)
                self._log.error(log_error)
                raise content_exceptions.TestFail(log_error)
            self._log.info("No Machine Check Errors are Logged in Ac Cycle '{}'".format(cycle_number))
        self._log.info("Machine Check Events Status is Verified in all the 10 Ac Cycles and No Machine Check Errors are"
                       " Logged.")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PowerManagementAcCycles.main() else Framework.TEST_RESULT_FAIL)
