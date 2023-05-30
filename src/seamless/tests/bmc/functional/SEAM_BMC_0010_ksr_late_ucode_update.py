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

    Attempts to send in a ucode capsule use to initiate the seamless update
"""
import sys
import time
from datetime import datetime

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.seamless.lib.seamless_common import SeamlessBaseTest


class SEAM_BMC_0010_ksr_late_ucode_update(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0010_ksr_late_ucode_update, self).__init__(test_log, arguments, cfg_opts)
        self.expected_ver = arguments.expected_ver
        self.flow_type = arguments.flow_type
        self.start_workload = arguments.start_workload
        self.warm_reset = False
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.get_ucode_command = self._workload_path + "GetUcodeVersion.ps1 " + self._powershell_credentials
        self.ping_sut_command = self._workload_path + "PingSut.ps1 " + self._powershell_credentials
        self.restart_sut_command = self._workload_path + "RestartSut.ps1 " + self._powershell_credentials
        self.ucode_patches = {'rollback': 0, '28': 1, '29': 2, '2A': 3, '2B': 4}
        self.latebinding = False
        self.time_update = None
        self.KSR_UPDATE_DELAY = 50
        self.LATE_UPDATE_DELAY = 12
        self.skip_reset = False
        self.activation = False
        self.sps_mode = arguments.sps_mode

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0010_ksr_late_ucode_update, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--flow_type', action='store', help="The type of flow for ucode update", default="")  # (early, ksr, late)
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")

    def check_capsule_pre_conditions(self):
        return True

    def evaluate_workload_output(self, output):
        return True

    def get_current_version(self, echo_version=True):
        output = self.run_powershell_command(self.get_ucode_command + ' ucode', get_output=True)
        version = "NONE"
        for line in output.split('\n'):
            if "msr[8b] =" in line:
                version = line.split(" = ")[1].split('`')[0]
                break
            elif "Current" in line:
                version = line.split(":")[1].strip()
        if echo_version:
            self._log.info("Version detected: " + version)
        return version

    def execute(self):
        result = False
        patch_ucode = False

        version = self.expected_ver.split('x')[1]

        initial_version = self.get_current_version().split('x')[1]
        if initial_version == version:
            self._log.info("The initial version '" + initial_version + "' is already the expected version")
            return result

        if (self.start_workload is True):
            self._log.info("start workloads: " + str(self.start_workload))
            self.start_workloads()

        patch_ucode = self.patch_ucode(version)

        try:
            if (patch_ucode):
                self._log.info("Execute command to update ucode version" + self.flow_type)
                if (self.flow_type == 'rollback' or self.ucode_patches[version] < self.ucode_patches[initial_version]):
                    self._log.info("Windows Ucode Update flow type" + str(self.flow_type) + "started: Warm reset the system")
                    self.warm_reset = True
                    post_version, errors = self.block_until_complete(version)
                elif (self.flow_type == 'ksr'):
                    self._log.info("KSR uCode Update: system soft reboots in 40 seconds")
                    time_start = datetime.now()
                    self.run_powershell_command(command=self._workload_path + 'KSRUcodeUpdate.ps1 ' + self._powershell_credentials, get_output=True)
                    time.sleep(self.KSR_UPDATE_DELAY)
                    self.time_update = datetime.now() - time_start
                    self.run_powershell_command(command=self._workload_path + 'KSRUcodeRestore.ps1 ' + self._powershell_credentials,
                                                get_output=True,
                                                echo_output=False)
                    post_version = self.get_current_version()
                elif (self.flow_type == 'late'):
                    self._log.info("Late uCode Update: system reboots in 9 seconds")
                    self.latebinding = True
                    time_start = datetime.now()
                    self.run_powershell_command(command=self._workload_path + 'LateUcodeUpdate.ps1 ' + self._powershell_credentials,
                                                get_output=True,
                                                echo_output=False)
                    time.sleep(self.LATE_UPDATE_DELAY)
                    self.time_update = datetime.now() - time_start
                    post_version = self.get_current_version()

                if post_version != self.expected_ver:
                    self._log.error("The version '" + post_version + "' is not the expected version '" + self.expected_ver + "'")
                    result = False
                else:
                    self._log.error("The version '" + post_version + "' is expected version '" + self.expected_ver + "'")
                    self._log.error("Checking post-update conditions")
                    result = self.examine_post_update_conditions("ucode")

        except RuntimeError as e:
            self._log.exception(e)
        if self.workloads_started:
            wl_output = self.stop_workloads()
            self._log.error("Evaluating workload output")
            if not self.evaluate_workload_output(wl_output):
                result = False
        return result

    def cleanup(self, return_status):
        if (self.flow_type == 'late'):
            self.summary_log.info("Reboot system after latebinding ucode update (temporary fix))")
            self.warm_reset = True
            self.block_until_complete('')
        super(SEAM_BMC_0010_ksr_late_ucode_update, self).cleanup(return_status)
        self.summary_log.info("Total time for uCode " + str(self.flow_type) + " update: " + str(self.time_update))


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0010_ksr_late_ucode_update.main() else Framework.TEST_RESULT_FAIL)
