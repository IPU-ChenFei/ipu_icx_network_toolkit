"""
!/usr/bin/env python
#########################################################################
INTEL CONFIDENTIAL
Copyright Intel Corporation All Rights Reserved.

The source code contained or described herein and all documents related to
the source code ("Material") are owned by Intel Corporation or its suppliers
or licensors. Title to the Material remains with Intel Corporation or its
suppliers and licensors. The Material may contain trade secrets and proprietary
and confidential information of Intel Corporation and its suppliers and
licensors, and is protected by worldwide copyright and trade secret laws and
treaty provisions. No part of the Material may be used, copied, reproduced,
modified, published, uploaded, posted, transmitted, distributed, or disclosed
in any way without Intel's prior express written permission.

No license under any patent, copyright, trade secret or other intellectual
property right is granted to or conferred upon you by disclosure or delivery
of the Materials, either expressly, by implication, inducement, estoppel or
otherwise. Any license under such intellectual property rights must be express
and approved by Intel in writing.3
#########################################################################
"""
import sys
import os
import time
from dtaf_core.lib.dtaf_constants import Framework
from src.seamless.tests.bmc.constants.pm_constants import SocwatchWindows, CoreCStates
from src.seamless.lib.pm_common import PmCommon, SocwatchCommon
from src.seamless.tests.bmc.constants import pm_constants


class PmScript(PmCommon, SocwatchCommon):
    """
    This class contains all callable PM Functions
    """
    BIOS_CONFIG_FILE = "socwatch_bios_knobs.cfg"
    bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), BIOS_CONFIG_FILE)

    def __init__(self, test_log, arguments, cfg_opts):
        super().__init__(test_log, arguments, cfg_opts)
        self.capsule_path = self._common_content_configuration.get_sps_n_capsule_operational()
        self.expected_ver = self._common_content_configuration.get_sps_n_version_operational()
        self.command_timeout = self._common_content_configuration.get_command_timeout()
        self.start_workload = None
        self.sps_mode = None
        self.warm_reset = None
        self.update_type = None
        self.activation = None
        self.ptu = arguments.ptu
        self.socwatch = arguments.socwatch
        self.cc6_value = arguments.cc6_value
        self.c0_value = arguments.c0_value
        self.c6_value = arguments.c6_value
        self.ptu_cmd = arguments.ptu_cmd

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument('--ptu', action='store_true',
                            help="Add argument if ptu workload to be performed")
        parser.add_argument('--socwatch', action='store_true',
                            help="Add argument if socwatch workload to be performed")
        parser.add_argument('--cc6_value', action='store', help="Add argument if cc6 workload to be performed")
        parser.add_argument('--c0_value', action='store', help="Add argument if c0  workload to be performed")
        parser.add_argument('--c6_value', action='store', help="Add argument if c6  workload to be performed")
        parser.add_argument('--ptu_cmd', action='store', help="Add argument if ptu  stress to be performed")

    def get_current_version(self, echo_version=True):
        """
        Read sps version
        :param echo_version: True if display output
        :return sps version
        """
        return self.get_sps_ver()

    def check_capsule_pre_conditions(self):
        # type: () -> None
        # To-Do add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        # type: () -> None
        # To-Do add workload output analysis
        return True

    def prepare(self):
        """
        Create test summary logger object
        Check for command line arguments
        """
        super().prepare()

    def execute(self):
        """
        This function executes all PTU and Socwatch callable functions
        :return: True if the test case is pass
        """
        # Setting the bios knob
        self.bios_knob_change(self.bios_config_file)
        if self.ptu:
            self.check_ptu_tool()
            self.install_ptu_tool()
            self._log.info("ptu is copied")
            if not self.check_ptu_tool():
                self._log.error("PTU tool is not available in SUT")
                raise RuntimeError("PTU tool is not available in SUT")
            self.deleting_file()
            self.execute_ptu_tool()
            time.sleep(pm_constants.COMMAND_TIMEOUT)
            self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
            time.sleep(pm_constants.TIMEOUT)
            self.kill_ptu_tool()
            self.deleting_csv_files_in_host()
            self.copy_csv_file_from_sut_to_host()
            self.read_csv_file()
        if self.socwatch:
            self.check_socwatch_tool()
            self.install_socwatch_tool()
            self._log.info("socwatch is copied")
            if not self.check_socwatch_tool():
                self._log.error("Socwatch tool is not available in SUT")
                raise RuntimeError("Socwatch tool is not available in SUT")
            self.execute_socwatch_tool()
            time.sleep(SocwatchWindows.COMMAND_TIMEOUT)
            self.copy_socwatch_csv_file_from_sut_to_host()
            self.verify_core_c_state_residency_frequency(CoreCStates.CORE_C_STATE_CC6,
                                                         CoreCStates.CC6_CONDITION %
                                                         CoreCStates.CORE_C_STATE_CC6)
            self.verify_pacakge_p_state_frequency()
        return True

    def cleanup(self, return_status):
        super().cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if
             PmScript.main()
             else Framework.TEST_RESULT_FAIL)
