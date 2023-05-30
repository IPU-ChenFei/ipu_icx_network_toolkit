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
import argparse
import logging
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.tdx_common_windows import WindowsTdxBaseTest


class TDXPartialMemoryMirroringWindows(WindowsTdxBaseTest):
    """
            This recipe tests compatibility with partial memory mirroring feature and is compatible with most OSes.
            The SUT must be populated with at least one memory channel pair that supports a mirror configuration.

            :Scenario: Enable partial memory mirroring BIOS knob with TDX enabled.

            :Phoenix ID: 22014296920

            :Test steps:

                :1: Boot to BIOS menu.

                :2: Enable TDX knobs.  Refer to Glasgow ID 69627 for steps.

                :3: Enable Partial Memory Mirroring BIOS knobs (see BIOS knobs file
                src/ras/tests/mem_mirroring/partial_mirroring_bios_knobs.cfg).

                :4: Reboot system and verify TDX and partial memory mirroring is enabled.

            :Expected results: TDX verification passes with partial memory knobs enabled.

            :Reported and fixed bugs:

            :Test functions:

        """
    def __init__(self, test_log: logging.Logger, arguments: argparse.Namespace, cfg_opts: ElementTree) -> None:
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(TDXPartialMemoryMirroringWindows, self).__init__(test_log, arguments, cfg_opts)
        self._PARTIAL_MIRROR_KNOB = "../../../collateral/partial_memory_mirroring_knobs.cfg"

    def execute(self):
        self._log.info("Setting Memory mode into 'Partial Mirror Mode'")
        bios_knob_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._PARTIAL_MIRROR_KNOB)
        self.set_knobs(bios_knob_file)

        self._log.info("Verifying TDX settings.")
        # check TDX is enabled and validated
        return self.validate_tdx_setup() and self.check_knobs(bios_knob_file, set_on_fail=False)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDXPartialMemoryMirroringWindows.main() else Framework.TEST_RESULT_FAIL)
