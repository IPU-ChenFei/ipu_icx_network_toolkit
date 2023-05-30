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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.seamless.lib.seamless_common import SeamlessBaseTest


class SEAM_BMC_0008_send_ucode_capsule_loop(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0008_send_ucode_capsule_loop, self).__init__(test_log, arguments, cfg_opts)
        self.capsule_path = arguments.capsule_path
        self.capsule_path2 = arguments.capsule_path2
        self.capsule_path3 = arguments.capsule_path3
        self.capsule_path4 = arguments.capsule_path4
        self.capsule_name = arguments.capsule_name
        self.capsule_name2 = arguments.capsule_name2
        self.capsule_name3 = arguments.capsule_name3
        self.capsule_name4 = arguments.capsule_name4
        self.expected_ver = arguments.expected_ver
        self.expected_ver2 = arguments.expected_ver2
        self.warm_reset = arguments.warm_reset
        self.start_workload = arguments.start_workload
        self.activation = arguments.activation
        self.loop_count = arguments.loop
        self.update_type = arguments.update_type
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.get_ucode_command = self._workload_path + "GetUcodeVersion.ps1 " + self._powershell_credentials
        self.ping_sut_command = self._workload_path + "PingSut.ps1 " + self._powershell_credentials
        self.restart_sut_command = self._workload_path + "RestartSut.ps1 " + self._powershell_credentials
        self.run_orchestrator = arguments.orchestrator
        self.capsule_xml = arguments.capsule_xml
        self.capsule_xml1 = arguments.capsule_xml
        self.capsule_xml2 = arguments.capsule_xml2
        self.skip_reset = False
        self.sps_mode = arguments.sps_mode
        # self.spi_access = arguments.spi_access
        self.spi_access = False
        self.stressors = arguments.stressors

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0008_send_ucode_capsule_loop, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--capsule_path', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--capsule_path2', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--capsule_path3', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--capsule_path4', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--expected_ver2', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--capsule_name', action='store', help="Name of the capsule to be used for the update", default="")
        parser.add_argument('--capsule_name2', action='store', help="Name of the capsule2 to be used for the update", default="")
        parser.add_argument('--capsule_name3', action='store', help="Name of the capsule3 to be used for the update", default="")
        parser.add_argument('--capsule_name4', action='store', help="Name of the capsule4 to be used for the update", default="")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--loop', type=int, default=1, help="Add argument for # of loops")
        parser.add_argument('--update_type', action='store', help="Specify if efi utility or fit ucode", default="fit_ucode")
        parser.add_argument('--orchestrator',
                            action='store_true',
                            help="Validate update through OrchestratorValidator before running. Requires \"--capulse_xml\".")
        parser.add_argument('--capsule_xml', action="store", help="Path to Capsule XML file for the update. Required for" "\"--orchestrator\".", default="")
        parser.add_argument('--capsule_xml2',
                            action="store",
                            help="Path to Capsule XML file for the second image. Required for \"--orchestrator\".",
                            default="")
        parser.add_argument('--activation', action='store_true', help="Add argument if only activation to be performed")
        parser.add_argument('--spi_access', action='store_true', help="pass argument to perform verification during update ucode", default="")
        parser.add_argument('--stressors', action='store_true', help="pass argument to perform verification after update sps", default="")

    def check_capsule_pre_conditions(self):
        # TODO: add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        # TODO: add workload output analysis
        return True

    def get_current_version(self, echo_version=True):
        """
        Read ucode version
        :param echo_version: True if display output
        :return bios version
        """
        # TODO: add correct command to read version
        version = None
        if self.update_type == "efi_utility":
            self._log.info("Check smbios table for EFI utility version, continue to boot system to windows")
            self._log.info("SMBIOS table reports incorrect utility region HSD:1508078875")
            version = "EFI utility"

        elif self.update_type == "inband":
            cmd = 'cat /proc/cpuinfo | grep microcode'
            result = self.run_ssh_command(cmd)
            version = result.stdout.split('\n')[0].split(' ')
            if echo_version:
                self._log.info("Version detected: " + version[1])
            version = version[1]

        else:
            cmd = 'cat /proc/cpuinfo | grep microcode'
            if self._os_type != OperatingSystems.LINUX:
                output = self.run_powershell_command(self.get_ucode_command, get_output=True)
            else:
                result = self.run_ssh_command(cmd)
                version = result.stdout.split('\n')[0].split(' ')
                if echo_version:
                    self._log.info("Version detected: " + version[1])
                return version[1]
            version = "NONE"
            for line in output.split('\n'):
                if "msr[8b] =" in line:
                    version = line.split(" = ")[1].split('`')[0]
                    break
                elif "BIOS" in line or "Previous" in line:
                    version = line.split(":")[1].strip()
            if echo_version:
                self._log.info("Version detected: " + version)

        return version

    def trigger_update(self, slot1_path, slot2_path):
        if self.update_type == 'inband':
            self._log.info("Sending In-Band Capsule Update...")
            return self.send_capsule_inband(slot1_path, self.start_workload, update_type="inband")
        elif (self.update_type == 'upgrade'):
            self._log.info("Sending upgrade capsule...")
            return self.send_capsule(slot1_path, self.CAPSULE_TIMEOUT, self.start_workload)
        elif (self.update_type == "downgrade"):
            self._log.info("Sending downgrade capsules...")
            return self.send_capsule(slot1_path, self.CAPSULE_TIMEOUT, self.start_workload, capsule_path2=slot2_path, update_type='ucode')
        else:
            self._log.info("Sending Out-Of-Band Capsule Update...")
            return self.send_capsule(slot1_path, self.CAPSULE_TIMEOUT, self.start_workload, capsule_path2=slot2_path, update_type='ucode')

    def execute(self):
        """
        TC:- 69957,70858
        Cmd :- python SEAM_BMC_0008_send_ucode_capsule_loop.py
            --capsule_path "n th version of fv1"
            --capsule_path2 "n th version of fv2"
            --capsule_path3 "n-1 th version of fv1"
            --capsule_path4 "n-1 th version of fv2"
            --expected_ver "nth version"
            --expected_ver2 "n-1 th version"
            --loop 100 --update_type ucode

        TC :- 66214.1
        cmd :- python SEAM_BMC_0008_send_ucode_capsule_loop.py
            --capsule_path "n th version of fv1"
            --capsule_path2 "n th version of fv2"
            --capsule_path3 "n-1 th version of fv1"
            --capsule_path4 "n-1 th version of fv2"
            --expected_ver "nth version"
            --expected_ver2 "n-1 th version"
            --warm_reset --update_type ucode
        """
        # Cache Expected Versions so we don't have to rewrite the command line nor the version checks.
        # A bit duct-tapey, but it should do fine.
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
        if self.capsule_name4 != "":
            self.capsule_path4 = self.find_cap_path(self.capsule_name4)
            self._log.info("capsule path4 {}".format(self.capsule_path4))
        expected_version1 = self.expected_ver
        expected_version2 = self.expected_ver2

        # Sort out Capsule paths to allow the user to specify only two capsules for inband mode.
        slot1_capsule1 = self.capsule_path
        slot1_capsule2 = self.capsule_path3 if self.update_type != "inband" else self.capsule_path2
        slot2_capsule1 = self.capsule_path2 if self.update_type != "inband" else None
        slot2_capsule2 = self.capsule_path4 if self.update_type != "inband" else None

        for x in range(self.loop_count):
            self._log.info("\n")
            self._log.info("Executing Update 1 on Loop #" + str(x))

            self.summary_log.info("\n\n")
            self.summary_log.info("Results of Update 1 on Loop #" + str(x))

            self.expected_ver = expected_version1
            self.capsule_xml = self.capsule_xml1
            if not self.trigger_update(slot1_capsule1, slot2_capsule1):
                return False

            if self.update_type not in ['downgrade', 'upgrade']:
                self._log.info("\n")
                self._log.info("Executing Update 2 on Loop #" + str(x))

                self.summary_log.info("\n\n")
                self.summary_log.info("Results of Update 2 on Loop #" + str(x))

                self.expected_ver = expected_version2
                self.capsule_xml = self.capsule_xml2
                if not self.trigger_update(slot1_capsule2, slot2_capsule2):
                    return False

            #if (x % 20 == 0):
            #    self._bmc_redfish.reset_bmc()
            #    time.sleep(100)

        self._log.info("\tChecking post-update conditions")
        return self.examine_post_update_conditions(self.update_type)

    def cleanup(self, return_status):
        super(SEAM_BMC_0008_send_ucode_capsule_loop, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0008_send_ucode_capsule_loop.main() else Framework.TEST_RESULT_FAIL)
