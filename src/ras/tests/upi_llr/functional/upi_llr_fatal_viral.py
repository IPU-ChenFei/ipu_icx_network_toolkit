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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory

from src.ras.tests.viral.viral_common import ViralCommon
from src.ras.lib.ras_upi_util import RasUpiUtil
from src.lib import content_exceptions


class UpiLlrFatalViral(ViralCommon):
    """
    Glasgow_id : 69374

    UPI uncorrectable CRC error
    """
    _BIOS_CONFIG_FILE = "upi_llr_fatal_viral_bios_knob.cfg"
    TEST_CASE_ID = ["G69374", "UPI_LLR_Fatal_Viral"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UpiLlrFatalViral object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UpiLlrFatalViral, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        self.args = arguments

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
        super(UpiLlrFatalViral, self).prepare()

    def execute(self):
        """
        This method is used to execute

        1.Execute Crunch Tool.
        2.Verify Viral is enabled
        3.Injects continuous CRC errors to cause a uncorr condition to occur
        4.verify Viral status bits are set as expected after a uncorrected UPI event
        5.Verify OS has hung (fatal )
        6.Reset target
        7.Verify OS is up and ready
        8.Verify viral is still enabled

        :return: True or False based on Test Fail or Pass.
        """
        csp = ProviderFactory.create(self.sil_cfg, self._log)
        ei = csp.get_cscripts_utils().get_ei_obj()
        ras_upi_util = RasUpiUtil(self.os, self._log, self._cfg, self._common_content_lib, self.args)

        # Execute Crunch Tool
        ras_upi_util.execute_crunch_tool()

        # Verify Viral Signaling is Enabled
        self.check_upi_viral_signaling_enabled(csp=csp)

        # Inject Error
        self._log.info("Inject Error")
        ei.injectUpiError(socket=0, port=0, num_crcs=0, stopInj=True)

        # Verify Viral Signaling Status bit
        self.verify_upi_viral_state_and_status_bit(csp=csp)

        # Check SUT is Hang or not
        if self.os.is_alive():
           raise content_exceptions.TestFail("SUT is alive after injecting error")
        self._log.info("OS got Hung as Expected")

        # Apply reboot
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)

        # Verify Viral signaling Still enabled
        self.check_upi_viral_signaling_enabled(csp=csp)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UpiLlrFatalViral.main() else Framework.TEST_RESULT_FAIL)
