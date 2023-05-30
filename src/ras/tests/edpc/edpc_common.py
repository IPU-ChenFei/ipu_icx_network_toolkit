#!/usr/bin/env python
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and propri-
# etary and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be ex-
# press and approved by Intel in writing.

import os
import re

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.dtaf_constants import ProductFamilies
from src.ras.lib.ras_common_utils import RasCommonUtil

from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration


class EdpcCommon(BaseTestCase):
    """
    This is common class for EDPC BIOS Setup.
    """
    _EDPC_BIOS_ENABLE = {"self._ras_commom_for_fatal.set_and_verify_bios_knobs()": 0x1,
                         "self._ras_commom_for_non_fatal.set_and_verify_bios_knobs()": 0x2}

    _FILE_NAME = "cscripts_log_file.log"
    _REGEX_CMD_FOR_DPC_DISABLED = r"dpcte.*DPC\sTrigger\sEnable.*0\s.*DPC\sdisabled"
    _REGEX_CMD_FOR_DPC_ERR_FATAL = r"dpcte.*DPC\sTrigger\sEnable.*1.*DPC\senabled\sDP\sdetects\suncorrerror\sor" \
                                   r"\sreceives\sERR_FATAL"
    _REGEX_CMD_FOR_DPC_ERR_NON_FATAL = r"dpcte.*DPC\sTrigger\sEnable.*2.*DPC\senabled\sDP\sdetects\suncorrerror\sor" \
                                       r"\sreceives\sERR_NONFATAL"
    ERROR_SEVERITY_FATAL = 1
    ERROR_SEVERITY_NONFATAL = 2

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file1=None, bios_config_file2=None):
        """
        Create an instance of sut os provider, BiosProvider and BIOS util

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file1: Bios Configuration file name
        :param bios_config_file2: Bios Configuration file name
        """
        super(EdpcCommon, self).__init__(test_log, arguments, cfg_opts)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider

        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider

        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider

        self._sv = self._cscripts.get_cscripts_utils().getSVComponent()
        self._ras = self._cscripts.get_ras_object()
        self._pcie = self._cscripts.get_cscripts_utils().get_pcie_obj()
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

        if bios_config_file1 and bios_config_file2:
            cur_path = os.path.dirname(os.path.realpath(__file__))
            enable_edpc_fatal_bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path,
                                                                                                    bios_config_file1)
            self._bios_util_edpc_fatal = BiosUtil(cfg_opts, enable_edpc_fatal_bios_config_file_path, self._bios, self._log,
                                                  self._common_content_lib)

            enable_edpc_non_fatal_bios_config_file_path = self._common_content_lib.get_config_file_path(
                cur_path,
                bios_config_file2)
            self._bios_util_edpc_non_fatal = BiosUtil(cfg_opts, enable_edpc_non_fatal_bios_config_file_path, self._bios,
                                                      self._log,
                                                      self._common_content_lib)
            self._ras_commom_for_fatal = RasCommonUtil(self._log, self._os, cfg_opts, self._content_cfg,
                                                       self._bios_util_edpc_fatal)
            self._ras_commom_for_non_fatal = RasCommonUtil(self._log, self._os, cfg_opts, self._content_cfg,
                                                           self._bios_util_edpc_non_fatal)

        self.log_file_path = self.get_cscrcipts_log_file_path()

        self._content_cfg = ContentConfiguration(self._log)
        self._reboot_timeout_in_sec = self._content_cfg.get_reboot_timeout()
        self.pcie_slot, self.portno, self.portdata = \
            self._common_content_lib.get_error_inj_pcie_port_num(self._sdp, self._pcie)

    def get_cscrcipts_log_file_path(self):
        """
        # We are getting the Path for thermal alarm check log file

        :return: log_file_path
        """
        cur_path = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(cur_path, self._FILE_NAME)
        return path

    def read_edpc_register_value(self):
        """
        This method will capture DPC status Register value based on the bios knobs setting using cscripts.

        :return:  dpcte_value
        """
        try:

            edpc_dpcte_dict = {ProductFamilies.ICX: 'pcie.pxp2.port0.cfg.dpcctl.dpcte',
                               ProductFamilies.SNR: 'pcie.pxp2.port0.cfg.dpcctl.dpcte',
                               ProductFamilies.SPR: 'pcie.pxp2.port0.cfg.dpcctl.dpcte'
                               }
            dpcte_value = self._cscripts.get_by_path(self._cscripts.UNCORE,
                                                     edpc_dpcte_dict[self._cscripts.silicon_cpu_family])
            return dpcte_value

        except Exception as ex:
            log_err = "Unable to read edpc enabled as fatal or Non Fatal Error due to the exception '{}'".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

    def check_edpc_enabled(self):
        """
        This method will set the edpc bios knobs for fatal and non fatal error and fetches the value set for
        DPC status Register based on the bios knobs setting.

        :return:  True if both fatal and non fatal verified successfully else false
        """
        edpc_enabled_successfully = []
        try:
            for bios_setting, error_type in self._EDPC_BIOS_ENABLE.items():
                self._log.info("set the edpc bios knob ")
                eval(bios_setting)
                if self.read_edpc_register_value() == error_type:
                    edpc_enabled_successfully.append(True)
                else:
                    edpc_enabled_successfully.append(False)
            return all(edpc_enabled_successfully)

        except Exception as ex:
            log_err = "Unable to check edpc enabled as non fatal Error due to the exception '{}'".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

    def verify_edpc_enabled(self):
        """
        This Method is used to Verify if Edpc is Enabled.

        :return: True if test is pass otherwise False.
        :raise: RuntimeError
        """
        try:
            if self.check_edpc_enabled():
                self._log.info("Verified: Fatal and Non Fatal errors when eDPC knob is Enabled")
                return True
            else:
                log_err = "unable to verify Fatal and Non Fatal errors when eDPC Bios knob enabled!"
                self._log.error(log_err)
                raise Exception(log_err)

        except Exception as ex:
            log_err = "An Exception Occurred: {}".format(str(ex))
            self._log.error(log_err)
            raise RuntimeError(log_err)

    def verify_dpc_is_disabled(self):
        """
        This Method is Used to to read out the edpc configuration registers current settings and verify whether dpc is
        in Disabled State.

        :return: None
        """
        self._log.info("Verify if DPC is Disabled")
        self._sdp.start_log(self.log_file_path, "w")
        self._ras.check_edpc_config(0, self.portno)
        self._sdp.stop_log()
        with open(self.log_file_path, "r") as log_file:
            log_file_list = log_file.readlines()
            self._log.info("".join(log_file_list))
            regex_out = re.findall(self._REGEX_CMD_FOR_DPC_DISABLED, "\n".join(log_file_list))
            if len(regex_out) != 0:
                self._log.info("DPC is in Disable State")
            else:
                self._log.error("DPC is Not in Disable State")

    def dpc_trigger_enable_type_error_uncorrerr(self, err_type):
        """
        This Method is Used to Write the Dpcte Binary based on the Error type and Verify the Dpc Trigger Type.

        :param err_type: ERROR_SEVERITY_NONFATAL = ERR_NONFATAL (Type 2), ERROR_SEVERITY_FATAL = ERR_FATAL (Type 1)
        :return: None
        """
        self._sdp.start_log(self.log_file_path, "w")
        self._log.info("Write dpcte binary to '{}'".format(err_type))
        self._ras.check_edpc_config(0, self.portno, err_type)
        self._log.info("Verify DPC Trigger Type")
        self._ras.check_edpc_config(0, self.pcie_slot)
        self._sdp.stop_log()
        with open(self.log_file_path, "r") as log_file:
            log_file_list = log_file.readlines()
            self._log.info("".join(log_file_list))
            if err_type == 1:
                regex_out = re.findall(self._REGEX_CMD_FOR_DPC_ERR_FATAL, "\n".join(log_file_list))
            else:
                regex_out = re.findall(self._REGEX_CMD_FOR_DPC_ERR_NON_FATAL, "\n".join(log_file_list))
            if len(regex_out) != 0:
                self._log.info("DPC is Enabled and DP detects uncorrerror or receives {} ".
                               format("ERR_FATAL" if err_type == 1 else "ERR_NONFATAL"))
            else:
                log_error = "DPC is Not Enabled"
                self._log.error(log_error)
                raise Exception(log_error)
