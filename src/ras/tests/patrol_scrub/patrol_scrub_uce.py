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

from src.ras.tests.patrol_scrub.patrol_scrub_common import PatrolScrubCommon


class PatrolScrubUCE(PatrolScrubCommon):
    """
    Glasgow_id : 58330
    Patrol Scrub

    Patrol scrubbing is accomplished using an engine that generates requests to memory addresses in a stride.

    Patrol scrubs are intended to ensure that data with a correctable error does not remain in DRAM long enough to
    stand a significant chance of further corruption to an uncorrectable error due to high energy particle error.

    This test case injects Memory UnCorrected Error then Verifies detection using Patrol Scrub.

    Test cas flow:

    -Check if sockets are detected
    -Inject Memory UnCorrected Error and Verifying error detection using Patrol Scrub
    -Obtain OS error logs for the test

    """
    _BIOS_CONFIG_FILE = "patrol_scrub_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PatrolScrubUCE object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PatrolScrubUCE, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Copy mcelog confg to SUT.
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        self._install_collateral.copy_mcelog_conf_to_sut()
        self._common_content_lib.clear_all_os_error_logs()  # This Method is used to Clear All OS Logs.
        self._ras_common.set_and_verify_bios_knobs()

    def execute(self):
        """
        This Method is used to execute the patrol scrub uncorrectable error using einj utils.

        :return: True or False based on Error Logged
        """

        return self.test_patrol_scrub(corrected_error=False)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PatrolScrubUCE.main() else Framework.TEST_RESULT_FAIL)
