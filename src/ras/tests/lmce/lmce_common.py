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
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################

import os
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.ras.lib.ras_mca_common import McaCommonUtils
from src.lib.install_collateral import InstallCollateral
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.lib.content_base_test_case import ContentBaseTestCase


class LmceCommon(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the Lmce Functionality Test Cases
    """
    TOOL_EXE_LOG_CMD = "cat exe.log"
    LMCE_OUTPUT_RAS_TOOL_LIST = ["Saw local machine check"]

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts,
            bios_config
    ):
        """
        Create an instance of sut os provider, BiosProvider, SiliconDebugProvider, SiliconRegProvider
         BIOS util and Config util,

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config: Bios Configuration file name
        """
        if bios_config:
            bios_config = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), bios_config)
        super(
            LmceCommon,
            self).__init__(
            test_log,
            arguments,
            cfg_opts,
            bios_config)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._execute_cmd_timeout_in_sec = self._common_content_configuration.get_command_timeout()
        self._mca_common = McaCommonUtils(self._log, self.os, self._common_content_lib,
                                          self._common_content_configuration, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._check_os_log = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration,
                                               self._common_content_lib)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the Bios knobs are Updated Properly.
        :return: None
        """
        super(LmceCommon, self).prepare()

    def lmce_check_log(self):
        """
        This Function is to verifies RAS Tool log indicated LMCE, messages contain LMCE information

        :return: True if string found else False.
        """
        self._log.info(self._mca_common.DUT_MESSAGES_FILE_NAME)
        command_result = self.os.execute(self.TOOL_EXE_LOG_CMD,
                                         self._common_content_configuration.get_command_timeout())
        if command_result.cmd_failed():
            if command_result.cmd_failed():
                log_error = "Failed to run cat exe.log command with return value = '{}' and " \
                            "std_error='{}'..".format(command_result.return_code, command_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)

        # Check for proper error message in /var/log/messages file
        lmce_indicated_in_messages = self._check_os_log.verify_os_log_error_messages(
             __file__, self._mca_common.DUT_MESSAGES_FILE_NAME, self._mca_common.LMCE_EXE_ERROR_MESSAGES_LIST)

        # Check for proper error message in Ras_tools output
        lmce_indicated_in_ras_tool_output = self._check_os_log.verify_os_log_error_messages(
            __file__, self._mca_common.DUT_RAS_TOOLS_FILE_NAME, self.LMCE_OUTPUT_RAS_TOOL_LIST)

        return lmce_indicated_in_messages & lmce_indicated_in_ras_tool_output
