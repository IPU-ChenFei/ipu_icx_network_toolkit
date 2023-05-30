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
from src.security.tests.ptt.ptt_common import PttBaseTest


class EnablePTT(PttBaseTest):
    """
    Glasgow ID : 58986
    This Test case is to enable PTT knob in BIOS and verify the knobs are set properly
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of EnableTxt
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(EnablePTT, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        Pre validate the SUT should be alive.

        :return: None
        """
        if not self._os.is_alive():
            self._log.error("System is not alive")
            raise RuntimeError("OS is not alive")

    def execute(self):
        """
        This function is to verify the BIOS knobs are set properly

        :return: True/False if everything works fine
        """
        return self.enable_verify_ptt()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if EnablePTT.main() else Framework.TEST_RESULT_FAIL)
