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
import time

from src.lib.install_collateral import InstallCollateral
from src.lib.content_configuration import ContentConfiguration
from src.lib import content_exceptions
from src.hsio.upi.hsio_upi_common import HsioUpiCommon


class RasUpiUtil(object):
    """
    This Class is Used as Ras Upi Util.
    """
    CMD_TO_START_CRUNCH_STRESS_ON_SUT = "./crunch-static-102 -e 0 -e 1 -e 2 -e 8 -e 9 -e 11 -e 13 -e 14 -e 16 -e "\
                                        "23 -e 25 -e 26 -e 28 -e 29 -e 30"
    DELAY_AFTER_REBOOT_IN_SEC = 20
    DELAY_BETWEEN_AC_POWER_POWER_CYCLE_IN_SEC = 15
    CMD_TO_CHECK_RUNNING_CRUNCH_TOOL = "ps -ef| grep crunch"

    CMD_TO_START_LIBQUANTUM_STRESS_ON_SUT = "nohup ./loop-libquantum.sh"
    CMD_TO_CHECK_RUNNING_LIBQUANTUM_TOOL = "ps -ef| grep libquantum"
    STRING_TO_CHECK_LIBQUANTUM_RUNNING = "./loop-libquantum.sh"

    CMD_TO_START_MPRIME_STRESS_ON_SUT = "./mprime -t"
    CMD_TO_CHECK_RUNNING_MPRIME_TOOL = "ps -ef| grep mprime"

    WAIT_TIME_FOR_TOOL_RUN_SEC = 10
    DELTA = 30

    def __init__(self, os_obj, log, cfg_opts, common_content_lib, arguments=None):
        self._os = os_obj
        self._log = log
        self._common_content_lib = common_content_lib
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts=cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_time = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        if arguments:
            self.hsioupi_obj = HsioUpiCommon(log, arguments, cfg_opts)

    def ac_cycle_if_os_not_alive(self, ac_obj, auto_reboot_expected=False):
        """
        If auto reboot is expected, then wait for SUT to respond
        If auto reboot is not expected, then check and forcefully power cycle SUT
        :param auto_reboot_expected:   True or False
        :raise: Exception if system will not respond.
        :return: None
        """
        try:
            if auto_reboot_expected is True:
                self._log.info("Ensure system is alive within (%d) seconds...", self._reboot_time)
                count = int(self._reboot_time / self.DELTA)
                for x in range(count):
                    time.sleep(self.DELTA)
                    if self._os.is_alive():
                        self._log.info("OS responded successfully")
                        return
                    else:
                        self._log.info("OS has not yet responded. Retrying...")

            self._log.info("Checking OS has responded or not...")
            # Check if system is alive or not
            # Power cycle system if not alive and wait till system becomes alive
            time.sleep(self.DELAY_BETWEEN_AC_POWER_POWER_CYCLE_IN_SEC)
            if self._os.is_alive():
                self._log.info("OS responded successfully")
            else:
                self._log.info("OS failed to respond. AC cycling...")
                self._common_content_lib.perform_graceful_ac_off_on(ac_power=ac_obj)
                self._os.wait_for_os(self._reboot_time)
                time.sleep(self.DELAY_AFTER_REBOOT_IN_SEC)

        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def execute_crunch_tool(self):
        """
        This Method to install crunch tool and execute it.
        :raise content_exception.
        """
        crunch_tool_path = self._install_collateral.install_crunch_tool()
        self._log.info("Crunch tool path: {}".format(crunch_tool_path))
        self._os.execute_async(self.CMD_TO_START_CRUNCH_STRESS_ON_SUT, crunch_tool_path)

        # Wait time for tool run
        time.sleep(self.WAIT_TIME_FOR_TOOL_RUN_SEC)

        crunch_stress_output = self._common_content_lib.execute_sut_cmd(
            sut_cmd=self.CMD_TO_CHECK_RUNNING_CRUNCH_TOOL, cmd_str=self.CMD_TO_CHECK_RUNNING_CRUNCH_TOOL,
            execute_timeout=self._command_timeout)
        self._log.info("{} output to check crunch tool is running or not : {}".format(
            self.CMD_TO_CHECK_RUNNING_CRUNCH_TOOL, crunch_stress_output))
        if self.CMD_TO_START_CRUNCH_STRESS_ON_SUT not in crunch_stress_output:
            raise content_exceptions.TestFail("Crunch tool is not executing")
        self._log.info("Crunch Tool Successfully Started")

    def inject_and_check_kti_crc_err_cnt(self, csp, num_crcs_value, inject_error=False):
        """
        This method is to check kti crc err cnt.
        :param csp
        :param num_crcs_value
        :param inject_error - True if need to inject the error else False.
        :return True or False
        """
        ei_obj = csp.get_cscripts_utils().get_ei_obj()
        no_of_socket = csp.get_socket_count()
        for each_socket in range(no_of_socket):

            #  To get number of port
            no_of_port = self.hsioupi_obj.get_upi_port_count()
            for each_port in range(no_of_port):
                if inject_error:
                    #  Inject CRC CE error on each socket and port
                    ei_obj.injectUpiError(socket=each_socket, port=each_port, num_crcs=num_crcs_value)

                #  kticrcerrcnt should be equal to num_crcs value if error injected else 0.
                kticrcerrcnt_value = csp.get_by_path(csp.UNCORE, "upi.upi{}.kticrcerrcnt".format(
                    each_port), socket_index=each_socket)
                if not kticrcerrcnt_value == num_crcs_value:
                    self._log.error("kticrcerrcnt: {} for socket: {} and port: {} is not correct. Expected value is: {}"
                                                      "".format(kticrcerrcnt_value, each_socket, each_port,
                                                                num_crcs_value))
                    return False
                self._log.info("kticrcerrcnt: {} for socket: {} and port: {} is found as expected"
                               "".format(kticrcerrcnt_value, each_socket, each_port))
        return True

    def install_libquantum_tool(self):
        """
        This Method to install libquantum tool.
        :return: libquantum_tool_path
        """
        libquantum_tool_path = self._install_collateral.install_libquantum_tool()
        self._log.info("Libquantum tool path: {}".format(libquantum_tool_path))
        return libquantum_tool_path

    def execute_libquantum_tool(self, libquantum_tool_path):
        """
        This Method is to execute Libquantum tool.
        :param: libquantum_tool_path: tool path on SUT
        :raise content_exception.
        """
        self._os.execute_async(self.CMD_TO_START_LIBQUANTUM_STRESS_ON_SUT, libquantum_tool_path)

        # Wait time for tool run
        time.sleep(self.WAIT_TIME_FOR_TOOL_RUN_SEC)

        Libquantum_stress_output = self._common_content_lib.execute_sut_cmd(
            sut_cmd=self.CMD_TO_CHECK_RUNNING_LIBQUANTUM_TOOL, cmd_str=self.CMD_TO_CHECK_RUNNING_LIBQUANTUM_TOOL,
            execute_timeout=self._command_timeout)
        self._log.info("{} output to check Libquantum tool is running or not : {}".format(
            self.CMD_TO_CHECK_RUNNING_LIBQUANTUM_TOOL, Libquantum_stress_output))
        if self.STRING_TO_CHECK_LIBQUANTUM_RUNNING not in Libquantum_stress_output:
            raise content_exceptions.TestFail("Libquantum tool is not executing")
        self._log.info("Libquantum Tool Successfully Started")

    def install_mprime_tool(self):
        """
        This Method to install mprime tool.
        :return: mprime_tool_path
        """
        mprime_tool_path = self._install_collateral.install_mprime_tool()
        self._log.info("mprime tool path: {}".format(mprime_tool_path))
        return mprime_tool_path

    def execute_mprime_tool(self, mprime_tool_path):
        """
        This Method is to execute mprime tool.
        :param: mprime_tool_path: tool path
        :raise content_exception.
        """
        self._os.execute_async(self.CMD_TO_START_MPRIME_STRESS_ON_SUT, mprime_tool_path)

        # Wait time for tool run
        time.sleep(self.WAIT_TIME_FOR_TOOL_RUN_SEC)

        mprime_stress_output = self._common_content_lib.execute_sut_cmd(
            sut_cmd=self.CMD_TO_CHECK_RUNNING_MPRIME_TOOL, cmd_str=self.CMD_TO_CHECK_RUNNING_MPRIME_TOOL,
            execute_timeout=self._command_timeout)
        self._log.info("{} output to check mprime tool is running or not : {}".format(
            self.CMD_TO_CHECK_RUNNING_MPRIME_TOOL, mprime_stress_output))
        if self.CMD_TO_START_MPRIME_STRESS_ON_SUT not in mprime_stress_output:
            raise content_exceptions.TestFail("mprime tool is not executing")
        self._log.info("mprime Tool Successfully Started")
