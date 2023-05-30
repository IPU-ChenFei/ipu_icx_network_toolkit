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

from src.sdsi.tests.agent.general.ib_provisioning_test import InBandProvisioningTest


class IbProvisioningTestGlobalReset(InBandProvisioningTest):
    """
    Verify the In Band provisioning of the SSKU enabled CPU by applying a capability activation payload and
    verify it is available with Global reset enabled.
    """

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 22013725176

    def prepare(self) -> None:
        """Perform preparation for test"""
        super().prepare()
        self._log.info("Enable Global Reset by disabling Global Reset Lock in the BIOS.")
        self.xmlcli_tool.set_bios_knobs({"MeGrLockEnabled": "0x0"})

        self._log.info("Perform reboot for the BIOS changes to take effect.")
        self.cycling_tool.perform_ac_cycle()

        self._log.info("Verify the Global reset is enabled")
        self.xmlcli_tool.verify_bios_knobs({"MeGrLockEnabled": "0x0"})

    def cleanup(self) -> None:
        """Perform cleanup for test"""
        self._log.info("Disable Global Reset by enabling Global Reset Lock in the BIOS.")
        self.xmlcli_tool.set_bios_knobs({"MeGrLockEnabled": "0x1"})

        self._log.info("Perform reboot for the BIOS changes to take effect.")
        self.cycling_tool.perform_ac_cycle()

        self._log.info("Verify the Global reset is disabled")
        self.xmlcli_tool.verify_bios_knobs({"MeGrLockEnabled": "0x1"})

        super().cleanup()


if __name__ == "__main__":
    sys.exit(not IbProvisioningTestGlobalReset.run())
