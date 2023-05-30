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

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from src.lib.boot_script_lib import BootScript
from src.lib.common_content_lib import CommonContentLib


class ExecuteBootScript(BaseTestCase):
    """
    Executes the boot script.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        super(ExecuteBootScript, self).__init__(test_log, arguments, cfg_opts)

        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider

        sut_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_cfg, test_log)

        sdp_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(sdp_cfg, test_log)

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

        self._boot_script_obj = BootScript(self._log, self._sdp, self._ac, self._common_content_lib, cfg_opts)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        pass

    def execute(self):
        """
        Copy platform specific smbios configuration file to C:||Automation folder if it does not exists.
        """

        if not self._boot_script_obj.run_boot_script():
            return False

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ExecuteBootScript.main() else Framework.TEST_RESULT_FAIL)
