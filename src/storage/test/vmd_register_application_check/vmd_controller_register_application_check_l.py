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
import os

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.lib import content_exceptions
from src.environment.os_installation import OsInstallation
from src.provider.storage_provider import StorageProvider
from src.lib.test_content_logger import TestContentLogger
from src.lib.install_collateral import InstallCollateral
from src.lib.common_content_lib import CommonContentLib
from src.storage.test.storage_common import StorageCommon


class VmdEnabledNoRaidRegisterApplicationCheck(StorageCommon):
    """
    Phoenix ID : 16013564260 - HHHL_VMD_Enabled_No_Raid_Register_Application_Check

    """
    TEST_CASE_ID = ["16013564260", "HHHL- VMD Enabled No Raid Register Application Check"]
    step_data_dict = {1: {'step_details': 'Enable VMD for One controller',
                          'expected_results': 'VMD is enabled as required'},
                      2: {'step_details': 'Copy Register Application Tester Tool to OS',
                          'expected_results': 'Register Application Tester Tool installed in OS'},
                      3: {'step_details': 'Run the Register Application Tester Tool ',
                          'expected_results': 'Check if able to read and write in respective VMD controller'}}

    TESTER_CMD_READ_VMD_CTRL_REG = "/root/tester/tester -r"
    TESTER_CMD_WRITE_VMD_CTRL_REG = "/root/tester/tester -w 0x1234"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VmdEnabledNoRaidRegisterApplicationCheck object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts
        sut_os_cfg = self._cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)

        super(VmdEnabledNoRaidRegisterApplicationCheck, self).__init__(test_log, arguments, cfg_opts)

        self._storage_provider = StorageProvider.factory(self._log, self.os, self._cfg_opts, "os")

        cur_path = os.path.dirname(os.path.realpath(__file__))

        self._os_installation_lib = OsInstallation(test_log, cfg_opts)

        self.log_dir = self._common_content_lib.get_log_file_dir()

        self._storage_common = StorageCommon(test_log, arguments, self._cfg_opts)

        self.collateral_installer = InstallCollateral(test_log, self.os, self._cfg_opts)

        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()

        self._os = ProviderFactory.create(sut_os_cfg, self._log)  # type: SutOsProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

        self.storage_common_obj = StorageCommon(self._log, arguments, cfg_opts)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        This method is to do the below tasks
        1. Copy and install register application tester tool.
        2. Execute Register Application Tester Commands to check read and write capabilities in VMD controller.

        :return None
        """
        # start of step 1
        self._test_content_logger.start_step_logger(1)

        super(VmdEnabledNoRaidRegisterApplicationCheck, self).prepare()

        # enable vmd for only one port
        self.storage_common_obj.enable_vmd_bios_knob_using_port_socket("iou0", 0)

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, True)

    def execute(self):
        """
        This method is used to enable VMD ports and run register app cmd.
        """
        result_list = []

        # start of step 2
        self._test_content_logger.start_step_logger(2)

        # install tester tool
        tester_path = self.collateral_installer.install_tester_tool()
        self._log.info("Tester Path = {}".format(tester_path))
        print("Tester Path = {}".format(tester_path))

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, True)

        # start of step 3
        self._test_content_logger.start_step_logger(3)

        # run read cmd
        temp_cmd = self.TESTER_CMD_READ_VMD_CTRL_REG

        # VMD register app read test
        vmd_ctrl_read_reg = self._common_content_lib.execute_sut_cmd(sut_cmd=temp_cmd,
                                                                     cmd_str="reading VMD ctrl reg",
                                                                     execute_timeout=5)
        vmd_ctrl_read_reg_list = vmd_ctrl_read_reg.split("\n")

        # check error in register app output
        if "error" in vmd_ctrl_read_reg_list[1]:
            result_list.append(False)
            raise content_exceptions.TestFail("There was an error on register reading")
        else:
            result_list.append(True)

        # VMD register app write test
        vmd_ctrl_write_reg = self._common_content_lib.execute_sut_cmd(sut_cmd=self.TESTER_CMD_WRITE_VMD_CTRL_REG,
                                                                      cmd_str="writing 0x1234 VMD ctrl reg",
                                                                      execute_timeout=5)
        vmd_ctrl_write_reg_list = vmd_ctrl_write_reg.split("\n")

        # check error in register app output
        if "error" in vmd_ctrl_write_reg_list[1]:
            result_list.append(False)
            raise content_exceptions.TestFail("There was an error on register writing")
        else:
            result_list.append(True)

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, True)

        return all(result_list)

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)
        super(VmdEnabledNoRaidRegisterApplicationCheck, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if VmdEnabledNoRaidRegisterApplicationCheck.main() else Framework.TEST_RESULT_FAIL)
