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

import time
import os
import re

from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.exceptions import OsStateTransitionException
from dtaf_core.lib.dtaf_constants import ProductFamilies
from dtaf_core.lib.exceptions import OsCommandException

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.provider.stressapp_provider import StressAppTestProvider


class IoPmCommon(ContentBaseTestCase):
    """
    This Class is used as common class for IO Power Management Cycling
    """
    UPI_POST_CODE_BREAK_POINT = 0x57000000  # boot postcode before OS is booted
    G3_OFF_TIME_SEC = 30  # wait time in G3 mechanical off state
    RESUME_FROM_BREAK_POINT_WAIT_TIME_SEC = 600  # time in seconds for os to resume from POST code break point
    OS_EXECUTE_COMMAND_TIME_SEC = 30  # max time in seconds that an arbitrary command should take to execute
    SUT_OFF_MAX_POLL_NUMBER = 24  # max number of times we will poll target is off
    SUT_OFF_POLL_TIME_SEC = 5  # seconds between polling target is off
    BIOS_PROGRESS_POLL_NUMBER = 180  # max number of times we will poll BIOS progress
    BIOS_PROGRESS_POLL_TIME_SEC = 5  # seconds between polling BIOS progress code
    WAIT_AFTER_G3_BEFORE_CSCRIPTS_INIT_SECONDS = 60

    GENERIC_HW_ERROR_JOURNALCTL = [r"\[Hardware Error\]"]
    GENERIC_MACHINE_CHECK_JOURNALCTL = GENERIC_HW_ERROR_JOURNALCTL + ["Machine check events logged"]
    UPI_MACHINE_CHECK_SOCKET0_JOURNALCTL = GENERIC_MACHINE_CHECK_JOURNALCTL + [r"CPU 0: Machine Check: 0 Bank 5"]
    BERT_PCIE_UCENF_JOURNALCTL = GENERIC_HW_ERROR_JOURNALCTL + [r"BERT: Error records from previous boot:",
                                                                r"type: recoverable",
                                                                r"section_type: PCIe error"]
    GENERIC_MACHINE_CHECK_JOURNALCTL_CORR = GENERIC_MACHINE_CHECK_JOURNALCTL + ["type: corrected"]

    UPI_MACHINE_CHECK_BOOTED_JOURNALCTL = GENERIC_HW_ERROR_JOURNALCTL + ["general processor error", "corrected"]

    POST_CODE_FREEZE_TIMEOUT_SEC = 30
    BIOS_BREAK_REG_PATH = 'ubox.ncdecs.biosscratchpad6_cfg'
    BIOS_PROGRESS_REG_PATH = 'ubox.ncdecs.biosnonstickyscratchpad7_cfg'
    LOW_LANE_FAILURE_RESULT = 0x4
    ALL_LANES_ACTIVE_RESULT = 0x7

    THERMAL_MONITOR_LOG_STATUS_REG = 'punit.package_therm_status.thermal_monitor_log'
    THERMAL_MONITOR_STATUS_REG = 'punit.package_therm_status.thermal_monitor_status'

    KTI_UPI_PATH_DICT = {ProductFamilies.CLX: "kti",
                         ProductFamilies.CPX: "kti",
                         ProductFamilies.SKX: "kti",
                         ProductFamilies.ICX: "upi.upi",
                         ProductFamilies.SPR: "upi.upi"}
    CSCRIPTS_SEVERITY = {"NONFATAL": "nonfatal",
                         "FATAL": "fatal"}
    CSCRIPTS_SEVERITY_BOOL = {CSCRIPTS_SEVERITY["NONFATAL"]: 0,
                              CSCRIPTS_SEVERITY["FATAL"]: 1}
    CSCRIPTS_PCIE_ERROR_TYPES = {'UCE': 'uce',
                                 'CE': 'ce'}
    HOST_ROOT_PATH = "host/root"
    SUT_PATH = r"c:\\workspace\\"

    # Workload selection, 0 for SSE2, 1 for AVX128, etc.
    SOLAR_WL_SSE2 = "0"
    SOLAR_WL_AVX128 = "1"
    SOLAR_WL_AVX256 = "2"
    SOLAR_WL_AVX512 = "3"
    SOLAR_WL_AVX128LITE = "4"
    SOLAR_WL_AVX256LITE = "5"
    SOLAR_WL_AVX512LITE = "6"
    SOLAR_WL_AVX512VNNI = "7"
    SOLAR_WL_DGEMM = "8"
    DICT_SOLAR_WL = {
        SOLAR_WL_SSE2: "SSE2",
        SOLAR_WL_AVX128: "AVX128",
        SOLAR_WL_AVX256: "AVX256",
        SOLAR_WL_AVX512: "AVX512",
        SOLAR_WL_AVX128LITE: "AVX128Lite",
        SOLAR_WL_AVX256LITE: "AVX256Lite",
        SOLAR_WL_AVX512LITE: "AVX512Lite",
        SOLAR_WL_AVX512VNNI: "AVX512-VNNI",
        SOLAR_WL_DGEMM: "DGEMM"
    }

    SOLAR_TEST_PSTATE = "pstate"
    SOLAR_START_DELAY_SEC = 5
    # PTU Workload selection.
    PTU_CPU_TEST = "ct"
    PTU_WORKLOAD_TEST_DICT = {
        ProductFamilies.ICX: "3",
        ProductFamilies.SPR: "1"}
    PTU_CPU_TEST_CORE_IA_SSE_TEST = "3"

    WINDOWS_PCIE_CORRECTABLE_ERR_SIGNATURE = ["id: 17",
                                              "corrected hardware error",
                                              "PCI Express",
                                              "CorrectableErrorStatus: 0x1"]

    WINDOWS_PCIE_NONFATAL_ERR_SIGNATURE = ["id: 17",
                                           "corrected hardware error",
                                           "PCI Express",
                                           "UncorrectableErrorStatus: 0x4000"]

    WINDOWS_UPI_CORRECTABLE_ERR_SIGNATURE = ["id: 19",
                                             "corrected hardware error",
                                             "Error Source: Corrected Machine Check",
                                             "Error Type: Bus/Interconnect Error"]
    MLC_STRESS_TOOL_PATH = "/home/mlc/Linux/mlc -t7200"
    MLC_DELAY_TIME_SEC = 30

    LINUX_UPI_16B_CRC_LLR_ERR_SIGNATURE = ["event severity: corrected",
                                           "Error 0, type: corrected",
                                           "general processor error",
                                           "processor_type: 0, IA32/X64"]

    LINUX_UPI_16B_CRC_LLR_ERR_SIGNATURE_JOURNALCTL = ["Corrected error",
                                                      "LL Rx detected CRC error",
                                                      "successful LLR without Phy Reinit"]

    PTU_DICT_WINDOWS = {"SUT_DIR": "C:\Program Files\Intel\Power Thermal Utility - Server Edition",
                        "PTU_FILE_NAME": "unified_server_ptu.zip",
                        "RUN_TDP": "ptu.exe -ct 1",
                        "PTU_INSTALLER_NAME": "Intel Power Thermal Utility - Server Edition (Internal Use Only).msi",
                        }

    PTU_KILL_WINDOWS_DICT = {ProductFamilies.ICX: "taskkill /IM xpptuicx.exe /F",
                             ProductFamilies.SPR: "taskkill /IM xpptuspr.exe /F",
                             }
    PTU_KILL_TIMEOUT_SECONDS = 60
    PTU_START_DELAY_SEC = 5

    PRIME95_DICT_WINDOWS = {"SUT_DIR": "C:\prime95",
                            "PRIME95_FILE_NAME": "prime95.zip",
                            "RUN_WORKLOAD":"prime95.exe -t",
                            "KILL_PROC":"taskkill /IM prime95.exe /F"
                            }

    MSR_ADDR_PACKAGE_RAPL_LIMIT = 0x610
    MSR_PACKAGE_RAPL_LIMIT_ADJUSTMENT = 0x200

    ITP_REG_REBOOT_DELAY_SEC = 15

    def __init__(self, test_log, arguments, cfg_opts, config):
        """
        Creates a new PmCyclingCommon object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        if config:
            config = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), config)
        super(IoPmCommon, self).__init__(test_log, arguments, cfg_opts, config)
        self._cfg = cfg_opts

        self.host_root_path = cfg_opts.find(self.HOST_ROOT_PATH).text

        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)

        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)

        self.product = self._common_content_lib.get_platform_family()

        self._os_log_obj = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration)
        self._stress_provider = StressAppTestProvider.factory(self._log, cfg_opts, self.os)
        self._install_collateral = InstallCollateral(self._log, self.os, self._cfg)

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
        super(IoPmCommon, self).prepare()

    def warm_reboot_non_blocking(self, alt_restart_cmd=False):
        """
        This method initiates a non-blocking warm reboot.

        return: none
        raise: RuntimeError
        """
        try:
            if alt_restart_cmd:
                restart_cmd = self.os.os_consts.Commands.SHUTDOWN_RESTART
            else:
                restart_cmd = self.os.os_consts.Commands.RESTART

            self._log.info("Restarting OS with cmd= " + str(restart_cmd))
            if not self.os.execute(restart_cmd, self.OS_EXECUTE_COMMAND_TIME_SEC):
                log_err = "Command Failed: " + str(restart_cmd)
                self._log.error(log_err)
                raise log_err
            time.sleep(self.ITP_REG_REBOOT_DELAY_SEC)
        except Exception as ex:
            log_err = "An Exception Occurred while attempting to reboot target : {}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

    def g3_cycle_non_blocking(self):
        """
        This method initiates a non-blocking G3 cycle.

        return: none
        raise: RuntimeError
        """
        try:
            self.os.execute(self.os.os_consts.Commands.SHUTDOWN, self.OS_EXECUTE_COMMAND_TIME_SEC)
            for j in range(self.SUT_OFF_MAX_POLL_NUMBER):
                time.sleep(self.SUT_OFF_POLL_TIME_SEC)
                if self.os.is_alive():
                    if j >= self.SUT_OFF_MAX_POLL_NUMBER:
                        raise OsStateTransitionException("Unable to power off the SUT!")
                else:
                    break
            if not self.ac_power.ac_power_off(self.G3_OFF_TIME_SEC):
                log_err = "Error: unable to power off Target"
                self._log.error(log_err)
                raise OsStateTransitionException(log_err)
            time.sleep(self.G3_OFF_TIME_SEC)
            if not self.ac_power.ac_power_on(self.G3_OFF_TIME_SEC):
                log_err = "Error: unable to power on Target"
                self._log.error(log_err)
                raise OsStateTransitionException(log_err)
            time.sleep(self.G3_OFF_TIME_SEC)
        except Exception as ex:
            log_err = "An Exception Occurred while attempting to cycle the target : {}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

    def set_bios_break(self, cscripts_obj, break_point):
        """
        This method is used to set a BIOS break point.

        param: Obj cscripts_obj
        param: break_point Hex value of BIOS progress code to break on
        return: none
        raise: RuntimeError
        """

        try:
            cscripts_obj.get_by_path(cscripts_obj.UNCORE, self.BIOS_BREAK_REG_PATH).write(break_point)
            reg_break_point = cscripts_obj.get_by_path(cscripts_obj.UNCORE, self.BIOS_BREAK_REG_PATH)
            if reg_break_point == break_point:
                self._log.info("Successfully wrote bios breakpoint({})".format(str(reg_break_point)))
            else:
                self._log.info("Failed to write bios breakpoint({}), actual={}".format(str(break_point),
                                                                                       str(reg_break_point)))
        except Exception as ex:
            log_err = "An Exception Occurred while setting BIOS break point : {}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

    def clear_bios_break(self, cscripts_obj):
        """
        This method is used to clear a BIOS break point.

        param: Obj cscripts_obj
        return: none
        raise: RuntimeError
        """
        self.set_bios_break(cscripts_obj, 0x0)

    def get_bios_progress_code(self, cscripts_obj):
        """
        This method is used to get the current BIOS progress code.

        param: Obj cscripts_obj used to read register
        return: current BIOS progress code
        raise: RuntimeError
        """

        try:
            return cscripts_obj.get_by_path(cscripts_obj.UNCORE, self.BIOS_PROGRESS_REG_PATH)
        except Exception as ex:
            log_err = "An Exception Occurred while getting current BIOS progress code : {}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

    def check_bios_progress_code(self, cscripts_obj, expected_progress_code):
        """
        This method is used to check the current BIOS progress code.
        This method raises an exception if the expected_progress_code is not reached within 15 minutes.

        param: Obj cscripts_obj
        param: Hex expected_progress_code value of expected BIOS progress code
        return: True if BIOS Progress code reached
        raise: RuntimeError
        """

        attempt = 0
        while self.BIOS_PROGRESS_POLL_NUMBER > attempt:
            try:
                current_post_code = self.get_bios_progress_code(cscripts_obj)
                self._log.info("Post Code " + str(current_post_code))
                if current_post_code == expected_progress_code:
                    # Check for frozen post
                    time.sleep(self.POST_CODE_FREEZE_TIMEOUT_SEC)
                    if expected_progress_code == self.get_bios_progress_code(cscripts_obj):
                        self._log.info("Post Code has frozen for " + str(self.POST_CODE_FREEZE_TIMEOUT_SEC))
                        return True
            except Exception as ex:
                log_err = "An Exception Occurred While Checking progress Code : {}".format(ex)
                self._log.error(log_err)
                if self.BIOS_PROGRESS_POLL_NUMBER <= attempt:
                    raise RuntimeError(log_err)
            attempt += 1
            if self.BIOS_PROGRESS_POLL_NUMBER <= attempt:
                log_err = "Sut did not reach progress code " + str(expected_progress_code)
                self._log.error(log_err)
                raise log_err
            time.sleep(self.BIOS_PROGRESS_POLL_TIME_SEC)

    def check_upi_lane_failover_enabled(self, cscripts_obj, socket=0, port=0):
        """
        Checks UPI Lane failover enabled.
        Raises Exception if failover is not enabled.

        :param cscripts_obj:
        :param socket: CPU socket number
        :param port: KTI/UPI port
        :return: none
        """

        upi_failover_en_product_reg_path_dict = {ProductFamilies.SKX: self.KTI_UPI_PATH_DICT[ProductFamilies.SKX] +
                                                 str(port) + "_reut_ph_ctr1.c_failover_en",
                                                 ProductFamilies.CLX: self.KTI_UPI_PATH_DICT[ProductFamilies.CLX] +
                                                 str(port) + "_reut_ph_ctr1.c_failover_en",
                                                 ProductFamilies.CPX: self.KTI_UPI_PATH_DICT[ProductFamilies.CPX] +
                                                 str(port) + "_reut_ph_ctr1.c_failover_en",
                                                 ProductFamilies.ICX: self.KTI_UPI_PATH_DICT[ProductFamilies.ICX] +
                                                 str(port) + ".ktireut_ph_ctr1.c_failover_en",
                                                 ProductFamilies.SPR: self.KTI_UPI_PATH_DICT[ProductFamilies.SPR] +
                                                 str(port) + ".ktireut_ph_ctr1.c_failover_en"}

        upi_failover_enable = cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                                       upi_failover_en_product_reg_path_dict
                                                       [cscripts_obj.silicon_cpu_family], socket_index=socket)
        if upi_failover_enable != 0x1:
            log_err = "Error UPI Failover IS NOT Enabled! "
            self._log.error(log_err)
            raise Exception(log_err)
        else:
            self._log.info("UPI Failover is Enabled")

    def check_upi_rx_lanes_active(self, cscripts_obj, expected_value, socket=0, port=0):
        """
        Checks UPI Lane failover enabled.
        Raises Exception if failover is not enabled.

        :param cscripts_obj:
        :param expected_value: hex expected value of Rx active ports
        :param socket: CPU socket number
        :param port: KTI/UPI port
        :return: none
        """

        upi_rx_lanes_active_product_reg_path_dict = {ProductFamilies.SKX: self.KTI_UPI_PATH_DICT[ProductFamilies.SKX] +
                                                     str(port) + "_reut_ph_css.s_clm",
                                                     ProductFamilies.CLX: self.KTI_UPI_PATH_DICT[ProductFamilies.CLX] +
                                                     str(port) + "_reut_ph_css.s_clm",
                                                     ProductFamilies.CPX: self.KTI_UPI_PATH_DICT[ProductFamilies.CPX] +
                                                     str(port) + "_reut_ph_css.s_clm",
                                                     ProductFamilies.ICX: self.KTI_UPI_PATH_DICT[ProductFamilies.ICX] +
                                                     str(port) + ".ktireut_ph_css.s_clm",
                                                     ProductFamilies.SPR: self.KTI_UPI_PATH_DICT[ProductFamilies.SPR] +
                                                     str(port) + ".ktireut_ph_css.s_clm"}

        upi_rx_lanes_active = cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                                       upi_rx_lanes_active_product_reg_path_dict
                                                       [cscripts_obj.silicon_cpu_family], socket_index=socket)
        if upi_rx_lanes_active != expected_value:
            log_err = "Error active Rx UPI lanes on socket {} port {} does not equal {}!".format(
                socket, port, expected_value)
            self._log.error(log_err)
            raise Exception(log_err)
        else:
            self._log.info("Active Rx UPI lanes on socket {} port {} equals {}".format(socket, port, expected_value))

    def reset_upi_link(self, cscripts_obj, socket=0, port=0):
        """
        Resets UPI Link of specified Socket and Port.

        :param cscripts_obj: cscripts object
        :param socket: socket number
        :param port: port number
        :return:
        """

        ph_ctr1_path_dict = {ProductFamilies.CLX: self.KTI_UPI_PATH_DICT[ProductFamilies.CLX] + str(port) +
                             "_reut_ph_ctr1",
                             ProductFamilies.CPX: self.KTI_UPI_PATH_DICT[ProductFamilies.CPX] + str(port) +
                             "_reut_ph_ctr1",
                             ProductFamilies.SKX: self.KTI_UPI_PATH_DICT[ProductFamilies.SKX] + str(port) +
                             "_reut_ph_ctr1",
                             ProductFamilies.ICX: self.KTI_UPI_PATH_DICT[ProductFamilies.ICX] + str(port) +
                             ".ktireut_ph_ctr1",
                             ProductFamilies.SPR: self.KTI_UPI_PATH_DICT[ProductFamilies.SPR] + str(port) +
                             ".ktireut_ph_ctr1"}
        # unlock Dfx if ICX
        if cscripts_obj.silicon_cpu_family == ProductFamilies.ICX or \
                cscripts_obj.silicon_cpu_family == ProductFamilies.SPR:
            self._log.info("Unlocking UPI dfx registers")

            cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                     "upi.upi" + str(port) + ".dfx_lck_ctl_cfg.reutenglck",
                                     socket_index=socket).write(0)
            cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                     "upi.upi" + str(port) + ".dfx_lck_ctl_cfg.reutlck",
                                     socket_index=socket).write(0)

        self._log.info("Reset UPI link")
        cscripts_obj.get_by_path(cscripts_obj.UNCORE, ph_ctr1_path_dict[cscripts_obj.silicon_cpu_family],
                                 socket_index=socket).cp_reset.write(1)

    def set_rx_data_lane_disable(self, cscripts_obj, socket=0, port=0, value=0x1):
        """
        Sets lane disable of specified Socket and Port.

        :param cscripts_obj: cscripts object
        :param socket: int socket number
        :param port: port number
        :param value: Hex value to set. (0x1)
        :return: none
        """

        lane_disable_path_rdv_dict = {ProductFamilies.CLX: self.KTI_UPI_PATH_DICT[ProductFamilies.CLX] + str(port) +
                                      "_reut_ph_rdc",
                                      ProductFamilies.CPX: self.KTI_UPI_PATH_DICT[ProductFamilies.CPX] + str(port) +
                                      "_reut_ph_rdc",
                                      ProductFamilies.SKX: self.KTI_UPI_PATH_DICT[ProductFamilies.SKX] + str(port) +
                                      "_reut_ph_rdc",
                                      ProductFamilies.ICX: self.KTI_UPI_PATH_DICT[ProductFamilies.ICX] + str(port) +
                                      ".ktireut_ph_rdc",
                                      ProductFamilies.SPR: self.KTI_UPI_PATH_DICT[ProductFamilies.SPR] + str(port) +
                                      ".ktireut_ph_rdc"}
        # Disable low lane
        cscripts_obj.get_by_path(cscripts_obj.UNCORE, lane_disable_path_rdv_dict[cscripts_obj.silicon_cpu_family],
                                 socket_index=socket).rxdatalanedisable.write(value)
        self.reset_upi_link(cscripts_obj, socket=socket, port=port)

    def set_rx_data_lane_enable(self, cscripts_obj, socket=0, port=0):
        """
        Sets lane disable to 0x0 of specified Socket and Port.

        :param cscripts_obj: cscripts object
        :param socket: socket number
        :param port: port number
        :return: none
        """
        self.set_rx_data_lane_disable(cscripts_obj, socket=socket, port=port, value=0x0)

    def inject_and_check_upi_error_single_injection(self,
                                                    cscripts_obj,
                                                    init_err_count=0,
                                                    socket=0,
                                                    port=0,
                                                    number_crc_err=1,
                                                    ignore_crc_cnt=False):
        """
        This method is used to inject UPI CRC errors.
        Warm boot (reboot) does not clear kticrcerrcnt.
        We return the injection error count for using in warm boot testing.
        This method injects a single error on each use.

        param: Obj cscripts_obj
        param: int init_count initial count of errors.
        param: ignore_crc_cnt  will not track injection count - just inject err
        return: int Current error injection count.
        raise: RuntimeError
        """
        try:
            ei = cscripts_obj.get_cscripts_utils().get_ei_obj()
            inject_count = init_err_count
            if not ignore_crc_cnt:
                if cscripts_obj.get_by_path(cscripts_obj.UNCORE, "upi.upi0.kticrcerrcnt", socket) == init_err_count:
                    self._log.debug("Before inject error, error count is found as expected")
                else:
                    log_err = "Before inject error, error count should have been " + str(init_err_count) +\
                              " but found some unexpected value"
                    self._log.error(log_err)
                    raise Exception(log_err)

                ei.injectUpiError(socket, port, number_crc_err)
                inject_count = init_err_count + 1
                if cscripts_obj.get_by_path(cscripts_obj.UNCORE, "upi.upi0.kticrcerrcnt", socket) == inject_count:
                    self._log.debug("Injected Error count matched the expected value : {}".format(inject_count))
                else:
                    log_err = "Inject Error Count did not match the expected value : {}".format(inject_count)
                    self._log.error(log_err)
                    raise log_err
            else:
                ei.injectUpiError(socket, port, number_crc_err)

        except Exception as ex:
            log_err = "An exception occurred during UPI error injection : {}".format(ex)
            self._log.error(log_err)
            raise log_err

        # if no error return current inject_count.
        return inject_count

    def inject_pcie_error_cscripts(self,
                                   cscripts_obj,
                                   error_type,
                                   socket=0,
                                   port='pxp0.port0',
                                   severity=CSCRIPTS_SEVERITY["NONFATAL"]):
        """
        This method is used to inject PCI errors.

        param: Obj cscripts_obj
        param: String error_type either CE or UCE
        param: int socket number
        param: String pcie complex and port number eg. 'pxp0.port0' or 'pxp3.pcieg5.port0'
        param: String severity either fatal or nonfatal. Used for UCE injection.
        return: None
        raise: RuntimeError
        """

        pcie_ctes_reg_path = {ProductFamilies.ICX: "pcie." + str(port) + ".cfg.erruncsev.ctes",
                              ProductFamilies.SPR: "pis." + str(port) + ".cfg.erruncsev.ctes"}

        try:
            ei = cscripts_obj.get_cscripts_utils().get_ei_obj()
            ei.resetInjectorLockCheck(0)
            # severity used for UCE injection
            if error_type == self.CSCRIPTS_PCIE_ERROR_TYPES['UCE']:
                try:
                    ei.injectPcieError(socket=socket, port=port, errType=error_type, severity=severity)
                except TypeError:
                    self._log.info("Trying to set severity manually...")
                    cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                             pcie_ctes_reg_path[cscripts_obj.silicon_cpu_family],
                                             socket_index=socket).write(self.CSCRIPTS_SEVERITY_BOOL[severity])
                    ei.injectPcieError(socket=socket, port=port, errType=error_type)
            else:
                ei.injectPcieError(socket=socket, port=port, errType=error_type)

        except Exception as ex:
            log_err = "An Exception Occurred during CScripts PCIe error injection : {}".format(ex)
            self._log.error(log_err)
            raise log_err

    def inject_pcie_ce_and_check_regs_cscripts(self, cscripts_obj, sdp_obj, socket=0, port='pxp0.port0'):
        """
        This method is used to inject and check for PCI receiver error.

        param: Obj cscripts_obj
        param: Obj sdp_obj
        param: int socket number
        param: String pcie complex and port number eg. 'pxp0.port0' or 'pxp3.pcieg5.port0'
        return: None
        raise: RuntimeError
        """
        pcie_rx_error_path = {ProductFamilies.ICX: "pcie." + str(port) + ".cfg.errcorsts.re",
                              ProductFamilies.SPR: "pi5." + str(port) + ".cfg.errcorsts.re"}
        sdp_obj.halt()
        self.inject_pcie_error_cscripts(cscripts_obj, 'ce', socket=socket, port=port)
        rx_exception = cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                                pcie_rx_error_path[cscripts_obj.silicon_cpu_family],
                                                socket_index=socket)
        sdp_obj.go()
        if rx_exception != 1:
            log_err = "Correctable Receiver Error not found in Receiver Exception register!"
            self._log.error(log_err)
            raise log_err
        else:
            self._log.info("Socket: {} Complex.Port: {} re = {}".format(socket, port, rx_exception))

    def get_receiver_mask_reg_value(self, cscripts_obj, socket=0, port='pxp0.port0'):
        """
        This method is used to retrieve the value of the receiver mask register

        param: Obj cscripts_obj
        param: int socket number
        param: String pcie complex and port number eg. 'pxp0.port0' or 'pxp3.pcieg5.port0'
        return: None
        raise: RuntimeError
        """

        pcie_reg_name = {ProductFamilies.ICX: "pcie." + str(port) + ".cfg.erruncmsk.rem",
                         ProductFamilies.SPR: "pi5." + str(port) + ".cfg.errcormsk.rem"}

        reg = cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                       pcie_reg_name[cscripts_obj.silicon_cpu_family],
                                       socket_index=socket)

        if reg is None:
            self._log.error("receiver mask register could not be read")
            raise RuntimeError
        return reg

    def get_correrr_counter_reg_value(self, cscripts_obj, socket=0, port='pxp0.port0'):
        """
        This method is used to retrieve the value of the correctable error counter

        param: Obj cscripts_obj
        param: int socket number
        param: String pcie complex and port number eg. 'pxp0.port0' or 'pxp3.pcieg5.port0'
        return: None
        raise: RuntimeError
        """

        pcie_reg_name = {ProductFamilies.ICX: "pcie." + str(port) + ".cfg.corerrcnt.errcnt",
                         ProductFamilies.SPR: "pi5." + str(port) + ".cfg.corerrcnt.errcnt"}

        reg = cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                       pcie_reg_name[cscripts_obj.silicon_cpu_family],
                                       socket_index=socket)

        if reg is None:
            self._log.error("correctable error counter register could not be read")
            raise RuntimeError
        return reg

    def inject_pcie_uce_and_check_regs_cscripts(self,
                                                cscripts_obj,
                                                sdp_obj,
                                                socket=0,
                                                port='pxp0.port0',
                                                severity=CSCRIPTS_SEVERITY["NONFATAL"]):
        """
        This method is used to inject completion time out error.
        This method will check CScripts register completion timeout exception (CTE)

        param: Obj cscripts_obj
        param: Obj sdp_obj
        param: int socket number
        param: String pcie complex and port number eg. 'pxp0.port0' or 'pxp3.pcieg5.port0'
        return: None
        raise: RuntimeError
        """
        pcie_cto_error_path = {ProductFamilies.ICX: "pcie." + str(port) + ".cfg.erruncsts.cte",
                               ProductFamilies.SPR: "pis." + str(port) + ".cfg.erruncsts.cte"}
        sdp_obj.halt()
        self.inject_pcie_error_cscripts(cscripts_obj, 'uce', socket=socket, port=port, severity=severity)
        cto_error = cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                             pcie_cto_error_path[cscripts_obj.silicon_cpu_family],
                                             socket_index=socket)
        sdp_obj.go()
        if cto_error != 1:
            log_err = "Uncorrectable CTO Error not found in Completion Timeout Exception Register!"
            self._log.error(log_err)
            raise log_err
        else:
            self._log.info("Socket: {} Complex.Port: {} cte = {}".format(socket, port, cto_error))

    def get_os_pcie_width(self):
        """
        This method gets pcie width from OS

        return: OS pcie lane width for configured pcie bdf
        raise: RuntimeError
        """
        try:
            # Checking OS data on pcie card
            lspci_os_get_width_cmd = "lspci -vvv -s " + str(self.OS_PCIE_BDF) + "|grep LnkSta:"
            ssh_cmd_result = self.os.execute(lspci_os_get_width_cmd, self.OS_EXECUTE_COMMAND_TIME_SEC)
            if ssh_cmd_result.return_code != 0:
                log_err = "OS cmd failed(" + str(lspci_os_get_width_cmd) + ")"
                self._log.error(log_err)
                raise log_err
            # some lspci output include commas - thus the wa
            os_width = int(ssh_cmd_result.stdout.split('x')[1].replace(",", " ,")[0:2])
            self._log.info("OS pcie width for BDF " + str(self.OS_PCIE_BDF) + " = " + str(os_width))
            return os_width

        except Exception as ex:
            log_err = "An Exception Occurred while attempting to OS get pcie width : {}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

    def check_processor_turbo_mode_win(self):
        """
        On Windows, check if processor in turbo mode.

        :return: True if in Turbo mode at the time of probe.
        """
        BASE_PROCESSOR_PERFORMANCE = 100
        perf = self.os.execute("powershell (Get-Counter -Counter "
                               "'\Processor Information(_Total)\% Processor Performance')"
                               ".CounterSamples.CookedValue", self._command_timeout)
        self._log.info("Proc performance: {}%".format(perf.stdout.strip()))

        return float(perf.stdout) > BASE_PROCESSOR_PERFORMANCE

    def set_powercfg_processor_throttle_min(self, percent):
        """
        On Windows, switch the power plan to BALANCED.
        And set minimum processor state
        """
        self.os.execute("powercfg.exe -setacvalueindex "
                        "SCHEME_BALANCED SUB_PROCESSOR PROCTHROTTLEMIN {}".format(percent),
                        self._command_timeout)
        self.os.execute("powercfg.exe -s SCHEME_BALANCED", self._command_timeout)

    def reset_powercfg(self):
        """
        Restore minimum processor state back to 100%
        """
        self.set_powercfg_processor_throttle_min(100)

    def install_prime95_on_sut_win(self):
        """
        Copy and install prime95 to Windows SUT.
        Prime95 is copied from zip file in the collateral folder.
        """
        if self.os.check_if_path_exists(self.PRIME95_DICT_WINDOWS['SUT_DIR'] + "\prime95.exe"):
            self._log.info("Prime95 already installed.")
            return

        prime95_host_path = self._install_collateral.download_tool_to_host(
            self.PRIME95_DICT_WINDOWS["PRIME95_FILE_NAME"])

        self._log.info("copying prime95 to SUT")
        self.os.execute(r"mkdir {}".format(self.SUT_PATH), self._command_timeout)
        self.os.copy_local_file_to_sut(prime95_host_path, r"{}".format(self.SUT_PATH))

        self._log.info("unzipping Prime95...")
        self.os.execute(r'powershell Expand-Archive -LiteralPath "{}{}" -DestinationPath "{}"'
                        .format(self.SUT_PATH, self.PRIME95_DICT_WINDOWS["PRIME95_FILE_NAME"], self.PRIME95_DICT_WINDOWS["SUT_DIR"]),
                        self._command_timeout)

        if not self.os.check_if_path_exists(self.PRIME95_DICT_WINDOWS['SUT_DIR'] + "\prime95.exe"):
            raise OsCommandException("Prime95 not installed properly!")

    def install_ptu_on_sut_win(self):
        """
        Copy and install PTU to Windows SUT.
        Windows PTU is copied from zip file in the collateral path Windows folder.
        The zip file contains an MSI file and PTU installation.
        These files can be generated with the relevant PTU installation file and the "/a" option.
        eg. "Intel Power Thermal Utility - Server Edition (Internal Use Only)_615179_v2.3_setup.exe" /a

        :return: None
        """
        if self.os.check_if_path_exists(self.PTU_DICT_WINDOWS['SUT_DIR'] + "\ptu.exe"):
            self._log.info("PTU already installed.")
            return

        ptu_host_path = self._install_collateral.download_tool_to_host(self.PTU_DICT_WINDOWS["PTU_FILE_NAME"])

        self._log.info("copying PTU to SUT")
        self.os.execute(r"mkdir {}".format(self.SUT_PATH), self._command_timeout)
        self.os.copy_local_file_to_sut(ptu_host_path, r"{}".format(self.SUT_PATH))

        self._log.info("unzipping PTU...")
        self.os.execute(r'powershell Expand-Archive -LiteralPath "{}{}" -DestinationPath "{}"'
                        .format(self.SUT_PATH, self.PTU_DICT_WINDOWS["PTU_FILE_NAME"], self.SUT_PATH), self._command_timeout)

        self._log.info("installing PTU...")
        result = self.os.execute(r'"{}" /quiet'.format(self.PTU_DICT_WINDOWS["PTU_INSTALLER_NAME"]),
                                 self._command_timeout, cwd=self.SUT_PATH)
        if result.cmd_failed():
            raise OsCommandException("Error while installing PTU!")

    def kill_ptu_win(self, silicon_cpu_family):
        """
                Kill PTU on Windows SUT.

                :param silicon_cpu_family: CPU family string
                :return: None
        """

        self.os.execute("taskkill /IM ptu.exe /F", self.PTU_KILL_TIMEOUT_SECONDS)
        self.os.execute(self.PTU_KILL_WINDOWS_DICT[silicon_cpu_family], self.PTU_KILL_TIMEOUT_SECONDS)

    def install_ptu_on_sut_linux(self):
        """
        Copy and install PTU to the SUT

        :return:
        """

        if self.os.execute("./ptu -v", self._command_timeout).return_code == 1:
            self._log.info("PTU already installed.")
            return
        # This matches the name used in src.lib.install_collateral
        ptu_file_name = "unified_server_ptu.tar.gz"
        install_collateral = InstallCollateral(self._log, self.os, self._cfg)
        tool_host_path = install_collateral.download_tool_to_host(tool_name=ptu_file_name)
        self.os.copy_local_file_to_sut(tool_host_path, "/root/")

        self.os.execute("tar -xvf " + ptu_file_name, self._command_timeout)

        if self.os.execute("./ptu -h", self._command_timeout).return_code == 1:
            self._log.info("PTU has been installed")
        else:
            err_log = "PTU NOT installed successfully!"
            self._log.error(err_log)
            raise Exception(err_log)

    def ptu_check_c6_state(self):
        """
        On windows, check in the PTU if the C6 state greater than 80%

        :return: True if %C6 greater than 80
        """
        C6_THRESHOLD = 70
        self.os.execute(r"rmdir /Q /S c:\PTU", self._command_timeout)
        self.os.execute(r'"C:\Program Files\Intel\Power Thermal Utility - Server Edition\PTU.exe"'
                        ' -mon -filter 0x08 -log -csv -t 1',
                        self._command_timeout)
        c6 = self.os.execute("powershell (Import-Csv 'c:\PTU\*_ptumon.csv')[0].c6",
                             self._command_timeout)

        self._log.info("The c6 state is: " + c6.stdout)
        return float(c6.stdout) > C6_THRESHOLD

    def ptu_check_c6_state_linux(self):
        """
        On Linux, check in the PTU if the C6 state greater than 90%

        :return: True if %C6 greater than 90. False otherwise.
        """
        c6_threshold = 90
        ptu_filter = 0x08
        ptu_running_duration_in_sec = 15
        self.os.execute("rm -rf /root/log/", self._command_timeout)
        self.os.execute("./ptu -y -mon -filter {} -log -logdir /root/log/ -csv -t {}"
                        .format(ptu_filter, ptu_running_duration_in_sec),
                        self._command_timeout)
        if not self.os.check_if_path_exists("/root/log/*ptumon.csv"):
            self._log.error("PTU C6 State not captured !")
            return False
        csv = self.os.execute("cat /root/log/*ptumon.csv", self._command_timeout)
        c6_list = []
        c6_scan_count = len(re.findall("CPU0", csv.stdout.strip()))
        for c6_value in range(c6_scan_count - 1):
            c6_list.append(csv.stdout.strip().split("CPU0")[c6_value+1].split(",")[5])
        c6 = max(c6_list)
        self._log.info("The C6 state is: {}".format(c6))
        return float(c6) > c6_threshold

    def ptu_execute_linux(self, test_type, workload, duration_sec):
        """
        Running PTU wokload on Linux SUT

        :param test_type: Specify the test type. e.g. "ct" for CPU test
        :param workload: Specify the workload to run under each test type.
        :param duration_sec: Specify the duration in second to run ptu workload.
        """
        self.ptu_kill_linux()
        self.os.execute_async("./ptu -y -{} {} -t {} ".format(test_type, workload, duration_sec))

    def ptu_kill_linux(self):
        """
        Kill PTU process on Linux SUT
        """
        self.os.execute("killall ptu", self._command_timeout)

    def solar_install(self):
        """
        Copy and install Solar to the SUT

        :return:
        """
        if self.os.check_if_path_exists("C:\Solar\Solar.exe"):
            self._log.info("Solar already installed.")
            return
        self._log.info("Copying Solar to SUT")
        self.os.execute(r"mkdir c:\workspace", self._command_timeout)
        self.os.copy_local_file_to_sut(
            self.host_root_path + r"\Solar-3.20.393.0.exe", r"c:\workspace")

        self._log.info("Installing Solar...")
        self.os.execute(r"c:\workspace\Solar-3.20.393.0.exe "
                        "--mode unattended --unattendedmodeui minimal",
                        self._command_timeout)

    def solar_execute(self, pm_test, workload, duration=3600):
        """
        Execute solar PM tests along with workload

        :param pm_test: The option which PM test to run. eg: pstate
        :param workload: The choice of workload to run. eg: SSE2
        :param duration: The time to run solar test and its workload, measured in second.
        :return:
        """
        self.solar_kill_process()

        solar_cmd = r"start C:\Solar\Solar.exe /{} ".format(pm_test) + \
            r"-scope 100:0:0 -rdist 100:0:0 -gvpoints Turbo -mode e -d sec:{}".format(duration)
        workload_cmd = r" & start C:\Solar\Workloads\WLPowerVirus.exe " \
            r"-a {} -d {}".format(workload, duration)
        if workload == self.SOLAR_WL_DGEMM:
            workload_cmd = r" & start C:\Solar\Workloads\WLDGEMM.exe " \
                r"-i 0 -d {}".format(duration)
        schtask_tr = "\"" + "cmd.exe /c " + solar_cmd + workload_cmd + "\""

        schtask_create = r"schtasks /create /SC ONCE /TN solar /TR {} /ST 00:00 /F" \
            .format(schtask_tr)

        self.os.execute(schtask_create, self._command_timeout)

        schtask_run = r"schtasks /run /TN solar"

        self.os.execute(schtask_run, self._command_timeout)

        schtask_del = r"powershell Unregister-ScheduledTask -TaskName solar -Confirm:$false"

        self.os.execute(schtask_del, self._command_timeout)

    def solar_kill_process(self):
        """
        Kills Solar process and workloads for Windows.
        """
        self.os.execute("powershell Stop-Process -Name 'WLPowerVirus','WLDGEMM','Solar'",
                        self._command_timeout)

    def inject_pcie_error(self, cscripts_obj, sdp_obj,
                          socket, port, err_type=None, severity=None):
        """
        inject pcie error with cscripts module

        :param socket:  socket to inject
        :param port: port to inject
        :param err_type: options are "uce", "ce", "both".
        """

        ei = cscripts_obj.get_cscripts_utils().get_ei_obj()

        sdp_obj.itp.smmentrybreak = 1

        self._log.info("Reset injector lock...")
        ei.resetInjectorLockCheck()

        self._log.info("Injecting pcie error...")
        ei.injectPcieError(socket, port, err_type, severity)

        if sdp_obj.is_halted():
            sdp_obj.go()

    def install_mlc_on_sut_linux(self):
        """
        Copy and install MLC to the SUT

        :return:
        """
        if self.os.execute("./mlc --help", self._command_timeout).return_code == 0:
            self._log.info("MLC already installed.")
            return
        # This matches the name used in src.lib.install_collateral
        mlc_file_name = "mlc.tgz"

        host_tool_path = self._install_collateral.download_tool_to_host(mlc_file_name)
        self.os.copy_local_file_to_sut(host_tool_path, "/root/")

        self.os.execute("tar -xvf " + mlc_file_name, self._command_timeout)

        self.os.execute("chmod +x mlc", self._command_timeout)
        if self.os.execute("./mlc --help", self._command_timeout).return_code == 0:
            self._log.info("MLC has been installed")
        else:
            err_log = "MLC NOT installed successfully!"
            self._log.error(err_log)
            raise Exception(err_log)

    def get_cpus_by_node_linux(self, node):
        """
        Determine platform processors IDs of the given NUMA node.

        :param node: The NUMA node number to find all its processors IDs
        :return: The string that contains processor IDs. e.g. '0-35,72-107'
        """

        proc_ids = self.os.execute("lscpu | grep node{}".format(node) + " | awk '{print $4}'", self._command_timeout)
        self._log.info("NUMA node{} CPU(s):   {}".format(node, proc_ids.stdout))
        return proc_ids.stdout.rstrip()

    def iperf3_stop(self):
        """
        Stop iperf3
        """
        self.os.execute("pkill iperf3", self._command_timeout)

    def start_mlc_stress(self, mlc_path_and_flags=MLC_STRESS_TOOL_PATH, specify_node=False):
        """
        Start the mlc stress app

        :param mlc_path_and_flags: the path and flags to run the mlc.
        :param specify_node: If true, will start mlc from node0 and run tests on node1.
        :return:
        """
        try:
            mlc_exe_name = mlc_path_and_flags.split("-")[0]
            cmd_result = self.os.execute(mlc_exe_name + " --help", self._command_timeout)
            if cmd_result.return_code != 0:
                self._log.info("Verified mlc is NOT installed.")
                self._log.info("Please install mlc app to " + str(os.path.dirname(mlc_path_and_flags)))
                log_err = "MLC not installed"
                self._log.error(log_err)
                raise log_err

            self._log.info("Starting MLC stress app..")
            if specify_node:
                node_0 = 0
                node_1 = 1
                cpus_node0 = self.get_cpus_by_node_linux(node_0)
                cpus_node1 = self.get_cpus_by_node_linux(node_1)
                mlc_path_and_flags = "taskset --cpu-list {} ".format(cpus_node0) + mlc_path_and_flags \
                          + " -k{}".format(cpus_node1)

            self._stress_provider.execute_async_stress_tool(mlc_path_and_flags, "mlc")
            time.sleep(self.MLC_DELAY_TIME_SEC)

        except Exception as ex:
            log_err = "An Exception Occurred while starting MLC stress : {}".format(ex)
            self._log.error(log_err)
            raise OsCommandException(log_err)

    def stop_mlc_stress(self):
        """
        Stop the mlc stress app

        :return:
        """
        self._log.info("Stopping MLC stress app..")
        app_name = os.path.basename(self.MLC_STRESS_TOOL_PATH).split(" ")[0]

        kill_cmd = "pkill {}".format(app_name)
        self.os.execute(kill_cmd, self._command_timeout)
        time.sleep(self.MLC_DELAY_TIME_SEC)

    def mount_nvme(self):
        """
        Mount nvme for Linux.

        :return: True if mount successfully, False otherwise.
        """
        nvme_partition_path = self._common_content_configuration.get_nvme_partition_to_mount()
        self.os.execute("mkdir /mnt/nvme/", self._command_timeout)
        self.os.execute("mount {} /mnt/nvme/".format(nvme_partition_path), self._command_timeout)
        check_mount = self.os.execute("grep -qs '/mnt/nvme ' /proc/mounts", self._command_timeout)
        if check_mount.return_code != 0:
            self._log.error("Mount not successful for {} !"
                            "Make sure nvme path consistent with config file!".format(nvme_partition_path))
            return False
        self.os.execute("touch /mnt/nvme/test", self._command_timeout)
        return True

    def get_thermal_monitor_log_reg(self, cscripts_obj, socket=0):
        """
        logs thermal status of specified Socket.

        :param cscripts_obj: cscripts object
        :param socket: int socket number
        :return: tuple (therm_log_sts, therm_sts)
        """

        # get thermal log status and thermal status
        therm_log_sts = cscripts_obj.get_by_path(cscripts_obj.UNCORE, self.THERMAL_MONITOR_LOG_STATUS_REG,
                                                 socket_index=socket)
        therm_sts = cscripts_obj.get_by_path(cscripts_obj.UNCORE, self.THERMAL_MONITOR_STATUS_REG, socket_index=socket)

        self._log.info("Thermal monitor log status socket: {} = {}".format(socket, therm_log_sts))
        self._log.info("Thermal monitor status socket: {} = {}".format(socket, therm_sts))

        return therm_log_sts, therm_sts

    def get_cpu_performance_percent(self):
        """
        Get cpu performance for Windows. In percentage of base frequency.
        """
        perf = self.os.execute("powershell (Get-Counter -Counter "
                               "'\Processor Information(_Total)\% Processor Performance')"
                               ".CounterSamples.CookedValue", self._command_timeout)
        return perf

    def get_cpu_frequency_linux(self):
        """
        Get cpu frequency on Linux.
        """
        cfreq = self.os.execute("lscpu | grep 'CPU MHz:' | awk '{print $3}'", self._command_timeout)

        return float(cfreq.stdout)

    def set_rapl_and_verify(self, sdp_obj, addr, diff):
        """
        Set rapl and verify for Windows. Solar is needed for verification.

        :param sdp_obj: the sdp object that queries or sets the msr
        :param addr: the msr address (Pakage_RAPL_LIMIT) that needs to be tuned.
        :param diff: value to subtract from P1 Limit.
        :return: the original msr value before change if RAPL verified successful,
                 zero otherwise.
        """
        SOLAR_START_DELAY_SEC = 5
        SOLAR_WL_DURATION_SEC = 300
        SOLAR_WL_CMD = "C:\Solar\Workloads\WLPowerVirus.exe -a {} -d {}"\
                       .format(self.SOLAR_WL_SSE2, SOLAR_WL_DURATION_SEC)

        sdp_obj.halt()
        msr_num_origin = sdp_obj.msr_read(addr, squash=True)
        sdp_obj.go()
        self._log.info("The original rapl value is: {}".format(hex(msr_num_origin)))

        self.os.execute_async(SOLAR_WL_CMD)
        time.sleep(SOLAR_START_DELAY_SEC)
        initial_cpu_perf_percentage = self.get_cpu_performance_percent().stdout.strip()
        self._log.info("Before the change, the cpu performance is: {}%".format(initial_cpu_perf_percentage))

        sdp_obj.halt()
        sdp_obj.msr_write(addr, msr_num_origin - diff)
        msr_num_modified = sdp_obj.msr_read(addr, squash=True)
        sdp_obj.go()
        self._log.info("The modified rapl value is: {}".format(hex(msr_num_modified)))

        rapl_throttling_cpu_perf_percentage = self.get_cpu_performance_percent().stdout.strip()
        self._log.info("After the change, the cpu performance is: {}%".format(rapl_throttling_cpu_perf_percentage))

        self.solar_kill_process()
        if float(initial_cpu_perf_percentage) > float(rapl_throttling_cpu_perf_percentage):
            self._log.info("RAPL throttling verified.")
            return msr_num_origin
        else:
            self._log.error("RAPL throttling failed!")
            return 0

    def set_rapl_and_verify_linux(self, sdp_obj, addr, diff):
        """
        Set rapl and verify for Linux. PTU is needed at root directory for verification.

        :param sdp_obj: the sdp object that queries or sets the msr
        :param addr: the msr address (Pakage_RAPL_LIMIT) that needs to be tuned.
        :param diff: value to subtract from P1 Limit.
        :return: the original msr value before change if RAPL verified successful,
                 zero otherwise.
        """
        PTU_START_DELAY_SEC = 5
        PTU_WL_CMD = "./ptu -y -{} {}".format(self.PTU_CPU_TEST, self.PTU_CPU_TEST_CORE_IA_SSE_TEST)

        sdp_obj.halt()
        msr_num_origin = sdp_obj.msr_read(addr, squash=True)
        sdp_obj.go()
        self._log.info("The original rapl value is: {}".format(hex(msr_num_origin)))

        self.os.execute_async(PTU_WL_CMD)
        time.sleep(PTU_START_DELAY_SEC)
        initial_cpu_freq = self.get_cpu_frequency_linux()
        self._log.info("Before the change, the cpu frequency is: {} MHz".format(initial_cpu_freq))

        sdp_obj.halt()
        sdp_obj.msr_write(addr, msr_num_origin - diff)
        msr_num_modified = sdp_obj.msr_read(addr, squash=True)
        sdp_obj.go()
        self._log.info("The modified rapl value is: {}".format(hex(msr_num_modified)))

        rapl_throttling_cpu_freq = self.get_cpu_frequency_linux()
        self._log.info("After the change, the cpu frequency is: {} MHz".format(rapl_throttling_cpu_freq))

        self.ptu_kill_linux()
        if initial_cpu_freq > rapl_throttling_cpu_freq:
            self._log.info("RAPL throttling verified.")
            return msr_num_origin
        else:
            self._log.error("RAPL throttling failed!")
            return 0
