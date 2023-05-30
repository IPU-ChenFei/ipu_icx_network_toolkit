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
import argparse
import logging
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.security.tests.mktme.mktme_common import MktmeBaseTest


class EnableMkTmeTxtSgx(MktmeBaseTest):
    """
    Phoenix ID : P15010766544 PI_Security_MKTME_boot_up_with_MKTME_and_TXT_and_SGX_enabled_with_CR_L
    """
    TEST_CASE_ID = ["P15010766544 PI_Security_MKTME_boot_up_with_MKTME_and_TXT_and_SGX_enabled_with_CR_L"]
    _BIOS_CONFIG_FILE_ENABLE = r"..\collateral\mktme_txt_sgx_en_knob.cfg"

    def __init__(self, test_log: logging.Logger, arguments: argparse.Namespace, cfg_opts: ElementTree) -> None:
        """Create an instance of EnableMkTmeTxtSgx.
        :param test_log: Logger object
        :param arguments: arguments as Namespace
        :param cfg_opts: Configuration object.
        :return: None
        """
        self.tme_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._BIOS_CONFIG_FILE_ENABLE)
        super(EnableMkTmeTxtSgx, self).__init__(test_log, arguments, cfg_opts)


    def execute(self):
        """Set the BIOS values and reboot the SUT"""

        # if mktme, TXT and SGX is not enabled by default, then reset the value, reboot and verify again
        try:
            self.bios_util.verify_bios_knob(bios_config_file=self.tme_bios_enable)
        except RuntimeError:
            # reapply mktme, txt and sgx values and reboot it.
            self.bios_util.set_bios_knob(bios_config_file=self.tme_bios_enable)
            self.perform_graceful_g3()
            self.bios_util.verify_bios_knob(bios_config_file=self.tme_bios_enable)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if EnableMkTmeTxtSgx.main() else Framework.TEST_RESULT_FAIL)
