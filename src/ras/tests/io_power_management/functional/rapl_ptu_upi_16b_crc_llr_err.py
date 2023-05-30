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


class RaplPtuUpi16bCrcLlrError(IoPmCommon):
    """
    Glasgow_id : 70727 PM RAS - Linux- RAPL+PTU workload+UPI 16-bit CRC LLR error injections

    With the PTU tool running a workload, this test case walks you through
    how to do UPI 16-bit CRC LLR error injection to the platform
    while the platform is utilizing RAPL to limit power/performance.
    """
    _BIOS_CONFIG_FILE = "rapl_ptu_upi_16b_crc_llr_err.cfg"
    EVENT_LOGGING_DELAY_SEC = 6
    NUM_CYCLE = 270

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new RaplPtuUpi16bCrcLlrError object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        super(RaplPtuUpi16bCrcLlrError, self).__init__(
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
        super(RaplPtuUpi16bCrcLlrError, self).prepare()

    def execute(self):

        self.install_ptu_on_sut_linux()

        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)

        p1_limit_origin = self.set_rapl_and_verify_linux(sdp_obj, self.MSR_ADDR_PACKAGE_RAPL_LIMIT, self.MSR_PACKAGE_RAPL_LIMIT_ADJUSTMENT)
        if not p1_limit_origin:
            return False

        self.ptu_execute_linux(self.PTU_CPU_TEST, self.PTU_CPU_TEST_CORE_IA_SSE_TEST, duration_sec=3600)
        time.sleep(self.PTU_START_DELAY_SEC)

        for i in range(0, self.NUM_CYCLE):
            self._log.info("Test on cycle {}".format(i))
            self._log.info("Clearing OS logs .......")
            self._common_content_lib.clear_all_os_error_logs()

            self.inject_and_check_upi_error_single_injection(cscripts_obj, init_err_count=i, socket=0, port=0)

            time.sleep(self.EVENT_LOGGING_DELAY_SEC)
            event_check = self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                        self._os_log_obj.DUT_DMESG_FILE_NAME,
                                                                        self.LINUX_UPI_16B_CRC_LLR_ERR_SIGNATURE)

            if not event_check:
                self._log.info("Test failed at cycle {}".format(i))
                self.ptu_kill_linux()
                sdp_obj.halt()
                sdp_obj.msr_write(self.MSR_ADDR_PACKAGE_RAPL_LIMIT, p1_limit_origin)
                sdp_obj.go()
                return False

        self.ptu_kill_linux()
        sdp_obj.halt()
        sdp_obj.msr_write(self.MSR_ADDR_PACKAGE_RAPL_LIMIT, p1_limit_origin)
        sdp_obj.go()
        return True


if __name__ == "__main__":

    sys.exit(Framework.TEST_RESULT_PASS if RaplPtuUpi16bCrcLlrError.main()
             else Framework.TEST_RESULT_FAIL)
