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

from src.lib import content_exceptions
from src.power_management.lib import reset_base_test


class WarmResetLinux(reset_base_test.ResetBaseTest):
    """
    HPALM ID : H81622
    Do warm reset and check for MCE
    Also runs the BurnInTest before runs cold reset
    """
    TEST_CASE_ID = "H81622"
    _BIT_TIMEOUT = 3  # in minutes

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of WarmResetLinux

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(WarmResetLinux, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(WarmResetLinux, self).prepare()
        self._common_content_lib.update_micro_code()

    def execute(self):
        """test main logic to check the functionality"""
        self._common_content_lib.clear_mce_errors()
        #self.execute_burnin_test(self._BIT_TIMEOUT)
        self.warm_reset()
        errors = self._common_content_lib.check_if_mce_errors()
        self._log.debug("MCE errors: %s", errors)
        if errors:
            raise content_exceptions.TestFail("There are MCE errors after "
                                              "cold reset: %s", errors)
        self._log.info("Test has been completed successfully!")
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(WarmResetLinux, self).cleanup(return_status)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if WarmResetLinux.main() else
             Framework.TEST_RESULT_FAIL)
