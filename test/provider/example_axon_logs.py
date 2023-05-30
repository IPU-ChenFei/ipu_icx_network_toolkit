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
import shutil
from xml.etree import ElementTree
import six
if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.common_content_lib import CommonContentLib
from src.lib.dtaf_content_constants import ProviderXmlConfigs


class ExampleAxonLogs(BaseTestCase):

    def __init__(self, test_log, arguments, cfg_opts):
        super(ExampleAxonLogs, self).__init__(test_log, arguments, cfg_opts)
        self._cfg = cfg_opts
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self._common_content_lib = CommonContentLib(test_log, self._os, cfg_opts)
        self.sdp = None
        self.sv = None

    def initialize_sdp_sv_objects(self):
        if self.sv is None:
            cpu = self._common_content_lib.get_platform_family()
            print(cpu)
            pch = self._common_content_lib.get_pch_family()
            print(pch)
            sv_cfg = ElementTree.fromstring(ProviderXmlConfigs.PYTHON_SV_XML_CONFIG.format(cpu, pch))
            print(sv_cfg)
            self.sv = ProviderFactory.create(sv_cfg, self._log)  # type: SiliconRegProvider

        # initialize sdp, if not already initialized
        if self.sdp is None:
            si_cfg = ElementTree.fromstring(ProviderXmlConfigs.SDP_XML_CONFIG)
            self.sdp = ProviderFactory.create(si_cfg, self._log)  # type: SiliconDebugProvider
        # initialize sv, if not already initialized

    def collect_axon_logs(self, post_code, cycle_num):
        try:
            self.initialize_sdp_sv_objects()
            print("sdp and sv objects created.")
            self.sdp.itp.unlock()
            status_scope = self.sv.get_status_scope_obj()
            # default_analyzers = ['ubox', 'm2iosf', 'cha', 'core', 'mcchnl', 'upi', 's3m', 'pm']
            default_analyzers = ['ubox']
            list_analyzers = default_analyzers

            self._common_content_lib.collect_axon_logs(post_code, cycle_num, list_analyzers, self.sdp, self.sv)
        except Exception as ex:
            self._log.error("Failed to collect axon logs due to exception: '{}'.".format(ex))

    def execute(self):
        self.collect_axon_logs("75", 10)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ExampleAxonLogs.main() else Framework.TEST_RESULT_FAIL)
