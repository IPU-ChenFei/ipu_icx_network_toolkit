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
from src.lib.dtaf_content_constants import TimeConstants
from src.hsio.upi.hsio_upi_common import HsioUpiCommon


class UpiWarmReset12Hr(HsioUpiCommon):
    """
    hsdes id: 22015141509  upi_linkwidth_rx_tx_warm_reset_cycling_12hr
    This test verifies UPI link width/rx/tx is stable and all lanes are active during each warm reset
    and repeat for 12 hours
    Note: after SPR BKC 57 C6 has to be disabled to reduce L1 link states seen in rx/tx
    """
    _BIOS_CONFIG_FILE = "C6_disabled.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UpiWarmReset12Hr object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UpiWarmReset12Hr, self).__init__(
            test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

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
        super(UpiWarmReset12Hr, self).prepare()

    def execute(self):
        return self.run_upi_cycle_tests("12Hr_test", self._upi_checks.WARM_RESET, num_cycles=2000,
                                        run_time=TimeConstants.TWELVE_HOURS_IN_SEC)


if __name__ == "__main__":

    sys.exit(Framework.TEST_RESULT_PASS if UpiWarmReset12Hr.main()
             else Framework.TEST_RESULT_FAIL)
