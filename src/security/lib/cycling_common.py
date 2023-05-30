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

import src.lib.content_exceptions as content_exceptions
from src.lib.dtaf_content_constants import ResetStatus
from src.lib.cbnt_constants import TpmVersions


class TbootCyclingCommon():

    BTG_P5_VALID = [0x000000070000007B, 0x000000070000007D, 0x0000000700000075]
    CBNT_BTG_P5_VALID = [0x0000000F0000007B, 0x0000000F0000007D, 0x0000000F00000075]
    BTG_SACM_INFO_MSR_ADDRESS = 0x13a

    def __init__(self, log, trusted_boot, reset_base_test, common_content_lib):
        self._log = log
        self._reset_base_test = reset_base_test
        self._common_content_lib = common_content_lib
        self._txt_cycle_type = {"warm_reboot": self._reset_base_test.warm_reset,
                                "ac_cycle": self._reset_base_test.graceful_g3,
                                "dc_cycle": self._reset_base_test.graceful_s5,
                                "suprise_ac_reset_cycle": self._reset_base_test.surprise_g3}
        self._current_cycle_number = 0
        self._trusted_boot = trusted_boot
        self._total_txt_cycle_number = 0
        self._cycle_str = None
        self._recovery_flag_status = False
        self.number_of_failures = 0
        self._number_of_success = 0
        self._list_failures = []
        self._reset_base_test.NUMBER_OF_RECOVERY_ATTEMPTS = 2
        self.sdp = None

    def trigger_txt_cycles_with_bootguard(self, total_txt_cycle_number, cycle_type, cycle_str,
                                          recovery_flag_status=True):
        """
        This method executes different cycles(warm reboot, ac cycle, dc cycle) for total no of tboot cycle with
         flashing bootguard profile 5

        :param total_txt_cycle_number: number of cycle
        :type: int
        :param cycle_type: function name for warm_reset, graceful_g3, graceful_s5
        :type: str
        :param cycle_str: name of the cycle type
        :type: str
        :param recovery_flag_status: True or False, as per user input in content configuration file.
        :type: bool
        """
        raise content_exceptions.TestNotImplementedError("Tboot cycle with boot guard not implemented")

    def trigger_txt_cycles_without_bootguard(self, total_txt_cycle_number, cycle_type, cycle_str,
                                             recovery_flag_status=True, boot_guard=None):
        """
        This method executes different cycles(warm reboot, ac cycle, dc cycle) for total no of tboot cycle
        without flashing bootguard profile 5

        :param total_txt_cycle_number: number of cycle
        :type: int
        :param cycle_type: function name for warm_reset, graceful_g3, graceful_s5
        :type: str
        :param cycle_str: name of the cycle type
        :type: str
        :param recovery_flag_status: True or False, as per user input in content configuration file.
        :type: bool
        """
        self._log.info("Executing Tboot {} cycling".format(cycle_str))
        self._total_txt_cycle_number = total_txt_cycle_number
        self._cycle_str = cycle_str
        self._recovery_flag_status = recovery_flag_status
        for cycle_number in range(total_txt_cycle_number):
            self._current_cycle_number = int(cycle_number + 1)
            self._log.info("{} Cycle {} started".format(cycle_str, self._current_cycle_number))
            start_time = time.time()
            serial_log_file = os.path.join(self._trusted_boot.serial_log_dir, "serial_log_iteration_%d.log" %
                                           self._current_cycle_number)
            self._trusted_boot.cng_log.redirect(serial_log_file)
            handler = self._txt_cycle_type[cycle_type]
            cycle_status = handler()
            end_time = time.time()
            boot_time = int(end_time - start_time)
            self._log.info("Cycle #{} completed with status code {}. Boot time for the "
                           "{} is {} sec.".format(self._current_cycle_number, cycle_status, self._cycle_str, boot_time))
            if cycle_status == 0:
                if not self._trusted_boot.verify_trusted_boot():  # verify the sut boot with trusted
                    self.number_of_failures += 1
                    self.log_tboot_error()
                self._log.info("SUT Booted to Trusted environment Successfully")
                self.sdp = boot_guard
                if not self.verify_profile_5():
                    self.number_of_failures += 1
                    self.log_bootguard_error()
                self._log.info("System booted with Boot guard profile 5")
                self._number_of_success += 1
            else:
                self.log_cycle_error()
                if not (self._current_cycle_number == total_txt_cycle_number):
                    self.recovery_check()

    def verify_profile_5(self):
        """
        Validate that SUT booted with the Boot Guard profile 5

        :return: True if the device booted with Boot Guard profile 5
        """
        valid_values = self.BTG_P5_VALID + self.CBNT_BTG_P5_VALID
        if self._trusted_boot.get_tpm_version() == TpmVersions.TPM1P2:
            valid_values = self.BTG_P5_VALID
        elif self._trusted_boot.get_tpm_version() == TpmVersions.TPM2:
            valid_values = self.CBNT_BTG_P5_VALID
        if self.sdp:
            return self.verify_boot_profile(valid_values)
        return self.verify_boot_profile_in_os(valid_values)

    def verify_boot_profile_in_os(self, valid_values):
        """
        This function reads the MSR value from the OS using rdmsr tool.

        :param valid_values: for Profile 5 verification
        :return: True if successful other False
        """
        msr_cmd = "rdmsr {}"
        msr_val = self._common_content_lib.execute_sut_cmd(msr_cmd.format(self.BTG_SACM_INFO_MSR_ADDRESS),"msr_cmd", 20)
        self._log.info("MSR %s value is :%s", hex(self.BTG_SACM_INFO_MSR_ADDRESS), msr_val.strip())
        if not int(msr_val, 16) in valid_values:
            valid_values = [hex(i) for i in valid_values]
            self._log.error(
                "Boot guard Profile 5 verification failed actual MSR value {} and excepted value {} ".format(str(msr_val),
                                                                                               valid_values))
            return False
        self._log.info("Boot Guard profile 5 Verification is successful")
        return True

    def verify_boot_profile(self, valid_values):
        """
        This function reads the contents of the BOOT_GUARD_SACM_INFO from read msr from OS and ITP command.
        verify boot guard profile.

        :param valid_values: boot guard profile msr values
        :return: return True if the value matches with boot guard profile values
        """
        self._log.info("Reading MSR value of Boot Guard")
        try:
            self.sdp.halt()
            msr_val = hex(self.sdp.msr_read(self.BTG_SACM_INFO_MSR_ADDRESS, squash=True))
            self._log.info("MSR Value {} ".format(msr_val))
        finally:
            self.sdp.go()
        result = int(msr_val, 16) in valid_values
        self._log.info("result {} ".format(result))
        if not result:
            self._log.error(
                "BtG Profile Verification failed for MSR value = {} valid values =  {}".format(str(msr_val),
                                                                                               valid_values))
        return result

    def recovery_check(self):
        """
        If the system encounter any hangs and SUT is down, this method helps to recover the SUT to boot to OS.

        :raise: content_exceptions.TestFail if SUT fails to boot to OS after ac cycle
        """
        self._log.info("Trying to Recover the system by Ac cycle")
        if self._recovery_flag_status:
            ret_val = self._reset_base_test.prepare_sut_for_retrigger()
            if not ret_val:
                raise content_exceptions.TestFail("Unable to recover the SUT even after performing recovery using ac "
                                                  "power cycle")
        else:
            raise content_exceptions.TestFail("User did not want to recover the system. Hence failing the TC's")

    def log_bootguard_error(self):
        """
        Logging bootguard failures and appending to failure list

        :raise: content_exceptions.TestFail if bootguard enabled fails
        """
        log_error = "SUT not booted to Boot guard profile 5 after the {} cycle {}".format(self._cycle_str, self._current_cycle_number)
        self._list_failures.append(log_error)
        self._log.error(log_error)
        raise content_exceptions.TestFail(log_error)

    def log_tboot_error(self):
        """
        Logging tboot failures and appending to failure list

        :raise: content_exceptions.TestFail if Tboot enabled fails
        """
        log_error = "SUT not booted to Tboot after the {} cycle {}".format(self._cycle_str, self._current_cycle_number)
        self._list_failures.append(log_error)
        self._log.error(log_error)
        raise content_exceptions.TestFail(log_error)

    def log_tboot_bootguard_error(self):
        """
        Logging bootguard test failures and appending to failure list

        :raise: content_exceptions.TestFail if bootguard profile 5 fails to execute
        """
        self.number_of_failures += 1
        log_error = "BtG Profile5 Verification failed for the {} cycle {}".format(self._cycle_str,
                                                                                  self._current_cycle_number)
        self._list_failures.append(log_error)
        self._log.error(log_error)
        raise content_exceptions.TestFail(log_error)

    def log_cycle_error(self):
        """
        Logging cycling test failures and appending to failure list

        :raise: content_exceptions.TestFail if cycling fails to execute
        """
        self.number_of_failures += 1
        if self._reset_base_test._failed_pc:
            log_error = "Cycle #{}: SUT is stuck at post code '{}' during {}" \
                .format(self._current_cycle_number, self._reset_base_test._failed_pc, self._cycle_str)
            self._log.error(log_error)
            self._list_failures.append(log_error)
        else:
            log_error = "Failed to execute the {} cycle number {}".format(self._cycle_str, self._current_cycle_number)
            self._log.error(log_error)
            self._list_failures.append(log_error)

    def cycling_summary_report(self):
        """
        Logs overall summary of the cycling test
        """
        self._log.info("Start Summary of Cycling test")
        self._log.info(
            "Total Number of cycle to Trigger {}; Triggered {}; number of cycles succeeded={} and failed ={}."
                .format(self._total_txt_cycle_number, self._current_cycle_number, self._number_of_success,
                        self.number_of_failures))
        if self.number_of_failures > 0:
            self._log.error("\n".join(self._list_failures))
        self._log.info("End Summary of Cycling test")
