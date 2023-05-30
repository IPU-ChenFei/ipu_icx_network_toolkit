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
from src.ras.tests.poison_flow.memory_poison_common import PoisonCommon


class MemoryPoisonEnable(PoisonCommon):
    """
    Glasgow_id : 58273
    This test verifies if Memory Poison is enabled.
    """
    BIOS_CONFIG_FILE = {
        ProductFamilies.CLX: "neoncity_memory_poison_bios_knobs.cfg",
        ProductFamilies.SKX: "neoncity_memory_poison_bios_knobs.cfg",
        ProductFamilies.ICX: "wilsoncity_memory_poison_bios_knobs.cfg",
        ProductFamilies.SNR: "wilsoncity_memory_poison_bios_knobs.cfg"
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new MemoryPoisonEnable object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(MemoryPoisonEnable, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.

        :return: None
        """
        super(MemoryPoisonEnable, self).prepare()

    def execute(self):
        """
        Call the function is_memory_poison_enable() and verify whether memory poison is enable or not.

        :return: memory poison enable status
        """

        return self.is_memory_poison_enable()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MemoryPoisonEnable.main() else Framework.TEST_RESULT_FAIL)
