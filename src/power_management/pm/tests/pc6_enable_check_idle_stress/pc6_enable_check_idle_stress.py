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

from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.dtaf_constants import Framework

from src.power_management.socwatch_common import SocWatchBaseTest
from src.provider.socwatch_provider import PackageCStates, CoreCStates


class PC6EnableCheckIdleStress(SocWatchBaseTest):
    """
    HPQC ID : H82174 (Linux) / H87938 (Windows)
    This Test case Enable/Disable C-state and P-State bios knob, install SocWatch Tool/Burintest in the SUT
    and Execute the Socwatch command and burnintest. Verify the Package P-State residency percentage
    """
    TEST_CASE_ID = ["H82174", "PI_Powermanagement_PC6_Enable_Check_Idle-Stress_SoCwatch_L",
                    "H87938", "PI_PowerManagement_Power_PC6_Enable_Idle-Stress_W_Package_CState"]
    CSTATE_ENABLE_BIOS_CONFIG_FILE = "cstate_enable_bios_knobs.cfg"
    PC_STATE_ENABLE_BIOS_CONFIG_FILE = "cstate_pstate_enable_turbo_disable_bios_knobs.cfg"
    BURNING_CONFIG_FILE = "cmdline_config_50_workload.txt"
    BURNING_CONFIG_FILE_WINDOWS = "cmdline_config_50_workload_windows.bitcfg"
    SOCWATCH_RUN_TIME = 300
    BIT_TIMEOUT = 6  # in minutes
    SYSTEM_IDLE_TIME = 60

    PC6_THRESHOLD = 80
    PC6_CONDITION = "%s > " + str(PC6_THRESHOLD)
    CC6_THRESHOLD = 90
    CC6_CONDITION = "%s > " + str(CC6_THRESHOLD)
    PC0_THRESHOLD = 99
    PC0_CONDITION = "%s > " + str(PC0_THRESHOLD)
    PC6_PCSTATE_ENABLE_THRESHOLD = 0.1
    PC6_PCSTATE_ENABLE_CONDITION = "%s > " + str(PC6_PCSTATE_ENABLE_THRESHOLD)

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of PC6EnableCheckIdleStress

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.cstate_enable_bios = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               self.CSTATE_ENABLE_BIOS_CONFIG_FILE)
        self.cstate_enable_pstate_enable_bios = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                             self.PC_STATE_ENABLE_BIOS_CONFIG_FILE)
        super(PC6EnableCheckIdleStress, self).__init__(test_log, arguments, cfg_opts, self.cstate_enable_bios)

        if self.os.os_type == OperatingSystems.LINUX:
            self.burnin_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   self.BURNING_CONFIG_FILE)
        elif self.os.os_type == OperatingSystems.WINDOWS:
            self.burnin_config_file = Path(os.path.dirname(os.path.abspath(__file__))).parent
            self.burnin_config_file = os.path.join(self.burnin_config_file, self.BURNING_CONFIG_FILE_WINDOWS)
        else:
            raise NotImplementedError("not implemented for this OS %s" % self._os.os_type)

    def prepare(self):
        # type: () -> None
        """
        This function will load bios defaults to SUT and Check the mce errors
        """
        super(PC6EnableCheckIdleStress, self).prepare()

    def execute(self):
        """
        This function install socwatch and burnin, execute socwath and burnin tool
        Copy CSV file to host, read and verify the C-state values
        Setting the C-state, P-state bios to enable and repeat the steps as above

        :return: True if test completed successfully, False otherwise.
        """
        # Brunin tool workload time is "0-ZERO"
        self.execute_socwatch_tool(socwatch_runtime=self.SOCWATCH_RUN_TIME, burnin_config_file=self.burnin_config_file,
                                   system_idle_timeout=self.SYSTEM_IDLE_TIME, execute_stress=False)
        # Verify the Core/Package C-state residency values
        self._log.info("Verify Package C-State residency percentage for PC6 > {}".format(self.PC6_THRESHOLD))
        # Verify PC6 package
        self.csv_reader_obj.verify_pacakge_c_state_residency(PackageCStates.PACKAGE_C_STATE_PC6, self.PC6_CONDITION %
                                                             PackageCStates.PACKAGE_C_STATE_PC6)
        # Verify C6 package
        self._log.info("Verify Core C-State residency percentage CC6 > {}".format(self.CC6_THRESHOLD))
        self.csv_reader_obj.verify_core_c_state_residency(CoreCStates.CORE_C_STATE_CC6,
                                                          self.CC6_CONDITION % CoreCStates.CORE_C_STATE_CC6)

        # Step2: Disable the Turbo mode bios
        self.set_verify_bios_knobs(self.cstate_enable_pstate_enable_bios)
        self.execute_socwatch_tool(self.SOCWATCH_RUN_TIME, self.burnin_config_file, self.BIT_TIMEOUT,
                                   self.SYSTEM_IDLE_TIME, execute_stress=True)
        # Verify the Core/Package C-state residency values
        self._log.info("Verify Package C-State residency percentage for PC0~{}/PC6~{}".format(self.PC0_THRESHOLD,
                                                                                              self.PC6_PCSTATE_ENABLE_THRESHOLD))
        # Verify PC0 package
        self.csv_reader_obj.verify_pacakge_c_state_residency(PackageCStates.PACKAGE_C_STATE_PC0, self.PC0_CONDITION %
                                                             PackageCStates.PACKAGE_C_STATE_PC0)
        # Verify PC6 package
        self.csv_reader_obj.verify_pacakge_c_state_residency(PackageCStates.PACKAGE_C_STATE_PC6,
                                                             self.PC6_PCSTATE_ENABLE_CONDITION %
                                                             PackageCStates.PACKAGE_C_STATE_PC6)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PC6EnableCheckIdleStress.main() else Framework.TEST_RESULT_FAIL)
