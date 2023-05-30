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

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.ras.lib.ras_common_utils import RasCommonUtil
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration


class WriteCRCCommon(BaseTestCase):
    """
    This Class is Used as Common Class For all the Write CRC Functionality Test Cases
    """
    _FILE_NAME = "CSCRIPTS_LOG_FILE.txt"
    WRITE_CRC_TRANSIENT_ERROR_CMDS_LIST = [
        "Hardware Error",
        "event severity: corrected",
        "Corrected error",
        "corrected Socket memory error count exceeded threshold",
        "corrected DIMM memory error count exceeded threshold"
    ]

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
            WriteCRCCommon,
            self).__init__(
            test_log,
            arguments,
            cfg_opts)
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
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self.err_inj_dict = {ProductFamilies.SKX: "self._cscripts.get_ecc_error_injection_object().SKXerrinj()",
                             ProductFamilies.CLX: "self._cscripts.get_ecc_error_injection_object().CLXerrinj()",
                             ProductFamilies.CPX: "self._cscripts.get_ecc_error_injection_object().CPXerrinj()",
                             ProductFamilies.ICX: "self._cscripts.get_ecc_error_injection_object()",
                             ProductFamilies.SNR: "self._cscripts.get_ecc_error_injection_object()",
                             ProductFamilies.SPR: "self._cscripts.get_ecc_error_injection_object()",
                             }
        self.err_inj_obj = self.err_inj_dict[self._cscripts.silicon_cpu_family]
        self._mu = self._cscripts.get_xnm_memicals_utils_object()
        self._ei = self._cscripts.get_cscripts_utils().get_ei_obj()
        self._log_file_path = self.get_cscripts_log_file()
        self._uncore_info = self._cscripts.get_cscripts_utils().get_uncoreinfo_obj()
        self._os_log_verify = OsLogVerifyCommon(self._log, self._os, self._common_content_configuration,
                                                self._common_content_lib)

    def get_cscripts_log_file(self):
        """
        We are getting the Path for Cscripts Log file

        :return: log_file_path
        """
        cur_path = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(cur_path, self._FILE_NAME)
        return path

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the Bios knobs are Updated Properly.

        :return: None
        """
        self._common_content_lib.clear_all_os_error_logs()  # This Method is used to Clear All OS Logs.
        self._log.info("Set the Bios Knobs to Default Settings")
        self._bios.default_bios_settings()  # To set the Bios Knobs to its default mode.
        self._log.info("Set the Bios Knobs as per our Test Case Requirements")
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._log.info("Bios Knobs are Set as per our TestCase and Reboot to Apply the Settings")
        self._os.reboot(int(self._reboot_timeout))  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

    def verify_write_crc_transient_alert_occurred(self):
        """
        This Method is used to verify if Write CRC Transient Alert Occured after error is Injected

        :return: alert_seen
        """
        alert_seen = False
        self._sdp.halt()
        if self._cscripts.silicon_cpu_family in self._common_content_lib.SILICON_14NM_FAMILY:
            pop_ch_list = self._mu.getPopChList(socket=0, mc=1)
        else:
            pop_ch_list = self._mu.get_pop_ch_list(socket=0, mc=1)
        for pop_ch in pop_ch_list:
            if self._cscripts.silicon_cpu_family in self._common_content_lib.SILICON_14NM_FAMILY:
                alert_signal = pop_ch.sktObj.uncore0.readregister("imc%d_c%d_alertsignal" % (pop_ch.mc, pop_ch.ch))
            else:
                alert_signal = pop_ch.regs.alertsignal.read()
            alert_seen |= alert_signal.seen
            if alert_signal:
                self._log.info(" %s saw Alert" % pop_ch._name)
                alert_seen = True
            if not alert_seen:
                self._log.info(" No alerts seen")
            self._log.info("")
            return alert_seen

    def verify_wrcrc_is_enabled(self):
        """
        This Method is used to verify if Write CRC is enabled or not through Bios Settings

        :return:
        """
        wrcrc_enable_status = False
        self._log.info("Verify if Write CRC is enabled")
        self._sdp.halt()
        if self._cscripts.silicon_cpu_family in self._common_content_lib.SILICON_14NM_FAMILY:
            if eval(self.err_inj_obj)._isWriteCRCEnabled(socket=0, mc=0, ch=0):
                self._log.info("Write CRC is Enabled Successfully")
                wrcrc_enable_status = True
            else:
                self._log.error("Write CRC is Not enabled")
        elif self._cscripts.silicon_cpu_family in self._common_content_lib.SILICON_10NM_CPU:
            if eval(self.err_inj_obj).is_wrcrc_enabled():
                self._log.info("Write CRC is Enabled Successfully")
                wrcrc_enable_status = True
            else:
                self._log.error("Write CRC is Not enabled")
        else:
            raise NotImplementedError("Not Implemented for this Platform")
        self._sdp.go()
        return wrcrc_enable_status

    def inject_write_crc_transient_error(self):
        """
        This Method is used to Inject the Write CRC Transient Error after Write CRC is enabled through Bios Knobs.

        :return:
        """
        try:
            ras_sku = self._uncore_info.skuinfo.get_ras_level(0)
            self._log.info("RAS Sku is %s" % ras_sku)
            self._sdp.halt()
            self._sdp.start_log(self._log_file_path, "w")
            if self._cscripts.silicon_cpu_family in self._common_content_lib.SILICON_14NM_FAMILY:
                if eval(self.err_inj_obj)._isWriteCRCEnabled(socket=0, mc=1, ch=0):
                    self._log.info("Write CRC is enabled")
                    eval(self.err_inj_obj).injectWriteCRC(socket=0, mc=1, ch=0)
                    self._sdp.stop_log()
                else:
                    self._log.error("Write CRC is not Enabled")
                    return False
            else:
                if eval(self.err_inj_obj).is_wrcrc_enabled():
                    self._log.info("Write CRC is enabled")
                    self._ei.injectWriteCRC(socket=0, mc=1, ch=0)
                    self._sdp.stop_log()
                else:
                    self._log.error("Write CRC is not Enabled")
                    return False

            with open(self._log_file_path, "r") as log_file:
                log_file_list = log_file.readlines()
                self._log.info("".join(log_file_list))
                if "Error injection is successful" in "".join(log_file_list):
                    self._log.info("WrCrc Error Injection is Successful")
                else:
                    self._log.error("WrCrc Error is Not Injected")
                    return False

            if self.verify_write_crc_transient_alert_occurred():
                self._log.info("ALERT signal asserted")
                self._log.info("Error injection is successful!")

                if not self._os.is_alive():
                    self._os.wait_for_os(self._reboot_timeout)
                if self._os_log_verify.verify_os_log_error_messages(__file__,
                                                                    self._os_log_verify.DUT_MESSAGES_FILE_NAME,
                                                                    self.WRITE_CRC_TRANSIENT_ERROR_CMDS_LIST):
                    return True
                return False
            else:
                return False

        except Exception as ex:
            self._log.error("Unable to Inject Write CRC Transient Error due to the Exception '{}'".format(ex))
            raise Exception(ex)
