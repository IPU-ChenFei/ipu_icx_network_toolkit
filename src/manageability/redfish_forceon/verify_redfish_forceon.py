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


class VerifyRedfishForceOnAPI(RedFishTestCommon):
    """
    HPQC ID: 80255
    This Testcase is basically to check the ability to Force On the server via the ResetType@Redfish command
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new  VerifyRedfishForceOnAPI object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyRedfishForceOnAPI, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """
        super(VerifyRedfishForceOnAPI, self).prepare()

    def execute(self):
        """
        Execute Main test case.

        :return: True if test completed successfully, False otherwise.
        """
        if not self.check_redfish_basic_authentication():
            self._log.info("Authorization to RedFish APIs failed!")
            raise RuntimeError("Error Occured during Authorization!")

        self._log.info("Force Off the System using RedFish API!")
        self.redfish_force_off()
        self._log.info("Force On the System!")
        self.redfish_force_on()

        if not self.os.is_alive():
            self._log.info("Failed to Force On the System through RedFish API!")
        else:
            self._log.info("Successfully Verified System Force On via RedFish API!")
        return self.check_sel()


# Execute this test with TestEngine when run as main.
if __name__ == '__main__':
    sys.exit(Framework.TEST_RESULT_PASS if VerifyRedfishForceOnAPI.main() else Framework.TEST_RESULT_FAIL)
