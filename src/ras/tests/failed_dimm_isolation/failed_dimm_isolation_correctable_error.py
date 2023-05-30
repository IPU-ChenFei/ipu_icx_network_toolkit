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
from src.ras.tests.failed_dimm_isolation.failed_dimm_isolation_common import FailedDimmIsolationBaseTest
from dtaf_core.lib.dtaf_constants import ProductFamilies


class FailedDimmIsolationCorrectableError(FailedDimmIsolationBaseTest):
    """
    Glasgow_id : 61157
    Test verifies failed DIMM isolation info is reported to the OS upon correctable memory error injection
    """
    # _BIOS_CONFIG_FILE = "neoncity_failed_dimm_isolation_correctable_error_bios_knobs.cfg"
    BIOS_CONFIG_FILE = {
        ProductFamilies.CLX: "neoncity_failed_dimm_isolation_correctable_error_bios_knobs.cfg",
        ProductFamilies.CPX: "neoncity_failed_dimm_isolation_correctable_error_bios_knobs.cfg",
        ProductFamilies.SKX: "neoncity_failed_dimm_isolation_correctable_error_bios_knobs.cfg",
        ProductFamilies.ICX: "wilsoncity_failed_dimm_isolation_correctable_error_bios_knobs.cfg",
        ProductFamilies.SNR: "wilsoncity_failed_dimm_isolation_correctable_error_bios_knobs.cfg"
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new FailedDimmIsolationCorrectableError object

        :param test_log: Used for debug and info messages
        :param arguments: Arguments used in Baseclass
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(FailedDimmIsolationCorrectableError, self).__init__(test_log, arguments, cfg_opts,
                                                                     self.BIOS_CONFIG_FILE)

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
        super(FailedDimmIsolationCorrectableError, self).prepare()

    def execute(self):
        """
        This Method is used to verify if Failed Dimm isolation for correctable memory error injection happened.

        :return: Boolean(True/False)
        """
        correctable_error_status = self.inject_correctable_error()
        return correctable_error_status

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if FailedDimmIsolationCorrectableError.main() else Framework.TEST_RESULT_FAIL)
