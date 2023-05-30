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

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_cr.crow_pass.pi_cr_2lm_osboot_l_w import PiCR2LMOsBoot


class PiCRRunDiagnosticSecurityState(PiCR2LMOsBoot):
    """
    HP QC  ID: 101117: PI_CR_RunDiagnosticSecurityState_L, H101162: PI_CR_RunDiagnosticSecurityState_W

    2LM Basic functionality check,verify diagnostic security.
    """

    TEST_CASE_ID = ["H101117", "PI_CR_RunDiagnosticSecurityState_L",
                    "H101162", "PI_CR_RunDiagnosticSecurityState_W"]

    step_data_dict = {1: {'step_details': 'Set the bios knob to 2LM and boot the system',
                          'expected_results': 'system should boot with 2 LM ..'},
                      2: {'step_details': 'Run security diagnostic.',
                          'expected_results': 'Diagnostic (Security State) test gets pass w/o error occurs.'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiCRRunDiagnosticSecurityState8by8 object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiCRRunDiagnosticSecurityState, self).__init__(test_log, arguments, cfg_opts)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._pi_cr_2lm_os_boot = PiCR2LMOsBoot(self._log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Boot the system with 2LM.

        :return: None
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._pi_cr_2lm_os_boot.prepare()
        result = self._pi_cr_2lm_os_boot.execute()
        if result:
            self._log.info("SUT booted with 2LM ...")
        else:
            content_exceptions.TestFail("Got error in OS boot 2LM test case ...")

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Verify state of diagnostic security output of DCPMM

        :return: True, if the test case is successful.
        :raise: None
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        diagnostic_data = self._ipmctl_provider.dimm_diagnostic_security()

        self._memory_common_lib.diagnostic_check(diagnostic_data)

        # Step Logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiCRRunDiagnosticSecurityState, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiCRRunDiagnosticSecurityState.main() else Framework.TEST_RESULT_FAIL)
