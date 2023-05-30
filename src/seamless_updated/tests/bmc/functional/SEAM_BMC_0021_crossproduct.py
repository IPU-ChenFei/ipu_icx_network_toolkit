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

"""

import os
import re
import sys
import time
import threading
import subprocess
import statistics
from datetime import datetime, timedelta

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from dtaf_core.lib.exceptions import OsCommandTimeoutException
from dtaf_core.lib.private.cl_utils.adapter.data_types import BIOS_CMD_KEY_ESC, BIOS_CMD_KEY_UP, BIOS_CMD_KEY_ENTER

from src.seamless.lib.seamless_common import SeamlessBaseTest, ThreadWithReturn


class SEAM_BMC_0021_crossproduct(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts, *args):
        super(SEAM_BMC_0021_crossproduct, self).__init__(test_log, arguments, cfg_opts, *args)
        self.sps_update_type = arguments.sps_update_type
        self.capsule_path = arguments.capsule_path
        self.expected_ver = arguments.expected_ver
        self.capsule_path2 = arguments.capsule_path2
        self.expected_ver2 = arguments.expected_ver2
        self.capsule_path3 = arguments.capsule_path3
        self.expected_ver3 = arguments.expected_ver3
        self.capsule_name = arguments.capsule_name
        self.capsule_name2 = arguments.capsule_name2
        self.capsule_name3 = arguments.capsule_name3
        self.loop_count = arguments.loop
        self.warm_reset = arguments.warm_reset
        self.start_workload = arguments.start_workload
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.get_bios_command = self._workload_path + "GetBiosVersion.ps1 " + self._powershell_credentials
        self.ping_sut_command = self._workload_path + "PingSut.ps1 " + self._powershell_credentials
        self.restart_sut_command = self._workload_path + "RestartSut.ps1 " + self._powershell_credentials
        self.smm_code_inject_command = self._workload_path + "SMMCodeInject.ps1 " + self._powershell_credentials
        self.get_smm_info_command = self._workload_path + "SMMInfo.ps1 " + self._powershell_credentials
        self.sut_mode = arguments.sut_mode
        self.capsule_type = arguments.capsule_type
        self.run_orchestrator = arguments.orchestrator
        self.capsule_xml = arguments.capsule_xml
        self.S5_cycle_loop = arguments.S5_cycle_loop
        self.rec_ver = ''
        self.opr_ver = ''
        self.skip_reset = False
        self.activation = False
        self.sps_mode = arguments.sps_mode
        self.crossproduct_pi_manageability = arguments.crossproduct_pi_manageability
        self.bmc_ip = cfg_opts.find('suts/sut/silicon/bmc/ip').text
        self.bmc_username = cfg_opts.find('suts/sut/silicon/bmc/credentials').get('user')
        self.bmc_password = cfg_opts.find('suts/sut/silicon/bmc/credentials').get('password')
        self.crossproduct_whea_uncorrectable_sps = arguments.crossproduct_whea_uncorrectable_sps
        self.crossproduct_whea_correctable_sps = arguments.crossproduct_whea_correctable_sps
        self.crossproduct_whea_uncorrectable_nf_sps = arguments.crossproduct_whea_uncorrectable_nf_sps
        self.crossproduct_whea_uncorrectable_smm = arguments.crossproduct_whea_uncorrectable_smm
        self.crossproduct_security_sps = arguments.crossproduct_security_sps
        self.crossproduct_bios = arguments.crossproduct_bios
        self.crossproduct_cstate_sps = arguments.crossproduct_cstate_sps
        self.smm_capsule = arguments.smm_capsule
        self.smm_command = arguments.smm_command
        self.sut_mode = arguments.sut_mode
        self.update_type = arguments.update_type
        self.crossproduct_fastboot = arguments.crossproduct_fastboot
        self.reboot_loop = arguments.reboot_loop
        self.capsule = "SPS"

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0021_crossproduct, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--capsule_path', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--capsule_name', action='store', help="Name of the capsule to be used for the update", default="")
        parser.add_argument('--capsule_name2', action='store', help="Name of the capsule2 to be used for the update", default="")
        parser.add_argument('--capsule_name3', action='store', help="Name of the capsule3 to be used for the update", default="")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--sut_mode', action='store', help="State if SUT is in EFI mode or DC power off mode", default="")
        parser.add_argument('--update_type', action='store', help="Specify if efi utility, fit ucode, inband", default="fit_ucode")
        parser.add_argument('--orchestrator',
                            action='store_true',
                            help="Validate update through OrchestratorValidator before running. Requires \"--capulse_xml\".")
        parser.add_argument('--capsule_xml', action="store", help="Path to Capsule XML file for the update. Required for" "\"--orchestrator\".", default="")
        parser.add_argument('--capsule_type', action='store', help="Add argument as 'negative' for negative usecases", default="")
        parser.add_argument('--S5_cycle_loop', type=int, default=0, help="Add argument for # of loops of S5 cycle")
        parser.add_argument('--loop', type=int, default=1, help="Add argument for # of loops")
        parser.add_argument('--capsule_path2', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--expected_ver2', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--sps_update_type', action='store', help="Add type of SPS update: operational or three_capsule", default="three_capsule")
        parser.add_argument('--crossproduct_whea_uncorrectable_sps', action='store_true', help="Add argument for crossproduct whea uncorrectable sps TC ")
        parser.add_argument('--crossproduct_whea_correctable_sps', action='store_true', help="Add argument for crossproduct whea correctable sps TC ")
        parser.add_argument('--crossproduct_whea_uncorrectable_nf_sps', action='store_true', help="Add argument for crossproduct whea uncorrectable non-fatal sps TC ")
        parser.add_argument('--crossproduct_whea_uncorrectable_smm', action='store_true', help="Add argument for crossproduct whea uncorrectable smm TC ")
        parser.add_argument('--smm_capsule', action='store', help="The smm capsule for code injection", default="")
        parser.add_argument('--smm_command',
                            action='store',
                            help="The smm command to be executed",
                            choices=["queryCapability", "code_inject", "code_stage", "code_activate"],
                            default="queryCapability")
        parser.add_argument('--reboot_loop', type=int, default=0, help="Add argument for # of loops of reboot")
        parser.add_argument('--crossproduct_fastboot', action='store_true', help="Add argument for crossproduct with powermanagement & fastboot", default="")
        parser.add_argument('--crossproduct_bios', action='store_true', help="Add argument for running crossproduct with bios capsule", default="")
        parser.add_argument('--crossproduct_pi_manageability', action='store_true', help="Add argument for crossproduct_pi_manageability TC", default="")
        parser.add_argument('--crossproduct_security_sps', action='store_true', help="Add argument for crossproduct security with SPS TC", default="")
        parser.add_argument('--crossproduct_cstate_sps', action='store_true', help="Add argument for crossproduct C State with SPS TC", default="")
        parser.add_argument('--capsule_path3', action='store', help="Path to the 3rd capsule to be used for the update", default="")
        parser.add_argument('--expected_ver3', action='store', help="The version expected to be reported after update of capsule3", default="")

    def get_current_version(self, echo_version=True):
        """
        Read sps version
        :param echo_version: True if display output
        :return ME version
        """
        if self.crossproduct_bios:
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

        elif self.crossproduct_whea_correctable_sps or self.crossproduct_whea_uncorrectable_sps or self.crossproduct_security_sps \
            or self.crossproduct_cstate_sps:
            time.sleep(10)
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

            self.rec_ver = version.split('(Recovery)')[0].strip()
            opr_ver = version.split('(Recovery)')[1].split('(Operational)')[0].replace(',', '').strip()

            if me_mode == 'Normal':
                me_mode = 'Operational'

            version = 'Operational: ' + opr_ver + ' Recovery: ' + self.rec_ver + ' Current State: ' + me_mode

            if echo_version:
                self._log.info("\tVersion detected: " + version)
            return version

    def get_expected_version(self, cap_path, exp_ver, echo_version=True):
        current_version = self.get_current_version()
        if re.search(r"RcvOnOpr", cap_path) or re.search(r"me_rcv_on_opr_capsule.bin\b", cap_path):
            opr = exp_ver.split("Operational: ")[1].strip().split(" ")[0]
            rcv = current_version.split("Recovery: ")[1].strip().split(" ")[0]
        elif re.search(r"Recovery", cap_path) or re.search(r"me_rcv_capsule.bin\b", cap_path):
            rcv = exp_ver.split("Recovery: ")[1].strip().split(" ")[0]
            opr = current_version.split("Operational: ")[1].strip().split(" ")[0]
        elif re.search(r"Operational", cap_path) or re.search(r"me_opr_capsule.bin\b", cap_path):
            opr = exp_ver.split("Operational: ")[1].strip().split(" ")[0]
            rcv = current_version.split("Recovery: ")[1].strip().split(" ")[0]
        else:
            raise RuntimeError("Invalid Capsule")
        mode = exp_ver.split("Current State: ")[1].strip()

        expected_ver = "Operational: " + opr + " Recovery: " + rcv + " Current State: " + mode

        return expected_ver

    def check_capsule_pre_conditions(self):
        #To-Do add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        #To-Do add workload output analysis
        return True

    def smm_get_current_version(self, cmd, echo_version=True):
        version = None
        output = self.run_powershell_command(command=self.get_smm_info_command + " " + str(cmd), get_output=True, echo_output=True)
        if 'Execution Succeeded' in output:
            for line in output.splitlines():
                print(line)
                if 'SMMCodeInjectRTVer' in line:
                    version = line.split(':')[1].strip()
        return version

    def smm_code_injection(self):
        """
        Function for executing SMM Code injection
        """
        result = False
        self._log.info("Executing command for code injection with a valid capsule: " + str(self.smm_capsule))
        output = self.run_powershell_command(command=self.smm_code_inject_command + " " + self.smm_capsule, get_output=True, echo_output=True)
        if ('ERROR' in output or 'Execution Succeeded' not in output):
            result = False
            raise RuntimeError("Code injection returned error")
        else:
            self._log.info("Code injection complete")
            for line in output.splitlines():
                if ('Authentication Time' in line):
                    self.authentication_time = line.split(':')[1]
                elif ('Execution Time' in line):
                    self.execution_time = line.split(':')[1]
            post_ver = self.smm_get_current_version('queryCapability')
            self._log.info("Version after code injection is: " + str(post_ver))
            if (str(self.expected_ver) == str(post_ver)):
                self._log.info("Version post code injection is same as expected version")
                result = self.examine_post_update_conditions("SMM")
            else:
                self._log.error("Version post code injection does not match expected version")
                result = False

        return result

    def post_whea_checks(self):

        if not self.os.is_alive():
            time.sleep(60)
            self.ac_power.ac_power_off()
            time.sleep(10)
            self.ac_power.ac_power_on()
            self.os.wait_for_os(self.reboot_timeout)
        self._log.info("Expected Version:{}".format(self.expected_ver))
        if self.get_current_version() == self.expected_ver:
            self._log.info("Update Successful")
            return True
        return False

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

        if self.crossproduct_bios:
            """
            TC 69678 Command:

                python3 .\src\seamless\tests\bmc\functional\SEAM_BMC_0021_crossproduct.py
                --crossproduct_bios
                --capsule_path C:\temp\Seamless\<respective BKC>\BIOS_OOB_Capsules\Prod_Capsules\OOB_ProductionBIOSUpdateCapsule_20P01_20P03\OOB_ProductionBIOSUpdateCapsule_20P01_20P03\WLYDCRB.SYS.WR.64.2021.01.2.02.1719_0020.P03_P801e0_LBG_SPS_ICX_Production_SMLS.cap
                --expected_ver P03 --warm_reset
            """
            command_list = ['python3', 'montana.py', '-f', 'getdeviceid.tdf']
            output = subprocess.check_output(command_list, cwd=r'C:\miv-mivsoftware-master\miv-mivsoftware-master\montana\bin', stderr=subprocess.STDOUT)
            time.sleep(2)
            pattern = re.compile(r'Region Name\s+\|\s+NM Operational Mode')  #Region Name\s+\|\s+NM Operational Mode')
            match_obj = pattern.search(output.decode('utf-8'))
            self._log.info(match_obj)
            if match_obj:
                self._log.info("Region Name is NM Operational Mode")
                self._log.info("Sending Bios Capsule Update...")
                return self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
            else:
                self._log.error("Region Name is not NM Operational Mode")
                return False

        elif self.crossproduct_pi_manageability:
            """
            TC 69682.1 Command:

                python3 .\src\seamless\tests\bmc\functional\SEAM_BMC_0021_crossproduct.py
                --crossproduct_pi_manageability
                --smm_command code_inject
                --expected_ver 0x00000001
                --smm_capsule cpucsr_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap
            """
            set_boot_device_command = [
                r'.\src\seamless\tools\ipmitool\ipmitool.exe', '-I', 'lanplus', '-U', self.bmc_username, '-P', self.bmc_password, '-H', self.bmc_ip, 'chassis',
                'bootdev', 'bios', '-C', '17'
            ]
            sut_power_on_command = [
                r'.\src\seamless\tools\ipmitool\ipmitool.exe', '-I', 'lanplus', '-U', self.bmc_username, '-P', self.bmc_password, '-H', self.bmc_ip, 'chassis',
                'power', 'on', '-C', '17'
            ]
            sut_power_reset_command = [
                r'.\src\seamless\tools\ipmitool\ipmitool.exe', '-I', 'lanplus', '-U', self.bmc_username, '-P', self.bmc_password, '-H', self.bmc_ip, 'chassis',
                'power', 'reset', '-C', '17'
            ]

            self._log.info("Performing a shutdown on the SUT.")
            self.os.shutdown(self.DC_POWER_DELAY)

            self._log.info("Waiting for 2 minutes for SUT to shutdown.")
            time.sleep(120)

            self._log.info("Setting boot device to BIOS using ipmitool.")
            self._log.info(" ".join(set_boot_device_command))
            output_set_boot_device = subprocess.check_output(set_boot_device_command, stderr=subprocess.STDOUT)
            if output_set_boot_device.find(b'Set Boot Device to bios') == -1:
                self._log.error("Failed to set boot device to BIOS.")
                return False
            else:
                self._log.info(output_set_boot_device.decode("utf-8"))

            self._log.info("Waiting for 30 seconds.")
            time.sleep(30)

            self._log.info("Performing SUT power on using ipmitool")
            self._log.info(" ".join(sut_power_on_command))
            output_sut_power_on = subprocess.check_output(sut_power_on_command, stderr=subprocess.STDOUT)
            if output_sut_power_on.find(b'Chassis Power Control: Up/On') == -1:
                self._log.error("Failed to power on the SUT.")
                return False
            else:
                self._log.info(output_sut_power_on.decode("utf-8"))

            self._log.info("Waiting for 30 seconds.")
            time.sleep(30)

            BIOS_TIMEOUT = 300
            self._log.info("Waiting for the SUT to boot to BIOS.")
            returned_value = self.bootmenu.wait_for_entry_menu(BIOS_TIMEOUT)
            self._log.info("wait_for_bios_boot_menu returned {}".format(returned_value))
            if not returned_value:
                self._log.error("Failed to enter BIOS boot menu within the timeout of {} seconds.".format(BIOS_TIMEOUT))
                return False
            else:
                self._log.info("SUT booted to BIOS successfully.")

            self._log.info("Waiting for 30 seconds.")
            time.sleep(30)
            self.bootmenu.press_key("DOWN", True, 15)
            self.bootmenu.press_key("DOWN", True, 15)
            self.bootmenu.press_key("DOWN", True, 15)
            self.bootmenu.press_key("ENTER", True, 15)

            self._log.info("Waiting for SUT to boot to OS.")
            self.os.wait_for_os(self._reboot_timeout)
            if not self.os.is_alive():
                self._log.error("SUT did not power on within the timeout of {} seconds.".format(self._reboot_timeout))
                return False
            else:
                self._log.info("SUT powered on successfully.")

            self._log.info("Waiting for 30 seconds.")
            time.sleep(30)

            self._log.info("Setting boot device to BIOS.")
            self._log.info(" ".join(set_boot_device_command))
            output_set_boot_device = subprocess.check_output(set_boot_device_command, stderr=subprocess.STDOUT)
            if output_set_boot_device.find(b'Set Boot Device to bios') == -1:
                self._log.error("Failed to set boot device to BIOS.")
                return False
            else:
                self._log.info(output_set_boot_device.decode("utf-8"))

            self._log.info("Waiting for 30 seconds.")
            time.sleep(30)

            self._log.info("Performing SUT power reset using ipmitool")
            self._log.info(" ".join(sut_power_reset_command))

            try:
                output_sut_power_reset = subprocess.check_output(sut_power_reset_command, stderr=subprocess.STDOUT)
                if output_sut_power_reset.find(b'Chassis Power Control: Reset') == -1:
                    self._log.error("Failed to restart the SUT.")
                    return False
                else:
                    self._log.info(output_sut_power_reset.decode("utf-8"))
            except subprocess.CalledProcessError as e:
                self._log.info(str(e.output))
                self._log.info(str(e.stdout))
                self._log.info(str(e.stderr))
                if e.returncode != 255:
                    self._log.error("Failed to restart the SUT.")
                    raise
                else:
                    self._log.info("Successfully restarted the SUT.")

            self._log.info("Waiting for 30 seconds.")
            time.sleep(30)

            self._log.info("Waiting for the SUT to boot to BIOS.")
            returned_value = self.bootmenu.wait_for_entry_menu(BIOS_TIMEOUT)
            self._log.info("wait_for_bios_boot_menu returned {}".format(returned_value))
            if not returned_value:
                self._log.error("Failed to enter BIOS boot menu within the timeout of {} seconds.".format(BIOS_TIMEOUT))
                return False
            else:
                self._log.info("SUT booted to BIOS successfully.")

            self._log.info("Waiting for 30 seconds.")
            time.sleep(30)
            self.bootmenu.press_key("DOWN", True, 15)
            self.bootmenu.press_key("DOWN", True, 15)
            self.bootmenu.press_key("DOWN", True, 15)
            self.bootmenu.press_key("ENTER", True, 15)

            self._log.info("Waiting for the SUT to boot to OS.")
            self.os.wait_for_os(self._reboot_timeout)
            if not self.os.is_alive():
                self._log.error("SUT did not power on within the timeout of {} seconds.".format(self._reboot_timeout))
                return False
            else:
                self._log.info("SUT booted to OS successfully.")

            self._log.info("Waiting for 60 seconds.")
            time.sleep(60)
            return self.smm_code_injection()

        elif self.crossproduct_whea_correctable_sps:
            """
            TC 70767 Command:

            python3 .\src\seamless\tests\bmc\functional\SEAM_BMC_0021_crossproduct.py
                --capsule_path C:\temp\Seamless\<respective BKC>\SPS_OOB_Capsules\OOB_SPSUpdateCapsule_03.249_03.263\OOB_SPSUpdateCapsule_03.249_03.263\SPS_E5_04.04.03.249.0_kn4_Operational.cap
                --capsule_path2 C:\temp\Seamless\<respective BKC>\SPS_OOB_Capsules\OOB_SPSUpdateCapsule_03.249_03.263\OOB_SPSUpdateCapsule_03.249_03.263\SPS_E5_04.04.03.263.0_kn4_Operational.cap
                --crossproduct_whea_correctable_sps
                --expected_ver 4.4.3.249
                --expected_ver2 4.4.3.263
                --sps_update_type=three_capsule
                --loop=1
            """

            self.BIOS_CONFIG_FILE = "whea_bios_knobs.cfg"
            if self.BIOS_CONFIG_FILE:
                bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
            self._log.info("=========SETTING BIOS KNOB AS PER CONFIG FILE=========")
            self.bios_util.set_bios_knob(bios_config_file)
            self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)
            self._log.info("=========VERIFYING THE CHANGED BIOS KNOB=========")
            self.bios_util.verify_bios_knob(bios_config_file)

            if (self.sps_update_type == 'three_capsule'):
                if self._product == "EGS":
                    file_ext = self.capsule_path2.split('.')[-1]
                    capsule_name2 = '_'.join(self.capsule_path.split('_')[0:-3])
                    self.capsule_upgrade_1 = capsule_name2 + "_me_rcv_on_opr_capsule." + file_ext
                    self.capsule_upgrade_2 = capsule_name2 + "_me_rcv_capsule." + file_ext
                    self.capsule_upgrade_3 = capsule_name2 + "_me_opr_capsule." + file_ext
                    capsule_name = '_'.join(self.capsule_path2.split('_')[0:-3])
                    self.capsule_downgrade_1 = capsule_name + "_me_rcv_on_opr_capsule." + file_ext
                    self.capsule_downgrade_2 = capsule_name + "_me_rcv_capsule." + file_ext
                    self.capsule_downgrade_3 = capsule_name + "_me_opr_capsule." + file_ext
                else:
                    file_ext = self.capsule_path2.split('.')[-1]
                    capsule_name2 = '_'.join(self.capsule_path.split('_')[0:-1])
                    self.capsule_downgrade_1 = capsule_name2 + "_RcvOnOpr." + file_ext
                    self.capsule_downgrade_2 = capsule_name2 + "_Recovery." + file_ext
                    self.capsule_downgrade_3 = capsule_name2 + "_Operational." + file_ext
                    capsule_name = '_'.join(self.capsule_path2.split('_')[0:-1])
                    self.capsule_upgrade_1 = capsule_name + "_RcvOnOpr." + file_ext
                    self.capsule_upgrade_2 = capsule_name + "_Recovery." + file_ext
                    self.capsule_upgrade_3 = capsule_name + "_Operational." + file_ext

                for x in range(self.loop_count):
                    self.get_current_version()
                    if not (self.capsule_path == ''):
                        expected_ver = self.expected_ver
                        self.expected_ver = "Operational: " + expected_ver + " Recovery: " + self.rec_ver + " Current State: " + 'Recovery'
                        if not self.send_capsule(self.capsule_downgrade_1, self.CAPSULE_TIMEOUT, self.start_workload, "SPS"):
                            return False
                        self.expected_ver = "Operational: " + expected_ver + " Recovery: " + expected_ver + " Current State: " + 'Recovery'
                        if not self.send_capsule(self.capsule_downgrade_2, self.CAPSULE_TIMEOUT, self.start_workload, "SPS"):
                            return False
                        self.expected_ver = "Operational: " + expected_ver + " Recovery: " + expected_ver + " Current State: " + 'Operational'
                        if not self.send_capsule(self.capsule_downgrade_3, self.CAPSULE_TIMEOUT, self.start_workload, "SPS"):
                            return False
                    if not (self.capsule_path2 == ''):  #only do upgrade
                        self.expected_ver = "Operational: " + self.expected_ver2 + " Recovery: " + self.rec_ver + " Current State: " + 'Recovery'
                        if not self.send_capsule(self.capsule_upgrade_1, self.CAPSULE_TIMEOUT, self.start_workload, "SPS"):
                            return False
                        self.expected_ver = "Operational: " + self.expected_ver2 + " Recovery: " + self.expected_ver2 + " Current State: " + 'Recovery'
                        if not self.send_capsule(self.capsule_upgrade_2, self.CAPSULE_TIMEOUT, self.start_workload, "SPS"):
                            return False
                        self.expected_ver = "Operational: " + self.expected_ver2 + " Recovery: " + self.expected_ver2 + " Current State: " + 'Operational'
                        if not self.send_capsule(self.capsule_upgrade_3, self.CAPSULE_TIMEOUT, self.start_workload, "SPS"):
                            return False

                    self._log.info("Automated  test  Loop number :" + str(x + 1))

                    self._log.info("\tChecking post-update conditions")
                    if self.examine_post_update_conditions("SPS"):
                        self._log.info("Reverting the BIOS settings into default..")
                        self.bios_util.load_bios_defaults()
                        return True

        elif self.crossproduct_whea_uncorrectable_sps:
            """
            TC 70768 Command:

            python3 .\\src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0021_crossproduct.py
            --capsule_path C:\\temp\\Seamless\\<respective BKC>\\SPS_OOB_Capsules\\OOB_SPSUpdateCapsule_03.249_03.263\\OOB_SPSUpdateCapsule_03.249_03.263\\SPS_E5_04.04.03.263.0_kn4_Operational.cap
            --crossproduct_whea_uncorrectable_sps
            --expected_ver Operational: 4.4.3.263 Current State: Operational
            --start_workload

            """

            self.BIOS_CONFIG_FILE = "whea_bios_knobs.cfg"
            if self.BIOS_CONFIG_FILE:
                bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
            self._log.info("=========SETTING BIOS KNOB AS PER CONFIG FILE=========")
            self.bios_util.set_bios_knob(bios_config_file)
            self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)
            self._log.info("=========VERIFYING THE CHANGED BIOS KNOB=========")
            self.bios_util.verify_bios_knob(bios_config_file)
            try:

                whea_clearevents_command = self.run_ssh_command(r"cd C:\Users\Administrator\WHEAHCT_Tool && Clear_whea_evts.cmd ")
                self._log.info(whea_clearevents_command)
                whea_installplugin_command = self.run_ssh_command(r"cd C:\Users\Administrator\WHEAHCT_Tool && installPlugin.bat")
                self._log.info(whea_installplugin_command)
                time.sleep(5)

                if (self.sps_update_type != 'three_capsule'):
                    return False
                if self._product == "EGS":
                    file_ext = self.capsule_path.split('.')[-1]
                    capsule_name = '_'.join(self.capsule_path.split('_')[0:-3])
                    self.capsule_upgrade_1 = capsule_name + "_me_rcv_on_opr_capsule." + file_ext
                    self.capsule_upgrade_2 = capsule_name + "_me_rcv_capsule." + file_ext
                    self.capsule_upgrade_3 = capsule_name + "_me_opr_capsule." + file_ext
                else:
                    file_ext = self.capsule_path.split('.')[-1]
                    capsule_name = '_'.join(self.capsule_path.split('_')[0:-1])
                    self.capsule_upgrade_1 = capsule_name + "_RcvOnOpr." + file_ext
                    self.capsule_upgrade_2 = capsule_name + "_Recovery." + file_ext
                    self.capsule_upgrade_3 = capsule_name + "_Operational." + file_ext

                self.get_current_version()
                if (self.capsule_path == ''):  #only do upgrade
                    return False
                expected_ver = self.expected_ver
                self.expected_ver = "Operational: " + expected_ver + " Recovery: " + self.rec_ver + " Current State: " + 'Recovery'
                if not self.send_capsule_without_version_check(self.capsule_upgrade_1, self.CAPSULE_TIMEOUT, self.start_workload):
                    return False
                if not self.post_whea_checks():
                    return False
                self.expected_ver = "Operational: " + expected_ver + " Recovery: " + expected_ver + " Current State: " + 'Recovery'
                if not self.send_capsule_without_version_check(self.capsule_upgrade_2, self.CAPSULE_TIMEOUT, self.start_workload):
                    return False
                if not self.post_whea_checks():
                    return False
                self.expected_ver = "Operational: " + expected_ver + " Recovery: " + expected_ver + " Current State: " + 'Operational'
                if not self.send_capsule_without_version_check(self.capsule_upgrade_3, self.CAPSULE_TIMEOUT, self.start_workload):
                    return False
                if not self.post_whea_checks():
                    return False
                self._log.info("\tChecking post-update conditions")
                return self.examine_post_update_conditions("SPS")
            finally:
                self._log.info("Reverting the BIOS settings into default..")
                self.bios_util.load_bios_defaults()
                
                
        elif self.crossproduct_whea_uncorrectable_nf_sps:
            """
            TC 70768 Command:

            python3 .\\src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0021_crossproduct.py
            --capsule_path C:\\temp\\Seamless\\<respective BKC>\\SPS_OOB_Capsules\\OOB_SPSUpdateCapsule_03.249_03.263\\OOB_SPSUpdateCapsule_03.249_03.263\\SPS_E5_04.04.03.263.0_kn4_Operational.cap
            --crossproduct_whea_uncorrectable_nf_sps
            --expected_ver Operational: 4.4.3.263 Current State: Operational
            --start_workload

            """

            self.BIOS_CONFIG_FILE = "whea_bios_knobs.cfg"
            if self.BIOS_CONFIG_FILE:
                bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
            self._log.info("=========SETTING BIOS KNOB AS PER CONFIG FILE=========")
            self.bios_util.set_bios_knob(bios_config_file)
            self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)
            self._log.info("=========VERIFYING THE CHANGED BIOS KNOB=========")
            self.bios_util.verify_bios_knob(bios_config_file)
            try:

                whea_clearevents_command = self.run_ssh_command(r"cd C:\Users\Administrator\WHEAHCT_Tool && Clear_whea_evts.cmd ")
                self._log.info(whea_clearevents_command)
                whea_installplugin_command = self.run_ssh_command(r"cd C:\Users\Administrator\WHEAHCT_Tool && installPlugin.bat")
                self._log.info(whea_installplugin_command)
                time.sleep(5)

                if (self.sps_update_type != 'three_capsule'):
                    return False
                if self._product == "EGS":
                    file_ext = self.capsule_path.split('.')[-1]
                    capsule_name = '_'.join(self.capsule_path.split('_')[0:-3])
                    self.capsule_upgrade_1 = capsule_name + "_me_rcv_on_opr_capsule." + file_ext
                    self.capsule_upgrade_2 = capsule_name + "_me_rcv_capsule." + file_ext
                    self.capsule_upgrade_3 = capsule_name + "_me_opr_capsule." + file_ext
                else:
                    file_ext = self.capsule_path.split('.')[-1]
                    capsule_name = '_'.join(self.capsule_path.split('_')[0:-1])
                    self.capsule_upgrade_1 = capsule_name + "_RcvOnOpr." + file_ext
                    self.capsule_upgrade_2 = capsule_name + "_Recovery." + file_ext
                    self.capsule_upgrade_3 = capsule_name + "_Operational." + file_ext

                self.get_current_version()
                if (self.capsule_path == ''):  #only do upgrade
                    return False
                expected_ver = self.expected_ver
                self.expected_ver = "Operational: " + expected_ver + " Recovery: " + self.rec_ver + " Current State: " + 'Recovery'
                if not self.send_capsule_without_version_check(self.capsule_upgrade_1, self.CAPSULE_TIMEOUT, self.start_workload):
                    return False
                if not self.post_whea_checks():
                    return False
                self.expected_ver = "Operational: " + expected_ver + " Recovery: " + expected_ver + " Current State: " + 'Recovery'
                if not self.send_capsule_without_version_check(self.capsule_upgrade_2, self.CAPSULE_TIMEOUT, self.start_workload):
                    return False
                if not self.post_whea_checks():
                    return False
                self.expected_ver = "Operational: " + expected_ver + " Recovery: " + expected_ver + " Current State: " + 'Operational'
                if not self.send_capsule_without_version_check(self.capsule_upgrade_3, self.CAPSULE_TIMEOUT, self.start_workload):
                    return False
                if not self.post_whea_checks():
                    return False
                self._log.info("\tChecking post-update conditions")
                return self.examine_post_update_conditions("SPS")
            finally:
                self._log.info("Reverting the BIOS settings into default..")
                self.bios_util.load_bios_defaults()

        elif self.crossproduct_whea_uncorrectable_smm:
            """
            TC 70771 Command:

            python3 .\src\seamless\tests\bmc\functional\SEAM_BMC_0021_crossproduct.py
                --crossproduct_whea_uncorrectable_smm
                --expected_ver 0x00000001 --smm_capsule cpucsr_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap
            """

            self.BIOS_CONFIG_FILE = "whea_bios_knobs.cfg"
            if self.BIOS_CONFIG_FILE:
                bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
            self._log.info("=========SETTING BIOS KNOB AS PER CONFIG FILE=========")
            self.bios_util.set_bios_knob(bios_config_file)
            self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)
            self._log.info("=========VERIFYING THE CHANGED BIOS KNOB=========")
            self.bios_util.verify_bios_knob(bios_config_file)

            self.run_ssh_command(r"cd C:\Users\Administrator\WHEAHCT_Tool && Clear_whea_evts.cmd")
            self.run_ssh_command(r"cd C:\Users\Administrator\WHEAHCT_Tool && installPlugin.bat")
            time.sleep(5)
            smm_thread = ThreadWithReturn(target=self.smm_code_injection)
            smm_thread.start()
            try:
                self._log.info("wheahct /err 32 /param1 2 /param2 0x1000000 /param3 0x40 /param4 0")
                self.run_ssh_command(r"C:\Users\Administrator\WHEAHCT_Tool\wheahct /err 32 /param1 2 /param2 0x1000000 /param3 0x40 /param4 0",
                                     timeout_seconds=20)
            except OsCommandTimeoutException:
                pass
            result = smm_thread.join()
            if not result:
                self._log.error("SMM code injection failed.")
            self._log.info("Reverting the BIOS settings into default..")
            self.bios_util.load_bios_defaults()
            return result

        elif self.crossproduct_security_sps:
            """
            TC 69683.1 Command:

            python3 .\src\seamless\tests\bmc\functional\SEAM_BMC_0021_crossproduct.py
                --crossproduct_security_sps
                --capsule_path C:\temp\Seamless\BKC#14\SPS_Capsules\OOB_SPSUpdateCapsule_03.249_03.263\OOB_SPSUpdateCapsule_03.249_03.263\SPS_E5_04.04.03.249.0_kn4_RcvOnOpr.cap
                --expected_ver "Operational: 4.4.3.249 Current State: Recovery"
                --capsule_path2 C:\temp\Seamless\BKC#14\SPS_Capsules\OOB_SPSUpdateCapsule_03.249_03.263\OOB_SPSUpdateCapsule_03.249_03.263\SPS_E5_04.04.03.249.0_kn4_Recovery.cap
                --expected_ver2 "Recovery: 4.4.3.249 Current State: Recovery"
                --capsule_path3 C:\temp\Seamless\BKC#14\SPS_Capsules\OOB_SPSUpdateCapsule_03.249_03.263\OOB_SPSUpdateCapsule_03.249_03.263\SPS_E5_04.04.03.249.0_kn4_Operational.cap
                --expected_ver3 "Operational: 4.4.3.249 Current State: Operational"
                --sut_mode S5
            """
            # TC 66448
            self._log.info("Initiating first capsule update\n")
            self.get_current_version()
            self.expected_ver = self.get_expected_version(self.capsule_path, self.expected_ver)
            self.os.shutdown()
            self._log.info("System entered into S5 state, waiting for SUT to settle down..")
            time.sleep(self.SUT_SETTLING_TIME)
            self._log.info("=========UPDATING SPS CAPSULE 1 IN S5 STATE==========\n")
            cap1 = self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule)
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
                else:
                    self._log.info("\tCurrent version {} is not the expected version {}".format(current_version, self.expected_ver))
                    return False
            else:
                raise RuntimeError("System not booted into OS after the given time..!!")
            self._log.info("Initiating second capsule update\n")
            self.expected_ver = self.get_expected_version(self.capsule_path2, self.expected_ver2)
            self.os.shutdown()
            self._log.info("System entered into S5 state, waiting for SUT to settle down..")
            time.sleep(self.SUT_SETTLING_TIME)
            self._log.info("=========UPDATING SPS CAPSULE 2 IN S5 STATE==========\n")
            cap2 = self.send_capsule(self.capsule_path2, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule)
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
                current_version2 = self.get_current_version()
                if current_version2 == self.expected_ver:
                    self._log.info("\tThe current version {} is the expected version {}".format(current_version2, self.expected_ver))
                else:
                    self._log.info("\tCurrent version {} is not the expected version {}".format(current_version2, self.expected_ver))
                    return False
            else:
                raise RuntimeError("System not booted into OS after the given time..!!")
            self._log.info("Initiating third capsule update\n")
            self.expected_ver = self.get_expected_version(self.capsule_path3, self.expected_ver3)
            self.os.shutdown()
            self._log.info("System entered into S5 state, waiting for SUT to settle down..")
            time.sleep(self.SUT_SETTLING_TIME)
            self._log.info("=========UPDATING SPS CAPSULE 3 IN S5 STATE==========\n")
            cap3 = self.send_capsule(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule)
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
                current_version3 = self.get_current_version()
                if current_version3 == self.expected_ver:
                    self._log.info("\tThe current version {} is the expected version {}".format(current_version3, self.expected_ver))
                else:
                    self._log.info("\tCurrent version {} is not the expected version {}".format(current_version3, self.expected_ver))
                    return False
            else:
                raise RuntimeError("System not booted into OS after the given time..!!")
            if cap1 and cap2 and cap3:
                pass
            else:
                self._log.info("Inputs or updates are not proper..!!")
                return False

            # TC 68057
            self._log.info("Rebooting to BIOS...")
            bios_path = "EDKII Menu,Socket Configuration,Processor Configuration"
            ret = self.bios_navigation_to_page(bios_path)
            if not ret:
                self._log.error("Navigation to {0} failed.".format(bios_path))
                return False
            time.sleep(15)

            if not self.select_and_enter_bios_item("Total Memory Encryption (TME)"):
                return False
            if not self.select_and_enter_bios_item("Enable"):
                return False
            if not self.select_and_enter_bios_item("Limit CPU PA to 46 bits"):
                return False
            time.sleep(2)
            self.setupmenu.press_key(BIOS_CMD_KEY_UP, True, 15)
            time.sleep(2)
            self.setupmenu.press_key(BIOS_CMD_KEY_ENTER, True, 15)
            time.sleep(2)
            if not self.select_and_enter_bios_item("Total Memory Encryption Multi-Tenant(TME-MT)"):
                return False
            if not self.select_and_enter_bios_item("Enable"):
                return False

            self.setupmenu.press(r'F10')
            time.sleep(5)
            self.setupmenu.press_key(r'Y', True, 10)
            time.sleep(5)
            self.setupmenu.press_key(BIOS_CMD_KEY_ESC, True, 15)
            time.sleep(30)
            self.setupmenu.press_key(BIOS_CMD_KEY_ESC, True, 15)
            time.sleep(30)
            self.setupmenu.press_key(BIOS_CMD_KEY_ESC, True, 15)
            time.sleep(30)

            # Do a system reset from BIOS
            self.setupmenu.press_key(BIOS_CMD_KEY_UP, True, 15)
            time.sleep(2)
            self.setupmenu.press_key(BIOS_CMD_KEY_ENTER, True, 15)
            time.sleep(2)

            self._log.info("Waiting for the SUT to boot to OS.")
            self.os.wait_for_os(self._reboot_timeout)
            if not self.os.is_alive():
                self._log.error("SUT did not power on within the timeout of {} seconds.".format(self._reboot_timeout))
                return False
            else:
                self._log.info("SUT booted to OS successfully.")

            self._log.info("Rebooting to BIOS...")
            ret = self.bios_navigation_to_page(bios_path)
            if not ret:
                self._log.error("Navigation to {0} failed.".format(bios_path))
                return False
            time.sleep(15)

            name = "Max TME-MT Keys"
            if self.setupmenu.select(name, None, True, 60) != "SUCCESS":
                self._log.error("Selecting {0} failed".format(name))
                return False
            ret1 = self.setupmenu.get_selected_item()
            if "0x3F" not in ret1.result_value:
                self._log.error("Couldn't find 0x3F in Max TME-MT Keys.")
                return False
            self._log.info("Found 0x3F in Max TME-MT Keys.")

            self.setupmenu.press_key(BIOS_CMD_KEY_ESC, True, 15)
            time.sleep(30)
            self.setupmenu.press_key(BIOS_CMD_KEY_ESC, True, 15)
            time.sleep(30)
            self.setupmenu.press_key(BIOS_CMD_KEY_ESC, True, 15)
            time.sleep(30)

            # Do a system reset from BIOS
            self.setupmenu.press_key(BIOS_CMD_KEY_UP, True, 15)
            time.sleep(2)
            self.setupmenu.press_key(BIOS_CMD_KEY_ENTER, True, 15)
            time.sleep(2)

            self._log.info("Waiting for the SUT to boot to OS.")
            self.os.wait_for_os(self._reboot_timeout)
            if not self.os.is_alive():
                self._log.error("SUT did not power on within the timeout of {} seconds.".format(self._reboot_timeout))
                return False
            else:
                self._log.info("SUT booted to OS successfully.")
            self._log.info("Reverting the BIOS settings into default..")
            self.bios_util.load_bios_defaults()
            return True

        elif self.crossproduct_cstate_sps:
            """
            TC 70769 Command:

            python3 .\\src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0021_crossproduct.py
                --capsule_path C:\\temp\\Seamless\\<respective BKC>\\SPS_OOB_Capsules\\OOB_SPSUpdateCapsule_03.249_03.263\\OOB_SPSUpdateCapsule_03.249_03.263\\SPS_E5_04.04.03.263.0_kn4_Operational.cap
                --crossproduct_cstate_sps
                --expected_ver 4.4.3.263 
                --start_workload

            """

            if (self.sps_update_type != 'three_capsule'):
                return False
            file_ext = self.capsule_path.split('.')[-1]
            capsule_name = '_'.join(self.capsule_path.split('_')[0:-1])
            self.capsule_upgrade_1 = capsule_name + "_RcvOnOpr." + file_ext
            self.capsule_upgrade_2 = capsule_name + "_Recovery." + file_ext
            self.capsule_upgrade_3 = capsule_name + "_Operational." + file_ext

            self.get_current_version()
            if (self.capsule_path == ''):  # only do upgrade
                return False
            expected_ver = self.expected_ver
            self.expected_ver = "Operational: " + expected_ver + " Recovery: " + self.rec_ver + " Current State: " + 'Recovery'
            if not self.send_capsule(self.capsule_upgrade_1, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule):
                return False
            self.expected_ver = "Operational: " + expected_ver + " Recovery: " + expected_ver + " Current State: " + 'Recovery'
            if not self.send_capsule(self.capsule_upgrade_2, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule):
                return False
            self.expected_ver = "Operational: " + expected_ver + " Recovery: " + expected_ver + " Current State: " + 'Operational'
            if not self.send_capsule(self.capsule_upgrade_3, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule):
                return False
            self._log.info("\tChecking post-update conditions")
            return self.examine_post_update_conditions("SPS")

        elif self.crossproduct_fastboot:
            """
            python3 .\src\seamless\tests\bmc\functional\SEAM_BMC_0021_crossproduct.py
            --crossproduct_fastboot
            --reboot_loop 1
            """
            self.BIOS_CONFIG_FILE = "c_states_enable.cfg"
            if self.BIOS_CONFIG_FILE:
                bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
            self._log.info("=========SETTING BIOS KNOB AS PER CONFIG FILE=========")
            self.bios_util.set_bios_knob(bios_config_file)
            self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)
            self._log.info("=========VERIFYING THE CHANGED BIOS KNOB=========")
            self.bios_util.verify_bios_knob(bios_config_file)
            c6_list = []
            cpu_percentage_check = self.run_ssh_command(r"top -n 20 -b")
            print(cpu_percentage_check.stdout.splitlines()[2])
            print(cpu_percentage_check.stderr)
            cpu_percentage = re.search("[0-9].[0-9]",cpu_percentage_check.stdout.splitlines()[2])
            print(cpu_percentage.group(0))
            if not float(cpu_percentage.group(0))< 2.0:
                print("Cpu % value is incorrect as per TC")
            print("Cpu % value is correct as per TC")
            cpu_power_monitor_response = self.run_ssh_command(r"cpupower monitor")
            print(cpu_power_monitor_response.stdout.splitlines(True))
            cpu_power_monitor_response_len = len(cpu_power_monitor_response.stdout.splitlines(True))
            for i in range(5,cpu_power_monitor_response_len):
                pipe_split = cpu_power_monitor_response.stdout.splitlines(True)[i].split("|")
                if float(pipe_split[4]):
                    print(float(pipe_split[4]))
                    c6_list.append(float(pipe_split[4]))
            print(c6_list)
            print(len(c6_list))
            c6_average = statistics.mean(c6_list) 
            print("C6 Average: {}".format(c6_average))
            if c6_average > 90:
                print("C6 state is suitably high")
            else:
                print("C6 state is not suitably high")
                return False
            time.sleep(5)
            turbostat_response = self.run_ssh_command(r"turbostat --num_iterations 1")
            print(turbostat_response.stdout.splitlines(True))
            turbostat_response_len = len(turbostat_response.stdout.splitlines(True))
            count = 0
            for i in range(1,turbostat_response_len):
                tab_split= turbostat_response.stdout.splitlines(True)[i].split("\t")
                print(tab_split)
                print(len(turbostat_response.stdout.splitlines(True)[1:]))
                if float(tab_split[4]) < 1.0:
                    count += 1
                    print(count)
                else:
                    print("Busy percentage is having undesired value")
            if count >= len(turbostat_response.stdout.splitlines(True)[1:])-5:
                self._log.info(r"Busy % column have desired value")
            else:
                self._log.info(r"Busy % column have undesired value")
                return False
            stress_utility_thread = ThreadWithReturn(target = self.run_ssh_command, args=("cd stressapptest-master/src && .//stressapptest -c 144 -s 120",))
            stress_utility_thread.start()
            time.sleep(30)
            c6_list_stress = []
            cpu_power_monitor_during_stress = self.run_ssh_command(r"cpupower monitor")
            print(cpu_power_monitor_during_stress.stdout.splitlines(True))
            cpu_power_monitor_during_stress_len = len(cpu_power_monitor_during_stress.stdout.splitlines(True))
            print(cpu_power_monitor_during_stress_len)
            for i in range(5,cpu_power_monitor_during_stress_len):
                pipe_split_stress = cpu_power_monitor_during_stress.stdout.splitlines()[i].split("|")
                print(pipe_split_stress)
                if float(pipe_split_stress[4])<1.0:
                    print(float(pipe_split_stress[4]))
                    c6_list_stress.append(float(pipe_split_stress[4]))
            print(c6_list_stress)
            print(len(c6_list_stress))
            c6_stress_average = statistics.mean(c6_list_stress) 
            print("C6 Average: {}".format(c6_stress_average))
            if c6_stress_average < 1:
                print("C6 state is suitably low")
            else:
                print("C6 state is not suitably low")
                return False
            utility_thread_response = stress_utility_thread.join()
            print(utility_thread_response.stdout)
            time.sleep(15)

            self.BIOS_CONFIG_FILE = "c_states_disable.cfg"
            if self.BIOS_CONFIG_FILE:
                bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
            self._log.info("=========SETTING BIOS KNOB AS PER CONFIG FILE=========")
            self.bios_util.set_bios_knob(bios_config_file)
            self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)
            self._log.info("=========VERIFYING THE CHANGED BIOS KNOB=========")
            self.bios_util.verify_bios_knob(bios_config_file)

            cpu_percentage_check = self.run_ssh_command(r"top -n 2 -b")
            print(cpu_percentage_check.stdout.splitlines()[2])
            print(cpu_percentage_check.stderr)
            cpu_percentage = re.search("[0-9].[0-9]",cpu_percentage_check.stdout.splitlines()[2])
            print(cpu_percentage.group(0))
            if not float(cpu_percentage.group(0))< 2.0:
                print("Cpu % value is incorrect as per TC")
                return False
            print("Cpu % value is correct as per TC")
            turbostat_response = self.run_ssh_command(r"turbostat --num_iterations 1")
            print(turbostat_response.stdout.splitlines(True))
            turbostat_response_len = len(turbostat_response.stdout.splitlines(True))
            count = 0
            for i in range(1,turbostat_response_len):
                tab_split= turbostat_response.stdout.splitlines(True)[i].split("\t")
                print(tab_split)
                print(len(turbostat_response.stdout.splitlines(True)[1:]))
                if int(tab_split[5]) > 2800:
                    count += 1
                    print(count)
                else:
                    print("Bzy_Mhz percentage is having undesired value")
            if count >= len(turbostat_response.stdout.splitlines(True)[1:])-5:
                self._log.info(r"Bzy_Mhz column before stress have desired value")
            else:
                self._log.info(r"Bzy_Mhz column before stress have undesired value")
                return False
            stress_utility_thread = ThreadWithReturn(target = self.run_ssh_command, args=("cd stressapptest-master/src && .//stressapptest -c 144 -s 180",))
            stress_utility_thread.start()
            time.sleep(60)
            turbostat_response = self.run_ssh_command(r"turbostat --num_iterations 1")
            print(turbostat_response.stdout.splitlines(True))
            turbostat_response_len = len(turbostat_response.stdout.splitlines(True))
            count = 0
            for i in range(1,turbostat_response_len):
                tab_split= turbostat_response.stdout.splitlines(True)[i].split("\t")
                print(tab_split)
                print(len(turbostat_response.stdout.splitlines(True)[1:]))
                if int(tab_split[5]) > 2800:
                    count += 1
                    print(count)
                else:
                    print("Bzy_Mhz percentage is having undesired value")
            if count >= len(turbostat_response.stdout.splitlines(True)[1:])-5:
                self._log.info(r"Bzy_Mhz column after stress have desired value")
            else:
                self._log.info(r"Bzy_Mhz column after stress have undesired value")
                return False

        self._log.info("Rebooting the SUT once before enabling 'Fast Boot'..")
        self.os.reboot(timeout=self.WARM_RESET_TIMEOUT)
        self._log.info("System booted into OS..!!\n")
        if self._os_type == OperatingSystems.LINUX or self._os_type == OperatingSystems.WINDOWS:
            self._log.info("======== ENABLING FAST BOOT IN BIOS ========\n")
            if self.change_bios_setup_option():
                self._log.info("Successfully updated the BIOS settings")
            else:
                self._log.info("System failed to enter BIOS Menu, 'Fast Boot' is already 'Enabled'..")
            time.sleep(self.DC_POWER_DELAY)
            if self._product == "EGS":
                self._dc_power.dc_power_on()
            elif self._product == "WHT":
                self._dc_power.dc_power_reset()
            self._log.info("Waiting for system to boot into OS..")
            self.os.wait_for_os(self.reboot_timeout)
            time.sleep(self.POST_SLEEP_DELAY)
            if self.sut_ssh.is_alive():
                self._log.info("System booted into OS..!!\n")
                if self.reboot_loop:
                    for x in range(self.reboot_loop):
                        self._log.info("Performing Reboot cycle, iteration: {}".format(x + 1))
                        self.os.reboot(timeout=self.WARM_RESET_TIMEOUT)
                        self._log.info("System booted into OS..!!\n")
                    self._log.info("==========PERFORMED {} ITERATION(S) OF REBOOT CYCLE===========\n".format(x + 1))
                    return True
                else:
                    self._log.info("Reboot loop argument and count not given, Exiting the process..!!")
                    return False
            else:
                self._log.info("System failed to boot into OS..!!\n")
                return False                

    def change_bios_setup_option(self):
        self._log.info("Changing the BIOS setup option and saving the settings...")
        bios_path = "EDKII Menu,Boot Options,Fast Boot Mode"
        ret = self.bios_navigation_to_page(bios_path)
        if ret:
            self.setupmenu.enter_selected_item(ignore=False, timeout=10)
            self.setupmenu.change_order([str("Enable")])
            ret = self.setupmenu.get_page_information()
            self._log.info("'Fast Boot' BIOS option {0}  ".format("Enabled"))
            self.setupmenu.press(r'F10')
            time.sleep(5)
            self.setupmenu.press_key(r'Y', True, 10)
            time.sleep(5)
            self.setupmenu.back_to_root(0.1, r'ESC')
            return True
        else:
            return False

    def select_and_enter_bios_item(self, name):
        if self.setupmenu.select(name, None, False, 60) != "SUCCESS":
            self._log.error("Selecting {0} failed".format(name))
            return False
        self._log.info("Selected {0}".format(name))
        self._log.info(self.setupmenu.get_selected_item().return_code)
        if self.setupmenu.enter_selected_item(ignore=False, timeout=10) != "SUCCESS":
            self._log.error("Entering selected item {0} failed".format(name))
            return False
        self._log.info("Entered selected item {0}".format(name))
        time.sleep(5)
        return True

    def cleanup(self, return_status):
        super(SEAM_BMC_0021_crossproduct, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0021_crossproduct.main() else Framework.TEST_RESULT_FAIL)
