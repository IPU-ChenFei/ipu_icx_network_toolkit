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

from src.hsio.pcie_upi_interop.pcie_upi_interop_common import PcieUpiInteropCommon


class Pxp4SpeedVerification4SX8X8(PcieUpiInteropCommon):
    """
    hsdes_id : 22014925104 PCI Express x UPI Interop - Verify all PXP ports train at 32 GT/s (Gen5) on 4S platform w/o UPI3 - PCIe x8x8
    hsdes_id : 22014922009 PCI Express x UPI Interop - Verify all PXP ports train at 32 GT/s (Gen5) with all UPI lanes active (slot walk) - PCIe x8x8

    The purpose of this test is to verify that all PXP ports train at Gen5 when all UPI lanes are active
    """
    _BIOS_CONFIG_FILE = None

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new Pxp4SpeedVerification4SX8X8 object
        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(Pxp4SpeedVerification4SX8X8, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.
        :return: None
        """
        super(Pxp4SpeedVerification4SX8X8, self).prepare()

    def execute(self):

        return self.run_pe3upi3_pxp4_verification_test(bifurcation=self._BIFURCATION_x8x8)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if Pxp4SpeedVerification4SX8X8.main() else Framework.TEST_RESULT_FAIL)
