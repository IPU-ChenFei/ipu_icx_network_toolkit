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
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.environment.os_installation import OsInstallation
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.provider.storage_provider import StorageProvider
from src.storage.test.storage_common import StorageCommon
from src.lib.dtaf_content_constants import SutInventoryConstants


class StorageBootingToSataUefimWindows(BaseTestCase):
    """
    HPALM : H82189-PI_Storage_BootingToSATA_UEFIM_W

    Install Windows OS on the platform and check ahci speed link.
    """

    TEST_CASE_ID = ["H82189", "PI_Storage_BootingToSATA_UEFIM_W"]

    step_data_dict = {1: {'step_details': 'start windows OS installation',
                          'expected_results': 'Windows OS installed successfully'},
                      2: {'step_details': 'Copy smartctl.exe to the SUT and check the ahci link speed',
                          'expected_results': 'smartctl.exe copied to the SUT and checked the ahci link speed'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageBootingToSataUefimWindows object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts
        self._arguments = arguments
        self._cc_log_path = arguments.outputpath

        super(StorageBootingToSataUefimWindows, self).__init__(test_log, arguments, cfg_opts)
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
        self._common_content_lib.update_sut_inventory_file(SutInventoryConstants.SATA, SutInventoryConstants.WINDOWS)

    @classmethod
    def add_arguments(cls, parser):
        super(StorageBootingToSataUefimWindows, cls).add_arguments(parser)
        # Use add_argument
        parser.add_argument('-o', '--outputpath', action="store", default="",
                            help="Log folder to copy log files to command center")

    def execute(self):
        """
        To install windows OS and check ahci speed link.

        :return: True or False
        """
        ret_val = list()

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        # To install windows OS
        ret_val.append(self._os_installation_lib.windows_os_installation())

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._log.info("Windows OS installed successfully ...")

        self.log_dir = self._common_content_lib.get_log_file_dir()

        self._os.wait_for_os(self._reboot_timeout)

        if not self._os.is_alive():
            self._log.error("System is not alive")
            raise content_exceptions.TestFail("System is not alive")

        install_collateral_obj = InstallCollateral(self._log, self._os, self._cfg_opts)

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        install_collateral_obj.copy_smartctl_exe_file_to_sut()

        storage_common_obj = StorageCommon(self._log, self._arguments, self._cfg_opts)

        # To check ahci link speed
        ret_val.append(storage_common_obj.check_ahci_link_speed_windows())

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        return all(ret_val)

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        # copy logs to CC folder if provided
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

        super(StorageBootingToSataUefimWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageBootingToSataUefimWindows.main() else Framework.TEST_RESULT_FAIL)
