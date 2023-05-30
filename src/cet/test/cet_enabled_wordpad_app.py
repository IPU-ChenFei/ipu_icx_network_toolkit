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
from src.lib.content_base_test_case import ContentBaseTestCase
from src.cet.lib.cet_common_lib import CETCommon


class CetEnabledWordpad(ContentBaseTestCase):
    WP_PROGRAM = "wordpad.exe"
    WP_MIT_OPT_BIT = "3"
    WP_MIT_AUDIT_OPT_BIT = "0"

    def __init__(self, test_log, arguments, cfg_opts):
        super(CetEnabledWordpad, self).__init__(test_log, arguments, cfg_opts)

        self._cet_common_obj = CETCommon(test_log, arguments, cfg_opts, bios_config_file=None)

    def prepare(self):
        # type: () -> None
        """
        1. Change registry values to enable CET for wordpad.exe app
        """
        self._cet_common_obj.set_cet_per_program(self.WP_PROGRAM, self.WP_MIT_OPT_BIT, self.WP_MIT_AUDIT_OPT_BIT)

    def execute(self):
        """This test is to verify wordpad.exe works as expected while CET is enabled

        1. open wordpad.exe and write text content
        2. perform copy, paste and cut
        3. check if wordpad is still not crashed
        """
        return self._cet_common_obj.test_wordpad_cet_enabled()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CetEnabledWordpad.main() else Framework.TEST_RESULT_FAIL)
