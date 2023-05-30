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


class EnableMktme(MktmeBaseTest):
    """
    HPQC ID : H79553-PI_Security_MKTME_Discovery_Number_of_Keys
    Glasgow ID : G59515-MKTME Enable (in-band)_Enable MKTME
    This Test case is enabling TME and MKTME BIOS Knobs and verify msr value, Max No of Keys
    """
    BIOS_CONFIG_FILE = "../security_tme_mktme_bios_enable.cfg"
    TEST_CASE_ID = ["G59515-MKTME Enable (in-band)_Enable MKTME","H79553-PI_Security_MKTME_Discovery_Number_of_Keys"]

    step_data_dict = {1: {'step_details': 'Enable TME and MK-TME Bios Knobs', 'expected_results': 'Verify TME and '
                                                                                                'MKTME Bios Knobs set'},
                      2: {'step_details': 'Checking msr value of MK-TME and Max No of Keys displays',
                          'expected_results': 'Verify MKTME msr value 0x100060000000B and Max No of Keys as 3F'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of EnableMktme

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.tme_mktme_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(EnableMktme, self).__init__(test_log, arguments, cfg_opts, self.tme_mktme_bios_enable)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self.cng_log.redirect(os.path.join(self.serial_log_dir, self._SERIAL_LOG_FILE))

    def prepare(self):
        # type: () -> None
        """
        This function check verify platform supporting the MKTME and Enabling TME and MK-TME Bios knobs.

        :raise: content_exceptions.TestNAError if there is any error while check CPU SKU support of MK-TME
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        # Verify platform will support MKTME or not
        if not self.verify_mktme():
            raise content_exceptions.TestNAError("This CPU SKU does not support for MK-TME")
        self._log.info("SUT supports MK-TME....")
        # Enabling TME and MK-TME BIOS Knobs
        super(EnableMktme, self).prepare()
        self._common_content_lib.update_micro_code()
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        check the TME, MK-TME MSR Value and Verify the Max No of Keys

        :return True else false
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        # Check the msr value and Max No of Keys for MK-TME
        self.msr_read_and_verify(self.MSR_TME_ADDRESS, self.MSR_MKTME_VAL)
        # Serial log path
        serial_log_path = os.path.join(self.serial_log_dir, self._SERIAL_LOG_FILE)
        self.verify_mktme_max_keys(serial_log_path)
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if EnableMktme.main()else Framework.TEST_RESULT_FAIL)
