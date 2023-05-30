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
import os
from dtaf_core.lib.dtaf_constants import Framework

from src.ras.tests.viral_injection_detection_recovery_with_bps_present.viral_injection_detection_recovery_common \
    import ViralInjectionDetectionRecoveryCommon


class VerifyViralInjectionDetectionRecoveryWithBPSPresentInDWR(ViralInjectionDetectionRecoveryCommon):
    """
    Glasgow_id : 60927

    Viral alert is a method of providing enhanced error containment in case of fatal errors using the viral alert bit
    in Intel UPI packet headers. Viral is propagated to all sockets and I/O entities for containment and reporting.
    """
    _BIOS_CONFIG_FILE = "viral_injection_with_dwr_enabled_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VerifyViralInjectionDetectionRecoveryWithBPS  object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyViralInjectionDetectionRecoveryWithBPSPresentInDWR, self).__init__(test_log, arguments, cfg_opts,
                                                                                       self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set and verify the bios knobs..

        :return: None
        """
        self._common_content_lib.clear_all_os_error_logs()  # This Method is used to Clear All OS Logs.
        self._ras_common_obj.set_and_verify_bios_knobs()

    def execute(self):
        """
        This method is used to execute verify_viral_injection_detection_recovery_with_bps_present method to verify if
        viral state is enabled after modifying the Bios Knob.

        :return: True or False based on the Output of enable_viral method.
        """
        return self.verify_viral_injection_detection_recovery_with_bps_present()


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if VerifyViralInjectionDetectionRecoveryWithBPSPresentInDWR.main() else Framework.TEST_RESULT_FAIL)
