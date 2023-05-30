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
from dtaf_core.providers.physical_control import PhysicalControlProvider

from src.lib.common_content_lib import CommonContentLib
from src.provider.host_usb_drive_provider import HostUsbDriveProvider
from src.collaterals.collateral_constants import CollateralConstants
from src.lib.install_collateral import InstallCollateral


class ExampleHostUsbDriveProvider(BaseTestCase):
    """
    Test Storage Provider APIs.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        super(ExampleHostUsbDriveProvider, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        print("Creating phy provider")
        phy_cfg = cfg_opts.find(PhysicalControlProvider.DEFAULT_CONFIG_PATH)
        self._phy = ProviderFactory.create(phy_cfg, test_log)  # type: PhysicalControlProvider
        print("Created phy provider")

        self._common_content_lib = CommonContentLib(test_log, self._os, cfg_opts)
        self._host_usb_provider = HostUsbDriveProvider.factory(test_log, cfg_opts, self._os)  # type: HostUsbDriveProvider

        self._install_collateral = InstallCollateral(test_log, self._os, cfg_opts)

    def prepare(self):
        """
        prepare.
        """
        pass

    def execute(self):
        """
        executes storage provider APIs.
        """
        usb_drive = self._host_usb_provider.get_hotplugged_usb_drive(self._phy)
        self._log.info("Hot-plugged USB drive='{}'".format(usb_drive))
        # self._host_usb_provider.format_drive(usb_drive)
        # self._host_usb_provider.copy_collateral_to_usb_drive(CollateralConstants.COLLATERAL_CMDTOOL, usb_drive)

        serial_number = self._host_usb_provider.get_drive_serial_number(usb_drive)
        self._log.info("Serial number of hot-plugged USB drive='{}'".format(serial_number))
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ExampleHostUsbDriveProvider.main() else Framework.TEST_RESULT_FAIL)
