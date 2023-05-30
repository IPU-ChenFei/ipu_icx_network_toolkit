#!/usr/bin/env python
# coding=utf-8
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
import time

from dtaf_core.providers.console_log import ConsoleLogProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.lib.common_content_lib import CommonContentLib
from src.provider.stressapp_provider import StressAppTestProvider
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions
from src.lib.content_configuration import ContentConfiguration
from src.hsio.upi.hsio_upi_common import HsioUpiCommon


class UpiLaneFailoverCommon(ContentBaseTestCase):
    """
    This Class is used as common class for all the UpiLaneFailover
    """
    CHECK_OS_DELAY_SEC = 15
    LINK_RESET_TIME_SEC = 10
    MAX_ICX_LCC_CORE_CNT = 6
    EINJCTL_REG_NAME = "rxeinjctl0"
    # UPI lane masks
    UPI_LANE_MASK_DISABLE_ALL_LOW_LANES = '0xff'
    UPI_LANE_MASK_DISABLE_ALL_HIGH_LANES = '0xff000'
    UPI_LANE_MASK_DISABLE_FIRST_LOW_LANE = '0x1'
    UPI_LANE_MASK_DISABLE_FIRST_HIGH_LANE = '0x20000'
    UPI_LANE_MASK_ALL_ENABLED = '0x0'

    # UPI error types
    UPI_CORRECTABLE_LINK_WIDTH_CHANGE_ERROR = "upc_correctable_link_width_change_error"
    UPI_SELF_HEALING_ERROR_TYPES = {UPI_CORRECTABLE_LINK_WIDTH_CHANGE_ERROR}

    # UPI Dmesg log error signatures
    UPI_CORRECTABLE_LINK_WIDTH_CHANGE_ERROR_DMESG_SIGNATURES = \
        [r"Hardware error from APEI Generic Hardware Error Source: 0",
         r"It has been corrected by h/w and requires no further action",
         r"event severity: corrected",
         r"Error 0, type: corrected",
         r"section_type: general processor error"]

    UPI_CORR_LINK_WIDTH_CHANGE_ERROR_JOURNALCTL_SIGNATURES = \
        ["severity: corrected",
         "type: corrected",
         "general processor error"]

    UPI_CORRECTABLE_LINK_WIDTH_CHANGE_ERROR_MESSAGES_LIST = ["Hardware event", "Corrected error",
                                                             "CPU"]

    # UPI dumprec.log error signatures in Windows DUT
    UPI_CORRECTABLE_LINK_WIDTH_CHANGE_ERROR_DUMPREC_SIGNATURES = ["Corrected Machine Check", "Error type:       BUS",
                                                                  "Operation:        Generic"]
    TRANSMIT = "transmit"
    RECEIVE = "receive"
    CSCRIPTS_FILE_NAME = "cscripts_log_file.log"
    _REGEX_CMD_FOR_CONNECTED_TO = r".*Connected\sto.*"
    _REGEX_CMD_FOR_UNCONNECTED = r".*unconnected.*"
    _REGEX_CMD_FOR_L0p = r"\|.*\s\s\sL0p.*"
    _REGEX_CMD_FOR_L1 = r"\|.*\s\s\sL1.*"
    WAIT_TIME_IN_SEC = 600
    _REGEX_CMD_FOR_CPU = r"CPU{}\s:\sLEP.*"
    _REGEX_CMD_FOR_SYSTEM = r"System\swill\sbe\streated\s{}.*Configuration"
    _REGEX_CMD_FOR_LINK_SPEED = r".*Link\sSpeed.*"
    PRIME_TOOL_EXECUTION_COMMAND = "./mprime -t"
    _MPRIME_PATH = "/root/Prime95/"
    PRIME95_PROCESS_CMD = "ps -ef | grep mprime"
    PCI_BUS_NUMBER_LIST = [0x7e, 0xfe]
    PCI_DEVICE_NUMBER_LIST = [0x2, 0x3]
    PCI_FUNC_NUMBER = 0x2
    PCI_OFFSET_VALUE = 0x10C
    HALT_GO_DELAY_SEC = 10

    def __init__(self, test_log, arguments, cfg_opts, config=None, console_log_path=None):
        """
        Creates a new UpiLaneFailoverCommon object

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param console_log_path: console log file path
        """
        if config:
            config = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), config)
        super(UpiLaneFailoverCommon, self).__init__(test_log, arguments, cfg_opts, config)
        self._cfg = cfg_opts
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)

        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)

        serial_log_cfg = cfg_opts.find(ConsoleLogProvider.DEFAULT_CONFIG_PATH)
        self._slog = ProviderFactory.create(serial_log_cfg, test_log)  # type: ConsoleLogProvider

        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._check_os_log = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration,
                                               self._common_content_lib)
        self.sum_of_connected_links = 0
        self.serial_console_log_path = console_log_path
        self.log_file_path = self.get_cscripts_log_file_path()
        self._initial_link_speed_in_gt_per_seconds = None
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._platform_stepping = self._common_content_lib.get_platform_stepping()
        self.hsioupi_obj = HsioUpiCommon(test_log,arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Copy mcelog.conf file to sut and reboot
        2. Clear All Os Logs before Starting the Test Case
        3. Set the bios knobs to its default mode.
        4. Set the bios knobs as per the test case.
        5. Reboot the SUT to apply the new bios settings.
        6. Verify the bios knobs whether they updated properly.

        :return: None
        """
        self._install_collateral.copy_mcelog_conf_to_sut()
        super(UpiLaneFailoverCommon, self).prepare()

    def get_cscripts_log_file_path(self):
        """
        # We are getting the Path for thermal alarm check log file

        :return: log_file_path
        """
        cur_path = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(cur_path, self.CSCRIPTS_FILE_NAME)
        return path

    def check_upi_lane_failover_enabled(self):
        """
            Check if UPI data lane failover is enabled in system

            :return: True or False
        """
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:
            upi_failover_en_product_reg_path_dict = {ProductFamilies.SKX: "kti0_reut_ph_ctr1.c_failover_en",
                                                     ProductFamilies.CLX: "kti0_reut_ph_ctr1.c_failover_en",
                                                     ProductFamilies.CPX: "kti0_reut_ph_ctr1.c_failover_en",
                                                     ProductFamilies.ICX: "upi.upi0.ktireut_ph_ctr1.c_failover_en",
                                                     ProductFamilies.SPR: "upi.upi0.ktireut_ph_ctr1.c_failover_en"}
            upi_lane_failover_enable = False
            try:
                self._log.info("Check if UPI lane Failover is Enabled:")

                upi_failover_enable = cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                                               upi_failover_en_product_reg_path_dict
                                                               [cscripts_obj.silicon_cpu_family])
                self._log.info("The register '{}' value is '{}'".format(upi_failover_en_product_reg_path_dict[
                                                                            cscripts_obj.silicon_cpu_family],
                                                                        upi_failover_enable))
                if upi_failover_enable == 1:
                    self._log.info("UPI lane Failover is Enabled:.........")
                    upi_lane_failover_enable = True
                else:
                    self._log.error("UPI lane Failover is not Enabled:.....")

            except Exception as ex:
                self._log.error("Exception occurred '{}'".format(ex))
                raise ex

            return upi_lane_failover_enable

    def inject_and_check_upi_link_width_change_failure(self, direction, lane_mask, change_both_link_ends=False):
        """
        Run transmit and receive UPI tests

        :param direction: transmit or receive
        :param lane_mask: UPI lane mask constants defined above
        :param change_both_link_ends: double end test=true
        :return:
        """
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:
            lane_map_code = None
            sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
            self._common_content_lib = CommonContentLib(self._log, self.os, self._cfg)
            socket_cnt = cscripts_obj.get_socket_count()
            thread_cnt = 2  # assuming 2 thread per core
            if socket_cnt < 2:
                raise RuntimeError("Can not run UPI test on a single socket platform")

            core_count, core_count_status = self._common_content_lib.get_core_count_from_os()
            if not core_count_status:
                raise RuntimeError("Failed to get core count to determine LCC or HCC on ICX")
            else:
                phy_cores = int((core_count / socket_cnt) / thread_cnt)
                lcc_sku = False
                if cscripts_obj.silicon_cpu_family == ProductFamilies.ICX:
                    if phy_cores <= self.MAX_ICX_LCC_CORE_CNT:
                        lcc_sku = True

            if direction != self.TRANSMIT and direction != self.RECEIVE:
                raise RuntimeError("UPI direction(transmit/receive) is not set or unexpected")

            port_count = self.hsioupi_obj.get_upi_port_count()

            # check if platform UPI ports are in a good state to run
            port_check = self._common_content_lib.check_platform_port_states(cscripts_obj, socket_cnt,
                                                                             port_count, require=True)
            if not port_check[0]:
                self._log.info("Found no Valid ports - Failing test ")
                return False
            port_count = port_check[1]
            self._log.info("Found " + str(port_count) + " valid ports")
            # Currently only ICX need dfx
            if cscripts_obj.silicon_cpu_family == ProductFamilies.ICX:
                # unlocking
                self._log.info("Unlocking UPI dfx registers ...")
                for socket in range(socket_cnt):
                    for port in range(port_count):
                        reg_unlock_path1_dict = {
                            ProductFamilies.ICX: "upi.upi" + str(port) + ".dfx_lck_ctl_cfg.reutenglck"}

                        reg_unlock_path2_dict = {
                            ProductFamilies.ICX: "upi.upi" + str(port) + ".dfx_lck_ctl_cfg.reutlck"}

                        cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                                 reg_unlock_path1_dict[cscripts_obj.silicon_cpu_family],
                                                 socket_index=socket).write(0)
                        cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                                 reg_unlock_path2_dict[cscripts_obj.silicon_cpu_family],
                                                 socket_index=socket).write(0)

            for socket in range(socket_cnt):
                for port in range(port_count):
                    # verify port is in a good state
                    if not self._common_content_lib.verify_port_state(cscripts_obj, socket, port):
                        self._log.info("Skipping invalid port-" + "socket" + str(socket) + " port" + str(port))
                        continue
                    self._log.info("\n Testing SOCKET " + str(socket) + " UPI PORT " + str(port))

                    ph_ctr1_path_dict = {ProductFamilies.CLX: "kti" + str(port) + "_reut_ph_ctr1",
                                         ProductFamilies.CPX: "kti" + str(port) + "_reut_ph_ctr1",
                                         ProductFamilies.SKX: "kti" + str(port) + "_reut_ph_ctr1",
                                         ProductFamilies.ICX: "upi.upi" + str(port) + ".ktireut_ph_ctr1",
                                         ProductFamilies.SPR: "upi.upi" + str(port) + ".ktireut_ph_ctr1"}

                    ph_css_path_dict = {ProductFamilies.CLX: "kti" + str(port) + "_reut_ph_css",
                                        ProductFamilies.CPX: "kti" + str(port) + "_reut_ph_css",
                                        ProductFamilies.SKX: "kti" + str(port) + "_reut_ph_css",
                                        ProductFamilies.ICX: "upi.upi" + str(port) + ".ktireut_ph_css",
                                        ProductFamilies.SPR: "upi.upi" + str(port) + ".ktireut_ph_css"}

                    get_peer_path_dict = {ProductFamilies.CLX: "kti" + str(port) + "_lp0",
                                          ProductFamilies.CPX: "kti" + str(port) + "_lp0",
                                          ProductFamilies.SKX: "kti" + str(port) + "_lp0",
                                          ProductFamilies.ICX: "upi.upi" + str(port) + ".ktilp0",
                                          ProductFamilies.SPR: "upi.upi" + str(port) + ".ktilp0"}

                    lane_disable_path_trx_dict = {ProductFamilies.CLX: "kti" + str(port) + "_reut_ph_tdc",
                                                  ProductFamilies.CPX: "kti" + str(port) + "_reut_ph_tdc",
                                                  ProductFamilies.SKX: "kti" + str(port) + "_reut_ph_tdc",
                                                  ProductFamilies.ICX: "upi.upi" + str(port) + ".ktireut_ph_tdc",
                                                  ProductFamilies.SPR: "upi.upi" + str(port) + ".ktireut_ph_tdc"}

                    lane_disable_path_rdv_dict = {ProductFamilies.CLX: "kti" + str(port) + "_reut_ph_rdc",
                                                  ProductFamilies.CPX: "kti" + str(port) + "_reut_ph_rdc",
                                                  ProductFamilies.SKX: "kti" + str(port) + "_reut_ph_rdc",
                                                  ProductFamilies.ICX: "upi.upi" + str(port) + ".ktireut_ph_rdc",
                                                  ProductFamilies.SPR: "upi.upi" + str(port) + ".ktireut_ph_rdc"}

                    setaccess_path_dict = {ProductFamilies.SPR: "upi.upi" + str(port),
                                           ProductFamilies.CPX: "kti" + str(port),
                                           ProductFamilies.SKX: "kti" + str(port),
                                           ProductFamilies.ICX: "upi.upi" + str(port)}

                    # Setting expected map codes based on a few elements
                    expected_lane_map_code = self.get_expected_lane_map_code(lane_mask, lcc_sku, direction, socket_cnt,
                                                                             socket, port)

                    if direction == self.TRANSMIT:
                        lane_disable_path = lane_disable_path_trx_dict[cscripts_obj.silicon_cpu_family]

                    else:  # Receive path
                        lane_disable_path = lane_disable_path_rdv_dict[cscripts_obj.silicon_cpu_family]

                    # check lane is enabled
                    if self.set_get_lane_mask("get", direction, socket, lane_disable_path,
                                              ph_ctr1_path_dict[cscripts_obj.silicon_cpu_family],
                                              setaccess_path_dict[cscripts_obj.silicon_cpu_family], sdp_obj=sdp_obj) != '0x0':
                        self._log.info("Found lane mask not cleared - Attempting to reset it to 0")
                        if not self.set_get_lane_mask("set", direction, socket, lane_disable_path,
                                                      ph_ctr1_path_dict[cscripts_obj.silicon_cpu_family],
                                                      setaccess_path_dict[cscripts_obj.silicon_cpu_family],
                                                      lanemask=self.UPI_LANE_MASK_ALL_ENABLED, sdp_obj=sdp_obj):
                            raise RuntimeError("Was not able to set lane mask  - Verify BIOS knobs are configured")

                    # Set time and data on the OS
                    self._common_content_lib.set_datetime_on_linux_sut()

                    self._log.info("Clearing OS logs .......")
                    self._common_content_lib.clear_all_os_error_logs()

                    # get peer information
                    peer_socket = cscripts_obj.get_field_value(scope=cscripts_obj.UNCORE, reg_path=get_peer_path_dict[
                        cscripts_obj.silicon_cpu_family], field="base_nodeid", socket_index=socket)
                    peer_port = cscripts_obj.get_field_value(scope=cscripts_obj.UNCORE, reg_path=get_peer_path_dict[
                        cscripts_obj.silicon_cpu_family], field="sending_port", socket_index=socket)

                    peer_socket = str(peer_socket).replace("[0x", "").replace("]", "")
                    peer_port = str(peer_port).replace("[0x", "").replace("]", "")

                    self._log.info("Disabling UPI lanes for test ...")
                    if not self.set_get_lane_mask("set", direction, socket, lane_disable_path,
                                                  ph_ctr1_path_dict[cscripts_obj.silicon_cpu_family],
                                                  setaccess_path_dict[cscripts_obj.silicon_cpu_family],
                                                  lanemask=lane_mask, sdp_obj=sdp_obj):
                        raise RuntimeError("Was not able to set lane mask ")

                    ph_css_peer_path_dict = {ProductFamilies.CLX: "kti" + str(peer_port) + "_reut_ph_css",
                                             ProductFamilies.CPX: "kti" + str(peer_port) + "_reut_ph_css",
                                             ProductFamilies.SKX: "kti" + str(peer_port) + "_reut_ph_css",
                                             ProductFamilies.ICX: "upi.upi" + str(peer_port) + ".ktireut_ph_css",
                                             ProductFamilies.SPR: "upi.upi" + str(peer_port) + ".ktireut_ph_css"}

                    peer_lane_disable_path_trx_dict = {ProductFamilies.CLX: "kti" + str(peer_port) + "_reut_ph_tdc",
                                                       ProductFamilies.CPX: "kti" + str(peer_port) + "_reut_ph_tdc",
                                                       ProductFamilies.SKX: "kti" + str(peer_port) + "_reut_ph_tdc",
                                                       ProductFamilies.ICX: "upi.upi" + str(port) + ".ktireut_ph_tdc",
                                                       ProductFamilies.SPR: "upi.upi" + str(port) + ".ktireut_ph_tdc"}

                    peer_lane_disable_path_rcv_dict = {ProductFamilies.CLX: "kti" + str(peer_port) + "_reut_ph_rdc",
                                                       ProductFamilies.CPX: "kti" + str(peer_port) + "_reut_ph_rdc",
                                                       ProductFamilies.SKX: "kti" + str(peer_port) + "_reut_ph_rdc",
                                                       ProductFamilies.ICX: "upi.upi" + str(port) + ".ktireut_ph_rdc",
                                                       ProductFamilies.SPR: "upi.upi" + str(port) + ".ktireut_ph_rdc"}

                    if direction == self.TRANSMIT:
                        peer_lane_disable_path = peer_lane_disable_path_trx_dict[cscripts_obj.silicon_cpu_family]
                    else:
                        peer_lane_disable_path = peer_lane_disable_path_rcv_dict[cscripts_obj.silicon_cpu_family]

                    if change_both_link_ends:
                        self._log.info("\nSetting peer lanemask for double end test\n")
                        if not self.set_get_lane_mask("set", direction, peer_socket, peer_lane_disable_path,
                                                      ph_ctr1_path_dict[cscripts_obj.silicon_cpu_family],
                                                      setaccess_path_dict[cscripts_obj.silicon_cpu_family],
                                                      lanemask=lane_mask, sdp_obj=sdp_obj):
                            raise RuntimeError("Was not able to set lane mask ")

                    # if transmit lane test - verify peer s_clm information else in the receive test verify
                    # the local s_clm
                    if direction == self.TRANSMIT:
                        self._log.info("Verify link partner observes a failover to lanes")
                        lane_map_code = cscripts_obj.get_field_value(scope=cscripts_obj.UNCORE,
                                                                     reg_path=ph_css_peer_path_dict[
                                                                         cscripts_obj.silicon_cpu_family],
                                                                     field="s_clm", socket_index=peer_socket)
                        if not lane_map_code:
                            raise content_exceptions.TestFail("failed to get lane map code")
                        lane_map_code = int(str(lane_map_code).replace("[0x", "").replace("]", ""))
                        self._log.info(
                            "The peer s_clm lane map code on socket" + str(peer_socket) + " port" + str(port) +
                            " reads:" + str(
                                ph_css_peer_path_dict[cscripts_obj.silicon_cpu_family]) + ".s_clm=" + str(
                                lane_map_code))

                    elif direction == self.RECEIVE:  # receive lanes
                        self._log.info("Verify link observes a failover to lanes")
                        lane_map_code = cscripts_obj.get_field_value(scope=cscripts_obj.UNCORE,
                                                                     reg_path=ph_css_path_dict[
                                                                         cscripts_obj.silicon_cpu_family],
                                                                     field="s_clm", socket_index=socket)
                    if not lane_map_code:
                        raise content_exceptions.TestFail("failed to get lane map code")
                    lane_map_code = int(str(lane_map_code).replace("[0x", "").replace("]", ""))
                    self._log.info(
                        "The s_clm lane map code on socket" + str(peer_socket) + " port" + str(port) + " reads:" +
                        str(ph_css_path_dict[cscripts_obj.silicon_cpu_family]) + ".s_clm=" + str(lane_map_code))

                    if lane_map_code != expected_lane_map_code:
                        self._log.error(
                            "FAIL: Expected peer s_clm lane map code to read as:" + str(expected_lane_map_code) +
                            ":actual=" + str(lane_map_code) + "-SOCKET " + str(socket) + " UPI PORT " + str(port))
                        return False
                    else:
                        self._log.info("PASS: s_clm indicated failover to correct lanes as expected code=" + str(
                            lane_map_code) + " -SOCKET " + str(socket) + " UPI PORT " + str(port))

                    # Clear disabled lanes
                    self._log.info("Resetting upi lanes...")
                    if not self.set_get_lane_mask("set", direction, socket, lane_disable_path,
                                                  ph_ctr1_path_dict[cscripts_obj.silicon_cpu_family],
                                                  setaccess_path_dict[cscripts_obj.silicon_cpu_family],
                                                  lanemask=self.UPI_LANE_MASK_ALL_ENABLED, sdp_obj=sdp_obj):
                        raise RuntimeError("Was not able to set lane mask ")

                    # Check OS logs for error message
                    time.sleep(self.CHECK_OS_DELAY_SEC)
                    if not self.obtain_messages_and_dmesg_and_parse_upi_corrected_errors():
                        self._log.error("Check in the OS Log for Error Message failed")
                        return False

            self._log.info("\n Test passed on all UPI ports\n")
            return True

    def obtain_messages_and_dmesg_and_parse_upi_corrected_errors(self):
        """
        Obtain the messages and dmesg files from Linux DUT using SSH to create and transfer the files, then parse the
        files for a UPI corrected error

        :return: True if successful in obtaining and parsing for the error, false otherwise
        """
        self._log.info("Obtain and parse corrected error logs in messages")
        verified_messages_contains_os_log_errors = \
            self._check_os_log.verify_os_log_error_messages(__file__, self._check_os_log.DUT_MESSAGES_FILE_NAME,
                                                            self.UPI_CORRECTABLE_LINK_WIDTH_CHANGE_ERROR_MESSAGES_LIST)

        self._log.info("Obtain and parse corrected error logs in dmesg")
        verified_dmesg_contains_os_log_errors = \
            self._check_os_log. \
                verify_os_log_error_messages(__file__, self._check_os_log.DUT_DMESG_FILE_NAME,
                                             self.UPI_CORRECTABLE_LINK_WIDTH_CHANGE_ERROR_DMESG_SIGNATURES)

        self._log.info("Obtain and parse corrected error logs in journalctl")
        verified_journalctl_contains_os_log_errors = \
            self._check_os_log.verify_os_log_error_messages(__file__,
                                                            self._check_os_log.DUT_JOURNALCTL_FILE_NAME,
                                                            self.UPI_CORR_LINK_WIDTH_CHANGE_ERROR_JOURNALCTL_SIGNATURES)

        return verified_messages_contains_os_log_errors or verified_dmesg_contains_os_log_errors or \
               verified_journalctl_contains_os_log_errors

    def set_get_lane_mask(self, action, direction, socket, lane_disable_path, ctr1_path, access_path, lanemask=None,
                          sdp_obj = None):
        """
        Get/Set lane mask to disable lanes - transmit or receive

        :param action: get or set
        :param direction: transmit and receive
        :param socket:
        :param lane_disable_path: assume transmit and receive path
        :param ctr1_path: path to control register to reset links
        :param access_path: path to update register access mode
        :param lanemask: disable lane mask
        :return:
        """
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:

            if direction == self.TRANSMIT:
                lane_field = "txdatalanedisable"
            elif direction == self.RECEIVE:
                lane_field = "rxdatalanedisable"
            else:
                raise RuntimeError("Unknown UPI direction variable given")

            reg_path = lane_disable_path + "." + str(lane_field)
            self._log.info("Lane disable path=" + str(reg_path))

            if action == "get":
                get_lane_mask = cscripts_obj.get_by_path(cscripts_obj.UNCORE, reg_path, socket_index=socket).get_value()
                get_lane_mask = str(get_lane_mask).replace("[", "").replace("]", "")
                get_lane_mask = self.check_hexified(get_lane_mask)
                self._log.info("Retrieving lane mask ... data currently reads: " + get_lane_mask)
                return get_lane_mask

            elif action == "set":
                self._log.info("Setting UPI lanes on socket" + str(socket) + "." + str(lane_disable_path) + "." + str(
                    lane_field) + ".write(" + str(lanemask) + ")")

                cscripts_obj.get_by_path(cscripts_obj.UNCORE, reg_path, socket_index=socket).write(int(lanemask, 16))

                lane_data = cscripts_obj.get_field_value(scope=cscripts_obj.UNCORE, reg_path=lane_disable_path,
                                                         field=lane_field, socket_index=socket)
                lane_data = str(lane_data).replace("[", "").replace("]", "")
                lane_data = self.check_hexified(lane_data)
                self._log.info(
                    "lanemask to set=" + str(lanemask) + "-lanemask disable register=" + str(lane_disable_path)
                    + "-- after write=" + str(lane_data))

                if lane_data != lanemask:
                    self._log.error("Unable to set lane mask")
                    return False
                # as of SPR IFWI 54.d26 no need to set access mode to pcicfg
                # reset lanes
                self._log.info("Reset UPI links to apply width change")

                cscripts_obj.get_by_path(cscripts_obj.UNCORE, ctr1_path, socket_index=socket).cp_reset.write(1)
                self._log.info("resetting links - " + str(ctr1_path) + ".cp_reset.write(1)")

                time.sleep(self.LINK_RESET_TIME_SEC)
                return True
            else:

                raise RuntimeError("Unknown action for transmit_lane_mask function")

    def check_hexified(self, value):
        """
        Ensure the value is a string, and convert to hex if not already

        :param value:
        :return:
        """
        str_value = str(value)
        if str_value.find("0x") == -1:
            str_modified = hex(int(str_value))
            return str_modified
        else:
            return str_value

    def get_expected_lane_map_code(self, lane_mask, is_lcc, direction, socketcnt, socket, port):
        """
        Set the expected lane map codes

        :param lane_mask: disable lane mask
        :param is_lcc:  True if ICX LCC SKU
        :param direction: receive or transmit
        :param socketcnt: socket count
        :param socket: socket number
        :param port: UPI port
        :return:
        """
        try:
            with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:
                # 1 in the list indicates port is reversed
                # [[0, 1, 0], [0, 1, 0]] -> socket0 port1 and socket1 port1 are reversed
                if direction == self.RECEIVE:
                    # receive port specifics
                    # Assuming 6 ports for CPX
                    rcv_cpx6_2s = [[0, 0, 1, 0, 1, 0], [1, 0, 1, 0, 0, 0]]  # Option 1 UPI cabling
                    rcv_cpx6_4s = [[0, 0, 1, 0, 1, 0], [1, 0, 1, 0, 0, 0], [0, 0, 1, 0, 1, 0], [1, 0, 1, 0, 0, 0]]
                    # 8S not verified as yet
                    rcv_cpx6_8s = [[0, 0, 1, 0, 1, 0], [1, 0, 1, 0, 0, 0], [0, 0, 1, 0, 1, 0], [1, 0, 1, 0, 0, 0],
                                   [0, 0, 1, 0, 1, 0], [1, 0, 1, 0, 0, 0], [0, 0, 1, 0, 1, 0], [1, 0, 1, 0, 0, 0]]

                    rcv_cpx4_2s = [[1, 1, 1], [1, 1, 1]]

                    # Assuming 2 socket & 3 ports for ICX
                    rcv_icxlcc = [[1, 1, 1], [1, 1, 1]]
                    rcv_icxhcc = [[0, 1, 0], [0, 1, 0]]

                    # default is all not reversed(up to 8S and 6 ports)
                    rev_ports = [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
                                 [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]

                    if cscripts_obj.silicon_cpu_family == ProductFamilies.ICX:
                        if is_lcc:
                            rev_ports = rcv_icxlcc
                        else:
                            rev_ports = rcv_icxhcc
                    elif cscripts_obj.silicon_cpu_family == ProductFamilies.CPX:
                        if not self.is_cpx4():

                            if socketcnt == 2:
                                rev_ports = rcv_cpx6_2s
                            elif socketcnt == 4:
                                rev_ports = rcv_cpx6_4s
                            elif socketcnt == 8:
                                rev_ports = rcv_cpx6_8s
                            else:
                                self._log.error("Unknown number of sockets for CPX6" + str(socket))
                                return False
                        else:  # CPX4
                            rev_ports = rcv_cpx4_2s

                    elif cscripts_obj.silicon_cpu_family == ProductFamilies.SPR:
                        # SPR A0 and B0 has 3 ports
                        if self._platform_stepping.startswith("A") or self._platform_stepping.startswith("B"):
                            if socketcnt == 2:
                                rev_ports = [[0, 0, 1], [0, 0, 1]]
                            elif socketcnt == 4:
                                rev_ports = [[0, 1, 0], [1, 0, 0], [0, 1, 0], [1, 0, 0]]
                            else:
                                self._log.error("Unknown number of sockets for SPR" + str(socket))
                                return False
                        else:
                            if socketcnt == 2:
                                rev_ports = [[0, 0, 1, 1], [0, 0, 1, 1]]
                            elif socketcnt == 4:
                                rev_ports = [[0, 1, 0], [1, 0, 0], [0, 1, 0], [1, 0, 0]]
                            elif socketcnt == 8:
                                rev_ports = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
                                             [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
                            else:
                                self._log.error("Unknown number of sockets for SPR" + str(socket))
                                return False

                    if rev_ports[socket][port] == 1:
                        return self.set_reversed_lane_map_code(lane_mask)
                    else:
                        return self.set_normal_lane_map_code(lane_mask)

                else:  # transmit
                    rev_ports = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]

                    if cscripts_obj.silicon_cpu_family == ProductFamilies.ICX:

                        if rev_ports[socket][port] == 1:
                            return self.set_reversed_lane_map_code(lane_mask)
                        else:
                            return self.set_normal_lane_map_code(lane_mask)

                    else:  # Other than ICX
                        return self.set_normal_lane_map_code(lane_mask)
        except Exception as ex:
            log_err = "An Exception Occurred : {}".format(ex)
            self._log.error(log_err)
            raise content_exceptions.TestFail(log_err)

    def set_normal_lane_map_code(self, lane_mask):
        """
        Map code that is expected if no lane reversals are present in the platform
        s.clm field
            0b111 - lanes 0..19
            0b001 - lanes 0..7
            0b100 - lanes 12..19'
            0x1  Failover to lower lanes [7:0]
            0x4  Failover to upper lanes [12:19]
            0x7  no fail-over
            0x0  no valid lane set

        :param lane_mask:
        :return:
        """
        self._log.info("Applying normal expected map code")
        # No reversal for any lanes
        if lane_mask == self.UPI_LANE_MASK_DISABLE_ALL_LOW_LANES:
            expected_lane_map_code = 0x4
        elif lane_mask == self.UPI_LANE_MASK_DISABLE_ALL_HIGH_LANES:
            expected_lane_map_code = 0x1
        elif lane_mask == self.UPI_LANE_MASK_DISABLE_FIRST_LOW_LANE:
            expected_lane_map_code = 0x4
        elif lane_mask == self.UPI_LANE_MASK_DISABLE_FIRST_HIGH_LANE:
            expected_lane_map_code = 0x1
        else:
            raise RuntimeError("Lane mask is not set or unexpected")

        return expected_lane_map_code

    def set_reversed_lane_map_code(self, lane_mask):
        """

        :param lane_mask:
        :return:
        """
        self._log.info("Applying reversed expected map code")
        # Lanes are reversed
        if lane_mask == self.UPI_LANE_MASK_DISABLE_ALL_LOW_LANES:
            expected_lane_map_code = 0x1
        elif lane_mask == self.UPI_LANE_MASK_DISABLE_ALL_HIGH_LANES:
            expected_lane_map_code = 0x4
        elif lane_mask == self.UPI_LANE_MASK_DISABLE_FIRST_LOW_LANE:
            expected_lane_map_code = 0x1
        elif lane_mask == self.UPI_LANE_MASK_DISABLE_FIRST_HIGH_LANE:
            expected_lane_map_code = 0x4
        else:
            raise RuntimeError("Lane mask is not set or unexpected")

        return expected_lane_map_code

    def is_cpx4(self, socket=0):
        """
        Check if the CPU installed is CPX4 or CPX6
        :param socket:
        :return: True if CPX4
        """
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:
            cap_reg_path = "pcu_cr_capid3_cfg"
            mcp_reg = cscripts_obj.get_by_path(cscripts_obj.UNCORE, cap_reg_path, socket_index=socket)
            if mcp_reg.capid3_6 == 1 and mcp_reg.capid3_7 == 0:
                # 1 die means 3 channel per MC    CPX6
                return False
            elif mcp_reg.capid3_6 == 0 and mcp_reg.capid3_7 == 1:
                # 2 die means 2 channel per MC    CPX4
                return True
            else:
                raise Exception("capid3 is not configured correctly!")

    def check_platform_port_states(self, socket_cnt, port_cnt, require=False):
        """
        Checking Link states. ICX and CPX have minimum 3 ports per socket if cfg'd correctly
        if require=True , this function will return a bool to indicate the requirement has been met

        :param socket_cnt:
        :param port_cnt:
        :param require: returns bool if True
        :return bool   if number of good ports >=3 to continue test # ICX and CPX have a min 3 ports/skt(6 on 4S CPX)
        """
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:
            good_state = [0xf, 0x5]
            # Assuming max 8S
            good_port_cnt_per_skt = [0, 0, 0, 0, 0, 0, 0, 0]

            for socket in range(socket_cnt):
                for port in range(port_cnt):
                    ph_css_path_dict = {ProductFamilies.CLX: "kti" + str(port) + "_reut_ph_css",
                                        ProductFamilies.CPX: "kti" + str(port) + "_reut_ph_css",
                                        ProductFamilies.ICX: "upi.upi" + str(port) + ".ktireut_ph_css",
                                        ProductFamilies.SPR: "upi.upi" + str(port) + ".ktireut_ph_css"}

                    rx_state = cscripts_obj.get_field_value(cscripts_obj.UNCORE,
                                                            reg_path=ph_css_path_dict[cscripts_obj.silicon_cpu_family],
                                                            field="s_rx_state", socket_index=socket)
                    tx_state = cscripts_obj.get_field_value(cscripts_obj.UNCORE,
                                                            reg_path=ph_css_path_dict[cscripts_obj.silicon_cpu_family],
                                                            field="s_tx_state", socket_index=socket)

                    if rx_state not in good_state or tx_state not in good_state:
                        self._log.info("Unexpected link state found on S" + str(socket) + " port(" + str(port) +
                                       "(expected=" + str(good_state) + ")but found Link state rx=" +
                                       str(rx_state) + " & tx=" + str(tx_state))
                    else:
                        self._log.info("Expected link state found(" + str(good_state) + ")")
                        good_port_cnt_per_skt[socket] += 2

            if require:
                for socket in range(socket_cnt):
                    if good_port_cnt_per_skt[socket] < 3:
                        self._log.info(
                            "Socket" + str(socket) + " does not have the required 3 ports available for test(" +
                            str(good_port_cnt_per_skt[socket]) + " valid ports detected)")
                        self._log.info("Try AC cycling the platform - and run again")
                        return False
                    else:
                        self._log.info(
                            "Socket" + str(socket) + " has " + str(good_port_cnt_per_skt[socket]) + " valid ports "
                                                                                                    "available")
                return True

    def verify_upi_coherent_link(self):
        """
        This Method is Used to Verify Upi Coherent Link by Calculating Number of Connections for Each Socket and Adding
        them.

        :return: True or False
        :raise: Exception if Unable to verify Upi Coherent Link
        """
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        upi_obj = cscripts_obj.get_upi_obj()
        self._common_content_lib = CommonContentLib(self._log, self.os, self._cfg)
        self._content_config_obj = ContentConfiguration(self._log)
        upi_link_status = False
        try:
            sockets_count = cscripts_obj.get_socket_count()
            if sockets_count >= 2:
                coherent_link_dict = {
                    "eXtreme Core Count": sockets_count * self._content_config_obj.get_extreme_core_count_multiplier(),
                    "High Core Count": sockets_count * self._content_config_obj.get_high_core_count_multiplier(),
                    "Low Core Count": sockets_count * self._content_config_obj.get_low_core_count_multiplier(),
                }
                self._log.info("There are '{}' Sockets in the System".format(sockets_count))
                self._log.info("Halt the System")
                sdp_obj.halt()
                expected_socket_link_count = \
                    coherent_link_dict[self._common_content_lib.get_cpu_physical_chop_info(cscripts_obj, sdp_obj,
                                                                                           self.CSCRIPTS_FILE_NAME)]
                self._log.info("Expected Coherent Links are '{}'".format(expected_socket_link_count))
                for socket in range(sockets_count):
                    sdp_obj.start_log(self.log_file_path, "w")
                    self._log.info("List Upi Topology Of Socket{}".format(socket))
                    upi_obj.topology(socket=socket)
                    sdp_obj.stop_log()
                    with open(self.log_file_path, "r") as log_file:
                        log_file_list = log_file.readlines()
                        self._log.info("".join(log_file_list))
                        connected_to_string = re.compile(self._REGEX_CMD_FOR_CONNECTED_TO)
                        # Removing Empty Strings from extracted List
                        connected_to_value = [val for val in
                                              (connected_to_string.search("".join(log_file_list)).group()
                                               .strip().split("|")) if val]
                        if re.match(self._REGEX_CMD_FOR_UNCONNECTED, "".join(connected_to_value)):
                            unconnected_string = re.compile(self._REGEX_CMD_FOR_UNCONNECTED)
                            # Remove Un Connected values from the List
                            connected_to_value = [val for val in connected_to_value if
                                                  not unconnected_string.match(val)]
                        self._log.info("Connections of Socket{} are '{}'".format(socket,
                                                                                 "".join(
                                                                                     connected_to_value
                                                                                     [1:]).strip()))
                        self._log.info("Socket{} has {} Connections".format(socket, len(connected_to_value) - 1))
                        self.sum_of_connected_links += len(connected_to_value) - 1
                self._log.info("There are '{}' Coherent Links and Expected Coherent Links are '{}'"
                               .format(self.sum_of_connected_links, expected_socket_link_count))
                if expected_socket_link_count == self.sum_of_connected_links:
                    self._log.info("Sum of Socket Links are equal to {} and are as Expected"
                                   .format(self.sum_of_connected_links))
                    upi_link_status = True
                else:
                    log_error = "Sum of Socket Links are {} which are Not Matched with expected Socket Links {}" \
                        .format(self.sum_of_connected_links, expected_socket_link_count)
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
            else:
                log_error = "This Test Only Supported on Systems which contains Atleast 2 Sockets"
                self._log.error(log_error)
                raise RuntimeError(log_error)
        except Exception as ex:
            self._log.error("Unable to Verify Upi Coherent Link due to Exception '{}'".format(ex))
            raise Exception(ex)
        finally:
            sdp_obj.go()
        return upi_link_status

    def verify_upi_link_power_management_status(self):
        """
        This Method is Used to Verify Upi Link Power Management Status and check if Link is Entered in L0p and L1.

        :return: None
        """
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        try:
            upi_obj = cscripts_obj.get_upi_obj()
            self._log.info("Halt the System ...")
            sdp_obj.halt()
            sdp_obj.start_log(self.log_file_path, "w")
            self._log.info("List the Upi Topology")
            upi_obj.topology()
            sdp_obj.stop_log()
            with open(self.log_file_path, "r") as log_file:
                log_file_list = log_file.readlines()
                self._log.info("".join(log_file_list))
                l0p_string = re.compile(self._REGEX_CMD_FOR_L0p)
                l1_string = re.compile(self._REGEX_CMD_FOR_L1)
                l0p_string_value = [val for val in (l0p_string.search("".join(log_file_list)).group().strip()
                                                    .split("|")) if val]
                self._log.info("Value of L0p is '{}'".format("".join(l0p_string_value[1:]).strip()))
                l1_string_value = [val for val in (l1_string.search("".join(log_file_list)).group().strip()
                                                   .split("|")) if val]
                self._log.info("Value of L1 is '{}'".format("".join(l1_string_value[1:]).strip()))
                if l0p_string_value[2].strip() == "" or l1_string_value[2].strip() == "":
                    log_error = "Link Does not Enter into L0p State and L1 State"
                    self._log.error(log_error)
                    raise Exception(log_error)
                else:
                    self._log.info("Link Entered into L0p State and L1 State Successfully")
        except Exception as ex:
            raise ex
        finally:
            sdp_obj.go()

    def verify_upi_sanity_check(self):
        """
        This Method is Used to Verify Upi Sanity Check by Validating the Data obtained from Serial Log.

        :return: True if Data in the Serial Log is Validated else False
        """
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        socket_count = cscripts_obj.get_socket_count()
        console_log_path = os.path.join(self._slog.logpath_local, self.serial_console_log_path)
        console_data = open(console_log_path).readlines()
        self._log.info("".join(console_data))
        regex_system = re.findall(self._REGEX_CMD_FOR_SYSTEM.format(socket_count), "".join(console_data))
        self._log.info("".join(set(regex_system)))
        if len(regex_system) != 0:
            self._log.info("System Configuration is As Expected for '{}' Sockets".format(socket_count))
        else:
            log_error = "System Configuration is Not as Expected for '{}' Sockets".format(socket_count)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        for socket in range(socket_count):
            regex_cpu = re.findall(self._REGEX_CMD_FOR_CPU.format(socket), "".join(console_data))
            self._log.info("CPU Configuration for Socket{} is - {}".format(socket, "".join(set(regex_cpu))))
            if len(regex_cpu) == 0:
                log_error = "Data in the Serial Log is Not As Expected for Socket{} and Sanity Check Failed" \
                    .format(socket)
                self._log.error(log_error)
                raise Exception(log_error)
            else:
                self._log.info("Data in the Serial log is as Expected and Sanity Check is Successful for Socket{}"
                               .format(socket))
        return True

    def execute_stress_tool(self):
        """
        This Method is Used to Install and Execute one of the CPU Stress tool (Prime95)

        :return:
        """
        if not self.os.is_alive():
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        self._log.info("Install Prime95 Stress tool")
        self._install_collateral.install_prime95()
        self._log.info("Installation of Prime95 Stress tool is Successful and Executing it")
        self.os.execute_async(self.PRIME_TOOL_EXECUTION_COMMAND, cwd=self._MPRIME_PATH)
        cmd_result = self.os.execute(self.PRIME95_PROCESS_CMD,
                                     self._common_content_configuration.get_command_timeout())
        if cmd_result.cmd_failed():
            log_error = "Failed to execute command line '{}'".format(self.PRIME95_PROCESS_CMD)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        if self.PRIME_TOOL_EXECUTION_COMMAND in cmd_result.stdout:
            self._log.info("Mprime process successfully started and process "
                           "details = '{}'".format(cmd_result.stdout))
        else:
            log_error = "Mprime process did not started successfully..."
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def verify_upi_link_speed(self, is_stress_tool_executed=None):
        """
        This Method is Used to Upi Link Speed by using Csripts Command before and after executing the Stress Tool and
        verify whether there is any change in link speed after executing stress test.

        :param is_stress_tool_executed: True or False to identify whether stress tool is executed.
        :return:
        """
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        link_speed_status = False
        try:
            upi_obj = cscripts_obj.get_upi_obj()
            sdp_obj.start_log(self.log_file_path, "w")
            self._log.info("Halt the System")
            sdp_obj.halt()
            self._log.info("List the Upi Topology")
            upi_obj.topology()
            sdp_obj.stop_log()
            with open(self.log_file_path, "r") as log_file:
                log_file_list = log_file.readlines()
                self._log.info("".join(log_file_list))
                link_speed_string = re.compile(self._REGEX_CMD_FOR_LINK_SPEED)
                if is_stress_tool_executed:
                    link_speed_in_gt_per_sec = link_speed_string.search("".join(log_file_list)).group() \
                                                   .split("|")[2].strip()[:4]
                    if not link_speed_in_gt_per_sec < self._initial_link_speed_in_gt_per_seconds:
                        self._log.info("Link Speed is Not Downgraded after Execution of Stress Tool")
                        link_speed_status = True
                    else:
                        log_error = "Link Speed is Downgraded after Execution of Stress Tool"
                        self._log.error(log_error)
                        raise RuntimeError(log_error)
                else:
                    self._initial_link_speed_in_gt_per_seconds = \
                        link_speed_string.search("".join(log_file_list)).group().split("|")[2].strip()[:4]
                    self._log.info(
                        "Initial Link Speed is '{}' GT/s".format(self._initial_link_speed_in_gt_per_seconds))
        except Exception as ex:
            raise ex
        finally:
            sdp_obj.go()
        return link_speed_status

    def verify_processor_upi_width(self):
        """
        This Method is Used to Verify Upi Processor Width by Getting Tx Link Speed and Rx Link Speed and Comparing
        both of them
        """
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        upi_width_status = True
        try:
            pci_obj = cscripts_obj.get_cscripts_utils().get_pci_obj()
            self._log.info("Halting the System ...")
            sdp_obj.halt()
            for bus_num in self.PCI_BUS_NUMBER_LIST:
                for dev_num in self.PCI_DEVICE_NUMBER_LIST:
                    pci_config_value = pci_obj.config(bus_num, dev_num, self.PCI_FUNC_NUMBER,
                                                      self.PCI_OFFSET_VALUE)
                    self._log.info(
                        "Pci Config Value of Bus Number '{}' and Device Number '{}' with Function Number '{}' "
                        "and Offset Value '{}' is '{}'".format(hex(bus_num), hex(dev_num),
                                                               hex(self.PCI_FUNC_NUMBER),
                                                               hex(self.PCI_OFFSET_VALUE),
                                                               hex(pci_config_value)))
                    tx_link_width = int(pci_config_value & 0x1F) + 1
                    self._log.info("Tx link Width Value for Bus Number '{}' and Device Number '{}' with"
                                   " Function Number '{}' and Offset Value '{}' is '{}'".
                                   format(hex(bus_num), hex(dev_num), hex(self.PCI_FUNC_NUMBER),
                                          hex(self.PCI_OFFSET_VALUE), tx_link_width))
                    rx_link_width = int(pci_config_value >> 5 & 0x1F) + 1
                    self._log.info("Rx link Width Value for Bus Number '{}' and Device Number '{}' with"
                                   " Function Number '{}' and Offset Value '{}' is '{}'".
                                   format(hex(bus_num), hex(dev_num), hex(self.PCI_FUNC_NUMBER),
                                          hex(self.PCI_OFFSET_VALUE), rx_link_width))
                    if tx_link_width == rx_link_width:
                        self._log.info(
                            "Tx Link Width is Equal to Rx Link Width for Bus Number '{}' and Device Number '{}' "
                            "with Function Number '{}' and Offset Value '{}'".format(hex(bus_num), hex(dev_num),
                                                                                     hex(self.PCI_FUNC_NUMBER),
                                                                                     hex(self.PCI_OFFSET_VALUE)))
                    else:
                        log_error = "Tx Link Width is Not Equal to Rx Link Width"
                        upi_width_status = False
                        self._log.error(log_error)
                        raise RuntimeError(log_error)
        except Exception as ex:
            raise ex
        finally:
            sdp_obj.go()
        return upi_width_status
