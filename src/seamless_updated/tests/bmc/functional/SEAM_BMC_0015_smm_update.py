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
import random
import warnings
from datetime import datetime, timedelta
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest


class SEAM_BMC_0015_smm_update(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0015_smm_update, self).__init__(test_log, arguments, cfg_opts)
        self.expected_ver = arguments.expected_ver
        self.expected_ver2 = arguments.expected_ver2
        self.smm_command = arguments.smm_command
        self.smm_capsule = arguments.smm_capsule
        self.smm_capsule2 = arguments.smm_capsule2
        self.capsule_size = 0
        self.log_level = arguments.log_level
        self.start_workload = arguments.start_workload
        self.log_type = arguments.log_type
        self.log_rev = arguments.log_rev
        self.warm_reset = False
        self.skip_reset = False
        self.authentication_time = None
        self.execution_time = None
        self.log_size = 0
        self.CSR_count = 0
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.get_smm_info_command = self._workload_path + "SMMInfo.ps1 " + self._powershell_credentials
        self.smm_code_inject_command = self._workload_path + "SMMCodeInject.ps1 " + self._powershell_credentials
        self.smm_code_stage_command = self._workload_path + "SMMCodeStage.ps1 " + self._powershell_credentials
        self.smm_set_log_level_command = self._workload_path + "SMMSetLogLevel.ps1 " + self._powershell_credentials
        self.smm_set_log_rev_command = self._workload_path + "SMMSetLogVer.ps1 " + self._powershell_credentials
        self.smm_set_log_type_command = self._workload_path + "SMMSetLogType.ps1 " + self._powershell_credentials
        self.smm_get_log_data_command = self._workload_path + "SMMGetLogData.ps1 " + self._powershell_credentials
        self.smm_get_log_file_command = self._workload_path + "SMMGetLogFile.ps1 " + self._powershell_credentials
        self.get_file_size_command = self._workload_path + "GetFileSize.ps1 " + self._powershell_credentials
        self.ping_sut_command = self._workload_path + "PingSut.ps1 " + self._powershell_credentials
        self.restart_sut_command = self._workload_path + "RestartSut.ps1 " + self._powershell_credentials
        self.enable_perioid_smi_command = self._workload_path + "EnablePeriodicSmi.ps1 " + self._powershell_credentials
        self.disable_perioid_smi_command = self._workload_path + "DisablePeriodicSmi.ps1 " + self._powershell_credentials
        self.update_type = arguments.update_type
        self.sps_mode = arguments.sps_mode
        self.rollover = arguments.rollover
        self.csr = arguments.csr
        self.verbosity_levels = arguments.verbosity_levels
        self.loop = arguments.loop
        self.multi_log = arguments.multi_log
        self.periodic_smi = arguments.periodic_smi
        self.activation = False
        self.KPI = int(arguments.KPI)
        self.msec_to_nsec = (10**6)
        self.CSR_loop = 500
        self.dmesg = 'dmesg'
        self.dmesg_c = 'dmesg -C'
        self.linux_capsule_path = '/root/smm_update/capsule/'
        self.dmesg_enable = "echo -n 'file mru_update.c +p; file mru_telemtry.c +p' > /sys/kernel/debug/dynamic_debug/control"

        if self._product == "WHT":
            self.capsules = [
                "Almost4MB_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap",
                #"cpucsr_VER_1_LSV_0_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap",
                "cpucsr_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap"
                #"cpucsr_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0_BLACKLIST_SIGN.Cap",
                #"emptypayload_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap"
            ]
            self.invalid_capsules = [
                "cpucsr_VER_1_LSV_0_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap",
                "cpucsr_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0_BLACKLIST_SIGN.Cap",
                "emptypayload_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap"
            ]
        elif self._product == "EGS":
            self.capsules = [
                "4MB_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0.Cap",
                "cpucsr_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0.Cap",
            ]
            self.invalid_capsules = [
                "cpucsr_VER_1_LSV_0_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0.Cap",
                "cpucsr_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0_denied_list_SIGN.Cap",
                "emptypayload_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0.Cap"
            ]

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0015_smm_update, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update",
                            default="")
        parser.add_argument('--expected_ver2', action='store',
                            help="The version expected to be reported after the second capsule update",
                            default="")
        parser.add_argument('--smm_command', action='store',
                            help="The smm command to be executed: queryCapability, code_inject, code_stage, code_activate",
                            default="queryCapability")
        parser.add_argument('--smm_capsule', action='store', help="The smm capsule for code injection", default="")
        parser.add_argument('--smm_capsule2', action='store', help="The smm capsule for second code injection",
                            default="")
        parser.add_argument('--log_level', action='store', help="The smm log level", default="info")
        parser.add_argument('--log_type', action='store', help="The smm log type", default="execution")
        parser.add_argument('--log_rev', action='store', help="The smm log rev", default="1")
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--update_type', action='store', help="Specify if two capsule or more / negative",
                            default="")
        parser.add_argument('--periodic_smi', action='store',
                            help="Add argument if you want to Enable and Disable periodic smi",
                            default="")
        parser.add_argument('--loop', type=int, default=1,
                            help="Add argument for # of loops of smm code inject tests")
        parser.add_argument('--rollover', action='store_true', help="Add argument for uefi variable space check",
                            default="")
        parser.add_argument('--csr', action='store_true', help="Add argument for CSR test register check",
                            default="")
        parser.add_argument('--verbosity_levels', action='store_true',
                            help="Add argument for uefi variable space check", default="")
        parser.add_argument('--multi_log', action='store_true', help="Add argument for uefi variable space check",
                            default="")
        parser.add_argument('--KPI', action='store', help="Set the KPI threshold", default="0")


    def check_capsule_pre_conditions(self):
        return True

    def evaluate_workload_output(self, output):
        return True

    def get_current_version(self, cmd, echo_version=True):
        version = None
        if self._os_type == OperatingSystems.LINUX:
            cmd = '/root/smm_update/mru_test -q'
            result = self.run_ssh_command(cmd,log_output=False)
            if 'code_rt_version' in result.stdout:
                for line in result.stdout.splitlines():
                    if 'code_rt_version' in line:
                        version = line.split(':')[1].strip()
            if echo_version:
                self._log.info("Version detected: " + str(version))
            return version
        else:
            output = self.run_powershell_command(command=self.get_smm_info_command + " " + str(cmd), get_output=True,
                                             echo_output=True)
            if 'Execution Succeeded' in output:
                for line in output.splitlines():
                    print(line)
                    if 'SMMCodeInjectRTVer' in line:
                        version = line.split(':')[1].strip()
            return version

    def check_KPI(self):
        # Only check authentication KPI if capsule is <= 128KB
        if int(self.capsule_size) <= 128:
            if self._os_type == OperatingSystems.LINUX:
                if (int( self.authentication_time) > self.KPI * self.msec_to_nsec):
                        self._log.info('Target authentication KPI: {0:>15}'.format(str(self.KPI * self.msec_to_nsec) + ' nSec'))
                        self._log.info('SMM Authentication time:   {0:>15}'.format(self.authentication_time))
                        #raise RuntimeError("Authentication time is greater than " + str(self.KPI) + " mSec")
                        warnings.warn("Authentication time is greater than " + str(self.KPI) + " mSec")
                self._log.info("Authentication time: " + str(self.authentication_time))
            else:
                auth_time = self.authentication_time.strip().split(' ')
                time_value_auth = auth_time[0]
                time_unit_auth = auth_time[1]
                if (time_unit_auth == 'nSec'):
                    if (int(time_value_auth) > self.KPI * self.msec_to_nsec):
                        self._log.info('Target authentication KPI: {0:>15}'.format(str(self.KPI * self.msec_to_nsec) + ' nSec'))
                        self._log.info('SMM Authentication time:   {0:>15}'.format(self.authentication_time))
                        #raise RuntimeError("Authentication time is greater than " + str(self.KPI) + " mSec")
                        warnings.warn("Authentication time is greater than " + str(self.KPI) + " mSec")
                else:
                    self._log.info("Authentication time: " + str(self.authentication_time))
                    raise RuntimeError("Authentication time unit is not nSec, check with SMM developer")

        # Execution time KPI not applicable except to special execution time capsule that is yet to be defined
        # exec_time = self.execution_time.strip().split(' ')
        # time_value_exec = exec_time[0]
        # time_unit_exec = exec_time[1]
        # if (time_unit_exec == 'nSec'):
        #     if (int(time_value_exec) >= self.KPI * self.msec_to_nsec):
        #         self._log.info("Exectuion time: " + str(self.execution_time))
        #         raise RuntimeError("Execution time is greater than " + str(self.KPI) + " mSec")
        # else:
        #     self._log.info("Exectuion time: " + str(self.execution_time))
        #     raise RuntimeError("Execution time unit is not nSec, check with SMM developer")
    def linux_log_level(self):
        if self.log_type == "execution":
            self.log_type = 1
        else:    
            self.log_type = 0
            
        if self.log_level == "info":
            self.log_level = 2
        elif self.log_level == "error":
            self.log_level = 0
        elif self.log_level == "warning":
            self.log_level = 1
        elif self.log_level == "verbose":
            self.log_level = 4
            
        


    def execute(self):

        result = False
        
        if self._os_type == OperatingSystems.LINUX:
            self.run_ssh_command(self.dmesg_enable,log_output=False)
            self.linux_log_level()
        
        if not(self.smm_capsule == ""):
            # Fixup default KPI by checking capsule size
            self.summary_log.info("Getting authentication KPI for: " + str(self.smm_capsule))
            # File size <= 128KB then KPI is 9ms. > 128KB then the KPI is not defined and will be set at 250ms
            if self._os_type == OperatingSystems.LINUX:
                cmd =  "ls -l " + self.linux_capsule_path + self.smm_capsule
                result = self.run_ssh_command(cmd,log_output=True)
                #self._log.info(result.stdout)
                self.capsule_size = int(result.stdout.split(' ')[4].strip())//1024
            else: 
                output = self.run_powershell_command(command = self.get_file_size_command + " C:\\Windows\\System32\\capsules\\" + str(self.smm_capsule), get_output = True, echo_output = True)
                for line in output.splitlines():
                    if(self.smm_capsule in line):
                        self.capsule_size = -1
                    elif self.capsule_size == 0:
                        self.capsule_size = line.strip()
            if self.KPI == 0:
                # Only check authentication KPI if capsule is <= 128KB
                if int(self.capsule_size) <= 128:
                    self.KPI = 9
                else:
                    self.KPI = 999

        if (self.start_workload):
            self.summary_log.info("\tStart workloads: " + str(self.start_workload))
            self._log.info("\tStarting workloads, wait two minutes till workloads stabilize...")
            self.begin_workloads()

        try:
            if (self.smm_command == "get_version"):
                cmd = 'queryCapability'
                version = self.get_current_version(cmd)
                if version == None:
                    self._log.error('Failed to detect version')
                    result = False
                    raise RuntimeError('SMM version not detected')
                else:
                    self._log.info("Current SMM version is: " + str(version))
                    result = True

            elif (self.smm_command == "query_smm"):
                cmd = 'queryCapability'
                if self._os_type == OperatingSystems.LINUX:
                    cmd = '/root/smm_update/mru_test -q /| tee /root/smm_update/SSTS/SSTS.log'
                    result = self.run_ssh_command(cmd)
                    if 'code_rt_version' in result.stdout:
                        self._log.info('SMM query successful')
                        result = True
                    else:
                        self._log.error('SMM query failed')
                        result = False
                        raise RuntimeError('SMM query failed')
                else:
                    self._log.info("Executing command for getting current smm info: " + str(self.smm_capsule))
                    output = self.run_powershell_command(command=self.get_smm_info_command + " " + str(cmd),
                                                     get_output=True, echo_output=True)
                    if 'Execution Succeeded' in output:
                        self._log.info('SMM query successful')
                        result = True
                    else:
                        self._log.error('SMM query failed')
                        result = False
                        raise RuntimeError('SMM query failed')
            elif (self.csr):
                """
                TC :- 67888.5
                python3 .\\src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0015_smm_update.py 
                --smm_command code_inject 
                --expected_ver 0x00000001 
                        --smm_capsule SCI_SampleStandAloneMMModule.efi_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_00000000-0000-0000-0000-000000000000.Cap 
                        --csr
                        --smm_capsule2 <invalid_capsule.cap>
                        --expected_ver2 0x00000001
                """
                self._log.info("CSR TEST Executing command for code injection with the first (valid) capsule: {}".format(self.smm_capsule))
                self._log.info("Setting log level to verbose")

                output = self.run_powershell_command(
                                command=self.smm_set_log_level_command + " verbose", get_output=True,
                                echo_output=True)
                for x in range(self.CSR_loop ):
                    if self._os_type == OperatingSystems.LINUX:
                        self.run_ssh_command(self.dmesg_c,log_output=False)
                        cmd =  "/root/smm_update/mru_test -l " + self.linux_capsule_path + self.smm_capsule+ " -u -R /| tee /root/smm_update/SSTS/SSTS.log"
                        result = self.run_ssh_command(cmd)
                        if 'Access Denied' in result.stdout or 'Unsupported' in result.stdout or 'Invalid Parameter' in result.stdout:
                            result = False
                            raise RuntimeError("Code injection returned error")
                        else:
                            self._log.info("Code injection complete")
                            for line in result.stdout.splitlines():
                                if ('CPU CSR' in line):
                                    self._log.info(line)
                                if ('After =' in line):
                                    self.CSR_count = (line.split('=')[1])
                                    CSR_int = int(self.CSR_count, base=16)
                                    #self._log.info(CSR_int)
                                    if (CSR_int > 64):
                                        raise RuntimeError("CSR counter over 0x3F")
                            result = self.run_ssh_command(self.dmesg,log_output=False)
                            for line in result.stdout.splitlines():
                                if('authentication time low' in line.lower()):
                                    self.authentication_time = line.split(':')[1].strip()
                                elif('execution time low' in line.lower()):
                                    self.execution_time = line.split(':')[1].strip()
                                
                        output1 = 'Execution Succeeded'
                        result = True
                    else:
                    
                        output1 = self.run_powershell_command(
                        command=self.smm_code_inject_command + " " + self.smm_capsule, get_output=True,
                            echo_output=True)

                        if ('ERROR' in output1 or 'Execution Succeeded' not in output1):

                            result = False
                            raise RuntimeError("Code injection returned error")
                        else:
                            self._log.info("Code injection complete")
                            for line in output1.splitlines():
                                if ('Authentication Time' in line):
                                    self.authentication_time = line.split(':')[1]
                                elif ('Execution Time' in line):
                                    self.execution_time = line.split(':')[1]
                        data = self.run_powershell_command(
                                                command=self.smm_get_log_data_command + " 20000",
                                                get_output=True, echo_output=False)
                        data1 = self.run_powershell_command(
                                                    command=self.smm_get_log_file_command, get_output=True,
                                                    echo_output=False)
                        for line in data1.splitlines():
                            if ('CPU CSR' in line):
                                self._log.info(line)
                            if ('After =' in line):
                                self.CSR_count = (line.split('=')[1])
                                CSR_int = int(self.CSR_count, base=16)
                                #self._log.info(CSR_int)
                                if (CSR_int > 64):
                                    raise RuntimeError("CSR counter over 0x3F")
                                
                    self.check_KPI()

                    if ('Execution Succeeded' in output1):
                        self._log.info(
                            "Executing command for code injection with an invalid/bad capsule: {}".format(
                                self.smm_capsule2))
                        if self._os_type == OperatingSystems.LINUX:
                            self.run_ssh_command(self.dmesg_c,log_output=False)
                            cmd =  "/root/smm_update/mru_test -l " + self.linux_capsule_path + self.smm_capsule2+ " -u -R /| tee /root/smm_update/SSTS/SSTS.log"
                            result = self.run_ssh_command(cmd)
                            if 'Access Denied' in result.stdout or 'Unsupported' in result.stdout or 'Invalid Parameter' in result.stdout:
                                self._log.error("The capsule trying to update is an invalid/bad capsule")
                                self._log.error("Code injection returned error as expected")

                        else:
                            output2 = self.run_powershell_command(
                                command=self.smm_code_inject_command + " " + self.smm_capsule2,
                                get_output=True, echo_output=True)
                            if ('ERROR' in output2 and 'Execution Succeeded' in output2):
                                self._log.error("The capsule trying to update is an invalid/bad capsule")
                                self._log.error("Code injection returned error as expected")
    

            elif (self.smm_command == "code_inject" and self.periodic_smi == "random"):
                """
                                        TC :- 67486.6
                                        cmd :- python3 .\src\seamless\tests\bmc\functional\SEAM_BMC_0015_smm_update.py 
                                            --smm_command code_inject 
                                            --loop 500 
                                            --periodic_smi random 
                                            --expected_ver 0x00000001 
                """
                for x in range(self.loop):
                    if x not in range(200, 300):
                        self._log.info(
                            "Executing the test with disable Periodic SMI :: iteration is in between 1 and 199; or 300 and 500 ")
                        if self._os_type == OperatingSystems.LINUX:
                            cmd =  "killall -9 smitrigger "
                            result = self.run_ssh_command(cmd)
                            result = True
                        else:
                            output = self.run_powershell_command(command=self.disable_perioid_smi_command, get_output=True,
                                                             echo_output=True)
                            if 'Disable periodic SMI successful' in output:
                                self._log.info('Periodic SMI disable successful')
                            else:
                                self._log.error('Periodic SMI disable failed')
                                raise RuntimeError('Periodic SMI disable failed')

                    else:
                        self._log.info(
                            "Executing the test with enable Periodic SMI :: iteration is in between 200 and 300")
                        if self._os_type == OperatingSystems.LINUX:
                            cmd =  "/root/smm_update/smmtrigger& "
                            result = self.run_ssh_command(cmd)
                            result = True
                        else:
                            output = self.run_powershell_command(command=self.enable_perioid_smi_command, get_output=True,
                                                             echo_output=True)
                            if 'Enable periodic SMI successful' in output:
                                self._log.info('Periodic SMI enable successful')
                            else:
                                self._log.error('Periodic SMI enable failed')
                                raise RuntimeError('Periodic SMI enable failed')

                    self.smm_capsule = random.choice(self.capsules)  # For randomly capsule selection.
                    self._log.info("Executing command for code injection with the capsule: {}".format(self.smm_capsule))
                    if self._os_type == OperatingSystems.LINUX:
                        self.run_ssh_command(self.dmesg_c,log_output=False)
                        cmd =  "/root/smm_update/mru_test -l " + self.linux_capsule_path + self.smm_capsule+ " -u -R /| tee /root/smm_update/SSTS/SSTS.log"
                        result = self.run_ssh_command(cmd)
                        if 'Access Denied' in result.stdout or 'Unsupported' in result.stdout or 'Invalid Parameter' in result.stdout:
                            result = False
                            raise RuntimeError("Code injection returned error")
                        else:
                            self._log.info("Code injection complete")
                        
                            result = self.run_ssh_command(self.dmesg,log_output=False)
                            for line in result.stdout.splitlines():
                                if('authentication time low' in line.lower()):
                                    self.authentication_time = line.split(':')[1].strip()
                                elif('execution time low' in line.lower()):
                                    self.execution_time = line.split(':')[1].strip()
                        result = True
                        
