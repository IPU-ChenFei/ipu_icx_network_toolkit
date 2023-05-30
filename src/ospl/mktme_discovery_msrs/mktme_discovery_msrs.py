#!/usr/bin/env python
##########################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and
# proprietary and confidential information of Intel Corporation and its
# suppliers and licensors, and is protected by worldwide copyright and trade
# secret laws and treaty provisions. No part of the Material may be used,copied,
# reproduced, modified, published, uploaded, posted, transmitted, distributed,
# or disclosed in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################

import os
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions
from src.security.tests.mktme.mktme_common import MktmeBaseTest


class MktmeDiscoveryMsrs(MktmeBaseTest):
    """
    Glasgow_Id = "G59514.2 -MKTME Discovery (in-band)_MSRs"
    This Test case is enabling TME and MKTME BIOS Knobs and verify msr values
    """
    BIOS_CONFIG_FILE = "../security_tme_mktme_bios_enable.cfg"
    TEST_CASE_ID = ["G59514.2", "MKTME Discovery (in-band)_MSRs"]

    STEP_DATA_DICT = {1: {'step_details': 'Verify if CPU SKU Supports MKTME',
                          'expected_results': 'CPU SKU Supports MKTME'},
                      2: {'step_details': 'Enable TME and MKTME Bios Knobs',
                          'expected_results': 'Verify TME and MKTME Bios '
                                              'Knobs are set'},
                      3: {'step_details': 'Checking Msr values of TME and MkTme',
                          'expected_results': 'Verify TME and MkTme Msr Values '
                                              'are same as Expected'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of MktmeDiscoveryMsrs

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.tme_mktme_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(MktmeDiscoveryMsrs, self).__init__(test_log, arguments, cfg_opts,
                                                 self.tme_mktme_bios_enable)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """
        This Method is Used to Verify CPU Sku Supports MKTME and Enable TME and MK-TME Bios knobs.

        :raise TestSetupError if Cpu Sku Doesn't Support MKTME.
        """
        self._test_content_logger.start_step_logger(1)
        # Verify platform will support MKTME or not
        if not self.verify_mktme():
            raise content_exceptions.TestSetupError("This CPU SKU does not support for MK-TME")
        self._log.info("SUT supports MK-TME Bios Knob")
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        super(MktmeDiscoveryMsrs, self).prepare()
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._common_content_lib.update_micro_code()

    def execute(self):
        """
        check the TME and MK-TME MSR Values.

        :return True if Msr Values are as Expected else false
        """
        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        # Check the msr to verify the TME Enable bit is set
        self.msr_read_and_verify(self.MSR_TME_CAPABILITY_ADDRESS, self.MSR_TME_CAPABILITY_VALUE)
        self.msr_read_and_verify(self.MSR_TME_ADDRESS, self.MSR_MKTME_VAL)
        self.msr_read_and_verify(self.MSR_TME_EXCLUDE_MASK_ADDRESS, self.MSR_TME_EXCLUDE_MASK_VALUE)
        self.msr_read_and_verify(self.MSR_TME_EXCLUDE_BASE_ADDRESS, self.MSR_TME_EXCLUDE_BASE_VALUE)
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MktmeDiscoveryMsrs.main() else Framework.TEST_RESULT_FAIL)
