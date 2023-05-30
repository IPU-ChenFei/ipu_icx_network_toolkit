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

from src.hsio.upi.hsio_upi_common import HsioUpiCommon


class UpiDegradation4sRemoveAllLinkWithMLC(HsioUpiCommon):
    """
    hsdes_id :  22014215834 Verify 4S UPI degradation- remove all links with MLC stress

    1.This test verifies OS functionality after 4S platform has been degraded to 0 ports
    2.Verify 1 socket S0 is available
    3.Verify OS is stable by running MLC stress for 2 hours
    """
    _BIOS_CONFIG_FILE = "upi_max_linkspeed.cfg"
    SOCKET_PORT_PAIR_DOWN_LIST = [(0, 2), (1, 2), (0, 0), (0, 1), (1, 0), (2, 0)]
    SOCKETS_LIST_AFTER_DEGRADATION = [0]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UpiDegradation4sRemoveAllLinkWithMLC object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UpiDegradation4sRemoveAllLinkWithMLC, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

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
        super(UpiDegradation4sRemoveAllLinkWithMLC, self).prepare()

    def execute(self):

        result = self.run_upi_degrade_test(socket_port_pairs_list=self.SOCKET_PORT_PAIR_DOWN_LIST,
                                           check_remaining_socket_count=1)

        return result


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UpiDegradation4sRemoveAllLinkWithMLC.main() else Framework.TEST_RESULT_FAIL)
