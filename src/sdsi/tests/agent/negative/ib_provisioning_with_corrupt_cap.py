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


class IbProvisioningWithCorruptCap(SDSiBaseTestCase):
    """
    Verify the In Band provisioning of the SSKU enabled CPU by applying a corrupt capability activation payload
    and verify it is unavailable.
    """

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 22013642595

    def execute(self) -> None:
        """
        Verify the In Band provisioning of the SSKU enabled CPU by applying a corrupt capability activation payload
        and verify it is unavailable.
        """
        # Ensure corrupt LAC cannot be applied to each socket
        for socket in range(self.sdsi_agent.num_sockets):
            self._log.info(f"Apply the corrupted payload configuration for socket {socket}.")
            try:
                self.sdsi_agent.apply_corrupt_lac(socket)
                error_msg = f'Corrupt LAC was successfully applied to socket {socket}.'
                self._log.error(error_msg)
                raise SDSiExceptions.NegativeProvisioningError(error_msg)
            except SDSiExceptions.ProvisioningError:
                self._log.info(f"Corrupted LAC configuration was not applied for socket {socket}.")

if __name__ == "__main__":
    sys.exit(not IbProvisioningWithCorruptCap.run())
