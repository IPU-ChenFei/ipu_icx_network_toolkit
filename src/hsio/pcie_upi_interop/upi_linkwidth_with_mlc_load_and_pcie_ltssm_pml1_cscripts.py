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

from src.pcie.tests.pi_pcie.pcie_common import LtssmTestType
from src.hsio.pcie_upi_interop.pcie_upi_interop_common import PcieUpiInteropCommon


class UpiLinkwidthWithMlcLoadAndPcieLtssmPML1Cscripts(PcieUpiInteropCommon):
    """
    Phoenix ID: 22014434505, 15010752766

    The purpose of this Test Case is run the PML1 LTSSM test on the configured PCIe endpoint at Gen4/Gen5 speed

    """
    TEST_CASE_ID = ["22014434505", "PCI Express x UPI Interop - upi_non_ras_linkwidth with mlc load and PCI Express - "
                                   "Endpoint LTSSM Testing - PML1 - cscripts"]
    _BIOS_CONFIG_FILE = "pcie_upi_interop_bios_knobs_config_{}.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a UpiLinkwidthWithMlcLoadAndPcieLtssmPML1Cscripts object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UpiLinkwidthWithMlcLoadAndPcieLtssmPML1Cscripts, self).__init__(test_log, arguments, cfg_opts,
                                                                              self._BIOS_CONFIG_FILE)

    def prepare(self):  # type: () -> None
        """
        prepare
        """
        super(UpiLinkwidthWithMlcLoadAndPcieLtssmPML1Cscripts, self).prepare()

    def execute(self):
        """
        This method is to execute:
        1. Check Link and Width Speed.
        2. Test LTSSM test execution
        3. Check MCE Log in OS Log.

        :return: True or False
        """

        return self.run_ltssm_with_mlc(LtssmTestType.PML1.split())


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UpiLinkwidthWithMlcLoadAndPcieLtssmPML1Cscripts.main() else Framework.TEST_RESULT_FAIL)
