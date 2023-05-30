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
import os
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider

from src.lib.common_content_lib import CommonContentLib
from src.lib.dtaf_content_constants import BootScriptConstants


class TestEgsBootScript(BaseTestCase):
    """
    Test boot script lib.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        super(TestEgsBootScript, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self.sdp_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = None

        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider

        self.csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._csp = None

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        pass

    def execute(self):
        """
        Copy platform specific smbios configuration file to C:||Automation folder if it does not exists.
        """
        # perform graceful ac off and on
        if self._os.is_alive():
            self._log.info("OS is alive, shutting down SUT...")
            self._os.shutdown(10)

        self._log.info("Powering off SUT...")
        self._ac.ac_power_off(10)
        time.sleep(10)
        self._log.info("Powering on SUT...")
        self._ac.ac_power_on(10)
        time.sleep(20)

        if self._common_content_lib.is_bootscript_required():
            ret_val = self._common_content_lib.execute_boot_script()
            if not ret_val:
                self._log.error("Boot script failed...")
                return False
            self._log.error("Boot script succeeded...")
        else:
            self._log.info("Boot script not required for this target...")

        self._log.info("Waiting for os to be alive...")
        self._os.wait_for_os(2000)

        result = self._os.execute("ls -l", 5)
        self._log.info("test result='{}'".format(result.stdout))

        self._sdp = ProviderFactory.create(self.sdp_cfg, self._log)  # type: SiliconDebugProvider
        self._csp = ProviderFactory.create(self.csp_cfg, self._log)  # type: SiliconRegProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, None)
        
        # to test if cscript works, we will get
        cpu_chop_info = self._common_content_lib.get_cpu_physical_chop_info(self._csp, self._sdp, "cpu_log_file.log")
        self._log.info("CPU Chop Info='{}'".format(cpu_chop_info))

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TestEgsBootScript.main() else Framework.TEST_RESULT_FAIL)
