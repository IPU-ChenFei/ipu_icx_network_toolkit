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
import os
import six

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.lib.dtaf_constants import Framework

from src.power_management.socwatch_common import SocWatchBaseTest
from src.provider.socwatch_provider import PackageCStates, CoreCStates


class CStateEnableCheckWindows(SocWatchBaseTest):
    """
    HPQC ID : H87943-PI_PowerManagement_Power_Cstate_Enable_Socwatch_W
    This Test case install SocWatch Tool/Burintest in the SUT and Execute the Socwatch command and burnintest
    Verify the Package C-State and Core C-state residency values
    """
    TEST_CASE_ID = ["H87943", "PI_PowerManagement_Power_Cstate_Enable_Socwatch_W"]
    BIOS_CONFIG_FILE_DISABLE = "power_cstate_enable_bios_knobs.cfg"
    BURNING_50_WORKLOAD_CONFIG_FILE = "cmdline_config_50_workload_windows.bitcfg"
    SOCWATCH_RUN_TIME = 900  # in seconds
    CC6_THRESHOLD = 70

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of CStateEnableCheckWindows

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """

        self.cstate_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               self.BIOS_CONFIG_FILE_DISABLE)
        super(CStateEnableCheckWindows, self).__init__(test_log, arguments, cfg_opts,
                                                       bios_config_file_path=self.cstate_bios_enable)
        self.burnin_config_file = Path(os.path.dirname(os.path.abspath(__file__))).parent

        self.burnin_config_file = os.path.join(self.burnin_config_file, self.BURNING_50_WORKLOAD_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        This function will Clear the mce errors and load bios defaults to SUT
        """
        super(CStateEnableCheckWindows, self).prepare()

    def execute(self):
        """
        This function install socwatch and burnin tool, execute socwatch and burnin tool
        Copy CSV file to host, read and verify the C-state values

        :return: True if test completed successfully, False otherwise.
        """

        self.execute_socwatch_tool(self.SOCWATCH_RUN_TIME, execute_stress=False)

        # Verify the Core C-state residency values
        self.csv_reader_obj.verify_core_c_state_residency(CoreCStates.CORE_C_STATE_CC6, "%s > %d" % (
            CoreCStates.CORE_C_STATE_CC6, self.CC6_THRESHOLD))

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CStateEnableCheckWindows.main() else Framework.TEST_RESULT_FAIL)
