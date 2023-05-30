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
import os
import time
import random
import re
import random
from datetime import datetime, timedelta
from warnings import resetwarnings
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest
from src.seamless.lib.seamless_common import SeamlessBaseTest, ThreadWithReturn


class SEAM_BMC_0013_prm_update(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0013_prm_update, self).__init__(test_log, arguments, cfg_opts)
        self.expected_ver = arguments.expected_ver
        self.expected_ver2 = arguments.expected_ver2
        self.flash_type = arguments.flash_type
        self.flow_type = arguments.flow_type
        self.start_workload = arguments.start_workload
        self.warm_reset = False
        self.prm_handler = arguments.prm_handler
        self.prm_path = arguments.prm_path
        self.capsule = arguments.capsule
        self.handler = arguments.handler
        self.loop_count = arguments.loop
        self.min_delay = arguments.min_delay
        self.max_delay = arguments.max_delay
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.prm_handler_command = self._workload_path + "PRMTestFlow.ps1 " + self._powershell_credentials
        self.update_prm_handler_command = self._workload_path + "PRMUpdate.ps1 " + self._powershell_credentials
        self.cleanup_prm_handler_command = self._workload_path + "PRMCleanup.ps1 " + self._powershell_credentials
        self.ping_sut_command = self._workload_path + "PingSut.ps1 " + self._powershell_credentials
        self.restart_sut_command = self._workload_path + "RestartSut.ps1 " + self._powershell_credentials
        self.regedit_command = self._workload_path + "Regedit.ps1 " + self._powershell_credentials
        self.prm_lock_command = self._workload_path + "Prm_lock.ps1 " + self._powershell_credentials
        self.prm_unlock_command = self._workload_path + "Prm_unlock.ps1 " + self._powershell_credentials
        self.prm_valid_capsule_same_ver = arguments.prm_valid_capsule_same_ver
        self.prm_valid_capsule_higher_ver = arguments.prm_valid_capsule_higher_ver
        self.prm_valid_capsule_lower_ver = arguments.prm_valid_capsule_lower_ver
        self.prm_valid_capsule_warm_reboot = arguments.prm_valid_capsule_warm_reboot
        self.prm_valid_capsule_ac_cycle = arguments.prm_valid_capsule_ac_cycle
        self.verify_prm_table_capability = arguments.verify_prm_table_capability
        self.corrupted_prm_header = arguments.corrupted_prm_header
        self.out_of_bounds_prm = arguments.out_of_bounds_prm
        self.garbage_load_prm = arguments.garbage_load_prm
        self.verify_prm_single_entry_handler = arguments.verify_prm_single_entry_handler
        self.verify_prm_flow_pre_update = arguments.verify_prm_flow_pre_update
        self.verify_prm_flow_post_update = arguments.verify_prm_flow_post_update
        self.prm_end_to_end_flow_for_address_translation = arguments.prm_end_to_end_flow_for_address_translation
        self.prm_registry_key_check = arguments.prm_registry_key_check
        self.atomic_operation = arguments.atomic_operation
        self.no_prm_table = arguments.no_prm_table
        self.prm_with_bios = arguments.prm_with_bios
        self.warm_reset = arguments.warm_reset
        self.capsule_path = arguments.capsule_path
        self.capsule_path2 = arguments.capsule_path2
        self.capsule_name = arguments.capsule_name
        self.capsule_name2 = arguments.capsule_name2
        self.invocation_time = None
        self.total_iter = 0
        self.update_time = None
        self.skip_reset = False
        self.activation = False
        self.total_iter = 0
        self.update_type = arguments.update_type
        self.sps_mode = arguments.sps_mode
        self.loop_count = arguments.loop
        self.acpi= arguments.acpi
        self.KPI = 1000 # PRM Invocation KPI is less than 1 second. 

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0013_prm_update, cls).add_arguments(parser)
        parser.add_argument('--flash_type', action='store', help="expected flash type to run the particular TC",default="")
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update",default="")
        parser.add_argument('--expected_ver2', action='store',help="The version expected to be reported after update of capsule2", default="")
        parser.add_argument('--flow_type', action='store', help="The type of flow for ucode update", default="")  #(invoke, update)
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--prm_handler', action='store', help="The prm handler to be invoked/updated", default="p1")
        parser.add_argument('--prm_path', action='store', help='The prm tool path')
        parser.add_argument('--capsule', action='store', help='The capsule image')
        parser.add_argument('--handler', action='store', help='The prm handler to be invoked using OS wrapper tool', default="")
        parser.add_argument('--update_type', action='store', help="Specify if efi utility, fit ucode, inband", default="fit_ucode")
        parser.add_argument('--prm_valid_capsule_same_ver',
                            action='store_true',
                            help="Add argument for sending valid PRM capsule with same version",
                            default="")
        parser.add_argument('--prm_valid_capsule_higher_ver',
                            action='store_true',
                            help="Add argument for sending valid PRM capsule with higher version",
                            default="")
        parser.add_argument('--prm_valid_capsule_lower_ver',
                            action='store_true',
                            help="Add argument for sending valid PRM capsule with lower version",
                            default="")
        parser.add_argument('--prm_valid_capsule_warm_reboot',
                            action='store_true',
                            help="Add argument for sending valid PRM capsule and give a warm reboot",
                            default="")
        parser.add_argument('--prm_valid_capsule_ac_cycle',
                            action='store_true',
                            help="Add argument for sending valid PRM capsule and reboot system using ac cycle",
                            default="")
        parser.add_argument('--verify_prm_table_capability',
                            action='store_true',
                            help="Add argument for verifying the capability of prm table is exposed correctly",
                            default="")
        parser.add_argument('--corrupted_prm_header',
                            action='store_true',
                            help="Add argument for sending a PRM capsule capsule containing a corrupted PRM header",
                            default="")
        parser.add_argument('--out_of_bounds_prm',
                            action='store_true',
                            help="Add argument for sending a PRM capsule capsule containing a upper size of a PRM handler",
                            default="")
        parser.add_argument('--garbage_load_prm',
                            action='store_true',
                            help="Add argument for sending a PRM capsule capsule containing a garbageload PRM handler",
                            default="")
        parser.add_argument('--verify_prm_single_entry_handler',
                            action='store_true',
                            help="Add argument for verifying whether the PRM single entry handler setup is successfull",
                            default="")
        parser.add_argument('--verify_prm_flow_pre_update',
                            action='store_true',
                            help="Add argument for verifying PRM flow can be invoked pre-update",
                            default="")
        parser.add_argument('--verify_prm_flow_post_update',
                            action='store_true',
                            help="Add argument for verifying PRM flow can be invoked post-update",
                            default="")
        parser.add_argument('--prm_registry_key_check',
                            action='store_true',
                            help="Add argument for verifying PRM flow can be invoked post-update",
                            default="")
        parser.add_argument('--prm_end_to_end_flow_for_address_translation',
                            action='store_true',
                            help="Add argument for excercising end to end flow for the included prm address translation handler",
                            default="")
        parser.add_argument('--atomic_operation',
                            action='store_true',
                            help="Add argument for sending a PRM capsule update while an atomic operation is in progress",
                            default="")
        parser.add_argument('--loop', type=int, default=1, help="Add argument for # of loops")
        parser.add_argument('--no_prm_table',
                            action='store_true',
                            help="Add argument for sending a PRM capsule update fails because no PRM Table is present",
                            default="")
        parser.add_argument('--prm_with_bios',
                            action='store_true',
                            help="Add argument for Performing a PRM update then update to a BIOS with a newer PRM version",
                            default="")
        parser.add_argument('--capsule_path', action='store', help="Path to the capsule to be used for the update",
                            default="")
        parser.add_argument('--capsule_path2', action='store', help="Path to the capsule to be used for the update",
                            default="")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--capsule_name', action='store', help="Name of the capsule to be used for the update",
                            default="")
        parser.add_argument('--capsule_name2', action='store', help="Name of the capsule to be used for the update",
                            default="")
        parser.add_argument('--min_delay', action='store', help="Sets the minimum delay to wait between PRM runs in"
                                                                "seconds (default: 0).")
        parser.add_argument('--max_delay', action='store', help='Sets the maximum delay to wait between PRM runs in'
                                                                'seconds. If specified, delay will be random.')
        parser.add_argument('--acpi', action='store_true', help="Cheking the ACPI PRTM Table and verigy the signature and other components", default="")

    def check_capsule_pre_conditions(self):
        return True

    def evaluate_workload_output(self, output):
        return True

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
        #tbd fucntion to read current prm status
        return version

    def invoke_prm_handler(self):
        output = self.run_powershell_command(command=self.prm_handler_command + " '-" + self.prm_handler + "'", get_output=True, echo_output=True)
        if 'Wrong input parameter' in output:
            result = False
            raise RuntimeError('Input handler is incorrect')
        else:
            self.Parse_Invocation_Output(output)
            result = True
            self._log.info('PRM Handler invocation successful: check memory table for output')

        return result

    def invoke_prm_handler_os_wrapper(self,handler = None):
        if handler == None:
            if (self.handler == 'dummy'):
                cmd = "rt_prm"
            elif (self.handler == "addrtrans"):
                cmd = "rt_addrtrans"
            else:
                raise RuntimeError("Input argument value for handler is incorrect")
        else:
            if (handler == 'dummy'):
                cmd = "rt_prm"
            elif (handler == "addrtrans"):
                cmd = "rt_addrtrans"
            else:
                raise RuntimeError("Input argument value for handler is incorrect")

        output = self.run_powershell_command(command=self.prm_handler_command + " " + cmd, get_output=True, echo_output=True)
        if 'Execution Failed' not in output:
            self.Parse_Invocation_Output(output)
            result = True
            if handler == None:
                if (self.handler == "addrtrans"):
                    self._log.info('PRM Addrtrans Handler invocation successful: check memory table for output')
                elif (self.handler == 'dummy'):
                    self._log.info('PRM Dummy Handler invocation successful: check memory table for output')
                else:
                    raise RuntimeError("Input argument value for handler is incorrect")
            else:
                if (handler == "addrtrans"):
                    self._log.info('PRM Addrtrans Handler invocation successful: check memory table for output')
                elif (handler == 'dummy'):
                    self._log.info('PRM Dummy Handler invocation successful: check memory table for output')
                else:
                    raise RuntimeError("Input argument value for handler is incorrect")
        else:

            result = False
            self._log.error('PRM Invoke Handler failed')
            raise RuntimeError("PRM Invoke Handler failed")

        return result

    def update_prm_handler(self):
        time_start = datetime.now()
        output = self.run_powershell_command(command=self.update_prm_handler_command + " " + self.capsule, get_output=True, echo_output=True)
        self.update_time = datetime.now() - time_start
        result = True
        self._log.info('PRM handler update executed: check memory tool for version')
        return result

    def update_prm_handler_os_wrapper(self):
        time_start = datetime.now()
        output = self.run_powershell_command(command=self.update_prm_handler_command, get_output=True, echo_output=True)
        self.update_time = datetime.now() - time_start
        self._log.info('PRM handler update executed: check memory tool for version')
        # if('PRM Handler Update Complete' in output):
        # self.update_time = datetime.now() - time_start
        # result = True
        # self._log.info('PRM handler update executed: check memory tool for version')
        # else:
        # result = False
        # self._log.error('PRM handler update failed')
        # raise RuntimeError("PRM handler update failed")
        return True

    def prm_cleanup(self):
        result = False
        self._log.info("Clean previous PRM update")
        output = self.run_powershell_command(command=self.cleanup_prm_handler_command, get_output=True, echo_output=True)
        self._log.info("PRM cleanup complete, restarting the system")
        self.warm_reset = True
        output = self.block_until_complete(None)
        result = True
        #to-do uncomment following after windows OS change
        # if 'PRM Update is cleaned up. Please reboot' in output:
        # self._log.info('PRM update cleanup was successful. Rebooting system')
        # self.warm_reset = True
        # output = self.block_until_complete(None)
        # result = True

        # else:
        # self._log.error("PRM cleanup failed")
        # result = False
        # raise RuntimeError("PRM cleanup failed")

        return result
        # Determine Delay
    # Determine Delay
    def get_delay(self):
        # Convert to floats
        min_delay = None
        max_delay = None
        if self.min_delay is not None:
            min_delay = float(self.min_delay)
        if self.max_delay is not None:
            max_delay = float(self.max_delay)

        # Generate delay count
        random.seed(datetime.now())
        if min_delay is not None and max_delay is not None:
            return random.uniform(min_delay, max_delay)
        elif min_delay is not None:
            return min_delay
        elif max_delay is not None:
            return max_delay

        return 0

    def base_address_with_offset(self,offset=0xDE):
        acpi_dump = self.run_ssh_command("\"C:\\Program Files\\RW-Everything\\Rw.exe\" /Command=\"ACPI Dump PRMT;RWExit\" /Stdout")
        print(acpi_dump.stderr)
        base_address_found = re.search("PRMT Table: +(0x[0-9A-Fa-f]+)", acpi_dump.stdout)
        if not base_address_found:
            self._log.error("Base Address of PRMT Table not found")
            return False
        base_address = int(base_address_found.group(1), 16)
        base_address_with_offset = hex(base_address + offset)
        return base_address_with_offset

    def verify_prmt_table_fields(self):
        acpi_dump = self.run_ssh_command("\"C:\\Program Files\\RW-Everything\\Rw.exe\" /Command=\"ACPI Dump PRMT;RWExit\" /Stdout")
        prmt_table_field1 = re.search("Signature\s\"PRMT\"", acpi_dump.stdout)
        prmt_table_field2 = re.search("OEM ID\s\"INTEL \"", acpi_dump.stdout)
        prmt_table_field3 = re.search("OEM Table ID\s\"INTEL ID\"", acpi_dump.stdout)
        prmt_table_field4 =  re.search("Creator ID\s\"INTL\"", acpi_dump.stdout)
        if prmt_table_field1 and prmt_table_field2 and prmt_table_field3 and prmt_table_field4:
            return True
        else:
            return False
            
    def dummy_handler_base_address(self):
        dummy_handler_response = self.run_ssh_command("\"C:\\Program Files\\RW-Everything\\Rw.exe\" /Command=\"R32 {};RWExit\" /Stdout".format(
            self.base_address_with_offset(0xDE)))
        dummy_handler_base_address_found = re.search("Read Memory Address .+ = (0x[0-9A-Fa-f]+)", dummy_handler_response.stdout)
        if not dummy_handler_base_address_found:
            self._log.error("Base Address of dummy handler not found")
            return False
        dummy_handler_base_address = dummy_handler_base_address_found.group(1)
        return dummy_handler_base_address

    def address_translation_base_address(self,offset=0x130):
        address_translation_response = self.run_ssh_command("\"C:\\Program Files\\RW-Everything\\Rw.exe\" /Command=\"R32 {};RWExit\" /Stdout".format(
            self.base_address_with_offset(offset)))
        address_translation_base_address_found = re.search("Read Memory Address .+ = (0x[0-9A-Fa-f]+)", address_translation_response.stdout)
        if not address_translation_base_address_found:
            self._log.error("Base Address of address translation not found")
            return False
        address_translation_base_address = address_translation_base_address_found.group(1)
        return address_translation_base_address

    def dummy_handler_version_1_x(self, minor_version):
        dummy_handler_version_response = self.run_ssh_command("\"C:\\Program Files\\RW-Everything\\Rw.exe\" /Command=\"DMEM {};RWExit\" /Stdout".format(
            self.dummy_handler_base_address()))
        dummy_handler_version = dummy_handler_version_response.stdout.splitlines()
        handler_version_part1 = re.search("v.i.c.e. .v.1...", dummy_handler_version[6])
        handler_version_part2 = re.search("{}...............".format(minor_version), dummy_handler_version[7])
        if handler_version_part1 and handler_version_part2:
            return True
        else:
            return False
    
    def validate_address_translation_contents(self):
        address_translation_response = self.run_ssh_command("\"C:\\Program Files\\RW-Everything\\Rw.exe\" /Command=\"DMEM {};RWExit\" /Stdout".format(
        self.address_translation_base_address()))
        address_translation_value = address_translation_response.stdout.splitlines()
        response = sum([len(re.findall("AF",line)) for line in address_translation_value])
        return response == 252
        
    def address_translation_offset_value_check(self,offset):
        offset_added_value = hex(int(self.address_translation_base_address(),16)+int(offset,16))
        print(offset_added_value)
        address_translation_response = self.run_ssh_command("\"C:\\Program Files\\RW-Everything\\Rw.exe\" /Command=\"R32 {};RWExit\" /Stdout".format(
            str(offset_added_value)))
        self._log.info("address_translation_response1: {}".format(address_translation_response.stdout))
        address_translation_base_address_found = re.search("Read Memory Address .+ = (0x[0-9A-Fa-f]+)", address_translation_response.stdout)
        print("address_translation_base_address_found: {}".format(address_translation_base_address_found))
        return address_translation_base_address_found.group(1)
    
    def check_KPI(self):
        if self._os_type != OperatingSystems.LINUX:
           if (int(float(self.invocation_time)) > self.KPI):
               self._log.info('PRM Invocation time:   {0:>15}'.format(self.invocation_time))
               warnings.warn("Invocation time is greater than " + str(self.KPI) + "Sec")
           else:
               self._log.info("PRM Invocation time bound to KPI metrics")
           self._log.info("Invocation time: " + str(self.invocation_time))
        else: 
            self._log.info("support to add PRM KPI values yet to be added in Linux")

    def Parse_Invocation_Output(self,output):
        for line in output.splitlines():
            if ('Process Time' in line):
               self.invocation_time = line.split(':')[1]
        if (self.invocation_time == None ):
                self._log.info('PRM KPI support missing in windows automation script, KPI validation skipped')
        else:
                self.check_KPI()
     
    def prm_handler_invocation_loop(self,flow_type,handler):

        if self.start_workloads:
                self.summary_log.info("\tStart workloads: " + str(self.start_workloads))
                self._log.info("\tStarting workloads, wait two minutes till workloads stabilize...")
                self.begin_workloads()

        if flow_type == 'update':
            for x in range(self.loop_count):
                self._log.info('Start of iteration ' + str(x + 1))
                # self.invoke_prm_handler_os_wrapper()
                self.update_prm_handler_os_wrapper()
                # self.invoke_prm_handler_os_wrapper()
                self._log.info('End of iteration ' + str(x + 1) + ': Check PRM version in RW tool')
                self.total_iter = x + 1
                self._log.info('Rollback before next iteration: ')
                result = self.prm_cleanup()
                time.sleep(self.get_delay())

        elif flow_type == 'invoke':
            for x in range(self.loop_count):
                self._log.info('Start of iteration ' + str(x + 1))
                result = self.invoke_prm_handler_os_wrapper(handler)
                self._log.info('End of iteration ' + str(x + 1) + ': Check PRM version in RW tool')
                self.total_iter = x + 1
                time.sleep(self.get_delay())

        return result

    def post_prm_cleanup(self):
        prm_cleanup = self.run_ssh_command("powershell -File C:\\Windows\\System32\\SeamlessupdateToolbox.ps1 -configuresystem -configname \"prmcleanup\"")
        self._log.info(prm_cleanup.stdout)
        self.os.reboot(self.WARM_RESET_TIMEOUT)

    def prm_update_atomic(self, capsule):
        if capsule == "PrmSamplePrintModule1.1.efi":
            prm_update = self.run_ssh_command("cd C:\\Windows\\System32\\ && prmupdatesvc.exe -update " + capsule)
            if "Update Failed" in prm_update.stdout:
                self._log.info("PRM Update desired output Failed")
                return True
            else:
                self._log.info("PRM Update returned undesired output")
                return False

    def prm_update(self, capsule):
        if capsule == "PrmSamplePrintModule1.1.efi":
            prm_update = self.run_ssh_command("cd C:\\Windows\\System32\\ && prmupdatesvc.exe -update " + capsule)
            if "Update Successful" in prm_update.stdout:
                self._log.info("PRM Update successfull")
                return True
            else:
                self._log.info("PRM Update failed")
                return False
        elif capsule == "PrmSamplePrintModule0.9.efi":
            prm_update = self.run_ssh_command("cd C:\\Windows\\System32\\ && prmupdatesvc.exe -update " + capsule)
            if "Update Failed" in prm_update.stdout:
                self._log.info("PRM Update desired output Failed")
                return True
            else:
                self._log.info("PRM Update returned undesired output")
                return False
        elif capsule == "PrmSamplePrintBadHdrv11.efi":
            prm_update = self.run_ssh_command("cd C:\\Windows\\System32\\ && prmupdatesvc.exe -update " + capsule)
            if "Update Failed" in prm_update.stdout:
                self._log.info("PRM Update desired output Failed")
                return True
            else:
                self._log.info("PRM Update returned undesired output")
                return False
        elif capsule == "PrmSamplePrintModule1.1large.efi":
            prm_update = self.run_ssh_command("cd C:\\Windows\\System32\\ && prmupdatesvc.exe -update " + capsule)
            if "Update Failed" in prm_update.stdout:
                self._log.info("PRM Update desired output Failed")
                return True
            else:
                self._log.info("PRM Update returned undesired output")
                return False
        elif capsule == "PrmSamplePrintv09.efi":
            prm_update = self.run_ssh_command("cd C:\\Windows\\System32\\ && prmupdatesvc.exe -update " + capsule)
            if "Update Failed" in prm_update.stdout:
                self._log.info("PRM Update desired output Failed")
                return True
            else:
                self._log.info("PRM Update returned undesired output")
                return False
    def execute(self):

        result = False

        if self.capsule_name != "":
            self.capsule_path = self.find_cap_path(self.capsule_name)
            self._log.info("capsule path {}".format(self.capsule_path))
        if self.capsule_name2 != "":
            self.capsule_path2 = self.find_cap_path(self.capsule_name2)
            self._log.info("capsule path2 {}".format(self.capsule_path2))

        if self.prm_valid_capsule_same_ver:
            """
            TC 67481.7 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --prm_valid_capsule_same_ver

            """

            self.flow_type = "invoke"
            self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return self.post_prm_cleanup()
            if not self.prm_update("PrmSamplePrintModule1.1.efi"):
                return self.post_prm_cleanup()
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            if self.dummy_handler_version_1_x(1):
                self._log.info("PRM dummy handler version updated to 1.1")
            else:
                return self.post_prm_cleanup()
            if self.prm_update("PrmSamplePrintModule1.1.efi"):
                return self.post_prm_cleanup()
            self.post_prm_cleanup()
            return result

        elif self.prm_valid_capsule_higher_ver:
            """
            TC 67368.4 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --prm_valid_capsule_higher_ver

            """
            self.flow_type = "invoke"
            self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return self.post_prm_cleanup()
            if not self.prm_update("PrmSamplePrintModule1.1.efi"):
                return self.post_prm_cleanup()
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            if self.dummy_handler_version_1_x(1):
                self._log.info("PRM dummy handler version updated to 1.1")
            else:
                return self.post_prm_cleanup()
            self.post_prm_cleanup()
            return result
        
        elif self.prm_valid_capsule_lower_ver:
            """
            TC 67369.7 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --prm_valid_capsule_lower_ver

            """
            self.flow_type = "invoke"
            self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return self.post_prm_cleanup()
            if not self.prm_update("PrmSamplePrintModule0.9.efi"):
                return self.post_prm_cleanup()
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return self.post_prm_cleanup()
            if not self.prm_update("PrmSamplePrintModule1.1.efi"):
                return self.post_prm_cleanup()
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            if self.dummy_handler_version_1_x(1):
                self._log.info("PRM dummy handler version updated to 1.1")
            else:
                return self.post_prm_cleanup()
            self.post_prm_cleanup()
            return result

        elif self.prm_valid_capsule_warm_reboot:
            """
            TC 67371.5 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --prm_valid_capsule_warm_reboot
            """

            self.flow_type = "invoke"
            self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return self.post_prm_cleanup()
            if not self.prm_update("PrmSamplePrintModule1.1.efi"):
                return self.post_prm_cleanup()
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            if self.dummy_handler_version_1_x(1):
                self._log.info("PRM dummy handler version updated to 1.1")
            else:
                return self.post_prm_cleanup()
            self._log.info("System performing Warm reboot ")
            self.run_powershell_command(command=self.restart_sut_command, get_output=True, echo_output=True)
            self._log.info("Waiting for OS to come alive")
            self.os.wait_for_os(self.reboot_timeout)
            time.sleep(60)
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            time.sleep(60)
            if self.dummy_handler_version_1_x(1):
                self._log.info("PRM dummy handler version updated to 1.1")
            else:
                return self.post_prm_cleanup()
            self.post_prm_cleanup()
            return result

        elif self.prm_valid_capsule_ac_cycle:
            """
            TC 67370.4 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --prm_valid_capsule_ac_cycle

            """
            self.flow_type = "invoke"
            self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return self.post_prm_cleanup()
            if not self.prm_update("PrmSamplePrintModule1.1.efi"):
                return self.post_prm_cleanup()
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            if self.dummy_handler_version_1_x(1):
                self._log.info("PRM dummy handler version updated to 1.1")
            else:
                return self.post_prm_cleanup()
            if self.os.is_alive():
                self._log.info("System about to turn off for ac cycle")
                time.sleep(60)
                self.ac_power.ac_power_off()
                self._log.info("System turned off")
                time.sleep(100)
                self.ac_power.ac_power_on()
                self._log.info("System turned on. Waiting for OS to come alive")
                self.os.wait_for_os(self.reboot_timeout)
                time.sleep(60)
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            time.sleep(30)
            if self.dummy_handler_version_1_x(1):
                self._log.info("PRM dummy handler version updated to 1.1")
            else:
                return self.post_prm_cleanup()
            self.post_prm_cleanup()
            return result
        
        elif self.verify_prm_table_capability:
            """
            TC 67374.5 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --verify_prm_table_capability
            """
            
            self.flow_type = "invoke"
            self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return self.post_prm_cleanup()
            if self.verify_prmt_table_fields():
                self._log.info("Following PRMT Table fields verified:")
                self._log.info("Signature \"PRMT\"")
                self._log.info("OEM ID \"INTEL \"")
                self._log.info("OEM Table ID \"INTEL ID\"")
                self._log.info("Creator ID \"INTL\"")
            else:
                return self.post_prm_cleanup()
            if self.validate_address_translation_contents():
                self._log.info("Address Translation handler's contents is 0xAF")
            else:
                return self.post_prm_cleanup()
            if not self.prm_update("PrmSamplePrintModule1.1.efi"):
                return self.post_prm_cleanup()
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            time.sleep(60)
            if self.dummy_handler_version_1_x(1):
                self._log.info("PRM dummy handler version updated to 1.1")
            else:
                return self.post_prm_cleanup()
            if self.verify_prmt_table_fields():
                self._log.info("Following PRMT Table fields verified:")
                self._log.info("Signature \"PRMT\"")
                self._log.info("OEM ID \"INTEL \"")
                self._log.info("OEM Table ID \"INTEL ID\"")
                self._log.info("Creator ID \"INTL\"")
            else:
                return self.post_prm_cleanup()
            if self.validate_address_translation_contents():
                self._log.info("Address Translation handler's contents is 0xAF")
            else:
                return self.post_prm_cleanup()
            self.post_prm_cleanup()
            return result

        elif self.verify_prm_single_entry_handler:
            """
            TC 67375.4 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --verify_prm_single_entry_handler

            """
            self.flow_type = "invoke"
            self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return self.post_prm_cleanup()
            if not self.prm_update("PrmSamplePrintModule1.1.efi"):
                return self.post_prm_cleanup()
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            if self.dummy_handler_version_1_x(1):
                self._log.info("PRM dummy handler version updated to 1.1")
            else:
                return self.post_prm_cleanup()
            self.post_prm_cleanup()
            return result
        
        elif self.verify_prm_flow_pre_update:
            """
            TC 67376.3 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --verify_prm_flow_pre_update

            """
            self.flow_type = "invoke"
            self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return self.post_prm_cleanup()
            if self.invoke_prm_handler_os_wrapper():
                self._log.info("PRM invoke dummy handler Successfull")
                self.flow_type = "invoke"
                self.handler = "addrtrans"
                addr_trans_invoke = self.invoke_prm_handler_os_wrapper()
                self._log.info("PRM invoke addrtrans handler Successfull")
                if not addr_trans_invoke:
                    self._log.info("Address translation invoke failed")
                    return self.post_prm_cleanup()
            else:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            self.post_prm_cleanup()
            return True

        elif self.verify_prm_flow_post_update:
            """
            TC 67376.3 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --verify_prm_flow_post_update

            """
            self.flow_type = "invoke"
            self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return self.post_prm_cleanup()
            if not self.prm_update("PrmSamplePrintModule1.1.efi"):
                return self.post_prm_cleanup()
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            if self.dummy_handler_version_1_x(1):
                self._log.info("PRM dummy handler version updated to 1.1")
            else:
                return self.post_prm_cleanup()
            if self.invoke_prm_handler_os_wrapper():
                self._log.info("PRM invoke dummy handler Successfull")
                self.flow_type = "invoke"
                self.handler = "addrtrans"
                addr_trans_invoke = self.invoke_prm_handler_os_wrapper()
                self._log.info("PRM invoke addrtrans handler Successfull")
                if not addr_trans_invoke:
                    self._log.info("Address translation invoke failed")
                    return self.post_prm_cleanup()
            else:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            self.post_prm_cleanup()
            return True

        elif self.prm_end_to_end_flow_for_address_translation:
            """
            TC 67379.4 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --prm_end_to_end_flow_for_address_translation

            """
            self.flow_type = "invoke"
            self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return self.post_prm_cleanup()
            if not self.prm_update("PrmSamplePrintModule1.1.efi"):
                return self.post_prm_cleanup()
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            if self.dummy_handler_version_1_x(1):
                self._log.info("PRM dummy handler version updated to 1.1")
            else:
                return self.post_prm_cleanup()
            self.flow_type = "invoke"
            self.handler = "addrtrans"
            addr_trans_invoke = self.invoke_prm_handler_os_wrapper()
            if not addr_trans_invoke:
                self._log.info("Address translation invoke failed")
                return self.post_prm_cleanup()
            if self.address_translation_offset_value_check("0x04") == "0x00000002":
                self._log.info("0x04 offset and value matching Correct")
                if  self.address_translation_offset_value_check("0x0C") == "0x01000000":
                    self._log.info("0x0C offset and value matching Correct")
                    self.post_prm_cleanup()
                    return True
                else:
                    self.post_prm_cleanup()
            else:
                self.post_prm_cleanup()


        elif self.corrupted_prm_header:
            """
            TC 69565.1 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --corrupted_prm_header

            """
            self.flow_type = "invoke"
            self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return False
            if not self.prm_update("PrmSamplePrintBadHdrv11.efi"):
                return False
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return False
                self.post_prm_cleanup()
            return result

        elif self.out_of_bounds_prm:
            """
            TC 69566.1 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --out_of_bounds_prm

            """
            self.flow_type = "invoke"
            self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return False
            if not self.prm_update("PrmSamplePrintModule1.1large.efi"):
                return False
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return False
                self.post_prm_cleanup()
            return result

        elif self.garbage_load_prm:
            """
            TC 69557.1 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --garbage_load_prm

            """
            self.flow_type = "invoke"
            self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return False
            if not self.prm_update("PrmSamplePrintv09.efi"):
                return False
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return False
                self.post_prm_cleanup()
            return result

        elif self.atomic_operation:
            """
            TC 67384.4 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --atomic_operation --loop

            """
            self.flow_type = "invoke"
            self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return self.post_prm_cleanup()
            self._log.info("Locking out PRM updates...")
            prm_lock = self.run_powershell_command(command=self.prm_lock_command, get_output=True,echo_output=True)
            self._log.info(prm_lock)
            addr_trans_invoke = self.prm_handler_invocation_loop("invoke","addrtrans")
            if not addr_trans_invoke:
                self._log.info("Address translation invoke failed")
                return self.post_prm_cleanup()
            if not self.prm_update_atomic("PrmSamplePrintModule1.1.efi"):
                return self.post_prm_cleanup()
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            self._log.info("Unlocking PRM updates...")
            prm_unlock = self.run_powershell_command(command=self.prm_unlock_command, get_output=True, echo_output=True)
            self._log.info(prm_unlock)
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return self.post_prm_cleanup()
            if not self.prm_update("PrmSamplePrintModule1.1.efi"):
                return self.post_prm_cleanup()
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            if self.dummy_handler_version_1_x(1):
                self._log.info("PRM dummy handler version updated to 1.1")
            else:
                return self.post_prm_cleanup()

            self._log.info("Parallely running dummy and addrtrans invoke handler")
            invoke_dummy_thread = ThreadWithReturn(target = self.prm_handler_invocation_loop,args =("invoke","dummy"))
            invoke_addrtrans_thread = ThreadWithReturn(target = self.prm_handler_invocation_loop,args =("invoke","addrtrans"))
            smi_command_thread = ThreadWithReturn(target=self.run_ssh_command,args =("cd C:\\Users\\Administrator && rw /Command=smi_read.rw /Stdout",))
            self._log.info("Starting dummy invoke thread")
            invoke_dummy_thread.start()
            self._log.info("Starting addrstrans invoke thread")
            invoke_addrtrans_thread.start()
            self._log.info("Starting smi_read thread")
            smi_command_thread.start()
            time.sleep(10)
            self._log.info("Finishing dummy invoke thread")
            result_dummy_thread = invoke_dummy_thread.join()
            self._log.info("Finishing addrstrans invoke thread")
            result_addrtrans_thread = invoke_addrtrans_thread.join()
            self._log.info("Finishing smi_read thread")
            result_smi_command_thread = smi_command_thread.join()

            if re.search("Delay 500 ms",str(result_smi_command_thread.stdout)):
                self._log.info("The required string Delay 500 ms present in output")
                if result_dummy_thread and result_addrtrans_thread:
                    self._log.info("Invoke dummy and addrtrans Successful")
                    self.post_prm_cleanup()
                    return True
                else:
                    self._log.info("Invoke dummy and addrtrans Failed")
                    return self.post_prm_cleanup()
            else:
                self._log.info("smi read command failed")
                return self.post_prm_cleanup()
            self.post_prm_cleanup()
            return result

        elif self.prm_with_bios:
            """
            TC 67375.4 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --capsule_path <path for Prm_specific_bios capsule>
            --expected_ver <Prm_specific_bios capsule version>
            --capsule_path2 <path for bios capsule>
            --expected_ver2 <bios capsule version>
            --prm_with_bios
            --warm_reset

            """
            if self.capsule_path != "" and self.capsule_path2 != "" and self.prm_with_bios:
                self.flow_type = "invoke"
                self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return self.post_prm_cleanup()
            if not self.prm_update("PrmSamplePrintModule1.1.efi"):
                return self.post_prm_cleanup()
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            if self.dummy_handler_version_1_x(1):
                self._log.info("PRM dummy handler version updated to 1.1")
            else:
                return self.post_prm_cleanup()
            if self.capsule_path != "" and self.capsule_path2 != "":
                self._log.info("============= {} ======================".format("Performing Bios Capsule Update"))
                capsule_update = self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
                if not capsule_update:
                    self._log.error("Bios capsule update failed")
                    return False
            if self.capsule_path != "" and self.capsule_path2 != "" and self.prm_with_bios:
                self.flow_type = "invoke"
                self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("Second PRM invoke dummy handler Failed")
                return result
            if self.dummy_handler_version_1_x(2):
                self._log.info("PRM dummy handler version updated to 1.2")
            else:
                return self.post_prm_cleanup()
            capsule_update2 = self.send_capsule(self.capsule_path2, self.CAPSULE_TIMEOUT,self.start_workload)
            if not capsule_update2:
                self._log.error("Bios capsule update failed post PRM operation")
                return False
            self.post_prm_cleanup()
            return result

        elif self.no_prm_table:
            """
            TC 67390.5 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --capsule_path <path for Prm_specific_bios capsule>
            --capsule_path2 <path for bios capsule>
            --expected_ver <Prm_specific_bios capsule version>
            --expected_ver2 <bios capsule version>
            --no_prm_table
            --warm_reset

            """
            if self.capsule_path != "" and self.capsule_path2 != "" and self.no_prm_table:
                self._log.info("============= {} ======================".format("Performing Bios Capsule Update"))
                capsule_update = self.send_capsule(self.capsule_path, self.CAPSULE_TIMEOUT, self.start_workload)
                if not capsule_update:
                    self._log.error("Bios capsule update failed")
                    return False
            self._log.info("============= {} ======================".format("Verifing PRMT Table......"))
            acpi_dump = self.run_ssh_command( "\"C:\\Program Files\\RW-Everything\\Rw.exe\" /Command=\"ACPI Dump PRMT;RWExit\" /Stdout")
            prmt_table_field = re.search("Signature\s\"PRMT\"", acpi_dump.stdout)
            if not prmt_table_field:
                self._log.info("============= {} ======================".format("PRMT TABLE NOT FOUND"))
            if not self.prm_update_atomic("PrmSamplePrintModule1.1.efi"):
                return self.post_prm_cleanup()
            capsule_update2 = self.send_capsule(self.capsule_path2, self.CAPSULE_TIMEOUT, self.start_workload)
            if not capsule_update2:
                self._log.error("Bios capsule update failed post PRM operation")
                return False
            self.post_prm_cleanup()
            return True

        elif self.prm_registry_key_check:
            """
            TC 69632.1 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --prm_registry_key_check

            """
            self._log.info("validating PrmSupportGranted parameter...")
            PrmSupportGranted_parameter = self.run_powershell_command(command=self.regedit_command, get_output=True,echo_output=True)
            self._log.info(PrmSupportGranted_parameter)
            PrmSupportGranted_parameter_found = re.search("01000000",PrmSupportGranted_parameter)
            if not PrmSupportGranted_parameter_found:
                self._log.error("PrmSupportGranted parameter 1 isn't found")
                return False
            self.flow_type = "invoke"
            self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return self.post_prm_cleanup()
            if not self.prm_update("PrmSamplePrintModule1.1.efi"):
                return self.post_prm_cleanup()
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            if self.dummy_handler_version_1_x(1):
                self._log.info("PRM dummy handler version updated to 1.1")
            else:
                return self.post_prm_cleanup()
            self.post_prm_cleanup()
            return result

        elif self.acpi:
            """
            TC 67383.4 Command:
            python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py 
            --capsule_path <path for Prm_specific_bios capsule>
            --capsule_path2 <path for bios capsule>
            --expected_ver <Prm_specific_bios capsule version>
            --expected_ver2 <bios capsule version>
            --acpi
            --warm_reset

            """

            self.flow_type = "invoke"
            self.handler = "dummy"
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return result
            time.sleep(3)
            if self.dummy_handler_version_1_x(0):
                self._log.info("PRM dummy handler version updated to 1.0")
            else:
                return self.post_prm_cleanup()
            if not self.prm_update("PrmSamplePrintModule1.1.efi"):
                return self.post_prm_cleanup()
            result = self.invoke_prm_handler_os_wrapper()
            if not result:
                self._log.error("PRM invoke dummy handler Failed")
                return self.post_prm_cleanup()
            if self.dummy_handler_version_1_x(1):
                self._log.info("PRM dummy handler version updated to 1.1")
            else:
                return self.post_prm_cleanup()

            acpi_dump = self.run_ssh_command(
                "\"C:\\Program Files\\RW-Everything\\Rw.exe\" /Command=\"ACPI Dump PRMT;RWExit\" /Stdout")
            prmt_table_field = re.search("Signature\s\"PRMT\"", acpi_dump.stdout)
            if not prmt_table_field:
                self._log.error("============= {} ======================".format("PRMT TABLE NOT FOUND"))
                self.post_prm_cleanup()
                raise RuntimeError("Signatrue is not found")
            else :
                self._log.info("Signature is PRMT as expected")
            prmt_table_field = re.search("OEM ID\s\"INTEL \"", acpi_dump.stdout)
            if not prmt_table_field:
                self._log.error("============= {} ======================".format("OEM ID NOT FOUND"))
                self.post_prm_cleanup()
                raise RuntimeError("OEM ID is not found")
            else :
                self._log.info("OEM ID is INTEL as expected")
            prmt_table_field = re.search("OEM Table ID\s\"INTEL ID\"", acpi_dump.stdout)
            if not prmt_table_field:
                self._log.error("============= {} ======================".format("OEM Table ID NOT FOUND"))
                self.post_prm_cleanup()
                raise RuntimeError("OEM Table ID is not found")
            else :
                self._log.info("OEM TABLE ID is INTEL ID as expected")
            prmt_table_line_list = acpi_dump.stdout.split('\n')
            prmt_table_field = re.search("01 00 00 00", prmt_table_line_list[8])
            if not prmt_table_field:
                self._log.error("============= {} ======================".format("0x50 offset is not matching"))
                self.post_prm_cleanup()
                raise RuntimeError("0x50 offset is not matching")
            else :
                self._log.info(" The MajorRevision field  value  is 0x0001 and the MiinorRevision value is 0x0000 as expected(Offset at 0x50 and 0x52)")
            self.post_prm_cleanup()

            return True

        elif self.flash_type == "verify_prm":
            """
            TC 67381.5 
            Command: python3 src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0013_prm_update.py --flash_type verify_prm

            """
            self.flow_type = "invoke"
            self.handler = "dummy"

            def check(ver):
                for i in range(2):
                    result = self.invoke_prm_handler_os_wrapper()
                    if not result:
                        self._log.error("PRM invoke dummy handler Failed")
                        return result
                    time.sleep(3)
                    if self.dummy_handler_version_1_x(ver):
                        self._log.info("PRM dummy handler version updated to 1.{}".format(ver))
                    else:
                        return False
                return result

            res = check(0)
            if res:
                if not self.prm_update("PrmSamplePrintModule1.1.efi"):
                    self.post_prm_cleanup()
                    return False
            else:
                self.post_prm_cleanup()
                return False

            res1 = check(1)
            self.post_prm_cleanup()
            if res1:
                return True
            else:
                return False

        try:

            if self.start_workloads:
                self.summary_log.info("\tStart workloads: " + str(self.start_workloads))
                self._log.info("\tStarting workloads, wait two minutes till workloads stabilize...")
                self.begin_workloads()

            time_start = datetime.now()

            if (self.flow_type == "invoke"):
                result = self.invoke_prm_handler_os_wrapper()

            if (self.flow_type == "update"):
                result = self.update_prm_handler_os_wrapper()
                # if(result):
                # self.handler = 'dummy'
                # result = self.invoke_prm_handler_os_wrapper()

            if (self.flow_type == "cleanup"):
                result = self.prm_cleanup()

            result = self.examine_post_update_conditions("PRM")
            self._log.info("\tPost update conditions checked")

        except RuntimeError as e:
            self._log.exception(e)

        if self.workloads_started:
            wl_output = self.stop_workloads()
            self._log.error("Evaluating workload output")
            if not self.evaluate_workload_output(wl_output):
                result = False
        return result

    def cleanup(self, return_status):
        super(SEAM_BMC_0013_prm_update, self).cleanup(return_status)
        self._log.info("Invocation time: " + str(self.invocation_time))
        self._log.info("Update time: " + str(self.update_time))
        self._log.info("Total iterations passed: " + str(self.total_iter))

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0013_prm_update.main() else Framework.TEST_RESULT_FAIL)
