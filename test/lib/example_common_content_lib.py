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
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.lib.common_content_lib import CommonContentLib


class ExampleCommonContentLib(BaseTestCase):

    def __init__(self, test_log, arguments, cfg_opts):
        super(ExampleCommonContentLib, self).__init__(test_log, arguments, cfg_opts)
        self._cfg = cfg_opts
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self._common_content_lib = CommonContentLib(test_log, self._os, cfg_opts)

    def execute(self):
        cpu_family = self._common_content_lib.get_platform_family()
        self._log.info("CPU family = {}.".format(cpu_family))
        pch_family = self._common_content_lib.get_pch_family()
        self._log.info("PCH family = {}.".format(pch_family))
        stepping = self._common_content_lib.get_platform_stepping()
        self._log.info("CPU Stepping family = {}.".format(stepping))
        qdf = self._common_content_lib.get_processor_qdf()
        self._log.info("CPU qdf = {}.".format(qdf))
        platform_type = self._common_content_lib.get_platform_type()
        self._log.info("Platform type = {}.".format(platform_type))
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ExampleCommonContentLib.main() else Framework.TEST_RESULT_FAIL)
