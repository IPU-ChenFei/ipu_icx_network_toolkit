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

import src.sdsi.lib.sdsi_exceptions as SDSiExceptions
from src.sdsi.lib.sdsi_base_test_case import SDSiBaseTestCase


class IbUpgradeLimitPerBootVerification(SDSiBaseTestCase):
    """
    Validate that register values for SDSi match expected functionality, and provisioning is allowed accordingly.
    """

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 22013734416

    def execute(self) -> None:
        """
        Validate that register values for SDSi match expected functionality, and provisioning is allowed accordingly.
        """
        # Erase Provisioning from CPUs to ensure clean config
        self.sdsi_agent.erase_provisioning()
        self.cycling_tool.perform_ac_cycle()

        # Provision sockets with LACs to test available update limit.
        for socket in range(self.sdsi_agent.num_sockets):
            self._log.info(f'Applying first LAC to socket {socket} with AKC. This will use both available updates.')
            self.sdsi_agent.apply_lac(socket)
            self._log.info(f'First LAC applied to socket {socket} as expected.')

            self._log.info(f'Applying second LAC to socket {socket}. This should fail due to insufficient updates.')
            try:
                self.sdsi_agent.apply_lac(socket)
                error_msg = f'Second provisioning should not succeed on socket {socket} due to insufficient updates.'
                self._log.error(error_msg)
                raise SDSiExceptions.NegativeProvisioningError(error_msg)
            except SDSiExceptions.ProvisioningError:
                self._log.info(f'Second LAC failed to apply to socket {socket} as expected.')

if __name__ == "__main__":
    sys.exit(not IbUpgradeLimitPerBootVerification.run())
