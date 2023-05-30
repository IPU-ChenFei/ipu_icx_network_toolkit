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
from dtaf_core.lib.os_lib import LinuxDistributions

from src.lib.dtaf_content_constants import RootDirectoriesConstants
from src.lib.test_content_logger import TestContentLogger
from src.lib.install_collateral import InstallCollateral
from src.storage.test.storage_common import StorageCommon
from src.lib import content_exceptions


class SATASSDFWUpgradeCheckAHCIMode(StorageCommon):
    """  Phoenix ID : 1308855057 SATASSD- FW upgrade check in AHCI Mode
    This test case functionality is to install, execute intelmas tool on SUT and upgrade the SSD FW
    """
    TEST_CASE_ID = ["1308855057", "SATASSD- FW upgrade check in AHCI Mode"]
    CHMOD_CMD = "chmod +x {}"
    MAS_TOOL_FOLDER = "/root/intelmastool/"
    FIND_CMD = "find {} -name *x86*"

    step_data_dict = {
        1: {'step_details': 'Verify if system booted to Rhel OS',
            'expected_results': 'Successfully verified that system booted to Rhel OS'},
        2: {'step_details': 'Install intelmastool',
            'expected_results': 'Successfully Installed intelmastool for RHEL'},
        3: {'step_details': 'Check the fw version of intelssd and update the SSD fw version',
            'expected_results': 'show and load Commands run successfully and fw update successful'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new SATASSDFWUpgradeCheckAHCIMode object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(SATASSDFWUpgradeCheckAHCIMode, self).__init__(test_log, arguments, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        super(SATASSDFWUpgradeCheckAHCIMode, self).prepare()
        # Step logger Start for Step 1
        self._test_content_logger.start_step_logger(1)
        if self.os.os_subtype.lower() != LinuxDistributions.RHEL.lower():
            raise content_exceptions.TestFail("System is in {} and not in RHEL!".format(self.os.os_subtype))
        self._log.info("System booted to RHEL Successfully!")
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, True)

    def execute(self):
        """
        This test case functionality is to install, execute intelmas tool on SUT and upgrade the SSD FW

        :return: True
        :raise: If Upgradation failed raise content_exceptions.TestFail
        """
        # Step logger Start for Step 2
        self._test_content_logger.start_step_logger(2)
        intelmas_file_path_host = self._common_content_configuration.get_intelmastool_path()
        # Copy intelmastool to SUT
        self._common_content_lib.copy_tool_to_collateral(intelmas_file_path_host)
        mas_tool_folder = self._common_content_lib.copy_zip_file_to_linux_sut(
                                            self.MAS_TOOL_FOLDER, intelmas_file_path_host)
        mastool_file = self._common_content_lib.execute_sut_cmd(self.FIND_CMD.format(self.MAS_TOOL_FOLDER),
                                                                cmd_str=self.FIND_CMD.format(self.MAS_TOOL_FOLDER),
                                                                execute_timeout=self._command_timeout,
                                                                cmd_path=mas_tool_folder)
        self._common_content_lib.execute_sut_cmd(sut_cmd=self.CHMOD_CMD.format(mastool_file),
                                                 cmd_str=self.CHMOD_CMD.format(mastool_file),
                                                 execute_timeout=self._command_timeout,
                                                 cmd_path=mas_tool_folder)
        # Installing intelmas Tool
        self._install_collateral.yum_install(mastool_file.strip())
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, True)

        # Step logger Start for Step 3
        self._test_content_logger.start_step_logger(3)
        intel_ssd_id_list = self.get_intelssd()
        self._log.info("Upgrade FW using intelmas load command on each Intel SSD present in the System")
        for each_id in intel_ssd_id_list:
            self.upgrade_ssd_fw_and_verify(each_id)
        self._log.info("Successfully Upgraded all Intel SSDs present in the System")
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(SATASSDFWUpgradeCheckAHCIMode, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SATASSDFWUpgradeCheckAHCIMode.main() else Framework.TEST_RESULT_FAIL)
