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
import re

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.lib.install_collateral import InstallCollateral
from src.storage.test.storage_common import StorageCommon
from src.lib import content_exceptions


class SataSsdConfigurationCheckAhciMode(StorageCommon):
    """  Phoenix ID : 1308839394 SATASSD-Configuration check in AHCI Mode

    This test case functionality is to install, execute fio tool on all SATA and m.2 ssds on system.
    """
    TEST_CASE_ID = ["1308839394", "SATASSD-Configuration check in AHCI Mode"]

    LSSCSI = "lsscsi | grep -e ATA | grep -e INTEL"
    REGEX_FOR_SSD = "/dev/\S+"
    step_data_dict = {
        1: {'step_details': 'Check if all the 8 SATA SSD is getting listed under the lsscsi command',
            'expected_results': 'All the 8 SATA SSD is getting listed under the lsscsi command'},
        2: {'step_details': 'Check the configuration of all the SATA SSDs',
            'expected_results': 'Successfully Verified the drive manufacturer and model number of all 8 SATA SSDs'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new SataSsdConfigurationCheckAhciMode object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(SataSsdConfigurationCheckAhciMode, self).__init__(test_log, arguments, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        super(SataSsdConfigurationCheckAhciMode, self).prepare()

    def execute(self):
        """
        This method functionality is to check configuration details of all SATA SSDs in the setup

        :return: True
        :raise: If installation failed raise content_exceptions.TestFail
        """
        # Step logger Start for Step 1
        self._test_content_logger.start_step_logger(1)
        # Get a list of all SSDs in the setup.
        ssd_list_info = self._common_content_lib.execute_sut_cmd(self.LSSCSI, self.LSSCSI, self._command_timeout)
        ssd_list = re.findall(self.REGEX_FOR_SSD, ssd_list_info)
        if len(ssd_list) <= 8:
            raise content_exceptions.TestFail("Please connect 8 SATA SSDs in the setup to go ahead!")
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, True)

        # Step logger Start for Step 2
        self._test_content_logger.start_step_logger(2)
        for each_ssd in ssd_list:
            self.check_ssd_manufacturer_and_model(each_ssd)
        self._log.info("Verified the drive manufacturer and model number on all 8 SATA SSDS")
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SataSsdConfigurationCheckAhciMode.main() else Framework.TEST_RESULT_FAIL)
