import time
import os

from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.provider_factory import ProviderFactory

from src.pcie.tests.pi_pcie.pcie_endpoint_ltssm_basetest import PcieEndPointLtssmBaseTest
from src.lib.test_content_logger import TestContentLogger
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon, PxpInventory, LtssmTestType
from src.lib.dtaf_content_constants import PcieSlotAttribute, PcieAttribute
from src.lib import content_exceptions
from src.hsio.upi.hsio_upi_common import HsioUpiCommon, UpiChecks, check_mlc_running
from src.lib.dtaf_content_constants import ProductFamilies


class PcieGens(object):
    GEN4 = 4
    GEN5 = 5


class PcieUpiInteropCommon(HsioUpiCommon, PcieCommon):

    SLOT_WALK_LOG_FILE = "slot_walk_log.txt"
    PCIEG5_PXP4_LINKSTS_REG_PATH = "uncore.pi5.pxp4.pcieg5.ports.cfg.linksts"
    _BIFURCATION_BIOS_KONB = "ConfigIOU3_0"
    _BIFURCATION_x16 = 0x4
    _BIFURCATION_x8x8 = 0x3
    _BIFURCATION_x8x4x4 = 0x1
    _BIFURCATION_x4x4x8 = 0x2
    _BIFURCATION_x4x4x4x4 = 0x0
    _BIFURCATION_VALUES_DICT = {0x4: "x_x_x_x16",
                                0x3: "x_x8x_x8",
                                0x2: "x_x8x4x4",
                                0x1: "x4x4x_x8",
                                0x0: "x4x4x4x4"}
    _BIFURCATION_LINKWIDTH_DICT = {0x4: [16, 0, 0, 0],
                                   0x3: [8, 0, 8, 0],
                                   0x2: [4, 4, 8, 0],
                                   0x1: [8, 0, 4, 4],
                                   0x0: [4, 4, 4, 4]}
    _BIFURCATION_ACTIVE_PORTS_DICT = {0x4: [0],
                                      0x3: [0, 2],
                                      0x2: [0, 1, 2],
                                      0x1: [0, 2, 3],
                                      0x0: [0, 1, 2, 3]}
    TEST_CASE_ID = None
    step_data_dict = {
        1: {'step_details': '1. Check PCIe device Link speed and Width speed\n2. Verify UPI Lane',
            'expected_results': '1. PCIe Link speed and width speed as Expected\n2. All UPI Lanes functional'},
        2: {'step_details': '1.  Disable the driver and run the ltssm test\n2. run MLC tool',
            'expected_results': '1. Device driver disabled successfully and passed ltssm Test\n2.'
                                ' MLC tool ran successfully'},
        3: {'step_details': '1. Check MCE Error\n2. Check Bandwidth Matrix',
            'expected_results': '1. No MCE Error Captured\n2. Bandwidth as expected'},
    }

    def __init__(self, test_log, arguments, cfg_opts, config=None):
        """
        Creates a new PcieUpiInteropCommon object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieUpiInteropCommon, self).__init__(test_log, arguments, cfg_opts, config)
        if config:
            if "{}" in config:
                config = config.format((self.reg_provider_obj.silicon_cpu_family).lower())
            config = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), config)
            self.bios_config_file_path = config
            self.bios_util.bios_config_file = config
        if self.TEST_CASE_ID:
            self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self._upi_checks = UpiChecks()
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.pcie_ltssm_basetest_obj = PcieEndPointLtssmBaseTest(self._log, arguments, cfg_opts, self.bios_config_file_path)
        self.csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.csp = ProviderFactory.create(self.csp_cfg, self._log)
        self.pcie_common = PcieCommon(self._log, self._args, self._cfg)
        self.pxp_inventory = PxpInventory(self.sdp, self.pcie_common.pcie_obj, self.pcie_common.PCIE_SLS_OUTPUT_LOG)
        self.MLC_PROCESS_CMD = "ps -ef | grep mlc"
        self.MLC_FILE_PERMISSION_CHANGE_CMD = "chmod 777 ./mlc"
        self.MLC_ITERATIONS = 7200
        self.SBR_TEST_WAIT_TIME_SEC = 60
        self.SBR_TEST_TIME_SEC = 360
        self.LTSSM_TEST_TIME_SEC = 13

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
        super(PcieUpiInteropCommon, self).prepare()

    def verify_pcieg5_pxp4_ports_linkwidth_speed(self, bifurcation,
                                                port0_target_speed_gen=PcieGens.GEN5,
                                                other_ports_speed_gen=PcieGens.GEN5):
        """
        Verify the generations for the ports under pxp4
        are the given target speed generation .

        :param port0_target_speed_gen: generation expected for port0.
        :param bifurcation: specify which bifurcation the system is configured.
        :param other_ports_speed_gen: specify the generation expected for other ports than port0.
        :return: True is verification successful. False otherwise.
        """
        path = self.PCIEG5_PXP4_LINKSTS_REG_PATH
        link_stats = self.reg_provider_obj.get_by_path(self.reg_provider_obj.SOCKET, path)
        all_ports_linkwidth_matched = True
        all_ports_generation_matched = True
        for port in self._BIFURCATION_ACTIVE_PORTS_DICT[bifurcation]:
            gen = link_stats[port] & 0xf
            linkwidth = (link_stats[port]>>4) & 0x3F
            self._log.info("Port{} is x{}, GEN{}".format(port, linkwidth, gen))
            if linkwidth != self._BIFURCATION_LINKWIDTH_DICT[bifurcation][port]:
                all_ports_linkwidth_matched = False

            if port == 0:
                if gen != port0_target_speed_gen:
                    all_ports_generation_matched = False
            elif gen != other_ports_speed_gen:
                all_ports_generation_matched = False

        if all_ports_linkwidth_matched and all_ports_generation_matched:
            self._log.info("All pxp4 ports linkwidth and generation match expected.")
        else:
            self._log.info("pxp4 ports linkwidth/generation not match!")
        return all_ports_linkwidth_matched and all_ports_generation_matched

    def slot_walk_check_max_speed(self):
        """
        Do slot walk to verify that all endpoints with active links
        are running at maximum link speed.
        This method would apply to platforms from GNR going forward.

        :return: True if all endpoints running at maximum speed. False otherwise.
        """
        if not self._product_family == ProductFamilies.GNR:
            log_error = "This method only applies to platforms from GNR going forward."
            self._log.error(log_error)
            raise RuntimeError(log_error)
        pxp_inventory = PxpInventory(self.sdp, self.pcie_obj, self.SLOT_WALK_LOG_FILE)
        inventory = pxp_inventory.get_pxp_inventory(positive_link_width_only=True, platform=ProductFamilies.GNR)
        all_ports_speed_matched = True
        for protocol in inventory.keys():
            for socket in inventory[protocol].keys():
                for endpoint in inventory[protocol][socket]:
                    if len(endpoint) == 0:
                        continue
                    bdf_address = self.get_device_bdf(int(socket), endpoint)
                    try:
                        max_speed = self.get_device_max_speed(bdf_address)
                        current_speed = self.get_device_current_speed(bdf_address)
                    except RuntimeError:
                        self._log.info("socket{} - {}: No linkcap/linksts info found for this endpoint, skipped.".format(socket, endpoint))
                        continue
                    self._log.info("socket{} - {}:".format(socket, endpoint))
                    self._log.info("linkcap: " + max_speed)
                    self._log.info("linksts: " + current_speed)
                    if max_speed == current_speed:
                        self._log.info("Speed match: socket{} - {}, {}".format(socket, endpoint, current_speed))
                    else:
                        self._log.error("Speed not match: socket{} - {} max linkspeed should be {}, but detected {}".\
                                        format(socket, endpoint, max_speed, current_speed))
                        all_ports_speed_matched = False
        if all_ports_speed_matched:
            self._log.info("All devices running at maximum link speed.")
        else:
            self._log.error("Some device(s) not running at maximum link speed.")
        return all_ports_speed_matched

    def run_pe3upi3_pxp4_verification_test(self, bifurcation,
                                           port0_target_speed_gen=PcieGens.GEN5,
                                           other_ports_speed_gen=PcieGens.GEN5,
                                           mlc_load=False):
        """
        Run tests that verifies the generations for the ports under pxp4
        are the given target speed generation.

        :param port0_target_speed_gen: generation expected for port0.
        :param bifurcation: specify which bifurcation the system is configured.
        :param other_ports_speed_gen: specify the generation expected for other ports than port0.
        :param mlc_load: specify if the mlc speed is needed for this test.
        :return: True if the test is successful, False otherwise.
        """
        self._log.info("Testing on bifurcation {}".format(self._BIFURCATION_VALUES_DICT[bifurcation]))
        import pysvtools.xmlcli.XmlCli as cli
        self._log.info("Setting bifurcation {} to {}".format(self._BIFURCATION_BIOS_KONB,
                                                             self._BIFURCATION_VALUES_DICT[bifurcation]))
        cli.CvProgKnobs(self._BIFURCATION_BIOS_KONB + "=" + str(bifurcation))
        self._log.info("Bios set, performing cold reset...")
        self.perform_graceful_g3()
        if mlc_load:
            num_cycle = 20
            mlc_path = self._install_collateral.install_mlc()
            self.os.execute_async("./mlc -t7200", cwd=mlc_path)
        else:
            num_cycle = 1
        test_passed = True
        for i in range(num_cycle):
            self._log.info("Test on cycle {}".format(i + 1))
            if not self.verify_pcieg5_pxp4_ports_linkwidth_speed(bifurcation,
                                                                 port0_target_speed_gen,
                                                                 other_ports_speed_gen):
                self._log.info("Test failed at cycle {}".format(i + 1))
                test_passed = False
                break

            if mlc_load:
                if not (check_mlc_running(self) \
                        and self.lanes_operational_check() \
                        and self.verify_no_upi_errors_indicated()):
                    self._log.info("Test failed at cycle {}".format(i + 1))
                    test_passed = False
                    break
                time.sleep(self.CHECK_INTERVAL_SEC)

        if mlc_load:
            self.os.kill_async_session()
            if test_passed:
                expected_bandwidth_dict = self.sum_sockets_expected_bandwidth()
                test_passed = self.check_bandwidth_with_mlc(expected_bandwidth_dict)

        return test_passed

    def run_pe3upi3_pxp4_cycling_test(self,bifurcation,
                                           port0_target_speed_gen=PcieGens.GEN5,
                                           normalized_speed_gen=PcieGens.GEN5,
                                           cycling_method=None):
        """
        Run cycling tests that verifies the generations for the ports under pxp4
        are the given target speed generation.

        :param port0_target_speed_gen: generation expected for port0.
        :param bifurcation: specify which bifurcation the system is configured.
        :param normalized_speed_gen: specify the generation expected for other ports than port0.
        :param cycling_method: Specifies the cycling method, either cold or warm. Will do both if not specified.
        :return: True if the test is successful, False otherwise.
        """
        self._log.info("Testing on bifurcation {}".format(self._BIFURCATION_VALUES_DICT[bifurcation]))
        import pysvtools.xmlcli.XmlCli as cli
        self._log.info("Setting bifurcation {} to {}".format(self._BIFURCATION_BIOS_KONB,
                                                             self._BIFURCATION_VALUES_DICT[bifurcation]))
        cli.CvProgKnobs(self._BIFURCATION_BIOS_KONB + "=" + str(bifurcation))
        self._log.info("Bios set, performing cold reset...")
        self.perform_graceful_g3()

        if cycling_method:
            num_cycle = 2
            cycling_methods = [cycling_method]
        else:
            cycling_methods = [self._upi_checks.COLD_RESET, self._upi_checks.WARM_RESET]
            num_cycle = 3

        test_passed = True
        for i in range(num_cycle):
            self._log.info("Test on cycle {}".format(i + 1))
            if not self.verify_pcieg5_pxp4_ports_linkwidth_speed(bifurcation,
                                                                 port0_target_speed_gen,
                                                                 normalized_speed_gen):
                self._log.info("Test failed at cycle {}".format(i + 1))
                test_passed = False
                break

            if i < num_cycle - 1:
                if cycling_methods[i] == self._upi_checks.COLD_RESET:
                    self._common_content_lib.perform_os_reboot(self.reboot_timeout)
                elif cycling_methods[i] == self._upi_checks.WARM_RESET:
                    self.perform_graceful_g3()

        return test_passed

    def run_slot_walk_verification_test(self, mlc_load=False):
        """
        Run tests that verifies that all pcie endpoints are running at maximun link speed.

        :param mlc_load: specify if the mlc speed is needed for this test.
        :return: True if the test is successful, False otherwise.
        """
        if mlc_load:
            num_cycle = 20
            mlc_path = self._install_collateral.install_mlc()
            self.os.execute_async("./mlc -t7200", cwd=mlc_path)
        else:
            num_cycle = 1
        test_passed = True
        for i in range(num_cycle):
            self._log.info("Test on cycle {}".format(i + 1))
            if not self.slot_walk_check_max_speed():
                self._log.info("Test failed at cycle {}".format(i + 1))
                test_passed = False
                break

            if not self.lanes_operational_check():
                self._log.info("Test failed at cycle {}".format(i + 1))
                test_passed = False
                break

            if mlc_load:
                if not (check_mlc_running(self) \
                        and self.verify_no_upi_errors_indicated()):
                    self._log.info("Test failed at cycle {}".format(i + 1))
                    test_passed = False
                    break
                time.sleep(self.CHECK_INTERVAL_SEC)

        if mlc_load:
            self.os.kill_async_session()
            if test_passed:
                expected_bandwidth_dict = self.sum_sockets_expected_bandwidth()
                test_passed = self.check_bandwidth_with_mlc(expected_bandwidth_dict)

        return test_passed

    def run_ltssm_with_mlc(self, ltssm_test_list):
        """
        This method is to execute:
        1. This test verifies link width is stable and all lanes are active
        2. MLC load for a minimum of  2 hrs
        3. LTSSM test running in parallel for 2hrs
        4. After MLC  has completed verify the bandwidth >=  85% of expected (based on current link speed)
        5. No LTSSM errors occurred

        :param ltssm_test_list: list of ltssm tests to run
        :return: True/False: True if expected UPI bandwidth met, False otherwise
        """

        self._log.info("Checking UPI lanes operational and Print upi errors....")
        self.check_upi_lanes_and_errors()

        # install MLC tool
        self._log.info("Installing MLC tool to sut")
        self.mlc_path = self._install_collateral.install_mlc()
        sut_path = self.pcie_common._pcie_ltssm_provider.install_ltssm_tool()


        # Starting MLC App run
        self._log.info("Starting MLC app for 2 hours.........")
        self.os.execute(self.MLC_FILE_PERMISSION_CHANGE_CMD, self._common_content_configuration.get_command_timeout(),
                        self.mlc_path)
        self.os.execute_async("./mlc -t{}".format(self.MLC_ITERATIONS), cwd=self.mlc_path)
        time.sleep(self.CMD_RE_CHECK_WAIT_TIME_SEC)

        if not check_mlc_running(self):
            raise content_exceptions.TestFail("MLC APP is not running")
        self._log.info("MLC app has successfully started.")
        # 2 hours timer
        stop_time = time.time() + self.TWO_HOURS_TIMER
        while stop_time > time.time():
            if self._common_content_configuration.get_pcie_ltssm_auto_discovery():

                self._log.info("Auto-discovering PCIe endpoints for testing")
                for socket, ports in self.pxp_inventory.get_populated_ports_dict().items():
                    if len(ports) < 1:
                        raise Exception("PCIe Auto-discovery did not detect any ports")
                    for port in ports:
                        bdf = self.pcie_common.get_device_bdf(socket, port)
                        did = self.pcie_common.get_device_id(bdf)
                        for each_test in ltssm_test_list:
                            if each_test == LtssmTestType.ASPML1 and not self.is_aspm_supported(
                                    bdf):
                                self._log.info("ASPM not supported on adapter {}, skipping".format(bdf))
                                return True
                            self.pcie_common._pcie_ltssm_provider.run_ltssm_tool(test_name=each_test,
                                                                                 device_id=did,
                                                                                 cmd_path=sut_path,
                                                                                 skip_errors_on_failures=None,
                                                                                 pxp_port=port, pxp_socket=socket)
                            if not check_mlc_running(self):
                                raise content_exceptions.TestFail("MLC APP is not running")

                            break
            else:
                self._log.info("Using PCIe endpoints defined in content configuration for testing")
                pcie_slot_list = self._common_content_configuration.get_pcie_slot_to_check()
                pcie_gen = self.pcie_common.get_pcie_device_generation(self.reg_provider_obj, self.sdp)
                pcie_device_info_list_from_config = self._common_content_configuration.get_required_pcie_device_details(
                    product_family=self.pcie_common._product_family, required_slot_list=pcie_slot_list)
                each_slot_info_dict_list = []
                for each_slot_info_dict in pcie_device_info_list_from_config:
                    # clear list and assigned pcie slot tag to list as argument require list.
                    each_slot_info_dict_list.clear()
                    each_slot_info_dict_list.append(each_slot_info_dict)
                    self._test_content_logger.start_step_logger(1)
                    pcie_device_info_dict = self.pcie_common.\
                        check_expected_device_speed_and_width(self.reg_provider_obj,
                                                              each_slot_info_dict_list,
                                                              each_slot_info_dict,
                                                              pcie_gen)
                    for bdf, device_details in pcie_device_info_dict.items():
                        for each_test in ltssm_test_list:
                            if each_test == LtssmTestType.ASPML1 and not self.is_aspm_supported(
                                    bdf):
                                self._log.info("ASPM not supported on adapter {}, skipping".format(bdf))
                                return True
                            self.pcie_common._pcie_ltssm_provider.run_ltssm_tool(test_name=each_test,
                                                                                 device_id=
                                                                                 device_details[PcieAttribute.DEVICE_ID],
                                                                                 cmd_path=sut_path,
                                                                                 skip_errors_on_failures=None, bdf=bdf)
                            if not check_mlc_running(self):
                                raise content_exceptions.TestFail("MLC APP is not running")
                        break

        self._log.info("Timer finished, 2 hours completed")
        if not check_mlc_running(self):
            raise content_exceptions.TestFail("MLC APP is not running")
        self._stress_provider_obj.kill_stress_tool(stress_tool_name="mlc",
                                                                    stress_test_command="mlc")
        self._log.info("Checking for any MCE Error.....")
        mce_error = self._common_content_lib.check_if_mce_errors()
        if mce_error:
            raise content_exceptions.TestFail("MCE error was Captured in Log.")
        self._log.debug("No MCE error was Captured in Os Log")
        self._log.info("Checking UPI lanes operational and Print upi errors after stress....")
        self.check_upi_lanes_and_errors()
        # Bandwidth results
        self._log.info("Checking Bandwidth status..................")
        expected_bandwidth_dict = self.sum_sockets_expected_bandwidth()

        expected_bandwidth_status = self.check_bandwidth_with_mlc(expected_bandwidth_dict)
        return expected_bandwidth_status
