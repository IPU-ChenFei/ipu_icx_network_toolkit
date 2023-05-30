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
from src.ras.lib.ras_einj_util import RasEinjCommon

from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.ras.tests.einj_tests.einj_common import EinjCommon
import src.lib.content_exceptions as content_exception


class EinjMemUncorrectableNonfatalStressAppTest(EinjCommon):
    """
    Glasgow_id : G62189

    This test case: Injects memory Uncorrectable non Fatal error: 0x00000010 and validate if the error is detected and
    corrected while stressing the system by running StressApp Test.
    """
    _bios_knobs_file = "einj_mem_biosknobs.cfg"
    TEST_CASE_ID = ["G62189", "Memory Uncorrectable Nonfatal EINJ During StressApp Test"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new EinjMemUncorrectableNonfatalStressAppTest object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(EinjMemUncorrectableNonfatalStressAppTest, self).__init__(test_log, arguments, cfg_opts,
                                                                        self._bios_knobs_file)
        self._common_content_config_lib = self._common_content_configuration
        self._os_log_obj = OsLogVerifyCommon(self._log, self.os, self._common_content_config_lib)

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
        super(EinjMemUncorrectableNonfatalStressAppTest, self).prepare()

    def execute(self):
        """
        1. Injects memory Uncorrectable Non Fatal error: 0x00000010 and validate if the error is detected and corrected
        2. Install Stress APP to SUT.
        3. Execute stress APP command on SUT.
        4. Verify Os Log- No mce log or kernel Log should capture.

        :return: True if Test Case Pass
        :raise: RuntimeError
        """
        failure_num = 0
        passed_num = 0
        t_end = time.time() + self._common_content_configuration.get_time_to_run_einj_stressapptest()
        test_run = 0

        self._log.info("Install the stress test APP")
        self._install_collateral.install_stress_test_app()
        self._ras_common_obj.execute_stress_app(self._common_content_configuration.memory_stress_test_execute_time())
        while time.time() < t_end:
            result = self._ras_einj_obj.einj_inject_and_check(self._ras_einj_obj.EINJ_MEM_UNCORRECTABLE_NONFATAL)
            test_run = 1 + test_run
            self._log.info("Test run number #%d", test_run)
            if result is False:
                failure_num = failure_num + 1
                self._log.error("The test case failed! This is failure number #%d", failure_num)
            else:
                passed_num = passed_num + 1
                self._log.info("TEST PASSED")
        if failure_num > 0:
            result = 0
        else:
            result = 1

        ret_val = self._os_log_obj.verify_os_log_error_messages(__file__, self._os_log_obj.DUT_DMESG_FILE_NAME,
                                                                self._ras_einj_obj._EINJ_UCE_ERROR_LOG_SIG,
                                                                check_error_not_found_flag=False)
        if ret_val:
            self._log.info("No unexpected OS error logs indicated")
        else:
            log_err = "Unexpected OS error logs was indicated"
            self._log.error(log_err)
            raise content_exception.TestFail(log_err)

        ret_val = self._os_log_obj.verify_os_log_error_messages(__file__, self._os_log_obj.DUT_STRESS_FILE_NAME,
                                                                self._ras_common_obj.REGEX_EINJ_STRESSAPPTEST_LOG,
                                                                check_error_not_found_flag=False)
        if ret_val:
            self._log.info("No unexpected OS error logs indicated")
        else:
            log_err = "Unexpected OS error logs was indicated"
            self._log.error(log_err)
            raise content_exception.TestFail(log_err)

        return result and ret_val

if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if EinjMemUncorrectableNonfatalStressAppTest.main() else Framework.TEST_RESULT_FAIL)
