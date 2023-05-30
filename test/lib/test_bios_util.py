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
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.uefi_shell import UefiShellProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider

from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.bios_util import ItpXmlCli
from src.lib.bios_util import BootOptions


class TestBiosUtil(BaseTestCase):
    """
    Test bios util APIs.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        super(TestBiosUtil, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)

        csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._csp = ProviderFactory.create(csp_cfg, test_log)  # type: SiliconRegProvider

        self._itp_xmlcli = ItpXmlCli(self._log, self._cfg)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider

        uefi_cfg = cfg_opts.find(UefiShellProvider.DEFAULT_CONFIG_PATH)
        print("uefi_cfg created...")
        self._uefi = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider
        print("UEFI obeject created...")

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        pass

    def execute(self):
        """
        Copy platform specific smbios configuration file to C:||Automation folder if it does not exists.
        """
        platform_xml_file = self._itp_xmlcli.get_platform_config_file_path()
        self._log.info("The platform config file '{}' generated successfully...".format(platform_xml_file))
        current_boot_order_string = self._itp_xmlcli.get_current_boot_order_string()
        self._itp_xmlcli.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac)
        self._uefi.wait_for_uefi(1800)
        self._itp_xmlcli.set_boot_order(current_boot_order_string)
        self._common_content_lib.perform_graceful_ac_off_on(self._ac)
        self._os.wait_for_os(1800)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TestBiosUtil.main() else Framework.TEST_RESULT_FAIL)
