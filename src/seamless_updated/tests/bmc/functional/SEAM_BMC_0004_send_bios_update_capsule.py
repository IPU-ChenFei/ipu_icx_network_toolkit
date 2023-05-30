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
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest


class SEAM_BMC_0004_send_bios_update_capsule(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0004_send_bios_update_capsule, self).__init__(test_log, arguments, cfg_opts)
        self.capsule_path = arguments.capsule_path
        self.capsule_path2 = arguments.capsule_path2
        self.capsule_path3 = arguments.capsule_path3
        self.capsule_path4 = arguments.capsule_path4
        self.expected_ver = arguments.expected_ver
        self.expected_ver2 = arguments.expected_ver2
        self.capsule_name = arguments.capsule_name
        self.capsule_name2 = arguments.capsule_name2
        self.capsule_name3 = arguments.capsule_name3
        self.capsule_name4 = arguments.capsule_name4
        self.warm_reset = arguments.warm_reset
        self.start_workload = arguments.start_workload
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.get_bios_command = self._workload_path + "GetBiosVersion.ps1 " + self._powershell_credentials
        self.ping_sut_command = self._workload_path + "PingSut.ps1 " + self._powershell_credentials
        self.restart_sut_command = self._workload_path + "RestartSut.ps1 " + self._powershell_credentials
        self.sut_mode = arguments.sut_mode
        self.capsule_type = arguments.capsule_type
        self.run_orchestrator = arguments.orchestrator
        self.capsule_xml = arguments.capsule_xml
        self.parallel_staging = arguments.parallel_staging
        self.warm_reset_loop = arguments.warm_reset_loop
        self.stress_staging = arguments.stress_staging
        self.stress_multi_staging = arguments.stress_multi_staging
        self.cold_reset_loop = arguments.cold_reset_loop
        self.ac_power_cycle = arguments.ac_power_cycle
        self.uefi_variable_space = arguments.uefi_variable_space
        self.bmc_bios_comm = arguments.bmc_bios_comm
        self.spi_access = arguments.spi_access
        self.skip_reset = False
        self.update_type = arguments.update_type
        self.activation = arguments.activation
        self.sps_mode = arguments.sps_mode
        self.ac_while_staging = arguments.ac_while_staging
        self.reboot_while_staging = arguments.reboot_while_staging


    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0004_send_bios_update_capsule, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--capsule_path', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--capsule_path2', action='store', help="Path to the 2nd capsule to be used for the update", default="")
        parser.add_argument('--capsule_path3', action='store', help="Path to the 3rd capsule to be used for the update", default="")
        parser.add_argument('--capsule_path4', action='store', help="Path to the 4th capsule to be used for the update", default="")
        parser.add_argument('--capsule_name', action='store', help="Name of the capsule to be used for the update", default="")
        parser.add_argument('--capsule_name2', action='store', help="Name of the capsule2 to be used for the update", default="")
        parser.add_argument('--capsule_name3', action='store', help="Name of the capsule3 to be used for the update", default="")
        parser.add_argument('--capsule_name4', action='store', help="Name of the capsule4 to be used for the update", default="")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--expected_ver2', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--sut_mode', action='store', help="State if SUT is in EFI mode or DC power off mode", default="")
        parser.add_argument('--orchestrator',
                            action='store_true',
                            help="Validate update through OrchestratorValidator"
                            "before running. Requires \"--capulse_xml\".")
        parser.add_argument('--capsule_xml', action="store", help="Path to Capsule XML file for the update. Required for" "\"--orchestrator\".", default="")
        parser.add_argument('--capsule_type', action='store', help="Add argument as 'negative' for negative usecases", default="")
        parser.add_argument('--parallel_staging', action='store_true', help="Add this argument if need to stage capsules parallelly", default="")
        parser.add_argument('--warm_reset_loop', type=int, default=0, help="Add argument for # of loops of warm reset")
        parser.add_argument('--stress_staging', action='store_true', help="Add this argument if need to update bios capsules by stress", default="")
        parser.add_argument('--stress_multi_staging',
                            action='store_true',
                            help="Add this argument if need to update multiple domain capsules by stress",
                            default="")
        parser.add_argument('--cold_reset_loop', type=int, default=0, help="Add argument for # of loops of cold reset")
        parser.add_argument('--ac_power_cycle', type=int, default=0, help="Add argument for # of loops of Ac power cycles")
        parser.add_argument('--update_type', action='store', help="Specify if efi utility, fit ucode, inband", default="fit_ucode")
        parser.add_argument('--activation', action='store_true', help="Add argument if only activation to be performed")
        parser.add_argument('--uefi_variable_space', action='store_true', help="Add argument for uefi variable space check", default="")
        parser.add_argument('--bmc_bios_comm', action='store_true', help="Add argument for testing the bios bmc communication after activation", default="")
        parser.add_argument('--spi_access', action='store_true', help="pass argument to perform verification after update sps", default="")
        parser.add_argument('--ac_while_staging', action='store_true',
                            help="Add this argument if need to stage capsules parallelly", default="")
        parser.add_argument('--reboot_while_staging', action='store_true',
                            help="Add this argument if need to reset SUT while staging", default="")

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
        if self.capsule_name2 != "":
            self.capsule_path2 = self.find_cap_path(self.capsule_name2)
            self._log.info("capsule path2 {}".format(self.capsule_path2))
        if self.capsule_name3 != "":
            self.capsule_path3 = self.find_cap_path(self.capsule_name3)
            self._log.info("capsule path3 {}".format(self.capsule_path3))
        if self.capsule_name4 != "":
            self.capsule_path4 = self.find_cap_path(self.capsule_name4)
            self._log.info("capsule path4 {}".format(self.capsule_path4))

        if self.capsule_type == 'negative':
            """
            TC :- 66090.2, 66169
            python SEAM_BMC_0004_send_bios_update_capsule.py 
            --capsule_path <Corrupted capsule> 
            --capsule_type negative'
            """
            self._log.info("Sending Bios Negative Capsule Update...")
            return self.send_capsule_negative(
                self.capsule_path,
                self.CAPSULE_TIMEOUT,
                self.start_workload,
                capsule_type="negative",
            )
        elif self.parallel_staging:
            """
            TC :- 66091.3
            cmd :- python3 SEAM_BMC_0004_send_bios_update_capsule.py 
            --capsule_path <path for 1st bios capsule>
            --capsule_path2 <path for 2nd bios capsule> --> (which need to be rejected)
            --expected_ver <bios cap1 version> 
            --parallel_staging
            --warm_reset
            """
            return self.send_capsule_parallel(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
        elif self.stress_staging:
            """
            TC :- 66101.1
            cmd :- python3 SEAM_BMC_0004_send_bios_update_capsule.py 
            --capsule_path <path for 1st bios capsule>
            --capsule_path2 <path for 2nd bios capsule>
            --expected_ver <bios cap1 version> 
            --stress_staging
            --warm_reset
            """
            if self.capsule_path and self.capsule_path2:
                self.warm_reset = False
                self._log.info("===========UPDATING FIRST VERSION OF BIOS CAPSULE===========\n")
                bios_update1 = self.send_capsule_without_version_check(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
                self._log.info("===========UPDATING SECOND VERSION OF BIOS CAPSULE===========\n")
                bios_update2 = self.send_capsule_without_version_check(self.capsule_path2, self.CAPSULE_TIMEOUT, self.start_workload)
                self._log.info("===========UPDATING THIRD VERSION OF BIOS CAPSULE===========\n")
                self.warm_reset = True
                bios_update3 = self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
            if bios_update1 and bios_update2 and bios_update3:
                self._log.info("====SUCCESSFULLY STAGED BIOS CAPSULES====")
                return True
            else:
                self._log.info("Inputs are not proper, exiting the process..!!")
                return False
        elif self.stress_multi_staging:
            """
            TC :- 66114.1
            cmd :- python3 SEAM_BMC_0004_send_bios_update_capsule.py 
            --capsule_path <path for SPS Opr capsule>
            --capsule_path2 <path for Ucode FV1 capsule>
            --capsule_path3 <path for Ucode FV2 capsule>
            --capsule_path4 <path for bios capsule>
            --expected_ver <bios cap version> 
            --stress_multi_staging
            --warm_reset
            """
            if self.capsule_path and self.capsule_path2 and self.capsule_path3 and self.capsule_path4:
                self.warm_reset = False
                self._log.info("===========UPDATING SPS CAPSULE===========\n")
                sps_update = self.send_capsule_without_version_check(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
                self._log.info("===========UPDATING UCODE CAPSULE 1===========\n")
                ucode_update1 = self.send_capsule_without_version_check(self.capsule_path2, self.CAPSULE_TIMEOUT, self.start_workload)
                self._log.info("===========UPDATING UCODE CAPSULE 2===========\n")
                ucode_update2 = self.send_capsule_without_version_check(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload)
                self._log.info("===========UPDATING BIOS CAPSULE===========\n")
                self.warm_reset = True
                bios_update = self.send_capsule(self.capsule_path4, self.CAPSULE_TIMEOUT, self.start_workload)
            if sps_update and ucode_update1 and ucode_update2 and bios_update:
                self._log.info("====SUCCESSFULLY UPDATED SPS, UCODE and BIOS CAPSULES====")
                return True
            else:
                self._log.info("Inputs are not proper, exiting the process..!!")
                return False
        elif self.warm_reset_loop:
            """
            TC :- 66056.2
            cmd :- python3 SEAM_BMC_0004_send_bios_update_capsule.py 
            --capsule_path <path for bios capsule>
            --expected_ver <bios cap version> 
            --warm_reset_loop <loop_count>
            """
            update_cap = self.send_capsule_without_version_check(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
            if self.warm_reset_loop and update_cap:
                for x in range(self.warm_reset_loop):
                    self._log.info("Performing Warm Reset cycle, iteration: {}".format(x + 1))
                    self.os.reboot(timeout=self.WARM_RESET_TIMEOUT)
                self._log.info("==========PERFORMED {} ITERATION(S) OF WARM RESET===========".format(x + 1))
                current_version = self.get_current_version()
                if current_version == self.expected_ver:
                    self._log.info("\tThe current version {} is the expected version {}".format(current_version, self.expected_ver))
                    return update_cap
                elif self.expected_ver in current_version:
                    self._log.info("\tThe expected version {} is in the current version {}".format(self.expected_ver, current_version))
                    return update_cap
                else:
                    self._log.info("\tCurrent version {} is not the expected version {}".format(current_version, self.expected_ver))
                    return False
        elif self.cold_reset_loop:
            """
            TC :- 66055.2
            cmd :- python3 SEAM_BMC_0004_send_bios_update_capsule.py 
            --capsule_path <path for bios capsule>
            --expected_ver <bios cap version> 
            --cold_reset_loop <loop_count>
            """
            update_cap = self.send_capsule_without_version_check(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
            if self.cold_reset_loop and update_cap:
                for x in range(self.cold_reset_loop):
                    self._log.info("Performing Cold Reset cycle, iteration: {}\n".format(x + 1))
                    self._extracted_from_execute_101()
                    self._extracted_from_execute_105("Waking up the system from S5 state..")
                    if self.sut_ssh.is_alive():
                        self._log.info("System booted into OS..!!\n")
                    else:
                        raise RuntimeError("System not booted into OS after the given time..!!")
            self._log.info("==========PERFORMED {} ITERATION(S) OF COLD RESET===========\n".format(x + 1))
            current_version = self.get_current_version()
            if current_version == self.expected_ver:
                self._log.info("\tThe current version {} is the expected version {}".format(current_version, self.expected_ver))
                return update_cap
            elif self.expected_ver in current_version:
                self._log.info("\tThe expected version {} is in the current version {}".format(self.expected_ver, current_version))
                return update_cap
            else:
                self._log.info("\tCurrent version {} is not the expected version {}".format(current_version, self.expected_ver))
                return False
        elif self.ac_power_cycle:
            """
            TC :- 66057.1
            cmd :- python3 SEAM_BMC_0004_send_bios_update_capsule.py 
            --capsule_path <path for bios capsule>
            --expected_ver <bios cap version> 
            --ac_power_cycle <loop_count>
            """
            update_cap = self.send_capsule_without_version_check(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
            if self.ac_power_cycle and update_cap:
                for x in range(self.ac_power_cycle):
                    self._log.info("Performing Ac Power cycle, iteration: {}\n".format(x + 1))
                    self._log.info("Removed Ac Power from the system..")
                    self.ac_power.ac_power_off(self.AC_POWER_DELAY)
                    self._log.info("Connected back Ac Power to the system, booting initiated..\n")
                    self.ac_power.ac_power_on(self.AC_POWER_DELAY)
                    self._log.info("Waiting for system to boot into OS..")
                    self.os.wait_for_os(self.reboot_timeout)
                    time.sleep(self.SLEEP_TIME)
                    if self.sut_ssh.is_alive():
                        self._log.info("System booted into OS..!!\n")
                    else:
                        raise RuntimeError("System not booted into OS after the given time..!!")
                self._log.info("==========PERFORMED {} ITERATION(S) OF AC POWER CYCLE===========\n".format(x + 1))
                current_version = self.get_current_version()
                if current_version == self.expected_ver:
                    self._log.info("\tThe current version {} is the expected version {}".format(current_version, self.expected_ver))
                    return update_cap
                elif self.expected_ver in current_version:
                    self._log.info("\tThe expected version {} is in the current version {}".format(self.expected_ver, current_version))
                    return update_cap
                else:
                    self._log.info("\tCurrent version {} is not the expected version {}".format(current_version, self.expected_ver))
                    return False
        elif self.sut_mode == 'S5':
            """
            TC :- 66244
            cmd :- python3 SEAM_BMC_0004_send_bios_update_capsule.py 
            --capsule_path <path for bios capsule>
            --expected_ver <bios cap version> 
            --sut_mode S5
            """
            self._extracted_from_execute_101()
            self._log.info("=========UPDATING BIOS CAPSULE IN S5 STATE==========\n")
            self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
            self._extracted_from_execute_105("Waking up the system from S5..\n")
            if not self.sut_ssh.is_alive():
                raise RuntimeError("System not booted into OS after the given time..!!")
            self._log.info("System booted into OS..!!\n")
            current_version = self.get_current_version()
            if current_version == self.expected_ver:
                self._log.info("\tThe current version {} is the expected version {}".format(current_version, self.expected_ver))
                return True
            elif self.expected_ver in current_version:
                self._log.info("\tThe expected version {} is in the current version {}".format(self.expected_ver, current_version))
                return True
            else:
                self._log.info("\tCurrent version {} is not the expected version {}".format(current_version, self.expected_ver))
                return False
        elif self.uefi_variable_space:
            """
            TC :- 66054.2
            cmd :- python SEAM_BMC_0004_send_bios_update_capsule.py --capsule_path <capsule path> 
            --expected_ver <bios expected ver>
            --uefi_variable_space 
            –-warm_reset
            """
            self._log.info("=====================Entering UEFI shell=======================")
            self._uefi_util_obj.enter_uefi_shell()
            cmd = "getmtc"
            monotonic_value_beforecapsule = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(cmd)
            self._log.info("Monotonic value before capsule:{}".format(monotonic_value_beforecapsule[1]))
            monotonic_value_beforecapsule_str = str(monotonic_value_beforecapsule[1])
            monotonic_value_beforecapsule_extracted = monotonic_value_beforecapsule_str[0:8]
            monotonic_value_beforecapsule_int = int(monotonic_value_beforecapsule_extracted, 15)
            self._log.info("Monotonic value before capsule integer:{}".format(monotonic_value_beforecapsule_int))
            self._uefi_obj.warm_reset()
            self._log.info("Wait till the system comes alive...")
            self.os.wait_for_os(self._reboot_timeout)

            self._log.info("Sending Bios Capsule Update...")
            update_cap = self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)

            self._log.info("=====================Entering UEFI shell=======================")
            self._uefi_util_obj.enter_uefi_shell()
            cmd = "getmtc"
            monotonic_value_aftercapsule = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(cmd)
            self._log.info("Monotonic value after capsule:{}".format(monotonic_value_aftercapsule[1]))
            monotonic_value_aftercapsule_str = str(monotonic_value_aftercapsule[1])
            monotonic_value_aftercapsule_extracted = monotonic_value_aftercapsule_str[0:8]
            monotonic_value_aftercapsule_int = int(monotonic_value_aftercapsule_extracted, 15)
            self._log.info("Monotonic value after capsule integer:{}".format(monotonic_value_aftercapsule_int))
            self._uefi_obj.warm_reset()
            self._log.info("Wait till the system comes alive...")
            self.os.wait_for_os(self._reboot_timeout)

            if monotonic_value_aftercapsule_int > monotonic_value_beforecapsule_int:
                self._log.info(" UEFI Space Unchanged ")
                return True
            else:
                self._log.info(" UEFI Space Disturbed ")
                return False

        elif self.bmc_bios_comm:
            """
              TC: 66058.1: 
              python3 .\src\seamless\tests\bmc\functional\SEAM_BMC_0004_send_bios_update_capsule.py 
              --capsule_path "capsule path of BIOS "
              --expected_ver " version of BIOS capsule"  
              --bmc_bios_comm --warm_reset
            """
            if self.capsule_path != "":
                self._log.info("============= {} ======================".format("Performing Bios Capsule Update"))
                capsule_update = self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
                if capsule_update:
                    self._log.info("============= {} ======================".format("Entering into Uefi shell"))
                    in_uefi = self._uefi_util_obj.enter_uefi_shell()
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
                    if fs is None:
                        raise RuntimeError("=========USB NOT DETECTED===========")
                    self._log.info("============= USB IS BEING DETECTED ======================".format(fs))
                    uefishell_cmd = [fs, 'dir', 'cd cmdtool', 'cmdtool.efi 20 18 01']
                    if in_uefi:
                        self._log.info("============= {} : {} ======================".format("Executing command", uefishell_cmd))
                        for command in uefishell_cmd:
                            print("command: ", command)
                            cmd_res = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(command)
                            self._log.info("Cmdtool command response:" + str(cmd_res))
                        cmd_res_whitespace_removed = cmd_res[3].replace(" ", "")
                        self._log.info("Cmdtool response after whitespace removal:" + str(cmd_res_whitespace_removed))
                        cmd_res_len = len(cmd_res_whitespace_removed)
                        self._log.info("Length of Cmdtool response after whitespace removal:" + str(cmd_res_len))
                        cmd_res_len_final = cmd_res_len - 3
                        self._log.info("Final length of cmd response tool:" + str(cmd_res_len_final))
                        self._uefi_obj.warm_reset()
                        self._log.info("Wait till the system comes alive...")
                        self.os.wait_for_os(self._reboot_timeout)

                    else:
                        self._log.error("Not able to get in uefi shell....")
                        return False

                    if cmd_res_len_final != 30:
                        return False

                    self._log.info("Length is 15 in responce data")
                    return True
        elif self.ac_while_staging:
            """
            TC :- 66091.3
            cmd :- python3 SEAM_BMC_0004_send_bios_update_capsule.py 
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
        elif self.reboot_while_staging:
            """
            TC :- 67563
            cmd :- python3 SEAM_BMC_0004_send_bios_update_capsule.py 
            --capsule_path <path for 1st bios capsule>
            --expected_ver <bios cap1 version> 
            --capsule_path2 <path for 2st bios capsule>
            --expected_ver2 <bios cap2 version> 
            --reboot_while_staging
            """
            self.warm_reset = False
            self.STAGING_REBOOT = True
            if self.capsule_path and self.capsule_path2 and self.expected_ver and self.expected_ver2:
                current_version = self.get_current_version()
                if  self.expected_ver not in current_version:
                    self._log.info(
                        "\tThe current version {} is the expected version {}".format(current_version, self.expected_ver))
                    return self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
                else:
                    self.expected_ver =self.expected_ver2
                    path=self.capsule_path2
                    return self.send_capsule(path, self.CAPSULE_TIMEOUT, self.start_workload)

            else:
                self._log.error("Inputs are not proper, exiting the process..!!")
                return False

        else:
            """
           TC :- 66050.3, 70584.1 & 66051.1 
           cmd :- python3 SEAM_BMC_0004_send_bios_update_capsule.py 
           --capsule_path <path for bios capsule>
           --expected_ver <bios cap version> 
           --start_workload
           --warm_reset
           """
            self._log.info("Sending Bios Capsule Update...")
            return self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)

    def _extracted_from_execute_101(self):
        self.os.shutdown(self.DC_POWER_DELAY)
        self._log.info("System entered into S5 state, waiting for SUT to settle down..")
        time.sleep(self.SUT_SETTLING_TIME)

    def _extracted_from_execute_105(self, arg0):
        self._log.info(arg0)
        if self._product == "EGS":
            self._dc_power.dc_power_on()
        elif self._product == "WHT":
            self._dc_power.dc_power_reset()
        self._log.info("Waiting for system to boot into OS..")
        self.os.wait_for_os(self.reboot_timeout)
        time.sleep(self.POST_SLEEP_DELAY)

    def cleanup(self, return_status):
        super(SEAM_BMC_0004_send_bios_update_capsule, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0004_send_bios_update_capsule.main() else Framework.TEST_RESULT_FAIL)
