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
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework, ProductFamilies

from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.ras.tests.mem_mirroring.mem_mirroring_common import MemMirroringBaseTest
from src.ras.tests.io_virtualization.interleave_base_test import InterleaveBaseTest
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.provider_factory import ProviderFactory


class VerifyCorrectableErrorSettingThreshold(MemMirroringBaseTest):
    """
    Glasgow_id : G55818-MEM RAS - Correctable Error Threshold Setting Verification
    This test case Verifies the threshold value for logging Correctable Errors (CE) and corresponding platform
    error reporting behavior in a non redundant mode.

    """
    TEST_CASE_ID = ["G55818", "MEM RAS - Correctable Error Threshold Setting Verification"]
    BIOS_CONFIG_FILE_LIST = ["all_correrr_threshold_setting_bios_knobs.cfg",
                             "five_correrr_threshold_setting_bios_knobs.cfg",
                             "ten_correrr_threshold_setting_bios_knobs.cfg",
                             "twenty_correrr_threshold_setting_bios_knobs.cfg",
                             "none_correrr_threshold_setting_bios_knobs.cfg"]
    BIOS_CONFIG_FILE = "all_correrr_threshold_setting_bios_knobs.cfg"

    REGEX_DIMM_INFO = [r"(Directory Mode\s*\|\s*Off\s*\|\s*Off\s*\|\s*Off\s*\|)"]

    REGEX_ADDDC_STATUS_CHECK = [r"\|\s*0\s*5\s*0\s*0\s*00\s\|"]

    DMESG_SIG_CE = ["Hardware event. This is not a software error.", "Corrected error", "event severity: corrected",
                    "Error 0, type: corrected"]
    ERROR_INJECTION_TIMEOUT = 30

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VerifyCorrectableErrorSettingThreshold object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for
        execution environment.
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE)
        super(VerifyCorrectableErrorSettingThreshold, self).__init__(test_log, arguments,
                                                                     cfg_opts, bios_config_file)
        self._os_log_verification_obj = OsLogVerifyCommon(self._log, self.os,
                                                          self._common_content_configuration,
                                                          self._common_content_lib)
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_cfg, test_log)
        self.mc_value = self._common_content_configuration.get_memory_micro_controller()
        self.sub_channel_value = self._common_content_configuration. \
            get_einj_mem_location_subchannel()[0]
        self.channel_value = self._common_content_configuration.get_memory_channel()
        self.socket_value = self._common_content_configuration.get_einj_mem_location_socket()[0]
        self.dimm_slot = self._common_content_configuration.get_einj_mem_location_dimm()[0]
        self.rank_value = self._common_content_configuration.get_einj_mem_location_rank()[0]
        self.sub_rank_value = self._common_content_configuration.get_einj_mem_location_sub_rank()[0]
        self.bank_group_value = self._common_content_configuration.get_einj_mem_location_bank_group()[0]
        self.bank_value = self._common_content_configuration.get_einj_mem_location_bank()[0]

    def prepare(self):
        """
        Creates a new VerifyCorrectableErrorSettingThreshold object and we are calling a Prepare
        function that sets the bios knobs

        :return: None
        """
        super(VerifyCorrectableErrorSettingThreshold, self).prepare()

    def execute(self):
        """
        This Method is Used to execute below:
        1. Executes mc.dimminfo and validating the output
        2. Executes ras.adddc_status_check and validating output
        3. Injects mem errors until the threshold value is set and validating the output
           of the error
        4. Resets the system by setting different bios values for correctable error
           threshold knob
        5. Injects mem errors until the threshold value is set for different threshold
           values set and validating the output of the error

        :return: True or False
        """
        uc_error_flag = []
        try:
            # Executing mc.dimminfo and validating the output
            if self.get_mc_dimm_info(self.REGEX_DIMM_INFO):
                self._log.info("All dimm information Validated.")
            else:
                uc_error_flag.append(False)
                log_err = "Please Check the Dimm Configuration"
                self._log.error(log_err)
                raise Exception(log_err)

            CORRTHRESHOLD_CMD = {
                ProductFamilies.SPR: "memss.mc{}.ch{}.correrrthrshld_{}",
                ProductFamilies.ICX: "memss.mc{}.ch{}.correrrthrshld_{}",
                ProductFamilies.SKX: "memss.mc{}.ch{}.correrrthrshld_{}",
                ProductFamilies.CPX: "imc0.correrrthrshld_0"
            }

            CHECK_VALUE_ERR_LOG_REG_CMD_DICT = {
                ProductFamilies.SPR: "memss.mc{}.ch{}.dis_corr_err_log",
                ProductFamilies.ICX: "memss.mc{}.ch{}.dis_corr_err_log",
                ProductFamilies.SKX: "memss.mc{}.ch{}.dis_corr_err_log",
                ProductFamilies.CPX: "imc0.dis_corr_err_log"

            }

            for threshold_val in range(4):
                self._log.info("Iteration {}: checking threshold value ".format(threshold_val + 1),
                               CORRTHRESHOLD_CMD[
                                   self._cscripts.silicon_cpu_family].format(
                                   self.mc_value,
                                   self.channel_value, threshold_val))
                corr_threshold_value = self._cscripts.get_by_path(scope=self._cscripts.UNCORE,
                                                                  reg_path=CORRTHRESHOLD_CMD[
                                                                      self._cscripts.silicon_cpu_family].format(
                                                                      self.mc_value,
                                                                      self.channel_value,
                                                                      threshold_val),
                                                                  socket_index=
                                                                  self._common_content_configuration.
                                                                  get_memory_socket())
                if corr_threshold_value == 0x7fff7fff:
                    self._log.info("Successfully verified the threshold value same as BIOS")
                else:
                    self._log.error("Threshold is not same as BIOS for mc {} and channel {}"
                                    .format(self.mc_value, self.channel_value))

            self._ras_common_obj.verify_adddc_status()
            self._sdp.go()

            # Injecting mem errors until the threshold value is set and validating the output
            ei = self._cscripts.get_cscripts_utils().get_ei_obj()
            for iteration in range(5):
                ei.injectMemError(socket=self.socket_value,
                                  channel=self.channel_value,
                                  sub_channel=self.sub_channel_value,
                                  dimm=self.dimm_slot, rank=self.rank_value,
                                  sub_rank=self.sub_rank_value,
                                  bank_group=self.bank_group_value,
                                  bank=self.bank_value, errType="ce")
                time.sleep(self.ERROR_INJECTION_TIMEOUT)
            self._sdp.go()

            self._log.info("Resets the system to change the Corr_error threshold value : 5")
            self.enable_interleave_bios_knobs(self.BIOS_CONFIG_FILE_LIST[1])

            for threshold_val in range(4):
                self._log.info("Iteration {}: checking threshold value ".format(threshold_val + 1),
                               CORRTHRESHOLD_CMD[
                                   self._cscripts.silicon_cpu_family].format(
                                   self.mc_value,
                                   self.channel_value,
                                   threshold_val))
                corr_threshold_value = self._cscripts.get_by_path(scope=self._cscripts.UNCORE,
                                                                  reg_path=CORRTHRESHOLD_CMD[
                                                                      self._cscripts.silicon_cpu_family].format(
                                                                      self.mc_value,
                                                                      self.channel_value,
                                                                      threshold_val),
                                                                  socket_index=
                                                                  self._common_content_configuration.
                                                                  get_memory_socket())
                if corr_threshold_value == 0x50005:
                    self._log.info("Successfully verified the threshold value same as BIOS")
                else:
                    self._log.error("Threshold is not same as BIOS for mc {} and channel {}"
                                    .format(self.mc_value, self.channel_value))

            ei.injectMemError(socket=self.socket_value,
                              channel=self.channel_value,
                              sub_channel=self.sub_channel_value,
                              dimm=self.dimm_slot, rank=self.rank_value,
                              sub_rank=self.sub_rank_value,
                              bank_group=self.bank_group_value,
                              bank=self.bank_value, errType="ce")
            time.sleep(self.ERROR_INJECTION_TIMEOUT)

            # Checking the SUT for captured Error
            ret_val = self._os_log_verification_obj.verify_os_log_error_messages(
                __file__, self._os_log_verification_obj.DUT_MESSAGES_FILE_NAME,
                self.DMESG_SIG_CE)
            self._sdp.stop_log()
            if ret_val:
                uc_error_flag.append(True)
            else:
                uc_error_flag.append(False)
            self._log.info("Memory CE Injected successfully")

            self._ras_common_obj.verify_adddc_status()

            self._log.info("Resets the system to change the Corr_error threshold value: 10")
            self.enable_interleave_bios_knobs(self.BIOS_CONFIG_FILE_LIST[2])

            for threshold_val in range(4):
                corr_threshold_value = self._cscripts.get_by_path(scope=self._cscripts.UNCORE,
                                                                  reg_path=CORRTHRESHOLD_CMD[
                                                                      self._cscripts.silicon_cpu_family].format(
                                                                      self.mc_value,
                                                                      self.channel_value,
                                                                      threshold_val),
                                                                  socket_index=
                                                                  self._common_content_configuration.
                                                                  get_memory_socket())
                if corr_threshold_value == 0x00100010:
                    self._log.info("Successfully verified the threshold value same as BIOS")
                else:
                    self._log.error(
                        "Threshold is not same as BIOS for mc {} and channel {}".format(
                            self.mc_value,
                            self.channel_value))

            ei.injectMemError(socket=self.socket_value,
                              channel=self.channel_value,
                              sub_channel=self.sub_channel_value,
                              dimm=self.dimm_slot,
                              rank=self.rank_value,
                              sub_rank=self.sub_rank_value,
                              bank_group=self.bank_group_value,
                              bank=self.bank_value, errType="ce")
            time.sleep(self.ERROR_INJECTION_TIMEOUT)

            # Checking the SUT for captured Error
            ret_val = self._os_log_verification_obj.verify_os_log_error_messages(
                __file__, self._os_log_verification_obj.DUT_MESSAGES_FILE_NAME,
                self.DMESG_SIG_CE)
            self._sdp.stop_log()
            if ret_val:
                uc_error_flag.append(True)
            else:
                uc_error_flag.append(False)
            self._log.info("Memory CE Injected successfully")

            self._log.info("Resets the system to change the Corr_error threshold value: 20")
            self.enable_interleave_bios_knobs(self.BIOS_CONFIG_FILE_LIST[3])
            for threshold_val in range(4):
                self._log.info("Iteration {}: checking threshold value ".format(threshold_val + 1),
                               CORRTHRESHOLD_CMD[
                                   self._cscripts.silicon_cpu_family].format(
                                   self.mc_value,
                                   self.channel_value,
                                   threshold_val))
                corr_threshold_value = self._cscripts.get_by_path(scope=self._cscripts.UNCORE,
                                                                  reg_path=CORRTHRESHOLD_CMD[
                                                                      self._cscripts.silicon_cpu_family].format(
                                                                      self.mc_value,
                                                                      self.channel_value,
                                                                      threshold_val),
                                                                  socket_index=
                                                                  self._common_content_configuration.
                                                                  get_memory_socket())
                if corr_threshold_value == 0x00200020:
                    self._log.info("Successfully verified the threshold value same as BIOS")
                else:
                    self._log.error(
                        "Threshold is not same as BIOS for mc {} and channel {}".format(
                            self.mc_value,
                            self.channel_value))

            ei.injectMemError(socket=self.socket_value,
                              channel=self.channel_value,
                              sub_channel=self.sub_channel_value,
                              dimm=self.dimm_slot,
                              rank=self.rank_value,
                              sub_rank=self.sub_rank_value,
                              bank_group=self.bank_group_value,
                              bank=self.bank_value, errType="ce")
            time.sleep(self.ERROR_INJECTION_TIMEOUT)

            # Checking the SUT for captured Error
            ret_val = self._os_log_verification_obj.verify_os_log_error_messages(
                __file__, self._os_log_verification_obj.DUT_MESSAGES_FILE_NAME,
                self.DMESG_SIG_CE)
            self._sdp.stop_log()
            if ret_val:
                uc_error_flag.append(True)
            else:
                uc_error_flag.append(False)
            self._log.info("Memory CE Injected successfully")

            self._log.info("Resets the system to change the Corr_error threshold value to None")
            self.enable_interleave_bios_knobs(self.BIOS_CONFIG_FILE_LIST[4])
            corr_error_log_value = self._cscripts.get_by_path(scope=self._cscripts.UNCORE,
                                                              reg_path=
                                                              CHECK_VALUE_ERR_LOG_REG_CMD_DICT[
                                                                  self._cscripts.silicon_cpu_family].format(
                                                                  self.mc_value,
                                                                  self.channel_value),
                                                              socket_index=
                                                              self._common_content_configuration.
                                                              get_memory_socket()).show()

            if corr_error_log_value == 0x0000:
                self._log.info("Successfully disabled Correctable error logging")
            else:
                self._log.error("Failed to disable correctable error logging")

            return all(flag for flag in uc_error_flag)

        except Exception as ex:
            uc_error_flag.append(False)
            self._sdp.stop_log()
            self._log.error("Exception Occured: ", str(ex))

        finally:
            if not self._os.is_alive():
                self._ac.ac_power_off(30)
                self._log.info("Power off SUT")
                self._ac.ac_power_on()
                self._log.info("Powering on the platform..")
                self._os.wait_for_os(self.reboot_timeout)
                self._log.info("The platform is now in OS..")
            self._sdp.go()
            self._sdp.stop_log()


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if VerifyCorrectableErrorSettingThreshold.main()
        else Framework.TEST_RESULT_FAIL)
