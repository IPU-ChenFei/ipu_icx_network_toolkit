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
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.tests.bmc.constants.ras_constants import RasWindows, RasLinux
from src.seamless.lib.ras_common import RasCommon



class RasScript(RasCommon):
    """
    This class contains all callable RAS Functions
    """
    BIOS_CFG = r"..\configuration\\"

    def __init__(self, test_log, arguments, cfg_opts):
        super().__init__(test_log, arguments, cfg_opts)
        self.capsule_path = arguments.capsule_path
        self.expected_ver = arguments.expected_ver
        self.capsule_path2 = arguments.capsule_path2
        self.expected_ver2 = arguments.expected_ver2
        self.capsule_path3 = arguments.capsule_path3
        self.expected_ver3 = arguments.expected_ver3
        self.command_timeout = self._common_content_configuration.get_command_timeout()
        self.start_workload = None
        self.sps_mode = None
        self.warm_reset = None
        self.update_type = None
        self.activation = None
        self.error_inj_flag = True
        self.STAGING_REBOOT = None
        self.error_type = arguments.error_type
        self.error = self.error_type
        self.err_inj = arguments.err_inj
        self.capsle_path = arguments.capsle_path
        self.capsule_type = arguments.capsule_type
        self.loop_count = arguments.loop
        self.bios_knob = arguments.bios_knob
        self.ac_on_off = arguments.ac_on_off


    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument('--capsule_path', action='store', help="Path to the capsule to be used for the update",
                            default="")
        parser.add_argument('--loop', type=int, default=1, help="Add argument for # of loops")
        parser.add_argument('--bios_knob', action='store', help="Add argument for bios knobs to be enabled")
        parser.add_argument('--capsule_type', action='store', help="Type of the capsule to be used",
                            default="")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update",
                            default="")
        parser.add_argument('--capsule_path2', action='store', help="Path to the 2nd capsule to be used for the update",
                            default="")
        parser.add_argument('--capsule_path3', action='store', help="Path to the 3rd capsule to be used for the update",
                            default="")
        parser.add_argument('--expected_ver2', action='store', help="The version expected to be reported after update",
                            default="")
        parser.add_argument('--expected_ver3', action='store', help="The version expected to be reported after update",
                            default="")
        parser.add_argument('--error_type', action='store',
                            help="Add argument if error_type workload to be performed")
        parser.add_argument('--err_inj', action='store_true',
                            help="Add argument if err_inj workload to be performed")
        parser.add_argument('--capsle_path', action='store_true',
                            help="Add argument if capsle_path workload to be performed")
        parser.add_argument('--ac_on_off', action='store_true',
                            help="Add argument if ac power on and off to be performed")

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
        #Setting the bios knob
        if self.bios_knob:
            bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CFG + self.bios_knob)
            self.bios_knob_change(bios_enable)
        self.ras_prepare()

    def execute(self):
        """
        This function executes all RAS callable functions
        :return: True if the test case is pass
        """

        if self.err_inj:
            self.error_type_command(self.error_type)
            self._log.info(f"error type is {self.error_type}")
            if self._os_type == OperatingSystems.WINDOWS:
                self.injection_error()
            else:
                self.error_inject_commands_linux()
            self.check_os_log_error_message(self.error_type)
        if self.capsle_path:
            self.ras_execute()

        return True

    def cleanup1(self, return_status):
        super().cleanup(return_status)
        self.bios_util.load_bios_defaults()

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if
             RasScript.main()
             else Framework.TEST_RESULT_FAIL)
