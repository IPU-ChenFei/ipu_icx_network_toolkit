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


class IbMultiSocketProvisioningSingleSocketSupport(SDSiBaseTestCase):
    """
    Verify that a CPU with external UPI links disabled to facilitate single socket operation can only be provisioned
    when installed in the valid sockets. The NVRAM region of the CPU may only read when installed in this socket.
    """

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 0

    def execute(self) -> None:
        """
        Verify that a CPU with external UPI links disabled to facilitate single socket operation can only be provisioned
        when installed in the valid sockets. The NVRAM region of the CPU may only read when installed in this socket.
        """
        for socket in range(self.sdsi_agent.num_sockets):
            if self.sdsi_agent.is_sdsi_enabled(socket):
                self._log.info(f'SDSi is enabled on socket {socket}. Provisioning is expected to succeed.')
                active_features = self.sdsi_agent.apply_lac(socket)
                self.cycling_tool.perform_ac_cycle()
                self.sdsi_agent.validate_active_feature_set(socket, active_features)
                self._log.info(f'Provisioning succeeded as expected for socket {socket}.')
            else:
                self._log.info(f'SDSi is not enabled on socket {socket}. Provisioning is expected to fail.')
                try:
                    active_features = self.sdsi_agent.apply_lac(socket)
                    self.cycling_tool.perform_ac_cycle()
                    self.sdsi_agent.validate_active_feature_set(socket, active_features)
                    error_msg = f'Provisioning was expected to fail but succeeded on socket {socket}.'
                    self._log.error(error_msg)
                    raise SDSiExceptions.NegativeProvisioningError(error_msg)
                except (SDSiExceptions.AgentReadError, SDSiExceptions.ProvisioningError):
                    self._log.info(f'Provisioning failed as expected for socket {socket}.')

if __name__ == "__main__":
    sys.exit(not IbMultiSocketProvisioningSingleSocketSupport.run())
