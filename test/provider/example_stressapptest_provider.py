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
from src.provider.host_usb_drive_provider import HostUsbDriveProvider
from src.provider.stressapp_provider import StressAppTestProvider


class ExampleStressAppTestProvider(BaseTestCase):
    """
    Test Storage Provider APIs.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        super(ExampleStressAppTestProvider, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self._common_content_lib = CommonContentLib(test_log, self._os, cfg_opts)
        self._host_usb_provider = HostUsbDriveProvider.factory(test_log, cfg_opts, self._os)  # type: HostUsbDriveProvider

        self._install_collateral = InstallCollateral(test_log, self._os, cfg_opts)

        self._stress_app_provider = StressAppTestProvider.factory(test_log, os_obj=self._os,
                                                                  cfg_opts=cfg_opts)  # type: StressAppTestProvider

    def prepare(self):
        """
        prepare.
        """
        pass

    def execute(self):
        """
        executes storage provider APIs.
        """
        self._install_collateral.install_stress_test_app()
        stress_app_execute_time = 10000

        stress_app_name = "stressapptest"
        stress_cmd_line = "./stressapptest -s {} -M -m -W -l stress.log ".format(stress_app_execute_time)
        self._stress_app_provider.execute_async_stress_tool(stress_cmd_line, stress_app_name)

        ret_code = self._stress_app_provider.check_app_running(stress_app_name, stress_cmd_line)
        self._log.info("Stress app return code='{}'".format(ret_code))

        time.sleep(180)

        self._stress_app_provider.kill_stress_tool(stress_app_name, stress_cmd_line)
        time.sleep(10)
        ret_code = self._stress_app_provider.check_app_running(stress_app_name, stress_cmd_line)
        self._log.info("Stress app return code='{}'".format(ret_code))
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ExampleStressAppTestProvider.main() else Framework.TEST_RESULT_FAIL)
