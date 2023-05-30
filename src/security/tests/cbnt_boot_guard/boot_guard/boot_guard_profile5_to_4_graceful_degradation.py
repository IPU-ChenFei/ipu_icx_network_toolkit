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
from src.lib.bios_util import PlatformConfigReader
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_common import BootGuardValidator


class BootGuardProfile5To4GracefulDegradation(BootGuardValidator):
    """
    Glasgow ID : 59040.2-Boot Guard Profile 5 to 4 graceful degradation
    This Test case Flashes Profile 5 ifwi and  Verify TPM is disabled.
    Platform should gracefully degrade to Profile 4.

    pre-requisites :
    Ensure that the system is in sync with the latest BKC. Ensure that the platform has no TPM installed, and that if
    there is an on board TPM, it is disabled (for example Whitley platform,  Jumper J5E1 1-2 closed). Also, ensure
    hat PTT (firmware TPM) is disabled in the BIOS setup.
    """
    TEST_CASE_ID = ["G59040.2", "Boot_Guard_Profile_5_to_4_graceful_degradation"]
    STEP_DATA_DICT = {1: {'step_details': 'TC 58206 BOOT GUARD Profile 5 should be flashed',
                          'expected_results': 'Boot Guard Profile 5 is flashed'},
                      2: {'step_details': 'Check TPM is disabled',
                          'expected_results': 'TPM should be disabled '},
                      3: {'step_details': 'It should be degrade to one level of profile',
                         'expected_results': 'Verify Boot guard profile5 is degraded to profile4'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of BootGuardProfile5To4GracefulDegradation

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(BootGuardProfile5To4GracefulDegradation, self).__init__(test_log, arguments, cfg_opts)
        self.platform_read = PlatformConfigReader(self.itp_xml_cli_util.get_platform_config_file_path(),
                                                  test_log=test_log)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        """
        Pre-validating whether sut is alive and checks for Bios flash version before flashing ifwi.

        :return: None
        """
        super(BootGuardProfile5To4GracefulDegradation, self).prepare()

    def execute(self):
        """
        This function is used to flash profile 5 binary and verify TPM is disabled.
        Verifies whether system booted with flash profile 4.

        :raise: raise content_exceptions.TestFail if sut not booted with profile 4.
        :return: True if Test case pass else fail
        """
        self._test_content_logger.start_step_logger(1)
        self.flash_binary_image(self.PROFILE5)
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._test_content_logger.start_step_logger(2)
        if not self.platform_read.verify_tpm_is_disabled():
            raise content_exceptions.TestFail("Seems TPM to be enabled, please disable it")
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._test_content_logger.start_step_logger(3)
        if not self.verify_profile_4():
            raise content_exceptions.TestFail("SUT is not degraded to profile4 as expected")
        self._log.info("SUT is degraded to BTG profile4 successfully")
        self._test_content_logger.end_step_logger(3, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if BootGuardProfile5To4GracefulDegradation.main() else
             Framework.TEST_RESULT_FAIL)