# need to add code injection status also KPI check
                    else:                   
                        output = self.run_powershell_command(command=self.smm_code_inject_command + " " + self.smm_capsule,
                                                         get_output=True, echo_output=True)

                        if ('ERROR' in output or 'Execution Succeeded' not in output):
                            if self.smm_capsule in self.invalid_capsules:
                                self._log.error("The capsule trying to update is an invalid/bad capsule")
                                self._log.error("Code injection returned error as expected")
                            else:
                                raise RuntimeError("Code injection returned error")

                        else:
                            self._log.info("Code injection complete")
                            for line in output.splitlines():
                                if ('Authentication Time' in line):
                                    self.authentication_time = line.split(':')[1]
                                elif ('Execution Time' in line):
                                    self.execution_time = line.split(':')[1]
                    self.check_KPI()

                    post_ver = self.get_current_version('queryCapability')
                    self._log.info("Version after code injection is: " + str(post_ver))
                    if (str(self.expected_ver) == str(post_ver)):
                        self._log.info("Version post code injection is same as expected version")
                        result = self.examine_post_update_conditions("SMM")
                    else:
                        self._log.error("Version post code injection does not match expected version")
                        result = False
                self._log.info("Number of loops executed: {}".format(x + 1))

            elif (self.smm_command == "code_inject" and self.periodic_smi == "enable_disable"):
                """
                                        TC :- 67560.4
                                        cmd :- python3 .\src\seamless\tests\bmc\functional\SEAM_BMC_0015_smm_update.py
                                            --smm_command code_inject 
                                            --loop 500
                                            --update_type two_capsules 
                                            --periodic_smi enable_disable 
                                            --expected_ver 0x00000001 
                                            --smm_capsule cpucsr_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap 
                                            --smm_capsule2 cpucsr_VER_1_LSV_0_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap
                """
                for x in range(self.loop):
                    if x not in range(200, 300):
                        self._log.info(
                            "Executing the test with disable Periodic SMI :: iteration is in between 1 and 199; or 300 and 500 ")
                        if self._os_type == OperatingSystems.LINUX:
                            cmd =  "killall -9 smitrigger "
                            result = self.run_ssh_command(cmd)
                            result = True
                        else:
                            output = self.run_powershell_command(command=self.disable_perioid_smi_command, get_output=True,
                                                             echo_output=True)
                            if 'Disable periodic SMI successful' in output:
                                self._log.info('Periodic SMI disable successful')
                            else:
                                self._log.error('Periodic SMI disable failed')
                                raise RuntimeError('Periodic SMI disable failed')
                    else:
                        self._log.info(
                            "Executing the test with enable Periodic SMI :: iteration is in between 200 and 300")
                        if self._os_type == OperatingSystems.LINUX:
                            cmd =  "/root/smm_update/smmtrigger& "
                            result = self.run_ssh_command(cmd)
                            result = True
                        else:
                            output = self.run_powershell_command(command=self.enable_perioid_smi_command, get_output=True,
                                                             echo_output=True)
                            if 'Enable periodic SMI successful' in output:
                                self._log.info('Periodic SMI enable successful')
                            else:
                                self._log.error('Periodic SMI enable failed')
                                raise RuntimeError('Periodic SMI enable failed')
                    if self.update_type == "two_capsules" and self.smm_capsule != "" and self.smm_capsule2 != "":
                        self._log.info("Executing command for code injection with the first (valid) capsule: {}".format(
                            self.smm_capsule))
                        if self._os_type == OperatingSystems.LINUX:
                            self.run_ssh_command(self.dmesg_c,log_output=False)
                            cmd =  "/root/smm_update/mru_test -l " + self.linux_capsule_path + self.smm_capsule+ " -u -R /| tee /root/smm_update/SSTS/SSTS.log"
                            result = self.run_ssh_command(cmd)
                            if 'Access Denied' in result.stdout or 'Unsupported' in result.stdout or 'Invalid Parameter' in result.stdout:
                                result = False
                                raise RuntimeError("Code injection returned error")
                            else:
                                self._log.info("Code injection complete")
                        
                                result = self.run_ssh_command(self.dmesg,log_output=False)
                                for line in result.stdout.splitlines():
                                    if('authentication time low' in line.lower()):
                                        self.authentication_time = line.split(':')[1].strip()
                                    elif('execution time low' in line.lower()):
                                        self.execution_time = line.split(':')[1].strip()
                            output1 = 'Execution Succeeded'
                            result = True
                        else: 
                            output1 = self.run_powershell_command(
                            command=self.smm_code_inject_command + " " + self.smm_capsule, get_output=True,
                            echo_output=True)

                            if('ERROR' in output1 or 'Execution Succeeded' not in output1):

                                result = False
                                raise RuntimeError("Code injection returned error")
                            else:
                                self._log.info("Code injection complete")
                                for line in output1.splitlines():
                                    if ('Authentication Time' in line):
                                        self.authentication_time = line.split(':')[1]
                                    elif ('Execution Time' in line):
                                        self.execution_time = line.split(':')[1]
                        self.check_KPI()
                        post_ver = self.get_current_version('queryCapability')
                        self._log.info("Version after code injection is: " + str(post_ver))
                        if (str(self.expected_ver) == str(post_ver)):
                            self._log.info("Version post code injection is same as expected version")
                            result = self.examine_post_update_conditions("SMM")
                        else:
                            self._log.error("Version post code injection does not match expected version")
                            result = False
                        if ('Execution Succeeded' in output1):
                            self._log.info(
                                "Executing command for code injection with an invalid/bad capsule: {}".format(
                                    self.smm_capsule2))
                            if self._os_type == OperatingSystems.LINUX:
                                self.run_ssh_command(self.dmesg_c,log_output=False)
                                cmd =  "/root/smm_update/mru_test -l " + self.linux_capsule_path + self.smm_capsule2+ " -u -R /| tee /root/smm_update/SSTS/SSTS.log"
                                result = self.run_ssh_command(cmd)
                                if 'Access Denied' in result.stdout or 'Unsupported' in result.stdout or 'Invalid Parameter' in result.stdout:
                                    self._log.error("The capsule trying to update is an invalid/bad capsule")
                                    self._log.error("Code injection returned error as expected")
                                    post_ver2 = self.get_current_version('queryCapability')
                                    self._log.info("Version after code injection is: {}".format(post_ver2))
                                    if (str(self.expected_ver2) == str(post_ver2)):
                                        self._log.info("Version post code injection is same as expected version")
                                        result = self.examine_post_update_conditions("SMM")


                            else: 
                                output2 = self.run_powershell_command(
                                    command=self.smm_code_inject_command + " " + self.smm_capsule2, get_output=True,
                                    echo_output=True)
                                if ('ERROR' in output2 and 'Execution Succeeded' in output2):
                                    self._log.error("The capsule trying to update is an invalid/bad capsule")
                                    self._log.error("Code injection returned error as expected")
                                    post_ver2 = self.get_current_version('queryCapability')
                                    self._log.info("Version after code injection is: {}".format(post_ver2))
                                    if (str(self.expected_ver2) == str(post_ver2)):
                                        self._log.info("Version post code injection is same as expected version")
                                        result = self.examine_post_update_conditions("SMM")
                self._log.info("Number of loops executed: {}".format(x + 1))

            elif (self.smm_command == "code_inject"):
                for x in range(self.loop):
                    self._log.info("Executing the test, loop: {}".format(x + 1))
                    if self.update_type == "negative":
                        """
                        TC :- 67887.3, 67484.5 & 67485.4
                        cmd :- python3 .\src\seamless\tests\bmc\functional\SEAM_BMC_0015_smm_update.py
                            --smm_command code_inject 
                            --update_type negative 
                            --expected_ver 0x00000001 
                            --smm_capsule <invalid_capsule.cap>
                            --loop <loop_count>
                        """
                        self._log.info(
                            "Executing command for code injection with an invalid/bad capsule: {}".format(
                                self.smm_capsule))
                        if self._os_type == OperatingSystems.LINUX:
                                self.run_ssh_command(self.dmesg_c,log_output=False)
                                cmd =  "/root/smm_update/mru_test -l " + self.linux_capsule_path + self.smm_capsule+ " -u -R /| tee /root/smm_update/SSTS/SSTS.log"
                                result = self.run_ssh_command(cmd)
                                if 'Access Denied' in result.stdout or 'Unsupported' in result.stdout or 'Invalid Parameter' in result.stdout:
                                    self._log.error("The capsule trying to update is an invalid/bad capsule")
                                    self._log.error("Code injection returned error as expected")
                                    post_ver = self.get_current_version('queryCapability')
                                    self._log.info("Version after code injection is: {}".format(post_ver))
                                    if (str(self.expected_ver) == str(post_ver)):
                                        self._log.info("Version post code injection is same as expected version")
                                        result = self.examine_post_update_conditions("SMM")
                        else:
                            output = self.run_powershell_command(
                                command=self.smm_code_inject_command + " " + self.smm_capsule,
                                get_output=True, echo_output=True)
                            if ('ERROR' in output and 'Execution Succeeded' in output):
                                self._log.error("The capsule trying to update is an invalid/bad capsule")
                                self._log.error("Code injection returned error as expected")
                                post_ver = self.get_current_version('queryCapability')
                                self._log.info("Version after code injection is: {}".format(post_ver))
                                if (str(self.expected_ver) == str(post_ver)):
                                    self._log.info("Version post code injection is same as expected version")
                                    result = self.examine_post_update_conditions("SMM")
                    elif self.update_type == "two_capsules" and self.smm_capsule != "" and self.smm_capsule2 != "":
                        """
                        TC :- 67889, 67890, 67891 & 67892
                        cmd :- python3 .\src\seamless\tests\bmc\functional\SEAM_BMC_0015_smm_update.py
                            --smm_command code_inject 
                            --update_type two_capsules 
                            --smm_capsule <valid_capsule.cap>
                            --expected_ver 0x00000001 
                            --smm_capsule2 <invalid_capsule.cap>
                            --expected_ver2 0x00000001
                            --loop <loop_count>
                        """
                        self._log.info(
                            "Executing command for code injection with the first (valid) capsule: {}".format(
                                self.smm_capsule))
                        if self._os_type == OperatingSystems.LINUX:
                            self.run_ssh_command(self.dmesg_c,log_output=False)
                            cmd =  "/root/smm_update/mru_test -l " + self.linux_capsule_path + self.smm_capsule+ " -u -R /| tee /root/smm_update/SSTS/SSTS.log"
                            result = self.run_ssh_command(cmd)
                            if 'Access Denied' in result.stdout or 'Unsupported' in result.stdout or 'Invalid Parameter' in result.stdout:
                                result = False
                                raise RuntimeError("Code injection returned error")
                            else:
                                self._log.info("Code injection complete")
                        
                                result = self.run_ssh_command(self.dmesg,log_output=False)
                                for line in result.stdout.splitlines():
                                    if('authentication time low' in line.lower()):
                                        self.authentication_time = line.split(':')[1].strip()
                                    elif('execution time low' in line.lower()):
                                        self.execution_time = line.split(':')[1].strip()
                            output1 = 'Execution Succeeded'
                            result = True
                        else:
                            output1 = self.run_powershell_command(
                                command=self.smm_code_inject_command + " " + self.smm_capsule, get_output=True,
                                echo_output=True)

                            if ('ERROR' in output1 or 'Execution Succeeded' not in output1):

                                result = False
                                raise RuntimeError("Code injection returned error")
                            else:
                                self._log.info("Code injection complete")
                                for line in output1.splitlines():
                                    if ('Authentication Time' in line):
                                        self.authentication_time = line.split(':')[1]
                                    elif ('Execution Time' in line):
                                        self.execution_time = line.split(':')[1]
                        self.check_KPI()
                        post_ver = self.get_current_version('queryCapability')
                        self._log.info("Version after code injection is: " + str(post_ver))
                        if (str(self.expected_ver) == str(post_ver)):
                            self._log.info("Version post code injection is same as expected version")
                            result = self.examine_post_update_conditions("SMM")
                        else:
                            self._log.error("Version post code injection does not match expected version")
                            result = False
                        if ('Execution Succeeded' in output1):
                            self._log.info(
                                "Executing command for code injection with an invalid/bad capsule: {}".format(
                                    self.smm_capsule2))
                            if self._os_type == OperatingSystems.LINUX:
                                self.run_ssh_command(self.dmesg_c,log_output=False)
                                cmd =  "/root/smm_update/mru_test -l " + self.linux_capsule_path + self.smm_capsule2+ " -u -R /| tee /root/smm_update/SSTS/SSTS.log"
                                result = self.run_ssh_command(cmd)
                                if 'Access Denied' in result.stdout or 'Unsupported' in result.stdout or 'Invalid Parameter' in result.stdout:
                                    self._log.error("The capsule trying to update is an invalid/bad capsule")
                                    self._log.error("Code injection returned error as expected")
                                    post_ver2 = self.get_current_version('queryCapability')
                                    self._log.info("Version after code injection is: {}".format(post_ver2))
                                    if (str(self.expected_ver2) == str(post_ver2)):
                                        self._log.info("Version post code injection is same as expected version")
                                        result = self.examine_post_update_conditions("SMM")
                            else:
                                output2 = self.run_powershell_command(
                                    command=self.smm_code_inject_command + " " + self.smm_capsule2,
                                    get_output=True, echo_output=True)
                                if ('ERROR' in output2 and 'Execution Succeeded' in output2):
                                    self._log.error("The capsule trying to update is an invalid/bad capsule")
                                    self._log.error("Code injection returned error as expected")
                                    post_ver2 = self.get_current_version('queryCapability')
                                    self._log.info("Version after code injection is: {}".format(post_ver2))
                                    if (str(self.expected_ver2) == str(post_ver2)):
                                        self._log.info("Version post code injection is same as expected version")
                                        result = self.examine_post_update_conditions("SMM")

                    elif self.rollover:
                        """
                        TC :- 69796.2
                        python3 .\\src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0015_smm_update.py 
                        --smm_command code_inject 
                        --expected_ver 0x00000001 
                        --smm_capsule Rollover1TestCase_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap 
                        --rollover 
                        --log_rev 2 
                        --log_type execution .
                        --loop 3

                        TC :- 69797.1
                        python3 .\\src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0015_smm_update.py 
                        --smm_command code_inject 
                        --expected_ver 0x00000001 
                        --smm_capsule Rollover3TestCase_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap 
                        --rollover 
                        --log_rev 2 
                        --log_type execution 
                        --loop 3
                        """
                        self._log.info("Executing command for SMM code injection with a valid capsule: {}".format(
                            self.smm_capsule))
                        if self._os_type == OperatingSystems.LINUX:
                            self.run_ssh_command(self.dmesg_c,log_output=False)
                            cmd =  "/root/smm_update/mru_test -l " + self.linux_capsule_path + self.smm_capsule+ " -u -R /| tee /root/smm_update/SSTS/SSTS.log"
                            result = self.run_ssh_command(cmd)
                            if 'Access Denied' in result.stdout or 'Unsupported' in result.stdout or 'Invalid Parameter' in result.stdout:
                                result = False
                                raise RuntimeError("Code injection returned error")
                            else:
                                self._log.info("Code injection complete")
                        
                                result = self.run_ssh_command(self.dmesg,log_output=False)
                                for line in result.stdout.splitlines():
                                    if('authentication time low' in line.lower()):
                                        self.authentication_time = line.split(':')[1].strip()
                                    elif('execution time low' in line.lower()):
                                        self.execution_time = line.split(':')[1].strip()
                            output1 = 'Execution Succeeded'
                            result = True    
                        else:    
                            output = self.run_powershell_command(
                                command=self.smm_code_inject_command + " " + self.smm_capsule, get_output=True,
                                echo_output=True)

                            if ('ERROR' not in output or 'Execution Succeeded' in output):

                                self._log.info("Code injection complete")
                                for line in output.splitlines():
                                    if ('Authentication Time' in line):
                                        self.authentication_time = line.split(':')[1]
                                    elif ('Execution Time' in line):
                                        self.execution_time = line.split(':')[1]
                        self.check_KPI()

                        post_ver = self.get_current_version('queryCapability')
                        self._log.info("Version after code injection is: " + str(post_ver))
                        if (str(self.expected_ver) == str(post_ver)):
                            self._log.info("Version post code injection is same as expected version")
                            result = self.examine_post_update_conditions("SMM")
                        else:
                            self._log.error("Version post code injection does not match expected version")
                            result = False
                        if self._os_type == OperatingSystems.LINUX:
                            cmd =  "/root/smm_update/mru_test -D " + str(self.log_rev)
                            result = self.run_ssh_command(cmd)
                            if 'Invalid' in result.stdout: #or '' in result.stdout:
                                result = False
                                raise RuntimeError("SMM query set_log_rev failed")
                            command1 = 'Execution Succeeded'
                        else:
                            command1 = self.run_powershell_command(
                                command=self.smm_set_log_rev_command + " " + str(self.log_rev), get_output=True,
                                echo_output=False)
                        if 'Execution Succeeded' in command1:
                            self._log.info('SMM query set_log_rev successful')
                            if self._os_type == OperatingSystems.LINUX:
                                cmd =  "/root/smm_update/mru_test -T " + str(self.log_type)
                                result = self.run_ssh_command(cmd)
                                if 'Invalid' in result.stdout: #or '' in result.stdout:
                                    result = False
                                    raise RuntimeError("SMM query set_log_type failed")
                                command2 = 'Execution Succeeded'
                            else:
                                command2 = self.run_powershell_command(
                                        command=self.smm_set_log_type_command + " " + str(self.log_type), get_output=True,
                                        echo_output=False)
                            if 'Execution Succeeded' in command2:
                                self._log.info('SMM query set_log_type successful')                                                                        
                                if self.log_size == 0:
                                    if self._os_type == OperatingSystems.LINUX:
                                        cmd =  "/root/smm_update/mru_test -G -R"
                                        result = self.run_ssh_command(cmd,log_output=False)
                                        if 'chunk2_size' in result.stdout:
                                            for line in result.stdout.splitlines():
                                                if 'chunk2_size' in line:
                                                    self.log_size = line.split(':')[1].strip()
                                                    self._log.info('Log size is: ' + str(self.log_size))
                                                    result = True
                                        else:
                                            result = False
                                            raise RuntimeError("SMM query get_log_size failed")
                                    else:
                                        output = self.run_powershell_command(
                                                command=self.get_smm_info_command + " getLogSize", get_output=True,
                                                echo_output=False)
                                        if 'Execution Succeeded' in output:
                                            self._log.info('SMM query get_log_size successful')
                                            for line in output.splitlines():
                                                if 'MaxDataChunkSize' in line:
                                                    self.log_size = line.split(':')[1]
                                                    self._log.info('Log size is: ' + str(self.log_size))
                                                    result = True
                                        else:
                                            self._log.error('SMM query get_log_size failed')
                                            result = False
                                            raise RuntimeError('SMM query get_log_size failed')
                                else:
                                    result = True
                                if result:
                                    if self._os_type == OperatingSystems.LINUX:
                                        self._log.info("Copying from SUT to HOST at")
                                            # needs to be updated when log_size is available linux
                                        copy_cmd = "pscp -l "+self._os_user+" -pw " +self._os_pass +" "+  self._os_ip+":/root/smm_update/SSTS/SSTS.log C:\Temp\SSTS.log"
                                        result = self.run_powershell_command(copy_cmd)
                                    else:
                                        command3 = self.run_powershell_command(
                                                command=self.smm_get_log_data_command + " " + str(self.log_size),
                                                get_output=True, echo_output=False)
                                        if 'Execution Succeeded' in command3:
                                            self._log.info('SMM query get_log_data successful')
                                            command4 = self.run_powershell_command(
                                                    command=self.smm_get_log_file_command, get_output=True,
                                                    echo_output=False)
                                            # print(command4)
                                            # exit()
                                            if 'remote powershell complete' in command4.splitlines()[0]:
                                                self._log.info("SMM query get_log_file failed: no log file present")
                                                result = False
                                                raise RuntimeError("SMM log file not present")
                                            else:
                                                self._log.error('SMM query set_log_level was successful')
                                                for line in output.splitlines():
                                                    self._log.info(line)
                                                    result = True
                                        else:
                                            self._log.error('SMM query get_log_data failed')
                                            result = False
                                            raise RuntimeError('SMM query get_log_data failed')
                                else:
                                    self._log.error('SMM query set_log_type failed')
                                    result = False
                                    raise RuntimeError('SMM query set_log_type failed')
                            else:
                                self._log.error('SMM query set_log_rev failed')
                                result = False
                                raise RuntimeError('SMM query set_log_rev failed')

                    elif self.verbosity_levels:
                        """
                        TC :- 69663.2
                        python3 .\\src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0015_smm_update.py 
                        --smm_command code_inject 
                        --expected_ver 0x00000001 
                        --smm_capsule AllLogLevelTestCase_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap 
                        --verbosity_levels 
                        --log_rev 2 
                        --log_type execution 
                        --loop 3
                        """
                        result = False
                        log_levels = ['error', 'warning', 'info', 'verbose']
                        self.log_level = random.choice(log_levels)
                        self._log.info("randomly selected log_level is : {}".format(self.log_level))
                        if self._os_type == OperatingSystems.LINUX:
                            self.linux_log_level()
                            cmd =  "/root/smm_update/mru_test -L " + str(self.log_level)
                            result = self.run_ssh_command(cmd)
                            if 'Invalid' in result.stdout:
                                result = False
                                raise RuntimeError("SMM query set_log_level failed")
                            else:
                                result = True
                                self._log.info("SMM query set_log_level successful set to "+str(self.log_level))
                            self.run_ssh_command(self.dmesg_c,log_output=False)
                            cmd =  "/root/smm_update/mru_test -l " + self.linux_capsule_path + self.smm_capsule+ " -u -R /| tee /root/smm_update/SSTS/SSTS.log"
                            result = self.run_ssh_command(cmd)
                            if 'Access Denied' in result.stdout or 'Unsupported' in result.stdout or 'Invalid Parameter' in result.stdout:
                                result = False
                                raise RuntimeError("Code injection returned error")
                            else:
                                self._log.info("Code injection complete")
                        
                                result = self.run_ssh_command(self.dmesg,log_output=False)
                                for line in result.stdout.splitlines():
                                    if('authentication time low' in line.lower()):
                                        self.authentication_time = line.split(':')[1].strip()
                                    elif('execution time low' in line.lower()):
                                        self.execution_time = line.split(':')[1].strip()
                            result = True    

                        else:
                            output = self.run_powershell_command(
                                command=self.smm_set_log_level_command + " " + str(self.log_level), get_output=True,
                                echo_output=True)
                            if 'Execution Succeeded' in output:
                                self._log.info('SMM query set_log_level successful')
                                print(output)
                                self._log.info("Executing command for SMM code injection with a valid capsule: {}".format(
                                    self.smm_capsule))
                                output = self.run_powershell_command(
                                    command=self.smm_code_inject_command + " " + self.smm_capsule, get_output=True,
                                    echo_output=True)

                                if ('ERROR' not in output or 'Execution Succeeded' in output):

                                    self._log.info("Code injection complete")
                                    for line in output.splitlines():
                                        if ('Authentication Time' in line):
                                            self.authentication_time = line.split(':')[1]
                                        elif ('Execution Time' in line):
                                            self.execution_time = line.split(':')[1]
                            else:
                                self._log.error('SMM query set_log_level {} failed'.format(self.log_level))
                                result = False
                                raise RuntimeError('SMM query set_log_level failed')
                        self.check_KPI()

                        post_ver = self.get_current_version('queryCapability')
                        self._log.info("Version after code injection is: " + str(post_ver))
                        if (str(self.expected_ver) == str(post_ver)):
                            self._log.info("Version post code injection is same as expected version")
                            result1 = self.examine_post_update_conditions("SMM")

                        else:
                            self._log.error("Version post code injection does not match expected version")
                            result = False

                        if self._os_type == OperatingSystems.LINUX:
                            cmd =  "/root/smm_update/mru_test -D " + str(self.log_rev)
                            result = self.run_ssh_command(cmd)
                            if 'Invalid' in result.stdout: 
                                result = False
                                raise RuntimeError("SMM query set_log_rev failed")
                            command1 = 'Execution Succeeded'
                        else:
                            command1 = self.run_powershell_command(
                                command=self.smm_set_log_rev_command + " " + str(self.log_rev), get_output=True,
                                echo_output=True)
                        print("\n\n")
                        print("Output of Command1:", command1)
                        print("\n\n")
                        if 'Execution Succeeded' in command1:
                            self._log.info('SMM query set_log_rev successful')
                            if self._os_type == OperatingSystems.LINUX:
                                cmd =  "/root/smm_update/mru_test -T " + str(self.log_type)
                                result = self.run_ssh_command(cmd)
                                if 'Invalid' in result.stdout:# or '' in result.stdout:
                                    result = False
                                    raise RuntimeError("SMM query set_log_type failed")
                                command2 = 'Execution Succeeded'
                            else:
                                command2 = self.run_powershell_command(
                                    command=self.smm_set_log_type_command + " " + str(self.log_type), get_output=True,
                                    echo_output=True)
                            print("\n\n")
                            print("Output of Command2:", command2)
                            print("\n\n")
                            if 'Execution Succeeded' in command2:
                                self._log.info('SMM query set_log_type successful')
                                if self.log_size == 0:
                                    if self._os_type == OperatingSystems.LINUX:
                                        cmd =  "/root/smm_update/mru_test -G -R"
                                        result = self.run_ssh_command(cmd,log_output=False)
                                        if 'chunk2_size' in result.stdout:
                                            for line in result.stdout.splitlines():
                                                if 'chunk2_size' in line:
                                                    self.log_size = line.split(':')[1].strip()
                                                    self._log.info('Log size is: ' + str(self.log_size))
                                                    result = True
                                        else:
                                            result = False
                                            raise RuntimeError("SMM query get_log_size failed")
                                    else:
                                        output = self.run_powershell_command(
                                            command=self.get_smm_info_command + " getLogSize", get_output=True,
                                            echo_output=True)
                                        if 'Execution Succeeded' in output:
                                            self._log.info('SMM query get_log_size successful')
                                            for line in output.splitlines():
                                                if 'MaxDataChunkSize' in line:
                                                    self.log_size = line.split(':')[1]
                                                    self._log.info('Log size is: ' + str(self.log_size))
                                            result = True
                                        else:
                                            self._log.error('SMM query get_log_size failed')
                                            result = False
                                            raise RuntimeError('SMM query get_log_size failed')
                                else:
                                    result = True
                                if result:
                                    if self._os_type == OperatingSystems.LINUX:
                                        self._log.info("Copying from SUT to HOST at")
                                            # needs to be updated when log_size is available linux
                                        copy_cmd = "pscp -l "+self._os_user+" -pw " +self._os_pass +" "+  self._os_ip+":/root/smm_update/SSTS/SSTS.log C:\Temp\SSTS.log"
                                        result = self.run_powershell_command(copy_cmd)
                                    else:
                                        command3 = self.run_powershell_command(
                                            command=self.smm_get_log_data_command + " " + str(self.log_size),
                                            get_output=True, echo_output=True)
                                        print("\n\n")
                                        print("Output of Command3:", command3)
                                        print("\n\n")
                                        if 'Execution Succeeded' in command3:
                                            self._log.info('SMM query get_log_data successful')
                                            command4 = self.run_powershell_command(command=self.smm_get_log_file_command,
                                                                               get_output=True, echo_output=True)
                                            print("\n\n")
                                            print("Output of Command4:", command4)
                                            print("\n\n")
                                        # exit()
                                            try:

                                                if 'remote powershell complete' in command4.splitlines()[1]:
                                                    self._log.info("SMM query get_log_file failed: no log file present")
                                                    result = False
                                                else:
                                                    self._log.error('SMM query set_log_level was successful')
                                                    for line in output.splitlines():
                                                        self._log.info(line)
                                                    if ('This is log in SMM_TELEMETRY_ERROR!' in command4
                                                        and 'This is log in SMM_TELEMETRY_WARN!' in command4
                                                        and 'This is log in SMM_TELEMETRY_INFO!' in command4
                                                        and 'This is log in SMM_TELMEMTRY_VERBOSE!' in command4):

                                                        self._log.info(
                                                            "Message \"This is log in SMM_TELEMETRY_ERROR!\" found in output")
                                                        self._log.info(
                                                            "Message \"This is log in SMM_TELEMETRY_WARN!\" found in output")
                                                        self._log.info(
                                                            "Message \"This is log in SMM_TELEMETRY_INFO!\" found in output")
                                                        self._log.info(
                                                            "Message \"This is log in SMM_TELMEMTRY_VERBOSE!\" found in output")
                                                        result = True
                                                    else:
                                                        self._log.error("Required outputs not present")
                                                        result = False
                                            except Exception as e:
                                                raise RuntimeError(e)


                                        else:
                                            self._log.error('SMM query get_log_data failed')
                                            result = False
                                            raise RuntimeError('SMM query get_log_data failed')
                            else:
                                self._log.error('SMM query set_log_type failed')
                                result = False
                                raise RuntimeError('SMM query set_log_type failed')
                        else:
                            self._log.error('SMM query set_log_rev failed')
                            result = False
                            raise RuntimeError('SMM query set_log_rev failed')

                    elif self.multi_log:
                        """
                        python3 .\\src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0015_smm_update.py 
                        --smm_command code_inject 
                        --expected_ver 0x00000001 
                        --multi_log 
                        --log_rev 2 
                        --log_type execution 
                        --loop 3
                        """
                        result = False
                        log_levels = ['error', 'warning', 'info', 'verbose']
                        self.log_level = random.choice(log_levels)
                        self._log.info("randomly selected log_level is : {}".format(self.log_level))
                        self.KPI = 9
                        if self._product == "EGS":
                            capsules = [
                                'AllLogLevelTestCase_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0.Cap',
                                'Rollover1TestCase_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0.Cap',
                                'Rollover3TestCase_VER_0_LSV_1_ID_63462139-a8b1-aa4e-9024-f2bb53ea4723_TYPE_0.Cap']
                        else:
                            capsules = [
                                'AllLogLevelTestCase_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap',
                                'Rollover1TestCase_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap',
                                'Rollover3TestCase_VER_0_LSV_1_ID_0C3D193E-88B9-4186-ACF1-6440320BCDDC_TYPE_0.Cap']
                        
                        if self._os_type == OperatingSystems.LINUX:
                            self.linux_log_level()
                            cmd =  "/root/smm_update/mru_test -L " + str(self.log_level)
                            result = self.run_ssh_command(cmd)
                            if 'Invalid' in result.stdout:# or '' in result.stdout:
                                result = False
                                raise RuntimeError("SMM query set_log_level failed")
                            else:
                                result = True
                                self._log.info("SMM query set_log_level successful set to "+str(self.log_level))
                            self.run_ssh_command(self.dmesg_c,log_output=False)
                            self.smm_capsule = random.choice(capsules)
                            self._log.info("randomly selected smm capsule is : {}".format(self.smm_capsule))
                            self._log.info("Executing command for SMM code injection with a valid capsule: {}".format(
                                    self.smm_capsule))
                            cmd =  "/root/smm_update/mru_test -l " + self.linux_capsule_path + self.smm_capsule+ " -u -R /| tee /root/smm_update/SSTS/SSTS.log"
                            result = self.run_ssh_command(cmd)
                            if 'Access Denied' in result.stdout or 'Unsupported' in result.stdout or 'Invalid Parameter' in result.stdout:
                                result = False
                                raise RuntimeError("Code injection returned error")
                            else:
                                self._log.info("Code injection complete")
                        
                                result = self.run_ssh_command(self.dmesg,log_output=False)
                                for line in result.stdout.splitlines():
                                    if('authentication time low' in line.lower()):
                                        self.authentication_time = line.split(':')[1].strip()
                                    elif('execution time low' in line.lower()):
                                        self.execution_time = line.split(':')[1].strip()
                            result = True    
                        else:
                        
                            output = self.run_powershell_command(
                                command=self.smm_set_log_level_command + " " + str(self.log_level), get_output=True,
                                echo_output=True)
                            if 'Execution Succeeded' in output:
                                self._log.info('SMM query set_log_level successful')
                                print(output)
                            
                                self.smm_capsule = random.choice(capsules)
                                self._log.info("randomly selected smm capsule is : {}".format(self.smm_capsule))
                                self._log.info("Executing command for SMM code injection with a valid capsule: {}".format(
                                    self.smm_capsule))
                                output1 = self.run_powershell_command(
                                    command=self.smm_code_inject_command + " " + self.smm_capsule, get_output=True,
                                    echo_output=True)
                                if ('ERROR' not in output1 or 'Execution Succeeded' in output1):
                                    self._log.info("Code injection complete")
                                    result = True
                                    for line in output1.splitlines():
                                        if ('Authentication Time' in line):
                                            self.authentication_time = line.split(':')[1]
                                        elif ('Execution Time' in line):
                                            self.execution_time = line.split(':')[1]
                            else:
                                self._log.error('SMM query set_log_level {} failed'.format(self.log_level))
                                result = False
                                raise RuntimeError('SMM query set_log_level failed')
                        self.check_KPI()

                        post_ver = self.get_current_version('queryCapability')
                        self._log.info("Version after code injection is: " + str(post_ver))
                        if (str(self.expected_ver) == str(post_ver)):
                            self._log.info("Version post code injection is same as expected version")
                            result = self.examine_post_update_conditions("SMM")
                        else:
                            self._log.error("Version post code injection does not match expected version")
                            result = False
                        if self._os_type == OperatingSystems.LINUX:
                            cmd =  "/root/smm_update/mru_test -D " + str(self.log_rev)
                            result = self.run_ssh_command(cmd)
                            if 'Invalid' in result.stdout: #or '' in result.stdout:
                                result = False
                                raise RuntimeError("SMM query set_log_rev failed")
                            command1 = 'Execution Succeeded'
                        else:
                            command1 = self.run_powershell_command(
                                command=self.smm_set_log_rev_command + " " + str(self.log_rev), get_output=True,
                                echo_output=True)
                        if 'Execution Succeeded' in command1:
                            self._log.info('SMM query set_log_rev successful')
                            if self._os_type == OperatingSystems.LINUX:
                                cmd =  "/root/smm_update/mru_test -T " + str(self.log_type)
                                result = self.run_ssh_command(cmd)
                                if 'Invalid' in result.stdout: #or '' in result.stdout:
                                    result = False
                                    raise RuntimeError("SMM query set_log_type failed")
                                command2 = 'Execution Succeeded'
                            else:
                                command2 = self.run_powershell_command(
                                        command=self.smm_set_log_type_command + " " + str(self.log_type), get_output=True,
                                        echo_output=True)
                            if 'Execution Succeeded' in command2:
                                self._log.info('SMM query set_log_type successful')                                                                        
                                if self.log_size == 0:
                                    if self._os_type == OperatingSystems.LINUX:
                                        cmd =  "/root/smm_update/mru_test -G -R"
                                        result = self.run_ssh_command(cmd,log_output=False)
                                        if 'chunk2_size' in result.stdout:
                                            for line in result.stdout.splitlines():
                                                if 'chunk2_size' in line:
                                                    self.log_size = line.split(':')[1].strip()
                                                    self._log.info('Log size is: ' + str(self.log_size))
                                                    result = True
                                        else:
                                            result = False
                                            raise RuntimeError("SMM query get_log_size failed")
                                    else:
                                        output = self.run_powershell_command(
                                                command=self.get_smm_info_command + " getLogSize", get_output=True,
                                                echo_output=True)
                                        if 'Execution Succeeded' in output:
                                            self._log.info('SMM query get_log_size successful')
                                            for line in output.splitlines():
                                                if 'MaxDataChunkSize' in line:
                                                    self.log_size = line.split(':')[1]
                                                    self._log.info('Log size is: ' + str(self.log_size))
                                                    result = True
                                        else:
                                            self._log.error('SMM query get_log_size failed')
                                            result = False
                                            raise RuntimeError('SMM query get_log_size failed')
                                else:
                                    result = True
                                if result:
                                    if self._os_type == OperatingSystems.LINUX:
                                        self._log.info("Copying from SUT to HOST at")
                                            # needs to be updated when log_size is available linux
                                        copy_cmd = "pscp -l "+self._os_user+" -pw " +self._os_pass +" "+  self._os_ip+":/root/smm_update/SSTS/SSTS.log C:\Temp\SSTS.log"
                                        result = self.run_powershell_command(copy_cmd)
                                    else:
                                        command3 = self.run_powershell_command(
                                                command=self.smm_get_log_data_command + " " + str(self.log_size),
                                                get_output=True, echo_output=True)
                                        if 'Execution Succeeded' in command3:
                                            self._log.info('SMM query get_log_data successful')
                                            command4 = self.run_powershell_command(
                                                    command=self.smm_get_log_file_command, get_output=True,
                                                    echo_output=True)
                                            # print(command4)
                                            # exit()
                                            if 'remote powershell complete' in command4.splitlines()[0]:
                                                self._log.info("SMM query get_log_file failed: no log file present")
                                                result = False
                                                raise RuntimeError("SMM log file not present")
                                            else:
                                                self._log.error('SMM query set_log_level was successful')
                                                for line in output.splitlines():
                                                    self._log.info(line)
                                                    result = True
                                        else:
                                            self._log.error('SMM query get_log_data failed')
                                            result = False
                                            raise RuntimeError('SMM query get_log_data failed')
                            else:
                                self._log.error('SMM query set_log_type failed')
                                result = False
                                raise RuntimeError('SMM query set_log_type failed')
                        else:
                            self._log.error('SMM query set_log_rev failed')
                            result = False
                            raise RuntimeError('SMM query set_log_rev failed')

                    else:
                        """
                        TC :- 67482.3 & 67483.3
                        cmd :- python3 .\src\seamless\tests\bmc\functional\SEAM_BMC_0015_smm_update.py
                            --smm_command code_inject  
                            --expected_ver 0x00000001 
                            --smm_capsule <valid_capsule.cap>
                            --loop <loop_count>
                        """
                        self._log.info("Executing command for code injection with a band/invalid capsule: " + str(
                            self.smm_capsule))
                        if self._os_type == OperatingSystems.LINUX:
                            self.run_ssh_command(self.dmesg_c,log_output=False)
                    #cmd = 'echo 2 > /sys/firmware/smm/start'
                            cmd =  "/root/smm_update/mru_test -l " + self.linux_capsule_path + self.smm_capsule+ " -u -R /| tee /root/smm_update/SSTS/SSTS.log"
                            result = self.run_ssh_command(cmd)
                            if 'Access Denied' in result.stdout or 'Unsupported' in result.stdout or 'Invalid Parameter' in result.stdout:
                                result = False
                                raise RuntimeError("Code injection returned error")
                            else:
                                self._log.info("Code injection complete")
                        
                                result = self.run_ssh_command(self.dmesg,log_output=False)
                                for line in result.stdout.splitlines():
                                    if('authentication time low' in line.lower()):
                                        self.authentication_time = line.split(':')[1].strip()
                                    elif('execution time low' in line.lower()):
                                        self.execution_time = line.split(':')[1].strip()
                                result = True
    
                        else:    
                            output = self.run_powershell_command(
                                command=self.smm_code_inject_command + " " + self.smm_capsule, get_output=True,
                                echo_output=True)

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
                        self.check_KPI()

                        post_ver = self.get_current_version('queryCapability')
                        self._log.info("Version after code injection is: " + str(post_ver))
                        if (str(self.expected_ver) == str(post_ver)):
                            self._log.info("Version post code injection is same as expected version")
                            result = self.examine_post_update_conditions("SMM")
                        else:
                            self._log.error("Version post code injection does not match expected version")
                            result = False
                self._log.info("Number of loops executed: {}".format(x + 1))

            elif (self.smm_command == "stage_capsule"):
                self._log.info("Executing command for staging capsule: " + str(self.smm_capsule))
                if self._os_type == OperatingSystems.LINUX:
                    self.run_ssh_command(self.dmesg_c,log_output=False)
                    cmd =  "/root/smm_update/mru_test -l " + self.linux_capsule_path + self.smm_capsule+ " -s -R /| tee /root/smm_update/SSTS/SSTS.log"
                    result = self.run_ssh_command(cmd)
                    if 'Access Denied' in result.stdout or 'Unsupported' in result.stdout or 'Invalid Parameter' in result.stdout:
                        result = False
                        raise RuntimeError("stage capsule returned error")
                    else:
                        self._log.info("stage capsule complete")
                        
                        result = self.run_ssh_command(self.dmesg,log_output=False)
                        for line in result.stdout.splitlines():
                            if('authentication time low' in line.lower()):
                                self.authentication_time = line.split(':')[1].strip()
                            elif('execution time low' in line.lower()):
                                self.execution_time = line.split(':')[1].strip()
                        result = True
                else:
                    output = self.run_powershell_command(
                        command=self.smm_code_stage_command + " C:\\Windows\\System32\\capsules\\" + str(self.smm_capsule),
                        get_output=True, echo_output=True)

                    if ('Execution Succeeded' not in output or 'ERROR' in output):
                        result = False
                        raise RuntimeError("Code staging returned error")
                    else:
                        self._log.info("Code staging complete")
                        for line in output.splitlines():
                            if ('Authentication Time' in line):
                                self.authentication_time = line.split(':')[1]
                            elif ('Execution Time' in line):
                                self.execution_time = line.split(':')[1]
                self.check_KPI()

                post_ver = self.get_current_version('queryCapability')
                self._log.info("Version post staging the capsule is: " + str(post_ver))
                if (self.get_current_version('queryCapability') == post_ver):
                    self._log.info("Version post capsule staging is same as current version")
                    self._log.info("Execution time is: " + str(self.execution_time))
                    result = self.examine_post_update_conditions("SMM")
                else:
                    self._log.error("Version post capsule staging has changed: unexpected behavior")
                    result = False


            elif (self.smm_command == "activate_capsule"):
                self._log.info("Executing command for activating previously staged capsule")
                if self._os_type == OperatingSystems.LINUX:
                    self.run_ssh_command(self.dmesg_c,log_output=False)
                    #cmd = 'echo 2 > /sys/firmware/smm/start'
                    cmd =  "/root/smm_update/mru_test -l " + self.linux_capsule_path + self.smm_capsule+ " -a -R /| tee /root/smm_update/SSTS/SSTS.log"
                    result = self.run_ssh_command(cmd)
                    if 'Access Denied' in result.stdout or 'Unsupported' in result.stdout or 'Invalid Parameter' in result.stdout:
                        result = False
                        raise RuntimeError("Code injection returned error")
                    else:
                        self._log.info("Code injection complete")
                        
                        result = self.run_ssh_command(self.dmesg,log_output=False)
                        for line in result.stdout.splitlines():
                            if('authentication time low' in line.lower()):
                                self.authentication_time = line.split(':')[1].strip()
                            elif('execution time low' in line.lower()):
                                self.execution_time = line.split(':')[1].strip()
                        result = True
                else:
                    output = self.run_powershell_command(command=self.get_smm_info_command + " codeActivate",
                                                     get_output=True, echo_output=True)

                    if ('Execution Succeeded' not in output or 'ERROR' in output):
                        result = False
                        raise RuntimeError("Capsule activation returned error")
                    else:
                        self._log.info("Capsule activation complete")
                        for line in output.splitlines():
                            if ('Authentication Time' in line):
                                self.authentication_time = line.split(':')[1]
                            elif ('Execution Time' in line):
                                self.execution_time = line.split(':')[1]
                self.check_KPI()

                post_ver = self.get_current_version('queryCapability')
                self._log.info("Version after activating capsule is: " + str(post_ver))
                if (self.expected_ver == post_ver):
                    self._log.info("Version post capsule activation is same as expected version")
                    self._log.info("Authentication time is: " + self.authentication_time)
                    result = self.examine_post_update_conditions("SMM")
                else:
                    self._log.error("Version post code injection does not match expected version")
                    result = False

            elif (self.smm_command == "get_log_level"):
                if self._os_type == OperatingSystems.LINUX:
                    cmd =  "/root/smm_update/mru_test -G -R"
                    result = self.run_ssh_command(cmd,log_output=False)
                    if 'log_level' in result.stdout:
                        for line in result.stdout.splitlines():
                            if 'log_level' in line:
                                self.log_level = line.split(':')[1].strip()
                                self._log.info('Log level is: ' + str(self.log_level))
                                result = True
                    else:
                        result = False
                        raise RuntimeError("SMM query get_log_level failed")
                else:
                    output = self.run_powershell_command(command=self.get_smm_info_command + " getLogLevel",
                                                     get_output=True, echo_output=True)
                    if 'Execution Succeeded' in output:
                        self._log.info('SMM query get_log_level successful')
                        for line in output.splitlines():
                            if 'LogLevel' in line:
                                log_level = line.split(':')[1]
                                self._log.info('Log level is: ' + str(log_level))
                        result = True
                    else:
                        self._log.error('SMM query get_log_level failed')
                        result = False
                        raise RuntimeError('SMM query get_log_level failed')

            elif (self.smm_command == "get_log_size"):
                if self._os_type == OperatingSystems.LINUX:
                    cmd =  "/root/smm_update/mru_test -G -R"
                    result = self.run_ssh_command(cmd,log_output=False)
                    if 'chunk2_size' in result.stdout:
                        for line in result.stdout.splitlines():
                            if 'chunk2_size' in line:
                                self.log_size = line.split(':')[1].strip()
                                self._log.info('Log size is: ' + str(self.log_size))
                                result = True
                    else:
                        result = False
                        raise RuntimeError("SMM query get_log_size failed")
                else:
                    output = self.run_powershell_command(command=self.get_smm_info_command + " getLogSize", get_output=True,
                                                     echo_output=True)
                    if 'Execution Succeeded' in output:
                        self._log.info('SMM query get_log_size successful')
                        for line in output.splitlines():
                            if 'MaxDataChunkSize' in line:
                                self.log_size = line.split(':')[1]
                                self._log.info('Log size is: ' + str(self.log_size))
                        result = True
                    else:
                        self._log.error('SMM query get_log_size failed')
                        result = False
                        raise RuntimeError('SMM query get_log_size failed')

            elif (self.smm_command == "get_log_data"):
                if self._os_type == OperatingSystems.LINUX:

                    self._log.info("Copying from SUT to HOST at")
                    # needs to be updated when log_size is available linux
                    copy_cmd = "pscp -l "+self._os_user+" -pw " +self._os_pass +" "+  self._os_ip+":/root/smm_update/SSTS/SSTS.log C:\Temp\SSTS.log"
                    self._log.info(copy_cmd)
                    result = self.run_powershell_command(copy_cmd)
                else:
                    if self.log_size == 0:
                        output = self.run_powershell_command(command=self.get_smm_info_command + " getLogSize",
                                                         get_output=True, echo_output=True)
                        if 'Execution Succeeded' in output:
                            self._log.info('SMM query get_log_size successful')
                            for line in output.splitlines():
                                if 'MaxDataChunkSize' in line:
                                    self.log_size = line.split(':')[1]
                                    self._log.info('Log size is: ' + str(self.log_size))
                            result = True
                        else:
                            self._log.error('SMM query get_log_size failed')
                            result = False
                            raise RuntimeError('SMM query get_log_size failed')
                    else:
                        result = True
                    if result:
                        output = self.run_powershell_command(command=self.smm_get_log_data_command + " " + self.log_size,
                                                         get_output=True, echo_output=True)
                        if 'Execution Succeeded' in output:
                            self._log.info('SMM query get_log_data successful')

                            result = True
                        else:
                            self._log.error('SMM query get_log_data failed')
                            result = False
                            raise RuntimeError('SMM query get_log_data failed')

            elif (self.smm_command == "get_log_file"):
                if self._os_type == OperatingSystems.LINUX:

                    self._log.info("Copying from SUT to HOST at")
                    # needs to be updated when log_size is available linux
                    copy_cmd = "pscp -l "+self._os_user+" -pw " +self._os_pass +" "+  self._os_ip+":/root/smm_update/SSTS/SSTS.log C:\Temp\SSTS.log"
                    self._log.info(copy_cmd)
                    result = self.run_powershell_command(copy_cmd)
                else:
                    output = self.run_powershell_command(command=self.smm_get_log_file_command, get_output=True,
                                                     echo_output=True)
                    if 'remote powershell complete' in output.splitlines()[1]:
                        self._log.info("SMM query get_log_file failed: no log file present")
                        raise RuntimeError("SMM log file not present")
                    else:
                        self._log.error('SMM query set_log_level was successful')
                        for line in output.splitlines():
                            self._log.info(line)
                        result = True

            elif (self.smm_command == "set_log_level"):
                if self._os_type == OperatingSystems.LINUX:
                    cmd =  "/root/smm_update/mru_test -L " + str(self.log_level)
                    result = self.run_ssh_command(cmd)
                    if 'Invalid' in result.stdout:# or '' in result.stdout:
                        result = False
                        raise RuntimeError("SMM query set_log_level failed")
                    cmd =  "/root/smm_update/smm_test -G"
                    result = self.run_ssh_command(cmd,log_output=False)
                    if 'log_level' in result.stdout:
                        for line in result.stdout.splitlines():
                            if 'log_level' in line:
                                self.log_level = line.split(':')[1].strip()
                                self._log.info('Log level is: ' + str(self.log_level))
                                result = True
                    else:
                        result = False
                        raise RuntimeError("SMM query set_log_level failed")
                    result = True
                else:
                    output = self.run_powershell_command(command=self.smm_set_log_level_command + " " + str(self.log_level),
                                                     get_output=True, echo_output=True)
                    if 'Execution Succeeded' in output:
                        self._log.info('SMM query set_log_level successful')
                        result = True
                    else:
                        self._log.error('SMM query set_log_level failed')
                        result = False
                        raise RuntimeError('SMM query set_log_level failed')

            elif (self.smm_command == "set_log_type"):
                if self._os_type == OperatingSystems.LINUX:
                    cmd =  "/root/smm_update/mru_test -T " + str(self.log_type)
                    result = self.run_ssh_command(cmd)
                    if 'Invalid' in result.stdout:# or '' in result.stdout:
                        result = False
                        raise RuntimeError("SMM query set_log_type failed")
                    cmd =  "/root/smm_update/smm_test -G"
                    result = self.run_ssh_command(cmd,log_output=False)
                    if 'log_type' in result.stdout:
                        for line in result.stdout.splitlines():
                            if 'log_type' in line:
                                self.log_level = line.split(':')[1].strip()
                                self._log.info('Log type is: ' + str(self.log_level))
                                result = True
                    else:
                        result = False
                        raise RuntimeError("SMM query set_log_level failed")
                    result = True
                else:
                    output = self.run_powershell_command(command=self.smm_set_log_type_command + " " + str(self.log_type),
                                                     get_output=True, echo_output=True)
                    if 'Execution Succeeded' in output:
                        self._log.info('SMM query set_log_type successful')
                        result = True
                    else:
                        self._log.error('SMM query set_log_type failed')
                        result = False
                        raise RuntimeError('SMM query set_log_type failed')

            elif (self.smm_command == "set_log_rev"):
                if self._os_type == OperatingSystems.LINUX:
                    cmd =  "/root/smm_update/mru_test -D " + str(self.log_rev)
                    result = self.run_ssh_command(cmd)
                    if 'Invalid' in result.stdout: #or '' in result.stdout:
                        result = False
                        raise RuntimeError("SMM query set_log_rev failed")
                    else:
                        result = True

                else:

                    output = self.run_powershell_command(command=self.smm_set_log_rev_command + " " + str(self.log_rev),
                                                     get_output=True, echo_output=True)
                    if 'Execution Succeeded' in output:
                        self._log.info('SMM query set_log_rev successful')
                        result = True
                    else:
                        self._log.error('SMM query set_log_rev failed')
                        result = False
                        raise RuntimeError('SMM query set_log_rev failed')

            elif (self.smm_command == "enable_periodic_smi"):
                if self._os_type == OperatingSystems.LINUX:
                    cmd =  "/root/smm_update/smmtrigger& "
                    result = self.run_ssh_command(cmd)
                    result = True
                else:
                    output = self.run_powershell_command(command=self.enable_perioid_smi_command, get_output=True,
                                                     echo_output=True)
                    if 'Enable periodic SMI successful' in output:
                        self._log.info('Periodic SMI enable successful')
                        result = True
                    else:
                        self._log.error('Periodic SMI enable failed')
                        result = False
                        raise RuntimeError('Periodic SMI enable failed')

            elif (self.smm_command == "disable_periodic_smi"):
                if self._os_type == OperatingSystems.LINUX:
                    cmd =  "killall -9 smitrigger "
                    result = self.run_ssh_command(cmd)
                    result = True
                else:
                    output = self.run_powershell_command(command=self.disable_perioid_smi_command, get_output=True,
                                                     echo_output=True)
                    if 'Disable periodic SMI successful' in output:
                        self._log.info('Periodic SMI disable successful')
                        result = True
                    else:
                        self._log.error('Periodic SMI disable failed')
                        result = False
                        raise RuntimeError('Periodic SMI disable failed')

            result = self.examine_post_update_conditions("SMM")

        except RuntimeError as e:
            self._log.exception(e)

        if self.workloads_started:
            wl_output = self.stop_workloads()
            self._log.error("Evaluating workload output")
            if not self.evaluate_workload_output(wl_output):
                result = False
        return result

    def cleanup(self, return_status):
        super(SEAM_BMC_0015_smm_update, self).cleanup(return_status)
        self._log.info('SMM Exectuion time: ' + str(self.execution_time))
        self._log.info('SMM Authentication time: ' + str(self.authentication_time))


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0015_smm_update.main() else Framework.TEST_RESULT_FAIL)
