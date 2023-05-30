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


class InBandEraseProvisioning(SDSiBaseTestCase):
    """
    Using SDSi Agent, apply a License Erase Certification Key and verify
    the CPU provisioning information stored in NVRAM is deleted.
    """

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 22013655727

    def execute(self) -> None:
        """
        Using SDSi Agent, apply a License Erase Certification Key and verify
        the CPU provisioning information stored in NVRAM is deleted.
        """
        # Provision sockets if there are no payloads on the socket in order to test erase functionality
        reset_required = False
        for socket in range(self.sdsi_agent.num_sockets):
            if not self.sdsi_agent.is_cpu_provisioned(socket):
                reset_required = True
                self._log.info(f"Socket {socket} is not already provisioned.")
                self.sdsi_agent.apply_lac(socket)

        # Reboot SUT to apply provisioned LACs if required
        if reset_required: self.cycling_tool.perform_ac_cycle()

        # Erase provisioning from all sockets
        self.sdsi_agent.erase_provisioning()

if __name__ == "__main__":
    sys.exit(not InBandEraseProvisioning.run())
