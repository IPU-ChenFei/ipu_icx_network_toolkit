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
from src.ras.lib.lmce_util import LmceUtil

from src.ras.tests.lmce.lmce_common import LmceCommon


class LmceEnabling(LmceCommon):
    """
        Glasgow_id : G58331-lmce_enabling
        LMCE allows the capability to deliver the SRAR-type of UCR event to only affected logical processor
        receiving the corrupted data (poison). This feature is supported as part of advanced RAS feature
        and offered in only shelf4 and shelf3 based processor SKUs.
        Check the following register bits to see if LMCE is set correctly
                msr 0x3a  bit20 is set
                msr 0x4d0  bit0 is set
                msr 0x179  bit27 is set
    """
    TEST_CASE_ID = ["G58331", "lmce_enabling"]
    _BIOS_CONFIG_FILE = "lmce_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new LmceEnabling object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(LmceEnabling, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the Bios knobs are Updated Properly.
        :return: None
        """
        super(LmceEnabling, self).prepare()

    def execute(self):
        """
        This Method is used to execute the method verifying_whether_lmce_is_enabled to verify if lmce is successfully
        enabled or not.

        :return:
        """
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        lmce_obj = LmceUtil(self.os, self._log, sdp_obj, cscripts_obj, self._common_content_lib,
                            self._common_content_configuration)
        result = lmce_obj.verify_lmce_is_enabled()
        return result


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LmceEnabling.main() else Framework.TEST_RESULT_FAIL)
