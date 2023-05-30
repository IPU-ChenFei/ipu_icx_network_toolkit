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
import os
import sys
import time
import threading
import concurrent.futures

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.seamless.lib.seamless_common import SeamlessBaseTest


class SEAM_BMC_0007_send_ucode_pair_update_capsule(SeamlessBaseTest):
    BIOS_CONFIG_FILE = "ucode_Biosknob.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0007_send_ucode_pair_update_capsule, self).__init__(test_log, arguments, cfg_opts)
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
        self.expected_ver3 = arguments.expected_ver3
        self.warm_reset = arguments.warm_reset
        self.update_type = arguments.update_type
        self.start_workload = arguments.start_workload
        self.sut_mode = arguments.sut_mode
        self.flash_type = arguments.flash_type
        self.inband_biosknob = arguments.inband_biosknob
        self.outband_biosknob = arguments.outband_biosknob
        self.stress_staging = arguments.stress_staging
        self.multi_stress_staging = arguments.multi_stress_staging
        self.skip_reset = False
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.get_ucode_command = self._workload_path + "GetUcodeVersion.ps1 " + self._powershell_credentials
        self.ping_sut_command = self._workload_path + "PingSut.ps1 " + self._powershell_credentials
        self.restart_sut_command = self._workload_path + "RestartSut.ps1 " + self._powershell_credentials
        self.run_orchestrator = arguments.orchestrator
        self.capsule_xml = arguments.capsule_xml
        self.activation = arguments.activation
        self.sps_mode = arguments.sps_mode
        self.start_network_workload = arguments.start_network_workload
        # self.spi_access = arguments.spi_access
        self.spi_access = False
        self.stressors = arguments.stressors
        self.reboot_while_staging = arguments.reboot_while_staging

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0007_send_ucode_pair_update_capsule, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument("--flash_type", action="store", help="Specify if upgrade, downgrade and alternate update of ucode capsule")
        parser.add_argument("--capsule_path", action="store", help="Path to the capsule to be used for the update", default="")
        parser.add_argument("--capsule_path2", action="store", help="Path to the capsule2 to be used for the update", default="")
        parser.add_argument("--capsule_path3", action="store", help="Path to the capsule3 to be used for the update", default="")
        parser.add_argument("--capsule_path4", action="store", help="Path to the capsule4 to be used for the update", default="")
        parser.add_argument("--expected_ver", action="store", help="The version expected to be reported after update", default="")
        parser.add_argument('--expected_ver2', action='store', help="The version expected to be reported after the alternate update", default="")
        parser.add_argument('--expected_ver3',
                            action='store',
                            help="The version expected to be reported after reverting the capsule to Nth version",
                            default="")
        parser.add_argument('--capsule_name', action='store', help="Name of the capsule to be used for the update", default="")
        parser.add_argument('--capsule_name2', action='store', help="Name of the capsule2 to be used for the update", default="")
        parser.add_argument('--capsule_name3', action='store', help="Name of the capsule3 to be used for the update", default="")
        parser.add_argument('--capsule_name4', action='store', help="Name of the capsule4 to be used for the update", default="")
        parser.add_argument("--stress_staging", action="store_true", help="Argument should pass to perform stress staging", default="")
        parser.add_argument("--multi_stress_staging", action="store_true", help="Argument should pass to perform multiple stress staging", default="")
        parser.add_argument("--warm_reset", action="store_true", help="Add argument if warm reset to be performed")
        parser.add_argument("--start_workload", action="store_true", help="Add argument if workload need to be started")
        parser.add_argument("--update_type", action="store", help="Specify if efi utility or fit ucode", default="fit_ucode")
        parser.add_argument("--sut_mode", action="store", help="State if SUT is in UEFI mode or DC power off mode", default="")
        parser.add_argument('--orchestrator',
                            action='store_true',
                            help="Validate update through OrchestratorValidator before running. Requires \"--capulse_xml\".")
        parser.add_argument('--capsule_xml', action="store", help="Path to Capsule XML file for the update. Required for" "\"--orchestrator\".", default="")
        parser.add_argument('--activation', action='store_true', help="Add argument if only activation to be performed")
        parser.add_argument("--inband_biosknob", action="store_true", help="Argument should pass to perform Enable/Disable Bios_Knob configuration", default="")
        parser.add_argument("--outband_biosknob",
                            action="store_true",
                            help="Argument should pass to perform Enable/Disable Bios_Knob configuration",
                            default="")
        parser.add_argument('--start_network_workload', action='store_true', help="Add argument if network workload need to be started.")
        parser.add_argument('--spi_access', action='store_true', help="pass argument to perform verification after update sps", default="")
        parser.add_argument('--stressors', action='store_true', help="pass argument to perform verification after update sps", default="")
        parser.add_argument('--reboot_while_staging', action='store_true',
                            help="Add this argument if need to reset SUT while staging", default="")

    def check_capsule_pre_conditions(self):
        # To-Do add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        # To-Do add workload output analysis
        return True

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
            cmd = "cat /proc/cpuinfo | grep microcode"
            if self._os_type != OperatingSystems.LINUX:
                output = self.run_powershell_command(self.get_ucode_command, get_output=True)
            else:
                result = self.run_ssh_command(cmd)
                version = result.stdout.split("\n")[0].split(" ")
                if echo_version:
                    self._log.info("Version detected: " + version[1])
                return version[1]
            version = "NONE"
            for line in output.split("\n"):
                if "msr[8b] =" in line:
                    version = line.split(" = ")[1].split("`")[0]
                    break
                elif "BIOS" in line or "Previous" in line:
                    version = line.split(":")[1].strip()
            if echo_version:
                self._log.info("Version detected: " + version)
        elif self.update_type == "inband":
            cmd = "cat /proc/cpuinfo | grep microcode"
            result = self.run_ssh_command(cmd)
            version = result.stdout.split("\n")[0].split(" ")
            if echo_version:
                self._log.info("Version detected: " + version[1])
            version = version[1]
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
        if self.capsule_name4 != "":
            self.capsule_path4 = self.find_cap_path(self.capsule_name4)
            self._log.info("capsule path4 {}".format(self.capsule_path4))
        try:
            if self.update_type == 'inband':
                if self.stress_staging:
                    """
                    TC :- 67187.2
                    cmd :- python SEAM_BMC_0007_send_ucode_pair_update_capsule.py
                        --capsule_path "capsule path of (n-1)th version"
                        --capsule_path2 "capsule path of (n)th version"
                        --capsule_path3 "capsule path of (n+1)th version"
                        --expected_ver 0x
                        --warm_reset --stress_staging --update_type inband
                    """
                    if self.capsule_path != "" and self.capsule_path2 != "" and self.capsule_path3 != "":
                        self.warm_reset = False
                        self.skip_reset = True
                        self._log.info("sending (n-1)th version capsules.... ")
                        result = self.send_capsule_inband(self.capsule_path, self.start_workload, update_type='inband')

                        self._log.info("sending (n)th version capsules... ")
                        result1 = self.send_capsule_inband(self.capsule_path2, self.start_workload, update_type='inband')

                        self.warm_reset = True
                        self.skip_reset = False
                        self._log.info("sending (n+1)th version capsule.... ")
                        result2 = self.send_capsule_inband(self.capsule_path3, self.start_workload, update_type='inband')

                        if result and result1 and result2:
                            return True
                        else:
                            self._log.error("some capsules are not flashed properly...")
                            return False
                    else:
                        self._log.error("capsule paths are not provided....")
                        return False

                elif self.multi_stress_staging:
                    """
                    TC - 67188.2
                    cmd - python SEAM_BMC_0007_send_ucode_pair_update_capsule.py
                        --capsule_path "Ucode capsule path of (n-1)th version"
                        --capsule_path2 "SPS capsule path of nth ver"
                        --capsule_path3 "BIOS capsule path of (n)th version"
                        --expected_ver 0x
                        --warm_reset --multi_stress_staging --update_type inband
                    """
                    if self.capsule_path != "" and self.capsule_path2 != "" and self.capsule_path3 != "":
                        self.warm_reset = False
                        self.skip_reset = True
                        self._log.info("\n===========UPDATING UCODE==========\n")
                        cap_resp1 = self.send_capsule_inband(self.capsule_path, self.start_workload, update_type="inband")
                        self._log.info("\n===========UPDATING SPS==========\n")
                        self.skip_reset = False
                        cap_resp2 = self.send_capsule_without_version_check(self.capsule_path2, self.CAPSULE_TIMEOUT, self.start_workload)
                        self._log.info("\n===========UPDATING BIOS==========\n")
                        self.warm_reset = True
                        cap_resp3 = self.send_capsule_without_version_check(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload)

                        exp_ver = self.get_current_version(echo_version=True)
                        if cap_resp1 and cap_resp2 and cap_resp3:
                            if self.expected_ver == exp_ver:
                                self._log.info("\t\tThe version {} is expected version {}".format(exp_ver, self.expected_ver))
                                return True
                            else:
                                self._log.error("\tThe version {} is not the expected version {}".format(exp_ver, self.expected_ver))
                                return False
                        else:
                            self._log.error("some capsules are not flashed properly...")
                            return False
                    else:
                        self._log.error("capsule paths are not provided....")
                        return False
                elif self.inband_biosknob:
                    """
                        =========================== inband_Biosknob.cfg ===============================
                        Socket Configuration -> Processor Configuration -> DEBUG INTERFACE -> Enable (msr 0xc80 bit[0] = 1)
                        Platform Configuration -> PCH Configuration -> DCI enable -> Enable
                    """
                    if self.BIOS_CONFIG_FILE:
                        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
                    self._log.info("=========SETTING BIOS KNOB AS PER CONFIG FILE=========")
                    self.bios_util.set_bios_knob(bios_config_file)
                    self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)
                    self._log.info("=========VERIFYING THE CHANGED BIOS KNOB=========")
                    self.bios_util.verify_bios_knob(self.BIOS_CONFIG_FILE)
                    if self.flash_type == "inband_versioncheck" and self.capsule_path != "" and self.capsule_path2 != "":
                        """
                        TC :- 67181.3
                        cmd :- python SEAM_BMC_0007_send_ucode_pair_update_capsule.py
                            --capsule_path "capsule path of (n-1)th version"
                            --expected_ver 0x
                            --capsule_path2 "capsule path of (n)th version"
                            --expected_ver2 0x
                            --inband_biosknob --update_type inband --flash_type inband_versioncheck --warm_reset
                        """
                        current_version = self.get_current_version()
                        if current_version == self.expected_ver:
                            self._log.info("\tThe current version {} is the expected version {}".format(current_version, self.expected_ver))
                            self._log.info("sending (n)th version capsules.... ")
                            result = self.send_capsule_inband(self.capsule_path2, self.start_workload, update_type='inband')
                            return True
                        else:
                            self._log.info("\tCurrent version {} is not the expected version {}".format(current_version, self.expected_ver))
                        self._log.info("sending (n-1)th version capsules.... ")
                        result = self.send_capsule_inband(self.capsule_path, self.start_workload, update_type='inband')
                        self._log.info("sending (n)th version capsules... ")
                        self.expected_ver = self.expected_ver2
                        result1 = self.send_capsule_inband(self.capsule_path2, self.start_workload, update_type='inband')
                        self._log.info("Reverting the BIOS settings into default..")
                        self.bios_util.load_bios_defaults()
                        self._log.info("=========VERIFIED THE DEFAULT BIOS KNOB SETTINGS=========")
                        if result and result1:
                            return True
                        else:
                            self._log.error("some capsules are not flashed properly...")
                            return False
                    elif self.capsule_path != "" and self.capsule_path2 != "" and self.capsule_path3 != "":
                        """
                        TC :- 68164.2
                        cmd :- python SEAM_BMC_0007_send_ucode_pair_update_capsule.py
                            --capsule_path "capsule path of (n-1)th version"
                            --expected_ver 0x
                            --capsule_path2 "capsule path of (n)th version"
                            --expected_ver2 0x
                            --capsule_path3 "capsule path of (n+1)th version"
                            --expected_ver3 0x
                            --inband_biosknob --update_type inband --warm_reset
                        """
                        self._log.info("sending (n-1)th version capsules.... ")
                        result = self.send_capsule_inband(self.capsule_path, self.start_workload, update_type='inband')
                        self._log.info("sending (n)th version capsules... ")
                        self.expected_ver = self.expected_ver2
                        result1 = self.send_capsule_inband(self.capsule_path2, self.start_workload, update_type='inband')
                        self._log.info("sending (n+1)th version capsule.... ")
                        self.expected_ver = self.expected_ver3
                        result2 = self.send_capsule_inband(self.capsule_path3, self.start_workload, update_type='inband')
                        self._log.info("Reverting the BIOS settings into default..")
                        self.bios_util.load_bios_defaults()
                        self._log.info("=========VERIFIED THE DEFAULT BIOS KNOB SETTINGS=========")
                        if result and result1 and result2:
                            return True
                        else:
                            self._log.error("some capsules are not flashed properly...")
                            return False

                    elif self.capsule_path != "":
                        """
                        TC :- 67202.2
                        cmd :- python SEAM_BMC_0007_send_ucode_pair_update_capsule.py
                            --capsule_path "inband capsule path of (n)th version"
                            --expected_ver 0x
                            --inband_biosknob --update_type inband --warm_reset
                        """
                        self._log.info("sending (n)th version capsules.... ")
                        result = self.send_capsule_inband(self.capsule_path, self.start_workload, update_type='inband')
                        self._log.info("Reverting the BIOS settings into default..")
                        self.bios_util.load_bios_defaults()
                        self._log.info("=========VERIFIED THE DEFAULT BIOS KNOB SETTINGS=========")
                        if result:
                            return True
                        else:
                            self._log.error("capsule is not flashed properly...")
                            return False
                    else:
                        self._log.error("capsule path is not provided....")
                        return False
                else:
                    self._log.error("some arguments are missing...")
                    return False
            elif self.outband_biosknob:
                """
                TC :- 66226.2
                cmd :- python SEAM_BMC_0007_send_ucode_pair_update_capsule.py
                    --capsule_path "Out_of_band capsule path"
                    --expected_ver 0x
                    --outband_biosknob --warm_reset
                """
                if self.BIOS_CONFIG_FILE:
                    bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
                self._log.info("=========SETTING BIOS KNOB AS PER CONFIG FILE=========")
                self.bios_util.set_bios_knob(bios_config_file)
                self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)
                self._log.info("=========VERIFYING THE CHANGED BIOS KNOB=========")
                self.bios_util.verify_bios_knob(self.BIOS_CONFIG_FILE)
                self._log.info("Sending Out-Of-Band Capsule Update...")
                capsule_result = self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
                self._log.info("Reverting the BIOS settings into default..")
                self.bios_util.load_bios_defaults()
                self._log.info("=========VERIFIED THE DEFAULT BIOS KNOB SETTINGS=========")
                if capsule_result:
                    return True
                else:
                    self._log.error("capsule is not flashed properly...")
                    return False
            else:
                if self.flash_type == "upgrade" and self.capsule_path != "" and self.capsule_path2 != "" and self.capsule_path3 != "":
                    """
                    TC - 66273.1,66216
                    cmd - python SEAM_BMC_0007_send_ucode_pair_update_capsule.py 
                        --capsule_path "(n-1)th version FV1"
                        --capsule_path2 "(n-1)th version FV2" --expected_ver 0x 
                        --capsule_path3 "(n)th version FV2"
                        --expected_ver2 0x --warm_reset --flash_type upgrade
                    """
                    resp = False
                    self._log.info("========================= upgrading FIT Ucode =====================")
                    if self.send_capsule(self.capsule_path,
                                         self.CAPSULE_TIMEOUT,
                                         self.start_workload,
                                         capsule_path2=self.capsule_path2,
                                         update_type="ucode"):
                        self.expected_ver = self.expected_ver2
                        if self.send_capsule(self.capsule_path3, self.CAPSULE_TIMEOUT):
                            resp = True
                    return resp
                elif self.flash_type == "downgrade" and self.capsule_path != "" and self.capsule_path2 != "" and self.capsule_path3 != "":
                    """
                    TC - 66206.1
                    cmd -python SEAM_BMC_0007_send_ucode_pair_update_capsule.py
                        --capsule_path "(n)th version FV2" --expected_ver 0x --capsule_path2 "(n-1)th version FV1"
                        --capsule_path3 "(n-1)th version FV2" --expected_ver2 0x
                        --flash_type downgrade --warm_reset
                    """
                    resp = False
                    self._log.info("========================= downgrading FIT Ucode =====================")
                    if self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload):
                        self.expected_ver = self.expected_ver2
                        if self.send_capsule(self.capsule_path2, self.CAPSULE_TIMEOUT, capsule_path2=self.capsule_path3, update_type="ucode"):
                            resp = True
                    return resp
                elif self.flash_type == "alternate":
                    """
                    TC:- 66227
                    python SEAM_BMC_0007_send_ucode_pair_update_capsunle.py --capsule_path <capsule path>
                        --capsule_path2 <capsule path 2> --expected_ver 0x
                        --capsule_path3 <capsule path 3> --expected_ver2 0x(Alternate Capsule)
                        --capsule_path4 <capsule path 4> --expected_ver3 0x
                        --flash_type alternate --warm_reset
                    """
                    self._log.info("===========UPDATING FV1 & FV2 CAPSULES===========\n")
                    ucode_update1 = self.send_capsule(self.capsule_path,
                                                      self.CAPSULE_TIMEOUT,
                                                      self.start_workload,
                                                      capsule_path2=self.capsule_path2,
                                                      update_type='ucode')
                    self._log.info("===========UPDATING ALTERNATE VERSION OF UCODE CAPSULE===========\n")
                    self.expected_ver = self.expected_ver2
                    ucode_update2 = self.send_capsule(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload)
                    self._log.info("=======REVERTING CAPSULES TO NTH VERSION AFTER ALTERNATE PATCH UPDATION=======\n")
                    self.expected_ver = self.expected_ver3
                    ucode_update3 = self.send_capsule(self.capsule_path4, self.CAPSULE_TIMEOUT, self.start_workload)
                    if ucode_update1 and ucode_update2 and ucode_update3:
                        self._log.info("===========SUCCESSFULLY UPDATED CAPSULES===========")
                        return True
                    else:
                        self._log.info("Inputs are not proper, exiting the process..!!")
                        return False
                elif self.stress_staging:
                    """
                    TC :- 66211.1
                    cmd :- python SEAM_BMC_0007_send_ucode_pair_update_capsule.py
                        --capsule_path "(n-1)th version of fv1 " --capsule_path2 "(n-1)th version of fv2"
                        --capsule_path3 "(n)th version of fv1" --capsule_path4 "(n)th version of fv2"
                        --expected_ver 0x --warm_reset --stress_staging
                    """
                    self._log.info("Begin stress staging...... ")
                    if self.capsule_path != "" and self.capsule_path2 != "" and self.capsule_path3 != "" and self.capsule_path4 != "":
                        self.warm_reset = False

                        self._log.info("sending (n-1)th version capsules....... ")
                        result = self.send_capsule_without_version_check(self.capsule_path,
                                                                         self.CAPSULE_TIMEOUT,
                                                                         self.start_workload,
                                                                         capsule_path2=self.capsule_path2,
                                                                         update_type="ucode")

                        self._log.info("sending (n)th version capsules....... ")
                        result1 = self.send_capsule_without_version_check(self.capsule_path3,
                                                                          self.CAPSULE_TIMEOUT,
                                                                          self.start_workload,
                                                                          capsule_path2=self.capsule_path4,
                                                                          update_type="ucode")

                        self.warm_reset = True
                        self._log.info("sending (n-1)th version capsule in FV1......... ")
                        result2 = self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)

                        if result and result1 and result2:
                            return True
                        else:
                            self._log.error("some capsules are not flashed properly.....")
                            return False
                    else:
                        self._log.error("capsule paths are not provided......")
                        return False
                elif self.multi_stress_staging:
                    self._log.info("Begin stress multiple staging...... ")
                    """
                    TC - 66212.3
                    cmd - python SEAM_BMC_0007_send_ucode_pair_update_capsule.py
                        --capsule_path "Ucode capsule path"
                        --capsule_path2 "SPS capsule path"
                        --capsule_path3 "BIOS capsule path"
                        --expected_ver 0x (should be ucode expected version)
                        --warm_reset --multi_stress_staging
                    """
                    if self.capsule_path != "" and self.capsule_path2 != "" and self.capsule_path3 != "":
                        self.warm_reset = False
                        self._log.info("\n===========UPDATING UCODE==========\n")
                        cap_resp1 = self.send_capsule_without_version_check(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
                        self._log.info("\n===========UPDATING SPS==========\n")
                        cap_resp2 = self.send_capsule_without_version_check(self.capsule_path2, self.CAPSULE_TIMEOUT, self.start_workload)
                        self._log.info("\n===========UPDATING BIOS==========\n")
                        self.warm_reset = True
                        cap_resp3 = self.send_capsule(self.capsule_path3, self.CAPSULE_TIMEOUT, self.start_workload)

                        if cap_resp1 and cap_resp2 and cap_resp3:
                            return True
                        else:
                            self._log.error("some capsules are not flashed properly...")
                            return False
                    else:
                        self._log.error("capsule paths are not provided....")
                        return False
                elif self.sut_mode == 'S5':
                    """
                    TC :- 66223.1
                    cmd :- python SEAM_BMC_0007_send_ucode_pair_update_capsule.py 
                    --capsule_path <path for (N-1)th ucode FV1 capsule>
                    --capsule_path2 <path for (N-1)th ucode FV2 capsule>
                    --expected_ver <(N-1)th ucode cap version>  
                    --sut_mode S5
                    """
                    self.get_current_version()
                    self.os.shutdown()
                    self._log.info("System entered into S5 state, waiting for SUT to settle down..")
                    time.sleep(self.SUT_SETTLING_TIME)
                    self._log.info("=========UPDATING(DOWNGRADE) UCODE CAPSULE IN S5 STATE==========\n")
                    self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload, capsule_path2=self.capsule_path2, update_type="ucode")
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
                elif self.reboot_while_staging:
                    """
                    TC :- 66274.1
                    cmd :- python3 SEAM_BMC_0007_send_ucode_pair_update_capsule.py 
                    --capsule_path <path for (N-1)th ucode FV1 capsule>
                    --capsule_path2 <path for (N-1)th ucode FV2 capsule>
                    --expected_ver <(N-1)th ucode cap version> 
                    --capsule_path3 <path for (N)th ucode FV1 capsule>
                    --expected_ver2 <(N)th ucode cap version> 
                    --reboot_while_staging
                    """

                    if  self.capsule_path != "" and self.capsule_path2 != "" and self.capsule_path3 != "":
                        resp = False
                        self._log.info("========================= Ucode Update=====================")
                        self.warm_reset = True
                        self.STAGING_REBOOT = False
                        if self.send_capsule(self.capsule_path,
                                             self.CAPSULE_TIMEOUT,
                                             self.start_workload,
                                             capsule_path2=self.capsule_path2,
                                             update_type="ucode"):
                            self.expected_ver = self.expected_ver2
                            self.warm_reset = False
                            self.STAGING_REBOOT = True
                            if self.send_capsule(self.capsule_path3, self.CAPSULE_TIMEOUT, update_type=""):
                                resp = True
                        return resp

                else:
                    """
                    TC :- 66213.1
                    cmd :- python SEAM_BMC_0007_send_ucode_pair_update_capsule.py
                        --capsule_path "" --capsule_path2 ""
                        --expected_ver 0x --warm_reset
                    """
                    self._log.error("Loading same FIT Ucode patch OOB....")
                    if not self.send_capsule(
                            self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload, capsule_path2=self.capsule_path2, update_type="ucode"):
                        return False
                    return True

        except Exception as e:
            self._log.error(e)

    def cleanup(self, return_status):
        super(SEAM_BMC_0007_send_ucode_pair_update_capsule, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0007_send_ucode_pair_update_capsule.main() else Framework.TEST_RESULT_FAIL)
