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
import time

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.provider.ptu_provider import PTUProvider


class ExamplePtuProvider(BaseTestCase):
    """
    Test Storage Provider APIs.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        super(ExamplePtuProvider, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self._common_content_lib = CommonContentLib(test_log, self._os, cfg_opts)
        self._install_collateral = InstallCollateral(test_log, self._os, cfg_opts)

        self._ptu_provider = PTUProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self._os,)  # type: PTUProvider

    def prepare(self):
        """
        prepare.
        """
        pass

    def execute(self):
        """
        executes storage provider APIs.
        """
        ptu_path = self._ptu_provider.install_ptu()
        print("PTU Installed..")

        self._ptu_provider.kill_ptu_tool()
        self._ptu_provider.set_percent_cores_to_stress(40)

        self._ptu_provider.execute_async_ptu_tool(self._ptu_provider.PTUMON_CPU_CT3, executor_path=ptu_path)

        if self._ptu_provider.check_ptu_app_running():
            self._log.info("PTU is running !!!")

        time.sleep(30)

        self._ptu_provider.kill_ptu_tool()
        if self._ptu_provider.check_ptu_app_running():
            self._log.info("PTU is still running !!!")
        else:
            self._log.info("PTU is killed !!!")
            self._ptu_provider.capture_ptu_logs(r"c:\temp")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ExamplePtuProvider.main() else Framework.TEST_RESULT_FAIL)
