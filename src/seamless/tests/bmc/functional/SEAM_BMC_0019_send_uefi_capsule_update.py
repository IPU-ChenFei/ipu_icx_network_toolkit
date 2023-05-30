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
import re
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.seamless.lib.seamless_common import SeamlessBaseTest


class SEAM_BMC_0019_send_uefi_capsule_update(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0019_send_uefi_capsule_update, self).__init__(test_log, arguments, cfg_opts)
        self.capsule_path = arguments.capsule_path
        self.capsule_path2 = arguments.capsule_path2
        self.capsule_path3 = arguments.capsule_path3
        self.capsule_path4 = arguments.capsule_path4
        self.capsule_path5 = arguments.capsule_path5
        self.capsule_path6 = arguments.capsule_path6
        self.capsule_path7 = arguments.capsule_path7
        self.capsule_path8 = arguments.capsule_path8
        self.expected_ver = arguments.expected_ver
        self.expected_ver2 = arguments.expected_ver2
        self.capsule_name = arguments.capsule_name
        self.capsule_name2 = arguments.capsule_name2
        self.capsule_name3 = arguments.capsule_name3
        self.capsule_name4 = arguments.capsule_name4
        self.capsule_name5 = arguments.capsule_name5
        self.capsule_name6 = arguments.capsule_name6
        self.capsule_name7 = arguments.capsule_name7
        self.capsule_name8 = arguments.capsule_name8
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
        self.uefi = arguments.uefi
        self.flash_type = arguments.flash_type
        self.fw_type = self.update_type
        self.skip_reset = False
        self.activation = False
        self.sps_mode = arguments.sps_mode
        self.capsule_type = arguments.capsule_type
        self.reboot_while_staging = arguments.reboot_while_staging

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0019_send_uefi_capsule_update, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--capsule_path', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--capsule_path2', action='store', help="Path to the capsule2 to be used for the update", default="")
        parser.add_argument('--capsule_path3', action='store', help="Path to the capsule3 to be used for the update", default="")
        parser.add_argument('--capsule_path4', action='store', help="Path to the capsule4 to be used for the update", default="")
        parser.add_argument('--capsule_path5', action='store', help="Path to the capsule5 to be used for the update", default="")
        parser.add_argument('--capsule_path6', action='store', help="Path to the capsule6 to be used for the update", default="")
        parser.add_argument('--capsule_path7', action='store', help="Path to the capsule7 to be used for the update", default="")
        parser.add_argument('--capsule_path8', action='store', help="Path to the capsule8 to be used for the update", default="")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--expected_ver2', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--capsule_name', action='store', help="Name of the capsule to be used for the update", default="")
        parser.add_argument('--capsule_name2', action='store', help="Name of the capsule2 to be used for the update", default="")
        parser.add_argument('--capsule_name3', action='store', help="Name of the capsule3 to be used for the update", default="")
        parser.add_argument('--capsule_name4', action='store', help="Name of the capsule4 to be used for the update", default="")
        parser.add_argument('--capsule_name5', action='store', help="Name of the capsule5 to be used for the update", default="")
        parser.add_argument('--capsule_name6', action='store', help="Name of the capsule6 to be used for the update", default="")
        parser.add_argument('--capsule_name7', action='store', help="Name of the capsule7 to be used for the update", default="")
        parser.add_argument('--capsule_name8', action='store', help="Name of the capsule8 to be used for the update", default="")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed", default=False)
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--update_type', action='store', help="Specify if efi utility or fit ucode", default="fit_ucode")
        parser.add_argument('--sut_mode', action='store', help="State if SUT is in UEFI mode or DC power off mode", default="")
        parser.add_argument('--orchestrator',
                            action='store_true',
                            help="Validate update through OrchestratorValidator before running. Requires \"--capulse_xml\".")
        parser.add_argument('--capsule_xml', action="store", help="Path to Capsule XML file for the update. Required for" "\"--orchestrator\".", default="")
        parser.add_argument('--uefi', action='store_true', help="Add argument if want to flash ucode when SUT in UEFI shell")
        parser.add_argument("--flash_type", action="store", help="Specify if upgrade, downgrade and alternate update of ucode capsule")
        parser.add_argument('--capsule_type', action='store', help="Add argument as 'negative' for negative usecases", default="")
        parser.add_argument('--reboot_while_staging', action='store_true',
                            help="Add this argument if need to reset the SUT while staging", default="")

    def check_capsule_pre_conditions(self):
        # TODO: add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        # TODO: add workload output analysis
        return True

    def get_uefi_shell_cmd(self, cmd):
        return self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(cmd)

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

    def get_uefi_shell_command(self, cmd):
        return self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(cmd)

    def get_uefi_smbios(self):
        result = False
        try:
            if self._uefi_util_obj.enter_uefi_shell():
                cmd = "smbiosview -t 134"
                self._log.info("=====================Executing UEFI command: {}=======================".format(cmd))
                uefi_cmd_res = self.get_uefi_shell_command(cmd)
                pos_20 = re.compile("00000020")
                pos_10 = re.compile("00000010")
                pos_10_data = list(filter(pos_10.match, uefi_cmd_res))
                pos_20_data = list(filter(pos_20.match, uefi_cmd_res))

                if len(pos_20_data) == 0:
                    self._log.info("============ Regions are not activated booting back to OS==================")
                    self._uefi_obj.warm_reset()
                    self.os.wait_for_os(self._reboot_timeout)
                    self._log.info("=============== Flashing capsules to activate the Regions ====================")
                    if self.flash_type == "uefi_0x2_FV1" or self.flash_type == "S5_0x2_FV1":
                        sut_mod = self.sut_mode
                        self.sut_mode = ""
                    if self.send_capsule_without_version_check(self.capsule_path,
                                                               self.CAPSULE_TIMEOUT,
                                                               self.start_workload,
                                                               capsule_path2=self.capsule_path2,
                                                               update_type="ucode"):
                        if self.flash_type == "uefi_0x2_FV1" or self.flash_type == "S5_0x2_FV1":
                            self.sut_mode = sut_mod
                        if self._uefi_util_obj.enter_uefi_shell():
                            uefi_cmd_res = self.get_uefi_shell_command(cmd)
                            pos_10_data = list(filter(pos_10.match, uefi_cmd_res))
                            pos_20_data = list(filter(pos_20.match, uefi_cmd_res))
                            region_10_val = pos_10_data[0][31:36]
                            region_20_val = pos_20_data[0][10:12]
                            self._log.info("Result of uefi 10th region : {}".format(region_10_val))
                            self._log.info("Result of uefi 20th region : {}".format(region_20_val))
                            if self.flash_type == "uefi_0x2_FV1" and region_20_val == "01":
                                cap_flash = self.uefi_S5()
                                if cap_flash:
                                    self._log.info("nth version of uefi flashed when sut is in uefi mode....")
                                    self._uefi_obj.warm_reset()
                                    self._log.info("Wait till the system boot into OS...")
                                    self.os.wait_for_os(self._reboot_timeout)
                                    return [region_10_val, region_20_val]
                                else:
                                    self._log.error("uefi_S5 function does not function well....")
                            elif self.flash_type == "S5_0x2_FV1" and region_20_val == "01":
                                cap_flash = self.uefi_S5()
                                if cap_flash:
                                    self._log.info("nth version of uefi flashed when sut is in S5 mode....")
                                    self._log.info("Waiting for system to boot into OS..")
                                    self.os.wait_for_os(self.reboot_timeout)
                                    time.sleep(self.POST_SLEEP_DELAY)
                                    return [region_10_val, region_20_val]
                                else:
                                    self._log.error("uefi_S5 function does not function well....")
                            else:
                                self._uefi_obj.warm_reset()
                                self._log.info("Wait till the system boot into OS...")
                                self.os.wait_for_os(self._reboot_timeout)
                                return [region_10_val, region_20_val]
                        else:
                            self._log.error("Failed to enter UEFI shell")
                    else:
                        self._log.error("====================== Capsules are not flashed to activate the Regions ==============================")
                else:
                    region_10_val = pos_10_data[0][31:36]
                    region_20_val = pos_20_data[0][10:12]
                    self._log.info("Result of uefi 10th region : {}".format(region_10_val))
                    self._log.info("Result of uefi 20th region : {}".format(region_20_val))
                    if self.flash_type == "uefi_0x2_FV1" and region_20_val == "01":
                        cap_flash = self.uefi_S5()
                        if cap_flash:
                            self._log.info("nth version of uefi flashed when sut is in uefi mode....")
                            self._uefi_obj.warm_reset()
                            self._log.info("Wait till the system boot into OS...")
                            self.os.wait_for_os(self._reboot_timeout)
                            return [region_10_val, region_20_val]
                        else:
                            self._log.error("uefi_S5 function does not function well....")
                    elif self.flash_type == "S5_0x2_FV1" and region_20_val == "01":
                        cap_flash = self.uefi_S5()
                        if cap_flash:
                            self._log.info("nth version of uefi flashed when sut is in S5 mode....")
                            self._log.info("Waiting for system to boot into OS..")
                            self.os.wait_for_os(self.reboot_timeout)
                            time.sleep(self.POST_SLEEP_DELAY)
                            return [region_10_val, region_20_val]
                        else:
                            self._log.error("uefi_S5 function does not function well....")
                    else:
                        self._uefi_obj.warm_reset()
                        self._log.info("Wait till the system boot into OS...")
                        self.os.wait_for_os(self._reboot_timeout)
                        return [region_10_val, region_20_val]
            else:
                self._log.error("Failed to get inside UEFI shell, Something went wrong....")
        except Exception as e:
            self._log.error(e)
            return result

    def uefi_S5(self):
        res = False
        if self.flash_type == "uefi_0x2_FV1":
            self._log.info("====================== Flashing Nth version of FV1 when sut is in uefi mode==============================")
            if self.send_capsule_without_version_check(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload):
                self._uefi_obj.warm_reset()
                self._log.info("Wait till the system boot to OS...")
                self.os.wait_for_os(self._reboot_timeout)
                res = True
            else:
                self._log.error("nth version capsule flashing failed....")
        elif self.flash_type == "S5_0x2_FV1":
            self._log.info("====================== Entering into S5 State ==============================")
            self._dc_power.dc_power_off()
            self._log.info("System entered into S5 state, waiting for SUT to settle down..")
            time.sleep(self.SUT_SETTLING_TIME)
            self._log.info("====================== Flashing Nth version of FV1 ==============================")
            if self.send_capsule(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload):
                self._log.info("Waking up the system from S5..\n")
                if self._product == "EGS":
                    self._dc_power.dc_power_on()
                    res = True
                elif self._product == "WHT":
                    self._dc_power.dc_power_reset()
                    res = True
                else:
                    self._log.error("Product neither EGS nor WHT....")
            else:
                self._log.error("nth version capsule flashing failed....")
        return res

    def execute(self):
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
        if self.capsule_name5 != "":
            self.capsule_path5 = self.find_cap_path(self.capsule_name5)
            self._log.info("capsule path5 {}".format(self.capsule_path5))
        if self.capsule_name6 != "":
            self.capsule_path6 = self.find_cap_path(self.capsule_name6)
            self._log.info("capsule path6 {}".format(self.capsule_path6))
        if self.capsule_name7 != "":
            self.capsule_path7 = self.find_cap_path(self.capsule_name7)
            self._log.info("capsule path7 {}".format(self.capsule_path7))
        if self.capsule_name8 != "":
            self.capsule_path8 = self.find_cap_path(self.capsule_name8)
            self._log.info("capsule path8 {}".format(self.capsule_path8))
        try:
            result = False
            self._log.info("Checking whether the Regions are activated or not....")
            uefi_data = self.get_uefi_smbios()
            if self.flash_type == "0x2_FV1":
                """
                TC : 66673.2
                cmd : python3 SEAM_BMC_0019_send_eufi_capsule_update.py 
                    --capsule_path "utilityCapsule_0x1_FV1"
                    --capsule_path2 "utilityCapsule_0x1_FV2"
                    --capsule_path3 "utilityCapsule_0x2_FV1"
                    --update_type efi_utility --flash_type 0x2_FV1
                """
                if uefi_data[1] == "02":
                    self._log.info("====================== nth version found downgradig uefi utility ==============================")
                    if self.send_capsule_without_version_check(self.capsule_path,
                                                               self.CAPSULE_TIMEOUT,
                                                               self.start_workload,
                                                               capsule_path2=self.capsule_path2,
                                                               update_type="ucode"):
                        self._log.info("entering into uefi shell.....")
                        uefi_data_check = self.get_uefi_smbios()
                        if uefi_data_check[1] == "01":
                            self._log.info("Downgradation successful ...")
                            self._log.info("====================== upgrading with nth version of FV1 ==============================")
                            if self.send_capsule_without_version_check(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload):
                                self._log.info("====================== Entring into uefi shell to read smbios regions data ==============================")
                                uefi_data1 = self.get_uefi_smbios()
                                if uefi_data1[0] == "00-01" and uefi_data1[1] == "02":
                                    result = True
                                else:
                                    self._log.error("Region data are not updated...")
                            else:
                                self._log.error("Nth version of fv1 not flashed properly....")
                        else:
                            self._log.error("Region not downgraded or something went wrong......")
                    else:
                        self._log.error("Downgradation failed ....")
                elif uefi_data[1] == "01":
                    self._log.info("====================== upgrading with nth version of FV1 ==============================")
                    if self.send_capsule_without_version_check(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload):
                        self._log.info("=============== Entring into uefi shell to read smbios regions data =====================")
                        uefi_data1 = self.get_uefi_smbios()
                        if uefi_data1[0] == "00-01" and uefi_data1[1] == "02":
                            result = True
                        else:
                            self._log.error("Region data are not updated...")
                    else:
                        self._log.error("nth version of 0x2 FV1 capsules not flashed properly...")
                else:
                    self._log.error("Something went wrong..")
            elif self.flash_type == "0x2_FV2":
                """
                TC : 66674.1
                cmd : python3 SEAM_BMC_0019_send_eufi_capsule_update.py 
                    --capsule_path "utilityCapsule_0x1_FV1"
                    --capsule_path2 "utilityCapsule_0x1_FV2"
                    --capsule_path3 "utilityCapsule_0x2_FV2"
                    --update_type efi_utility --flash_type 0x2_FV2
                """                """
                TC : 66687.2
                cmd : python3 SEAM_BMC_0019_send_eufi_capsule_update.py 
                    --capsule_path "utilityCapsule_0x1_FV1"
                    --capsule_path2 "utilityCapsule_0x1_FV2"
                    --capsule_path3 "utilityCapsule_0x2_FV2"
                    --update_type efi_utility --flash_type 0x2_FV2
                    --reboot_while_staging
                """
                if uefi_data[1] == "02":
                    self._log.info("====================== Nth version of UEFI found, downgrading UEFI utility version==============================")
                    if self.send_capsule_without_version_check(self.capsule_path,
                                                               self.CAPSULE_TIMEOUT,
                                                               self.start_workload,
                                                               capsule_path2=self.capsule_path2,
                                                               update_type="ucode"):
                        self._log.info("entering into uefi shell.....")
                        uefi_data_check = self.get_uefi_smbios()
                        if uefi_data_check[1] == "01":
                            self._log.info("Downgradation successful ...")
                            self._log.info("====================== upgrading with Nth version of FV2 ==============================")
                            if self.reboot_while_staging:
                                self.STAGING_REBOOT = True
                            if self.send_capsule_without_version_check(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload):
                                self._log.info("====================== Entering into UEFI shell to read smbios region data ==============================")
                                uefi_data1 = self.get_uefi_smbios()
                                if uefi_data1[0] == "00-00" and uefi_data1[1] == "02":
                                    result = True
                                else:
                                    self._log.error("Region data is not updated...")
                            else:
                                self._log.error("Nth version of FV2 capsule is not flashed properly....")
                        else:
                            self._log.error("Region not downgraded or something went wrong......")
                    else:
                        self._log.error("Downgradation failed ....")
                elif uefi_data[1] == "01":
                    self._log.info("====================== Upgrading with Nth version of FV2 ==============================")
                    if self.reboot_while_staging:
                        self.STAGING_REBOOT = True
                    if self.send_capsule_without_version_check(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload):
                        self._log.info("====================== Entering into UEFI shell to read smbios region data ==============================")
                        uefi_data1 = self.get_uefi_smbios()
                        if uefi_data1[0] == "00-00" and uefi_data1[1] == "02":
                            result = True
                        else:
                            self._log.error("Region data is not updated...")
                    else:
                        self._log.error("Nth version of FV2 capsules are not flashed properly...")
                else:
                    self._log.error("Something went wrong..")
            elif self.flash_type == "downgrade":
                """
                TC : 66683.2
                cmd : python3 SEAM_BMC_0019_send_eufi_capsule_update.py 
                    --capsule_path "utilityCapsule_0x1_FV1" 
                    --capsule_path2 "utilityCapsule_0x1_FV1" 
                    --capsule_path3 "utilityCapsule_0x2_FV1" 
                    --update_type efi_utility --flash_type downgrade
                """
                if uefi_data[1] == "01":
                    self._log.info("====================== (N-1)th version found, Upgrading UEFI utility version ==============================")
                    if self.send_capsule_without_version_check(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload):
                        self._log.info("Entring into UEFI shell to read smbios data....")
                        uefi_data_check = self.get_uefi_smbios()
                        if uefi_data_check[1] == "02":
                            self._log.info("====================== Downgrading UEFI utility version ==============================")
                            if self.send_capsule_without_version_check(self.capsule_path,
                                                                       self.CAPSULE_TIMEOUT,
                                                                       self.start_workload,
                                                                       capsule_path2=self.capsule_path2,
                                                                       update_type="ucode"):
                                self._log.info("====================== Entering into UEFI shell to read smbios region data ==============================")
                                uefi_data1 = self.get_uefi_smbios()
                                if uefi_data1[1] == "01":
                                    result = True
                                else:
                                    self._log.error("Region data is not updated...")
                            else:
                                self._log.error("Downgradation failed ....")
                        else:
                            self._log.error("Region is not upgraded or something went wrong...")
                    else:
                        self._log.error("Upgradation failed ....")
                elif uefi_data[1] == "02":
                    self._log.info("====================== Downgrading UEFI utility version==============================")
                    if self.send_capsule_without_version_check(self.capsule_path,
                                                               self.CAPSULE_TIMEOUT,
                                                               self.start_workload,
                                                               capsule_path2=self.capsule_path2,
                                                               update_type="ucode"):
                        self._log.info("====================== Entering into UEFI shell to read smbios region data ==============================")
                        uefi_data1 = self.get_uefi_smbios()
                        if uefi_data1[1] == "01":
                            result = True
                        else:
                            self._log.error("Region data is not updated...")
                    else:
                        self._log.error("Downgradation failed ....")
                else:
                    self._log.error("Something went wrong....")

            elif self.flash_type == "uefi_0x2_FV1":
                """
                TC : 66682.1
                cmd : python3 SEAM_BMC_0019_send_eufi_capsule_update.py
                    --capsule_path "utilityCapsule_0x1_FV1"
                    --capsule_path2 "utilityCapsule_0x1_FV2"
                    --capsule_path3 "utilityCapsule_0x2_FV1"
                    --update_type efi_utility --flash_type uefi_0x2_FV1
                    --sut_mode uefi
                """
                if uefi_data[1] == "01":
                    uefi_data_check = self.get_uefi_smbios()
                    if uefi_data_check[0] == "00-01" and uefi_data_check[1] == "02":
                        result = True
                    else:
                        self._log.error("failed to update nth version of fv1....")
                elif uefi_data[1] == "02":
                    self._log.info("====================== Nth version found, Downgrading the UEFI utility version==============================")
                    sut_mod = self.sut_mode
                    self.sut_mode = ""
                    if self.send_capsule_without_version_check(self.capsule_path,
                                                               self.CAPSULE_TIMEOUT,
                                                               self.start_workload,
                                                               capsule_path2=self.capsule_path2,
                                                               update_type="ucode"):
                        self._log.info("Entering into UEFI shell to read smbios data .....")
                        self.sut_mode = sut_mod
                        uefi_data_check = self.get_uefi_smbios()
                        if uefi_data_check[1] == "01":
                            uefi_data_check1 = self.get_uefi_smbios()
                            if uefi_data_check1[0] == "00-01" and uefi_data_check1[1] == "02":
                                result = True
                            else:
                                self._log.error("nth version of fv1 not found....")
                        else:
                            self._log.error("nth version not updated or something went wrong....")
                    else:
                        self._log.error("uefi downgradation failed....")
                else:
                    self._log.error("20th region is is not activated or something went wrong.....")
            elif self.flash_type == "parallel":
                """
                TC : 66690
                cmd : python3 SEAM_BMC_0019_send_uefi_capsule_update.py 
                    --capsule_path "utilityCapsule_0x1_FV1"
                    --capsule_path2 "utilityCapsule_0x1_FV2"
                    --capsule_path3 "utilityCapsule_0x2_FV2"
                    --expected_ver "EFI utility" --update_type efi_utility --flash_type parallel --warm_reset
                """
                if uefi_data[1] == "02":
                    self._log.info("====================== Nth version of UEFI found, Downgrading the UEFI utility version ==============================")
                    if self.send_capsule_without_version_check(self.capsule_path,
                                                               self.CAPSULE_TIMEOUT,
                                                               self.start_workload,
                                                               capsule_path2=self.capsule_path2,
                                                               update_type="ucode"):
                        self._log.info("Entering into UEFI shell.....")
                        uefi_data_check = self.get_uefi_smbios()
                        if uefi_data_check[1] == "01":
                            self._log.info("Downgradation successful...!!")
                            self._log.info("====================== Upgrading with Nth version of FV2 ==============================")
                            self.warm_reset = True
                            if self.send_capsule_parallel(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload):
                                self._log.info("====================== Entering into UEFI shell to read smbios region data ==============================")
                                uefi_data1 = self.get_uefi_smbios()
                                if uefi_data1[0] == "00-00" and uefi_data1[1] == "02":
                                    result = True
                                else:
                                    self._log.error("Region data is not updated...")
                            else:
                                self._log.error("Nth version of FV2 not flashed properly....")
                        else:
                            self._log.error("Region is not downgraded or something went wrong......")
                    else:
                        self._log.error("Downgradation failed....!!")
                elif uefi_data[1] == "01":
                    self._log.info("====================== Upgrading with Nth version of FV2 ==============================")
                    self.warm_reset = True
                    if self.send_capsule_parallel(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload):
                        self._log.info("====================== Entering into UEFI shell to read smbios region data ==============================")
                        uefi_data1 = self.get_uefi_smbios()
                        if uefi_data1[0] == "00-00" and uefi_data1[1] == "02":
                            result = True
                        else:
                            self._log.error("Region data is not updated...")
                    else:
                        self._log.error("Nth version of FV2 capsules is flashed properly...")
                else:
                    self._log.error("Something went wrong..")
            elif self.flash_type == "S5_0x2_FV1":
                """
                TC : 66689.2
                cmd : python3 SEAM_BMC_0019_send_uefi_capsule_update.py
                    --capsule_path "utilityCapsule_0x1_FV1"
                    --capsule_path2 "utilityCapsule_0x1_FV2"
                    --capsule_path3 "utilityCapsule_0x2_FV1"
                    --update_type efi_utility --flash_type S5_0x2_FV1
                    --sut_mode S5
                """
                if uefi_data[1] == "01":
                    uefi_data_check = self.get_uefi_smbios()
                    if uefi_data_check[0] == "00-01" and uefi_data_check[1] == "02":
                        result = True
                    else:
                        self._log.error("failed to update nth version of fv1....")
                elif uefi_data[1] == "02":
                    self._log.info("====================== Nth version found, Downgrading the UEFI utility version==============================")
                    sut_mod = self.sut_mode
                    self.sut_mode = ""
                    if self.send_capsule_without_version_check(self.capsule_path,
                                                               self.CAPSULE_TIMEOUT,
                                                               self.start_workload,
                                                               capsule_path2=self.capsule_path2,
                                                               update_type="ucode"):
                        self._log.info("Entering into UEFI shell to read smbios data .....")
                        self.sut_mode = sut_mod
                        uefi_data_check = self.get_uefi_smbios()
                        if uefi_data_check[1] == "01":
                            uefi_data_check1 = self.get_uefi_smbios()
                            if uefi_data_check1[0] == "00-01" and uefi_data_check1[1] == "02":
                                result = True
                            else:
                                self._log.error("nth version of fv1 not found....")
                        else:
                            self._log.error("nth version not flashed or something went wrong....")
                    else:
                        self._log.error("uefi downgradation failed....")
                else:
                    self._log.error("20th region is is not activated or something went wrong.....")
            elif self.capsule_type == "negative":
                """
                TCs : 66678.1, 66679.1, 66680.1
                cmd : python3 SEAM_BMC_0019_send_uefi_capsule_update.py 
                    --capsule_path "utilityCapsule_0x1_FV1"
                    --capsule_path2 "utilityCapsule_0x1_FV2"
                    --capsule_path3 "negative capsule path"
                    --expected_ver "EFI utility" --update_type efi_utility --capsule_type negative
                """
                if uefi_data[1] == "02" or "01":
                    self._log.info("================= Regions are activated. Proceeding with flashing negative capsules =================")
                    # self.warm_reset = True
                    if self.send_capsule_negative(self.capsule_path3, self.CAPSULE_TIMEOUT, capsule_type="negative", update_type="ucode"):
                        self._log.info("Entering into UEFI shell.....")
                        uefi_data_check = self.get_uefi_smbios()
                        if uefi_data_check == uefi_data:
                            self._log.info("Expected version is same as the Initial version as Expected")
                            result = True
                        else:
                            self._log.error("Expected version is not same as the Initial version...Need to check the issue")
                    else:
                        self._log.error("Issue in sending negative capsules....")
                else:
                    self._log.error("There is a issue in activating the region....!!")
            elif self.flash_type == "ucode_uefi":
                """
                TC :- 66681.1
                cmd : python3 SEAM_BMC_0019_send_uefi_capsule_update.py
                    --capsule_path "utilityCapsule_0x1_FV1"
                    --capsule_path2 "utilityCapsule_0x1_FV2"
                    --capsule_path3 "Ucode OOB nth version fv1"
                    --capsule_path4 "Ucode OOB nth version fv2"
                    --update_type efi_utility --flash_type ucode_uefi
                """
                if uefi_data[1] == "01":
                    self._log.info("======Flashing Ucode OOB in both regions===========")
                    if self.send_capsule_without_version_check(self.capsule_path3, self.CAPSULE_TIMEOUT, capsule_path2=self.capsule_path4, update_type="ucode"):
                        self._log.info("======Flashing uefi utility of n-1th version in both regions===========")
                        if self.send_capsule_without_version_check(self.capsule_path,
                                                                   self.CAPSULE_TIMEOUT,
                                                                   capsule_path2=self.capsule_path2,
                                                                   update_type="ucode"):
                            self._log.info("entring into uefi shell....")
                            uefi_data_check = self.get_uefi_smbios()
                            if uefi_data_check[1] == "01":
                                result = True
                            else:
                                self._log.error("Region does not have n-1th version...")
                        else:
                            self._log.error("efi utility N-1th version not flashed properly...")
                    else:
                        self._log.error("Ucode OOB not flashed properly.....")
                elif uefi_data[1] == "02":
                    self._log.info("nth version of uefi found, Downgrading uefi......")
                    if self.send_capsule_without_version_check(self.capsule_path, self.CAPSULE_TIMEOUT, capsule_path2=self.capsule_path2, update_type="ucode"):
                        uefi_check = self.get_uefi_smbios()
                        if uefi_check[1] == "01":
                            self._log.info("======Flashing Ucode OOB in both regions===========")
                            if self.send_capsule_without_version_check(self.capsule_path3,
                                                                       self.CAPSULE_TIMEOUT,
                                                                       capsule_path2=self.capsule_path4,
                                                                       update_type="ucode"):
                                self._log.info("======Flashing uefi utility of n-1th version in both regions===========")
                                if self.send_capsule_without_version_check(self.capsule_path,
                                                                           self.CAPSULE_TIMEOUT,
                                                                           capsule_path2=self.capsule_path2,
                                                                           update_type="ucode"):
                                    self._log.info("entring into uefi shell....")
                                    uefi_data_check = self.get_uefi_smbios()
                                    if uefi_data_check[1] == "01":
                                        result = True
                                    else:
                                        self._log.error("Region does not have n-1th version...")
                                else:
                                    self._log.error("efi utility N-1th version not flashed properly...")
                            else:
                                self._log.error("Ucode OOB not flashed properly.....")
                        else:
                            self._log.error("uefi does not updated to n-1th version")
                    else:
                        self._log.error("uefi downgradation failed....")
                else:
                    self._log.error("20th Region not activated...")

            elif self.flash_type == "stress_staging":
                """
                TC: - 66685.2
                cmd : python3 SEAM_BMC_0019_send_uefi_capsule_update.py
                    --capsule_path "utilityCapsule_0x1_FV1"
                    --capsule_path2 "utilityCapsule_0x1_FV2"
                    --capsule_path3 "utilityCapsule_0x2_FV2"
                    --update_type efi_utility --flash_type stress_staging
                """
                if uefi_data[1] == "01":
                    self._log.info("========= n-1 th version found Upgrading with Nth version of fv2================")
                    if self.send_capsule_without_version_check(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload):
                        uefi_data_check = self.get_uefi_smbios()
                        if uefi_data_check[1] == "02":
                            self._log.info("========= Begin stress staging================")
                            self._log.info("=========Downgrading uefi without warm reset================")
                            if self.send_capsule_without_version_check(self.capsule_path,
                                                                       self.CAPSULE_TIMEOUT,
                                                                       self.start_workload,
                                                                       capsule_path2=self.capsule_path2,
                                                                       update_type="ucode"):
                                self._log.info("=========Upgrading uefi with warm reset================")
                                if self.send_capsule_without_version_check(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload):
                                    uefi_data1 = self.get_uefi_smbios()
                                    if uefi_data1[1] == "02":
                                        result = True
                                    else:
                                        self._log.error("Region data is not updated...")
                                else:
                                    self._log.error("nth version of uefi not flashed....")
                            else:
                                self._log.error("Downgradation failed....")
                        else:
                            self._log.error("20th region data not updated....")
                    else:
                        self._log.error("nth version of uefi not flashed....")
                elif uefi_data[1] == "02":
                    self._log.info("========= Begin stress staging================")
                    self._log.info("=========Downgrading uefi without warm reset================")
                    if self.send_capsule_without_version_check(self.capsule_path,
                                                               self.CAPSULE_TIMEOUT,
                                                               self.start_workload,
                                                               capsule_path2=self.capsule_path2,
                                                               update_type="ucode"):
                        self._log.info("=========Upgrading uefi with warm reset================")
                        if self.send_capsule_without_version_check(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload):
                            uefi_data1 = self.get_uefi_smbios()
                            if uefi_data1[1] == "02":
                                result = True
                            else:
                                self._log.error("Region data is not updated...")
                        else:
                            self._log.error("nth version of uefi not flashed....")
                    else:
                        self._log.error("Downgradation failed....")
            elif self.flash_type == "multi_stress_staging":
                """
                TC :- 66686.2
                cmd :- python3 .\src\seamless\tests\bmc\functional\SEAM_BMC_0019_send_uefi_capsule_update.py 
                    --capsule_path "utilityCapsule_0x1_FV1" 
                    --capsule_path2 "utilityCapsule_0x1_FV2" 
                    --capsule_path3 "SPSUpdateCapsule Operational capsule" 
                    --capsule_path4 "BIOS capsule"
                    --capsule_path5 "utilityCapsule_0x2_FV1"
                    --update_type efi_utility --flash_type multi_stress_staging
                """
                if uefi_data[1] == "01":
                    self._log.info("=============n-1th version of uefi found===============")
                    self._log.info("Begin multi stage stress staging...")
                    self._log.info("flashing sps without warm reset....")
                    if self.send_capsule_without_version_check(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload):
                        self._log.info("flashing BIOS without warm reset....")
                        if self.send_capsule_without_version_check(self.capsule_path4, self.CAPSULE_TIMEOUT, self.start_workload):
                            self._log.info("flashing uefi nth version of fv1 with warm reset....")
                            if self.send_capsule_without_version_check(self.capsule_path5, self.CAPSULE_TIMEOUT, self.start_workload):
                                self._log.info("entring into uefi shell to check uefi updated or not...")
                                uefi_data_check = self.get_uefi_smbios()
                                if uefi_data_check[1] == "02" and uefi_data_check[0] == "00-01":
                                    result = True
                                else:
                                    self._log.error("Region data are not updated with nth version of fv1...")
                            else:
                                self._log.error("nth version of uefi not flashed....")
                        else:
                            self._log.error("Bios not flashed properly...")
                    else:
                        self._log.error("SPS not flashed properly...")
                elif uefi_data[1] == "02":
                    self._log.info("=========nth version of uefi found proceeding with downgradation of uefi================")
                    if self.send_capsule_without_version_check(self.capsule_path,
                                                               self.CAPSULE_TIMEOUT,
                                                               self.start_workload,
                                                               capsule_path2=self.capsule_path2,
                                                               update_type="ucode"):
                        self._log.info("entring into uefi shell to check downgradation occurred or not...")
                        uefi_data_check = self.get_uefi_smbios()
                        if uefi_data_check[1] == "01":
                            self._log.info("Downgradation successful...")
                            self._log.info("Begin multi stage stress staging...")
                            self._log.info("flashing sps without warm reset....")
                            if self.send_capsule_without_version_check(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload):
                                self._log.info("flashing BIOS without warm reset....")
                                if self.send_capsule_without_version_check(self.capsule_path4, self.CAPSULE_TIMEOUT, self.start_workload):
                                    self._log.info("flashing uefi nth version of fv1 with warm reset....")
                                    if self.send_capsule_without_version_check(self.capsule_path5, self.CAPSULE_TIMEOUT, self.start_workload):
                                        self._log.info("entring into uefi shell to check uefi updated or not...")
                                        uefi_data1 = self.get_uefi_smbios()
                                        if uefi_data1[1] == "02" and uefi_data1[0] == "00-01":
                                            result = True
                                        else:
                                            self._log.error("Region data are not updated with nth version of fv1....")
                                    else:
                                        self._log.error("nth version of uefi not flashed....")
                                else:
                                    self._log.error("Bios not flashed properly...")
                            else:
                                self._log.error("SPS not flashed properly...")
                        else:
                            self._log.error("Downgradation unsuccessful 20th region data not updated...")
                    else:
                        self._log.error("something went wrong while downgrading uefi....")
                else:
                    self._log.error("Something went wrong 20th region data not available....")
            elif self.flash_type == "capsule_missmatch":
                """
                TC :- 66676
                cmd :- python3 .\src\seamless\tests\bmc\functional\SEAM_BMC_0019_send_uefi_capsule_update.py
                    --capsule_path "utilityCapsule_0x1_FV1"
                    --capsule_path2 "utilityCapsule_0x1_FV2"
                    --capsule_path3 "utilityCapsule_0x2_FV2"
                    --update_type efi_utility --flash_type capsule_missmatch
                """
                if (uefi_data[1] == "02" and uefi_data[0] == "00-01") or uefi_data[1] == "01":
                    self._log.info("n-1th version or nth version of fv1 found flashing nth version of uefi in fv2 region...")
                    if self.send_capsule_without_version_check(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload):
                        self._log.info("entring into uefi shell to check uefi version...")
                        uefi_data_check = self.get_uefi_smbios()
                        if uefi_data_check[1] == "02" and uefi_data_check[0] == "00-00":
                            self._log.info("nth version of fv2 uefi found....")
                            self._log.info("flashing single capsule n-1th of uefi 0x1 fv1....")
                            if self.send_capsule_without_version_check(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload):
                                self._log.info("entring into uefi shell to check uefi version...")
                                uefi_data1 = self.get_uefi_smbios()
                                if uefi_data1[1] == "02":
                                    result = True
                                else:
                                    self._log.error("uefi does not have nth version...")
                            else:
                                self._log.error("failed to flash n-1th version of uefi....")
                        else:
                            self._log.error("uefi could not updated to nth version...")
                    else:
                        self._log.error("failed to flash nth version of uefi....")
                elif uefi_data[1] == "02" and uefi_data[0] == "00-00":
                    self._log.info("nth version of fv2 uefi found....")
                    self._log.info("flashing single capsule n-1th of uefi 0x1 fv1....")
                    if self.send_capsule_without_version_check(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload):
                        self._log.info("entring into uefi shell to check uefi version...")
                        uefi_data1 = self.get_uefi_smbios()
                        if uefi_data1[1] == "02" and uefi_data1[0] == "00-00":
                            result = True
                        else:
                            self._log.error("uefi does not have nth version...")
                    else:
                        self._log.error("failed to flash n-1th version of uefi....")
                else:
                    self._log.error("Something went wrong 20th region data not available....")
            elif self.flash_type == "uefi_missing":
                """
                TC: 66677.1
                cmd :- python3 SEAM_BMC_0019_send_uefi_capsule_update.py 
                    --capsule_path "utilityCapsule_0x1_FV1"
                    --capsule_path2 "utilityCapsule_0x1_FV2"
                    --capsule_path3 "Ucode oob nth version of fv1"
                    --capsule_path4 "Ucode oob nth version of fv2"
                    --update_type efi_utility --flash_type uefi_missing --expected_ver 0x(ucode expected_ver)
                """
                if uefi_data[1] == "01":
                    self._log.info("Flashing ucode OOB....")
                    if self.send_capsule_without_version_check(self.capsule_path3,
                                                               self.CAPSULE_TIMEOUT,
                                                               self.start_workload,
                                                               capsule_path2=self.capsule_path4,
                                                               update_type="ucode"):
                        self._log.info("entring into uefi shell to check uefi has n-1th version or not......")
                        uefi_data_check = self.get_uefi_smbios()
                        self.update_type = "fit_ucode"
                        exp_ver = self.get_current_version()
                        if uefi_data_check[1] == "01" and self.expected_ver == exp_ver:
                            result = True
                        else:
                            self._log.error("uefi does not have n-1th version or ucode expected version does not match....")
                    else:
                        self._log.error("failed to flash ucode OOB in fv2 region....")
                elif uefi_data[1] == "02":
                    self._log.info("nth version of uefi found, downgrading uefi....")
                    if self.send_capsule_without_version_check(self.capsule_path,
                                                               self.CAPSULE_TIMEOUT,
                                                               self.start_workload,
                                                               capsule_path2=self.capsule_path2,
                                                               update_type="ucode"):
                        self._log.info("entring into uefi shell to check uefi has n-1th version or not......")
                        uefi_check = self.get_uefi_smbios()
                        if uefi_check[1] == "01":
                            self._log.info("Flashing ucode OOB....")
                            if self.send_capsule_without_version_check(self.capsule_path3,
                                                                       self.CAPSULE_TIMEOUT,
                                                                       self.start_workload,
                                                                       capsule_path2=self.capsule_path4,
                                                                       update_type="ucode"):
                                self._log.info("entring into uefi shell to check uefi has n-1th version or not......")
                                uefi_data_check = self.get_uefi_smbios()
                                self.update_type = "fit_ucode"
                                exp_ver = self.get_current_version()
                                if uefi_data_check[1] == "01" and self.expected_ver == exp_ver:
                                    result = True
                                else:
                                    self._log.error("uefi does not have n-1th version or ucode expected version does not match....")
                            else:
                                self._log.error("failed to flash ucode OOB in fv2 region....")
                        else:
                            self._log.error("uefi does not contain n-1th version....")
                    else:
                        self._log.error("uefi downgradation failed.....")
                else:
                    self._log.error("20th region is not activated...")
            elif self.flash_type == "uefi_ucode":
                """
                TC: 66675.1
                cmd :- python3 SEAM_BMC_0019_send_uefi_capsule_update.py 
                    --capsule_path "utilityCapsule_0x1_FV1"
                    --capsule_path2 "utilityCapsule_0x1_FV2"
                    --capsule_path3 "Ucode oob nth version of fv1"
                    --capsule_path4 "Ucode oob nth version of fv2"
                    --capsule_path5 "utilityCapsule_0x2_FV1"
                    --update_type efi_utility --flash_type uefi_ucode --expected_ver 0x(ucode expected_ver)
                """
                if uefi_data[1] == "02":
                    self._log.info("nth version of uefi found downgrading uefi.....")
                    if self.send_capsule_without_version_check(self.capsule_path,
                                                               self.CAPSULE_TIMEOUT,
                                                               self.start_workload,
                                                               capsule_path2=self.capsule_path2,
                                                               update_type="ucode"):
                        self._log.info("entring into uefi to check uefi version....")
                        uefi_data_check = self.get_uefi_smbios()
                        if uefi_data_check[1] == "01":
                            self._log.info("n-1th version of uefi found, flashing ucode oob.....")
                            if self.send_capsule_without_version_check(self.capsule_path3,
                                                                       self.CAPSULE_TIMEOUT,
                                                                       self.start_workload,
                                                                       capsule_path2=self.capsule_path4,
                                                                       update_type="ucode"):
                                self._log.info("entring into uefi to check 20th region contain n-1th version or not....")
                                uefi_data_check1 = self.get_uefi_smbios()
                                update_typ = self.update_type
                                self.update_type = "fit_ucode"
                                exp_ver = self.get_current_version()
                                if uefi_data_check1[1] == "01" and self.expected_ver == exp_ver:
                                    self.update_type = update_typ
                                    self._log.info("n-1th version found, flashing nth version of uefi FV1.....")
                                    if self.send_capsule_without_version_check(self.capsule_path5, self.CAPSULE_TIMEOUT, self.start_workload):
                                        self._log.info("entring into uefi shell to check uefi version......")
                                        uefi_data_check2 = self.get_uefi_smbios()
                                        if uefi_data_check2[1] == "02":
                                            result = True
                                        else:
                                            self._log.error("nth version of uefi not found....")
                                    else:
                                        self._log.error("failed to flash nth version of uefi.....")
                                else:
                                    self._log.error("20th region has data....")
                            else:
                                self._log.error("failed to flash Ucode OOB......")
                        else:
                            self._log.error("n-1th version not found.....")
                    else:
                        self._log.error("failed to downgrade uefi.....")
                elif uefi_data[1] == "01":
                    self._log.info("n-1th version of uefi found, flashing ucode oob.....")
                    if self.send_capsule_without_version_check(self.capsule_path3,
                                                               self.CAPSULE_TIMEOUT,
                                                               self.start_workload,
                                                               capsule_path2=self.capsule_path4,
                                                               update_type="ucode"):
                        self._log.info("entring into uefi to check uefi version....")
                        uefi_data_check1 = self.get_uefi_smbios()
                        update_typ = self.update_type
                        self.update_type = "fit_ucode"
                        exp_ver = self.get_current_version()
                        if uefi_data_check1[1] == "01" and self.expected_ver == exp_ver:
                            self.update_type = update_typ
                            self._log.info("n-1th version found, flashing nth version of uefi FV1..........")
                            if self.send_capsule_without_version_check(self.capsule_path5, self.CAPSULE_TIMEOUT, self.start_workload):
                                self._log.info("entring into uefi shell to check uefi version......")
                                uefi_data_check2 = self.get_uefi_smbios()
                                if uefi_data_check2[1] == "02":
                                    result = True
                                else:
                                    self._log.error("nth version of uefi not found....")
                            else:
                                self._log.error("failed to flash nth version of uefi.....")
                        else:
                            self._log.error("20th region has data....")
                    else:
                        self._log.error("failed to flash Ucode OOB......")
                else:
                    self._log.error("uefi 20th region not activated")
            else:
                self._log.error("Some commands are missing....")
        except Exception as e:
            self._log.error(e)
        finally:
            self._uefi_obj.warm_reset()
            self._log.info("Wait till the system boot into OS...")
            self.os.wait_for_os(self._reboot_timeout)
            return result

    def cleanup(self, return_status):
        super(SEAM_BMC_0019_send_uefi_capsule_update, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0019_send_uefi_capsule_update.main() else Framework.TEST_RESULT_FAIL)
