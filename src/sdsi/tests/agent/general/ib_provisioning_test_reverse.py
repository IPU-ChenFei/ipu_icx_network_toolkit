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
import random
import sys

from src.sdsi.lib.sdsi_base_test_case import SDSiBaseTestCase


class IbProvisioningTestReverse(SDSiBaseTestCase):
    """
    This test case is to verify the IB provisioning of the SSKU enabled CPU by applying the license key certificate,
    and a capability activation payload and verify it is available. This test writes to sockets in varying order.
    For 2 socket systems, write socket 1 then 0. For 4 and 8 socket systems, write to sockets in a random order.
    """

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 22013767530

    def execute(self) -> None:
        """
        Verify the IB provisioning of the SSKU enabled CPU by applying a capability activation payload and verify it is
        available. This test writes to sockets in varying order. For 2 socket systems, write socket 1 then 0.
        For 4 and 8 socket systems, write to sockets in a random order.
        """
        feature_info = {}
        socket_order = list(range(self.sdsi_agent.num_sockets))[::-1]
        if self.sdsi_agent.num_sockets > 2: random.shuffle(socket_order)

        # Apply LACs to sockets in reverse order / random order.
        for socket in socket_order:
            feature_info[socket] = self.sdsi_agent.apply_lac(socket)

        # Reboot SUT to apply changes then validate registry values.
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_agent.validate_default_registry_values()

        # Validate the LACs are applied correctly and activated after reboot.
        for socket in socket_order:
            self.sdsi_agent.validate_active_feature_set(socket, feature_info[socket])

if __name__ == "__main__":
    sys.exit(not IbProvisioningTestReverse.run())
