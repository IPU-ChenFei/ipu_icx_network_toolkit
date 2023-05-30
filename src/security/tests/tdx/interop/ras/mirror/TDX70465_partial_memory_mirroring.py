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
    :Partial Memory Mirroring:

    Verify TDX enabled with partial memory mirroring.
"""
import sys
import os

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest
from src.lib import content_exceptions


class TDXPartialMemoryMirroring(LinuxTdxBaseTest):
    """
            This recipe tests compatibility with partial memory mirroring feature and is compatible with most OSes.
            The SUT must be populated with at least one memory channel pair that supports a mirror configuration.

            :Scenario: Enable partial memory mirroring BIOS knob with TDX enabled.

            :Phoenix ID: 18014073804

            :Test steps:

                :1: Boot to BIOS menu.

                :2: Enable TDX knobs.  Refer to Glasgow ID 69627 for steps.

                :3: Enable Partial Memory Mirroring BIOS knobs (see BIOS knobs file
                src/ras/tests/mem_mirroring/partial_mirroring_bios_knobs.cfg).

                :4: Reboot system and verify TDX and partial memory mirroring is enabled.

            :Expected results: TDX verification passes with partial memory knobs enabled.

            :Reported and fixed bugs:
            2022WW26:  Partial mirroring and SGX are no longer POR for SPR:
            https://hsdes.intel.com/appstore/article/#/15011250485

            :Test functions:

        """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of sut os provider, XmlcliBios provider, BIOS util and Config util
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        """
        super(TDXPartialMemoryMirroring, self).__init__(test_log, arguments, cfg_opts)
        self._PARTIAL_MIRROR_KNOB = "../../../collateral/partial_memory_mirroring_knobs.cfg"

    def prepare(self):
        if not self.one_dpc_config_check() and not self.two_dpc_config_check():
            raise content_exceptions.TestSetupError("Dimm configuration on SUT does not support partial memory "
                                                    "mirroring.")
        super(TDXPartialMemoryMirroring, self).prepare()

    def execute(self):
        bios_knob_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._PARTIAL_MIRROR_KNOB)
        self.set_knobs(bios_knob_file)

        # check TDX is disabled and validated
        knob_check = self.check_tdx_knobs(tdx_enabled=False)
        key_check = self.get_keys("tdx") == 0

        return knob_check and key_check and self.check_knobs(bios_knob_file, set_on_fail=False)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDXPartialMemoryMirroring.main() else Framework.TEST_RESULT_FAIL)
