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

from src.hsio.upi.hsio_upi_common import HsioUpiCommon


class UpiTxState(HsioUpiCommon):
    """
    hsdes id: 22012848279 upi_non_ras_tx_state
    HSD ID: 18016910123 PI_Verify_UPI_Tx_Status_at_OS
    This test verifies upi trx port state in L0 and ready
    Note: after SPR BKC 57 C6 has to be disabled to reduce L1 link states seen in rx/tx
    """
    _BIOS_CONFIG_FILE = "C6_disabled.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UpiTxState object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UpiTxState, self).__init__(
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
        super(UpiTxState, self).prepare()

    def execute(self):

        tx_ports_in_expected_l0_state = self.verify_tx_ports_l0_state()
        if not tx_ports_in_expected_l0_state:
            self.verify_no_upi_errors_indicated()
            return False

        return self.verify_no_upi_errors_indicated()


if __name__ == "__main__":

    sys.exit(Framework.TEST_RESULT_PASS if UpiTxState.main()
             else Framework.TEST_RESULT_FAIL)
