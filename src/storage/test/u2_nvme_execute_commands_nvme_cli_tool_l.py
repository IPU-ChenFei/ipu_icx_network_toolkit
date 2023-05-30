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
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.provider.storage_provider import StorageProvider
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions


class U2NvmeExecuteCommandsNvmeCLITool(BaseTestCase):
    """
    Phoenix ID : 16013802852-U.2 Nvme - Execute the commands of Nvme cli tool.
                Execute the nvme cli tools in rhel OS.
    """
    REGEX_TO_GET_TEMPERATURE_FROM_SMART_LOG = r"temperature[^A-Za-z0-9]*(\S+)"
    TEST_CASE_ID = ["16013802852", "U.2 Nvme - Execute the commands of Nvme cli tool"]
    STEP_DATA_DICT = {
        1: {'step_details': 'install nvme cli tool',
            'expected_results': 'Successfully installed nvme cli tool'},
        2: {'step_details': 'get the list of nvme devices',
            'expected_results': 'listed nvme devices as expected'},
        3: {'step_details': 'execute the commands for smart-log error-log etc',
            'expected_results': 'executed the commands successfully'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new U2NvmeExecuteCommandsNvmeCLITool object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts
        self.nvme_disk_list = None
        self.log_len = 512
        self.log_id = 2

        super(U2NvmeExecuteCommandsNvmeCLITool, self).__init__(test_log, arguments, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self.execute_timeout = self._common_content_configuration.get_command_timeout()  # command timeout in seconds
        sut_os_cfg = self._cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self.os = ProviderFactory.create(sut_os_cfg, self._log)  # type: SutOsProvider
        self._storage_provider = StorageProvider.factory(self._log, self.os, self._cfg_opts, "os")
        self._common_content_lib = CommonContentLib(self._log, self.os, None)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def execute(self):

        lsblk_res = self._storage_provider.get_booted_device()
        self._log.info("booted device is {}".format(str(lsblk_res)))

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._common_content_lib.execute_sut_cmd(sut_cmd=self._storage_provider.CMD_TO_INSTALL_NVME_CLI,
                                                 cmd_str=self._storage_provider.CMD_TO_INSTALL_NVME_CLI,
                                                 execute_timeout=self.execute_timeout)
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        self.nvme_disk_list = self._common_content_configuration.get_nvme_disks()
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        for disk in self.nvme_disk_list:  # loop to check if the devices exist on the SUT
            disk_exist = self._common_content_lib.execute_sut_cmd("ls " + disk,
                                                                  "Executing ls on {} to check if the device "
                                                                  "exist".format(disk), self.execute_timeout)
            if not (disk == disk_exist.strip()):
                raise content_exceptions.TestFail("NVME disk is not being detected, Please check again")
            self._log.info("NVME {} Device is detected in the SUT".format(disk_exist.strip()))

            cmd_smart_log_output = self.os.execute(self._storage_provider.CMD_TO_GET_SMART_LOG.format(disk),
                                                   self.execute_timeout)
            self._log.debug("smart log output {}".format(cmd_smart_log_output.stdout))
            temp = re.findall(self.REGEX_TO_GET_TEMPERATURE_FROM_SMART_LOG, cmd_smart_log_output.stdout)
            self._log.debug("disk temperature is {}".format(temp))

            cmd_error_log_output = self.os.execute(self._storage_provider.CMD_TO_GET_ERROR_LOG.format(disk),
                                                   self.execute_timeout)
            self._log.debug("error log output {}".format(cmd_error_log_output.stdout))
            cmd_log_output = self.os.execute(self._storage_provider.CMD_TO_GET_LOG.format(
                disk, self.log_len, self.log_id), self.execute_timeout)
            self._log.debug("log output {}".format(cmd_log_output.stdout))
            cmd_id_ctrl_output = self.os.execute(self._storage_provider.CMD_ID_CTRL.format(disk),
                                                 self.execute_timeout)
            self._log.debug("id ctrl output {}".format(cmd_id_ctrl_output.stdout))
            if not lsblk_res[:5] in disk:
                self._common_content_lib.execute_sut_cmd(sut_cmd=self._storage_provider.CMD_TO_FORMAT.format(disk),
                                                         cmd_str=self._storage_provider.CMD_TO_FORMAT.format(disk),
                                                         execute_timeout=self.execute_timeout)

            self._common_content_lib.execute_sut_cmd(sut_cmd=self._storage_provider.CMD_TO_RESET.format(disk[:-2]),
                                                     cmd_str=self._storage_provider.CMD_TO_RESET.format(disk[:-2]),
                                                     execute_timeout=self.execute_timeout)

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)
        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        super(U2NvmeExecuteCommandsNvmeCLITool, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if U2NvmeExecuteCommandsNvmeCLITool.main() else Framework.TEST_RESULT_FAIL)
