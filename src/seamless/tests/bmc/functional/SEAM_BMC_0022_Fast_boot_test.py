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
import os
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest


class SEAM_BMC_0022_Fast_boot(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0022_Fast_boot, self).__init__(test_log, arguments, cfg_opts)
        self.warm_reset = False
        self.reboot_loop = arguments.reboot_loop
        self.expected_ver = arguments.expected_ver

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0022_Fast_boot, cls).add_arguments(parser)
        parser.add_argument('--reboot_loop', type=int, default=0, help="Add argument for # of loops of reboot")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update", default="")

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

    def change_bios_setup_option(self):
        self._log.info("Changing the BIOS setup option and saving the settings...")
        bios_path = "EDKII Menu,Boot Options,Fast Boot Mode"
        ret = self.bios_navigation_to_page(bios_path)
        if ret:
            self.setupmenu.enter_selected_item(ignore=False, timeout=10)
            self.setupmenu.change_order([str("Enable")])
            ret = self.setupmenu.get_page_information()
            self._log.info("'Fast Boot' BIOS option {0}  ".format("Enabled"))
            self.setupmenu.press(r'F10')
            time.sleep(5)
            self.setupmenu.press_key(r'Y', True, 10)
            time.sleep(5)
            self.setupmenu.back_to_root(0.1, r'ESC')
            return True
        else:
            return False

    def execute(self):
        """
        TC :- 71165 & 71166
        cmd :- python3 SEAM_BMC_0022_Fast_boot_test.py
        --reboot_loop <loop_count>
        """
        self._log.info("Rebooting the SUT once before enabling 'Fast Boot'..")
        self.os.reboot(timeout=self.WARM_RESET_TIMEOUT)
        self._log.info("System booted into OS..!!\n")
        if self._os_type == OperatingSystems.LINUX or self._os_type == OperatingSystems.WINDOWS:
            self._log.info("======== ENABLING FAST BOOT IN BIOS ========\n")
            if self.change_bios_setup_option():
                self._log.info("Successfully updated the BIOS settings")
            else:
                self._log.info("System failed to enter BIOS Menu, 'Fast Boot' is already 'Enabled'..")
            time.sleep(self.DC_POWER_DELAY)
            if self._product == "EGS":
                self._dc_power.dc_power_on()
            elif self._product == "WHT":
                self._dc_power.dc_power_reset()
            self._log.info("Waiting for system to boot into OS..")
            self.os.wait_for_os(self.reboot_timeout)
            time.sleep(self.POST_SLEEP_DELAY)
            if self.sut_ssh.is_alive():
                self._log.info("System booted into OS..!!\n")
                if self.reboot_loop:
                    for x in range(self.reboot_loop):
                        self._log.info("Performing Reboot cycle, iteration: {}".format(x + 1))
                        self.os.reboot(timeout=self.WARM_RESET_TIMEOUT)
                        self._log.info("System booted into OS..!!\n")
                    self._log.info("==========PERFORMED {} ITERATION(S) OF REBOOT CYCLE===========\n".format(x + 1))
                    return True
                else:
                    self._log.info("Reboot loop argument and count not given, Exiting the process..!!")
                    return False
            else:
                self._log.info("System failed to boot into OS..!!\n")
                return False

    def cleanup(self, return_status):
        super(SEAM_BMC_0022_Fast_boot, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0022_Fast_boot.main() else Framework.TEST_RESULT_FAIL)
