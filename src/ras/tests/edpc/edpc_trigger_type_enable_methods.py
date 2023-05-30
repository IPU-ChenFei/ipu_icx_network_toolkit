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
from src.ras.tests.edpc.edpc_common import EdpcCommon


class EdpcTriggerTypeEnableMethods(EdpcCommon):
    """
    Glasgow_id : 58966
    Test objective is to set up the DPC Trigger Enable types and verify that the trigger types have been set up.
    C-scripts are used to set and verify the DPC Trigger Enable

    There are two DPC Trigger Enable types
    1 -> DPC enabled DP detects uncorrerror or receives ERR_FATAL |
    2 -> DPC enabled DP detects uncorrerror or receives ERR_NONFATAL or ERR_FATAL
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new EdpcTriggerTypeEnableMethods object

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(EdpcTriggerTypeEnableMethods, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.

        :return: None
        """
        self._common_content_lib.clear_all_os_error_logs()  # This Method is used to Clear All OS Logs.
        self._log.info("Set the Bios Knobs to Default Settings")
        self._bios.default_bios_settings()

    def execute(self):
        """
        This Method is Used to Verify if DPC is Disabled Initially and set up the dpcte Values and verify if they set
         accordingly.

        :return: True
        """
        self.verify_dpc_is_disabled()
        self.dpc_trigger_enable_type_error_uncorrerr(err_type=self.ERROR_SEVERITY_FATAL)
        self.dpc_trigger_enable_type_error_uncorrerr(err_type=self.ERROR_SEVERITY_NONFATAL)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if EdpcTriggerTypeEnableMethods.main() else Framework.TEST_RESULT_FAIL)
