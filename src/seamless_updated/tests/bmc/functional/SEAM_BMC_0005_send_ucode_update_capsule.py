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


class SEAM_BMC_0005_send_ucode_update_capsule(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0005_send_ucode_update_capsule, self).__init__(test_log, arguments, cfg_opts)
        self.capsule_path = arguments.capsule_path
        self.capsule_path2 = arguments.capsule_path2
        self.capsule_path3 = arguments.capsule_path3
        self.expected_ver = arguments.expected_ver
        self.expected_ver2 = arguments.expected_ver2
        self.expected_ver3 = arguments.expected_ver3
        self.capsule_name = arguments.capsule_name
        self.capsule_name2 = arguments.capsule_name2
        self.capsule_name3 = arguments.capsule_name3
        self.warm_reset = arguments.warm_reset
        self.execution_type = arguments.execution_type
        self.update_type = arguments.update_type
        self.fw_type = self.update_type
        self.one_capsule = arguments.one_capsule
        self.two_capsule = arguments.two_capsule
        self.start_workload = arguments.start_workload
        self.sut_mode = arguments.sut_mode
        self.capsule_type = arguments.capsule_type
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.get_ucode_command = self._workload_path + "GetUcodeVersion.ps1 " + self._powershell_credentials
        self.ping_sut_command = self._workload_path + "PingSut.ps1 " + self._powershell_credentials
        self.restart_sut_command = self._workload_path + "RestartSut.ps1 " + self._powershell_credentials
        self.run_orchestrator = arguments.orchestrator
        self.capsule_xml = arguments.capsule_xml
        self.parallel_staging = arguments.parallel_staging
        self.multi_update_flow = arguments.multi_update_flow
        self.skip_reset = False
        self.activation = arguments.activation
        self.sps_mode = arguments.sps_mode
        self.spi_access = False
        # self.spi_access = arguments.spi_access
        self.stressors = arguments.stressors
        self.ac_while_staging = arguments.ac_while_staging

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0005_send_ucode_update_capsule, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--capsule_path', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--capsule_path2', action='store', help="Path to the 2nd capsule to be used for the update", default="")
        parser.add_argument('--capsule_path3', action='store', help="Path to the 3rd capsule to be used for the update", default="")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update of capsule", default="")
        parser.add_argument('--expected_ver2', action='store', help="The version expected to be reported after update of capsule2", default="")
        parser.add_argument('--expected_ver3', action='store', help="The version expected to be reported after update of capsule3", default="")
        parser.add_argument('--capsule_name', action='store', help="Name of the capsule to be used for the update", default="")
        parser.add_argument('--capsule_name2', action='store', help="Name of the capsule2 to be used for the update", default="")
        parser.add_argument('--capsule_name3', action='store', help="Name of the capsule3 to be used for the update", default="")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--update_type', action='store', help="Specify if efi utility, fit ucode, inband", default="fit_ucode")
        parser.add_argument('--one_capsule', action='store_true', help="Add argument if upgrading version")
        parser.add_argument('--two_capsule', action='store_true', help="Add argument if downgrading version")
        parser.add_argument('--sut_mode', action='store', help="State if SUT is in EFI mode or DC power off mode", default="")
        parser.add_argument('--orchestrator',
                            action='store_true',
                            help="Validate update through OrchestratorValidator before running. Requires \"--capulse_xml\".")
        parser.add_argument('--capsule_xml', action="store", help="Path to Capsule XML file for the update. Required for" "\"--orchestrator\".", default="")
        parser.add_argument('--multi_update_flow', action='store_true', help='Add argument if multiple ucode update flow required')
        parser.add_argument('--capsule_type', action='store', help="Add argument as 'negative' for negative usecases", default="")
        parser.add_argument('--parallel_staging', action='store_true', help="Add this argument if need to update capsules parallelly", default="")
        parser.add_argument('--execution_type',
                            action='store',
                            help="Add argument if inband/outband flow stress bad capsule update to be performed",
                            default="")

        parser.add_argument('--activation', action='store_true', help="Add argument if only activation to be performed")
        # parser.add_argument('--spi_access', action='store_true',
        #                     help="pass argument to perform verification after update sps", default="")
        parser.add_argument('--stressors', action='store_true', help="pass argument to perform verification after update sps", default="")
        parser.add_argument('--ac_while_staging', action='store_true',
                            help="Add this argument if need to stage capsules parallelly", default="")

    def get_current_version(self, echo_version=True):
        """
        Read ucode version
        :param echo_version: True if display output
        :return bios version
        """
        # To-do add correct command to read version
        version = None
        if self.update_type == "efi_utility":
            self._log.info("Check smbios table for EFI utility version, continue to boot system to windows")
            self._log.info("SMBIOS table reports incorrect utility region HSD:1508078875")
            version = "EFI utility"

        elif self.update_type == "fit_ucode":
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

        elif self.update_type == "inband":
            cmd = 'cat /proc/cpuinfo | grep microcode'
            result = self.run_ssh_command(cmd)
            version = result.stdout.split('\n')[0].split(' ')
            if echo_version:
                self._log.info("Version detected: " + version[1])
            version = version[1]

        return version

    def check_capsule_pre_conditions(self):
        # To-Do add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        # To-Do add workload output analysis
        return True

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

        if self.update_type == 'inband':
            if self.capsule_type == 'negative':
                """
                TC:- 67184.1, 67185.1, 67186.1
                python SEAM_BMC_0005_send_ucode_update_capsule.py
                --update_type inband 
                --capsule_path <negative capsule>
                --expected_ver <current version> --capsule_type nagative'
                """
                self._log.info("Sending In-Band Negative Capsule Update...")
                capsule_result = self.send_capsule_inband(self.capsule_path, self.start_workload, update_type="inband", capsule_type="negative")
                return capsule_result
            elif self.multi_update_flow:
                """
                TC :- 68164.2
                cmd :- python SEAM_BMC_0005_send_ucode_update_capsule.py
                    --capsule_path "ucode inband (n-1)th version"
                    --expected_ver 0x
                    --capsule_path2 "ucode inband (n)th version"
                    --expected_ver2 0x
                    --capsule_path3 "ucode inband (n+1)th version"
                    --expected_ver3 0x
                    --update_type inband --multi_update_flow --warm_reset
                """
                self._log.info("Sending In-Band Capsule Update of (n-1)th version...")
                capsule_result = self.send_capsule_inband(self.capsule_path, self.start_workload, update_type="inband")

                self._log.info("Sending In-Band Capsule Update of (n)th version...")
                self.expected_ver = self.expected_ver2
                capsule_result2 = self.send_capsule_inband(self.capsule_path2, self.start_workload, update_type="inband")

                self._log.info("Sending In-Band Capsule Update of (n+1)th version...")
                self.expected_ver = self.expected_ver3
                capsule_result3 = self.send_capsule_inband(self.capsule_path3, self.start_workload, update_type="inband")

                if capsule_result and capsule_result2 and capsule_result3:
                    return True
                else:
                    return False
            elif self.execution_type == 'stress_badcapsule':
                """
                TC :- 67191.1
                cmd :- python SEAM_BMC_0005_send_ucode_update_capsule.py --update_type inband --execution_type stress_badcapsule
                    --capsule_path "ucode inband (n-1)th version"
                    --expected_ver 0x
                    --capsule_path2 "ucode inband negative Capsule"
                    --capsule_path3 "ucode inband (n)th version"
                    --expected_ver2 0x
                    --warm_reset

                """
                if self.capsule_path != "" and self.capsule_path2 != "" and self.capsule_path3 != "":
                    self.warm_reset = False
                    self.skip_reset = True
                    self._log.info("sending (n-1)th version capsules.... ")
                    result = self.send_capsule_inband(self.capsule_path, self.start_workload, update_type='inband')

                    self._log.info("sending negative capsules... ")
                    result1 = self.send_capsule_inband(self.capsule_path2, self.start_workload, update_type='inband', capsule_type="negative")

                    self.warm_reset = True
                    self.skip_reset = False
                    self.expected_ver = self.expected_ver2
                    self._log.info("sending nth version capsule.... ")
                    result2 = self.send_capsule_inband(self.capsule_path3, self.start_workload, update_type='inband')

                    if result and result1 and result2:
                        return True
                    else:
                        self._log.error("some capsules are not flashed properly...")
                        return False
            elif self.execution_type == 'inband_parallel':
                """
                TC :- 67204.1
                python SEAM_BMC_0005_send_ucode_update_capsule.py
                --update_type inband
                --capsule_path <capsule path> 
                --expected_ver <capsule version> 
                --execution_type inband_parallel 
                --warm_reset
                """
                capsule_res = self.send_capsule_inband_parallel(self.capsule_path, self.start_workload, update_type="inband", capsule_path2=self.capsule_path2)
                if capsule_res:
                    return True
                else:
                    return False
            else:
                """
                TC:- 68723 & 67182.3
                python SEAM_BMC_0005_send_ucode_update_capsule.py
                --update_type inband
                --capsule_path <capsule path>
                --expected_ver <capsule version> 
                --warm_reset'
                """
                self._log.info("Sending In-Band Capsule Update...")
                capsule_result = self.send_capsule_inband(self.capsule_path, self.start_workload, update_type="inband")
        elif self.update_type != 'inband' and self.capsule_type == 'negative':
            if self.execution_type != 'outband_stress_badcapsule':
                """
                TC :- 66208, 66209.1, 66210.1
                python SEAM_BMC_0005_send_ucode_update_capsule.py 
                --capsule_path <negative capsule> 
                --capsule_type negative'
                """
                self._log.info("Sending Out-Of-Band Negative Capsule Update...")
                capsule_result = self.send_capsule_negative(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload, capsule_type="negative")
            elif self.execution_type == 'outband_stress_badcapsule':
                """
                TC :- 66215.2
                python SEAM_BMC_0005_send_ucode_update_capsule.py
                --capsule_type negative 
                --capsule_path <capsule path> 
                --capsule_path2 <capsule2 path 
                --expected_ver <capsule2 ver>
                --execution_type outband_stress_badcapsule
                --warm_reset
                """
                self._log.info("Sending Out-Of-Band Negative Capsule Update...")
                capsule_result = self.send_capsule_negative(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload, capsule_type="negative")
                if capsule_result:
                    self._log.info("Sending Out-Of-Band Capsule Update...")
                    capsule_result2 = self.send_capsule(self.capsule_path2, self.CAPSULE_TIMEOUT, self.start_workload)
                    if capsule_result2:
                        return True
                    else:
                        return False
        elif self.parallel_staging:
            """
            TC :- 66276.2
            cmd :- python SEAM_BMC_0005_send_ucode_update_capsule.py 
            --capsule_path <path for Nth ucode FV2 capsule>
            --capsule_path2 <path for (N-1)th ucode FV2 capsule>
            --expected_ver <Nth ucode cap version>  
            --parallel_staging
            --warm_reset
            """
            return self.send_capsule_parallel(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
        elif self.sut_mode == 'S5':
            """
            TC :- 66222.1
            cmd :- python SEAM_BMC_0005_send_ucode_update_capsule.py 
            --capsule_path <path for Nth ucode FV2 capsule>
            --expected_ver <Nth ucode cap version>  
            --sut_mode S5
            """
            self.get_current_version()
            self.os.shutdown()
            self._log.info("System entered into S5 state, waiting for SUT to settle down..")
            time.sleep(self.SUT_SETTLING_TIME)
            self._log.info("=========UPDATING UCODE CAPSULE IN S5 STATE==========\n")
            self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
            self._log.info("Waking up the system from S5..\n")
            if self._product == "EGS":
                self._dc_power.dc_power_on()
            elif self._product == "WHT":
                self._dc_power.dc_power_reset()
            self._log.info("Waiting for system to boot into OS..")
            self.os.wait_for_os(self.reboot_timeout)
            time.sleep(self.POST_SLEEP_DELAY)
            if self.sut_ssh.is_alive():
                self._log.info("System booted into OS..!!\n")
                current_version = self.get_current_version()
                if current_version == self.expected_ver:
                    self._log.info("\tThe current version {} is the expected version {}".format(current_version, self.expected_ver))
                    return True
                else:
                    self._log.info("\tCurrent version {} is not the expected version {}".format(current_version, self.expected_ver))
                    return False
            else:
                raise RuntimeError("System not booted into OS after the given time..!!")

        elif self.ac_while_staging:
            """
            TC :- 66091.3
            cmd :- python3 SEAM_BMC_0005_send_ucode_update_capsule.py 
            --capsule_path <path for 1st bios capsule
            --ac_while_staging
            """

            result = False

            if self.capsule_path != "":
                self.warm_reset = False
                self.ac_while_staging = True
                self.expected_ver = self.get_current_version()
                return self.send_capsule_ac_while_staging(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
            else:
                if self.capsule_path == "":
                    self._log.error("Capsule 1 is not present in the command")

                raise RuntimeError("Command is not proper. Please check the command.")

        else:
            """
            TC :- 66207.3
            cmd :- python SEAM_BMC_0005_send_ucode_update_capsule.py
                --capsule_path "ucode OOB FV2"
                --expected_ver 0x
                --warm_reset
            """
            self._log.info("Sending Out-Of-Band Capsule Update...")
            capsule_result = self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)

        return capsule_result

    def cleanup(self, return_status):
        super(SEAM_BMC_0005_send_ucode_update_capsule, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0005_send_ucode_update_capsule.main() else Framework.TEST_RESULT_FAIL)
