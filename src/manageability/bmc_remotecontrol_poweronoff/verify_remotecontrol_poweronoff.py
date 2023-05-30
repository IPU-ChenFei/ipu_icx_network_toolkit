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
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.manageability.lib.redfish_test_common import RedFishTestCommon


class VerifyBMCRemoteControlPowerOnOff(RedFishTestCommon):
    """
    HPQC ID: 80016
    This Testcase is basically to check the ability to Power On/Off  via the WebGUI
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new  VerifyBMCRemoteControlPowerOnOff object.

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyBMCRemoteControlPowerOnOff, self).__init__(test_log, arguments, cfg_opts)
        self._console_log_path = os.path.join(self.serial_log_dir, self._SERIAL_LOG_FILE)

    def prepare(self):
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """
        super(VerifyBMCRemoteControlPowerOnOff, self).prepare()
        self.change_power_setting_for_redfish(mask=True)

    def execute(self):
        """
        Execute Main test case.

        :return: True if test completed successfully, False otherwise.
        """
        if not self.check_redfish_basic_authentication():
            self._log.info("Authorization to RedFish APIs failed!")
            raise RuntimeError("Error Occured during Authorization!")

        self._log.info("UnCheck Force Enter BIOS Setup Option using WebGUI!")
        self.redfish_check_uncheck_force_enter_bios_setup(check=False)

        self._log.info("Power On the System!")
        self.redfish_power_on()

        self._log.info("Perform Graceful Shutdown!")
        self.redfish_graceful_shutdown()

        self._log.info("Check Force Enter BIOS Setup Option using WebGUI!")
        self.redfish_check_uncheck_force_enter_bios_setup(check=True)

        self._log.info("Power On the System!")
        self.system_forceon_async()
        if not self._common_content_lib.check_for_bios_state(self._console_log_path):
            log_error = "Failed to Boot to BIOS!"
            raise RuntimeError(log_error)
        else:
            self.redfish_check_uncheck_force_enter_bios_setup(check=False)

        self._log.info("SUT shudown immediately then power on to OS!")
        self.redfish_graceful_restart()

        self._log.info("Perform Immediate Shutdown!")
        self.redfish_force_off()

        self._log.info("Power on the System!")
        self.redfish_power_on()
        return self.check_sel()

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self.change_power_setting_for_redfish(mask=False)
        super(VerifyBMCRemoteControlPowerOnOff, self).cleanup(return_status)


# Execute this test with TestEngine when run as main.
if __name__ == '__main__':
    sys.exit(Framework.TEST_RESULT_PASS if VerifyBMCRemoteControlPowerOnOff.main() else Framework.TEST_RESULT_FAIL)
