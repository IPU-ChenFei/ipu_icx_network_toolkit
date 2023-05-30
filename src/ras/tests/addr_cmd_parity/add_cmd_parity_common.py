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
import time

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.ras.lib.ras_common_utils import RasCommonUtil
from src.ras.lib.os_log_verification import OsLogVerifyCommon


class AddrCommon(BaseTestCase):
    """
    This Class is Used as Common Class For all the Addr Command parity Test Cases
    """
    _TIME_SLEEP_IN_SEC = 10
    _LOG_FILE_PATH = "log_file_path.log"

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts,
            bios_config_file
    ):
        """
        Create an instance of sut os provider, BiosProvider, SiliconDebugProvider, SiliconRegProvider
         BIOS util and Config util,

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(
            AddrCommon,
            self).__init__(
            test_log,
            arguments,
            cfg_opts)
        self._cfg = cfg_opts
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider

        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, bios_config_file)

        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._ras_common = RasCommonUtil(self._log, self._os, cfg_opts, self._common_content_configuration,
                                         self._bios_util)
        self._ei = self._cscripts.get_cscripts_utils().get_ei_obj()
        self._klaxon = self._cscripts.get_klaxon_object()

        self._os_log_obj = OsLogVerifyCommon(self._log, self._os, self._common_content_configuration,
                                             self._common_content_lib)

    def is_cap_enabled(self):
        """
        This function verify the cap function is enabled are not by checking the read register value

        :return: Boolean (True or false)- True if enable and False if not.
        """
        try:
            is_cap_enabled = False
            platform = self._common_content_lib.get_platform_family()
            mu = self._cscripts.get_xnm_memicals_utils_object()
            self._sdp.halt()
            if platform in self._common_content_lib.SILICON_14NM_FAMILY:
                popChList = mu.getPopChList()
                cap_en = 0
                for popCh in popChList:
                    #  checking the read register value
                    chknBit = popCh.sktObj.uncore0.readregister("imc%d_c%d_mc0_dp_chkn_bit" % (popCh.mc, popCh.ch))
                    if not cap_en:
                        cap_en = chknBit.en_rdimm_par_err_log
                    #  Checking the cmd address consistency on the system
                    elif cap_en != chknBit.en_rdimm_par_err_log:
                        self._log.error("Command Address Parity set inconsistently on system!")
                        self._log.error("%s.%s.en_rdimm_par_err_log=%d" % (
                        popCh.sktObj._name, chknBit.name, chknBit.en_rdimm_par_err_log))
                        raise Exception("Command Address Parity set inconsistently on system!")

                    if chknBit.dis_rdimm_par_chk:
                        self._log.warning("RDIMM parity checking is disabled through %s.%s.dis_rdimm_par_chk=1" % (
                        popCh.sktObj._name, chknBit.name))
                        is_cap_enabled = True

                    ddr4_ca_ctl = popCh.sktObj.uncore0.readregister("imc%d_c%d_ddr4_ca_ctl" % (popCh.mc, popCh.ch))
                    if cap_en != ddr4_ca_ctl.erf_en0:

                        self._log.info("%s.%s.erf_en0=%d is not set the same as %s.en_rdimm_par_err_log=%d." % (
                        popCh.sktObj._name, ddr4_ca_ctl.name, ddr4_ca_ctl.erf_en0, chknBit.name, chknBit.en_rdimm_par_err_log))
                        self._log.info("CA Parity is not setup correctly in the system")
                        is_cap_enabled = True
                return not is_cap_enabled
            else:
                for pop_ch in mu.get_pop_ch_list():
                    chkn_bit = pop_ch.regs.mc0_dp_chkn_bit.read()

                    if not is_cap_enabled:
                        is_cap_enabled = int(chkn_bit.en_rdimm_par_err_log)
                    elif is_cap_enabled != int(chkn_bit.en_rdimm_par_err_log):
                        self._log.error("Command Address Parity set inconsistently on system!")
                        self._log.error("%s.en_rdimm_par_err_log=%d" % (chkn_bit.path, chkn_bit.en_rdimm_par_err_log))
                        raise Exception("Command Address Parity set inconsistently on system!")

                    if chkn_bit.dis_rdimm_par_chk:
                        # MEB - changed to warning as this is not an error if UDIMMs are populated
                        # if the disable is set, return 0 and log the error.
                        self._log.warning("RDIMM parity checking is disabled through %s.dis_rdimm_par_chk=1" % chkn_bit.path)
                        is_cap_enabled = False

                    # check the ddr4_ca_ctl:
                    ddr4_ca_ctl = pop_ch.regs.ddr4_ca_ctl.read()

                    if ("ddrt" in pop_ch.dimm_dict.keys() or "ddrt2" in pop_ch.dimm_dict.keys()) and len(
                            pop_ch.dimm_dict) == 1:
                        enable_erf = 0
                    else:
                        enable_erf = 1
                    if int(ddr4_ca_ctl.erf_en0) != enable_erf:
                        # MEB - changed to warning as this is not an error if UDIMMs are populated
                        self._log.warning("%s.erf_en0=%d is not set the same as" % (ddr4_ca_ctl.path, ddr4_ca_ctl.erf_en0))
                        self._log.warning("%s.en_rdimm_par_err_log=%d." % (chkn_bit.path, chkn_bit.en_rdimm_par_err_log))
                        self._log.warning("CA Parity is not setup correctly in the system")
                        is_cap_enabled = False

                return is_cap_enabled
        except Exception as ex:
            log_err = "An Exception Occurred : {}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

        finally:
            self._log.info("Resume the Machine")
            self._sdp.go()

    def show_alert_seen(self, socket=None, mc=None, ch=None):
        """
        This Function is to check the status of the injected error has seen or not.

        :param socket: Socket Number
        :param mc: Memory Controller
        :param ch: Channel Number
        :return: True if alert seen is visible else False.
        :raise: RuntimeError
        """
        try:
            product = self._common_content_lib.get_platform_family()
            mu = self._cscripts.get_xnm_memicals_utils_object()
            self._log.info("Check Alert Status:")
            self._sdp.halt()
            if product in self._common_content_lib.SILICON_14NM_FAMILY:
                popChList = mu.getPopChList(socket=socket, mc=mc, ch=ch)
                alertSeen = False
                for popCh in popChList:
                    alertSignal = popCh.sktObj.uncore0.readregister("imc%d_c%d_alertsignal" % (popCh.mc, popCh.ch))
                    alertSeen |= alertSignal.seen
                    if alertSignal:
                        self._log.info("Alert Found : %s " % popCh._name)
                        alerSeen = True
                if not alertSeen:
                    self._log.info(" No alerts seen")
            else:
                self._log.info("Check Alert Status:")
                alertSeen = False
                for pop_ch in mu.get_pop_ch_list():
                    alertSeen = pop_ch.regs.alertsignal.read()
                    alertSeen |= alertSeen.seen
                    if alertSeen:
                        self._log.info("  %s saw Alert" % pop_ch.name)
                if not alertSeen:
                    self._log.error("  No alerts seen")

            return alertSeen
        except Exception as ex:
            log_err = "An Exception occurred {}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

        finally:
            self._log.info("Resume the Machine")
            self._sdp.go()

    def inject_ca_parity(self):
        """
        This Function is to inject CA Parity.

        return: True if error injected else False
        raise: RuntimeError if any exception occurred while executing itp command.
        """
        try:
            product = self._common_content_lib.get_platform_family()
            self._log.info("Halt the System")
            self._sdp.halt()
            if product in self._common_content_lib.SILICON_14NM_FAMILY:
                self._ei.injectCAParity(socket=1, channel=1)
            else:
                self._ei.injectCMDParity(socket=0, channel=0)
            inject_parity = False
            if product in self._common_content_lib.SILICON_14NM_FAMILY:
                if self.show_alert_seen():
                    self._log.info("CA Parity Error Injection is successful")
                    self._log.info("Doing MCA Check")
                    time.sleep(self._TIME_SLEEP_IN_SEC)
                    self._log.info("Execute the check mem error itp Command")
                    self._sdp.start_log(self._LOG_FILE_PATH, "w")
                    self._sdp.halt()
                    self._klaxon.m2mem_errors()
                    self._sdp.stop_log()
                    time.sleep(self._common_content_configuration.itp_halt_time_in_sec())
                    with open(self._LOG_FILE_PATH, "r") as log_file:
                        log_file_list = log_file.readlines()
                        self._log.info("The Log Error are {}".format("".join(log_file_list)))
                    self._log.info("The Log Error are: {}".format(log_file_list))
                    inject_parity = True
                else:
                    log_err = "CA Parity Error Injection is not happen"
                    self._log.error(log_err)
                    raise RuntimeError(log_err)
            else:
                self._sdp.start_log(self._LOG_FILE_PATH, "w")
                self._sdp.halt()
                self._klaxon.check_mem_errors()
                self._sdp.stop_log()
                time.sleep(self._common_content_configuration.itp_halt_time_in_sec())
                with open(self._LOG_FILE_PATH, "r") as log_file:
                    log_file_list = log_file.readlines()
                    self._log.info("The Log Error are {}".format("".join(log_file_list)))
                inject_parity = True

            return inject_parity
        except Exception as ex:
            log_err = "Exception Occurred : {}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

        finally:
            self._log.info("Resume the Machine")
            self._sdp.go()
