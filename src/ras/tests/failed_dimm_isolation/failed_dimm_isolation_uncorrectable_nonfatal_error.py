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


class FailedDimmIsolationUnCorrNonFatalError(FailedDimmIsolationBaseTest):
    """
    Glasgow_id : 61158
    Test verifies failed DIMM isolation info is reported to the OS upon uncorrectable nonfatal memory error injection
    """
    _BIOS_CONFIG_FILE = "failed_dimm_isolation_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new FailedDimmIsolationUnCorrNonFatalError object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(FailedDimmIsolationUnCorrNonFatalError, self).__init__(test_log, arguments, cfg_opts,
                                                                     self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.

        :return: None
        """
        super(FailedDimmIsolationUnCorrNonFatalError, self).prepare()

    def execute(self):
        """
        executing inject_uncorrectable_non_fatal_error method to verify if failed DIMM isolation info is reported to
        the OS upon uncorrectable nonfatal memory error injection.

        :return: True if inject_uncorrectable_non_fatal_error method is executed Successfully.
        """
        return self._einj_error.einj_inject_and_check(self._einj_error.EINJ_MEM_UNCORRECTABLE_NONFATAL,
                                                      failed_dimm_isolation_check=True)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if FailedDimmIsolationUnCorrNonFatalError.main() else
             Framework.TEST_RESULT_FAIL)
