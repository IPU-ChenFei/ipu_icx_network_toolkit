#!/usr/bin/env python
##########################################################################
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
##########################################################################
import os
import re
import threading
from pathlib import Path
import time
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.lib import content_exceptions
from src.rdt.lib.rdt_utils import RdtUtils
from dtaf_core.lib.dtaf_constants import OperatingSystems, ProductFamilies
from dtaf_core.providers.provider_factory import ProviderFactory
from src.pcie.lib.pcie_common_utils import PcieCommonUtil
from src.lib.dtaf_content_constants import IntelPcieDeviceId, WindowsMemrwToolConstant, CommonConstants

from src.lib.dtaf_content_constants import IntelPcieDeviceId
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from src.lib.dtaf_content_constants import PcieCyclingConstant
from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.pcie_provider import PcieProvider
from src.lib.dtaf_content_constants import PcieAttribute, PcieSlotAttribute
from src.provider.storage_provider import StorageProvider
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import LinuxCyclingToolConstant
from src.pcie.lib.slot_mapping_utils import SlotMappingUtils

from src.provider.pcie_ltssm_provider import PcieLtssmToolProvider


class LtssmTestType:
    ASPML1 = "aspml1"
    LINKDISABLE = "linkDisable"
    LINKRETRAIN = "linkRetrain"
    PML1 = "pml1"
    SBR = "sbr"
    SPEEDCHANGE = "SpeedChange"
    SPEEDCHANGE_ALL = "SpeedChangeAll"
    TXEQREDO = "txEqRedo"


