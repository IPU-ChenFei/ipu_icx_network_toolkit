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
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.uefi_shell import UefiShellProvider
from dtaf_core.providers.physical_control import PhysicalControlProvider

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.bios_util import ChooseBoot
from src.lib.bios_util import BootOptions
import src.lib.content_exceptions as content_exceptions


class ExampleChooseBoot(BaseTestCase):
    """
    Test Storage Provider APIs.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        super(ExampleChooseBoot, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_cfg, test_log)  # type:  AcPowerControlProvider

        bios_boot_menu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self._bios_boot_menu_obj = ProviderFactory.create(bios_boot_menu_cfg, test_log)  # type: BiosBootMenuProvider

        uefi_cfg = cfg_opts.find(UefiShellProvider.DEFAULT_CONFIG_PATH)
        self._uefi = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider

        self._common_content_lib = CommonContentLib(test_log, self._os, cfg_opts)
        self._content_cfg = ContentConfiguration(test_log)

        try:
            phy_cfg = cfg_opts.find(PhysicalControlProvider.DEFAULT_CONFIG_PATH)
            self._phy = ProviderFactory.create(phy_cfg, test_log)  # type: PhysicalControlProvider
        except Exception as ex:
            self._log.error("Physical controller configuration not populated in System_Configuration.xml...")
            raise content_exceptions.TestSetupError(ex)

        self._choose_boot = ChooseBoot(self._bios_boot_menu_obj, self._content_cfg, test_log, self._ac, self._os, cfg_opts)

    def prepare(self):
        """
        prepare.
        """
        pass

    def execute(self):
        """
        executes storage provider APIs.
        """
        self._phy.connect_usb_to_sut(10)
        self._choose_boot.boot_choice(BootOptions.UEFI)
        self._log.info("Waiting to boot to UEFI...")
        self._uefi.wait_for_uefi(self._content_cfg.get_reboot_timeout())
        result = self._uefi.execute("map -r", 10)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac)
        self._os.wait_for_os(self._content_cfg.get_reboot_timeout())
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ExampleChooseBoot.main() else Framework.TEST_RESULT_FAIL)
