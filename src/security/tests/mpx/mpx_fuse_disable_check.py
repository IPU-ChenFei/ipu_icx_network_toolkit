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
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from src.lib.test_content_logger import TestContentLogger
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions
from src.security.tests.mpx.mpx_constants import MpxConstants


class MpxFuseDisableCheck(ContentBaseTestCase):
    """
    Glasgow ID : G59467.2 - MPX Fuse Disable Check
    This Test case is Used to Ensure that MPX is fused off on programs that do not support MPX by checking Mpx Fuse
    bit(pl_dis) Status.
    """
    TEST_CASE_ID = ["G59467.2 - MPX Fuse Disable Check"]

    STEP_DATA_DICT = {1: {'step_details': 'Check MPX Fuse Bit (pl_dis) Status',
                          'expected_results': 'Status of MPX Fuse Bit (pl_dis) is Verified'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of MpxFuseDisableCheck

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(MpxFuseDisableCheck, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(
            test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)

    def prepare(self):
        # type: () -> None
        """
        This Method is Used to Prepare the SUT
        """
        super(MpxFuseDisableCheck, self).prepare()

    @staticmethod
    def verify_mpx_fuse_status_using_sv(pythonsv, log):
        """
        This Method is Used to Verify Status Of MPX Fuse Bit (pl_dis) by Using PythonSv

        :raise content_exceptions.TestFail: if MPX Fuse Bit (pl_dis) is Not Disabled
        """
        mpx_fuse_status = pythonsv.get_by_path(pythonsv.UNCORE,
                                               MpxConstants.MPX_FUSE_BIT_DICT[pythonsv.silicon_cpu_family])
        log.debug("MPX Fuse Bit (pl_dis) status is '{}'".format(mpx_fuse_status))
        if mpx_fuse_status == 0x1:
            raise content_exceptions.TestFail("MPX is Not Fused Off")
        log.info("MPX is Fused Off")

    def execute(self):
        """
        This Method is Used to Verify the Status of MPX Fuse Bit (pl_dis) Using PythonSv.

        :return True
        """
        self._test_content_logger.start_step_logger(1)
        with ProviderFactory.create(self.si_dbg_cfg, self._log) as sdp_obj:
            sdp_obj.halt()
            self._common_content_lib.execute_pythonsv_function(self.verify_mpx_fuse_status_using_sv)
            sdp_obj.go()
        self._test_content_logger.end_step_logger(1, True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MpxFuseDisableCheck.main() else Framework.TEST_RESULT_FAIL)
