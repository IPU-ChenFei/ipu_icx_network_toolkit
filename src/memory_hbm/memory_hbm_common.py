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
import re
import six
import sys
import time
import glob
import ntpath
import os.path
import zipfile
import platform
import subprocess
from os import path
from subprocess import Popen, PIPE, STDOUT

from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.memory_constants import MemoryTopology, MemoryClusterConstants
from src.lib.memory_constants import PlatformMode
from src.lib.platform_config import PlatformConfiguration
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import TimeConstants, StressAppTestConstants, RootDirectoriesConstants
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib.content_artifactory_utils import ContentArtifactoryUtils

from src.provider.stressapp_provider import StressAppTestProvider
from src.provider.cpu_info_provider import CpuInfoProvider
from src.provider.memory_provider import MemoryProvider, MemoryInfo

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.bios_menu import BiosSetupMenuProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.physical_control import PhysicalControlProvider


class MemoryHbmCommon(ContentBaseTestCase):
    """
    Class is mainly used to parse memory DDR and HBM.
    """
    HBM_MEMORY_PER_SOCKET = 64
    MEM_STREAM_CMD = "python mem-Stream.py"
    RUNNING_STREAM = "stream"
    STREAM_FOLDER = "app_logs/stream"
    EXECUTE_TIME = TimeConstants.ONE_HOUR_IN_SEC
    HBM_STREAM_CMD = "python hbm_stream.py --test=HBM-STREAM-001 --timeout={}".format(EXECUTE_TIME)
    SNC_BIOS_KNOB = "SncEn"
    QUAD_EXPECTED_VALUE = "0xe"
    SNC4_EXPECTED_VALUE = "0xf"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file_path=None):
        """
        Create a new MemoryHbmCommon object.
        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(MemoryHbmCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path)
        self._log = test_log
        self._cpu_info_provider = CpuInfoProvider.factory(self._log, cfg_opts, self.os)
        self._memory_provider = MemoryProvider.factory(self._log, cfg_opts=cfg_opts, os_obj=self.os)
        self._cpu_info_provider.populate_cpu_info()
        self._socket_present = int(self._cpu_info_provider.get_number_of_sockets())
        self._install_collateral = InstallCollateral(test_log, self.os, cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._silicon_family = self._common_content_lib.get_platform_family()
        self._artifactory_obj = ContentArtifactoryUtils(test_log, self.os, self._common_content_lib, cfg_opts)
        self.no_ping = 0
        self.threshold = 3
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_cfg, test_log)
        phy_cfg = cfg_opts.find(PhysicalControlProvider.DEFAULT_CONFIG_PATH)
        self._phy = ProviderFactory.create(phy_cfg, test_log)
        setupmenu_cfg = cfg_opts.find(BiosSetupMenuProvider.DEFAULT_CONFIG_PATH)
        self.setupmenu = ProviderFactory.create(setupmenu_cfg, test_log)
        bootmenu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self.bootmenu = ProviderFactory.create(bootmenu_cfg, test_log)

    @staticmethod
    def get_ddr_hbm_hardware_component_information(ddr_hbm_dict):
        """
        Function is used to separate ddr and hbm information.
        :return: ddr_info, hbm_info
        """
        ddr_info = {}
        hbm_info = {}
        for locator, value in ddr_hbm_dict.items():
            if PlatformMode.HBM_MODE in locator:
                hbm_info[locator] = value
            else:
                ddr_info[locator] = value
        return ddr_info, hbm_info

    def execute_prime95_windows(self, cmd, prime95_path):
        """
                Function to execute prime95 application.

                :param cmd: command to run prime95
                :param prime95_path: path of the executor.
                """
        self._log.info("Starting the prime95 test..")

        # -t refers to torture test
        self._log.info("prime95 test command line is '{}'".format(cmd))
        self._log.info("prime95 test is running from directory '{}'".format(prime95_path))

        prime95_execute_res = self.os.execute(cmd, TimeConstants.ONE_HOUR_IN_SEC, prime95_path)

        if prime95_execute_res.cmd_failed():
            self._log.info("Prime95 execution thread has been stopped...")

    def verify_number_of_nodes(self, memory_mode, cluster_mode):
        """
        This function is used to verify the number of nodes based on the memory mode like 1LM, 2LM, HBM and
        cluster mode like Quad, SNC4.
        :param memory_mode: memory modes like 1LM (Flat), 2LM (Cache), HBM only
        :param cluster_mode : like Quad, SNC4
        """
        # 1LM - Flat, 2LM - Cache, HBM only
        if memory_mode == MemoryTopology.TWO_LM and cluster_mode == MemoryClusterConstants.QUAD_STRING:
            number_of_nodes = self._socket_present * 1
        elif memory_mode == MemoryTopology.TWO_LM and cluster_mode == MemoryClusterConstants.SNC4_STRING:
            number_of_nodes = self._socket_present * 4
        elif memory_mode == MemoryTopology.ONE_LM and cluster_mode == MemoryClusterConstants.QUAD_STRING:
            number_of_nodes = self._socket_present * 2
        elif memory_mode == MemoryTopology.ONE_LM and cluster_mode == MemoryClusterConstants.SNC4_STRING:
            number_of_nodes = self._socket_present * 8
        elif memory_mode == PlatformMode.HBM_MODE and cluster_mode == MemoryClusterConstants.QUAD_STRING:
            number_of_nodes = self._socket_present * 1
        elif memory_mode == PlatformMode.HBM_MODE and cluster_mode == MemoryClusterConstants.SNC4_STRING:
            number_of_nodes = self._socket_present * 4
        else:
            raise content_exceptions.TestFail("Please check modes ...")

        node_list_os = self._memory_provider.get_snc_node_info()
        self._log.info("Expected Number of nodes for mode '{}' with '{}' for '{}' sockets are : {}".
                       format(memory_mode, cluster_mode, self._socket_present, number_of_nodes))
        self._log.info("Nodes list from the OS is : {}".format(node_list_os))
        self._log.info("Number of nodes from the OS are : {}".format(len(node_list_os)))

        if number_of_nodes != len(node_list_os):
            error_statement = "The number of nodes in the system is not " \
                              "correct : For mode {} with {} for {} sockets and only {} node(s) are present.." \
                .format(memory_mode, cluster_mode, self._socket_present, len(node_list_os))
            raise content_exceptions.TestFail(error_statement)

    def snc_check_with_pythonsv_values(self, bios_file_path, expected_reg_value):
        """
        Function to set and verify the bios knobs and verify the PythonSv values for SNC4
        """
        self.set_and_verify_bios_knobs(bios_file_path)

        self.initialize_sv_objects()
        self.initialize_sdp_objects()

        self.SDP.itp.unlock()  # To execute itp.unlock()
        ltssm_obj = self.SV.get_ltssm_object()
        ltssm_obj.sls()  # To execute sls() command
        # To get Socket count
        sockets_count = self.SV.get_socket_count()
        self._log.info("Socket count : {}".format(sockets_count))

        for each_socket in range(0, sockets_count):
            # Executing sv.sockets.uncore.upi.upi0.ktilk_snc_config for each socket.
            value = self.SV.get_by_path(
                self.SV.UNCORE, PlatformConfiguration.MEMORY_KTILK_SNC_CONFIG[self._silicon_family],
                socket_index=each_socket)
            self._log.info("Socket {} value is : {}".format(each_socket, value))

            if expected_reg_value not in hex(value):
                raise content_exceptions.TestFail("value: {} not matched with expected value : {} for "
                                                  "socket{}".format(value, expected_reg_value, each_socket))
            self._log.error("ktilk_snc_config value: {} matched with expected value : {} for socket{}".
                            format(value, expected_reg_value, each_socket))

    def verify_installed_hbm_memory(self):
        """
        This function is used to verify the installed HBM memory in the SUT
        """
        # Get the list of configured memory sizes of installed dimm
        installed_memory_size_dict = self._memory_provider.get_installed_hardware_component_information(MemoryInfo.SIZE)
        ddr_size_dict, hbm_size_dict = self.get_ddr_hbm_hardware_component_information(
            installed_memory_size_dict)
        self._log.info("HBM memory list : {}".format(hbm_size_dict))
        if OperatingSystems.WINDOWS == self.os.os_type:
            total_hbm_memory = sum(map(int, hbm_size_dict.values())) / 1024
        elif OperatingSystems.LINUX == self.os.os_type:
            total_hbm_memory = sum(map(int, hbm_size_dict.values()))
        else:
            raise NotImplementedError("Test is not implemented for %s" % self.os.os_type)
        total_hbm_memory_config = self._socket_present * self.HBM_MEMORY_PER_SOCKET
        self._log.info("Total HBM memory in SUT is : {}".format(total_hbm_memory))
        self._log.info("Total HBM memory in from config is : {}".format(total_hbm_memory_config))
        if total_hbm_memory != total_hbm_memory_config:
            raise content_exceptions.TestFail("HBM memory not matched in SUT ...")
        self._log.info("HBM Memory matched in the SUT ...")

        return True

    def mem_stream_test(self):
        """
        This function is used to execute mem stream test
        """
        # Copy mem Stream from ATF to SUT
        zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder("mem-Stream.zip")
        sut_path = self._common_content_lib.copy_zip_file_to_linux_sut(self.STREAM_FOLDER, zip_file_path)

        self._log.info("Executing the command : {}".format(self.MEM_STREAM_CMD))

        self._install_collateral.screen_package_installation()

        self._log.info("Starting the Mem Stream '{}'".format(self.MEM_STREAM_CMD))
        self.os.execute_async(self.MEM_STREAM_CMD, cwd=sut_path)
        time.sleep(self.WAIT_TIME)

        if not self._stress_provider.check_app_running(self.RUNNING_STREAM, self.RUNNING_STREAM):
            raise content_exceptions.TestFail("Mem Stream is not running")
        self._log.info("Mem-Stream is started to run ...")

        stress_execute_time = time.time() + self.EXECUTE_TIME - (2 * TimeConstants.ONE_MIN_IN_SEC)
        while time.time() < stress_execute_time:
            time.sleep(TimeConstants.ONE_MIN_IN_SEC)
            if not (self.os.is_alive() and
                    self._stress_provider.check_app_running(self.RUNNING_STREAM, self.RUNNING_STREAM)):
                self.no_ping += 1
                if self.no_ping == self.threshold:
                    raise content_exceptions.TestFail("System did not ping for 3 times during Mem-Stream test run..."
                                                      "Exiting the test...")
            self._log.info("SUT is alive and Mem-Stream tool is running ...")

        self._stress_provider.kill_stress_tool(self.RUNNING_STREAM, self.RUNNING_STREAM)

    def hbm_stream_test(self):
        """
        This function is used to execute mem stream test
        """
        # Copy mem Stream from ATF to SUT
        zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder("hbm_stream.zip")
        sut_path = self._common_content_lib.copy_zip_file_to_linux_sut(self.STREAM_FOLDER, zip_file_path)

        self._log.info("Executing the command : {}".format(self.HBM_STREAM_CMD))

        self._install_collateral.screen_package_installation()

        self._log.info("Starting the HBM Stream '{}'".format(self.HBM_STREAM_CMD))
        self.os.execute_async(self.HBM_STREAM_CMD, cwd=sut_path)
        time.sleep(self.WAIT_TIME)

        if not self._stress_provider.check_app_running(self.RUNNING_STREAM, self.RUNNING_STREAM):
            raise content_exceptions.TestFail("HBM Stream is not running")
        self._log.info("HBM-Stream is started to run ...")

        stress_execute_time = time.time() + self.EXECUTE_TIME - (2 * TimeConstants.ONE_MIN_IN_SEC)
        while time.time() < stress_execute_time:
            time.sleep(TimeConstants.ONE_MIN_IN_SEC)
            if self.os.is_alive():
                if not self._stress_provider.check_app_running(self.RUNNING_STREAM, self.RUNNING_STREAM):
                    self._log.info("SUT is alive but HBM-Stream tool stopped running ...")
                    break

            if not (self.os.is_alive() and
                    self._stress_provider.check_app_running(self.RUNNING_STREAM, self.RUNNING_STREAM)):
                self.no_ping += 1
                if self.no_ping == self.threshold:
                    raise content_exceptions.TestFail("System did not ping for 3 times during HBM-Stream test run..."
                                                      "Exiting the test...")
            self._log.info("SUT is alive and HBM-Stream tool is running ...")

        self._stress_provider.kill_stress_tool(self.RUNNING_STREAM, self.RUNNING_STREAM)

    def get_default_cluster_mode(self):
        """
        This method returns the Default cluster mode enabled on the Platform.

        return: Cluster mode
        """
        cluster_mode = MemoryClusterConstants.QUAD_STRING
        # Get the current value of SNC knob from Platform config
        ret_value = self.bios_util.get_bios_knob_current_value(self.SNC_BIOS_KNOB)
        ret_value = ret_value.replace("\\r","").replace("\\n","")
        self._log.info("Current value of SNC bios knob is {}".format(ret_value))
        if ret_value == "0x0F":
            cluster_mode = MemoryClusterConstants.SNC4_STRING
        self._log.info("Default Mode enabled on this Platform is : {}".format(cluster_mode))
        return cluster_mode

    def snc_check_with_pythonsv_value(self, expected_reg_value):
        """
        Function to check snc mode

        :param expected_reg_value: check which value to check
        """
        self.initialize_sv_objects()
        self.initialize_sdp_objects()

        self.SDP.itp.unlock()  # To execute itp.unlock()
        ltssm_obj = self.SV.get_ltssm_object()
        ltssm_obj.sls()  # To execute sls() command
        # To get Socket count
        sockets_count = self.SV.get_socket_count()
        self._log.info("Socket count : {}".format(sockets_count))

        pythonsv_cmd = eval("PlatformConfiguration.MEMORY_SNC_CONFIG[self._silicon_family]")

        if expected_reg_value == self.SNC4_EXPECTED_VALUE:
            pythonsv_cmd = eval("PlatformConfiguration.MEMORY_KTILK_SNC_CONFIG[self._silicon_family]")

        for each_socket in range(0, sockets_count):
            value = self.SV.get_by_path(self.SV.UNCORE, pythonsv_cmd, socket_index=each_socket)
            self._log.info("Socket {} value is : {}".format(each_socket, value))

            if expected_reg_value not in hex(value):
                raise content_exceptions.TestFail("value: {} not matched with expected value : {} for "
                                                  "socket{}".format(value, expected_reg_value, each_socket))
            self._log.error("Value: {} matched with expected value : {} for socket{}".
                            format(value, expected_reg_value, each_socket))

    def check_usb_name(self, usb_drive_name):

        if usb_drive_name:
            usb_new = ""
            usb_split = usb_drive_name.split()
            for word in usb_split:
                if len(word) > 16:
                    usb_new = usb_new + "[\s\S]*"
                    break
                else:
                    usb_new = usb_new + " " + word

            usb_drive_name_temp = usb_new.strip()

        if usb_drive_name_temp is None:
            usb_drive_name_temp = usb_drive_name

        self._log.info("Shows the usb name is a Regex or direct name --> {}".format(usb_drive_name_temp))

        return usb_drive_name_temp

    def format_usb_drive(self, size):
        """
        Function to format the usb drive before copying the memtest86 tool
        :- size Pendrive Size accepted size values are 8,16,32,64
        """
        size = str(size)
        if str(platform.architecture()).find("WindowsPE") != -1:
            try:
                p = Popen(["diskpart"], stdin=PIPE, stdout=PIPE)
                if six.PY2:
                    ret = p.stdin.write(b'rescan \n')
                    ret = p.stdin.write(b'list disk \n')
                    ret = p.stdin.write(b'exit \n')
                    ret = p.stdout.read()
                    a = ret.split(",")
                    a = str(a).strip()
                    a = " ".join(a.split())
                elif six.PY3:
                    ret = p.stdin.write(bytes("rescan \n", encoding='utf-8'))
                    time.sleep(2)
                    ret = p.stdin.write(bytes("list disk \n", encoding='utf-8'))
                    time.sleep(2)
                    ret = p.stdin.write(bytes("exit \n", encoding='utf-8'))
                    ret = p.communicate()
                    a = str(ret).split(",")
                    a = str(a).strip()
                    a = " ".join(a.split())
                try:
                    if size == "8":
                        for i in ("7 GB", "7.8 GB", "7.5 GB", "6 GB", "6.5 GB", "6.8 GB"):
                            try:
                                if a.index(str(i)) != -1:
                                    index = a.index(str(i))
                                    self._log.info(
                                        "Usb Available Size That was Found {0} {1}".format(a[index:index + 2], "GB"))
                                    data = (a[index - 19:index + 2])
                                    break
                            except:
                                continue
                    elif size == "16":
                        for i in ("14 GB", "14.5 GB", "13 GB", "12.5 GB", "13.5 GB"):
                            try:
                                if a.index(str(i)) != -1:
                                    index = a.index(str(i))
                                    self._log.info(
                                        "Usb Available Size That was Found {0} {1}".format(a[index:index + 2], "GB"))
                                    data = (a[index - 20:index + 2])
                                    break
                            except:
                                continue
                    elif size == "32":
                        for i in ("27 GB", "27.5 GB", "28 GB", "28.5 GB", "28.8 GB","28.2 GB","28.7 GB","28.9 GB", "29 GB","29.2 GB","29.3 GB","29.5 GB"):
                            try:
                                if a.index(str(i)) != -1:
                                    index = a.index(str(i))
                                    self._log.info(
                                        "Usb Available Size That was Found {0} {1}".format(a[index:index + 2], "GB"))
                                    data = (a[index - 20:index + 2])
                                    break
                            except:
                                continue
                    elif size == "64":
                        for i in ("57 GB", "57.5 GB","56 GB", "56.5 GB", "56.8 GB", "57.8 GB", "58 GB", "58.5 GB", "59.5 GB", "60 GB"):
                            try:
                                if a.index(str(i)) != -1:
                                    index = a.index(str(i))
                                    self._log.info(
                                        "Usb Available Size That was Found {0} {1}".format(a[index:index + 2], "GB"))
                                    data = (a[index - 20:index])
                                    break
                            except:
                                continue
                    else:
                        self._log.error(
                            "Please Ensure that pendrive size is Correct and Connected To Host-Machine Supported size "
                            "of USb 8,16,32,64gb {0}".format(
                                ret))
                        return False
                    mb = (int(a[index:index + 2]) * 1000)
                    ntfs = (mb - 4000)
                    fat_size = 3000
                except Exception as ex:
                    self._log.error(
                        "Please Ensure that pendrive size is Correct and Connected To Host-Machine Supported size of "
                        "USb 8,16,32,64gb {0}".format(
                            ex))
                    return False
                a = ["Disk 1", "Disk 2", "Disk 3", "Disk 4"]
                for i in range(0, 10):
                    if a[i] in data:
                        pendrive_disk = a[i]
                        self._log.info("This {0} is USB_Device".format(pendrive_disk))
                        break
                time.sleep(10)
                try:
                    if six.PY2:
                        p = Popen([b'diskpart'], stdin=PIPE)
                        res1 = p.stdin.write(b'list vol \n')
                        time.sleep(4)
                        p.stdin.flush()
                        res1 = p.stdin.write(b'rescan \n')
                        time.sleep(4)
                        p.stdin.flush()
                        res1 = p.stdin.write(b'list disk \n')
                        time.sleep(1)
                        p.stdin.flush()
                        res1 = p.stdin.write(b'select ' + str(pendrive_disk) + ' \n')
                        time.sleep(1)
                        p.stdin.flush()
                        try:
                            res4 = p.stdin.write(b'clean \n')
                            time.sleep(5)
                            p.stdin.flush()
                        except:
                            res4 = p.stdin.write(b'clean \n')
                            time.sleep(5)
                            p.stdin.flush()
                        res1 = p.stdin.write(b'rescan \n')
                        time.sleep(5)
                        p.stdin.flush()
                        res1 = p.stdin.write(b'select ' + str(pendrive_disk) + ' \n')
                        time.sleep(2)
                        p.stdin.flush()
                        res6 = p.stdin.write(b"create partition primary \n")
                        time.sleep(3)
                        p.stdin.flush()
                        res6 = p.stdin.write(b"FORMAT FS=fat32 Label=MemTest86 QUICK \n")
                        time.sleep(6)
                        p.stdin.flush()
                        res7 = p.stdin.write(b"assign letter=H \n")
                        time.sleep(2)
                        p.stdin.flush()
                        res8 = p.stdin.write(b"active \n")
                        time.sleep(2)
                        p.stdin.flush()
                        res8 = p.stdin.write(b"exit \n")
                        time.sleep(2)
                        p.stdin.flush()
                    elif six.PY3:
                        p = Popen(['diskpart'], stdin=PIPE)
                        res1 = p.stdin.write(bytes('list vol \n', encoding='utf8'))
                        time.sleep(4)
                        p.stdin.flush()
                        res1 = p.stdin.write(bytes('rescan \n', encoding='utf8'))
                        time.sleep(2)
                        p.stdin.flush()
                        res1 = p.stdin.write(bytes('list disk \n', encoding='utf8'))
                        time.sleep(2)
                        p.stdin.flush()
                        res1 = p.stdin.write(bytes('select ' + str(pendrive_disk) + ' \n', encoding='utf8'))
                        time.sleep(2)
                        p.stdin.flush()
                        try:
                            res4 = p.stdin.write(bytes('clean \n', encoding='utf8'))
                            time.sleep(8)
                            p.stdin.flush()
                        except:
                            res1 = p.stdin.write(bytes('rescan \n', encoding='utf8'))
                            time.sleep(3)
                            p.stdin.flush()
                            res1 = p.stdin.write(bytes('select ' + str(pendrive_disk) + ' \n', encoding='utf8'))
                            time.sleep(2)
                            p.stdin.flush()
                            res4 = p.stdin.write(bytes('clean \n', encoding='utf8'))
                            time.sleep(8)
                            p.stdin.flush()

                        res1 = p.stdin.write(bytes('select ' + str(pendrive_disk) + ' \n', encoding='utf8'))
                        time.sleep(2)
                        p.stdin.flush()
                        res6 = p.stdin.write(
                            bytes("create partition primary \n", encoding='utf8'))
                        time.sleep(3)
                        p.stdin.flush()
                        res6 = p.stdin.write(bytes("FORMAT FS=fat32 Label=MemTest86 QUICK \n", encoding='utf8'))
                        time.sleep(6)
                        p.stdin.flush()
                        res7 = p.stdin.write(bytes("assign letter=H \n", encoding='utf8'))
                        time.sleep(2)
                        p.stdin.flush()
                        res8 = p.stdin.write(bytes("active \n", encoding='utf8'))
                        time.sleep(2)
                        p.stdin.flush()
                        res8 = p.stdin.write(bytes("exit \n", encoding='utf8'))
                        time.sleep(2)
                        p.stdin.flush()
                    # Downloading memtest86 from ATF Frog
                    if str(platform.architecture()).find("WindowsPE") != -1:
                        zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder\
                            ("memtest86.zip", "UEFI")
                    else:
                        self._log.info("NOT yet Implemented for Linux")
                    # Extracting MemTest86
                    self._log.info("MemTest86 Tool Extraction To Pendrive In-Progress")
                    if str(platform.architecture()).find("WindowsPE") != -1:
                        Target_path = "H:"
                        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                            zip_ref.extractall(Target_path)
                            zip_ref.close()
                        self._log.info("MemTest86 Tool Extraction To Pendrive Successfull")
                        return True
                    elif str(platform.architecture()).find(r"ELF") != -1:
                        self._log.info("NOT yet Implemented for Linux")
                        return True
                except Exception as ex:
                    self._log.error("Issues Encounterd While Formatting Pendrive: {0}".format(ex))
                    return False
            except Exception as ex:
                self._log.info("Runas Administrator Priveillage Needs To Be Given {0}".format(ex))
                return False
        elif (str(platform.architecture()).find(r"ELF") != -1):
            self._log.error("Not yet Implemented for LINUX Hostmachines")

    def platform_ac_power_off(self):

        if self._ac.ac_power_off() == True:
            self._log.info("Platfor(SUT) AC-power TURNED OFF")
        else:
            self._log.error("Failed TO Do AC-power OFF")
            return False
        # Making Sure Platform AC-Power is Turned OFF
        if self._ac.get_ac_power_state() == False:
            self._log.info("Platform(SUT) AC-power TURNED-OFF Confrimed")
            time.sleep(3)
            return True
        else:
            self._log.error("Platform(SUT) AC-power TURNED-Off Confrimation failed")
            return False

    def platform_ac_power_on(self):
        if self._ac.ac_power_on() == True:
            self._log.info("Platfor(SUT) AC-power TURNED ON")
        else:
            self._log.error("Failed TO Do AC-power ON")
            return False
        time.sleep(4)
        if self._ac.get_ac_power_state() == True:
            self._log.info("Platform(SUT) AC-power TURNED-ON Confrimed")
            time.sleep(5)
            return True
        else:
            self._log.error("Failed To Platform(SUT) AC-power TURNED-Off Confrimation")
            return False

    def switch_usb_to_target(self):  # changed
        if (self._phy.connect_usb_to_sut() != True):
            self._log.error("USB Switching To SUT Failed")
            return False
        return True

    def switch_usb_to_host(self):  # changed
        if (self._phy.connect_usb_to_host() != True):
            self._log.error("USB Switching To Host Failed")
            return False
        return True

    def bios_path_navigation(self, path):
        path = path.split(',')
        try:
            for i in range(len(path)):
                time.sleep(10)
                ret = self.setupmenu.get_page_information()
                ret = self.setupmenu.select(str(path[i]), None, 60, True)
                print(self.setupmenu.get_selected_item().return_code)
                self.setupmenu.enter_selected_item(False,10)
                self._log.info("Entered into {0} ".format(path[i]))
            return True
        except Exception as ex:
            self._log.error("{0} Issues Observed".format(ex))
            return False

    def enter_into_bios(self):
        self._log.info("Waiting To Enter Into Bios Setup Menu")
        ret=self.setupmenu.wait_for_entry_menu(10000)
        for i in range(0, 10):
            f2_state = self.setupmenu.press(r'F2')
            time.sleep(0.3)
            if f2_state:
                self._log.info("F2 keystroke Pressed")
                break
        ret = self.setupmenu.wait_for_bios_setup_menu(30)
        if(str(ret) == "SUCCESS"):
            self._log.info("Entered Into Bios Menu")
            return True
        else:
            self._log.error("Failed To Enter Into Bios Menu Page,Close COM Port if opened in Putty Check")
            return False

    def press_button(self, button_to_press, not_ignore, timeout):
        for i in range(0, 10):
            state = self.setupmenu.press_key(button_to_press, not_ignore, timeout)
            time.sleep(0.3)
            if state:
                self._log.info("{} keystroke Pressed".format(button_to_press))
                break