class PxpInventory:
    def __init__(self, sdp_obj, pcie_obj, sls_log):
        """
        Class returns a PxpInventory object

        :param sdp_obj: sdp object
        :param pcie_obj: pcie object instantiated from cscripts or pythosv reg provider
        :param sls_log: reference to log file to store output from sls() command
        """
        self._sdp_obj = sdp_obj
        self._pcie_obj = pcie_obj
        self._sls_log = sls_log

    class IOProtocol:
        PCIE = "PCIE"
        CXL = "CXL"

    class PCIeLinkSpeed:
        GEN1 = "GEN1"
        GEN2 = "GEN2"
        GEN3 = "GEN3"
        GEN4 = "GEN4"
        GEN5 = "GEN5"
        MAPPING = {GEN1: "2.5", GEN2: "5", GEN3: "8", GEN4: "16", GEN5: "32"}
        GEN_DICT = {GEN1: "0x1", GEN2: "0x2", GEN3: "0x3", GEN4: "0x4", GEN5: "0x5"}


    class PCIeLinkWidth:
        x0 = "0"
        x2 = "2"
        x4 = "4"
        x8 = "8"
        x16 = "16"

    def get_slot_inventory(self, platform=ProductFamilies.SPR, silicon_reg_provider_obj=None,
                           positive_link_width_only=False):
        """
        This method is to get the pcie slots dict.

        :param platform
        :param silicon_reg_provider_obj
        :return {'PCIE': {'0': {'pxp1.pcieg5.port0': {'speed': 'GEN4', 'width': 'x8', 'bifurcation': 'x8'},
        'pxp2.pcieg5.port0': {'speed': 'GEN1', 'width': 'x0', 'bifurcation': 'x8'},
        'pxp3.pcieg5.port0': {'speed': 'GEN1', 'width': 'x0', 'bifurcation': 'x8'},
        '1': {'pxp1.pcieg5.port0': {'speed': 'GEN4', 'width': 'x8', 'bifurcation': 'x8'},
        'pxp0.pcieg5.port2': {'speed': 'GEN1', 'width': 'x0'}}},
         'CXL': {'0': {'pxp1.pcieg5.port0': {'speed': 'GEN4', 'width': 'x8', 'bifurcation': 'x8'},
        'pxp2.pcieg5.port0': {'speed': 'GEN1', 'width': 'x0', 'bifurcation': 'x8'},
        'pxp3.pcieg5.port0': {'speed': 'GEN1', 'width': 'x0', 'bifurcation': 'x8'},
        '1': {'pxp1.pcieg5.port0': {'speed': 'GEN4', 'width': 'x8', 'bifurcation': 'x8'},
        'pxp0.pcieg5.port2': {'speed': 'GEN1', 'width': 'x0'}}}
        """
        pcie_ports = {}
        cxl_ports = {}
        inventory = {}
        pcie_dict = {}
        cxl_dict = {}
        socket = '0'

        pattern_pcie_dict = {
            ProductFamilies.SPR: r"pxp\d.(?:pcieg\d)?.\w+\s\(pcieg\d\)\s*is\sx{}\s*\(ilw=(?:x)?\d+\)\s\({}",
            ProductFamilies.GNR: r"pxp\d.\w+\d\s*is\sx{}\s*\(ilw=\d+\)\s\({}"
        }

        pattern_cxl_dict = {
            ProductFamilies.SPR: r"pxp\d.(?:pcieg\d)?.\w+\d\s\(CXL\)\s*is\sx{}\s*\(ilw=(?:x)?\d+\)\s\({}",
            # to be verified.
            ProductFamilies.GNR: r"place holder: x{}, {}"
        }

        pattern_port_dict = {
            ProductFamilies.SPR: r"pxp\d.(?:pcieg\d)?.\w+\d",
            ProductFamilies.GNR: r"pxp\d.\w+\d"
        }

        pattern_pcie = pattern_pcie_dict[platform]
        pattern_cxl = pattern_cxl_dict[platform]
        pattern_port = pattern_port_dict[platform]

        link_width = r"\d+"
        if positive_link_width_only:
            link_width = "[1-9]+"

        link_speed = r"GEN\d"
        pattern_pcie = pattern_pcie.format(link_width, link_speed)
        pattern_cxl = pattern_cxl.format(link_width, link_speed)

        bifurcated_dict = {}
        self._sdp_obj.start_log(self._sls_log, "w")
        self._pcie_obj.sls()
        self._sdp_obj.stop_log()
        with open(self._sls_log, "r") as log_file:
            pcie_sls_log = log_file.readlines()
            for line in pcie_sls_log:
                match_socket = re.findall(r"SOCKET(\d)", line)
                if len(match_socket) > 0:
                    pcie_ports[match_socket[0]] = {}
                    cxl_ports[match_socket[0]] = {}
                    socket = match_socket[0]
                    continue
                data = re.findall(r"PXP(\d)\sis\s(.*)", line)
                if len(data) > 0:
                    if data[0][1].count('x2') > 0:
                        bifurcated_dict["pxp{}".format(data[0][0])] = {"p0": data[0][1].split(' ')[0],
                                                                       "p1": data[0][1].split(' ')[1],
                                                                       "p2": data[0][1].split(' ')[2],
                                                                       "p3": data[0][1].split(' ')[3],
                                                                       "p4": data[0][1].split(' ')[4],
                                                                       "p5": data[0][1].split(' ')[5],
                                                                       "p6": data[0][1].split(' ')[6],
                                                                       "p7": data[0][1].split(' ')[7]}
                    else:
                        bifurcated_dict["pxp{}".format(data[0][0])] = {"p0": data[0][1].split(' ')[0],
                                                                       "p1": data[0][1].split(' ')[2],
                                                                       "p2": data[0][1].split(' ')[4],
                                                                       "p3": data[0][1].split(' ')[6],
                                                                       }

                match_pxp_pcie = re.findall(pattern_pcie, line)
                match_pxp_cxl = re.findall(pattern_cxl, line)

                if len(match_pxp_pcie) > 0:
                    match_pxp_port = re.findall(pattern_port, match_pxp_pcie[0])
                    if len(match_pxp_port) > 0:
                        speed_regex = "pxp.*\(ilw=(?:x)?\d+\)\s\((GEN\d)"
                        width_regex = "pxp\d.(?:pcieg\d)?.\w+\s\(pcieg\d\)\s*is\s(x\d+)\s*"
                        pcie_ports[socket][match_pxp_port[0]] = {
                            r"speed": re.findall(speed_regex, match_pxp_pcie[0])[0],
                            r"width": re.findall(width_regex, match_pxp_pcie[0])[0],
                            r"bifurcation": bifurcated_dict[match_pxp_port[0].split('.')[0]]["p{}".format(
                                match_pxp_port[0].split('.')[-1][-1])]
                        }
                if len(match_pxp_cxl) > 0:
                    speed_regex = "pxp.*\(ilw=(?:x)?\d+\)\s\((GEN\d)"
                    width_regex = "pxp\d.(?:pcieg\d)?.\w+\s\(CXL\)\s*is\s(x\d+)\s*"
                    match_cxl_port = re.findall(pattern_port, match_pxp_cxl[0])
                    if len(match_cxl_port) > 0:
                        self._sdp_obj.start_log(self._sls_log, "w")
                        try:
                            self._sdp_obj.halt()
                            cxl = silicon_reg_provider_obj.get_cxl_obj()
                            cxl.get_device_type(int(socket), match_cxl_port[0])
                            cxl.get_cxl_version(int(socket), match_cxl_port[0])
                        except Exception as ex:
                            content_exceptions.TestError(ex)
                        finally:
                            self._sdp_obj.go()
                            self._sdp_obj.stop_log()
                        with open(self._sls_log, "r") as fp:
                            var = fp.read()
                        cxl_ports[socket][match_cxl_port[0]] = {
                            r"speed": re.findall(speed_regex, line)[0],
                            r"width": re.findall(width_regex, line)[0],
                            r"cxl_type": re.findall(r"INFO: CXL.*(Type \d+)", var)[0],
                            r"cxl_version": re.findall(r"INFO: Device version.*(CXL \S+)", var)[0],
                            r"bit_rate": str(self._pcie_obj.getBitrate(int(socket), match_cxl_port[0]))
                        }

            inventory["PCIE"] = pcie_ports
            inventory["CXL"] = cxl_ports

            return inventory

    def get_pxp_inventory(self, link_width=None, link_speed=None,
                          positive_link_width_only=False, platform=ProductFamilies.SPR):
        """ Returns a dictionary with PCIE and CXL ports on each socket based on given filters

        :param link_width - link width filter
        :param link_speed - link speed filter
        :param positive_link_width_only: if True, further filter the result so that only devices with non-zero
                          linkwidth were returned.
        :param platform: specify the name of the platform.
        :return dict: dictionary of PCIE and CXL ports per socket

        Usage examples:

        get_pxp_inventory()
        get_pxp_inventory()[IOProtocol.CXL]
        get_pxp_inventory(link_width=PCIeLinkWidth.x16)
        get_pxp_inventory(link_width=PCIeLinkWidth.x16, link_speed=PCIeLinkSpeed.GEN5)
        get_pxp_inventory(link_speed=PCIeLinkSpeed.GEN5)[Protocol.CXL]["SOCKET1"])
        get_pxp_inventory(link_width=PCIeLinkWidth.x8, link_speed=PCIeLinkSpeed.GEN4)[IOProtocol.PCIE])
        """

        pcie_ports = {}
        cxl_ports = {}
        inventory = {}
        socket = 0

        pattern_pcie_dict = {
            ProductFamilies.SPR: r"pxp\d.(?:pcieg\d)?.\w+\s\(pcieg\d\)\s*is\sx{}\s*\(ilw=(?:x)?\d+\)\s\({}",
            ProductFamilies.GNR: r"pxp\d.\w+\d\s*is\sx{}\s*\(ilw=\d+\)\s\({}"
        }

        pattern_cxl_dict = {
            ProductFamilies.SPR: r"pxp\d.(?:pcieg\d)?.\w+\d\s\(CXL\)\s*is\sx{}\s*\(ilw=(?:x)?\d+\)\s\({}",
            # to be verified.
            ProductFamilies.GNR: r"place holder: x{}, {}"
        }

        pattern_port_dict = {
            ProductFamilies.SPR: r"pxp\d.(?:pcieg\d)?.\w+\d",
            ProductFamilies.GNR: r"pxp\d.\w+\d"
        }

        pattern_pcie = pattern_pcie_dict[platform]
        pattern_cxl = pattern_cxl_dict[platform]
        pattern_port = pattern_port_dict[platform]
        if link_width is None:
            link_width = "\d+"
            if positive_link_width_only:
                link_width = "[1-9]+"
        if link_speed is None:
            link_speed = "GEN\d"
        pattern_pcie = pattern_pcie.format(link_width, link_speed)
        pattern_cxl = pattern_cxl.format(link_width, link_speed)

        self._sdp_obj.start_log(self._sls_log, "w")
        self._pcie_obj.sls()
        self._sdp_obj.stop_log()
        with open(self._sls_log, "r") as log_file:
            pcie_sls_log = log_file.readlines()
            for line in pcie_sls_log:
                match_socket = re.findall(r"SOCKET(\d)", line)
                if len(match_socket) > 0:
                    pcie_ports[match_socket[0]] = ""
                    cxl_ports[match_socket[0]] = ""
                    socket = match_socket[0]
                    continue
                match_pxp_pcie = re.findall(pattern_pcie, line)
                match_pxp_cxl = re.findall(pattern_cxl, line)
                if len(match_pxp_pcie) > 0:
                    match_pxp_port = re.findall(pattern_port, match_pxp_pcie[0])
                    if len(match_pxp_port) > 0:
                        pcie_ports[socket] = pcie_ports[socket] + "+" + "".join(match_pxp_port[0])
                if len(match_pxp_cxl) > 0:
                    match_cxl_port = re.findall(pattern_port, match_pxp_cxl[0])
                    if len(match_cxl_port) > 0:
                        cxl_ports[socket] = cxl_ports[socket] + "+" + "".join(match_cxl_port[0])

                # inventory dicts cleanup
            for (socket, _), (socket, _) in zip(pcie_ports.items(), cxl_ports.items()):
                pcie_ports[socket] = pcie_ports[socket][1:].split("+")
                cxl_ports[socket] = cxl_ports[socket][1:].split("+")

            inventory["PCIE"] = pcie_ports
            inventory["CXL"] = cxl_ports

            return inventory

    def get_populated_ports_dict(self, linkspeed=None):
        """
        Returns socket value for pxp port dict

        :param linkspeed: PCIeLinkSpeed value
        :return dict
        """
        socket_pxp_ports = {}
        for protocol, sockets in self.get_pxp_inventory(positive_link_width_only=True, link_speed=linkspeed).items():
            for socket, ports in sockets.items():
                if ports != ['']:
                    socket_pxp_ports[socket] = ports
        return socket_pxp_ports

    def get_socket_for_pxp_port_dict(self, pxp_port_dict):
        """
        Returns socket value for pxp port dict

        :param pxp_port_dict: socket:pxp port dict
        :return str
        """
        for socket, pxp_port_list in pxp_port_dict.items():
            for _ in pxp_port_list:
                return socket

    def get_pxp_ports_first_populated_socket(self, link_speed=PCIeLinkSpeed.GEN5, ioprotocol=IOProtocol.PCIE):
        """ Scans the pxp inventory for first populated socket with pxp ports and returns a dict with pxp ports for
        that socket

        :param link_speed: PCIeLinkSpeed enum value
        :param ioprotocol: IOProtocol enum value
        :return dict
        """

        socket_pxp_ports = {}
        pcie = self.get_pxp_inventory(link_speed=link_speed)[ioprotocol]
        for detected_socket in pcie.keys():
            if pcie[detected_socket] != ['']:
                socket_pxp_ports[detected_socket] = pcie[detected_socket]
        return socket_pxp_ports


