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

import sys
import os
from src.lib.content_base_test_case import ContentBaseTestCase
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from dtaf_core.lib.dtaf_constants import ProductFamilies


class VerifyTransientWrDataCRCError(ContentBaseTestCase):
    """
    HPALM ID : 81514
    phoneix Id: 18014074622 : "PI_RAS_TransientWrDataCRCErrorUsingCScripts_S_MEM08_L"
    This test verifies Transient WR CRC Data Error using Cscripts

    :return:  True if pass, False if not
    """
    _bios_knobs_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Wr_CRC_Data_Error_bios_knobs.cfg")
    DMESG_SIG = ["Hardware Error", "event severity: corrected", "section_type: memory error",
                 "Error 0, type: corrected"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new TransientWrDataCRCError object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyTransientWrDataCRCError, self).__init__(test_log, arguments, cfg_opts, self._bios_knobs_file)
        self._os_log_verification_obj = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration,
                                                          self._common_content_lib)
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        # Getting the mc, socket and channel from configuration
        self.mc_number = self._common_content_configuration.get_memory_micro_controller()
        self.socket_number = self._common_content_configuration.get_memory_socket()
        self.channel_number = self._common_content_configuration.get_memory_channel()

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

        super(VerifyTransientWrDataCRCError, self).prepare()

    def execute(self):
        """
        This Method is used to execute the method injectWriteCRC to inject wrcrc Transient Error.

        :return: True if test case is Pass else False
        """
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        csp = ProviderFactory.create(self.sil_cfg, self._log)
        ei = csp.get_cscripts_utils().get_ei_obj()
        # Halting the system
        sdp_obj.halt_and_check()
        self._product = self._common_content_lib.get_platform_family()
        wr_crc_dimm_alert_reg_path_dict = {
                                          ProductFamilies.SPR: "memss.mc{}.ch{}.correrrorstatus.dimm_alert".format(self.mc_number, self.channel_number),
                                          ProductFamilies.SKX: "mc{}_ch{}_correrrorstatus.dimm_alert".format(self.mc_number, self.channel_number),
                                          ProductFamilies.CLX: "mc{}_ch{}_correrrorstatus.dimm_alert".format(self.mc_number, self.channel_number),
                                          ProductFamilies.CPX: "mc{}_ch{}_correrrorstatus.dimm_alert".format(self.mc_number, self.channel_number),
                                          ProductFamilies.SNR: "memss.mc{}.ch{}.correrrorstatus.dimm_alert".format(self.mc_number, self.channel_number),
                                          ProductFamilies.ICX: "memss.mc{}.ch{}.correrrorstatus.dimm_alert".format(self.mc_number, self.channel_number)
                                          }
        alert_res = csp.get_by_path(csp.UNCORE, wr_crc_dimm_alert_reg_path_dict[self._product], self.socket_number)

        self._log.debug("Dimm Alert result : '{}' ".format(alert_res))
        if alert_res != 0:
            raise Exception("Dimm Alert is not 0 as per the requirement ")
        wr_crc_alert_signal_reg_path_dict = {
                                             ProductFamilies.SPR: "memss.mc{}.ch{}.alertsignal.seen".format(self.mc_number, self.channel_number),
                                             ProductFamilies.SKX: "mc{}_ch{}_alertsignal.seen".format(self.mc_number, self.channel_number),
                                             ProductFamilies.CLX: "mc{}_ch{}_alertsignal.seen".format(self.mc_number, self.channel_number),
                                             ProductFamilies.CPX: "mc{}_ch{}_alertsignal.seen".format(self.mc_number, self.channel_number),
                                             ProductFamilies.SNR: "memss.mc{}.ch{}.alertsignal.seen".format(self.mc_number, self.channel_number),
                                             ProductFamilies.ICX: "memss.mc{}.ch{}.alertsignal.seen".format(self.mc_number, self.channel_number)
                                             }
        alert_signal = csp.get_by_path(csp.UNCORE, wr_crc_alert_signal_reg_path_dict[self._product], self.socket_number)

        self._log.debug("alert Signal result : '{}' ".format(alert_signal))
        if alert_signal != 0:
            raise Exception("Alert Signal is not 0 as per the requirement ")
        ei.dimm_type_config_dump()
        # Injecting the Error
        ei._injectWriteCRC(0, 0, 0, 0)
        wrcrc_alert_res_reg_path_dict = {
                                        ProductFamilies.SPR: "memss.mc{}.ch{}.alertsignal.seen".format(self.mc_number, self.channel_number),
                                        ProductFamilies.SKX: "mc{}_ch{}_alertsignal.seen".format(self.mc_number, self.channel_number),
                                        ProductFamilies.CLX: "mc{}_ch{}_alertsignal.seen".format(self.mc_number, self.channel_number),
                                        ProductFamilies.CPX: "mc{}_ch{}_alertsignal.seen".format(self.mc_number, self.channel_number),
                                        ProductFamilies.SNR: "memss.mc{}.ch{}.alertsignal.seen".format(self.mc_number, self.channel_number),
                                        ProductFamilies.ICX: "memss.mc{}.ch{}.alertsignal.seen".format(self.mc_number, self.channel_number)
                                        }
        wrcrc_alert_res = csp.get_by_path(csp.UNCORE, wrcrc_alert_res_reg_path_dict[self._product], self.socket_number)
        self._log.debug("Alert Signal result after WRCRC Error Injection : '{}' ".format(wrcrc_alert_res))
        if wrcrc_alert_res != 1:
            raise Exception("Alert Signal is not 1 after WRCRC Error Injection")

        wrcrc_shadow_res_reg_path_dict = {
                                         ProductFamilies.SPR: "memss.mc{}.ch{}.imc0_mc_status_shadow.mscod".format(self.mc_number, self.channel_number),
                                         ProductFamilies.SKX: "mc{}_ch{}_imc0_mc_status_shadow.mscod".format(self.mc_number, self.channel_number),
                                         ProductFamilies.CLX: "mc{}_ch{}_imc0_mc_status_shadow.mscod".format(self.mc_number, self.channel_number),
                                         ProductFamilies.CPX: "mc{}_ch{}_imc0_mc_status_shadow.mscod".format(self.mc_number, self.channel_number),
                                         ProductFamilies.SNR: "memss.mc{}.ch{}.imc0_mc_status_shadow.mscod".format(self.mc_number, self.channel_number),
                                         ProductFamilies.ICX: "memss.mc{}.ch{}.imc0_mc_status_shadow.mscod".format(self.mc_number, self.channel_number)
                                         }
        wrcrc_shadow_res = csp.get_by_path(csp.UNCORE, wrcrc_shadow_res_reg_path_dict[self._product], self.socket_number)
        self._log.debug("MC Status Shadow after WRCRC Error Injection : '{}' ".format(wrcrc_shadow_res))
        if wrcrc_shadow_res != 0x00000200:
            raise Exception("Mscod is not 0x00000200 after WRCRC Error Injection")
        # Resuming the System
        sdp_obj.go()
        # Checking the SUT for captured Error
        ret_val = self._os_log_verification_obj.verify_os_log_error_messages(
            __file__, self._os_log_verification_obj.DUT_DMESG_FILE_NAME,
            self.DMESG_SIG)
        if ret_val:
            return True
        return False

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyTransientWrDataCRCError.main() else Framework.TEST_RESULT_FAIL)
