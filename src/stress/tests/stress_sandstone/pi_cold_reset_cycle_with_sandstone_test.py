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

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.dtaf_content_constants import SandstoneTestConstants
from src.stress.lib.stress_common import StressStabilityCommon

from src.lib import content_exceptions


class ColdResetCycleWithSandstoneTest(StressStabilityCommon):
    """
    This class is used to check cold reset with sandstone stress
    Pheonix ID: 16014494318 - PI_Cold_Reset_Cycle_With_Sandstone_Test
    """
    TEST_CASE_ID = ["16014494318", "PI_Cold_Reset_Cycle_With_Sandstone_Test"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of ColdResetCycleWithSandstoneTest

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(ColdResetCycleWithSandstoneTest, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        This method does the following things
        1. install DNF Utils
        2. install proxy chain
        3. install Docker repo
        4. install penIPMI tool
        5. Reload Daemon
        6. Enable Docker
        7. Start Docker

        :return: None
        """

        super(ColdResetCycleWithSandstoneTest, self).prepare()

        self.sandstone_pre_req()

    def execute(self):
        """
        This method does the following things
        1. Download and install the SandStone tool
        2. Takes the version number from content config for sandstone tool and runs the stress on the system
        3. Reboots the system for specified amount of cycles and checks if system is alive after all the reboots

        :return: True if test completed successfully, False otherwise.
        """
        ret_val = []

        total_reboots = self._common_content_configuration.get_num_of_sandstone_cycles()
        for cycle in range(total_reboots):
            time.sleep(10)

            self.start_docker_service()

            self._log.info("Iteration {} of {}.".format(cycle, total_reboots))

            sandstone_res = self.os.execute(SandstoneTestConstants.RUN_SANDSTONE_TEST.format(
                self.sandstone_version_number, cycle), self._command_timeout)
            if sandstone_res.return_code != 0:
                ret_val.append(False)
                self._log.info("Cycle {} - Sandstone result exited with non-successful".format(cycle))
            else:
                self._log.info("Cycle {} - Sandstone result exited with pass".format(cycle))
                ret_val.append(True)

            # perform cold reset to platform from ipmi
            ipmi_reset_cmd = self.os.execute(SandstoneTestConstants.IPMI_TOOL_POWER_CYCLE, self._command_timeout)
            if ipmi_reset_cmd.cmd_failed():
                self._log.error("IPMI power cycle command failed. Debug output: {}".format(ipmi_reset_cmd))
                raise content_exceptions.TestFail("ipmi command failed on iteration {} of {}.".format(cycle,
                                                                                                      total_reboots))
            self.os.wait_for_os(self.reboot_timeout)
            self._log.info("system is alive.")

        host_path = self._common_content_lib.copy_log_files_to_host("16014494318", SandstoneTestConstants.ROOT, ".log")

        self._log.info("Logs are copied to '{}'".format(host_path))
        return all(ret_val)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ColdResetCycleWithSandstoneTest.main() else Framework.TEST_RESULT_FAIL)
