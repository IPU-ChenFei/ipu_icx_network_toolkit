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
from src.ras.tests.edpc.edpc_common import EdpcCommon


class VerifyEdpcEnabled(EdpcCommon):
    """
    Glasgow_id : 58298

    This test case is a functional check of the "DPC Enable" with in the reference BIOS set up.
    """

    _EDPC_BIOS_SETUP_FATAL = "edpc_enable_fatal_bios_knobs.cfg"
    _EDPC_BIOS_SETUP_NON_FATAL = "edpc_enable_non_fatal_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new  EdpcBiosSetup object.

        :param test_log: Used for debug and info messages
        :param arguments: none
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyEdpcEnabled, self).__init__(test_log, arguments, cfg_opts, self._EDPC_BIOS_SETUP_FATAL,
                                            self._EDPC_BIOS_SETUP_NON_FATAL)

    def prepare(self):
        """
        This prepare method is to set the bios knobs to default and to clear the OS logs.

        """
        self._common_content_lib.clear_all_os_error_logs()
        self._log.info("set the Bios Knobs to Default")
        self._bios.default_bios_settings()  # To set the Bios Knobs to its default mode.

    def execute(self):
        """
        This method verify if edpc is set to fatal and non fatal

        :return: True if test completed successfully, False otherwise.
        """
        return self.verify_edpc_enabled()


if __name__ == '__main__':
    sys.exit(Framework.TEST_RESULT_PASS if VerifyEdpcEnabled.main() else Framework.TEST_RESULT_FAIL)
