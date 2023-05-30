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


class IbProvisioningWarmReset(SDSiBaseTestCase):
    """
    This test is to verify after applying the CAP, the ssku updates available counter is not reset to default value
    after the warm reset of the SUT.
    """

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 22013745930

    def execute(self) -> None:
        """
        This test is to verify after applying the CAP, the ssku updates available counter is not reset to default value
        after the warm reset of the SUT.
        """
        feature_list = []
        for socket in range(self.sdsi_agent.num_sockets):
            feature_list.append(self.sdsi_agent.apply_lac(socket))

        self._log.info("Perform a warm reset on SUT.")

        # Negative check warm reboot registers + CAP status
        self.sdsi_agent.verify_agent()
        try:
            self.sdsi_agent.validate_default_registry_values()
            error_msg = 'Register values were reset on warm reboot.'
            self._log.error(error_msg)
            raise SDSiExceptions.NegativeProvisioningError(error_msg)
        except (SDSiExceptions.LicenseKeyFailCountError, SDSiExceptions.AvailableUpdatesError):
            self._log.info('Register values not reset as expected.')
        for socket in range(self.sdsi_agent.num_sockets):
            self.sdsi_agent.validate_active_feature_set(socket, feature_list[socket], False)
        self._log.info('Features not activated with warm reboot expected.')

        # Positive check cold reboot registers
        self._log.info("Perform a cold reset.")
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_agent.verify_agent()
        self.sdsi_agent.validate_default_registry_values()
        for socket in range(self.sdsi_agent.num_sockets):
            self.sdsi_agent.validate_active_feature_set(socket, feature_list[socket])
        self._log.info('Features were activated with warm reboot expected.')

if __name__ == "__main__":
    sys.exit(not IbProvisioningWarmReset.run())
