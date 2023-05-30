#!/usr/bin/env python
##########################################################################
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
##########################################################################
"""
    :TDX Max Keys Check:

    Verify TDX max keys are displayed in BIOS.
"""
import sys

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.private.cl_utils.adapter import data_types
from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest


class TdxMaxKey(LinuxTdxBaseTest):
    """
            This recipe tests the maximum number of keys available for TDX.

            :Scenario: With TDX enabled, verify that max keys can be split between MKTME and TDX.

            :Prerequisite:  SUT must be configured with the latest BKC applicable for the platform.

            :Phoenix ID: 18014073129

            :Test steps:

                :1: Boot to BIOS menu.

                :2: Verify the max keys available match expected max keys available for platform.

            :Expected results: Max keys for program should match.

            :Reported and fixed bugs:

            :Test functions:

        """

    def execute(self):
        self._log.debug("Booting to BIOS menu.")
        # knob check
        self.boot_to_tdx_knob()

        self.serial_bios_util.select_knob(self.tdx_consts.MAX_KEYS_LABEL, data_types.BIOS_UI_OPT_TYPE)
        page_values = self.serial_bios_util.get_page_information()
        keys = 0
        for value in page_values:
            if value[0] == self.tdx_consts.MAX_KEYS_LABEL:
                keys = int(value[1])
                break
        msr_keys = self.get_keys()
        if keys == self.tdx_consts.MAX_KEYS and msr_keys == self.tdx_consts.MAX_KEYS:
            self._log.info("Max keys match expected values from BIOS and MSRs. Max: {}, MSR: {}, BIOS: {}".format(
                self.tdx_consts.MAX_KEYS, msr_keys, keys))
            return True
        else:
            self._log.info("Max keys do not match expected values from BIOS and MSRs. Max: {}, MSR: {}, BIOS: {}".format(
                self.tdx_consts.MAX_KEYS, msr_keys, keys))
            return False


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxMaxKey.main() else Framework.TEST_RESULT_FAIL)
