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
# and approved by Intel in writing
#################################################################################
"""
    :Seamless BMC capsule stage test

    Attempts to send in an sps capsule use to initiate the seamless update
"""
import sys
import time
import threading
import re
import concurrent.futures

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.seamless.lib.seamless_common import SeamlessBaseTest


class SEAM_BMC_0003_send_sps_update_capsule(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0003_send_sps_update_capsule, self).__init__(test_log, arguments, cfg_opts)
        self.capsule_path = arguments.capsule_path
        self.capsule_path2 = arguments.capsule_path2
        self.capsule_path3 = arguments.capsule_path3
        self.capsule_name = arguments.capsule_name
        self.capsule_name2 = arguments.capsule_name2
        self.capsule_name3 = arguments.capsule_name3
        self.expected_ver = arguments.expected_ver
        self.expected_ver2 = arguments.expected_ver2
        self.expected_ver3 = arguments.expected_ver3
        self.update_type = arguments.update_type
        self.sps_update_verification = arguments.sps_update_verification
        self.warm_reset = arguments.warm_reset
        self.start_workload = arguments.start_workload
        self.capsule_type = arguments.capsule_type
        self.sut_mode = arguments.sut_mode
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.run_PnP_command = self._workload_path + "RunPnPTest.ps1 " + self._powershell_credentials
        self.get_sps_command = self._workload_path + "GetSPSVersion.ps1 " + self._powershell_credentials
        self.regionName = ""
        self.run_orchestrator = arguments.orchestrator
        self.capsule_xml = arguments.capsule_xml
        self.capsule = "SPS"
        self.parallel_staging = arguments.parallel_staging
        self.spi_access = arguments.spi_access
        self.pnp = arguments.pnp
        self.skip_reset = False
        self.activation = False
        self.sps_mode = arguments.sps_mode
        self.ac_while_staging = arguments.ac_while_staging
        self.reboot_while_staging = arguments.reboot_while_staging

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0003_send_sps_update_capsule, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--capsule_path', action='store', help="Path to the capsule to be used for the update", default="")
        parser.add_argument('--capsule_path2', action='store', help="Path to the 2nd capsule to be used for the update", default="")
        parser.add_argument('--capsule_path3', action='store', help="Path to the 3rd capsule to be used for the update", default="")
        parser.add_argument('--capsule_name', action='store', help="Name of the capsule to be used for the update", default="")
        parser.add_argument('--capsule_name2', action='store', help="Name of the capsule2 to be used for the update", default="")
        parser.add_argument('--capsule_name3', action='store', help="Name of the capsule3 to be used for the update", default="")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update of capsule", default="")
        parser.add_argument('--expected_ver2', action='store', help="The version expected to be reported after update of capsule2", default="")
        parser.add_argument('--expected_ver3', action='store', help="The version expected to be reported after update of capsule3", default="")
        parser.add_argument('--update_type', action='store', help="Specify if efi utility, fit ucode, inband", default="fit_ucode")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--sut_mode', action='store', help="State if SUT is in UEFI mode or DC power off mode", default="")
        parser.add_argument('--capsule_type', action='store', help="Add argument as 'negative' for negative usecases", default="")
        parser.add_argument('--orchestrator',
                            action='store_true',
                            help="Validate update through OrchestratorValidator before running. Requires \"--capulse_xml\".")
        parser.add_argument('--capsule_xml', action="store", help="Path to Capsule XML file for the update. Required for" "\"--orchestrator\".", default="")
        parser.add_argument('--pnp', action='store_true', help="pass argument to execute pnp tool command")
        parser.add_argument('--parallel_staging', action='store_true', help="Add this argument if need to stage capsules parallelly", default="")
        parser.add_argument('--sps_update_verification', action='store_true', help="pass argument to perform verification after update sps")
        parser.add_argument('--spi_access', action='store_true', help="pass argument to perform verification after update sps", default="")
        parser.add_argument('--ac_while_staging', action='store_true',
                            help="Add this argument if need to stage capsules parallelly", default="")
        parser.add_argument('--reboot_while_staging', action='store_true',
                            help="Add this argument if need to reset SUT while staging", default="")

    def get_current_version(self, echo_version=True):
        """
        Read sps version
        :param echo_version: True if display output
        :return ME version
        """
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

        rec_ver = version.split('(Recovery)')[0].strip()
        opr_ver = version.split('(Recovery)')[1].split('(Operational)')[0].replace(',', '').strip()

        if me_mode == 'Normal':
            me_mode = 'Operational'

        version = 'Operational: ' + opr_ver + ' Recovery: ' + rec_ver + ' Current State: ' + me_mode

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
        # TODO: add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        # TODO: add workload output analysis
        return True

    def access_permission(self):
        if self._os_type != OperatingSystems.LINUX:
            return True
        else:
            cmd = "chmod 777 *"
            result = self.run_ssh_command(cmd)
            return result

    def pnp_test(self):
        if self._os_type != OperatingSystems.LINUX:
            output = self.run_powershell_command(self.run_PnP_command, get_output=True)
            return output
        else:
            cmd = "./mlc"
            result = self.run_ssh_command(cmd)
            output = result.stdout
            return output

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

        if self.capsule_type == 'negative':
            """
            TC's :- 64964.2, 64965.1
            cmd :- python SEAM_BMC_0003_send_sps_update_capsule.py
                --capsule_path "corrupted capsule path"
                --capsule_type negative
            """
            self._log.info("Sending SPS Negative Capsule Update...")
            return self.send_capsule_negative(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule, capsule_type="negative")
        elif self.parallel_staging:
            """
            TC :- 66172.2
            cmd :- python SEAM_BMC_0003_send_sps_update_capsule.py 
            --capsule_path "Operational capsule path 1" 
            --capsule_path2 "Operational capsule path 2" --> (which need to be rejected)
            --expected_ver "Operational: x.x.x.x Current State: Operational" --> (Capsule 1 version)
            --parallel_staging
            """
            self.expected_ver = self.get_expected_version(self.capsule_path, self.expected_ver)
            self.send_capsule_parallel(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
            exp_ver = self.get_current_version(echo_version=True)
            if self.expected_ver == exp_ver:
                self._log.info("\t\tThe current version {} is the expected version {}".format(exp_ver, self.expected_ver))
                return True
            else:
                self._log.error("\t\tThe current version {} is not the expected version {}".format(exp_ver, self.expected_ver))
                return False

        elif self.sps_update_verification:
            """
            TC :- 67936.1
            cmd :- python SEAM_BMC_0003_send_sps_update_capsule.py
                --capsule_path "capsule path of Recovery on Operational"
                --expected_ver "Operational: 4.4.3.249 Current State: Recovery"
                --capsule_path2 "Recovery capsule path"
                --expected_ver2 "Recovery: 4.4.3.249 Current State: Recovery"
                --capsule_path3 "Operational capsule path"
                --expected_ver3 "Operational: 4.4.3.249 Current State: Operational"
                --sps_update_verification
            """
            result = False
            self._log.info("sending recovery on operational capsule....")
            self.expected_ver = self.get_expected_version(self.capsule_path, self.expected_ver)
            cap_res1 = self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule)

            if cap_res1:
                self._bmc_ipmi.ipmi_cmd("raw 0x2e 0xdf 0x57 0x01 0x00 0x01")
                self._bmc_ipmi.ipmi_cmd("0x6 0x2")
                exp_ver = self.get_current_version(echo_version=True)
                if self.expected_ver == exp_ver:
                    self._log.info("\t\tThe version {} is expected version {}".format(exp_ver, self.expected_ver))
                    result = True
                else:
                    self._log.error("\t\tThe version {} is not expected version {}".format(exp_ver, self.expected_ver))
                    return False
            else:
                self._log.error("recovery on operational capsule failed to flash...")
                return False

            self._log.info("sending recovery capsule....")
            self.expected_ver = self.expected_ver2
            self.expected_ver = self.get_expected_version(self.capsule_path2, self.expected_ver)
            cap_res2 = self.send_capsule(self.capsule_path2, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule)

            if cap_res2:
                self._bmc_ipmi.ipmi_cmd("raw 0x2e 0xdf 0x57 0x01 0x00 0x01")
                self._bmc_ipmi.ipmi_cmd("0x6 0x2")
                exp_ver2 = self.get_current_version(echo_version=True)
                if self.expected_ver == exp_ver2:
                    self._log.info("\t\tThe version {} is expected version {}".format(exp_ver2, self.expected_ver))
                    result = True
                else:
                    self._log.error("\t\tThe version {} is not expected version {}".format(exp_ver2, self.expected_ver))
                    return False
            else:
                self._log.error("recovery capsule failed to flash...")
                return False
            self._log.info("sending Operational capsule....")
            self.expected_ver = self.expected_ver3
            self.expected_ver = self.get_expected_version(self.capsule_path3, self.expected_ver)
            cap_res3 = self.send_capsule(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule)

            if cap_res3:
                self._bmc_ipmi.ipmi_cmd("raw 0x2e 0xdf 0x57 0x01 0x00 0x01")
                self._bmc_ipmi.ipmi_cmd("0x6 0x2")
                exp_ver3 = self.get_current_version(echo_version=True)
                if self.expected_ver == exp_ver3:
                    self._log.info("\t\tThe version {} is expected version {}".format(exp_ver3, self.expected_ver))
                    result = True
                else:
                    self._log.error("\t\tThe version {} is not expected version {}".format(exp_ver3, self.expected_ver))
                    return False
            else:
                self._log.error("Operational capsule failed to flash...")
                return False
            return result

        elif self.pnp:
            """
            TC : - 64970.2
            cmd : - python SEAM_BMC_0003_send_sps_update_capsule.py
                --capsule_path "capsule path of SPS Operational"
                --expected_ver "Operational: 4.4.3.249 Current State: Operational"
                --pnp --warm_reset
            """
            flag = False
            self.expected_ver = self.get_expected_version(self.capsule_path, self.expected_ver)
            res = self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule)
            if res:
                self._log.info("============== {} ===========".format("PnP(mlc) results"))
                self.access_permission()
                pnp_res = self.pnp_test()
                result = pnp_res.split("\n")
                self._log.info("============ {} ==============".format("Measuring Status"))
                for task in result:
                    if re.search(r"Measuring", task):
                        flag = True
                        self._log.info("{} is Done".format(task.strip()))
                if flag is True:
                    return True
                else:
                    self._log.error("All mlc data not measured properly...")
                    return False
            else:
                self._log.error("Capsule failed to flash...")
                return False
        elif self.sut_mode == 'S5':
            """
            TC : - 66448.4
            cmd : - python SEAM_BMC_0003_send_sps_update_capsule.py 
            --capsule_path "capsule path of Recovery on Operational" 
            --expected_ver "Operational: x.x.x.x Current State: Recovery" 
            --capsule_path2 "Recovery capsule path" 
            --expected_ver2 "Recovery: x.x.x.x Current State: Recovery" 
            --capsule_path3 "Operational capsule path" 
            --expected_ver3 "Operational: x.x.x.x Current State: Operational"
            --sut_mode S5
            """
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
                return True
            else:
                self._log.info("Inputs or updates are not proper..!!")
        elif self.sps_mode:
            """
            TC :- 64963.1
            cmd :- python3 SEAM_BMC_0003_send_sps_update_capsule.py
                --capsule_path "SPS_Operational_cap"
                --expected_ver "Operational: x.x.x.xxx Current State: Operational" --sps_mode
            """
            self._log.info("Sending SPS Operational Capsule Update to check sps mode...")
            self.expected_ver = self.get_expected_version(self.capsule_path, self.expected_ver)
            cap_res = self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule)
            if cap_res:
                self._log.info("============cheking sps current mode after capsule flashed=======================")
                if self._os_type == OperatingSystems.WINDOWS:
                    sps_info = self.run_powershell_command(self.get_sps_command, get_output=True)
                else:
                    cmd = './spsInfoLinux64'
                    result = self.run_ssh_command(cmd)
                    sps_info = result.stdout
                sps_state_info = re.search(r"Current ?State\s\(\d+:\d+\)\:\s+(.*)\s\(\d+\)", sps_info)
                current_state = sps_state_info.group(1)
                self._log.info("Current state : {}".format(current_state))
                if current_state.strip() != "Normal":
                    self._log.error("current state is: {}, not Normal".format(current_state))
                    return False
                else:
                    return True
            else:
                self._log.error("capsule not flashed properly or SUT is in linux...")
                return False
        elif self.reboot_while_staging:
            """
            TC :- 64967.1
            cmd :- python3 SEAM_BMC_0003_send_sps_update_capsule.py
            --capsule_path <path for 1st SPS capsule>
            --expected_ver <SPS cap1 version> 
            --reboot_while_staging
            """
            self.warm_reset = False
            self.STAGING_REBOOT = True
            if self.capsule_path  and self.expected_ver:
                return self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)

        elif self.ac_while_staging:
            """
            TC :- 66091.3
            cmd :- python3 SEAM_BMC_0003_send_sps_update_capsule.py 
            --capsule_path <path for 1st SPS capsule
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
            Note: If workload required, need to add the argument --start_workload for below commands.
            
            TC :- 70256.1
            cmd :- python3 SEAM_BMC_0003_send_sps_update_capsule.py
                --capsule_path "Operational capsule path"
                --expected_ver "Operational : <Operational ver> Current State: Operational" 
                --start_workload'

            TC :- 64975.3, 64977.2
            cmd :- python SEAM_BMC_0003_send_sps_update_capsule.py
                --capsule_path "capsule path of Recovery on Operational"
                --expected_ver "Operational: 4.4.3.249 Current State: Recovery"
                --capsule_path2 "Recovery capsule path"
                --expected_ver2 "Recovery: 4.4.3.249 Current State: Recovery"
                --capsule_path3 "Operational capsule path"
                --expected_ver3 "Operational: 4.4.3.249 Current State: Operational"
            """
            self._log.info("Sending SPS Capsule Update...")

            self.expected_ver = self.get_expected_version(self.capsule_path, self.expected_ver)
            self._log.info("=========1st Capsule============\n")
            if not self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule):
                return False
            if self.capsule_path2 == "" and self.capsule_path3 == "":
                self._log.info("ITS A SINGLE CAPSULE UPDATION")
                return True
            elif self.capsule_path2 != "" and self.capsule_path3 != "":
                self.expected_ver = self.expected_ver2
                self.expected_ver = self.get_expected_version(self.capsule_path2, self.expected_ver)
                self._log.info("=========2nd Capsule============\n")
                if not self.send_capsule(self.capsule_path2, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule):
                    return False
                self.expected_ver = self.expected_ver3
                self.expected_ver = self.get_expected_version(self.capsule_path3, self.expected_ver)
                self._log.info("=========3rd Capsule============\n")
                self.expected_ver = self.get_expected_version(self.capsule_path3, self.expected_ver)
                if not self.send_capsule(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload, self.capsule):
                    return False
                else:
                    return True
            else:
                self._log.info("One of the Capsule is not passed as argument in 3 stage Capsule Updation")
                return False

    def cleanup(self, return_status):
        super(SEAM_BMC_0003_send_sps_update_capsule, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0003_send_sps_update_capsule.main() else Framework.TEST_RESULT_FAIL)
