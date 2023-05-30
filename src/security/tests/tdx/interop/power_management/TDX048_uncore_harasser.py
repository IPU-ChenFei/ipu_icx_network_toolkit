#!/usr/bin/env python
##########################################################################
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
##########################################################################
"""
    :Uncore Harasser with TDX:

    Launch a given number of TD guests and run uncore harasser pm_utis test suite on the SUT for prescribed amount of
    time."""

import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.interop.power_management.pm_utils_base_test import TdxPmUtilsBaseTest


class TdxUncoreHarasser(TdxPmUtilsBaseTest):
    """
           This is a test for testing with pm_utils suite with TD guests as part of the TDX feature.

           The following parameters in the content_configuration.xml file should be populated before running a test.

            Change <TDX><num_of_vms> to control the number of TD guests that will be run in parallel.
            Change <security><power_management><pmutils_timeout> to control how long the test will run.  Please note
            pm_utils time parameter takes in minutes, not seconds.

            :Scenario: Launch the number of TD guests prescribed, initiate uncore harasser pm_utils on the SUT, run
            pm_utils for the necessary time to complete the tests, then verify the SUT and the TD guests have not
            crashed.

            :Phoenix IDs:  22013350360

            :Test steps:

                :1: Launch a TD guest.

                :2: On SUT, build and launch pm_utils test suite.

                :3: Run until workload tests complete.

            :Expected results: Each TD guest should boot and the pm_utils test suite should run to completion with no
            errors on the SUT or any of the TD guests.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new object for TdxRaplHarasser

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(TdxUncoreHarasser, self).__init__(test_log, arguments, cfg_opts)
        self.pm_util_timeout = self._common_content_configuration.security_pmutils_running_time()
        self.pm_util_cmd = self.tdx_consts.PmUtilsCmds.PMUTILS_UNCORE_HARASSER.format(self.pm_util_timeout)  # command

    def execute(self):
        return super(TdxUncoreHarasser, self).execute()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxUncoreHarasser.main() else Framework.TEST_RESULT_FAIL)
