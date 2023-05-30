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
import re
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework, ProductFamilies

from src.lib.install_collateral import InstallCollateral
from src.ras.tests.mem_mirroring.mem_mirroring_common import MemMirroringBaseTest


class VerifyStressTrafficAfterDegradedStateMemSddc(MemMirroringBaseTest):
    """
    Glasgow_id : G62126-Stress Traffic after Degraded State- Memory SDDC
    This test case injects memory correctable error and verifies SDDC +1 MCA logs in CScripts and logs reported in OS.
.
    """
    TEST_CASE_ID = ["G62126", "Stress Traffic after Degraded State- Memory SDDC"]
    BIOS_CONFIG_FILE = "sddc_plus1_cscripts_cpx.cfg"
    ZERO_ERROR_SIGN_REGEX = r"0x0"
    REGEX_ADDDC_STATUS_CHECK_AFTER_EI = [
        r"(sparing\_patrol\_status\.copy\_complete\s*\=\s0x1\s\(Spare\sOperation\sComplete\))",
        r"(sparing\_control\.sddc\_sparing\s*\=\s1)"]
    sparectl_cmd_dict = {
        ProductFamilies.CPX: "self.SV._sv.sockets.uncore0.imc{}_sparectl.spare_enable",
        ProductFamilies.SKX: "self.SV._sv.sockets.uncore0.imc{}_sparectl.spare_enable",
        ProductFamilies.SPR: "self.SV._sv.sockets.uncore.memss.imc{}_sparectl.spare_enable",
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
    _RESUME_TIMEOUT = 10
    _WAITING_TIMEOUT = 600
    _ERR_INJ_TIMEOUT = 5
    DEV0_MSK_VALUE = 0xf
    DEV1_MSK_VALUE = 0x0
    DEV0_MSK_VALUE1 = 0x1
    DEV0_VALUE = 3
    CORE_ADDR = 0x1000
    REGEX_DIMM_INFO = [r"(Directory\sMode\s*\|\s*Off\s*\|\s*Off\s*\|\s*Off\s*\|)"]
    REGEX_ADDDC_STATUS_CHECK_BEFORE_EI = [
        r"(sparing\_control\.sddc\_sparing\s*\=\s*0)",
        r"(sparing\_control\.channel\_select\s*\=\s*0)",
        r"(sparing\_control\.region\_size\s*\=\s0)",
        r"(sparing\_patrol\_status\.copy\_complete\s*\=\s*0x0)",
        r"(sparing\_patrol\_status\.copy\_in\_progress\s*\=\s*0x0)"]
    REGEX_ADDDC_STATUS_CHECK_COPY_COMPLETE = [
        # r"(sparing\_patrol\_status\.copy\_complete\s*\=\s0x1\s\(Spare\sOperation\sComplete\))",
        r"(sparing\_control\.sddc\_sparing\s*\=\s1)"]
    REGEX_ADDDC_STATUS_CHECK_COPY_PROGRESS = [
        r"(sparing\_control\.sddc\_sparing\s*\=\s*1)",
        r"(sparing\_control\.region\_size\s*\=\s1)",
        r"(sparing\_patrol\_status\.copy\_in\_progress\s*\=\s0x1\s\(Spare\sOperation\sin\sprogress\))"
    ]
    REGEX_ADDDC_STATUS_CHECK_THRESHOLD_AFTER_EI = [
        r"(\|\s*3\s*3\s*1\s*0\s*00\s\|)"
    ]
    DMESG_SIG_CE = ["Hardware event. This is not a software error.", "Transaction: Memory read error",
                    "Hardware Error"]
    REGEX_FOR_CE_EXCEEDING_THRESHOLD = [r"(0\snew\scorrectable\sHA\serror\sdetected)"]
    REGEX_FOR_VALIDATING_CE_DEVMSK_EINJ = [
        r"(1\snew\scorrectable\sHA\serror\sdetected)",
        r"(Fail\sDRAM\sdevice\snum\s:\s1)",
        r"(Detected\san\serror\son\sDDR\sbus\sDATA\sbit\s4\s\(Logical\sDRAM\sdevice\#\s1\sDATA\sbit\s0\))",
        r"(Detected\san\serror\son\sDDR\sbus\sDATA\sbit\s5\s\(Logical\sDRAM\sdevice\#\s1\sDATA\sbit\s1\))",
        r"(Detected\san\serror\son\sDDR\sbus\sDATA\sbit\s6\s\(Logical\sDRAM\sdevice\#\s1\sDATA\sbit\s2\))",
        r"(Detected\san\serror\son\sDDR\sbus\sDATA\sbit\s7\s\(Logical\sDRAM\sdevice\#\s1\sDATA\sbit\s3\))"
        ]
    ERROR_SIGN_REGEX = r"\s*errortype\s\[20\:11\]\s=\s0x2\s\-\-\>\sBit\s1\:\sTxn\shad\san\sECC\scorrected\serror\s\(corrected\sby\sECC\sduring\sretry\)\;"
    TOP_CMD = r"top -1 -n 5 -b| grep 'load average:'"
    REGEX_TOP_CMD_OUTPUT = r"load\saverage\:\s0\.00\,\s0\.00\,\s0\.00"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VerifyStressTrafficAfterDegradedStateMemSddc object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE)
        super(VerifyStressTrafficAfterDegradedStateMemSddc, self).__init__(test_log, arguments, cfg_opts,
                                                                           bios_config_file)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        """
        Creates a new VerifyStressTrafficAfterDegradedStateMemSddc object and we are calling a Prepare function
        Prepare Function does the Following tasks:
            1. Set the bios knobs to its default mode.
            2. Set the bios knobs as per the test case.
            3. Reboot the SUT to apply the new bios settings.
            4. Verify the bios knobs that are set.
        :return: None
        """
        super(VerifyStressTrafficAfterDegradedStateMemSddc, self).prepare()
        self.initialize_sv_objects()
        self.initialize_sdp_objects()

    def execute(self):
        """
        This Method is Used to execute below:
        1. Executes mc.dimminfo and validating the output
        2. Executes klaxon.m2mem_errors and imc_errors and validating for 0 errors
        3. Executes ras.adddc_status_check and validating output
        4. Initialises ei object and executing memDevs
        5. Injects mem errors until the threshold value is set and validating the output of the error
        6. Executes ras.adddc_status_check for copy_complete and threshold values
        7. Injects Mem Error and validating the error injection output
        8. Executes Klaxon.m2mem_errors for validating the memory error detected
        9. Execute Stress App Test and Observes the "top" session for "Load Average" values.

        :return: True or False
        """
        sddc_stress_traffic_flag = []
        usage_data = []
        try:
            # Executing mc.dimminfo and validating the output
            if self.get_mc_dimm_info(self.REGEX_DIMM_INFO):
                self._log.info("All dimm information Validated.")
                sddc_stress_traffic_flag.append(True)
            else:
                sddc_stress_traffic_flag.append(False)
                log_err = "Please Check the Dimm Configuration"
                self._log.error(log_err)
                raise Exception(log_err)
            # Executing klaxon.m2mem_errors and imc_errors and validating for 0 errors
            if not self.check_system_error(self.ZERO_ERROR_SIGN_REGEX):
                self._log.info("No errors detected!")
                sddc_stress_traffic_flag.append(True)
            else:
                sddc_stress_traffic_flag.append(False)
                self._log.error("Memory Errors detected, Please check configuration")
            # Initialising ei object and executing memDevs
            self._ei.memDevs()
            self._ei.memDevs(dev0=1)
            self._ei.memDevs(dev0msk=self.DEV0_MSK_VALUE)
            self._ei.memDevs(dev1msk=self.DEV1_MSK_VALUE)
            # executing ras.adddc_status_check and validating output
            self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True, adddc_status_check_list=self.REGEX_ADDDC_STATUS_CHECK_BEFORE_EI)
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
            # print(mc0_status, mc1_status, sparectl_status_mc0, sparectl_status_mc1)
            if mc1_status == 0x1 and mc0_status == 0x1 and sparectl_status_mc1 == 0x1 and sparectl_status_mc0 == 0x1:
                self._log.info("Verified Spare enabled status Successfully")
                sddc_stress_traffic_flag.append(True)
            else:
                self._log.error("Failed to verify Spare enabled status")
                sddc_stress_traffic_flag.append(False)

            self.SDP.halt()
            # Injecting mem errors until the threshold value is set and validating the output of the error
            for iteration in range(3):
                self.SDP.start_log(self._MEM_LOG_FILE, "w")
                print("iteration {}".format(iteration + 1))
                self._ei.injectMemError(self.CORE_ADDR, errType="ce")
                self.SDP.stop_log()
                time.sleep(self._ERR_INJ_TIMEOUT)
            # Validates the error injection log from console
            with open(self._MEM_LOG_FILE, "r") as error_log:
                self._log.info("Checking the error log file")
                err_log_read = error_log.read()  # Getting the error log
                self._log.info("Extracting the error log info from : {}".format(err_log_read))
                error_check_status = self._common_content_lib.extract_regex_matches_from_file(
                    err_log_read, self.REGEX_FOR_VALIDATING_CE_DEVMSK_EINJ)
                if error_check_status:
                    sddc_stress_traffic_flag.append(True)
                    self._log.info("Validation of error log: PASS")
                else:
                    sddc_stress_traffic_flag.append(False)
                    self._log.error("Validation of error log: Fail")

            # Executing ras.adddc_status_check and validating the output
            self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True,
                adddc_status_check_list=self.REGEX_ADDDC_STATUS_CHECK_THRESHOLD_AFTER_EI)

            # Executing ras.adddc_status_check for copy_complete and threshold values
            self.SDP.go()
            self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True,
                adddc_status_check_list=self.REGEX_ADDDC_STATUS_CHECK_COPY_PROGRESS)
            self.SDP.start_log(self._MEM_LOG_FILE, "w")
            self._ei.injectMemError(self.CORE_ADDR, errType="ce")
            self.SDP.stop_log()
            time.sleep(self._ERR_INJ_TIMEOUT)
            # Validates the error injection log from console
            with open(self._MEM_LOG_FILE, "r") as error_log:
                self._log.info("Checking the error log file")
                err_log_read = error_log.read()  # Getting the error log
                self._log.info("Extracting the error log info from : {}".format(err_log_read))
                error_check_status = self._common_content_lib.extract_regex_matches_from_file(
                    err_log_read, self.REGEX_FOR_CE_EXCEEDING_THRESHOLD)
                if error_check_status:
                    sddc_stress_traffic_flag.append(True)
                    self._log.info("Validation of error log: PASS")
                else:
                    sddc_stress_traffic_flag.append(False)
                    self._log.error("Validation of error log: Fail")
            self._ras_common_obj.verify_adddc_status(
                adddc_status_check=True,
                adddc_status_check_list=self.REGEX_ADDDC_STATUS_CHECK_COPY_COMPLETE)

            for i in range(3):
                print("Resuming the system!")
                self.SDP.go()
                time.sleep(self._RESUME_TIMEOUT)
            if not self._os.is_alive():
                self._log.info("os not alive!, Waiting for OS to come alive")
                self._os.wait_for_os(self._WAITING_TIMEOUT)

            # Executing the klaxon.m2mem_errors and imc_errors and validating the output
            if not self.check_system_error(self.ERROR_SIGN_REGEX):
                self._log.info("Memory Errors detected successfully!")
                sddc_stress_traffic_flag.append(True)
            else:
                sddc_stress_traffic_flag.append(False)
                self._log.error("No errors detected!")
            if self._os_log_obj.verify_os_log_error_messages(__file__,
                                                             self._os_log_obj.DUT_MESSAGES_FILE_NAME,
                                                             self.DMESG_SIG_CE):
                self._log.info("Success: Memory CE not Injected after exceeding threshold")
                sddc_stress_traffic_flag.append(True)
            else:
                sddc_stress_traffic_flag.append(False)
                log_err = "Error Not found in OS logs! error expected in OS logs when injecting Memory CE"
                self._log.error(log_err)
                raise Exception(log_err)
            # Installing stressapp test
            self._log.info("Installs the stress test APP")
            self._install_collateral.install_stress_test_app()
            self._ras_common_obj.execute_stress_app(
                self._common_content_configuration.memory_stress_test_execute_time())

            # Executing top command and validating load average value
            output_txt = self._common_content_lib.execute_sut_cmd(self.TOP_CMD, self.TOP_CMD, self._command_timeout)
            time.sleep(self._ERR_INJ_TIMEOUT)
            self._log.debug("Result of top command is :{}".format(output_txt))
            top_cmd_data = [cmd_data.strip() for cmd_data in output_txt.split("\n") if cmd_data != ""]
            # for valid_data in top_cmd_data:
            usage_data.append(str(bool(ele for ele in top_cmd_data if ele not in self.REGEX_TOP_CMD_OUTPUT)))
            if all(usage_data):
                sddc_stress_traffic_flag.append(True)
                self._log.info("Load average is showing output in top command")
            else:
                sddc_stress_traffic_flag.append(False)
                self._log.error("Load average is showing 0 output in top command")
            print(sddc_stress_traffic_flag)
            return all(sddc_stress_traffic_flag)

        except Exception as ex:
            self._log.error("Exception Occured: ", str(ex))
        finally:
            self.SDP.go()
            self.SDP.stop_log()

    def cleanup(self, return_status):
        super(VerifyStressTrafficAfterDegradedStateMemSddc, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if VerifyStressTrafficAfterDegradedStateMemSddc.main() else Framework.TEST_RESULT_FAIL)