class PcieCommon(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the Pcie Test Cases
    """

    SLOT_C = "slot_c"
    SLEEP_FOR_ONE_MINUTE_IN_SEC = 60
    RESTART = "./restart.sh"
    REBOOT_CMD = {"ac_cycle": "init 0", "warm_reboot": "init 6"}
    HALT_CYCLE_DIR = "/root/Desktop"
    HALT_CMD = "haltcycle"
    CAT_COMMAND = "cat {}"
    PCIERRPOLL_CMD = "./PCIERRpoll -all"
    PCIERRPOLL_STR = "PCIERRpoll"
    ILVSS_STR = "ilvss"
    PCIE_ERR_POLL_SUCCESS_STR = "No errors found in selected PCIe devices"
    DRIVERS_LIST = ["mlx5_ib", "mlx5_core", "i40iw", "i40e"]
    REGEX_FOR_SLOT_E_BY_FOUR_BIFURCATION = [r"PXP1\sis\sx4\s\S+\sx4\s\S+\sx4\s\S+\sx4",
                                            r"PXP3\sis\sx4\s\S+\sx4\s\S+\sx4\s\S+\sx4"]
    LINUX_CYCLING_ERROR_TYPE_LIST = ["MemErrorCount", "LinkErrorCount", "ProcErrorCount"]
    WIN_CYCLING_ERROR_TYPE_LIST = ["MemoryErrorCount", "LinkErrorCount", "ProcessorErrorCount"]
    CYCLING_APP_NAME = {OperatingSystems.LINUX: "cycle", OperatingSystems.WINDOWS: "CycleService"}
    CYCLING_PROCEESS_COMMAND = {OperatingSystems.LINUX: "cycle.sh", OperatingSystems.WINDOWS: "CycleService"}
    PCIE_SLS_OUTPUT_LOG = "pcie_sls_output.log"
    REG_PROVIDER_CSCRIPTS = "CscriptsSiliconRegProvider"
    REG_PROVIDER_PYTHONSV = "PythonsvSiliconRegProvider"
    SEC_BUS_PATH = {
        ProductFamilies.SPR: "uncore.pi5.{}.cfg.secbus",
        ProductFamilies.EMR: "uncore.pi5.{}.cfg.secbus",
        ProductFamilies.GNR: "io{}.uncore.pi5.{}.cfg.secbus"
    }

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file_path=None):
        """
        Create an instance of PcieCommon

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        if bios_config_file_path:
            if "/" not in bios_config_file_path:
                bios_config_file_path = os.path.join(os.path.dirname(os.path.abspath(
                    __file__)), bios_config_file_path)
        super(PcieCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path)
        self._args = arguments
        self._cfg = cfg_opts
        self._product_family = self._common_content_lib.get_platform_family()
        self._pcie_provider = PcieProvider.factory(test_log, self.os, cfg_opts, "os", uefi_obj=None)
        self._pcie_util_obj = PcieCommonUtil(self._log, self.os, self._common_content_configuration,
                                             self._pcie_provider,cfg_opts)
        self._storage_provider = StorageProvider.factory(test_log, self.os, cfg_opts, "os")
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._cycling_time_in_sec = self._common_content_configuration.get_pcie_cycling_time_to_execute()
        self._no_of_cycle_for_devcon_utility_test = self._common_content_configuration.\
            get_number_of_cycle_to_execute_devcon_utility_test()
        self._ltssm_debug_tool_provider = self._common_content_configuration.get_ltssm_debug_tool_provider()
        self._pcie_ltssm_provider = PcieLtssmToolProvider.factory(log=test_log, cfg_opts=cfg_opts,
                                                                  os_obj=self.os, pcie_provider_obj=self._pcie_provider,
                                                                  silicon_reg_ltssm_provider=self._ltssm_debug_tool_provider)

        self._stres_provider_obj = StressAppTestProvider.factory(self._log,cfg_opts,self.os)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.sdp_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp_obj = ProviderFactory.create(self.sdp_cfg, self._log)
        self._utils = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os,
                               cfg_opts)
        self.PCIE_SLOT_MAPPING_WITH_BUS = SlotMappingUtils.get_slot_bus_mappping_dict()
        self.reg_provider_obj = ProviderFactory.create(self.sil_cfg, self._log)
        self.reg_provider_class = type(self.reg_provider_obj).__name__
        if self.reg_provider_class == self.REG_PROVIDER_CSCRIPTS:
            # get_pcie_obj() not present in commlib\utils\utils.py for gnr cscripts.
            if self.reg_provider_obj.silicon_cpu_family == ProductFamilies.GNR:
                from platforms.GNR.gnrpciedefs import gnrpciedefs
                self.pcie_obj = gnrpciedefs()
            else:
                self.pcie_obj = self.reg_provider_obj.get_cscripts_utils().get_pcie_obj()
        elif self.reg_provider_class == self.REG_PROVIDER_PYTHONSV:
            self.pcie_obj = self.reg_provider_obj.get_ltssm_object()
        else:
            raise RuntimeError("reg provider can only be cscripts or pythonsv!")
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self.pxp_inventory = PxpInventory(self.sdp_obj, self.pcie_obj, self.get_sls_log_path())

    def ltssm_prepare(self):
        """
        This method is to disable the driver(Exception Cases).

        :return None
        """

        if self.os.os_type == OperatingSystems.LINUX:
            for each_driver in self.DRIVERS_LIST:
                self.os.execute("modprobe -r {}".format(each_driver), self._command_timeout)
        if self.os.os_type == OperatingSystems.WINDOWS:
            if self._common_content_configuration.disable_pcie_cards():
                deviceid_list = self._common_content_configuration.get_pcie_cards_to_be_diabled()
                for each_device_id in deviceid_list:
                    self._pcie_ltssm_provider._pcie_provider_obj.disable_kernel_driver(each_device_id)

    def execute_the_cycling_tool(self, arguments=None, directory_path=None, boot_type=None):
        """
        This Method is to execute the reboot cycling tool.

        :param boot_type
        :param arguments
        :param directory_path
        """
        try:
            if self.os.os_type == OperatingSystems.LINUX:
                args = ""
                for key, value in arguments.items():
                    args = args + '"%s"="%s" ' % (key, value)
                args = args.strip()
                self._log.debug(args)
                try:
                    self._install_collateral.install_python_package('pexpect')
                except:
                    self._log.error("pexpect package did not install....So trying without proxy now...")
                    self.os.execute("pip install pexpect", self._command_timeout)
                finally:
                    try:
                        cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd="pip freeze | grep pexpect",
                                                                              cmd_str="checking pexpect package on SUT",
                                                                              execute_timeout=self._command_timeout)
                        self._log.info("pexpect package on SUT: {}".format(cmd_output))
                    except:
                        raise content_exceptions.TestFail("Please install pexpect package on SUT Manually")

                cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd="python3 {} {}".format(
                    LinuxCyclingToolConstant.CYCLING_SCRIPTS_FILE_NAME, args), cmd_str="script",
                    execute_timeout=self._command_timeout, cmd_path=directory_path)
                self._log.debug("script Execution Output: {}".format(cmd_output))
                self._install_collateral.screen_package_installation()
                self.os.execute_async(self.REBOOT_CMD[boot_type])
                time.sleep(self.SLEEP_FOR_ONE_MINUTE_IN_SEC)
                if boot_type == "ac_cycle":
                    self.perform_cold_reboot_cycle()
                elif boot_type == "warm_reboot":
                    self.perform_warm_reboot_cycle()
                else:
                    raise content_exceptions.TestFail("Test Case not implemented for : {}".format(boot_type))
            else:
                self.execute_the_cycling_tool_win(arguments=arguments, directory_path=directory_path, boot_type=
                boot_type)

        except Exception as ex:
            raise content_exceptions.TestFail("Failed to execute the Cycling tool: {}".format(ex))

        finally:
            #  Applying AC cycle to bring SUT UP to stop cycling tool after Testing.
            #  If SUT did not come to OS trying 2 more time.
            for each_time in range(0, 3):
                try:
                    self._log.info("Apply AC cycle Attempt: #{}".format(each_time+1))
                    self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
                    self._common_content_lib.wait_for_os(self.reboot_timeout)
                    break
                except:
                    self._log.error("SUT did not booted to OS in Attempt: #{}".format(each_time+1))
                    continue
            if self.os.os_type == OperatingSystems.WINDOWS:
                self._common_content_lib.execute_sut_cmd(sut_cmd=WindowsMemrwToolConstant.TERMINATE_CYCLING_APP,
                                                         cmd_str="disable the cycling App", execute_timeout=
                                                         self._command_timeout, cmd_path=
                                                         self._common_content_lib.C_DRIVE_PATH)
            elif self.os.os_type == OperatingSystems.LINUX:
                self._common_content_lib.execute_sut_cmd(sut_cmd=self.HALT_CMD, cmd_str="Halt Cycling",
                                                         execute_timeout=self._command_timeout,
                                                         cmd_path=self.HALT_CYCLE_DIR)

            self._stres_provider_obj.kill_stress_tool(stress_tool_name=self.CYCLING_APP_NAME[self.os.os_type],
                                                      stress_test_command=self.CYCLING_PROCEESS_COMMAND[
                                                          self.os.os_type])

    def execute_the_cycling_tool_win(self, arguments=None, directory_path=None, boot_type=None):
        """
        This method is to execute the cycling tool in Windows.

        :param arguments
        :param directory_path
        :param boot_type
        """
        try:
            args = ""
            for key, value in arguments.items():
                args = args + '"%s"="%s" ' % (key, value)
            args = args.strip()
            self._log.debug(args)
            self._install_collateral.install_pip_package('pbr')
            self._install_collateral.install_pip_package('wexpect')
            sut_cmd = "python {} {}".format(
                         WindowsMemrwToolConstant.CYCLING_SCRIPT_FILE_NAME, args)
            stress_thread = threading.Thread(target=self._execute_cycle_tool,
                                             args=(sut_cmd, directory_path,))
            # Thread has been started
            stress_thread.start()
            time.sleep(self.SLEEP_FOR_ONE_MINUTE_IN_SEC)
            if self._stres_provider_obj.check_app_running(app_name=WindowsMemrwToolConstant.CYCLING_HOST_FOLDER_NAME):
                raise content_exceptions.TestFail("Failed to run Cycling tool")
            self._log.debug("Cycling Tool executed and now test started...")

            if boot_type == "ac_cycle":
                total_number_of_count = self.perform_cold_reboot_cycle()
                self._log.info("Total Number of Successfully Cold Reboot: #{} completed".format(total_number_of_count))
            elif boot_type == "warm_reboot":
                total_number_of_count = self.perform_warm_reboot_cycle()
                self._log.info("Total number of Successfully Warm Reboot: #{} completed".format(total_number_of_count))
            else:
                raise content_exceptions.TestFail("Test is not implemented for boot type: {}".format(boot_type))
        except Exception as ex:
            raise content_exceptions.TestFail("Exception Occurred during Cycling: {}".format(ex))

    def perform_cold_reboot_cycle(self):
        """
        This method is to do cold reboot.

        :return count
        """
        start_time = time.time()
        count = 0
        while time.time() - start_time <= self._cycling_time_in_sec:

            if not self.os.is_alive():
                count = count + 1
                self._log.info("SUT is not Alive... Performing AC Cycle on SUT")
                time.sleep(self.SLEEP_FOR_ONE_MINUTE_IN_SEC)
                self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
                self._common_content_lib.wait_for_os(self.reboot_timeout)
                self._log.info("Cold Reboot cycle  # {} completed and SUT booted to OS Successfully".format(count))

            time.sleep(self.SLEEP_FOR_ONE_MINUTE_IN_SEC * 3)
            self._log.info("Cycling Test is in progress....")
        return count

    def perform_warm_reboot_cycle(self):
        """
        This method is to warm reboot cycle.

        :return: count
        """
        start_time = time.time()
        count = 0
        while time.time() - start_time <= self._cycling_time_in_sec:

            if not self.os.is_alive():
                count = count + 1
                self._log.info("SUT is not Alive... Waiting for SUT to Alive")
                self._common_content_lib.wait_for_os(self.reboot_timeout)
                self._log.info("Warm Reboot cycle  # {} completed and SUT booted to OS Successfully".format(count))

            time.sleep(self.SLEEP_FOR_ONE_MINUTE_IN_SEC)
            self._log.info("Cycling Test is in progress....")
        return count

    def verify_cycling_log(self):
        """
        This method is to verify the cycling log.

        :return True
        :raise content_exception
        """
        if self.os.os_type == OperatingSystems.LINUX:
            for each_type in self.LINUX_CYCLING_ERROR_TYPE_LIST:
                error_count = self._common_content_lib.execute_sut_cmd(sut_cmd=self.CAT_COMMAND.format(
                    each_type), cmd_str=each_type, execute_timeout=self._command_timeout,
                    cmd_path=LinuxCyclingToolConstant.LOG_DIR)
                if int(error_count.strip('')):
                    raise content_exceptions.TestFail("Error type: '{}' was Captured with count value: '{}'".format(
                        each_type, error_count))
                self._log.info("Error type: {} has no error in Log: {}".format(each_type, error_count))
            self._log.info("No Error is Captured as Expected")

        elif self.os.os_type == OperatingSystems.WINDOWS:
            for each_type in self.WIN_CYCLING_ERROR_TYPE_LIST:
                error_count_string = self._common_content_lib.execute_sut_cmd(sut_cmd="powershell get-content {}".format(
                    each_type), cmd_str=each_type, execute_timeout=self._command_timeout,
                    cmd_path=WindowsMemrwToolConstant.CYCLING_LOG_DIR)

                clean = re.compile('<.*?>')
                error_count_number = re.sub(clean, '', error_count_string)
                if int(error_count_number.strip('\n')) != 0:
                    raise content_exceptions.TestFail("Error type: '{}' was Captured with count value: '{}'".format(
                        each_type, error_count_number))
                self._log.info("Error Type: {} has no error in Log: {}".format(each_type, error_count_number))
            self._log.info("No Error is Captured as Expected")

    def _execute_cycle_tool(self, cmd, cmd_dir):
        """
        Function to execute cycle tool application.

        :param cmd: command to run cycle tool
        :param cmd_dir: path of the executor.
        """
        self._log.info("Executing the cycle tool...")

        self._log.debug("cycle tool command line is '{}'".format(cmd))
        self._log.debug("cycle tool is running from directory '{}'".format(cmd_dir))

        stress_execute_res = self.os.execute(cmd, self._command_timeout*70, cmd_dir)

        if stress_execute_res.cmd_failed():
            self._log.info("Cycle tool thread has been stopped")

    def verify_required_slot_pcie_device_linux(self, cscripts_obj, pcie_slot_device_list=None, generation=5,
                                               lnk_cap_width_speed=False, lnk_stat_width_speed=False,
                                               bifurcation=False):
        """
        This method is to verify the PCIe device and its link speed and width.

        :param cscripts_obj
        :param pcie_slot_device_list
        :param generation
        :param lnk_cap_width_speed
        :param lnk_stat_width_speed
        :param bifurcation
        :raise content_exception
        """
        device_info_list = []
        self._log.info("PCIe Device details from Config: {}".format(pcie_slot_device_list))
        for each_slot in pcie_slot_device_list:
            slot_name = each_slot[PcieSlotAttribute.SLOT_NAME]
            self._log.info("PCIe Slot Name: {}".format(slot_name))
            if slot_name == self.SLOT_C:
                try:
                    bus_output = "0x" + each_slot['bus']
                except:
                    raise content_exceptions.TestFail("Please Add bus tag for slot_c")
            else:
                csp_path_attribute = PcieSlotAttribute.PCIE_SLOT_CSP_PATH
                socket_attribute = PcieSlotAttribute.PCIE_SLOT_SOCKET
                if self._product_family in [ProductFamilies.EMR, ProductFamilies.SPR]:
                    csp_path = self.PCIE_SLOT_MAPPING_WITH_BUS[slot_name][csp_path_attribute][self._product_family].format(
                        generation)
                elif self._product_family in [ProductFamilies.GNR]:
                    csp_path = self.PCIE_SLOT_MAPPING_WITH_BUS[slot_name][csp_path_attribute][self._product_family]
                else:
                    raise content_exceptions.TestFail("Not Implemented for product family- {}".format(
                        self._product_family))
                self._log.debug("csp register to get bus info is: {}".format(csp_path))
                socket = self.PCIE_SLOT_MAPPING_WITH_BUS[slot_name][socket_attribute][self._product_family]
                self._log.info("Socket for PCIe Slot: {} is {}".format(slot_name, socket))
                bus_output = cscripts_obj.get_by_path(cscripts_obj.SOCKET, csp_path, socket)
                if not bus_output:
                    raise content_exceptions.TestFail("PCIe device bus is not captured with cscripts for slot:"
                                                      " {}".format(slot_name))
            self._log.debug("Slot Name: {} is mapped to bus: {}".format(slot_name, bus_output))
            bus_output = str(bus_output)[2:]  # Converting Register byte into string. Here, bus value in hexa required.

            pcie_device_info_dict = self._pcie_provider.get_device_details_with_bus(bus_output)
            if not pcie_device_info_dict:
                raise content_exceptions.TestFail("Pcie Device for Slot: {} with bus: {} was not visible in OS "
                                                  "".format(slot_name, bus_output))
            device_info_list.append(pcie_device_info_dict)
            for key, value in pcie_device_info_dict.items():
                if lnk_cap_width_speed:
                    if not bifurcation:
                        width = self._pcie_provider.get_link_cap_width_by_bdf(bdf=key)
                        if not each_slot[PcieSlotAttribute.PCIE_DEVICE_WIDTH] in width:
                            raise content_exceptions.TestFail("Link Status width for slot: {} is capture unexpected:" \
                                                              " {}. Expected Width is: {}".format(
                                slot_name, width, each_slot[PcieSlotAttribute.PCIE_DEVICE_WIDTH]
                            ))
                        self._log.debug("PCIe Link Cap Width for Slot: {} found as Expected: {}".format(
                                slot_name, width))
                    speed = self._pcie_provider.get_link_cap_speed_by_bdf(bdf=key)

                    expected_speed = each_slot[PcieSlotAttribute.PCIE_DEVICE_SPEED_IN_GT_SEC]
                    if expected_speed not in speed:
                        raise content_exceptions.TestFail("Link Speed for Slot: {} was captured unexpected: {}."
                                                          "Expected Speed is : {}".format(slot_name, speed,
                                                                                          expected_speed))
                    self._log.debug("Link Cap Speed for Slot Name: {} found as expected: {}".format(slot_name,
                                                                                                        expected_speed))

                elif lnk_stat_width_speed:
                    width = self._pcie_provider.get_link_status_width_by_bdf(bdf=key)
                    if not each_slot[PcieSlotAttribute.PCIE_DEVICE_WIDTH] in width:
                        raise content_exceptions.TestFail("Link Status width for slot: {} is capture unexpected:" \
                                                          " {}. Expected Width is: {}".format(
                            slot_name, width, each_slot[PcieSlotAttribute.PCIE_DEVICE_WIDTH]
                        ))
                    self._log.debug("PCIe Width for Slot: {} found as Expected: {}".format(
                        slot_name, width))

                    speed = self._pcie_provider.get_link_status_speed_by_bdf(bdf=key)
                    expected_speed = each_slot[PcieSlotAttribute.PCIE_DEVICE_SPEED_IN_GT_SEC]
                    if expected_speed not in speed:
                        raise content_exceptions.TestFail("Link Speed for Slot: {} was captured unexpected: {}."
                                                          "Expected Speed is : {}".format(slot_name, speed,
                                                                                          expected_speed))

                    self._log.info("Negotiated Speed for Slot Name: {} found as expected and matched {} from "
                                   "config : {}".format(slot_name, speed, expected_speed))
                    break
        return device_info_list

    def verify_required_slot_pcie_device(self, cscripts_obj, pcie_slot_device_list=None, generation=5,
                                         lnk_cap_width_speed=False, lnk_stat_width_speed=False, bifurcation=False):
        """
        This method is to verify the PCIe device, Link Speed and Link Width for Windows.

        :param cscripts_obj
        :param pcie_slot_device_list
        :param generation
        :param lnk_cap_width_speed
        :param lnk_stat_width_speed
        :param bifurcation
        :return list_of_pcie_info_dict
        :raise content_exception
        """
        list_of_pcie_info_dict = []
        if self.os.os_type == OperatingSystems.LINUX:
            list_of_pcie_info_dict = self.verify_required_slot_pcie_device_linux(
                cscripts_obj=cscripts_obj, pcie_slot_device_list=pcie_slot_device_list, generation=generation,
                lnk_cap_width_speed=lnk_cap_width_speed, lnk_stat_width_speed=lnk_stat_width_speed,
                bifurcation=bifurcation
            )
        elif self.os.os_type == OperatingSystems.WINDOWS:
            list_of_pcie_info_dict = self.verify_required_slot_pcie_device_win(
                cscripts_obj=cscripts_obj, pcie_slot_device_list=pcie_slot_device_list, generation=generation,
                lnk_cap_width_speed=lnk_cap_width_speed, lnk_stat_width_speed=lnk_stat_width_speed,
                bifurcation=bifurcation)
        else:
            raise content_exceptions.TestFail("Still Not Implemented for OS type: {}".format(self.os.os_type))
        return list_of_pcie_info_dict

    def verify_required_slot_pcie_device_win(self, cscripts_obj, pcie_slot_device_list=None, generation=5,
                                             lnk_cap_width_speed=False, lnk_stat_width_speed=False,
                                             bifurcation=None):
        """
        This method is to verify the PCIe device, Link Speed and Link Width for Windows.

        :param cscripts_obj
        :param pcie_slot_device_list
        :param generation
        :param lnk_cap_width_speed
        :param lnk_stat_width_speed
        :param bifurcation
        :raise content_exception
        """
        device_info_list = []
        self._log.info("PCIe Device details from Config: {}".format(pcie_slot_device_list))
        for each_slot in pcie_slot_device_list:
            slot_name = each_slot[PcieSlotAttribute.SLOT_NAME]
            self._log.info("PCIe Slot Name: {}".format(slot_name))
            if slot_name == self.SLOT_C:
                try:
                    bus_output = each_slot['bus']
                except:
                    raise content_exceptions.TestFail("Please Add bus tag for slot_c")
            else:
                csp_path_attribute = PcieSlotAttribute.PCIE_SLOT_CSP_PATH
                socket_attribute = PcieSlotAttribute.PCIE_SLOT_SOCKET
                if self._product_family in [ProductFamilies.SPR, ProductFamilies.EMR]:
                    csp_path = self.PCIE_SLOT_MAPPING_WITH_BUS[slot_name][csp_path_attribute][self._product_family].format(
                        generation)
                elif self._product_family in [ProductFamilies.GNR]:
                    csp_path = self.PCIE_SLOT_MAPPING_WITH_BUS[slot_name][csp_path_attribute][self._product_family]
                else:
                    raise content_exceptions.TestFail("Not implemented for product families- {}".format(
                        self._product_family))
                self._log.debug("csp register to get bus info is: {}".format(csp_path))

                socket = self.PCIE_SLOT_MAPPING_WITH_BUS[slot_name][socket_attribute][self._product_family]
                self._log.info("Socket for PCIe Slot: {} is {}".format(slot_name, socket))
                bus_output = cscripts_obj.get_by_path(cscripts_obj.SOCKET, csp_path, socket)
                if not bus_output:
                    raise content_exceptions.TestFail("PCIe device bus is not captured with cscripts for slot:"
                                                      " {}".format(slot_name))
            self._log.debug("Slot Name: {} is mapped to bus: {}".format(slot_name, bus_output))
            pcie_device_info_dict = self._pcie_provider.get_device_details_with_bus(str(int(bus_output)))
            if not pcie_device_info_dict:
                raise content_exceptions.TestFail("Pcie Device for Slot: {} with bus: {} was not visible in OS "
                                                  "".format(slot_name, bus_output))
            device_info_list.append(pcie_device_info_dict)
            for key, value in pcie_device_info_dict.items():
                if bifurcation:
                    # Bifurcation slot speed is not reflecting in memrw tool output.Verifying Speed and Width from csp
                    pcie = cscripts_obj.get_cscripts_utils().get_pcie_obj()
                    port_mapped = self.PCIE_SLOT_MAPPING_WITH_BUS[
                        self._product_family][slot_name][PcieSlotAttribute.PORT_MAPPED_WITH_GEN.format(generation)]
                    negotiated_width = pcie.get_negotiated_link_width(socket=socket, portstr=port_mapped)
                    link_speed = 2 ** pcie.get_current_link_speed(socket=socket, portstr=port_mapped)
                    if each_slot[PcieSlotAttribute.PCIE_DEVICE_WIDTH] not in str(negotiated_width):
                        raise content_exceptions.TestFail("Width for slot: {} is captured unexpected: {}"
                                                          "Expected Width is: {}".format(slot_name,
                                                                                         negotiated_width,
                                                                                         each_slot[PcieSlotAttribute.PCIE_DEVICE_WIDTH]))
                    self._log.info("Link width for slot: {} is captured as expected: {}".format(slot_name,
                                                                                                negotiated_width))
                    if each_slot[PcieSlotAttribute.PCIE_DEVICE_SPEED_IN_GT_SEC] not in str(link_speed):
                        raise content_exceptions.TestFail("Link Speed for slot: {} is captured unexpected: {}"
                                                          "Expected speed is: {}".format(slot_name,
                                                                                         link_speed,
                                                                                         each_slot[PcieSlotAttribute.PCIE_DEVICE_SPEED_IN_GT_SEC]))
                    self._log.info("Link Speed for slot: {} is captured as Expected: {}".format(slot_name,
                                                                                                link_speed))

                else:
                    if lnk_cap_width_speed:
                        if not each_slot[PcieSlotAttribute.PCIE_DEVICE_WIDTH] in value[PcieAttribute.LINKCAP_WIDTH]:
                            raise content_exceptions.TestFail("Link Cap Width for slot: {} is captured unexpected: {} "
                                                              "Expected Width is: {}".format(
                                slot_name, value[PcieAttribute.LINKCAP_WIDTH], each_slot[
                                    PcieSlotAttribute.PCIE_DEVICE_WIDTH]))
                        self._log.debug("Link Cap Width for slot: {} found as Expected: {}".format(
                            slot_name, value[PcieAttribute.LINKCAP_WIDTH]))
                        if not each_slot[PcieSlotAttribute.PCIE_DEVICE_SPEED_IN_GT_SEC] in \
                            value[PcieAttribute.LINKCAP_SPEED]:
                            raise content_exceptions.TestFail("Link Cap Speed for slot: {} is captured unexpected: {}"
                                                              ". Expected Speed is: {}".format(
                                slot_name, value[PcieAttribute.LINKCAP_SPEED], each_slot[
                                    PcieSlotAttribute.PCIE_DEVICE_SPEED_IN_GT_SEC]))
                        self._log.debug("Link Cap Speed for slot: {} is captured as Expected: {}".format(
                            slot_name, value[PcieAttribute.LINKCAP_SPEED]))

                    if lnk_stat_width_speed:
                        if not each_slot[PcieSlotAttribute.PCIE_DEVICE_WIDTH] in value[PcieAttribute.LINKSTATUS_WIDTH]:
                            raise content_exceptions.TestFail("Link Status width for slot: {} is capture unexpected:" \
                                                              " {}. Expected Width is: {}".format(
                                slot_name, value[PcieAttribute.LINKSTATUS_WIDTH],
                                each_slot[PcieSlotAttribute.PCIE_DEVICE_WIDTH]
                            ))
                        self._log.debug("PCIe Width for Slot: {} found as Expected: {}".format(
                            slot_name, value[PcieAttribute.LINKSTATUS_WIDTH]))

                        speed = value[PcieAttribute.LINKCAP_SPEED].replace('.0', '')
                        expected_speed = each_slot[PcieSlotAttribute.PCIE_DEVICE_SPEED_IN_GT_SEC]
                        if expected_speed not in speed:
                            raise content_exceptions.TestFail("Link Speed for Slot: {} was captured unexpected: {}."
                                                              "Expected Speed is : {}".format(slot_name, speed,
                                                                                              expected_speed))
                        self._log.debug("Negotiated Speed for Slot Name: {} found as expected: {}".format(slot_name,
                                                                                                          expected_speed))

        return device_info_list

    def verify_bifurcation_status_in_sls(self, csp, sdp):
        """
        This method is to verify the bifurcation in sls output.

        :param csp
        :param sdp
        """
        sdp.start_log(self.PCIE_SLS_OUTPUT_LOG, "w")
        self.pcie_obj.sls()
        sdp.stop_log()
        with open(self.PCIE_SLS_OUTPUT_LOG, "r") as log_file:
            pcie_sls_log = log_file.read()
            self._log.info(pcie_sls_log)
        bifurcation_status = self._common_content_lib.extract_regex_matches_from_file(
            pcie_sls_log, self.REGEX_FOR_SLOT_E_BY_FOUR_BIFURCATION)
        if not bifurcation_status:
            raise content_exceptions.TestFail("Bifurcation is not set for Slot E")
        self._log.info("Bifurcation reflected as Expected in pcie.sls command")

    def perform_pcie_cyling(self, reboot_type):
        """
        This method is to perform Cycling test for PCIe.

        :param reboot_type
        """
        from src.hsio.cxl.cxl_common import CxlCommon
        cxl_common_obj = CxlCommon(self._log, self._args, self._cfg)
        cxl_common_obj.initialize_os_cyling_script()
        self.verify_io_speed_and_width_bw_sls_and_os(protocol="PCIE")
        time_out_in_sec = self._common_content_configuration.get_pcie_cycling_time_to_execute()
        count = 0
        start_time = time.time()
        while time.time() - start_time <= time_out_in_sec:
            self._common_content_lib.execute_sut_cmd("./pci_check_cycle.sh", "health check", self._command_timeout,
                                                     "/root")
            if reboot_type == "warm_reboot":
                self._common_content_lib.perform_os_reboot(self.reboot_timeout)
            else:
                self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
            self._common_content_lib.wait_for_os(reboot_timeout=self.reboot_timeout)
            time.sleep(self.WAIT_TIME)
            self._log.info("Cycle Number-{} got completed Successfully".format(count))
            count += 1

        self.verify_io_speed_and_width_bw_sls_and_os(protocol="PCIE")
        cxl_common_obj.check_cap_err_cnt()
        return

    def verify_io_speed_and_width_bw_sls_and_os(self, protocol):
        """
        This method is to verify (PCIE or CXL) speed and width between SLS and OS.

        :param protocol
        """
        slot_dict = self.pxp_inventory.get_slot_inventory(platform=self._common_content_lib.get_platform_family(),
                                                          silicon_reg_provider_obj=self.reg_provider_obj,
                                                          positive_link_width_only=True)[protocol]
        self._log.info("PCIe dict info from SLS- {}".format(slot_dict))
        ret_val = False
        for each_socket, each_socket_dict in slot_dict.items():
            for each_port, each_port_dict in each_socket_dict.items():
                ret_val = True
                bus = self.get_pxp_secbus(pxp_port=each_port, socket=int(each_socket))
                self._log.info("Bus number for socket- {} and port- {} is- {}".format(each_socket, each_port, bus))
                os_width = self._pcie_provider.get_link_status_width_by_bdf(str(bus)[2:] + ":00.0")
                self._log.info("Width for socket- {} and port- {} in OS is- {}".format(each_socket, each_port,
                                                                                       os_width))
                if os_width != each_port_dict['width']:
                    self._log.info("Expected width for Socket- {} and Port- {} is- {}".format(each_socket, each_port,
                                                                                              each_port_dict['width']))
                    raise content_exceptions.TestFail("Unexpected Width-{} was found for Socket- {} and Port- {}"
                                                      "".format(os_width, each_socket, each_port))
                os_speed = self._pcie_provider.get_link_status_speed_by_bdf(str(bus)[2:] + ":00.0")
                self._log.info("Speed for socket- {} and port- {} in OS is- {}".format(each_socket, each_port,
                                                                                       os_speed))
                if PxpInventory.PCIeLinkSpeed.MAPPING[each_port_dict['speed']] not in os_speed:
                    self._log.info("Expected Speed for Socket- {} and Port- {} is- {}".format(each_socket, each_port,
                                                                                              each_port_dict['speed']))
                    raise content_exceptions.TestFail("Unexpected Speed-{} was found for Socket- {} and Port- {}"
                                                      "".format(os_speed, each_socket, each_port))

        if not ret_val:
            raise content_exceptions.TestFail("No ({}) Card is Populated on SUT".format(protocol))

        return True

    def get_bus_id_for_slot(self, csp=None, slot_name=None, gen=5, check_bus_flag=True):
        """
        This method is to get the bus id for slot.

        :param slot_name - name of the slot for which bus is required.
        :param csp - cscripts obj.
        :param gen - Controller generation
        :param check_bus_flag - flag to raise if bus is not visible.
        :return bus id
        """
        self._log.info("Getting the BUS ID for slot.")
        if slot_name == PcieSlotAttribute.SLOT_C:
            bus_id = self._common_content_configuration.get_bus_id(product=self._product_family, slot_name=slot_name)
        elif slot_name == PcieSlotAttribute.SLOT_M_2:
            bus_id = self._common_content_configuration.get_bus_id(product=self._product_family, slot_name=slot_name)
        else:
            csp_path_attribute = PcieSlotAttribute.PCIE_SLOT_CSP_PATH
            socket_attribute = PcieSlotAttribute.PCIE_SLOT_SOCKET
            if self._product_family in [ProductFamilies.SPR, ProductFamilies.EMR]:
                csp_path = self.PCIE_SLOT_MAPPING_WITH_BUS[slot_name][csp_path_attribute][self._product_family].format(
                    gen)
            elif self._product_family in [ProductFamilies.GNR]:
                csp_path = self.PCIE_SLOT_MAPPING_WITH_BUS[slot_name][csp_path_attribute][self._product_family]
            else:
                raise content_exceptions.TestFail("Not Implemented for product family- {}".format(self._product_family))
            self._log.debug("csp register to get bus info is: {}".format(csp_path))

            socket = self.PCIE_SLOT_MAPPING_WITH_BUS[slot_name][socket_attribute][self._product_family]
            self._log.info("Socket for PCIe Slot: {} is {}".format(slot_name, socket))
            bus_id = csp.get_by_path(csp.SOCKET, csp_path, socket)
            if not bus_id and check_bus_flag:
                raise content_exceptions.TestFail("PCIe device bus is not captured with cscripts for slot:"
                                                  " {}".format(slot_name))
        return bus_id

    def get_driver_list_to_load_and_unloads(self, csp=None):
        """
        This method is to get driver list

        :param csp
        :return driver_name_list
        """
        driver_name_list = []
        self._log.info("Getting Driver List for Load & Unloads.")
        slot_list = PcieSlotAttribute.PCIE_SLOTS_LIST
        for each_slot in slot_list:
            bus_id = self.get_bus_id_for_slot(csp=csp, slot_name=each_slot, gen=5, check_bus_flag=False)
            if each_slot == self.SLOT_C:

                bus_id = "0x" + bus_id
            if not bus_id:
                continue
            self._log.debug("Bus id: {} is for slot Name: {}".format(bus_id, each_slot))
            device_details = self._pcie_provider.get_device_details_with_bus(bus=str(bus_id)[2:])
            if not device_details:
                continue
            for each_bdf, value in device_details.items():
                bdf = each_bdf
                break
            self._log.debug("Device details: {}".format(device_details))
            driver_name = self._pcie_provider.get_pcie_driver_name_by_bdf(bdf=bdf)
            if driver_name:
                driver_name_list.append(driver_name)
        return driver_name_list

    def run_pcierrpoll(self, timeout, pcierrpoll_path):
        """
        This Method will execute the pcierrpoll tool for given time

        :param timeout : The amount of time to wait before checking the error log
        :param pcierrpoll_path : Path of the tool in sut
        :raise: ontent_exceptions.TestFail if failed to find the success string in log
        """
        delete_files_cmd = "rm -rf ERRlog*"
        self._log.info("Removing Error log files.")
        self.os.execute_async(delete_files_cmd, cwd=pcierrpoll_path)
        self.os.execute_async(self.PCIERRPOLL_CMD, cwd=pcierrpoll_path)
        if not self._utils.check_cmd_running(self.PCIERRPOLL_CMD):
            raise content_exceptions.TestFail("The Pcierrpoll tool instance is running on SUT successfully")
        time.sleep(timeout)
        find_cmd = "find {} -type f -name 'ERRlog*'".format(pcierrpoll_path)
        pcierrlog_file = self._common_content_lib.execute_sut_cmd(find_cmd,
                                                                  find_cmd, self._command_timeout,
                                                                  cmd_path=pcierrpoll_path)
        pcie_hostfilepath_before_stress = self.log_dir + "\\" + pcierrlog_file.strip().split("/")[-1]
        self.os.copy_file_from_sut_to_local(pcierrlog_file.strip(), pcie_hostfilepath_before_stress)
        with open(pcie_hostfilepath_before_stress, "r") as pcie_handler:
            self._log.debug("{} contents : {}".format(pcierrlog_file, "\n".join(pcie_handler.readlines())))
            if not self.PCIE_ERR_POLL_SUCCESS_STR in pcie_handler.readlines():
                content_exceptions.TestFail(
                    "Correctable errors found in selected PCIe devices before running the stress")
        self._log.info("No errors found in selected PCIe devices before running the stress")

    def run_pcierrpoll_win(self, timeout, pcierrpoll_path):
        """
        This Method will execute the pcierrpoll tool for given time

        :param timeout : The amount of time to wait before checking the error log
        :param pcierrpoll_path : Path of the tool in sut
        :raise: content_exceptions.TestFail if failed to find the success string in log
        """
        delete_files_cmd = "del ERRlog*"
        find_cmd = "where ERRlog*"
        self._log.info("Removing Error log files.")
        self.os.execute(delete_files_cmd, cwd=pcierrpoll_path, timeout=self._command_timeout)
        self._log.info("Executing the command : {}".format(self.PCIERRPOLL_CMD_WIN))
        self.os.execute(cmd=self.PCIERRPOLL_CMD_WIN, timeout=self._command_timeout, cwd=pcierrpoll_path)
        pcierrlog_file = (self._common_content_lib.execute_sut_cmd(find_cmd,
                                                                  find_cmd, self._command_timeout,
                                                                  cmd_path=pcierrpoll_path))

        self.os.copy_file_from_sut_to_local(pcierrlog_file.strip(),
                                           os.path.join(self.log_dir + os.sep, Path(pcierrlog_file).name.strip()))
        pcie_hostfilepath_before_stress = self.log_dir + "\\" + Path(pcierrlog_file).name
        with open(pcie_hostfilepath_before_stress.strip(), "r") as pcie_handler:
            for eachline in pcie_handler.readlines():
                if self.PCIERRPOLL_STR in eachline:
                    self._log.info("No errors found in selected PCIe devices before running the stress")
                    return True
            raise content_exceptions.TestFail("Error found in PCIe devices before running stress")

    def check_expected_device_speed_and_width(self, csp, slot_info_dict_list, slot_info_dict, pcie_gen):
        """
        Verifying PCIe device Link speed and Width for device.

        :param csp: cscript_object
        :param slot_info_dict_list: list of slot info
        :param slot_info_dict: Slot Info
        :param pcie_gen: PCIe device genration
        :return pcie_device_info_dict: verified pcie device info
        """
        self._log.info("Verifying PCIe device Link speed and Width for device: {}".format(slot_info_dict))
        pcie_device_info_dict = self.verify_required_slot_pcie_device(cscripts_obj=csp,
                                                                      pcie_slot_device_list=slot_info_dict_list,
                                                                      generation=pcie_gen, lnk_stat_width_speed=True,
                                                                      lnk_cap_width_speed=False)[0]
        self._log.info("Device Link Speed and Width found as Expected")
        return pcie_device_info_dict

    def get_pcie_device_generation(self, csp, sdp):
        """
        Get pcie device generation from pcie.sls.

        :param csp: cscript obj
        :param sdp: sdp_obj
        :return generation: pcie device generation
        """
        
        sdp.start_log(self.PCIE_SLS_OUTPUT_LOG, "w")
        self.pcie_obj.sls()
        sdp.stop_log()
        with open(self.PCIE_SLS_OUTPUT_LOG, "r") as log_file:
            pcie_sls_log = log_file.read()
            self._log.info(pcie_sls_log)
        generation = 0
        index = pcie_sls_log.split().index("SOCKET{}".format(self._common_content_configuration.get_cscripts_ei_pcie_device_socket()))
        while index:
            index += 1
            if self._common_content_configuration.get_cscripts_ei_pcie_device_pxp_port() == pcie_sls_log.split()[index]:
                generation = pcie_sls_log.split()[index+1].strip(')')
                break
        if not generation:
            raise content_exceptions.TestFail("Could not extract pcie device generation")
        return generation[-1]

    def trigger_sld(self, reg_expptmbar, addressOffset):
        """
        This Method will write to the expptmbar (Direct Media Access Register) of a PXP port to trigger an SLD

        :param reg_expptmbar : expptmbar register of the pxp port where the SLD should happen
        :param addressOffset : address offset of the pcibar_address register
        """

        import svtools.itp2baseaccess as base

        base_obj = base.baseaccess()
        reg_expptmbar = reg_expptmbar & 0xFFFFFFFFFFFFE0000
        base_obj.mem(reg_expptmbar)
        base_obj.mem(reg_expptmbar + addressOffset)
        base_obj.mem(reg_expptmbar + addressOffset, 4, 1)
        base_obj.mem(reg_expptmbar + addressOffset)

    def get_pcie_controller_gen(self, link_speed_gen):
        """
        This method is to get the PCIE controller gen.
        """
        gen_dict = {PxpInventory.PCIeLinkSpeed.GEN1: 1,
                    PxpInventory.PCIeLinkSpeed.GEN2: 2,
                    PxpInventory.PCIeLinkSpeed.GEN3: 3,
                    PxpInventory.PCIeLinkSpeed.GEN4: 4,
                    PxpInventory.PCIeLinkSpeed.GEN5: 5}

        return gen_dict[link_speed_gen]

    def get_device_bdf(self, socket, port, tested_link_speed=5):
        """
        Gets the device Bus function Number for Pxp port
        :param socket: socket number
        :param port: pxp port
        :param tested_link_speed: GEN speed at which port is linked (i.e.: 4, 5)
        :return str
        """

        if self.reg_provider_class == self.REG_PROVIDER_PYTHONSV:
            # pythonsv is using slightly different nomenclature than cscripts
            match = re.match(r"(pxp\d).(\w+)", port)
            port = port.replace(match.group(), "{}.pcieg{}.{}".format(match.groups()[0], tested_link_speed,
                                                                      match.groups()[1]))

        product_family = self._common_content_lib.get_platform_family()
        io_die = None
        if product_family == ProductFamilies.GNR:
            io0_pxps_path = "io0.uncore.pi5.pxps"
            pxps_per_io_die = len(self.reg_provider_obj.get_by_path(self.reg_provider_obj.SOCKET, io0_pxps_path))
            pxp_port_count = int(re.search(r"\d+", port).group())
            io_die = int(pxp_port_count / pxps_per_io_die)

        sec_bus_reg_path_dict = {ProductFamilies.SPR: "uncore.pi5.{}.cfg.secbus".format(port),
                                 ProductFamilies.EMR: "uncore.pi5.{}.cfg.secbus".format(port),
                                 ProductFamilies.GNR: "io{}.uncore.pi5.{}.cfg.secbus".format(io_die, port)}

        sec_bus_output = self.reg_provider_obj.get_by_path(self.reg_provider_obj.SOCKET, socket_index=socket,
                                             reg_path=sec_bus_reg_path_dict[product_family])
        return hex(sec_bus_output).replace('0x', '')

    def get_device_id(self, bdf):
        """
        Gets the device id for a given bdf
        :param bdf - int or hex value for bdf as obtained from the debug provider
        :return str
        """
        if self.os.os_type == OperatingSystems.LINUX:
            cmd = "cat /sys/bus/pci/devices/0000:{}:00.0/device".format(bdf)
            output = self._common_content_lib.execute_sut_cmd(cmd, "get device id", self._command_timeout)
            return output.strip("\n").replace('0x', '')
        else:
            raise Exception("not implemented on %s" % self.os.os_type)

    def get_sls_log_path(self):
        """
        This method is to get the sls log.

        return sls log path.
        """
        sls_log_file_name = self.PCIE_SLS_OUTPUT_LOG
        return os.path.join(self.log_dir, sls_log_file_name)

    def verify_link_width_speed(self, gen=PxpInventory.PCIeLinkSpeed.GEN5, protocol=PxpInventory.IOProtocol.PCIE):
        """
        This method is to verify the Link Width and speed between PCIE.SLS() and OS.

        :param gen
        :param protocol
        """
        pxp_inventory_obj = PxpInventory(self.sdp_obj, self.pcie_obj, self.get_sls_log_path())

        pcie_dict = pxp_inventory_obj.get_slot_inventory(platform=self._product_family,
                                                         silicon_reg_provider_obj=self.reg_provider_obj)[protocol]

        ret_val = False
        for each_socket, pcie_ports_dict in pcie_dict.items():
            for each_port, device_details_dict in pcie_ports_dict.items():
                if device_details_dict['speed'] == gen:
                    ret_val = True
                    self._log.info("Gen-{} card was found on socket-{} and port-{}. "
                                   "so, proceeding the test for the slots".format(device_details_dict['speed'],
                                                                                  each_socket, each_port))

                    sls_width = device_details_dict['width']

                    bus_out = self.get_pxp_secbus(pxp_port=each_port, socket=int(each_socket))

                    if self.verify_link_speed(bus_num=bus_out, gen=gen, socket=int(each_socket), port=each_port):
                        self._log.info("Link Speed was found as expected for Socket-{} and Port-{}"
                                                          .format(each_socket, each_port))
                        self.verify_link_width(bus_num=bus_out, expected_width=sls_width, socket=int(each_socket),
                                               port=each_port)

        if not ret_val:
            raise content_exceptions.TestFail("{} Card was not detected in SLS".format(gen))

    def get_pxp_io_die(self, pxp_port):
        """
        This method will return io_die for given pxport.

        :param pxp_port
        """
        if pxp_port.split('.')[0] in ["pxp0", "pxp1", "pxp2", "pxp3"]:
            io_die = 0
        else:
            io_die = 1
        return io_die

    def get_pxp_secbus(self, pxp_port, socket):
        """
        This method will give secbus of given port and socket.

        :param pxp_port
        :param socket
        """
        io_die = self.get_pxp_io_die(pxp_port)
        if self._product_family == ProductFamilies.GNR:
            sec_bus_reg = self.SEC_BUS_PATH[self._product_family].format(io_die, pxp_port)
        else:
            sec_bus_reg = self.SEC_BUS_PATH[self._product_family].format(pxp_port)

        bus_out = self.reg_provider_obj.get_by_path(self.reg_provider_obj.SOCKET,
                                                    sec_bus_reg,
                                                    int(socket))
        return bus_out

    def verify_link_speed(self, bus_num, gen=PxpInventory.PCIeLinkSpeed.GEN5, socket=0, port="pxp3.pcieg5.port0"):
        """
        This method is to verify the Link Speed.

        :param bus_num
        :param gen
        :param socket
        :param port
        """
        speed = self._pcie_provider.get_link_status_speed_by_bdf(str(bus_num)[2:] + ":00.0")
        if PxpInventory.PCIeLinkSpeed.MAPPING[gen] not in speed:
            self._log.error("Expected Speed - {}".format(gen))
            self._log.error("Speed in OS- {}".format(speed))
            raise content_exceptions.TestFail("Speed-{} was not found as expect for Socket-{} and Port-{}"
                                              .format(speed, socket, port))
        self._log.info("Speed in OS- {}".format(speed))
        self._log.info("Speed-{} was found as expected for Socket-{} and Port-{}".format(speed, socket,
                                                                                         port))
        return True

    def verify_link_width(self, bus_num, expected_width, socket, port):
        """
        This method is to verify the Link Width.

        :param bus_num
        :param expected_width
        :param socket
        :param port
        """
        os_width = self._pcie_provider.get_link_status_width_by_bdf(str(bus_num)[2:] + ":00.0")
        if os_width != expected_width:
            self._log.error("Expected width- {}".format(expected_width))
            self._log.error("Speed in OS- {}".format(os_width))
            raise content_exceptions.TestFail("Width-{} was not found as expect for Socket-{} and Port-{}"
                                              .format(os_width, socket, port))
        self._log.info("Expected Width - {}".format(expected_width))
        self._log.info("Width in OS- {}".format(os_width))
        self._log.info("Width-{} was found as expected for Socket-{} and Port-{}".format(os_width, socket,
                                                                                         port))

    def get_device_max_speed(self, bdf):
        """
        Gets the device max speed for a given bdf
        :param bdf: int or hex value for bdf as obtained from the debug provider
        :return: max speed.
        """
        if self.os.os_type == OperatingSystems.LINUX:
            cmd = "lspci -vv -s {}:00.0 | grep 'LnkCap:' | grep -o 'Speed\s[1-9]*GT/s'".format(bdf)
            os_output = self.os.execute(cmd, self._command_timeout).stdout
            if len(os_output) == 0:
                raise RuntimeError("No link speed info found for device at {}:00.0".format(bdf))
            else:
                return os_output.strip()
        else:
            raise Exception("not implemented on %s" % self.os.os_type)

    def get_device_current_speed(self, bdf):
        """
        Gets the device current speed for a given bdf
        :param bdf: int or hex value for bdf as obtained from the debug provider
        :return: list of [max_speed, current_speed]
        """
        if self.os.os_type == OperatingSystems.LINUX:
            cmd = "lspci -vv -s {}:00.0 | grep 'LnkSta:' | grep -o 'Speed\s[1-9]*GT/s'".format(bdf)
            os_output = self.os.execute(cmd, self._command_timeout).stdout
            if len(os_output) == 0:
                raise RuntimeError("No link speed info found for device at {}:00.0".format(bdf))
            else:
                return os_output.strip()
        else:
            raise Exception("not implemented on %s" % self.os.os_type)

    def is_aspm_supported(self, bdf):
        """
        Gets the ASPM capability for a given bdf
        :param bdf: int or hex value for bdf as obtained from the debug provider
        :return: boolean
        """
        if self.os.os_type == OperatingSystems.LINUX:
            cmd = "lspci -vv -s {}:00.0 | grep 'LnkCap:' | grep -o 'ASPM not supported'".format(bdf)
            os_output = self.os.execute(cmd, self._command_timeout).stdout
            if len(os_output) == 0:
                return True
            else:
                return False
        else:
            raise Exception("not implemented on %s" % self.os.os_type)
