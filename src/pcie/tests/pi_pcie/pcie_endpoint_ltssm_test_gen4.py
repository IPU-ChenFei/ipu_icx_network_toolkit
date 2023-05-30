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

from src.lib.test_content_logger import TestContentLogger
from src.pcie.tests.pi_pcie.pcie_endpoint_ltssm_basetest import PcieEndPointLtssmBaseTest


class PcieEndPointLtssmTestingGen4Linux(PcieEndPointLtssmBaseTest):
    """
    HPQC ID : H89962-PI_PCIe_Endpoint_LTSSM_Testing_Gen4_L

    The purpose of this Test Case is to verify the functionality of all supported pcie link state transition
    for a specific adapter in all slot of the system.
    """
    BIOS_CONFIG_FILE = "gen4_bios_knobs_config.cfg"
    TEST_CASE_ID = ["H89962", "PI_PCIe_Endpoint_LTSSM_Testing_Gen4_L"]

    step_data_dict = {
        1: {'step_details': 'Check PCIe device Link speed and Width speed',
            'expected_results': 'PCIe Link speed and width speed as Expected'},
        2: {'step_details': 'Disable the driver and run the ltssm test',
            'expected_results': 'Device driver disabled successfully and passed ltssm Test'},
        3: {'step_details': 'Check MCE Error',
            'expected_results': 'No MCE Error Captured'},
        4: {'step_details': 'Boot the SUT',
            'expected_results': 'SUT booted Successfully'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PcieEndPointLtssmTestingGen4Linux object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieEndPointLtssmTestingGen4Linux, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._sut_path = self._pcie_ltssm_provider.install_ltssm_tool()
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self.LTSSM_TEST_NAME_LIST = self._common_content_configuration.get_ltssm_test_list()

    def execute(self):
        """
        This method is to execute:
        1. Check Link and Width Speed.
        2. Test LTSSM Tool execution
        3. Check MCE Log in OS Log.

        :return: True or False
        """
        super(PcieEndPointLtssmTestingGen4Linux, self).execute(
            tested_link_speed=self.pxp_inventory.PCIeLinkSpeed.GEN4)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieEndPointLtssmTestingGen4Linux.main() else Framework.TEST_RESULT_FAIL)
