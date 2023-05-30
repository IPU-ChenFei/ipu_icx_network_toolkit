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
from src.provider.storage_provider import StorageProvider
from src.storage.lib.storage_common import StorageCommon
from src.lib.dtaf_content_constants import SutInventoryConstants


class StorageM2NvmeOSInstallWindows(BaseTestCase):
    """
    Glasgow : EGS_PV_1293-M.2 NVME OS installation.
    Pheonix Id : 16013597924-M.2 NVME OS installation(Windows).

    Install Windows OS on M.2 NVME
    """
    TEST_CASE_ID = ["EGS_PV_1293", "P16013597924", "M.2 NVME OS installation"]
    NVME_SSD_NAME_WINDOWS = "nvme_ssd_name_windows"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageM2NvmeOSInstallWindows object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts

        self._cc_log_path = arguments.outputpath
        super(StorageM2NvmeOSInstallWindows, self).__init__(test_log, arguments, cfg_opts)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()  # command timeout in seconds
        sut_os_cfg = self._cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        os = ProviderFactory.create(sut_os_cfg, self._log)  # type: SutOsProvider

        self._storage_provider = StorageProvider.factory(self._log, os, self._cfg_opts, "os")
        self._common_content_lib = CommonContentLib(self._log, os, None)
        self.storage_common = StorageCommon(self._log, self._cfg_opts)
        self.name_ssd = None
        self.log_dir = None

    @classmethod
    def add_arguments(cls, parser):
        super(StorageM2NvmeOSInstallWindows, cls).add_arguments(parser)
        # Use add_argument
        parser.add_argument('-o', '--outputpath', action="store", default="",
                            help="Log folder to copy log files to command center")

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        sut_inv_file_path = self._os_installation_lib.get_sut_inventory_file_path()
        self.name_ssd = None
        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if self.NVME_SSD_NAME_WINDOWS in line:
                    self.name_ssd = line
                    break

        if not self.name_ssd:
            raise content_exceptions.TestError("Unable to find ssd name, please check the file under "
                                               "{}".format(sut_inv_file_path))

        self.name_ssd = self.name_ssd.split("=")[1]

        self._log.info("NVME SSD Name from config file : {}".format(self.name_ssd))
        self._common_content_lib.update_sut_inventory_file(SutInventoryConstants.NVME, SutInventoryConstants.WINDOWS)


    def execute(self):

        ret_val = []
        ret_val.append(self._os_installation_lib.windows_os_installation())
        self._log.info("Windows OS installed successfully ...")
        self.log_dir = self._common_content_lib.get_log_file_dir()
        ret_val.append(self.storage_common.verify_os_boot_device_type(SutInventoryConstants.NVME))

        return all(ret_val)

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        # copy logs to CC folder if provided
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

        super(StorageM2NvmeOSInstallWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageM2NvmeOSInstallWindows.main() else Framework.TEST_RESULT_FAIL)
