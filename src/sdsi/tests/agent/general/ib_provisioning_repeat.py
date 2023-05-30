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

from src.sdsi.lib.sdsi_base_test_case import SDSiBaseTestCase


class InBandProvisioningRepeat(SDSiBaseTestCase):
    """
    Verify the inband provisioning of the SSKU enabled CPU by applying an LAC and verify it is available.
    Repeat process multiple times with erase certificate between to verify sustained functionality.
    """
    REPEAT_COUNT = 30

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 0

    def execute(self) -> None:
        """
        Verify the inband provisioning of the SSKU enabled CPU by applying an LAC and verify it is available.
        Repeat process multiple times with erase certificate between to verify sustained functionality.
        """
        for repeat_count in range(self.REPEAT_COUNT):
            # Provision an LAC on each socket
            self._log.info(f'Performing repeated provisioning #{repeat_count}.')
            active_features = [self.sdsi_agent.apply_lac(socket) for socket in range(self.sdsi_agent.num_sockets)]

            # Cold reboot and validate features are active.
            self.cycling_tool.perform_ac_cycle()
            for socket in range(self.sdsi_agent.num_sockets):
                self.sdsi_agent.validate_active_feature_set(socket, active_features[socket])

            # Erase Provisioning from all sockets
            self.sdsi_agent.erase_provisioning()
            self.cycling_tool.perform_ac_cycle()

if __name__ == "__main__":
    sys.exit(not InBandProvisioningRepeat.run())
