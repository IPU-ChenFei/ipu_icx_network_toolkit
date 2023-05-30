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
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.console_log import ConsoleLogProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.lib.common_content_lib import CommonContentLib


class ExampleConProvider(BaseTestCase):
    """
    Test Storage Provider APIs.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        super(ExampleConProvider, self).__init__(test_log, arguments, cfg_opts)
        os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(os_cfg, self._log)
        self.con_cfg = cfg_opts.find(ConsoleLogProvider.DEFAULT_CONFIG_PATH)

    def get_con_provider(self):
        con_obj = ProviderFactory.create(self.con_cfg, self._log)  # type: ConsoleLogProvider
        return con_obj

    def prepare(self):
        """
        prepare.
        """
        pass

    def execute(self):
        """
        executes storage provider APIs.
        """
        serial_log = "serial_log_{}.log"
        for index in range(3):
            with self.get_con_provider() as con_obj:
                con_obj.redirect(serial_log.format(index))
                self._os.reboot(900)
                self._log.info("SUT booted to OS")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ExampleConProvider.main() else Framework.TEST_RESULT_FAIL)
