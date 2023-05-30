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


class VerifyAdddcEnabledNibbleErrorInjection(MemMirroringBaseTest):
    """
        Glasgow_id : G64806-inject_a_nibble_error_trigger_adddc_not_pcls
        This test injects correctable multibit errors till threshold is met and
        checks whether ADDDC was activated. PCLS should only work with a single-bit error injection
    """
    TEST_CASE_ID = ["G64806", "inject_a_nibble_error_trigger_adddc_not_pcls"]
    _BIOS_CONFIG_FILE = "pcls_bios_knobs.cfg"
    REGEX_DIMM_INFO = [r"(Directory Mode\s*\|\s*Off\s*\|\s*Off\s*\|\s*Off\s*\|)",
                       r"(ECC\s\/\sCAP\sChecking\s*\|\s*On\s\/\sOn\s*\|\s*On\s\/\sOn\s*\|\s*On\s\/\sOn\s*\|)"]
    REGEX_FOR_VALIDATING_CE_DEVMSK_EINJ = [
        r"(\s*Dev\s0\s\=\s*1\;\sXOR\smask\s\=\s0000000f)",
        r"(\s*Dev\s1\s\=\s*2\;\sXOR\smask\s\=\s00000000)",
        r"(1\snew\scorrectable\sHA\serror\sdetected)",
        r"(Detected\san\serror\son\sDDR\sbus\sDATA\sbit\s4\s\(Logical\sDRAM\sdevice\#\s1\sDATA\sbit\s0\))",
        r"(Detected\san\serror\son\sDDR\sbus\sDATA\sbit\s5\s\(Logical\sDRAM\sdevice\#\s1\sDATA\sbit\s1\))",
        r"(Detected\san\serror\son\sDDR\sbus\sDATA\sbit\s6\s\(Logical\sDRAM\sdevice\#\s1\sDATA\sbit\s2\))",
        r"(Detected\san\serror\son\sDDR\sbus\sDATA\sbit\s7\s\(Logical\sDRAM\sdevice\#\s1\sDATA\sbit\s3\))"]
    REGEX_RAS_ADDDC_STATUS_EI = [r"(\|\s*3\s*3\s*1\s*0\s*00\s\|)"]
    DMESG_SIG_CE = ["Hardware event. This is not a software error.", "Transaction: Memory read error", "Hardware Error"]
    REGEX_COPY_COMPLETE_STATUS_CHECK = [
        r"(\|\s*0\s*3\s*0\s*0\s*00\s\|)", r"(\|ADDDC\sfaildevice\s\=\s*1\s\(Rank\d\)\|)"]
    REGEX_COPY_PROGRESS_STATUS_CHECK = [
        r"(sparing\_patrol\_status\.copy\_in\_progress\s*=\s0x1\s\(Spare\sOperation\sin\sprogress\))",
        r"(sparing\_control\.adddc\_sparing\s*\=\s1)",
        r"(\|\s*0\s*3\s*0\s*0\s*00\s\|)", ]
    sparectl_cmd_dict = {
        ProductFamilies.CPX: "self.SV._sv.sockets.uncore0.imc{}_sparectl.spare_enable",
        ProductFamilies.SKX: "self.SV._sv.sockets.uncore0.imc{}_sparectl.spare_enable",
        ProductFamilies.SPR: "self.SV._sv.sockets.uncore0.memss.imc{}_sparectl.spare_enable",
        ProductFamilies.ICX: "self.SV._sv.sockets.uncore0.memss.imc{}_sparectl.spare_enable",
        ProductFamilies.CLX: "self.SV._sv.sockets.uncore0.memss.imc{}_sparectl.spare_enable"
    }
    err_status_cmd_dict = {
        ProductFamilies.CPX: "self.SV._sv.socket{}.uncore0.imc{}_c{}_correrrorstatus.err_overflow_stat",
        ProductFamilies.SKX: "self.SV._sv.socket{}.uncore0.imc{}_c{}_correrrorstatus.err_overflow_stat",
        ProductFamilies.CLX: "self.SV._sv.socket{}.uncore0.memss.mc{}.ch{}.correrrorstatus.err_overflow_stat",
        ProductFamilies.SPR: "self.SV._sv.socket{}.uncore0.memss.mc{}.ch{}.correrrorstatus.err_overflow_stat",
        ProductFamilies.ICX: "self.SV._sv.socket{}.uncore0.memss.mc{}.ch{}.correrrorstatus.err_overflow_stat"
    }
    spare_enable_cmd_dict = {
        ProductFamilies.CPX: "self.SV._sv.socket{}.uncore0.imc{}_sparing_control.spare_enable",
        ProductFamilies.SKX: "self.SV._sv.socket{}.uncore0.imc{}_sparing_control.spare_enable",
        ProductFamilies.SPR: "self.SV._sv.socket{}.uncore0.imc{}_sparing_control.spare_enable",
        ProductFamilies.ICX: "self.SV._sv.socket{}.uncore0.imc{}_sparing_control.spare_enable",
        ProductFamilies.CLX: "self.SV._sv.socket{}.uncore0.imc{}_sparing_control.spare_enable"
    }
    spare_enable_verify_cmd_dict = {
        ProductFamilies.CPX: "self.SV._sv.sockets.uncore0.imc{}_sparing_control.spare_enable",
        ProductFamilies.SKX: "self.SV._sv.sockets.uncore0.imc{}_sparing_control.spare_enable",
        ProductFamilies.SPR: "self.SV._sv.sockets.uncore0.imc{}_sparing_control.spare_enable",
        ProductFamilies.ICX: "self.SV._sv.sockets.uncore0.imc{}_sparing_control.spare_enable",
        ProductFamilies.CLX: "self.SV._sv.sockets.uncore0.imc{}_sparing_control.spare_enable"
    }
    ZERO_ERROR_SIGN_REGEX = r"0x0"
    _ERR_INJ_TIMEOUT = 5
    _RESUME_SYS_TIMEOUT = 3

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VerifyAdddcEnabledNibbleErrorInjection object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self._BIOS_CONFIG_FILE)
        super(VerifyAdddcEnabledNibbleErrorInjection, self).__init__(test_log, arguments, cfg_opts,
                                                                     bios_config_file)
        self.initialize_sv_objects()
        self.initialize_sdp_objects()
        self.mc_value = self._common_content_configuration.get_memory_micro_controller()
        self.channel_value = self._common_content_configuration.get_memory_channel()
        self.socket_value = self._common_content_configuration.get_memory_socket()
        self.dimm_slot = self._common_content_configuration.get_einj_mem_location_dimm()[0]
        self.rank_value = self._common_content_configuration.get_einj_mem_location_rank()[0]

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
        super(VerifyAdddcEnabledNibbleErrorInjection, self).prepare()

    def execute(self):
        """
        This method executes below:
            1. Sets sparing control spare_enable to 1 for Sockets and verifying the output
            2.Executing mc.dimminfo and validating the output
            3.Executing klaxon.m2mem_errors and imc_errors and validating for 0 errors
            4. Halts & Verifies the error status register
            5. Initialising ei object and executing memDevs
            6. Injecting ce errors until the threshold value is set and validating the output of the error
            7. executes ras.adddc_status_check for verifying spare copy complete and copy in progress status

        """
        adddc_flag = []
        try:
            # Sets sparing control spare_enable to 1 for Sockets
            exec(self.spare_enable_cmd_dict[self._cscripts.silicon_cpu_family].format(0, 0) + "=0x1")
            exec(self.spare_enable_cmd_dict[self._cscripts.silicon_cpu_family].format(0, 1) + "=0x1")
            exec(self.spare_enable_cmd_dict[self._cscripts.silicon_cpu_family].format(1, 0) + "=0x1")
            exec(self.spare_enable_cmd_dict[self._cscripts.silicon_cpu_family].format(1, 1) + "=0x1")
            exec(self.sparectl_cmd_dict[self._cscripts.silicon_cpu_family].format(0) + "=1")
            exec(self.sparectl_cmd_dict[self._cscripts.silicon_cpu_family].format(1) + "=1")

            # Verifying the spare enable value
            mc0_status = eval(self.spare_enable_verify_cmd_dict[self._cscripts.silicon_cpu_family].format(0))
            mc1_status = eval(self.spare_enable_verify_cmd_dict[self._cscripts.silicon_cpu_family].format(1))
            sparectl_status_mc0 = eval(self.sparectl_cmd_dict[self._cscripts.silicon_cpu_family].format(0))
            sparectl_status_mc1 = eval(self.sparectl_cmd_dict[self._cscripts.silicon_cpu_family].format(1))
            print(mc0_status, mc1_status, sparectl_status_mc0, sparectl_status_mc1)
            if mc1_status == 0x1 and mc0_status == 0x1 and sparectl_status_mc1 == 0x1 and sparectl_status_mc0 == 0x1:
                self._log.info("Verified Spare enabled status Successfully")
                adddc_flag.append(True)
            else:
                self._log.error("Failed to verify Spare enabled status")
                adddc_flag.append(False)

            # Executing mc.dimminfo and validating the output
            if self.get_mc_dimm_info(self.REGEX_DIMM_INFO):
                self._log.info("All dimm information Validated.")
                adddc_flag.append(True)
            else:
                log_err = "Please Check the Dimm Configuration"
                adddc_flag.append(False)
                self._log.error(log_err)
                raise Exception(log_err)

            # Halts & Verifies the error status register
            self.SDP.halt()
            for i in range(3):
                err_status_s0_imc0 = eval(
                    self.err_status_cmd_dict[self._cscripts.silicon_cpu_family].format(0, 0, i))
                err_status_s0_imc1 = eval(
                    self.err_status_cmd_dict[self._cscripts.silicon_cpu_family].format(0, 1, i))
                err_status_s1_imc0 = eval(
                    self.err_status_cmd_dict[self._cscripts.silicon_cpu_family].format(1, 0, i))
                err_status_s1_imc1 = eval(
                    self.err_status_cmd_dict[self._cscripts.silicon_cpu_family].format(1, 1, i))
                if err_status_s0_imc0 == 0x0 and err_status_s0_imc1 == 0x0 and \
                        err_status_s1_imc0 == 0x0 and err_status_s1_imc1 == 0x0:
                    self._log.info("Error Overflow Status is 0 as expected")
                    adddc_flag.append(True)
                else:
                    adddc_flag.append(False)
                    self._log.error("Failed to verify Error Overflow Status")
                    raise Exception("Failed to verify Error Overflow Status")

            # Executing klaxon.m2mem_errors and imc_errors and validating for 0 errors
            if not self.check_system_error(self.ZERO_ERROR_SIGN_REGEX):
                self._log.info("No errors detected!")
                adddc_flag.append(True)
            else:
                adddc_flag.append(False)
                self._log.error("Memory Errors detected, Please check configuration")

            # Initialising ei object and executing memDevs
            self._ei.memDevs()
            self._ei.memDevs(dev0=1, dev0msk=0x0000000f, dev1=2, dev1msk=0x00000000)

            # executing ras.adddc_status_check
            self._ras_common_obj.verify_adddc_status(adddc_status_check=False)

            # Injecting ce errors until the threshold value is set and validating the output of the error
            for iteration in range(3):
                self._sdp.start_log(self._MEM_LOG_FILE, "w")
                print("iteration {}".format(iteration + 1))
                self._ei.injectMemError(socket=self.socket_value, channel=self.channel_value,
                                        dimm=self.dimm_slot, rank=self.rank_value, errType='x4sddc')
                self._sdp.stop_log()
                time.sleep(self._ERR_INJ_TIMEOUT)
            # Validates the error injection log from console
            with open(self._MEM_LOG_FILE, "r") as error_log:
                self._log.info("Checking the error log file")
                err_log_read = error_log.read()  # Getting the error log
                self._log.info("Extracting the error log info from : {}".format(err_log_read))
                error_check_status = self._common_content_lib.extract_regex_matches_from_file(
                    err_log_read, self.REGEX_FOR_VALIDATING_CE_DEVMSK_EINJ)
                if error_check_status:
                    adddc_flag.append(True)
                    self._log.info("Validation of error log: PASS")
                else:
                    adddc_flag.append(False)
                    self._log.error("Validation of error log: Fail")

            # executing ras.adddc_status_check for verifying overflow flag
            self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True, adddc_status_check_list=self.REGEX_RAS_ADDDC_STATUS_EI)
            self._log.info("Resuming the device!")
            self.SDP.go()
            time.sleep(self._RESUME_SYS_TIMEOUT)
            self._log.info("Verifying Sparing enable copy in progress status:")
            copy_progress_status = self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True, adddc_status_check_list=self.REGEX_COPY_PROGRESS_STATUS_CHECK)
            if copy_progress_status:
                adddc_flag.append(True)
                self._log.info("Spare Operation is in progress")
            else:
                adddc_flag.append(False)
                self._log.error("failed to find spare operation is in progress")
            self._log.info("Resume the device: ")
            self.SDP.go()
            time.sleep(self._ERR_INJ_TIMEOUT)
            self._log.info("Verifying Sparing enable copy Complete status:")
            copy_progress_status = self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True, adddc_status_check_list=self.REGEX_COPY_COMPLETE_STATUS_CHECK)
            if copy_progress_status:
                adddc_flag.append(True)
                self._log.info("Spare Operation is Complete")
            else:
                adddc_flag.append(False)
                self._log.error("failed to find spare operation is Complete")
            if self._os_log_obj.verify_os_log_error_messages(
                    __file__, self._os_log_obj.DUT_MESSAGES_FILE_NAME, self.DMESG_SIG_CE):
                self._log.info("Successfully injected memory correctable error, Error log found.")
                adddc_flag.append(True)
            else:
                adddc_flag.append(False)
                log_err = "Error Not found in OS logs! error expected in OS logs when injecting Memory CE"
                self._log.error(log_err)
                raise Exception(log_err)

            return all(adddc_flag)

        except Exception as ex:
            raise Exception("Exception Occurred: ", str(ex))
        finally:
            self.SDP.go()

    def cleanup(self, return_status):
        super(VerifyAdddcEnabledNibbleErrorInjection, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if VerifyAdddcEnabledNibbleErrorInjection.main() else Framework.TEST_RESULT_FAIL)
