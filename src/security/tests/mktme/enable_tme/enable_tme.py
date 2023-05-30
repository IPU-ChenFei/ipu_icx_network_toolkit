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
# secret laws and treaty provisions. No part of the Material may be used,
# copied, reproduced, modified, published, uploaded, posted, transmitted,
# distributed, or disclosed in any way without Intel's prior express written
# permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################
import sys
import os

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.security.tests.mktme.mktme_common import MktmeBaseTest
from src.lib.bios_util import BiosUtil


class EnableTme(MktmeBaseTest):
    """
    Glasgow ID : G58196
    Phoenix ID : P18014070782
    Verify TME msr value at given msr address after TME enable.
    """
    TEST_CASE_ID = ["G58196",
                    "P18014070782 - Verify TME can be enabled with BIOS knobs"]
    step_data_dict = {
        1: {'step_details': 'Verify EnableTme is disable',
            'expected_results': 'EnableTme value is 0x00 '},
        2: {'step_details': 'Check EnableTme is Enable',
            'expected_results': 'EnableTme value is 0x01'},
        3: {'step_details': 'Run ITP commands'
                            'execute itp.threads[0].msr(0x982)',
            'expected_results': 'match msr value  0x000000000000b '}
    }

    _BIOS_CONFIG_FILE_ENABLE = "tme_enable_knob.cfg"
    _BIOS_CONFIG_FILE_DISABLE = "tme_disable_knob.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of EnableTme

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.tme_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            self._BIOS_CONFIG_FILE_ENABLE)
        self.tme_bios_disable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             self._BIOS_CONFIG_FILE_DISABLE)
        super(EnableTme, self).__init__(test_log, arguments, cfg_opts)
        self.bios_util = BiosUtil(cfg_opts, bios_obj=self.bios, log=self._log, common_content_lib=self._common_content_lib)
        self._test_content_logger = TestContentLogger(self._log,
                                                      self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        Checking EnableTme knob is default disable or not
        Loading BIOS defaults settings.

        :return: None
        """
        super(EnableTme, self).prepare()

    def execute(self):
        """
        Sets the bios knobs according to configuration file.
        This method verify msr value for the given address
        return: True if test completed successfully, False otherwise.
        """
        self._test_content_logger.start_step_logger(1)
        # if ME and TME-MT is not disabled by default, then reset the value, reboot and verify again
        try:
            self.bios_util.verify_bios_knob(bios_config_file=self.tme_bios_disable)
        except RuntimeError:
            # Disable TME and TME-MT now.
            self.bios_util.set_bios_knob(bios_config_file=self.tme_bios_disable)
            self.perform_graceful_g3()
            self.bios_util.verify_bios_knob(bios_config_file=self.tme_bios_disable)

        self._test_content_logger.end_step_logger(1, return_val=True)
        self._test_content_logger.start_step_logger(2)
        self.bios_util.set_bios_knob(bios_config_file=self.tme_bios_enable)
        self.perform_graceful_g3()
        self.bios_util.verify_bios_knob(bios_config_file=self.tme_bios_enable)
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._test_content_logger.start_step_logger(3)
        self.msr_read_and_verify(self.MSR_TME_ADDRESS, self.ENABLE_TME_MSR_VALUE, squash=False)
        self._test_content_logger.end_step_logger(3, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if EnableTme.main() else Framework.TEST_RESULT_FAIL)
