#!/usr/bin/env python
##########################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and
# proprietary and confidential information of Intel Corporation and its
# suppliers and licensors, and is protected by worldwide copyright and trade
# secret laws and treaty provisions. No part of the Material may be used,copied,
# reproduced, modified, published, uploaded, posted, transmitted, distributed,
# or disclosed in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################

import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.test_content_logger import TestContentLogger
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions
from src.security.tests.cbnt_boot_guard.cbnt_boot_guard_constants import CBnTConstants


class CpuFuseCheck(ContentBaseTestCase):
    """
    Glasgow ID : G58665.2 - Check CPU Fuse
    This Test case is Used to Check CPU Fuse Bit(anchor_cove_en)
    """
    TEST_CASE_ID = ["G58665.2", "Check CPU Fuse"]

    STEP_DATA_DICT = {1: {'step_details': 'Check CPU Fuse Bit(anchor_cove_en)',
                          'expected_results': 'Status of CPU Fuse Bit(anchor_cove_en) is Verified'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of CpuFuseCheck

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(CpuFuseCheck, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(
            test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """
        This Method is Used to Prepare the SUT
        """
        super(CpuFuseCheck, self).prepare()

    @staticmethod
    def check_cpu_fuse_using_sv(pythonsv, log):
        """
        This Method is Used to Verify Status Of Cpu Fuse Bit(anchor_cove_en) by Using PythonSv

        :raise TestFail: if Cpu Fuse Bit(anchor_cove_en) is Not Set
        """

        cpu_fuse_bit = pythonsv.get_by_path(pythonsv.UNCORE,
                                            CBnTConstants.CPU_FUSE_BIT_DICT[pythonsv.silicon_cpu_family])
        log.debug("Cpu Fuse Bit (anchor_cove_en) status is '{}'".format(cpu_fuse_bit))
        if not cpu_fuse_bit == 0x1:
            raise content_exceptions.TestFail("CPU Fuse Bit(anchor_cove_en) is Not Set")
        log.info("CPU Fuse Bit(anchor_cove_en) is Set")

    def execute(self):
        """
        This Method is Used to Check CPU Fuse Bit (anchor_cove_en) Status

        :return True
        """
        self._test_content_logger.start_step_logger(1)
        self._common_content_lib.execute_pythonsv_function(self.check_cpu_fuse_using_sv)
        self._test_content_logger.end_step_logger(1, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CpuFuseCheck.main() else Framework.TEST_RESULT_FAIL)
