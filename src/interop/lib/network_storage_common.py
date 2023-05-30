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

import os
import subprocess
import sys
import six
import time
import re
from shutil import copy
import shutil
import threading
from src.interop.lib.thread_log_util import ThreadLogUtil
import platform

from dtaf_core.lib.exceptions import OsCommandException, OsCommandTimeoutException
from src.environment.os_installation import OsInstallation
from src.interop.lib.accelerator_library import AcceleratorLibrary
from src.lib.dtaf_content_constants import RaidConstants, SutInventoryConstants
from src.storage.test.storage_common import StorageCommon
# from importlib_metadata import FileNotFoundError

from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import ProductFamilies
from dtaf_core.lib.os_lib import LinuxDistributions

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_artifactory_utils import ContentArtifactoryUtils
from src.lib.content_configuration import ContentConfiguration
from src.lib.dtaf_content_constants import BonnieTool, LttsmToolConstant, CcbPackageConstants, RasPcieAer, \
    PcmToolConstants, PcmMemoryConstants

from src.lib import content_exceptions
from src.lib.dtaf_content_constants import TurboStatConstants, RDTConstants, VROCConstants, RasRunnerToolConstant

from src.lib.dtaf_content_constants import WindowsMemrwToolConstant, StressCrunchTool, StressMprimeTool,\
    StressLibquantumTool
from src.lib.dtaf_content_constants import BurnInConstants, SgxHydraToolConstants

from src.lib.dtaf_content_constants import DynamoToolConstants, IOmeterToolConstants, TimeConstants

from src.lib.dtaf_content_constants import Mprime95ToolConstant
from src.lib.dtaf_content_constants import LttsmToolConstant
from src.collaterals.collateral_constants import CollateralConstants
from src.lib.dtaf_content_constants import PTUToolConstants
from src.lib.tools_constants import ArtifactoryName, ArtifactoryTools
from src.lib.grub_util import GrubUtil
from src.provider.stressapp_provider import StressAppTestProvider

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path
from src.interop.lib.thread_log_util import ThreadLogUtil

