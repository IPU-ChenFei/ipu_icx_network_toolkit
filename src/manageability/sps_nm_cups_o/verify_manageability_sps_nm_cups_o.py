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
import os
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.miv.miv_common import MivCommon
from src.provider.cpu_info_provider import CpuInfoProvider


class VerifyManageabilitySpsNmCupsO(MivCommon):
    """
    HPQC ID: 80229-PI_Manageability_SPS_NM_CUPS_O
    This Testcase is basically to Verify Core Sensor Reading.
    """
    _50_PERCENTAGE_OF_CORES = 50
    _100_PERCENTAGE_OF_CORES = 100
    _TIME_DELAY = 120
    _WAIT_TIME = 10

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new  VerifyManageabilitySpsNmCupsO object.

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyManageabilitySpsNmCupsO, self).__init__(test_log, arguments, cfg_opts)
        self._cpu_info_provider = CpuInfoProvider.factory(self._log, cfg_opts, self._os)  # type: CpuInfoProvider

    def prepare(self):  # type: () -> None
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """
        self.use_ping = True
        self.use_getdeviceid = True
        super(VerifyManageabilitySpsNmCupsO, self).prepare()

    def execute(self):
        """
        Execute Main test case.

        Testcase Flow:
        step1 : Run PTU with 100 % of cores to stress single CPU
        step2 : Save Node Manager Statistics data by running statistics.tdf
        step3 : Run PTU with 100% of Cores to stress all CPU
        step4 : Save the Node Manager Statistics by running statistics.tdf
        step5 : Compare Get Node Manager Statistics

        :return: True if test completed successfully, False otherwise.
        """
        ret_value = True
        self.ptu_path = self._ptu_provider.install_ptu()
        power_value_with_single_cpu_stressed = 0
        power_value_with_all_cpu_stressed = 0
        # Run PTU to stress single CPU
        ptu_run = self.run_ptu_stress_tool_on_given_cpu(0x1)
        self._log.info("Started ptu stress tool on single CPU")
        if ptu_run:
            self._log.info("Running the PTU tool for {} seconds".format(self._TIME_DELAY))
            # we need to run the ptu for atleast 120 seconds hence the delay
            time.sleep(self._TIME_DELAY)
            power_value_with_single_cpu_stressed = int(self.run_statistics_on_domain1())
            self._log.info("Average Power Value when single cpu is stressed : {}".format(power_value_with_single_cpu_stressed))
            self._ptu_provider.kill_ptu_tool()
            time.sleep(self._WAIT_TIME)

        # Run PTU to stress all CPU
        self.run_ptu_stress_tool_on_given_cpu(self.ALL_CPU)
        self._log.info("Started ptu stress tool on all CPU")
        if ptu_run:
            self._log.info("Running the PTU tool for {} seconds".format(self._TIME_DELAY))
            # we need to run the ptu for atleast 120 seconds hence the delay
            time.sleep(self._TIME_DELAY)
            power_value_with_all_cpu_stressed = int(self.run_statistics_on_domain1())
            self._log.info("Average Power Value when all cpus are stressed : {}".format(power_value_with_all_cpu_stressed))
            self._ptu_provider.kill_ptu_tool()

        self._log.info("Compare Get Node Manager Statistics values of single and all cpu stressed values.")
        if power_value_with_single_cpu_stressed >= power_value_with_all_cpu_stressed:
            error = "Core Sensor reading verification failed! Power value when single cpu is stressed " \
                    "is greater when compared to all cpu stressed with 100% of cores"
            self._log.error(error)
            raise content_exceptions.TestFail(error)

        self._log.info("Core Sensor reading Verified! Power value when single cpu is stressed "
                       "is less when compared to all cpu stressed with 100% of cores")
        return ret_value


# Execute this test with TestEngine when run as main.
if __name__ == '__main__':
    sys.exit(Framework.TEST_RESULT_PASS if VerifyManageabilitySpsNmCupsO.main() else Framework.TEST_RESULT_FAIL)
