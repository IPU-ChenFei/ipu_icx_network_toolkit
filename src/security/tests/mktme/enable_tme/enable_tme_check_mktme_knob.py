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
import time

from dtaf_core.lib.dtaf_constants import Framework

from src.security.tests.mktme.mktme_common import MktmeBaseTest
from src.lib.bios_util import ItpXmlCli, PlatformConfigReader
from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions


class EnableTmeCheckMktmeKnob(MktmeBaseTest):
    """
    Glasgow ID : G58195.1-MKTME Enable (in-band)_Without TME
    HPQC ID - H81141-Verify_MKTME_cannot_be_enabled_without_enabling_TME
    Phoneix ID - P18014075686-Verify_MKTME_cannot_be_enabled_without_enabling_TME
    Phoenix ID - P18014070697 - Verify MKTME cannot be enabled without enabling TME
    
    Enable/Diable TME and Verify MKTME Bios knob visible or not
    """
    TEST_CASE_ID = ["G58195.1-MKTME Enable (in-band)_Without TME",
                    "H81141-Verify_MKTME_cannot_be_enabled_without_enabling_TME",
                    "P18014075686 - Verify_MKTME_cannot_be_enabled_without_enabling_TME",
                    "P18014070697 - Verify MKTME cannot be enabled without enabling TME"]

    BIOS_CONFIG_FILE_ENABLE = "tme_enable_knob.cfg"
    BIOS_CONFIG_FILE_DISABLE = "tme_disable_knob.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of EnableTmeCheckMktmeKnob

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.tme_bios_enable_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                        self.BIOS_CONFIG_FILE_ENABLE)
        self.tme_bios_disable_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                         self.BIOS_CONFIG_FILE_DISABLE)
        super(EnableTmeCheckMktmeKnob, self).__init__(test_log, arguments, cfg_opts, self.tme_bios_enable_config_path)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)


    def prepare(self):
        # type: () -> None
        """
        Enable TME knob and verify the TME Knob

        :return: None
        """
        super(EnableTmeCheckMktmeKnob, self).prepare()

    def execute(self):
        """.
        1. Read MSR value after enabling the TME knob.
        2. Updating the platform config file, Get MKTME knob status and verify the bios knob visible.
        3. Disable TME Knob, Update the platform config file.
        4. Get MKTME knob status and verify the bios knob visible.

        :return: True if test completed successfully, False otherwise.
        :raise: raise content_exceptions.TestFail if MKTME Knobs status not visible after TME knob enable.
        """
        # Generating he platform config file
        platform_file = ItpXmlCli(self._log, self._cfg)
        platform_read = PlatformConfigReader(platform_file.get_platform_config_file_path(), test_log=self._log)
        # Check MKTME Bios Knob is visible or not
        mktme_knob_status = platform_read.get_knob_status(self.MKTME_KNOB_NAME)
        self._log.info("MK-TME Knob status in bios menu= %s", mktme_knob_status)
        time.sleep(self.WAIT_TIME_DELAY)
        if platform_read.HIDDEN_KNOB_STATUS == mktme_knob_status:
            raise content_exceptions.TestFail("MKTME Knob is not visible")
        # Disable TME Bios Knob
        self.bios_util.set_bios_knob(bios_config_file=self.tme_bios_disable_config_path)
        self.perform_graceful_g3()
        self.bios_util.verify_bios_knob(bios_config_file=self.tme_bios_disable_config_path)
        # Updating the platform config file
        platform_read.update_xml_file(platform_file.get_platform_config_file_path())
        # Check MKTME Bios Knob should not be visible
        mktme_knob_status = platform_read.get_knob_status(self.MKTME_KNOB_NAME)
        time.sleep(self.WAIT_TIME_DELAY)
        self._log.info("MK-TME Knob status in bios menu= %s", mktme_knob_status)
        if platform_read.HIDDEN_KNOB_STATUS != mktme_knob_status:
            raise content_exceptions.TestFail("MKTME knob is still exposed after disable TME")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if EnableTmeCheckMktmeKnob.main() else Framework.TEST_RESULT_FAIL)
