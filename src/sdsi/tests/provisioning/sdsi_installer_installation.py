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
"""DEPRECATION WARNING - Not included in agent scripts/libraries, which will become the standard test scripts."""
import warnings
warnings.warn("This module is not included in agent scripts/libraries.", DeprecationWarning, stacklevel=2)
import sys

from dtaf_content.src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib
from dtaf_core.lib.dtaf_constants import Framework

from src.lib.content_base_test_case import ContentBaseTestCase


class SDSiInstallerInstallation(ContentBaseTestCase):
    """
    Glasgow_ID: 69489
    Phoenix_ID: 18014075443
    The installation of the SDSi Installer application. Usage of SDSi Installer for platform data collection.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SDSiInstallation
        :param cfg_opts: Configuration options for execution environment.
        :param test_log: Used for debug, error and info messages
        """
        super(SDSiInstallerInstallation, self).__init__(test_log, arguments, cfg_opts)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(SDSiInstallerInstallation, self).prepare()

    def execute(self):
        """
            Verifies the SPR_SDSi_Installer and spr_output_parser and verify the usage.
            1. Verify SPR_SDSi_Installer and spr_output_parser are available on the SUT.
            2. Verify the SPR_SDSi_Installer by initiating --help command.
        """
        self._log.info("Verify the SPR_SDSi_Installer by initiating --help command.")
        self._sdsi_installer.verify_sdsi_installer()
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """Test cleanup"""
        super(SDSiInstallerInstallation, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SDSiInstallerInstallation.main()
             else Framework.TEST_RESULT_FAIL)
