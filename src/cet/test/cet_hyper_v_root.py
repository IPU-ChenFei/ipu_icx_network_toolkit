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
from src.cet.lib.cet_common_lib import CETCommon
from src.lib.content_base_test_case import ContentBaseTestCase



class CetHyperVRoot(ContentBaseTestCase):
    """
           Phoenix_ID  :

           This test is to test CETQuickTest and CETTest on Hyper-V enabled Root.

           """
    EXEC_FILE = "CetTest.exe"
    MITIGATION_OPTION = "1"
    MIT_AUDIT_OPT = "2"

    def __init__(self, test_log, arguments, cfg_opts):
        super(CetHyperVRoot, self).__init__(test_log, arguments, cfg_opts)
        self._cet_common_obj = CETCommon(test_log, arguments, cfg_opts, bios_config_file=None)

    def prepare(self):
        # type: () -> None
        """
        prepare the system to test cet test and cet quick test
        Enable CET by changing CET bits on Regisrty Editor.
        Make sure Hyper-V is enabled manually

        """
        self._cet_common_obj.set_cet_per_program(self.EXEC_FILE, self.MITIGATION_OPTION, self.MIT_AUDIT_OPT)

    def execute(self):
        """
        This function is to perform CET test and CETquick test on root

        """
        return self._cet_common_obj.cet_quick_test() and self._cet_common_obj.cet_test("")

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CetHyperVRoot.main() else Framework.TEST_RESULT_FAIL)
