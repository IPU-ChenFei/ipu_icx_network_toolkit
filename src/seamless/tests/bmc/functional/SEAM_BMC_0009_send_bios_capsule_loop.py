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
import random
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest


class SEAM_BMC_0009_send_bios_capsule_loop(SeamlessBaseTest):
    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0009_send_bios_capsule_loop, self).__init__(test_log, arguments, cfg_opts)
        self.capsule_path = arguments.capsule_path
        self.expected_ver = arguments.expected_ver
        self.capsule_path2 = arguments.capsule_path
        self.expected_ver2 = arguments.expected_ver
        self.capsule_path3 = arguments.capsule_path2
        self.expected_ver3 = arguments.expected_ver2
        self.capsule_name = arguments.capsule_name
        self.capsule_name2 = arguments.capsule_name
        self.capsule_name3 = arguments.capsule_name2
        self.warm_reset = arguments.warm_reset
        self.loop_count = arguments.loop
        self.activation = arguments.activation
        self.start_workload = arguments.start_workload
        self.DelJournal_command = self._workload_path + "DelJournal.ps1 " + self._powershell_credentials_bmc
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
        self.run_orchestrator = arguments.orchestrator
        self.capsule_xml = arguments.capsule_xml
        self.capsule_xml2 = arguments.capsule_xml
        self.capsule_xml3 = arguments.capsule_xml2
        self.skip_reset = False
        self.sps_mode = arguments.sps_mode
        # self.spi_access = arguments.spi_access
        self.spi_access = False
        self.stressors = arguments.stressors
        self.update_type = "bios_loop"
        self.journal_timeout_min = 100
        self.journal_timeout_max = 120
        self.bmc_timeout_min = 10
        self.bmc_timeout_max = 20
        self.journal_count = 30000
        self.ac_while_staging = arguments.ac_while_staging

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0009_send_bios_capsule_loop, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--capsule_path', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--capsule_path2', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--expected_ver2', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--capsule_name', action='store', help="Name of the capsule to be used for the update", default="")
        parser.add_argument('--capsule_name2', action='store', help="Name of the capsule2 to be used for the update", default="")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--loop', type=int, default=1, help="Add argument for # of loops")
        parser.add_argument('--orchestrator',
                            action='store_true',
                            help="Validate update through OrchestratorValidator"
                            "before running. Requires \"--capulse_xml\".")
        parser.add_argument('--capsule_xml', action="store", help="Path to Capsule XML file for the update. Required for" "\"--orchestrator\".", default="")
        parser.add_argument('--capsule_xml2',
                            action="store",
                            help="Path to Capsule XML file for the second image."
                            "Required for \"--orchestrator\".",
                            default="")
        parser.add_argument('--activation', action='store_true', help="Add argument if only activation to be performed")
        parser.add_argument('--spi_access', action='store_true', help="pass argument to perform verification after update sps", default="")
        parser.add_argument('--stressors', action='store_true', help="pass argument to perform verification after update sps", default="")
        parser.add_argument('--ac_while_staging',action='store_true',help="Add this argument if need to to AC while staging")

    def check_capsule_pre_conditions(self):
        # TODO: add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        # TODO: add workload output analysis
        return True

    def get_current_version(self, echo_version=True):
        """
        Read bios version
        :param echo_version: True if display output
        :return bios version
        """
        # cmd = 'dmidecode | grep "Version: ' + str(self._product)[0] + '"'
        cmd = 'dmidecode -s bios-version'
        if self._os_type != OperatingSystems.LINUX:
            output = self.run_powershell_command(self.get_bios_command, get_output=True)
            if output is  None:
                raise RuntimeError ('output is null')
        else:
            result = self.run_ssh_command(cmd)
            if result is None:
                raise RuntimeError ('output is null')
            version = result.stdout
            if echo_version:
                self._log.info("Version detected: {}".format(version))
            return version
        version = "NONE"
        for line in output.split('\n'):
            if "SMBIOSBIOSVersion : " in line:
                version = line.split(' : ')[1]
                break
        if echo_version:
            self._log.info("Version detected: {}".format(version))
        return version

    def execute(self):
        """
        TC :- 70600
        cmd :- python3 SEAM_BMC_0009_send_bios_capsule_loop.py
        --capsule_path <path for 1st BIOS capsule>
        --expected_ver <bios cap1 version>
        --capsule_path2 <path for 2nd BIOS capsule>
        --expected_ver2 <bios cap2 version>
        --warm_reset
        --loop <loop_count>
        """
        if self.stressors:
            self.spi_access = True
        if self.capsule_name != "":
            self.capsule_path = self.find_cap_path(self.capsule_name)
            self._log.info("capsule path {}".format(self.capsule_path))
            self.capsule_path2 = self.find_cap_path(self.capsule_name2)
            self._log.info("capsule path2 {}".format(self.capsule_path2))
        if self.capsule_name3 != "":
            self.capsule_path3 = self.find_cap_path(self.capsule_name3)
            self._log.info("capsule path3 {}".format(self.capsule_path3))

        if self.ac_while_staging:
            for x in range(self.loop_count):
                if not (self.capsule_path2 == ''):  # only do upgrade
                    self.capsule_path = self.capsule_path2
                    self.expected_ver = self.get_current_version()
                    self.capsule_xml = self.capsule_xml2
                    if (self._bmc_redfish._skip_sel_count > self.journal_count):
                        self._log.info(self._bmc_redfish._skip_sel_count)
                        output = self.run_powershell_command(self.DelJournal_command, get_output=True)
                        self._log.info(output)
                        self._log.info("bmcreset_logs_v6")
                        time.sleep(random.randint(self.journal_timeout_min, self.journal_timeout_max))
                    self.ac_while_staging = True
                    if not self.send_capsule_ac_while_staging(self.capsule_path, self.CAPSULE_TIMEOUT,
                                                              self.start_workload):
                        return False
                if not (self.capsule_path3 == ''):  # only do downgrade
                    self.capsule_path = self.capsule_path3
                    self.expected_ver = self.get_current_version()
                    self.capsule_xml = self.capsule_xml3
                    if (self._bmc_redfish._skip_sel_count > self.journal_count):
                        self._log.info(self._bmc_redfish._skip_sel_count)
                        output = self.run_powershell_command(self.DelJournal_command, get_output=True)
                        self._log.info(output)
                        self._log.info("bmcreset_logs_v6")
                        time.sleep(random.randint(self.journal_timeout_min, self.journal_timeout_max))
                    self.ac_while_staging = True
                    if not self.send_capsule_ac_while_staging(self.capsule_path, self.CAPSULE_TIMEOUT,
                                                              self.start_workload):
                        return False
                self._log.info("Automated  test  Loop number : {}".format(x + 1))
            self._log.info("\tChecking post-update conditions")
            return self.examine_post_update_conditions("BIOS")
        else:
            for x in range(self.loop_count):
                if not (self.capsule_path2 == ''):  # only do upgrade
                    self.capsule_path = self.capsule_path2
                    self.expected_ver = self.expected_ver2
                    self.capsule_xml = self.capsule_xml2
                    if (self._bmc_redfish._skip_sel_count > self.journal_count):
                        self._log.info(self._bmc_redfish._skip_sel_count)
                        output = self.run_powershell_command(self.DelJournal_command, get_output=True)
                        self._log.info("bmcreset_logs_v6")
                        time.sleep(random.randint(self.journal_timeout_min,self.journal_timeout_max))
                    if not self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload):
                        return False
                if not (self.capsule_path3 == ''):  # only do downgrade
                    self.capsule_path = self.capsule_path3
                    self.expected_ver = self.expected_ver3
                    self.capsule_xml = self.capsule_xml3
                    if (self._bmc_redfish._skip_sel_count > self.journal_count):
                        self._log.info(self._bmc_redfish._skip_sel_count)
                        output = self.run_powershell_command(self.DelJournal_command, get_output=True)
                        self._log.info("bmcreset_logs_v6")
                        time.sleep(random.randint(self.journal_timeout_min,self.journal_timeout_max))
                    if not self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload):
                        return False
                self._log.info("Automated  test  Loop number : {}".format(x+1))
            self._log.info("\tChecking post-update conditions")
            return self.examine_post_update_conditions("BIOS")

    def cleanup(self, return_status):
        super(SEAM_BMC_0009_send_bios_capsule_loop, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0009_send_bios_capsule_loop.main() else Framework.TEST_RESULT_FAIL)
