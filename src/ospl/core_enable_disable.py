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
from src.ras.tests.core_enable_disable.core_enable_disable_common import CoreEnableDisableBase


class CoreEnableDisable(CoreEnableDisableBase):
    """
    Glasgow_id : 59496, H81521
    Checks current core count, disables 4 cores via bios, and verifies that after bios updates, it has expected core
    count, Cleanup will recover disabled cores
    Test case flow:
    -get the initial core count , disable 4 cores , get the current core count , verify the count difference and enable
     all cores back to default state.
    """

    TEST_CASE_ID = ["H81521-PI_RAS_CPU_CORE_ENABLE_DISABLE"]
    _CORE_DISABLE_BIOS_CONFIG_FILE = "core_disable_bios_knobs.cfg"
    _CORE_ENABLE_BIOS_CONFIG_FILE = "core_enable_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new  CoreEnableDisable object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(CoreEnableDisable, self).__init__(test_log, arguments, cfg_opts, self._CORE_ENABLE_BIOS_CONFIG_FILE,
                                                self._CORE_DISABLE_BIOS_CONFIG_FILE)

    def prepare(self):
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """
        super(CoreEnableDisable, self).prepare()
        self._common_content_lib.update_micro_code()

    def execute(self):
        """
        Execute Main test case.

        :return: True if test completed successfully, False otherwise.
        """
        status = self.verify_core_enable_disable()
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        return status


# Execute this test with TestEngine when run as main.
if __name__ == '__main__':
    test_result = CoreEnableDisable.main()
    sys.exit(Framework.TEST_RESULT_PASS if test_result else Framework.TEST_RESULT_FAIL)
