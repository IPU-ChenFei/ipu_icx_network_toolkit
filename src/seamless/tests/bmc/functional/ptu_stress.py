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
from src.seamless.lib.pm_common import PmCommon, SocwatchCommon
from src.seamless.tests.bmc.constants import pm_constants


class PtuStress(PmCommon, SocwatchCommon):
    """
    This class contains all callable PM Functions
    """
    BIOS_CONFIG_FILE = "socwatch_bios_knobs.cfg"
    bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), BIOS_CONFIG_FILE)

    def __init__(self, test_log, arguments, cfg_opts):
        super().__init__(test_log, arguments, cfg_opts)
        self.capsule_path = arguments.capsule_path
        self.expected_ver = arguments.expected_ver
        self.warm_reset = arguments.warm_reset
        self.start_workload = arguments.start_workload
        self.sps_mode = arguments.sps_mode
        self.update_type = arguments.update_type
        self.activation = arguments.activation
        self.capsule_name = arguments.capsule_name
        self.capsule_name2 = arguments.capsule_name2
        self.capsule_name3 = arguments.capsule_name3
        self.capsule_path2 = arguments.capsule_path2
        self.capsule_path3 = arguments.capsule_path3
        self.expected_ver2 = arguments.expected_ver2
        self.expected_ver3 = arguments.expected_ver3
        self.loop_count = arguments.loop
        self.capsule_type = arguments.capsule_type
        self.ptu = arguments.ptu
        self.STAGING_REBOOT = None
        self.c0_value = arguments.c0_value
        self.c6_value = arguments.c6_value
        self.ptu_cmd = arguments.ptu_cmd


    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument('--capsule_name', action='store', help="Name of the capsule to be used for the update",
                            default="")
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--capsule_path', action='store', help="Path to the capsule to be used for the update",
                            default="")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update",
                            default="")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--update_type', action='store', help="Specify if efi utility, fit ucode, inband", default="fit_ucode")
        parser.add_argument('--activation', action='store_true', help="Add argument if only activation to be performed")
        parser.add_argument('--capsule_path2', action='store', help="Path to the 2nd capsule to be used for the update",
                            default="")
        parser.add_argument('--capsule_name2', action='store', help="Name of the capsule2 to be used for the update",
                            default="")
        parser.add_argument('--expected_ver2', action='store', help="The version expected to be reported after update",
                            default="")
        parser.add_argument('--capsule_name3', action='store', help="Name of the capsule3 to be used for the update",
                            default="")
        parser.add_argument('--capsule_path3', action='store', help="Path to the 3rd capsule to be used for the update",
                            default="")
        parser.add_argument('--expected_ver3', action='store', help="The version expected to be reported after update",
                            default="")
        parser.add_argument('--loop', type=int, default=1, help="Add argument for # of loops")
        parser.add_argument('--capsule_type', action='store', help="Add argument as 'negative' for negative usecases",
                            default="")
        parser.add_argument('--ptu', action='store_true',
                            help="Add argument if ptu workload to be performed")
        parser.add_argument('--c0_value', action='store', help="Add argument if c0  workload to be performed")
        parser.add_argument('--c6_value', action='store', help="Add argument if c6  workload to be performed")
        parser.add_argument('--ptu_cmd', action='store', help="Add argument if ptu  stress to be performed")

    def get_current_version(self, echo_version=True):
        """
        Read sps & bios & ucode version
        :param echo_version: True if display output
        :return sps version
        :return bios version
        :return ucode version
        """
        if self.capsule_type == 'bios':
            return self.get_bios_ver()
        if self.capsule_type == 'sps':
            return self.get_sps_ver()
        if self.capsule_type == 'ucode':
            return self.get_ucode_ver()

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
        if self.bios_config_file:
            self.bios_knob_change(self.bios_config_file)
        else:
            raise RuntimeError("Config file does not exist")

    def execute(self):
        """
        This function executes all PTU callable functions
        :return: True if the test case is pass
        """
        if self.ptu:
            if not self.check_ptu_tool():
                self.install_ptu_tool()
            self._log.info("PTU tool is installed successfully")
            if not self.check_ptu_tool():
                self._log.error("PTU tool is not available in SUT")
                raise RuntimeError("PTU tool is not available in SUT")
            self.deleting_file()
            self.execute_ptu_tool()
            self._log.info(f"Stress tool will be wait for {pm_constants.COMMAND_TIMEOUT} seconds")
            time.sleep(pm_constants.COMMAND_TIMEOUT)
            if self.capsule_type == 'bios':
                if self.capsule_name != "":
                    self.capsule_path = self.find_cap_path(self.capsule_name)
                    self._log.info("capsule path {}".format(self.capsule_path))
                if self.capsule_path != "":
                    self.STAGING_REBOOT = False
                    self._log.info("sending nth version capsule {}".format(self.expected_ver))
                    self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
                else:
                    if self.capsule_path == "":
                        self._log.error("Capsule 1 is not present in the command")
                    raise RuntimeError("Command is not proper. Please check the command.")
            if self.capsule_type == 'sps':
                for count in range(self.loop_count):
                    self._log.info("Loop Number:{}".format(count))
                    if self.capsule_path != "":
                        self.update_type = "SPS"
                        self.STAGING_REBOOT = False
                        self._log.info("sending nth version capsule {}".format(self.expected_ver))
                        if self.expected_ver != self.get_current_version():
                            self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload,
                                              self.expected_ver)
                        else:
                            raise RuntimeError("Expected version and current version are same")
                    if self.capsule_path2 != "":
                        self.update_type = "SPS"
                        self.STAGING_REBOOT = False
                        if self.expected_ver2 != self.get_current_version():
                            self.send_capsule(self.capsule_path2, self.CAPSULE_TIMEOUT, self.start_workload,
                                              self.expected_ver2)
                        else:
                            raise RuntimeError("Expected version and current version are same")
                    if self.capsule_path3 != "":
                        self.update_type = "SPS"
                        self.STAGING_REBOOT = False
                        if self.expected_ver3 != self.get_current_version():
                            self.send_capsule(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload,
                                              self.expected_ver3)
                        else:
                            raise RuntimeError("Expected version and current version are same")
            if self.capsule_type == 'ucode':
                for count in range(self.loop_count):
                    self._log.info("Loop Number:{}".format(count))
                    if self.capsule_name != "":
                        self.capsule_path = self.find_cap_path(self.capsule_name)
                        self._log.info("capsule path {}".format(self.capsule_path))
                    if self.capsule_path != "":
                        self.update_type = "UCODE"
                        self.STAGING_REBOOT = False
                        reset = self.warm_reset
                        self.warm_reset = False
                        # self.expected_ver = self.get_current_version()
                        self._log.info("sending nth version capsule {}".format(self.expected_ver))
                        self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload,
                                          self.expected_ver)
                    if self.capsule_name2 != "":
                        self.capsule_path2 = self.find_cap_path(self.capsule_name2)
                        self._log.info("capsule path2 {}".format(self.capsule_path2))
                    if self.capsule_path2 != "":
                        self.update_type = "UCODE"
                        self.STAGING_REBOOT = False
                        if reset:
                            self.warm_reset = True
                        self.send_capsule(self.capsule_path2, self.CAPSULE_TIMEOUT, self.start_workload,
                                          self.expected_ver2)
            time.sleep(pm_constants.TIMEOUT)
            self.kill_ptu_tool()
            self.deleting_csv_files_in_host()
            self.copy_csv_file_from_sut_to_host()
            self.read_csv_file()
            return True

    def cleanup(self, return_status):
        super().cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if
             PtuStress.main()
             else Framework.TEST_RESULT_FAIL)
