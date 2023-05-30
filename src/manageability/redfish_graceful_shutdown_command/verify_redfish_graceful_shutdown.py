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
from src.manageability.lib.redfish_test_common import RedFishTestCommon


class VerifyRedfishGracefulShutdownAPI(RedFishTestCommon):
    """
    HPQC ID: 80032
    This Testcase is basically to check the ability to Gracefully Shutdown the server via the ResetType@Redfish command
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new  VerifyRedfishOnOffAPI object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyRedfishGracefulShutdownAPI, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """
        super(VerifyRedfishGracefulShutdownAPI, self).prepare()
        self.change_power_setting_for_redfish(mask=True)

    def execute(self):
        """
        Execute Main test case.

        :return: True if test completed successfully, False otherwise.
        """
        if not self.check_redfish_basic_authentication():
            self._log.info("Authorization to RedFish APIs failed!")
            raise RuntimeError("Error Occured during Authorization!")

        self._log.info("Perform 10 Cycles of Graceful Shutdown!")
        for i in range(1, 11):
            self._log.info("Press power button on SUT and boot into the OS!- Cycle {}".format(i))
            if not self.os.is_alive():
                self._log.info("System has been turned off! Boot it to OS")
                self.redfish_power_on()
            else:
                self._log.info("System is already Up!")
            self.redfish_graceful_shutdown()
            self._log.info("ShutDown the System Gracefully!- Cycle {}".format(i))

        self._log.info("Successfully Completed 10 Cycles of Graceful Shutdown!")
        return self.check_sel()

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        if not self.os.is_alive():
            self._log.info("System has been turned off! Boot it to OS")
            self.redfish_power_on()
        self.change_power_setting_for_redfish(mask=False)
        super(VerifyRedfishGracefulShutdownAPI, self).cleanup(return_status)


# Execute this test with TestEngine when run as main.
if __name__ == '__main__':
    sys.exit(Framework.TEST_RESULT_PASS if VerifyRedfishGracefulShutdownAPI.main() else Framework.TEST_RESULT_FAIL)
