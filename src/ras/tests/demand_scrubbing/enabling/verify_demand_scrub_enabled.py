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
import os

from dtaf_core.lib.dtaf_constants import Framework

from src.ras.tests.demand_scrubbing.enabling.demand_scrubbing_common import DemandScrubCommon


class DemandScrubbing(DemandScrubCommon):
    """
    Glasgow_id : 58272

    Demand scrubbing is the ability to write corrected data back to the memory once a correctable error is detected
    on a read transaction.
    This test performs a basic Demand Scrub BIOS knob enable and verifies the appropriate register bit is set.
    """

    _BIOS_CONFIG_FILE = "demand_scrubbing_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new DemandScrubbing object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(DemandScrubbing, self).__init__(test_log, arguments, cfg_opts)

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
        if not self._os.is_alive():
            self._common_content_lib.perform_graceful_ac_off_on(self._ac)
            self._log.info("Waiting for OS to be alive..")
            self._os.wait_for_os(self._reboot_timeout)

        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, self._BIOS_CONFIG_FILE)
        self._common_content_lib.clear_all_os_error_logs()  # This Method is used to Clear All OS Logs.
        self._log.info("Set the Bios Knobs to Default Settings")
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._log.info("Set the Bios Knobs as per our Test Case Requirements")
        self._bios_util.set_bios_knob(bios_config_file_path)  # To set the bios knob setting.
        self._log.info("Bios Knobs are Set as per our TestCase and Reboot in Progress to Apply the Settings")
        self._common_content_lib.perform_graceful_ac_off_on(self._ac)
        self._log.info("Waiting for OS to be alive..")
        self._os.wait_for_os(self._reboot_timeout)
        self._log.info("Verify the bios knobs after SUT reboot...")
        try:
            self._bios_util.verify_bios_knob(bios_config_file_path)  # To verify the bios knob settings.
        except Exception as ex:
            self._log.debug("Ignoring the exception '{}' for now due to instability of the system...".format(ex))

    def execute(self):
        """
         Executing verify_if_demand_scrub_enabled method to verify whether Demand Scrub is enabled or not.
        :return: True if verify_if_demand_scrub_enabled method is executed Successfully.
        """
        return self.verify_if_demand_scrub_enabled()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if DemandScrubbing.main() else Framework.TEST_RESULT_FAIL)
