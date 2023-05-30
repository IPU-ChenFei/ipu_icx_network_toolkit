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
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.provider_factory import ProviderFactory

import src.lib.content_exceptions as content_exception
from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon


class UpiLlrCrc16bG3Cycle(IoPmCommon):
    """
    Glasgow_id : 70715 PM RAS - UPI LLR CRC 16b G3 Cycling - Linux
    """
    NUM_CYCLES = 10
    _BIOS_CONFIG_FILE = "upi_llr_16_bit_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UpiLlrCrcG3Cycle object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        super(UpiLlrCrc16bG3Cycle, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

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
        super(UpiLlrCrc16bG3Cycle, self).prepare()

    def execute(self):
        """
        llr crc error injection in early boot during G3 cycling.

        :return: True or False based on Test Case fail or pass.
        """

        for i in range(self.NUM_CYCLES):
            try:
                self._log.info("Executing injection loop: " + str(i))
                # initiate G3 cycle
                self.g3_cycle_non_blocking()
                time.sleep(self.WAIT_AFTER_G3_BEFORE_CSCRIPTS_INIT_SECONDS)
                with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:
                    try:
                        cscripts_obj.get_sockets()
                    except:
                        self._log.error("Cscripts check Failed...Cscripts is not working.")
                    # set BIOS break point
                    self.set_bios_break(cscripts_obj, self.UPI_POST_CODE_BREAK_POINT)
                    # wait for target to enter break point
                    self.check_bios_progress_code(cscripts_obj, self.UPI_POST_CODE_BREAK_POINT)
                    # inject error
                    self.inject_and_check_upi_error_single_injection(cscripts_obj, socket=0, port=0)
                    # reset break point
                    self.clear_bios_break(cscripts_obj)
                # wait for os and check os logs
                self.os.wait_for_os(self.RESUME_FROM_BREAK_POINT_WAIT_TIME_SEC)
                if not self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                     self._os_log_obj.DUT_JOURNALCTL_CURRENT_BOOT,
                                                                     self.UPI_MACHINE_CHECK_SOCKET0_JOURNALCTL):
                    log_err = "Error NOT found in OS logs! "
                    self._log.error(log_err)
                    raise content_exception.TestFail(log_err)
            except Exception as ex:
                self._log.error("Failed on loop: " + str(i))
                log_err = "An Exception Occurred : {}".format(ex)
                self._log.error(log_err)
                raise content_exception.TestFail(log_err)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UpiLlrCrc16bG3Cycle.main() else Framework.TEST_RESULT_FAIL)
