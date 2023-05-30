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

from src.ras.lib.smbus_error_util import SmbusErrorUtil
from src.ras.tests.mem_smbus_recovery.mem_smbus_common import MemSmbusCommon


class MemSmbusErrorInjection(MemSmbusCommon):
    """
    Glasgow ID: 58527
    This test injects SMBus Error and checks error recovery
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new MemSmbusErrorInjection object
        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(MemSmbusErrorInjection, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Setting the bios knobs to its default mode.
        3. Setting the bios knobs as per the test case.
        4. Rebooting the SUT to apply the new bios settings.
        5. Verifying the bios knobs that are set.
        :return: None
        """
        super(MemSmbusErrorInjection, self).prepare()

    def execute(self):
        test_status = False
        smbus_error_utils_obj = SmbusErrorUtil(self._log, self._sdp, self._cscripts)
        smb_rec = smbus_error_utils_obj.is_smbus_error_recovery_enabled(socket_index=0, mc=None)

        if not smb_rec:
            self._log.info("SMBus error recovery is not enabled by BIOS...")
            return test_status

        self._log.info("Verify SMBus error recovery...")
        is_smb_rec = smbus_error_utils_obj.smb_error_injection(socket_index=0, mc=None)
        if not is_smb_rec:
            self._log.error("FAIL: SMBus error recovery \n")
        else:
            test_status = True
            self._log.info("PASS: SMBus error recovery\n")

        return test_status


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MemSmbusErrorInjection.main() else Framework.TEST_RESULT_FAIL)
