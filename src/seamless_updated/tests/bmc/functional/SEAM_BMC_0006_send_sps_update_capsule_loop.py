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

    Attempts to send in an sps capsule use to initiate the seamless update
"""
import sys
import time
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest

class SEAM_BMC_0006_send_sps_update_capsule_loop(SeamlessBaseTest):
    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0006_send_sps_update_capsule_loop, self).__init__(test_log, arguments, cfg_opts)
        self.capsule_path = arguments.capsule_path
        self.expected_ver = arguments.expected_ver
        self.capsule_path2 = arguments.capsule_path
        self.expected_ver2 = arguments.expected_ver
        self.capsule_path3 = arguments.capsule_path2
        self.expected_ver3 = arguments.expected_ver2
        self.capsule_name = arguments.capsule_name
        self.capsule_name2 = arguments.capsule_name2
        self.capsule_name3 = arguments.capsule_name3
        self.capsule_type = arguments.capsule_type
        self.loop_count = arguments.loop
        self.warm_reset = arguments.warm_reset
        self.activation = arguments.activation
        self.start_workload = arguments.start_workload
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.restart_sut_command = self._workload_path + "RestartSut.ps1 " + self._powershell_credentials
        self.run_orchestrator = arguments.orchestrator
        self.capsule_xml = arguments.capsule_xml
        self.capsule_xml2 = arguments.capsule_xml
        self.capsule_xml3 = arguments.capsule_xml2
        self.skip_reset = False
        self.sps_mode = arguments.sps_mode
        self.capsule = "SPS"
        self.update_type = "sps_loop"
        # self.spi_access = arguments.spi_access
        self.spi_access = False
        self.stressors = arguments.stressors


    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0006_send_sps_update_capsule_loop, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--capsule_path', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--capsule_path2', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--expected_ver2', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--capsule_path3', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--expected_ver3', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--capsule_name', action='store', help="Name of the capsule to be used for the update", default="")
        parser.add_argument('--capsule_name2', action='store', help="Name of the capsule2 to be used for the update", default="")
        parser.add_argument('--capsule_name3', action='store', help="Name of the capsule3 to be used for the update", default="")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--loop', type=int, default=1,help="Add argument for # of loops")
        parser.add_argument('--capsule_type', action='store', help="Add type of update capsule", default="")
        parser.add_argument('--orchestrator', action='store_true', help="Validate update through OrchestratorValidator"
                                                                        "before running. Requires \"--capulse_xml\".")
        parser.add_argument('--capsule_xml', action="store", help="Path to Capsule XML file for the update. Required for"
                                                                  "\"--orchestrator\".", default="")
        parser.add_argument('--capsule_xml2', action="store", help="Path to Capsule XML file for the update. Required for"
                                                                   "\"--orchestrator\".", default="")
        parser.add_argument('--activation',action='store_true', help="Add argument if only activation to be performed")
        parser.add_argument('--spi_access', action='store_true',help="pass argument to perform verification after update sps", default="")
        parser.add_argument('--stressors', action='store_true',help="pass argument to perform verification after update sps", default="")

    def check_capsule_pre_conditions(self):
        # TODO: add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        # TODO: add workload output analysis
        return True

    def get_current_version(self, echo_version=True):
        """
        Read ME version with BMC refish
        :param echo_version: True if display output
        :return ME version
        """
        
        if self._os_type != OperatingSystems.LINUX:
            output = self.run_powershell_command(self.get_sps_command, get_output=True)
        else:
            cmd = './spsInfoLinux64'
            result = self.run_ssh_command(cmd)
            output = result.stdout

        version = "NONE"
        me_mode = "NONE"
        for line in output.splitlines():
            if "Current State" in line or "CurrentState" in line:
                me_mode = line.split('):')[1].strip().split(' ')[0]
            elif "SPS Image FW version" in line:
                version = line.split(':')[1]
                break            
        
        try:
            rec_ver = version.split('(Recovery)')[0].strip()
            opr_ver = version.split('(Recovery)')[1].split('(Operational)')[0].replace(',', '').strip()

            if me_mode == 'Normal':
                me_mode = 'Operational'

            version = 'Operational: ' + opr_ver + ' Recovery: ' + rec_ver + ' Current State: ' + me_mode
            
        except IndexError:
            if self.sut_ssh.is_alive() == False:
                self._log.error("SUT is offline/not connecting - Test Failed")
                self._log.debug("Version results: " + version)
                raise RuntimeError("SUT is offline/won't connect\n")
            else :
                raise RuntimeError
                
        if echo_version:
            self._log.info("\tVersion detected: " + version)
        return version

    def execute(self):
        if self.stressors:
            self.spi_access = True
        if self.capsule_name != "":
            self.capsule_path = self.find_cap_path(self.capsule_name)
            self._log.info("capsule path {}".format(self.capsule_path))
        if self.capsule_name2 != "":
            self.capsule_path2 = self.find_cap_path(self.capsule_name2)
            self._log.info("capsule path2 {}".format(self.capsule_path2))
        if self.capsule_name3 != "":
            self.capsule_path3 = self.find_cap_path(self.capsule_name3)
            self._log.info("capsule path3 {}".format(self.capsule_path3))
        for x in range(self.loop_count):
            if not(self.capsule_path2 == ''): #only do upgrade
                self.capsule_path = self.capsule_path2
                self.expected_ver = self.expected_ver2
                self.capsule_xml = self.capsule_xml2
                if not self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload, "SPS"):
                    return False
            if not(self.capsule_path3 == ''): #only do downgrade
                self.capsule_path = self.capsule_path3
                self.expected_ver = self.expected_ver3
                self.capsule_xml = self.capsule_xml3
                if not self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload, "SPS"):
                    return False
            self._log.info("Automated  test  Loop number :" + str(x+1))
            #if (x % 20 == 0):
            #    self._bmc_redfish.reset_bmc()
            #    time.sleep(100)
            
        self._log.info("\tChecking post-update conditions")
        return self.examine_post_update_conditions("SPS")
        
    def cleanup(self, return_status):
        super(SEAM_BMC_0006_send_sps_update_capsule_loop, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0006_send_sps_update_capsule_loop.main() else Framework.TEST_RESULT_FAIL)
