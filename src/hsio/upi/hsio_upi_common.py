import os
import re
import time
import random
from enum import Enum
from datetime import datetime
from imp import importlib
from ast import literal_eval

from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.exceptions import OsCommandException

from src.lib.content_base_test_case import ContentBaseTestCase
from dtaf_core.lib.dtaf_constants import ProductFamilies
from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions
from src.lib.content_configuration import ContentConfiguration
from src.lib.common_content_lib import CommonContentLib
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.bios_util import ChooseBoot
from src.hsio.upi.upi_telemetry import UpiTelemetry
from src.lib.bios_util import BiosUtil
from src.lib.dtaf_content_constants import TimeConstants


class UpiChecks:
    def __init__(self):
        self.LANE = "lane"
        self.TOPOLOGY = "topology"
        self.RX_STATE = "rx_state"
        self.TX_STATE = "tx_state"
        self.MAX_LINK_SPEED = "max_link_speed"
        self.MIN_LINK_SPEED = "min_link_speed"
        self.MIXED_LINK_SPEED = "mixed_link_speed"

        self.COLD_RESET = "COLD"
        self.WARM_RESET = "WARM"


class UpiModules:
    MOD_UPI_STATUS = ".upiStatus"
    MOD_UPI_UTILS = ".upiUtils"


