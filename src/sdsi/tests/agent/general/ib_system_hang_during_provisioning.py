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

from dtaf_core.lib.exceptions import OsCommandTimeoutException

from src.sdsi.tests.agent.general.ib_provisioning_test import InBandProvisioningTest


class InBandSystemHang(InBandProvisioningTest):
    """
    Verify the IB provisioning of the SSKU enabled CPU by applying a capability activation payload and verify it
    is available after the system hang.
    """

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 22013768611

    def execute(self) -> None:
        """
        Verify the IB provisioning of the SSKU enabled CPU by applying a capability activation payload and verify it
        is available after the system hang.
        """
        self.xmlcli_tool.set_bios_knobs({"PpinControl": "0x1"})

        self._log.info("Checking if sysrq is enabled")
        if not int(self.sut_os_tool.execute_cmd('cat /proc/sys/kernel/sysrq')) == 1:
            self._log.info("Sysrq was enabled for this boot")
            self.sut_os_tool.execute_cmd('sysctl -w kernel.sysrq=1')

        self._log.info("Executing OS command to crash the system")
        try: self.sut_os_tool.execute_cmd('echo c > /proc/sysrq-trigger')
        except OsCommandTimeoutException: super().execute()

if __name__ == "__main__":
    sys.exit(not InBandSystemHang.run())
