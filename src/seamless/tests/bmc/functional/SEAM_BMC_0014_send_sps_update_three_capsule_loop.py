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
import random
from datetime import datetime, timedelta
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest

class SEAM_BMC_0014_send_sps_update_three_capsule_loop(SeamlessBaseTest):
    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0014_send_sps_update_three_capsule_loop, self).__init__(test_log, arguments, cfg_opts)
        self.update_type = arguments.update_type
        self.sps_update_type = arguments.sps_update_type
        self.capsule_path = arguments.capsule_path
        self.expected_ver = arguments.expected_ver
        self.capsule_path2 = arguments.capsule_path
        self.expected_ver2 = arguments.expected_ver
        self.capsule_path3 = arguments.capsule_path2
        self.expected_ver3 = arguments.expected_ver2
        self.capsule_name = arguments.capsule_name
        self.capsule_name2 = arguments.capsule_name
        self.capsule_name3 = arguments.capsule_name2
        self.capsule_type = arguments.capsule_type
        self.loop_count = arguments.loop
        self.warm_reset = arguments.warm_reset
        self.activation = arguments.activation
        self.rec_ver = ''
        self.opr_ver = ''
        self.start_workload = arguments.start_workload
        self.skip_reset = False
        self.sps_mode = arguments.sps_mode
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.restart_sut_command = self._workload_path + "RestartSut.ps1 " + self._powershell_credentials
        self.DelJournal_command = self._workload_path + "DelJournal.ps1 " + self._powershell_credentials_bmc
        # self.spi_access = arguments.spi_access
        self.spi_access = False
        self.stressors = arguments.stressors
        self.ver_timeout = 120
        self.journal_count = 30000
        self.journal_timeout_min = 100
        self.journal_timeout_max = 120
        #define 3 sps capsules
        if (self.sps_update_type == 'three_capsule'):
            if self._product == "EGS":
                file_ext = self.capsule_path2.split('.')[-1]
                capsule_name = '_'.join(self.capsule_path2.split('_')[0:-3])
                self.capsule_upgrade_1 = capsule_name + "_me_rcv_on_opr_capsule." + file_ext
                self.capsule_upgrade_2 = capsule_name + "_me_rcv_capsule." + file_ext
                self.capsule_upgrade_3 = capsule_name + "_me_opr_capsule." + file_ext
                capsule_name2 = '_'.join(self.capsule_path3.split('_')[0:-3])
                self.capsule_downgrade_1 = capsule_name2 + "_me_rcv_on_opr_capsule." + file_ext
                self.capsule_downgrade_2 = capsule_name2 + "_me_rcv_capsule." + file_ext
                self.capsule_downgrade_3 = capsule_name2 + "_me_opr_capsule." + file_ext
            else:
                file_ext = self.capsule_path2.split('.')[-1]
                capsule_name = '_'.join(self.capsule_path2.split('_')[0:-1])
                self.capsule_upgrade_1 = capsule_name + "_RcvOnOpr." + file_ext
                self.capsule_upgrade_2 = capsule_name + "_Recovery." + file_ext
                self.capsule_upgrade_3 = capsule_name + "_Operational." + file_ext
                capsule_name2 = '_'.join(self.capsule_path3.split('_')[0:-1])
                self.capsule_downgrade_1 = capsule_name2 + "_RcvOnOpr." + file_ext
                self.capsule_downgrade_2 = capsule_name2 + "_Recovery." + file_ext
                self.capsule_downgrade_3 = capsule_name2 + "_Operational." + file_ext

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0014_send_sps_update_three_capsule_loop, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--capsule_path', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--capsule_path2', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--expected_ver2', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--capsule_name', action='store', help="Name of the capsule to be used for the update", default="")
        parser.add_argument('--capsule_name2', action='store', help="Name of the capsule2 to be used for the update", default="")
        parser.add_argument('--update_type', action='store', help="Specify if efi utility, fit ucode, inband", default="fit_ucode")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--loop', type=int, default=1, help="Add argument for # of loops")
        parser.add_argument('--capsule_type', action='store', help="Add type of update capsule", default="")
        parser.add_argument('--sps_update_type', action='store', help="Add type of SPS update: operational or three_capsule", default="operational")
        parser.add_argument('--activation', action='store_true', help="Add argument if only activation to be performed")
        parser.add_argument('--spi_access', action='store_true', help="pass argument to perform verification after update sps", default="")
        parser.add_argument('--stressors', action='store_true', help="pass argument to perform verification after update sps", default="")

    def check_capsule_pre_conditions(self):
        #To-Do add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        #To-Do add workload output analysis
        return True
    
    def time_delay(self, timeout=None):
        """
        Time delay added to check if SUT is alive
        :param timeout: time allowed to give BMC to exit recovery mode
        :return Boolean True if Sut is alive
        """
        time_end = 0
        one_sec = 1
        while timeout > time_end: 
            time.sleep(one_sec)
            time_end += 1
            if self.sut_ssh.is_alive():
                self._log.info("SUt alive going to version check\n")
                return True
        raise RuntimeError("SUT is offline/won't connect\n")
        
    def get_current_version(self, echo_version=True):
        """
        Read sps version
        :param echo_version: True if display output
        :return ME version
        """
        self.time_delay(self.ver_timeout)
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
            self.rec_ver = version.split('(Recovery)')[0].strip()
            opr_ver = version.split('(Recovery)')[1].split('(Operational)')[0].replace(',', '').strip()        
        except IndexError:
            if self.sut_ssh.is_alive() == False:
                self._log.error("SUT is offline/not connecting - Test Failed")
                self._log.debug("Version results: {}".format(version))
                raise RuntimeError("SUT is offline/won't connect\n")
            else :
                raise RuntimeError
        if me_mode == 'Normal':
            me_mode = 'Operational'        
        version = "Operational: {} Recovery: {} Current State: {}".format(opr_ver,self.rec_ver,me_mode)
        if echo_version:
            self._log.info("\tVersion detected: {}".format(version))
        return version

    def execute(self):
        if self.stressors:
            self.spi_access = True
        if self.capsule_name != "":
            self.capsule_path = self.find_cap_path(self.capsule_name)
            self._log.info("capsule path {}".format(self.capsule_path))
            self.capsule_path2 = self.find_cap_path(self.capsule_name)
            self._log.info("capsule path2 {}".format(self.capsule_path))
        if self.capsule_name2 != "":
            self.capsule_path3 = self.find_cap_path(self.capsule_name2)
            self._log.info("capsule path3 {}".format(self.capsule_path2))
        if (self.sps_update_type == "operational"):
            if (self._bmc_redfish._skip_sel_count > self.journal_count):
                    self._log.info(self._bmc_redfish._skip_sel_count)
                    output = self.run_powershell_command(self.DelJournal_command, get_output=True)
                    self._log.info(output)
                    self._log.info("bmcreset_logs_v9")
                    time.sleep(random.randint(self.journal_timeout_min,self.journal_timeout_max))
            for x in range(self.loop_count):
                self.capsule_path = self.capsule_path2
                self.expected_ver = self.expected_ver2
                if not self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload, "SPS"):
                    return False
                self.capsule_path = self.capsule_path3
                self.expected_ver = self.expected_ver3
                if not self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload, "SPS"):
                    return False
                self._log.info("Automated  test  Loop number :{}".format(x+1))

        elif (self.sps_update_type == "three_capsule"):
            """
            TC :- 64968.3 & 70589
            cmd :- python SEAM_BMC_0014_send_sps_update_three_capsule_loop.py
                --sps_update_type three_capsule
                --capsule_path <>
                --expected_ver
                --capsule_path2 <>
                --expected_ver2
                --loop <No of loops>
            """
            for x in range(self.loop_count):
                self.get_current_version()
                if not (self.capsule_path2 == ''):  #only do upgrade
                    if (self._bmc_redfish._skip_sel_count > self.journal_count):
                        self._log.info(self._bmc_redfish._skip_sel_count)
                        output = self.run_powershell_command(self.DelJournal_command, get_output=True)
                        self._log.info(output)
                        self._log.info("bmcreset_logs_v9")
                        time.sleep(random.randint(self.journal_timeout_min,self.journal_timeout_max))
                        self._log.info(self._bmc_redfish._skip_sel_count)
                    self.expected_ver = "Operational: " + self.expected_ver2 + " Recovery: " + self.rec_ver + " Current State: " + 'Recovery'
                    if not self.send_capsule(self.capsule_upgrade_1, self.CAPSULE_TIMEOUT, self.start_workload, "SPS"):
                        return False
                    self.expected_ver = "Operational: " + self.expected_ver2 + " Recovery: " + self.expected_ver2 + " Current State: " + 'Recovery'
                    if not self.send_capsule(self.capsule_upgrade_2, self.CAPSULE_TIMEOUT, self.start_workload, "SPS"):
                        return False
                    self.expected_ver = "Operational: " + self.expected_ver2 + " Recovery: " + self.expected_ver2 + " Current State: " + 'Operational'
                    if not self.send_capsule(self.capsule_upgrade_3, self.CAPSULE_TIMEOUT, self.start_workload, "SPS"):
                        return False
                    self._log.info(self._bmc_redfish._skip_sel_count)
                if not (self.capsule_path3 == ''):
                    if (self._bmc_redfish._skip_sel_count > self.journal_count):
                        self._log.info(self._bmc_redfish._skip_sel_count)
                        output = self.run_powershell_command(self.DelJournal_command, get_output=True)
                        self._log.info("bmcreset_logs_v9")
                        time.sleep(random.randint(self.journal_timeout_min,self.journal_timeout_max))
                    self.expected_ver = "Operational: " + self.expected_ver3 + " Recovery: " + self.rec_ver + " Current State: " + 'Recovery'
                    if not self.send_capsule(self.capsule_downgrade_1, self.CAPSULE_TIMEOUT, self.start_workload, "SPS"):
                        return False
                    self.expected_ver = "Operational: " + self.expected_ver3 + " Recovery: " + self.expected_ver3 + " Current State: " + 'Recovery'
                    if not self.send_capsule(self.capsule_downgrade_2, self.CAPSULE_TIMEOUT, self.start_workload, "SPS"):
                        return False
                    self.expected_ver = "Operational: " + self.expected_ver3 + " Recovery: " + self.expected_ver3 + " Current State: " + 'Operational'
                    if not self.send_capsule(self.capsule_downgrade_3, self.CAPSULE_TIMEOUT, self.start_workload, "SPS"):
                        return False
                self._log.info("Automated  test  Loop number :{}".format(x+1))
        else:
            raise RuntimeError("SPS update type argument does not match: operational or three_capsule")
        self._log.info("\tChecking post-update conditions")
        return self.examine_post_update_conditions("SPS")

    def cleanup(self, return_status):
        super(SEAM_BMC_0014_send_sps_update_three_capsule_loop, self).cleanup(return_status)
                           
if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0014_send_sps_update_three_capsule_loop.main() else Framework.TEST_RESULT_FAIL)
