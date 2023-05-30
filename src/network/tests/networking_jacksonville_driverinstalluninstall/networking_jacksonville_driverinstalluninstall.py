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
import sys
import shutil

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.driver_provider import DriverProvider
from src.provider.driver_provider import NetworkDrivers
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions


class JacksonvilleDriverInstallUnistall(ContentBaseTestCase):
    """
    HPQC ID : H80068
    1) installs Jacksonville Driver and verifies whether the driver is loaded.
    2) uninstalls Jacksonville Driver and verifies whether the driver is not loaded.
    3) reinstall Jacksonville Driver and verifies whether the driver is loaded.
    """
    TEST_CASE_ID = ["H80068"]
    step_data_dict = {
        1: {'step_details': 'Install Jacksonville driver in sut using make',
            'expected_results': 'Jacksonville driver should be installed successfully'},
        2: {'step_details': 'Uninstall Jacksonville driver in sut',
            'expected_results': 'Jacksonville driver should be uninstalled successfully'},
        3: {'step_details': 'Reinstall Jacksonville driver in sut',
            'expected_results': 'Jacksonville driver should be installed successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of JacksonvilleDriverInstallUnistall.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(JacksonvilleDriverInstallUnistall, self).__init__(test_log, arguments, cfg_opts)
        self._driver_provider = DriverProvider.factory(self._log, cfg_opts, self.os)  # type: DriverProvider
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):  # type: () -> None
        """Pre-checks if the test case is applicable Linux OS."""
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError(
                "{} installation is not implemented for the os: {}".format(
                    NetworkDrivers.JACKSONVILLE_DRIVER_NAME, self.os.os_type))
        super(JacksonvilleDriverInstallUnistall, self).prepare()

    def execute(self):  # type: () -> bool
        """
        This function calls Driver installation provider and performs below step.
        1) Checks JacksonvilleDriver installed successful.
        2) Verify Un-installation JacksonvilleDriver is successful.
        3) Verify Reloads the JacksonvilleDriver is successful.

        :return: True if all steps executes and getting the status as expected.
        """
        self._test_content_logger.start_step_logger(1)
        self.copy_driver_files()
        self._driver_provider.install_driver(
            NetworkDrivers.JACKSONVILLE_DRIVER_CODE, NetworkDrivers.JACKSONVILLE_DRIVER_NAME)
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._test_content_logger.start_step_logger(2)
        self._driver_provider.uninstall_driver(
            NetworkDrivers.JACKSONVILLE_DRIVER_CODE, NetworkDrivers.JACKSONVILLE_DRIVER_NAME)
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._test_content_logger.start_step_logger(3)
        self._driver_provider.load_driver(
            NetworkDrivers.JACKSONVILLE_DRIVER_CODE, NetworkDrivers.JACKSONVILLE_DRIVER_NAME)
        self._test_content_logger.end_step_logger(3, return_val=True)
        return True

    def copy_driver_files(self):
        """copy the driver zip files to sut by getting the path from content configuration file."""
        self._log.info("copying driver zip file {} to sut".format(NetworkDrivers.JACKSONVILLE_DRIVER_NAME))
        jacksonville_source_path = self._common_content_configuration.get_jacksonville_driver()
        shutil.copy(jacksonville_source_path, self._common_content_lib.get_collateral_path())
        self._common_content_lib.copy_zip_file_to_linux_sut(DriverProvider.DRIVER_DEST_PATH_LINUX,
                                                            os.path.basename(jacksonville_source_path))


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if JacksonvilleDriverInstallUnistall.main()
             else Framework.TEST_RESULT_FAIL)
