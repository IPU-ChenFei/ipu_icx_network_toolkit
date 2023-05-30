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


class VerifyAdddcEnabledInSameBankDifferentDevices(MemMirroringBaseTest):
    """
        Glasgow_id : G63942-ADC(SR)Same Bank_Different Devices
        This test injects correctable multibit errors till threshold is met and checks whether ADDDC was
        activated and the steps are repeated for different devices same banks.
    """
    TEST_CASE_ID = ["G63942", "ADC(SR)Same Bank_Different Devices"]
    _BIOS_CONFIG_FILE = "adddc_same_device_adjacent_banks_cpx.cfg"
    REGEX_DIMM_INFO = [r"(Directory\sMode\s*\|\s*Off\s*\|\s*Off\s*\|\s*Off\s*\|)",
                       r"(Channel Mode\s*\|Independent\|Independent\|Independent\s\|)",
                       r"(ADDDC\s*\|\s*Enable\s*\|\s*Enable\s*\|\s*Enable\s*\|)",
                       r"(ECC\s\/\sCAP\sChecking\s*\|\s*On\s\/\sOn\s*\|\s*On\s\/\sOn\s*\|\s*On\s\/\sOn\s*\|)"]
    REGEX_RAS_ADDDC_STATUS_AFTER_EI = [r"(\s*\|\s*3\s*3\s*1\s*0\s*00\s\|)"]
    SPARE_ENABLE_CMD_DICT = {ProductFamilies.CPX: "imc{}_sparectl.spare_enable",
                             ProductFamilies.SKX: "imc{}_sparectl.spare_enable",
                             ProductFamilies.CLX: "imc{}_sparectl.spare_enable",
                             ProductFamilies.SPR: "memss.imc{}_sparectl.spare_enable",
                             ProductFamilies.ICX: "memss.imc{}_sparectl.spare_enable"}
    REGEX_ADDDC_SPARING_STATUS_CHECK = [r"(sparing\_control\.adddc\_sparing\s*\=\s1)",
                                        r"(sparing\_control\.region\_size\s*\=\s0\s\(Bank\))",
                                        r"(\|\sbank\sgroup\(11\:10\)\s*\|\s*2\s*\|)",
                                        r"(\|\sbank\s\(09\:08\)\s*\|\s*3\s*\|)",
                                        r"(\|\schip\sselect\s\(02\:00\)\s\|\s*0\s*\|\s*0\s*\|)",
                                        r"(\|\s*0\s*0\s*2\s*3\s*\|\senable\s\|)",
                                        r"(\|\s*0\s*0\s*2\s*2\s*\|\s*bank\s*\|)",
                                        r"(ADDDC\sfaildevice\s\=\s*3\s\(Rank0\))",
                                        r"(\|\s*0\s*3\s*0\s*0\s*00\s\|)"]
    REGEX_RAS_ADDDC_STATUS_AFTER_EI_ADJ_BANK = [r"(\|\s*0\s*3\s*0\s*0\s*00\s\|)"]
    ZERO_ERROR_SIGN_REGEX = r"0x0"
    EI_LOG_FILE = "ei_log_file.txt"
    REGEX_EI_LOG_FILE = [r"(1\snew\scorrectable\sHA\serror\sdetected)", r"(\|\s*1\s*3\s*0\s*0\s*00\s\|)",
                         r"(Error\sinjected\ssuccessfully)",
                         r"(Error\sis\sconsumed\sby\shost\smemory\sread\srequest\!)",
                         r"(socket0\simc0\shas\snmCache\s0\sand\spmemCache\s0)"]
    REGEX_EI_LOG_FILE_AFTER_THREE_EI = [r"(1\snew\scorrectable\sHA\serror\sdetected)",
                                        r"(\|\s*3\s*3\s*1\s*0\s*00\s\|)",
                                        r"(Error\sinjected\ssuccessfully)",
                                        r"(Error\sis\sconsumed\sby\shost\smemory\sread\srequest\!)",
                                        r"(socket0\simc0\shas\snmCache\s0\sand\spmemCache\s0)"]
    REGEX_EI_LOG_FILE_ADJ_BANK = [r"(1\snew\scorrectable\sHA\serror\sdetected)",
                                  r"(\|\s*0\s*3\s*0\s*0\s*00\s\|)"]
    REGEX_EI_LOG_FILE_MAPPING_OUT_BANK = [r"(0\snew\scorrectable\sHA\serror\sdetected)",
                                          r"(\|\s*0\s*3\s*0\s*0\s*00\s\|)"]
    REGEX_EI_LOG_FILE_MAPPING_OUT_SAME_BANK_DIFF_DEVICE = [r"(1\snew\scorrectable\sHA\serror\sdetected)",
                                                           r"(\|\s*1\s*2\s*0\s*0\s*00\s\|)"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VerifyAdddcEnabledInSameBankDifferentDevices object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self._BIOS_CONFIG_FILE)
        super(VerifyAdddcEnabledInSameBankDifferentDevices, self).__init__(test_log, arguments, cfg_opts,
                                                                           bios_config_file)
        self.mc_value = self._common_content_configuration.get_memory_micro_controller()
        self.sub_channel_value = self._common_content_configuration.get_einj_mem_location_subchannel()
        self.channel_value = self._common_content_configuration.get_memory_channel()
        self.socket_value = self._common_content_configuration.get_einj_mem_location_socket()
        self.dimm_slot = self._common_content_configuration.get_einj_mem_location_dimm()
        self.rank_value = self._common_content_configuration.get_einj_mem_location_rank()
        self.sub_rank_value = self._common_content_configuration.get_einj_mem_location_sub_rank()
        self.bank_group_value = self._common_content_configuration.get_einj_mem_location_bank_group()
        self.bank_value = self._common_content_configuration.get_einj_mem_location_bank()

    def prepare(self):
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        super(VerifyAdddcEnabledInSameBankDifferentDevices, self).prepare()

    def execute(self):
        """
        This method executes below:
            1.Enables SDDC sparing in sockets
            2.Executes mc.dimminfo and validating the output
            3.Executing klaxon.m2mem_errors and imc_errors and validating for 0 errors
            4.Halts and sets smmexitbreak =1
            5.Initialising ei object and executing memDevs.
            6.Injects correctable errors to the target rank/bank. After injection, correctable
            error count will increases and overflow flag will be set on the target rank.
            7.Makes the system go. Verifies SMI is seen in the debug/serial output.
            adddc_sparing should be enabled and the spare operation starts. Upon initiating
            the spare copy, the correctable error counter and overflow bit will be cleared by
            HW. PLUS1_RANK0.faildevice fields will indicate the failed DRAM device number
            8.Verifies the bank is mapped out by injecting an error to the same bank.
            No error should be injected.
            9.Changes the target device and injects error on the same bank as above.
            10. Injects 3 correctable errors to the target rank, same bank as above and verifies After
            injection, correctable error count will increases and overflow flag will be set on the target rank.
            11.Makes the system go. Verifies SMI is seen in the debug/serial output.
            adddc_sparing should be enabled and the spare operation starts and verifies Upon initiating
            the spare copy, the correctable error counter and overflow bit will be cleared by
            HW. PLUS1_RANK0.faildevice fields will indicate the failed DRAM device number
            12.Verifies the bank is mapped out by injecting an error to the same bank.
            13.Halts, Sets smmexitbreak=0 and resumes the system.
        """
        adddc_result_flag = []
        try:
            self.initialize_sv_objects()
            self.initialize_sdp_objects()
            self.SV._sv.socket0.uncore0.imc0_sparectl.spare_enable = 1
            self.SV._sv.socket0.uncore0.imc1_sparectl.spare_enable = 1
            spare_enable_cmd_result = self._cscripts.get_by_path(
                scope=self._cscripts.UNCORE,
                reg_path=self.SPARE_ENABLE_CMD_DICT[
                    self._cscripts.silicon_cpu_family].format(self.mc_value))
            if spare_enable_cmd_result == 0x1:
                self._log.info("Successfully verified Spare enable command")
                adddc_result_flag.append(True)
            else:
                self._log.error("Failed to verify spare enable command")
                adddc_result_flag.append(False)
            # Executing klaxon.m2mem_errors and imc_errors and validating for 0 errors
            if not self.check_system_error(self.ZERO_ERROR_SIGN_REGEX):
                self._log.info("No errors detected!")
            else:
                self._log.error("Memory Errors detected, Please check configuration")

            # Executing mc.dimminfo and validating the output
            if self.get_mc_dimm_info(self.REGEX_DIMM_INFO):
                self._log.info("All dimm information Validated.")
            else:
                log_err = "Please Check the Dimm Configuration"
                self._log.error(log_err)
                raise Exception(log_err)
            self._sdp.halt()
            self._sdp.itp.cv.smmexitbreak = 1

            # Initialising ei object and executing memDevs
            self._ei.memDevs(dev0=3, dev0msk=0x2, dev1=2, dev1msk=0x0)
            self._ei.resetInjectorLockCheck()
            self._ei._checkInjectorLock(True, True)
            time.sleep(10)

            # Injecting ce errors until the threshold value is set and validating the output of the error
            self._sdp.start_log(log_file_name=self.EI_LOG_FILE, mode="w")
            self._ei.injectMemError(socket=self.socket_value, channel=self.channel_value,
                                    dimm=self.dimm_slot, rank=self.rank_value, sub_rank=self.sub_rank_value,
                                    bank_group=self.bank_group_value, bank=self.bank_value, errType="ce")
            self._sdp.stop_log()

            with open(self.EI_LOG_FILE, "r") as ei_log:
                self._log.info("Checking the error log file")
                log_file = ei_log.read()  # Getting the error log
                #   Calling the Memory mirror utils object method to verify error
                self._log.info("Extracting the Error info from : {}".format(log_file))
                log_file_check_status = self._common_content_lib.extract_regex_matches_from_file(
                    log_file, self.REGEX_EI_LOG_FILE)
            if log_file_check_status:
                self._log.info("Error injected successfully!")
                adddc_result_flag.append(True)
            else:
                self._log.error("Issue in Error injection! Error log not found!")
                adddc_result_flag.append(False)

            # executing ras.adddc_status_check
            self._ras_common_obj.verify_adddc_status(adddc_status_check=False)

            for i in range(0, 2):
                # Injecting ce errors until the threshold value is set and validating the output of the error
                self._sdp.start_log(log_file_name=self.EI_LOG_FILE, mode="w")
                self._ei.injectMemError(socket=self.socket_value, channel=self.channel_value,
                                        dimm=self.dimm_slot, rank=self.rank_value, sub_rank=self.sub_rank_value,
                                        bank_group=self.bank_group_value, bank=self.bank_value, errType="ce")
                self._sdp.stop_log()

            with open(self.EI_LOG_FILE, "r") as ei_log:
                self._log.info("Checking the error log file")
                log_file = ei_log.read()  # Getting the error log
                #   Calling the Memory mirror utils object method to verify error
                self._log.info("Extracting the Error info from : {}".format(log_file))
                log_file_check_status = self._common_content_lib.extract_regex_matches_from_file(
                    log_file, self.REGEX_EI_LOG_FILE_AFTER_THREE_EI)
            if log_file_check_status:
                self._log.info("Error injected successfully!")
                adddc_result_flag.append(True)
            else:
                self._log.error("Issue in Error injection! Error log not found!")
                adddc_result_flag.append(False)

            # executing ras.adddc_status_check
            self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True, adddc_status_check_list=self.REGEX_RAS_ADDDC_STATUS_AFTER_EI)
            self._sdp.go()
            adddc_sparing_status = self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True, adddc_status_check_list=self.REGEX_ADDDC_SPARING_STATUS_CHECK)
            if adddc_sparing_status:
                self._log.info("adddc_sparing_status is successfully updated")
                adddc_result_flag.append(True)
            else:
                self._log.error("failed to find adddc_sparing_status")
                adddc_result_flag.append(False)

            # Injecting ce errors until the threshold value is set and validating the output of the error
            self._sdp.start_log(log_file_name=self.EI_LOG_FILE, mode="w")
            self._ei.injectMemError(socket=self.socket_value, channel=self.channel_value,
                                    dimm=self.dimm_slot, rank=self.rank_value, sub_rank=self.sub_rank_value,
                                    bank_group=self.bank_group_value, bank=self.bank_value, errType="ce")
            self._sdp.stop_log()

            with open(self.EI_LOG_FILE, "r") as ei_log:
                self._log.info("Checking the error log file")
                log_file = ei_log.read()  # Getting the error log
                #   Calling the Memory mirror utils object method to verify error
                self._log.info("Extracting the Error info from : {}".format(log_file))
                log_file_check_status = self._common_content_lib.extract_regex_matches_from_file(
                    log_file, self.REGEX_EI_LOG_FILE_MAPPING_OUT_BANK)
            if log_file_check_status:
                self._log.info("Error injected successfully!")
                adddc_result_flag.append(True)
            else:
                self._log.error("Issue in Error injection! Error log not found!")
                adddc_result_flag.append(False)
            # Changes the target device and injects another error to the same bank
            ei.memDevs(dev0=2, dev0msk=0x03)
            # Injecting ce errors until the threshold value is set and validating the output of the error
            # in Different device Same bank
            for i in range(0, 3):
                self._sdp.start_log(log_file_name=self.EI_LOG_FILE, mode="w")
                self._ei.injectMemError(socket=self.socket_value, channel=self.channel_value,
                                        dimm=self.dimm_slot, rank=self.rank_value, sub_rank=self.sub_rank_value,
                                        bank_group=self.bank_group_value, bank=self.bank_value, errType="ce")
                self._sdp.stop_log()

            with open(self.EI_LOG_FILE, "r") as ei_log:
                self._log.info("Checking the error log file in adjacent bank")
                log_file = ei_log.read()  # Getting the error log
                #   Calling the Memory mirror utils object method to verify error
                self._log.info("Extracting the Error info from : {}".format(log_file))
                log_file_check_status = self._common_content_lib.extract_regex_matches_from_file(
                    log_file, self.REGEX_EI_LOG_FILE_ADJ_BANK)
            if log_file_check_status:
                self._log.info("Error injected successfully!")
                adddc_result_flag.append(True)
            else:
                self._log.error("Issue in Error injection! Error log not found!")
                adddc_result_flag.append(False)

            self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True, adddc_status_check_list=self.REGEX_RAS_ADDDC_STATUS_AFTER_EI_ADJ_BANK)

            for i in range(0, 4):
                self._sdp.go()
                time.sleep(5)
            adddc_sparing_status = self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True, adddc_status_check_list=self.REGEX_ADDDC_SPARING_STATUS_CHECK)
            if adddc_sparing_status:
                self._log.info("adddc_sparing_status is successfully updated")
                adddc_result_flag.append(True)
            else:
                self._log.error("failed to find adddc_sparing_status")
                adddc_result_flag.append(False)

            self._sdp.start_log(log_file_name=self.EI_LOG_FILE, mode="w")
            self._ei.injectMemError(socket=self.socket_value, channel=self.channel_value,
                                    dimm=self.dimm_slot, rank=self.rank_value, sub_rank=self.sub_rank_value,
                                    bank_group=self.bank_group_value, bank=self.bank_value, errType="ce")
            self._sdp.stop_log()

            with open(self.EI_LOG_FILE, "r") as ei_log:
                self._log.info("Checking the error log file")
                log_file = ei_log.read()
                #   Calling the Memory mirror utils object method to verify error
                self._log.info("Extracting the Error info from : {}".format(log_file))
                log_file_check_status = self._common_content_lib.extract_regex_matches_from_file(
                    log_file, self.REGEX_EI_LOG_FILE_MAPPING_OUT_SAME_BANK_DIFF_DEVICE)
            if log_file_check_status:
                self._log.info("PASS: Error log found")
                adddc_result_flag.append(True)
            else:
                self._log.error("Error log not found, Error injection failed!")
                adddc_result_flag.append(False)
            self._sdp.halt()
            self._sdp.itp.cv.smmexitbreak = 0
            self._sdp.go()
            return all(adddc_result_flag)
        except Exception as ex:
            self._log.info("Exception Occured! ", str(ex))
            raise ex
        finally:
            self._sdp.go()

    def cleanup(self, return_status):
        super(VerifyAdddcEnabledInSameBankDifferentDevices, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if VerifyAdddcEnabledInSameBankDifferentDevices.main() else Framework.TEST_RESULT_FAIL)
