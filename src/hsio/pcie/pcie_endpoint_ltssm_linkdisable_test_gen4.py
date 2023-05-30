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
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.test_content_logger import TestContentLogger
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon, LtssmTestType
from src.lib.dtaf_content_constants import PcieSlotAttribute, PcieAttribute
from src.lib import content_exceptions
from src.pcie.tests.pi_pcie.pcie_endpoint_ltssm_test_gen4 import PcieEndPointLtssmTestingGen4Linux


class PcieEndPointLtssmLinkDisableTestingGen4Linux(PcieEndPointLtssmTestingGen4Linux):
    """
    Phoenix ID: 14015470724

    The purpose of this Test Case is run the Link Disable LTSSM test on the configured PCIe endpoint at Gen4 speed

    """
    TEST_CASE_ID = ["14015470724", "PCI_Express_Endpoint_LTSSM_Testing_EnableDisable"]
    LTSSM_TEST = LtssmTestType.LINKDISABLE

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PcieEndPointLtssmLinkDisableTestingGen4Linux object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieEndPointLtssmLinkDisableTestingGen4Linux, self).__init__(test_log, arguments, cfg_opts)
        self.LTSSM_TEST_NAME_LIST = self.LTSSM_TEST.split()

    def prepare(self):  # type: () -> None
        """
        prepare
        """
        super(PcieEndPointLtssmLinkDisableTestingGen4Linux, self).prepare()

    def execute(self):
        """
        This method is to execute:
        1. Check Link and Width Speed.
        2. Test LTSSM test execution
        3. Check MCE Log in OS Log.

        :return: True or False
        """
        super(PcieEndPointLtssmLinkDisableTestingGen4Linux, self).execute()
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieEndPointLtssmLinkDisableTestingGen4Linux.main() else Framework.TEST_RESULT_FAIL)
