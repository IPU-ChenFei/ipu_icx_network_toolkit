#!/usr/bin/env python
###############################################################################
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
###############################################################################
import sys

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib import content_exceptions
from src.power_management.lib import reset_base_test

class PowerManagementForceShutdownLinux(reset_base_test.ResetBaseTest):
    """
    HPALM ID : H81593
    Do forceful Shutdown and check for MCE
    """
    TEST_CASE_ID = ["H81593"]
    _TIMEOUT = 5

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of PowerManagementForceShutdownLinux

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(PowerManagementForceShutdownLinux, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("This Test is Supported only on Linux")


    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(PowerManagementForceShutdownLinux, self).prepare()

    def execute(self):
        """test main logic to check the functionality of forceful shutdown"""
        self._common_content_lib.clear_mce_errors()
        self._log.info("Initiating force shutdown...")
        self.surprise_s5(self._TIMEOUT)
        errors = self._common_content_lib.check_if_mce_errors()
        self._log.debug("MCE errors: %s", errors)
        if errors:
            raise content_exceptions.TestFail("There are MCE errors after "
                                              "Force Shutdown: %s" % errors)
        self._log.info("Test has been completed successfully!")
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PowerManagementForceShutdownLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PowerManagementForceShutdownLinux.main() else Framework.TEST_RESULT_FAIL)
