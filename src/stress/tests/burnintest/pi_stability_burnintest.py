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

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import TimeConstants
from src.provider.stressapp_provider import StressAppTestProvider


class StabilityBurnInTest(ContentBaseTestCase):
    """
    HPQC ID : H82202-PI_Stress_Stability_BurnInTest_L
    This Test case install BurnInTest tool and execute burnintest to stress the system with specific percentage
    """
    TEST_CASE_ID = ["H82202", "PI_Stress_Stability_BurnInTest_L"]
    BURNING_60_WORKLOAD_CONFIG_FILE = "cmdline_config_60_workload.txt"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of StabilityBurnInTest

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(StabilityBurnInTest, self).__init__(test_log, arguments, cfg_opts)
        self.burnin_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               self.BURNING_60_WORKLOAD_CONFIG_FILE)
        self.stress_app_provider = StressAppTestProvider.factory(test_log, os_obj=self.os, cfg_opts=cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        This function load bios defaults to SUT
        """
        super(StabilityBurnInTest, self).prepare()

    def execute(self):
        """
        This function install burnin tool, execute burnin tool with 60% of workload

        :return: True if test completed successfully, False otherwise.
        """
        # install burnin tool
        bit_location = self.collateral_installer.install_burnintest()
        self.stress_app_provider.execute_burnin_test(self.log_dir, TimeConstants.FORTY_EIGHT_HOURS/60, bit_location,
                                                     self.burnin_config_file)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StabilityBurnInTest.main() else Framework.TEST_RESULT_FAIL)
