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


class EsmmSaveState(EsmmSaveCommon):
    """
    Glasgow_id : G58335-_74_01_02_esmm_save_state_enabled

    This test verifies that esmm Save State is enabled.
    """
    TEST_CASE_ID = ["G58335", "_74_01_02_esmm_save_state_enabled"]
    BIOS_CONFIG_FILE = "esmm_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new EsmmSaveState object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(EsmmSaveState, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        super(EsmmSaveState, self).prepare()

    def execute(self):
        """
        This Method is Used to Execute is_esmm_save_state_enable method and check whether Esmm Save State is Enabled

        :return: True or False
        """
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj, \
                ProviderFactory.create(self.si_dbg_cfg, self._log) as sdp_obj:
            esmm_utils_obj = EsmmSaveUtil(self._log, sdp_obj, cscripts_obj)
            return esmm_utils_obj.is_esmm_save_state_enable()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if EsmmSaveState.main() else Framework.TEST_RESULT_FAIL)
