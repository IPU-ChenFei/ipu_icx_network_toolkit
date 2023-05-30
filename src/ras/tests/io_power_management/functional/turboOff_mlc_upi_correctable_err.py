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


class LinuxTurboOffMlcUpiCorrectableErrors(IoPmCommon):
    """
    Glasgow_id : 70594 PM RAS - Linux - turbo mode Off -MLC stress - UPI 16-bit CRC LLR error
    injections + OS log checks
    This test will require the screen package installed on SUT

    This test case is a power management test that injects  a corrected UPI 16-bit CRC LLR error
    while the platform has turbo mode off and running MLC stress
    test currently assumes MLC is installed at /home/mlc/Linux
    """
    _BIOS_CONFIG_FILE = "turbo_off_mlc_upi_16bit_llr_err_bios_knob.cfg"
    EVENT_LOGGING_DELAY_SEC = 40
    CLEAR_LOG_DELAY_SEC = 10
    NUM_CYCLES = 50

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new LinuxTurboOffMlcUpiCorrectableErrors object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        super(LinuxTurboOffMlcUpiCorrectableErrors, self).__init__(
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
        super(LinuxTurboOffMlcUpiCorrectableErrors, self).prepare()

    def execute(self):

        # Start MLC on SUT
        self.start_mlc_stress()

        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        try:
            for i in range(0, self.NUM_CYCLES):
                self._log.info("Clearing OS logs .......")
                self._common_content_lib.clear_all_os_error_logs()
                time.sleep(self.CLEAR_LOG_DELAY_SEC)

                self.inject_and_check_upi_error_single_injection(cscripts_obj, init_err_count=i)
                time.sleep(self.EVENT_LOGGING_DELAY_SEC)

                event_check = self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                            self._os_log_obj.DUT_JOURNALCTL_FILE_NAME,
                                                                            self.GENERIC_MACHINE_CHECK_JOURNALCTL_CORR)
                if not event_check:
                    self._log.info("Test failed at cycle {}".format(i))
                    return False
                self._log.info("Finished Loop " + str(i))

        except Exception as ex:
            self._log.error("Failed on loop: " + str(i))
            log_err = "An Exception Occurred : {}".format(ex)
            self._log.error(log_err)
            return False
        finally:
            self._log.debug("Running finally..")
            self.stop_mlc_stress()

        return True

if __name__ == "__main__":

    sys.exit(Framework.TEST_RESULT_PASS if LinuxTurboOffMlcUpiCorrectableErrors.main()
             else Framework.TEST_RESULT_FAIL)