class SupportMethods(object):

    def __init__(self, log, os_obj, cfg_opts):
        self._log = log
        self._os = os_obj
        self.sut_os = self._os.os_type
        self._cfg = cfg_opts
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self.reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg)
        self._stress_provider = StressAppTestProvider.factory(self._log, cfg_opts, self._os)
        self._thread_logger = ThreadLogUtil(self._log, self._os, cfg_opts)
        self._os_installation_lib = OsInstallation(self._log, cfg_opts)
        self._accelerator_lib = AcceleratorLibrary(self._log, self._os, cfg_opts)

    def gen_variables(self):
        self.gen3_check = self._common_content_configuration.get_gen3_present()
        self.gen4_check = self._common_content_configuration.get_gen4_present()
        self.gen5_check = self._common_content_configuration.get_gen5_present()
        self.gen_nic_interface_name_sut = self._common_content_configuration.get_gen_nic_interface_name_sut()
        self.gen_nic_interface_name_peer = self._common_content_configuration.get_gen_nic_interface_name_peer()
        self.gen_static_ip_sut = self._common_content_configuration.get_gen_static_ip_sut()
        self.gen_static_ip_peer = self._common_content_configuration.get_gen_static_ip_peer()
        self.gen_count = 0
        self.gen_storage_device_list = []
        if self.gen3_check.lower() == 'yes':
            self.gen_count += 1
            self.gen3_type = self._common_content_configuration.get_gen3_type()
            self.gen3_bdf = self._common_content_configuration.get_gen3_bdf_values()

        if self.gen4_check.lower() == 'yes':
            self.gen_count += 1
            self.gen4_type = self._common_content_configuration.get_gen4_type()
            self.gen4_bdf = self._common_content_configuration.get_gen4_bdf_values()

        if self.gen5_check.lower() == 'yes':
            self.gen_count += 1
            self.gen5_type = self._common_content_configuration.get_gen5_type()
            self.gen5_bdf = self._common_content_configuration.get_gen5_bdf_values()


        if self.gen3_check.lower() == 'yes' and self.gen3_type.lower() == "storage":
            self.gen_count -= 1
            self.gen3_storage_device = self._common_content_configuration.get_gen3_storage_device_name()
            self.gen_storage_device_list.append(self.gen3_storage_device)

        if self.gen4_check.lower() == 'yes' and self.gen4_type.lower() == "storage":
            self.gen_count -= 1
            self.gen4_storage_device = self._common_content_configuration.get_gen4_storage_device_name()
            self.gen_storage_device_list.append(self.gen4_storage_device)

        if self.gen5_check.lower() == 'yes' and self.gen4_type.lower() == "storage":
            self.gen_count -= 1
            self.gen5_storage_device = self._common_content_configuration.get_gen5_storage_device_name()
            self.gen_storage_device_list.append(self.gen5_storage_device)

        if self.gen_nic_interface_name_sut.lower() != "na":
            self.gen_nic_interface_name_sut_list = self.gen_nic_interface_name_sut.split(';')

        if self.gen_nic_interface_name_peer.lower() != "na":
            self.gen_nic_interface_name_peer_list = self.gen_nic_interface_name_peer.split(';')

        if self.gen_static_ip_sut.lower() != "na":
            self.gen_static_ip_sut_list = self.gen_static_ip_sut.split(';')

        if self.gen_static_ip_peer.lower() != "na":
            self.gen_static_ip_peer_list = self.gen_static_ip_peer.split(';')

        return self.gen_nic_interface_name_peer_list, self.gen_static_ip_sut_list, \
               self.gen_static_ip_peer_list, self.gen_storage_device_list

    def gen_network_traffic_test(self):
        peer_connection_check, peer_client = self.peer_ssh_connection()
        if peer_connection_check == True:
            peer_interface_presence_check = self.gen_peer_interface_check(peer_client, self.gen_nic_interface_name_peer_list)

            if peer_interface_presence_check == True:
                self.gen_assign_static_ip_peer(peer_client, self.gen_static_ip_peer_list,
                                                                self.gen_nic_interface_name_peer_list)
                peer_iperf_present = self.peer_iperf_check(peer_client)
                if peer_iperf_present == True:
                    sub_thread_1 = threading.Thread(target=self.gen_start_iperf_peer, args=(peer_client,))
                    sub_thread_1.start()
                elif peer_iperf_present == False:
                    self._log.error('Iperf not installed in peer system. Please install before running test.')
                    raise content_exceptions.TestFail('Test failed as iperf not installed in Peer system')
            elif peer_interface_presence_check == False:
                self._log.error('Could not find specified interface in peer system')
                raise content_exceptions.TestFail('Could not find specified interface in peer system')
        elif peer_connection_check == False:
            self._log.error('Test failed as peer connection could not be established..')
            raise content_exceptions.TestFail('Test failed as peer connection could not be established..')

        # peer_client.close()
        interface_presence_check = self.gen_sut_interface_check(self.gen_nic_interface_name_peer_list)
        if interface_presence_check == True:
            self.gen_assign_static_ip_sut(self.gen_nic_interface_name_peer_list, self.gen_static_ip_sut_list)
            self.disable_firewall_sut()
            ping_result = self.gen_ping_sut_to_peer(self.gen_static_ip_peer_list)
            # ping_result = True
            network_traffic_thread_list = []
            if ping_result == True:
                network_thread_list = []
                self._log.info("All prequisites successfully completed before network traffic workload run")
                for interaion_count in range(len(self.gen_static_ip_peer_list)):
                    gen_wise_static_ip_for_run_list = self.gen_static_ip_peer_list[interaion_count].split(',')
                    for each_static_ip in gen_wise_static_ip_for_run_list:
                        t21 = threading.Thread(target=self.gen_start_iperf_sut, args=(each_static_ip,))
                        network_thread_list.append(t21)
                if len(network_thread_list) > 0:
                    for thread_run in network_thread_list:
                        time.sleep(1)
                        sub_thread_2_log_handler = self._thread_logger.thread_logger(thread_run)
                        thread_run.start()

                    for thread_run in network_thread_list:
                        sub_thread_1.join()
                        thread_run.join()
                        self._thread_logger.stop_thread_logging(sub_thread_2_log_handler)
                peer_client.close()
                self._log.info("Peer client closed")
            else:
                self._log.error('test failed as server client ping was unsuccessful')
                raise content_exceptions.TestFail('test failed as server client ping was unsuccessful')

        elif interface_presence_check == False:
            raise content_exceptions.TestFail('test failed ')

    def raid_fio(self,fio_cmd): # modify
        # ....fio code ... start


        REGEX_FOR_FIO = r'\serr=\s0'
        FIO_TOOL_NAME = r"fio"

        fio_cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=fio_cmd,
                                                                  cmd_str=fio_cmd,
                                                                  execute_timeout=self._command_timeout)

        self._log.info(fio_cmd_output.strip())
        reg_output = re.findall(REGEX_FOR_FIO, fio_cmd_output.strip())
        if not len(reg_output):
            raise content_exceptions.TestFail('Un-expected Error Captured in Fio output Log')
        self._log.info('No Error Captured as Expected')
        self._stress_provider.check_app_running(app_name=FIO_TOOL_NAME,
                                                stress_test_command="./" + FIO_TOOL_NAME)
        self._log.info("FIO Command execution has completed successfully and been Verified Bandwidth!")
        # Fio code insertion.... end

    def LTSSM_tool_test(self, sut_folder_path):
        random_cycles_cfg = self._common_content_configuration.get_random_cycles()
        bus_value_of_the_PCIe_device_width_speed_cfg = self._common_content_configuration.get_bus_value_of_the_PCIe_device_width_speed()
        execution_details = self._common_content_lib.execute_sut_cmd(sut_cmd="./LTSSMtool randomCycles {} {} "
                                                                             "-w 5000 -tw 1 -tw sbr 0 -tw pml1 0 -tw "
                                                                             "linkdisable 0".format(random_cycles_cfg,bus_value_of_the_PCIe_device_width_speed_cfg), cmd_str="set permission",
                                                                     execute_timeout=self._command_timeout, cmd_path=
                                                                     sut_folder_path)
        self._log.debug(execution_details)
        if "Error Summary [[48;2;0;0;0m[91mFAILED" in execution_details:

            return 1
        else:
            return 0


    def stressapptest_installation_check(self):
        stdout_msg = self._common_content_lib.execute_sut_cmd(sut_cmd='command -v stressapptest >/dev/null && '
                                                                      'echo "Stressapptest is installed" || echo "Stressapptest is not installed"',
                                                              execute_timeout=self._command_timeout,
                                                              cmd_str="stressapp installation check")
        self._log.debug(stdout_msg)
        return stdout_msg


    def memory_check_before_stressapptest(self):
        memory_status = self._common_content_lib.execute_sut_cmd(sut_cmd='free -h',
                                                                 execute_timeout=self._command_timeout,
                                                                 cmd_str="memory check")
        self._log.info('\n' + memory_status)
        return memory_status


    def stressapp_memory_stress_test(self):
        stress_duration_cfg = self._common_content_configuration.get_workload_time()
        memory_stress_test_execution_details = self._common_content_lib.execute_sut_cmd(
            sut_cmd='stressapptest -W -M -m -s {} -l /opt/stresapp.log'.format(stress_duration_cfg),
            execute_timeout=self._command_timeout,
            cmd_str="stressapp test")
        self._log.debug(memory_stress_test_execution_details)

        return memory_stress_test_execution_details

    def sut_interface_check(self):
        nic_interface_name_sut_cfg = self._common_content_configuration.get_nic_interface_name_sut()
        interface_presence_check = self._common_content_lib.execute_sut_cmd(sut_cmd = 'ifconfig {}'.format(nic_interface_name_sut_cfg),
                                                                            execute_timeout=self._command_timeout,
                                                                            cmd_str= 'sut_interface check')
        self._log.debug(interface_presence_check)
        echo_check = self._common_content_lib.execute_sut_cmd(sut_cmd = 'echo "$?"',
                                                                            execute_timeout=self._command_timeout,
                                                                            cmd_str= 'sut_interface check')
        self._log.debug(echo_check)
        if '0' in echo_check:
            return True
        else:
            return False

    def assign_static_ip_sut(self):
        nic_interface_name_sut_cfg = self._common_content_configuration.get_nic_interface_name_sut()
        static_ip_sut_cfg = self._common_content_configuration.get_static_ip_sut()
        sut_static_ip = self._common_content_lib.execute_sut_cmd(
            sut_cmd='ifconfig {} {} up'.format(nic_interface_name_sut_cfg, static_ip_sut_cfg),
            execute_timeout=self._command_timeout,
            cmd_str='assigning static ip sut')
        self._log.debug(sut_static_ip)

    def ping_sut_to_peer(self):
        static_ip_peer_cfg = self._common_content_configuration.get_static_ip_peer()
        peer_static_ip = static_ip_peer_cfg.split('/')
        self._log.info("pinging peer interface for 10 seconds")
        ping_result = self._common_content_lib.execute_sut_cmd(
            sut_cmd='ping -c 10 {}'.format(peer_static_ip[0]),
            execute_timeout=self._command_timeout,
            cmd_str='pinging to peer')
        self._log.debug(ping_result)
        if 'ttl=64' in ping_result:
            self._log.debug('Ping successful')
            return True
        else:
            self._log.debug('Ping between client and server unsuccessful')
            return False

    def sut_iperf_check(self):
        sut_iperf_check_op = self._common_content_lib.execute_sut_cmd(
            sut_cmd='command -v iperf',
            execute_timeout=self._command_timeout,
            cmd_str='checking presence of iperf on client')
        self._log.debug(sut_iperf_check_op)
        sut_iperf_echo = self._common_content_lib.execute_sut_cmd(
            sut_cmd='echo "$?"',
            execute_timeout=self._command_timeout,
            cmd_str='echo for iperf check command')
        self._log.debug(sut_iperf_echo)
        if '0' in sut_iperf_echo:
            return True
        else :
            return False

    def start_iperf_sut(self):
        static_ip_peer_cfg = self._common_content_configuration.get_static_ip_peer()
        duration_iperf_op_cfg = self._common_content_configuration.get_duration_iperf_op()
        duration_iperf_run_cfg = self._common_content_configuration.get_workload_time()
        parallel_thread_count_cfg = self._common_content_configuration.get_parallel_thread_count()
        ip_peer = static_ip_peer_cfg.split('/')
        iperf_output =  self._common_content_lib.execute_sut_cmd(
            sut_cmd=' iperf -c {} -p 5500 -i {} -t {} -P {}'.format
            (ip_peer[0], duration_iperf_op_cfg, duration_iperf_run_cfg,parallel_thread_count_cfg),
            execute_timeout=self._command_timeout,
            cmd_str='initiating iperf on client')
        self._log.debug(iperf_output)
        if 'Transfer' and 'Bandwidth' in iperf_output:
            self._log.debug("Network Traffic test passed")

        else :
            self._log.error("Network Traffic test failed")
    def disable_firewall_sut(self):
        self._common_content_lib.execute_sut_cmd(
            sut_cmd='systemctl disable firewalld',
            execute_timeout=self._command_timeout,
            cmd_str='disable firewall')
        self._log.debug("Disabled Firewall in SUT")

    def peer_ssh_connection(self):
        import paramiko

        hostname = self._common_content_configuration.get_peer_host_name()
        username = self._common_content_configuration.get_peer_user_name()
        password = self._common_content_configuration.get_peer_password()

        client_1 = paramiko.SSHClient()
        client_1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self._log.info('Establishing SSH connection......')
            client_1.connect(hostname=hostname, username=username, password=password)
        except:
            self._log.info("[!] Cannot connect to the SSH Server")
            return False, client_1
        else:
            self._log.info("ssh connection successful")
            return True, client_1

    def peer_interface_check(self,client):
        nic_interface_name_peer_cfg = self._common_content_configuration.get_nic_interface_name_peer()
        (stdin, stdout, stderr) = client.exec_command('ifconfig {}'.format(nic_interface_name_peer_cfg))
        for line in stdout.readlines():
            self._log.debug(line)

        for line in stderr.readlines():
            self._log.error(line)

        (stdin, stdout, stderr) = client.exec_command('echo "$?"')
        for op_line in stdout.readlines():
            self._log.debug(op_line)
        if '0' in op_line:
            return True
        else:
            return False

    def assign_static_ip_peer(self,client):
        nic_interface_name_peer_cfg = self._common_content_configuration.get_nic_interface_name_peer()
        static_ip_peer_cfg = self._common_content_configuration.get_static_ip_peer()
        (stdin, stdout, stderr) = client.exec_command('ifconfig {} {} up'.format(nic_interface_name_peer_cfg, static_ip_peer_cfg))
        for line in stdout.readlines():
            self._log.debug(line)

        (stdin, stdout, stderr) = client.exec_command('systemctl disable firewalld')

    def peer_iperf_check(self, client):
        (stdin, stdout, stderr) = client.exec_command('command -v iperf')
        for line in stdout.readlines():
            self._log.debug(line)
        (stdin, stdout, stderr) = client.exec_command('echo "$?"')
        for line in stdout.readlines():
            if '0' in line:
                self._log.debug("iperf installed in peer")
                return True

            else :
                return False

    def start_iperf_peer(self,client):
        (stdin, stdout, stderr) = client.exec_command('iperf -s -p 5500 &')
        for line in stdout.readlines():
            self._log.debug(line)

        if stderr:
            for line in stderr.readlines():
                self._log.error(line)

    def gen_peer_interface_check(self,client, gen_nic_interface_name_peer_list):
        interface_indicator = True
        for gen_sprecific_interfaces_names in gen_nic_interface_name_peer_list:
            each_interface_gen_wise_list = gen_sprecific_interfaces_names.split(',')
            for nic_interface_name_peer_cfg in each_interface_gen_wise_list:
                self._log.debug("Checking presence in peer system for interface {}".format(nic_interface_name_peer_cfg))
                (stdin, stdout, stderr) = client.exec_command('ifconfig {}'.format(nic_interface_name_peer_cfg))
                for line in stdout.readlines():
                    self._log.debug(line)

                self._log.debug("Peer interface {} present".format(nic_interface_name_peer_cfg))

                for line in stderr.readlines():
                    self._log.error(line)

                (stdin, stdout, stderr) = client.exec_command('echo "$?"')
                for op_line in stdout.readlines():
                    self._log.debug(op_line)
                if '0' not in op_line:
                    interface_indicator = False

        return interface_indicator

    def gen_assign_static_ip_peer(self,client, gen_static_ip_peer_list, gen_nic_interface_name_peer_list):
        if len(gen_static_ip_peer_list) == len(gen_nic_interface_name_peer_list):
            for i in range(len(gen_static_ip_peer_list)):
                each_interface_gen_wise_list = gen_nic_interface_name_peer_list[i].split(',')
                each_static_ip_gen_wise_list = gen_static_ip_peer_list[i].split(',')
                if len(each_interface_gen_wise_list) == len(each_static_ip_gen_wise_list):
                    for j in range(len(each_static_ip_gen_wise_list)):
                        self._log.debug("Assigning static ip for peer interface {}".format(each_interface_gen_wise_list[j]))
                        (stdin, stdout, stderr) = client.exec_command('ifconfig {} {} up'.format(each_interface_gen_wise_list[j], each_static_ip_gen_wise_list[j]))
                        for line in stdout.readlines():
                            self._log.debug(line)
                        self._log.debug("static ip for interface {} assigned to {}.".format(each_interface_gen_wise_list[j], each_static_ip_gen_wise_list[j]))

        (stdin, stdout, stderr) = client.exec_command('systemctl disable firewalld')
        self._log.debug("Firewall disabled in peer system")

    def gen_start_iperf_peer(self,client):

        self._log.debug("Starting iperf in peer system for port 5500")
        (stdin, stdout, stderr) = client.exec_command('iperf -s -p 5500 &')
        for line in stdout.readlines():
            self._log.debug(line)

        if stderr:
            for line in stderr.readlines():
                self._log.error(line)

    def gen_sut_interface_check(self,gen_nic_interface_name_peer_list):
        interface_indicator = True
        for i in gen_nic_interface_name_peer_list:
            for nic_interface_name_sut_cfg in i.split(','):

                self._log.debug("Verifying in SUT for presence of interface {}".format(nic_interface_name_sut_cfg))
                interface_presence_check = self._common_content_lib.execute_sut_cmd(sut_cmd = 'ifconfig {}'.format(nic_interface_name_sut_cfg),
                                                                                    execute_timeout=self._command_timeout,
                                                                                    cmd_str= 'sut_interface check')
                # self._log.debug(interface_presence_check)
                echo_check = self._common_content_lib.execute_sut_cmd(sut_cmd = 'echo "$?"',
                                                                                    execute_timeout=self._command_timeout,
                                                                                    cmd_str= 'sut_interface check')
                self._log.debug(echo_check)
                if '0' not in echo_check:
                    interface_indicator = False
                else:
                    self._log.debug("interface {} present in SUT")

        return interface_indicator

    def gen_assign_static_ip_sut(self,gen_nic_interface_name_peer_list, gen_static_ip_sut_list):
        if len(gen_static_ip_sut_list) == len(gen_nic_interface_name_peer_list):
            for i in range(len(gen_static_ip_sut_list)):
                each_interface_gen_wise_list = gen_nic_interface_name_peer_list[i].split(',')
                each_static_ip_gen_wise_list = gen_static_ip_sut_list[i].split(',')
                if len(each_interface_gen_wise_list) == len((each_static_ip_gen_wise_list)):

                    for j in range(len(each_static_ip_gen_wise_list)):
                        sut_static_ip = self._common_content_lib.execute_sut_cmd(
                            sut_cmd='ifconfig {} {} up'.format(each_interface_gen_wise_list[j], each_static_ip_gen_wise_list[j]),
                            execute_timeout=self._command_timeout,
                            cmd_str='assigning static ip sut')
                        self._log.debug(sut_static_ip)


    def gen_ping_sut_to_peer(self, gen_static_ip_peer_list):
        ping_indicator = True
        for i in gen_static_ip_peer_list:
            for static_ip_peer_cfg in i.split(','):

                peer_static_ip = static_ip_peer_cfg.split('/')
                self._log.info("pinging peer interface with ip {} for 6 seconds".format(peer_static_ip[0]))
                ping_result = self._common_content_lib.execute_sut_cmd(
                    sut_cmd='ping -c 6 {}'.format(peer_static_ip[0]),
                    execute_timeout=self._command_timeout,
                    cmd_str='pinging to peer')
                # self._log.debug(ping_result)
                if 'ttl=64' in ping_result:
                    self._log.debug('Ping successful for peer static ip {}'.format(peer_static_ip[0]))

                else:
                    self._log.debug('Ping between client and server unsuccessful')
                    ping_indicator = False

        return ping_indicator

    def gen_start_iperf_sut(self, static_ip_peer_cfg):

        duration_iperf_op_cfg = self._common_content_configuration.get_duration_iperf_op()
        duration_iperf_run_cfg = self._common_content_configuration.get_workload_time()
        parallel_thread_count_cfg = self._common_content_configuration.get_parallel_thread_count()
        ip_peer = static_ip_peer_cfg.split('/')
        iperf_output =  self._common_content_lib.execute_sut_cmd(
            sut_cmd=' iperf -c {} -p 5500 -i {} -t {} -P {}'.format
            (ip_peer[0], duration_iperf_op_cfg, duration_iperf_run_cfg,parallel_thread_count_cfg),
            execute_timeout=self._command_timeout,
            cmd_str='initiating iperf on client')
        self._log.debug(iperf_output)
        if 'Bandwidth' in iperf_output and 'Transfer' in iperf_output:
            self._log.info("Network traffic test passed for interface static ip {}".format(ip_peer[0]))

    def network_traffic_test_iperf(self):
        peer_connection_check, peer_client = self.peer_ssh_connection()
        if peer_connection_check == True:
            peer_interface_presence_check = self.peer_interface_check(peer_client)
            if peer_interface_presence_check == True:
                self.assign_static_ip_peer(peer_client)
                peer_iperf_present = self.peer_iperf_check(peer_client)
                if peer_iperf_present == True:

                    t11 = threading.Thread(target=self.start_iperf_peer, args=(peer_client,))
                    t11.start()

                elif peer_iperf_present == False:
                    self._log.error('Iperf not installed in peer system. Please install before running test.')
            elif peer_interface_presence_check == False:
                self._log.error(
                    'Could not find specified interface {} in peer system'.format(
                        self._common_content_configuration.get_nic_interface_name_peer()))
        elif peer_connection_check == False:
            self._log.error('Test failed as peer connection could not be established..')
            raise content_exceptions.TestFail('Test failed as peer connection could not be established..')

        # peer_client.close()
        interface_presence_check = self.sut_interface_check()
        if interface_presence_check == True:
            self.assign_static_ip_sut()
            self.disable_firewall_sut()
            ping_result = self.ping_sut_to_peer()
            # ping_result = True
            if ping_result == True:
                self._log.info("All prerequisites successfully completed before Network Traffic test")
                t21 = threading.Thread(target=self.start_iperf_sut)
                sub_thread_log_handler = self._thread_logger.thread_logger(t21)
                time.sleep(1)
                t21.start()
                t11.join()
                t21.join()
                self._thread_logger.stop_thread_logging(sub_thread_log_handler)
                peer_client.close()

            else:
                self._log.error('test failed as server client ping was unsuccessful')
                # raise content_exceptions.TestFail('test failed as server client ping was unsuccessful')

        elif interface_presence_check == False:
            raise content_exceptions.TestFail('test failed ')

    def cpu_stress_mprime(self,mprime_sut_folder_path):
        ARGUMENT_IN_DICT = {"Join Gimps?": "N", "Your choice": "15", "Number of cores to torture test": "0",
                            "Number of torture test threads to run": "96",
                            "Use hyperthreading": "Y", "Type of torture test to run ": "1",
                            "Customize settings": "N", "Run a weaker torture test": "N",
                            "Accept the answers above?": "Y"}

        UNEXPECTED_EXPECT = ["Your choice", "Join Gimps?", "Customize settings", "Run a weaker torture test"]
        core_count = self._common_content_lib.get_core_count_from_os()[0]
        self._log.debug('Number of cores %d', core_count)
        core_count = int(core_count / 2)
        if ARGUMENT_IN_DICT.get("Number of cores to torture test", None):
            ARGUMENT_IN_DICT["Number of cores to torture test"] = \
                str(core_count)
        (unexpected_expect, successfull_test) = \
            self._stress_provider.execute_mprime(arguments=ARGUMENT_IN_DICT, execution_time=
            self._common_content_configuration.get_workload_time(), cmd_dir=
                                                 mprime_sut_folder_path.strip())
        self._log.debug(unexpected_expect)
        self._log.debug(successfull_test)
        if len(successfull_test) != core_count:
            raise content_exceptions.TestFail('Torture Test is not started on {} threads'.format(core_count))
        else :
            self._log.debug("CPU stress test passed ")
        invalid_expect = []
        for expect in unexpected_expect:
            if expect not in UNEXPECTED_EXPECT:
                invalid_expect.append(expect)
        self._log.debug(invalid_expect)
        # if invalid_expect:
        #     raise content_exceptions.TestFail('%s are Mandatory options for torture Test' % invalid_expect)
        self._stress_provider.check_app_running(app_name=Mprime95ToolConstant.MPRIME_TOOL_NAME,
                                                stress_test_command="./" + Mprime95ToolConstant.MPRIME_TOOL_NAME)

    def memory_stress_stressapptest(self, stdout_msg):
        if 'Stressapptest is installed' in stdout_msg:

            cpu_stressapp_test_details = self.stressapp_memory_stress_test()
            if 'Status: PASS' in cpu_stressapp_test_details:
                pass
            else:
                raise content_exceptions.TestFail('Memory stress app test failed')

        else:
            self._log.error("Stressapp is not installed")
            raise content_exceptions.TestFail("Memory Stress app failed as Stressapp is not installed")

    def ltssm_test(self,ltssm_folder_path):
        execution_status = self.LTSSM_tool_test(ltssm_folder_path)
        self._stress_provider.check_app_running(app_name=LttsmToolConstant.LTSSM_TOOL_SUT_FOLDER_NAME_LINUX,
                                                stress_test_command="./" + LttsmToolConstant.LTSSM_TOOL_SUT_FOLDER_NAME_LINUX)
        if execution_status == 0:
            self._log.debug('LTSSM Test passed')
        else:
            self._log.error('LTSSM Test failed')

    def execute_imunch(self):
        self._common_content_lib.execute_sut_cmd(sut_cmd='systemctl daemon-reload',
                                                 execute_timeout=self._command_timeout, cmd_str='daemon reload')
        self._common_content_lib.execute_sut_cmd(sut_cmd='systemctl restart docker',
                                                 execute_timeout=self._command_timeout,
                                                 cmd_str='systemctl restart docker')
        self._common_content_lib.execute_sut_cmd(sut_cmd='systemctl disable firewalld',
                                                 execute_timeout=self._command_timeout,
                                                 cmd_str='systemctl disable firewalld')
        self._common_content_lib.execute_sut_cmd(sut_cmd='systemctl disable firewalld',
                                                 execute_timeout=self._command_timeout,
                                                 cmd_str='systemctl disable firewalld')
        self._common_content_lib.execute_sut_cmd(
            sut_cmd='docker pull prt-registry.sova.intel.com/sandstone:imunch-2.9.0-official',
            execute_timeout=self._command_timeout,
            cmd_str='executing docker imunch pull')

        execution_details = self._common_content_lib.execute_sut_cmd(
            sut_cmd='docker run -i --rm --privileged --entrypoint /bin/bash prt-registry.sova.intel.com/sandstone:imunch-2.9.0-official '
                    '/tests/run-test.sh /tests/imunch {}'.format(self._common_content_configuration.get_workload_time()),
            execute_timeout=self._command_timeout, cmd_str='executing Imunch stress')


    def launch_harasser(self):
        pmutil_run = str(self._common_content_configuration.get_workload_time()//60)
        pmutil_snooze = self._common_content_configuration.get_pmutil_snoozetime()

        cstate_op = self._common_content_lib.execute_sut_cmd(
            sut_cmd='./pm_utility/pmutil_bin -t {} -y {} -cstate_harass=1'.format(pmutil_run, pmutil_snooze),
            execute_timeout=self._command_timeout,
            cmd_str='launch c-state harasser')
        self._log.debug(cstate_op)

        pstate_op = self._common_content_lib.execute_sut_cmd(
            sut_cmd='./pm_utility/pmutil_bin -t {} -y {} -pstate_harass=1'.format(pmutil_run, pmutil_snooze),
            execute_timeout=self._command_timeout,
            cmd_str='launch p-state harasser')
        self._log.debug(pstate_op)


        harasser_output = self._common_content_lib.execute_sut_cmd(
            sut_cmd='./pm_utility/pmutil_bin -t {} -y {} -socket_rapl_harass=1'.format(pmutil_run, pmutil_snooze),
            execute_timeout=self._command_timeout,
            cmd_str='launch harasser')

        self._log.debug(harasser_output)
        if 'harasser completed' in harasser_output:
            self._log.info("PM_harasser test passed")
        else :
            self._log.error("PM_harasser test failed")

    def accelerator_workload(self,qat_workload_reqd,dlb_workload_reqd,dsa_workload_reqd,iaa_workload_reqd):
        # Step logger start for Step 1

        qat_workload_thread = threading.Thread(target=self._accelerator_lib.run_qat_workload_on_host)
        qat_log_handler = self._thread_logger.thread_logger(qat_workload_thread)
        dlb_workload_thread = threading.Thread(target=self._accelerator_lib.run_dpdk_workload_on_host)
        dlb_log_handler = self._thread_logger.thread_logger(dlb_workload_thread)
        dsa_workload_thread = threading.Thread(target=self._accelerator_lib.dsa_workload_on_host)
        dsa_log_handler = self._thread_logger.thread_logger(dsa_workload_thread)
        iax_workload_thread = threading.Thread(target=self._accelerator_lib.iax_workload_on_host)
        iax_log_handler = self._thread_logger.thread_logger(iax_workload_thread)

        if qat_workload_reqd.lower() == 'true':
            qat_workload_thread.start()
        if dlb_workload_reqd.lower() == 'true':
            dlb_workload_thread.start()
        if dsa_workload_reqd.lower() == 'true':
            dsa_workload_thread.start()
        if iaa_workload_reqd.lower() == 'true':
            iax_workload_thread.start()

        qat_workload_thread.join()
        dlb_workload_thread.join()
        dsa_workload_thread.join()
        iax_workload_thread.join()

        self._thread_logger.stop_thread_logging(qat_log_handler)
        self._thread_logger.stop_thread_logging(dlb_log_handler)
        self._thread_logger.stop_thread_logging(dsa_log_handler)
        self._thread_logger.stop_thread_logging(iax_log_handler)

    def execute_fisher_command(self,workload_command):
        fisher_command = "fisher --workload='{}' --injection-type=memory-correctable --runtime={}".format(workload_command, self._common_content_configuration.get_workload_time())
        create_shell_script_cmd = "touch test.sh"
        self._log.debug(create_shell_script_cmd)


        insert_workload_cmd = 'echo "{}" > test.sh'.format(fisher_command)
        self._log.debug(insert_workload_cmd)

        delete_file_cmd = 'rm -rf test.sh'

        bash_cmd = "sh test.sh"
        self._common_content_lib.execute_sut_cmd(create_shell_script_cmd, create_shell_script_cmd,
                                                 self._command_timeout)
        self._common_content_lib.execute_sut_cmd(insert_workload_cmd, insert_workload_cmd, self._command_timeout)

        fisher_test = self._os.execute(bash_cmd, self._command_timeout, cwd="/root")
        self._common_content_lib.execute_sut_cmd(delete_file_cmd, delete_file_cmd, self._command_timeout)
        fisher_result = fisher_test.stderr

        self._log.debug(fisher_result)

    def non_raid_creation(self):
        sut_inv_file_path = self._os_installation_lib.get_sut_inventory_file_path()
        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if "non_raid_ssd_name" in line:
                    self.non_raid_disk_name = line
                    break

        if not self.non_raid_disk_name:
            raise content_exceptions.TestError("Unable to find non RAID SSD name, please check the file under "
                                               "{}".format(sut_inv_file_path))

        self.non_raid_disk_name = self.non_raid_disk_name.split("=")[1]
        self._log.info("non RAID SSD Name from config file : {}".format(self.non_raid_disk_name))
        self._common_content_lib.update_sut_inventory_file(SutInventoryConstants.NVME, self._os.os_subtype.lower())
        return self.non_raid_disk_name

    def cpu_monitoring(self):
        self._log.info("CPU workload starting")
        cpu_monitor_count = str(int(self._common_content_configuration.get_workload_time())//6)
        monitor_op = self._common_content_lib.execute_sut_cmd(sut_cmd="sar -u 6 {}".format(cpu_monitor_count),
                                                              execute_timeout=self._command_timeout,
                                                              cmd_str="executing sar -u 6 {}".format(cpu_monitor_count))

    def execute_geekbench(self):
        geekbench_workload_time = str(round(self._common_content_configuration.get_workload_time()/3600,2))
        self._common_content_lib.execute_sut_cmd(sut_cmd='systemctl daemon-reload',
                                                 execute_timeout=self._command_timeout, cmd_str='daemon reload')
        self._common_content_lib.execute_sut_cmd(sut_cmd='systemctl restart docker',
                                                 execute_timeout=self._command_timeout,
                                                 cmd_str='systemctl restart docker')
        self._common_content_lib.execute_sut_cmd(sut_cmd='systemctl disable firewalld',
                                                 execute_timeout=self._command_timeout,
                                                 cmd_str='systemctl disable firewalld')
        self._common_content_lib.execute_sut_cmd(
            sut_cmd='docker pull prt-registry.sova.intel.com/sandstone:ive-genie-geekbenchpintsx-v1p0-21ww41-4',
            execute_timeout=self._command_timeout,
            cmd_str='executing docker pull')

        execution_details = self._common_content_lib.execute_sut_cmd(
            sut_cmd='docker run -i --rm --privileged --entrypoint '
                    '/bin/bash prt-registry.sova.intel.com/sandstone:ive-genie-geekbenchpintsx-v1p0-21ww41-4 /run_content.sh -t {}'.format(geekbench_workload_time),
            execute_timeout=self._command_timeout, cmd_str='executing geekbench stress')

        self._log.debug(execution_details)


    def pcie_error_injection(self,ras_einj_obj):
        result_list = []
        for i in range(4):
            for val in ras_einj_obj._einj_pcie_bridge_list:
                addr = ras_einj_obj.einj_pcie_error_addr_sec_bus(val)
                result_list.append(
                    ras_einj_obj.einj_inject_and_check(ras_einj_obj.EINJ_PCIE_CORRECTABLE,
                                                             address=addr))


