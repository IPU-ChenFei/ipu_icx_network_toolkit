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
from src.pcie.tests.pcie_common import PcieCommon


class VerifyPCIeDMILinkStatus(PcieCommon):
    """
    TestCase ID : 53951

    This TestCase checks DMI Link Status of PCIe card in the System.

    """
    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VerifyPCIeDMILinkStatus object,

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param arguments: None
        """
        super(VerifyPCIeDMILinkStatus, self).__init__(test_log, arguments, cfg_opts)

    def execute(self):
        """
        This TestCase checks DMI Link Status of PCIe card in the System.

        :return: True if passed else False
        :raise: None
        """
        return self.verify_pcie_dmi_link_status()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyPCIeDMILinkStatus.main() else Framework.TEST_RESULT_FAIL)
