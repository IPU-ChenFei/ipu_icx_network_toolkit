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


class SEAM_pfr(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_pfr, self).__init__(test_log, arguments, cfg_opts)
        self.warm_reset = False
        self.reboot_loop = arguments.reboot_loop
        self.expected_ver = arguments.expected_ver
        self.pfr = arguments.pfr
        self.update_type = None

    @classmethod
    def add_arguments(cls, parser):
        # super().add_arguments(parser)
        parser.add_argument('--reboot_loop', type=int, default=0, help="Add argument for # of loops of reboot")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--pfr', action='store_true', help="Add argument to make pfr provisioned",default=False)

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

    def run_provision(self, current_state):
        """
        This Function will run the pfr command.
        current_state: current status of pfr Provisioning.
                        current state is True means pfr is provisioned
                        current state is False means pfr is non provisioned
        return: NA
        """
        if current_state and not self.pfr:
            cmd = "pfrconfig -u"
        elif not self.pfr:
            cmd = "pfrconfig -g"
        elif current_state and self.pfr:
            return
        elif self.pfr:
            cmd = "pfrconfig -p"
        try:
            self.get_uefi_shell_cmd(cmd)
        except:
            self._log.debug("Moving to next step")

    def log_check(self):
        """
        This Function will check the log file.
        current_state: checking the string
        return:spi geometry success or not
        """
        path = os.path.join(self.log_dir, "dtaf_log.log")
        file = open(path, "r",encoding = "utf-8")
        store = file.read()
        if r"Program SPI Geometry } Success" in store:
            self._log.info("able to read spi Geometry")
            result1 = True
        else:
            self._log.info("not able to read spi Geometry")
            result1 = False
        return result1

    def ac_cycle(self):
        self._log.info("Performing Ac Power cycle")
        self._log.info("Removed Ac Power from the system..")
        self.ac_power.ac_power_off(self.AC_POWER_DELAY)
        self._log.info("Connected back Ac Power to the system, booting initiated..\n")
        self.ac_power.ac_power_on(self.AC_POWER_DELAY)
        self._log.info("Waiting for system to boot into OS..")
        self.os.wait_for_os(self.reboot_timeout)

    def check_provision(self):
        """
        This Function check whether it is in provision or un-provision state according to the user input
        return: True if pfr is Provisioned
        """
        output = self.get_uefi_shell_cmd("pfrconfig -i")
        for i in range(0, len(output)):
            if "PFR Provisioned? Yes" in output[i]:
                self._log.info("It is in provisioned state")
                return True
            elif "PFR Provisioned? No" in  output[i]:
                self._log.info("It is in Non provisioned state")
                return False
        raise RuntimeError("Unable to read provision state")

    def prepare(self):
        super().prepare()

    def execute(self):
        """
        This Function will set pfr or non pfr according to the user input
        """
        bios_path = "Boot Manager Menu,UEFI Internal Shell"
        ret = self.bios_navigation_to_page(bios_path)
        if ret:
            current_state = self.check_provision()
            self.run_provision(current_state)
        else:
            raise RuntimeError("Unable to boot to EFI Shell")
        if not self.log_check():
            raise RuntimeError("unable to check the log")
        self.ac_cycle()
        if current_state and self.pfr:
            return True
        bios_path = "Boot Manager Menu,UEFI Internal Shell"
        ret = self.bios_navigation_to_page(bios_path)
        result = False
        if ret:
            current_state = self.check_provision()
            if current_state == self.pfr:
                result = True
        else:
            raise RuntimeError("Unable to boot to EFI Shell")
        self.ac_cycle()
        return result

    def cleanup(self, return_status):
        super().cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_pfr.main() else Framework.TEST_RESULT_FAIL)
