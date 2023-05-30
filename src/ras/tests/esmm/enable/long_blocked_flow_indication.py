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
from dtaf_core.providers.provider_factory import ProviderFactory

from src.ras.lib.esmm_util import EsmmSaveUtil
from src.ras.tests.esmm.esmm_common import EsmmSaveCommon


class LongBlockedFlowIndication(EsmmSaveCommon):
    """
    Glasgow_id : G58334-_74_01_01_long_blocked_flow_indication_enabled

    This test verifies that Long and Blocked Flow Indication is enabled.

    Thread in Long Flow/Blocked indicators: SMMs are used to handle errors by firmware.
    This indicator is used to reduce the SMM rendezvous loop time.
    """
    TEST_CASE_ID = ["G58334", "_74_01_01_long_blocked_flow_indication_enabled"]
    BIOS_CONFIG_FILE = "esmm_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new LongBlockedFlowIndication object

        :param test_log: Used for debug and info messages.
        :param arguments: arguments for base class.
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(LongBlockedFlowIndication, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.

        :return: None
        """
        super(LongBlockedFlowIndication, self).prepare()  # call Base class prepare which is common to TC: 58334,
        # 58335, 58336.

    def execute(self):
        """
        This Method is Used to Execute is_long_and_blocked_flow_indication_enabled method and check whether long and
        blocked flow indication is Enabled

        :return: True or False
        """
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj, \
                ProviderFactory.create(self.si_dbg_cfg, self._log) as sdp_obj:
            esmm_utils_obj = EsmmSaveUtil(self._log, sdp_obj, cscripts_obj)
            return esmm_utils_obj.is_long_and_blocked_flow_indication_enabled()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LongBlockedFlowIndication.main() else Framework.TEST_RESULT_FAIL)
