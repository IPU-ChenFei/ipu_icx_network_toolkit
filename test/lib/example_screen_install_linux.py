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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.lib.install_collateral import InstallCollateral


class ExampleScreenInstallLinux(BaseTestCase):
    """
    Test Storage Provider APIs.
    """
    _SCREEN_ZIP_NAME = "screen.zip"
    _SCREEN_RPM_NAME = "screen-4.1.0-0.25.20120314git3c2946.el7.x86_64.rpm"

    def __init__(self, test_log, arguments, cfg_opts):
        super(ExampleScreenInstallLinux, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self._install_collateral = InstallCollateral(test_log, self._os, cfg_opts)

    def prepare(self):
        """
        prepare.
        """
        pass

    def execute(self):
        """
        Installs screen rpm
        """
        self._install_collateral.screen_package_installation()
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ExampleScreenInstallLinux.main() else Framework.TEST_RESULT_FAIL)
