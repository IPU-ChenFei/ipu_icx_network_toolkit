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
"""
    :Seamless BMC capsule stage test

    Attempts to send in an bios capsule use to initiate the seamless update
"""
import sys
import time
from datetime import datetime, timedelta
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest
import os
import threading
import concurrent.futures


class SEAM_BMC_0020_set_bios_knob_and_send_bios_update_capsule(SeamlessBaseTest):

    BIOS_CONFIG_FILE = "bios_knob.cfg"

    def __init__(self, test_log, arguments, cfg_opts, *args):
        super(SEAM_BMC_0020_set_bios_knob_and_send_bios_update_capsule, self).__init__(test_log, arguments, cfg_opts, *args)
        self.capsule_path = arguments.capsule_path
        self.expected_ver = arguments.expected_ver
        self.capsule_name = arguments.capsule_name
        self.warm_reset = arguments.warm_reset
        self.start_workload = arguments.start_workload
        self.start_workload_command = self._workload_path + \
            "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + \
            "StopWorkloads.ps1 " + self._powershell_credentials
        self.get_bios_command = self._workload_path + \
            "GetBiosVersion.ps1 " + self._powershell_credentials
        self.ping_sut_command = self._workload_path + \
            "PingSut.ps1 " + self._powershell_credentials
        self.restart_sut_command = self._workload_path + \
            "RestartSut.ps1 " + self._powershell_credentials
        self.sut_mode = arguments.sut_mode
        self.capsule_type = arguments.capsule_type
        self.run_orchestrator = arguments.orchestrator
        self.capsule_xml = arguments.capsule_xml
        self.S5_cycle_loop = arguments.S5_cycle_loop
        self.skip_reset = False
        self.activation = False
        self.sps_mode = arguments.sps_mode

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0020_set_bios_knob_and_send_bios_update_capsule, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--capsule_path', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--capsule_name', action='store', help="Name of the capsule to be used for the update", default="")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--sut_mode', action='store', help="State if SUT is in EFI mode or DC power off mode", default="")
        parser.add_argument('--orchestrator',
                            action='store_true',
                            help="Validate update through OrchestratorValidator"
                            "before running. Requires \"--capulse_xml\".")
        parser.add_argument('--capsule_xml', action="store", help="Path to Capsule XML file for the update. Required for" "\"--orchestrator\".", default="")
        parser.add_argument('--capsule_type', action='store', help="Add argument as 'negative' for negative usecases", default="")
        parser.add_argument('--S5_cycle_loop', type=int, default=0, help="Add argument for # of loops of S5 cycle")

    def get_current_version(self, echo_version=True):
        """
        Read bios version
        :param echo_version: True if display output
        :return bios version
        """
        cmd = 'dmidecode | grep "Version: ' + str(self._product)[0] + '"'
        # cmd = 'dmidecode | grep "Version: W"'
        if self._os_type != OperatingSystems.LINUX:
            output = self.run_powershell_command(self.get_bios_command, get_output=True)
        else:
            result = self.run_ssh_command(cmd)
            version = result.stdout.split('\n')[0].split(' ')
            if echo_version:
                self._log.info("Version detected: " + version[1])
            return version[1]
        version = "NONE"
        for line in output.split('\n'):
            if "SMBIOSBIOSVersion : " in line:
                version = line.split(' : ')[1]
                break
        if echo_version:
            self._log.info("Version detected : " + version)
        return version

    def check_capsule_pre_conditions(self):
        # To-Do add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        # To-Do add workload output analysis
        return True

    def execute(self):
        if self.capsule_name != "":
            self.capsule_path = self.find_cap_path(self.capsule_name)
            self._log.info("capsule path {}".format(self.capsule_path))
        if self.S5_cycle_loop:
            """
            TC :- 66116.1
            cmd :- python3 SEAM_BMC_0020_set_bios_knob_and_send_bios_update_capsule.py 
            --capsule_path <path for BIOS capsule> 
            --expected_ver <bios cap version>
            --S5_cycle_loop <loop_count>
            """
            if self.BIOS_CONFIG_FILE:
                bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
            self._log.info("=========SETTING BIOS KNOB AS PER CONFIG FILE=========")
            self.bios_util.set_bios_knob(bios_config_file)
            self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)
            self._log.info("=========VERIFYING THE CHANGED BIOS KNOB=========")
            self.bios_util.verify_bios_knob(bios_config_file)
            if self._os_type == OperatingSystems.LINUX and self.start_workload:
                self._log.info("OS is Linux --Start_workload")
                self.access_permission()
                start_load = threading.Thread(target=self.workload_lin)
                self._log.info("=========INITIATING WORKLOAD===========\n")
                start_load.start()
                self._log.info("Waiting for some seconds for stabilizing workload..")
                time.sleep(self.SUT_SETTLING_TIME)
                self._log.info("=========UPDATING CAPSULE WHILE WORKLOAD IN PROGRESS IN BACKGROUND===========\n")
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    self.output = executor.submit(self.send_capsule, self.capsule_path, self.CAPSULE_TIMEOUT)
                    update_cap1 = self.output.result()
                start_load.join()
            else:
                update_cap1 = self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
            if update_cap1:
                if self.BIOS_CONFIG_FILE:
                    bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
                self._log.info("=========VERIFYING THE BIOS KNOB AFTER CAPSULE UPDATE=========")
                self.bios_util.verify_bios_knob(bios_config_file)
                self._log.info("Update of BIOS capsule is done and verified the BIOS knob changes\n")
                self._log.info("Performing S5 cycles..")
                for x in range(self.S5_cycle_loop):
                    self._log.info("Performing S5 cycle, iteration: {}\n".format(x + 1))
                    self.os.shutdown(self.DC_POWER_DELAY)
                    self._log.info("System entered into S5 state, waiting for SUT to settle down..")
                    time.sleep(self.SUT_SETTLING_TIME)
                    self._log.info("Waking up the system from S5 state..")
                    if self._product == "EGS":
                        self._dc_power.dc_power_on()
                    elif self._product == "WHT":
                        self._dc_power.dc_power_reset()
                    self._log.info("Waiting for system to boot into OS..")
                    self.os.wait_for_os(self.reboot_timeout)
                    time.sleep(self.POST_SLEEP_DELAY)
                    if self.sut_ssh.is_alive():
                        self._log.info("System booted into OS..!!\n")
                    else:
                        raise RuntimeError("System not booted into OS after the given time..!!")
                self._log.info("==========PERFORMED {} ITERATION(S) OF S5 CYCLE(S)===========\n".format(x + 1))
                self._log.info("Reverting the BIOS settings into default..")
                self.bios_util.load_bios_defaults()
                return True
            else:
                self._log.info("Capsule update failed..!!")
                return False
        else:
            """
            TC :- 66049.1 & 70584.1
            cmd :- python3 SEAM_BMC_0020_set_bios_knob_and_send_bios_update_capsule.py 
            --capsule_path <path for BIOS capsule> 
            --expected_ver <bios cap version>
            --warm_reset
            """
            if self.BIOS_CONFIG_FILE:
                bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
            self._log.info("=========SETTING BIOS KNOB AS PER CONFIG FILE=========")
            self.bios_util.set_bios_knob(bios_config_file)
            self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)
            self._log.info("=========VERIFYING THE CHANGED BIOS KNOB=========")
            self.bios_util.verify_bios_knob(bios_config_file)
            if self._os_type == OperatingSystems.LINUX and self.start_workload:
                self._log.info("OS is Linux --Start_workload")
                self.access_permission()
                start_load = threading.Thread(target=self.workload_lin)
                self._log.info("=========INITIATING WORKLOAD===========\n")
                start_load.start()
                self._log.info("Waiting for some seconds for stabilizing workload..")
                time.sleep(self.SUT_SETTLING_TIME)
                self._log.info("=========UPDATING CAPSULE WHILE WORKLOAD IN PROGRESS IN BACKGROUND===========\n")
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    self.output = executor.submit(self.send_capsule, self.capsule_path, self.CAPSULE_TIMEOUT)
                    update_cap1 = self.output.result()
                start_load.join()
            else:
                update_cap1 = self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
            if update_cap1:
                self._log.info("=========VERIFYING THE BIOS KNOB AFTER CAPSULE UPDATE=========")
                self.bios_util.verify_bios_knob(bios_config_file)
                self._log.info("Update of BIOS capsule is done and verified the BIOS knob changes")
                self._log.info("Reverting the BIOS settings into default..")
                self.bios_util.load_bios_defaults()
                return True
            else:
                self._log.info("Capsule update failed..!!")
                return False

    def cleanup(self, return_status):
        super(SEAM_BMC_0020_set_bios_knob_and_send_bios_update_capsule, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0020_set_bios_knob_and_send_bios_update_capsule.main() else Framework.TEST_RESULT_FAIL)
