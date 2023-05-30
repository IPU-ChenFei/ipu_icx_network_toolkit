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


import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.ras.tests.ieh_global.functional.ieh_register_status_common import \
    IehCommon


class IehGlobalErrorTimerValidity(IehCommon):
    """
    Glasgow ID: 58519

    This test ascertains the Global Error Timer indicates a valid reading out of PWRGOOD reset.
    """
    _BIOS_CONFIG_FILE = "ieh_global_error_timer_validity_bios_configuration.cfg"
    TEST_CASE_ID = ["G58519", "_29_02_07_ieh_global_error_timer_validity"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new IehGlobalErrorTimerValidity object,

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param arguments: None
        """
        super(IehGlobalErrorTimerValidity, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.

        :return: None
        """
        super(IehGlobalErrorTimerValidity, self).prepare()

    def execute(self):
        """
        Calling Function get_global_error_timer_status() to check the valid reading out of PWRGOOD reset.

        :return: True if valid else False
        """
        return self.check_ieh_global_time_register_value_status()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if IehGlobalErrorTimerValidity.main()
             else Framework.TEST_RESULT_FAIL)
