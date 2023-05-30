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
# from src.ras.lib.mem_mirroring_util import MemMirroringUtil
from src.ras.tests.mem_mirroring.mem_mirroring_common import MemMirroringBaseTest


class VerifyMemMirroringEnabled(MemMirroringBaseTest):
    """
        Glasgow_id : 58313
        Memory Mirroring is a method of keeping a duplicate (secondary or mirrored) copy of the contents of memory as
        a redundant backup for use if the primary memory fails. The mirrored copy of the memory is stored in memory of
        the same processor socket. Dynamic (without reboot) fail-over to the mirrored DIMMs is transparent to the OS
        and applications.

        Primary usage model for this feature is to provide more reliable memory. Such memory space will be fault
        tolerant in case of single bit, multi-bit, single device, multi-device faults.
    """
    BIOS_CONFIG_FILE = "verify_mem_mirroring_enabled_bios_knob.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new MirrorEnabling object

        :param test_log: Used for debug and info messages
        :param arguments: Arguments used in Baseclass
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyMemMirroringEnabled, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

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
        super(VerifyMemMirroringEnabled, self).prepare()

    def execute(self):
        """
        This Method is used to execute the method is_mem_mirroring_enabled to verify if mem mirroring is enabled or not
        :return: mem mirroring enable status(True/False)
        """
        return self.is_mem_mirroring_enabled()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyMemMirroringEnabled.main() else Framework.TEST_RESULT_FAIL)
