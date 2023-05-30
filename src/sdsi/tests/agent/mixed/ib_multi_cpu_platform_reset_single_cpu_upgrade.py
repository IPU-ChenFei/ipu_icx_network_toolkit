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


class IbMultiCpuResetSingleCpuUpgrade(SDSiBaseTestCase):
    """
    Verify single CPU with capabilities and make sure that it is not affecting the other CPUs.
    """

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 18014074497

    def execute(self) -> None:
        """
        Verify single CPU with capabilities and make sure that it is not affecting the other CPUs.
        """
        for socket in range(self.sdsi_agent.num_sockets):
            # Ensure cpu is not provisioned after erase
            if self.sdsi_agent.is_cpu_provisioned(socket):
                error_msg = f'Socket {socket} is provisioned after erase operation.'
                self._log.error(error_msg)
                raise SDSiExceptions.EraseProvisioningError(error_msg)

            # Provision payload on single socket and verify
            active_features = self.sdsi_agent.apply_lac(socket)
            self.cycling_tool.perform_ac_cycle()
            self.sdsi_agent.validate_active_feature_set(socket, active_features)

            # Verify provisioning is not applied to other sockets
            for other_socket in [s for s in range(self.sdsi_agent.num_sockets) if s != socket]:
                if self.sdsi_agent.is_cpu_provisioned(other_socket):
                    error_msg = f'Socket {other_socket} is provisioned after provisioning socket {socket}.'
                    self._log.error(error_msg)
                    raise SDSiExceptions.ProvisioningError(error_msg)

            # Erase provisioning to continue test
            self.sdsi_agent.erase_provisioning()
            self.cycling_tool.perform_ac_cycle()

if __name__ == "__main__":
    sys.exit(not IbMultiCpuResetSingleCpuUpgrade.run())
