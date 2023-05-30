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

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.content_base_test_case import ContentBaseTestCase
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.lib import content_exceptions
from src.ras.lib.ras_upi_util import RasUpiUtil
from src.hsio.upi.hsio_upi_common import HsioUpiCommon


class UpiLlrCrcCommon(ContentBaseTestCase):
    """
    This Class is used as common class for all the CRC Test Cases
    """
    S0 = 0
    PORT = 0
    CRC_ERC = 1
    INITIAL_INJECT_COUNT = 1
    LAST_INJECT_COUNT = 3
    CRC_16_BIT_MODE = 0x0
    CRC_32_BIT_MODE = 0x1
    EINJCTL_REG_NAME = "rxeinjctl0"
    GOOD_PORT_STATE = [0xf, 0xd, 0x5]
    os_error_log_delay_sec = 20
    THRESHOLD_SET_VALUE = 0x8014
    HALT_GO_DELAY_SEC = 10

    UPI_CORRECTABLE_LINK_RETRY_WO_INIT_ERR_SIGNATURE = ["Hardware Error",
                                                        "Corrected error",
                                                        "LL Rx detected CRC error",
                                                        "successful LLR without Phy Reinit"]
    UPI_CORRECTABLE_LINK_RETRY_W_INIT_ERR_SIGNATURE = ["Hardware Error",
                                                       "Corrected error",
                                                       "LL Rx detected CRC error",
                                                       "successful LLR with Phy Reinit"]

    def __init__(self, test_log, arguments, cfg_opts, config):
        """
        Creates a new UpiLlrCrcCommon object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), config)
        super(UpiLlrCrcCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file)

        self._cfg = cfg_opts

        self._args = arguments

        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)

        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)

        self.product = self._common_content_lib.get_platform_family()

        self._os_log_obj = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration)
        self._install_collateral = InstallCollateral(test_log, self.os, self._cfg)
        self.hsioupi_obj = HsioUpiCommon(test_log,arguments, cfg_opts)

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
        self._install_collateral.copy_mcelog_binary_to_sut()
        super(UpiLlrCrcCommon, self).prepare()

    def check_upi_llr_crc_enabled(self, expected_crc_mode):
        """

        :return:
        """
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:
            sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
            sv_obj = cscripts_obj.get_cscripts_utils().getSVComponent()
            is_upi_llr_crc_enabled = False

            self._log.info("Halting the System")
            sdp_obj.halt()
            time.sleep(self.HALT_GO_DELAY_SEC)

            self._log.info("Refreshing the System")
            sv_obj.refresh()
            if expected_crc_mode == self.CRC_32_BIT_MODE:
                self._log.info("Verify whether UPI LLR 32 bit Rolling CRC is Enabled through Bios")
            else:
                self._log.info("Verify whether UPI LLR 16 bit Rolling CRC is Enabled through Bios")

            upi_llr_crc_reg_path_dict = {ProductFamilies.CLX: "kti0_ls.current_crc_mode",
                                         ProductFamilies.SKX: "kti0_ls.current_crc_mode",
                                         ProductFamilies.CPX: "kti0_ls.current_crc_mode",
                                         ProductFamilies.ICX: "upi.upi0.ktils.current_crc_mode",
                                         ProductFamilies.SNR: "upi.upi0.ktils.current_crc_mode",
                                         ProductFamilies.SPR: "upi.upi0.ktils.current_crc_mode",
                                         }

            current_crc_mode = cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                                        upi_llr_crc_reg_path_dict[cscripts_obj.silicon_cpu_family])

            sdp_obj.go()
            time.sleep(self.HALT_GO_DELAY_SEC)
            if expected_crc_mode == self.CRC_32_BIT_MODE:
                if current_crc_mode == expected_crc_mode:
                    self._log.info("UPI LLR 32 Bit Rolling CRC is Enabled")
                    is_upi_llr_crc_enabled = True
                else:
                    self._log.info("UPI LLR 32 Bit Rolling CRC is Not Enabled")
            else:
                if current_crc_mode == expected_crc_mode:
                    self._log.info("UPI LLR 16 Bit Rolling CRC is Enabled")
                    is_upi_llr_crc_enabled = True
                else:
                    self._log.info("UPI LLR 16 Bit Rolling CRC is Not Enabled")

            return is_upi_llr_crc_enabled

    def get_upi_llr_kti_err_st_reg(self, field_name="mscod_code", upiport=0, action="", socket=0, cscripts_obj=None):
        """
        probably can remove the csp -- and call cscripts_obj directly
        function gathers field data from the upi_llr_kti_err_st  register

        :param cscripts_obj: Cscripts object
        :param field_name: field name to get
        :param upiport: upi port to gather data
        :param action:  clear will clear status register
        :param socket  socket to get info
        :return: field data
        """
        upi_llr_kti_err_st_reg_path_dict = {ProductFamilies.CLX: "kti" + str(upiport) + "_bios_err_st",
                                            ProductFamilies.CPX: "kti" + str(upiport) + "_bios_err_st",
                                            ProductFamilies.SKX: "kti" + str(upiport) + "_bios_err_st",
                                            ProductFamilies.ICX: "upi.upi" + str(upiport) + ".bios_kti_err_st",
                                            ProductFamilies.SPR: "upi.upi" + str(upiport) + ".bios_kti_err_st",
                                            ProductFamilies.SNR: "upi.upi" + str(upiport) + ".bios_kti_err_st"}

        if action == "clear":
            self._log.info("Clearing status register(" +
                           upi_llr_kti_err_st_reg_path_dict[cscripts_obj.silicon_cpu_family] + ") on upi " +
                           "port " + str(upiport))
            cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                     upi_llr_kti_err_st_reg_path_dict[cscripts_obj.silicon_cpu_family],
                                     socket_index=socket).write(0)
            status_reg = cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                                  upi_llr_kti_err_st_reg_path_dict
                                                  [cscripts_obj.silicon_cpu_family], socket_index=socket).get_value()
            return status_reg
        if field_name == "":
            status_reg = cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                                  upi_llr_kti_err_st_reg_path_dict
                                                  [cscripts_obj.silicon_cpu_family], socket_index=socket).get_value()
            return status_reg
        else:
            self._log.info("Getting UPI LLR field( " + field_name + ") on socket" + str(socket) +
                           " upi port " + str(upiport))
            field_data = cscripts_obj.get_field_value(scope=cscripts_obj.UNCORE,
                                                      reg_path=upi_llr_kti_err_st_reg_path_dict
                                                      [cscripts_obj.silicon_cpu_family],
                                                      field=field_name, socket_index=socket)
            return field_data

    def inject_upi_crc_err(self, socket, port, num_crcs=1, resume_procs=False, sdp=None, cscripts_obj=None):
        """
        inject error with cscripts module
        injectUpiError(self, socket, port, num_crcs=1, stopInj=False, haltFirst=True, checkEInjLock=True,
                showErrorRegs=True, direction="rx", laneNum="random", cleanErrors=None)

        :param socket:  socket to inject
        :param port: port to inject- Change port to 2 if testing on system with 3 UPI ports
        :param num_crcs:  default=1
        :param resume_procs  resume procs in this method or false wait for later in script
        :param sdp  itp object
        :param cscripts_obj cscripts object
        :return: True or False - Cscript does not give any response - so this will return True if function completes
        """
        errinj_obj = cscripts_obj.get_cscripts_utils().get_platform_module().get_ei_obj()
        try:
            self._log.info("Halting processors ...")
            sdp.halt_and_check()
            time.sleep(self.HALT_GO_DELAY_SEC)

            self._log.info("Injecting crc error - socket=" + str(socket) + " port= " + str(port))

            errinj_obj.injectUpiError(socket, port, num_crcs, showErrorRegs=False)
        except Exception as ex:
            raise content_exceptions.TestFail("Unable to inject the error due to : {}".format(ex))
        finally:
            if resume_procs:
                self._log.info("Resuming processors ...")
                sdp.go()
                time.sleep(self.HALT_GO_DELAY_SEC)

        return True

    def inject_llr_upi_port_test(self, socket_to_test="all", init=False):
        """
        tests UPI LLR crc errors - single port and multi port w and w/o phy init

        :param socket_to_test:  all will cycle thru detected sockets, specify socket otherwise
        :param init:  do a physical init(reset) after injection
        :return:
        """
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:
            if socket_to_test is "all":
                first_socket_to_test = 0
                socket_cnt = cscripts_obj.get_socket_count()
            else:
                first_socket_to_test = int(socket_to_test)
                socket_cnt = first_socket_to_test + 1
            sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
            error_delay_sec = 10
            results = []
            expected_err_cnt = '1'
            self._common_content_lib = CommonContentLib(self._log, self.os, self._cfg)

            port_count = self.hsioupi_obj.get_upi_port_count()

            # check if platform UPI ports are in a good state to run
            port_check = self._common_content_lib.check_platform_port_states(cscripts_obj, socket_cnt,
                                                                             port_count, require=True)
            if not port_check[0]:
                self._log.info("Found no Valid ports - Failing test ")
                return False
            port_count = port_check[1]

            for socket in range(first_socket_to_test, socket_cnt):
                for port in range(port_count):
                    # verify port is in a good state
                    if not self._common_content_lib.verify_port_state(cscripts_obj, socket, port):
                        self._log.info("Skipping invalid port-" + "socket" + str(socket) + " port" + str(port))
                        continue
                    self._log.info(">>>>>> Testing Socket{} port{}".format(socket, port))
                    rxeinjctl0_path_dict = {ProductFamilies.CLX: "kti" + str(port) + "_rxeinjctl0",
                                            ProductFamilies.CPX: "kti" + str(port) + "_rxeinjctl0",
                                            ProductFamilies.SKX: "kti" + str(port) + "_rxeinjctl0",
                                            ProductFamilies.ICX: "upi.upi" + str(port) + ".ktirxeinjctl0",
                                            ProductFamilies.SPR: "upi.upi" + str(port) + ".ktirxeinjctl0"
                                            }

                    self._log.info("Clearing OS logs .......")
                    self._common_content_lib.clear_all_os_error_logs()
                    self._log.info("Clear status registers...")
                    err_st_reg = self.get_upi_llr_kti_err_st_reg(field_name="", upiport=port, socket=socket,
                                                                 cscripts_obj=cscripts_obj)
                    if err_st_reg != 0:
                        self.get_upi_llr_kti_err_st_reg(field_name="", upiport=port, action="clear", socket=socket,
                                                        cscripts_obj=cscripts_obj)

                    if init:
                        self._log.info("Causing a error and physical init/reset by writing " +
                                       str(rxeinjctl0_path_dict[cscripts_obj.silicon_cpu_family])
                                       + "=0xcacb2143  on port " + str(port))

                        # physical reset via rxeinjctl register
                        before_get_reg_output = cscripts_obj.get_by_path(cscripts_obj.UNCORE, rxeinjctl0_path_dict[
                            cscripts_obj.silicon_cpu_family], socket_index=socket)
                        self._log.info(" rxeinjctl0_path returned data=" + str(before_get_reg_output) + "\n")

                        self._log.info("Halting processors ...")
                        sdp_obj.halt_and_check()
                        time.sleep(self.HALT_GO_DELAY_SEC)

                        cscripts_obj.get_by_path(cscripts_obj.UNCORE,
                                                 rxeinjctl0_path_dict[cscripts_obj.silicon_cpu_family]
                                                 , socket_index=socket).write(0xcacb2143)
                        time.sleep(error_delay_sec)

                        after_get_reg_output = cscripts_obj.get_by_path(cscripts_obj.UNCORE, rxeinjctl0_path_dict[
                            cscripts_obj.silicon_cpu_family], socket_index=socket)
                        self._log.info(" rxeinjctl0_path returned data=" + str(after_get_reg_output) + "\n")

                        expected_mscod_data = '0x31'  # LLR CRC error w PHYsical init

                    else:  # w/o PHY init
                        self._log.info("           Injecting error on port" + str(port))
                        self.inject_upi_crc_err(socket, port, num_crcs=1, sdp=sdp_obj, cscripts_obj=cscripts_obj)
                        time.sleep(error_delay_sec)

                        expected_mscod_data = 0x30  # LLR CRC error w/o PHY

                    self._log.info("Verify UPI LLR CRC transient err is detected...")
                    mscod_data = self.get_upi_llr_kti_err_st_reg(field_name="mscod_code", upiport=port, socket=socket,
                                                                 cscripts_obj=cscripts_obj)
                    mscod_data = str(mscod_data).replace("[", "").replace("]", "")

                    mscod_data = self.check_hexified(mscod_data)

                    self._log.info("mscod data= " + str(mscod_data))

                    mscod_res = mscod_data == self.check_hexified(expected_mscod_data)
                    if mscod_res:
                        self._log.info("mscod_code data was as expected")
                    else:
                        self._log.info("Unexpected mscod data=" + str(mscod_data) + " -expected " + self.check_hexified(
                            expected_mscod_data))

                    # check err cnt
                    err_cnt_data = self.get_upi_llr_kti_err_st_reg(field_name="cor_err_cnt", upiport=port,
                                                                   socket=socket, cscripts_obj=cscripts_obj)
                    err_cnt_data = str(err_cnt_data).replace("[0x", "").replace("]", "")
                    corr_err_res = err_cnt_data >= expected_err_cnt
                    if corr_err_res:
                        self._log.info("Correctable err cnt data was as expected (" + str(err_cnt_data) + ")")
                    else:
                        self._log.info(
                            "Unexpected error count data= " + str(err_cnt_data) + " -expected= " + str(expected_err_cnt))

                    self._log.info("Resuming processors ...")
                    sdp_obj.go()
                    time.sleep(self.os_error_log_delay_sec)
                    # Check for proper error message in OS logs
                    os_result = self.check_llr_os_logs(init=init)

                    results.append(mscod_res & corr_err_res & os_result)

            for port_check in results:
                if not port_check:
                    self._log.info(results)
                    return False
            self._log.info("\n                   Test passed on all ports")
            return True

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

    def set_error_threshold(self, cscripts_obj, sdp_obj, socket=0, port=0, threshold_value=0x8003):
        """
        This Function is use to set the error threshold to three.

        :param cscripts_obj
        :param sdp_obj
        :param socket
        :param port
        :param threshold_value
        :return: None
        :raise: content_exception
        """
        try:
            if not sdp_obj.is_halted():
                sdp_obj.halt()
            self._log.info("Threshold Value: {}".format(threshold_value))
            if self._common_content_lib.SILICON_10NM_CPU:
                reg_path = "upi.upi{}.kticsmithres".format(port)
                cscripts_obj.get_by_path(cscripts_obj.UNCORE, reg_path=reg_path, socket_index=socket).write(
                    threshold_value)
                set_threshold_output = cscripts_obj.get_by_path(cscripts_obj.UNCORE, reg_path=reg_path,
                                                                socket_index=socket).read()
            else:
                reg_path = "kti{}_csmithres".format(port)
                cscripts_obj.get_by_path(cscripts_obj.UNCORE, reg_path=reg_path, socket_index=socket).write(
                    threshold_value)
                set_threshold_output = cscripts_obj.get_by_path(cscripts_obj.UNCORE, reg_path=reg_path,
                                                                socket_index=socket).read()
            if set_threshold_output != threshold_value:
                self._log.error("Threshold was not set {}".format(set_threshold_output))
                raise content_exceptions.TestFail("Expected Threshold was not set")
            self._log.info("Threshold set as expected: {}".format(set_threshold_output))
        except Exception as ex:
            log_err = "An Exception Occurred during setting error threshold: {}".format(ex)
            self._log.error(log_err)
            raise log_err
        finally:
            sdp_obj.go()

    def inject_upi_error_thresh_stress(self, cscripts_obj=None, sdp_obj=None, socket=0, port=0,
                                       threshold_count=3):
        """
        This Function is use to inject upi error above threshold and verifying in OS.

        :param cscripts_obj- cscript object
        :param sdp_obj- sdp object
        :param socket
        :param port
        :param threshold_count
        :return: None
        :raise: content_exception
        """
        try:
            no_of_err_inj_after_threshold = threshold_count  # SPR-Ensure bios is set the same as threshold_cnt to pass

            ei = cscripts_obj.get_cscripts_utils().get_ei_obj()

            kticrcerrcnt_reg_path = "upi.upi{}.kticrcerrcnt".format(port)
            if not cscripts_obj.get_by_path(cscripts_obj.UNCORE, reg_path=kticrcerrcnt_reg_path, socket_index=socket):
                self._log.debug("Before injecting errors, error count is found=0 as expected")
            else:
                log_err = "Before injecting errors, error count should have been zero but found some unexpected value"
                self._log.error(log_err)
                raise content_exceptions.TestFail(log_err)
            # this effectively doubles count so we can cross threshold 2 times
            max_injection_count = threshold_count + no_of_err_inj_after_threshold

            for inject_count in range(self.INITIAL_INJECT_COUNT, max_injection_count + 1):  # add 1 because we start at 1
                self._common_content_lib.clear_all_os_error_logs()
                self._log.info("Injecting UPI error# {} - socket{}, port{}".format(str(inject_count), str(socket), str(port)))
                # Verify halt capability is functional
                sdp_obj.halt_and_check()
                sdp_obj.go()
                ei.injectUpiError(socket=socket, port=port, num_crcs=self.CRC_ERC)
                time.sleep(self.os_error_log_delay_sec)  # cscripts resumes platform and log error

                # threshold is reset after each csmi - so OS logs only show at threshold points
                if inject_count == threshold_count or inject_count == max_injection_count:
                    os_result = self._os_log_obj.verify_os_log_error_messages(
                        __file__, self._os_log_obj.DUT_JOURNALCTL_FILE_NAME,
                        self.UPI_CORRECTABLE_LINK_RETRY_WO_INIT_ERR_SIGNATURE, os_log_in_dtaf=False)
                    if not os_result:
                        self._log.error("Expected error Signature was not captured in OS")
                        raise content_exceptions.TestFail("Expected error Signature was not captured in OS")
                else:
                    os_result = self._os_log_obj.verify_os_log_error_messages(
                        __file__, self._os_log_obj.DUT_JOURNALCTL_FILE_NAME,
                        self.UPI_CORRECTABLE_LINK_RETRY_WO_INIT_ERR_SIGNATURE, check_error_not_found_flag=True,
                        os_log_in_dtaf=False)

                    if not os_result:
                        self._log.error("Error Captured in OS before reaching Threshold - injection count=" +
                                        str(inject_count))
                        raise content_exceptions.TestFail("Error Captured in OS before reaching Threshold")
                    else:
                        self._log.info("OS log did not get Injection logged in OS - as expected")

                if cscripts_obj.get_by_path(cscripts_obj.UNCORE, reg_path=kticrcerrcnt_reg_path, socket_index=socket) \
                        == inject_count:
                    self._log.debug("Injected Error count matched the expected value : {}".format(inject_count))
                else:
                    log_err = "Inject Error Count did not match the expected value : {}".format(inject_count)
                    raise content_exceptions.TestFail(log_err)

        except Exception as ex:
            log_err = "An Exception Occurred during error inject injection : {}".format(ex)
            raise content_exceptions.TestFail(log_err)

    def inject_upi_threshold_test(self, csp=None, sdp=None, stress_test=None,
                                  threshold_value=None):
        """
        This method is to inject upi threshold test.
        Currently SPR threshold is set with BIOS knob(EmcaCsmiThreshold) and csmi is only created when threshold is met
        This test will hit threshold 2 times to verify CSMIs only occur at threshold

        :param csp
        :param sdp
        :param stress_test
        :param threshold_value
        """
        # AC power Cycle to clear all errors and proceeding for other port.
        self._log.info("AC cycle platform to clear all errors")
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)

        ras_upi_util = RasUpiUtil(self.os, self._log, self._cfg, self._common_content_lib, self._args)
        # Number of socket
        socket_count = csp.get_socket_count()

        if stress_test:
            # Execute Crunch Tool
            ras_upi_util.execute_crunch_tool()
        port_count = self.hsioupi_obj.get_upi_port_count()
        # check if platform UPI ports are in a good state to run
        port_check = self._common_content_lib.check_platform_port_states(csp, socket_count,
                                                                         port_count, require=True)
        if not port_check[0]:
            self._log.info("Found no Valid ports - Failing test ")
            return False
        port_count = port_check[1]

        # To test each socket
        for each_socket in range(socket_count):
            self._log.info("Socket Number: {} has {} ports".format(each_socket, port_count))

            # To test each port
            for each_port in range(port_count):
                self._log.info("Test has started for Socket: {} and Port: {}".format(each_socket, each_port))

                # Clear OS Log
                self._common_content_lib.clear_all_os_error_logs()

                if self.product != ProductFamilies.SPR:
                    self.set_error_threshold(cscripts_obj=csp, sdp_obj=sdp, socket=each_socket, port=each_port,
                                             threshold_value=threshold_value)

                # Extract threshold value which we set.
                exact_threshold_value = threshold_value - 0x8000

                # Inject Upi error and Verify
                self.inject_upi_error_thresh_stress(cscripts_obj=csp, sdp_obj=sdp, socket=each_socket,
                                                    port=each_port, threshold_count=exact_threshold_value)

        return True  # this test depends on exceptions for failure - so assume pass if no exceptions

    def check_llr_os_logs(self, init=False):
        """
        param init:

        """
        # Check for proper error message in OS logs
        if init:
            err_signature = self.UPI_CORRECTABLE_LINK_RETRY_W_INIT_ERR_SIGNATURE
        else:
            err_signature = self.UPI_CORRECTABLE_LINK_RETRY_WO_INIT_ERR_SIGNATURE

        os_result = self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                  self._os_log_obj.DUT_JOURNALCTL_FILE_NAME,
                                                                  err_signature)
        if os_result:
            self._log.info("OS log data matched signature as expected")

        return os_result
