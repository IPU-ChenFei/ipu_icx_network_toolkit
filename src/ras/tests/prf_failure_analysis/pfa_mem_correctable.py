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
from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.ras.tests.prf_failure_analysis.predictive_failure_common import PredictiveFailureAnalysisBaseTest


class PfaMemoryCorrectedError(PredictiveFailureAnalysisBaseTest):
    """
    Glasgow_id : 58304
    This test injects a memory corrected error to trigger page error threshold and check for Offlining page in mcelog
    """

    BIOS_CONFIG_FILE = {
        ProductFamilies.CLX: "neoncity_predictive_failure_bios.cfg",
        ProductFamilies.SKX: "neoncity_predictive_failure_bios.cfg",
        ProductFamilies.ICX: "xnm_predictive_failure_bios.cfg",
        ProductFamilies.SNR: "xnm_predictive_failure_bios.cfg"
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PfaMemoryCorrectedError object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PfaMemoryCorrectedError, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

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
        super(PfaMemoryCorrectedError, self).prepare()

    def execute(self):
        """
        This Method is used to checks if einj has been initialized,
        executes the test, then checks if the error was successfully injected and off-line page was triggered

        :return: True or False based on self.inject_correctable_error()
        """
        return self.inject_correctable_error()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PfaMemoryCorrectedError.main() else Framework.TEST_RESULT_FAIL)
