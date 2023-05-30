#!/usr/bin/env python
##########################################################################
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
##########################################################################
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.ras.tests.io_virtualization.pass_through_base_test import PciPassThroughBaseTest


class VirtualizationHyperVPciNetworkPassthrough(PciPassThroughBaseTest):
    """
    This test case is to Network a PCI-E device passed to the VM (VT-d).
    """

    bios_config_file = "vtd_bios_knobs.cfg"

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts
    ):
        """
        Create an instance of VirtualizationHyperVPciNetworkPassthrough

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(
            VirtualizationHyperVPciNetworkPassthrough,
            self).__init__(
            test_log,
            arguments,
            cfg_opts, bios_config_file=self.bios_config_file)
        self.cfg_opts = cfg_opts

    def prepare(self):  # type: () -> None
        """
        execute the prepare.
        """
        super(VirtualizationHyperVPciNetworkPassthrough, self).prepare()

    def execute(self):  # type: () -> bool
        """
        execute the test steps.
        """
        super(VirtualizationHyperVPciNetworkPassthrough, self).execute()

        return True

    def cleanup(self, return_status):
        """
        execute the cleanup.
        """
        super(VirtualizationHyperVPciNetworkPassthrough, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationHyperVPciNetworkPassthrough.main()
             else Framework.TEST_RESULT_FAIL)
