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
    :Prime95 stress test on TD guest:

    Launch a given number of TD guests and run prime95 on each TD guest for prescribed amount of time.
"""
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.workloads.tdvm_workload_base_test import TDGuestWorkloadBaseTest


class TDGuestMprime(TDGuestWorkloadBaseTest):
    """
            This recipe tests TD guest boot and requires the use of a OS supporting TD guest.  The parameters of
            this test can be customized by the settings in the content_configuration.xml.

            Change <TDX><num_of_vms> to control the number of TD guests that will be run in parallel.

            Change <security><mprime_running_time> to control the number of seconds that mprime will be run for;
            minimum enforced run time is 1 hr.

            :Scenario: Launch the number of TD guests prescribed, initiate mprime on each TD guest, run for the
             prescribed amount of time per above parameters, then verify the SUT and the TD guests have not crashed.

            :Phoenix ID: 18014073959

            :Test steps:

                :1: Launch a TD guest.

                :2: On TD guest, launch mprime.

                :3: Repeat steps 1 and 2 for the prescribed number of TD guests.

                :4: Run for prescribed amount of time (refer to beginning of this section for how to change the time).

            :Expected results: Each TD guest should boot and mprime should run for the prescribed amount of time with
            no errors on the SUT or any of the TD guests.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new object for TDGuestMprime

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(TDGuestMprime, self).__init__(test_log, arguments, cfg_opts)
        self._tool_sut_folder_path = self.install_collateral.install_prime95().strip() + "/"
        self._tool_name = self.tdx_consts.WorkloadToolNames.MPRIME
        self._tool_run_time = self._common_content_configuration.security_mprime_running_time()
        if self._tool_run_time < self.tdx_consts.TimeConstants.HOUR_IN_SECONDS:
            self._log.warning("Time set in config file is less than an hour; setting run time to an hour.")
            self._tool_run_time = self.tdx_consts.TimeConstants.HOUR_IN_SECONDS
        self._tool_run_cmd = self.tdx_consts.MPRIME_CMD
        self._tool_build_cmd = ""  # no build needed, tool comes pre-built

    def execute(self):
        return super(TDGuestMprime, self).execute()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDGuestMprime.main() else Framework.TEST_RESULT_FAIL)
