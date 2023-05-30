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

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.lib.content_base_test_case import ContentBaseTestCase


class DwrCommon(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the Dwr Test Cases
    """

    _dict_dwr_enable = {
        ProductFamilies.CLX: "uncore0.biosscratchpad7",
        ProductFamilies.SKX: "uncore0.biosscratchpad7",
        ProductFamilies.CPX: "uncore0.biosscratchpad7",
        ProductFamilies.ICX: "uncore.ubox.ncdecs.biosscratchpad7_cfg",
        ProductFamilies.SPR: "uncore.ubox.ncdecs.biosscratchpad7_cfg",
    }
    _WAIT_FOR_DMI_LINK_DOWN = 25
    _WAIT_FOR_DAL_RECONFIG = 120
    _CHECK_25TH_BIT = 25
    _CHECK_26TH_BIT = 26

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file):
        """
        Create an instance of sut os provider, BiosProvider, SiliconDebugProvider, SiliconRegProvider
         BIOS util and Config util
        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(DwrCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        self._cfg = cfg_opts
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._product = self._common_content_lib.get_platform_family()

    def verify_dwr_enable(self):
        """
        This functions Verifies whether Dwr is Enabled or not

        return: Returns True if Dwr Enabled, Else False Dwr Not Enabled
        """
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:
            dwr_enable = False
            try:
                self._log.info("Verifying if Dwr is enabled or not")
                # Getting the Register Value
                if self._product not in self._dict_dwr_enable:
                    log_error = "The DWR enable not implemented for platform '{}'..". \
                        format(self._product)
                    self._log.error(log_error)
                    raise NotImplementedError(log_error)

                reg_path = self._dict_dwr_enable[self._product]
                dwr_enable_reg_value = cscripts_obj.get_by_path(cscripts_obj.SOCKETS, reg_path)
                self._log.info("The register '{}' value is '{}'".format(reg_path, dwr_enable_reg_value))

                # Checking the Bit 25
                dwr_check_bit = self._common_content_lib.get_bits(list(dwr_enable_reg_value), self._CHECK_25TH_BIT)
                if dwr_check_bit == 1:
                    self._log.info("DWR is Enabled...")
                    dwr_enable = True
                else:
                    self._log.error("DWR is Not Enabled...")

            except Exception as ex:
                self._log.error("Exception occurred '{}'".format(ex))
                raise ex

            return dwr_enable

    def dwr_error_injection(self):
        """
        This Function Injects an ierr by bringing down an IIO link and trying to do a
        read on a device downstream of the link.

        return: True if Dwr_flow is detected else False
        """
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj, \
                ProviderFactory.create(self.si_dbg_cfg, self._log) as sdp_obj:
            self._log.info("Injecting a Three Strike Errror")
            err_inj_obj = cscripts_obj.get_cscripts_ei_object()
            err_inj_obj.injectThreeStrike()
            time.sleep(self._WAIT_FOR_DMI_LINK_DOWN)
            self._log.info("Retraining the DMI....")
            cscripts_obj.get_sockets()[0].uncore0.pxp_dmi_lnkcon.active_state_link_pm_control = 2
            cscripts_obj.get_sockets()[0].uncore0.pxp_dmi_devctrl2.compltodis = 0
            cscripts_obj.get_sockets()[0].uncore0.pxp_b0d07f0_reutengltron.phyreset = 0
            sdp_obj.itp.resettarget()
            self._log.info("Wait for OS")
            self.os.wait_for_os(self.reboot_timeout)
            reg_path = self._dict_dwr_enable[self._product]
            dwr_enable_reg_value = cscripts_obj.get_by_path(cscripts_obj.SOCKETS, reg_path)
            self._log.info("The register '{}' value is '{}'".format(reg_path, dwr_enable_reg_value))
            dwr_flow = False
            try:
                #  Checking the Bit 26
                dwr_check_bit = self._common_content_lib.get_bits(list(dwr_enable_reg_value), self._CHECK_26TH_BIT)
                self._log.info("dwr value of 26 th bit '{}'".format(dwr_check_bit))
                #  Due to Some Issues Manually we could not able to get the value of 26 bit as 1. So it is Failing
                if dwr_check_bit == 1:
                    self._log.info("DWR Flow is Detected")
                    dwr_flow = True
                else:
                    self._log.error("DWR Flow is Not Detected...")

            except Exception as ex:
                self._log.error("Exception occurred '{}'".format(ex))
                raise ex
            finally:
                return dwr_flow
