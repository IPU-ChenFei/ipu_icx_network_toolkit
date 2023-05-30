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
import time

from dtaf_core.lib.dtaf_constants import ProductFamilies
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.ras.lib.ras_einj_util import RasEinjCommon
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions
from src.hsio.upi.hsio_upi_common import HsioUpiCommon


class ViralCommon(ContentBaseTestCase):
    """
    This Class is used as common class for all the Viral Test Cases
    """
    TIME_SEC_BETWEEN_OS_ALIVE_PINGS = 20
    MSR_REG = 0x178
    _PCIE_UNCORRECTABLE_ERROR_STRING = "Uncorrectable error detected in uncerrsts.completion_time_out_status"
    PORT_INFO_DICT = {}
    _PCIE_PORT_INFO = {}
    _SOCKET_NUMBER = 0
    _CHECK_PORT_REGEX = "\|\s+(\d+)\s+\|\s+(\S+)\s+\|\s+(\S+)\s+\|"

    def __init__(self, test_log, arguments, cfg_opts, config=None):
        """
        Creates a new ViralCommon object

        :param test_log: Used for debug and info messages
        :param arguments:None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        if config:
            config = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), config)
        super(ViralCommon, self).__init__(test_log, arguments, cfg_opts, config)

        self._cfg = cfg_opts

        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._ras_einj_obj = RasEinjCommon(self._log, self.os, cfg_opts, self._common_content_lib,
                                           self._common_content_configuration, self.ac_power)
        self._product = self._common_content_lib.get_platform_family()
        self._pcie_common_obj = None  # PcieCommon(self._log, arguments, cfg_opts)
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
        super(ViralCommon, self).prepare()

    def check_viral_enable(self):
        """
        verify if viral is enabled after modifying the Bios Knobs

        return: True if viral is enable
        """
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        viral = False
        try:
            sdp_obj.halt()
            if sdp_obj.msr_read(self.MSR_REG)[0] & 2 ** 1:
                self._log.info("Viral Enable bit is set in MSR MS_REG")
                viral = True
            else:
                self._log.info(
                    "Viral is not enabled because IA32_MCG_CONTAIN.VIRAL_ENABLE(MSR MS_REG, bit 1) is not set")
        except Exception as ex:
            raise ex
        finally:
            sdp_obj.go()
        return viral

    def get_viral_status_and_state_registers(self):
        """
        This method returns status registers at different test points

        :return: viral_state, viral_status,upi_viral_state, upi_viral_status
        """
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:
            iio_config_path = "m2iosf0.viral_1_5_2_cfg"
            upi_config_path = "upi.upi0.ktiviral"
            viral_state = cscripts_obj.get_field_value(scope=cscripts_obj.UNCORE, reg_path=iio_config_path,
                                                       field="iio_viral_state")
            viral_status = cscripts_obj.get_field_value(scope=cscripts_obj.UNCORE, reg_path=iio_config_path,
                                                        field="iio_viral_status")
            upi_viral_state = cscripts_obj.get_field_value(scope=cscripts_obj.UNCORE, reg_path=upi_config_path,
                                                           field="kti_viral_state")
            upi_viral_status = cscripts_obj.get_field_value(scope=cscripts_obj.UNCORE, reg_path=upi_config_path,
                                                            field="kti_viral_status")
            return viral_state, viral_status, upi_viral_state, upi_viral_status

    def inject_pcie_fatal_and_verify_viral(self):
        """
        This method injects PCI Fatal Error and trigger Viral

        return: True or false
        """
        with ProviderFactory.create(self.si_dbg_cfg, self._log) as sdp_obj:
            try:
                (initial_viral_state, initial_viral_status, upi_initial_viral_state,
                 upi_initial_viral_status) = self.get_viral_status_and_state_registers()
                if initial_viral_state == 0x0 and initial_viral_status == 0x0:
                    if self.check_viral_enable():
                        self._log.info("Viral status and viral state are cleared")
                        self._log.info("Inject PCIE Uncorrectable Fatal Error")
                        self._pcie_common_obj.inject_and_verify_cscripts_pcie_error(error_type="uce")
                        (viral_state_before_reset, viral_status_before_reset, upi_viral_state_before_reset,
                         upi_viral_status_before_reset) = self.get_viral_status_and_state_registers()
                        if upi_viral_state_before_reset == 0x0 and viral_status_before_reset == 0x0:
                            self._log.info("Error Injected Successfully")
                            self._log.info("Reset the System")
                            sdp_obj.reset_target()
                            self._log.info("Check System is alive or not")
                            self.os.wait_for_os(self._common_content_configuration.get_reboot_timeout())
                            self._log.info("Check viral state and viral status")
                            (viral_state_after_reset, viral_status_after_reset, upi_viral_state_after_reset,
                             upi_viral_status_after_reset) = self.get_viral_status_and_state_registers()
                            if upi_viral_status_after_reset == 0x1 and viral_status_after_reset == 0x1:
                                self._log.info("collect os logs ")
                                if self._ras_einj_obj. \
                                        einj_check_os_log(error_type=self._ras_einj_obj.EINJ_PCIE_UNCORRECTABLE_FATAL):
                                    self._log.info("Viral Test Passed")
                                    return True
                            else:
                                self._log.info("Viral Test Failed")
                                return False
                    else:
                        log_error = "Viral State is Not Enabled after Modifying the Bios knobs"
                        self._log.error(log_error)
            except Exception as ex:
                self._log.error("Unable to Inject PCIE Fatal Error due to the Exception '{}'".format(ex))
                raise ex

    def check_upi_viral_signaling_enabled(self, csp):
        """
        This method is to check the viral is enabled or not.

        :param csp
        :raise content_exception
        """
        viral_reg_path = {ProductFamilies.SPR: "upi.upi{}.ktiviral"}
        # Total number of Socket
        no_of_socket = csp.get_socket_count()
        port_count = self.hsioupi_obj.get_upi_port_count()
        # check if platform UPI ports are in a good state to run
        port_check = self._common_content_lib.check_platform_port_states(csp, no_of_socket,
                                                                         port_count, require=True)
        if not port_check[0]:
            self._log.info("Found no Valid ports - Failing test ")
            return False
        port_count = port_check[1]
        for each_socket in range(no_of_socket):
            for each_port in range(port_count):
                reg_path = viral_reg_path[self._product].format(each_port)
                reg_output = csp.get_by_path(csp.UNCORE, reg_path, socket_index=each_socket)
                self._log.info("Output of Register: {} is {}".format(reg_path, reg_output))

                # Checking Last 3 bit
                if not reg_output and 0x7 == 0x7:
                    raise content_exceptions.TestFail("Viral bit is not enabled for socket: {} and port: {}".format(
                        each_socket, each_port))
                self._log.info("Viral bit are set as Expected for socket: {} and port: {}".format(each_socket,
                                                                                                  each_port))

        return True

    def verify_upi_viral_state_and_status_bit(self, csp):
        """
        This method is to verify viral state and viral status.

        :param csp
        :raise content_exceptions
        """
        viral_reg_path = {ProductFamilies.SPR: "upi.upi{}.ktiviral"}
        # Total number of Socket
        no_of_socket = csp.get_socket_count()
        port_count = self.hsioupi_obj.get_upi_port_count()
        # check if platform UPI ports are in a good state to run
        port_check = self._common_content_lib.check_platform_port_states(csp, no_of_socket,
                                                                         port_count, require=True)
        if not port_check[0]:
            self._log.info("Found no Valid ports - Failing test ")
            return False
        port_count = port_check[1]

        for each_socket in range(no_of_socket):
            for each_port in range(port_count):
                reg_path = viral_reg_path[self._product].format(each_port)
                reg_output = csp.get_by_path(csp.UNCORE, reg_path, socket_index=each_socket)
                self._log.info("Output of Register: {} is {}".format(reg_path, reg_output))

                # Checking Last 3 bit and 30, 31 bit
                if not reg_output >= 0xc0000007:
                    raise content_exceptions.TestFail("Viral Status and state was not found as expected for socket: {} "
                                                      "and port: {}".format(each_socket, each_port))
                self._log.info("Viral Status and state found as Expected for socket: {} and port: {}".format(each_socket,
                                                                                                  each_port))

        return True
