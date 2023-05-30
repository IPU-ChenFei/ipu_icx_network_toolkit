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
import time

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions
from src.security.tests.mktme.mktme_common import MktmeBaseTest


class EnableTmeMktme(MktmeBaseTest):
    """
    Glasgow ID : 59511.0-MKTME_Enable_(in-band)_Activate_MSR
    Phoenix ID : 18014071089 - Verify the contents of MKTME MSRs
    This Test case is enabling TME and MKTME BIOS Knobs and verify msr values
    """
    BIOS_CONFIG_FILE = "../security_tme_mktme_bios_enable.cfg"
    TEST_CASE_ID = ["59511.0-MKTME_Enable_(in-band)_Activate_MSR",
                    "18014071089 - Verify the contents of MKTME MSRs"]

    step_data_dict = {1: {'step_details': 'Check SUT in Linux OS and CPU '
                                          'SKU Supports MKTME',
                          'expected_results': 'SUT should be in Linux '
                                              'OS and Supports MKTME'},
                      2: {'step_details': 'Enable TME and MKME Bios Knobs',
                          'expected_results': 'Verify TME and MKTME Bios '
                                              'Knobs set'},
                      3: {'step_details': 'Checking msr value of MKTME',
                          'expected_results': 'Verify MKTME msr value '
                                              '0x100060000000B'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of EnableTmeMktme

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.tme_mktme_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(EnableTmeMktme, self).__init__(test_log, arguments, cfg_opts,
                                             self.tme_mktme_bios_enable)
        self._test_content_logger = TestContentLogger(
            test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        This function check verify platform supporting the MKTME and
        Enabling TME and MK-TME Bios knobs.

        :raise RuntimeError if there is any error while check CPU SKU
        support of MK-TME
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        # Verify platform will support MKTME or not
        if not self.verify_mktme():
            raise content_exceptions.TestNAError("This CPU SKU does not "
                                                 "support for MK-TME")
        self._log.info("SUT supports MK-TME Bios Knob....")
        time.sleep(self.WAIT_TIME_DELAY)
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        # Enabling TME and MKTME BIOS Knobs
        super(EnableTmeMktme, self).prepare()
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        check the TME and MK-TME MSR Values.

        :return True else false
        """
        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        # Check the msr to verify the TME Enable bit is set
        self.msr_read_and_verify(self.MSR_TME_ADDRESS, self.ENABLE_TME_MSR_VALUE, squash=False)
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if EnableTmeMktme.main()
             else Framework.TEST_RESULT_FAIL)