class HsioUpiCommon(ContentBaseTestCase):

    REG_PROVIDER_CSCRIPTS = "CscriptsSiliconRegProvider"
    REG_PROVIDER_PYTHONSV = "PythonsvSiliconRegProvider"

    PKG_UPI_CSCRIPTS = {ProductFamilies.ICX: "commlibs.qpi.xnmupi",
                        ProductFamilies.SPR: "commlibs.qpi.xnmupi",
                        ProductFamilies.EMR: "commlibs.qpi.xnmupi",
                        ProductFamilies.GNR: "platforms.GNR.gnrupi"}

    UPI_MOD_DEFS = {ProductFamilies.SPR: "platforms.SPR.sprupidefs",
                    ProductFamilies.GNR: "platforms.GNR.gnrupidefs",
                    ProductFamilies.ICX: "platforms.ICX.icxupidefs"
                    }

    PKG_UPI_PYSV = {ProductFamilies.ICX: "icelakex.upi",
                    ProductFamilies.SPR: "sapphirerapids.upi"}

    PLATFROM_WITH_IO_DIE = [ProductFamilies.GNR]

    UPI_SPEED_SETTING_REG_PATH_DICT = {ProductFamilies.ICX: "uncore.upi.ktimisc{port}.ktimiscstat.kti_rate",
                                       ProductFamilies.SPR: "uncore.upi.upi{port}.pipe_clk_rate_ctrl.cri_freq_select",
                                       ProductFamilies.EMR: "uncore.upi.upi{port}.pipe_clk_rate_ctrl.cri_freq_select",
                                       ProductFamilies.GNR: "io{io_die}.uncore.upi.upi{port}.upi_regs.pipe_clk_rate_ctrl.link_rate"}

    UPI_LANES_STATUS_REG_PATH_DICT = {ProductFamilies.ICX: "uncore.upi.upi{port}.ktireut_ph_css.s_clm",
                                      ProductFamilies.SPR: "uncore.upi.upi{port}.ktireut_ph_css.s_clm",
                                      ProductFamilies.EMR: "uncore.upi.upi{port}.ktireut_ph_css.s_clm",
                                      ProductFamilies.GNR: "io{io_die}.uncore.upi.upi{port}.upi_regs.ktireut_ph_css.s_clm"}

    UPI_PORTS_RX_STATUS_REG_PATH_DICT = {ProductFamilies.ICX: "uncore.upi.upi{port}.ktireut_ph_css.s_rx_state",
                                         ProductFamilies.SPR: "uncore.upi.upi{port}.ktireut_ph_css.s_rx_state",
                                         ProductFamilies.EMR: "uncore.upi.upi{port}.ktireut_ph_css.s_rx_state",
                                         ProductFamilies.GNR: "io{io_die}.uncore.upi.upi{port}.upi_regs.ktireut_ph_css.s_rx_state"}

    UPI_PORTS_TX_STATUS_REG_PATH_DICT = {ProductFamilies.ICX: "uncore.upi.upi{port}.ktireut_ph_css.s_tx_state",
                                         ProductFamilies.SPR: "uncore.upi.upi{port}.ktireut_ph_css.s_tx_state",
                                         ProductFamilies.EMR: "uncore.upi.upi{port}.ktireut_ph_css.s_tx_state",
                                         ProductFamilies.GNR: "io{io_die}.uncore.upi.upi{port}.upi_regs.ktireut_ph_css.s_tx_state"}

    ERR_REGISTERS_PARENT_PATH = {ProductFamilies.ICX: "uncore.upi.upi{port}.",
                                 ProductFamilies.SPR: "uncore.upi.upi{port}.",
                                 ProductFamilies.EMR: "uncore.upi.upi{port}.",
                                 ProductFamilies.GNR: "io{io_die}.uncore.upi.upi{port}.upi_regs."}

    ERR_REGISTER_LIST = ['ktierrcnt0_cntr', 'ktierrcnt1_cntr', 'ktierrcnt2_cntr',
                         'kticrcerrcnt', 'ktiviral', 'bios_kti_err_st']

    ERR_MASK_LIST = ['ktierrcnt0_mask', 'ktierrcnt1_mask', 'ktierrcnt2_mask']

    SPEED_MAX = {ProductFamilies.ICX: 0x6,
                 ProductFamilies.SPR: 0x3,
                 ProductFamilies.EMR: 0x9,
                 ProductFamilies.GNR: 0x9}

    SPEED_MIN = {ProductFamilies.ICX: 0x4,
                 ProductFamilies.SPR: 0x1,
                 ProductFamilies.EMR: 0x2,
                 ProductFamilies.GNR: 0x3}

    SPEED_PRESET_ICX = {"S0P0": 0x6,
                        "S0P1": 0x5,
                        "S0P2": 0x4,
                        "S0P3": 0x6,
                        "S1P0": 0x6,
                        "S1P1": 0x5,
                        "S1P2": 0x4,
                        "S1P3": 0x6,
                        "S2P0": 0x6,
                        "S2P1": 0x5,
                        "S2P2": 0x4,
                        "S2P3": 0x6,
                        "S3P0": 0x6,
                        "S3P1": 0x5,
                        "S3P2": 0x4,
                        "S3P3": 0x6}

    SPEED_PRESET_SPR = {"S0P0": 0x3, "S0P1": 0x2, "S0P2": 0x1, "S0P3": 0x3,
                        "S1P0": 0x3, "S1P1": 0x2, "S1P2": 0x1, "S1P3": 0x3,
                        "S2P0": 0x3, "S2P1": 0x2, "S2P2": 0x1, "S2P3": 0x3,
                        "S3P0": 0x3, "S3P1": 0x2, "S3P2": 0x1, "S3P3": 0x3,
                        "S4P0": 0x3, "S4P1": 0x2, "S4P2": 0x1, "S4P3": 0x3,
                        "S5P0": 0x3, "S5P1": 0x2, "S5P2": 0x1, "S5P3": 0x3,
                        "S6P0": 0x3, "S6P1": 0x2, "S6P2": 0x1, "S6P3": 0x3,
                        "S7P0": 0x3, "S7P1": 0x2, "S7P2": 0x1, "S7P3": 0x3}

    SPEED_PRESET_EMR = {"S0P0": 0x4, "S0P1": 0x3, "S0P2": 0x2, "S0P3": 0x9,
                        "S1P0": 0x4, "S1P1": 0x3, "S1P2": 0x2, "S1P3": 0x9,
                        "S2P0": 0x4, "S2P1": 0x3, "S2P2": 0x2, "S2P3": 0x9,
                        "S3P0": 0x4, "S3P1": 0x3, "S3P2": 0x2, "S3P3": 0x9,
                        "S4P0": 0x4, "S4P1": 0x3, "S4P2": 0x2, "S4P3": 0x9,
                        "S5P0": 0x4, "S5P1": 0x3, "S5P2": 0x2, "S5P3": 0x9,
                        "S6P0": 0x4, "S6P1": 0x3, "S6P2": 0x2, "S6P3": 0x9,
                        "S7P0": 0x4, "S7P1": 0x3, "S7P2": 0x2, "S7P3": 0x9}

    SPEED_PRESET_GNR = {"S0P0": 0x9, "S0P1": 0x8, "S0P2": 0x3,
                        "S0P3": 0x9, "S0P4": 0x8, "S0P5": 0x3,
                        "S1P0": 0x9, "S1P1": 0x8, "S1P2": 0x3,
                        "S1P3": 0x9, "S1P4": 0x8, "S1P5": 0x3,
                        "S2P0": 0x9, "S2P1": 0x8, "S2P2": 0x3,
                        "S2P3": 0x9, "S2P4": 0x8, "S2P5": 0x3,
                        "S3P0": 0x9, "S3P1": 0x8, "S3P2": 0x3,
                        "S3P3": 0x9, "S3P4": 0x8, "S3P5": 0x3,
                        "S4P0": 0x9, "S4P1": 0x8, "S4P2": 0x3,
                        "S4P3": 0x9, "S4P4": 0x8, "S4P5": 0x3,
                        "S5P0": 0x9, "S5P1": 0x8, "S5P2": 0x3,
                        "S5P3": 0x9, "S5P4": 0x8, "S5P5": 0x3,
                        "S6P0": 0x9, "S6P1": 0x8, "S6P2": 0x3,
                        "S6P3": 0x9, "S6P4": 0x8, "S6P5": 0x3,
                        "S7P0": 0x9, "S7P1": 0x8, "S7P2": 0x3,
                        "S7P3": 0x9, "S7P4": 0x8, "S7P5": 0x3}

    SPEED_PRESET_DICT = {ProductFamilies.ICX: SPEED_PRESET_ICX,
                         ProductFamilies.SPR: SPEED_PRESET_SPR,
                         ProductFamilies.EMR: SPEED_PRESET_EMR,
                         ProductFamilies.GNR: SPEED_PRESET_GNR}

    LINK_RATES = {
        ProductFamilies.ICX: {
            3: "4.8",
            4: "9.6",
            5: "10.4",
            6: "11.2"},
        ProductFamilies.SPR: {
            0: "2.5",
            1: "12.8",
            2: "14.4",
            3: "16.0"},
        ProductFamilies.EMR: {
            1: "2.5",
            2: "12.8",
            3: "14.4",
            4: "16.0",
            9: "20.0"},
        ProductFamilies.GNR: {
            0: "2.5",
            1: "12.8",
            2: "14.4",
            3: "16.0",
            4: "32.0",
            8: "20.0",
            9: "24.0"}
    }

    SPR_MIN_LINK_SPEED = "12.8"

    STREAM_TARGET_BW_DICT = {ProductFamilies.SPR: "(8 * {} * 8) * 67 / 100"}

    UPI_NUMA_NODES = "lscpu | grep NUMA"
    MLC_PROCESS_CMD = "ps -ef | grep mlc"
    SPEC_PROCESS_CMD = "ps -ef | grep run_spec"
    BASIC_PNP_PROCESS_CMD = "ps -ef | grep basic_pnp_setup"
    STREAM_PROCESS_CMD = "pgrep run_stream.sh"
    CSCRIPTS_FILE_NAME = "cscripts_log_file.log"
    _REGEX_CMD_FOR_LINK_SPEED = r".*Link\sSpeed.*"
    CHECK_INTERVAL_SEC = 300
    TWO_HOURS_TIMER = 7200
    CMD_RE_CHECK_WAIT_TIME_SEC = 20
    STRESSAPP_START_DELAY_SEC = 120
    STRESSAPP_ARGS = " -s 9000 --cc_test"
    RUN_SPEC_FILE = "./run_spec.sh"
    BASIC_PNP_SETUP_FILE = "./basic_pnp_setup.sh"
    C6_STATE_TEST_RUNTIME_SEC = 1800
    PACKAGE_C6_STATE_DELAY_SEC = 60
    LOAD_AVG_1_MIN_THRESHOLD_IDLE = 8
    LOAD_AVG_1_MIN_THRESHOLD_UNDER_STRESS = 50
    RX_TX_C6_STATES = [0xf, 0xa, 0x5, 0x6, 0x8, 0x9, 0xc, 0xd, 0xe]
    L0_states = [0xf, 0xe, 0xc, 0xd]
    KTI_REGISTERS_NO_ERROR_VALUE = 0x0
    KTI_REMOTE_VIRAL_LPBK_EN = 0x10

    MESH_TEST_CACHE_STRESS = "cache_stress_ss_mlc"
    MESH_TEST_LOCK_NORANDOM = "lock_ss_mlc_noramdom"
    MESH_TEST_SPECIAL_CYCLES = "special_cycles_ss_mlc"
    MESH_TEST_LOCK = "lock_ss_mlc"
    MESH_TEST_RANDOM = "random_ss_mlc"
    MESH_START_DELAY_SEC = 120
    MESH_RUN_TIME_MIN = 999
    NUMACTL_ROUTE_COST_2_HOPS = 31

    TOPOLOGY_CONFIG_PATH = 'suts/sut/silicon/upi_topology/socket_port_pair'
    SOCKETS_LIST_AFTER_DEGRADATION = None
    MLC_STARTUP_BASE_COMMAND = "/mlc --loaded_latency -d0 -T -K1 -t"
    MLC_RUN_FILE = r'C:\Automation\Tools\mlc_run_file.txt'
    # additional time added to mlc app to ensure app does not stop before 2 hr timer expires
    MLC_STARTUP_ADD_SEC = 300
    UPI_TOPOLOGY_LOG_FILE = "upi_topology.txt"
    MLC_STRESS_CMD = "./mlc_internal"
    CHECK_STRESS_RETRY_CNT = 3

    def __init__(self, test_log, arguments, cfg_opts, config=None):
        """
        Creates a new HsioUpiCommon object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        if config:
            config = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), config)
        super(HsioUpiCommon, self).__init__(test_log, arguments, cfg_opts, config)
        self._cfg = cfg_opts
        self.bios_dir_path = os.path.dirname(os.path.abspath(__file__))
        self.sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self.os = ProviderFactory.create(self.sut_os_cfg, test_log)  # type: SutOsProvider
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._content_config_obj = ContentConfiguration(self._log)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self._stress_provider_obj = StressAppTestProvider.factory(self._log, cfg_opts, self.os)
        self._upi_checks = UpiChecks()
        self._upi_checks_12Hr_list = [self.lanes_operational_check,
                                      self.verify_rx_ports_l0_state,
                                      self.verify_tx_ports_l0_state]
        self._upi_tests_dict = {self._upi_checks.LANE: self.lanes_operational_check,
                                self._upi_checks.MAX_LINK_SPEED: self.verify_max_link_speed_set,
                                self._upi_checks.MIN_LINK_SPEED: self.verify_min_link_speed_set,
                                self._upi_checks.MIXED_LINK_SPEED: self.verify_link_speed_mixed,
                                self._upi_checks.RX_STATE: self.verify_rx_ports_l0_state,
                                self._upi_checks.TOPOLOGY: self.print_upi_topology,
                                self._upi_checks.TX_STATE: self.verify_tx_ports_l0_state}

        self.reg_provider_obj = ProviderFactory.create(self.sil_cfg, self._log)
        self.sdp = ProviderFactory.create(self.sdp_cfg, self._log)
        self.reg_provider_class = type(self.reg_provider_obj).__name__
        if self.reg_provider_obj.silicon_cpu_family == ProductFamilies.GNR:
            self.sdp.go()  # workaround for HSD https://hsdes.intel.com/appstore/article/#/14015937375
            # update the bios file path for gnr if this is a min/max linkspeed test
            if config and config.find("linkspeed") != -1 and config.find("mixed") == -1:
                index = config.find(".cfg")
                config = config[:index] + "_gnr" + config[index:]
                self.bios_config_file_path = config
                self.bios_util.bios_config_file = config
        self.upi_module_paths = self.UPI_MOD_DEFS
        self.upi_telemetry = UpiTelemetry(self._log, self.os, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        super(HsioUpiCommon, self).prepare()
        self.upi_telemetry.collect_upi_telemetry_to_csv(self.__class__.__name__, 0)

    def cleanup(self, return_status):
        """
        Clean up the test.
        Need to reset the bios for degradation tests that have sockets disconnected.
        """
        if self.SOCKETS_LIST_AFTER_DEGRADATION is not None:
            self.bios_util.load_bios_defaults()
            self.perform_graceful_g3()
        super(HsioUpiCommon, self).cleanup(return_status)
        self.upi_telemetry.collect_upi_telemetry_to_csv(self.__class__.__name__, 1)

    def import_upi_module(self, upi_module):
        """
        Import upi module from cscripts/pythonsv libs.

        :param upi_module: name of upi modules defined in UpiModules class to import.
        :return: The module imported.
        """
        if self.reg_provider_class == self.REG_PROVIDER_CSCRIPTS:
            module_path = self.PKG_UPI_CSCRIPTS[self.reg_provider_obj.silicon_cpu_family]
        elif self.reg_provider_class == self.REG_PROVIDER_PYTHONSV:
            module_path = self.PKG_UPI_PYSV[self.reg_provider_obj.silicon_cpu_family]
        else:
            raise RuntimeError("reg provider can only be cscripts or pythonsv!")

        imported_module = importlib.import_module(upi_module, module_path)
        return imported_module

    def start_stressapp(self, stressapp_log, args=STRESSAPP_ARGS):
        """
        Start stressapp workload.

        :param args: The flags to run the stressapp test.
        :return:
        """
        try:
            stressapp_exe_name = "./stressapptest"

            cmd_result = self.os.execute(stressapp_exe_name + " --help", self._command_timeout)
            if cmd_result.return_code != 0:
                self._log.info("Verified Stressapp is NOT installed.")
                log_err = "Stressapp not installed"
                self._log.error(log_err)
                raise log_err

            self._log.info("Starting stressapp test..")
            stressapp_cmd = stressapp_exe_name + args + " -l " + stressapp_log
            self._log.info(stressapp_cmd)
            if self._common_content_configuration.is_container_env():
                self.os.execute_async(stressapp_cmd)
            else:
                self._stress_provider_obj.execute_async_stress_tool(stressapp_cmd, "stressapptest")

        except Exception as ex:
            log_err = "An Exception Occurred while starting stressapp test : {}".format(ex)
            self._log.error(log_err)
            raise OsCommandException(log_err)

    def stop_stressapp(self):
        """
        Stop the Stressapp test.

        :return:
        """
        self._log.info("Stopping Stressapp test..")
        self.os.execute("pkill stressapptest", self._command_timeout)

    def setup_stressapp_and_run(self):
        """
        This method does the following:
        1.Install stressapp on SUT.
        2.Start the stressapp.
        3.Check if the log is created successfully.

        :return: True if the log is created successfully, False otherwise.
        """
        if not self._common_content_configuration.is_container_env():
            self._install_collateral.install_stress_test_app()
        time_stamp = datetime.now().strftime("-%Y-%m-%d-%H-%M-%S")
        stressapp_log = "Stressapp{}.log".format(time_stamp)
        self.start_stressapp(stressapp_log=stressapp_log)
        self._log.info("Pausing {} secs to allow stressapp startup to stabilize".format(str(self.STRESSAPP_START_DELAY_SEC)))
        time.sleep(self.STRESSAPP_START_DELAY_SEC)
        if not self.os.check_if_path_exists(stressapp_log):
            self._log.info("Stressapp log not captured!")
            self.stop_stressapp()
            return False

        return True

    def get_cpu_loadavg(self, wait_to_stabilize=False):
        """
        get stats from /proc/loadavg.

        :param wait_to_stabilize: (bool) if true, adds additional time delay for load to stabilize
        :return: a list that contains all the stats present in /proc/loadavg.
        """
        if wait_to_stabilize:
            self._log.info("Pausing {} secs to allow stress load to stabilize".format(str(self.STRESSAPP_START_DELAY_SEC)))
            time.sleep(self.STRESSAPP_START_DELAY_SEC)
        self._log.info("Pausing {} secs before getting load average".format(str(self.STRESSAPP_START_DELAY_SEC)))
        time.sleep(self.STRESSAPP_START_DELAY_SEC)

        return self.os.execute("cat /proc/loadavg", self._command_timeout).stdout.split()

    def verify_max_link_speed_set(self):
        """
        Verifies that the link speed have been set to max for all upi ports.

        :return: True if speed set correctly. False otherwise.
        """

        self._log.info("Scanning speed settings...")

        register_path = self.UPI_SPEED_SETTING_REG_PATH_DICT[self.reg_provider_obj.silicon_cpu_family]
        target = self.SPEED_MAX[self.reg_provider_obj.silicon_cpu_family]
        max_link_speed_set_successfully = self.verify_reg_value_as_expected_on_all_upi_ports(register_path, target)

        if max_link_speed_set_successfully:
            self._log.info("Scan finished, all ports speed set to max.")
        else:
            self._log.info("Scan finished, some port speeds not set to max. Details listed above.")
        return max_link_speed_set_successfully

    def verify_min_link_speed_set(self):
        """
        Verifies that the link speed have been set to minimum for all upi ports.

        :return: True if speed set correctly. False otherwise.
        """

        self._log.info("Scanning speed settings...")

        register_path = self.UPI_SPEED_SETTING_REG_PATH_DICT[self.reg_provider_obj.silicon_cpu_family]
        target = self.SPEED_MIN[self.reg_provider_obj.silicon_cpu_family]
        min_link_speed_set_successfully = self.verify_reg_value_as_expected_on_all_upi_ports(register_path, target)

        if min_link_speed_set_successfully:
            self._log.info("Scan finished, all ports speed set to minimum.")
        else:
            self._log.info("Scan finished, some port speeds not set to minimum. Details listed above.")
        return min_link_speed_set_successfully

    def verify_no_upi_errors_indicated(self):
        """
        Scans all the registers listed in ERR_REGISTER_LIST for all sockets and upi ports.

        :return: True if no error detected. False otherwise.
        """

        num_of_registers_total = len(self.ERR_REGISTER_LIST)
        num_of_registers_passed = 0
        self._log.info("Scanning registers for errors")
        for register in self.ERR_REGISTER_LIST:
            target = [self.KTI_REGISTERS_NO_ERROR_VALUE]
            if register == 'ktiviral':
                target.append(self.KTI_REMOTE_VIRAL_LPBK_EN)
            register_path = self.ERR_REGISTERS_PARENT_PATH[self.reg_provider_obj.silicon_cpu_family] + register
            reg_value_as_expected_on_all_upi_ports = self.verify_reg_value_as_expected_on_all_upi_ports(register_path,
                                                                                                        target=target)
            if reg_value_as_expected_on_all_upi_ports:
                num_of_registers_passed += 1

        all_registers_passed = (num_of_registers_total == num_of_registers_passed)
        if all_registers_passed:
            self._log.info("Scan finished, no errors detected.")
        else:
            self._log.info("Scan finished, errors detected. Details listed above.")
        return all_registers_passed

    def lanes_operational_check(self, package_c6_test=False):
        """
        Verifies that all lanes operational.
        :param  package_c6_test:  if package C6 testing - set to True
        :return: True if all lanes operational. False otherwise.
        """
        if package_c6_test:
            lanemap_code_list = [0x7, 0x1]
            self._log.info("Verifying expected lane map code in PC6 environment")
        else:
            lanemap_code_list = 0x7
        self._log.info("Scanning lanes")

        register_path = self.UPI_LANES_STATUS_REG_PATH_DICT[self.reg_provider_obj.silicon_cpu_family]
        all_lanes_operational_on_all_upi_ports = self.verify_reg_value_as_expected_on_all_upi_ports(register_path,
                                                                                                    target=lanemap_code_list)

        if all_lanes_operational_on_all_upi_ports:
            self._log.info("Scan finished, all lanes operational.")
        else:
            self._log.info("Scan finished, some lanes not operational. Details listed above.")
        return all_lanes_operational_on_all_upi_ports

    def verify_rx_ports_l0_state(self):
        """
        Verify rcv ports are in L0 state(L0_states = [0xf, 0xe, 0xc, 0xd]

        :return: True if rcv ports are in L0 state. False otherwise.
        """

        self._log.info("Scanning ports")

        register_path = self.UPI_PORTS_RX_STATUS_REG_PATH_DICT[self.reg_provider_obj.silicon_cpu_family]
        all_rx_ports_in_l0_state = self.verify_reg_value_as_expected_on_all_upi_ports(register_path, target=self.L0_states)

        if all_rx_ports_in_l0_state:
            self._log.info("Scan finished, all ports are in correct rx state.")
        else:
            self._log.info("Scan finished, some ports not in correct rx state. Details listed above.")
        return all_rx_ports_in_l0_state

    def verify_tx_ports_l0_state(self):
        """
        Verify trx ports are in L0 state(data=0xf)

        :return: True if trx ports are in L0 state. False otherwise.
        """

        self._log.info("Scanning ports")

        register_path = self.UPI_PORTS_TX_STATUS_REG_PATH_DICT[self.reg_provider_obj.silicon_cpu_family]
        all_tx_ports_in_l0_state = self.verify_reg_value_as_expected_on_all_upi_ports(register_path, target=self.L0_states)

        if all_tx_ports_in_l0_state:
            self._log.info("Scan finished, all ports are in correct tx state.")
        else:
            self._log.info("Scan finished, some ports not in correct tx state. Details listed above.")
        return all_tx_ports_in_l0_state

    def verify_rx_ports_c6_state(self):
        """
        Verify rcv ports are in various states during c6
        after an L1(0xa) exit, the UPI link will go back to TxDetect state (0x5), then through Polling (0x6),
        Config (0x8 / 0x9), and L0 (0xf).

        :return: True if rcv ports are in any of above states. False otherwise.
        """

        self._log.info("Scanning ports")

        register_path = self.UPI_PORTS_RX_STATUS_REG_PATH_DICT[self.reg_provider_obj.silicon_cpu_family]
        all_rx_ports_in_c6_state = self.verify_reg_value_as_expected_on_all_upi_ports(register_path,
                                                                                      target=self.RX_TX_C6_STATES)

        if all_rx_ports_in_c6_state:
            self._log.info("Scan finished, all ports are in correct rx states.")
        else:
            self._log.info("Scan finished, some ports not in correct rx state. Details listed above.")
        return all_rx_ports_in_c6_state

    def verify_tx_ports_c6_state(self):
        """
        Verify trx ports are in various states during c6
        after an L1(0xa) exit, the UPI link will go back to TxDetect state (0x5), then through Polling (0x6),
        Config (0x8 / 0x9), and L0 (0xf).

        :return: True if trx ports are in any of above states. False otherwise.
        """

        self._log.info("Scanning ports")

        register_path = self.UPI_PORTS_TX_STATUS_REG_PATH_DICT[self.reg_provider_obj.silicon_cpu_family]
        all_tx_ports_in_c6_state = self.verify_reg_value_as_expected_on_all_upi_ports(register_path,
                                                                                      target=self.RX_TX_C6_STATES)

        if all_tx_ports_in_c6_state:
            self._log.info("Scan finished, all ports are in correct tx states.")
        else:
            self._log.info("Scan finished, some ports not in correct tx state. Details listed above.")
        return all_tx_ports_in_c6_state

    def verify_reg_value_as_expected_on_all_upi_ports(self, register_path, target):
        """
        Generic method that checks if the value in the registers match the target
        for all upi ports across all sockets.

        :param register_path: the path that leads the registers.
        :param target: list or int -check if the value in the registers match the target.
        :return: True if all registers pass the verification. False otherwise.
        """
        if not isinstance(target, list):
            target = [target]

        utils = self.import_upi_module(UpiModules.MOD_UPI_UTILS)

        all_reg_values_as_expected = True
        socket_list = self.SOCKETS_LIST_AFTER_DEGRADATION
        port_info_dict = {'port': 's',
                          'io_die': 's'}
        if socket_list is None:
            data = self.reg_provider_obj.get_by_path(self.reg_provider_obj.SOCKETS, register_path.format(**port_info_dict))
            if register_path in [self.UPI_LANES_STATUS_REG_PATH_DICT[self.reg_provider_obj.silicon_cpu_family],
                                 self.UPI_PORTS_RX_STATUS_REG_PATH_DICT[self.reg_provider_obj.silicon_cpu_family],
                                 self.UPI_PORTS_TX_STATUS_REG_PATH_DICT[self.reg_provider_obj.silicon_cpu_family]]:
                self._log.info("sv.sockets.{} - {}:".format(register_path, data))

        sockets = self.reg_provider_obj.get_sockets()
        for skt in sockets:
            skt_num = skt.target_info["socketNum"]
            if socket_list is not None and skt_num not in socket_list:
                continue
            # Filter out inactive ports.
            ports = [x[1] for x in utils.removeDanglingKtiEndpoints(utils.getKtiDevices(skt))]
            for port in ports:
                port_info_dict['io_die'] = self.get_io_die_for_upi_port(port)
                port_info_dict['port'] = port
                data = self.reg_provider_obj.get_by_path(self.reg_provider_obj.SOCKET, register_path.format(**port_info_dict),
                                                         skt_num)
                self._log.info("sv.socket{}.{} - {}".format(skt_num, register_path.format(**port_info_dict), data))

                if data in target:
                    continue
                else:
                    self._log.info("Mismatch detected in {}:".format(data.path))
                    self._log.info("Value detected was {}".format(data))
                    self._log.info("Value should be one of the following")
                    hex_states = []
                    for state in target:
                        hex_states.append(hex(state))
                    self._log.info(hex_states)
                    all_reg_values_as_expected = False

        return all_reg_values_as_expected

    def verify_upi_topology(self):
        """
        Verify if topology is the same as present in the config file.

        :return: True if the topologies are the same, or no topology found in config file.
        False otherwise.
        """

        topology_verified = True
        connection_dict = {}
        pairs = self._cfg.findall(self.TOPOLOGY_CONFIG_PATH)
        if not pairs:
            self._log.info("No topology found in system config file, verification skipped.")
            return True

        try:
            for pair in pairs:
                ports = literal_eval(pair.text)
                connection_dict[ports[0]] = ports[1]
                connection_dict[ports[1]] = ports[0]

            utils = self.import_upi_module(UpiModules.MOD_UPI_UTILS)

            sockets = self.reg_provider_obj.get_sockets()
            for skt in sockets:
                skt_num = skt.target_info["socketNum"]
                ports = [x[1] for x in utils.removeDanglingKtiEndpoints(utils.getKtiDevices(skt))]
                for port in ports:
                    (peer_skt_num, peer_port) = utils.getPeerDevice(skt_num, port, sktObj=False)

                    if (skt_num, port) not in connection_dict.keys():
                        self._log.info("Topology mismatch detected for port S{}P{}:".format(int(skt_num), int(port)))
                        self._log.info("This port should be inactive but is connected to S{}P{}".format(int(peer_skt_num),
                                                                                                        int(peer_port)))
                        topology_verified = False
                        continue

                    connection_expected = connection_dict[(skt_num, port)]
                    if connection_expected != (peer_skt_num, peer_port):
                        self._log.info("Topology mismatch detected for port S{}P{}:".format(int(skt_num), int(port)))
                        self._log.info("Peer port should be S{}P{} but detected S{}P{}".format(connection_expected[0],
                                                                                               connection_expected[1],
                                                                                               int(peer_skt_num),
                                                                                               int(peer_port)))
                        topology_verified = False
            if topology_verified:
                self._log.info("Scan finished, upi topology verified.")
            else:
                self._log.info("Scan finished, upi topology verification failed. Details listed above.")
            return topology_verified

        except Exception as ex:
            raise ex

    def print_upi_topology(self):
        """
        Print upi topology

        :return: True. This is needed for upper level methods.
        """

        u = self.import_upi_module(UpiModules.MOD_UPI_STATUS)
        self._log.info("Printing UPI topology...")
        u.printTopology()
        return True

    def print_link(self):
        """
        Print Upi Link
        """
        upi_link = self.import_upi_module(UpiModules.MOD_UPI_STATUS)
        self._log.info("Printing UPI info...")
        upi_link.printLink()

    def print_upi_info(self):
        """
        Print upi info
        """

        u = self.import_upi_module(UpiModules.MOD_UPI_STATUS)
        self._log.info("Printing UPI info...")
        u.printInfo()

    def print_upi_link_speed(self):
        """
        Print upi link speed.
        """

        u = self.import_upi_module(UpiModules.MOD_UPI_STATUS)
        self._log.info("Printing UPI link speed...")
        u.printLinkSpeed()

    def print_upi_errors(self):
        """
        Print upi errors
        """
        u = self.import_upi_module(UpiModules.MOD_UPI_STATUS)
        self._log.info("Printing UPI errors...")
        u.printErrors()

    def get_io_die_for_upi_port(self, port):
        """
        Get the number of IO die for a given port.

        :param port: the port number.
        """
        if self.reg_provider_obj.silicon_cpu_family not in self.PLATFROM_WITH_IO_DIE:
            return None

        u = self.import_upi_module(UpiModules.MOD_UPI_UTILS)
        io_die = u.getIOdie(port)

        return io_die

    def get_link_speed_single_port(self, socket=0, port=0):
        """
        Get link speed for a single upi port.

        :param socket: socket number.
        :param port: port number.
        :return: The link speed for the upi port.
        """
        register_path = self.UPI_SPEED_SETTING_REG_PATH_DICT[self.reg_provider_obj.silicon_cpu_family]
        port_info_dict = {}
        port_info_dict['io_die'] = self.get_io_die_for_upi_port(port)
        port_info_dict['port'] = port
        return self.reg_provider_obj.get_by_path(self.reg_provider_obj.SOCKET, register_path.format(**port_info_dict), socket)

    def verify_link_speed_mixed(self):
        """
        For all upi ports, compare the preset link speed of the port and its partner port on another socket.
        Get the minimum of the two preset values and check if it matches the actual link speed.

        """

        self._log.info("Scanning speed settings...")
        mixed_link_speed_set_successfully = True
        utils = self.import_upi_module(UpiModules.MOD_UPI_UTILS)

        speed_dict = self.SPEED_PRESET_DICT[self.reg_provider_obj.silicon_cpu_family]

        sockets = self.reg_provider_obj.get_sockets()
        for skt in sockets:
            skt_num = skt.target_info["socketNum"]
            ports = [x[1] for x in utils.removeDanglingKtiEndpoints(utils.getKtiDevices(skt))]
            for port in ports:
                (peer_skt_num, peer_port) = utils.getPeerDevice(skt_num, port, sktObj=False)
                speed_preset = speed_dict["S{}P{}".format(int(skt_num), int(port))]
                peer_speed_preset = speed_dict["S{}P{}".format(int(peer_skt_num), int(peer_port))]

                speed_expected = min(speed_preset, peer_speed_preset)
                speed_actual = self.get_link_speed_single_port(skt_num, port)

                if speed_expected != speed_actual:
                    self._log.info("Link speed mismatch detected in port S{}P{}:".format(int(skt_num), int(port)))
                    self._log.info("Value should be {} but detected {}".format(hex(speed_expected),
                                                                               hex(speed_actual)))
                    mixed_link_speed_set_successfully = False
        if mixed_link_speed_set_successfully:
            self._log.info("Scan finished, all ports speed set correctly.")
        else:
            self._log.info("Scan finished, some port speeds not set correctly. Details listed above.")
        return mixed_link_speed_set_successfully

    def verify_numactl_route_cost(self, expected_numactl_route_cost):
        """
        This method is to check "numactl -H" to see all 4 sockets in the matrix at
        the bottom and the 0<->2 and 1<->3 entries should have a route cost of 31

        :return Boolean - True if equal to 31 else False.
        """
        numactl_regex_dict = {31: [r"0:\s+[0-9]+\s+[0-9]+\s+{}".format(expected_numactl_route_cost),
                                   r"1:\s+[0-9]+\s+[0-9]+\s+[0-9]+\s+{}".format(expected_numactl_route_cost),
                                   r"2:\s+{}\s+[0-9]+\s+[0-9]+\s+[0-9]+".format(expected_numactl_route_cost),
                                   r"3:\s+[0-9]+\s+31+\s+[0-9]+\s+[0-9]+".format(expected_numactl_route_cost)]
                              }
        command_output = self._common_content_lib.execute_sut_cmd("numactl -H", "numactl -H", self._command_timeout)
        self._log.info("numactl -H output- {}".format(command_output))
        ret_value = self._common_content_lib.extract_regex_matches_from_file(command_output,
                                                                             numactl_regex_dict[
                                                                                 expected_numactl_route_cost])
        return ret_value

    def verify_upi_port_connection(self, upi_port_num=2):
        """
        This method is to verify UPI port connection.

        :param upi_port_num - UPI port number
        :return boolean - True if port is available else False.
        """
        utils = self.import_upi_module(UpiModules.MOD_UPI_UTILS)
        sockets = self.reg_provider_obj.get_sockets()
        original_active_ports_dict = {}
        for skt in sockets:
            skt_num = skt.target_info["socketNum"]
            utils.removeDanglingKtiEndpoints(utils.getKtiDevices(skt))
            ports = {socket_port_pair[1] for socket_port_pair in
                     utils.removeDanglingKtiEndpoints(utils.getKtiDevices(skt))}
            self._log.info("Socket- {} and Ports- {}".format(skt_num, ports))
            original_active_ports_dict[skt_num] = ports
            if upi_port_num not in original_active_ports_dict[skt_num]:
                return False
        return True

    def sum_sockets_expected_bandwidth(self, num_of_lanes=24, efficiency=0.67, threshold=0.85):
        """
        Sum up the bandwidth between 2 sockets, if they are connected directly.

        :param num_of_lanes: The number of lanes for each port.
        :param efficiency: 1 port raw upi bandwidth efficiency.
        :param threshold: Sets the threshold for the expectation.
        :return: A dictionary that map a pair of socket numbers to the expected bandwidth
        between them. Note that the first socket number in the pair will always be
        the smaller one.
        """
        utils = self.import_upi_module(UpiModules.MOD_UPI_UTILS)
        bandwidth_dict = {}

        sockets = self.reg_provider_obj.get_sockets()
        for skt in sockets:
            skt_num = skt.target_info["socketNum"]
            ports = [socket_port_pair[1] for socket_port_pair in
                     utils.removeDanglingKtiEndpoints(utils.getKtiDevices(skt))]
            for port in ports:
                peer_skt_num = utils.getPeerDevice(skt_num, port, sktObj=False)[0]
                if peer_skt_num > skt_num:
                    register_value = self.get_link_speed_single_port(skt_num, port)
                    actual_speed = self.LINK_RATES[self.reg_provider_obj.silicon_cpu_family][register_value]
                    # 24(lanes)*0.125(1 Byte/8 bits)*speed(GT/s) ] * 0.67 * 0.85 = 1.7 * speed(GT/s)
                    coefficient = num_of_lanes * 0.125 * efficiency * threshold
                    if (skt_num, peer_skt_num) not in bandwidth_dict.keys():
                        bandwidth_dict[(skt_num, peer_skt_num)] = 0
                    bandwidth_dict[(skt_num, peer_skt_num)] += coefficient * float(actual_speed)
        for socket_pair in bandwidth_dict.keys():
            self._log.info("The bandwidth between sockets {} is expected to be {} GB/s".format(socket_pair,
                                                                                               bandwidth_dict[socket_pair]))
        return bandwidth_dict

    def check_bandwidth_with_mlc(self, bandwidth_expected_dict):
        """
        Check if mlc bandwidth matrix meets the expectation.

        :param bandwidth_expected_dict: A dictionary that map a pair of socket numbers to the bandwidth
        between them. Note that the first socket number in the pair will always be
        the smaller one.
        :return: True if expectations are met. False otherwise.
        """
        sut_mlc_install_path = self._install_collateral.install_mlc()
        mlc_bw_cmd = sut_mlc_install_path + "/mlc --bandwidth_matrix"
        self._log.info("Starting MLC bandwidth with cmd={}".format(mlc_bw_cmd))
        mlc_bandwidth_results = self.os.execute(mlc_bw_cmd,
                                                self._common_content_configuration.get_command_timeout(), sut_mlc_install_path)
        if mlc_bandwidth_results.return_code != 0:
            self._log.error("mlc bandwidth test not executed properly!")
            return False
        self._log.info(mlc_bandwidth_results.stdout.strip())
        raw_data = mlc_bandwidth_results.stdout.partition('Numa node\t')[2].strip().replace('-', "").split('\t\n')[1:]
        mlc_matrix = [list(map(float, row.strip().split('\t')))[1:] for row in raw_data]

        verification_succeed = True
        for skt_pair in bandwidth_expected_dict.keys():
            try:
                mlc_result = mlc_matrix[skt_pair[0]][skt_pair[1]] / 1000
                expected_value = bandwidth_expected_dict[skt_pair]
                if not mlc_result >= expected_value:
                    verification_succeed = False
                    self._log.info("The actual bandwidth between {} and {} is {} GB/s, but expected {} GB/s"\
                                   .format(skt_pair[0], skt_pair[1], mlc_result, expected_value))
            except IndexError as ex:
                self._log.error("One or more data point(s) missing in bandwidth matrix from mlc...")
                raise ex

        if verification_succeed:
            self._log.info("Verification succeed, all bandwidths meets expectation.")
        else:
            self._log.info("Bandwidth failed to meet expectation, details listed above.")

        return verification_succeed

    def degrade_upi_ports(self, degrade_num=None, socket_port_pairs_list=None, verify_degradation=True):
        """
        Disables ports for degradation tests.
        BIOS xmlcli is used for degradation and requires cold reset.

        :param degrade_num: The number to ports to shut down for each socket.
        Ports will be selected randomly
        :param socket_port_pairs_list: specifiy the ports you want to shut donw.
        e.g. [(0,0),(1,3)] means ports Socket0 Port0 and Socket1 Port3 are to be shut down.
        This param will be ignored if degrade_num is not None.
        :param verify_degradation: Setting this param to False will skip the verification process.
        :return: True if the degradation verified, False otherwise.
        Returns true if verification is skipped as well
        """
        utils = self.import_upi_module(UpiModules.MOD_UPI_UTILS)

        original_active_ports_dict = {}
        ports_down_dict = {}
        bios_knobs = ""
        sockets = self.reg_provider_obj.get_sockets()
        if degrade_num is not None:
            for skt in sockets:
                skt_num = skt.target_info["socketNum"]
                if skt_num not in ports_down_dict.keys():
                    ports_down_dict[skt_num] = set()

                ports = {socket_port_pair[1] for socket_port_pair in
                         utils.removeDanglingKtiEndpoints(utils.getKtiDevices(skt))}
                original_active_ports_dict[skt_num] = ports
                ports_available = [port for port in original_active_ports_dict[skt_num]
                                   if port not in ports_down_dict[skt_num]]
                num_ports_to_shut_down = degrade_num - len(ports_down_dict[skt_num])
                if len(ports_available) >= num_ports_to_shut_down:
                    down_ports = random.sample(ports_available, num_ports_to_shut_down)
                    for port in down_ports:
                        (peer_skt, peer_port) = utils.getPeerDevice(skt_num, port, sktObj=False)
                        if peer_skt not in ports_down_dict.keys():
                            ports_down_dict[peer_skt] = set()
                        ports_down_dict[peer_skt].add(peer_port)
                        ports_down_dict[skt_num].add(port)
                        bios_knobs += "Cpu{}P{}KtiPortDisable=1,".format(skt_num, port)
        elif socket_port_pairs_list is not None:
            for skt in sockets:
                skt_num = skt.target_info["socketNum"]
                ports_down_dict[skt_num] = set()

                ports = {socket_port_pair[1] for socket_port_pair in
                         utils.removeDanglingKtiEndpoints(utils.getKtiDevices(skt))}
                original_active_ports_dict[skt_num] = ports
            for socket_port in socket_port_pairs_list:
                (peer_skt, peer_port) = utils.getPeerDevice(socket_port[0], socket_port[1], sktObj=False)
                ports_down_dict[peer_skt].add(peer_port)
                ports_down_dict[socket_port[0]].add(socket_port[1])
                bios_knobs += "Cpu{}P{}KtiPortDisable=1,".format(socket_port[0], socket_port[1])
        else:
            self._log.warning("Both parameters are None, degradation skipped.")
            return
        self._log.info("Setting bios knobs: {}".format(bios_knobs))
        import pysvtools.xmlcli.XmlCli as cli
        cli.CvProgKnobs(bios_knobs)
        self._log.info("Bios set, performing cold reset...")
        self.perform_graceful_g3()

        if verify_degradation:
            # verification below
            self._log.info("Verifying if degradation occurred...")
            successful_degradation = True
            for skt in sockets:
                skt_num = skt.target_info["socketNum"]
                current_active_ports = {socket_port_pair[1] for socket_port_pair in
                                        utils.removeDanglingKtiEndpoints(utils.getKtiDevices(skt))}
                for port in original_active_ports_dict[skt_num]:
                    port_active = port in current_active_ports
                    port_down_expected = port in ports_down_dict[skt_num]
                    if port_active and port_down_expected:
                        self._log.info("S{}P{} should be down but still active!".format(skt_num, port))
                        successful_degradation = False
                    elif not port_active and not port_down_expected:
                        self._log.info("S{}P{} should be active but is down!".format(skt_num, port))
                        successful_degradation = False
            if successful_degradation:
                self._log.info("Degradation verified.")
            else:
                self._log.error("Verification failed, degradation not occur properly.")
            return successful_degradation

        else:
            self._log.info("Degradation verification skipped")
            return True

    def verify_number_of_sockets_linux(self, num_expected):
        """
        On Linux, verify that the os sees expected number of sockets
        via lscpu.

        :param num_expectecd: The expected number to check against.
        :return: True if the correct number displayed by lscpu. False otherwise.
        """
        num_of_sockets = self.os.execute("lscpu | grep 'Socket(s):' | awk '{print $2}'",
                                         self._command_timeout).stdout.strip()
        self._log.info("The number of socket(s) displayed by lscpu is {}".format(num_of_sockets))
        if int(num_of_sockets) == num_expected:
            self._log.info("Number of socket(s) verification succeeded")
            return True
        else:
            self._log.error("Number of socket(s) did not meet expected number {}".format(num_expected))
            return False

    def run_upi_stressapp_test(self, test, num_cycle=20):
        """
        Run upi stressapp test.

        :param test: specifies the test provided in class UpiChecks.
        :param num_cycle: specifies how many cycles to run.
        :param interval_sec: the time between each polling.
        :return: True if the test is successful, False otherwise.
        """
        idle_loadavg = self.get_cpu_loadavg(wait_to_stabilize=True)
        self._log.info("Idle Load average(1min) is : {}".format(idle_loadavg[0]))
        if float(idle_loadavg[0]) > self.LOAD_AVG_1_MIN_THRESHOLD_IDLE:
            self._log.info("Pausing {} seconds for idle load to stabilize".format(str(self.STRESSAPP_START_DELAY_SEC)))
            time.sleep(self.STRESSAPP_START_DELAY_SEC)
            if float(self.get_cpu_loadavg()[0]) > self.LOAD_AVG_1_MIN_THRESHOLD_IDLE:
                self._log.info("Idle Load average(1min) after wait time is : {}".format(idle_loadavg[0]))
                self._log.error("CPU load average not close to zero enough!")
                return False

        if not self.setup_stressapp_and_run():
            return False

        for i in range(num_cycle):
            self._log.info("Test on cycle {}".format(i + 1))

            loadavg = self.get_cpu_loadavg()
            self._log.info("Load average(1min) is : {}".format(loadavg[0]))
            if float(loadavg[0]) < self.LOAD_AVG_1_MIN_THRESHOLD_UNDER_STRESS:
                self._log.info("CPU load average too low - Pausing for more time to run")
                time.sleep(self.STRESSAPP_START_DELAY_SEC)
                loadavg = self.get_cpu_loadavg(wait_to_stabilize=True)
                self._log.info("Load average(1min) is : {}".format(loadavg[0]))
                if float(loadavg[0]) < self.LOAD_AVG_1_MIN_THRESHOLD_UNDER_STRESS:
                    self._log.info("CPU load average too low - Stopping test")
                    self.stop_stressapp()
                    return False
                self.stop_stressapp()
                return False

            if not self._upi_tests_dict[test]():
                self._log.info("Test failed at cycle {}".format(i + 1))
                self.stop_stressapp()
                return False

            if test == self._upi_checks.TOPOLOGY and not self.verify_upi_topology():
                self._log.info("Test failed at cycle {}".format(i + 1))
                self.stop_stressapp()
                return False

            if not self.verify_no_upi_errors_indicated():
                self._log.info("Test failed at cycle {}".format(i + 1))
                self.stop_stressapp()
                return False

            if i < num_cycle - 1:
                time.sleep(self.CHECK_INTERVAL_SEC)

        self.stop_stressapp()
        return True

    def run_upi_mesh_stress_test(self, test, mesh_test, num_cycle=20):
        """
        Run upi mesh stress test.

        :param test: specifies the test provided in class UpiChecks.
        :param mesh_test: specifies which mesh test to run.
        :param num_cycle: specifies how many cycles to run.
        :param polling_interval_sec: the time between each polling.
        :return: True if the test is successful, False otherwise.
        """
        self._log.info("Checking if mesh tools are installed...")
        mesh_dir = "/root/dm_xprod/dm_xprod-master/"
        mesh_app_path = "mesh_stress/" + mesh_test + "/" + mesh_test + ".pl"

        if not self.os.check_if_path_exists(mesh_dir + mesh_app_path):
            self._log.error("Mesh app not installed properly on SUT!")
            self._install_collateral.install_mesh_stress()

        self.print_upi_topology()

        screen_log = self.os.execute_async(cmd="cd " + mesh_dir + " && source setup.sh && ./" +
                                           mesh_app_path + " -r " + str(self.MESH_RUN_TIME_MIN), log_enable=True)
        time.sleep(self.MESH_START_DELAY_SEC)
        if self.os.execute("pgrep mlc_internal", self._command_timeout).return_code == 1:
            self._log.error("Mesh test not start properly!")
            screen_log_content = self.os.execute("cat {}".format(screen_log), self._command_timeout).stdout
            self._log.debug(screen_log_content)
            return False

        for i in range(num_cycle):
            self._log.info("Test on cycle {}".format(i + 1))
            check_meshstress_retry = self.CHECK_STRESS_RETRY_CNT
            # Check stress is still running
            while check_meshstress_retry > 0:
                check_meshstress_retry -= 1
                if self.os.execute("pgrep mlc_internal", self._command_timeout).return_code == 1:
                    self._log.info("Checking if stress is running failed - retrying")
                    time.sleep(self.CMD_RE_CHECK_WAIT_TIME_SEC)
                else:
                    break
            if check_meshstress_retry == 0:
                self._log.error("platform stress is not running ...  halting the test")
                ps_output = self.os.execute("ps -ef", self._command_timeout).stdout
                self._log.debug(ps_output)
                screen_log_content = self.os.execute("cat {}".format(screen_log), self._command_timeout).stdout
                self._log.debug(screen_log_content)
                demsg_log_content = self.os.execute("dmesg", self._command_timeout).stdout
                self._log.debug(demsg_log_content)
                self.os.kill_async_session()
                return False

            if not self._upi_tests_dict[test]():
                self._log.info("Test failed at cycle {}".format(i + 1))
                self.os.kill_async_session()
                return False

            if test == self._upi_checks.TOPOLOGY and not self.verify_upi_topology():
                self._log.info("Test failed at cycle {}".format(i + 1))
                self.os.kill_async_session()
                return False

            if not self.lanes_operational_check():
                self._log.info("Test failed at cycle {}".format(i + 1))
                self.os.kill_async_session()
                return False

            if not self.verify_tx_ports_l0_state():
                self._log.info("Test failed at cycle {}".format(i + 1))
                self.os.kill_async_session()
                return False

            if not self.verify_rx_ports_l0_state():
                self._log.info("Test failed at cycle {}".format(i + 1))
                self.os.kill_async_session()
                return False

            if not self.verify_no_upi_errors_indicated():
                self._log.info("Test failed at cycle {}".format(i + 1))
                self.os.kill_async_session()
                return False

            if i < num_cycle - 1:
                time.sleep(self.CHECK_INTERVAL_SEC)

        self.print_upi_topology()
        self.os.kill_async_session()
        return True

    def run_upi_cycle_tests(self, test, cycling_method, num_cycles=20, run_time=TimeConstants.TWO_HOUR_IN_SEC):
        """
        Run upi cycling test.

        :param test: specifies the test provided in class UpiChecks.(if 12 Hr test this will be txt value-12Hr_test)
        :param cycling_method: Specifies how the SUT to be cycled, either "COLD" or "WARM"
        :param num_cycles: specifies how many cycles to run.
        :param run_time: run time in seconds
        :return: True if the test is successful, False otherwise.
        """
        start_time = time.perf_counter()
        num_cycle_finished = 0
        for i in range(num_cycles):
            self._log.info("Test on cycle {}".format(i + 1))
            if test == "12Hr_test":
                for run_test in self._upi_checks_12Hr_list:
                    if not run_test():
                        self._log.info("Test failed at cycle {}".format(i + 1))
                        return False
            else:
                if not self._upi_tests_dict[test]():
                    self._log.info("Test failed at cycle {}".format(i + 1))
                    return False

                if test == self._upi_checks.TOPOLOGY and not self.verify_upi_topology():
                    self._log.info("Test failed at cycle {}".format(i + 1))
                    return False

                if not self.verify_no_upi_errors_indicated():
                    self._log.info("Test failed at cycle {}".format(i + 1))
                    return False

            num_cycle_finished += 1
            if i < num_cycles - 1:
                present_time = time.perf_counter()
                if present_time - start_time >= run_time:
                    self._log.info("{} hr timer reached, skipping remaining cycles...".format
                                   (str(run_time/TimeConstants.ONE_HOUR_IN_SEC)))
                    break
                try:
                    if cycling_method == self._upi_checks.WARM_RESET:
                        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
                    elif cycling_method == self._upi_checks.COLD_RESET:
                        self.perform_graceful_g3()
                    else:
                        self._log.error("Cycling method can only be 'WARM' or 'COLD'!")
                        return False
                except Exception as ex:
                    self.print_upi_errors()
                    self.print_upi_info()
                    self.print_upi_link_speed()
                    raise ex
        self._log.info("Number of test cycles finished: {}".format(num_cycle_finished))
        if num_cycle_finished != num_cycles and num_cycle_finished < 5:
            self._log.error("Test failed: {} hrs timer reached before at least 5 test cycles finished.".
                            format(str(run_time/TimeConstants.ONE_HOUR_IN_SEC)))
            return False
        return True

    def run_upi_package_c6_test(self, test, test_duration_sec=60, poll_time_sec=30):
        """
        Run upi package c6 test.

        :param test: specifies the test provided in class UpiChecks.
        :param test_duration_sec: test duration time in seconds
        :param poll_time_sec: Poll time in seconds
        :return: True if the test is successful, False otherwise.
        """
        run_time = 0
        while run_time < test_duration_sec:
            if run_time % poll_time_sec == 0:
                if test == self._upi_checks.LANE and not self._upi_tests_dict[test](package_c6_test=True):
                    return False
                elif test == self._upi_checks.TOPOLOGY and not self.verify_upi_topology():
                    return False
                elif test != self._upi_checks.TOPOLOGY and test != self._upi_checks.LANE:
                    if not self._upi_tests_dict[test]():
                        return False

                rx_ports_in_expected_c6_state = self.verify_rx_ports_c6_state()
                tx_ports_in_expected_c6_state = self.verify_tx_ports_c6_state()
                no_errors_detected = self.verify_no_upi_errors_indicated()

                if not (rx_ports_in_expected_c6_state and tx_ports_in_expected_c6_state and no_errors_detected):
                    return False

                if not self.ptu_check_c6_state_linux():
                    self._log.error("System not in c6 state!")
                    return False

            time.sleep(1)
            run_time += 1

        return True

    def run_upi_idling_test(self, test):
        """
        Run upi idling test.

        :param test: specifies the test provided in class UpiChecks.
        :return: True if the test is successful, False otherwise.
        """
        self.print_upi_topology()
        run_time = 0
        while run_time < self.TWO_HOURS_TIMER:
            if run_time % self.CHECK_INTERVAL_SEC == 0:
                if not self._upi_tests_dict[test]():
                    return False

                if not self.lanes_operational_check():
                    self._log.info("Test failed after {} seconds".format(run_time))
                    return False

                if not self.verify_rx_ports_l0_state():
                    self._log.info("Test failed after {} seconds".format(run_time))
                    return False

                if not self.verify_tx_ports_l0_state():
                    self._log.info("Test failed after {} seconds".format(run_time))
                    return False

                if not self.verify_no_upi_errors_indicated():
                    self._log.info("Test failed after {} seconds".format(run_time))
                    return False
            time.sleep(1)
            run_time += 1

        self._log.info("Timer finished, 2 hours completed")
        return True

    def run_upi_degrade_test(self, num_ports_to_degrade=None, socket_port_pairs_list=None,
                             check_remaining_socket_count=None, num_mlc_check_cycles=20):
        """
        This method runs upi degradation test along with mlc workload.

        :param num_ports_to_degrade: The number to ports to shut down for each socket.
        Ports will be selected randomly
        :param socket_port_pairs_list: specifiy the ports you want to shut donw.
        e.g. [(0,0),(1,3)] means ports Socket0 Port0 and Socket1 Port3 are to be shut down.
        This param will be ignored if num_ports_to_degrade is not None.
        :param check_remaining_socket_count: If not None, the topology verification process would be skipped
        and this number will be used to check if the os sees the same number of sockets.
        :param num_mlc_check_cycles: The number of cycles to run the test.
        If set to 0, the test will run once without mlc load.
        """
        self.print_upi_topology()
        if check_remaining_socket_count is None:
            if not self.degrade_upi_ports(num_ports_to_degrade, socket_port_pairs_list):
                return False
            self.print_upi_topology()
        else:
            self.degrade_upi_ports(num_ports_to_degrade, socket_port_pairs_list, verify_degradation=False)
            if not self.verify_number_of_sockets_linux(check_remaining_socket_count):
                return False

        run_mlc = True
        if num_mlc_check_cycles == 0:
            num_mlc_check_cycles = 1
            run_mlc = False

        if run_mlc:
            mlc_path = self._install_collateral.install_mlc()
            self.os.execute_async("./mlc -t7200", cwd=mlc_path)

        for i in range(num_mlc_check_cycles):
            self._log.info("Test on cycle {}".format(i + 1))

            # Check stress is still running
            if run_mlc:
                if self.os.execute("pgrep mlc", self._command_timeout).return_code == 1:
                    self._log.error("platform stress is not running ...  halting the test")
                    return False

            if not self.lanes_operational_check():
                self._log.info("Test failed at cycle {}".format(i + 1))
                self.os.kill_async_session()
                return False

            if not self.verify_rx_ports_l0_state():
                self._log.info("Test failed at cycle {}".format(i + 1))
                self.os.kill_async_session()
                return False

            if not self.verify_no_upi_errors_indicated():
                self._log.info("Test failed at cycle {}".format(i + 1))
                self.os.kill_async_session()
                return False

            if i < num_mlc_check_cycles - 1:
                time.sleep(self.CHECK_INTERVAL_SEC)

        self.os.kill_async_session()
        return True

    def verify_upi_with_mlc(self, test_type):
        """
        This Method is Used to Upi Link Speed by using Csripts Command before and after executing the MLC and
        verify whether there is >=85% of bandwidth after MLC
        Mixed speeds will assume the lowest speed

        :param test_type: test type
        :return:
        """

        self.print_upi_topology()

        sockets, ports = self.check_sockets_and_ports()
        # Mixed speeds will use lowest speed for BW calculation
        if test_type == self._upi_checks.MIXED_LINK_SPEED:
            upi_link_speed = self.SPR_MIN_LINK_SPEED
        else:
            upi_link_speed = self.get_upi_link_speed()

        self._log.info("UPI_Link_Speed - {}GT/s".format(upi_link_speed))
        self.print_upi_errors()

        if not self.verify_no_upi_errors_indicated():

            raise content_exceptions.TestFail("Please Apply AC cycle to clear CRC error")

        sut_mlc_install_path = self._install_collateral.install_mlc()
        self.os.execute("chmod 777 ./mlc", self._common_content_configuration.get_command_timeout(),
                        sut_mlc_install_path)

        # extract node ranges
        numa_nodes = self.os.execute(self.UPI_NUMA_NODES, self._common_content_configuration.get_command_timeout(),
                                     sut_mlc_install_path).stdout
        node_index = []
        for i in range(6, len(numa_nodes.split()), 4):
            node_index.append(numa_nodes.split()[i])
        self._log.info("Node list - {}".format(node_index))

        # open cfg file handle for MLC execution , create file  and copy to SUT
        mlc_run_file_name = self.MLC_RUN_FILE.split('\\')[-1]

        if self._common_content_configuration.is_container_env():
            container_mlc_run_file = self._install_collateral.util_constants["LINUX_USR_ROOT_PATH"] + "/" + \
                                                    mlc_run_file_name
            mlc_run_cfg_file = open(container_mlc_run_file, 'w')
        else:
            mlc_run_cfg_file = open(self.MLC_RUN_FILE, 'w')

        for cpu_list in range(len(node_index)):
            if cpu_list == (len(node_index) - 1):
                ram_node = 0
            else:
                ram_node = cpu_list + 1
            cfg_append = str(node_index[cpu_list]) + " R seq 1g dram " + str(ram_node) + "\n"
            mlc_run_cfg_file.write(cfg_append)
        mlc_run_cfg_file.close()

        sut_mlc_run_file_path = self._install_collateral.util_constants["LINUX_USR_ROOT_PATH"] + "/" + mlc_run_file_name
        if not self._common_content_configuration.is_container_env():
            self.os.copy_local_file_to_sut(self.MLC_RUN_FILE, sut_mlc_run_file_path)

        mlc_start_command = sut_mlc_install_path + self.MLC_STARTUP_BASE_COMMAND + \
                            str(self.TWO_HOURS_TIMER + self.MLC_STARTUP_ADD_SEC) + \
                            " -o" + mlc_run_file_name

        self._log.info("Starting MLC with cmd={}".format(mlc_start_command))
        self.os.execute_async(mlc_start_command, cwd=os.path.dirname(sut_mlc_run_file_path))

        time.sleep(self.CMD_RE_CHECK_WAIT_TIME_SEC)

        if not check_mlc_running(self):
            raise content_exceptions.TestFail("MLC APP is not running")

        # 2 hours timer
        starttime = datetime.now()

        while (datetime.now() - starttime).seconds < int(self.TWO_HOURS_TIMER):
            if (datetime.now() - starttime).seconds % self.CHECK_INTERVAL_SEC == 0:
                if not self._upi_tests_dict[test_type]():
                    raise content_exceptions.TestFail("{} Failure Detected".format(self._upi_tests_dict[test_type]))
                self._log.info("Checking for CRC error...........")
                self.print_upi_errors()
                if not self.verify_no_upi_errors_indicated():
                    raise content_exceptions.TestFail("CRC error Detected")
                if not check_mlc_running(self):
                    raise content_exceptions.TestFail("MLC APP is not running")

            time.sleep(1)

        self._log.info("Timer finished, 2 hours completed")

        if not check_mlc_running(self):
            raise content_exceptions.TestFail("MLC APP is not running")

        self._stress_provider_obj.kill_stress_tool(stress_tool_name="mlc", stress_test_command="mlc")

        # Bandwidth results
        expected_bandwidth_dict = self.sum_sockets_expected_bandwidth()

        return self.check_bandwidth_with_mlc(expected_bandwidth_dict)

    def check_sockets_and_ports(self):
        """
        Check and return number of sockets and ports.

        :return sockets, ports
        """
        ports = self.get_upi_port_count()
        return self.reg_provider_obj.get_socket_count(), ports

    def get_upi_link_speed(self):
        """
        This Method is Used to get Upi Link Speed.

        :return:
        """
        try:
            initial_link_speed = self.get_link_speed_single_port()
            initial_link_speed_in_gt_per_seconds = \
                self.LINK_RATES[self.reg_provider_obj.silicon_cpu_family][initial_link_speed]
            self._log.info(
                "Initial Link Speed is '{}' GT/s".format(initial_link_speed_in_gt_per_seconds))
        except Exception as ex:
            raise ex
        return initial_link_speed_in_gt_per_seconds

    def get_cscripts_log_file_path(self):
        """
        # We are getting the Path sdp log file.

        :return: log_file_path
        """
        cur_path = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(cur_path, self.CSCRIPTS_FILE_NAME)
        return path

    def verify_upi_error_rate_with_stream(self, test, stream_type="avx3", test_duration_hrs=2):
        """
        This Method is Used to check Upi Error rate by using Csripts Command before and after executing the stream work load and
        verify whether there is Triad best rate >=67% of POR bandwidth after stream

        :param stream_type: (str) Type of stream work load
        :param test : specifies the test provided in class UpiChecks
        :param test_duration_hrs:  (int) Duration of test, run_strean.sh needs to be executed
        :return (Bool): True - on success, False - on Failure
        """
        BUFFER_TIMER_SEC = 1800
        HR_TO_SEC = 3600
        self.check_dimm_configuration()

        self._log.info("Install stream workload on SUT")
        stream_path = self._install_collateral.install_run_stream()
        self._log.debug("run_stream.sh path is - {}".format(stream_path))

        dimm_speed = self._common_content_lib.get_os_dimm_speed()
        stream_target_bw = self.calculate_stream_target_bandwidth(dimm_speed[0])
        self._log.info("Stream Target BW is {}".format(stream_target_bw))

        self._log.info("Starting to compute the iterations")
        compute_result = self.compute_stream_iterations(stream_type, test_duration_hrs, stream_path)
        if not compute_result["status"]:
            return False

        self._log.info("Starting stream work load in SUT")
        if not self.launch_stream(stream_type, compute_result["iterations"], stream_path):
            return False
        end_time = 0

        # covert the test duration in Hrs to Seconds and add a buffer of 30 Minutes
        total_test_runtime_in_sec = (test_duration_hrs * HR_TO_SEC) + BUFFER_TIMER_SEC
        start_time = time.time()
        while (start_time + total_test_runtime_in_sec) > time.time():
            self._log.info("Checking for UPI error...........")
            self.print_upi_errors()
            if not self.verify_no_upi_errors_indicated():
                self._log.info("UPI Error is detected")
                self.stop_runstream()
                return False

            if not self._upi_tests_dict[test]():
                self.stop_runstream()
                return False

            cmd_result = self.os.execute(self.STREAM_PROCESS_CMD, self._common_content_configuration.get_command_timeout()).stdout
            if cmd_result:
                self._log.info("run_stream work load is running on SUT...........")
            else:
                end_time = time.time()
                break
            time.sleep(self.CHECK_INTERVAL_SEC)
            end_time = time.time()
        self._log.info("Stream work load ran for {}s".format(end_time - start_time))
        if not self.post_process_stream_output("stream_output.txt", stream_path, stream_target_bw):
            return False
        self.stop_runstream()
        return True

    def launch_stream(self, stream_type="avx3", iteration_counter=56000, path="/root"):
        """
        This method is used to launch the stream overload

        :param stream_type : (str)  Type of stread workload
        :param iteration_counter: (int)  No of iteration
        :param path : (str)  Location of the .run_stream.sh script

        return (Boolean): True -on successful start of workload
                          False - on failure to start
        """
        DOCKER_CONNECT_DELAY_IN_SEC = 60
        self._stress_provider_obj.kill_stress_tool(stress_tool_name="stream", stress_test_command="./run_stream")
        self.os.execute("rm -rf stream_output.txt", self._common_content_configuration.get_command_timeout(),
                        path)
        self.os.execute_async('./run_stream.sh {} {} > stream_output.txt'.format(stream_type, iteration_counter),
                              cwd=path)
        time.sleep(DOCKER_CONNECT_DELAY_IN_SEC)
        stream_output = self.os.execute("head stream_output.txt",
                                        self._common_content_configuration.get_command_timeout(), path)
        self._log.debug("stream output:\n{}".format(stream_output.stdout))
        if "Running Stream benchmark" not in stream_output.stdout:
            self._log.info("Fail to start run_stream.sh workload")
            return False
        self._log.info("run_stream.sh work load started successfully")
        return True

    def post_process_stream_output(self, stream_output_file, run_stream_path, stream_target_bw):
        """
        This method is used to post process the stream output

        :param stream_output_file (str): stream file name
        :param stream_target_bw (float): BW to be compared against Triad BW
        :param run_stream_path (str): Location of the stream output file
        return (Bool): True - on success, False - on Failure
        """
        run_stream_output = self.os.execute('cat {}'.format(stream_output_file), self._common_content_configuration.get_command_timeout(), run_stream_path)
        self._log.debug("Stream work load output:\n{}".format(run_stream_output.stdout))
        best_triad_rate = re.findall(r'Triad:\s+(\d+(?:\.\d+)?)\s.*', run_stream_output.stdout, re.IGNORECASE | re.MULTILINE)
        if best_triad_rate:
            self._log.info("The Triad best rate - {}MB/s".format(best_triad_rate[0]))
        else:
            self._log.info("Fail to extract the Triad best rate from {}".format(stream_output_file))
            return False

        self._log.info("Compare Triad best rate with the stream target bandwidth")
        if not float(best_triad_rate[0]) >= stream_target_bw:
            self._log.info("Best Triad rate is lesser than the stream target bandwidth")
            return False
        self._log.info("Triad best rate is better than the stream target Bandwidth")
        return True

    def calculate_stream_target_bandwidth(self, dimm_speed):
        """
        This method used to calculate the stream target bandwidth

        :param dimm_speed (str) : dimm speed
        return: stream target bandwidth
        """
        target_bandwidth = self.STREAM_TARGET_BW_DICT[self.reg_provider_obj.silicon_cpu_family].format(int(dimm_speed))
        stream_target_bandwidth = eval(target_bandwidth)
        return stream_target_bandwidth

    def check_dimm_configuration(self):
        """This method is used to Check SUT is populated in 1 DIMM per Channel configuration

        return : None
        raise: Test Fail
        """
        sockets, ports = self.check_sockets_and_ports()
        self._log.info("Check SUT is populated in 1 DIMM per Channel configuration")
        if self._common_content_lib.get_os_dimm_configuration(sockets) != 1:
            raise content_exceptions.TestFail("1 DIMM configuration != 1DPC config")

        self._log.info("check all DIMMs operate at same speed")
        dimm_speed = self._common_content_lib.get_os_dimm_speed()
        if len(dimm_speed) > 1:
            raise content_exceptions.TestFail("DIMMs are not configured at same frequency")

    def stop_runstream(self):
        """This method is used to stop the run stream"""
        self._log.info("Stopping run_stream test..")
        self.os.execute("pkill run_stream", self._command_timeout)

    def verify_upi_with_spec_cpu(self, test_type):
        """
        This Method is Used for Upi with spec_cpu load and verify upi errors after that.
        Example: Consider a max linkspeed case.
        Set bios to max linkspeed - 16Gt/s. Restart the machine.
        Verify speed is set to max and run spec cpu load. Check for UPI errors every few minutes, there shouldn't be any
        Test passes if the load executes for 2hours with no UPI errors reported.

        :param test_type: type of test to run.
        :return:
        """

        self.print_upi_topology()
        self._upi_tests_dict[test_type]()
        sockets, ports = self.check_sockets_and_ports()
        upi_link_speed = self.get_upi_link_speed()
        self._log.info("UPI_Link_Speed - {}GT/s".format(upi_link_speed))
        self.print_upi_errors()

        if not self.verify_no_upi_errors_indicated():
            self._log.info("Power cycling to re-check again")
            ChooseBoot.graceful_sut_ac_power_on()
            self._os.wait_for_os(self.reboot_timeout)
            if not self.verify_no_upi_errors_indicated():
                raise content_exceptions.TestFail("CRC Errors not clear even after a re-boot")

        spec_cpu_path = self._install_collateral.install_run_stream()
        spec_cpu_path = os.path.join(spec_cpu_path[0:-6], "speccpu")
        basic_pnp_setup_path = os.path.join(spec_cpu_path[:-7], "setup")
        self.os.execute("chmod 777 {}".format(self.BASIC_PNP_SETUP_FILE), self._common_content_configuration.get_command_timeout(),
                        basic_pnp_setup_path)
        self._log.info("Starting basic_pnp_setup.sh shell script..........")
        self.os.execute(self.BASIC_PNP_SETUP_FILE, self._common_content_configuration.get_command_timeout(),
                        basic_pnp_setup_path)

        # Starting spec_cpu run
        self._log.info("Running run_spec.sh shell script..........")
        self.os.execute_async("{} intrate".format(self.RUN_SPEC_FILE), cwd=spec_cpu_path)
        time.sleep(self.CHECK_INTERVAL_SEC)
        self._log.info("Check for run_spec.sh has started.....")
        try:
            cmd_result = self.os.execute(self.SPEC_PROCESS_CMD,
                                         self._common_content_configuration.get_command_timeout()).stdout
            if not self.RUN_SPEC_FILE in cmd_result.split():
                self._log.info("Run_spec not running")
                raise content_exceptions.TestFail("./run_spec.sh did not ran, please check manual settings")
        except:
            self._log.info("Couldn't check if run_spec.sh has started or not. Will check again in 5 minutes!!!")

        # 2 hours timer
        while self.TWO_HOURS_TIMER:
            if self.TWO_HOURS_TIMER % self.CHECK_INTERVAL_SEC == 0:

                # adjusting 1 sec in the timer wasted for CRC checks
                self.TWO_HOURS_TIMER -= 1

                # restart spec_cpu_run if 2 hours not completed
                for check in range(3):
                    try:
                        self._log.info("Check {} on run_spec.sh running.....".format(check + 1))
                        cmd_result = self.os.execute(self.SPEC_PROCESS_CMD,
                                                     self._common_content_configuration.get_command_timeout()).stdout
                        self._log.info(cmd_result)
                        if not self.RUN_SPEC_FILE in cmd_result.split():
                            self._log.info("Run_spec completed, Re-starting as 2 hours not yet completed")
                            self.os.execute_async("{} intrate".format(self.RUN_SPEC_FILE), cwd=spec_cpu_path)
                        break
                    except:
                        self._log.info("re-checking {} after {} seconds if run_spec.sh is still running".
                                       format(check + 1, self.CMD_RE_CHECK_WAIT_TIME_SEC))
                        # adjusting 1 sec in the timer wasted for Re-checks
                        time.sleep(self.CMD_RE_CHECK_WAIT_TIME_SEC)
                        self.TWO_HOURS_TIMER -= self.CMD_RE_CHECK_WAIT_TIME_SEC

                if not self._upi_tests_dict[test_type]():
                    raise content_exceptions.TestFail("{} Failure Detected".format(self._upi_tests_dict[test_type]))
                self._log.info("Checking for CRC error...........")
                self.print_upi_errors()
                if not self.verify_no_upi_errors_indicated():
                    raise content_exceptions.TestFail("CRC error Detected")

            mins, secs = divmod(self.TWO_HOURS_TIMER, 60)
            timer = '{:02d}:{:02d}'.format(mins, secs)
            print(timer, end="\r")
            time.sleep(1)
            self.TWO_HOURS_TIMER -= 1
        self._log.info("Timer finished, 2 hours completed")
        self._stress_provider_obj.kill_stress_tool(stress_tool_name="run_spec", stress_test_command=self.RUN_SPEC_FILE)
        self._log.info("Final Check for CRC error...........")
        self.print_upi_errors()
        if not self.verify_no_upi_errors_indicated():
            self._log.info("UPI Error check fail, TEST FAILED")
            return False
        return True

    def compute_stream_iterations(self, stream_type="avx3", test_duration_hrs=2, path="/root"):
        """
        This method is used to launch the stream overload

        :param stream_type : (str)  Type of stread workload
        :param test_duration_hrs: (int)  Duration to run stream in Hrs
        :param path : (str)  Location of the .run_stream.sh script

        return (dict): status (bool) - True on success / False on failure
                        iterations (int) - iterations to complete the test duration
        """
        sockets, ports = self.check_sockets_and_ports()
        result = {"status": False, "iterations": 500}
        if sockets == 4:
            result["iterations"] = 100
        elif sockets == 8:
            result["iterations"] = 50
        STREAM_EXECUTION_SEC = 3600
        self._stress_provider_obj.kill_stress_tool(stress_tool_name="stream", stress_test_command="./run_stream")
        start_time = time.time()
        stream_result = self.os.execute('./run_stream.sh {} {}'.format(stream_type, result["iterations"]),
                                        STREAM_EXECUTION_SEC, cwd=path)
        stream_timer = time.time() - start_time
        if stream_result.cmd_failed():
            self._log.info(("Failed to execute the command {} and the "
                                   "error is {}..".format(stream_result, stream_result.stderr)))
            return result
        self._log.info("Duration to run stream for {} iterations is {}s".format(result["iterations"], stream_timer))
        self._log.debug("stream output:\n{}".format(stream_result.stdout))
        if not re.search("running stream benchmark", stream_result.stdout, flags=re.I):
            self._log.info("Fail to start run_stream.sh workload")
            return result
        computed_iterations = (test_duration_hrs * STREAM_EXECUTION_SEC * result["iterations"]) / stream_timer
        self._log.info("Computed stream s for {} Hr is {}s".format(test_duration_hrs, computed_iterations))
        result["status"] = True
        result["iterations"] = int(computed_iterations)
        return result

    def set_upi_link_random_speed(self):
        """
        Function to set the random link speeds using BIOS knobs

        return None
        """
        bios_knobs = ""
        utils = self.import_upi_module(UpiModules.MOD_UPI_UTILS)
        sockets = self.reg_provider_obj.get_sockets()
        for skt in sockets:
            skt_num = skt.target_info["socketNum"]
            utils.removeDanglingKtiEndpoints(utils.getKtiDevices(skt))
            ports = {socket_port_pair[1] for socket_port_pair in
                     utils.removeDanglingKtiEndpoints(utils.getKtiDevices(skt))}
            self._log.info("Socket- {} and Ports- {}".format(skt_num, ports))
            for port in ports:
                bios_knobs += "Cpu{}P{}KtiLinkSpeed=0x{},".format(skt_num, port, random.randrange(0, 3))
        bios_knobs += "QpiLinkSpeed = 0x8F," + "QpiLinkSpeedMode = 0x1"
        self._log.info("Setting bios knobs: {}".format(bios_knobs))
        import pysvtools.xmlcli.XmlCli as cli
        cli.CvProgKnobs(bios_knobs)

    def get_upi_port_count(self):
        """
        Get the upi port count

        :return:  number of UPI ports
        """

        module = importlib.import_module(self.UPI_MOD_DEFS[self._common_content_lib.get_platform_family()])
        self.sdp.start_log(self.UPI_TOPOLOGY_LOG_FILE)
        upi_defs_obj = eval("module.%supidefs()" % self._common_content_lib.get_platform_family().lower())
        upi_defs_obj.topology()
        self.sdp.stop_log()

        with open(self.UPI_TOPOLOGY_LOG_FILE) as log_file:
            cmd_output = log_file.read()
            reg_output = re.findall(r"Port\s\d+", cmd_output)
            port_count = len(list(set(reg_output)))

        if port_count < 2:
            raise content_exceptions.TestFail("Invalid port count for UPI testing. Check if platform is multi-socket "
                                              "and upi.topology output reports correct port count")

        return port_count
		
    def check_upi_lanes_and_errors(self):
        """
        Check for UPI lanes operational (0x7) and print upi Errors.

        :return Null
        """
        # Verify all lanes operational (data=7)
        self._log.info("Verifying upi lanes operational status (0x7)")
        self.lanes_operational_check()
        self._log.info("Print UPI Errors---")
        self.print_upi_errors()

    def configure_bios_knobs(self, bios_file_name, cfg_opts):
        """
        This method is used to load the bios from the bios config file, it operates based on the CPU family type

        bios_file_name: Name of the bios file to be loaded
        cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.

        :return Null
        """
        cpu_family = self._common_content_lib.get_platform_family().lower()
        bios_config_file_path = bios_file_name + cpu_family + ".cfg"
        complete_bios_config_file_path = os.path.join(self.bios_dir_path, bios_config_file_path)

        self._log.info("Bios file selected: {}".format(complete_bios_config_file_path))
        self.bios_util = BiosUtil(cfg_opts,
                                  bios_config_file=complete_bios_config_file_path,
                                  bios_obj=self.bios, common_content_lib=self._common_content_lib,
                                  log=self._log)


def check_mlc_running(self):
    """
    This Method is Used to verify if MLC stress is still running

    :return: True it mlc is running
    """

    # Need to try multiple times as due to load on system, sometimes it doesn't respond back before timeout
    self._log.info("Check MLC stress app is running .....")
    for check in range(3):
        try:
            cmd_result = self.os.execute(self.MLC_PROCESS_CMD,
                                         self._common_content_configuration.get_command_timeout()).stdout
            if "/mlc" not in cmd_result:
                self._log.info("MLC APP not running")
                return False
            break
        except:
            self._log.info("Re-checking process running after {} seconds, retry - {}".
                           format(self.CMD_RE_CHECK_WAIT_TIME_SEC, check + 1))
            if check == 2:
                raise content_exceptions.TestFail("Failed to verify whether MLC app is running or not!!!!")
            time.sleep(self.CMD_RE_CHECK_WAIT_TIME_SEC)
    self._log.info("MLC stress APP is running ")
    return True
