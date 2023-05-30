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
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory

from src.ras.tests.pcie.keysight_card.keysight_card_common import KeysightPcieErrorInjectorCommon
from src.ras.lib.ras_common_utils import RasCommonUtil
from src.lib import content_exceptions


class PcieHwSurpriseLinkDown(KeysightPcieErrorInjectorCommon):
    """
    Glasgow_id : 43878

    The objective of this test is to check the response of Surprise Link Down error.
    """

    BIOS_CONFIG_FILE = "pcie_hw_surprise_link_down_bios_knobs.cfg"
    DELAY_TIME_IN_SEC = 40

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PcieHwSurpriseLinkDown object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieHwSurpriseLinkDown, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._ras_common_util_obj = RasCommonUtil(self._log, self.os, cfg_opts, self._common_content_configuration)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.

        :return: None
        """
        super(PcieHwSurpriseLinkDown, self).prepare()
        pass

    def execute(self):
        """
        1. Create Keysight provider obj.
        2. Inject Surprise Link Down Error.
        3. Verify Error signature in OS Log.

        :return: True
        """
        #  Create Keysight provider object
        key_sight_provider = self.create_keysight_provider_object()

        #  Inject SLD Error
        key_sight_provider.surprise_link_down()

        #  Wait for some time to after error injection.
        time.sleep(self.DELAY_TIME_IN_SEC)

        if self.os.is_alive():
            raise content_exceptions.TestFail("System did not get Hung after Surprise Link down")

        self._ras_common_util_obj.ac_cycle_if_os_not_alive(self.ac_power, auto_reboot_expected=True)

        self.os.wait_for_os(self.reboot_timeout)

        # Verify OS Log.
        os_error_found = self._os_log_ver_obj.verify_os_log_error_messages(__file__,
                                                                           self._os_log_ver_obj.DUT_MESSAGES_FILE_NAME,
                                                                           self.SURPRISE_LINK_DOWN_ERR_SIG)
        if not os_error_found:
            raise content_exceptions.TestFail("Error Signature was not Captured in OS Log")
        self._log.info("Error Signature was captured in OS Log as Expected")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieHwSurpriseLinkDown.main() else Framework.TEST_RESULT_FAIL)
