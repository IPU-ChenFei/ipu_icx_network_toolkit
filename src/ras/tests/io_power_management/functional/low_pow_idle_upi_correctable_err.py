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
from dtaf_core.providers.provider_factory import ProviderFactory

from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon


class LowPowerIdleUpiCorrectableErrors(IoPmCommon):
    """
    Glasgow_id : 70579 PM RAS - Windows - Low power idle state (Package C6) + UPI 16-bit CRC LLR error injections + OS log checks

    This test case is a power management test that injects  a corrected UPI 16-bit CRC LLR error
    while the platform is in a idle low power state.
    """
    _BIOS_CONFIG_FILE = "low_pow_idle_upi_16bit_llr_err_bios_knob.cfg"
    EVENT_LOGGING_DELAY_SEC = 30
    SYSTEM_COOL_DOWN_SEC = 30
    NUM_CYCLE = 60

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new LowPowerIdleUpiCorrectableErrors object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        super(LowPowerIdleUpiCorrectableErrors, self).__init__(
            test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        super(LowPowerIdleUpiCorrectableErrors, self).prepare()

    def execute(self):

        self.install_ptu_on_sut_win()

        self.set_powercfg_processor_throttle_min(5)

        time.sleep(self.SYSTEM_COOL_DOWN_SEC)
        if not self.ptu_check_c6_state():
            self._log.error("System not in C6 state!")
            return False

        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)

        for i in range(0, self.NUM_CYCLE):

            self._log.info("Clearing OS logs .......")
            self._common_content_lib.clear_all_os_error_logs()

            self.inject_and_check_upi_error_single_injection(cscripts_obj, init_err_count=i, socket=0, port=0)

            time.sleep(self.EVENT_LOGGING_DELAY_SEC)

            event_check = self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                        self._os_log_obj.DUT_WINDOWS_WHEA_LOG,
                                                                        self.WINDOWS_UPI_CORRECTABLE_ERR_SIGNATURE)
            if not event_check:
                self._log.info("Error Log not found on first try...")
                time.sleep(self.EVENT_LOGGING_DELAY_SEC)
                event_check = self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                            self._os_log_obj.DUT_WINDOWS_WHEA_LOG,
                                                                            self.WINDOWS_UPI_CORRECTABLE_ERR_SIGNATURE)
                if not event_check:
                    self._log.info("Test failed at cycle {}".format(i))
                    return False

        self.reset_powercfg()
        return True


if __name__ == "__main__":

    sys.exit(Framework.TEST_RESULT_PASS if LowPowerIdleUpiCorrectableErrors.main()
             else Framework.TEST_RESULT_FAIL)
