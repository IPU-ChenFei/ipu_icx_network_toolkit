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
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.provider_factory import ProviderFactory


class VerifyMemErrorExceedingThreshold(MemMirroringBaseTest):
    """
    Glasgow_id : G56091-MEM RAS - Uncorrectable Multi-bit Error logging after CE threshold is exceeded
    This test case injects memory correctable error and verifies SDDC +1 MCA logs in CScripts and logs reported in OS.

    """
    TEST_CASE_ID = ["G56091", "MEM RAS - Uncorrectable Multi-bit Error logging after CE threshold is exceeded"]
    BIOS_CONFIG_FILE = "uce_multi_bit_exceeding_threshold.cfg"

    REGEX_DIMM_INFO = [r"(Directory Mode\s*\|\s*Off\s*\|\s*Off\s*\|\s*Off\s*\|)"]

    REGEX_FOR_CE_EXCEEDING_THRESHOLD = [r"(0\snew\scorrectable\sHA\serror\sdetected)"]

    REGEX_ADDDC_STATUS_CHECK = [r"\|\s*0\s*5\s*0\s*0\s*00\s\|"]

    DMESG_SIG_CE = ["MemCtrl: Corrected read error", "Corrected error", "event severity: corrected",
                    "Error 0, type: corrected"]
    DMESG_SIG_UCE = ["Uncorrected error", "MCA: Data CACHE Level-0 Data-Read Error",
                     "Hardware event. This is not a software error."]
    _MEM_LOG_FILE = "memory_mirroring_log_file.txt"
    _ERROR_INJECTION_TIMEOUT = 5

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VerifyMemErrorExceedingThreshold object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE)
        super(VerifyMemErrorExceedingThreshold, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        self._reboot_time_out = self._common_content_configuration.get_reboot_timeout()
        self._os_log_verification_obj = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration,
                                                          self._common_content_lib)
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_cfg, test_log)
        self.mc_value = self._common_content_configuration.get_memory_micro_controller()
        self.subself.channel_value = self._common_content_configuration.get_einj_mem_location_subchannel()[0]
        self.channel_value = self._common_content_configuration.get_memory_channel()
        self.socket_value = self._common_content_configuration.get_einj_mem_location_socket()[0]
        self.dimm_slot = self._common_content_configuration.get_einj_mem_location_dimm()[0]
        self.rank_value = self._common_content_configuration.get_einj_mem_location_rank()[0]

    def prepare(self):
        """
        Creates a new VerifyMemErrorExceedingThreshold object and we are calling a Prepare function
        Prepare Function does the Following tasks:
            1. Set the bios knobs to its default mode.
            2. Set the bios knobs as per the test case.
            3. Reboot the SUT to apply the new bios settings.
            4. Verify the bios knobs that are set.
        :return: None
        """
        super(VerifyMemErrorExceedingThreshold, self).prepare()

    def execute(self):
        """
        This Method is Used to execute below:
        1. Executes mc.dimminfo and validating the output
        2. Executes ras.adddc_status_check and validating output
        3. Injects mem errors until the threshold value is set and validating the output of the error
        4. Injects Mem Error and validating the error injection output
        5. Injects the Mem UnCorrectable Error and validating the output
        6. Resets the exit break

        :return: True or False
        """
        uc_error_flag = []
        try:
            self._sdp.start_log("sddc_plus_one.log")
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

            # Verifying the threshold value for each socket
            for threshold_val in range(4):
                self._log.info("Iteration {}: checking threshold value ".format(threshold_val + 1),
                               CORRTHRESHOLD_CMD[
                    self._cscripts.silicon_cpu_family].format(
                    self.mc_value, self.channel_value, threshold_val))
                corr_threshold_value = self._cscripts.get_by_path(scope=self._cscripts.UNCORE,
                                                                  reg_path=CORRTHRESHOLD_CMD[
                                                                      self._cscripts.silicon_cpu_family].format(
                                                                      self.mc_value, self.channel_value, threshold_val),
                                                                  socket_index=self._common_content_configuration.get_memory_socket())
                if corr_threshold_value == 0x50005:
                    self._log.info("Successfully verified the threshold value same as BIOS")
                else:
                    self._log.error(
                        "Threshold is not same as BIOS for mc {} and channel {}".format(
                            self.mc_value, self.channel_value))

            self._ras_common_obj.verify_adddc_status(adddc_status_check=True,
                                                     adddc_status_check_list=self.REGEX_ADDDC_STATUS_CHECK)
            self._sdp.go()

            # Injecting mem errors until the threshold value is set and validating the output of the error
            ei = self._cscripts.get_cscripts_utils().get_ei_obj()
            for iteration in range(5):
                ei.injectMemError(socket=self.socket_value, channel=self.channel_value,
                                  sub_channel=self.subself.channel_value,
                                  dimm=self.dimm_slot, rank=self.rank_value, errType="ce")
                self._log.info("Iteration: {} Memory CE Injected successfully".format(iteration + 1))
            self._sdp.go()
            ei.injectMemError(socket=self.socket_value, channel=self.channel_value,
                              sub_channel=self.subself.channel_value,
                              dimm=self.dimm_slot, rank=self.rank_value, errType="uce")
            time.sleep(self._ERROR_INJECTION_TIMEOUT)
            self._log.info("Memory UCE Injected successfully")
            self._sdp.go()
            if not self._os.is_alive():
                self._log.info("SUT is down! Successfully injected Uncorrected Error!")
                uc_error_flag.append(True)
            else:
                self._log.error("SUT is still up! failed to inject Uncorrectable Error!")
                uc_error_flag.append(False)
            self._sdp.stop_log()
            self._log.info("Restarting the SUT after injecting the errors")

            # Restart the SUT
            if self._ac.ac_power_off(30):
                self._log.info("Power off the SUT")
                self._ac.ac_power_on()
                self._log.info("Powering on the platform..")
                self._os.wait_for_os(self._reboot_time_out)
                self._log.info("The platform is now in OS..")
            else:
                self._log.error("The platform did not power on..")
                raise SystemError("The platform did not power on..")

            ei.injectMemError(socket=self.socket_value, channel=self.channel_value, sub_channel=self.subself.channel_value,
                              dimm=self.dimm_slot, rank=self.rank_value, errType="ce")
            time.sleep(self._ERROR_INJECTION_TIMEOUT)
            self._log.info("Memory CE Injected successfully")
            self._sdp.go()

            # Injecting the memory uncorrectable error
            ei.injectMemError(socket=self.socket_value,
                              channel=self.channel_value,
                              sub_channel=self.subself.channel_value,
                              dimm=self.dimm_slot,
                              rank=self.rank_value, errType="uce")
            time.sleep(self._ERROR_INJECTION_TIMEOUT)
            self._log.info("Memory UCE Injected successfully")
            ret_val = self._os_log_verification_obj.verify_os_log_error_messages(
                __file__, self._os_log_verification_obj.DUT_MESSAGES_FILE_NAME,
                self.DMESG_SIG_UCE)
            self._sdp.stop_log()
            if ret_val:
                uc_error_flag.append(True)
            else:
                uc_error_flag.append(False)
                self._sdp.stop_log()
                self._sdp.go()
            return all(flag for flag in uc_error_flag)

        except Exception as ex:
            uc_error_flag.append(False)
            self._sdp.stop_log()

            self._log.error("Exception occured: ", str(ex))

        finally:
            if not self._os.is_alive():
                self._ac.ac_power_off(30)
                self._log.info("Power off SUT")
                self._ac.ac_power_on()
                self._log.info("Powering on the platform..")
                self._os.wait_for_os(self._reboot_time_out)
                self._log.info("The platform is now in OS..")
            self._sdp.go()
            self._sdp.stop_log()

    def cleanup(self, return_status):
        """
        This method executes the final cleanup procedure after test execution.

        :param return_status:
        :return:
        """
        super(VerifyMemErrorExceedingThreshold, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyMemErrorExceedingThreshold.main()
             else Framework.TEST_RESULT_FAIL)

