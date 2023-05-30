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

from src.ras.tests.mem_mirroring.mem_mirroring_common import MemMirroringBaseTest


class UncorrectableMultiBitErrorsDue(MemMirroringBaseTest):
    """
    Glasgow_id : 55724

    This test case: Injects memory correctable error: 0x08 and validate if the error is detected and corrected.
    """
    _bios_knobs_file = "Uncorrectable_Multi_bit_Errors_DUE_cpx.cfg"
    REGEX_FOR_VALIDATING_UCE_DEVMSK_EINJ = [r"(Uncorrected\serror)",
                                            r"(Transaction\:\sMemory\sread\serror)",
                                            r"(Hardware\sevent\.\sThis\sis\snot\sa\ssoftware\serror\.)"]
    _ERROR_INJECTION_TIMEOUT = 180
    ZERO_ERROR_SIGN_REGEX = r"0x0"
    ERROR_SIGN_REGEX = r"\s*errortype\s\[20\:11\]\s=\s0x4\s\-\-\>\sBit\s2\:\sTxn\scould\snot\sbe\scorrected\sby\sECC\;"
    REGEX_DIMM_INFO = [r"(Directory Mode\s*\|\s*Off\s*\|\s*Off\s*\|\s*Off\s*\|)",
                       r"(ECC\s\/\sCAP\sChecking\s*\|\s*On\s\/\sOn\s*\|\s*On\s\/\sOn\s*\|\s*On\s\/\sOn\s*\|)"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UncorrectableMultiBitErrorsDue object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.

        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self._bios_knobs_file)
        super(UncorrectableMultiBitErrorsDue, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        self.mc_value = self._common_content_configuration.get_memory_micro_controller()
        self.channel_value = self._common_content_configuration.get_memory_channel()
        self.socket_value = self._common_content_configuration.get_memory_socket()
        self.dimm_slot = self._common_content_configuration.get_einj_mem_location_dimm()[0]
        self.rank_value = self._common_content_configuration.get_einj_mem_location_rank()[0]

    def prepare(self):
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        super(UncorrectableMultiBitErrorsDue, self).prepare()
        self.initialize_sv_objects()
        self.initialize_sdp_objects()

    def execute(self):
        """
        This test case executes the following:
        1. Executes mc.dimminfo and validates the output
        2. Executes ras.adddc_status_check and validating output
        3. Executes klaxon.m2mem_errors and imc_errors and validating for 0 errors
        4. Verifies the threshold value for each socket
        5. Injects an uncorrected error in socket
        6. Verifies the message.log for uncorrected error strings
        7. Resets the system and injects the error in another socket

        """
        uce_due = []
        try:
            # Executing mc.dimminfo and validating the output
            if self.get_mc_dimm_info(self.REGEX_DIMM_INFO):
                self._log.info("All dimm information Validated.")
            else:
                uce_due.append(False)
                log_err = "Please Check the Dimm Configuration"
                self._log.error(log_err)
                raise Exception(log_err)
            self.SDP.go()
            CORRTHRESHOLD_CMD = {
                ProductFamilies.SPR: "memss.mc{}.ch{}.correrrthrshld_{}",
                ProductFamilies.ICX: "memss.mc{}.ch{}.correrrthrshld_{}",
                ProductFamilies.SKX: "memss.mc{}.ch{}.correrrthrshld_{}",
                ProductFamilies.CPX: "imc{}_c{}_correrrthrshld_{}",
                ProductFamilies.CLX: "imc{}_c{}_correrrthrshld_{}"
            }

            # Verifying the threshold value for each socket
            for threshold_val in range(4):
                corr_threshold_value = self._cscripts.get_by_path(scope=self._cscripts.UNCORE,
                                                                  reg_path=CORRTHRESHOLD_CMD[
                                                                      self._cscripts.silicon_cpu_family].
                                                                  format(self.mc_value,
                                                                         self.channel_value,
                                                                         threshold_val),
                                                                  socket_index=self.socket_value)
                if corr_threshold_value == 0x10001:
                    self._log.info("Successfully verified the threshold value: same as BIOS")
                else:
                    self._log.error(
                        "Threshold is not same as BIOS for mc {} and channel {}".format(
                            self.mc_value, self.channel_value))
            # executing ras.adddc_status_check and validating output
            self._ras_common_obj.verify_adddc_status(adddc_status_check=False)
            # Executing klaxon.m2mem_errors and imc_errors and validating for 0 errors
            if not self.check_system_error(self.ZERO_ERROR_SIGN_REGEX):
                self._log.info("No errors detected!")
            else:
                uce_due.append(False)
                self._log.error("Memory Errors detected, Please check configuration")
            self.SDP.go()
            # Injects an uncorrected error in socket
            self._ei.injectMemError(socket=self.socket_value, channel=self.channel_value,
                                        dimm=self.dimm_slot, rank=self.rank_value, errType="uce")

            self.SDP.go()
            self._log.info("Injection completed")
            time.sleep(self._ERROR_INJECTION_TIMEOUT)
            if not self._os.is_alive():
                self.SDP.itp.resettarget()
                time.sleep(self._ERROR_INJECTION_TIMEOUT)
            if self._os_log_obj.verify_os_log_error_messages(__file__,
                                                             self._os_log_obj.DUT_MESSAGES_FILE_NAME,
                                                             self.REGEX_FOR_VALIDATING_UCE_DEVMSK_EINJ):
                self._log.info("Successfully injected memory Uncorrectable error")
            else:
                log_err = "Error Not found in OS logs! error expected in OS logs when injecting Memory UCE"
                self._log.error(log_err)

            # Executing the klaxon.m2mem_errors and imc_errors and validating the output
            if not self.check_system_error(self.ERROR_SIGN_REGEX):
                self._log.info("Memory Errors detected successfully!")
            else:
                uce_due.append(False)
                self._log.error("No errors detected!")
            self._log.info("Restarting the SUT after injecting the errors")

            self.SDP.itp.resettarget()
            time.sleep(self._ERROR_INJECTION_TIMEOUT)
            if not self.os.is_alive():
                self._log.info("Waiting for OS to be alive...")
                self.os.wait_for_os(self._ERROR_INJECTION_TIMEOUT)

            self._ei.injectMemError(socket=1, channel=self.channel_value,
                                    dimm=self.dimm_slot, rank=self.rank_value, errType="uce")
            self.SDP.go()
            self._log.info("Memory UCE Injected successfully")

            return all(uce_due)

        except Exception as ex:
            uce_due.append(False)
            self._log.error("Exception Occurred: ", str(ex))
        finally:
            self.SDP.go()

    def cleanup(self, return_status):
        super(UncorrectableMultiBitErrorsDue, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UncorrectableMultiBitErrorsDue.main()
             else Framework.TEST_RESULT_FAIL)
