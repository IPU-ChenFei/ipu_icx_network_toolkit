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
"""
	This Script is used for DC cycle during Seamless Pmem FW update
	To make this ipmitool to be copied to host
    Example for Rariton update in system configuration file
    In the system_configuration file need to comment banino related DC tag
    Need to add ipmitool path in the dc tag id = 2 as in the example below
    C:\jenkins\workspace\Seamless_EGS_DTAF_Automation_4917\dtaf_content\src\seamless\tools\ipmitool\ipmitool.exe

"""
import sys
import random
import time
from datetime import datetime, timedelta
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest


class DC_CYCLE(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super().__init__(test_log, arguments, cfg_opts)
        self.warm_reset = False
        self.random_seed = int(random.randrange(1, 10))
        random.seed(self.random_seed)
        self._log.info("Seed Value {}\n".format(self.random_seed))
        self.loop = 100 # Value can be changed according to number of loop cycle
        self.DELAY_DC_POWEROFF = 30

    def check_capsule_pre_conditions(self):
        pass

    def get_current_version(self, echo_version=True):
        pass

    def examine_post_update_conditions(self):
        pass

    def evaluate_workload_output(self, output):
        pass

    def block_until_complete(self, pre_version):
        pass

    def prepare(self):
        self.time_start_test = datetime.now()

    def dc_cycle(self):
        self.os.wait_for_os(self.reboot_timeout)
        self._log.info("Performing DC Power cycle")
        self._dc_power.dc_power_off()
        time.sleep(self.DELAY_DC_POWEROFF)
        if self._dc_power.get_dc_power_state():
            raise RuntimeError("Unable to poweroff SUT")
        self._log.info("Connected back DC Power to the system, booting initiated..\n")
        self._dc_power.dc_power_on()
        self._log.info("Waiting for system to boot into OS..")
        self.os.wait_for_os(self.reboot_timeout)

    def execute(self):
        '''
        DC cycle will trigger between 180  to 240 seconds (random value)
        Input: No of DC cycles which we want to trigger thats a user input value in this code
        Return: True when it completes the specified no of platform DC cycles
        '''

        for i in range(self.loop):
            reboot_after_update = random.randrange(180, 240) # Value can be changed according to number of dimms
            self._log.info("waiting for {} seconds".format(reboot_after_update))
            time.sleep(reboot_after_update)
            self._log.info("loop number: {}".format(i))
            self.dc_cycle()
        return True

    def cleanup(self, return_status):
        super().cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if DC_CYCLE.main() else Framework.TEST_RESULT_FAIL)
