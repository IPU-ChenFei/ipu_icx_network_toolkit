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
from src.pcie.tests.pcie_common import PcieCommon


class PcieEnumerationLinux(PcieCommon):
    """
    Glasgow_id : 79588
    This Testcase is used to check if a pcie device exist in the system and
    checks Information of all Pcie Connected Devices.

    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PcieEnumerationLinux object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieEnumerationLinux, self).__init__(test_log, arguments, cfg_opts)

    def execute(self):
        """
        This is Used to Verify if Pcie Card is Detected in System and
        verify if the Speed and Width of Pcie Device is
        as Expected.

        :return: True or False
        """
        return self.verify_pcie_enumeration()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieEnumerationLinux.main() else Framework.TEST_RESULT_FAIL)
