#!/usr/bin/env python
##########################################################################
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
##########################################################################

import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.ras.tests.dwr.dwr_common import DwrCommon


class DownGradedWarmReset(DwrCommon):
    """
    Glasgow_id : 59148
    This TestCase is When DWR feature is enabled, Lewisburg can demote Host Partition Reset Timeout (HPR TO)
    events into a demoted warm reset i.e., warm reset without the negotiation.System is not guaranteed to reliably boot
    after the demoted warm reset, but the expectation is that it will load UEFI-FW in most instances. UEFI-FW is
    expected to boot in safe mode following a demoted warm reset. UEFI-FW reads a Lewisburg status register to determine
    if the last reset was a Demoted Warm Reset. When booting after demoted warm reset,the UEFI-FW is expected to perform
    minimal initialization steps, read error logs, deposit error logs to non-volatile memory and issue a global reset.
    UEFI-FW should not attempt to boot an OS in this mode. The sole purpose of the demoted warm reset is to increase the
    odds that the OEM firmware will be able to collect error logs in fatal error conditions.
    """
    _BIOS_CONFIG_FILE = "../dwr_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new DownGradedWarmReset object
        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(DownGradedWarmReset, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

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
        super(DownGradedWarmReset, self).prepare()

    def execute(self):
        """
        Executing check_dwr_enable method to verify whether dwr enable is
        enabled or not.
        :return: True if dwr_enable method is executed Successfully.
        """
        return self.verify_dwr_enable()  # Verify whether dwr is enabled or not


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if DownGradedWarmReset.main() else Framework.TEST_RESULT_FAIL)
