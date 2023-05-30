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
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon
from src.memory.tests.memory_cr.apache_pass.provisioning.pi_cr_2lm_osboot_l_w import PICR2lmOsBoot


class PICRRunDiagnosticFirmware(CrProvisioningTestCommon):
    """
    HP QC  ID: 79528 (Linux) and 82163 (Windows)
    2LM Basic functionality check,verify diagnostic firmware.
    """

    TEST_CASE_ID = "H79528/H82163_PI_CR_RunDiagnosticFirmware"

    step_data_dict = {1: {'step_details': 'Clear OS logs and Set the bios knobs, Restart the system, Boot to OS '
                                          'properly and verify the bios knobs. Check the detected DIMM in system.',
                          'expected_results': 'Clear ALL the system OS logs and BIOS setting done. Successfully '
                                              'boot to OS & Verified the bios knobs. Display all of installed DIMMs '
                                              'with correct attributes values Capacity: same as config & Health '
                                              'state:Healthy'},
                      2: {'step_details': 'Run firmware diagnostic.',
                          'expected_results': 'Diagnostic (Firmware) test gets pass w/o error occurs'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PICRRunDiagnosticConfig object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PICRRunDiagnosticFirmware, self).__init__(test_log, arguments, cfg_opts, bios_config_file=None)

        self._pi_cr_2lm_os_boot = PICR2lmOsBoot(self._log, arguments, cfg_opts)

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        1. Verify DDR and CR dimm population as per configuration.
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._pi_cr_2lm_os_boot.prepare()
        self._pi_cr_2lm_os_boot.execute()

        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Verify state of firmware diagnostic output of dcpmm

        :return: True, if the test case is successful.
        :raise: None
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        diagnostic_data = self._ipmctl_provider.dimm_diagnostic_firmware()

        self._memory_common_lib.diagnostic_check(diagnostic_data)

        # Step Logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PICRRunDiagnosticFirmware, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PICRRunDiagnosticFirmware.main()
             else Framework.TEST_RESULT_FAIL)
