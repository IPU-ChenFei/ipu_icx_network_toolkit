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

    Attempts to send in a capsule use to initiate the seamless update
"""
import sys
import time
from datetime import datetime, timedelta

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.seamless.lib.seamless_common import SeamlessBaseTest


class SEAM_BMC_0018_send_capsule_update_in_uefi_shell(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0018_send_capsule_update_in_uefi_shell, self).__init__(test_log, arguments, cfg_opts)
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
        self.update_type = arguments.update_type
        self.start_workload = arguments.start_workload
        self.sut_mode = arguments.sut_mode
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.get_ucode_command = self._workload_path + "GetUcodeVersion.ps1 " + self._powershell_credentials
        self.ping_sut_command = self._workload_path + "PingSut.ps1 " + self._powershell_credentials
        self.restart_sut_command = self._workload_path + "RestartSut.ps1 " + self._powershell_credentials
        self.run_orchestrator = arguments.orchestrator
        self.capsule_xml = arguments.capsule_xml
        self.flash_type = arguments.flash_type
        self.capsule = "SPS"
        self.skip_reset = False
        self.activation = False
        self.sps_mode = arguments.sps_mode

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0018_send_capsule_update_in_uefi_shell, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--capsule_path', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--capsule_path2', action='store', help="Path to the capsule2 to be used for the update", default="")
        parser.add_argument('--capsule_path3', action='store', help="Path to the capsule3 to be used for the update", default="")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--expected_ver2', action='store', help="The version expected to be reported after 2nd capsule update", default="")
        parser.add_argument('--expected_ver3', action='store', help="The version expected to be reported after 3rd capsule update", default="")
        parser.add_argument('--capsule_name', action='store', help="Name of the capsule to be used for the update", default="")
        parser.add_argument('--capsule_name2', action='store', help="Name of the capsule2 to be used for the update", default="")
        parser.add_argument('--capsule_name3', action='store', help="Name of the capsule3 to be used for the update", default="")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--update_type', action='store', help="Specify if efi utility or fit ucode", default="fit_ucode")
        parser.add_argument('--sut_mode', action='store', help="State if SUT is in UEFI mode or DC power off mode", default="")
        parser.add_argument('--orchestrator',
                            action='store_true',
                            help="Validate update through OrchestratorValidator before running. Requires \"--capulse_xml\".")
        parser.add_argument('--capsule_xml', action="store", help="Path to Capsule XML file for the update. Required for" "\"--orchestrator\".", default="")
        parser.add_argument("--flash_type", action="store", help="Specify if upgrade, downgrade and alternate update of ucode capsule")
        parser.add_argument('--uefi', action='store_true', help="Add argument if want to flash capsule when SUT in UEFI shell")

    def check_capsule_pre_conditions(self):
        # TODO: add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        # TODO: add workload output analysis
        return True

    def get_current_version(self, echo_version=True):
        if self.update_type == 'bios':
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
                    self._log.info("Version detected: {}".format(version[1]))
                return version[1]
            version = "NONE"
            for line in output.split('\n'):
                if "SMBIOSBIOSVersion : " in line:
                    version = line.split(' : ')[1]
                    break
            if echo_version:
                self._log.info("Version detected : {}".format(version))
            return version
        elif self.update_type == 'sps':
            """
                    Read sps version
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

            rec_ver = version.split('(Recovery)')[0].strip()
            opr_ver = version.split('(Recovery)')[1].split('(Operational)')[0].replace(',', '').strip()

            if me_mode == 'Normal':
                me_mode = 'Operational'

            version = 'Operational: ' + opr_ver + ' Recovery: ' + \
                rec_ver + ' Current State: ' + me_mode

            if echo_version:
                self._log.info("\tVersion detected: " + version)
            return version
        else:
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

    def get_expected_version(self, cap_path, exp_ver, echo_version=True):
        current_version = self.get_current_version()
        if "RcvOnOpr" in cap_path:
            opr = exp_ver.split("Operational: ")[1].strip().split(" ")[0]
            rcv = current_version.split("Recovery: ")[1].strip().split(" ")[0]
        elif "Recovery" in cap_path:
            rcv = exp_ver.split("Recovery: ")[1].strip().split(" ")[0]
            opr = current_version.split("Operational: ")[1].strip().split(" ")[0]
        elif "Operational" in cap_path:
            opr = exp_ver.split("Operational: ")[1].strip().split(" ")[0]
            rcv = current_version.split("Recovery: ")[1].strip().split(" ")[0]
        else:
            raise RuntimeError("Invalid Capsule")
        mode = exp_ver.split("Current State: ")[1].strip()

        expected_ver = "Operational: " + opr + \
            " Recovery: " + rcv + " Current State: " + mode

        return expected_ver

    def execute(self):
        global result
        if self.capsule_name != "":
            self.capsule_path = self.find_cap_path(self.capsule_name)
            self._log.info("capsule path {}".format(self.capsule_path))
        if self.capsule_name2 != "":
            self.capsule_path2 = self.find_cap_path(self.capsule_name2)
            self._log.info("capsule path2 {}".format(self.capsule_path2))
        if self.capsule_name3 != "":
            self.capsule_path3 = self.find_cap_path(self.capsule_name3)
            self._log.info("capsule path3 {}".format(self.capsule_path3))
        try:
            if self.flash_type == "upgrade":
                """
                TC :- 66220.1
                cmd :- python SEAM_BMC_0018_send_capsule_update_in_uefi_shell.py 
                --capsule_path <(N-1)th ucode FV1 cap path>
                --capsule_path2 <(N-1)th ucode FV2 cap path> 
                --expected_ver <(N-1)th ucode cap version>
                --capsule_path3 <Nth ucode FV2 cap path> 
                --expected_ver2 <Nth ucode cap version> 
                --sut_mode uefi
                --flash_type upgrade
                """
                print("Entering capsule Upgrade TESTCASE")
                result = False
                if self.capsule_path != "" and self.capsule_path2 != "" and self.capsule_path3 != "":
                    self.get_current_version()
                    self._log.info("============= Rebooting & Entering UEFI shell ==============")
                    uefi_resp = self._uefi_util_obj.enter_uefi_shell()
                    if uefi_resp:
                        self._log.info("============= Sending Downgraded (N-1th) capsule versions FV1 & FV2 =============")
                        cap_resp = self.send_capsule(self.capsule_path,
                                                     self.CAPSULE_TIMEOUT,
                                                     self.start_workload,
                                                     capsule_path2=self.capsule_path2,
                                                     update_type='ucode')
                        if cap_resp:
                            self._uefi_obj.warm_reset()
                            self._log.info("Wait till the system comes alive...")
                            self.os.wait_for_os(self._reboot_timeout)
                            current_version = self.get_current_version()
                            if current_version == self.expected_ver:
                                self._log.info("\tThe current version {} is the expected version {}".format(current_version, self.expected_ver))
                            else:
                                self._log.info("\tCurrent version {} is not the expected version {}".format(current_version, self.expected_ver))
                                result = False
                    else:
                        self._log.error("UEFI shell Access Failed")
                        return False
                    self._log.info("================ Rebooting & Re-Entering UEFI shell for Upgraded patch flash ======================")
                    uefi_resp2 = self._uefi_util_obj.enter_uefi_shell()
                    if uefi_resp2:
                        self._log.info("============= Sending Upgraded Nth capsule version =============")
                        self.expected_ver = self.expected_ver2
                        cap_resp2 = self.send_capsule(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload)
                    else:
                        self._log.error("UEFI shell Access Failed")
                        return False
                    if cap_resp and cap_resp2:
                        self._uefi_obj.warm_reset()
                        self._log.info("============= System Reboot to OS underway =============")
                        self.os.wait_for_os(self._reboot_timeout)
                        current_version = self.get_current_version()
                        if current_version == self.expected_ver:
                            self._log.info("\tThe current version {} is the expected version {}".format(current_version, self.expected_ver))
                            result = True
                        else:
                            self._log.info("\tCurrent version {} is not the expected version {}".format(current_version, self.expected_ver))
                            result = False
            elif self.flash_type == "downgrade":
                """
                TC :- 66221.1
                cmd :- python SEAM_BMC_0018_send_capsule_update_in_uefi_shell.py 
                --capsule_path <(N-1)th ucode FV1 cap path>
                --capsule_path2 <(N-1)th ucode FV2 cap path> 
                --expected_ver <(N-1)th ucode cap version> 
                --sut_mode uefi
                --flash_type downgrade
                """
                print("Entering Capsule Downgrade TESTCASE")
                result = False
                if self.capsule_path != "" and self.capsule_path2 != "":
                    self.get_current_version()
                    self._log.info("============= Rebooting & Entering UEFI shell =============")
                    uefi_resp = self._uefi_util_obj.enter_uefi_shell()
                    if uefi_resp:
                        self._log.info("============= Sending Downgraded (N-1th) capsule version =============")
                        cap_resp = self.send_capsule(self.capsule_path,
                                                     self.CAPSULE_TIMEOUT,
                                                     self.start_workload,
                                                     capsule_path2=self.capsule_path2,
                                                     update_type='ucode')
                    else:
                        self._log.error("UEFI shell Access Failed")
                        return False
                    if cap_resp:
                        self._uefi_obj.warm_reset()
                        self._log.info("============= System Reboot to OS underway =============")
                        self.os.wait_for_os(self._reboot_timeout)
                        current_version = self.get_current_version()
                        if current_version == self.expected_ver:
                            self._log.info("\tThe current version {} is the expected version {}".format(current_version, self.expected_ver))
                            result = True
                        else:
                            self._log.info("\tCurrent version {} is not the expected version {}".format(current_version, self.expected_ver))
                            result = False
            elif self.sut_mode == 'uefi' and self.update_type == 'bios':
                """
                TC :- 67409.1
                cmd :- python SEAM_BMC_0018_send_capsule_update_in_uefi_shell.py 
                --capsule_path <path for bios capsule>
                --expected_ver <bios cap version>  
                --sut_mode uefi
                --update_type bios
                """
                result = False
                self.get_current_version()
                self._log.info("============= Rebooting and Entering into UEFI shell ==============")
                uefi_resp = self._uefi_util_obj.enter_uefi_shell()
                if uefi_resp:
                    self._log.info("Updating BIOS capsule..")
                    cap_resp = self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
                else:
                    self._log.error("System failed to enter UEFI Shell")
                    return False
                if cap_resp:
                    self._uefi_obj.warm_reset()
                    self._log.info("============= System Reboot to OS underway.. =============")
                    self.os.wait_for_os(self._reboot_timeout)
                    current_version = self.get_current_version()
                    if current_version == self.expected_ver:
                        self._log.info("\tThe current version {} is the expected version {}".format(current_version, self.expected_ver))
                        result = True
                    elif self.expected_ver in current_version:
                        self._log.info("\tThe expected version {} is in the current version {}".format(self.expected_ver, current_version))
                        result = True
                    else:
                        self._log.info("\tCurrent version {} is not the expected version {}".format(current_version, self.expected_ver))
                        result = False
            elif self.sut_mode == 'uefi' and self.update_type == 'sps':
                """
                TC :- 66173.1
                cmd :- python SEAM_BMC_0018_send_capsule_update_in_uefi_shell.py 
                --capsule_path "capsule path of Recovery on Operational" 
                --expected_ver "Operational: x.x.x.x Current State: Recovery" 
                --capsule_path2 "Recovery capsule path" 
                --expected_ver2 "Recovery: x.x.x.x Current State: Recovery" 
                --capsule_path3 "Operational capsule path" 
                --expected_ver3 "Operational: x.x.x.x Current State: Operational" 
                --sut_mode uefi
                --update_type sps
                """
                result = False
                self.get_current_version()
                self._log.info("============= Initiating Recovery-On-Operational Capsule Update==============")
                self._log.info("============= Rebooting and Entering into UEFI shell ==============")
                uefi_resp1 = self._uefi_util_obj.enter_uefi_shell()
                if uefi_resp1:
                    self._log.info("Updating SPS capsule 1..")
                    cap_resp1 = self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule)
                else:
                    self._log.error("System failed to enter UEFI Shell")
                    return False
                if cap_resp1:
                    self._uefi_obj.warm_reset()
                    self._log.info("============= System Reboot to OS underway =============")
                    self.os.wait_for_os(self._reboot_timeout)
                    self.expected_ver = self.get_expected_version(self.capsule_path, self.expected_ver)
                    current_version = self.get_current_version()
                    if current_version == self.expected_ver:
                        self._log.info("\tThe current version {} is the expected version {}".format(current_version, self.expected_ver))
                    else:
                        self._log.info("\tCurrent version {} is not the expected version {}".format(current_version, self.expected_ver))
                        result = False
                self._log.info("============= Initiating Recovery Capsule Update==============")
                self._log.info("============= Rebooting and Entering into UEFI shell ==============")
                uefi_resp2 = self._uefi_util_obj.enter_uefi_shell()
                if uefi_resp2:
                    self._log.info("Updating SPS capsule 2..")
                    cap_resp2 = self.send_capsule(self.capsule_path2, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule)
                else:
                    self._log.error("System failed to enter UEFI Shell")
                    return False
                if cap_resp2:
                    self._uefi_obj.warm_reset()
                    self._log.info("============= System Reboot to OS underway =============")
                    self.os.wait_for_os(self._reboot_timeout)
                    self.expected_ver = self.get_expected_version(self.capsule_path2, self.expected_ver2)
                    current_version2 = self.get_current_version()
                    if current_version2 == self.expected_ver:
                        self._log.info("\tThe current version {} is the expected version {}".format(current_version2, self.expected_ver))
                    else:
                        self._log.info("\tCurrent version {} is not the expected version {}".format(current_version2, self.expected_ver))
                        result = False
                self._log.info("============= Initiating Operational Capsule Update==============")
                self._log.info("============= Rebooting and Entering into UEFI shell ==============")
                uefi_resp3 = self._uefi_util_obj.enter_uefi_shell()
                if uefi_resp3:
                    self._log.info("Updating SPS capsule 3..")
                    cap_resp3 = self.send_capsule(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule)
                else:
                    self._log.error("System failed to enter UEFI Shell")
                    return False
                if cap_resp3:
                    self._uefi_obj.warm_reset()
                    self._log.info("============= System Reboot to OS underway =============")
                    self.os.wait_for_os(self._reboot_timeout)
                    self.expected_ver = self.get_expected_version(self.capsule_path3, self.expected_ver3)
                    current_version3 = self.get_current_version()
                    if current_version3 == self.expected_ver:
                        self._log.info("\tThe current version {} is the expected version {}".format(current_version3, self.expected_ver))
                    else:
                        self._log.info("\tCurrent version {} is not the expected version {}".format(current_version3, self.expected_ver))
                        result = False
                if cap_resp1 and cap_resp2 and cap_resp3:
                    result = True

            elif self.sut_mode == 'uefi' and self.update_type == 'inband':
                """
                   TC-67196.3:  Seamless Ucode Update Flow with SUT in UEFI shell & Post update Verification
                   Command: python3 SEAM_BMC_0018_send_capsule_update_in_uefi_shell.py 
                     --update_type inband --sut_mode uefi --capsule_path <N> --expected_ver <> --warm_reset
                   Prerequisites: CapsuleApp.efi & firmware(N).cap Capsule should be copied inside USB.  
                     ==================================================================================================
                   TC-67197.2: Seamless Ucode Update Flow downgrade, with SUT in UEFI shell & Post update Verification
                   Command: python3 SEAM_BMC_0018_send_capsule_update_in_uefi_shell.py 
                     --update_type inband --sut_mode uefi --capsule_path <N-1> --expected_ver <> --warm_reset
                   Prerequisites: CapsuleApp.efi & firmware(N-1).cap Capsule should be copied inside USB.
                """
                result = False
                self.get_current_version()
                self._log.info("============= {} ======================".format("Entring into Uefi shell"))
                in_uefi = self._uefi_util_obj.enter_uefi_shell()
                if in_uefi:
                    self._log.info("Sending In-Band Capsule Update...")
                    self.send_capsule_inband(self.capsule_path, self.start_workload, update_type="inband")
                else:
                    self._log.error("System failed to enter UEFI Shell")
                    return False
                """
                        :Reversing capsule path 
                        :partitioning with backslash and reversing again to get capsule name.

                """
                reversed_string = self.capsule_path[::-1]
                Partitioned_string = reversed_string.partition('\\')
                before_partitioned = Partitioned_string[0]
                again_reverse = before_partitioned[::-1]
                entire_command = 'CapsuleApp.efi ' + again_reverse + ' -NR'
                print(entire_command)
                output = self.get_uefi_shell_cmd('map -r')
                fs = None
                for i, line in enumerate(output):
                    if "FS0" in line and "USB" in output[i + 1]:
                        fs = "fs0:"
                    elif "FS1" in line and "USB" in output[i + 1]:
                        fs = "fs1:"
                    elif "FS2" in line and "USB" in output[i + 1]:
                        fs = "fs2:"
                self._log.info("Trying to detect USB.........\n")
                if fs is not None:
                    self._log.info("============= USB IS BEING DETECTED ======================".format(fs))
                    uefishell_cmd = [
                        fs,
                        'dir',
                        entire_command,  # 'CapsuleApp.efi L0-8b000370_C0-8c000250_D0-8d000190.cap -NR',
                        'CapsuleApp.efi -E'
                    ]
                else:
                    raise RuntimeError("=========USB NOT DETECTED===========")
                    return False
                if in_uefi:
                    self._log.info("============= {} : {} ======================".format("Executing command", uefishell_cmd))
                    for command in uefishell_cmd:
                        print("command: ", command)
                        cmd_res = self.get_uefi_shell_cmd(command)
                        for i, line in enumerate(cmd_res):
                            if "CapsuleApp" in line and "Unsupported" in cmd_res[i + 1]:
                                self._log.error("=========Capsule image updating isn't completed===========")
                                return False
                        for i in cmd_res:
                            if "ESRT - Not Found" in i:
                                self._log.error("=========LastAttemptStatus isn't Successfull===========")
                                return False
                        if cmd_res:
                            result = True
                else:
                    self._log.error("Not able to get in uefi shell....")
                    return result

        except Exception as e:
            self._log.info(e)

        finally:
            self._uefi_obj.warm_reset()
            self._log.info("Wait till the system comes alive...")
            self.os.wait_for_os(self._reboot_timeout)
        return result

    def cleanup(self, return_status):
        super(SEAM_BMC_0018_send_capsule_update_in_uefi_shell, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0018_send_capsule_update_in_uefi_shell.main() else Framework.TEST_RESULT_FAIL)
