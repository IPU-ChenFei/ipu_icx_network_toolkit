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


class LmceRecovery(LmceCommon):
    """
    Glasgow ID: G58333-_76_02_02

    This test LMCE allows the capability to deliver the SRAR-type of UCR event to only affected logical processor
    receiving the corrupted data (poison).
    This feature is supported as part of advanced RAS feature and offered in only shelf4 and shelf3 based processor SKUs
    """
    TEST_CASE_ID = ["G58333", "_76_02_02"]
    _BIOS_CONFIG_FILE = "lmce_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new LmceRecovery object

        :param test_log: Used for debug and info messages
        :param arguments: Used in based class.
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(LmceRecovery, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Setting the bios knobs to its default mode.
        3. Setting the bios knobs as per the test case.
        4. Rebooting the SUT to apply the new bios settings.
        5. Verifying the bios knobs that are set.
        :return: None
        """
        super(LmceRecovery, self).prepare()

    def execute(self):
        """
        This Method is used to execute the method verifying_whether_lmce_is_enabled to verify if lmce is successfully
        enabled or not.
        execute the execute_lmce function to inject and verify the Lmce Error Recovery

        :return: True if Test Case pass else return False.
        """
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        lmce_obj = LmceUtil(self.os, self._log, sdp_obj, cscripts_obj, self._common_content_lib,
                            self._common_content_configuration)
        test_status = False
        try:

            result = lmce_obj.verify_lmce_is_enabled()

            if not result:
                self._log.info("Lmce is Not Enabled")
                return test_status

            self._log.info("Verify Lmce error recovery...")
            is_lmce_rec = lmce_obj.execute_lmce(self.ac_power)
            if not is_lmce_rec:
                self._log.error("FAIL: Lmce error recovery \n")
            else:
                test_status = True
                self._log.info("PASS: Lmce error recovery\n")

        except Exception as ex:
            log_error = "An exception occurred:\n{}".format(str(ex))
            self._log.error(log_error)
            raise ex

        return test_status


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LmceRecovery.main() else Framework.TEST_RESULT_FAIL)
