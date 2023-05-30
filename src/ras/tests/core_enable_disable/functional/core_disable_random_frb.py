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


class CoreDisableRandomFrb(CoreEnableDisableBase):
    """
    Glasgow_id : 58511
    Checks current core count, disables random cores via bios, and verifies that after bios updates, has expected
    core count
    """
    _CORE_ENABLE_BIOS_CONFIG_FILE = "core_enable_frb_bios_knobs.cfg"
    _CORE_DISABLE_BIOS_CONFIG_FILE = "core_disable_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new CoreDisableRandomFrb object

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(CoreDisableRandomFrb, self).__init__(test_log, arguments, cfg_opts, self._CORE_ENABLE_BIOS_CONFIG_FILE,
                                                   self._CORE_DISABLE_BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Copy mcelog.conf file to sut and reboot
        2. Clear All Os Logs before Starting the Test Case
        3. Set the bios knobs to its default mode.
        4. Set the bios knobs as per the test case.
        5. Reboot the SUT to apply the new bios settings.
        6. Verify the bios knobs whether they updated properly.

        :return: None
        """
        super(CoreDisableRandomFrb, self).prepare()

    def execute(self):
        """
        This Method is used to Execute verify_core_count_before_and_after_disabling_cores to verify the Count of Os
        Cores and Itp Core before and after disabling the Cores

        :return: True or False based on the execution of verify_core_count_before_and_after_disabling_cores
        """
        return self.verify_core_count_before_and_after_disabling_cores()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CoreDisableRandomFrb.main() else Framework.TEST_RESULT_FAIL)
