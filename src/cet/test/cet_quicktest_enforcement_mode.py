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


class CetEnforcementMode(ContentBaseTestCase):
    """
        Phoenix_ID  :

        This test is to verify shadowstack enforcement mode works as expected and returns the expected outcome.

        """

    def __init__(self, test_log, arguments, cfg_opts):
        super(CetEnforcementMode, self).__init__(test_log, arguments, cfg_opts)
        self._cet_common_obj = CETCommon(test_log, arguments, cfg_opts, bios_config_file=None)

    def prepare(self):
        # type: () -> None
        """This function prepares for shadowstack test
        1. clear event logs to capture the Error caused by shadowstack.exe
        2. Enable shadawstack enforecement mode"""
        self._cet_common_obj.clear_event_log()
        self._cet_common_obj.set_cet_enforcement_mode()

    def execute(self):
        """This function tests the shadowstack
        1. Verify RET_SS and RET_DS values match and non zero
        2. Verify ERROR 1000 is seen in event viewer"""
        reg_values = self._cet_common_obj.verify_Shadowstack_values(self.run_cet_quicktest())

        if self._cet_common_obj.check_shadowstack_event_log("") == 1000:
            validErrorId = True

        return validErrorId and reg_values


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CetEnforcementMode.main() else Framework.TEST_RESULT_FAIL)
