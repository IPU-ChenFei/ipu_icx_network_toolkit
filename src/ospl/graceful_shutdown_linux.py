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


class GracefulShutdownLinux(reset_base_test.ResetBaseTest):
    """
    HPALM ID : H81595-PI_Powermanagement_Graceful_Shutdown_L
    Do Graceful Shutdown and check for MCE
    """
    TEST_CASE_ID = ["H81595-PI_Powermanagement_Graceful_Shutdown_L"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of GracefulShutdownLinux

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(GracefulShutdownLinux, self).__init__(test_log, arguments, cfg_opts)
        
    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(GracefulShutdownLinux, self).prepare()
        self._common_content_lib.update_micro_code()

    def execute(self):
        """test main logic to check the functionality"""
        for cycle_number in range(self._common_content_configuration.get_num_of_dc_cycles()):
            self._log.info("Power Dc cycle %d", cycle_number)
            self._common_content_lib.clear_mce_errors()
            self.graceful_s5()
            errors = self._common_content_lib.check_if_mce_errors()
            self._log.debug("MCE errors: %s", errors)
            if errors:
                raise content_exceptions.TestFail("There are MCE errors after "
                                                  "Graceful Shutdown: %s", errors)
            self._log.info("Test has been completed successfully!")
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(GracefulShutdownLinux, self).cleanup(return_status)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)



if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if GracefulShutdownLinux.main() else Framework.TEST_RESULT_FAIL)
