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
from src.hsio.pcie.bifurcation.bifurcation_base_test import BifurcationBaseTest


class PcieLinkTrainingAndInitializationBifurcation(BifurcationBaseTest):
    """
    Phoenix ID: 15010162501

    This test is meant to verify the Link Width of the populated PCIe devices after Bifurcation through BIOS Knobs
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PcieLinkTrainingAndInitializationBifurcation object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieLinkTrainingAndInitializationBifurcation, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):  # type: () -> None
        """
        prepare
        """
        super(PcieLinkTrainingAndInitializationBifurcation, self).prepare()

    def execute(self):
        """
        This method is to execute:
        1. verify the Speed and Width of Card (x4x4x4x4) in OS.

        :return: True or False
        """
        if self._common_content_configuration.get_pcie_bifurcation_auto_discovery():
            self.validate_speed_width_in_os()
        else:
            self.validate_speed_and_width_in_os()
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieLinkTrainingAndInitializationBifurcation.main() else
             Framework.TEST_RESULT_FAIL)
