#!/usr/bin/env python
##########################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and proprietary
# and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions0. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################

import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.security.tests.mktme.mktme_common import MktmeBaseTest


class MktmeDiscoveryTmeEnumeration(MktmeBaseTest):
    """
    Glasgow ID : G58194, G59474
    Phoenix ID : P18014070409
    This Test case executes ITP commands to verify if the SUT's CPU SKU supports MKTME.
    """
    TEST_CASE_ID = ["G58194.4- MKTME Discovery (in-band)_TmeEnumeration",
                    "G59474.0- MKTME Discovery (in-band)_TmeEnumeration",
                    "P18014070409 - Verify the proper TME/MKTME enumeration scheme"]
    step_data_dict = {
        1: {'step_details': 'Run ITP commands '
            'first command (itp.threads[0].cpuid_edx(0x7) & (1 << 18)) != 0  '
            'second command itp.threads[0].cpuid_eax(0x1b) == 1 '
            'third command  (itp.threads[0].cpuid_ecx(0x7) & (1 << 13)) != 0 ',
            'expected_results': 'first ,second and third command should return True'},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of MktmeDiscoveryTmeEnumeration

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(MktmeDiscoveryTmeEnumeration, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        pre-checks if the sut is alive or not.
        """
        super(MktmeDiscoveryTmeEnumeration, self).prepare()

    def execute(self):
        """
        This function is used to verify ITP commands

        :return: True if SUT's CPU SKU supports MKTME.
        """
        self._test_content_logger.start_step_logger(1)
        ret_value = self.verify_mktme()
        if ret_value:
            self._log.info("SUT's CPU SKU supports MKTME.")
        else:
            self._log.error("SUT's CPU SKU does not supports MKTME.")

        self._test_content_logger.end_step_logger(1, ret_value)
        return ret_value

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MktmeDiscoveryTmeEnumeration.main() else Framework.TEST_RESULT_FAIL)

