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

from src.provider.copy_usb_provider import UsbRemovableDriveProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.install_collateral import InstallCollateral


class TestUsbRemovableDriveCopyProvider(BaseTestCase):
    """
    Class to copy file to sut usb and vice versa then copy to host
    """

    HELLO_TXT_FILE = "hello.zip"

    def __init__(self, test_log, arguments, cfg_opts):

        super(TestUsbRemovableDriveCopyProvider, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._copy_usb = UsbRemovableDriveProvider.factory(test_log, cfg_opts, self._os)
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        if not self._os.is_alive():
            self._log.error("System is not alive")
            raise RuntimeError("OS is not alive")

    def execute(self):  # type: () -> bool
        """
        Function that has the following functionalities.
        1. Copy file to sut.
        2. Copy file from sut to usb.
        3. Unzip the file in the usb.
        4. Copy the file from usb to sut.
        5. Copy the file from sut to host.

        :return: path of the host folder.
        """

        zip_file_path = self._install_collateral.download_and_copy_zip_to_sut(
            self.HELLO_TXT_FILE.split(".")[0], self.HELLO_TXT_FILE)

        self._log.info("Copying to SUT is done ....")
        usb_file_path = self._copy_usb.copy_file_from_sut_to_usb(self._common_content_lib,
                                                                 self._common_content_configuration, zip_file_path)
        self._log.info("Copying to USB is done ....")
        sut_file_path = self._copy_usb.copy_file_from_usb_to_sut(self._common_content_lib,
                                                                 self._common_content_configuration, usb_file_path)
        self._log.info("Copying to back to SUT is done ....")
        host_file_path = self._common_content_lib.copy_log_files_to_host("Test_folder", sut_file_path, ".txt")

        self._log.info("Copying to back to HOST is done .... The file is under {}".format(host_file_path))

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TestUsbRemovableDriveCopyProvider.main() else Framework.TEST_RESULT_FAIL)
