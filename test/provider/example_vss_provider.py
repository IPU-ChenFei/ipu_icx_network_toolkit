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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.memory.lib.memory_common_lib import MemoryCommonLib
from src.provider.vss_provider import VssProvider


class VSSTestProvider(BaseTestCase):
    """
    Class to test VSS functionalitites
    """

    def __init__(self, test_log, arguments, cfg_opts):

        super(VSSTestProvider, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self._memory_common_lib = MemoryCommonLib(test_log, cfg_opts, self._os)
        self._vss_provider = VssProvider.factory(test_log, os_obj=self._os, cfg_opts=cfg_opts)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        if not self._os.is_alive():
            self._log.error("System is not alive")
            raise RuntimeError("OS is not alive")

    def execute(self):  # type: () -> bool
        """
        Function to test one of the install collateral functionalities.
        """
        list_processes = ["mem64.exe"]

        # Example code to show how you should call the methods..
        self._vss_provider.execute_vss_memory_test_package()

        # For safety purpose - Just to wait for 10 more sec, so that the process will start in the background.
        time.sleep(10)

        self._memory_common_lib.verify_background_process_running(' '.join(map(str, list_processes)))
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VSSTestProvider.main() else Framework.TEST_RESULT_FAIL)
