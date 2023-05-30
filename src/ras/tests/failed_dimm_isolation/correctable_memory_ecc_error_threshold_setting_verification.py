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


class CorrectableMemoryEccErrorThresholdSettingVerify(MemMirroringBaseTest):
    """
    Glasgow_id : 62987

    This test case: Verification of the threshold value for logging Correctable Errors (CE)
    and corresponding platform error reporting behavior in a non redundant mode.
    """
    _bios_knobs_file = "correctable_memory_ecc_error_threshold_setting.cfg"
    REGEX_FOR_VALIDATING_UCE_DEVMSK_EINJ = [r"(Error\sinjected\ssuccessfully)",
                                            r"(\s1\sError\sdetected)"]
    ERROR_SIGN_REGEX = [r"type: corrected", r"event severity: corrected", r"Hardware Error"]
    _ERROR_INJECTION_TIMEOUT = 5
    ZERO_ERROR_SIGN_REGEX = r"0x0"
    REGEX_DIMM_INFO = [r"(Directory Mode\s*\|\s*Off\s*\|\s*Off\s*\|\s*Off\s*\|)",
                       r"(ECC\s\/\sCAP\sChecking\s*\|\s*On\s\/\sOn\s*\|\s*On\s\/\sOn\s*\|\s*On\s\/\sOn\s*\|)"]
    VALID_REGEX_BEFORE_EI = 0x0
    ADDRV_REGEX_BEFORE_EI = 0x0
    CORRCOUNT_REGEX_BEFORE_EI = 0x0
    ADDDC_STATUS_REGEX = [r"\|\s*0\s*1\s*0\s*0\s*00\s\|"]
    ADDDC_STATUS_REGEX_CE_THRESHOLD_NINE = [r"\|\s*0\s*9\s*0\s*0\s*00\s\|"]
    ADDDC_STATUS_REGEX_CE_THRESHOLD_ALL = [r"\|\s*0\s*7fff\s*0\s*0\s*00\s\|"]
    ADDDC_STATUS_REGEX_CE_THRESHOLD_NINE_AFTER_EI = [r"\|\s*9\s*9\s*1\s*0\s*00\s\|"]
    ADDDC_STATUS_REGEX_AFTER_EI = [r"\|\s*1\s*1\s*1\s*0\s*00\s\|"]
    ADDDC_STATUS_REGEX_CE_THRESHOLD_ALL_AFTER_EI = [r"\|\s*18\s*7fff\s*0\s*0\s*00\s\|"]
    DEV0MSK = 0x1
    DEV1MSK = 0x0
    ERROR_SIGN_FILE_LIST = [r"1\snew\scorrectable\sHA\serror\sdetected", "\|\s*1\s*1\s*1\s*0\s*00\s\|"]
    ERROR_SIGN_FILE_LIST_NINE = [r"1\snew\scorrectable\sHA\serror\sdetected", r"\|\s*9\s*9\s*1\s*0\s*00\s\|"]
    ERROR_SIGN_FILE_LIST_ALL = [r"1\snew\scorrectable\sHA\serror\sdetected", r"\|\s*18\s*7fff\s*0\s*0\s*00\s\|"]
    ERROR_LOG_FILE = "error_log_file.txt"
    VALID_REGEX_AFTER_EI = 0x1
    ADDRV_REGEX_AFTER_EI = 0x1
    CORRCOUNT_REGEX_AFTER_EI = 0x1
    CORRCOUNT_REGEX_AFTER_EI_NINE = 0x9
    CORRCOUNT_REGEX_AFTER_EI_ALL = 0x18
    BIOS_CONFIG_FILE_LIST = ["nine_correctable_memory_ecc_error_threshold_setting_verification.cfg",
                             "all_correctable_memory_ecc_error_threshold_setting_verification.cfg"]
    MC_STATUS_CMD_DICT = {
        ProductFamilies.SPR: "memss.mc{}.ch{}.imc{}_m2mem_mci_status_shadow",
        ProductFamilies.ICX: "memss.mc{}.ch{}.imc{}_m2mem_mci_status_shadow",
        ProductFamilies.SKX: "memss.mc{}.ch{}.imc0_m2mem_mci_status_shadow",
        ProductFamilies.CPX: "imc{}_m2mem_mci_status_shadow",
        ProductFamilies.CLX: "memss.mc{}.ch{}.imc{}_m2mem_mci_status_shadow",
        ProductFamilies.SNR: "memss.mc{}.ch{}.imc{}_m2mem_mci_status_shadow"
    }
    CORRTHRESHOLD_CMD = {
        ProductFamilies.SPR: "memss.mc{}.ch{}.correrrthrshld_{}",
        ProductFamilies.ICX: "memss.mc{}.ch{}.correrrthrshld_{}",
        ProductFamilies.SKX: "memss.mc{}.ch{}.correrrthrshld_{}",
        ProductFamilies.CPX: "imc{}_c{}_correrrthrshld_{}",
        ProductFamilies.CLX: "memss.mc{}.ch{}.correrrthrshld_{}",
        ProductFamilies.SNR: "memss.mc{}.ch{}.correrrthrshld_{}"
    }
    CORRERROR_STATUS_CMD_DICT = {
        ProductFamilies.SPR: "memss.mc{}.ch{}.correrrorstatus",
        ProductFamilies.SKX: "mc{}_ch{}_correrrorstatus",
        ProductFamilies.CLX: "mc{}_ch{}_correrrorstatus",
        ProductFamilies.CPX: "imc{}_c{}_correrrorstatus",
        ProductFamilies.SNR: "memss.mc{}.ch{}.correrrorstatus",
        ProductFamilies.ICX: "memss.mc{}.ch{}.correrrorstatus"
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new CorrectableMemoryEccErrorThresholdSettingVerify object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.

        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self._bios_knobs_file)
        super(CorrectableMemoryEccErrorThresholdSettingVerify, self).__init__(test_log, arguments, cfg_opts,
                                                                              bios_config_file)
        self.mc_value = self._common_content_configuration.get_memory_micro_controller()
        self.channel_value = self._common_content_configuration.get_memory_channel()
        self.socket_value = self._common_content_configuration.get_einj_mem_location_socket()[0]
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
        super(CorrectableMemoryEccErrorThresholdSettingVerify, self).prepare()

    def execute(self):
        """
        This Method is Used to execute below:
        1. Executes klaxon.m2mem_errors, klaxon.imc_errors and validates for 0 errors
        2. Executes mc.dimminfo and validates the output
        3. Validates the mc status command output
        4. Verifies the threshold value for each socket
        5. Executes ras.adddc_status_check and validating output
        6. Injects mem errors until the threshold value is set and validating the output
           of the error
        7. Resets the system by setting different bios values for correctable error
           threshold knob
        8. Injects mem errors until the threshold value is set for different threshold
           values set and validating the output of the error

        :return: True or False
        """
        uce_due = []
        try:
            self.initialize_sv_objects()
            self.initialize_sdp_objects()
            if not self.check_system_error(self.ZERO_ERROR_SIGN_REGEX):
                self._log.info("PASS: No memory errors detected!")
                uce_due.append(True)
            else:
                self._log.error("Unknown Memory errors are detected, please reset and try again")
                uce_due.append(False)
            # Validates the mc status command
            check_mc_status_valid = self._cscripts.get_by_path(
                self._cscripts.UNCORES,
                self.MC_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value, self.channel_value),
                socket_index=0).valid
            check_mc_status_addrv = self._cscripts.get_by_path(
                self._cscripts.UNCORES,
                self.MC_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value, self.channel_value),
                socket_index=0).addrv
            check_mc_status_cor_err_cnt = self._cscripts.get_by_path(
                self._cscripts.UNCORES,
                self.MC_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value, self.channel_value),
                socket_index=0).corrcount
            if check_mc_status_valid == self.VALID_REGEX_BEFORE_EI and \
                    check_mc_status_addrv == self.ADDRV_REGEX_BEFORE_EI \
                    and check_mc_status_cor_err_cnt == self.CORRCOUNT_REGEX_BEFORE_EI:
                self._log.info("MC Status is validated successfully!")
                uce_due.append(True)
            else:
                self._log.error("MC Status values are incorrect!")
                uce_due.append(False)
            # Validates the mc.dimminfo Output
            if self.get_mc_dimm_info(self.REGEX_DIMM_INFO):
                self._log.info("All dimm information Validated.")
                uce_due.append(True)
            else:
                uce_due.append(False)
                log_err = "Please Check the Dimm Configuration"
                self._log.error(log_err)
                raise Exception(log_err)
            time.sleep(self._ERROR_INJECTION_TIMEOUT)

            # Verifying the threshold value for each socket
            for threshold_val in range(4):
                corr_threshold_value = self._cscripts.get_by_path(
                    scope=self._cscripts.UNCORE, reg_path=self.CORRTHRESHOLD_CMD[
                        self._cscripts.silicon_cpu_family].format(
                        self.mc_value, self.channel_value, threshold_val),
                    socket_index=self.socket_value)
                if corr_threshold_value == 0x10001:
                    self._log.info("Successfully verified the threshold value: same as BIOS")
                    uce_due.append(True)
                else:
                    uce_due.append(False)
                    self._log.error(
                        "Threshold is not same as BIOS for mc {} and channel {}".format(
                            self.mc_value, self.channel_value))
            correrrorstatus_cmd_result = self._cscripts.get_by_path(
                self._cscripts.UNCORES,
                self.CORRERROR_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value,
                                                              self.channel_value)).err_overflow_stat
            if correrrorstatus_cmd_result == 0x0:
                self._log.info("Overflow status flag is as expected as 0")
                uce_due.append(True)
            else:
                uce_due.append(False)
                self._log.error("Overflow status flag is not as expected as 0")
            # executing ras.adddc_status_check and validating output
            self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True,
                adddc_status_check_list=self.ADDDC_STATUS_REGEX)
            self.SDP.halt()
            self._ei.memDevs()
            self._ei.memDevs(dev0msk=self.DEV0MSK, dev1msk=self.DEV1MSK)
            self._sdp.start_log(self.ERROR_LOG_FILE, "w")
            self._ei.injectMemError(socket=self.socket_value, channel=self.channel_value,
                                    dimm=self.dimm_slot, rank=self.rank_value, errType='ce')
            self._sdp.stop_log()
            time.sleep(self._ERROR_INJECTION_TIMEOUT)
            with open(self.ERROR_LOG_FILE, 'r') as memory_error_log:
                err_log = memory_error_log.read()
            if self._ras_common_obj.check_signature_in_log_file(err_log, self.ERROR_SIGN_FILE_LIST):
                self._log.info("Error injected Successfully!")
                uce_due.append(True)
            else:
                self._log.error("Error log not found! Error injection is not successful!")
                uce_due.append(False)
            # validates the error overflow status flag after error injection
            correrrorstatus_cmd_result = self.SV._sv.socket0.uncore0.imc0_c0_correrrorstatus.err_overflow_stat
            if correrrorstatus_cmd_result == 0x1:
                self._log.info("Overflow status flag is updated as expected")
                uce_due.append(True)
            else:
                uce_due.append(False)
                self._log.error("Overflow status flag is not updated as expected")
            # Validates the mc status flags after error injection
            check_mc_status_valid = self._cscripts.get_by_path(
                self._cscripts.UNCORES,
                self.MC_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value, self.channel_value),
                socket_index=0).valid
            check_mc_status_addrv = self._cscripts.get_by_path(
                self._cscripts.UNCORES,
                self.MC_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value, self.channel_value),
                socket_index=0).addrv
            check_mc_status_cor_err_cnt = self._cscripts.get_by_path(
                self._cscripts.UNCORES,
                self.MC_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value, self.channel_value),
                socket_index=0).corrcount

            if check_mc_status_valid == self.VALID_REGEX_AFTER_EI and \
                    check_mc_status_addrv == self.ADDRV_REGEX_AFTER_EI \
                    and check_mc_status_cor_err_cnt == self.CORRCOUNT_REGEX_AFTER_EI:
                self._log.info("MC Status is validated successfully!")
                uce_due.append(True)
            else:
                self._log.error("MC Status values are incorrect!")
                uce_due.append(False)

            # executing ras.adddc_status_check and validating output
            self._log.info("RAS ADDDC Status Check after error injection!")
            self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True,
                adddc_status_check_list=self.ADDDC_STATUS_REGEX_AFTER_EI)
            self.SDP.go()
            time.sleep(self._ERROR_INJECTION_TIMEOUT)

            if self._os_log_obj.verify_os_log_error_messages(__file__,
                                                             self._os_log_obj.DUT_MESSAGES_FILE_NAME,
                                                             self.ERROR_SIGN_REGEX):
                self._log.info("Error found in OS logs! error expected in OS logs when injecting Memory CE")
                uce_due.append(True)
            else:
                uce_due.append(False)
                log_err = "Error Not found in OS logs! error expected in OS logs when injecting Memory CE"
                self._log.error(log_err)
                raise Exception(log_err)

            self._log.info("Resets the system to change the Correctable error threshold value: 9")
            bios_config_file_nine = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), self.BIOS_CONFIG_FILE_LIST[0])
            self.enable_interleave_bios_knobs(bios_config_file_nine)
            self._ei.resetInjectorLockCheck()
            self.SDP.halt()
            correrrorstatus_cmd_result = self._cscripts.get_by_path(
                self._cscripts.UNCORES,
                self.CORRERROR_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value,
                                                              self.channel_value)).err_overflow_stat

            if correrrorstatus_cmd_result == 0x0:
                self._log.info("Overflow status flag is updated as expected")
                uce_due.append(True)
            else:
                uce_due.append(False)
                self._log.error("Overflow status flag is not updated as expected")
            # executing ras.adddc_status_check and validating output
            self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True,
                adddc_status_check_list=self.ADDDC_STATUS_REGEX_CE_THRESHOLD_NINE)
            for i in range(10):
                self._sdp.start_log(self.ERROR_LOG_FILE, "w")
                self._ei.injectMemError(socket=self.socket_value, channel=self.channel_value,
                                        dimm=self.dimm_slot, rank=self.rank_value, errType='ce')
                self._sdp.stop_log()
            with open(self.ERROR_LOG_FILE, 'r') as memory_error_log:
                err_log = memory_error_log.read()
            if self._ras_common_obj.check_signature_in_log_file(err_log, self.ERROR_SIGN_FILE_LIST_NINE):
                self._log.info("Error injected Successfully!")
                uce_due.append(True)
            else:
                self._log.error("Error log not found! Error injection is not successful!")
                uce_due.append(False)
            check_mc_status_valid = self._cscripts.get_by_path(
                self._cscripts.UNCORES, self.MC_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value, self.channel_value),
                socket_index=0).valid
            check_mc_status_addrv = self._cscripts.get_by_path(
                self._cscripts.UNCORES, self.MC_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value, self.channel_value),
                socket_index=0).addrv
            check_mc_status_cor_err_cnt = self._cscripts.get_by_path(
                self._cscripts.UNCORES, self.MC_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value, self.channel_value),
                socket_index=0).corrcount
            if check_mc_status_valid == self.VALID_REGEX_AFTER_EI and \
                    check_mc_status_addrv == self.ADDRV_REGEX_AFTER_EI \
                    and check_mc_status_cor_err_cnt == self.CORRCOUNT_REGEX_AFTER_EI_NINE:
                self._log.info("MC Status is validated successfully!")
                uce_due.append(True)
            else:
                uce_due.append(False)
                self._log.error("MC Status values are incorrect!")
            # executing ras.adddc_status_check and validating output
            self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True,
                adddc_status_check_list=self.ADDDC_STATUS_REGEX_CE_THRESHOLD_NINE_AFTER_EI)
            correrrorstatus_cmd_result = self._cscripts.get_by_path(
                self._cscripts.UNCORES,
                self.CORRERROR_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value,
                                                              self.channel_value)).err_overflow_stat
            if correrrorstatus_cmd_result == 0x1:
                self._log.info("Overflow status flag is updated as expected")
                uce_due.append(True)
            else:
                uce_due.append(False)
                self._log.error("Overflow status flag is not updated as expected")
            self.SDP.go()

            self._log.info("Resets the system to change the Correctable error threshold value: 0x7fff")
            bios_config_file_all = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), self.BIOS_CONFIG_FILE_LIST[1])
            self.enable_interleave_bios_knobs(bios_config_file_all)
            self._ei.resetInjectorLockCheck()
            self.SDP.halt()
            correrrorstatus_cmd_result = self._cscripts.get_by_path(
                self._cscripts.UNCORES,
                self.CORRERROR_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value,
                                                              self.channel_value)).err_overflow_stat

            if correrrorstatus_cmd_result == 0x0:
                self._log.info("Overflow status flag is updated as expected")
                uce_due.append(True)
            else:
                self._log.error("Overflow status flag is not updated as expected")
                uce_due.append(False)
            # executing ras.adddc_status_check and validating output
            self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True,
                adddc_status_check_list=self.ADDDC_STATUS_REGEX_CE_THRESHOLD_ALL)
            for i in range(25):
                self._sdp.start_log(self.ERROR_LOG_FILE, "w")
                self._ei.injectMemError(socket=self.socket_value, channel=self.channel_value,
                                        dimm=self.dimm_slot, rank=self.rank_value, errType='ce')
                self._sdp.stop_log()
            with open(self.ERROR_LOG_FILE, 'r') as memory_error_log:
                err_log = memory_error_log.read()
            if self._ras_common_obj.check_signature_in_log_file(err_log, self.ERROR_SIGN_FILE_LIST_ALL):
                self._log.info("Error injected Successfully!")
                uce_due.append(True)
            else:
                uce_due.append(False)
                self._log.error("Error log not found! Error injection is not successful!")
            check_mc_status_valid = self._cscripts.get_by_path(
                self._cscripts.UNCORES, self.MC_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value, self.channel_value),
                socket_index=0).valid
            check_mc_status_addrv = self._cscripts.get_by_path(
                self._cscripts.UNCORES, self.MC_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value, self.channel_value),
                socket_index=0).addrv
            check_mc_status_cor_err_cnt = self._cscripts.get_by_path(
                self._cscripts.UNCORES, self.MC_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value, self.channel_value),
                socket_index=0).corrcount
            if check_mc_status_valid == self.VALID_REGEX_AFTER_EI and \
                    check_mc_status_addrv == self.ADDRV_REGEX_AFTER_EI \
                    and check_mc_status_cor_err_cnt == self.CORRCOUNT_REGEX_AFTER_EI_ALL:
                self._log.info("MC Status is validated successfully!")
                uce_due.append(True)
            else:
                uce_due.append(False)
                self._log.error("MC Status values are incorrect!")
            # executing ras.adddc_status_check and validating output
            self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True,
                adddc_status_check_list=self.ADDDC_STATUS_REGEX_CE_THRESHOLD_ALL_AFTER_EI)
            correrrorstatus_cmd_result = self._cscripts.get_by_path(
                self._cscripts.UNCORES,
                self.CORRERROR_STATUS_CMD_DICT[
                    self._cscripts.silicon_cpu_family]
                    .format(self.mc_value,
                            self.channel_value)).err_overflow_stat
            if correrrorstatus_cmd_result == 0x0:
                self._log.info("Overflow status flag is updated as expected")
                uce_due.append(True)
            else:
                self._log.error("Overflow status flag is not updated as expected")
                uce_due.append(False)
            self.SDP.go()
            print(uce_due)
            return all(uce_due)
        except Exception as ex:
            uce_due.append(False)
            self._log.error("Exception Occurred: ", str(ex))
        finally:
            self.SDP.go()

    def cleanup(self, return_status):
        super(CorrectableMemoryEccErrorThresholdSettingVerify, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CorrectableMemoryEccErrorThresholdSettingVerify.main()
             else Framework.TEST_RESULT_FAIL)
