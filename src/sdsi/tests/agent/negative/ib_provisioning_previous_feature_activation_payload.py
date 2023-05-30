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
from typing import Tuple

import src.sdsi.lib.sdsi_exceptions as SDSiExceptions
from src.sdsi.lib.sdsi_base_test_case import SDSiBaseTestCase


class IbProvisioningPreviousFeatureActivationPayload(SDSiBaseTestCase):
    """
    This test is to verify platform behavior when a used Feature Activation Payload is applied to
    a previously provisioned system. Subsequent feature application should be disallowed.
    """

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 22013642500

    def execute(self) -> None:
        """
        This test is to verify platform behavior when a used Feature Activation Payload is applied to
        a previously provisioned system. Subsequent feature application should be disallowed.
        """
        # Provision sockets with the same LACs twice
        for socket in range(self.sdsi_agent.num_sockets):
            # Retrieve the LAC to apply twice
            available_lac: Tuple[int, str] = list(self.sdsi_agent.get_applicable_lacs(socket).items())[0] # noqa

            # Apply LAC for the first time, expecting success.
            self._log.info(f'Applying LAC to socket {socket} for the first time.')
            self.sdsi_agent.apply_lac(socket, available_lac)
            self._log.info(f'LAC applied to socket {socket} as expected.')

            # Apply same LAC to the same socket, expecting failure
            self.cycling_tool.perform_ac_cycle()
            self._log.info(f'Applying same LAC to socket {socket}.')
            try:
                self.sdsi_agent.apply_lac(socket, available_lac)
                error_msg = f'Second provisioning should not succeed on socket {socket} due to duplicate LAC.'
                self._log.error(error_msg)
                raise SDSiExceptions.NegativeProvisioningError(error_msg)
            except SDSiExceptions.ProvisioningError:
                self._log.info(f'LAC failed to apply to socket {socket} as expected.')

if __name__ == "__main__":
    sys.exit(not IbProvisioningPreviousFeatureActivationPayload.run())
