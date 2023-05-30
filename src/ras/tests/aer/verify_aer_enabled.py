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
from src.ras.tests.aer.aer_common import AerBaseTest
from src.ras.lib.ras_aer_util import AerUtil
from dtaf_core.lib.dtaf_constants import ProductFamilies


class VerifyAerEnabled(AerBaseTest):
    """
        Glasgow_id : 58288
        This test checks that the Advanced Error Reporting (AER) Registers Error Masks and
        Error Severity are enabled correctly
    """
    BIOS_CONFIG_FILE = {
        ProductFamilies.ICX: "aer_enable_bios_knob.cfg"
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VerifyAerEnabled object

        :param test_log: Used for debug and info messages
        :param arguments: Arguments used in Baseclass
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyAerEnabled, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Setting the bios knobs to its default mode.
        3. Setting the bios knobs as per the test case.
        4. Rebooting the SUT to apply the new bios settings.
        5. Verifying the bios knobs that are set.

        :return: None
        """
        super(VerifyAerEnabled, self).prepare()

    def execute(self):
        """
        This Method is used to execute the method is_Aer_enabled to verify if Aer is enabled or not
        :return: Aer enable status(True/False)
        """
        aer_utils_obj = AerUtil(self._log, self._cscripts, self._sdp)
        return aer_utils_obj.is_aer_enabled()

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyAerEnabled.main() else Framework.TEST_RESULT_FAIL)
