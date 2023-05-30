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
from src.ras.tests.einj_tests.einj_mem_uncorrectable_non_fatal import EinjMemUnCorrectableNonFatal
from src.ras.tests.einj_tests.einj_mem_correctable import EinjMemCorrectable

from src.lib.bios_util import BiosUtil
from src.lib.config_util import ConfigUtil
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.ras.lib.ras_smm_common import RasSmmCommon
from src.lib.install_collateral import InstallCollateral
from dtaf_core.providers.ac_power import AcPowerControlProvider


class CloakingCommon(BaseTestCase):
    """
    This Class is Used as Common Class For all the cloaking Test Cases
    """
    _ERROR_CONTROL = 0x17f
    _MCA_ERROR_CONTROL = 0x52
    _AC_POWER_WAIT_TIME = 3
    _AC_POWER_TIME_OUT = 30

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts,
            bios_file
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
            CloakingCommon,
            self).__init__(
            test_log,
            arguments,
            cfg_opts)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider
        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self._sv = self._cscripts.get_cscripts_utils().getSVComponent()
        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, bios_file)
        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)
        self._common_content_config = ContentConfiguration(self._log)
        self._smm = RasSmmCommon(self._log, self._cscripts, self._sdp)
        self._reboot_timeout_in_sec = self._common_content_config.get_reboot_timeout()
        self._execute_cmd_timeout_in_sec = self._common_content_config.get_command_timeout()
        self._reboot_timeout_in_sec = self._common_content_config.get_reboot_timeout()
        self._execute_cmd_timeout_in_sec = self._common_content_config.get_command_timeout()
        self._itp_halt_delay_sec = self._common_content_config.itp_halt_time_in_sec()
        # Create an ErrorInjection Uncorrectable NonFatal object to run Functionality of Uncloaked
        # Uncorrectable NonFatalError
        self._einj_uncna_obj = EinjMemUnCorrectableNonFatal(test_log, arguments, cfg_opts)
        self._einj_corr_obj =  EinjMemCorrectable(test_log, arguments, cfg_opts)  # Create an ErrorInjection 
        # Correctable object to run the functionality of Uncloaked Correctable Error
        ac_power_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)  # type: AcPowerControlProvider
        self._ac_power = ProviderFactory.create(ac_power_cfg, test_log)
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)

    def is_cloaking_enabled(self):
        """
        This Method is to check the clocking in enable or not.

        :return: True if enable else False
        """
        try:
            ret_val = False
            self._sdp.halt()
            self._sv.refresh()
            self._smm.enter_smm_mode()
            self._sdp.halt()
            time.sleep(self._itp_halt_delay_sec)
            error_control = self._sdp.msr_read(self._ERROR_CONTROL)
            cmci_disable = self._common_content_lib.get_bits(error_control, 4)
            self._log.info("CMCI_DISABLE bit is : {}".format(cmci_disable))
            mca_error_control = self._sdp.msr_read(self._MCA_ERROR_CONTROL)
            cerr_rd_status = self._common_content_lib.get_bits(mca_error_control, 0)
            self._log.info("CERR_RD_STATUS_IN_SMM_ONLY bit is : {}".format(cerr_rd_status))
            ucna_rd_status = self._common_content_lib.get_bits(mca_error_control, 1)
            self._log.info("UCNA_RD_STATUS_IN_SMM_ONLY bit is : {}".format(ucna_rd_status))
            self._sdp.go()
            time.sleep(self._itp_halt_delay_sec)
            ret_val = cerr_rd_status and ucna_rd_status and cmci_disable

        except Exception as ex:
            log_error = "An exception occurred:\n{}".format(str(ex))
            self._log.error(log_error)
            raise ex
        return ret_val

    def set_bios_knobs_cloaking_test(self):
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.

        :return: None
        """
        self._log.info("Clear all OS error logs...")
        self._common_content_lib.clear_all_os_error_logs()

        self._log.info("Set the Bios Knobs to Default Settings")
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.

        self._log.info("Set the Bios Knobs as per our Test Case Requirements")
        self._bios_util.set_bios_knob()  # To set the bios knob setting.

        self._log.info("Bios Knobs are Set as per our TestCase and Reboot to Apply the Settings")
        self._os.reboot(int(self._reboot_timeout_in_sec))  # To apply the new bios setting.

        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

    def cloaking_injecting_memory_uncorrectable_non_fatal_error(self):
        """
        This Function Injects the MemoryUncorrectableNonFatalError and Sets the Cloaking BiosKnobs
        and Validates the Error Log

        :return result: True on expected result else False
        """
        try:
            uncloaked_result = self._einj_uncna_obj._ras_einj_obj.einj_inject_and_check\
                (self._einj_uncna_obj._ras_einj_obj.EINJ_MEM_UNCORRECTABLE_NONFATAL)
            if not uncloaked_result:
                self._log.info("Cannot proceed with cloaking test since uncloaked injection failed... Exiting")
                return uncloaked_result

            self._log.info("Proceed with cloaking test since uncloaked injection passed...")
            self.set_bios_knobs_cloaking_test()
            cloaked_result = not self._einj_uncna_obj._ras_einj_obj.einj_inject_and_check(
                self._einj_uncna_obj._ras_einj_obj.EINJ_MEM_UNCORRECTABLE_NONFATAL)

            if not cloaked_result:
                self._log.info("Unexpectedly observed reported error logs even when cloaking was enabled. "
                               "With cloaking enabled, the uncorrectable error should have been hidden")
                return cloaked_result

        except Exception as ex:
            log_error = "An exception occurred:\n{}".format(str(ex))
            self._log.error(log_error)
            raise ex

        return cloaked_result and uncloaked_result

    def cloaking_injecting_memory_correctable_error(self):
        """
        This Function Injects the MemoryCorrectableError and Sets the Cloaking BiosKnobs
        and Validates the Error Log

        :return result: True on expected result else False
        """
        try:
            uncloaked_result = self._einj_corr_obj._ras_einj_obj.einj_inject_and_check\
                (self._einj_uncna_obj._ras_einj_obj.EINJ_MEM_CORRECTABLE)
            if not uncloaked_result:
                log_err = "Cannot proceed with cloaking test since uncloaked injection failed... Exiting"
                self._log.error(log_err)
                raise log_err

            if self._ac_power.ac_power_off(self._AC_POWER_TIME_OUT):
                self._log.info("AC power supply has been removed")
            else:
                log_error = "Failed to power-off SUT.."
                self._log.error(log_error)
                raise RuntimeError(log_error)
            time.sleep(self._AC_POWER_WAIT_TIME)
            if self._ac_power.ac_power_on(self._AC_POWER_TIME_OUT):
                self._log.info("AC power supply has been connected")
            else:
                log_error = "Failed to power-on SUT.."
                self._log.error(log_error)
                raise RuntimeError(log_error)
            self._os.wait_for_os(self._reboot_timeout_in_sec)  # Wait for System to come in OS State

            self._log.info("Proceed with cloaking test since uncloaked injection passed...")
            self.set_bios_knobs_cloaking_test()
            cloaked_result = not self._einj_corr_obj._ras_einj_obj.einj_inject_and_check(
                self._einj_uncna_obj._ras_einj_obj.EINJ_MEM_CORRECTABLE)

            if not cloaked_result:
                log_err = "Unexpectedly observed reported error logs even when cloaking was enabled. " \
                          "With cloaking enabled, the correctable error should have been hidden"
                self._log.error(log_err)
                raise log_err

        except Exception as ex:
            log_error = "An exception occurred:\n{}".format(str(ex))
            self._log.error(log_error)
            raise ex

        return cloaked_result and uncloaked_result
