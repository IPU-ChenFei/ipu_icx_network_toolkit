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

import re
import os
import time

from src.seamless.lib.seamless_common import SeamlessBaseTest
from src.seamless.tests.bmc.constants.sgx_constants import SGXConstants, PortAllocation, TimeDelay, LinuxPath
from dtaf_core.lib.dtaf_constants import OperatingSystems

class SgxCommon(SeamlessBaseTest):
    """
    This Class is Used as Common Class For all the SGX TCB RESET LESS UPDATE Test Cases
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Default options
        """
        super().__init__(test_log, arguments, cfg_opts)
        #Windows OS Specific Paramters:
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.sgx_check_update_command = self._workload_path + "SGXCheck.ps1 " + self._powershell_credentials
        self.sgx_svn_update_command = self._workload_path + "SGXSvnUpdate.ps1 " + self._powershell_credentials
        self.sgx_svn_version_command = self._workload_path + "SGXSvnVersion.ps1 " + self._powershell_credentials
        self.sgx_rollback_command = self._workload_path + "SGXRollBack.ps1 " + self._powershell_credentials
        self.sgx_vm_command = self._workload_path + "SGXVmsStart.ps1 " + self._powershell_credentials
        self.ping_sut_command = self._workload_path + "PingSut.ps1 " + self._powershell_credentials
        self.restart_sut_command = self._workload_path + "RestartSut.ps1 " + self._powershell_credentials
        #KPI Validation Specific:
        self.invocation_time = None
        self.update_time = None
        self.activation = False


    def get_ucode_ver(self, echo_version=True):
        """
        Read ucode version
        :param echo_version: True if display output
        :return UCODE version
        """
        if self._os_type != OperatingSystems.LINUX:
            output = self.run_powershell_command(self.get_ucode_command, get_output=True)
        else:
            result = self.run_ssh_command(SGXConstants.GET_UCODE_LINUX_CMD)
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
        """
        Read SVN version
        :param echo_version: True if display output
        :return SVN version
        """
        version = None
        if self._os_type != OperatingSystems.LINUX:
            output = self.run_powershell_command(command=self.sgx_svn_version_command, get_output=True)
            self._log.info(output)
            version = output.split('\n')[0].split(' ')
            version = str(version[1])
        else:
            result = self.sut_ssh.execute(cmd=SGXConstants.SGX_APP, timeout=TimeDelay.SYSTEM_TIMEOUT,cwd=LinuxPath.LINUX_SGX_APP_PATH)
            if 'SE_SVN' in result.stdout:
                for line in result.stdout.splitlines():
                    if 'SE_SVN' in line:
                        version = line.split(':')[-1].strip()
        if echo_version:
            self._log.info("SVN Version detected: " + str(version))
        return version

    def create_ucode_patch_link(self):
        """
        Function to create a link to ucode patch 
        """
        if (self.multi_step_patch == True):
            self.sut_ssh.execute_async(cmd=SGXConstants.LIN_UCODE_PATCH_LINK_CMD.format(str(self.capsule), str(self.patch_FMS_name)), cwd=LinuxPath.LINUX_UCODE_PATCH_PATH)
        return True

    def sgx_checkupdate(self):
        """
        Copy the UCode patch and reload 
        :return TRUE on successful update
        """
        self._log.info("Executing command for getting sgx_checkupdate ")
        if self._os_type != OperatingSystems.LINUX:
            cmd = (SGXConstants.WIN_COPY_TOOL + str(self.capsule) + SGXConstants.WIN_UCODE_DEF_DLL)
            result = self.run_ssh_command(cmd)
            output = result.stdout
            if 'Copied success' in output or 'Success' in output:
                self._log.info('Ucode patch copy successful')
            else:
                self._log.error('Ucode patch copy failed')
                raise RuntimeError('Ucode patch copy failed')
            output = self.run_powershell_command(command=self.sgx_check_update_command, get_output=True, echo_output=True)
            if 'Execution Succeeded' in output:
                self._log.info('sgx_checkupdate successful')
            else:
                self._log.error('sgx_checkupdate failed')
                raise RuntimeError('sgx_checkupdate failed')
        else:
            if self.multi_step_patch:
                self.run_ssh_command(SGXConstants.LIN_UCODE_COPY_MULTI_STEP_CMD.format(str(self.capsule)))
                self.create_ucode_patch_link()
            else:
                self.run_ssh_command(SGXConstants.LIN_UCODE_COPY_CMD.format(str(self.capsule)))
            ucode_ver = self.get_ucode_ver()
            if (int(str(self.expected_ucode.upper()),16) >= int(str(ucode_ver.upper()),16)):
                self._log.info("Upgrade Ucode")
                self.run_ssh_command(SGXConstants.LIN_UCODE_UPGRADE_RELOAD)
            else:
                self._log.info("downgrade Ucode")
                self.run_ssh_command(SGXConstants.LIN_UCODE_DOWNGRADE_RELOAD)
        self._log.info("Ucode Patch Copied and reloaded")
        ucode_ver = self.get_ucode_ver()
        if(str(self.expected_ucode.upper()) == str(ucode_ver.upper())):
            self._log.info("Version Ucode is same as expected version")
        else:
            self._log.error("Version post SGX_checkupdate does not match expected ucode version")
            raise RuntimeError("SGXcheck Ucode version did not match expected version " + str(self.expected_ucode.upper()))
        return True
        
    def sgx_svnupdate(self):
        """
        Function to perform SVN update 
        :return TRUE on successful update
        """
        self._log.info("Running Sgx_VM for SVN update")
        if self._os_type != OperatingSystems.LINUX:
            #Need to recheck this dependency based on the latest Windows POC implementation.
            output = self.run_powershell_command(command=self.sgx_vm_command, get_output=True, echo_output=True)
            if 'Execution Succeeded' in output:
                self._log.info('SGX VM running')
            else:
                self._log.error('SGX VM failed')
                raise RuntimeError('SGX VM failed')
        self._log.info("Executing command for getting sgx_svnupdate ")
        if self._os_type != OperatingSystems.LINUX:
            output = self.run_powershell_command(command=self.sgx_svn_update_command, get_output=True, echo_output=True)
            if 'Execution Succeeded' in output:
                self._log.info('sgx_svn update successful')
            else:
                self._log.error('sgx_svn updatefailed')
                raise RuntimeError('sgx_svn update failed')
        else:
            self.run_ssh_command(SGXConstants.LIN_SVN_UPDATE)
            result = self.run_ssh_command(SGXConstants.DMESG_CMD,log_output=False)
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
        """
        Function to perform Ucode patch roll back 
        """
        self._log.info("Executing command for SGX rollback to original version")
        if self._os_type == OperatingSystems.LINUX:
            self.run_ssh_command(SGXConstants.LIN_UCODE_ROLLBACK)
        else:
            output = self.run_powershell_command(command=self.sgx_rollback_command, get_output=True, echo_output=True)
            if 'Execution Succeeded' in output:
                self._log.info('SGX rollback successful')
                return True
            else:
                self._log.error('SGX rollback failed')
                raise RuntimeError('SGX rollback failed')

    def launch_sgx_workload(self):
        """
        Function to launch sgx app workload
        """
        if (self.start_workload == True):
            self._log.info("launch app-workload")
            self.sut_ssh.execute_async(cmd=SGXConstants.SGX_LINUX_WORKLOAD, cwd=LinuxPath.LINUX_SGX_WORKLOAD_PATH)
        return True

    def kill_sgx_workload(self):
        """
        Function to kill sgx app workload
        """
        if (self.start_workload == True):
            self._log.info("kill app-workload")
            result = self.sut_ssh.execute(cmd=SGXConstants.LIN_GET_WORKLOAD_PID, timeout=TimeDelay.SYSTEM_TIMEOUT, cwd=LinuxPath.ROOT_PATH)
            self._log.info("app-workload PID = {}".format(result.stdout))
            pid_app_workload = re.findall("\d+", result.stdout)
            for line in pid_app_workload:
                result = self.sut_ssh.execute(cmd=SGXConstants.LIN_KILL_PID.format(line), timeout=TimeDelay.SYSTEM_TIMEOUT, cwd=LinuxPath.ROOT_PATH)
        return True

    def launch_sgx_vm(self):
        """
        Function to launch sgx vm 
        """
        self._log.info("Executing command for SGX VM's to launch a virtual machine")
        if self._os_type == OperatingSystems.LINUX:
            port = PortAllocation.SGX_VM_PORT
            for x in range(0, self.sgx_count):
                port += 1
                vm_cmd = "_"+str(x)
                self._log.info(SGXConstants.LIN_SGX_VM_CMD.format(vm_cmd,port))
                result = self.sut_ssh.execute_async(cmd=SGXConstants.LIN_SGX_VM_CMD.format(vm_cmd,port),cwd=LinuxPath.ROOT_PATH)
            time.sleep(TimeDelay.VM_CREATION_SLEEP_TIMEOUT)
            #Add code to verify the VM up time - Need SSHPASS packages installed.
            self._log.info("VM Launch process completed")
        else:
            self._log.info("windows OS WIP....")
        return True

       
    def handle_vm_process(self, option):
        """
        Function to verify the sgx vm count and kill the vm
        """
        result = self.sut_ssh.execute(cmd=SGXConstants.LIN_GET_QEMU_PID, timeout=TimeDelay.SYSTEM_TIMEOUT, cwd=LinuxPath.ROOT_PATH)
        self._log.info("vm process id detected == {}".format(result.stdout))
        vm_exe_count = re.findall("\d+", result.stdout)
        if (len(vm_exe_count) == self.sgx_count) and (option == "count"):
            self._log.info("Count of the running VM's {}".format(len(vm_exe_count)))
            return True
        elif (len(vm_exe_count) == self.sgx_count) and (option == "kill"):
            for line in vm_exe_count:
                self._log.info("vm process id terminated == {}".format(line))
                result = self.sut_ssh.execute(cmd=SGXConstants.LIN_KILL_PID.format(line), timeout=TimeDelay.SYSTEM_TIMEOUT, cwd=LinuxPath.ROOT_PATH)
            return True
        else:
            self._log.info("Expected number of sgx vm not created")
            return False
        
    def verify_attestation_status(self):
        """
        Function to verify the sgx enclave attestation status
        """
        if self._os_type == OperatingSystems.LINUX:
            self._log.info("Verifying the attestation status")
            result = self.sut_ssh.execute(cmd=SGXConstants.SGX_APP, timeout=TimeDelay.SYSTEM_TIMEOUT,cwd=LinuxPath.LINUX_LOCAL_ATTEST_SGX_APP_PATH)
            for line in result.stdout.splitlines():
                if not ('succeed' in line.lower()):
                    return False
        else:
            self._log.info("windows OS WIP....")
        return True

    def update_msr(self):
        """
        Function to override msr value
        """
        if self._os_type == OperatingSystems.LINUX:
            self._log.info("override msr value")
            result = self.sut_ssh.execute(cmd=SGXConstants.LIN_READ_MSR.format(hex(self.target_msr)), timeout=TimeDelay.SYSTEM_TIMEOUT,cwd=LinuxPath.ROOT_PATH)
            self._log.info("Read MSR Before Update: {}".format(result.stdout))
            self._log.info("MSR needs update: {}".format(hex(self.target_msr)))
            self._log.info("Override value : {}".format(hex(self.msr_update_value)))
            result = self.sut_ssh.execute(cmd=SGXConstants.LIN_WRITE_MSR.format(hex(self.target_msr),hex(self.msr_update_value)),timeout=TimeDelay.SYSTEM_TIMEOUT,cwd=LinuxPath.ROOT_PATH)
            result = self.sut_ssh.execute(cmd=SGXConstants.LIN_READ_MSR.format(hex(self.target_msr)), timeout=TimeDelay.SYSTEM_TIMEOUT,cwd=LinuxPath.ROOT_PATH)
            self._log.info("Read MSR After Update: {}".format(result.stdout))
        else:
            self._log.info("windows OS WIP....")
        return True

    def sgx_update(self):
        """
        Function to verify the sgx tcb recovery flow
        """
        self._log.info("Executing command for SGX update E2E with ucode patch: " + str(self.capsule))
        self.launch_sgx_vm()
        self.handle_vm_process(option="count")
        self.launch_sgx_workload()
        self.sgx_checkupdate()
        self.sgx_svnupdate()
        self.sgx_cleanup()
        self.warm_boot()
        self._log.info('SGX update E2E')
        return True

    def local_attestation(self):
        """
        Function to verify local attestation flow
        """
        output = False
        self._log.info("Validate the local attestation")
        output = self.verify_attestation_status()
        if (output == True):
            self.launch_sgx_vm()
            self.launch_sgx_workload()
            self.sgx_checkupdate()
            self.sgx_svnupdate()
            output = self.verify_attestation_status()
            self.sgx_cleanup()
        return output

    def enclave_before_svnupdate(self):
        """
        Function to verify the sgx tcb recovery flow
        """
        self._log.info("Executing command for SGX update E2E with ucode patch: " + str(self.capsule))
        self.sgx_checkupdate()
        self.launch_sgx_vm()
        self.launch_sgx_workload()
        self.sgx_svnupdate()
        self.sgx_cleanup()
        self.warm_boot()
        self._log.info('SGX update E2E')
        return True

    def enclave_after_svnupdate(self):
        """
        Function to verify the sgx tcb recovery flow
        """
        self._log.info("Executing command for SGX update E2E with ucode patch: " + str(self.capsule))
        self.sgx_checkupdate()
        self.sgx_svnupdate()
        self.launch_sgx_vm()
        self.launch_sgx_workload()
        self.sgx_cleanup()
        self.warm_boot()
        self._log.info('SGX update E2E')
        return True

    def clear_mci_ctl_register(self):
        """
        Function to verify the sgx tcb recovery flow
        """
        version = None
        self.launch_sgx_vm()
        self.handle_vm_process(option="count")
        version = self.get_svn_version()
        if (version != None):
            self.update_msr()
        version = self.get_svn_version()
        if (version == None):
            self.handle_vm_process(option="kill")
            return True
        else:
            return False

    def sgx_disabled(self):
        """
        Function to launch vm without SGX 
        """
        self._log.info("Executing command for VM to launch a virtual machine without sgx")
        if self._os_type == OperatingSystems.LINUX:
            port = PortAllocation.SGX_VM_PORT
            for x in range(0, self.vm_count):
                port += 1
                vm_cmd = "_"+str(x)
                self._log.info(SGXConstants.LIN_GEN_VM_CMD.format(vm_cmd,port))
                result = self.sut_ssh.execute_async(cmd=SGXConstants.LIN_GEN_VM_CMD.format(vm_cmd,port),cwd=LinuxPath.ROOT_PATH)
            time.sleep(TimeDelay.VM_CREATION_SLEEP_TIMEOUT)
            #Add code to verify the VM up time - Need SSHPASS packages installed.
            result = self.run_ssh_command(cmd=SGXConstants.LIN_CHECK_VM_STATUS.format(port),timeout_seconds=TimeDelay.VM_CREATION_SLEEP_TIMEOUT)
            if ('up' in result.stdout):
                self._log.info(result.stdout)
                result = self.run_ssh_command(cmd=SGXConstants.LIN_CHECK_VM_SGX_STATUS.format(port),timeout_seconds=TimeDelay.VM_CREATION_SLEEP_TIMEOUT)
                if ('sgx' in result.stdout):
                    self._log.info("SGX is not enumerated")
            else:
                self._log.info("VM is not live")
                return False 
            self._log.info("VM Launch process completed")
        else:
            self._log.info("windows OS WIP....")
        return True

    def sgx_update_without_rollback(self):
        """
        Function to perform patch specific updates
        """
        self.sgx_checkupdate()
        self.sgx_svnupdate()
        return True
        
    def sgx_cleanup(self):
        """
        Function to cleanup patches, workloads and vms
        """
        self.sgx_rollback()
        self.kill_sgx_workload()
        self.handle_vm_process(option="kill")
        return True

    def update_patch_versions(self, ucode_ver,svn_ver,capsule_ver):
        """
        Function to update patch versions
        """
        self.expected_ucode = ucode_ver
        self.expected_svn = svn_ver
        self.capsule = capsule_ver

    def sgx_update_in_series(self):
        """
        Function to perform series of patch updates
        """
        self._log.info("Executing series of SGX update")
        #Update N to N+1 version
        self.sgx_update_without_rollback()

        if (self.sgx_ucode_patch_count >= 2):
            #Update N+1 to N+2 version
            self.update_patch_versions(ucode_ver = self.expected_ucode2,svn_ver = self.expected_svn2,capsule_ver = self.capsule2)
            self.sgx_update_without_rollback()
            
        if (self.sgx_ucode_patch_count >= 3):
            #Update N+2 to N+3 version
            self.update_patch_versions(ucode_ver = self.expected_ucode3,svn_ver = self.expected_svn3,capsule_ver = self.capsule3)
            self.sgx_update_without_rollback()
        
        if (self.sgx_ucode_patch_count >= 4):
            #Update N+2 to N+3 version
            self.update_patch_versions(ucode_ver = self.expected_ucode4,svn_ver = self.expected_svn4,capsule_ver = self.capsule4)
            self.sgx_update_without_rollback()

        self.sgx_rollback()
        self.warm_boot()
        return True

    def sgx_loop(self):
        self._log.info("Executing command for SGX loop for linux")

        ucode1 = self.expected_ucode
        svn1 = self.expected_svn
        capsule1 = self.capsule

        current_ucode_version = self.get_ucode_ver()
        self._log.info("SUT Ucode current version {}".format(current_ucode_version))

        for x in range(self.loop_count):
            self.launch_sgx_vm()

            if self.start_workload:
                self._log.info("Starting app-workload")
                val = self.sut_ssh.execute_async(cmd=SGXConstants.SGX_LINUX_WORKLOAD, cwd=LinuxPath.LINUX_SGX_WORKLOAD_PATH)

            self.update_patch_versions(ucode_ver = ucode1,svn_ver = svn1,capsule_ver = capsule1)
            self.sgx_checkupdate()
            self.sgx_svnupdate()

            self.update_patch_versions(ucode_ver = self.expected_ucode2,svn_ver = self.expected_svn2,capsule_ver = self.capsule2)
            self.sgx_checkupdate()
            self.sgx_svnupdate()

            self.update_patch_versions(ucode_ver = self.expected_ucode3,svn_ver = self.expected_svn3,capsule_ver = self.capsule3)
            self.sgx_checkupdate()
            self.sgx_svnupdate()

            if self.warm_reset:
                self.warm_boot()
                self.expected_ucode = self.expected_ucode3
                self.expected_svn = self.expected_svn3
                self._log.info("expected ucode after reboot {}".format(self.expected_ucode))
                self._log.info("expected svn after reboot {}".format(self.expected_svn))
                self.expected_ucode = self.expected_ucodebase
                self.expected_svn = self.expected_svnbase
                self.sgx_rollback()
                self.warm_boot()
           
            if self.dc_cycle:
                self.cold_boot()
                self.expected_ucode = self.expected_ucode3
                self.expected_svn = self.expected_svn3
                self._log.info("expected ucode after reboot {}".format(self.expected_ucode))
                self._log.info("expected svn after reboot {}".format(self.expected_svn))
                self.expected_ucode = self.expected_ucodebase
                self.expected_svn = self.expected_svnbase
                self.sgx_rollback()
                self.cold_boot()

            self._log.info("Automated  test  Loop number :" + str(x + 1))
        return True

    def warm_boot(self):
        """
        Function to perform warm reboot
        """
        self._log.info("\tWarm reset the system")

        if self._os_type != OperatingSystems.LINUX and not self.sut_ssh.is_alive():
                self.run_powershell_command(command=self.restart_sut_command, get_output=True)
        else:
            self._log.info("\t reboot through SSH")
            self.sut_ssh.reboot(timeout=TimeDelay.REBOOT_OS_TIMEOUT)
        return True

    def cold_boot(self):
        """
        Function to perform cold reboot
        """
        self._log.info("\tCold boot the system")
        self.os.shutdown(self.DC_POWER_DELAY)
        self._log.info("System entered into S5 state, waiting for SUT to settle down..")
        time.sleep(self.SUT_SETTLING_TIME)
        self._dc_power.dc_power_on(timeout=TimeDelay.VM_STABLE_TIMEOUT)
        self.os.wait_for_os(TimeDelay.REBOOT_OS_TIMEOUT)


    def perform_sgx_tcb_recovery(self):
        """
        Function to perform sgx tcb recovery 
        """
        result = False
        self._log.info("SGX TCB execution function")

        if(self.sgx_command == "sgx_update"):
            self._log.info("Execute the sgx_udpate")
            result = self.sgx_update()
                
        elif(self.sgx_command == "svn_ver"):
            self._log.info("Execute the get_svn_version")
            version = self.get_svn_version()
            if (version != None):
                result = True
                
        elif(self.sgx_command == "sgx_checkupdate"):
            self._log.info("Execute the sgx_checkupdate")
            result = self.sgx_checkupdate()
                
        elif(self.sgx_command == "sgx_svnupdate"):
            self._log.info("Execute the sgx_svnupdate")
            result = self.sgx_svnupdate()
                
        elif(self.sgx_command == "sgx_rollback"):
            self._log.info("Execute the sgx_rollback")
            result = self.sgx_rollback()

        elif(self.sgx_command == "local_attestation"):
            self._log.info("local_attestation")
            result = self.local_attestation()

        elif(self.sgx_command == "enclave_before_svnupdate"):
            self._log.info("enclave_before_svnupdate")
            result = self.enclave_before_svnupdate()

        elif(self.sgx_command == "enclave_after_svnupdate"):
            self._log.info("enclave_after_svnupdate")
            result = self.enclave_after_svnupdate() 

        elif(self.sgx_command == "sgx_update_in_series"):
            self._log.info("sgx_update_in_series")
            result = self.sgx_update_in_series()  
            
        elif(self.sgx_command == "clear_mci_ctl_register"):
            self._log.info("clear_mci_ctl_register")
            result = self.clear_mci_ctl_register()
            if (result == True):
                self.warm_boot()

        elif(self.sgx_command == "sgx_loop"):
            self._log.info("execute sgx loop")
            result = self.sgx_loop()

        elif(self.sgx_command == "sgx_disabled"):
            self._log.info("check sgx status within VM")
            result = self.sgx_loop()

        else:
            raise RuntimeError("sgx_command was not set as one of the options: sgx_update, sgx_checkupdate, sgx_svnupdate, sgx_rollback, launch_sgx_workload")
            result = False

        return result


