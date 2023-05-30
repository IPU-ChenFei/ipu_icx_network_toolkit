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
import os

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.environment.os_installation import OsInstallation
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.storage.lib.storage_common import StorageCommon
from src.lib.dtaf_content_constants import SutInventoryConstants


class StorageBootingToNvmeUefimWindows(BaseTestCase):
    """
    HPALM : H80269-PI_Storage_BootingToNVMe_UEFIM_W

    Install Windows OS on the NVMe
    """

    TEST_CASE_ID = ["H80269", "PI_Storage_BootingToNVMe_UEFIM_W"]

    step_data_dict = {1: {'step_details': 'start windows OS installation',
                          'expected_results': 'Windows OS installed successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageBootingToNvmeUefimWindows object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts
        self._arguments = arguments
        self._cc_log_path = arguments.outputpath

        super(StorageBootingToNvmeUefimWindows, self).__init__(test_log, arguments, cfg_opts)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()  # command timeout in seconds
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()  # reboot timeout in seconds
        sut_os_cfg = self._cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, self._log)  # type: SutOsProvider
        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg_opts)
        self.log_dir = None
        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self.storage_common = StorageCommon(self._log, self._cfg_opts)
        self._common_content_lib.update_sut_inventory_file(SutInventoryConstants.NVME,SutInventoryConstants.WINDOWS)


    @classmethod
    def add_arguments(cls, parser):
        super(StorageBootingToNvmeUefimWindows, cls).add_arguments(parser)
        # Use add_argument
        parser.add_argument('-o', '--outputpath', action="store", default="",
                            help="Log folder to copy log files to command center")

    def execute(self):

        ret_val = list()

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        ret_val.append(self._os_installation_lib.windows_os_installation())

        self.log_dir = self._common_content_lib.get_log_file_dir()

        self._os.wait_for_os(self._reboot_timeout)

        if not self._os.is_alive():
            raise content_exceptions.TestFail("System is not alive")

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        ret_val.append(self.storage_common.verify_os_boot_device_type("Nvme"))

        return all(ret_val)

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        # copy logs to CC folder if provided
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

        super(StorageBootingToNvmeUefimWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageBootingToNvmeUefimWindows.main() else Framework.TEST_RESULT_FAIL)
