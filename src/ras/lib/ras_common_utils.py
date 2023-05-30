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
import re
import time

from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.lib.common_content_lib import CommonContentLib


class RasCommonUtil:
    """
    This class is for common Ras util.
    """

    DELTA = 30
    WAIT_FOR_OS = 800
    AC_TIME_OUT_DELAY = 3
    DELAY_AFTER_REBOOT_IN_SEC = 20
    ITP_LOG_FILE = "itp_log_file.log"
    DELAY_BETWEEN_AC_POWER_POWER_CYCLE_IN_SEC = 15
    _LINUX_USR_ROOT_PATH = "/root"
    _CMD_FOR_STRESS_TIME_OUT_IN_SEC = 4000
    _CMD_FOR_LOAD_AVG = "cat /proc/loadavg"
    _CMP_LOAD_AVERAGE_BEFORE_STRESSAPP = 1
    _CMD_FOR_STRESS_APP = "./stressapptest -s {} -F -l stress.log "
    _UC_ON_BOTH_CH_KLAXON_MEM_SIG = ["0x00000304 : errortype", "uc = 0x1", "corr_err = 0x1"]
    _UC_ON_BOTH_CH_KLAXON_M2MEM_SIG = ["uc [61] = 0x1", "errortype [20:11] = 0x4"]
    _UC_KLAXON_MEM_SIG = ["0x0000030c : errortype", "0x00000001 : mirrorcorrerr"]
    _UC_KLAXON_M2MEM_SIG = ["corrcount [52:38] = 0x1", "errortype [20:11] = 0xc"]
    _UC_ERROR_LOG_SIG = ["mirrored memory", "Uncorrected error", "Hardware event", "Error enabled"]
    _UC_ERROR_LOG_MIROR_FAILOVER_SIG = ["Corrected error", "Error enabled", "Memory read error", "Hardware event"]
    _STRESS_TRAFFIC_AFTER_DEGRADED_STATE_OS_SIG = ["kernel: mce", "mcelog"]
    _UPI_LLR_16B_CRC_ERROR = ["Hardware Error", "Corrected error", "LL Rx detected CRC error",
                              "successful LLR without Phy Reinit"]


    _UC_ERROR_ON_BOTH_CHANNEL = {
        ProductFamilies.SKX: [0x0, 0x4, 0x0],
        ProductFamilies.CLX: [0x0, 0x4, 0x0],
        ProductFamilies.CPX: [0x0, 0x4, 0x0],
        ProductFamilies.ICX: [0x0, 0x304, 0x0],
        ProductFamilies.SPR: [0x0, 0x304, 0x0]
    }

    _MIRROR_FAILOVER_SIGN = ["Mirror Failover", "SSR state Save! Flag:0", "stop and save patrol scrub info",
                             "Mirror Failover mailbox call successful"]
    _UC_ERROR_ON_PRI_CH_LOG_SIG = ["mirrored memory", "Corrected error", "Hardware event",
                                   "Transaction: Memory read error"]
    _CE_ERROR_LOG_SIG = ["mirrored memory", "Corrected error"]  # ADDR xxxxxxxx : Append Run time based on Mirror Addr

    REGEX_EINJ_STRESSAPPTEST_LOG = ["Status: PASS - please verify no corrected errors"]
    _EINJ_CE_ERROR_LOG_SIG = ["Error 0", "type: corrected", "Hardware Error", "event severity: corrected"]

    _EINJ_UCE_ERROR_LOG_SIG = ["event severity: recoverable", "Uncorrected error", "Hardware Error"]

    _CE_ERROR_ON_PRI_CHANNEL = {
        ProductFamilies.SKX: [0x1, 0xa, 0x0],
        ProductFamilies.CLX: [0x1, 0xa, 0x0],
        ProductFamilies.CPX: [0x1, 0xa, 0x0],
        ProductFamilies.ICX: [0x0, 0x0, 0x0],
        ProductFamilies.SPR: [0x0, 0x0, 0x0]
    }
    _UC_ERR_ON_PRI_CH_WITHOUT_FAILOVER = {
        ProductFamilies.SKX: [0x1, 0xc, 0x0],
        ProductFamilies.CLX: [0x1, 0xc, 0x0],
        ProductFamilies.CPX: [0x1, 0xc, 0x0],
        ProductFamilies.ICX: [0x1, 0x30c, 0x0],
        ProductFamilies.SPR: [0x1, 0x30c, 0x0]
    }
    _UC_ERR_ON_SEC_CH_WITHOUT_FAILOVER = {
        ProductFamilies.SKX: [0x1, 0xa, 0x0],
        ProductFamilies.CLX: [0x1, 0xa, 0x0],
        ProductFamilies.CPX: [0x1, 0xa, 0x0],
        ProductFamilies.ICX: [0x0, 0x0, 0x0],
        ProductFamilies.SPR: [0x0, 0x0, 0x0],
    }
    _UC_ERR_ON_PRI_FAILOVER = {
        ProductFamilies.SKX: [0x0, 0x14, 0x1],
        ProductFamilies.CLX: [0x0, 0x14, 0x1],
        ProductFamilies.CPX: [0x0, 0x14, 0x1],
        ProductFamilies.ICX: [0x0, 0x314, 0x1],
        ProductFamilies.SPR: [0x0, 0x314, 0x1]
    }
    _UC_ON_PRI_CHANNEL = {
        ProductFamilies.SKX: [0x1, 0xc, 0x0],
        ProductFamilies.CLX: [0x1, 0xc, 0x0],
        ProductFamilies.CPX: [0x1, 0xc, 0x0],
        ProductFamilies.ICX: [0x1, 0xc, 0x0],
        ProductFamilies.SPR: [0x1, 0xc, 0x0]
    }
    _UC_ON_PRI_CE_ON_SEC ={
        ProductFamilies.SKX: [0x1, 0xe, 0x0],
        ProductFamilies.CLX: [0x1, 0xe, 0x0],
        ProductFamilies.CPX: [0x1, 0xe, 0x0],
        ProductFamilies.ICX: [0x1, 0xe, 0x0],
        ProductFamilies.SPR: [0x1, 0xe, 0x0]
    }
    RAS_ADDDC_LOG_FILE = "ras_adddc_status_log.txt"

    def __init__(self, log, os, cfg_opts, common_content_config, bios_util=None, csp= None, sdp= None):
        self._log = log
        self._os = os
        self._cfg = cfg_opts
        self._bios_util = bios_util
        self._reboot_time = self._reboot_time = common_content_config.get_reboot_timeout()
        self._common_content_config = common_content_config
        self._csp = csp
        self._sdp = sdp
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

    def ac_cycle_if_os_not_alive(self, ac_obj, auto_reboot_expected=False):
        """
        If auto reboot is expected, then wait for SUT to respond
        If auto reboot is not expected, then check and forcefully power cycle SUT

        :param auto_reboot_expected:   True or False
        :raise: Exception if system will not respond.
        :return: None
        """
        try:
            if auto_reboot_expected is True:
                self._log.info("Ensure system is alive within (%d) seconds...", self._reboot_time)
                count = int(self._reboot_time / self.DELTA)
                for x in range(count):
                    time.sleep(self.DELTA)
                    if self._os.is_alive():
                        self._log.info("OS responded successfully")
                        return
                    else:
                        self._log.info("OS has not yet responded. Retrying...")

            self._log.info("Checking OS has responded or not...")
            # Check if system is alive or not
            # Power cycle system if not alive and wait till system becomes alive
            time.sleep(self.DELAY_BETWEEN_AC_POWER_POWER_CYCLE_IN_SEC)
            if self._os.is_alive():
                self._log.info("OS responded successfully")
            else:
                self._log.info("OS failed to respond. AC cycling...")
                self._common_content_lib.perform_graceful_ac_off_on(ac_power=ac_obj)
                self._os.wait_for_os(self._reboot_time)
                time.sleep(self.DELAY_AFTER_REBOOT_IN_SEC)

        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def set_and_verify_bios_knobs(self):
        """
        This method is to set the bios knobs and verify the bios knobs.

        return: None
        """
        try:
            self._log.info("Set the Bios Knobs to Default Settings")
            self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
            self._log.info("Set the Bios Knobs as per our Test Case Requirements")
            self._bios_util.set_bios_knob()  # To set the bios knob setting.
            self._log.info("Bios Knobs are Set as per our TestCase and Reboot to Apply the Settings")
            self._sdp.pulse_pwr_good()
            self._os.wait_for_os(self._reboot_time)
            self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def log_klaxon_machine_check_errors(self, klaxon_machine_signature_list=None, error_validate=False):
        """
        This method is to show the Machine Check Error.

        :param: klaxon_machine_signature_list : Machine error signature list which is to validate.
        :param: error_validate : Validate the signature if True else only Log the error.
        :return: True if signature found in Log else False.
        :raise: RuntimeError
        """
        try:
            machine_signature_list = []
            klaxon = self._csp.get_klaxon_object()
            self._sdp.halt()
            time.sleep(self._common_content_config.itp_halt_time_in_sec())
            self._log.info("Machine Check Error")

            #   Going to open the cscript log file to capture the machine check error output
            self._sdp.start_log(self.ITP_LOG_FILE, "w")
            if self._common_content_lib.get_platform_family() in self._common_content_lib.SILICON_10NM_CPU:
                machine_signature_list=klaxon_machine_signature_list
                klaxon.check_machine_check_errors()
            self._sdp.stop_log()

            with open(self.ITP_LOG_FILE, "r") as mirroring_log:
                self._log.info("Checking the log file")
                machine_check_errors_log = mirroring_log.read()  # Getting the machine error log
                self._log.info(machine_check_errors_log)
                ret_val = True
            if error_validate:
                ret_val = self.check_signature_in_log_file(machine_check_errors_log, machine_signature_list)
            return ret_val

        except Exception as ex:
            log_error = "An exception occurred:\n{}".format(str(ex))
            self._log.error(log_error)
            raise RuntimeError(log_error)
        finally:
            self._sdp.go()

    def log_klaxon_memory_errors(self, klaxon_m2mem_file_signature_list=None, klaxon_mem_error_signature_list=None,
                                 error_validate_flag=False):
        """
        This Function is to check the memory error in klaxon.

        :param: klaxon_m2meme_file : list of signature in m2mem which is to check.
        :param: klaxon_mem_error : list of signature in mem error command to check.
        :param: error_validate_flag : if true it will validate the log else it will only log to log file.
        :return: True if signature found in log else False.
        :raise: RuntimeError
        """
        try:
            klaxon = self._csp.get_klaxon_object()
            self._sdp.halt()
            self._sdp.start_log(self.ITP_LOG_FILE, "w")
            if self._common_content_lib.get_platform_family() in self._common_content_lib.SILICON_14NM_FAMILY:
                klaxon_signature_list = klaxon_m2mem_file_signature_list
                klaxon.m2mem_errors()
            else:
                klaxon_signature_list = klaxon_mem_error_signature_list
                klaxon.check_mem_errors()
            self._sdp.stop_log()
            with open(self.ITP_LOG_FILE, 'r') as klaxon_log:
                klaxon_mem_log = klaxon_log.read()
                self._log.info(klaxon_mem_log)
                ret_val = True
            if error_validate_flag:
                ret_val = self.check_signature_in_log_file(klaxon_mem_log, klaxon_signature_list)
            return ret_val
        except Exception as ex:
            log_err = "An Exception Occurred :{}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

        finally:
            self._sdp.go()

    def check_signature_in_log_file(self, output_file_log, error_signature_list_to_parse):
        """
        This function is to validate the signature in Log.

        :param: output_file_log: out put Log where signature need to be search.
        :param: error_signatue_list_to_parse: list of error which is to search.
        :return: True if all string found else False.
        :raise: RuntimeError.
        """
        found = 0
        try:
            for string_to_look in error_signature_list_to_parse:
                self._log.info("Looking for [%s]", string_to_look)
                if re.findall(string_to_look, output_file_log.strip(), re.IGNORECASE | re.MULTILINE):
                    self._log.info(" String found")
                    found = found + 1
                else:
                    self._log.error(" String Not found")

            if found == len(error_signature_list_to_parse):
                self._log.info("All the strings from the list are found")
                self._log.info("exp %d act %d", len(error_signature_list_to_parse), found)
                verified_log_error_messages_bool = True
            else:
                self._log.error("All the strings from the list are NOT found")
                self._log.info("exp %d act %d", len(error_signature_list_to_parse), found)
                verified_log_error_messages_bool = False

            return verified_log_error_messages_bool

        except Exception as ex:
            log_err = "An Exception Occurred :{}".format(ex)
            self._log.error(log_err)
            raise RuntimeError(log_err)

    def inject_memory_error(self, err_addr=None, error_type=None, Inject2ndChannel= False,
                                one_Injection=True, Imm_Consume=True, imm_Inject=True, error_signature_file_list=None,
                                   error_validate_flag=False):
        """
        This method is to inject the MemError.

        :param: err_addr: Address to inject format: 0x12345678
        :param: error_type: Error type to inject, "ce"-correctable, "uce"- uncorrectable,
                            "mirror_uce" - mirror uncorrectable.
        :param: Inject2Channel: Error Inject on 2nd Channel
        :param: one_Injection: perform a single injection; do not keep injection enabled continuously
        :param: Imm_Consume: read newly injected error immediately,  else leave error in memory for scrub or another
                            app to find.
        :param: imm_Inject: inject error immediately, else leave injectors armed for some other agent to inject at a
                            later time
        :param: error_signature_file_list: signature list which need to validate in log.
        :param: error_validate_flag: True if need to validate signature else False.

        :return: True if all signature found in error else False.
        :raise: RuntimeError
        """
        try:
            ei = self._csp.get_cscripts_utils().get_ei_obj()
            self._sdp.halt()
            self._sdp.start_log(self.ITP_LOG_FILE, "w")
            ei.injectMemError(addr=err_addr, errType=error_type, Inj2ndCh=Inject2ndChannel, oneInjection=
                                                    one_Injection, immConsume=Imm_Consume, immInject=imm_Inject)
            self._sdp.stop_log()
            with open(self.ITP_LOG_FILE, 'r') as memory_error_log:
                err_log = memory_error_log.read()
                self._log.info(err_log)
                ret_val = True

            if error_validate_flag:
                ret_val = self.check_signature_in_log_file(err_log, error_signature_file_list)

            return ret_val
        except Exception as ex:
            log_err = "An Exception Occurred : {}".format(str(ex))
            self._log.error(log_err)
            raise RuntimeError(log_err)

        finally:
            self._sdp.go()

    def execute_stress_app(self, stress_app_execute_time):
        """
        This Function is use to execute the stress App execution.

        :param: stress_app_execute_time: param for time
        :return: None
        :raise: RuntimeError
        """
        try:
            ret_cmd = self._os.execute(self._CMD_FOR_LOAD_AVG, self._common_content_config.get_command_timeout(),
            cwd=self._LINUX_USR_ROOT_PATH)
            if ret_cmd.cmd_failed():
                log_err = "Failed to run command '{}' with return = '{}' and std_error='{}'..".format(
                    self._CMD_FOR_LOAD_AVG, ret_cmd.return_code, ret_cmd.stderr)
                self._log.error(log_err)
                raise log_err

            self._log.info("Starting the stress app  test")
            command_line = self._CMD_FOR_STRESS_APP.format(stress_app_execute_time)
            result_verify = self._os.execute(command_line, self._CMD_FOR_STRESS_TIME_OUT_IN_SEC,
                                             cwd=self._LINUX_USR_ROOT_PATH)

            if result_verify.cmd_failed():
                log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..". \
                    format(command_line, result_verify.return_code, result_verify.stderr)
                self._log.error(log_error)
                raise log_error

            ret_cmd = self._os.execute(self._CMD_FOR_LOAD_AVG, self._common_content_config.get_command_timeout(),
                                       cwd=self._LINUX_USR_ROOT_PATH)
            if ret_cmd.cmd_failed():
                log_err = "Failed to run command '{}' with return = '{}' and std_error= '{}'..".format(
                                        self._CMD_FOR_LOAD_AVG, ret_cmd.return_code, ret_cmd.stderr)
                self._log.error(log_err)
                raise log_err
        except Exception as ex:
            log_err = "Unable to Execute Stress App due to an Exception : {}".format(ex)
            self._log.error(log_err)
            raise log_err

    def verify_adddc_status(self, adddc_status_check=False, adddc_status_check_list=None):
        """
        This method verifies ras adddc status check regex logs

        :param: adddc_status_check_list : Machine error signature list which is to validate.
        :param: adddc_status_check : Validate the signature if True else only Log the error.
        :raise: RuntimeError
        return True Or False
        """
        ras_adddc_log_status = False
        try:
            # Creating RAS object in cscripts
            self.ras_obj = self._csp.get_ras_object()
            self._sdp.start_log(self.RAS_ADDDC_LOG_FILE, "w")
            socket_value = self._common_content_config.get_memory_socket()
            channel_value = self._common_content_config.get_memory_channel()
            self.ras_obj.adddc_status_check(socket_value, channel_value)
            time.sleep(10)
            self._sdp.stop_log()
            if adddc_status_check:
                #   Reading the log output of adddc_Status_check
                with open(self.RAS_ADDDC_LOG_FILE, "r") as ras_log:
                    self._log.info("Checking the adddc_Status_check log file")
                    ras_adddc_status_log = ras_log.read()  # Getting the adddc_Status_check log
                    #   Calling the Memory mirror utils object method to verify adddc_Status_check
                    self._log.info("Extracting the adddc_Status_check log from : {}".format(ras_adddc_status_log))
                    ras_adddc_log_status = self._common_content_lib.extract_regex_matches_from_file(ras_adddc_status_log,
                                                                                                    adddc_status_check_list)
                    if ras_adddc_log_status:
                        self._log.info("Validation of memory configurations from adddc_Status_check PASS")
                    else:
                        self._log.error("Validation of memory configurations from adddc_Status_check Fail")
            else:
                ras_adddc_log_status=True
        except Exception as e:
            self._log.error("Execption Occured: ", str(e))
        return ras_adddc_log_status
