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
import time
import subprocess

from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

import src.lib.content_exceptions as content_exceptions
from src.lib.dtaf_content_constants import ResetStatus, PowerStates
from src.provider.sgx_provider import SGXProvider
from src.power_management.lib.reset_base_test import ResetBaseTest, BootFlow


class SGXCyclingCommon(ResetBaseTest):
    """
    SGX Cycling common test case
    """
    SGX_ENABLE_BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"
    _WARM_REBOOT_REG = "warm_reboot_registration"
    _WARM_REBOOT = "warm_reboot"
    _AC_CYCLE = "ac_cycle"
    _AC_CYCLE_REG = "ac_cycle_registration"
    _DC_CYCLE = "dc_cycle"
    _DC_CYCLE_REG = "dc_cycle_registration"
    _IPMI_CYCLE = "ipmi_cycle"
    _IPMI_CYCLE_REG = "ipmi_cycle_registration"
    NUMBER_OF_RECOVERY_ATTEMPTS = 2
    IPMI_POWEROFF_CMD = "chassis power off"
    IPMI_POWERON_CMD = "chassis power on"
    IPMI_C17_STR = "-C 17"
    IPMI_PATH = None
    MPA_REGISTRATION_LOG_PATH = "/var/log/mpa_registration.log"
    C_DRIVE_PATH = "C:\\"
    ROOT = "/root"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new CyclingCommon object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self.enable_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    self.SGX_ENABLE_BIOS_CONFIG_FILE)
        super(SGXCyclingCommon, self).__init__(test_log, arguments, cfg_opts, self.enable_bios_config_file)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx_provider = SGXProvider.factory(self._log, cfg_opts, self.os, self.sdp)

        self.sgx_cycle_type = {self._WARM_REBOOT: self.warm_reset,
                               self._AC_CYCLE: self.graceful_g3,
                               self._DC_CYCLE: self.graceful_s5,
                               self._IPMI_CYCLE: self.ipmi_cycle,
                               self._WARM_REBOOT_REG: self.warm_reset,
                               self._AC_CYCLE_REG: self.graceful_g3,
                               self._DC_CYCLE_REG: self.graceful_s5
                               }

        self._current_cycle_number = 0
        self._total_sgx_cycle_number = 0
        self._cycle_str = None
        self._recovery_flag_status = False
        self.bmc_poweroff_cmd = ""
        self.bmc_poweroff_on = ""
        self.BMC_IP_ADDR = None
        self.BMC_PASSWORD = None
        self.BMC_DEBUG_USER = None

    def trigger_sgx_cycle(self, total_sgx_cycle_number, cycle_type, cycle_str, recovery_flag_status, registration=False):
        """
        This method executes different cycles(warm reboot, ac cycle, dc cycle) for total no of sgx cycle

        :param total_sgx_cycle_number: number of cycle :type: int
        :param cycle_type: function name for warm_reset, graceful_g3, graceful_s5 :type: str
        :param cycle_str: name of the cycle type :type: str
        :param recovery_flag_status: True or False, as per user input in content configuration file. :type: bool
        """
        self._log.info("Executing SGX {} cycling".format(cycle_str))
        self._total_sgx_cycle_number = total_sgx_cycle_number
        self._cycle_str = cycle_str
        self._recovery_flag_status = recovery_flag_status
        for cycle_number in range(total_sgx_cycle_number):
            self._current_cycle_number = cycle_number + 1
            self._log.info("{} Cycle {} started".format(cycle_str, self._current_cycle_number))
            start_time = time.time()
            serial_log_file = os.path.join(self.serial_log_dir, "serial_log_iteration_%d.log" %
                                           self._current_cycle_number)
            self.cng_log.redirect(serial_log_file)
            self._cycle_status = cycle_type()
            end_time = time.time()
            boot_time = int(end_time - start_time)
            self._log.info("Cycle #{} completed with status code {}. Boot time for the "
                           "{} is {} sec.".format(self._current_cycle_number, self._cycle_status, self._cycle_str,
                                                  boot_time))
            if self._cycle_status == 0:
                self._log.info(
                    "{} Cycle {} completed. Checking for SGX status".format(cycle_str, self._current_cycle_number))
                if registration:
                    self.check_sgx_registration()
                    self.append_logs(self._current_cycle_number)
                else:
                    self.check_sgx_app_status()
            else:
                self.log_cycle_error()
                if not (self._current_cycle_number == total_sgx_cycle_number):
                    self.recovery_check()

    def check_sgx_registration(self):
        """
        Checks SGX Registration is Successful after each cycle
        """
        self._log.info("Verifying SGX registration status")
        if not self.sgx_provider.verify_mp_registration():
            self.log_sgx_registration_error()
        self.check_sgx_app_status()
        self._log.info("SGX Registration is Successful after {} Cycle '{}'".format(self._cycle_str, self._current_cycle_number))

    def append_logs(self, cycle_number):
        """
        Appending MPA registration logs
        :param: cycle_number current cycle number
        """
        self._log.info("Appending Log information")
        log_dir = self._common_content_lib.get_log_file_dir()
        destination = os.path.join(log_dir,"mpa_registration_complete.log")
        sourcepath = os.path.join(log_dir, os.path.basename(self.MPA_REGISTRATION_LOG_PATH))
        self.os.copy_file_from_sut_to_local(self.MPA_REGISTRATION_LOG_PATH, sourcepath)
        with open(sourcepath, "r") as sourceobj:
            with open(destination, "a+") as destobj:
                destobj.write("Registration cycle number {} ".format(cycle_number))
                destobj.write(sourceobj.read())
        self.delete_file(self.MPA_REGISTRATION_LOG_PATH)

    def delete_file(self, filepath):
        """
        Function to delete a file.

        :param filepath: path of the file to be deleted
        :return: True if success
        """
        self._log.info("Deleting Log information file")
        try:
            if OperatingSystems.LINUX in self.os.os_type:
                if self.os.check_if_path_exists(filepath):
                    self._common_content_lib.execute_sut_cmd("rm -rf {}".format(filepath),
                                                             "To delete a file", self._command_timeout, self.ROOT)
                else:
                    raise content_exceptions.TestFail("Cannot find the file {} to delete".format(filepath))
            elif OperatingSystems.WINDOWS in self.os.os_type:
                file_exists = self._common_content_lib.execute_sut_cmd(self.PS_CMD_TO_CHECK_FILE_EXISTS_OR_NOT.
                                                                       format(filepath),
                                                                       "To check whether file exists or not",
                                                                       self._command_timeout, self.C_DRIVE_PATH)
                if 'True' in file_exists:
                    self._common_content_lib.execute_sut_cmd("DEL /Q {}".format(filepath), "To delete a file",
                                                             self._command_timeout, self.C_DRIVE_PATH)
                else:
                    raise content_exceptions.TestFail("Can not find the file {}".format(filepath))
            self._log.info("Successfully deleted the file {} ".format(filepath))
            return True

        except Exception:
            raise content_exceptions.TestFail("Error while trying to delete the file {} . ".format(filepath))

    def check_sgx_app_status(self):
        """
        Checks SGX is enabled or not and runs the sgx_run_app_test
        """
        self._log.info("Verifying SGX app status")
        flag = True
        if not self.sgx_provider.is_sgx_enabled():
            flag = False
            self.log_sgx_error()
        else:
            if not self.sgx_provider.run_sgx_app_test():
                flag = False
                self.log_sgx_run_app_error()
        if flag:
            self._number_of_success += 1
            self._log.info("SGX is enabled after {} Cycle '{}'".format(self._cycle_str, self._current_cycle_number))

    def log_sgx_run_app_error(self):
        """
        Logging SGX run app test failures and appending to failure list

        :raise: content_exceptions.TestFail if SGX run app fails to execute
        """
        self._number_of_failures += 1
        log_error = "Failed to run SGX run app for {} cycle {}".format(self._cycle_str, self._current_cycle_number)
        self._list_failures.append(log_error)
        self._log.error(log_error)
        raise content_exceptions.TestFail(log_error)

    def log_sgx_error(self):
        """
        Logging SGX failures and appending to failure list

        :raise: content_exceptions.TestFail if SGX enabled fails
        """
        self._number_of_failures += 1
        log_error = "SGX is not enabled after the {} cycle {}".format(self._cycle_str, self._current_cycle_number)
        self._list_failures.append(log_error)
        self._log.error(log_error)
        raise content_exceptions.TestFail(log_error)

    def log_sgx_registration_error(self):
        """
        Logging SGX failures and appending to failure list

        :raise: content_exceptions.SGX Registration is not Enabled.
        """
        self._number_of_failures += 1
        log_error = "SGX Registration is not enabled after the {} cycle {}".format(self._cycle_str, self._current_cycle_number)
        self._list_failures.append(log_error)
        self._log.error(log_error)
        raise content_exceptions.TestFail(log_error)

    def log_cycle_error(self):
        """
        Logging cycling test failures and appending to failure list

        :raise: content_exceptions.TestFail if cycling fails to execute
        """
        self._number_of_failures += 1
        if self._failed_pc:
            log_error = "Cycle #{}: SUT is stuck at post code '{}' during {}" \
                .format(self._current_cycle_number, self._failed_pc, self._cycle_str)
            self._log.error(log_error)
            self._list_failures.append(log_error)
        else:
            log_error = "Failed to execute the {} cycle number {}".format(self._cycle_str, self._current_cycle_number)
            self._log.error(log_error)
            self._list_failures.append(log_error)

    def recovery_check(self):
        """
        If the system encounter any hangs and SUT is down, this method helps to recover the SUT to boot to OS.

        :raise: content_exceptions.TestFail if SUT fails to boot to OS after ac cycle
        """
        self._log.info("Trying to Recover the system by Ac cycle")
        if self._recovery_flag_status:
            ret_val = self.prepare_sut_for_retrigger()
            if not ret_val:
                raise content_exceptions.TestFail("Unable to recover the SUT even after performing recovery using ac "
                                                  "power cycle")
        else:
            raise content_exceptions.TestFail("User did not want to recover the system. Hence failing the TC's")

    def __ipmi_poweroff(self):
        """
        executes the BMC power off command using IPMI tool
        :return : True if the power OFF command is successful else False
        """
        max_attempts = 2
        attempt_num = 1
        is_shutdown = False
        while attempt_num <= max_attempts:
            self._log.info("Attempt#%d: Shutting down the SUT.", attempt_num)
            attempt_num = attempt_num + 1
            if self.execute_ipmi_cmd(self.IPMI_POWEROFF_CMD):
                is_shutdown = True
                break
            time.sleep(30)
        if not is_shutdown:
            self._log.error("Failed to shutdown the SUT.")
            return False

        attempt_num = 1
        is_shutdown = False
        while attempt_num <= max_attempts:
            self._log.info("Attempt#%d: Waiting until SUT state is S5.", attempt_num)
            attempt_num = attempt_num + 1
            power_state = self._common_content_lib.get_power_state(self.phy)
            if power_state == PowerStates.S5:
                is_shutdown = True
                break
            self.fail_or_log(
                "SUT did not entered into %s state, actual state is %s" % (PowerStates.S5, power_state),
                self.log_or_fail)
            time.sleep(60)

        return is_shutdown

    def __ipmi_poweron(self):
        """
        Executes the BMC power ON command using IPMI tool
        :return: True if the power ON command is successful else False
        """
        max_attempts = 2
        attempt_num = 1
        is_poweron = False
        while attempt_num <= max_attempts:
            self._log.info("Attempt#%d: poweron the SUT.", attempt_num)
            time.sleep(30)
            attempt_num = attempt_num + 1
            if self.execute_ipmi_cmd(self.IPMI_POWERON_CMD):
                is_poweron = True
                break
        if not is_poweron:
            self._log.error("Failed to poweron the SUT using IPMI command.")
            return False
        return True

    def execute_ipmi_cmd(self, ipmi_cmd):
        """
        Executes the Ipmi command and check for the status of the executed command.
        :return: True if the command is successful else False
        """
        try:
            self.__cmd_ipmitool = (
                r"{0} -I lanplus {1} -H {2} -U {3} -P {4}".format(self.IPMI_PATH, self.IPMI_C17_STR, self.BMC_IP_ADDR, self.BMC_DEBUG_USER, self.BMC_PASSWORD))
            self._log.info("IPMI Command {}".format(self.__cmd_ipmitool + " " + str(ipmi_cmd)))
            opt = subprocess.Popen(self.__cmd_ipmitool + " " + str(ipmi_cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   shell=True)
            output = opt.stdout.read()
            self._log.info(output)
            return self._system_status(output)
        except Exception:
            self._log.error("Execution Of Given " + str(ipmi_cmd) + " Failed")
            return False

    def _system_status(self, outuput):
        """
        Checks the status of executed command output and returns if the command is successful True or False
        :return: True if poweron/poweroff command is successful else False connection establish is failed.
        """
        power_off_str = r"Chassis Power Control: Down/Off"
        power_on_str = r"Chassis Power Control: Up/On"
        connection_fail_str = r"Unable to establish IPMI v2 / RMCP+ session"
        if str(outuput).find(power_off_str) != -1:
            self._log.info("SUT Is Powered Off using BMC Ip")
            return True
        elif str(outuput).find(power_on_str) != -1:
            self._log.info("SUT Is Powered On using BMC IP")
            return True
        elif str(outuput).find(connection_fail_str) != -1:
            self._log.debug("Unable to establish the RMCP Session using IP")
            return False
        else:
            self._log.debug("error unable to get the BMC status")
            return False

    def ipmi_cycle(self):
        """
        Execute ipmi poweroff and poweron command and wait for os to be alive.
        :return: True if ipmi poweron and poweroff successful else failure code.
        """
        if not self._common_content_lib.check_os_alive():
            self._log.error("SUT is not up, cannot execute the ipmi shutdown command..")
            return ResetStatus.OS_NOT_ALIVE

        if not self.__ipmi_poweroff():
            power_state = self._common_content_lib.get_power_state(self.phy)
            if power_state != PowerStates.S5:
                self.fail_or_log(
                    "SUT did not entered into %s state, actual state is %s" % (PowerStates.S5, power_state),
                    self.log_or_fail)
                bios_pc, fpga_pc = self._common_content_lib.get_post_code(self.pc_phy)
                if bios_pc is not None:
                    self._log.info("FPGA PC='{}' BIOS PC='{}'".format(fpga_pc, bios_pc))
                    self._failed_pc = bios_pc
                    self._boot_flow = BootFlow.POWER_OFF
                    return ResetStatus.PC_STUCK
                else:
                    self._log.error("Unable to read the post code")
                    return ResetStatus.STATE_CHANGE_FAILURE

        self._log.info("SUT is in S5 state.")

        if not self.__ipmi_poweron():
            self._log.error("Failed to perform power ON operation on SUT using ipmi command..")
            return ResetStatus.DC_FAILURE

        status = self._wait_for_os()
        if status != ResetStatus.SUCCESS:
            return status

        power_state = self._common_content_lib.get_power_state(self.phy)
        if power_state != PowerStates.S0:
            self.fail_or_log("SUT did not entered into %s state, actual state is %s" % (PowerStates.S0, power_state),
                             self.log_or_fail)
            return ResetStatus.STATE_CHANGE_FAILURE

        self._log.info("SUT is in S0 state and network is up.")
        self._log.info("Waiting for all OS services to be up...")
        self._common_content_lib.wait_for_sut_to_boot_fully()
        return ResetStatus.SUCCESS

    def _wait_for_os(self):
        start_time = time.time()
        pc_available = True

        bios_pc, fpga_pc = self._common_content_lib.get_post_code(self.pc_phy)
        if bios_pc is None:
            pc_available = False
            self._log.info("Post code data not available.")

        if pc_available:
            prev_pc = None
            pc_stuck_start_time = start_time
            while True:
                elapsed_time = time.time() - start_time
                pc_stuck_elapsed_time = time.time() - pc_stuck_start_time
                bios_pc, fpga_pc = self._common_content_lib.get_post_code(self.pc_phy)
                if bios_pc is not None:
                    if prev_pc is None:
                        prev_pc = bios_pc
                    self._log.info("FPGA PC='{}' BIOS PC='{}'".format(fpga_pc, bios_pc))
                    if prev_pc == bios_pc:
                        if pc_stuck_elapsed_time > self.pc_stuck_time_out:
                            self._log.error("SUT is stuck at post code %s for more than %d seconds.", bios_pc,
                                            self.pc_stuck_time_out)
                            break
                    else:
                        pc_stuck_start_time = time.time()
                        prev_pc = bios_pc
                else:
                    self._log.error("Unable to read the post code")
                if self._common_content_lib.check_os_alive() or elapsed_time >= self.reboot_timeout:
                    break
        else:
            self._log.info("Waiting for OS to be alive.")
            while True:
                elapsed_time = time.time() - start_time
                if self._common_content_lib.check_os_alive() or elapsed_time >= self.reboot_timeout:
                    break

        if pc_available:
            bios_pc, fpga_pc = self._common_content_lib.get_post_code(self.pc_phy)
            if bios_pc is not None:
                self._log.info("FPGA PC='{}' BIOS PC='{}'".format(fpga_pc, bios_pc))
            else:
                self._log.error("Unable to read the post code")

        if not self._common_content_lib.check_os_alive():
            if pc_available:
                if bios_pc not in self.os_post_codes:
                    self._log.error("SUT Failed to boot to OS with post code %s "
                                    "within %d seconds" % (str(bios_pc), self.reboot_timeout))
                else:
                    self._log.error("Sut has booted to OS with post code %s and within %d seconds, "
                                    "but network service failed." % (str(bios_pc), self.reboot_timeout))
            else:
                self._log.error("SUT Failed to boot to OS within %d seconds." % self.reboot_timeout)

            self._boot_flow = BootFlow.POWER_ON
            self._failed_pc = bios_pc
            if self._failed_pc is None:
                return ResetStatus.OS_NOT_ALIVE
            else:
                return ResetStatus.PC_STUCK

        return ResetStatus.SUCCESS

    def cleanup(self, return_status):
        """Test Cleanup
        Logs overall summary of the cycling test

        :param: return_status True if Test case pass else False
        """
        self._log.info("Start Summary of Cycling test")
        self._log.info(
            "Total Number of cycle to Trigger={}; Triggered={}; number of cycles succeeded={} and failed={}."
                .format(self._total_sgx_cycle_number, self._current_cycle_number, self._number_of_success,
                        self._number_of_failures))
        if self._number_of_failures > 0:
            self._log.error("\n".join(self._list_failures))
        self._log.info("End Summary of Cycling test")
        if self.os.is_alive():
            self._common_content_lib.store_os_logs(self.log_dir)
        # copy logs to CC folder
        self._log.info("Command center log folder='{}'".format(self._cc_log_path))
        self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)
        if return_status:
            self._log.info(self._PASS_INFO)
        else:
            self._log.error(self._FAIL_INFO)
