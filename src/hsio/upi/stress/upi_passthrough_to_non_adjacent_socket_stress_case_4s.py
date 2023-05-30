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

from src.hsio.upi.functional.upi_passthrough_to_non_adjacent_socket_basic_case_4s import \
    UpiPassthroughToAdjacentSocketBasic4s


class UpiPassthroughToAdjacentSocketStress4s(UpiPassthroughToAdjacentSocketBasic4s):
    """
    hsdes_id : 22014226986

    This test checks for proper passthrough of UPI traffic from non-adjacent
    NUMA Nodes (CPU sockets) via a common adjacent node.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UpiPassthroughToAdjacentSocketStress4s object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UpiPassthroughToAdjacentSocketStress4s, self).__init__(test_log, arguments, cfg_opts)

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
        super(UpiPassthroughToAdjacentSocketStress4s, self).prepare()

    def execute(self):
        """
        This method is to execute

        1. Check Port 2 is connected.
        2. Set the Bios to Disable Port 2.
        3. Check Port is disable or not.
        4. Check Numactl rout cost - i.e 31.
        5. Apply stress on Network.
        6. Set the Bios to re-establish the Port.
        7. Verify the Port is re-established or not.
        """
        super(UpiPassthroughToAdjacentSocketStress4s, self).execute(stress=True, num_ns='2',
                                                                    test_duration=
                                                                    self.UPI_PASSTHROUGH_STRESS_TEST_RUN_TIME_SEC)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UpiPassthroughToAdjacentSocketStress4s.main() else
             Framework.TEST_RESULT_FAIL)
