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

import sys
import time
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest


class SEAM_BMC_0023_Cycling_test(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0023_Cycling_test, self).__init__(test_log, arguments, cfg_opts)
        self.warm_reset = False
        self.warm_boot_cycle = arguments.warm_boot_cycle
        self.cold_boot_cycle = arguments.cold_boot_cycle
        self.expected_ver = arguments.expected_ver
        self.update_type = None

    @classmethod
    def add_arguments(cls,parser):
        super(SEAM_BMC_0023_Cycling_test, cls).add_arguments(parser)
        parser.add_argument('--warm_boot_cycle', type=int, default=0, help="Add argument for # of loops of reboot")
        parser.add_argument('--cold_boot_cycle', type=int, default=0, help="Add argument for # of loops of cold boot")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update",
                            default="")

    def get_current_version(self, echo_version=True):
        pass

    def check_capsule_pre_conditions(self):
        # type: () -> None
        #To-Do add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        # type: () -> None
        #To-Do add workload output analysis
        return True

    def execute(self):
        if self.warm_boot_cycle:
            """
            TC :- 64958
            cmd :- python3 SEAM_BMC_0023_Cycling_test.py 
            --warm_boot_cycle <loop_count>
            """
            self._log.info("========== Running WarmBootCycling Test ==========")
            for cycle in range(self.warm_boot_cycle):
                self._log.info("Beginning Of Cycle {}" .format(cycle+1))
                self._log.info("==== Step1.1: Checking the PCIe device under device manager ====")
                if self._os_type == OperatingSystems.LINUX:
                    self._log.info("==== Running '{}' command ====".format(self.LSPCICMD))
                    result = self.run_ssh_command(self.LSPCICMD)
                elif self._os_type == OperatingSystems.WINDOWS:
                    self._log.info("==== Running '{}' command ====".format(self.WINLSPCI))
                    result = self.os.execute(self.WINLSPCI, 10)
                self._log.info("{}".format(result))
                if result == "":
                    self._log.error("Failed to Execute '{}' command..!!".format(self.LSPCICMD))
                    return False
                self._log.info("===== Step2: Performing Warm Reboot =====")
                self.os.reboot(timeout=self.WARM_RESET_TIMEOUT)
                self._log.info("System booting into OS..!!\n")
                if not self.sut_ssh.is_alive():
                    self._log.error("Failed To Enter Into OS at {0} Cycle..!!".format(cycle+1))
                    return False
                self._log.info("Entered Into OS Completed {0} Cycle".format(cycle + 1))
            self._log.info("=========== Successfully Completed Cycling For Total Counts Of {0} ===========".format(
                cycle+1))
            return True
        elif self.cold_boot_cycle:
            """
            TC :- 64959
            cmd :- python3 SEAM_BMC_0023_Cycling_test.py 
            --cold_boot_cycle <loop_count>
            """
            main_timer = time.time()
            for i in range(self.cold_boot_cycle):
                self._log.info(
                    "===== BEGINNING OF COLD BOOT S5 CYCLE === Current Count {0} === Total Count {1} <--".format(
                        i+1, self.cold_boot_cycle))
                start = time.time()
                self._log.info("==== Step1.1: Checking the PCIe device under device manager ====")
                if self._os_type == OperatingSystems.LINUX:
                    self._log.info("==== Running '{}' command ====".format(self.LSPCICMD))
                    result = self.run_ssh_command(self.LSPCICMD)
                elif self._os_type == OperatingSystems.WINDOWS:
                    self._log.info("==== Running '{}' command ====".format(self.WINLSPCI))
                    result = self.os.execute(self.WINLSPCI, 10)
                self._log.info("{}".format(result))
                if result == "":
                    self._log.error("Failed to Checking PCIe devices information...!!")
                    return False
                self._log.info('Shutting down the Platform')
                try:
                    self.os.shutdown(self.DC_POWER_DELAY)
                    time.sleep(self.SUT_SETTLING_TIME)
                except Exception as e:
                    self._log.error("{0}".format(e))
                    return False
                if not self.sut_ssh.is_alive():
                    self._log.info("Verified shutdown command for Cycle {0}".format(i+1))
                else:
                    self._log.error("Failed Verified shutdown command for {0}...!!".format(i+1))
                    return False
                if self._product == "WHT":
                    if self._dc_power.dc_power_reset() == True:
                        self._log.info("Platform DC Power Turned On {0} Cycle".format(i + 1))
                        self._log.info("Waiting for system to boot into OS..")
                        self.os.wait_for_os(self.reboot_timeout)
                        time.sleep(self.POST_SLEEP_DELAY)
                        if (self._dc_power.get_dc_power_state() == True):
                            self._log.info("Verified Platform DC Power On {0} Cycle".format(i + 1))
                        else:
                            self._log.error("Failed To Verify Platform DC Power On {0} Cycle...!!".format(i + 1))
                            return False
                    else:
                        self._log.error("Failed To Do Platform DC Power On {0} Cycle...!!".format(i + 1))
                        return False
                elif self._product == "EGS":
                    if self._dc_power.dc_power_on() == True:
                        self._log.info("Platform DC Power Turned On {0} Cycle".format(i + 1))
                        self._log.info("Waiting for system to boot into OS..")
                        self.os.wait_for_os(self.reboot_timeout)
                        time.sleep(self.POST_SLEEP_DELAY)
                        if (self.sut_ssh.is_alive() == True):
                            self._log.info("Verified Platform DC Power On {0} Cycle".format(i + 1))
                        else:
                            self._log.error("Failed To Verify Platform DC Power On {0} Cycle...!!".format(i + 1))
                            return False
                    else:
                        self._log.error("Failed To Do Platform DC Power On {0} Cycle...!!".format(i+1))
                        return False
                self._log.info("Waiting For Platform OS TO Boot-Up Cycle {0}".format(i+1))
                self.os.wait_for_os(self.reboot_timeout)
                time.sleep(self.POST_SLEEP_DELAY)
                if self.sut_ssh.is_alive():
                    self._log.info("Entered Into OS, Completed Cycle {0}".format(i+1))
                else:
                    self._log.error("Failed To Enter Into OS at Cycle {0}...!!".format(i+1))
                    return False
                end = time.time()
                total_time_taken = (abs(start - end))
                total_time_taken = ("{:05.2f}".format(total_time_taken))
                self._log.info(
                    "Cold Boot S5 Cycle === Current Count {0} === Total Count {1} === Time Taken For Current Cycle {2} Seconds ===".format(
                        i+1, self.cold_boot_cycle, total_time_taken))
            final_end = time.time()
            total_time_taken = (abs(main_timer - final_end))
            total_time_taken = ("{:05.2f}".format(total_time_taken))
            self._log.info(
                "Completed Cold Boot S5 Cycling Successfully  For Total Count Of {0} Total Time Taken {1} ===".format(
                    self.cold_boot_cycle, total_time_taken))
            return True

    def cleanup(self, return_status):
        super(SEAM_BMC_0023_Cycling_test, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0023_Cycling_test.main() else Framework.TEST_RESULT_FAIL)
