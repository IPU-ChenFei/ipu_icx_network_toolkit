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

    Attempts to send in a SGX dll patch use to initiate the seamless update
            
            
"""
    
    
import sys
import time
import os
from datetime import datetime, timedelta
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest

class SEAM_BMC_0024_sgx_update(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0024_sgx_update, self).__init__(test_log, arguments, cfg_opts)
        self.expected_ver = ""
        self.expected_ucode = arguments.expected_ucode
        self.expected_svn = arguments.expected_svn
        self.start_workload = arguments.start_workload
        self.warm_reset = arguments.warm_reset
        self.sgx_command = arguments.sgx_command
        self.capsule = arguments.capsule
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.sgx_check_update_command = self._workload_path + "SGXCheck.ps1 " + self._powershell_credentials
        self.sgx_svn_update_command = self._workload_path + "SGXSvnUpdate.ps1 " + self._powershell_credentials
        self.sgx_svn_version_command = self._workload_path + "SGXSvnVersion.ps1 " + self._powershell_credentials
        self.sgx_rollback_command = self._workload_path + "SGXRollBack.ps1 " + self._powershell_credentials
        self.sgx_vm_command = self._workload_path + "SGXVmsStart.ps1 " + self._powershell_credentials
        self.ping_sut_command = self._workload_path + "PingSut.ps1 " + self._powershell_credentials
        self.restart_sut_command = self._workload_path + "RestartSut.ps1 " + self._powershell_credentials
        self.invocation_time = None
        self.update_time = None
        self.activation = False
        self.update_type = arguments.update_type
        self.dmesg = 'dmesg'
        self.dmesg_c = 'dmesg -C'
        self.linux_capsule_path = '/root/'
        self.linux_sgx_app_path = '/root/sgx/ereport'
        self.dmesg_svn = "dmesg | grep -i sgx"
        
    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0024_sgx_update, cls).add_arguments(parser)
        parser.add_argument('--expected_ucode', action='store', help="The ucode version expected to be reported after update", default="")
        parser.add_argument('--expected_svn', action='store', help="The svn version expected to be reported after update", default="")
        parser.add_argument('--sgx_command', action='store', help="The sgx cmd to be executed:svn_ver, sgx_update, sgx_checkupdate, sgx_svnupdate, sgx_rollback", default="svn_ver")
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--capsule', action='store', help='The path for ucode update DLL')
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--update_type', action='store', help="Specify if efi utility, fit ucode, inband", default="fit_ucode")

    def check_capsule_pre_conditions(self):
        return True

    def evaluate_workload_output(self, output):
        return True;

    def get_current_version(self, echo_version=True):
        version = None
        #tbd fucntion to read current svn version
        return version
    
    def get_ucode_ver(self, echo_version=True):
        """
        Read ucode version
        :param echo_version: True if display output
        :return bios version
        """
        cmd = 'cat /proc/cpuinfo | grep -im 1 microcode'
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
            elif "Current" in line or "BIOS" in line:
                version = line.split(":")[1].strip()
        if echo_version:
            self._log.info("Version detected: " + version)
        return version
    
    def get_svn_version(self, echo_version=True):
        version = None
        #tbd fucntion to read current svn version
#        time.sleep(10)
        cmd = ''
        if self._os_type != OperatingSystems.LINUX:
            output = self.run_powershell_command(command=self.sgx_svn_version_command, get_output=True)
            self._log.info(output)
            version = output.split('\n')[0].split(' ')
            version = str(version[1])
        else:
            #/bin/sh -c '"cd /boot && ls -l"'
            result = self.sut_ssh.execute(cmd='./app', timeout=600,cwd=self.linux_sgx_app_path)
            #self._log.info(result.stdout)
            if 'CPUSVN' in result.stdout:
                for line in result.stdout.splitlines():
                    if 'CPUSVN' in line:
                        version = line.split(' ')[2].strip()        
        if echo_version:
            self._log.info("SVN Version detected: " + version)
        return version

    def sgx_checkupdate(self):
        #self._log.info("Executing command for SGX checkupdate with DLL patch: " + str(self.capsule))
        self._log.info("Executing command for getting sgx_checkupdate ")
        if self._os_type != OperatingSystems.LINUX:
            cmd = ('sfpcopy64.exe ' + str(self.capsule) + ' C:\Windows\System32\mcupdate_GenuineIntel.dll')
            result = self.run_ssh_command(cmd)
            output = result.stdout
            if 'Copied success' in output or 'Success' in output:
                self._log.info('sfpcopy64 successful')
            else:
                self._log.error('sfpcopy64 failed')
                raise RuntimeError('sfpcopy64 failed')
            output = self.run_powershell_command(command=self.sgx_check_update_command, get_output=True, echo_output=True)
            if 'Execution Succeeded' in output:
                self._log.info('sgx_checkupdate successful')
            else:
                self._log.error('sgx_checkupdate failed')
                raise RuntimeError('sgx_checkupdate failed')
        else:
            cmd = ('iucode_tool -K ' + str(self.capsule) + ' --overwrite')
            #cmd = "pwd"
            result = self.run_ssh_command(cmd)
            self._log.info(result.stdout)
            cmd = ('echo 1 > /sys/devices/system/cpu/microcode/reload')
            result = self.run_ssh_command(cmd)
            
        ucode_ver = self.get_ucode_ver()
        if(str(self.expected_ucode.upper()) == str(ucode_ver.upper())):
            self._log.info("Version Ucode is same as expected version")
        else:
            self._log.error("Version post SGx_checkupdate does not match expected ucode version")
            raise RuntimeError("SGXcheck Ucode version did not match expected version")
        return True
        
    def sgx_svnupdate(self):
        self._log.info("Running Sgx_VM for SVN update")
        if self._os_type != OperatingSystems.LINUX:
            output = self.run_powershell_command(command=self.sgx_vm_command, get_output=True, echo_output=True)
            if 'Execution Succeeded' in output:
                self._log.info('SGX VM running')
            else:
                self._log.error('SGX VM failed')
                raise RuntimeError('SGX VM failed')
        self._log.info("Executing command for getting sgx_svnupdate ")
        if self._os_type != OperatingSystems.LINUX:
            output = self.run_powershell_command(command=self.sgx_svn_update_command, get_output=True, echo_output=True)
        #self._log.info(output)
            if 'Execution Succeeded' in output:
                self._log.info('sgx_svn update successful')
            else:
                self._log.error('sgx_svn updatefailed')
                raise RuntimeError('sgx_svn update failed')
        else:
            cmd = ('echo 1 > /sys/devices/system/cpu/microcode/svnupdate')
            result = self.run_ssh_command(cmd)
            result = self.run_ssh_command(self.dmesg,log_output=False)
            for line in result.stdout.splitlines():
                if('sgx_updatesvn' in line.lower()):
                    ret = line.split(' ')[5].strip()
                    if (ret != '0'):
                        raise RuntimeError('sgx_svn update failed ret = ' + ret)
        version = self.get_svn_version()
        if(str(self.expected_svn.upper()) == str(version.upper())):
            self._log.info("Version svn is same as expected version")
        else:
            self._log.error("Version post SGx_svnupdate does not match expected svn version")
            raise RuntimeError("svn version did not match expected version")
        return True
    
    def sgx_rollback(self):
        self._log.info("Executing command for SGX rollback to original version")
        if self._os_type == OperatingSystems.LINUX:
            cmd = 'rm -f /lib/firmware/intel-ucode/*'
            result = self.run_ssh_command(cmd)
        else:
            output = self.run_powershell_command(command=self.sgx_rollback_command, get_output=True, echo_output=True)
            if 'Execution Succeeded' in output:
                self._log.info('SGX rollback successful')
            else:
                self._log.error('SGX rollback failed')
                raise RuntimeError('SGX rollback failed')
        if self.warm_reset:
            self._log.info("\tWarm reset the system")
            if self._os_type != OperatingSystems.LINUX and not self.sut_ssh.is_alive():
                self.run_powershell_command(command=self.restart_sut_command, get_output=True)
            else:
                self._log.info("\t reboot through SSH")
                self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)
            ucode_ver = self.get_ucode_ver()
            if(str(self.expected_ucode.upper()) == str(ucode_ver.upper())):
                self._log.info("Version Ucode is same as expected version")
            else:
                self._log.error("Version post SGx rollback does not match expected ucode version")
                raise RuntimeError("SGXcheck Ucode version did not match expected version")
            version = self.get_svn_version()
            if(str(self.expected_svn.upper()) == str(version.upper())):
                self._log.info("Version svn is same as expected version")
            else:
                self._log.error("Version post SGx_svnupdate does not match expected svn version")
                raise RuntimeError("svn version did not match expected version")
        return True
        
    def sgx_update(self):
        self._log.info("Executing command for SGX update E2E with DLL patch: " + str(self.capsule))
        self.sgx_checkupdate()
        self.sgx_svnupdate()
        #self.update_time = datetime.now() - time_start
        self._log.info('SGX update E2E')
        return True
    
    def execute(self):
        result = False           
        try:
            if self.start_workloads:
                self.summary_log.info("\tStart workloads: " + str(self.start_workloads))
                self._log.info("\tStarting workloads, wait two minutes till workloads stabilize...")
                self.begin_workloads()    
            #time_start = datetime.now()
#sgx_update, sgx_checkupdate, sgx_svnupdate, sgx_rollback"        
            if(self.sgx_command == "sgx_update"):
                result = self.sgx_update()
                
            elif(self.sgx_command == "svn_ver"):
                version = self.get_svn_version()
                result = True
                
            elif(self.sgx_command == "sgx_checkupdate"):
                result = self.sgx_checkupdate()
                
            elif(self.sgx_command == "sgx_svnupdate"):
                result = self.sgx_svnupdate()
                
            elif(self.sgx_command == "sgx_rollback"):
                result = self.sgx_rollback()
            else:
                raise RuntimeError("sgx_command was not set as one of the options: sgx_update, sgx_checkupdate, sgx_svnupdate, sgx_rollback")
     
        except RuntimeError as e:
            self._log.exception(e)
            
        if self.workloads_started:
                wl_output = self.stop_workloads()
                self._log.error("Evaluating workload output")
                if not self.evaluate_workload_output(wl_output):
                    result = False
        return result

    def cleanup(self, return_status):
        super(SEAM_BMC_0024_sgx_update, self).cleanup(return_status)
 
if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0024_sgx_update.main() else Framework.TEST_RESULT_FAIL)
