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

from dtaf_core.lib.dtaf_constants import Framework

from src.pcie.tests.pi_pcie.pcie_common import PcieCommon, PxpInventory


class PcieGen5eLinkSpeedAndWidthVerification(PcieCommon):
    """
    Phoenix ID: 15010155361

    To verify that each Gen5 PCI express slot in the system can link a Gen5 adapter at all supported link widths.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PcieGen5eLinkWidthVerification object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieGen5eLinkSpeedAndWidthVerification, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):  # type: () -> None
        """
        prepare
        """
        super(PcieGen5eLinkSpeedAndWidthVerification, self).prepare()

    def execute(self):
        """
        This method is to execute:
        1. Check Link and Width Speed.

        :return: True or False
        """
        self.verify_link_width_speed(gen=PxpInventory.PCIeLinkSpeed.GEN5, protocol=PxpInventory.IOProtocol.PCIE)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieGen5eLinkSpeedAndWidthVerification.main() else Framework.TEST_RESULT_FAIL)
