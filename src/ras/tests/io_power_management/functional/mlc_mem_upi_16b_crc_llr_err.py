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

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.lib.dtaf_constants import Framework
from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon


class MlcMemUpi16bCrcLlrError(IoPmCommon):
    """
    Glasgow_id : 70755 PM RAS - Linux- Secondary Socket Mem access+MLC workload + UPI 16-bit CRC LLR error injections

    In this test case, we will be using MLC(memory latency Checker) to provide workload on CPU1(secondary socket) forcing large traffic on UPI lanes
    Once worload is estabnlisd inject a corrected UPI 16-bit CRC LLR error on socket1
    """
    _BIOS_CONFIG_FILE = "mlc_mem_upi_16b_crc_llr_err.cfg"
    EVENT_LOGGING_DELAY_SEC = 6
    CLEAR_LOG_DELAY_SEC = 3
    NUM_CYCLE = 225
    MLC_PATH_AND_LOADED_LATENCY_7200_SEC_POLL = "./mlc --loaded_latency -t7200"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new MlcMemUpi16bCrcLlrError object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(MlcMemUpi16bCrcLlrError, self).__init__(
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
        super(MlcMemUpi16bCrcLlrError, self).prepare()

    def execute(self):

        self.install_mlc_on_sut_linux()

        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)

        self.start_mlc_stress(mlc_path_and_flags=self.MLC_PATH_AND_LOADED_LATENCY_7200_SEC_POLL, specify_node=True)

        for i in range(self.NUM_CYCLE):
            self._log.info("Test on cycle {}".format(i + 1))
            self._log.info("Clearing OS logs .......")
            self._common_content_lib.clear_all_os_error_logs()
            time.sleep(self.CLEAR_LOG_DELAY_SEC)

            self._log.info("Checking if mlc still running...")
            if self.os.execute("pgrep mlc", self._command_timeout).return_code != 0:
                self._log.error("MLC closed unexpectedly!")
                return False
            self._log.info("Check finished, mlc still running")

            self.inject_and_check_upi_error_single_injection(cscripts_obj, init_err_count=i, socket=1, port=0, ignore_crc_cnt=True)

            time.sleep(self.EVENT_LOGGING_DELAY_SEC)
            event_check = self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                        self._os_log_obj.DUT_JOURNALCTL_FILE_NAME,
                                                                        self.LINUX_UPI_16B_CRC_LLR_ERR_SIGNATURE_JOURNALCTL)

            if not event_check:
                self._log.info("Test failed at cycle {}".format(i + 1))
                self.stop_mlc_stress()
                return False

        self.stop_mlc_stress()
        return True


if __name__ == "__main__":

    sys.exit(Framework.TEST_RESULT_PASS if MlcMemUpi16bCrcLlrError.main()
             else Framework.TEST_RESULT_FAIL)
