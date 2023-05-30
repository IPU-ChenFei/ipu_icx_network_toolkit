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
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib.dtaf_content_constants import VROCConstants


class PiStorageRSTeDriverInstallationW(ContentBaseTestCase):
    """
    HPALM : 82190-PI_Storage_RSTeDriver_Installation_exe_W
    This test case functionality is to install and verify VROC Tool
    """
    TEST_CASE_ID = ["H82190", "PI_Storage_RSTeDriver_Installation_exe_W"]

    step_data_dict = {1: {'step_details': 'Install the Windows driver run VROCSetup.exe -s.'
                                          'Reboot and Verify driver installed correctly using any method like checking'
                                          ' in control panel or driver queries.',
                          'expected_results': 'The driver was installed and verified successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PiStorageRSTeDriverInstallationW object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PiStorageRSTeDriverInstallationW, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.WINDOWS:
            raise NotImplementedError("This Test is Supported only on Windows")

        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        super(PiStorageRSTeDriverInstallationW, self).prepare()

    def execute(self):
        """
        Install and verify VROC Tool

        :return: True
        :raise: If installation failed raise content_exceptions.TestFail
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        verify_output = self._common_content_lib.execute_sut_cmd(VROCConstants.VERIFY_VROC_CMD,
                                                                 VROCConstants.VERIFY_VROC_CMD, self._command_timeout)
        self._log.debug("Verify command:{} output:{}".format(VROCConstants.VERIFY_VROC_CMD, verify_output))
        if VROCConstants.TOOL_NAME in verify_output:
            # TODO: Waiting for uninstall implementation
            self._log.debug("TODO: Need steps for uninstall implementation to remove existing installation")
        self._install_collateral.install_vroc_tool_windows()
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        # TODO: Waiting for uninstall implementation
        super(PiStorageRSTeDriverInstallationW, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiStorageRSTeDriverInstallationW.main() else Framework.TEST_RESULT_FAIL)
