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
import random
import os
import re
from datetime import datetime, timedelta
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest
from dtaf_core.lib.config_file_constants import ConfigFileParameters
import subprocess
import glob

class SEAM_BMC_0017_send_random_oob_update(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0017_send_random_oob_update, self).__init__(test_log, arguments, cfg_opts)
        self.iterations = int(arguments.iterations)
        self.stressors = arguments.stressors
        self.start_workload = arguments.start_workload
        self.spi_access = False
        self.update_type = "random_oob"
        self.update_activity =['staging','activation','both']
        self.update_list = ['ucode_upgrade','ucode_downgrade','bios_upgrade','bios_downgrade','sps_op_downgrade','sps_op_upgrade', 'sps_rec_upgrade','sps_rec_downgrade']
        self.capsule_path = ''
        self.expected_ver = ''
        self.warm_reset = False
        self.updates_executed = []
        self.count = {}
        self.total_count = {}
        self.sps_lower_cap_name = arguments.sps_lower_cap_name
        self.sps_higher_cap_name = arguments.sps_higher_cap_name
        self.ucode_lower_cap_name = arguments.ucode_lower_cap_name
        self.ucode_higher_cap_name = arguments.ucode_higher_cap_name
        self.bios_lower_cap_name = arguments.bios_lower_cap_name
        self.bios_higher_cap_name = arguments.bios_higher_cap_name
        self.sps_lower_ver = arguments.sps_lower_ver
        self.sps_higher_ver = arguments.sps_higher_ver
        self.ucode_lower_ver = arguments.ucode_lower_ver
        self.sps_mode = arguments.sps_mode
        self.ucode_higher_ver = arguments.ucode_higher_ver
        self.bios_lower_ver = arguments.bios_lower_ver
        self.bios_higher_ver = arguments.bios_higher_ver
        sps_op_downgrade = self.find_cap_path(self.sps_lower_cap_name)
        sps_op_upgrade = self.find_cap_path(self.sps_higher_cap_name)
        ucode_downgrade_fv1 = self.find_cap_path(self.ucode_lower_cap_name)
        ucode_downgrade_fv2 = self.find_cap_path(self.ucode_lower_cap_name.replace("FV1", "FV2"))
        ucode_upgrade = self.find_cap_path(self.ucode_higher_cap_name)
        bios_downgrade = self.find_cap_path(self.bios_lower_cap_name)
        bios_upgrade = self.find_cap_path(self.bios_higher_cap_name)
        self._log.info("sps_op_downgrade {}".format(sps_op_downgrade))
        self._log.info("sps_op_upgrade {}".format(sps_op_upgrade))
        self._log.info("ucode_downgrade_fv1 {}".format(ucode_downgrade_fv1))
        self._log.info("ucode_downgrade_fv2 {}".format(ucode_downgrade_fv2))
        self._log.info("ucode_upgrade {}".format(ucode_upgrade))
        self._log.info("bios_downgrade {}".format(bios_downgrade))
        self._log.info("bios_upgrade {}".format(bios_upgrade))
        self._log.info("sps lower ver : {}".format(self.sps_lower_ver))
        self._log.info("sps higher ver : {}".format(self.sps_higher_ver))
        self._log.info("ucode_downgrade fv1 {}".format(ucode_downgrade_fv1))
        self._log.info("ucode_downgrade fv2 {}".format(ucode_downgrade_fv2))

        self.bios_expected_ver = self.bios_higher_ver
        self.ucode_expected_ver = self.ucode_higher_ver
        print("bios higher expected ver : {}".format(self.bios_expected_ver))
        print("ucode higher expected ver : {}".format(self.ucode_expected_ver))
        print("bios lower expected ver : {}".format(self.bios_lower_ver))
        print("ucode lower expected ver : {}".format(self.ucode_lower_ver))
   
        self.capsule_expected_ver_map = {'sps_op_upgrade':{'capsule_op_upgrade': sps_op_upgrade,'Operational_ver':'Operational: '+self.sps_higher_ver,'State':'Current State: Operational'},
                                         'sps_op_downgrade':{'capsule_op_downgrade':sps_op_downgrade, 'Operational_ver':'Operational: '+self.sps_lower_ver,'State':'Current State: Operational'},        
                                         'sps_rec_downgrade':{'expected_ver': self.sps_lower_ver},
                                         'sps_rec_upgrade':{'expected_ver': self.sps_higher_ver},
                                    'bios_downgrade':{'capsule_downgrade':bios_downgrade,'expected_ver':self.bios_lower_ver},
                                    'bios_upgrade':{'capsule_upgrade':bios_upgrade,'expected_ver':self.bios_higher_ver},
                                    'ucode_upgrade':{'capsule_upgrade':ucode_upgrade,'expected_ver':self.ucode_higher_ver},
                                    'ucode_downgrade':{'capsule_downgrade_fv1':ucode_downgrade_fv1,'capsule_downgrade_fv2':ucode_downgrade_fv2,'expected_ver':self.ucode_lower_ver}}
        
    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0017_send_random_oob_update, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--iterations', action='store', help="Number of iterations", default="1")
        parser.add_argument('--sps_lower_ver', action='store',help="SPS with lower version", default="")
        parser.add_argument('--sps_higher_ver', action='store',help="SPS with higher version", default="")
        parser.add_argument('--ucode_lower_ver', action='store',help="UCODE with lower version", default="")
        parser.add_argument('--ucode_higher_ver', action='store',help="UCODE with higher version", default="")
        parser.add_argument('--bios_lower_ver', action='store',help="BIOS with lower version", default="")
        parser.add_argument('--bios_higher_ver', action='store',help="BIOS with higher version", default="")
        parser.add_argument('--stressors', action='store_true',help="Set if want to add stressors")
        parser.add_argument('--sps_lower_cap_name', action='store',help="SPS lower version cap", default="")
        parser.add_argument('--sps_higher_cap_name', action='store',help="SPS higher version cap", default="")
        parser.add_argument('--ucode_lower_cap_name', action='store',help="UCODE lower version cap", default="")
        parser.add_argument('--ucode_higher_cap_name', action='store',help="UCODE higher version cap", default="")
        parser.add_argument('--bios_lower_cap_name', action='store',help="BIOS lower version cap", default="")
        parser.add_argument('--bios_higher_cap_name', action='store',help="BIOS higher version cap", default="")
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
     
    def check_capsule_pre_conditions(self):
        #To-Do add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        #To-Do add workload output analysis
        return True

    def command_string(self, upgrade_configuration,expected_ver, capsule_path):
        """
        Creates a powershell command for the individual test scripts 
        :param upgrade_configuration: tuple with the ( update type, activity )
        :param expected_ver: expected version after update
        :param capsule_path: location of update capsule 
        """

        cmd_string = " "
        
        if (upgrade_configuration[0] == 'sps_op_upgrade' or upgrade_configuration[0] == 'sps_op_downgrade' ):
           cmd_string = ['python3', 'src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0006_send_sps_update_capsule_loop.py',     
                        '--capsule_path='+capsule_path, '--expected_ver='+self.expected_ver, '--loop=1']
    
        
        elif (upgrade_configuration[0] == 'sps_rec_upgrade' or upgrade_configuration[0] == 'sps_rec_downgrade'):

            cmd_string = ['python3', 'src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0014_send_sps_update_three_capsule_loop.py',
                         '--capsule_path='+capsule_path, '--expected_ver='+expected_ver, 
                         '--sps_update_type=three_capsule', '--loop=1']


        elif (upgrade_configuration[0] == 'bios_upgrade' or upgrade_configuration[0] == 'bios_downgrade' ):

            cmd_string = ['python3', 'src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0009_send_bios_capsule_loop.py', 
                         '--capsule_path='+self.capsule_path, '--expected_ver='+self.expected_ver, 
                         '--loop=1']

        
        elif (upgrade_configuration[0] == 'ucode_upgrade'):
        
            cmd_string  = ['python3', 'src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0008_send_ucode_capsule_loop.py', 
                           '--capsule_path='+self.capsule_path, '--expected_ver='+self.expected_ver, 
                           '--loop=1', '--update_type=upgrade']

            
        elif (upgrade_configuration[0] == 'ucode_downgrade'):
            cmd_string = ['python3', 'src\\seamless\\tests\\bmc\\functional\\SEAM_BMC_0008_send_ucode_capsule_loop.py', 
                          '--capsule_path='+self.capsule_path, '--capsule_path2='+str(self.capsule_path2), 
                          '--expected_ver='+self.expected_ver, '--loop=1', '--update_type=downgrade']
    
            
    
        if(upgrade_configuration[1] == 'activation'):
            cmd_string.extend(['--warm_reset', '--activation'])
        
        elif(upgrade_configuration[1] == 'both'):
            cmd_string.append('--warm_reset')


        if (self.stressors):
            cmd_string.append('--stressors')

        if(self.start_workload):
            cmd_string.append('--start_workload')
        

        return cmd_string

        
    def get_current_version(self, echo_version=True): 
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
            # output = result.output
            output = result.stdout

        version = "NONE"
        for line in output.splitlines():
            if "SPS Image FW version" in line:
                version = line.split(':')[1]
            elif "CurrentState" in line or "Current State" in line:
                ME_mode = line.split('):')[1].strip().split(' ')[0]
                
       
        
        try:
            rec_ver = version.split('(Recovery)')[0].strip()
            opr_ver = version.split('(Recovery)')[1].split('(Operational)')[0].replace(',', '').strip()
        
        except IndexError:
            if self.sut_ssh.is_alive() == False:
                self._log.error("SUT is offline/not connecting - Test Failed")
                self._log.debug("Version results: " + version)
                raise RuntimeError("SUT is offline/won't connect")
            else:
                raise RuntimeError

        version = self._bmc_ipmi.get_me_state()

        version = 'Operational: ' + opr_ver + ' Recovery: ' + rec_ver + ' Current State: ' + ME_mode
        
        if echo_version:
            self._log.info("\tVersion detected: " + version)
        return version
        
    def get_current_sps_version(self, echo_version=True): 
        """
        Read sps version
        :param echo_version: True if display output
        :return ME version
        """
        # if self._os_type != OperatingSystems.LINUX:
            # output = self.run_powershell_command(self.get_sps_command, get_output=True)
        # else:
            # cmd = './spsInfoLinux64'
            # result = self.run_ssh_command(cmd)
            # output = result.output
           
        if self._os_type != OperatingSystems.LINUX and not self.sut_ssh.is_alive():
            output = self.run_powershell_command(self.get_sps_command, get_output=True)
        elif self._os_type == OperatingSystems.WINDOWS and self.sut_ssh.is_alive():
            cmd = 'C:\spsInfoWin64.exe'
            self._log.info("Logging spsinfo through SSH")
            result = self.run_ssh_command(cmd)
            output = result.stdout
        else:
            cmd = './spsInfoLinux64'
            result = self.run_ssh_command(cmd)
            output = result.stdout

        version = "NONE"
        for line in output.splitlines():
            if "SPS Image FW version" in line:
                version = line.split(':')[1]
            elif "CurrentState" in line or "Current State" in line:
                ME_mode = line.split('):')[1].strip().split(' ')[0]
        
        try:
            rec_ver = version.split('(Recovery)')[0].strip()
            opr_ver = version.split('(Recovery)')[1].split('(Operational)')[0].replace(',', '').strip()
            
        except IndexError:
            if  not self.sut_ssh.is_alive():
                self._log.error("SUT is offline/not connecting - Test Failed")
                self._log.debug("Version results: " + version)
                raise RuntimeError("SUT is offline/won't connect")

        #ME_mode = self._bmc_ipmi.get_me_state()

        version = [rec_ver, opr_ver]
        return version
        
    def get_bios_version(self, echo_version=True):
        """
        Read bios version
        :param echo_version: True if display output
        :return bios version
        """
        cmd = 'dmidecode | grep "Version: ' + str(self._product)[0] + '"'
        # cmd = 'dmidecode | grep "Version: W"'
        if self._os_type != OperatingSystems.LINUX:
            output = self.run_powershell_command(self.get_bios_command, get_output=True)
        else :
            result = self.run_ssh_command(cmd)
            version = result.stdout.split('\n')[0].split(' ')
            if echo_version:
                self._log.info("Version detected: " + version[1])
            return version[1]
        version = "NONE"
        for line in output.split('\n'):
            if "SMBIOSBIOSVersion : " in line:
                version = line.split(' : ')[1]
                break
        if echo_version:
            self._log.info("Version detected: " + version)
        return version
        
    def get_ucode_version(self, echo_version=True):
        """
        Read ucode version
        :param echo_version: True if display output
        :return bios version
        """
        # TODO: add correct command to read version
        version = None
        
            
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

        return version

    def execute(self):
        result = False
        if self.stressors:
            self.spi_access = True
        """
        Example of command:
        python3 src\seamless\tests\bmc\functional\SEAM_BMC_0017_send_random_oob_update.py 
        --sps_lower_cap_name SPS_E5_04.04.04.051.0_kn4_Operational.cap --sps_lower_ver 4.4.4.51 
        --sps_higher_cap_name SPS_E5_04.04.04.053.0_kn4_Operational.cap --sps_higher_ver 4.4.4.53 
        --bios_lower_cap_name WLYDCRB.SYS.WR.64.2021.12.1.01.0404_0020.P17_P80270_LBG_SPS_ICX_Production_SMLS.cap --bios_lower_ver P17 
        --bios_higher_cap_name WLYDCRB.SYS.WR.64.2021.13.4.02.0455_0020.P18_P80280_LBG_SPS_ICX_Production_SMLS.cap --bios_higher_ver P18 
        --ucode_lower_cap_name L0-0b000280_C0-0c0002f0_D0-0d000270_FV1.cap --ucode_lower_ver 0xd000270 
        --ucode_higher_cap_name L0-0b000280_C0-0c0002f0_D0-0d000280_FV1.cap --ucode_higher_ver 0xd000280 
        --iterations 2
        """
        for i in range(self.iterations):
            self.update = random.choice(self.update_list)
            self.activity = random.choice(self.update_activity)
            if ('sps' in self.update):
                self.activity = ' '

            config_tuple = (self.update,self.activity)

            self._log.info("===================Updating: " + str(self.update)+"====================")


            if(self.update=='sps_op_upgrade'):

                capsule_path = self.capsule_expected_ver_map['sps_op_upgrade']['capsule_op_upgrade']
                current_ver = self.get_current_sps_version()
                self.expected_ver = self.capsule_expected_ver_map['sps_op_upgrade']['Operational_ver'] + ' Recovery: '+ str(current_ver[0]) + ' Current State: Operational'

                cmd = self.command_string (config_tuple, self.expected_ver, capsule_path)

                self._log.info('Upgrading SPS version: {}'.format(cmd))
                result = (False if subprocess.call(cmd, shell=True) else True)

            elif(self.update=='sps_op_downgrade'):

                capsule_path = self.capsule_expected_ver_map['sps_op_downgrade']['capsule_op_downgrade']
                current_ver = self.get_current_sps_version()
                self.expected_ver = self.capsule_expected_ver_map['sps_op_downgrade']['Operational_ver'] + ' Recovery: '+ str(current_ver[0]) + ' Current State: Operational'

                cmd = self.command_string (config_tuple, self.expected_ver, capsule_path)
                
                self._log.info('Downgrading SPS version: {}'.format(cmd))
                result = (False if subprocess.call(cmd, shell=True) else True)



            elif(self.update=='sps_rec_downgrade'):
                capsule_path = self.capsule_expected_ver_map['sps_op_downgrade']['capsule_op_downgrade']
                expected_ver = self.capsule_expected_ver_map['sps_rec_downgrade']['expected_ver']

                current_ver = self.get_current_sps_version()
                
                cmd = self.command_string (config_tuple, expected_ver, capsule_path)

                self._log.info('Downgrading SPS version three capsule method step 1: {}'.format(cmd))
                result = (False if subprocess.call(cmd, shell=True) else True)



            elif(self.update=='sps_rec_upgrade'):
                capsule_path = self.capsule_expected_ver_map['sps_op_upgrade']['capsule_op_upgrade']
                expected_ver = self.capsule_expected_ver_map['sps_rec_upgrade']['expected_ver']
                
                cmd = self.command_string (config_tuple, expected_ver, capsule_path)
                
                self._log.info('Downgrading SPS version three capsule method step 1: {}'.format(cmd))
                result = (False if subprocess.call(cmd, shell=True) else True)





            elif(self.update=='bios_downgrade'):
                self._log.info("===================Update Activity: " + str(self.activity))

                self.capsule_path = self.capsule_expected_ver_map['bios_downgrade']['capsule_downgrade']


                if(self.activity=='staging'):
                    
                    self.expected_ver = self.get_bios_version()
                   
                    cmd = self.command_string (config_tuple, self.expected_ver, self.capsule_path)

                    self._log.info('Downgrading Bios version : {}'.format(cmd))
                    result = (False if subprocess.call(cmd, shell=True) else True)

                    self.bios_expected_ver = self.expected_ver



                elif (self.activity == 'activation'):

                    self.expected_ver = self.bios_expected_ver
                    
                    cmd = self.command_string (config_tuple, self.expected_ver, self.capsule_path)


                    self._log.info('Downgrading Bios version : {}'.format(cmd))

                    result = (False if subprocess.call(cmd, shell=True) else True)

                    self.ucode_expected_ver = self.get_ucode_version()
                    self.bios_expected_ver = self.get_bios_version()


                elif (self.activity == 'both'):

                    self.expected_ver = self.capsule_expected_ver_map['bios_downgrade']['expected_ver']
                    
                    cmd = self.command_string (config_tuple, self.expected_ver, self.capsule_path)

                    self._log.info('Downgrading Bios version : {}'.format(cmd))
                    result = (False if subprocess.call(cmd, shell=True) else True)

                    self.ucode_expected_ver = self.get_ucode_version()
                    self.bios_expected_ver = self.get_bios_version()



            #bios changes

            elif(self.update=='bios_upgrade'):

                self._log.info("===================Update Activity: " + str(self.activity))

                self.capsule_path = self.capsule_expected_ver_map['bios_upgrade']['capsule_upgrade']

                if(self.activity=='staging'):


                    self.expected_ver = self.get_bios_version()
                    
                    cmd = self.command_string (config_tuple, self.expected_ver, self.capsule_path)

                   
                    self._log.info('Upgrading Bios version : {}'.format(cmd))
                    result = (False if subprocess.call(cmd, shell=True) else True)

                    self.bios_expected_ver = self.expected_ver


                elif (self.activity == 'activation'):

                    self.expected_ver = self.bios_expected_ver

                    cmd = self.command_string (config_tuple, self.expected_ver, self.capsule_path)                    
                    
                    self._log.info('Upgrading Bios version : {}'.format(cmd))
                    result = (False if subprocess.call(cmd, shell=True) else True)

                    self.ucode_expected_ver = self.get_ucode_version()
                    self.bios_expected_ver = self.get_bios_version()


                elif (self.activity == 'both'):

                    self.expected_ver = self.capsule_expected_ver_map['bios_upgrade']['expected_ver']

                    cmd = self.command_string (config_tuple, self.expected_ver, self.capsule_path)
                    
                    self._log.info('Upgrading Bios version : {}'.format(cmd))
                    result = (False if subprocess.call(cmd, shell=True) else True)

                    self.ucode_expected_ver = self.get_ucode_version()
                    self.bios_expected_ver = self.get_bios_version()




            
            #ucode changes 
            elif(self.update=='ucode_upgrade'):
                self._log.info("===================Update Activity: " + str(self.activity))
                self.capsule_path = self.capsule_expected_ver_map['ucode_upgrade']['capsule_upgrade']



                if(self.activity=='staging'):
                    
                    self.expected_ver = self.get_ucode_version()

                    cmd = self.command_string (config_tuple, self.expected_ver, self.capsule_path)

                    self._log.info('Upgrading uCode version : {}'.format(cmd))
                    result = (False if subprocess.call(cmd, shell=True) else True)

                    self.ucode_expected_ver = self.expected_ver


                elif (self.activity == 'activation'):

                    self.expected_ver = self.ucode_expected_ver
                    print(self.expected_ver)
                    print(self.capsule_path)

                    cmd = self.command_string (config_tuple, self.expected_ver, self.capsule_path)

                    self._log.info('Upgrading uCode version : {}'.format(cmd))
                    result = (False if subprocess.call(cmd, shell=True) else True)

                    self.ucode_expected_ver = self.get_ucode_version()
                    self.bios_expected_ver = self.get_bios_version()


                elif (self.activity == 'both'):

                    self.expected_ver = self.capsule_expected_ver_map['ucode_upgrade']['expected_ver']

                    cmd = self.command_string (config_tuple, self.expected_ver, self.capsule_path)


                    self._log.info('Upgrading uCode version : {}'.format(cmd))
                    result = (False if subprocess.call(cmd, shell=True) else True)

                    self.ucode_expected_ver = self.get_ucode_version()
                    self.bios_expected_ver = self.get_bios_version()




            elif(self.update=='ucode_downgrade'):
                self._log.info("===================Update Activity: " + str(self.activity))

                self.capsule_path = self.capsule_expected_ver_map['ucode_downgrade']['capsule_downgrade_fv1']
                self.capsule_path2 = self.capsule_expected_ver_map['ucode_downgrade']['capsule_downgrade_fv2']



                if(self.activity == 'staging'):

                    self.expected_ver = self.get_ucode_version()

                    cmd = self.command_string (config_tuple, self.expected_ver, self.capsule_path)

                    self._log.info('Downgrading uCode version : {}'.format(cmd))
                    result = (False if subprocess.call(cmd, shell=True) else True)

                    self.ucode_expected_ver = self.expected_ver


                elif (self.activity == 'activation'):

                    self.expected_ver = self.ucode_expected_ver

                    cmd = self.command_string (config_tuple, self.expected_ver, self.capsule_path)

                    self._log.info('Downgrading uCode version : {}'.format(cmd))
                    result = (False if subprocess.call(cmd, shell=True) else True)

                    self.ucode_expected_ver = self.get_ucode_version()
                    self.bios_expected_ver = self.get_bios_version()


                elif (self.activity == 'both'):
                    self.expected_ver = self.capsule_expected_ver_map['ucode_downgrade']['expected_ver']

                    cmd = self.command_string (config_tuple, self.expected_ver, self.capsule_path)
                    
                    self._log.info('Downgrading uCode version : {}'.format(cmd))
                    result = (False if subprocess.call(cmd, shell=True) else True)

                    self.ucode_expected_ver = self.get_ucode_version()
                    self.bios_expected_ver = self.get_bios_version()
                




            #end of selection 
                
            self._log.info("Completed loop " + str(i+1))
            self._log.info("==============Completed update: " + self.update + " "+ self.activity+"==================")
            time_delay = random.randint(0,300)
            self._log.info("Wait for " + str(time_delay) + " seconds...")
            self.updates_executed.append((self.update,self.activity,time_delay))
            if self.update in self.count.keys():
                self.count[self.update] = self.count[self.update]+1
            else:
                self.count[self.update] = 1
            if ((self.update, self.activity)) in self.total_count.keys():
                self.total_count[(self.update, self.activity)] = self.total_count[(self.update, self.activity)]+1
            else:
                self.total_count[(self.update, self.activity)] = 1
            time.sleep(time_delay)
                              
        return result
        
    def cleanup(self, return_status):
        super(SEAM_BMC_0017_send_random_oob_update, self).cleanup(return_status)
        for each in self.updates_executed:
            self._log.info('Updates executed: ' + each[0] + ' ' + each[1] + ' followed by delay of ' + str(each[2]) + ' seconds')
        for update,val in self.count.items():
            self._log.info('Update ' + update + ' executed ' + str(val) + ' times')
        for update,val in self.total_count.items():
            self._log.info('Update ' + update[0] +' '+update[1] + ' executed ' + str(val) + ' times')
  

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0017_send_random_oob_update.main() else Framework.TEST_RESULT_FAIL)
