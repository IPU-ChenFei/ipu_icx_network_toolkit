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

from src.power_management.lib.reset_base_test import ResetBaseTest
import src.lib.content_exceptions as content_exceptions


class PowerManagementBasicWarmReset(ResetBaseTest):
    """
    Testcase_id : H92918 - PI_Powermanagement_Basic_Warm_Reset_W, H92919 - PI_Powermanagement_Basic_Warm_Reset_L
    This TestCase is Used to Check there has no harm to SUT when the AC is cut-off during boot up
    or shutdown.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PowerManagementBasicWarmReset object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PowerManagementBasicWarmReset, self).__init__(test_log, arguments, cfg_opts)

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
        super(PowerManagementBasicWarmReset, self).prepare()

    def execute(self):
        """
        This Method is Used to verify status of MCE in Every Warm Reset of 10 Cycles'

        :return: True or False
        """
        mce_errors = []
        for cycle_number in range(self._common_content_configuration.get_num_of_reboot_cycles()):
            self._log.info("Reboot cycle %d", cycle_number)
            self._common_content_lib.clear_mce_errors()
            self.warm_reset()
            errors = self._common_content_lib.check_if_mce_errors()
            if errors:
                mce_errors.append("MCE Errors during the Cycle_{} are '{}'".format(cycle_number, errors))

        if mce_errors:
            raise content_exceptions.TestFail("\n".join(mce_errors))

        self._log.info("Sut is booted back to OS in all the '{}' Reboot Cycles and there are no Machine Check "
                       "Errors Logged".format(self._common_content_configuration.get_num_of_reboot_cycles()))
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PowerManagementBasicWarmReset.main() else Framework.TEST_RESULT_FAIL)
