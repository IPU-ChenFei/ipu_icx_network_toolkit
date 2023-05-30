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
from src.storage.lib.storage_common import StorageCommon
from src.lib.test_content_logger import TestContentLogger
from src.provider.storage_provider import StorageProvider
from src.lib.dtaf_content_constants import SutInventoryConstants


class StorageBootingToU2NvmeWindows(BaseTestCase):
    """
    Phoenix ID : 18015948171-PI_Storage_BootingTo_U.2_W

    Install Windows OS on connected NVMe U.2 card and boot into it,
    """
    TEST_CASE_ID = ["18015948171", "PI_Storage_BootingTo_U.2_W"]
    NVME_SSD_NAME_WINDOWS = "nvme_ssd_name_windows"
    name_ssd = None

    step_data_dict = {1: {'step_details': 'start windows OS installation',
                          'expected_results': 'Windows OS installed successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageBootingToU2NvmeWindows object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts

        self._cc_log_path = arguments.outputpath

        super(StorageBootingToU2NvmeWindows, self).__init__(test_log, arguments, cfg_opts)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()  # command timeout in seconds
        sut_os_cfg = self._cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, self._log)  # type: SutOsProvider
        self._storage_provider = StorageProvider.factory(self._log, self._os, self._cfg_opts, "os")
        self._common_content_lib = CommonContentLib(self._log, self._os, None)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self.log_dir = self._common_content_lib.get_log_file_dir()
        self.storage_common = StorageCommon(self._log, self._cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    @classmethod
    def add_arguments(cls, parser):
        super(StorageBootingToU2NvmeWindows, cls).add_arguments(parser)
        # Use add_argument
        parser.add_argument('-o', '--outputpath', action="store", default="",
                            help="Log folder to copy log files to command center")

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        sut_inv_file_path = self._os_installation_lib.get_sut_inventory_file_path()
        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if self.NVME_SSD_NAME_WINDOWS in line:
                    self.name_ssd = line
                    break

        if not self.name_ssd:
            raise content_exceptions.TestError("Unable to find ssd name, please check the file under "
                                               "{}".format(sut_inv_file_path))
        self.name_ssd = self.name_ssd.split("=")[1]
        self._log.info("SSD Name from config file : {}".format(self.name_ssd))
        self._common_content_lib.update_sut_inventory_file(SutInventoryConstants.NVME, SutInventoryConstants.WINDOWS)

    def execute(self):
        """
        This method is used to install the WINDOWS OS
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._os_installation_lib.windows_os_installation()

        self.log_dir = self._common_content_lib.get_log_file_dir()

        self._os.wait_for_os(self._reboot_timeout)

        if not self._os.is_alive():
            raise content_exceptions.TestFail("System is not alive")

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        self.storage_common.verify_os_boot_device_type("Nvme")

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        # copy logs to CC folder if provided
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

        super(StorageBootingToU2NvmeWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageBootingToU2NvmeWindows.main() else Framework.TEST_RESULT_FAIL)
