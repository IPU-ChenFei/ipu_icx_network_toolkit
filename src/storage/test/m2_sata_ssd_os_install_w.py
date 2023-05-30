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
from dtaf_core.providers.ac_power import AcPowerControlProvider

from src.environment.os_installation import OsInstallation
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.lib.install_collateral import InstallCollateral
from src.storage.lib.storage_common import StorageCommon
from src.lib.dtaf_content_constants import SutInventoryConstants


class M2SataSsdOsInstallationWindows(BaseTestCase):
    """
    Phoenix : 16014319349 - M.2 SATASSD OS installation (Windows)

    Install Windows OS on the platform
    """

    TEST_CASE_ID = ["16014319349", "M.2 SATASSD OS installation"]

    step_data_dict = {1: {'step_details': 'start windows OS installation',
                          'expected_results': 'Windows OS installed successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new M2SataSsdOsInstallationWindows object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts

        self._cc_log_path = arguments.outputpath
        super(M2SataSsdOsInstallationWindows, self).__init__(test_log, arguments, cfg_opts)
        sut_os_cfg = self._cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self.os = ProviderFactory.create(sut_os_cfg, self._log)  # type: SutOsProvider
        self._common_content_lib = CommonContentLib(self._log, self.os, self._cfg_opts)

        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()  # command timeout in seconds
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self.ac_power = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider

        self.log_dir = self._common_content_lib.get_log_file_dir()

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self.install_collateral_obj = InstallCollateral(self._log, self.os, self._cfg_opts)
        self.storage_common = StorageCommon(self._log, self._cfg_opts)
        self.name_ssd = None

    @classmethod
    def add_arguments(cls, parser):
        super(M2SataSsdOsInstallationWindows, cls).add_arguments(parser)
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
                if SutInventoryConstants.SATA_SSD_NAME_WINDOWS in line:
                    self.name_ssd = line
                    break
            else:
                raise content_exceptions.TestError("Unable to find ssd name for {} installation, please check "
                                                   "and update it correctly".format(sut_inv_file_path))

        self.name_ssd = self.name_ssd.split("=")[1]

        self._log.info("SSD Name from config file : {}".format(self.name_ssd))
        self._common_content_lib.update_sut_inventory_file(SutInventoryConstants.SATA, self.os.os_subtype.lower())

    def execute(self):

        ret_val = list()

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        ret_val.append(self._os_installation_lib.windows_os_installation())

        self._log.info("Windows OS installed successfully ...")

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)
        self.os.wait_for_os(self._reboot_timeout)

        if not self.os.is_alive():
            self._log.error("System is not alive")
            raise content_exceptions.TestFail("System is not alive")

        ret_val.append(self.storage_common.verify_os_boot_device_type("SATA"))

        return all(ret_val)

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        # copy logs to CC folder if provided
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

        super(M2SataSsdOsInstallationWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if M2SataSsdOsInstallationWindows.main() else Framework.TEST_RESULT_FAIL)
