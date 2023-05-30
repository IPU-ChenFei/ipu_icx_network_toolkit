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


class IbOutOfOrderFeatureActivationProvisioning(SDSiBaseTestCase):
    """
    Expectation is that a license with a higher revision id than those previously applied are provisioned,
    but if a revision id is skipped, then a license for that CPU with that revision id will not be provisioned.
    The OOB-MSM driver will need to be configured to load on every OS boot since our content includes system resets.
    """

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 22013740200

    def execute(self) -> None:
        """
        Expectation is that a license with a higher revision id than those previously applied are provisioned,
        but if a revision id is skipped, then a license for that CPU with that revision id will not be provisioned.
        """
        # Loop through each socket to perform out of order provisioning
        for socket in range(self.sdsi_agent.num_sockets):
            # Retrieve the 3 payloads to use for the test
            available_lacs = self.sdsi_agent.get_applicable_lacs(socket)
            if len(list(available_lacs)) < 3:
                error_msg = f'Not enough available payloads for socket {socket}. At least 3 are required for this test.'
                self._log.error(error_msg)
                raise SDSiExceptions.MissingCapError(error_msg)
            lac_one: Tuple[int, str] = list(available_lacs.items())[0] # noqa
            lac_two: Tuple[int, str] = list(available_lacs.items())[1] # noqa
            lac_three: Tuple[int, str] = list(available_lacs.items())[2] # noqa

            # Provision middle revision, expecting success
            self._log.info(f'Applying middle revision LAC to socket {socket}, success expected: {lac_one[1]}')
            self.sdsi_agent.apply_lac(socket, lac_two)
            self._log.info(f'Middle revision LAC provision success for socket {socket}.')

            # Provision previous revision, expecting failure
            self._log.info(f'Applying previous revision LAC to socket {socket}, failure expected: {lac_one[1]}')
            try:
                self.sdsi_agent.apply_lac(socket, lac_one)
                error_msg = f'Previous provisioning succeeded for previous revision number for socket {socket}.'
                self._log.error(error_msg)
                raise SDSiExceptions.CapRevisionError(error_msg)
            except SDSiExceptions.ProvisioningError:
                self._log.info(f'Previous revision LAC provision failed as expected for socket {socket}.')

            # Perform reboot to reset available updates
            self.cycling_tool.perform_ac_cycle()

            # Provision final revision, expecting success
            self._log.info(f'Applying final revision LAC to socket {socket}, success expected: {lac_three[1]}')
            self.sdsi_agent.apply_lac(socket, lac_three)
            self._log.info(f'Final revision LAC provision success for socket {socket}.')

if __name__ == "__main__":
    sys.exit(not IbOutOfOrderFeatureActivationProvisioning.run())
