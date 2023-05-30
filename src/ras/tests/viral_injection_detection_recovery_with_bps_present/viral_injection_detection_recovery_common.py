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

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.console_log import ConsoleLogProvider
from src.provider.ipmctl_provider import IpmctlProvider

from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.ras.lib.ras_common_utils import RasCommonUtil
from dtaf_core.lib.dtaf_constants import ProductFamilies
from src.ras.lib.ras_einj_util import RasEinjCommon


class ViralInjectionDetectionRecoveryCommon(BaseTestCase):
    """
    Glasgow_id : 60851

    Viral alert is a method of providing enhanced error containment in case of fatal errors using the viral alert bit
    in Intel UPI packet headers. Viral is propagated to all sockets and I/O entities for containment and reporting.

    """

    _PCIE_ID = 5375
    _SDP_LOG_FILE_NAME = "cscripts_command_output.log"
    _REGEX_CMD_FOR_VIRAL_INTERRUPT = r"Viral Interrupt Received : (\S+\s+\S+)"
    _REGEX_CMD_FOR_VIRAL_POLICY_ENABLE = r"Viral Policy Enable :"
    _REGEX_CMD_FOR_VIRAL_STATUS = r"Viral Status :"
    _IPMCTL_CMD_FOR_VIRAL_STATUS = "ipmctl show -d ViralPolicy,ViralState -dimm"
    _CHECK_VIRAL_INTERRUPT_RECEIVED_STRING = "Viral Interrupt Received"
    _CHECK_VIRAL_INTERRUPT_NOT_RECEIVED_STRING = "Not Received"
    _CHECK_NOT_VIRAL_STRING = ["Not Viral","False"]
    _CHECK_VIRAL_STRING = ["Viral","True"]
    _CHECK_FALSE_POLICY_STRING = "False"
    _CHECK_TRUE_POLICY_STRING = "True"
    _VIRAL_POLICY_STRING = "ViralPolicy"
    _VIRAL_STATE_STRING = "ViralState"

    def __init__(self, test_log, arguments, cfg_opts, config):
        """
        Creates a new ViralInjectionDetectionRecoveryCommon object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(ViralInjectionDetectionRecoveryCommon, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self._nvd = self._cscripts.get_cscripts_nvd_object()
        self._klaxon = self._cscripts.get_cscripts_utils().get_klaxon_obj()
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, config)
        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)

        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout_in_sec = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()

        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_obj = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider

        self._wait_time_in_sec = self._common_content_configuration.itp_halt_time_in_sec()
        self._os_time_out_in_sec = self._common_content_configuration.os_full_ac_cycle_time_out()
        self._einj_util = RasEinjCommon(self._log, self._os, cfg_opts, self._common_content_lib,
                                        self._common_content_configuration)
        self._ipmctl_provider = IpmctlProvider.factory(test_log, self._os, execution_env="os",cfg_opts=cfg_opts)
        self._ras_common_obj = RasCommonUtil(self._log, self._os, cfg_opts, self._common_content_configuration,
                                             self._bios_util)

    def get_viral_policy_of_dimms(self):
        """This method captures cscripts log by executing get_viral_policy() and returns the viral policy
        and viral status by parsing the log file

        :return: viral_policy, viral_status
        """
        viral_policy = ""
        viral_status = ""

        self._sdp.start_log(self._SDP_LOG_FILE_NAME)
        self._nvd.dimms[0].get_viral_policy()
        self._sdp.stop_log()
        logfile = os.path.abspath(self._SDP_LOG_FILE_NAME)
        viral_file_header = open(logfile, "r")
        viral_policy_data = viral_file_header.readlines()
        for each in viral_policy_data:
            if self._REGEX_CMD_FOR_VIRAL_POLICY_ENABLE in each:
                viral_policy = each.split(":")[1].strip()
            if self._REGEX_CMD_FOR_VIRAL_STATUS in each:
                viral_status = each.split(":")[1].strip()
        viral_file_header.close()
        os.remove(logfile)
        if viral_policy == "" or viral_status == "":
            self._log.error("Unable to get Viral Policy")
            raise RuntimeError("Failed to run get_viral_policy() in cscripts")
        return viral_policy, viral_status

    def get_smart_info_of_dimms(self):
        """
        This method captures cscripts log by executing get_smart_info() and returns the viral interrupt
        and viral status by parsing the log file

        :return: Viral_interrupt value
        """
        viral_interrupt = ""
        self._sdp.start_log(self._SDP_LOG_FILE_NAME)
        self._nvd.dimms[0].get_smart_info()
        self._sdp.stop_log()
        logfile = os.path.abspath(self._SDP_LOG_FILE_NAME)
        viral_file_header = open(logfile, "r")
        viral_policy_data = viral_file_header.readlines()
        for each in viral_policy_data:
            if re.match(self._REGEX_CMD_FOR_VIRAL_INTERRUPT , each.strip()):
                viral_interrupt = re.match(self._REGEX_CMD_FOR_VIRAL_INTERRUPT, each.strip()).group(1)
                self._log.info("Viral Interrupt Received : {}".format(viral_interrupt))
        viral_file_header.close()
        os.remove(logfile)
        if viral_interrupt == "":
            self._log.error("Unable to get smart info")
            raise RuntimeError("Failed to run get_smart_info() in cscripts")
        return viral_interrupt

    def get_dimms_list(self):
        """
        This method checks if the all DCPMM DIMMs are enabled or not .

        :returns True if enabled else false
        """
        ret_value = True
        self._sdp.start_log(self._SDP_LOG_FILE_NAME)
        self._nvd.show_list()
        self._sdp.stop_log()
        logfile = os.path.abspath(self._SDP_LOG_FILE_NAME)
        file_header = open(logfile, "r")
        dimms_list = file_header.readlines()
        for each in dimms_list:
            if "dimm" in each:
                if str(each.split("|")[9].strip()) == "Enabled":
                    continue
                else:
                    ret_value = False
        file_header.close()
        os.remove(logfile)
        if not ret_value:
            self._log.error("DIMMS not in Enabled State!")
            raise RuntimeError("Dimms not enabled in show dimms!")
        return ret_value

    def verify_viral_injection_detection_recovery_with_bps_present(self):
        """
        This method returns status registers at different test points

        :return: viral_state, viral_status,upi_viral_state, upi_viral_status
        """
        try:
            ret_val = True
            # # Check that /var/log/messages file is empty and dmesg command does not give any output
            self._common_content_lib.clear_os_log()
            self._common_content_lib.clear_dmesg_log()
            # Make sure your SUT has PCIE card installed and detected
            self._log.info("Make sure SUT has PCIE card Installed and Detected")
            if self._common_content_lib.detect_pcie_card_on_linux_sut(self._PCIE_ID):
                self._log.info("PCIE card Detected!")
                self._log.info("Make sure DIMMs are Detected!")
                if self._common_content_lib.detect_dimms_on_linux_sut():
                    self._log.info("DIMMs Detected!")
                    self._log.info("Make sure there is no uncorrectable errors oe Memory errors logged")
                    if self._cscripts.silicon_cpu_family in [ProductFamilies.ICX, ProductFamilies.SNR,
                                                             ProductFamilies.SPR]:
                        self._klaxon.check_sys_errors()
                        self._klaxon.check_mem_errors()
                    if self._cscripts.silicon_cpu_family in [ProductFamilies.CLX, ProductFamilies.SKX,
                                                             ProductFamilies.CPX]:
                        self._klaxon.m2mem_errors()
                    self._log.info("Clear System error log through CScripts.")
                    self._sdp.itp.cv.resetbreak = 1
                    self._sdp.itp.resettarget()
                    self._nvd.dimms[0].clear_history()
                    self._sdp.itp.cv.resetbreak = 0
                    self._sdp.halt()
                    self._sdp.go()
                    self._os.wait_for_os(self._os_time_out_in_sec)
                    self._log.info("Check that all the DIMMs have the Viral Policy and Viral State set Properly")
                    if not self._ipmctl_provider.get_viral_status_of_dcpmm_dimms():
                        self._log.error("Viral Status and Viral Policy of DIMMS are not Set Properly!")
                        ret_val = False
                    viralpolicy, viralstatus = self.get_viral_policy_of_dimms()
                    if viralpolicy == self._CHECK_FALSE_POLICY_STRING and viralstatus in self._CHECK_VIRAL_STRING:
                        self._log.error("Viral Policy and Viral Status are not set properly!")
                        ret_val = False
                    viralinterrupt = self.get_smart_info_of_dimms()
                    if viralinterrupt == self._CHECK_VIRAL_INTERRUPT_RECEIVED_STRING:
                        self._log.error("Viral Interrupt Received is not False!")
                        ret_val = False
                    self._log.info("Injecting Viral PCIE Uncorrectable Fatal error")
                    self._einj_util.einj_inject_and_check(error_type=self._einj_util.EINJ_PCIE_UNCORRECTABLE_FATAL,
                                                          viral=True)
                    viralinterrupt = self.get_smart_info_of_dimms()
                    if viralinterrupt == self._CHECK_VIRAL_INTERRUPT_NOT_RECEIVED_STRING:
                        self._log.error("Viral Interrupt Received is Not True after Injection!")
                        ret_val = False
                    viralpolicy, viralstatus = self.get_viral_policy_of_dimms()
                    if viralpolicy == self._CHECK_FALSE_POLICY_STRING and viralstatus in self._CHECK_VIRAL_STRING:
                        self._log.error("Viral Policy and Viral Status are not set properly after reset!")
                        ret_val = False
                    self._log.info("Warm reset the system!")
                    self._sdp.itp.cv.resetbreak = 1
                    self._sdp.itp.resettarget()
                    self._sdp.itp.cv.resetbreak = 0
                    self._sdp.halt()
                    self._sdp.go()
                    self._os.wait_for_os(self._os_time_out_in_sec)
                    viralinterrupt = self.get_smart_info_of_dimms()
                    if viralinterrupt == self._CHECK_VIRAL_INTERRUPT_NOT_RECEIVED_STRING:
                        self._log.error("Viral Interrupt Received is Not True after reset!")
                        ret_val = False
                    viralpolicy, viralstatus = self.get_viral_policy_of_dimms()
                    if viralpolicy == self._CHECK_FALSE_POLICY_STRING and viralstatus in self._CHECK_VIRAL_STRING:
                        self._log.error("Viral Policy and Viral Status are not set properly after reset!")
                        ret_val = False
                    self._log.info("Cold reset the system")
                    self._ac_obj.ac_power_off(self._common_content_configuration.ac_power_off_wait_time())
                    self._log.info("powering on!!")
                    self._ac_obj.ac_power_on(self._common_content_configuration.ac_power_off_wait_time())
                    self._log.info("Cold reset done!")
                    self._os.wait_for_os(self._reboot_timeout_in_sec)
                    viralinterrupt = self.get_smart_info_of_dimms()
                    if viralinterrupt == self._CHECK_VIRAL_INTERRUPT_RECEIVED_STRING:
                        self._log.error("Viral Interrupt Received is not False after cold reset!")
                        ret_val = False
                    dimms_enabled_check = self.get_dimms_list()
                    if not dimms_enabled_check:
                        self._log.error("Dimms Not Enabled!")
                        ret_val = False
                    self._common_content_lib.collect_all_logs_from_linux_sut()
                    errortype = self._einj_util.EINJ_PCIE_UNCORRECTABLE_FATAL
                    check_os_log_success = self._einj_util.einj_check_os_log(errortype)
                    if not check_os_log_success:
                        self._log.error("Failed to find the appropriate OS logs after error injection!")
                        ret_val = False
                    return ret_val
                else:
                    self._log.error("No DIMMs in the SUT!")
                    return False
            else:
                self._log.error("No PCIE Card detected in the System!")
                return False
        except Exception as ex:
            log_err = "Exception Occurred : {}".format(ex)
            self._log.error(log_err)
            raise log_err
