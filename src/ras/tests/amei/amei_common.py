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

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from src.ras.lib.ras_smm_common import RasSmmCommon
from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.content_base_test_case import ContentBaseTestCase


class AmeiCommon(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the Amei Test Cases
    """

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
        if bios_config_file:
            bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), bios_config_file)
        super(
            AmeiCommon,
            self).__init__(
            test_log,
            arguments,
            cfg_opts, bios_config_file)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, bios_config_file)
        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)
        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider

        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider

        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()

        self._smm = RasSmmCommon(self._log, self._cscripts, self._sdp)

    def check_machine_check_bank_write_enable(self):
        """
        Check if machine check bank write is enable in system

        :return: None
        :raise: RuntimeError if unable to verify whether machine check bank write enable is enabled or not.
        """
        try:
            machine_check_bank_write_enable_status = self.is_machine_check_bank_write_enabled()
            if machine_check_bank_write_enable_status:
                self._log.info("Machine Check Bank Write is Enabled Successfully")
            else:
                self._log.error("Machine Check Bank Write is Not Enabled")
            return machine_check_bank_write_enable_status
        except Exception as ex:
            log_error = "Unable to Check Whether Machine Check Bank Write is Enabled or Not due to exception '{}'" \
                .format(ex)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def check_machine_check_bank_write_capable(self):
        """
        Check if machine check bank write is capable in system

        :return: None
        :raise: RuntimeError if unable to verify whether machine check bank write capable is enabled or not.
        """
        try:
            machine_check_bank_write_capable_status = self.is_machine_check_bank_write_capable()
            if machine_check_bank_write_capable_status:
                self._log.info("Machine Check Bank Write is Capable")
            else:
                self._log.error("Machine Check Bank Write is Not Capable")
            return machine_check_bank_write_capable_status
        except Exception as ex:
            log_error = "Unable to Check Whether Machine Check Bank Write is Capable or Not due to exception '{}'" \
                .format(ex)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def is_machine_check_bank_write_enabled(self):
        """
        Checks if machine check bank writes are enabled. Part of the Machine Check Bank Overwrite feature.
        Checks the register field DEBUG_ERR_INJ_CTL.MCBW_E (MSR 0x1E3, bit 0) from System Management Mode (SMM).

        :return: True if machine check bank writes are enabled, False otherwise.
        """
        self._smm.enter_smm_mode()
        self._sdp.halt()
        # Writing the Msr
        self._sdp.msr_write(0x1E3, 1)
        # Reading from MSR Register
        msr_value = self._sdp.msr_read(0x1E3)
        # Reading 0th Bit of MSR
        msr_bit = self._common_content_lib.get_bits(msr_value, 0)
        if msr_bit:
            self._log.info("Machine Check Bank Write is Enabled")
            return True
        else:
            self._log.error("Machine Check Bank Write is Not Enabled")
            return False

    def is_machine_check_bank_write_capable(self):
        """
        Indicates if the socket supports the Machine Check Bank Overwrite feature.
        Checks SMM_MCA_CAP[55] (that bit is copied from fuse FUSE_EMCA_EP_DISABLE) and fuse ERROR_SPOOFING.

        :return return_flag:
        """
        return_flag = 0
        # Enter SMM, read the register, exit SMM
        self._smm.enter_smm_mode()
        self._sdp.halt()
        smm_mca_cap = self._sdp.msr_read(0x17D)
        smm_mca_cap_55_bit = self._common_content_lib.get_bits(smm_mca_cap, 55)
        if smm_mca_cap_55_bit:
            self._log.info("Machine Check Bank Overwrite Feature is Enabled")
            return_flag = 1
        else:
            self._log.info("Machine Check Bank Overwrite feature is not supported")
        self._smm.exit_smm_mode()
        return return_flag
