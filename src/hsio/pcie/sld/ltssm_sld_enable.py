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

import os
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.pcie.tests.pi_pcie.pcie_endpoint_ltssm_testing import PcieEndPointLtssmTesting


class PcieEndPointLtssmSldEnable(PcieEndPointLtssmTesting):
    """
    Phoenix ID: 16016514206

    To verify LTSSM tests with SLD enable at Gen5 speed - Linux, Windows
    """
    TEST_CASE_ID = ["16016514206", "16016514266", "LTSSM_with_SLD_enable_in_Windows", "LTSSM_with_SLD_enable_in_LInux"]
    BIOS_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sld_logging_bios_knobs.cfg")

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PcieEndPointLtssmSldEnableLinux object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieEndPointLtssmSldEnable, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

    def prepare(self):  # type: () -> None
        """
        prepare
        """
        super(PcieEndPointLtssmSldEnable, self).prepare()

    def execute(self):
        """
        This method is to execute:
        1. Check Link and Width Speed.
        2. Test LTSSM test execution
        3. Check MCE Log in OS Log.

        :return: True or False
        """
        super(PcieEndPointLtssmSldEnable, self).execute()
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieEndPointLtssmSldEnable.main() else Framework.TEST_RESULT_FAIL)
