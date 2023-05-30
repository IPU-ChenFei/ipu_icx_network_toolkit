#!/usr/bin/env python
##########################################################################
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
##########################################################################

import sys
import time
from dtaf_core.lib.dtaf_constants import Framework
from src.ras.lib.ras_einj_common import RasEinjCommon
from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon


class PackageC6EinjPcieCorError(IoPmCommon):
    """
    Glasgow_id : 70548 PM RAS - Package C6 with PCIe Corr errors

     Using the PTU tool to confirm the system is operating in package c6 state and then injecting PCIe corr error.

    """
    _BIOS_CONFIG_FILE = "package_c6_pcie_corr_err.cfg"
    LOOP_CYCLES = 90
    SYSTEM_IDLE_DOWN_SEC = 30

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PackageC6EinjPcieCorError object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        super(PackageC6EinjPcieCorError, self).__init__(
            test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        self._ras_einj_obj = RasEinjCommon(self._log, self.os, self._common_content_lib,
                                           self._common_content_configuration, self.ac_power)

    def prepare(self):
        # type: () -> None
        """
        1. Ensure PTU app is available on SUT
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """

        self.install_ptu_on_sut_linux()
        super(PackageC6EinjPcieCorError, self).prepare()

    def execute(self):
        """
        1. Allow platform to go to idle C6 state
        2. Inject einj pcie corr errors for x number of loops

        :return:

        """
        # Give platform time to go idle
        self._log.info("Waiting for platform to go to idle C6 state")
        time.sleep(self.SYSTEM_IDLE_DOWN_SEC)
        if not self.ptu_check_c6_state_linux():
            self._log.error("System not in C6 state!")
            return False

        return self._ras_einj_obj.einj_inject_and_check(self._ras_einj_obj.EINJ_PCIE_CORRECTABLE,
                                                        loops_count=self.LOOP_CYCLES)


if __name__ == "__main__":

    sys.exit(Framework.TEST_RESULT_PASS if PackageC6EinjPcieCorError.main()
             else Framework.TEST_RESULT_FAIL)
